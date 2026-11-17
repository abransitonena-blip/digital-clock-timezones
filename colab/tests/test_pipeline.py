"""Pruebas del pipeline (sin GPU): reparacion de islas y salida de Blender.

    python3 colab/tests/test_pipeline.py --self-test     (deben pasar los 4 tests)

Usa el modulo bpy si esta instalado (pip install bpy) o el binario de Blender
de la variable AP3D_BLENDER. Las mallas de prueba se crean aqui mismo.
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import trimesh

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
RIG = os.path.join(os.path.dirname(AQUI), "ap3d", "blender_rig.py")
TMP = tempfile.mkdtemp(prefix="ap3d_test_")
FALLAS = []


def check(cond, msg):
    print(("  OK   " if cond else "  FALLA ") + msg)
    if not cond:
        FALLAS.append(msg)


def blender(inp, out, *extra):
    blend = os.environ.get("AP3D_BLENDER")
    args = ["--", "--in", inp, "--out", out, "--stage", "all", "--preview", "0",
            "--turntable", "0", "--relieve", "0"] + list(extra)
    if blend and os.path.exists(blend):
        cmd = [blend, "-b", "--factory-startup", "-P", RIG] + args
    else:
        cmd = [sys.executable, RIG] + args
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    p = os.path.join(out, "rig_info.json")
    if not os.path.exists(p):
        print(r.stdout[-2000:], r.stderr[-2000:])
        raise RuntimeError("Blender no genero rig_info.json")
    return json.load(open(p))


def caja_con_piezas():
    """Jack-in-the-Box (escala 1:4): caja, manivela separada 1.3 cm (3 % del
    tamano, como los 5.3 cm del modelo de 1.70 m), brazo a 1.5 cm, polvo."""
    caja = trimesh.creation.box((0.4, 0.4, 0.4))
    caja.apply_translation((0, 0, 0.2))
    manivela = trimesh.creation.cylinder(0.01, 0.12)
    manivela.apply_translation((0.223, 0, 0.25))
    brazo = trimesh.creation.cylinder(0.02, 0.2)
    brazo.apply_translation((-0.235, 0, 0.3))
    polvo = trimesh.creation.icosphere(radius=0.003)
    polvo.apply_translation((0, 0, 0.6))
    return trimesh.util.concatenate([caja, manivela, brazo, polvo])


def test_islas():
    print("1) Islas flotantes")
    from ap3d.engine import fix_islands
    m, rep = fix_islands(caja_con_piezas())
    check(rep["islas"] == 4, f"detecta 4 islas ({rep['islas']})")
    check(rep["eliminadas"] == 1, "elimina el polvo")
    check(rep["ancladas"] == 2, "ancla manivela y brazo")
    check(rep["puentes"] == 2, "suelda cada pieza con un puente cilindrico")
    check(rep["finales"] == 1, "queda 1 sola pieza (islands_final = 1)")
    from scipy.spatial import cKDTree
    parts = sorted(m.split(only_watertight=False), key=lambda p: -p.area)
    t = cKDTree(np.vstack([parts[0].vertices, trimesh.sample.sample_surface(parts[0], 40000, seed=1)[0]]))
    gaps = [float(t.query(trimesh.sample.sample_surface(p, 3000, seed=1)[0])[0].min()) for p in parts[1:]]
    check(all(g < 0.01 for g in gaps), f"ninguna pieza queda flotando (huecos {[round(g, 4) for g in gaps]} m)")
    # triangulos sueltos (como image_rig.blend: 17,324 islas falsas)
    c = caja_con_piezas()
    sopa = trimesh.Trimesh(c.vertices[c.faces].reshape(-1, 3), np.arange(len(c.faces) * 3).reshape(-1, 3),
                           process=False)
    _, r2 = fix_islands(sopa)
    check(r2["vertices_soldados"] > 0 and r2["islas"] == 4 and r2["finales"] == 1,
          f"suelda triangulos sueltos antes de contar islas ({r2['islas']} islas reales)")


def test_prop_rigido():
    print("2) Prop rigido (sin esqueleto, escala real, pivote en la base, Roblox, QA)")
    from ap3d.engine import fix_islands
    m, _ = fix_islands(caja_con_piezas())     # como en el motor: islas reparadas antes de Blender
    m.apply_scale(4.25)                       # sale a tamano humano, como el bug
    glb = os.path.join(TMP, "caja.glb")
    m.export(glb)
    out = os.path.join(TMP, "caja")
    d = blender(glb, out, "--rig", "auto", "--tipo_activo", "prop_rigid", "--altura_prop", "0.40",
                "--roblox_tris", "12000")
    q = d["qa"]
    check(not q["has_rig"] and d["rig"] == "ninguno", "sin Armature")
    check(abs(q["dimensions_m"][2] - 0.40) < 0.005, f"altura 0.40 m ({q['dimensions_m'][2]})")
    check(abs(d["pivote"]["z_min"]) < 1e-3 and abs(d["pivote"]["x"]) < 1e-3 and abs(d["pivote"]["y"]) < 1e-3,
          "pivote en la base centrada")
    check(os.path.exists(os.path.join(out, "modelo_roblox.fbx")), "exporta modelo_roblox.fbx")
    check((d.get("roblox_triangulos") or 0) <= 12000, f"Roblox <= 12k triangulos ({d.get('roblox_triangulos')})")
    check(q["textures_packed"], "texturas empaquetadas")
    for k in ("islands", "non_manifold_edges", "triangles", "vertices", "dimensions_m", "has_rig",
              "textures_packed", "asset_type", "roblox_ready", "warnings", "passed"):
        check(k in q, f"QA incluye {k}")
    check(q["asset_type"] == "prop_rigid", "asset_type = prop_rigid")
    check(q["roblox_ready"], "roblox_ready = true")
    check(q["passed"], f"qa.passed = true (criticas: {q.get('critical')})")
    fbx = open(os.path.join(out, "modelo_roblox.fbx"), "rb").read()
    check(not any(n in fbx for n in (b"Suelo", b"Camara", b"Luz_")), "el FBX no trae Suelo, Camara ni Luz_*")


def test_aristas_duras():
    print("5) Hard surface: las esquinas no se redondean al reducir para Roblox")
    caja = trimesh.creation.box((0.4, 0.3, 0.4))
    for _ in range(5):
        caja = caja.subdivide()                 # ~24k triangulos, caja densa
    caja.merge_vertices()
    # ruido de 0.8 mm como una malla generada por IA (sin proteccion las
    # aristas se movian 4.1 mm; con proteccion 0 mm)
    caja.vertices += np.random.default_rng(0).normal(0, 0.0008, caja.vertices.shape)
    caja.apply_translation((0, 0, 0.2))
    glb = os.path.join(TMP, "caja_densa.glb")
    caja.export(glb)
    out = os.path.join(TMP, "caja_densa")
    d = blender(glb, out, "--rig", "auto", "--tipo_activo", "prop_rigid", "--altura_prop", "0.40",
                "--roblox_tris", "1500")
    der = d.get("roblox_deriva_aristas_m")
    check(d.get("roblox_aristas_protegidas", 0) > 0, f"aristas protegidas ({d.get('roblox_aristas_protegidas')})")
    check(der is not None and der < 0.001, f"deriva de esquinas < 1 mm ({der} m)")
    check((d.get("roblox_triangulos") or 1e9) <= 1500, f"Roblox <= 1500 ({d.get('roblox_triangulos')})")


def _denso(m, n=3):
    m = m.copy()
    for _ in range(n):
        m = m.subdivide()
    return m


def _persona():
    partes = [trimesh.creation.box((0.4, 0.22, 0.6)), trimesh.creation.icosphere(radius=0.12)]
    partes[0].apply_translation((0, 0, 1.25))
    partes[1].apply_translation((0, 0, 1.72))
    for x in (0.1, -0.1):
        p = trimesh.creation.cylinder(0.07, 0.95)
        p.apply_translation((x, 0, 0.47))
        partes.append(p)
    for x in (0.5, -0.5):
        p = trimesh.creation.cylinder(0.05, 0.75)
        p.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0)))
        p.apply_translation((x, 0, 1.48))
        partes.append(p)
    cuello = trimesh.creation.cylinder(0.05, 0.12)
    cuello.apply_translation((0, 0, 1.6))
    partes.append(cuello)
    return trimesh.util.concatenate(partes)


def test_clasificacion_auto():
    print("6) Modo Auto: figura sobre caja = prop (sin rig); busto y persona se respetan")
    caja = _denso(trimesh.creation.box((0.4, 0.4, 0.4)), 4)
    caja.apply_translation((0, 0, 0.2))
    resorte = _denso(trimesh.creation.cylinder(0.05, 0.15), 2)
    resorte.apply_translation((0, 0, 0.47))
    torso = _denso(trimesh.creation.box((0.16, 0.1, 0.2)), 3)
    torso.apply_translation((0, 0, 0.64))
    brazos = _denso(trimesh.creation.box((0.5, 0.05, 0.05)), 3)
    brazos.apply_translation((0, 0, 0.7))
    cabeza = _denso(trimesh.creation.icosphere(radius=0.08), 1)
    cabeza.apply_translation((0, 0, 0.82))
    jack = trimesh.util.concatenate([caja, resorte, torso, brazos, cabeza])
    pecho = trimesh.creation.icosphere(subdivisions=4, radius=1.0)
    pecho.apply_scale((0.22, 0.13, 0.2))
    pecho.vertices[:, 2] = np.maximum(pecho.vertices[:, 2], -0.12)     # busto cortado abajo
    pecho.apply_translation((0, 0, 0.12))
    cuello = _denso(trimesh.creation.cylinder(0.045, 0.1), 2)
    cuello.apply_translation((0, 0, 0.33))
    cab = trimesh.creation.icosphere(subdivisions=4, radius=0.11)
    cab.apply_translation((0, 0, 0.48))
    busto = trimesh.util.concatenate([pecho, cuello, cab])
    for nom, m, ok in (("jack", jack, lambda d: d["rig"] == "ninguno"),
                       ("busto", busto, lambda d: d["rig"] != "ninguno"),
                       ("persona_auto", _denso(_persona(), 2), lambda d: d["rig"] == "humanoide")):
        glb = os.path.join(TMP, nom + ".glb")
        m = m.copy()
        # glTF es Y-arriba (como sale de Hunyuan): Z de la prueba -> Y
        m.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, (1, 0, 0)))
        m.export(glb)
        d = blender(glb, os.path.join(TMP, nom), "--rig", "auto", "--tipo_activo", "auto",
                    "--roblox_tris", "0")
        c = d.get("clasificacion") or {}
        check(ok(d), f"{nom}: rig {d['rig']} (tipo {c.get('tipo')}, base_caja {c.get('base_caja')}, "
                     f"rect {c.get('rect_base')})")


def test_personaje():
    print("3) Personaje (rig Mixamo)")
    partes = [trimesh.creation.box((0.4, 0.22, 0.6)), trimesh.creation.icosphere(radius=0.12)]
    partes[0].apply_translation((0, 0, 1.25))
    partes[1].apply_translation((0, 0, 1.72))
    for x in (0.1, -0.1):
        p = trimesh.creation.cylinder(0.07, 0.95)
        p.apply_translation((x, 0, 0.47))
        partes.append(p)
    for x in (0.5, -0.5):
        p = trimesh.creation.cylinder(0.05, 0.75)
        p.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0)))
        p.apply_translation((x, 0, 1.48))
        partes.append(p)
    cuello = trimesh.creation.cylinder(0.05, 0.12)
    cuello.apply_translation((0, 0, 1.6))
    partes.append(cuello)
    glb = os.path.join(TMP, "persona.glb")
    pm = trimesh.util.concatenate(partes)
    pm.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, (1, 0, 0)))   # Y arriba
    pm.export(glb)
    out = os.path.join(TMP, "persona")
    d = blender(glb, out, "--rig", "auto", "--tipo_activo", "character", "--height", "1.75",
                "--roblox_tris", "0")
    check(d["rig"] == "humanoide" and d["qa"]["has_rig"], "rig humanoide")
    check(d.get("huesos", 0) >= 23, f"huesos Mixamo ({d.get('huesos')})")
    check(abs(d["qa"]["dimensions_m"][2] - 1.75) < 0.01, "altura 1.75 m")


def test_texturas_non_color():
    print("4) Mapas de datos en Non-Color (normal, rugosidad)")
    p = os.path.join(TMP, "caja", "modelo.blend")
    code = ("import bpy,sys;bpy.ops.wm.open_mainfile(filepath=sys.argv[-1]);bad=[]\n"
            "for m in bpy.data.materials:\n"
            " nt=getattr(m,'node_tree',None)\n"
            " if not nt: continue\n"
            " for l in nt.links:\n"
            "  n=l.from_node\n"
            "  if n.type=='TEX_IMAGE' and n.image and (l.to_node.type=='NORMAL_MAP' or l.to_socket.name in ('Roughness','Metallic')) and n.image.colorspace_settings.name!='Non-Color': bad.append(n.image.name)\n"
            "print('MALOS',len(bad))")
    s = os.path.join(TMP, "chk.py")
    open(s, "w").write(code)
    blend = os.environ.get("AP3D_BLENDER")
    cmd = ([blend, "-b", "--factory-startup", "-P", s, "--", p] if blend and os.path.exists(blend)
           else [sys.executable, s, p])
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    check("MALOS 0" in r.stdout, "ningún mapa de datos en sRGB")


if __name__ == "__main__":
    # --self-test (o sin argumentos): las 4 pruebas del estandar del pipeline
    test_islas()
    test_prop_rigido()
    test_personaje()
    test_texturas_non_color()
    if "--self-test" not in sys.argv or "--todo" in sys.argv:
        test_aristas_duras()
        test_clasificacion_auto()
    print("\n" + ("TODO OK" if not FALLAS else f"{len(FALLAS)} FALLAS: " + "; ".join(FALLAS)))
    sys.exit(1 if FALLAS else 0)
