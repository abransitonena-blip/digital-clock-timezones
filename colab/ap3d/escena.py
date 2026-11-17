"""Blender (sin ventana): arma una escena/cuarto con varios modelos ya
generados.

    blender -b -P escena.py -- --items items.json --out carpeta --ancho 5 --fondo 4

items.json: [{"glb": ".../modelo_animado.glb", "nombre": "sofa", "alto": 0.9}, ...]

* Cada modelo se escala a su altura real y se apoya en el suelo.
* Acomodo: los muebles grandes van contra las paredes (de mayor a menor),
  los chicos al centro, sin encimarse (cajas que no se tocan + 10 cm de paso).
* Cuarto: piso, 3 paredes, luz de sol y de ventana. Exporta escena.glb
  (con las animaciones de cada modelo), escena.blend y escena.json.
"""
import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--items", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--ancho", type=float, default=5.0)
ap.add_argument("--fondo", type=float, default=4.0)
ap.add_argument("--alto", type=float, default=2.7)
args = ap.parse_args(argv)
os.makedirs(args.out, exist_ok=True)
items = json.load(open(args.items))

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
W, F, A = args.ancho, args.fondo, args.alto
GAP = 0.10


def mat(name, rgb, rough=0.8):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bs = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bs.inputs["Base Color"].default_value = (*rgb, 1)
    bs.inputs["Roughness"].default_value = rough
    return m


def plane(name, size, loc, rot, m):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0], size[1], 1)
    o.data.materials.append(m)
    return o


cuarto = [plane("Piso", (W, F), (0, 0, 0), (0, 0, 0), mat("piso", (0.42, 0.33, 0.25), 0.6)),
          plane("Pared_fondo", (W, A), (0, F / 2, A / 2), (math.pi / 2, 0, 0),
                mat("pared", (0.82, 0.8, 0.76))),
          plane("Pared_izq", (F, A), (-W / 2, 0, A / 2), (math.pi / 2, 0, math.pi / 2),
                bpy.data.materials["pared"]),
          plane("Pared_der", (F, A), (W / 2, 0, A / 2), (math.pi / 2, 0, -math.pi / 2),
                bpy.data.materials["pared"])]

# ---- importar y escalar cada modelo
cosas = []
for it in items:
    before = set(bpy.data.objects)
    try:
        bpy.ops.import_scene.gltf(filepath=it["glb"])
    except Exception as e:
        print("no se pudo importar", it.get("nombre"), e)
        continue
    new = [o for o in bpy.data.objects if o not in before]
    # el importador crea formas de hueso (Icosphere) para mostrar el esqueleto: fuera
    formas = {pb.custom_shape for o in new if o.type == "ARMATURE" for pb in o.pose.bones
              if pb.custom_shape}
    for o in list(new):
        if o in formas or (o.type == "MESH" and o.name.startswith("Icosphere") and not o.data.materials):
            new.remove(o)
            bpy.data.objects.remove(o, do_unlink=True)
    roots = [o for o in new if o.parent is None or o.parent not in new]
    grupo = bpy.data.objects.new("Obj_" + it.get("nombre", "x"), None)
    scene.collection.objects.link(grupo)
    for r in roots:
        r.parent = grupo
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in new:
        if o.type == "MESH":
            me = o.evaluated_get(dg).to_mesh()
            step = max(1, len(me.vertices) // 4000)
            pts += [o.matrix_world @ me.vertices[i].co for i in range(0, len(me.vertices), step)]
            o.evaluated_get(dg).to_mesh_clear()
    if not pts:
        continue
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    alto = float(it.get("alto") or 1.0)
    k = alto / max(mx.z - mn.z, 1e-6)
    grupo.scale = (k, k, k)
    dx, dy = (mx.x - mn.x) * k, (mx.y - mn.y) * k
    centro = Vector(((mn.x + mx.x) / 2 * k, (mn.y + mx.y) / 2 * k, mn.z * k))
    cosas.append(dict(g=grupo, w=dx, d=dy, off=centro, nombre=it.get("nombre", "objeto"),
                      pared=it.get("pared", dx * dy > 0.5)))

# ---- acomodo: grandes contra las paredes, chicos al centro
cosas.sort(key=lambda c: -c["w"] * c["d"])
ocupado = []


def libre(x0, y0, x1, y1):
    if x0 < -W / 2 + 0.02 or x1 > W / 2 - 0.02 or y0 < -F / 2 + 0.02 or y1 > F / 2 - 0.02:
        return False
    return all(x1 + GAP <= a or x0 - GAP >= c or y1 + GAP <= b or y0 - GAP >= d
               for a, b, c, d in ocupado)


def place(c):
    w, d = c["w"], c["d"]
    cand = []
    if c["pared"]:
        # pared del fondo (de izq a der), luego paredes laterales girados 90
        x = -W / 2 + 0.05
        while x + w <= W / 2:
            cand.append((x + w / 2, F / 2 - 0.03 - d / 2, 0.0))           # frente hacia el cuarto
            x += 0.1
        y = F / 2 - 0.05
        while y - w >= -F / 2:
            cand.append((-W / 2 + 0.03 + d / 2, y - w / 2, math.pi / 2))
            cand.append((W / 2 - 0.03 - d / 2, y - w / 2, -math.pi / 2))
            y -= 0.1
    # centro (espiral desde el medio, un poco hacia el frente)
    for r in [i * 0.15 for i in range(40)]:
        for a in range(0, 360, 30):
            cand.append((r * math.cos(math.radians(a)), 0.3 + r * math.sin(math.radians(a)), 0.0))
    for cx, cy, rot in cand:
        ww, dd = (d, w) if abs(math.sin(rot)) > 0.5 else (w, d)
        box = (cx - ww / 2, cy - dd / 2, cx + ww / 2, cy + dd / 2)
        if libre(*box):
            ocupado.append(box)
            g = c["g"]
            g.rotation_euler = (0, 0, rot)
            off = c["off"].copy()
            off.rotate(g.rotation_euler)
            g.location = (cx - off.x, cy - off.y, -off.z)
            return True
    return False


colocados, fuera = [], []
for c in cosas:
    (colocados if place(c) else fuera).append(c["nombre"])
for c in cosas:
    if c["nombre"] in fuera:
        c["g"].hide_render = True

# ---- luz
bpy.ops.object.light_add(type="SUN", location=(2, -3, 5))
sol = bpy.context.object
sol.data.energy = 3.0
sol.rotation_euler = (math.radians(50), 0, math.radians(30))
bpy.ops.object.light_add(type="AREA", location=(0, -F / 2 + 0.2, A * 0.7))
ven = bpy.context.object
ven.data.energy = 300
ven.data.size = 1.5
ven.rotation_euler = (math.radians(90), 0, 0)
bpy.ops.object.camera_add(location=(0, -F * 1.25, A * 0.9))
cam = bpy.context.object
cam.rotation_euler = (Vector((0, 0, A * 0.3)) - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam

# ---- exportar
info = {"cuarto_m": [W, F, A], "colocados": colocados, "no_cupieron": fuera,
        "objetos": [{"nombre": c["nombre"], "ancho_m": round(c["w"], 2), "fondo_m": round(c["d"], 2),
                     "pos": [round(v, 2) for v in c["g"].location]} for c in cosas]}
bpy.ops.export_scene.gltf(filepath=os.path.join(args.out, "escena.glb"), export_format="GLB",
                          export_animations=True, export_lights=True)
try:
    bpy.ops.file.pack_all()
except Exception:
    pass
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(args.out, "escena.blend"), compress=True)
json.dump(info, open(os.path.join(args.out, "escena.json"), "w"), indent=2, ensure_ascii=False)
print("ESCENA", json.dumps(info, ensure_ascii=False))
