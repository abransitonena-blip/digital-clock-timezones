"""Renders del Cubo AP (armado, explotado y en corte) a partir de cubo_ap.blend. python3 render.py"""
import bpy, math, os
from mathutils import Vector
OUT = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, "cubo_ap.blend"))
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 40
try: sc.cycles.use_denoising = True
except Exception: pass
sc.render.resolution_x, sc.render.resolution_y = 1400, 1000
sc.render.film_transparent = False
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.92, 0.93, 0.95, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 0, -0.01)); piso = bpy.context.active_object
mp = bpy.data.materials.new("piso"); mp.use_nodes = True; mp.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.95, 0.95, 0.96, 1); piso.data.materials.append(mp)
bpy.ops.object.light_add(type='AREA', location=(120, -160, 220)); l = bpy.context.active_object; l.data.energy = 9e5; l.data.size = 150
l.rotation_euler = (math.radians(40), 0, math.radians(35))
bpy.ops.object.light_add(type='AREA', location=(-180, 60, 120)); l2 = bpy.context.active_object; l2.data.energy = 2.5e5; l2.data.size = 120
l2.rotation_euler = (math.radians(60), 0, math.radians(-110))
bpy.ops.object.camera_add(); cam = bpy.context.active_object; sc.camera = cam; cam.data.lens = 70; cam.data.clip_end = 5000
def mirar(pos, objetivo):
    cam.location = pos; d = Vector(objetivo) - Vector(pos); cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
O = bpy.data.objects
refs = [o for o in O if o.name.startswith("Ref_")]
def ver(nombres_ocultos):
    for o in O:
        if o.type == 'MESH' and o is not piso: o.hide_render = o.name in nombres_ocultos
def rend(nombre):
    sc.render.filepath = os.path.join(OUT, nombre); bpy.ops.render.render(write_still=True); print("render", nombre)
import sys
SOLO = sys.argv[1] if len(sys.argv) > 1 else "todo"
if SOLO == "todo":
  # 1) armado
  ver({o.name for o in refs})
  mirar((230, -300, 230), (0, 0, 38)); rend("render_armado.png")
  O["Tapa"].location.z += 55; O["Empaque"].location.z += 26
  ver(set())
  mirar((250, -320, 300), (0, 0, 55)); rend("render_explotado.png")
  O["Tapa"].location.z -= 55; O["Empaque"].location.z -= 26
# 3) corte a la mitad (se quita y < 0) para ver pared, ranura, empaque y postes
corte = []
import bmesh
for n in ["Cuerpo", "Tapa", "Empaque"] + [r.name for r in refs]:
    o = O[n].copy(); o.data = O[n].data.copy(); sc.collection.objects.link(o); corte.append(o)
    bm = bmesh.new(); bm.from_mesh(o.data)
    r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0.37, 0, 0), plane_no=(1, 0, 0), clear_outer=True)
    bmesh.ops.contextual_create(bm, geom=[e for e in r["geom_cut"] if isinstance(e, bmesh.types.BMEdge)])   # tapa el corte
    bm.to_mesh(o.data); bm.free()
ver({o.name for o in O if o.type == 'MESH' and o not in corte and o is not piso})
mirar((260, -170, 150), (0, 0, 35)); rend("render_corte.png")
