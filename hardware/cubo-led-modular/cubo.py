"""Cubo AP: módulo LED modular, impermeable (IP67 de diseño). Modelo paramétrico para Blender 4.x.
Uso en Blender: Scripting → Abrir → cubo.py → Run. Sin pantalla: python3 cubo.py
Genera cubo_ap.blend, STL de cuerpo/tapa/empaque y renders."""
import bpy, bmesh, math, os, sys
from mathutils import Vector
OUT = os.path.dirname(os.path.abspath(__file__))
# ---------------- parámetros (mm) ----------------
L = 80.0          # lado exterior del cubo
HB = 66.0         # alto del cuerpo
HL = 14.0         # alto de la tapa (total = HB + HL = 80)
WALL = 4.0        # pared (deja lugar a la ranura del empaque)
FLOOR = 3.5       # fondo
R = 7.0           # radio de las esquinas
GROOVE_W, GROOVE_D = 2.4, 1.7    # ranura para cordón de silicón de 2.5 mm
BOSS_D, INSERT_D = 10.0, 4.2     # postes de esquina y barreno para inserto M3
GLAND = 16.2      # barreno para prensaestopas M16 (entrada 127 V y salida LED)
VENT = 12.2       # barreno para membrana de ventilación M12 (evita condensación)
TAB_L, TAB_W, TAB_T = 26.0, 12.0, 4.0   # orejas de montaje
# ---------------- utilidades ----------------
def limpiar():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene; s.unit_settings.system = 'METRIC'; s.unit_settings.scale_length = 0.001
def caja_redondeada(nombre, sx, sy, sz, r, z0=0.0, seg=10):
    """Prisma de sx×sy con esquinas verticales redondeadas, de z0 a z0+sz."""
    bm = bmesh.new()
    pts = []
    for cx, cy, a0 in ((sx/2-r, sy/2-r, 0), (-sx/2+r, sy/2-r, 90), (-sx/2+r, -sy/2+r, 180), (sx/2-r, -sy/2+r, 270)):
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg); pts.append((cx + r*math.cos(a), cy + r*math.sin(a)))
    vb = [bm.verts.new((x, y, z0)) for x, y in pts]; vt = [bm.verts.new((x, y, z0 + sz)) for x, y in pts]
    bm.faces.new(vb[::-1]); bm.faces.new(vt)
    n = len(pts)
    for i in range(n): bm.faces.new((vb[i], vb[(i+1) % n], vt[(i+1) % n], vt[i]))
    me = bpy.data.meshes.new(nombre); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(nombre, me); bpy.context.collection.objects.link(ob); return ob
def cilindro(nombre, d, h, loc, rot=(0, 0, 0), seg=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=d/2, depth=h, location=loc, rotation=rot)
    ob = bpy.context.active_object; ob.name = nombre; return ob
def cubo_(nombre, size, loc):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); ob = bpy.context.active_object; ob.name = nombre; ob.scale = size
    bpy.ops.object.transform_apply(scale=True); return ob
def booleana(base, otro, op='DIFFERENCE', borrar=True):
    m = base.modifiers.new("b", 'BOOLEAN'); m.operation = op; m.object = otro; m.solver = 'EXACT'
    bpy.context.view_layer.objects.active = base
    for o in bpy.context.selected_objects: o.select_set(False)
    base.select_set(True); bpy.ops.object.modifier_apply(modifier=m.name)
    if borrar: bpy.data.objects.remove(otro, do_unlink=True)
def biselar(ob, ancho=0.8, seg=3):
    m = ob.modifiers.new("bisel", 'BEVEL'); m.width = ancho; m.segments = seg; m.limit_method = 'ANGLE'; m.angle_limit = math.radians(35)
    bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier=m.name)
def texto(nombre, s, size, prof, loc, rot=(0, 0, 0)):
    bpy.ops.object.text_add(location=loc, rotation=rot); t = bpy.context.active_object; t.name = nombre
    t.data.body = s; t.data.size = size; t.data.extrude = prof; t.data.align_x = 'CENTER'; t.data.align_y = 'CENTER'
    bpy.ops.object.convert(target='MESH'); return bpy.context.active_object
def material(nombre, color, rough=0.5, metal=0.0, trans=0.0):
    m = bpy.data.materials.new(nombre); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if trans: b.inputs["Transmission Weight"].default_value = trans
    return m
# ---------------- modelo ----------------
limpiar()
# CUERPO
cuerpo = caja_redondeada("Cuerpo", L, L, HB, R)
hueco = caja_redondeada("hueco", L - 2*WALL, L - 2*WALL, HB, R - WALL, z0=FLOOR)
booleana(cuerpo, hueco)
for sx in (1, -1):                                   # postes de esquina con inserto M3
    for sy in (1, -1):
        c = (sx*(L/2 - WALL - BOSS_D/2 + 1.5), sy*(L/2 - WALL - BOSS_D/2 + 1.5))
        p = cilindro("poste", BOSS_D, HB - FLOOR, (c[0], c[1], FLOOR + (HB - FLOOR)/2)); booleana(cuerpo, p, 'UNION')
        h = cilindro("ins", INSERT_D, 10, (c[0], c[1], HB - 5 + 0.01)); booleana(cuerpo, h)
ranura = caja_redondeada("ran", L - WALL + GROOVE_W, L - WALL + GROOVE_W, GROOVE_D + 0.01, R - WALL/2 + GROOVE_W/2, z0=HB - GROOVE_D)
dentro = caja_redondeada("ran_in", L - WALL - GROOVE_W, L - WALL - GROOVE_W, GROOVE_D + 0.4, R - WALL/2 - GROOVE_W/2, z0=HB - GROOVE_D - 0.2)
booleana(ranura, dentro); booleana(cuerpo, ranura)
# barrenos: prensaestopas (izq. 127 V, der. salida LED) y ventila (atrás)
booleana(cuerpo, cilindro("g1", GLAND, 12, (-L/2, 0, 22), (0, math.pi/2, 0)))
booleana(cuerpo, cilindro("g2", GLAND, 12, (L/2, 0, 22), (0, math.pi/2, 0)))
booleana(cuerpo, cilindro("v", VENT, 12, (0, L/2, 48), (math.pi/2, 0, 0)))
for sx in (1, -1):                                   # postes para la placa (M3, 60 × 60)
    for sy in (1, -1):
        p = cilindro("pp", 7, 6, (sx*30, sy*30, FLOOR + 3)); booleana(cuerpo, p, 'UNION')
        booleana(cuerpo, cilindro("ph", 2.8, 6, (sx*30, sy*30, FLOOR + 3.6)))
for sy in (1, -1):                                   # orejas de montaje con ranura
    t = caja_redondeada("oreja", TAB_L, TAB_W + 4, TAB_T, 4)
    t.location = (0, sy*(L/2 + TAB_W/2 - 2), 0); bpy.ops.object.select_all(action='DESELECT'); t.select_set(True)
    bpy.context.view_layer.objects.active = t; bpy.ops.object.transform_apply(location=True)
    booleana(cuerpo, t, 'UNION')
    s = caja_redondeada("slot", 10, 4.4, 10, 2.2, z0=-2); s.location = (0, sy*(L/2 + TAB_W/2), 0)
    bpy.ops.object.select_all(action='DESELECT'); s.select_set(True); bpy.context.view_layer.objects.active = s; bpy.ops.object.transform_apply(location=True)
    booleana(cuerpo, s)
logo = texto("logo", "AP", 16, 0.8, (0, -L/2 + 0.6, HB/2), (math.pi/2, 0, 0)); booleana(cuerpo, logo)
biselar(cuerpo, 0.6)
# TAPA
tapa = caja_redondeada("Tapa", L, L, HL, R, z0=HB)
int_tapa = caja_redondeada("int_tapa", L - 2*WALL, L - 2*WALL, HL - 3.0, R - WALL, z0=HB - 0.01)
booleana(tapa, int_tapa)
for sx in (1, -1):
    for sy in (1, -1):
        c = (sx*(L/2 - WALL - BOSS_D/2 + 1.5), sy*(L/2 - WALL - BOSS_D/2 + 1.5))
        p = cilindro("tposte", BOSS_D, HL - 3.0, (c[0], c[1], HB + (HL - 3.0)/2)); booleana(tapa, p, 'UNION')
        booleana(tapa, cilindro("tb", 3.4, HL + 2, (c[0], c[1], HB + HL/2)))
        booleana(tapa, cilindro("tc", 6.5, 3.2, (c[0], c[1], HB + HL - 1.5)))       # cabeza del tornillo
booleana(tapa, cilindro("guia_luz", 3.2, HL + 2, (0, 22, HB + HL/2)))              # guía de luz del LED de estado
ventana = caja_redondeada("ventana", 36, 14, 1.2, 3, z0=HB + HL - 1.0); ventana.location = (0, -22, 0)
bpy.ops.object.select_all(action='DESELECT'); ventana.select_set(True); bpy.context.view_layer.objects.active = ventana; bpy.ops.object.transform_apply(location=True)
booleana(tapa, ventana)                                                              # zona delgada: ventana de antena Bluetooth
biselar(tapa, 1.2)
# EMPAQUE (cordón de silicón en la ranura)
emp = caja_redondeada("Empaque", L - WALL + 2.2, L - WALL + 2.2, 2.4, R - WALL/2 + 1.1, z0=HB - GROOVE_D)
emp_in = caja_redondeada("emp_in", L - WALL - 2.2, L - WALL - 2.2, 3.0, R - WALL/2 - 1.1, z0=HB - GROOVE_D - 0.3)
booleana(emp, emp_in)
# INTERIOR de referencia (no se imprime): placa de potencia, placa de control y prensaestopas
fuente = cubo_("Ref_fuente_ACDC", (52, 44, 24), (0, -4, FLOOR + 6 + 12))
control = cubo_("Ref_placa_control", (60, 60, 1.6), (0, 0, FLOOR + 6 + 30))
esp = cubo_("Ref_ESP32C3", (18, 25, 3), (0, -14, FLOOR + 6 + 32.3))
borne = cubo_("Ref_borneras", (10, 30, 10), (28, 0, FLOOR + 6 + 36))
for i, x in enumerate((-L/2 - 6, L/2 + 6)):
    pg = cilindro(f"Prensaestopas_{i+1}", 22, 8, (x, 0, 22), (0, math.pi/2, 0), seg=6)   # tuerca hexagonal
    cb = cilindro(f"Cable_{i+1}", 7, 30, (x + (-16 if x < 0 else 16), 0, 22), (0, math.pi/2, 0))
vent = cilindro("Membrana_ventila", 16, 3, (0, L/2 + 1.5, 48), (math.pi/2, 0, 0), seg=40)
# materiales
mats = {"Cuerpo": material("ASA_gris", (0.16, 0.17, 0.19), 0.55), "Tapa": material("ASA_tapa", (0.85, 0.86, 0.88), 0.4),
        "Empaque": material("Silicon", (0.9, 0.35, 0.1), 0.6), "Ref_fuente_ACDC": material("Fuente", (0.12, 0.12, 0.12), 0.7),
        "Ref_placa_control": material("PCB", (0.05, 0.35, 0.15), 0.4), "Ref_ESP32C3": material("Metal", (0.7, 0.7, 0.72), 0.3, 1.0),
        "Ref_borneras": material("Borne", (0.1, 0.4, 0.85), 0.5)}
neg = material("Negro", (0.03, 0.03, 0.03), 0.6)
for ob in bpy.data.objects:
    if ob.type == 'MESH':
        ob.data.materials.clear(); ob.data.materials.append(mats.get(ob.name, neg))
        for f in ob.data.polygons: f.use_smooth = False
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "cubo_ap.blend"))
# STL para imprimir (unidades: mm); se triangula antes para que la malla salga cerrada
for nombre in ("Cuerpo", "Tapa", "Empaque"):
    ob = bpy.data.objects[nombre]; bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='EAR_CLIP')
    bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges); bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(ob.data); bm.free()
    bpy.ops.wm.stl_export(filepath=os.path.join(OUT, f"{nombre.lower()}.stl"), export_selected_objects=True, global_scale=1.0)
print("modelo listo:", [o.name for o in bpy.data.objects])
