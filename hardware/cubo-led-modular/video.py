"""Video de presentación de los productos AP (Blender 4.x, Cycles). Parte de cubo_ap.blend y agrega el Nodo AP con su carcasa.
  python3.11 video.py cuadros 1 480     -> PNG en ./video_cuadros/ (se puede cortar y retomar por rangos)
  python3.11 video.py prueba 200        -> un solo cuadro de prueba
  ffmpeg -framerate 24 -i video_cuadros/%04d.png -c:v libx264 -pix_fmt yuv420p -crf 23 ap_productos.mp4
Tomas (24 cuadros/s, 20 s):
  1–120   Cubo AP cerrado, cámara girando.
  121–240 Vista explotada: tapa, empaque y la placa v3 (ESP32-C3 soldado) suben.
  241–360 Nodo AP: carcasa cerrada; la tapa sube y deja ver la placa con el CH32V003.
  361–480 El sistema: cubo + 3 nodos en la misma línea DMX; las tiras cambian de color a la vez (modo espejo)."""
import bpy, bmesh, math, os, sys
from mathutils import Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(AQUI, "cubo_ap.blend"))
sc = bpy.context.scene; O = bpy.data.objects
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 16
try: sc.cycles.use_denoising = True
except Exception: pass
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
sc.render.fps = 24; sc.frame_start, sc.frame_end = 1, 480
sc.view_settings.view_transform = 'AgX'

def mat(nombre, color, rugo=0.5, metal=0.0, emision=None, fuerza=0.0):
    m = bpy.data.materials.new(nombre); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rugo; b.inputs["Metallic"].default_value = metal
    if emision is not None:
        b.inputs["Emission Color"].default_value = (*emision, 1); b.inputs["Emission Strength"].default_value = fuerza
    return m

def caja(nombre, dx, dy, dz, x, y, z, m):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z + dz / 2)); o = bpy.context.active_object
    o.scale = (dx, dy, dz); bpy.ops.object.transform_apply(scale=True); o.name = nombre; o.data.materials.append(m)
    return o

def restar(o, cortador):
    md = o.modifiers.new("corte", 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = cortador; md.solver = 'EXACT'
    bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(cortador, do_unlink=True)

def placa_textura(nombre, W, H, imagen, x, y, z):
    """Placa de 1.6 mm con la vista realista de fabricación como textura (la imagen tiene 2 mm de margen)."""
    cuerpo = caja(nombre + "_fr4", W, H, 1.6, x, y, z, mat(nombre + "_fr4", (0.05, 0.25, 0.12), 0.6))
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    for v in bm.verts: v.co.x *= W; v.co.y *= H
    uv = bm.loops.layers.uv.new()
    for f in bm.faces:
        for lp in f.loops:
            px, py = lp.vert.co.x, lp.vert.co.y
            lp[uv].uv = ((px + W / 2 + 2) / (W + 4), (py + H / 2 + 2) / (H + 4))
    me = bpy.data.meshes.new(nombre); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(nombre, me); sc.collection.objects.link(o); o.location = (x, y, z + 1.61)
    m = bpy.data.materials.new(nombre + "_tex"); m.use_nodes = True; nt = m.node_tree
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(imagen)
    nt.links.new(t.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    nt.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.45
    me.materials.append(m)
    return [cuerpo, o]

def texto(cuerpo, tam, m):
    bpy.ops.object.text_add(); t = bpy.context.active_object; t.data.body = cuerpo; t.data.size = tam
    t.data.align_x = 'CENTER'; t.data.extrude = 0.0; t.data.materials.append(m)
    return t

def clave(o, prop, cuadro, valor):
    setattr(o, prop, valor); o.keyframe_insert(data_path=prop, frame=cuadro)

def visible(o, desde, hasta):
    """Solo se renderiza entre los cuadros desde..hasta."""
    for f, v in ((1, True), (desde, False), (hasta + 1, True)):
        if f < 1: continue
        o.hide_render = v; o.keyframe_insert("hide_render", frame=f)

# ---------------- Mundo, piso y luces ----------------
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.90, 0.92, 0.95, 1)
for f, s in ((1, 0.7), (360, 0.7), (361, 0.08), (480, 0.08)): bg.inputs[1].default_value = s; bg.inputs[1].keyframe_insert("default_value", frame=f)
bpy.ops.mesh.primitive_plane_add(size=3000, location=(0, 0, -0.01)); piso = bpy.context.active_object
piso.data.materials.append(mat("piso", (0.93, 0.93, 0.95), 0.35))
bpy.ops.object.light_add(type='AREA', location=(150, -220, 300)); l1 = bpy.context.active_object
l1.data.size = 200; l1.rotation_euler = (math.radians(35), 0, math.radians(30))
for f, e in ((1, 1.2e6), (360, 1.2e6), (361, 1.5e5), (480, 1.5e5)): l1.data.energy = e; l1.data.keyframe_insert("energy", frame=f)
bpy.ops.object.light_add(type='AREA', location=(-250, 120, 180)); l2 = bpy.context.active_object
l2.data.size = 160; l2.rotation_euler = (math.radians(60), 0, math.radians(-115)); l2.data.energy = 3e5

# ---------------- Cubo AP con la placa v3 ----------------
for n in ("Ref_ESP32C3", "Ref_ESP_chip", "Ref_tira_-1", "Ref_tira_1"): O[n].hide_render = True    # v3: sin módulo enchufable
tex = bpy.data.materials["PCB_textura"].node_tree
for nd in tex.nodes:
    if nd.type == "TEX_IMAGE": nd.image = bpy.data.images.load(os.path.join(AQUI, "placa-control-v3", "vista_placa_arriba.png"))
placa_cubo = [o for o in O if o.name.startswith("Ref_") and not o.hide_render and o.name != "Ref_fuente_ACDC"]
# explotado: 130–190 sube; en 361 vuelve armado
for o, dz in [(O["Tapa"], 75), (O["Empaque"], 42)] + [(o, 38) for o in placa_cubo]:
    z0 = o.location.z
    for f, z in ((1, z0), (130, z0), (190, z0 + dz), (360, z0 + dz), (361, z0)):
        o.location.z = z; o.keyframe_insert("location", index=2, frame=f)

# ---------------- Nodo AP con carcasa ----------------
gris, claro = bpy.data.materials["ASA_gris"], bpy.data.materials["ASA_tapa"]
verde = mat("borne_verde", (0.05, 0.35, 0.15), 0.5); metal = mat("metal", (0.8, 0.8, 0.82), 0.25, 1.0)
negro = bpy.data.materials["Negro"]
NODOS = [(175.0, -10.0), (265.0, -10.0), (355.0, -10.0)]
def nodo(i, x0, y0):
    # carcasa: base abierta 58 × 46 × 20 con paredes de 2 mm y ventanas laterales para las borneras
    base = caja(f"Nodo{i}_base", 58, 46, 20, x0, y0, 0, gris)
    restar(base, caja("hueco", 54, 42, 20, x0, y0, 2, gris))
    restar(base, caja("v_izq", 6, 30, 11, x0 - 28, y0 - 2, 8, gris))
    restar(base, caja("v_der", 6, 28, 11, x0 + 28, y0, 8, gris))
    restar(base, caja("v_fre", 13, 6, 11, x0 - 12, y0 - 22, 8, gris))   # J4: DMX sale por el frente
    piezas = placa_textura(f"Nodo{i}_placa", 50, 38, os.path.join(AQUI, "nodo", "placa", "vista_placa_arriba.png"), x0, y0, 4)
    for nom, dx, dy, px, py in (("J1", 8, 10.2, -21.0, 10.5), ("J3", 7, 10.5, -21.5, -1.5), ("J4", 10.5, 7, -12.0, -13.0), ("J2", 8, 25.4, 21.5, 0.0)):
        piezas.append(caja(f"Nodo{i}_{nom}", dx, dy, 8.5, x0 + px, y0 + py, 5.6, verde))
    tapa = caja(f"Nodo{i}_tapa", 58, 46, 3, x0, y0, 20, claro)
    luz = caja(f"Nodo{i}_luz", 3, 3, 0.6, x0 + 7.2, y0 - 8.5, 23, mat(f"luz{i}", (0.1, 0.9, 0.3), 0.3, emision=(0.1, 1.0, 0.3), fuerza=8))
    t = texto("NODO AP", 5.5, mat(f"rotulo{i}", (0.2, 0.22, 0.25), 0.6)); t.location = (x0, y0 + 9, 23.02)
    return base, tapa, [luz, t], piezas
nodos = [nodo(i, x, y) for i, (x, y) in enumerate(NODOS)]
# toma 3: la tapa del primer nodo sube 260–300 y baja en 361
b1, tapa1, extras1, _ = nodos[0]
for o in [tapa1] + extras1:
    z0 = o.location.z
    for f, z in ((1, z0), (260, z0), (300, z0 + 48), (360, z0 + 48), (361, z0)):
        o.location.z = z; o.keyframe_insert("location", index=2, frame=f)

# cable DMX: del cubo al primer nodo y entre nodos (tubos)
def tubo(nombre, pts, r, m):
    cu = bpy.data.curves.new(nombre, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 4
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts): bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    o = bpy.data.objects.new(nombre, cu); sc.collection.objects.link(o); cu.materials.append(m); return o
azul = mat("cable_dmx", (0.08, 0.12, 0.35), 0.5)
tubo("dmx_0", [(77, -6, 22), (110, -25, 2), (140, -22, 2), (146, -14, 9)], 2.2, azul)
for k in range(2):
    xa, xb = NODOS[k][0], NODOS[k + 1][0]
    tubo(f"dmx_{k+1}", [(xa - 12, -30, 9), (xa - 4, -55, 2), (xb - 45, -45, 2), (xb - 32, -12, 9)], 2.2, azul)

# tiras LED: una por nodo y una del cubo; color sincronizado (modo espejo) en la toma 4
tira_m = mat("tira", (0.95, 0.95, 0.95), 0.4, emision=(1, 1, 1), fuerza=0.0)
bsdf = tira_m.node_tree.nodes["Principled BSDF"]
SEC = [(361, (1.0, 0.05, 0.05)), (390, (1.0, 0.05, 0.05)), (400, (0.05, 1.0, 0.15)), (425, (0.05, 1.0, 0.15)), (435, (0.1, 0.2, 1.0)),
       (455, (0.1, 0.2, 1.0)), (465, (1.0, 0.7, 0.35)), (480, (1.0, 0.7, 0.35))]
for f, cl in SEC: bsdf.inputs["Emission Color"].default_value = (*cl, 1); bsdf.inputs["Emission Color"].keyframe_insert("default_value", frame=f)
for f, s in ((1, 0.0), (360, 0.0), (361, 14.0), (480, 14.0)): bsdf.inputs["Emission Strength"].default_value = s; bsdf.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
for k, (x, y) in enumerate(NODOS): caja(f"tira_{k}", 10, 170, 2, x + 14, y + 110, 0, tira_m)

# ---------------- Cámara y textos ----------------
bpy.ops.object.camera_add(); cam = bpy.context.active_object; sc.camera = cam; cam.data.lens = 50; cam.data.clip_end = 8000
def toma(f, pos, objetivo):
    cam.location = pos; d = Vector(objetivo) - Vector(pos); cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
def orbita(f0, f1, c, r, h, a0, a1, z_obj, pasos=6):
    for k in range(pasos + 1):
        a = math.radians(a0 + (a1 - a0) * k / pasos); f = round(f0 + (f1 - f0) * k / pasos)
        toma(f, (c[0] + r * math.sin(a), c[1] - r * math.cos(a), h), (c[0], c[1], z_obj))
orbita(1, 120, (0, 0), 330, 190, -55, 5, 40)
orbita(121, 240, (0, 0), 420, 300, 10, 40, 92)
x1, y1 = NODOS[0]
orbita(241, 360, (x1, y1), 150, 175, -35, 20, 4)
toma(361, (150, -780, 430), (175, 45, 0)); toma(480, (175, -700, 380), (180, 55, 0))
for fc in cam.animation_data.action.fcurves:
    for kp in fc.keyframe_points: kp.interpolation = 'BEZIER' if kp.co.x not in (120, 240, 360) else 'CONSTANT'

oscuro = mat("txt_oscuro", (0.03, 0.04, 0.06), 0.8, emision=(0.02, 0.03, 0.05), fuerza=1.0)
ob = oscuro.node_tree.nodes["Principled BSDF"]; ob.inputs["Base Color"].default_value = (0, 0, 0, 1); ob.inputs["Roughness"].default_value = 1.0
ob.inputs["Specular IOR Level"].default_value = 0.0
blanco = mat("txt_blanco", (1, 1, 1), 0.8, emision=(1, 1, 1), fuerza=3.0)
def rotulo(t1, t2, f0, f1, m):
    a = texto(t1, 0.042, m); b = texto(t2, 0.019, m)
    for o, yy in ((a, -0.135), (b, -0.165)):
        o.parent = cam; o.location = (0, yy, -1.0); o.rotation_euler = (0, 0, 0)
        visible(o, f0, f1)
rotulo("Cubo AP", "Controlador LED IP67 · Wi-Fi · Bluetooth · DMX", 8, 120, oscuro)
rotulo("Placa v3: chip ESP32-C3 soldado", "Sin módulos · antena externa U.FL · 5 canales PWM", 128, 240, oscuro)
rotulo("Nodo AP", "CH32V003 · DMX512 → RGBW · 3 A por canal", 248, 360, oscuro)
rotulo("Un solo sistema", "El cubo transmite DMX y los nodos copian su color", 368, 480, blanco)

# ---------------- Render ----------------
modo = sys.argv[1] if len(sys.argv) > 1 else "prueba"
if os.environ.get("ESCALA"): sc.render.resolution_percentage = int(os.environ["ESCALA"])
salida = os.path.join(AQUI, "video_cuadros"); os.makedirs(salida, exist_ok=True)
if modo == "prueba":
    f = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    sc.frame_set(f); sc.render.filepath = os.path.join(salida, f"prueba_{f:04d}.png"); bpy.ops.render.render(write_still=True)
else:
    a, b = int(sys.argv[2]), int(sys.argv[3])
    for f in range(a, b + 1):
        ruta = os.path.join(salida, f"{f:04d}.png")
        if os.path.exists(ruta): continue                 # retomar donde quedó
        sc.frame_set(f); sc.render.filepath = ruta; bpy.ops.render.render(write_still=True)
        print("cuadro", f, flush=True)
