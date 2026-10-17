"""Renders con Blender de las piezas imprimibles (STL), las placas (GLB) y los ensambles caja + placa de AP Electric.

Usos (desde la carpeta hardware/ap-electric):

  Con Blender instalado (Windows/Mac/Linux), sin abrir la ventana:
      blender -b -P blender/render_blender.py -- --salida blender/renders
  Solo algunas piezas (filtro por nombre) y más calidad:
      blender -b -P blender/render_blender.py -- --solo caja --muestras 128 --res 1920x1200
  Con el módulo Python de Blender (pip install bpy==4.2.0):
      python blender/render_blender.py --salida blender/renders

Qué renderiza:
  accesorios/stl/*.stl          las 29 piezas imprimibles, una imagen por pieza
  web/modelos3d/AP_*.glb        las seis placas con sus piezas (colores por tipo de pieza) y la caja
  ensamble: la caja AP Rack con una placa dentro y la tapa levantada (ensamble_rack16.jpg, ensamble_rl4.jpg)

Opciones: --rehacer si (vuelve a renderizar lo que ya existe)  --salida CARPETA  --solo TEXTO (solo lo que contenga el texto)  --res ANCHOxALTO  --muestras N (Cycles)  --motor CYCLES|EEVEE
Son renders de diseño: nada está fabricado ni impreso. Los colores de las placas son solo de apariencia.
"""
import math, os, sys, glob
import bpy
from mathutils import Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, ".."))      # hardware/ap-electric


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    o = {"salida": os.path.join(AQUI, "renders"), "solo": "", "res": "1280x800", "muestras": 48, "motor": "CYCLES", "rehacer": "no"}
    i = 0
    while i < len(a):
        k = a[i].lstrip("-")
        if k in o and i + 1 < len(a):
            o[k] = type(o[k])(a[i + 1]) if k == "muestras" else a[i + 1]; i += 2
        else:
            i += 1
    return o


_vacio = {}
COLOR = {  # nombre de la pieza (fragmento) -> (RGB, rugosidad, metal)
    "tapa": ((0.91, 0.36, 0.02), 0.45, 0.0), "union": ((0.78, 0.78, 0.80), 0.4, 0.0),
    "tpu": ((0.03, 0.03, 0.035), 0.7, 0.0), "alivio": ((0.03, 0.03, 0.035), 0.7, 0.0), "tapon": ((0.03, 0.03, 0.035), 0.7, 0.0),
    "pasacables": ((0.03, 0.03, 0.035), 0.7, 0.0), "riel": ((0.75, 0.77, 0.80), 0.3, 0.9), "pila": ((0.7, 0.72, 0.75), 0.3, 0.9),
    "bandeja": ((0.16, 0.18, 0.22), 0.5, 0.0), "caja": ((0.16, 0.18, 0.22), 0.5, 0.0),
    "clip_din": ((0.91, 0.36, 0.02), 0.45, 0.0), "placa_pulsadores": ((0.92, 0.92, 0.9), 0.35, 0.0),
}
DEFECTO = ((0.91, 0.36, 0.02), 0.45, 0.0)       # naranja AP Electric (PETG)


def limpiar(res, muestras, motor):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _vacio.clear()                                   # los objetos de la escena anterior ya no existen
    sc = bpy.context.scene
    w, h = [int(x) for x in res.lower().split("x")]
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
    if motor.upper() == "EEVEE":
        sc.render.engine = "BLENDER_EEVEE_NEXT" if bpy.app.version >= (4, 2, 0) else "BLENDER_EEVEE"
    else:
        sc.render.engine = "CYCLES"
        sc.cycles.samples = int(muestras); sc.cycles.use_denoising = True
        try:
            sc.cycles.device = "CPU"
        except Exception:
            pass
    sc.view_settings.view_transform = "Filmic" if "Filmic" in bpy.types.ColorManagedViewSettings.bl_rna.properties["view_transform"].enum_items.keys() else "Standard"
    sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 90
    mundo = bpy.data.worlds.new("mundo"); sc.world = mundo; mundo.use_nodes = True
    bg = mundo.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.045, 0.055, 0.075, 1); bg.inputs[1].default_value = 0.6
    return sc


def material(nombre, rgb, rug, metal):
    m = bpy.data.materials.new(nombre); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rug; p.inputs["Metallic"].default_value = metal
    return m


def piso(zmin, tam):
    bpy.ops.mesh.primitive_plane_add(size=tam * 14, location=(0, 0, zmin))
    p = bpy.context.active_object
    p.data.materials.append(material("piso", (0.07, 0.085, 0.11), 0.55, 0.0))
    return p


def luces(c, r):
    def area(nombre, pos, energia, color, tam):
        d = bpy.data.lights.new(nombre, "AREA"); d.energy = energia; d.color = color; d.size = tam
        o = bpy.data.objects.new(nombre, d); bpy.context.collection.objects.link(o)
        o.location = c + Vector(pos) * r
        t = o.constraints.new("TRACK_TO"); t.target = vacio(c); t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    area("principal", (-1.2, -1.4, 1.8), 90 * r * r, (1.0, 0.96, 0.9), r * 1.6)
    area("relleno", (1.8, -0.8, 0.8), 28 * r * r, (0.75, 0.88, 1.0), r * 2.0)
    area("contraluz", (0.2, 1.8, 1.3), 55 * r * r, (1.0, 0.55, 0.25), r * 1.2)


def vacio(c):
    k = tuple(round(x, 5) for x in c)
    if k not in _vacio:
        e = bpy.data.objects.new("objetivo", None); e.location = c; bpy.context.collection.objects.link(e); _vacio[k] = e
    return _vacio[k]


def camara(c, r, azim=-35, elev=32, dist=4.4, foco=50):
    d = bpy.data.cameras.new("cam"); d.lens = foco
    d.clip_start = r * 0.01; d.clip_end = r * 200           # piezas de 2 cm: el plano cercano por omisión (10 cm) las cortaba
    o = bpy.data.objects.new("cam", d); bpy.context.collection.objects.link(o); bpy.context.scene.camera = o
    a, e = math.radians(azim), math.radians(elev)
    o.location = c + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * r * dist
    t = o.constraints.new("TRACK_TO"); t.target = vacio(c); t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"


def caja_limites(objs):
    mn = Vector((1e9, 1e9, 1e9)); mx = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        for v in o.bound_box:
            w = o.matrix_world @ Vector(v)
            mn = Vector((min(mn[i], w[i]) for i in range(3))); mx = Vector((max(mx[i], w[i]) for i in range(3)))
    return mn, mx


def escena(objs, salida, dist=4.4, azim=-35, elev=32):
    mn, mx = caja_limites(objs)
    c = (mn + mx) / 2; r = max((mx - mn)) / 2
    piso(mn.z, r)
    luces(c, r)
    camara(c, r, azim, elev, dist)
    bpy.context.scene.render.filepath = salida
    bpy.ops.render.render(write_still=True)
    print("render:", salida)


def importar_stl(ruta):
    try:
        bpy.ops.wm.stl_import(filepath=ruta)           # Blender 4.1 o posterior
    except AttributeError:
        bpy.ops.import_mesh.stl(filepath=ruta)         # Blender 3.x
    o = bpy.context.selected_objects[0]
    o.scale = (0.001, 0.001, 0.001)
    bpy.context.view_layer.update()
    return o


def pintar(o, nombre):
    rgb, rug, metal = DEFECTO
    for frag, v in COLOR.items():
        if frag in nombre:
            rgb, rug, metal = v; break
    o.data.materials.clear(); o.data.materials.append(material(nombre, rgb, rug, metal))
    # bordes vivos y superficies planas limpias (en Blender 4.1 o posterior: sombreado automático por ángulo)
    bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(32))
    except Exception:
        try:
            bpy.ops.object.shade_flat()
        except Exception:
            pass


def importar_glb(ruta):
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=ruta)
    return [o for o in bpy.data.objects if o not in antes]


def ancla(objs, z0=0.0):
    """Mueve el grupo para que quede centrado en x, y y apoyado en z = z0."""
    mn, mx = caja_limites([o for o in objs if o.type == "MESH"])
    d = Vector(((mn.x + mx.x) / -2, (mn.y + mx.y) / -2, z0 - mn.z))
    for o in objs:
        if o.parent is None:
            o.location += d
    bpy.context.view_layer.update()


def ya(o, sub, n):
    """True si la imagen ya existe y no se pidió rehacerla (--rehacer si): permite reanudar un lote interrumpido."""
    return o["rehacer"] != "si" and os.path.exists(os.path.join(o["salida"], sub, n + ".jpg"))


def renders_stl(o):
    hechos = []
    for f in sorted(glob.glob(os.path.join(RAIZ, "accesorios", "stl", "*.stl"))):
        n = os.path.splitext(os.path.basename(f))[0]
        if o["solo"] and o["solo"] not in n or ya(o, "piezas", n):
            continue
        sc = limpiar(o["res"], o["muestras"], o["motor"])
        pieza = importar_stl(f); pintar(pieza, n)
        ancla([pieza]); escena([pieza], os.path.join(o["salida"], "piezas", n + ".jpg"))
        hechos.append(n)
    return hechos


def renders_glb(o):
    hechos = []
    for f in sorted(glob.glob(os.path.join(RAIZ, "web", "modelos3d", "*.glb"))):
        n = os.path.splitext(os.path.basename(f))[0]
        if o["solo"] and o["solo"] not in n or ya(o, "placas", n):
            continue
        sc = limpiar(o["res"], o["muestras"], o["motor"])
        objs = importar_glb(f)
        ancla(objs); escena([x for x in objs if x.type == "MESH"], os.path.join(o["salida"], "placas", n + ".jpg"), dist=4.0, azim=-30, elev=38)
        hechos.append(n)
    return hechos


def renders_ensamble(o):
    hechos = []
    for placa, nombre in (("AP_RACK16", "ensamble_rack16"), ("AP_RL4", "ensamble_rl4"), ("AP_RACKAO4", "ensamble_ao4"), ("AP_LED8", "ensamble_led8")):
        if o["solo"] and o["solo"] not in nombre or ya(o, "ensambles", nombre):
            continue
        sc = limpiar(o["res"], o["muestras"], o["motor"])
        caja = importar_stl(os.path.join(RAIZ, "accesorios", "stl", "caja_rack.stl")); pintar(caja, "caja")
        tapa = importar_stl(os.path.join(RAIZ, "accesorios", "stl", "tapa_caja_rack.stl")); pintar(tapa, "tapa")
        bpy.context.view_layer.update()
        mnc, mxc = caja_limites([caja]); cx, cy = (mnc.x + mxc.x) / 2, (mnc.y + mxc.y) / 2
        placa_objs = importar_glb(os.path.join(RAIZ, "web", "modelos3d", placa + ".glb"))
        raiz_p = [x for x in placa_objs if x.parent is None]
        # la placa GLB (en metros) se centra en la caja y se apoya sobre los postes (3 mm de piso + 6 mm de postes)
        mn, mx = caja_limites([x for x in placa_objs if x.type == "MESH"])
        d = Vector((cx - (mn.x + mx.x) / 2, cy - (mn.y + mx.y) / 2, 0.0090 - mn.z))
        for x in raiz_p:
            x.location += d
        tapa.location.z += (mxc.z - mnc.z) + 0.030          # tapa levantada 30 mm
        bpy.context.view_layer.update()
        todo = [caja, tapa] + [x for x in placa_objs if x.type == "MESH"]
        escena(todo, os.path.join(o["salida"], "ensambles", nombre + ".jpg"), dist=4.6, azim=-32, elev=30)
        hechos.append(nombre)
    return hechos


if __name__ == "__main__":
    o = args()
    os.makedirs(o["salida"], exist_ok=True)
    total = renders_stl(o) + renders_glb(o) + renders_ensamble(o)
    print("listo: %d renders en %s" % (len(total), o["salida"]))
