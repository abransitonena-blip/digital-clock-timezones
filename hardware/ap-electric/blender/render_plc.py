"""Renders con Blender del PLC AP Rack con sus salidas encendidas y cableadas, de los cables y contactos con sus materiales, y de las piezas de diseño generativo.

  blender -b -P blender/render_plc.py -- --salida blender/renders/plc
  python blender/render_plc.py --solo salidas --muestras 96       (con el módulo bpy)

Escenas: plc_salidas (el módulo con las LED de salida encendidas y cables con puntera en las bornas), cable_aplink, conexion_24v, contacto_rele,
         generativo_soporte (soporte de riel híbrido sobre el riel), generativo_tapa (tapa ventilada por mapa de calor).
Requisitos: haber generado antes los GLB de materiales/ y las piezas de generativo/ (python3 materiales/modelos_cables.py; python3 generativo/generar.py).
Son renders de diseño: no hay cables ni piezas fabricados. Los colores de las piezas de las placas son de apariencia.
"""
import math, os, sys
import bpy
from mathutils import Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import render_blender as R  # noqa: E402

RAIZ = R.RAIZ
M3D = os.path.join(RAIZ, "web", "modelos3d")
GEN = os.path.join(RAIZ, "generativo", "salida")


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    o = {"salida": os.path.join(AQUI, "renders", "plc"), "solo": "", "muestras": "64", "res": "1600x1000", "rehacer": "no"}
    for i in range(0, len(a) - 1, 2):
        k = a[i].lstrip("-")
        if k in o: o[k] = a[i + 1]
    o["muestras"] = int(o["muestras"])
    return o


def mat_emision(nombre, rgb, fuerza):
    m = bpy.data.materials.new(nombre); m.use_nodes = True
    n = m.node_tree.nodes; p = n["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Emission Color"].default_value = (*rgb, 1); p.inputs["Emission Strength"].default_value = fuerza
    return m


def nombre_base(o):
    return o.name.split(".")[0]


def cable_curva(puntos, radio, material, nombre="cable"):
    cu = bpy.data.curves.new(nombre, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = radio; cu.bevel_resolution = 5; cu.use_fill_caps = True
    sp = cu.splines.new("BEZIER"); sp.bezier_points.add(len(puntos) - 1)
    for bp, (co, hl, hr) in zip(sp.bezier_points, puntos):
        bp.co = co; bp.handle_left = hl; bp.handle_right = hr
    ob = bpy.data.objects.new(nombre, cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(material)
    return ob


def escena_plc(o):
    sc = R.limpiar(o["res"], o["muestras"], "CYCLES")
    caja = R.importar_stl(os.path.join(RAIZ, "accesorios", "stl", "caja_rack.stl")); R.pintar(caja, "caja")
    tapa = R.importar_stl(os.path.join(GEN, "tapa_ventilada_generativa.stl")); R.pintar(tapa, "tapa")
    bpy.context.view_layer.update()
    mnc, mxc = R.caja_limites([caja]); cx, cy = (mnc.x + mxc.x) / 2, (mnc.y + mxc.y) / 2
    objs = R.importar_glb(os.path.join(M3D, "AP_RACK16.glb"))
    mn, mx = R.caja_limites([x for x in objs if x.type == "MESH"])
    d = Vector((cx - (mn.x + mx.x) / 2, cy - (mn.y + mx.y) / 2, 0.0090 - mn.z))
    for x in objs:
        if x.parent is None: x.location += d
    tapa.location.z += (mxc.z - mnc.z) + 0.060; tapa.location.x += 0.085; tapa.location.y -= 0.050; tapa.rotation_euler = (0, 0, math.radians(-7))   # tapa levantada y corrida: se ven las bornas, los cables y las LED
    bpy.context.view_layer.update()
    por_nombre = {nombre_base(x): x for x in objs}
    centro_placa = Vector(((mn.x + mx.x) / 2 + d.x, (mn.y + mx.y) / 2 + d.y, 0))
    # LED de salida: encendidas Q1 Q2 Q5 Q8 Q9 Q12 Q16 (patrón de ejemplo)
    on = {1, 2, 5, 8, 9, 12, 16}
    verde = mat_emision("led_on", (0.2, 1.0, 0.35), 60); apagado = mat_emision("led_off", (0.05, 0.12, 0.06), 0.0)
    for k in range(1, 17):
        ob = por_nombre.get("DL%d" % k)
        if ob is not None and ob.type == "MESH":
            ob.data = ob.data.copy(); ob.data.materials.clear(); ob.data.materials.append(verde if k in on else apagado)
    # cables con puntera en las bornas J6, J8, J10, J12 (salida impar y +V)
    rojo = R.material("pvc_rojo", (0.62, 0.03, 0.02), 0.5, 0.0); azul = R.material("pvc_azul", (0.03, 0.15, 0.55), 0.5, 0.0)
    cobre = R.material("cu_estanado", (0.74, 0.76, 0.78), 0.3, 1.0); collar = R.material("collar", (0.7, 0.06, 0.05), 0.45, 0.0)
    n_cables = 0
    for j, colores in ((6, (azul, rojo)), (8, (azul, rojo)), (10, (azul, rojo)), (12, (azul, rojo))):
        b = por_nombre.get("J%d" % j)
        if b is None: continue
        mn_b, mx_b = R.caja_limites([b] + [h for h in b.children_recursive if h.type == "MESH"])
        ancho_x = mx_b.x - mn_b.x
        saliente = -1.0 if ((mn_b.y + mx_b.y) / 2) < centro_placa.y else 1.0
        y_entrada = (mn_b.y if saliente < 0 else mx_b.y)
        for k, mt in ((0, colores[0]), (1, colores[1])):             # polo 1 = salida, polo 2 = +V
            x = mn_b.x + (k + 0.5) / 3.0 * ancho_x
            z = mn_b.z + (mx_b.z - mn_b.z) * 0.42
            p0 = Vector((x, y_entrada, z))
            tubo = bpy.data.objects.new("puntera", bpy.data.meshes.new("puntera")); bpy.context.collection.objects.link(tubo)
            bpy.ops.mesh.primitive_cylinder_add(radius=0.00105, depth=0.008, rotation=(math.pi / 2, 0, 0), location=p0 + Vector((0, saliente * 0.004, 0))); t = bpy.context.active_object; t.data.materials.append(cobre)
            bpy.ops.mesh.primitive_cylinder_add(radius=0.0015, depth=0.006, rotation=(math.pi / 2, 0, 0), location=p0 + Vector((0, saliente * 0.011, 0))); c = bpy.context.active_object; c.data.materials.append(collar)
            fin = p0 + Vector((0.02 * (k - 0.5), saliente * 0.20, -(z - 0.0005)))
            pts = [(p0 + Vector((0, saliente * 0.014, 0)), p0 + Vector((0, saliente * 0.010, 0)), p0 + Vector((0, saliente * 0.04, 0.0))),
                   (p0 + Vector((0.01 * (k - 0.5), saliente * 0.09, 0.025)), p0 + Vector((0, saliente * 0.06, 0.03)), p0 + Vector((0, saliente * 0.12, 0.02))),
                   (fin, fin + Vector((0, -saliente * 0.05, 0.01)), fin + Vector((0, saliente * 0.05, 0)))]
            cable_curva(pts, 0.0015, mt, "cable_%d_%d" % (j, k)); n_cables += 1
    todo = [caja, tapa] + [x for x in objs if x.type == "MESH"]
    return todo, n_cables


def escena_glb(archivo, o, dist=3.4, azim=-30, elev=28, escala=1.0):
    R.limpiar(o["res"], o["muestras"], "CYCLES")
    objs = R.importar_glb(os.path.join(M3D, archivo))
    R.ancla(objs)
    return [x for x in objs if x.type == "MESH"]


def escena_generativo_soporte(o):
    R.limpiar(o["res"], o["muestras"], "CYCLES")
    gen = R.importar_stl(os.path.join(GEN, "soporte_generativa.stl")); par = R.importar_stl(os.path.join(GEN, "soporte_parametrica.stl"))
    for ob, nom, col in ((gen, "gen", (0.33, 0.35, 0.42)), (par, "par", (0.91, 0.36, 0.02))):
        ob.data.materials.clear(); ob.data.materials.append(R.material(nom, col, 0.45, 0.0))
        bpy.context.view_layer.objects.active = ob; ob.select_set(True)
        try:
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(32))
        except Exception:
            pass
    objs = [gen, par]
    R.ancla(objs)
    return objs


def render(o, nombre, objs, dist=4.2, azim=-30, elev=28, fondo_luz=None):
    ruta = os.path.join(o["salida"], nombre + ".jpg")
    R.escena(objs, ruta, dist=dist, azim=azim, elev=elev)


if __name__ == "__main__":
    o = args(); os.makedirs(o["salida"], exist_ok=True); hechos = []
    def quiere(n): return (not o["solo"] or o["solo"] in n) and (o["rehacer"] == "si" or not os.path.exists(os.path.join(o["salida"], n + ".jpg")))
    if quiere("plc_salidas"):
        objs, n = escena_plc(o); render(o, "plc_salidas", objs, dist=3.6, azim=-25, elev=30); hechos.append("plc_salidas")
    for n, archivo, dist in (("cable_aplink", "AP_CABLE_APLINK.glb", 3.0), ("cable_aplink_detalle", "AP_CABLE_APLINK_DETALLE.glb", 2.3), ("conexion_24v", "AP_CONEXION_24V.glb", 4.2), ("contacto_rele", "AP_CONTACTO_RELE.glb", 5.2), ("cable_24v", "AP_CABLE_24V.glb", 3.0)):
        if quiere(n):
            objs = escena_glb(archivo, o); render(o, n, objs, dist=dist, azim=-35, elev=30); hechos.append(n)
    if quiere("generativo_soporte"):
        objs = escena_generativo_soporte(o); render(o, "generativo_soporte", objs, dist=4.2, azim=-38, elev=24); hechos.append("generativo_soporte")
    if quiere("generativo_tapa"):
        R.limpiar(o["res"], o["muestras"], "CYCLES")
        t = R.importar_stl(os.path.join(GEN, "tapa_ventilada_generativa.stl")); R.pintar(t, "tapa"); R.ancla([t])
        t.location.z += 0.02; t.rotation_euler = (math.radians(-18), 0, 0)
        render(o, "generativo_tapa", [t], dist=3.0, azim=-20, elev=48); hechos.append("generativo_tapa")
    print("listo: %s" % ", ".join(hechos))
