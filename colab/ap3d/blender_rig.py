"""Script de Blender (4.2 LTS o mas nuevo) que se ejecuta sin ventana:

    blender -b -t 0 -P blender_rig.py -- --in modelo.glb --out carpeta [...]

Hace:
  1. Importa la malla texturizada, la une, la pone de pie en el suelo,
     centrada y a la altura pedida (1.80 m por defecto).
  2. Detecta las proporciones del cuerpo (cadera, hombros, manos, pies)
     midiendo la propia malla, y crea un esqueleto con nombres de Mixamo
     (mixamorig:Hips, ...) para que sirvan las animaciones de Mixamo,
     Unity, Unreal y Blender.
  3. Pesos: se calculan sobre una copia remallada y cerrada (voxel) con
     el metodo de calor de Blender y se transfieren a la malla real. Asi
     no fallan por agujeros y cada hueso mueve su zona completa (no solo
     una banda, como pasaba antes). Si aun asi falla, hay respaldo por
     distancia a los huesos.
  4. Crea animaciones (reposo, caminar, correr, saludar, saltar, bailar).
  5. Exporta GLB animado, FBX, BLEND (con texturas empaquetadas), OBJ,
     STL, piezas por hueso, LODs ligeros, visor web y videos.
  6. Repara vertices sin peso y reporta cuantos vertices mueve cada hueso.
"""
import argparse
import json
import math
import os
import sys
import time

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

T0 = time.time()


def log(*a):
    print(f"[rig {time.time() - T0:6.1f}s]", *a, flush=True)


# ----------------------------------------------------------------- args
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--in", dest="inp", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--rig", default="humanoide",
                choices=["auto", "humanoide", "cuadrupedo", "cabeza", "objeto", "vehiculo", "mueble", "ninguno"])
ap.add_argument("--height", type=float, default=1.8)
ap.add_argument("--rotate", type=float, default=0.0,
                help="giro extra en grados alrededor de Z")
ap.add_argument("--video", default="Caminar")
ap.add_argument("--video_res", type=int, default=1080)
ap.add_argument("--samples", type=int, default=48)
ap.add_argument("--turntable", type=int, default=1)
ap.add_argument("--loops", type=int, default=2)
ap.add_argument("--relieve", type=float, default=0.8,
                help="fuerza del mapa de relieve (normal) sacado de la textura; 0 = sin relieve")
ap.add_argument("--stage", default="all", choices=["all", "export", "extra", "video", "quads"],
                help="export: archivos y vista previa; video: solo videos. "
                     "Se lanzan los dos a la vez en procesos separados para ir el doble de rapido")
ap.add_argument("--preview", type=int, default=1, help="0 = no renderizar vista_previa.png")
ap.add_argument("--detalle", type=int, default=1,
                help="1 = esqueleto detallado: dedos de manos y pies, ojos y mandibula")
ap.add_argument("--memoria", default="", help="json con correcciones de tipo del usuario")
ap.add_argument("--huesos", default="", help="json del editor: mover articulaciones y huesos extra")
ap.add_argument("--tipo_activo", default="auto",
                choices=["auto", "character", "prop_rigid", "prop_articulated"],
                help="character: rig de personaje; prop_rigid: sin esqueleto; prop_articulated: rig rigido")
ap.add_argument("--caras", type=int, default=0,
                help="reducir a estas caras al importar (0 = no tocar); modo Optimizar")
ap.add_argument("--altura_prop", type=float, default=0.40, help="altura real de props en metros")
ap.add_argument("--roblox_tris", type=int, default=12000, help="0 = sin exportacion Roblox")
ap.add_argument("--fast", type=int, default=0, help="pruebas: video corto")
args = ap.parse_args(argv)
os.makedirs(args.out, exist_ok=True)
INFO = {"rig": args.rig, "avisos": []}

scene = bpy.context.scene
vl = bpy.context.view_layer
scene.render.fps = 30


# ------------------------------------------------------------ helpers
def _nodes(idb):
    """Activa nodos solo si hace falta (use_nodes esta obsoleto en Blender 5 y
    desaparece en 6: alli los materiales y mundos ya tienen nodos)."""
    if getattr(idb, "node_tree", None) is None:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            idb.use_nodes = True
    return idb


def deselect_all():
    for o in scene.objects:
        o.select_set(False)


def activate(o, others=()):
    deselect_all()
    for x in others:
        x.select_set(True)
    o.select_set(True)
    vl.objects.active = o


def fcurves_of(act):
    """Compatible con Blender 4.2 (action.fcurves) y 4.4+/5.x (capas)."""
    try:
        return list(act.fcurves)
    except AttributeError:
        pass
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []):
                out += list(cb.fcurves)
    return out


def verts_np(obj):
    me = obj.data
    co = np.empty(len(me.vertices) * 3, dtype=np.float64)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    M = np.array(obj.matrix_world)
    return co @ M[:3, :3].T + M[:3, 3]


# ------------------------------------------------------------ importar
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
vl = bpy.context.view_layer
scene.render.fps = 30
ext = os.path.splitext(args.inp)[1].lower()
if ext in (".glb", ".gltf"):
    bpy.ops.import_scene.gltf(filepath=args.inp)
elif ext == ".obj":
    bpy.ops.wm.obj_import(filepath=args.inp)
elif ext == ".fbx":
    bpy.ops.import_scene.fbx(filepath=args.inp)
else:
    raise SystemExit("formato no soportado: " + ext)

meshes = [o for o in scene.objects if o.type == "MESH"]
if not meshes:
    raise SystemExit("el archivo no tiene mallas")
for o in meshes:
    activate(o)
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
activate(meshes[0], meshes[1:])
if len(meshes) > 1:
    bpy.ops.object.join()
obj = vl.objects.active
obj.name = "Modelo"
for o in list(scene.objects):
    if o is not obj:
        bpy.data.objects.remove(o, do_unlink=True)
activate(obj)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
# Soldar vertices duplicados (costuras de UV, caras sueltas): si quedan
# separados, cada copia recibe un peso distinto y la malla se rasga en
# triangulos al animar. Las UV se conservan (Blender las guarda por esquina).
_nv0 = len(obj.data.vertices)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.remove_doubles(threshold=1e-5)
bpy.ops.object.mode_set(mode="OBJECT")
INFO["vertices_soldados"] = _nv0 - len(obj.data.vertices)

def _aristas_duras(o, grados=35.0):
    """Vertices en aristas con angulo diedro > 35 grados (esquinas de cajas,
    pedestales, marcos): se protegen al reducir triangulos."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(o.data)
    lim = math.radians(grados)
    out = set()
    for e in bm.edges:
        if len(e.link_faces) == 2:
            try:
                if e.calc_face_angle() > lim:
                    out.update(v.index for v in e.verts)
            except ValueError:
                pass
        elif len(e.link_faces) == 1:
            out.update(v.index for v in e.verts)      # borde abierto
    bm.free()
    return sorted(out)


def reducir_caras(o, objetivo, proteger=True):
    """Reduce a 'objetivo' caras con Decimate (conserva UV y textura); con
    proteger, los vertices de aristas > 35 grados no se colapsan."""
    n0 = len(o.data.polygons)
    if objetivo <= 0 or n0 <= objetivo:
        return n0
    activate(o)
    dm = o.modifiers.new("Reducir", "DECIMATE")
    dm.ratio = max(0.001, objetivo / n0)
    dm.use_collapse_triangulate = True
    if proteger:
        duras = _aristas_duras(o)
        if duras and len(duras) < 0.5 * len(o.data.vertices):
            g = o.vertex_groups.new(name="Reducir")
            g.add(list(range(len(o.data.vertices))), 1.0, "REPLACE")
            g.add(duras, 0.0, "REPLACE")
            dm.vertex_group = g.name
            INFO["aristas_protegidas"] = len(duras)
    bpy.ops.object.modifier_apply(modifier=dm.name)
    for g in list(o.vertex_groups):
        if g.name == "Reducir":
            o.vertex_groups.remove(g)
    return len(o.data.polygons)


if args.caras > 0:
    _c0 = len(obj.data.polygons)
    _c1 = reducir_caras(obj, args.caras)
    INFO["reduccion"] = {"antes": _c0, "despues": _c1}
    log("caras reducidas", _c0, "->", _c1)

# Normalizar: de pie, centrado, pies en Z=0, altura pedida, mirando a -Y
if args.rotate:
    obj.data.transform(Matrix.Rotation(math.radians(args.rotate), 4, "Z"))
co = verts_np(obj)
mn, mx = co.min(0), co.max(0)
h = max(mx[2] - mn[2], 1e-6)
s = args.height / h
cx, cy = (mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2
obj.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation((-cx, -cy, -mn[2])))
obj.data.update()
bpy.ops.object.shade_smooth() if len(obj.data.polygons) < 400000 else None
co = verts_np(obj)
H = float(co[:, 2].max())
INFO.update(vertices=len(obj.data.vertices), caras=len(obj.data.polygons),
            altura_m=round(H, 3))
log("malla", INFO["vertices"], "vertices", INFO["caras"], "caras")
def has_gap(vals, bins=24):
    """Hay un hueco en el centro (dos piernas separadas, patas...)."""
    if len(vals) < 50:
        return False
    h, _ = np.histogram(vals, bins)
    # suavizar: un hueco real (entre piernas) ocupa varias casillas; una
    # casilla vacia suelta es solo la rejilla regular de vertices
    h = np.convolve(h, [1, 1, 1], "same")
    inner = h[3:-3]
    return bool(len(inner)) and (inner.min() <= 0.02 * h.max())


def rectangularity(p):
    """Area del casco convexo / area de su rectangulo minimo alineado al
    casco (1.0 = rectangulo, 0.785 = elipse, 0.5 = triangulo)."""
    p = np.unique(np.round(p, 5), axis=0)
    if len(p) < 4:
        return None
    p = p[np.lexsort((p[:, 1], p[:, 0]))]

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for q in p:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    for q in p[::-1]:
        while len(up) >= 2 and cross(up[-2], up[-1], q) <= 0:
            up.pop()
        up.append(q)
    h = np.array(lo[:-1] + up[:-1])
    if len(h) < 3:
        return None
    area = 0.5 * abs(np.dot(h[:, 0], np.roll(h[:, 1], 1)) - np.dot(h[:, 1], np.roll(h[:, 0], 1)))
    best = None
    for i in range(len(h)):
        e = h[(i + 1) % len(h)] - h[i]
        n_ = np.linalg.norm(e)
        if n_ < 1e-12:
            continue
        u = e / n_
        w = np.array([-u[1], u[0]])
        a_ = np.ptp(h @ u) * np.ptp(h @ w)
        best = a_ if best is None else min(best, a_)
    return float(area / best) if best else None


def classify(co, H):
    """persona / cuadrupedo / cabeza (busto) / objeto, midiendo la malla:
    piernas separadas, brazos (hombros mucho mas anchos que la cintura),
    cuello (franja estrecha bajo una parte ancha) y proporciones."""
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    ancho = float(x.max() - x.min())
    largo = float(y.max() - y.min())
    low = co[z < 0.07 * H]
    frac_low = len(low) / max(len(co), 1)
    piernas_x = has_gap(low[:, 0]) if len(low) else False
    patas_y = has_gap(low[:, 1]) if len(low) else False

    def width(z0, z1):
        sl = co[(z >= z0 * H) & (z < z1 * H)]
        if len(sl) < 20:
            return 0.0
        return float(np.percentile(sl[:, 0], 98) - np.percentile(sl[:, 0], 2))

    prof = [width(i / 20, (i + 1) / 20) for i in range(20)]
    cintura = max(width(0.40, 0.60), 1e-6)
    hombros = max(prof[14:19])
    brazos = hombros > 1.8 * cintura and H > 1.5 * largo
    # cuello: un tramo estrecho con algo bastante mas ancho encima y debajo
    cuello = False
    for i in range(2, 15):
        w = prof[i]
        if w <= 0:
            continue
        arriba = max(prof[i + 1:])
        abajo = max(prof[:i])
        if arriba > 1.6 * w and abajo > 1.6 * w:
            cuello = True
            break
    # base en forma de caja / pedestal (Jack-in-the-Box, caja musical,
    # vitrina): seccion rectangular (casco convexo ~ su rectangulo) y ancho
    # constante en el 5-30 % inferior. Un busto tiene seccion eliptica (~0.78).
    rects, anchos = [], []
    for i in range(1, 6):
        sl = co[(z >= i * 0.05 * H) & (z < (i + 1) * 0.05 * H)][:, :2]
        if len(sl) < 30:
            continue
        r_ = rectangularity(sl)
        if r_ is not None:
            rects.append(r_)
            anchos.append(prof[i])
    # 0.95: dos piernas juntas dan ~0.91, una caja 0.99-1.0
    base_caja = (len(rects) >= 3 and float(np.median(rects)) > 0.95
                 and max(anchos) < 1.15 * max(min(anchos), 1e-6)
                 and max(anchos) > 0.45 * max(prof))
    medida = {"ancho": round(ancho / H, 2), "largo": round(largo / H, 2),
              "base_caja": bool(base_caja), "plano": bool(min(ancho, largo) < 0.07 * max(ancho, H)), "rect_base": round(float(np.median(rects)), 2) if rects else None,
              "piernas": bool(piernas_x), "patas": bool(patas_y), "brazos": bool(brazos),
              "cuello": cuello, "base": round(frac_low, 3)}
    L_ = max(ancho, largo)
    low_l = low[:, 1] if largo >= ancho else low[:, 0]
    ruedas = has_gap(low_l) if len(low) else False
    medida["ruedas"] = bool(ruedas)
    if H < 0.55 * L_ and ruedas and not brazos:
        tipo = "vehiculo"
    elif base_caja:
        tipo = "objeto"                       # figura sobre caja/pedestal: prop
    elif min(ancho, largo) < 0.07 * max(ancho, H):
        tipo = "objeto"                       # plano y fino: cuadro, marco, placa, espejo
    elif largo > 1.05 * H and patas_y and frac_low < 0.15:
        tipo = "cuadrupedo"
    elif (piernas_x and H > 1.15 * largo) or brazos:
        tipo = "humanoide"
    elif cuello:
        tipo = "cabeza"
    else:
        tipo = "objeto"
    # Lo aprendido del usuario: si corrigio antes un modelo con medidas
    # parecidas, se usa su eleccion (vecino mas cercano).
    try:
        if args.memoria and os.path.exists(args.memoria):
            ej = json.load(open(args.memoria)).get("tipos", [])
            fv = np.array([float(medida.get(k, 0)) for k in
                           ("ancho", "largo", "base", "piernas", "patas", "brazos", "cuello")])
            # 3 vecinos mas cercanos, voto pesado por cercania
            vec = sorted(((float(np.linalg.norm(fv - np.array(e["f"]))), e["tipo"]) for e in ej
                          if len(e.get("f", [])) == len(fv)))[:3]
            votos = {}
            for dist, t_ in vec:
                if dist < 0.35:
                    votos[t_] = votos.get(t_, 0.0) + 1.0 / (dist + 0.05)
            if votos:
                t_best = max(votos, key=votos.get)
                conf = votos[t_best] / sum(votos.values())
                medida["confianza_aprendida"] = round(conf, 2)
                if t_best != tipo and conf >= 0.6:
                    log("aprendido de tus correcciones ->", t_best, "confianza", round(conf, 2))
                    medida["aprendido_de"] = tipo
                    tipo = t_best
    except Exception as e:
        log("memoria no leida:", e)
    INFO["clasificacion"] = dict(medida, tipo=tipo)
    return tipo


MUEBLE = {}


def find_panels(co, H):
    """Puertas y cajones en el frente (-Y) de un mueble: mapa de profundidad
    del frente; las ranuras (zonas mas hundidas) separan los paneles.
    Panel alto = puerta con bisagra al lado de fuera; ancho = cajon."""
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    ymin, ymax = float(y.min()), float(y.max())
    D = ymax - ymin
    if D < 0.05 * H:
        return []
    xmin, xmax = float(x.min()), float(x.max())
    W = xmax - xmin
    n = 72
    gx = np.clip(((x - xmin) / max(W, 1e-9) * (n - 1)).astype(int), 0, n - 1)
    gz = np.clip((z / max(H, 1e-9) * (n - 1)).astype(int), 0, n - 1)
    depth = np.full((n, n), np.nan)
    order = np.argsort(-y)            # el mas al frente (menor y) queda al final
    depth[gz[order], gx[order]] = y[order]
    front = np.nanpercentile(depth, 10)
    rel = depth - front
    face = rel < 0.06 * D                       # celdas del plano frontal
    groove = (rel >= 0.006 * D) & (rel < 0.25 * D)
    panel = face & ~groove
    # componentes conexas (4-vecinos)
    lab = np.zeros((n, n), dtype=int)
    k = 0
    comps = []
    for i in range(n):
        for j in range(n):
            if panel[i, j] and lab[i, j] == 0:
                k += 1
                st, cells = [(i, j)], []
                lab[i, j] = k
                while st:
                    a, b = st.pop()
                    cells.append((a, b))
                    for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        u, v = a + da, b + db
                        if 0 <= u < n and 0 <= v < n and panel[u, v] and lab[u, v] == 0:
                            lab[u, v] = k
                            st.append((u, v))
                comps.append(cells)
    out = []
    for cells in comps:
        if len(cells) < 0.015 * n * n or len(cells) > 0.85 * n * n:
            continue
        c = np.array(cells)
        z0, z1 = c[:, 0].min() / (n - 1) * H, (c[:, 0].max() + 1) / (n - 1) * H
        x0 = xmin + c[:, 1].min() / (n - 1) * W
        x1 = xmin + (c[:, 1].max() + 1) / (n - 1) * W
        fill = len(cells) / max((np.ptp(c[:, 0]) + 1) * (np.ptp(c[:, 1]) + 1), 1)
        if fill < 0.6:
            continue
        w, h = x1 - x0, z1 - z0
        kind = "cajon" if w > 1.4 * h else "puerta"
        # bisagra hacia el borde exterior del mueble
        hinge = x0 if (x0 + x1) / 2 < (xmin + xmax) / 2 else x1
        out.append(dict(kind=kind, x0=x0, x1=x1, z0=z0, z1=z1, hinge=hinge, front=ymin, D=D))
    # Un mueble de verdad tiene ranuras que separan al menos 2 paneles
    if len(out) < 2 or groove.sum() < 0.01 * n * n:
        return []
    return out[:8]


if args.rig == "auto":
    args.rig = classify(co, H)
    if args.rig == "objeto":
        try:
            _pn = find_panels(co, H)
            if _pn:
                args.rig = "mueble"
                INFO["clasificacion"]["tipo"] = "mueble"
        except Exception as e:
            log("paneles:", e)
    INFO["rig"] = args.rig
    log("esqueleto automatico:", args.rig, INFO.get("clasificacion"))

# ---- tipo de activo: personaje / prop rigido / prop articulado
PERSONAJES = ("humanoide", "cuadrupedo", "cabeza")
ta = args.tipo_activo
if ta == "character" and args.rig not in ("humanoide", "cuadrupedo") and args.rig != "ninguno":
    args.rig = "humanoide"                # "Personaje" pedido: rig Mixamo
elif ta == "prop_rigid":
    args.rig = "ninguno"                  # sin Armature ni deformacion
elif ta == "prop_articulated" and args.rig in PERSONAJES:
    args.rig = "objeto"
elif ta == "auto" and args.rig == "objeto":
    ta = "prop_rigid"                     # un objeto suelto no necesita huesos
    args.rig = "ninguno"
if ta == "auto":
    ta = "character" if args.rig in PERSONAJES else (
        "prop_articulated" if args.rig in ("vehiculo", "mueble", "objeto") else "prop_rigid")
INFO["tipo_activo"] = ta
INFO["rig"] = args.rig
ES_PROP = ta.startswith("prop")
if ES_PROP and args.rig != "vehiculo" and args.altura_prop > 0 and abs(args.altura_prop - H) > 1e-3:
    # Escala real de prop (un Jack-in-the-Box no mide 1.70 m); pivote en la base.
    # Objeto acostado (linterna, espada, llave): la medida va al lado mayor.
    lado_ = float(max(co[:, 0].max() - co[:, 0].min(), co[:, 1].max() - co[:, 1].min()))
    acostado = H < 0.5 * lado_
    k_ = args.altura_prop / (lado_ if acostado else H)
    INFO["escala_prop"] = "lado mayor (acostado)" if acostado else "altura"
    obj.data.transform(Matrix.Scale(k_, 4))
    obj.data.update()
    co = verts_np(obj)
    H = float(co[:, 2].max())
    INFO["altura_m"] = round(H, 3)
    log("prop escalado a", round(H, 3), "m")
mn_, mx_ = co.min(0), co.max(0)
INFO["pivote"] = {"x": round(float((mn_[0] + mx_[0]) / 2), 4), "y": round(float((mn_[1] + mx_[1]) / 2), 4),
                  "z_min": round(float(mn_[2]), 4)}
# Aristas duras: props con suavizado por angulo (35 grados) para que cajas,
# marcos y metal no se vean derretidos; personajes con suavizado completo.
activate(obj)
try:
    if ES_PROP:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35), keep_sharp_edges=True)
        INFO["aristas_duras"] = "35 grados"
except Exception:
    try:
        bpy.ops.object.shade_smooth()
        obj.data.use_auto_smooth = True
        obj.data.auto_smooth_angle = math.radians(35)
    except Exception:
        pass

# Material: asegurar que se vea en Cycles / Eevee / visores
for slot in obj.material_slots:
    m = slot.material
    if m and m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                try:
                    n.inputs["Roughness"].default_value = 0.65
                except Exception:
                    pass


# ------------------------------------------------- deteccion de cuerpo
def detect_humanoid(co, H):
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    # Entrepierna: punto mas alto sin malla en la franja central bajo 0.6H
    strip = co[(np.abs(x) < 0.025 * H) & (z < 0.62 * H) & (z > 0.12 * H)]
    crotch = float(strip[:, 2].min()) if len(strip) else 0.48 * H
    crotch_raw = crotch
    if not (0.42 * H <= crotch <= 0.55 * H):
        crotch = 0.48 * H        # muslos juntos: proporcion humana media
    hip_z = crotch + 0.04 * H

    # Pies
    feet = co[z < 0.06 * H]
    lf = feet[feet[:, 0] > 0]
    rf = feet[feet[:, 0] < 0]
    fx_l = float(np.median(lf[:, 0])) if len(lf) else 0.09 * H
    fx_r = float(np.median(rf[:, 0])) if len(rf) else -0.09 * H
    toe_y = float(feet[:, 1].min()) if len(feet) else -0.12 * H
    heel_y = float(feet[:, 1].max()) if len(feet) else 0.03 * H

    # Ancho de la pierna a la altura de la cadera
    band = co[(z > crotch - 0.06 * H) & (z < crotch)]
    leg_x = 0.085 * H
    if len(band):
        bl = band[band[:, 0] > 0.01 * H]
        if len(bl):
            leg_x = float(np.median(bl[:, 0]))
    leg_x = min(max(leg_x, 0.05 * H), 0.14 * H)

    # Cuello real: franja central mas estrecha entre 45 % y 92 % de la altura
    # con la cabeza (mas ancha) encima. Personajes cabezones (chibi, mascotas)
    # tienen el cuello mucho mas abajo que el 86 % humano.
    neck_z = 0.86 * H
    cen = co[np.abs(x) < 0.30 * H]
    best = None
    for zz in np.linspace(0.45 * H, 0.92 * H, 48):
        sl = cen[np.abs(cen[:, 2] - zz) < 0.012 * H]
        if len(sl) < 15:
            continue
        w = float(np.percentile(sl[:, 0], 95) - np.percentile(sl[:, 0], 5))
        above = cen[(cen[:, 2] > zz + 0.03 * H) & (cen[:, 2] < zz + 0.15 * H)]
        if len(above) < 15:
            continue
        wa = float(np.percentile(above[:, 0], 95) - np.percentile(above[:, 0], 5))
        below = cen[(cen[:, 2] < zz - 0.03 * H) & (cen[:, 2] > zz - 0.15 * H)]
        if len(below) < 15:
            continue
        wb = float(np.percentile(below[:, 0], 95) - np.percentile(below[:, 0], 5))
        # cuello real: mas estrecho que lo de arriba (cabeza) Y que lo de abajo
        if wa > 1.25 * w and wb > 1.15 * w and (best is None or w / wa < best[0]):
            best = (w / wa, float(zz))
    if best is not None:
        neck_z = best[1]
    neck_z = min(max(neck_z, 0.45 * H), 0.9 * H)
    cabezon = neck_z < 0.78 * H
    if cabezon:
        # cuerpo corto: la entrepierna real esta mas abajo
        lim = neck_z - 0.15 * H
        crotch = crotch_raw if 0.06 * H <= crotch_raw <= lim else min(crotch, 0.45 * neck_z)
        hip_z = crotch + 0.04 * H

    # Torso: ancho en el pecho (justo bajo el cuello)
    c0, c1 = (neck_z - 0.16 * H, neck_z - 0.08 * H)
    chest = co[(z > c0) & (z < c1) & (np.abs(x) < 0.30 * H)]
    sh_x = float(np.abs(chest[:, 0]).max()) * 0.80 if len(chest) else 0.11 * H
    sh_x = min(max(sh_x, 0.06 * H), 0.2 * H)
    sh_z = neck_z - 0.045 * H
    torso_y = float(np.median(chest[:, 1])) if len(chest) else 0.0

    # Manos: el punto mas lejano a cada lado entre 0.40H y 0.95H
    def hand(side):
        c = co[(z > 0.25 * H) & (z < neck_z) & (side * x > sh_x + 0.04 * H)]
        if len(c) < 20:
            return Vector((side * (sh_x + 0.10 * H), torso_y, sh_z - 0.25 * (sh_z - hip_z))), False
        i = int(np.argmax(side * c[:, 0] + 0.15 * c[:, 2] / H))
        tip = c[i]
        near = c[np.linalg.norm(c - tip, axis=1) < 0.05 * H]
        p = near.mean(0)
        return Vector((float(p[0]), float(p[1]), float(p[2]))), True

    hl, okl = hand(1)
    hr, okr = hand(-1)
    if not (okl and okr):
        INFO["avisos"].append("brazos pegados al cuerpo: se usaron "
                              "proporciones estandar")
    return dict(H=H, crotch=crotch, hip_z=hip_z, fx_l=fx_l, fx_r=fx_r,
                toe_y=toe_y, heel_y=heel_y, leg_x=leg_x, sh_x=sh_x,
                sh_z=sh_z, torso_y=torso_y, hand_l=hl, hand_r=hr,
                neck_z=neck_z, cabezon=cabezon)


CLOTH = {}          # vertice de tela (falda/tunica) -> cuanto cuelga (0..1)
TELA = []           # cadenas de huesos de tela: [(nombre, angulo, nivel)]


def cloth_chains():
    """Huesos de tela: 4 cadenas de 3 huesos (frente, atras, izq., der.)
    que cuelgan de la cadera hasta el borde de la tunica. Los vertices de
    tela pasan a esos huesos segun su angulo y altura, y las animaciones
    les dan movimiento secundario (inercia y balanceo)."""
    # Solo si de verdad hay tela suelta (tunica, falda, capa larga)
    if len(CLOTH) < max(1500, 0.04 * len(obj.data.vertices)):
        return 0
    if sum(1 for k in CLOTH.values() if k > 0.5) < 600:
        return 0
    P = "mixamorig:"
    co_ = verts_np(obj)
    idx = np.fromiter(CLOTH.keys(), dtype=np.int64)
    pts = co_[idx]
    hips = arm.data.bones.get(P + "Hips")
    if hips is None:
        return 0
    hc = np.array(hips.head_local)
    top = float(hc[2])
    hem = float(np.percentile(pts[:, 2], 2))
    if top - hem < 0.12 * H:
        return 0
    ang = np.arctan2(pts[:, 0] - hc[0], -(pts[:, 1] - hc[1]))   # 0 = frente
    rad = np.hypot(pts[:, 0] - hc[0], pts[:, 1] - hc[1])
    LADOS = (("Frente", 0.0), ("Izq", math.pi / 2), ("Atras", math.pi), ("Der", -math.pi / 2))
    bpy.ops.object.mode_set(mode="OBJECT")
    activate(arm)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.data.edit_bones
    levels = [top - (top - hem) * f for f in (0.0, 0.35, 0.68, 1.0)]
    for lado, a0 in LADOS:
        sel = np.abs(np.angle(np.exp(1j * (ang - a0)))) < math.pi / 4
        r = float(np.median(rad[sel])) if sel.sum() > 20 else float(np.median(rad))
        prev = eb[P + "Hips"]
        for i in range(3):
            n = f"{P}Tela{lado}{i + 1}"
            b = eb.new(n)
            rr = r * (0.55 + 0.45 * i / 2)
            b.head = Vector((hc[0] + math.sin(a0) * rr, hc[1] - math.cos(a0) * rr, levels[i]))
            b.tail = Vector((hc[0] + math.sin(a0) * rr * 1.08, hc[1] - math.cos(a0) * rr * 1.08,
                             levels[i + 1]))
            b.parent = prev
            b.use_connect = False
            prev = b
            TELA.append((n, a0, i))
    bpy.ops.object.mode_set(mode="OBJECT")
    for n, _, _ in TELA:
        if obj.vertex_groups.get(n) is None:
            obj.vertex_groups.new(name=n)
    gh = obj.vertex_groups.get(P + "Hips")
    gi = {g.index: g for g in obj.vertex_groups}
    me_ = obj.data
    for j, vi in enumerate(idx):
        v = me_.vertices[int(vi)]
        wh = next((e.weight for e in v.groups if e.group == gh.index), 0.0)
        if wh <= 0.01:
            continue
        h = (top - pts[j, 2]) / (top - hem)
        lvl = min(2, max(0, int(h * 3)))
        # reparto suave entre los 2 lados mas cercanos
        da = [(abs(np.angle(np.exp(1j * (ang[j] - a0)))), lado) for lado, a0 in LADOS]
        da.sort()
        (d1, l1), (d2, l2) = da[0], da[1]
        w1 = 1 - d1 / (d1 + d2 + 1e-9)
        move = wh * min(1.0, CLOTH[int(vi)]) * min(1.0, h * 1.6)
        gh.add([int(vi)], wh - move, "REPLACE")
        obj.vertex_groups[f"{P}Tela{l1}{lvl + 1}"].add([int(vi)], move * w1, "ADD")
        obj.vertex_groups[f"{P}Tela{l2}{lvl + 1}"].add([int(vi)], move * (1 - w1), "ADD")
    log("huesos de tela:", len(TELA))
    return len(TELA)


def cloth_weights():
    P = "mixamorig:"
    bones = arm.data.bones
    gidx = {g.name: g.index for g in obj.vertex_groups}
    iname = {v: k for k, v in gidx.items()}
    # miembro -> (huesos del miembro, hueso ancla, radio normal del miembro)
    LIMB = {}
    for side in ("Left", "Right"):
        LIMB.update({P + side + n: ("leg", P + "Hips", 0.075 * H) for n in ("UpLeg", "Leg")})
        LIMB.update({P + side + n: ("leg", P + "Hips", 0.06 * H)
                     for n in ("Foot", "ToeBase", "Toe1", "Toe2", "Toe3", "Toe4", "Toe5")})
        LIMB.update({P + side + n: ("arm", P + "Spine2", 0.055 * H) for n in ("Arm", "ForeArm")})
    seg = {}
    for n in LIMB:
        b = bones.get(n)
        if b is not None:
            seg[n] = (np.array(b.head_local), np.array(b.tail_local))
    if not seg:
        return 0
    me_ = obj.data
    co_ = verts_np(obj)
    moved = 0
    CLOTH.clear()
    gh = {}
    for v in me_.vertices:
        if not v.groups:
            continue
        e = max(v.groups, key=lambda x: x.weight)
        n = iname.get(e.group)
        if n not in seg:
            continue
        a_, c_ = seg[n]
        p = co_[v.index]
        ab = c_ - a_
        t = np.clip((p - a_) @ ab / max(ab @ ab, 1e-9), 0, 1)
        dist = np.linalg.norm(p - (a_ + t * ab))
        kind, anchor, r = LIMB[n]
        if dist <= r:
            continue
        # 0 dentro del miembro -> 1 cuando esta a 2.2 veces el radio
        k = min(1.0, (dist - r) / (1.2 * r))
        k = k * k * (3 - 2 * k)
        if kind == "arm":
            k *= 0.7          # mangas: siguen algo al brazo
        g_anchor = obj.vertex_groups.get(anchor)
        if g_anchor is None:
            continue
        for ge in v.groups:
            nm = iname.get(ge.group)
            if nm in seg:
                w0 = ge.weight
                obj.vertex_groups[nm].add([v.index], w0 * (1 - k), "REPLACE")
                g_anchor.add([v.index], w0 * k, "ADD")
        moved += 1
        if kind == "leg":
            CLOTH[v.index] = k
    log("tela: vertices liberados de piernas/brazos:", moved)
    return moved


REGION_ORDER = ["Cabeza", "Ojo izq.", "Ojo der.", "Mandibula", "Cuello", "Torso", "Cadera",
                "Hombro izq.", "Brazo izq.", "Antebrazo izq.", "Mano izq.", "Dedos mano izq.",
                "Hombro der.", "Brazo der.", "Antebrazo der.", "Mano der.", "Dedos mano der.",
                "Muslo izq.", "Pierna izq.", "Pie izq.", "Dedos pie izq.",
                "Muslo der.", "Pierna der.", "Pie der.", "Dedos pie der.", "Tela (túnica/capa)"]


def region_of(bone):
    """Nombre de la parte del cuerpo para un hueso (para piezas y GLB)."""
    n = bone.split(":")[-1]
    lado = " izq." if n.startswith("Left") else (" der." if n.startswith("Right") else "")
    core = n.replace("Left", "").replace("Right", "")
    if core.startswith("Hand") and core != "Hand":
        return "Dedos mano" + lado
    if core.startswith("Toe") and core != "ToeBase":
        return "Dedos pie" + lado
    tabla = {"Head": "Cabeza", "HeadTop_End": "Cabeza", "Eye": "Ojo", "Jaw": "Mandibula",
             "Neck": "Cuello", "Spine": "Torso", "Spine1": "Torso", "Spine2": "Torso",
             "Hips": "Cadera", "Shoulder": "Hombro", "Arm": "Brazo", "ForeArm": "Antebrazo",
             "Hand": "Mano", "UpLeg": "Muslo", "Leg": "Pierna", "Foot": "Pie", "ToeBase": "Pie"}
    if core.startswith("Tela"):
        return "Tela (túnica/capa)"
    if core in tabla:
        return tabla[core] + lado
    return core + lado


def head_bones(co, H):
    """Busto o cabeza: raiz, cuello, cabeza, mandibula y dos ojos."""
    P = "mixamorig:"
    z = co[:, 2]
    ty = float(np.median(co[:, 1]))
    # cuello = franja mas estrecha entre 15 % y 60 % de la altura
    best, neck_z = 1e9, 0.35 * H
    for zz in np.linspace(0.15 * H, 0.6 * H, 19):
        sl = co[np.abs(z - zz) < 0.02 * H]
        if len(sl) > 30:
            w = float(np.percentile(sl[:, 0], 97) - np.percentile(sl[:, 0], 3))
            if w < best:
                best, neck_z = w, float(zz)
    head_z = neck_z + 0.04 * H
    hv = co[z > head_z]
    front = float(np.percentile(hv[:, 1], 2)) if len(hv) else ty - 0.3 * H
    hw = float(np.percentile(hv[:, 0], 98) - np.percentile(hv[:, 0], 2)) if len(hv) else 0.6 * H
    hh = H - head_z
    ez = head_z + 0.55 * hh
    ex = 0.2 * hw
    dz = 0.1 * hh
    B = [("Hips", (0, ty, 0), (0, ty, max(neck_z - 0.1 * H, 0.05 * H)), None),
         ("Neck", (0, ty, max(neck_z - 0.1 * H, 0.05 * H)), (0, ty, head_z), "Hips"),
         ("Head", (0, ty, head_z), (0, ty, H), "Neck"),
         ("Jaw", (0, (front + ty) / 2, head_z + 0.3 * hh),
          (0, front + 0.02 * hh, head_z + 0.08 * hh), "Head")]
    for side, name in ((1, "Left"), (-1, "Right")):
        B.append((name + "Eye", (side * ex, front + 0.12 * hh, ez),
                  (side * ex, front + 0.01 * hh, ez), "Head"))
    INFO["cabeza"] = {"cuello_z": round(neck_z / H, 2)}
    return [(P + n, Vector(h), Vector(t), (P + p) if p else None) for n, h, t, p in B]


def object_bones(co, H):
    """Objeto: raiz + 3 huesos de abajo hacia arriba para doblarlo, saltar,
    flotar o bailar con estilo de dibujo animado."""
    cx = float(np.median(co[:, 0]))
    cy = float(np.median(co[:, 1]))
    B = [("Raiz", (cx, cy, 0), (cx, cy, 0.05 * H), None),
         ("Base", (cx, cy, 0.05 * H), (cx, cy, 0.38 * H), "Raiz"),
         ("Medio", (cx, cy, 0.38 * H), (cx, cy, 0.7 * H), "Base"),
         ("Arriba", (cx, cy, 0.7 * H), (cx, cy, H), "Medio")]
    return [(n, Vector(h), Vector(t), p) for n, h, t, p in B]


VEH = {}


def vehicle_bones(co, H):
    """Vehiculo: raiz, carroceria y 4 ruedas. Cada rueda delantera cuelga de
    un pivote de direccion vertical (la "T" que se usa en rigs de autos):
    el pivote gira para doblar y la rueda gira sobre su eje para avanzar."""
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    li = 1 if np.ptp(y) >= np.ptp(x) else 0       # eje largo
    si = 1 - li                                      # eje lateral
    L = float(np.ptp(co[:, li]))
    lmin, lmax = float(co[:, li].min()), float(co[:, li].max())
    smin, smax = float(co[:, si].min()), float(co[:, si].max())
    smid = (smin + smax) / 2
    r = min(0.42 * H, 0.17 * L)
    piso = co[z < 0.05 * H]
    ejes = []
    for half in (0, 1):
        lo, hi = (lmin, lmin + L / 2) if half == 0 else (lmin + L / 2, lmax)
        p = piso[(piso[:, li] >= lo) & (piso[:, li] < hi)]
        ejes.append(float(np.median(p[:, li])) if len(p) > 10 else lo + (0.18 if half == 0 else 0.32) * L)
    lado = 0.5 * (smax - smin) * 0.82
    # radio real: la cuerda de la rueda a una altura h cumple r = (w^2 + h^2) / 2h
    h_ = 0.10 * H
    est = []
    for e in ejes:
        band = co[(co[:, 2] < h_) & (np.abs(co[:, li] - e) < 0.3 * L)]
        if len(band) > 20:
            w = 0.5 * float(np.percentile(band[:, li], 97) - np.percentile(band[:, li], 3))
            est.append((w * w + h_ * h_) / (2 * h_))
    if est:
        r = float(np.clip(np.median(est), 0.12 * H, 0.45 * H))
    B = []

    def P(lv, sv, zv):
        v = [0.0, 0.0, zv]
        v[li] = lv
        v[si] = sv
        return Vector(v)

    lc = (lmin + lmax) / 2
    B.append(("Raiz", P(lc, smid, 0), P(lc, smid, 0.1 * H), None))
    B.append(("Carroceria", P(lc, smid, r), P(lc, smid, H), "Raiz"))
    VEH.update(li=li, si=si, r=r, ruedas={}, smid=smid)
    for eje, (pref, frente) in zip(ejes, (("D", True), ("T", False))):
        for sgn, ln in ((-1, "I"), (1, "D")):
            nm = f"Rueda_{pref}{ln}"
            c = P(eje, smid + sgn * lado, r)
            padre = "Raiz"
            if frente:
                piv = f"Direccion_{pref}{ln}"
                B.append((piv, c, c + Vector((0, 0, 0.6 * r)), "Raiz"))   # pivote vertical
                padre = piv
            eje_v = [0.0, 0.0, 0.0]
            eje_v[si] = sgn * 0.5 * r
            B.append((nm, c, c + Vector(eje_v), padre))                    # eje de la rueda
            VEH["ruedas"][nm] = (np.array(c), sgn)
    INFO["vehiculo"] = {"radio_rueda_m": round(r, 3), "ejes": [round(e, 3) for e in ejes],
                        "eje_largo": "Y" if li == 1 else "X"}
    return [(n, Vector(h), Vector(t), p) for n, h, t, p in B]


def vehicle_weights():
    """Pesos rigidos: cada punto dentro del cilindro de una rueda es 100 % de
    esa rueda; el resto, carroceria (un auto no se deforma como un cuerpo)."""
    li, si, r = VEH["li"], VEH["si"], VEH["r"]
    co_ = verts_np(obj)
    for g in list(obj.vertex_groups):
        obj.vertex_groups.remove(g)
    gb = obj.vertex_groups.new(name="Carroceria")
    asign = np.full(len(co_), -1)
    nombres = list(VEH["ruedas"])
    for k, nm in enumerate(nombres):
        c, sgn = VEH["ruedas"][nm]
        d = np.hypot(co_[:, li] - c[li], co_[:, 2] - c[2])
        lado_ok = (co_[:, si] - VEH["smid"]) * sgn > 0.45 * abs(c[si] - VEH["smid"])
        # solo el disco de la rueda: dentro del radio, por debajo de su borde
        # superior y en la banda lateral de la llanta (puertas y paneles fuera)
        banda = np.abs(co_[:, si] - c[si]) < 0.75 * r
        bajo = co_[:, 2] < c[2] + 0.98 * r
        asign[(d < 1.0 * r) & lado_ok & banda & bajo & (asign < 0)] = k
    for k, nm in enumerate(nombres):
        g = obj.vertex_groups.new(name=nm)
        idx = np.nonzero(asign == k)[0].tolist()
        if idx:
            g.add(idx, 1.0, "REPLACE")
    rest = np.nonzero(asign < 0)[0].tolist()
    gb.add(rest, 1.0, "REPLACE")
    INFO["vertices_por_rueda"] = {nm: int((asign == k).sum()) for k, nm in enumerate(nombres)}
    log("ruedas:", INFO["vertices_por_rueda"])


def furniture_bones(co, H):
    pan = find_panels(co, H)
    cx, cy = float(np.median(co[:, 0])), float(np.median(co[:, 1]))
    B = [("Raiz", (cx, cy, 0), (cx, cy, 0.05 * H), None),
         ("Cuerpo", (cx, cy, 0.05 * H), (cx, cy, H), "Raiz")]
    MUEBLE["paneles"] = []
    np_, nc_ = 0, 0
    for p in pan:
        if p["kind"] == "puerta":
            np_ += 1
            nm = f"Puerta_{np_}"
            hd = (p["hinge"], p["front"], p["z0"])
            B.append((nm, hd, (p["hinge"], p["front"], p["z1"]), "Cuerpo"))   # eje = bisagra
        else:
            nc_ += 1
            nm = f"Cajon_{nc_}"
            zc = (p["z0"] + p["z1"]) / 2
            xc = (p["x0"] + p["x1"]) / 2
            B.append((nm, (xc, p["front"] + 0.3 * p["D"], zc), (xc, p["front"], zc), "Cuerpo"))
        MUEBLE["paneles"].append((nm, p))
    INFO["mueble"] = {"puertas": np_, "cajones": nc_}
    return [(n, Vector(h), Vector(t), pa) for n, h, t, pa in B]


def furniture_weights():
    co_ = verts_np(obj)
    for g in list(obj.vertex_groups):
        obj.vertex_groups.remove(g)
    gb = obj.vertex_groups.new(name="Cuerpo")
    asign = np.full(len(co_), -1)
    for k, (nm, p) in enumerate(MUEBLE["paneles"]):
        prof = 0.6 * p["D"] if p["kind"] == "cajon" else 0.08 * p["D"]
        m = ((co_[:, 0] >= p["x0"]) & (co_[:, 0] <= p["x1"]) & (co_[:, 2] >= p["z0"])
             & (co_[:, 2] <= p["z1"]) & (co_[:, 1] <= p["front"] + prof) & (asign < 0))
        asign[m] = k
    for k, (nm, p) in enumerate(MUEBLE["paneles"]):
        g = obj.vertex_groups.new(name=nm)
        idx = np.nonzero(asign == k)[0].tolist()
        if idx:
            g.add(idx, 1.0, "REPLACE")
    gb.add(np.nonzero(asign < 0)[0].tolist(), 1.0, "REPLACE")
    INFO["vertices_por_panel"] = {nm: int((asign == k).sum())
                                  for k, (nm, _) in enumerate(MUEBLE["paneles"])}


EXTRAS = []         # huesos agregados por el usuario: (nombre_corto, indice_en_cadena)


def _g2b(p):
    """glTF (Y arriba) -> Blender (Z arriba)."""
    return Vector((float(p[0]), -float(p[2]), float(p[1])))


def apply_bone_edits(bones, ed):
    """mover: {hueso: [x,y,z]} nueva posicion de la articulacion (cabeza).
    extra: [{nombre, padre, head, tail}] huesos nuevos (colas, alas, pelo).
    borrar: [hueso] (solo extras). Coordenadas en glTF (las del visor)."""
    clean = lambda n: n.replace(":", "").replace(".", "")
    by = {clean(n): i for i, (n, *_r) in enumerate(bones)}
    bones = [list(b) for b in bones]
    movidos = 0
    for nm, pos in (ed.get("mover") or {}).items():
        i = by.get(clean(nm))
        if i is None:
            continue
        old = bones[i][1].copy()
        new = _g2b(pos)
        bones[i][1] = new
        for b in bones:                       # la cola del padre sigue a la articulacion
            if (b[2] - old).length < 1e-4:
                b[2] = new.copy()
        if (bones[i][2] - bones[i][1]).length < 0.01 * H:
            bones[i][2] = bones[i][1] + Vector((0, 0, 0.05 * H))
        movidos += 1
    pref = "mixamorig:" if args.rig in ("humanoide", "cabeza") else ""
    names = {clean(b[0]): b[0] for b in bones}
    nuevos = 0
    for k, e in enumerate(ed.get("extra") or []):
        corto = "Extra_" + "".join(ch for ch in str(e.get("nombre", k)) if ch.isalnum() or ch == "_")[:20]
        p_ = str(e.get("padre", ""))
        padre = names.get(clean(p_)) or names.get(clean(pref + p_)) or names.get(clean(pref + "Extra_" + p_))
        if padre is None:
            padre = bones[0][0]
        nm = pref + corto
        hd, tl = _g2b(e["head"]), _g2b(e["tail"])
        if (tl - hd).length < 1e-4:
            continue
        bones.append([nm, hd, tl, padre])
        names[clean(nm)] = nm
        EXTRAS.append((corto, int(e.get("orden", 0))))
        nuevos += 1
    INFO["edicion_huesos"] = {"movidos": movidos, "extra": nuevos}
    log("editor: articulaciones movidas", movidos, "huesos nuevos", nuevos)
    return [tuple(b) for b in bones]


def extra_motion(anim, t):
    """Movimiento secundario de los huesos extra (colas, alas, orejas):
    vaiven con retraso creciente a lo largo de la cadena."""
    amp = {"Correr": 0.35, "Saltar": 0.4, "Bailar": 0.35, "Caminar": 0.22,
           "Avanzar": 0.15, "Flotar": 0.25}.get(anim, 0.1)
    out = {}
    for corto, i in EXTRAS:
        ph = 2 * math.pi * t - 0.7 * (i + 1)
        out[corto] = wrot(corto, ((0, 0, 1), amp * (0.6 + 0.3 * i) * math.sin(ph)),
                          ((1, 0, 0), 0.4 * amp * math.sin(ph * 2 + 1)))
    return out


BONES = []          # (nombre, cabeza, cola, padre)


def humanoid_bones(d):
    H, ty = d["H"], d["torso_y"]
    P = "mixamorig:"
    hz = d["hip_z"]
    neck_z = d.get("neck_z", 0.86 * H)
    head_z = min(neck_z + 0.035 * H, 0.93 * H)
    top_sp = max(neck_z - 0.04 * H, hz + 0.06 * H)
    sp = [hz + (top_sp - hz) * f for f in (0.0, 0.33, 0.66, 1.0)]
    B = [
        ("Hips", (0, ty, min(d["crotch"] + 0.01 * H, sp[1] - 0.01 * H)), (0, ty, sp[1]), None),
        ("Spine", (0, ty, sp[1]), (0, ty, sp[2]), "Hips"),
        ("Spine1", (0, ty, sp[2]), (0, ty, sp[3]), "Spine"),
        ("Spine2", (0, ty, sp[3]), (0, ty, neck_z), "Spine1"),
        ("Neck", (0, ty, neck_z), (0, ty, head_z), "Spine2"),
        ("Head", (0, ty, head_z), (0, ty, head_z + 0.8 * (H - head_z)), "Neck"),
        ("HeadTop_End", (0, ty, head_z + 0.8 * (H - head_z)), (0, ty, 1.0 * H), "Head"),
    ]
    for side, name, hand in ((1, "Left", d["hand_l"]), (-1, "Right", d["hand_r"])):
        sh = Vector((side * d["sh_x"], ty, d["sh_z"]))
        clav = Vector((side * 0.03 * H, ty, d["sh_z"] + 0.01 * H))
        wrist = sh + (hand - sh) * 0.86
        elbow = sh + (wrist - sh) * 0.5 + Vector((0, 0.015 * H, 0))
        B += [
            (name + "Shoulder", clav, sh, "Spine2"),
            (name + "Arm", sh, elbow, name + "Shoulder"),
            (name + "ForeArm", elbow, wrist, name + "Arm"),
            (name + "Hand", wrist, hand + (hand - wrist) * 0.3, name + "ForeArm"),
        ]
        fx = d["fx_l"] if side > 0 else d["fx_r"]
        hip = Vector((side * d["leg_x"], ty, hz - 0.035 * H))
        ankle = Vector((fx, d["heel_y"] - 0.04 * H, 0.05 * H))
        knee = (hip + ankle) / 2 + Vector((0, -0.015 * H, 0))
        ball = Vector((fx, d["toe_y"] + 0.06 * H, 0.015 * H))
        toe = Vector((fx, d["toe_y"], 0.01 * H))
        B += [
            (name + "UpLeg", hip, knee, "Hips"),
            (name + "Leg", knee, ankle, name + "UpLeg"),
            (name + "Foot", ankle, ball, name + "Leg"),
            (name + "ToeBase", ball, toe, name + "Foot"),
        ]
    if args.detalle:
        B += detail_bones(d, B)
    return [(P + n, Vector(h), Vector(t), (P + p) if p else None) for n, h, t, p in B]


def detail_bones(d, base):
    """Dedos de las manos (5 x 3 falanges), dedos de los pies, ojos y
    mandibula. Todo se coloca midiendo la malla: largo y ancho real de cada
    mano y pie, y el frente y ancho de la cabeza. Nombres de Mixamo en los
    dedos de la mano (LeftHandIndex1...)."""
    H, ty, co = d["H"], d["torso_y"], d["co"]
    out = []
    byname = {n: (Vector(h), Vector(t)) for n, h, t, _ in base}
    d["dedos"] = {}
    Yv = Vector((0, 1, 0))
    for side, name in ((1, "Left"), (-1, "Right")):
        wrist, tip0 = byname[name + "Hand"]
        u = (tip0 - wrist)
        if u.length < 1e-6:
            continue
        u.normalize()
        w = Yv - u * Yv.dot(u)          # eje a lo ancho de la mano
        if w.length < 0.2:
            w = Vector((0, 0, 1)) - u * u.z
        w.normalize()
        rel = co - np.array(wrist)
        pu = rel @ np.array(u)
        pw = rel @ np.array(w)
        pn = rel @ np.array(u.cross(w))
        m = (pu > -0.005 * H) & (pu < 0.16 * H) & (np.abs(pw) < 0.09 * H) & (np.abs(pn) < 0.07 * H)
        if m.sum() > 30:
            L = float(np.percentile(pu[m], 99))
            w0, w1 = float(np.percentile(pw[m], 3)), float(np.percentile(pw[m], 97))
        else:
            L, w0, w1 = 0.10 * H, -0.035 * H, 0.035 * H
        L = min(max(L, 0.06 * H), 0.15 * H)
        W = min(max(w1 - w0, 0.035 * H), 0.11 * H)
        wc = (w0 + w1) / 2
        knuck = wrist + u * (0.45 * L) + w * wc
        # la mano termina en los nudillos
        for i, (n, h, t, p) in enumerate(base):
            if n == name + "Hand":
                base[i] = (n, h, tuple(knuck), p)
        d["dedos"][name] = (tuple(w), side)
        # indice hacia el frente (-Y), menique hacia atras
        front = -1.0 if w.y > 0 else 1.0
        for fname, off, ln in (("Index", -0.36, 1.0), ("Middle", -0.12, 1.08),
                               ("Ring", 0.12, 1.0), ("Pinky", 0.36, 0.82)):
            a = knuck + w * (front * -off * W * -1)
            prev = name + "Hand"
            for k, seg in enumerate((0.26, 0.17, 0.12), 1):
                b_ = a + u * (seg * L * ln)
                out.append((f"{name}Hand{fname}{k}", tuple(a), tuple(b_), prev))
                prev, a = f"{name}Hand{fname}{k}", b_
        tdir = (u * 0.75 + w * (front * 0.65)).normalized()
        a = wrist + u * (0.12 * L) + w * (wc + front * 0.42 * W)
        prev = name + "Hand"
        for k, seg in enumerate((0.20, 0.15, 0.12), 1):
            b_ = a + tdir * (seg * L)
            out.append((f"{name}HandThumb{k}", tuple(a), tuple(b_), prev))
            prev, a = f"{name}HandThumb{k}", b_

        # Dedos del pie: 5 huesos repartidos en el ancho real del pie
        fx = d["fx_l"] if side > 0 else d["fx_r"]
        fm = (co[:, 2] < 0.05 * H) & (side * co[:, 0] > 0) & (co[:, 1] < d["toe_y"] + 0.09 * H)
        if fm.sum() > 20:
            x0, x1 = float(np.percentile(co[fm, 0], 4)), float(np.percentile(co[fm, 0], 96))
        else:
            x0, x1 = fx - 0.035 * H, fx + 0.035 * H
        if x1 - x0 < 0.03 * H:
            x0, x1 = fx - 0.03 * H, fx + 0.03 * H
        for k in range(5):
            xx = x0 + (x1 - x0) * (k + 0.5) / 5
            out.append((f"{name}Toe{k + 1}", (xx, d["toe_y"] + 0.045 * H, 0.014 * H),
                        (xx, d["toe_y"] + 0.004 * H, 0.010 * H), name + "ToeBase"))

    # Cabeza: ojos y mandibula
    head_z = byname["Head"][0].z
    hv = co[co[:, 2] > head_z + 0.01 * H]
    if len(hv) > 50:
        front = float(np.percentile(hv[:, 1], 2))
        hw = float(np.percentile(hv[:, 0], 98) - np.percentile(hv[:, 0], 2))
    else:
        front, hw = ty - 0.07 * H, 0.12 * H
    hh = H - head_z
    ez = head_z + 0.50 * hh
    ex = min(max(0.21 * hw, 0.018 * H), 0.05 * H)
    for side, name in ((1, "Left"), (-1, "Right")):
        out.append((name + "Eye", (side * ex, front + 0.035 * H, ez),
                    (side * ex, front + 0.003 * H, ez), "Head"))
    out.append(("Jaw", (0, (front + ty) / 2, head_z + 0.22 * hh),
                (0, front + 0.012 * H, head_z + 0.06 * hh), "Head"))
    INFO["esqueleto_detallado"] = True
    return out


def quadruped_bones(co, H):
    """Cuadrupedo mirando a -Y: columna, cuello, cabeza, cola y 4 patas."""
    y, z = co[:, 1], co[:, 2]
    y0, y1 = float(y.min()), float(y.max())     # y0 = frente (cabeza)
    L = y1 - y0
    body = co[z > 0.45 * H]
    bz = float(np.median(body[:, 2])) if len(body) else 0.65 * H
    xs = float(np.percentile(np.abs(co[z < 0.3 * H][:, 0]), 70)) if (z < 0.3 * H).any() else 0.1 * L
    B = []
    chain = [y1 - 0.18 * L, y1 - 0.35 * L, y1 - 0.55 * L, y0 + 0.28 * L]
    names = ["Hips", "Spine", "Spine1", "Spine2"]
    prev = None
    for i, n in enumerate(names):
        a = Vector((0, chain[i], bz))
        b = Vector((0, chain[i + 1] if i + 1 < len(chain) else y0 + 0.2 * L, bz))
        B.append((n, a, b, prev))
        prev = n
    head = co[y < y0 + 0.15 * L]
    hz = float(head[:, 2].mean()) if len(head) else 0.85 * H
    B.append(("Neck", Vector((0, y0 + 0.2 * L, bz)), Vector((0, y0 + 0.1 * L, hz)), "Spine2"))
    B.append(("Head", Vector((0, y0 + 0.1 * L, hz)), Vector((0, y0, hz)), "Neck"))
    B.append(("Tail", Vector((0, y1 - 0.08 * L, bz)), Vector((0, y1, bz - 0.1 * H)), "Hips"))
    for side, sn in ((1, "Left"), (-1, "Right")):
        for fy, fn, par in ((y0 + 0.25 * L, "Front", "Spine2"), (y1 - 0.2 * L, "Back", "Hips")):
            top = Vector((side * xs, fy, bz - 0.05 * H))
            mid = Vector((side * xs, fy, 0.3 * H))
            bot = Vector((side * xs, fy, 0.02 * H))
            B.append((f"{sn}{fn}Leg", top, mid, par))
            B.append((f"{sn}{fn}Shin", mid, bot, f"{sn}{fn}Leg"))
    return B


# ------------------------------------------------------------ armature
arm = None
if args.rig != "ninguno":
    if args.rig == "humanoide":
        D = detect_humanoid(co, H)
        D["co"] = co
        BONES = humanoid_bones(D)
        INFO["proporciones"] = {k: (v if isinstance(v, bool) else round(v, 3) if isinstance(v, float) else list(map(lambda q: round(q, 3), v)))
                                for k, v in D.items() if k not in ("co", "dedos")}
    elif args.rig == "cabeza":
        BONES = head_bones(co, H)
    elif args.rig == "objeto":
        BONES = object_bones(co, H)
    elif args.rig == "vehiculo":
        BONES = vehicle_bones(co, H)
    elif args.rig == "mueble":
        BONES = furniture_bones(co, H)
    else:
        BONES = quadruped_bones(co, H)

    # ---- ediciones del usuario (editor de esqueleto en el visor)
    if args.huesos and os.path.exists(args.huesos):
        try:
            BONES = apply_bone_edits(BONES, json.load(open(args.huesos)))
        except Exception as e:
            INFO["avisos"].append(f"edicion de huesos: {e}")
    adata = bpy.data.armatures.new("Esqueleto")
    arm = bpy.data.objects.new("Esqueleto", adata)
    scene.collection.objects.link(arm)
    activate(arm)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for n, hd, tl, par in BONES:
        b = adata.edit_bones.new(n)
        b.head, b.tail = hd, tl
        if (b.tail - b.head).length < 1e-4:
            b.tail = b.head + Vector((0, 0, 0.01))
        b.roll = 0
        eb[n] = b
    for n, hd, tl, par in BONES:
        if par:
            eb[n].parent = eb[par]
            eb[n].use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")
    adata.display_type = "STICK"
    arm.show_in_front = True
    INFO["huesos"] = len(BONES)
    log("esqueleto", args.rig, len(BONES), "huesos")

    # -------------------------------------------------------- pesos
    def skin_by_distance(target):
        """Respaldo: pesos suaves por distancia a cada segmento de hueso."""
        P = verts_np(target)
        names, dist = [], []
        for b in arm.data.bones:
            if not b.use_deform or b.name.endswith("_End"):
                continue
            a = np.array(b.head_local)
            c = np.array(b.tail_local)
            ab = c - a
            t = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-9), 0, 1)
            q = a + t[:, None] * ab
            names.append(b.name)
            dist.append(np.linalg.norm(P - q, axis=1))
        dist = np.stack(dist, 1)
        w = np.exp(-(dist / (0.035 * H)) ** 2)
        w[dist > dist.min(1, keepdims=True) * 1.8 + 0.02 * H] = 0
        w /= w.sum(1, keepdims=True) + 1e-12
        for j, n in enumerate(names):
            vg = target.vertex_groups.get(n) or target.vertex_groups.new(name=n)
            idx = np.nonzero(w[:, j] > 0.01)[0]
            for i in idx:
                vg.add([int(i)], float(w[i, j]), "REPLACE")

    # Copia cerrada para calcular los pesos con calor. Si el calor falla
    # (malla con capas, alas, tunicas...) se reintenta con un proxy mas
    # grueso y mas cerrado antes de caer al respaldo por distancia.
    def make_proxy(div, max_f):
        px = obj.copy()
        px.data = obj.data.copy()
        px.name = "Proxy"
        scene.collection.objects.link(px)
        px.data.materials.clear()
        px.modifiers.clear()
        px.vertex_groups.clear()
        activate(px)
        rm = px.modifiers.new("Remesh", "REMESH")
        rm.mode = "VOXEL"
        rm.voxel_size = H / div
        try:
            rm.adaptivity = 0.0
        except Exception:
            pass
        bpy.ops.object.modifier_apply(modifier=rm.name)
        if len(px.data.polygons) > max_f:
            dm = px.modifiers.new("Dec", "DECIMATE")
            dm.ratio = max_f / len(px.data.polygons)
            bpy.ops.object.modifier_apply(modifier=dm.name)
        return px

    def fill_from_neighbors(px):
        """Vertices que el calor dejo sin hueso copian al vecino con peso
        mas cercano (en la copia cerrada, asi no se cuela entre miembros)."""
        from mathutils.kdtree import KDTree
        me_ = px.data
        good = [v.index for v in me_.vertices if v.groups]
        bad = [v.index for v in me_.vertices if not v.groups]
        if not good or not bad:
            return 0
        kd = KDTree(len(good))
        for i in good:
            kd.insert(me_.vertices[i].co, i)
        kd.balance()
        names = {g.index: g.name for g in px.vertex_groups}
        fixes = []
        for i in bad:
            _, j, _ = kd.find(me_.vertices[i].co)
            fixes.append((i, [(names[e.group], e.weight) for e in me_.vertices[j].groups]))
        for i, ws in fixes:
            for n, w in ws:
                px.vertex_groups[n].add([i], w, "REPLACE")
        return len(bad)

    heat_ok = False
    proxy = None
    mejor = None          # (vacios, intento, div, max_f)
    for intento, (div, max_f) in enumerate(((150.0, 70000), (100.0, 40000), (65.0, 20000)), 1):
        if proxy is not None:
            bpy.data.objects.remove(proxy, do_unlink=True)
        proxy = make_proxy(div, max_f)
        log("proxy de pesos", len(proxy.data.polygons), "caras (intento", intento, ")")
        activate(arm, [proxy])
        try:
            bpy.ops.object.parent_set(type="ARMATURE_AUTO")
        except Exception as e:
            log("calor fallo:", e)
            continue
        nv = len(proxy.data.vertices)
        empty = sum(1 for v in proxy.data.vertices if not v.groups)
        if len(proxy.vertex_groups) and empty <= 0.02 * nv:
            heat_ok = True
            INFO["pesos_intento"] = intento
            break
        log("calor dejo", empty, "vertices sin peso de", nv)
        if len(proxy.vertex_groups) and empty <= 0.40 * nv:
            fr = empty / nv
            # el intento mas fino gana si deja menos de 10 % sin peso
            if mejor is None or (mejor[0] > 0.10 and fr < mejor[0]):
                mejor = (fr, intento, div, max_f)
    if not heat_ok and mejor is not None:
        # Calor parcial (capas, tiras, garras): se rehace el mejor intento y
        # los huecos se rellenan con los vecinos. Mucho mejor que la distancia.
        _, intento, div, max_f = mejor
        bpy.data.objects.remove(proxy, do_unlink=True)
        proxy = make_proxy(div, max_f)
        activate(arm, [proxy])
        try:
            bpy.ops.object.parent_set(type="ARMATURE_AUTO")
            n_ = fill_from_neighbors(proxy)
            heat_ok = True
            INFO["pesos_intento"] = intento
            INFO["pesos_rellenados"] = n_
            log("calor parcial: rellenados", n_, "vertices con sus vecinos")
        except Exception as e:
            log("calor parcial fallo:", e)
    if not heat_ok:
        INFO["avisos"].append("pesos por calor fallaron 3 veces; se uso respaldo por distancia")
        for g in list(proxy.vertex_groups):
            proxy.vertex_groups.remove(g)
        skin_by_distance(proxy)
    INFO["pesos"] = "calor (Blender)" if heat_ok else "distancia"
    log("pesos:", INFO["pesos"])

    # Transferir a la malla real
    for b in arm.data.bones:
        if b.use_deform and not obj.vertex_groups.get(b.name):
            obj.vertex_groups.new(name=b.name)
    activate(obj)
    dt = obj.modifiers.new("Pesos", "DATA_TRANSFER")
    dt.object = proxy
    dt.use_vert_data = True
    dt.data_types_verts = {"VGROUP_WEIGHTS"}
    dt.vert_mapping = "POLYINTERP_NEAREST"
    dt.layers_vgroup_select_src = "ALL"
    dt.layers_vgroup_select_dst = "NAME"
    bpy.ops.object.modifier_apply(modifier=dt.name)
    bpy.data.objects.remove(proxy, do_unlink=True)

    # Normalizar y limitar a 4 huesos por vertice (Unity/Unreal/Godot)
    activate(obj)
    bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
    try:
        bpy.ops.object.vertex_group_smooth(group_select_mode="ALL", factor=0.5, repeat=2)
    except Exception:
        pass
    bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
    bpy.ops.object.vertex_group_normalize_all(group_select_mode="ALL", lock_active=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    for g in list(obj.vertex_groups):
        if arm.data.bones.get(g.name) is None:
            obj.vertex_groups.remove(g)

    # Reparar vertices que quedaron sin peso (se quedarian quietos y
    # estirarian la malla): copian los pesos del vertice con peso mas
    # cercano. Asi el 100 % de la malla sigue al esqueleto.
    from mathutils.kdtree import KDTree
    me = obj.data
    gi2name = {g.index: g.name for g in obj.vertex_groups}
    weighted = [v.index for v in me.vertices
                if any(e.weight > 1e-4 for e in v.groups)]
    nv = len(me.vertices)
    sin_peso = nv - len(weighted)
    if 0 < sin_peso < nv and weighted:
        kd = KDTree(len(weighted))
        for i in weighted:
            kd.insert(me.vertices[i].co, i)
        kd.balance()
        wset = set(weighted)
        fixes = []
        for v in me.vertices:
            if v.index in wset:
                continue
            _, j, _ = kd.find(v.co)
            fixes.append((v.index, [(gi2name[e.group], e.weight)
                                    for e in me.vertices[j].groups]))
        for i, ws in fixes:
            for n, w in ws:
                obj.vertex_groups[n].add([i], w, "REPLACE")
    INFO["vertices_sin_peso_reparados"] = int(sin_peso)

    # Fisica de telas: tunicas, capas, alas y faldas que quedan lejos del
    # hueso de la pierna o del brazo no deben seguir al miembro (se rasgan).
    # Se reparte su peso hacia la cadera / espalda segun la distancia, como
    # una tela que cuelga. Mejora mucho a personajes con ropa suelta.
    INFO["vertices_tela"] = cloth_weights() if args.rig == "humanoide" else 0
    try:
        INFO["huesos_tela"] = cloth_chains() if INFO["vertices_tela"] else 0
        INFO["huesos"] = INFO.get("huesos", 0) + INFO["huesos_tela"]
    except Exception as e:
        INFO["avisos"].append(f"huesos de tela: {e}")
        bpy.ops.object.mode_set(mode="OBJECT")
    if INFO["vertices_tela"]:
        # tras mover peso a la cadera: suavizar, maximo 4 huesos y sumar 1
        # (si no, el exportador corta pesos y la tela se rasga en triangulos)
        activate(obj)
        bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
        try:
            bpy.ops.object.vertex_group_smooth(group_select_mode="ALL", factor=0.6, repeat=3)
        except Exception:
            pass
        bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
        bpy.ops.object.vertex_group_normalize_all(group_select_mode="ALL", lock_active=False)
        bpy.ops.object.mode_set(mode="OBJECT")

    # Ojos y mandibula: solo su zona real. El calor les daba media cabeza;
    # lo que queda fuera vuelve al hueso de la cabeza.
    def limit_group(gname, keep_fn, to="mixamorig:Head"):
        g = obj.vertex_groups.get(gname)
        gh = obj.vertex_groups.get(to)
        if g is None or gh is None:
            return 0
        moved = []
        for v in me.vertices:
            for e in v.groups:
                if e.group == g.index and e.weight > 0:
                    k_ = keep_fn(v.co)
                    if k_ < 1.0:
                        moved.append((v.index, e.weight, k_))
        for i, w_, k_ in moved:
            if k_ <= 0:
                g.remove([i])
            else:
                g.add([i], w_ * k_, "REPLACE")
            gh.add([i], w_ * (1 - k_), "ADD")
        return len(moved)

    if args.rig in ("humanoide", "cabeza") and (args.detalle or args.rig == "cabeza"):
        for side in ("Left", "Right"):
            b = arm.data.bones.get(f"mixamorig:{side}Eye")
            if b is not None:
                c = b.tail_local.copy()
                r = 0.016 * H
                limit_group(b.name, lambda p, c=c, r=r: max(0.0, min(1.0, 2.0 - (p - c).length / r)))
        b = arm.data.bones.get("mixamorig:Jaw")
        if b is not None:
            jz, jy, tipz = b.head_local.z, b.head_local.y, b.tail_local.z

            def jaw_keep(p):
                if p.z > jz or p.y > jy + 0.01 * H:
                    return 0.0
                # suave: 1 en la barbilla, 0 al llegar a la altura del eje
                return max(0.0, min(1.0, (jz - p.z) / max(jz - tipz, 1e-4)))
            limit_group(b.name, jaw_keep)
    # Cobertura por hueso (para ver de un vistazo si un hueso no mueve nada)
    gi2name = {g.index: g.name for g in obj.vertex_groups}
    cnt = {g.name: 0 for g in obj.vertex_groups}
    for v in me.vertices:
        for e in v.groups:
            if e.weight > 0.05:
                cnt[gi2name[e.group]] += 1
    INFO["vertices_por_hueso"] = cnt
    _fino = ("Thumb", "Index", "Middle", "Ring", "Pinky", "Toe", "Eye", "Jaw", "Tela", "Neck", "Raiz",
             "Extra_")
    vacios = [n for n, c in cnt.items() if c == 0 and not n.endswith("_End")
              and not any(x in n for x in _fino)]
    INFO["huesos_finos_sin_zona"] = sum(1 for n, c in cnt.items()
                                        if c == 0 and any(x in n for x in _fino))
    if vacios:
        INFO["avisos"].append("huesos sin zona: " + ", ".join(vacios))
    log("pesos reparados:", sin_peso, "vertices; huesos vacios:", len(vacios))

    if args.rig == "vehiculo":
        vehicle_weights()
        INFO["pesos"] = "rigidos (vehiculo)"
    elif args.rig == "mueble":
        furniture_weights()
        INFO["pesos"] = "rigidos (mueble)"
    obj.parent = arm
    am = obj.modifiers.new("Armature", "ARMATURE")
    am.object = arm


# ------------------------------------------------------------ animaciones
ANIMS = {}


def pb(name):
    if args.rig in ("humanoide", "cabeza"):
        name = "mixamorig:" + name
    return arm.pose.bones.get(name)


def wrot(name, *rots):
    """Rotacion definida en ejes del mundo -> cuaternion local del hueso."""
    b = pb(name)
    if b is None:
        return None
    M = b.bone.matrix_local.to_quaternion()
    R = Quaternion()
    for axis, ang in rots:
        R = Quaternion(Vector(axis), ang) @ R
    return M.inverted() @ R @ M


# amplitud del balanceo de la tela y ciclos por animacion
SWAY = {"Caminar": (0.16, 1), "Correr": (0.32, 1), "Bailar": (0.28, 2), "Saltar": (0.35, 1),
        "Saludar": (0.05, 1), "Reposo": (0.03, 1), "Manos": (0.03, 1), "Hablar": (0.03, 1)}


def cloth_motion(anim, t):
    """Movimiento secundario: cada hueso de tela sigue al cuerpo con retraso
    (inercia) y mas amplitud hacia el borde, como una tela real."""
    amp, cyc = SWAY.get(anim, (0.0, 1))
    if amp <= 0:
        return {}
    out = {}
    X, Y = (1, 0, 0), (0, 1, 0)
    for n, a0, i in TELA:
        short = n.split(":")[-1]
        lag = 0.55 * (i + 1)
        ph = 2 * math.pi * cyc * t - lag
        if anim == "Saltar":
            # al subir la tela se queda abajo, al caer se levanta
            sw = amp * math.sin(2 * math.pi * t - 0.6 - 0.3 * i)
            # rota hacia afuera segun su lado
            out[short] = wrot(short, (X, -sw * math.cos(a0)), (Y, sw * math.sin(a0)))
            continue
        # vaiven adelante-atras (piernas) y un poco de lado a lado
        fb = amp * (0.6 + 0.4 * i) * math.sin(ph)
        lr = 0.4 * amp * (0.6 + 0.4 * i) * math.sin(ph * 0.5 + 1.0)
        out[short] = wrot(short, (X, fb), (Y, lr))
    return out


def build_action(name, frames, pose_fn, step=2):
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm.animation_data_create()
    arm.animation_data.action = act
    for b in arm.pose.bones:
        b.rotation_mode = "QUATERNION"
    keyed = set()
    movidos = set()
    for f in list(range(0, frames, step)) + [frames]:
        t = (f % frames) / frames
        scene.frame_set(f)
        for b in arm.pose.bones:
            b.rotation_quaternion = Quaternion()
            b.location = Vector()
        pose = pose_fn(t)
        if TELA:
            pose.update(cloth_motion(name, t))
        if EXTRAS:
            pose.update(extra_motion(name, t))
        for bname, val in pose.items():
            b = pb(bname)
            if b is None or val is None:
                continue
            if isinstance(val, Quaternion):
                b.rotation_quaternion = val
            else:
                b.location = val
                movidos.add(b.name)
        for b in arm.pose.bones:
            b.keyframe_insert("rotation_quaternion", frame=f)
            if b.parent is None or b.name in movidos:
                b.keyframe_insert("location", frame=f)
            keyed.add(b.name)
    for fc in fcurves_of(act):
        try:
            fc.modifiers.new("CYCLES")
        except Exception:
            pass
    try:
        act.frame_range = (0, frames)
    except Exception:
        pass
    ANIMS[name] = (act, frames)
    return act


def humanoid_anims(D):
    S = math.sin
    pi = math.pi
    hl, hr = D["hand_l"], D["hand_r"]
    shl = Vector((D["sh_x"], 0, D["sh_z"]))
    # angulo actual del brazo respecto a la horizontal -> bajar a ~ -72 grados
    elev_l = math.atan2(hl.z - shl.z, max(hl.x - shl.x, 1e-3))
    elev_r = math.atan2(hr.z - shl.z, max(-hr.x - shl.x, 1e-3))
    down_l = max(0.0, elev_l + math.radians(72))
    down_r = max(0.0, elev_r + math.radians(72))
    X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
    Hh = D["H"]

    def arms(swing_l=0, swing_r=0, fore=0.15, extra_l=0, extra_r=0):
        return {
            "LeftArm": wrot("LeftArm", (Y, down_l - extra_l), (X, swing_l)),
            "RightArm": wrot("RightArm", (Y, -(down_r - extra_r)), (X, swing_r)),
            "LeftForeArm": wrot("LeftForeArm", (X, -fore)),
            "RightForeArm": wrot("RightForeArm", (X, -fore)),
        }

    def legs(a_l, a_r, k_l, k_r, foot=0.0):
        return {
            "LeftUpLeg": wrot("LeftUpLeg", (X, a_l)),
            "RightUpLeg": wrot("RightUpLeg", (X, a_r)),
            "LeftLeg": wrot("LeftLeg", (X, k_l)),
            "RightLeg": wrot("RightLeg", (X, k_r)),
            "LeftFoot": wrot("LeftFoot", (X, -0.5 * k_l + foot)),
            "RightFoot": wrot("RightFoot", (X, -0.5 * k_r + foot)),
        }

    def hips_up(dz):
        # Hips apunta hacia +Z: su eje local Y es el Z del mundo
        return Vector((0, dz, 0))

    def tpose(t):
        return {}

    def idle(t):
        b = S(2 * pi * t)
        p = arms(0.03 * b, -0.03 * b, 0.12)
        p["Spine1"] = wrot("Spine1", (X, -0.02 * b))
        p["Head"] = wrot("Head", (Z, 0.05 * S(2 * pi * t + 1)))
        p["Hips"] = hips_up(0.004 * Hh * b)
        return p

    def walk(t):
        a = 2 * pi * t
        p = legs(-0.42 * S(a), 0.42 * S(a),
                 0.75 * max(0, S(a + 1.6)), 0.75 * max(0, S(a + 1.6 + pi)))
        p.update(arms(0.35 * S(a), -0.35 * S(a), 0.25))
        p["Hips"] = hips_up(0.012 * Hh * abs(S(2 * a)) - 0.01 * Hh)
        p["Spine"] = wrot("Spine", (Z, 0.08 * S(a)))
        p["Spine2"] = wrot("Spine2", (Z, -0.1 * S(a)))
        return p

    def run(t):
        a = 2 * pi * t
        p = legs(-0.75 * S(a), 0.75 * S(a),
                 1.3 * max(0, S(a + 1.4)), 1.3 * max(0, S(a + 1.4 + pi)))
        p.update(arms(0.6 * S(a), -0.6 * S(a), 1.3))
        p["Hips"] = hips_up(0.03 * Hh * abs(S(2 * a)) - 0.03 * Hh)
        p["Spine"] = wrot("Spine", (X, -0.18), (Z, 0.1 * S(a)))
        return p

    def wave(t):
        a = 2 * pi * t
        p = arms(0, 0, 0.12, extra_r=down_r + math.radians(65))
        p["RightForeArm"] = wrot("RightForeArm", (Y, -0.5 - 0.45 * S(2 * a)))
        p["Head"] = wrot("Head", (Z, -0.15), (Y, -0.05))
        p["Spine1"] = wrot("Spine1", (Y, 0.04 * S(a)))
        return p

    def jump(t):
        # 0-0.3 agacharse, 0.3-0.7 aire, 0.7-1 caer y recuperar
        if t < 0.3:
            c = math.sin(t / 0.3 * pi / 2)
            up = -0.12 * Hh * c
            k = 1.2 * c
            ar = 0.0
        elif t < 0.7:
            u = (t - 0.3) / 0.4
            up = 0.35 * Hh * math.sin(u * pi)
            k = 0.4 * (1 - math.sin(u * pi))
            ar = math.radians(140) * math.sin(u * pi)
        else:
            u = (t - 0.7) / 0.3
            c = math.sin((1 - u) * pi)
            up = -0.1 * Hh * c
            k = 1.0 * c
            ar = 0
        p = legs(-k * 0.6, -k * 0.6, k, k, foot=0.0)
        p.update(arms(0, 0, 0.2, extra_l=ar, extra_r=ar))
        p["Hips"] = hips_up(up)
        p["Spine"] = wrot("Spine", (X, -0.25 * k / 1.2))
        return p

    def dance(t):
        a = 2 * pi * t
        p = legs(-0.2 * max(0, S(a)), -0.2 * max(0, -S(a)),
                 0.5 * max(0, S(a)), 0.5 * max(0, -S(a)))
        p.update(arms(0.3 * S(2 * a), -0.3 * S(2 * a), 1.2,
                      extra_l=0.9 + 0.4 * S(a), extra_r=0.9 - 0.4 * S(a)))
        p["Hips"] = hips_up(0.02 * Hh * S(2 * a) - 0.02 * Hh)
        p["Spine"] = wrot("Spine", (Y, 0.12 * S(a)), (Z, 0.15 * S(a)))
        p["Head"] = wrot("Head", (Y, -0.1 * S(2 * a)))
        return p

    FING = ("Thumb", "Index", "Middle", "Ring", "Pinky")

    def fingers(curl_l, curl_r=None):
        """Cierra los dedos (0 = abiertos, 1 = puno)."""
        out = {}
        curl_r = curl_l if curl_r is None else curl_r
        for name, c in (("Left", curl_l), ("Right", curl_r)):
            info = D.get("dedos", {}).get(name)
            if not info:
                continue
            axis, side = info
            for fn in FING:
                amp = 0.55 if fn == "Thumb" else 1.25
                for k in (1, 2, 3):
                    out[f"{name}Hand{fn}{k}"] = wrot(f"{name}Hand{fn}{k}", (axis, side * amp * c))
        return out

    HAS_F = bool(D.get("dedos"))
    if HAS_F:
        # dedos relajados en todas las animaciones y puno al correr
        _idle, _walk, _run, _wave, _dance = idle, walk, run, wave, dance
        idle = lambda t: {**_idle(t), **fingers(0.22 + 0.04 * S(2 * pi * t))}
        walk = lambda t: {**_walk(t), **fingers(0.3)}
        run = lambda t: {**_run(t), **fingers(0.85)}
        wave = lambda t: {**_wave(t), **fingers(0.25, 0.03)}
        dance = lambda t: {**_dance(t), **fingers(0.4 + 0.3 * S(4 * pi * t))}

    def hands(t):
        # abrir y cerrar las manos, una desfasada de la otra
        a = 2 * pi * t
        p = arms(0, 0, 0.9, extra_l=0.5, extra_r=0.5)
        p.update(fingers(0.5 - 0.5 * math.cos(a), 0.5 + 0.5 * math.cos(a)))
        return p

    def talk(t):
        a = 2 * pi * t
        p = idle(t)
        p["Jaw"] = wrot("Jaw", (X, 0.16 * abs(S(3 * a)) + 0.05 * abs(S(7 * a))))
        p["Head"] = wrot("Head", (X, 0.06 * S(2 * a)), (Z, 0.08 * S(a)))
        return p

    build_action("Reposo", 72, idle, step=3)
    if HAS_F:
        build_action("Manos", 48, hands)
    if pb("Jaw") is not None:
        build_action("Hablar", 48, talk)
    build_action("Caminar", 32, walk)
    build_action("Correr", 20, run)
    build_action("Saludar", 48, wave)
    build_action("Saltar", 40, jump)
    build_action("Bailar", 48, dance)
    build_action("Pose_T", 2, tpose, step=1)


def quadruped_anims():
    S = math.sin
    pi = math.pi
    X, Z = (1, 0, 0), (0, 0, 1)

    def walk(t, amp=0.35, k=0.5):
        a = 2 * pi * t
        ph = {"LeftFront": 0, "RightBack": 0.25 * 2 * pi,
              "RightFront": pi, "LeftBack": pi + 0.25 * 2 * pi}
        p = {}
        for n, o in ph.items():
            p[n + "Leg"] = wrot(n + "Leg", (X, amp * S(a + o)))
            p[n + "Shin"] = wrot(n + "Shin", (X, -k * max(0, S(a + o + 1.5))))
        p["Tail"] = wrot("Tail", (Z, 0.3 * S(a)))
        p["Head"] = wrot("Head", (X, 0.06 * S(2 * a)))
        return p

    def idle(t):
        a = 2 * pi * t
        return {"Tail": wrot("Tail", (Z, 0.25 * S(a))),
                "Neck": wrot("Neck", (X, 0.05 * S(a))),
                "Head": wrot("Head", (Z, 0.1 * S(a + 1)))}

    build_action("Reposo", 72, idle, step=3)
    build_action("Caminar", 36, walk)
    build_action("Correr", 20, lambda t: walk(t, 0.7, 1.0))


def head_anims():
    S, pi = math.sin, math.pi
    X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)

    def eyes(yaw, pitch=0.0):
        return {"LeftEye": wrot("LeftEye", (Z, yaw), (X, pitch)),
                "RightEye": wrot("RightEye", (Z, yaw), (X, pitch))}

    def idle(t):
        a = 2 * pi * t
        p = {"Neck": wrot("Neck", (X, 0.02 * S(a))), "Head": wrot("Head", (Z, 0.04 * S(a + 1)))}
        p.update(eyes(0.12 * S(2 * a), 0.03 * S(a)))
        return p

    def talk(t):
        a = 2 * pi * t
        p = idle(t)
        p["Jaw"] = wrot("Jaw", (X, 0.22 * abs(S(3 * a)) + 0.06 * abs(S(7 * a))))
        p["Head"] = wrot("Head", (X, 0.05 * S(2 * a)), (Z, 0.06 * S(a)))
        return p

    def look(t):
        a = 2 * pi * t
        yaw = 0.45 * S(a)
        p = {"Head": wrot("Head", (Z, 0.35 * S(a - 0.4))), "Neck": wrot("Neck", (Z, 0.1 * S(a - 0.6)))}
        p.update(eyes(yaw, 0.1 * S(2 * a)))
        return p

    def nod(t):
        a = 2 * pi * t
        return {"Head": wrot("Head", (X, 0.22 * S(2 * a))), "Neck": wrot("Neck", (X, 0.06 * S(2 * a)))}

    def shake(t):
        a = 2 * pi * t
        return {"Head": wrot("Head", (Z, 0.35 * S(3 * a))), "Neck": wrot("Neck", (Z, 0.08 * S(3 * a)))}

    def surprise(t):
        k = math.sin(min(1.0, t * 3) * pi / 2) * (1 - max(0.0, t - 0.7) / 0.3)
        p = {"Jaw": wrot("Jaw", (X, 0.35 * k)), "Head": wrot("Head", (X, -0.18 * k))}
        p.update(eyes(0.0, -0.15 * k))
        return p

    build_action("Reposo", 72, idle, step=3)
    build_action("Hablar", 48, talk)
    build_action("Mirar", 72, look, step=3)
    build_action("Asentir", 36, nod)
    build_action("Negar", 36, shake)
    build_action("Sorpresa", 40, surprise)


def vehicle_anims():
    S, pi = math.sin, math.pi
    si = VEH["si"]
    eje = [0, 0, 0]
    eje[si] = 1
    eje = tuple(eje)
    largo = [0, 0, 0]
    largo[VEH["li"]] = 1
    largo = tuple(largo)
    Z = (0, 0, 1)
    ruedas = list(VEH["ruedas"])

    def spin(t, vueltas):
        return {n: wrot(n, (eje, -2 * pi * vueltas * t)) for n in ruedas}

    def idle(t):
        a = 2 * pi * t
        return {"Carroceria": wrot("Carroceria", (largo, 0.004 * S(a)), (eje, 0.004 * S(2 * a)))}

    def drive(t):
        p = spin(t, 2)
        a = 2 * pi * t
        p["Carroceria"] = wrot("Carroceria", (eje, 0.012 * S(4 * a)))
        return p

    def turn(t):
        a = 2 * pi * t
        ang = 0.45 * S(a)
        p = spin(t, 2)
        for n in ("Direccion_DI", "Direccion_DD"):
            p[n] = wrot(n, (Z, ang))
        p["Carroceria"] = wrot("Carroceria", (largo, -0.05 * S(a)))   # se inclina en la curva
        return p

    def suspension(t):
        a = 2 * pi * t
        return {"Carroceria": wrot("Carroceria", (largo, 0.06 * S(a)), (eje, 0.04 * S(2 * a + 1)))}

    def brake(t):
        k = math.sin(min(1.0, t * 2.5) * pi) if t < 0.4 else math.exp(-(t - 0.4) * 6) * math.cos((t - 0.4) * 30)
        p = spin(min(t, 0.4), 1)
        p["Carroceria"] = wrot("Carroceria", (eje, 0.07 * k))      # cabeceo al frenar
        return p

    build_action("Reposo", 72, idle, step=3)
    build_action("Avanzar", 48, drive)
    build_action("Girar", 72, turn, step=3)
    build_action("Suspension", 48, suspension)
    build_action("Frenar", 48, brake)


def furniture_anims():
    pi = math.pi
    pan = MUEBLE.get("paneles", [])

    def amount(t):           # 0 -> abre -> se queda -> cierra
        if t < 0.35:
            u = t / 0.35
        elif t < 0.65:
            u = 1.0
        else:
            u = 1 - (t - 0.65) / 0.35
        return u * u * (3 - 2 * u)

    def pose(t, solo=None):
        k = amount(t)
        p = {}
        for nm, d in pan:
            if solo and not nm.startswith(solo):
                continue
            if d["kind"] == "puerta":
                sgn = -1 if d["hinge"] <= (d["x0"] + d["x1"]) / 2 else 1
                p[nm] = wrot(nm, ((0, 0, 1), sgn * 1.75 * k))     # ~100 grados
            else:
                p[nm] = Vector((0, 0.55 * d["D"] * k, 0))          # el cajon sale
        return p

    build_action("Reposo", 24, lambda t: {}, step=4)
    build_action("Abrir todo", 72, pose, step=2)
    if any(d["kind"] == "puerta" for _, d in pan):
        build_action("Abrir puertas", 72, lambda t: pose(t, "Puerta"), step=2)
    if any(d["kind"] == "cajon" for _, d in pan):
        build_action("Abrir cajones", 72, lambda t: pose(t, "Cajon"), step=2)


def object_anims():
    S, pi = math.sin, math.pi
    X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)

    def up(dz):
        return Vector((0, dz, 0))      # la raiz apunta hacia +Z

    def idle(t):
        a = 2 * pi * t
        return {"Medio": wrot("Medio", (Y, 0.03 * S(a))), "Arriba": wrot("Arriba", (Y, 0.04 * S(a + 0.5)))}

    def float_(t):
        a = 2 * pi * t
        return {"Raiz": up(0.06 * H * (1 + S(a))), "Base": wrot("Base", (Z, 0.15 * S(a)))}

    def spin(t):
        return {"Raiz": wrot("Raiz", (Z, 2 * pi * t))}

    def bounce(t):
        a = 2 * pi * t
        h = abs(S(a))
        return {"Raiz": up(0.25 * H * h),
                "Medio": wrot("Medio", (X, 0.18 * (1 - h))),
                "Arriba": wrot("Arriba", (X, -0.22 * (1 - h)))}

    def dance(t):
        a = 2 * pi * t
        return {"Base": wrot("Base", (Y, 0.12 * S(2 * a))), "Medio": wrot("Medio", (Y, -0.2 * S(2 * a))),
                "Arriba": wrot("Arriba", (Y, 0.25 * S(2 * a + 0.6))), "Raiz": up(0.03 * H * abs(S(2 * a)))}

    def wave(t):
        a = 2 * pi * t
        return {"Medio": wrot("Medio", (X, 0.15 * S(a))), "Arriba": wrot("Arriba", (X, 0.25 * S(a - 0.8)))}

    build_action("Reposo", 72, idle, step=3)
    build_action("Flotar", 72, float_, step=3)
    build_action("Girar", 96, spin, step=4)
    build_action("Rebotar", 36, bounce)
    build_action("Bailar", 48, dance)
    build_action("Saludar", 48, wave)


if arm is not None:
    activate(arm)
    bpy.ops.object.mode_set(mode="POSE")
    if args.rig == "humanoide":
        humanoid_anims(D)
    elif args.rig == "cabeza":
        head_anims()
    elif args.rig == "objeto":
        object_anims()
    elif args.rig == "vehiculo":
        vehicle_anims()
    elif args.rig == "mueble":
        furniture_anims()
    else:
        quadruped_anims()
    bpy.ops.object.mode_set(mode="OBJECT")
    INFO["animaciones"] = list(ANIMS)
    log("animaciones:", ", ".join(ANIMS))


def set_anim(name):
    if arm is None or not ANIMS:
        return 72
    if name not in ANIMS:
        name = "Caminar" if "Caminar" in ANIMS else next(iter(ANIMS))
    act, n = ANIMS[name]
    arm.animation_data.action = act
    # Blender 4.4+: asignar la ranura de la accion
    try:
        if act.slots and arm.animation_data.action_slot is None:
            arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    return n


# ------------------------------------------------------------ calidad de UV
def uv_quality():
    """Revision rapida de las UV (lo que piden los modeladores): cuanto de la
    textura se aprovecha, triangulos invertidos y estiramiento."""
    me = obj.data
    if not me.uv_layers:
        return None
    me.calc_loop_triangles()
    nt = len(me.loop_triangles)
    if nt == 0:
        return None
    uvd = np.zeros(len(me.loops) * 2, dtype=np.float32)
    me.uv_layers.active.data.foreach_get("uv", uvd)
    uvd = uvd.reshape(-1, 2)
    li = np.zeros(nt * 3, dtype=np.int64)
    me.loop_triangles.foreach_get("loops", li)
    vi = np.zeros(nt * 3, dtype=np.int64)
    me.loop_triangles.foreach_get("vertices", vi)
    co_ = np.zeros(len(me.vertices) * 3, dtype=np.float32)
    me.vertices.foreach_get("co", co_)
    co_ = co_.reshape(-1, 3)
    u = uvd[li].reshape(nt, 3, 2)
    p = co_[vi].reshape(nt, 3, 3)
    a_uv = 0.5 * ((u[:, 1, 0] - u[:, 0, 0]) * (u[:, 2, 1] - u[:, 0, 1])
                  - (u[:, 2, 0] - u[:, 0, 0]) * (u[:, 1, 1] - u[:, 0, 1]))
    a3 = 0.5 * np.linalg.norm(np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]), axis=1)
    invertidos = float((a_uv < 0).mean())
    ok = a3 > 1e-12
    r = np.abs(a_uv[ok]) / a3[ok]
    r = r / max(np.median(r), 1e-12)
    estir = float(np.mean((r < 0.33) | (r > 3.0)))
    # cobertura: rasteriza los centros de triangulo en una rejilla de 256
    g = np.zeros((256, 256), dtype=np.int32)
    cx = np.clip((u.mean(1)[:, 0] % 1) * 255, 0, 255).astype(int)
    cy = np.clip((u.mean(1)[:, 1] % 1) * 255, 0, 255).astype(int)
    np.add.at(g, (cy, cx), 1)
    cobertura = float(np.abs(a_uv).sum())
    return {"cobertura_pct": round(min(cobertura, 1.0) * 100, 1),
            "invertidos_pct": round(invertidos * 100, 2),
            "estirados_pct": round(estir * 100, 2),
            "nota": "buena" if estir < 0.05 and cobertura > 0.5 else
                    ("aceptable" if estir < 0.15 else "revisar")}


try:
    INFO["uv"] = uv_quality()
    log("UV:", INFO["uv"])
except Exception as e:
    INFO["avisos"].append(f"revision de UV: {e}")


# ------------------------------------------------------------ relieve
def add_relief(strength):
    """Crea un mapa de normales a partir de la textura (luminancia -> altura,
    filtro Sobel) y lo conecta al material: arrugas, costuras y detalles
    se ven con volumen. Se exporta en GLB/FBX/BLEND."""
    done = 0
    for m in obj.data.materials:
        if m is None or not m.use_nodes:
            continue
        nt = m.node_tree
        bs = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bs is None or bs.inputs["Normal"].is_linked:
            continue
        lk = bs.inputs["Base Color"].links
        if not lk or lk[0].from_node.type != "TEX_IMAGE" or lk[0].from_node.image is None:
            continue
        src = lk[0].from_node.image
        w, h = src.size
        if w * h == 0:
            continue
        px = np.empty(w * h * 4, dtype=np.float32)
        src.pixels.foreach_get(px)
        px = px.reshape(h, w, 4)
        hgt = px[..., :3] @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        # suavizado leve para no amplificar ruido de la IA
        hgt = (hgt + np.roll(hgt, 1, 0) + np.roll(hgt, -1, 0)
               + np.roll(hgt, 1, 1) + np.roll(hgt, -1, 1)) / 5
        gx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * 0.5
        gy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * 0.5
        # Dos escalas: detalle fino (poros, costuras) + formas medianas (pliegues)
        big = hgt.copy()
        for sh_ in (2, 4, 8):
            big = (big + np.roll(big, sh_, 0) + np.roll(big, -sh_, 0)
                   + np.roll(big, sh_, 1) + np.roll(big, -sh_, 1)) / 5
        gx2 = (np.roll(big, -4, 1) - np.roll(big, 4, 1)) * 0.125
        gy2 = (np.roll(big, -4, 0) - np.roll(big, 4, 0)) * 0.125
        k = 7.0
        gx = gx + 2.5 * gx2
        gy = gy + 2.5 * gy2
        n = np.dstack([-gx * k, -gy * k, np.ones_like(hgt)])
        n /= np.linalg.norm(n, axis=2, keepdims=True)
        out = np.ones((h, w, 4), dtype=np.float32)
        out[..., :3] = n * 0.5 + 0.5
        img = bpy.data.images.new(m.name + "_normal", w, h, alpha=False, float_buffer=False)
        img.colorspace_settings.name = "Non-Color"
        img.pixels.foreach_set(out.ravel())
        img.pack()
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = img
        tn.location = (lk[0].from_node.location.x, lk[0].from_node.location.y - 320)
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = strength
        nm.location = (tn.location.x + 300, tn.location.y)
        uvl = lk[0].from_node.inputs["Vector"].links
        if uvl:
            nt.links.new(uvl[0].from_socket, tn.inputs["Vector"])
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bs.inputs["Normal"])
        done += 1
    return done


def add_pbr():
    """PBR basico (critica de los modeladores: sin roughness/metallic, o metal
    al 100 %). Metal = 0 y un mapa de rugosidad estimado del color: zonas
    claras y saturadas algo mas brillantes, oscuras y grises mas mates."""
    n = 0
    for m in obj.data.materials:
        if m is None or not m.use_nodes:
            continue
        nt = m.node_tree
        bs = next((x for x in nt.nodes if x.type == "BSDF_PRINCIPLED"), None)
        if bs is None:
            continue
        if not bs.inputs["Metallic"].is_linked:
            bs.inputs["Metallic"].default_value = 0.0
        lk = bs.inputs["Base Color"].links
        if bs.inputs["Roughness"].is_linked or not lk or lk[0].from_node.type != "TEX_IMAGE":
            continue
        src = lk[0].from_node.image
        if src is None or src.size[0] == 0:
            continue
        w, h = src.size
        px = np.empty(w * h * 4, dtype=np.float32)
        src.pixels.foreach_get(px)
        px = px.reshape(h, w, 4)[..., :3]
        mx, mn = px.max(2), px.min(2)
        sat = (mx - mn) / np.maximum(mx, 1e-4)
        lum = px @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        r = np.clip(0.82 - 0.25 * sat - 0.18 * lum, 0.35, 0.95)
        out = np.ones((h, w, 4), dtype=np.float32)
        out[..., 0] = out[..., 1] = out[..., 2] = r
        img = bpy.data.images.new(m.name + "_rugosidad", w, h, alpha=False)
        img.colorspace_settings.name = "Non-Color"
        img.pixels.foreach_set(out.ravel())
        img.pack()
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = img
        uvl = lk[0].from_node.inputs["Vector"].links
        if uvl:
            nt.links.new(uvl[0].from_socket, tn.inputs["Vector"])
        nt.links.new(tn.outputs["Color"], bs.inputs["Roughness"])
        n += 1
    return n


try:
    INFO["mapas_rugosidad"] = add_pbr()
except Exception as e:
    INFO["avisos"].append(f"PBR: {e}")

if args.relieve > 0:
    try:
        INFO["mapas_relieve"] = add_relief(args.relieve)
        log("mapas de relieve:", INFO["mapas_relieve"])
    except Exception as e:
        INFO["avisos"].append(f"relieve: {e}")


# ------------------------------------------------------------ exportar
OUT = args.out
files = {}


# "export": lo principal (GLB, web, FBX, .blend). "extra": lo demas, en otro
# proceso a la vez (OBJ, STL, piezas, pesos, LOD). Asi Blender tarda la mitad.
EXTRA = {"obj", "stl_mm", "piezas", "pesos", "lod1_50", "lod2_15", "visor_web", "roblox"}
# la malla en cuadros (QuadriFlow + horneado, ~15 s) va en su propio proceso, en
# segundo plano: no frena la entrega del modelo
CUADROS = {"quads"}


def verify_textures():
    """Mapas de datos (normal, rugosidad, metal, ORM) en Non-Color y todas las
    imagenes empaquetadas antes de exportar FBX/GLB."""
    fixed = 0
    directas = 0
    for m in bpy.data.materials:
        if not getattr(m, "node_tree", None):
            continue
        # imagen -> MIX (multiplicar por un color fijo) -> Base Color: lo crea
        # el importador glTF por el baseColorFactor. Se conecta la imagen
        # directa: color real y el exportador FBX ya ve (y embebe) la textura.
        nt = m.node_tree
        for l in list(nt.links):
            mx = l.from_node
            if l.to_socket.name != "Base Color" or mx.type not in ("MIX", "MIX_RGB"):
                continue
            if getattr(mx, "blend_type", "") != "MULTIPLY":
                continue
            imgs = [i.links[0].from_socket for i in mx.inputs
                    if i.enabled and i.is_linked and i.links[0].from_node.type == "TEX_IMAGE"]
            otros = [i for i in mx.inputs if i.enabled and i.is_linked
                     and i.links[0].from_node.type != "TEX_IMAGE"]
            if len(imgs) == 1 and not otros:
                nt.links.new(imgs[0], l.to_socket)
                directas += 1
        for l in m.node_tree.links:
            n = l.from_node
            if n.type != "TEX_IMAGE" or n.image is None:
                continue
            dest = l.to_socket.name
            if l.to_node.type == "NORMAL_MAP" or dest in ("Roughness", "Metallic", "Normal"):
                if n.image.colorspace_settings.name != "Non-Color":
                    n.image.colorspace_settings.name = "Non-Color"
                    fixed += 1
    for k_, img in enumerate(bpy.data.images):
        # el exportador FBX distingue imagenes por su ruta: sin ruta, todas
        # chocan y solo se embebe una (o ninguna)
        if not img.filepath and img.source in ("FILE", "GENERATED"):
            ext = {"JPEG": ".jpg"}.get(img.file_format, ".png")
            img.filepath_raw = f"//tex_{k_}_{bpy.path.clean_name(img.name)}{ext}"
    for img in bpy.data.images:
        if img.source in ("FILE", "GENERATED") and not img.packed_file and img.has_data:
            try:
                img.pack()
            except Exception:
                pass
    packed = all(bool(i.packed_file) for i in bpy.data.images
                 if i.users and i.source in ("FILE", "GENERATED") and i.has_data)
    INFO["texturas_non_color_corregidas"] = fixed
    INFO["texturas_conectadas_directo"] = directas
    return packed


TEXTURAS_EMPAQUETADAS = verify_textures()


def export(kind, fn, path):
    if args.stage == "video":
        return
    if args.stage == "export" and (kind in EXTRA or kind in CUADROS):
        return
    if args.stage == "extra" and kind not in EXTRA:
        return
    if args.stage == "quads" and kind not in CUADROS:
        return
    t_ = time.time()
    if "preparacion_s" not in INFO.setdefault("tiempos_export", {}):
        INFO["tiempos_export"]["preparacion_s"] = round(t_ - T0, 1)   # importar, rig, pesos
    try:
        fn()
        files[kind] = os.path.basename(path)
        INFO["tiempos_export"][kind] = round(time.time() - t_, 1)
        log("exportado", os.path.basename(path))
    except Exception as e:
        INFO["avisos"].append(f"{kind}: {e}")
        log("ERROR exportando", kind, e)


# Pose de descanso para exportar el estatico / impresion
if arm is not None:
    set_anim("Pose_T" if "Pose_T" in ANIMS else next(iter(ANIMS)))
    scene.frame_set(0)


def sel_export_objects():
    deselect_all()
    obj.select_set(True)
    if arm is not None:
        arm.select_set(True)
        vl.objects.active = arm
    else:
        vl.objects.active = obj


p = os.path.join(OUT, "modelo_animado.glb")


def _glb():
    sel_export_objects()
    kw = dict(filepath=p, export_format="GLB", use_selection=True,
              export_apply=False, export_yup=True, export_texcoords=True,
              export_normals=True, export_materials="EXPORT")
    if arm is not None:
        kw.update(export_animations=True, export_skins=True)
        try:
            bpy.ops.export_scene.gltf(**kw, export_animation_mode="ACTIONS",
                                      export_force_sampling=True)
            return
        except TypeError:
            pass
    bpy.ops.export_scene.gltf(**kw)


export("glb_animado", _glb, p)

# GLB ligero para el visor web y el celular: malla comprimida con Draco y
# texturas JPEG. Pesa ~4-8 veces menos y carga mucho mas rapido por el tunel.
p_web = os.path.join(OUT, "modelo_web.glb")


def _glb_web():
    sel_export_objects()
    kw = dict(filepath=p_web, export_format="GLB", use_selection=True,
              export_apply=False, export_yup=True, export_texcoords=True,
              export_normals=True, export_materials="EXPORT",
              export_draco_mesh_compression_enable=True,
              export_draco_mesh_compression_level=6,
              export_draco_position_quantization=14,
              export_draco_normal_quantization=10,
              export_draco_texcoord_quantization=12)
    for extra in (dict(export_image_format="JPEG", export_jpeg_quality=88),
                  dict(export_image_format="JPEG"), {}):
        try:
            if arm is not None:
                bpy.ops.export_scene.gltf(**kw, **extra, export_animations=True,
                                          export_skins=True, export_animation_mode="ACTIONS")
            else:
                bpy.ops.export_scene.gltf(**kw, **extra)
            return
        except TypeError:
            continue


export("glb_web", _glb_web, p_web)

p_fbx = os.path.join(OUT, "modelo_rig.fbx")


def _fbx():
    sel_export_objects()
    bpy.ops.export_scene.fbx(
        filepath=p_fbx, use_selection=True, add_leaf_bones=False,
        bake_anim=arm is not None, bake_anim_use_all_actions=True,
        bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
        path_mode="COPY", embed_textures=True, armature_nodetype="NULL",
        axis_forward="-Z", axis_up="Y", mesh_smooth_type="FACE",
        primary_bone_axis="Y", secondary_bone_axis="X")


export("fbx", _fbx, p_fbx)

UE5 = {"Hips": "pelvis", "Spine": "spine_01", "Spine1": "spine_02", "Spine2": "spine_03",
       "Neck": "neck_01", "Head": "head", "LeftShoulder": "clavicle_l", "LeftArm": "upperarm_l",
       "LeftForeArm": "lowerarm_l", "LeftHand": "hand_l", "RightShoulder": "clavicle_r",
       "RightArm": "upperarm_r", "RightForeArm": "lowerarm_r", "RightHand": "hand_r",
       "LeftUpLeg": "thigh_l", "LeftLeg": "calf_l", "LeftFoot": "foot_l", "LeftToeBase": "ball_l",
       "RightUpLeg": "thigh_r", "RightLeg": "calf_r", "RightFoot": "foot_r", "RightToeBase": "ball_r"}
for _s, _l in (("Left", "l"), ("Right", "r")):
    for _f, _u in (("Thumb", "thumb"), ("Index", "index"), ("Middle", "middle"), ("Ring", "ring"),
                   ("Pinky", "pinky")):
        for _k in (1, 2, 3):
            UE5[f"{_s}Hand{_f}{_k}"] = f"{_u}_0{_k}_{_l}"
p_ue = os.path.join(OUT, "modelo_ue5.fbx")


def _ue5():
    """Esqueleto con nombres del maniqui de UE5 (pelvis, spine_01, thigh_l...):
    el IK Retargeter de Unreal lo reconoce solo. Se renombra, se exporta y se
    devuelve el nombre original (los grupos de vertices se renombran solos)."""
    if arm is None or args.rig != "humanoide":
        raise RuntimeError("solo para personajes humanos")
    orig = {}
    for b in arm.data.bones:
        short = b.name.split(":")[-1]
        if short in UE5:
            orig[UE5[short]] = b.name
            b.name = UE5[short]
    try:
        sel_export_objects()
        bpy.ops.export_scene.fbx(filepath=p_ue, use_selection=True, add_leaf_bones=False,
                                 bake_anim=False, path_mode="COPY", embed_textures=True,
                                 armature_nodetype="NULL", axis_forward="-Z", axis_up="Y",
                                 mesh_smooth_type="FACE", primary_bone_axis="Y",
                                 secondary_bone_axis="X", global_scale=1.0)
    finally:
        for new, old in orig.items():
            arm.data.bones[new].name = old


if args.rig == "humanoide":
    export("ue5_fbx", _ue5, p_ue)

# Malla estatica (sin esqueleto) para Mixamo / impresion
p_obj = os.path.join(OUT, "modelo_estatico.obj")


def _obj():
    deselect_all()
    obj.select_set(True)
    vl.objects.active = obj
    bpy.ops.wm.obj_export(filepath=p_obj, export_selected_objects=True,
                          export_materials=True, path_mode="COPY",
                          apply_modifiers=False, forward_axis="NEGATIVE_Z",
                          up_axis="Y")


export("obj", _obj, p_obj)

p_stl = os.path.join(OUT, "modelo_impresion3d.stl")


def _stl():
    deselect_all()
    obj.select_set(True)
    vl.objects.active = obj
    try:
        bpy.ops.wm.stl_export(filepath=p_stl, export_selected_objects=True,
                              apply_modifiers=False, global_scale=1000.0)
    except AttributeError:
        bpy.ops.export_mesh.stl(filepath=p_stl, use_selection=True,
                                global_scale=1000.0)


export("stl_mm", _stl, p_stl)

# Piezas: una pieza por hueso dominante (para ver/editar por partes)
if arm is not None:
    p_pz = os.path.join(OUT, "piezas.glb")

    def _piezas():
        pz = obj.copy()
        pz.data = obj.data.copy()
        pz.name = "Piezas"
        scene.collection.objects.link(pz)
        pz.modifiers.clear()
        pz.parent = None
        me = pz.data
        gnames = [region_of(g.name) for g in pz.vertex_groups]
        regions = sorted(set(gnames), key=lambda r: REGION_ORDER.index(r) if r in REGION_ORDER else 99)
        ridx = {r: i for i, r in enumerate(regions)}
        dom = np.zeros(len(me.vertices), dtype=np.int32)
        for v in me.vertices:
            if v.groups:
                g = max(v.groups, key=lambda x: x.weight)
                dom[v.index] = ridx[gnames[g.group]]
        me.materials.clear()
        rng = np.random.default_rng(3)
        gnames = regions
        for i, n in enumerate(gnames):
            m = bpy.data.materials.new(n)
            c = rng.random(3) * 0.75 + 0.25
            m.diffuse_color = (*c, 1)
            _nodes(m)
            bs = next(nd for nd in m.node_tree.nodes if nd.type == "BSDF_PRINCIPLED")
            bs.inputs["Base Color"].default_value = (*c, 1)
            me.materials.append(m)
        for poly in me.polygons:
            vs = [dom[v] for v in poly.vertices]
            poly.material_index = int(max(set(vs), key=vs.count))
        activate(pz)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.separate(type="MATERIAL")
        bpy.ops.object.mode_set(mode="OBJECT")
        parts = [o for o in scene.objects if o.name.startswith("Piezas")]
        for o in parts:
            if o.data.materials:
                o.name = o.data.materials[o.data.polygons[0].material_index if o.data.polygons else 0].name
            o.vertex_groups.clear()
        deselect_all()
        for o in parts:
            o.select_set(True)
        vl.objects.active = parts[0]
        bpy.ops.export_scene.gltf(filepath=p_pz, export_format="GLB",
                                  use_selection=True, export_yup=True)
        INFO["piezas"] = len(parts)
        for o in parts:
            bpy.data.objects.remove(o, do_unlink=True)

    export("piezas", _piezas, p_pz)

    # Mapa de pesos: cada hueso con su color, mezclados segun el peso.
    # Donde un color se funde con otro es donde la malla se dobla.
    p_ps = os.path.join(OUT, "pesos.glb")

    def _pesos():
        pw = obj.copy()
        pw.data = obj.data.copy()
        pw.name = "Pesos"
        scene.collection.objects.link(pw)
        pw.modifiers.clear()
        pw.parent = None
        me = pw.data
        names = [g.name for g in pw.vertex_groups]
        rng = np.random.default_rng(3)
        cols = rng.random((max(1, len(names)), 3)) * 0.75 + 0.25
        vc = np.full((len(me.vertices), 3), 0.08)
        for v in me.vertices:
            tot = sum(e.weight for e in v.groups)
            if tot > 1e-6:
                vc[v.index] = sum(cols[e.group] * e.weight for e in v.groups) / tot
        attr = me.color_attributes.new("Pesos", "FLOAT_COLOR", "POINT")
        rgba = np.ones((len(me.vertices), 4), dtype=np.float32)
        rgba[:, :3] = vc
        attr.data.foreach_set("color", rgba.ravel())
        me.color_attributes.active_color = attr
        me.materials.clear()
        m = bpy.data.materials.new("pesos")
        _nodes(m)
        bs = next(nd for nd in m.node_tree.nodes if nd.type == "BSDF_PRINCIPLED")
        ca = m.node_tree.nodes.new("ShaderNodeVertexColor")
        ca.layer_name = "Pesos"
        m.node_tree.links.new(ca.outputs["Color"], bs.inputs["Base Color"])
        me.materials.append(m)
        pw.vertex_groups.clear()
        deselect_all()
        pw.select_set(True)
        vl.objects.active = pw
        kw = dict(filepath=p_ps, export_format="GLB", use_selection=True, export_yup=True)
        try:
            bpy.ops.export_scene.gltf(**kw, export_vertex_color="ACTIVE")
        except TypeError:
            bpy.ops.export_scene.gltf(**kw, export_colors=True)
        bpy.data.objects.remove(pw, do_unlink=True)

    export("pesos", _pesos, p_ps)

# LOD: versiones mas ligeras (mismo esqueleto y animaciones) para
# juegos, web y celulares.
def _lod(ratio, path):
    lo = obj.copy()
    lo.data = obj.data.copy()
    lo.name = f"LOD_{int(ratio * 100)}"
    scene.collection.objects.link(lo)
    activate(lo)
    am_ = [m for m in lo.modifiers if m.type == "ARMATURE"]
    for m in am_:
        lo.modifiers.remove(m)
    dm = lo.modifiers.new("Dec", "DECIMATE")
    dm.ratio = ratio
    dm.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=dm.name)
    if arm is not None:
        am2 = lo.modifiers.new("Armature", "ARMATURE")
        am2.object = arm
    deselect_all()
    lo.select_set(True)
    if arm is not None:
        arm.select_set(True)
        vl.objects.active = arm
    kw = dict(filepath=path, export_format="GLB", use_selection=True,
              export_apply=False, export_yup=True, export_materials="EXPORT")
    try:
        if arm is not None:
            bpy.ops.export_scene.gltf(**kw, export_animations=True, export_skins=True,
                                      export_animation_mode="ACTIONS")
        else:
            bpy.ops.export_scene.gltf(**kw)
    finally:
        INFO.setdefault("lod_caras", {})[os.path.basename(path)] = len(lo.data.polygons)
        bpy.data.objects.remove(lo, do_unlink=True)


# Roblox Studio: copia reducida (MeshPart ~10-20k triangulos), escala real
# aplicada, texturas embebidas, sin suelo ni luces de vista previa.
p_rbx = os.path.join(OUT, "modelo_roblox.fbx")


def _texturas_roblox(o, lado=1024):
    """Roblox reduce toda textura a 1024 px al importar: se embeben copias a
    1024 (el modelo principal conserva las de 2048). Devuelve lo creado para
    borrarlo despues."""
    mats, imgs, por_img = [], [], {}
    for slot in o.material_slots:
        m = slot.material
        if not m or not getattr(m, "node_tree", None):
            continue
        cambia = []
        for n in m.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image:
                if not n.image.has_data:
                    try:
                        n.image.pixels[0]          # cargar pixeles (empaquetada)
                    except Exception:
                        pass
                if max(n.image.size) > lado:
                    cambia.append(n)
        if not cambia:
            continue
        m2 = m.copy()
        m2.name = m.name + "_roblox"
        mats.append(m2)
        for n in m2.node_tree.nodes:
            if n.type != "TEX_IMAGE" or not n.image or n.image.name not in [c.image.name for c in cambia]:
                continue
            im = por_img.get(n.image.name)
            if im is None:
                src = n.image
                w, h = src.size
                k = lado / max(w, h)
                w2, h2 = max(1, int(w * k)), max(1, int(h * k))
                tmp = src.copy()
                tmp.scale(w2, h2)
                px = np.empty(w2 * h2 * 4, dtype=np.float32)
                tmp.pixels.foreach_get(px)
                bpy.data.images.remove(tmp)
                # imagen NUEVA (no copia de archivo): al empaquetar guarda los
                # pixeles reducidos y no el archivo original de 2048
                im = bpy.data.images.new(src.name + "_1k", w2, h2, alpha=True,
                                         float_buffer=False, is_data=src.colorspace_settings.name == "Non-Color")
                im.pixels.foreach_set(px)
                # guardar como PNG real y cargarlo como archivo: el exportador
                # FBX solo embebe imagenes de archivo
                pth = os.path.join(OUT, f"_roblox_{len(por_img)}_{bpy.path.clean_name(src.name)}_1k.png")
                im.filepath_raw = pth
                im.file_format = "PNG"
                im.save()
                bpy.data.images.remove(im)
                im = bpy.data.images.load(pth)
                im.name = src.name + "_1k"
                im.colorspace_settings.name = src.colorspace_settings.name
                im.pack()
                try:
                    os.remove(pth)
                except OSError:
                    pass
                por_img[n.image.name] = im
                imgs.append(im)
            n.image = im
        slot.material = m2
    if imgs:
        INFO["roblox_textura_px"] = max(max(i.size) for i in imgs)
    return mats, imgs


rb_mats, rb_imgs = [], []


def _roblox():
    obj.data.calc_loop_triangles()
    tris = len(obj.data.loop_triangles)
    target = int(args.roblox_tris)
    rb = obj.copy()
    rb.data = obj.data.copy()
    rb.name = "Roblox"
    scene.collection.objects.link(rb)
    activate(rb)
    arms = [m for m in rb.modifiers if m.type == "ARMATURE"]
    for m in arms:
        rb.modifiers.remove(m)
    duras = []
    if tris > target:
        dm = rb.modifiers.new("Dec", "DECIMATE")
        dm.ratio = target / tris
        dm.use_collapse_triangulate = True
        if INFO.get("tipo_activo", "").startswith("prop"):
            # hard surface: los vertices de aristas > 35 grados no se colapsan
            duras = _aristas_duras(rb)
            if duras and len(duras) < 0.5 * len(rb.data.vertices) and not os.environ.get("AP3D_SIN_ARISTAS"):
                g = rb.vertex_groups.new(name="Decimar")
                g.add(list(range(len(rb.data.vertices))), 1.0, "REPLACE")
                g.add(duras, 0.0, "REPLACE")
                dm.vertex_group = g.name
                dm.vertex_group_factor = 1.0
        co0 = [rb.matrix_world @ rb.data.vertices[i].co for i in duras]
        bpy.ops.object.modifier_apply(modifier=dm.name)
        if co0:
            # deriva de esquinas: cuanto se movieron las aristas duras
            from mathutils.bvhtree import BVHTree
            dg = bpy.context.evaluated_depsgraph_get()
            tree = BVHTree.FromObject(rb, dg)
            mw_i = rb.matrix_world.inverted()
            paso = max(1, len(co0) // 4000)
            dmax = max((tree.find_nearest(mw_i @ c)[3] or 0) for c in co0[::paso])
            esc = max(rb.matrix_world.to_scale())
            INFO["roblox_deriva_aristas_m"] = round(float(dmax * esc), 5)
            INFO["roblox_aristas_protegidas"] = len(duras)
        for gg in list(rb.vertex_groups):
            if gg.name == "Decimar":
                rb.vertex_groups.remove(gg)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    global rb_mats, rb_imgs
    try:
        rb_mats, rb_imgs = _texturas_roblox(rb)
    except Exception as e:
        rb_mats, rb_imgs = [], []
        INFO["avisos"].append(f"texturas Roblox a 1024: {e}")
    if arm is not None:
        am2 = rb.modifiers.new("Armature", "ARMATURE")
        am2.object = arm
    rb.data.calc_loop_triangles()
    INFO["roblox_triangulos"] = len(rb.data.loop_triangles)
    deselect_all()
    rb.select_set(True)
    if arm is not None:
        arm.select_set(True)
        vl.objects.active = arm
    try:
        bpy.ops.export_scene.fbx(filepath=p_rbx, use_selection=True, add_leaf_bones=False,
                                 bake_anim=arm is not None, bake_anim_use_all_actions=True,
                                 bake_anim_use_nla_strips=False, path_mode="COPY",
                                 embed_textures=True, mesh_smooth_type="FACE",
                                 apply_scale_options="FBX_SCALE_ALL",
                                 axis_forward="-Z", axis_up="Y")
        # copia de respaldo en OBJ + MTL + PNG (mismo modelo ligero de Roblox)
        try:
            dobj = os.path.join(OUT, "obj")
            os.makedirs(dobj, exist_ok=True)
            deselect_all()
            rb.select_set(True)
            vl.objects.active = rb
            # el exportador OBJ no escribe imagenes empaquetadas: se guardan
            # junto al .obj y el .mtl apunta a ellas por nombre
            rutas = {}
            for slot in rb.material_slots:
                nt = getattr(slot.material, "node_tree", None) if slot.material else None
                for n in (nt.nodes if nt else []):
                    im = getattr(n, "image", None) if n.type == "TEX_IMAGE" else None
                    if im is None or im.name in rutas:
                        continue
                    nom = bpy.path.clean_name(im.name) + ".png"
                    dst = os.path.join(dobj, nom)
                    if im.packed_file and im.file_format == "PNG":
                        open(dst, "wb").write(im.packed_file.data)
                    else:
                        im2 = im.copy()
                        im2.filepath_raw = dst
                        im2.file_format = "PNG"
                        im2.save()
                        bpy.data.images.remove(im2)
                    rutas[im.name] = (im, im.filepath_raw)
                    im.filepath_raw = dst
            try:
                bpy.ops.wm.obj_export(filepath=os.path.join(dobj, "modelo.obj"),
                                      export_selected_objects=True, export_materials=True,
                                      path_mode="STRIP", export_animation=False, apply_modifiers=True,
                                      forward_axis="NEGATIVE_Z", up_axis="Y")
            finally:
                for im, fp in rutas.values():
                    im.filepath_raw = fp
            files["obj"] = "obj/modelo.obj"
        except Exception as e:
            INFO["avisos"].append(f"OBJ: {e}")
    finally:
        bpy.data.objects.remove(rb, do_unlink=True)
        for m in rb_mats:
            bpy.data.materials.remove(m)
        for im in rb_imgs:
            bpy.data.images.remove(im)


if args.roblox_tris > 0:
    export("roblox", _roblox, p_rbx)

_nf = len(obj.data.polygons)
for _r, _tag in ((0.5, "lod1_50"), (0.15, "lod2_15")):
    if _nf * _r >= 1500:
        _pl = os.path.join(OUT, f"modelo_{_tag}.glb")
        export(_tag, lambda r=_r, pth=_pl: _lod(r, pth), _pl)

# Malla en cuadrados limpios (como "Smart Mesh" de Tripo): QuadriFlow +
# horneado del color y del relieve de la malla original, para no perder
# detalle. Lleva el mismo esqueleto y animaciones.
p_quads = os.path.join(OUT, "modelo_quads.glb")


def _quads():
    target = int(min(max(len(obj.data.polygons) // 4, 4000), 24000))
    # copia en pose de descanso, sin esqueleto
    q = obj.copy()
    q.data = obj.data.copy()
    q.name = "Quads"
    scene.collection.objects.link(q)
    q.parent = None
    q.modifiers.clear()
    q.vertex_groups.clear()
    q.matrix_world = obj.matrix_world.copy()
    activate(q)
    # QuadriFlow necesita una malla cerrada y sin "pellizcos" (vertices donde
    # se tocan dos partes). Se cierra con voxeles, se arreglan los pellizcos y
    # se reintenta con otro tamano de voxel si hace falta.
    base = q.data.copy()
    ok = False
    for div in (260.0, 200.0, 150.0):
        old_me = q.data
        q.data = base.copy()
        if old_me is not base and old_me.users == 0:
            bpy.data.meshes.remove(old_me)
        activate(q)
        rm = q.modifiers.new("Cerrar", "REMESH")
        rm.mode = "VOXEL"
        rm.voxel_size = H / div
        bpy.ops.object.modifier_apply(modifier=rm.name)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_mode(type="VERT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.mesh.select_non_manifold(extend=False, use_wire=True, use_boundary=False,
                                         use_multi_face=True, use_non_contiguous=True,
                                         use_verts=True)
        bpy.ops.mesh.delete(type="VERT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.fill_holes(sides=0)
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode="OBJECT")
        nf0 = len(q.data.polygons)
        r = bpy.ops.object.quadriflow_remesh(target_faces=target, use_mesh_symmetry=False,
                                             use_preserve_sharp=False, use_preserve_boundary=False,
                                             smooth_normals=True, seed=0)
        if "FINISHED" in r and len(q.data.polygons) < 0.8 * nf0:
            ok = True
            break
        log("quads: reintento con otro voxel")
    metodo = "QuadriFlow"
    if not ok:
        # Respaldo seguro: el remallado de voxeles de Blender tambien da solo
        # cuadrados (rejilla uniforme). Tamano calculado para ~target caras.
        old_me = q.data
        q.data = base.copy()
        if old_me.users == 0:
            bpy.data.meshes.remove(old_me)
        activate(q)
        area = sum(p.area for p in q.data.polygons)
        rm = q.modifiers.new("Cuadros", "REMESH")
        rm.mode = "VOXEL"
        rm.voxel_size = max(math.sqrt(area / target), H / 400)
        bpy.ops.object.modifier_apply(modifier=rm.name)
        sm = q.modifiers.new("Suave", "SMOOTH")
        sm.factor = 0.5
        sm.iterations = 3
        bpy.ops.object.modifier_apply(modifier=sm.name)
        nf0 = 10 ** 9
        metodo = "voxeles"
        ok = len(q.data.polygons) > 100
    bpy.data.meshes.remove(base)
    if not ok:
        bpy.data.objects.remove(q, do_unlink=True)
        raise RuntimeError("no se pudo remallar en cuadrados")
    INFO["quads_metodo"] = metodo
    nq = len(q.data.polygons)
    if nq >= 0.8 * nf0 or nq == 0:
        bpy.data.objects.remove(q, do_unlink=True)
        raise RuntimeError("QuadriFlow no pudo remallar este modelo")
    # UV nuevas y textura horneada desde la malla original
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.003)
    bpy.ops.object.mode_set(mode="OBJECT")
    q.data.materials.clear()
    size = 2048
    img_c = bpy.data.images.new("quads_color", size, size)
    img_n = bpy.data.images.new("quads_normal", size, size, float_buffer=False)
    img_n.colorspace_settings.name = "Non-Color"
    mat = bpy.data.materials.new("quads")
    _nodes(mat)
    nt = mat.node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tc = nt.nodes.new("ShaderNodeTexImage"); tc.image = img_c
    tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = img_n
    nm = nt.nodes.new("ShaderNodeNormalMap")
    q.data.materials.append(mat)
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 1
    scene.cycles.use_denoising = False
    try:
        scene.cycles.device = "GPU" if INFO.get("render") in ("CUDA", "OPTIX") else "CPU"
    except Exception:
        pass
    bk = scene.render.bake
    bk.use_selected_to_active = True
    bk.cage_extrusion = 0.02 * H
    bk.max_ray_distance = 0.06 * H
    bk.margin = 8
    # el original debe estar en la misma pose (descanso) y visible
    am_ = [m for m in obj.modifiers if m.type == "ARMATURE"]
    for m in am_:
        m.show_render = m.show_viewport = False
    try:
        deselect_all()
        obj.select_set(True)
        q.select_set(True)
        vl.objects.active = q
        nt.nodes.active = tc
        bk.use_pass_direct = bk.use_pass_indirect = False
        bk.use_pass_color = True
        bpy.ops.object.bake(type="DIFFUSE")
        nt.nodes.active = tn
        bpy.ops.object.bake(type="NORMAL")
    finally:
        for m in am_:
            m.show_render = m.show_viewport = True
    img_c.pack()
    img_n.pack()
    nt.links.new(tc.outputs["Color"], bs.inputs["Base Color"])
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bs.inputs["Normal"])
    # pesos del esqueleto desde la malla original
    if arm is not None:
        for g in obj.vertex_groups:
            q.vertex_groups.new(name=g.name)
        activate(q)
        dt = q.modifiers.new("Pesos", "DATA_TRANSFER")
        dt.object = obj
        dt.use_vert_data = True
        dt.data_types_verts = {"VGROUP_WEIGHTS"}
        dt.vert_mapping = "POLYINTERP_NEAREST"
        dt.layers_vgroup_select_src = "ALL"
        dt.layers_vgroup_select_dst = "NAME"
        bpy.ops.object.modifier_apply(modifier=dt.name)
        bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
        bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
        bpy.ops.object.vertex_group_normalize_all(group_select_mode="ALL", lock_active=False)
        bpy.ops.object.mode_set(mode="OBJECT")
        q.parent = arm
        amq = q.modifiers.new("Armature", "ARMATURE")
        amq.object = arm
    deselect_all()
    q.select_set(True)
    if arm is not None:
        arm.select_set(True)
        vl.objects.active = arm
    kw = dict(filepath=p_quads, export_format="GLB", use_selection=True, export_yup=True,
              export_materials="EXPORT", export_apply=False)
    try:
        if arm is not None:
            bpy.ops.export_scene.gltf(**kw, export_animations=True, export_skins=True,
                                      export_animation_mode="ACTIONS")
        else:
            bpy.ops.export_scene.gltf(**kw)
        try:
            pf = os.path.join(OUT, "modelo_quads.fbx")
            bpy.ops.export_scene.fbx(filepath=pf, use_selection=True, add_leaf_bones=False,
                                     bake_anim=arm is not None, bake_anim_use_all_actions=True,
                                     bake_anim_use_nla_strips=False, path_mode="COPY",
                                     embed_textures=True, mesh_smooth_type="FACE",
                                     axis_forward="-Z", axis_up="Y")
            files["quads_fbx"] = os.path.basename(pf)
        except Exception as e:
            INFO["avisos"].append(f"quads FBX: {e}")
    finally:
        INFO["quads_caras"] = nq
        bpy.data.objects.remove(q, do_unlink=True)


export("quads", _quads, p_quads)

# Visor web: abre visor.html (junto a los .glb) y elige la animacion.
def _visor():
    html = """<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Visor AP 3D</title>
<script type="module" src="https://cdn.jsdelivr.net/npm/@google/model-viewer@3.5.0/dist/model-viewer.min.js"></script>
<style>body{margin:0;font-family:system-ui;background:#16181d;color:#eee}
model-viewer{width:100vw;height:82vh;background:#22252c}
.bar{display:flex;gap:8px;flex-wrap:wrap;padding:10px}
button{background:#2f6fed;color:#fff;border:0;border-radius:8px;padding:8px 14px;font-size:15px}
button.off{background:#444}</style></head><body>
<model-viewer id="mv" src="modelo_animado.glb" camera-controls autoplay ar
 shadow-intensity="1" exposure="1.1" environment-image="neutral"></model-viewer>
<div class="bar" id="anims"></div><div class="bar" id="lods"></div>
<script>
const mv=document.getElementById('mv'),A=document.getElementById('anims'),L=document.getElementById('lods');
const lods=__LODS__;
function btn(p,t,f){const b=document.createElement('button');b.textContent=t;b.onclick=f;p.appendChild(b);return b}
mv.addEventListener('load',()=>{A.innerHTML='';(mv.availableAnimations||[]).forEach(n=>
 btn(A,n.replace('_',' '),()=>{mv.animationName=n;mv.play()}))});
lods.forEach(([f,t])=>btn(L,t,()=>{mv.src=f}));
</script></body></html>"""
    lods = [["modelo_animado.glb", "Calidad completa"]]
    for k, t in (("lod1_50", "Ligero 50%"), ("lod2_15", "Muy ligero 15%")):
        if k in files:
            lods.append([files[k], t])
    with open(os.path.join(OUT, "visor.html"), "w") as fh:
        fh.write(html.replace("__LODS__", json.dumps(lods)))


export("visor_web", _visor, os.path.join(OUT, "visor.html"))

# Archivo de Blender con todo empaquetado
p_blend = os.path.join(OUT, "modelo.blend")


def _blend():
    try:
        bpy.ops.file.pack_all()
    except Exception:
        pass
    bpy.ops.wm.save_as_mainfile(filepath=p_blend, compress=True, copy=True)


# ------------------------------------------------------------ escena / video
def render(**kw):
    """Renderiza; si falla el reductor de ruido, reintenta sin el y luego en CPU."""
    try:
        return bpy.ops.render.render(**kw)
    except Exception as e:
        log("render fallo:", e, "-> reintento sin reductor de ruido")
        scene.cycles.use_denoising = False
    try:
        return bpy.ops.render.render(**kw)
    except Exception as e:
        log("render fallo:", e, "-> reintento en CPU (rapido: menos muestras y resolucion)")
        scene.cycles.device = "CPU"
        scene.cycles.samples = min(scene.cycles.samples, 8)
        scene.render.resolution_percentage = 50
        INFO["avisos"].append("render en CPU: la GPU no estuvo disponible para Blender")
        return bpy.ops.render.render(**kw)


def setup_render():
    scene.render.engine = "CYCLES"
    dev = "CPU"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        # CUDA primero: en Colab OptiX suele fallar y hacia caer el render al
        # procesador (GPU al 0 % y minutos de espera).
        for t in ("CUDA", "OPTIX"):
            try:
                prefs.compute_device_type = t
                prefs.get_devices()
                if any(d.type == t for d in prefs.devices):
                    for d in prefs.devices:
                        d.use = d.type == t
                    dev = t
                    break
            except Exception:
                continue
    except Exception:
        pass
    scene.cycles.device = "GPU" if dev != "CPU" else "CPU"
    INFO["render"] = dev
    log("render en", dev)
    if dev == "CPU":
        # Sin GPU para Blender: video mas chico para no tardar minutos
        args.samples = min(args.samples, 8)
        scene.render.resolution_percentage = 50
    scene.cycles.samples = args.samples
    # Rapidez: muestreo adaptativo, rebotes justos y datos persistentes entre cuadros
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.03
    scene.cycles.max_bounces = 4
    scene.cycles.diffuse_bounces = 2
    scene.cycles.glossy_bounces = 2
    scene.cycles.transmission_bounces = 2
    scene.cycles.transparent_max_bounces = 4
    scene.render.use_persistent_data = True
    scene.cycles.use_denoising = True
    try:
        # OIDN (usa la GPU en Blender 4.2+); OptiX falla en algunas GPU de Colab
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
        scene.cycles.denoising_use_gpu = True
    except Exception:
        pass
    scene.render.resolution_x = args.video_res
    scene.render.resolution_y = args.video_res
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX" if "AgX" in [
        i.identifier for i in scene.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"

    prev = bpy.data.collections.get("Preview_Studio") or bpy.data.collections.new("Preview_Studio")
    if prev.name not in scene.collection.children:
        scene.collection.children.link(prev)
    # Mundo
    w = bpy.data.worlds.new("Mundo")
    scene.world = w
    _nodes(w)
    bg = w.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.045, 0.05, 0.065, 1)
    bg.inputs[1].default_value = 1.0
    # Luces de 3 puntos
    for name, loc, en, size in (("Clave", (2.5, -3, 3.5), 900, 2.5),
                                ("Relleno", (-3, -2, 2), 350, 3),
                                ("Contra", (0, 3.5, 3), 600, 2)):
        L = bpy.data.lights.new(name, "AREA")
        L.energy = en * (H / 1.8) ** 2
        L.size = size
        o = bpy.data.objects.new(name, L)
        o.location = Vector(loc) * (H / 1.8)
        o.rotation_euler = (Vector((0, 0, H * 0.5)) - o.location).to_track_quat("-Z", "Y").to_euler()
        prev.objects.link(o)
    # Suelo
    bpy.ops.mesh.primitive_plane_add(size=H * 20, location=(0, 0, 0))
    fl = vl.objects.active
    fl.name = "Suelo"
    m = bpy.data.materials.new("Suelo")
    _nodes(m)
    bs = next(nd for nd in m.node_tree.nodes if nd.type == "BSDF_PRINCIPLED")
    bs.inputs["Base Color"].default_value = (0.09, 0.1, 0.12, 1)
    bs.inputs["Roughness"].default_value = 0.85
    fl.data.materials.append(m)
    for c_ in list(fl.users_collection):
        c_.objects.unlink(fl)
    prev.objects.link(fl)
    # Camara
    cam_d = bpy.data.cameras.new("Camara")
    cam_d.lens = 50
    cam = bpy.data.objects.new("Camara", cam_d)
    prev.objects.link(cam)
    scene.camera = cam
    return cam


def aim(cam, ang, dist, z):
    cam.location = Vector((math.sin(ang) * dist, -math.cos(ang) * dist, z))
    cam.rotation_euler = (Vector((0, 0, H * 0.5)) - cam.location).to_track_quat("-Z", "Y").to_euler()


def set_video_output(path):
    r = scene.render
    try:
        r.image_settings.media_type = "VIDEO"      # Blender 5.x
    except Exception:
        pass
    r.image_settings.file_format = "FFMPEG"
    r.ffmpeg.format = "MPEG4"
    r.ffmpeg.codec = "H264"
    r.ffmpeg.constant_rate_factor = "HIGH"
    r.ffmpeg.ffmpeg_preset = "GOOD"
    r.filepath = path


videos_ok = True
DO_VIDEOS = args.stage in ("all", "video")
DO_PREVIEW = args.stage in ("all", "export") and bool(args.preview)
if args.stage in ("extra", "quads"):
    DO_VIDEOS = DO_PREVIEW = False
try:
    cam = setup_render()
except Exception as e:
    videos_ok = False
    INFO["avisos"].append(f"escena de render: {e}")

dist = H * 2.6
if videos_ok and DO_VIDEOS and arm is not None and ANIMS:
    try:
        n = set_anim(args.video)
        aim(cam, math.radians(30), dist, H * 0.62)
        scene.frame_start = 0
        scene.frame_end = (n * max(1, args.loops) - 1) if not args.fast else 3
        path = os.path.join(OUT, f"video_{args.video.lower()}.mp4")
        set_video_output(path)
        log("render animacion", args.video, scene.frame_end + 1, "cuadros")
        render(animation=True)
        files["video_animacion"] = os.path.basename(path)
    except Exception as e:
        INFO["avisos"].append(f"video animacion: {e}")

if videos_ok and DO_VIDEOS and args.turntable:
    try:
        if arm is not None:
            set_anim("Reposo" if "Reposo" in ANIMS else next(iter(ANIMS)))
        frames = 96 if not args.fast else 4
        piv = bpy.data.objects.new("Pivote", None)
        scene.collection.objects.link(piv)
        cam.parent = None
        aim(cam, 0, dist, H * 0.62)
        cam.parent = piv
        piv.rotation_euler = (0, 0, 0)
        piv.keyframe_insert("rotation_euler", frame=0)
        piv.rotation_euler = (0, 0, 2 * math.pi)
        piv.keyframe_insert("rotation_euler", frame=frames)
        for fc in fcurves_of(piv.animation_data.action):
            for k in fc.keyframe_points:
                k.interpolation = "LINEAR"
        scene.frame_start = 0
        scene.frame_end = frames - 1
        path = os.path.join(OUT, "video_giro360.mp4")
        set_video_output(path)
        log("render giro 360")
        render(animation=True)
        files["video_360"] = os.path.basename(path)
    except Exception as e:
        INFO["avisos"].append(f"video 360: {e}")

# Vista previa PNG
if videos_ok and DO_PREVIEW:
    try:
        if arm is not None:
            set_anim("Pose_T" if "Pose_T" in ANIMS else next(iter(ANIMS)))
        scene.frame_set(0)
        r = scene.render
        try:
            r.image_settings.media_type = "IMAGE"
        except Exception:
            pass
        r.image_settings.file_format = "PNG"
        r.filepath = os.path.join(OUT, "vista_previa.png")
        render(write_still=True)
        files["vista_previa"] = "vista_previa.png"
    except Exception as e:
        INFO["avisos"].append(f"vista previa: {e}")

export("blend", _blend, p_blend)

INFO["archivos"] = files
INFO["segundos"] = round(time.time() - T0, 1)
def qa_gate():
    """Control de calidad del modelo final (bloque info.qa): piezas flotantes,
    bordes no manifold, triangulos, vertices, medidas, esqueleto, texturas y
    Roblox. passed = sin alertas criticas."""
    import bmesh
    from mathutils.bvhtree import BVHTree
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    # soldar costuras de UV en la copia: no son islas reales
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    parent = list(range(len(bm.verts)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for e in bm.edges:
        a, b = find(e.verts[0].index), find(e.verts[1].index)
        if a != b:
            parent[a] = b
    comp = {}
    for f_ in bm.faces:
        comp.setdefault(find(f_.verts[0].index), []).append(f_)
    partes = len(comp)
    flot = 0
    if partes > 1:
        # una pieza que TOCA o atraviesa el cuerpo (anclada, soldada con
        # puente) no flota; solo cuentan las que quedan separadas en el aire
        area = {k: sum(f_.calc_area() for f_ in fs) for k, fs in comp.items()}
        cuerpo = max(area, key=area.get)
        fs0 = comp[cuerpo]
        vi = {}
        for f_ in fs0:
            for v in f_.verts:
                vi.setdefault(v.index, len(vi))
        vs = [None] * len(vi)
        for i_, j_ in vi.items():
            vs[j_] = bm.verts[i_].co.copy()
        tree = BVHTree.FromPolygons(vs, [[vi[v.index] for v in f_.verts] for f_ in fs0])
        ext = max(obj.dimensions) or 1.0
        for k, fs in comp.items():
            if k == cuerpo:
                continue
            vv = {v.index: v.co for f_ in fs for v in f_.verts}
            d = 1e9
            for c in list(vv.values())[::max(1, len(vv) // 3000)]:
                loc, nor, _i, dd = tree.find_nearest(c)
                if loc is None:
                    continue
                if (c - loc).dot(nor) < 0:      # vertice DENTRO del cuerpo: esta soldada
                    d = 0.0
                    break
                d = min(d, dd)
            if d > 0.004 * ext:
                flot += 1
    nverts = len(bm.verts)
    bm.free()
    me.calc_loop_triangles()
    tris = len(me.loop_triangles)
    co_ = verts_np(obj)
    dims = (co_.max(0) - co_.min(0)) if len(co_) else np.zeros(3)
    ta = INFO.get("tipo_activo", "")
    crit, w = [], []
    if flot:
        crit.append(f"{flot} piezas flotando separadas del cuerpo")
    if nm:
        w.append(f"{nm} bordes no manifold")
    if tris > 20000 and args.roblox_tris <= 0:
        w.append(f"{tris:,} triangulos: pesado para Roblox (activa el preset Roblox)")
    if ta.startswith("prop") and dims[2] > 1.5 and args.rig != "vehiculo":
        crit.append(f"prop de {dims[2]:.2f} m de alto: revisa la altura del prop")
    if ta == "character" and not (1.0 <= dims[2] <= 2.6):
        w.append(f"personaje de {dims[2]:.2f} m (lo normal: 1.70-2.10 m)")
    if not TEXTURAS_EMPAQUETADAS:
        crit.append("hay texturas sin empaquetar")
    if len(co_) and abs(float(co_[:, 2].min())) > 1e-3:
        crit.append("la base no esta en Z = 0")
    if ta == "prop_rigid" and arm is not None:
        crit.append("prop rigido con esqueleto")
    rt = INFO.get("roblox_triangulos")
    der = INFO.get("roblox_deriva_aristas_m")
    if der is not None and der > 0.01 * max(dims.max(), 1e-6):
        w.append(f"las aristas se movieron {der * 1000:.1f} mm al reducir para Roblox")
    if rt and rt > 15000:
        crit.append(f"FBX Roblox con {rt:,} triangulos (> 15,000)")
    INFO["qa"] = {"islands": 1 + flot, "mesh_parts": partes, "non_manifold_edges": nm,
                  "triangles": tris, "vertices": nverts,
                  "dimensions_m": [round(float(x), 3) for x in dims],
                  "has_rig": arm is not None, "textures_packed": bool(TEXTURAS_EMPAQUETADAS),
                  "asset_type": ta or "auto", "roblox_triangles": rt,
                  "hard_surface": ta.startswith("prop"),
                  "corner_drift_m": der,
                  "roblox_ready": bool(rt) and rt <= 15000 and bool(TEXTURAS_EMPAQUETADAS),
                  "warnings": crit + w, "critical": crit, "passed": not crit}
    log("QA:", INFO["qa"])


try:
    qa_gate()
except Exception as e:
    INFO["avisos"].append(f"QA: {e}")

_info_name = {"video": "rig_info_video.json", "extra": "rig_info_extra.json",
              "quads": "rig_info_quads.json"}.get(
    args.stage, "rig_info.json")
with open(os.path.join(OUT, _info_name), "w") as f:
    json.dump(INFO, f, indent=2, ensure_ascii=False, default=str)
log("listo", json.dumps(files))
