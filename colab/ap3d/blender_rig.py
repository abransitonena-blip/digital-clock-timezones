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
                choices=["humanoide", "cuadrupedo", "ninguno"])
ap.add_argument("--height", type=float, default=1.8)
ap.add_argument("--rotate", type=float, default=0.0,
                help="giro extra en grados alrededor de Z")
ap.add_argument("--video", default="Caminar")
ap.add_argument("--video_res", type=int, default=1080)
ap.add_argument("--samples", type=int, default=48)
ap.add_argument("--turntable", type=int, default=1)
ap.add_argument("--loops", type=int, default=3)
ap.add_argument("--fast", type=int, default=0, help="pruebas: video corto")
args = ap.parse_args(argv)
os.makedirs(args.out, exist_ok=True)
INFO = {"rig": args.rig, "avisos": []}

scene = bpy.context.scene
vl = bpy.context.view_layer
scene.render.fps = 30


# ------------------------------------------------------------ helpers
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

    # Torso: ancho en el pecho
    chest = co[(z > 0.70 * H) & (z < 0.78 * H) & (np.abs(x) < 0.26 * H)]
    sh_x = float(np.abs(chest[:, 0]).max()) * 0.80 if len(chest) else 0.11 * H
    sh_x = min(max(sh_x, 0.08 * H), 0.16 * H)
    sh_z = 0.815 * H
    torso_y = float(np.median(chest[:, 1])) if len(chest) else 0.0

    # Manos: el punto mas lejano a cada lado entre 0.40H y 0.95H
    def hand(side):
        c = co[(z > 0.40 * H) & (z < 0.95 * H) & (side * x > sh_x + 0.06 * H)]
        if len(c) < 20:
            return Vector((side * (sh_x + 0.06 * H), torso_y, 0.50 * H)), False
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
                sh_z=sh_z, torso_y=torso_y, hand_l=hl, hand_r=hr)


BONES = []          # (nombre, cabeza, cola, padre)


def humanoid_bones(d):
    H, ty = d["H"], d["torso_y"]
    P = "mixamorig:"
    hz = d["hip_z"]
    sp = [hz, hz + 0.09 * H, hz + 0.18 * H, hz + 0.27 * H]
    neck_z = 0.86 * H
    head_z = 0.895 * H
    B = [
        ("Hips", (0, ty, d["crotch"] + 0.01 * H), (0, ty, sp[1]), None),
        ("Spine", (0, ty, sp[1]), (0, ty, sp[2]), "Hips"),
        ("Spine1", (0, ty, sp[2]), (0, ty, sp[3]), "Spine"),
        ("Spine2", (0, ty, sp[3]), (0, ty, neck_z), "Spine1"),
        ("Neck", (0, ty, neck_z), (0, ty, head_z), "Spine2"),
        ("Head", (0, ty, head_z), (0, ty, 0.98 * H), "Neck"),
        ("HeadTop_End", (0, ty, 0.98 * H), (0, ty, 1.0 * H), "Head"),
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
    return [(P + n, Vector(h), Vector(t), (P + p) if p else None) for n, h, t, p in B]


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
        BONES = humanoid_bones(D)
        INFO["proporciones"] = {k: (round(v, 3) if isinstance(v, float) else list(map(lambda q: round(q, 3), v)))
                                for k, v in D.items()}
    else:
        BONES = quadruped_bones(co, H)

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

    # Copia cerrada para calcular los pesos con calor
    proxy = obj.copy()
    proxy.data = obj.data.copy()
    proxy.name = "Proxy"
    scene.collection.objects.link(proxy)
    proxy.data.materials.clear()
    activate(proxy)
    rm = proxy.modifiers.new("Remesh", "REMESH")
    rm.mode = "VOXEL"
    rm.voxel_size = H / 180.0
    try:
        rm.adaptivity = 0.0
    except Exception:
        pass
    bpy.ops.object.modifier_apply(modifier=rm.name)
    if len(proxy.data.polygons) > 120000:
        dm = proxy.modifiers.new("Dec", "DECIMATE")
        dm.ratio = 120000 / len(proxy.data.polygons)
        bpy.ops.object.modifier_apply(modifier=dm.name)
    log("proxy de pesos", len(proxy.data.polygons), "caras")

    activate(arm, [proxy])
    heat_ok = True
    try:
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    except Exception as e:
        heat_ok = False
        INFO["avisos"].append(f"pesos por calor fallaron: {e}")
    filled = sum(1 for g in proxy.vertex_groups)
    if heat_ok:
        # verificar que no haya vertices sin peso
        nv = len(proxy.data.vertices)
        empty = sum(1 for v in proxy.data.vertices if not v.groups)
        if filled == 0 or empty > 0.02 * nv:
            heat_ok = False
            INFO["avisos"].append(f"{empty} vertices sin peso con calor; "
                                  "se uso respaldo por distancia")
    if not heat_ok:
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
    # Cobertura por hueso (para ver de un vistazo si un hueso no mueve nada)
    cnt = {g.name: 0 for g in obj.vertex_groups}
    for v in me.vertices:
        for e in v.groups:
            if e.weight > 0.05:
                cnt[gi2name[e.group]] += 1
    INFO["vertices_por_hueso"] = cnt
    vacios = [n for n, c in cnt.items() if c == 0 and not n.endswith("_End")]
    if vacios:
        INFO["avisos"].append("huesos sin zona: " + ", ".join(vacios))
    log("pesos reparados:", sin_peso, "vertices; huesos vacios:", len(vacios))

    obj.parent = arm
    am = obj.modifiers.new("Armature", "ARMATURE")
    am.object = arm


# ------------------------------------------------------------ animaciones
ANIMS = {}


def pb(name):
    if args.rig == "humanoide":
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


def build_action(name, frames, pose_fn, step=2):
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm.animation_data_create()
    arm.animation_data.action = act
    for b in arm.pose.bones:
        b.rotation_mode = "QUATERNION"
    keyed = set()
    for f in list(range(0, frames, step)) + [frames]:
        t = (f % frames) / frames
        scene.frame_set(f)
        for b in arm.pose.bones:
            b.rotation_quaternion = Quaternion()
            b.location = Vector()
        pose = pose_fn(t)
        for bname, val in pose.items():
            b = pb(bname)
            if b is None or val is None:
                continue
            if isinstance(val, Quaternion):
                b.rotation_quaternion = val
            else:
                b.location = val
        for b in arm.pose.bones:
            b.keyframe_insert("rotation_quaternion", frame=f)
            if b.parent is None:
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

    build_action("Reposo", 72, idle, step=3)
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


if arm is not None:
    activate(arm)
    bpy.ops.object.mode_set(mode="POSE")
    if args.rig == "humanoide":
        humanoid_anims(D)
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


# ------------------------------------------------------------ exportar
OUT = args.out
files = {}


def export(kind, fn, path):
    try:
        fn()
        files[kind] = os.path.basename(path)
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
        gnames = [g.name for g in pz.vertex_groups]
        dom = np.zeros(len(me.vertices), dtype=np.int32)
        for v in me.vertices:
            if v.groups:
                g = max(v.groups, key=lambda x: x.weight)
                dom[v.index] = g.group
        me.materials.clear()
        rng = np.random.default_rng(3)
        for i, n in enumerate(gnames):
            m = bpy.data.materials.new("pieza_" + n.split(":")[-1])
            c = rng.random(3) * 0.75 + 0.25
            m.diffuse_color = (*c, 1)
            m.use_nodes = True
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


_nf = len(obj.data.polygons)
for _r, _tag in ((0.5, "lod1_50"), (0.15, "lod2_15")):
    if _nf * _r >= 1500:
        _pl = os.path.join(OUT, f"modelo_{_tag}.glb")
        export(_tag, lambda r=_r, pth=_pl: _lod(r, pth), _pl)

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
def setup_render():
    scene.render.engine = "CYCLES"
    dev = "CPU"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for t in ("OPTIX", "CUDA"):
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
    scene.cycles.samples = args.samples
    scene.cycles.use_denoising = True
    try:
        scene.cycles.denoiser = "OPTIX" if dev == "OPTIX" else "OPENIMAGEDENOISE"
    except Exception:
        pass
    scene.render.resolution_x = args.video_res
    scene.render.resolution_y = args.video_res
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX" if "AgX" in [
        i.identifier for i in scene.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
    INFO["render"] = dev

    # Mundo
    w = bpy.data.worlds.new("Mundo")
    scene.world = w
    w.use_nodes = True
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
        scene.collection.objects.link(o)
    # Suelo
    bpy.ops.mesh.primitive_plane_add(size=H * 20, location=(0, 0, 0))
    fl = vl.objects.active
    fl.name = "Suelo"
    m = bpy.data.materials.new("Suelo")
    m.use_nodes = True
    bs = next(nd for nd in m.node_tree.nodes if nd.type == "BSDF_PRINCIPLED")
    bs.inputs["Base Color"].default_value = (0.09, 0.1, 0.12, 1)
    bs.inputs["Roughness"].default_value = 0.85
    fl.data.materials.append(m)
    # Camara
    cam_d = bpy.data.cameras.new("Camara")
    cam_d.lens = 50
    cam = bpy.data.objects.new("Camara", cam_d)
    scene.collection.objects.link(cam)
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
try:
    cam = setup_render()
except Exception as e:
    videos_ok = False
    INFO["avisos"].append(f"escena de render: {e}")

dist = H * 2.6
if videos_ok and arm is not None and ANIMS:
    try:
        n = set_anim(args.video)
        aim(cam, math.radians(30), dist, H * 0.62)
        scene.frame_start = 0
        scene.frame_end = (n * max(1, args.loops) - 1) if not args.fast else 3
        path = os.path.join(OUT, f"video_{args.video.lower()}.mp4")
        set_video_output(path)
        log("render animacion", args.video, scene.frame_end + 1, "cuadros")
        bpy.ops.render.render(animation=True)
        files["video_animacion"] = os.path.basename(path)
    except Exception as e:
        INFO["avisos"].append(f"video animacion: {e}")

if videos_ok and args.turntable:
    try:
        if arm is not None:
            set_anim("Reposo" if "Reposo" in ANIMS else next(iter(ANIMS)))
        frames = 120 if not args.fast else 4
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
        bpy.ops.render.render(animation=True)
        files["video_360"] = os.path.basename(path)
    except Exception as e:
        INFO["avisos"].append(f"video 360: {e}")

# Vista previa PNG
if videos_ok:
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
        bpy.ops.render.render(write_still=True)
        files["vista_previa"] = "vista_previa.png"
    except Exception as e:
        INFO["avisos"].append(f"vista previa: {e}")

export("blend", _blend, p_blend)

INFO["archivos"] = files
INFO["segundos"] = round(time.time() - T0, 1)
with open(os.path.join(OUT, "rig_info.json"), "w") as f:
    json.dump(INFO, f, indent=2, ensure_ascii=False, default=str)
log("listo", json.dumps(files))
