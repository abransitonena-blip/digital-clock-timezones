#!/usr/bin/env python3
"""Modelos 3D de cables, conectores y contactos de AP Electric, con sus materiales (plásticos y cobre o aleaciones) como materiales PBR con nombre.

    python3 materiales/modelos_cables.py        (desde hardware/ap-electric)   ->   web/modelos3d/AP_CABLE_*.glb, AP_BORNE_KF128.glb, AP_CONTACTO_RELE.glb, AP_CONEXION_24V.glb
                                                                                    y materiales/materiales.json (tabla de materiales de cada parte)

Cada pieza es un conjunto de partes con material propio: se ven los hilos de cobre, el aislante, la puntera, el cuerpo plástico y el contacto metálico.
Medidas de dibujo [H] (conectores JST XH y bornes KF128 de catálogo); las aleaciones son recomendaciones de ingeniería de uso general [CG] y se deben confirmar con la hoja del fabricante de cada pieza.
Unidades: mm en el código, metros en el GLB (como las placas).
"""
import json, math, os
import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "..", "web", "modelos3d")

# ------------------------------------------------------------ materiales (apariencia) -> nombre, color base sRGB, metal, rugosidad
MAT = {
    "cobre_electrolitico": ((0.80, 0.42, 0.25), 1.0, 0.28),      # Cu ETP C11000, hilos desnudos
    "cobre_estanado":      ((0.74, 0.76, 0.78), 1.0, 0.30),      # puntera y hilos estañados
    "bronce_fosforado":    ((0.72, 0.52, 0.30), 1.0, 0.35),      # contactos a presión (CuSn5), estañado visto en el crimp
    "laton":               ((0.80, 0.65, 0.28), 1.0, 0.32),      # latón (abrazadera del borne)
    "acero_zincado":       ((0.62, 0.65, 0.70), 1.0, 0.40),      # tornillos
    "plata_oxido_estano":  ((0.86, 0.87, 0.90), 1.0, 0.18),      # AgSnO2 de los contactos del relé
    "pvc_rojo":            ((0.75, 0.08, 0.06), 0.0, 0.5), "pvc_negro": ((0.03, 0.03, 0.035), 0.0, 0.5), "pvc_azul": ((0.05, 0.25, 0.75), 0.0, 0.5),
    "pvc_blanco":          ((0.92, 0.92, 0.9), 0.0, 0.5), "pvc_amarillo": ((0.9, 0.72, 0.05), 0.0, 0.5), "pvc_verde": ((0.05, 0.55, 0.15), 0.0, 0.5),
    "pa66_blanco":         ((0.93, 0.92, 0.86), 0.0, 0.55),      # cuerpo del conector XH
    "pa66_verde":          ((0.08, 0.50, 0.22), 0.0, 0.55),      # cuerpo del borne
    "pa_collar_rojo":      ((0.78, 0.10, 0.08), 0.0, 0.45),      # collar aislante de la puntera
    "funda_pvc":           ((0.12, 0.13, 0.16), 0.0, 0.55),      # funda exterior
}


def mat(nombre, alfa=1.0):
    c, m, r = MAT[nombre]
    return PBRMaterial(name=nombre, baseColorFactor=[c[0], c[1], c[2], alfa], metallicFactor=m, roughnessFactor=r, doubleSided=True)


def pieza(malla, nombre, alfa=1.0):
    malla.visual = trimesh.visual.TextureVisuals(material=mat(nombre, alfa))
    return malla


def cil(r, p0, p1, sec=14):
    return trimesh.creation.cylinder(radius=r, segment=[list(p0), list(p1)], sections=sec)


def caja(dx, dy, dz, c):
    m = trimesh.creation.box(extents=[dx, dy, dz]); m.apply_translation(c); return m


def polilinea(pts, r, sec=10):
    return trimesh.util.concatenate([cil(r, pts[i], pts[i + 1], sec) for i in range(len(pts) - 1)])


def camino_trenzado(L, radio, paso, fase, centro=(0.0, 0.0), n=90):
    t = np.linspace(0, L, n)
    return [(x, centro[0] + radio * math.cos(2 * math.pi * x / paso + fase), centro[1] + radio * math.sin(2 * math.pi * x / paso + fase)) for x in t]


def hilos(L, rcable, nhilos, rhilo, x0, x1, camino=None, giro=0.0):
    """Haz de hilos finos de cobre (centro + corona) entre x0 y x1 siguiendo un camino de eje opcional."""
    pos = [(0.0, 0.0)] + [(2 * rhilo * 0.98 * math.cos(2 * math.pi * k / max(1, nhilos - 1)), 2 * rhilo * 0.98 * math.sin(2 * math.pi * k / max(1, nhilos - 1))) for k in range(nhilos - 1)]
    if nhilos > 7:                                          # segunda corona
        pos = [(0.0, 0.0)] + [(2 * rhilo * math.cos(2 * math.pi * k / 6), 2 * rhilo * math.sin(2 * math.pi * k / 6)) for k in range(6)] + \
              [(4 * rhilo * math.cos(2 * math.pi * k / (nhilos - 7) + 0.3), 4 * rhilo * math.sin(2 * math.pi * k / (nhilos - 7) + 0.3)) for k in range(nhilos - 7)]
    mallas = []
    for (py, pz) in pos:
        if camino is None:
            mallas.append(cil(rhilo, (x0, py, pz), (x1, py, pz), 6))
        else:
            mallas.append(polilinea([(x, y + py, z + pz) for (x, y, z) in camino if x0 <= x <= x1], rhilo, 6))
    return trimesh.util.concatenate(mallas)


def conector_xh(x, sentido, n=4, y0=0.0, z0=0.0, pasos=2.5):
    """Carcasa JST XH de n polos (PA66 blanco, dibujo [H]): 2.5 mm de paso, con las terminales de crimp (bronce fosforado estañado) asomando por detrás."""
    ancho = (n - 1) * pasos + 5.0
    cuerpo = caja(7.0, ancho, 5.75, (x + sentido * 3.5, y0, z0))
    ranuras = [caja(7.4, 1.4, 4.0, (x + sentido * 3.5, y0 + (i - (n - 1) / 2) * pasos, z0 + 1.2)) for i in range(n)]
    return cuerpo, ranuras


def cable_aplink(L=250.0, detalle=False):
    """Cable AP LINK de 4 hilos (SENSE, B, A, GND) con carcasa JST XH de 4 polos en cada extremo. A y B van trenzados (paso de 30 mm).
    detalle=True: tramo corto de 70 mm con 8 mm de hilos de cobre sin aislante a la vista (7 hilos de 0.25 mm = 22 AWG) en cada extremo."""
    esc = trimesh.Scene()
    colores = {"SENSE": "pvc_amarillo", "B": "pvc_azul", "A": "pvc_blanco", "GND": "pvc_negro"}
    ys = [(-3.75, "SENSE"), (-1.25, "B"), (1.25, "A"), (3.75, "GND")]
    x_aisl0 = (22.0 if detalle else 14.0); x_aisl1 = L - x_aisl0
    aisl = {n: [] for _, n in ys}; cobre = []; crimp = []; xh = []
    for (y, n) in ys:
        if n in ("A", "B"):
            fase = 0.0 if n == "B" else math.pi
            eje = camino_trenzado(L, 1.1, 30.0, fase)
        else:
            eje = [(x, y, 0.0) for x in np.linspace(0, L, 60)]
        aisl[n].append(polilinea([(x, yy, zz) for x, yy, zz in eje if x_aisl0 <= x <= x_aisl1], 0.72))
        if detalle:
            cobre.append(hilos(L, 0.72, 7, 0.125, 0.0, L, camino=eje))
        else:
            cobre.append(polilinea(eje, 0.34, 8))
    for (x, s) in ((0.0, 1), (L, -1)):
        cuerpo, _ = conector_xh(x, s)
        xh.append(cuerpo)
        for (y, n) in ys:
            yy = {"B": -1.25, "A": 1.25}.get(n, y)
            crimp.append(caja(6.0, 1.3, 1.9, (x + s * 3.8, yy, 0.0)))
    for n in colores:
        esc.add_geometry(pieza(trimesh.util.concatenate(aisl[n]), colores[n]), node_name="aislante_" + n)
    esc.add_geometry(pieza(trimesh.util.concatenate(cobre), "cobre_electrolitico"), node_name="cobre_hilos")
    esc.add_geometry(pieza(trimesh.util.concatenate(crimp), "bronce_fosforado"), node_name="terminales_crimp")
    esc.add_geometry(pieza(trimesh.util.concatenate(xh), "pa66_blanco"), node_name="carcasas_xh")
    return esc


def puntera(x, sentido, r_cable, color_collar="pa_collar_rojo"):
    tubo = cil(1.05, (x, 0, 0), (x + sentido * 8.0, 0, 0), 20)                       # tubo de cobre estañado de 8 mm
    collar = cil(1.5, (x + sentido * 8.0, 0, 0), (x + sentido * 14.0, 0, 0), 20)     # collar aislante
    return tubo, collar


def cable_alimentacion(L=220.0):
    esc = trimesh.Scene()
    cuerpos = {}
    for (y, color, nom) in ((-2.0, "pvc_rojo", "positivo"), (2.0, "pvc_negro", "negativo")):
        aisl = cil(1.5, (14, y, 0), (L - 14, y, 0), 24)
        hil = trimesh.util.concatenate([cil(0.16, (0, y + dy, dz), (L, y + dy, dz), 6) for (dy, dz) in
                                        [(0, 0)] + [(0.34 * math.cos(2 * math.pi * k / 6), 0.34 * math.sin(2 * math.pi * k / 6)) for k in range(6)] +
                                        [(0.66 * math.cos(2 * math.pi * k / 12 + .26), 0.66 * math.sin(2 * math.pi * k / 12 + .26)) for k in range(12)]])
        esc.add_geometry(pieza(aisl, color), node_name="aislante_" + nom)
        esc.add_geometry(pieza(hil, "cobre_estanado"), node_name="hilos_" + nom)
        for (x, s) in ((0.0, 1), (L, -1)):
            tubo = cil(1.05, (x, y, 0), (x + s * 8.0, y, 0), 20); collar = cil(1.5, (x + s * 8.0, y, 0), (x + s * 14.0, y, 0), 20)
            esc.add_geometry(pieza(tubo, "cobre_estanado"), node_name="puntera_%s_%s" % (nom, "a" if s > 0 else "b"))
            esc.add_geometry(pieza(collar, "pa_collar_rojo"), node_name="collar_%s_%s" % (nom, "a" if s > 0 else "b"))
    return esc


def borne_kf128(polos=3, paso=5.08):
    esc = trimesh.Scene()
    ancho = polos * paso
    cuerpo = caja(ancho, 10.0, 10.5, (ancho / 2, 0, 5.25))
    esc.add_geometry(pieza(cuerpo, "pa66_verde"), node_name="cuerpo_pa66")
    tornillos, abrazaderas, pines = [], [], []
    for i in range(polos):
        x = (i + 0.5) * paso
        tornillos.append(cil(1.25, (x, 0, 7.5), (x, 0, 11.4), 16))                   # tornillo de cabeza
        tornillos.append(cil(1.7, (x, 0, 10.9), (x, 0, 11.4), 16))
        abrazaderas.append(caja(3.8, 3.6, 0.8, (x, 0, 6.2)))                         # abrazadera de latón estañado
        abrazaderas.append(caja(3.8, 0.8, 3.0, (x, -1.8, 4.8)))
        pines.append(cil(0.45, (x, 3.0, 0.0), (x, 3.0, -3.5), 10)); pines.append(cil(0.45, (x, 3.0, 0.0), (x, 3.0, 4.5), 10))   # patas a la placa
    esc.add_geometry(pieza(trimesh.util.concatenate(tornillos), "acero_zincado"), node_name="tornillos")
    esc.add_geometry(pieza(trimesh.util.concatenate(abrazaderas), "laton"), node_name="abrazaderas_laton")
    esc.add_geometry(pieza(trimesh.util.concatenate(pines), "cobre_estanado"), node_name="patas_cobre_estanado")
    return esc


def contacto_rele():
    esc = trimesh.Scene()
    fijo = caja(10.0, 3.0, 0.8, (6.0, 0, 0.4)); soporte = caja(3.0, 3.0, 9.0, (10.0, 0, 4.5))
    mov = caja(14.0, 3.0, 0.25, (7.0, 0, 6.5))                                       # lámina móvil
    b1 = cil(1.9, (4.0, 0, 0.8), (4.0, 0, 1.6), 24); b2 = cil(1.9, (4.0, 0, 6.2), (4.0, 0, 5.5), 24)
    esc.add_geometry(pieza(trimesh.util.concatenate([fijo, soporte]), "cobre_electrolitico"), node_name="terminal_fijo_cobre")
    esc.add_geometry(pieza(mov, "bronce_fosforado"), node_name="lamina_movil_bronce")
    esc.add_geometry(pieza(trimesh.util.concatenate([b1, b2]), "plata_oxido_estano"), node_name="contactos_AgSnO2")
    return esc


def conexion_24v():
    """Un borne KF128 de 3 polos con dos cables de 24 V y puntera metidos en los polos 1 y 3."""
    esc = trimesh.Scene()
    b = borne_kf128()
    for n, g in b.geometry.items():
        esc.add_geometry(g, node_name="borne_" + n)
    for (px, color, nom) in ((0.5 * 5.08, "pvc_rojo", "positivo"), (2.5 * 5.08, "pvc_negro", "negativo")):
        tubo = cil(1.05, (px, -1.0, 4.8), (px, -9.0, 4.8), 20); collar = cil(1.5, (px, -9.0, 4.8), (px, -15.0, 4.8), 20)
        aisl = cil(1.5, (px, -15.0, 4.8), (px, -60.0, 4.8), 24)
        esc.add_geometry(pieza(tubo, "cobre_estanado"), node_name="puntera_" + nom)
        esc.add_geometry(pieza(collar, "pa_collar_rojo"), node_name="collar_" + nom)
        esc.add_geometry(pieza(aisl, color), node_name="aislante_" + nom)
    return esc


def exportar(esc, nombre):
    esc = esc.copy()
    esc.apply_scale(0.001)
    esc.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0]))   # z arriba (STL/CAD) -> y arriba (glTF)
    ruta = os.path.join(SALIDA, nombre + ".glb")
    esc.export(ruta)
    return os.path.getsize(ruta)


TABLA = [
    # parte, material recomendado (producción), alternativa, por qué, (dato general [CG])
    ("Hilos del cable AP LINK y de 24 V", "Cobre electrolítico ETP C11000 estañado, trenzado fino (clase 5)", "Cobre desnudo; CCA (aluminio recubierto de cobre) NO recomendado",
     "Mejor conductividad (100 % IACS) y el estañado evita la corrosión en bornas y soldadura; el trenzado fino aguanta flexión y vibración"),
    ("Aislante del cable", "PVC 70-80 °C (tableros) o XLPE 90-125 °C (cerca de calor)", "Silicona o TPE para temperatura alta o cables que se mueven",
     "PVC: barato y autoextinguible; XLPE: más temperatura y menos deformación; confirmar la clase de ignifugación de la hoja del fabricante"),
    ("Punta del cable de 24 V (puntera)", "Tubo de cobre electrolítico estañado, collar de PA o PP", "Latón estañado (más barato, peor conductividad)",
     "Cobre estañado: baja resistencia de contacto y no se oxida; la puntera evita que los hilos se abran bajo el tornillo"),
    ("Terminales de crimp del conector XH (contactos a presión)", "Bronce fosforado CuSn5 (C51000) estañado", "Latón CuZn30 (menos resorte, más barato); CuBe C17200 (resorte premium, trato especial por el berilio)",
     "Un contacto a presión necesita elasticidad: el bronce fosforado conserva la fuerza de contacto con los ciclos de conexión (conductividad 15-20 % IACS, suficiente para pocos mA del AP LINK)"),
    ("Cuerpo plástico del conector XH y del borne", "PA66 con fibra de vidrio (V-0, 105-125 °C)", "PBT-GF; PA46 si se suelda con reflujo sin plomo",
     "Resiste la temperatura de soldadura y es autoextinguible (UL 94 V-0); el PA absorbe humedad y cambia medidas: tolerancias abiertas en el prototipo"),
    ("Abrazadera del borne de tornillo", "Latón CuZn39Pb3 (C38500) estañado o niquelado", "Cobre estañado para más corriente; CuCrZr (C18150) para bornes de 30 A o más",
     "El latón se mecaniza fácil y aguanta el apriete del tornillo; el cobre y el CuCrZr bajan la resistencia y el calentamiento cuando la corriente sube"),
    ("Tornillo del borne", "Acero zincado pasivado (o acero inoxidable A2)", "Latón niquelado (menos par, más conductividad)", "Resistencia mecánica al apriete; la corriente va por la abrazadera, no por el tornillo"),
    ("Contactos del relé (los de la placa RL4 y del 7R Tour)", "AgSnO2 (plata-óxido de estaño) sobre lámina de bronce o CuSn6", "AgNi 90/10 para cargas resistivas pequeñas; AgCdO ya no se usa (cadmio)",
     "AgSnO2 resiste el desgaste y la soldadura del arco en cargas con motor o lámparas; es el que traen los relés de potencia (confirmar con la hoja del relé elegido)"),
    ("Pistas y planos de la placa", "Cobre 2 oz (70 µm) con acabado HASL sin plomo o ENIG", "Cobre 3-4 oz para 10 A o más (placa especial)",
     "El diseño actual usa pistas de +V de 0.8 mm con fusible de 3 A: no se ha medido el calentamiento"),
    ("Caja y tapa (prototipo impreso)", "PETG (interior) o ASA (exterior, resiste la luz del sol)", "PA12 por sinterizado (MJF) para series cortas; PC/ABS inyectado en producción",
     "PETG: fácil de imprimir y tenaz; ASA no amarillea; en producción la caja se inyecta (PC/ABS V-0) y se necesita molde"),
    ("Soporte de riel generativo", "PETG o PA12-CF (fibra de carbono corta) impreso", "Aluminio mecanizado o fundido si la carga lo exige",
     "Forma optimizada por topología; la rigidez real de una pieza impresa depende de la orientación de las capas: hay que probarla"),
]


def escribir_tabla():
    tabla = [{"parte": p, "material_recomendado": m, "alternativas": a, "por_que": q, "origen": "[CG] conocimiento general de ingeniería; confirmar con la hoja del fabricante de cada pieza"} for p, m, a, q in TABLA]
    with open(os.path.join(AQUI, "materiales.json"), "w", encoding="utf-8") as f:
        json.dump(tabla, f, ensure_ascii=False, indent=1)
    return tabla


if __name__ == "__main__":
    os.makedirs(SALIDA, exist_ok=True)
    for nombre, f in (("AP_CABLE_APLINK", cable_aplink), ("AP_CABLE_APLINK_DETALLE", lambda: cable_aplink(70.0, True)), ("AP_CABLE_24V", cable_alimentacion), ("AP_BORNE_KF128", borne_kf128), ("AP_CONTACTO_RELE", contacto_rele), ("AP_CONEXION_24V", conexion_24v)):
        esc = f()
        print("%-18s %6.0f KB  partes: %s" % (nombre, exportar(esc, nombre) / 1024, ", ".join(esc.geometry.keys())))
    print(len(escribir_tabla()), "filas en materiales.json")
