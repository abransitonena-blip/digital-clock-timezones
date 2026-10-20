"""Ambiente de casa para la web: una lámpara de mesa encendida, un apagador de pared y la caja AP Home (cerebro) con su cable, sobre una mesa de madera, de noche.

    /tmp/claude-0/bpyenv/bin/python blender/render_casa.py -- --res 1600x1000 --muestras 96 --salida blender/renders/casa

Reutiliza materiales y ayudas de render_rustico.py. Todo es ilustrativo: la lámpara, el apagador y la pared son objetos genéricos de ambientación;
la caja AP Home es un prisma con LED y botón, no el modelo de la placa. Nada fabricado.
"""
import math, os, sys
import bpy
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_blender as R  # noqa: E402
import render_rustico as T  # noqa: E402


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    o = {"salida": os.path.join(T.AQUI, "renders", "casa"), "res": "1600x1000", "muestras": "96"}
    for i in range(0, len(a) - 1, 2):
        k = a[i].lstrip("-")
        if k in o: o[k] = a[i + 1]
    o["muestras"] = int(o["muestras"])
    return o


def emisor(nombre, rgb, fuerza):
    m = bpy.data.materials.new(nombre); m.use_nodes = True; n = m.node_tree.nodes["Principled BSDF"]
    n.inputs["Base Color"].default_value = (*rgb, 1); n.inputs["Emission Color"].default_value = (*rgb, 1); n.inputs["Emission Strength"].default_value = fuerza
    return m


def escena(o):
    R.limpiar(o["res"], o["muestras"], "CYCLES")
    w = bpy.context.scene.world; bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.02, 0.025, 0.04, 1); bg.inputs[1].default_value = 0.35
    T.mesa(0.0, ancho=1.6, fondo=0.7)
    yp = 0.36                                                                    # pared al fondo de la mesa
    yeso = T.mat_simple("yeso", (0.80, 0.74, 0.64), 0.92)
    T.caja_prisma("pared", 2.6, 0.04, 1.4, (0, yp + 0.02, 0.62), yeso)
    T.caja_prisma("zoclo", 2.6, 0.02, 0.07, (0, yp - 0.01, 0.0), T.mat_simple("zoclo", (0.35, 0.22, 0.12), 0.6))
    # apagador de pared (placa blanca y balancín)
    blanco = T.mat_simple("plastico_blanco", (0.9, 0.9, 0.86), 0.35)
    T.caja_prisma("placa_apagador", 0.078, 0.008, 0.125, (0.30, yp - 0.004, 0.36), blanco, bisel=0.002)
    T.caja_prisma("balancin", 0.026, 0.008, 0.044, (0.30, yp - 0.011, 0.36), blanco, bisel=0.003)
    # lámpara de mesa (base de cerámica, vástago y pantalla encendida)
    cer = T.mat_simple("ceramica", (0.78, 0.45, 0.28), 0.4)
    T.cil("lampara_base", 0.05, 0.03, (-0.38, 0.12, 0.015), cer)
    T.cil("lampara_vastago", 0.012, 0.20, (-0.38, 0.12, 0.13), cer)
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.115, radius2=0.075, depth=0.15, location=(-0.38, 0.12, 0.30)); pan = bpy.context.active_object; pan.name = "pantalla"
    pan.data.materials.append(emisor("pantalla_luz", (1.0, 0.62, 0.30), 7.0))
    for q in pan.data.polygons: q.use_smooth = True
    # luz de la lámpara (cálida)
    d = bpy.data.lights.new("foco_lampara", "POINT"); d.energy = 55; d.color = (1.0, 0.6, 0.28); d.shadow_soft_size = 0.05
    l = bpy.data.objects.new("foco_lampara", d); bpy.context.collection.objects.link(l); l.location = (-0.38, 0.12, 0.29)
    # caja AP Home (cerebro): caja blanca con LED verde, botón y un cable de baja tensión hacia la lámpara
    caja = T.caja_prisma("home_caja", 0.085, 0.055, 0.03, (0.02, 0.05, 0.015), blanco, bisel=0.004)
    T.cil("home_boton", 0.0075, 0.004, (0.045, 0.045, 0.032), T.mat_simple("boton", (0.15, 0.15, 0.16), 0.5))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0032, location=(-0.012, 0.045, 0.031)); led = bpy.context.active_object; led.name = "home_led"
    led.data.materials.append(emisor("led_verde", (0.2, 1.0, 0.4), 60.0))
    T.caja_prisma("home_etiqueta", 0.04, 0.012, 0.0006, (0.012, 0.027, 0.0304), T.mat_simple("etiq", (0.12, 0.12, 0.14), 0.5))
    negro = T.mat_simple("cable_blanco", (0.82, 0.82, 0.78), 0.5)
    ruta = T.catmull([Vector(p) for p in [(-0.02, 0.05, 0.012), (-0.10, 0.06, 0.004), (-0.20, 0.03, 0.004), (-0.30, 0.08, 0.004), (-0.36, 0.11, 0.008)]], 10)
    T.cable_poly(ruta, 0.0016, negro, "cable_baja_tension")
    # una planta chica y un libro, para que se sienta cuarto
    T.cil("maceta", 0.04, 0.07, (0.55, 0.18, 0.035), T.mat_simple("barro", (0.55, 0.30, 0.18), 0.8))
    verde = T.mat_simple("hoja", (0.12, 0.35, 0.15), 0.6)
    for k in range(7):
        a = k * math.tau / 7
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, location=(0.55 + 0.04 * math.cos(a), 0.18 + 0.04 * math.sin(a), 0.11 + 0.012 * (k % 3))); h = bpy.context.active_object
        h.scale = (1, 0.35, 1.9); h.rotation_euler = (0.3 * math.cos(a), 0.3 * math.sin(a), a); h.data.materials.append(verde)
    T.caja_prisma("libro", 0.16, 0.11, 0.03, (-0.65, 0.20, 0.015), T.mat_simple("libro", (0.18, 0.28, 0.42), 0.6), bisel=0.002)
    c = Vector((-0.12, 0.10, 0.17))
    # luz de relleno fría (ventana) y cámara
    d2 = bpy.data.lights.new("ventana", "AREA"); d2.energy = 14; d2.color = (0.6, 0.75, 1.0); d2.size = 1.2
    l2 = bpy.data.objects.new("ventana", d2); bpy.context.collection.objects.link(l2); l2.location = (1.4, -0.9, 0.9)
    t = l2.constraints.new("TRACK_TO"); t.target = R.vacio(c); t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    T.camara_dof(c, 0.42, -18, 16, 2.7, foco_mm=42, fstop=4.0, objetivo=R.vacio(Vector((0.02, 0.05, 0.03))))
    os.makedirs(o["salida"], exist_ok=True)
    bpy.context.scene.render.filepath = os.path.join(o["salida"], "casa_ambiente.jpg")
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    escena(args())
