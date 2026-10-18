"""Fotos de estilo rústico (banco de taller de madera, latón envejecido, luz cálida) del PLC AP Rack con su cable de alimentación unido a la placa.

  blender -b -P blender/render_rustico.py -- --salida blender/renders/rustico
  python blender/render_rustico.py --solo cable_union --muestras 128      (con el módulo bpy)

Escenas: banco_general, cable_union (el conector de 24 V en la placa), plano_cenital (todo sobre la mesa visto desde arriba), detalle_cobre (hilos y punteras),
         caja_madera (la caja con tapa de madera y tornillos de latón), tablero_fuente (fuente de 24 V sobre su riel y el cable hacia el PLC).
Después: python3 blender/foto_final.py (viñeta, grano y tono cálido) -> *_foto.jpg.
La fuente de 24 V, los cables y las herramientas son piezas ILUSTRATIVAS genéricas (no son un producto ni una marca); las placas y la caja son los modelos de este repositorio.
"""
import math, os, random, sys
import bpy
from mathutils import Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import render_blender as R  # noqa: E402

RAIZ = R.RAIZ
M3D = os.path.join(RAIZ, "web", "modelos3d")
GEN = os.path.join(RAIZ, "generativo", "salida")


PLC = bool(os.environ.get("APPLC"))                  # APPLC=1: el AP PLC C24 con su caja en vez del AP Rack 16


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    o = {"salida": os.path.join(AQUI, "renders", "rustico"), "solo": "", "muestras": "96", "res": "1600x1000", "rehacer": "no"}
    for i in range(0, len(a) - 1, 2):
        k = a[i].lstrip("-")
        if k in o: o[k] = a[i + 1]
    o["muestras"] = int(o["muestras"])
    return o


# ------------------------------------------------------------------ materiales rústicos
def mat_madera(nombre, base=(0.30, 0.17, 0.08), claro=(0.55, 0.36, 0.18), semilla=0.0, anillos=18.0, escala_veta=(0.05, 1.0, 1.0)):
    m = bpy.data.materials.new(nombre); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links
    p = N["Principled BSDF"]
    co = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = escala_veta; mp.inputs["Location"].default_value = (semilla, semilla * 0.7, semilla * 0.3)
    L.new(co.outputs["Object"], mp.inputs["Vector"])
    ruido = N.new("ShaderNodeTexNoise"); ruido.inputs["Scale"].default_value = 3.0; ruido.inputs["Detail"].default_value = 6.0
    L.new(mp.outputs["Vector"], ruido.inputs["Vector"])
    onda = N.new("ShaderNodeTexWave"); onda.wave_type = "BANDS"; onda.bands_direction = "Y"; onda.inputs["Scale"].default_value = anillos * 5.0
    onda.inputs["Distortion"].default_value = 3.5; onda.inputs["Detail"].default_value = 4.0; onda.inputs["Detail Scale"].default_value = 1.6
    L.new(mp.outputs["Vector"], onda.inputs["Vector"])
    mezcla = N.new("ShaderNodeMixRGB"); mezcla.blend_type = "MULTIPLY"; mezcla.inputs["Fac"].default_value = 0.55
    L.new(onda.outputs["Color"], mezcla.inputs["Color1"]); L.new(ruido.outputs["Color"], mezcla.inputs["Color2"])
    rampa = N.new("ShaderNodeValToRGB"); rampa.color_ramp.elements[0].color = (*base, 1); rampa.color_ramp.elements[1].color = (*claro, 1)
    rampa.color_ramp.elements[0].position = 0.25; rampa.color_ramp.elements[1].position = 0.8
    L.new(mezcla.outputs["Color"], rampa.inputs["Fac"]); L.new(rampa.outputs["Color"], p.inputs["Base Color"])
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.35; bump.inputs["Distance"].default_value = 0.0006
    L.new(onda.outputs["Fac"], bump.inputs["Height"]); L.new(bump.outputs["Normal"], p.inputs["Normal"])
    p.inputs["Roughness"].default_value = 0.62
    return m


def mat_metal_viejo(nombre, rgb, rug_min=0.28, rug_max=0.6, metal=1.0, escala=60.0):
    m = bpy.data.materials.new(nombre); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Metallic"].default_value = metal
    co = N.new("ShaderNodeTexCoord"); ruido = N.new("ShaderNodeTexNoise"); ruido.inputs["Scale"].default_value = escala; ruido.inputs["Detail"].default_value = 8.0
    L.new(co.outputs["Object"], ruido.inputs["Vector"])
    rampa = N.new("ShaderNodeMapRange"); rampa.inputs["To Min"].default_value = rug_min; rampa.inputs["To Max"].default_value = rug_max
    L.new(ruido.outputs["Fac"], rampa.inputs["Value"]); L.new(rampa.outputs["Result"], p.inputs["Roughness"])
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.15; bump.inputs["Distance"].default_value = 0.0002
    L.new(ruido.outputs["Fac"], bump.inputs["Height"]); L.new(bump.outputs["Normal"], p.inputs["Normal"])
    return m


def mat_simple(nombre, rgb, rug=0.5, metal=0.0):
    return R.material(nombre, rgb, rug, metal)


# ------------------------------------------------------------------ piezas del taller
def caja_prisma(nombre, dx, dy, dz, centro, mat, bisel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=centro); o = bpy.context.active_object; o.scale = (dx / 2, dy / 2, dz / 2); o.name = nombre
    bpy.ops.object.transform_apply(scale=True)
    if bisel > 0:
        b = o.modifiers.new("bisel", "BEVEL"); b.width = bisel; b.segments = 2
    o.data.materials.append(mat)
    return o


def cil(nombre, r, h, centro, mat, rot=(0, 0, 0), seg=32):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=centro, rotation=rot, vertices=seg); o = bpy.context.active_object; o.name = nombre
    o.data.materials.append(mat)
    return o


def mesa(zsup=0.0, ancho=1.3, fondo=0.9):
    """Banco de taller: tablones de madera con juntas, desiguales y teñidos distinto."""
    random.seed(4)
    n = 7; w = fondo / n
    for i in range(n):
        tint = random.uniform(-0.04, 0.04)
        m = mat_madera("tablon%d" % i, base=(0.26 + tint, 0.15 + tint / 2, 0.07), claro=(0.50 + tint, 0.32 + tint / 2, 0.15), semilla=i * 3.7, anillos=random.uniform(12, 24))
        caja_prisma("tablon%d" % i, ancho, w - 0.004, 0.035, (0, -fondo / 2 + w * (i + 0.5), zsup - 0.0175 - random.uniform(0, 0.0012)), m, bisel=0.0015)


def luz_calida(c, r, tam=1.0):
    def area(nom, pos, energia, color, size):
        d = bpy.data.lights.new(nom, "AREA"); d.energy = energia; d.color = color; d.size = size
        o = bpy.data.objects.new(nom, d); bpy.context.collection.objects.link(o); o.location = c + Vector(pos) * r
        t = o.constraints.new("TRACK_TO"); t.target = R.vacio(c); t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    area("lampara", (-1.4, -1.0, 1.7), 95 * r * r * tam, (1.0, 0.70, 0.40), r * 1.4)          # lámpara de taller (cálida)
    area("ventana", (1.9, -0.6, 1.0), 22 * r * r * tam, (0.62, 0.78, 1.0), r * 2.2)            # luz fría de ventana, tenue
    area("contra", (0.2, 1.8, 1.2), 40 * r * r * tam, (1.0, 0.62, 0.30), r * 1.0)


def camara_dof(c, r, azim, elev, dist, foco_mm=55, fstop=3.2, objetivo=None):
    R.camara(c, r, azim, elev, dist, foco=foco_mm)
    cam = bpy.context.scene.camera
    cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = fstop
    cam.data.dof.focus_object = objetivo if objetivo is not None else R.vacio(c)


def mundo_taller():
    w = bpy.context.scene.world; bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.05, 0.035, 0.025, 1); bg.inputs[1].default_value = 0.5


# ------------------------------------------------------------------ el PLC con la placa y el cable de 24 V
def catmull(pts, n=14):
    """Curva suave (Catmull-Rom) por los puntos de control: el cable cae y se apoya como uno real."""
    P = [pts[0]] + list(pts) + [pts[-1]]; out = []
    for k in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[k - 1], P[k], P[k + 1], P[k + 2]
        for j in range(n):
            t = j / n; t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(pts[-1])
    return out


def cable_poly(puntos, radio, mat, nombre="cable"):
    cu = bpy.data.curves.new(nombre, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = radio; cu.bevel_resolution = 4; cu.use_fill_caps = True
    sp = cu.splines.new("POLY"); sp.points.add(len(puntos) - 1)
    for pt, v in zip(sp.points, puntos): pt.co = (v.x, v.y, v.z, 1.0)
    ob = bpy.data.objects.new(nombre, cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(mat)
    return ob


class Taller:
    """Todo lo que lleva la mesa: la caja con la placa, la fuente de 24 V, el cable, el carrete, las herramientas."""
    def __init__(self, o):
        R.limpiar(o["res"], o["muestras"], "CYCLES"); mundo_taller()
        mesa(0.0)
        self.latón = mat_metal_viejo("laton_viejo", (0.62, 0.43, 0.16), 0.30, 0.62, 1.0, 90.0)
        self.acero = mat_metal_viejo("acero", (0.56, 0.58, 0.60), 0.28, 0.55, 1.0, 140.0)
        self.cobre_est = mat_metal_viejo("cobre_estanado", (0.74, 0.76, 0.78), 0.22, 0.4, 1.0, 200.0)
        self.pa = mat_simple("pa66", (0.90, 0.88, 0.80), 0.55)
        self.rojo = mat_simple("pvc_rojo", (0.55, 0.02, 0.015), 0.45); self.negro = mat_simple("pvc_negro", (0.012, 0.012, 0.014), 0.5)
        self.collar = mat_simple("collar", (0.62, 0.05, 0.04), 0.45)
        self.caja, self.placa, self.j1 = self.plc()
        self.fuente()
        self.cable_24v()

    def plc(self):
        caja = R.importar_stl(os.path.join(RAIZ, "accesorios", "stl", "caja_plc.stl" if PLC else "caja_rack.stl")); R.pintar(caja, "caja")
        caja.data.materials.clear(); caja.data.materials.append(mat_simple("caja_negra", (0.02, 0.02, 0.024), 0.6))
        bpy.context.view_layer.update()
        mnc, mxc = R.caja_limites([caja]); cx, cy = (mnc.x + mxc.x) / 2, (mnc.y + mxc.y) / 2
        objs = R.importar_glb(os.path.join(M3D, "AP_PLC_C24.glb" if PLC else "AP_RACK16.glb"))
        mn, mx = R.caja_limites([x for x in objs if x.type == "MESH"])
        d = Vector((cx - (mn.x + mx.x) / 2, cy - (mn.y + mx.y) / 2, 0.0090 - mn.z))
        for x in objs:
            if x.parent is None: x.location += d
        bpy.context.view_layer.update()
        verde = bpy.data.materials.new("led_on"); verde.use_nodes = True; pn = verde.node_tree.nodes["Principled BSDF"]
        pn.inputs["Base Color"].default_value = (0.2, 1, 0.35, 1); pn.inputs["Emission Color"].default_value = (0.2, 1, 0.35, 1); pn.inputs["Emission Strength"].default_value = 80
        for x in objs:
            n = x.name.split(".")[0]
            if x.type == "MESH" and n.startswith("DL") and n[2:].isdigit() and int(n[2:]) in ({1, 3, 4, 7, 10, 12} if PLC else {1, 2, 5, 8, 9, 12, 16}):
                x.data = x.data.copy(); x.data.materials.clear(); x.data.materials.append(verde)
        j6 = [x for x in objs if x.name.split(".")[0] == ("J8" if PLC else "J6")][0]
        o6 = j6.matrix_world.translation.copy()                                  # J6 está en (36, 6.4) mm de la placa; J1 en (11, 9)
        j1 = o6 + Vector(((11.0 - 36.0) / 1000.0, -(9.0 - 6.4) / 1000.0, 0.0))
        self.todo_placa = objs
        return caja, objs, j1

    def fuente(self):
        """Fuente genérica de 24 V (ilustrativa): caja de aluminio con tapa de bornas y una placa de datos."""
        c = Vector((self.caja.location.x - (0.235 if PLC else 0.215), self.caja.location.y + 0.01, 0.0))
        gris = mat_metal_viejo("fuente_gris", (0.42, 0.44, 0.46), 0.35, 0.6, 0.9, 50.0)
        cuerpo = caja_prisma("fuente", 0.090, 0.100, 0.045, c + Vector((0, 0, 0.0225)), gris, bisel=0.002)
        placa = caja_prisma("placa_datos", 0.050, 0.030, 0.0006, c + Vector((0.008, -0.012, 0.0453)), mat_simple("etiqueta", (0.82, 0.78, 0.62), 0.7))
        bpy.ops.object.text_add(location=c + Vector((-0.012, -0.0045, 0.0457))); t = bpy.context.active_object
        t.data.body = "24 V CC"; t.data.size = 0.0075; t.data.extrude = 0.0001; t.data.materials.append(mat_simple("tinta", (0.03, 0.02, 0.01), 0.6))
        # bornas de tornillo (arriba, al lado cercano a la placa): + y -
        self.bornas = []
        for k, mt in ((0, self.rojo), (1, self.negro)):
            bx = c + Vector((0.026 + 0.0, 0.0, 0.0)) + Vector((0.0, 0.0, 0.0))
            pos = c + Vector((0.029, 0.017 - 0.014 * k * 2 + 0.014, 0.0466))
            caja_prisma("borne_f%d" % k, 0.0082, 0.0120, 0.0095, c + Vector((0.0460, 0.0265 - k * 0.030, 0.0325)), mat_simple("borne_pa", (0.12, 0.13, 0.14), 0.5), bisel=0.0005)
            cil("tornillo_f%d" % k, 0.0021, 0.0016, c + Vector((0.0460, 0.0265 - k * 0.030, 0.0381)), self.latón, seg=18)
            self.bornas.append(c + Vector((0.0510, 0.0265 - k * 0.030, 0.0325)))
        cil("led_fuente", 0.0022, 0.0012, c + Vector((0.020, 0.030, 0.0456)), mat_simple("led_f", (0.1, 0.9, 0.2), 0.3), seg=14)
        self.fuente_c = c

    def cable_24v(self):
        """Cable de 24 V: conector VH en la placa (J1) -> sobre la pared de la caja -> mesa -> puntera en la borna de la fuente."""
        j1 = self.j1; w_x = self.caja.location.x
        p0 = j1 + Vector((0.00198, 0, 0.0))
        caja_prisma("cabecera_VH", 0.0100, 0.0082, 0.0090, p0 + Vector((0, 0, 0.0045)), self.pa, bisel=0.0004)
        caja_prisma("conector_VH", 0.0108, 0.0080, 0.0125, p0 + Vector((0, 0, 0.0090 + 0.0045)), self.pa, bisel=0.0005)
        for k, (mt, pb) in enumerate(((self.rojo, self.bornas[0]), (self.negro, self.bornas[1]))):
            inicio = j1 + Vector((0.00396 * k, 0, 0.0152))
            borna_entrada = pb + Vector((0.0, 0.0, 0.0))
            lado = 1.0 - 2.0 * k
            ctrl = [inicio, inicio + Vector((0, 0, 0.012)),
                    inicio + Vector((-0.012, 0.004 * lado, 0.032)),
                    Vector((self.caja.location.x - (0.110 if PLC else 0.098), inicio.y + 0.012 * lado, 0.050)),
                    Vector((self.caja.location.x - (0.130 if PLC else 0.118), inicio.y + 0.020 * lado - 0.015 * k, 0.012)),
                    Vector((pb.x + 0.034, pb.y + 0.012 * lado, 0.0035)),
                    Vector((pb.x + 0.016, pb.y, 0.0045)), pb + Vector((0.008, 0, 0))]
            ruta = catmull(ctrl, 10)
            cable_poly(ruta, 0.0016, mt, "cable_24v_%d" % k)
            # puntera con collar justo antes de la borna
            cil("puntera_%d" % k, 0.00105, 0.008, pb + Vector((0.0045, 0, 0)), self.cobre_est, rot=(0, math.pi / 2, 0), seg=20)
            cil("collar_%d" % k, 0.0016, 0.006, pb + Vector((0.0115, 0, 0)), self.collar, rot=(0, math.pi / 2, 0), seg=20)

    def utiles(self, rng=None):
        rng = rng or random.Random(11)
        base = Vector((self.caja.location.x, self.caja.location.y, 0.0))
        # carrete de cable rojo
        c = base + Vector((-0.02, 0.215, 0.0))
        pl = mat_simple("carrete", (0.05, 0.05, 0.055), 0.6)
        cil("carrete_a", 0.045, 0.003, c + Vector((0, 0, 0.0015)), pl); cil("carrete_b", 0.045, 0.003, c + Vector((0, 0, 0.0555)), pl)
        cil("carrete_n", 0.022, 0.052, c + Vector((0, 0, 0.0285)), pl)
        hilo = mat_simple("hilo_carrete", (0.5, 0.02, 0.02), 0.4)
        cil("carrete_hilo", 0.036, 0.048, c + Vector((0, 0, 0.0285)), hilo, seg=64)
        # destornillador
        d0 = base + Vector((0.10, -0.205, 0.0))
        cil("mango", 0.0105, 0.095, d0 + Vector((0, 0, 0.0105)), mat_simple("mango", (0.85, 0.32, 0.03), 0.4), rot=(0, math.pi / 2, math.radians(8)))
        cil("varilla", 0.0028, 0.10, d0 + Vector((-0.095, -0.0075, 0.0105)), self.acero, rot=(0, math.pi / 2, math.radians(8)))
        # punteras y tornillos sueltos
        for i in range(7):
            x = base.x - 0.16 + rng.uniform(0, 0.1); y = base.y - 0.17 + rng.uniform(-0.03, 0.03)
            cil("p%d" % i, 0.0010, 0.008, Vector((x, y, 0.0011)), self.cobre_est, rot=(0, math.pi / 2, rng.uniform(0, 3.14)), seg=14)
            cil("pc%d" % i, 0.0015, 0.006, Vector((x + 0.007, y, 0.0016)), self.collar, rot=(0, math.pi / 2, rng.uniform(0, 3.14)), seg=14)
        for i in range(8):
            x = base.x + 0.11 + rng.uniform(0, 0.12); y = base.y + 0.13 + rng.uniform(-0.04, 0.04)
            cil("t%d" % i, 0.0016, 0.012, Vector((x, y, 0.0016)), self.latón, rot=(0, math.pi / 2, rng.uniform(0, 6.28)), seg=14)
            cil("th%d" % i, 0.0032, 0.0016, Vector((x - 0.0068, y, 0.0016)), self.latón, rot=(0, math.pi / 2, 0), seg=14)
        # etiqueta de papel kraft con el nombre
        e = caja_prisma("etiqueta_kraft", 0.060, 0.034, 0.0008, base + Vector((0.22, 0.01, 0.0004)), mat_simple("kraft", (0.55, 0.40, 0.24), 0.8))
        e.rotation_euler[2] = math.radians(-12)
        bpy.ops.object.text_add(location=base + Vector((0.195, 0.012, 0.0010))); t = bpy.context.active_object; t.rotation_euler[2] = math.radians(-12)
        t.data.body = "AP PLC C24" if PLC else "AP RACK 16"; t.data.size = 0.0075; t.data.extrude = 0.00005; t.data.materials.append(mat_simple("tinta2", (0.08, 0.05, 0.03), 0.7))

    def objetos_enfoque(self):
        return [self.caja] + [x for x in self.todo_placa if x.type == "MESH"]


def render_escena(o, nombre, cam_target, azim, elev, dist, foco=55, fstop=3.2, con_utiles=True, extra=None, objetivo=None):
    t = Taller(o)
    if con_utiles: t.utiles()
    objs = t.objetos_enfoque()
    c = cam_target(t) if callable(cam_target) else cam_target
    r = c[1]; centro = c[0]
    luz_calida(centro, max(r, 0.12) * 1.1)
    camara_dof(centro, r, azim, elev, dist, foco_mm=foco, fstop=fstop, objetivo=objetivo(t) if callable(objetivo) else None)
    bpy.context.scene.render.filepath = os.path.join(o["salida"], nombre + ".jpg")
    bpy.ops.render.render(write_still=True)
    print("render:", nombre)


def piso_banco():
    pass


if __name__ == "__main__":
    o = args(); os.makedirs(o["salida"], exist_ok=True); hechos = []
    def quiere(n): return (not o["solo"] or o["solo"] in n) and (o["rehacer"] == "si" or not os.path.exists(os.path.join(o["salida"], n + ".jpg")))
    if quiere("banco_general"):
        render_escena(o, "banco_general", lambda t: (Vector((t.caja.location.x - 0.075, t.caja.location.y + 0.03, 0.02)), 0.17), -28, 33, 3.0, foco=45, fstop=5.0); hechos.append("banco_general")
    if quiere("cable_union"):
        render_escena(o, "cable_union", lambda t: (t.j1 + Vector((-0.02, 0.0, 0.012)), 0.07), 125, 55, 3.0, foco=60, fstop=16.0, con_utiles=False,
                      objetivo=lambda t: (lambda e: (setattr(e, "location", t.j1 + Vector((0.002, 0, 0.012))), e)[1])(bpy.data.objects.new("foco", None))); hechos.append("cable_union")
    if quiere("plano_cenital"):
        render_escena(o, "plano_cenital", lambda t: (Vector((t.caja.location.x - 0.03, t.caja.location.y + 0.03, 0.0)), 0.30), -2, 86, 3.6, foco=50, fstop=8.0); hechos.append("plano_cenital")
    if quiere("tablero_fuente"):
        render_escena(o, "tablero_fuente", lambda t: (t.fuente_c + Vector((0.03, 0.0, 0.02)), 0.09), -42, 38, 3.2, foco=50, fstop=14.0,
                      objetivo=lambda t: (lambda e: (setattr(e, "location", t.bornas[0]), e)[1])(bpy.data.objects.new("foco2", None))); hechos.append("tablero_fuente")
    print("listo: %s" % ", ".join(hechos))
