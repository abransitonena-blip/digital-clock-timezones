"""Exporta los modelos 3D de AP Electric a otros formatos (carpeta formatos/).

  piezas imprimibles (accesorios/stl)  ->  3MF, OBJ, FBX  (el STL ya está en accesorios/stl)
  placas AP Rack y caja (web/modelos3d) ->  FBX y .blend  (el GLB ya está en web/modelos3d; el STEP sale de KiCad con tools/exportar_formatos.sh)
  escena completa                       ->  AP_Electric_piezas.blend (las 29 piezas ordenadas en una mesa, con materiales)

Uso (desde hardware/ap-electric):   blender -b -P formatos/exportar_formatos.py     o     python formatos/exportar_formatos.py   (con: pip install bpy==4.2.0 trimesh numpy)
Son modelos de diseño: nada está fabricado ni impreso. Las unidades de los archivos de piezas son milímetros (3MF, OBJ) o metros (FBX, .blend).
"""
import glob, math, os, sys
import bpy

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, ".."))
sys.path.insert(0, os.path.join(RAIZ, "blender"))
import render_blender as R  # noqa: E402  (materiales y utilidades de importación)


def dir_(*p):
    d = os.path.join(AQUI, *p); os.makedirs(d, exist_ok=True); return d


def piezas():
    try:
        import trimesh
    except ImportError:
        trimesh = None
    n = 0
    for f in sorted(glob.glob(os.path.join(RAIZ, "accesorios", "stl", "*.stl"))):
        nombre = os.path.splitext(os.path.basename(f))[0]
        if trimesh is not None:
            m = trimesh.load(f)
            m.export(os.path.join(dir_("3mf"), nombre + ".3mf"))             # milímetros
            m.export(os.path.join(dir_("obj"), nombre + ".obj"))             # milímetros
        bpy.ops.wm.read_factory_settings(use_empty=True)
        o = R.importar_stl(f); R.pintar(o, nombre)
        bpy.ops.export_scene.fbx(filepath=os.path.join(dir_("fbx"), nombre + ".fbx"), use_selection=False, apply_scale_options="FBX_SCALE_ALL")
        n += 1
    return n


def placas():
    n = 0
    for f in sorted(glob.glob(os.path.join(RAIZ, "web", "modelos3d", "*.glb"))):
        nombre = os.path.splitext(os.path.basename(f))[0]
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=f)
        bpy.ops.export_scene.fbx(filepath=os.path.join(dir_("fbx"), nombre + ".fbx"))
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(dir_("blend"), nombre + ".blend"), compress=True)
        n += 1
    return n


def escena():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    fs = sorted(glob.glob(os.path.join(RAIZ, "accesorios", "stl", "*.stl")))
    col = bpy.data.collections.new("piezas_AP"); bpy.context.scene.collection.children.link(col)
    cols = 6; paso = 0.20
    for i, f in enumerate(fs):
        nombre = os.path.splitext(os.path.basename(f))[0]
        o = R.importar_stl(f); R.pintar(o, nombre); o.name = nombre
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
        o.location.x = (i % cols) * paso; o.location.y = -(i // cols) * paso
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(dir_("blend"), "AP_Electric_piezas.blend"), compress=True)
    return len(fs)


if __name__ == "__main__":
    a = piezas(); b = placas(); c = escena()
    print("listo: %d piezas (3MF/OBJ/FBX), %d placas (FBX/.blend) y la escena con %d piezas" % (a, b, c))
