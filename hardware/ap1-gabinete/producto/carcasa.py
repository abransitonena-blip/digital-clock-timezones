"""AP ELECTRIC · carcasa de riel DIN para cada producto, generada a partir de su placa.

Perfil escalonado de tablero (como los equipos modulares de riel DIN): hombros a 27 mm sobre la placa con los
enchufes de tornillo encima de cada conector, frente central a 46 mm con el panel oscuro, el logo AP en relieve,
LED de estado, botones y la etiqueta del producto. Traba naranja para el riel de 35 mm.

    python3 carcasa.py placas.json SALIDA_DIR      (placas.json: conectores de cada placa, de extraer.py en KiCad)

Salidas por producto: <p>.wrl (modelo con colores en unidades de KiCad, para el render), <p>_cuerpo.stl y
<p>_frente.stl (piezas para imprimir en PETG / ASA o como modelo para el molde).
"""
import json, math, os, sys
import numpy as np
import trimesh
from manifold3d import Manifold, CrossSection, FillRule
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

ZB, Z1, Z2 = -9.0, 27.0, 46.0        # espalda (riel), hombros y frente, en mm sobre la cara de la placa
COL = {                               # color, especular, brillo, transparencia
    "cuerpo": ((0.86, 0.865, 0.85), 0.25, 0.25, 0.0),     # RAL 7035
    "frente": ((0.11, 0.12, 0.14), 0.35, 0.5, 0.0),       # panel antracita
    "naranja": ((1.0, 0.42, 0.04), 0.3, 0.35, 0.0),       # color AP
    "blanco": ((0.97, 0.97, 0.97), 0.2, 0.3, 0.0),
    "gris": ((0.55, 0.57, 0.6), 0.2, 0.3, 0.0),
    "oscuro": ((0.05, 0.05, 0.06), 0.1, 0.2, 0.0),
    "texto": ((0.22, 0.23, 0.25), 0.1, 0.2, 0.0),
    "metal": ((0.78, 0.79, 0.8), 0.9, 0.8, 0.0),
    "riel": ((0.72, 0.74, 0.76), 0.8, 0.6, 0.0),
    "verde": ((0.15, 0.95, 0.35), 0.8, 0.9, 0.0),
    "rojo": ((1.0, 0.12, 0.08), 0.8, 0.9, 0.0),
    "azul": ((0.15, 0.55, 1.0), 0.8, 0.9, 0.0),
    "amarillo": ((1.0, 0.82, 0.05), 0.3, 0.4, 0.0),
    "red": ((0.42, 0.44, 0.47), 0.2, 0.3, 0.0),           # enchufes de red: gris oscuro
}

def caja(x0, y0, z0, x1, y1, z1):
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))

def cilindro(x, y, z0, h, r, seg=40):
    return Manifold.cylinder(h, r, r, seg).translate((x, y, z0))

def perfil(puntos, u0, u1):
    """Polígono en (v, z) extruido a lo largo de u."""
    cs = CrossSection([puntos], FillRule.EvenOdd)
    m = cs.extrude(u1 - u0)                       # en (v, z, u)
    return m.warp(lambda p: (p[2] + u0, p[0], p[1])) if False else _vzu(m, u0)

def _vzu(m, u0):
    mesh = m.to_mesh()
    v = np.array(mesh.vert_properties)[:, :3]
    t = np.array(mesh.tri_verts)
    nv = np.column_stack([v[:, 2] + u0, v[:, 0], v[:, 1]])     # (v, z, u) -> (u, v, z): rotación (det = +1)
    from manifold3d import Mesh
    return Manifold(Mesh(vert_properties=nv.astype(np.float32), tri_verts=t.astype(np.uint32)))

FUENTE = FontProperties(family="DejaVu Sans", weight="bold")
FUENTE_N = FontProperties(family="DejaVu Sans", weight="normal")

def texto(s, alto, u, v, z, h=0.5, ancla="izq", negrita=True, ancho_max=None):
    """Texto en relieve sobre un plano z, leído de frente (v crece hacia abajo en la placa)."""
    tp = TextPath((0, 0), s, size=1.0, prop=FUENTE if negrita else FUENTE_N)
    ext = tp.get_extents()
    esc = alto / 0.73                               # alto de las mayúsculas ~ 0.73 del tamaño
    if ancho_max and ext.width * esc > ancho_max:
        esc = ancho_max / ext.width
    polys = [np.array(p) * esc for p in tp.to_polygons(closed_only=True) if len(p) >= 3]
    if not polys:
        return Manifold()
    ancho = ext.width * esc
    dx = {"izq": 0, "centro": -ancho / 2, "der": -ancho}[ancla] - ext.x0 * esc
    cs = CrossSection([p.tolist() for p in polys], FillRule.EvenOdd)
    m = cs.extrude(h).to_mesh()
    vv = np.array(m.vert_properties)[:, :3]
    t = np.array(m.tri_verts)
    nv = np.column_stack([u + dx + vv[:, 0], v - vv[:, 1], z + vv[:, 2]])   # espejo en v: se invierten las caras
    from manifold3d import Mesh
    return Manifold(Mesh(vert_properties=nv.astype(np.float32), tri_verts=t[:, ::-1].astype(np.uint32)))

def redondo(u0, v0, u1, v1, r, seg=10):
    """Rectángulo con esquinas redondeadas (puntos en u, v)."""
    pts = []
    for (cu, cv, a0) in [(u1 - r, v0 + r, -90), (u1 - r, v1 - r, 0), (u0 + r, v1 - r, 90), (u0 + r, v0 + r, 180)]:
        for k in range(seg + 1):
            a = math.radians(a0 + 90 * k / seg)
            pts.append((cu + r * math.cos(a), cv + r * math.sin(a)))
    return pts

def losa(pts, z0, h):
    return CrossSection([pts], FillRule.EvenOdd).extrude(h).translate((0, 0, z0))

def triangulo(u, v, z, lado):
    """Triángulo amarillo de advertencia de tensión peligrosa, con el rayo."""
    h = lado * math.sqrt(3) / 2
    tri = CrossSection([[(u - lado / 2, v + h / 2), (u + lado / 2, v + h / 2), (u, v - h / 2)]], FillRule.EvenOdd)
    r = lado * 0.07
    borde = tri.offset(-r * 0.0, join_type=None) if False else tri
    amar = borde.extrude(0.4).translate((0, 0, z))
    s = lado / 10.0                                   # rayo
    rayo = CrossSection([[(u + 0.6 * s, v - 2.2 * s), (u - 1.4 * s, v + 0.9 * s), (u - 0.1 * s, v + 0.9 * s), (u - 0.9 * s, v + 3.4 * s),
                          (u + 1.5 * s, v - 0.2 * s), (u + 0.2 * s, v - 0.2 * s), (u + 1.1 * s, v - 2.2 * s)]], FillRule.EvenOdd)
    contorno = tri - tri.offset(-0.55 * s, CrossSection.JoinType.Miter if hasattr(CrossSection, "JoinType") else 0)
    return amar, (rayo.extrude(0.5).translate((0, 0, z)) + contorno.extrude(0.5).translate((0, 0, z)))

def construir(cfg, placa):
    """Devuelve {color: Manifold} en coordenadas locales (u a lo largo del riel, v hacia abajo, z hacia el frente)."""
    P = {k: Manifold() for k in COL}
    def add(c, m): P[c] = P[c] + m
    Wu, Hv = cfg["Wu"], cfg["Hv"]
    con = cfg["conectores"]
    arriba = [c for c in con if c["lado"] == "arriba"]
    abajo = [c for c in con if c["lado"] == "abajo"]
    n0 = max([c["v1"] for c in arriba] + [4.0]) + 2.2
    n1 = min([c["v0"] for c in abajo] + [Hv - 4.0]) - 2.2
    if n1 - n0 > 36:                              # frente de 36 mm como máximo: toda la familia se ve pareja
        cm = (n0 + n1) / 2; n0, n1 = cm - 18, cm + 18
    vc = (n0 + n1) / 2
    v0, v1 = min(-2.5, vc - 45), max(Hv + 2.5, vc + 45)
    u0, u1 = -2.5, Wu + 2.5
    ch = 1.2
    # cuerpo: perfil escalonado con chaflanes, extruido a lo largo del riel
    pf = [(v0, ZB + ch), (v0 + ch, ZB), (v1 - ch, ZB), (v1, ZB + ch), (v1, Z1 - ch), (v1 - ch, Z1),
          (n1 + 0.0, Z1), (n1, Z2 - 2.0), (n1 - 2.0, Z2), (n0 + 2.0, Z2), (n0, Z2 - 2.0), (n0, Z1), (v0 + ch, Z1), (v0, Z1 - ch)]
    cuerpo = perfil(pf, u0, u1)
    # ranura del riel en la espalda y tapas laterales con nervaduras de ventilación
    cuerpo = cuerpo - caja(u0 - 1, vc - 18.0, ZB - 1, u1 + 1, vc + 18.0, ZB + 1.2)
    for k in range(7):
        z = 2.0 + k * 3.2
        for uu in (u0, u1):
            cuerpo = cuerpo - caja(uu - 0.6, n0 + 4, z, uu + 0.6, n1 - 4, z + 1.4)
    # bolsillos de los enchufes (y del puerto AP LINK)
    for c in con:
        cuerpo = cuerpo - caja(c["u0"] - 0.4, c["v0"] - 0.4, 0, c["u1"] + 0.4, c["v1"] + 0.4, Z1 + 1)
    # panel frontal antracita (membrana), un poco hundido en el frente
    m = 1.6
    panel = losa(redondo(u0 + m, n0 + m, u1 - m, n1 - m, 1.8), Z2 - 0.3, 0.7)
    cuerpo = cuerpo - losa(redondo(u0 + m - 0.2, n0 + m - 0.2, u1 - m + 0.2, n1 - m + 0.2, 2.0), Z2 - 0.3, 1.0)
    add("cuerpo", cuerpo)
    add("frente", panel)
    zf = Z2 + 0.4
    # logo AP: cuadro naranja redondeado con las letras en blanco
    hn = n1 - n0
    lg = min(13.0, hn * 0.42)
    lu, lv = u0 + m + 4.5, n0 + m + 4.0
    add("naranja", losa(redondo(lu, lv, lu + lg, lv + lg, lg * 0.22), zf, 0.6))
    add("blanco", texto("AP", lg * 0.48, lu + lg / 2, lv + lg * 0.74, zf + 0.6, 0.35, "centro"))
    add("blanco", texto("ELECTRIC", lg * 0.13, lu + lg / 2, lv + lg + 3.0, zf, 0.35, "centro"))
    # nombre y descripción
    tu = lu + lg + 5
    add("blanco", texto(cfg["nombre"], min(6.0, hn * 0.17), tu, lv + lg * 0.5, zf, 0.4))
    add("gris", texto(cfg["sub"], min(2.6, hn * 0.075), tu, lv + lg * 0.5 + 5.0, zf, 0.35, negrita=False))
    # LED y botones al lado derecho del frente
    x = u1 - m - 5.5
    yl = n1 - m - 9.5 if cfg.get("leds_abajo") else n0 + m + 6.5
    for (txt, col) in reversed(cfg["leds"]):
        add(col, cilindro(x, yl, zf - 0.4, 1.3, 1.55))
        add("frente", cilindro(x, yl, zf - 0.4, 0.6, 2.4) - cilindro(x, yl, zf - 1, 3, 1.55))
        add("gris", texto(txt, 1.5, x, yl + 5.0, zf, 0.3, "centro", ancho_max=7))
        x -= 7.5
    yb = n1 - m - 8.0
    x = u1 - m - 6.5
    for txt in reversed(cfg.get("botones", [])):
        add("gris", cilindro(x, yb, zf - 0.4, 1.6, 3.0) + cilindro(x, yb, zf - 0.4, 1.9, 2.6))
        add("gris", texto(txt, 1.4, x, yb + 5.8, zf, 0.3, "centro"))
        x -= 10
    if cfg.get("usb"):
        uu = x - 6
        add("oscuro", losa(redondo(uu - 4.6, yb - 1.7, uu + 4.6, yb + 1.7, 1.6), zf - 0.3, 0.75))
        add("gris", texto("USB-C", 1.4, uu, yb + 5.8, zf, 0.3, "centro"))
    if cfg.get("red"):
        a, b = triangulo(tu + 3.5, n1 - m - 7.0, zf, 7.0)
        add("amarillo", a); add("oscuro", b)
        add("amarillo", texto(cfg["red"], 1.9, tu + 9, n1 - m - 6.0, zf, 0.3, negrita=True))
    # etiqueta blanca para escribir (como en los tableros)
    if cfg.get("etiqueta", True):
        eu0 = tu + (25 if cfg.get("red") else 0)
        add("blanco", losa(redondo(eu0, n1 - m - 4.5, eu0 + 26, n1 - m - 1.2, 0.6), zf, 0.25))
    # enchufes de tornillo sobre cada conector (y AP LINK como zócalo)
    for c in con:
        cu0, cv0, cu1, cv1 = c["u0"], c["v0"], c["u1"], c["v1"]
        afuera = -1 if c["lado"] == "arriba" else 1
        if c["tipo"] == "link":
            add("oscuro", caja(cu0, cv0, 0, cu1, cv1, Z1 - 0.8))
            add("naranja", caja(cu0 - 0.4, cv0 - 0.4, Z1 - 0.8, cu1 + 0.4, cv1 + 0.4, Z1 - 0.5) - caja(cu0 + 0.8, cv0 + 0.8, Z1 - 1, cu1 - 0.8, cv1 - 0.8, Z1))
            add("texto", texto(c["txt"], 1.6, (cu0 + cu1) / 2, (cv1 + 3.4) if afuera < 0 else (cv0 - 1.4), Z1, 0.25, "centro", ancho_max=cu1 - cu0 + 6))
            continue
        col = "red" if c["tipo"] == "red" else "naranja"
        zt = Z1 + 6.0
        add(col, caja(cu0, cv0, 2.0, cu1, cv1, zt) - caja(cu0 - 1, (cv1 if afuera < 0 else cv0) - 1.6 * (-afuera) - 10 * (afuera > 0), zt - 2.2,
                                                         cu1 + 1, (cv0 + 0.0) if afuera < 0 else cv1 + 1, zt + 1)
            if False else caja(cu0, cv0, 2.0, cu1, cv1, zt))
        n = max(1, c["n"]); paso = (cu1 - cu0) / n
        for k in range(n):
            pu = cu0 + paso * (k + 0.5)
            sv = (cv0 + cv1) / 2 - afuera * 1.2
            r = min(1.6, paso * 0.33)
            add("metal", cilindro(pu, sv, zt - 0.6, 1.0, r))
            add("oscuro", caja(pu - r * 0.9, sv - 0.25, zt + 0.1, pu + r * 0.9, sv + 0.25, zt + 0.5))
            # entrada del cable, en la cara de afuera
            fv = cv0 if afuera < 0 else cv1
            add("oscuro", caja(pu - paso * 0.3, fv - 0.5, zt - 4.6, pu + paso * 0.3, fv + 0.5, zt - 1.6))
        # leyenda en el hombro, del lado del frente
        lv = (cv1 + 3.6) if afuera < 0 else (cv0 - 1.6)
        add("texto", texto(c["txt"], 1.7, (cu0 + cu1) / 2, lv, Z1, 0.25, "centro", ancho_max=cu1 - cu0 + 4))
    # traba del riel (naranja) abajo y la marca del fabricante en el hombro
    uc = (u0 + u1) / 2
    add("naranja", caja(uc - 5, v1 - 3, ZB + 0.6, uc + 5, v1 + 2.5, ZB + 5.2) - caja(uc - 2, v1 - 0.5, ZB, uc + 2, v1 + 1.5, ZB + 7))
    return P, (u0, v0, u1, v1, vc)

def riel(u0, u1, vc):
    pf = [(vc - 17.5, ZB - 1.0), (vc - 13.5, ZB - 1.0), (vc - 13.5, ZB - 7.5), (vc + 13.5, ZB - 7.5), (vc + 13.5, ZB - 1.0),
          (vc + 17.5, ZB - 1.0), (vc + 17.5, ZB), (vc + 12.5, ZB), (vc + 12.5, ZB - 6.5), (vc - 12.5, ZB - 6.5), (vc - 12.5, ZB), (vc - 17.5, ZB)]
    return perfil(pf, u0, u1)

def a_trimesh(m):
    mm = m.to_mesh()
    v = np.array(mm.vert_properties)[:, :3]
    return trimesh.Trimesh(v, np.array(mm.tri_verts), process=True)

def escribir_wrl(partes, T, ruta):
    """VRML 2 con un Shape por color; T = matriz 4x4 de local a coordenadas de KiCad (mm); KiCad usa 0.1 pulgada."""
    with open(ruta, "w") as f:
        f.write("#VRML V2.0 utf8\n")
        for nombre, m in partes.items():
            if m.is_empty():
                continue
            t = a_trimesh(m)
            t.apply_transform(T)
            (r, g, b), es, br, tr = COL[nombre]
            pts = " ".join("%.4f %.4f %.4f" % tuple(p / 2.54) for p in t.vertices)
            idx = " ".join("%d %d %d -1" % tuple(fc) for fc in t.faces)
            f.write("Shape { appearance Appearance { material Material { diffuseColor %.3f %.3f %.3f specularColor %.2f %.2f %.2f "
                    "ambientIntensity 0.3 shininess %.2f transparency %.2f } }\n" % (r, g, b, es, es, es, br, tr))
            f.write(" geometry IndexedFaceSet { creaseAngle 0.6 coord Coordinate { point [ %s ] }\n coordIndex [ %s ] } }\n" % (pts, idx))

PRODUCTOS = {
    "uno": dict(nombre="AP UNO", sub="PLC · IoT · 4 canales 20 A · DMX / Modbus", rot=0,
                leds=[("PWR", "verde"), ("RUN", "verde"), ("RED", "azul"), ("FALLA", "rojo")], botones=["MODO", "RESET"], usb=True,
                txt={"J12": "S1  S2", "J13": "S3  S4", "J14": "E1  E2", "J15": "E3  E4", "J5": "FOCO 1", "J8": "FOCO 2", "J3": "+V",
                     "J1": "12-24 V", "J4": "CH1-CH4", "J16": "RS-485", "J11": "AP LINK"}),
    "foco127": dict(nombre="AP FOCO 127", sub="2 focos LED de corriente constante · 2 × 500 mA", rot=0, red="127-220 V~",
                    leds=[("PWR", "verde"), ("F1", "verde"), ("F2", "verde"), ("FALLA", "rojo")],
                    txt={"J1": "LINK IN", "J2": "LINK OUT", "J4": "FOCO 1", "J5": "FOCO 2", "J6": "L   N"}),
    "red4": dict(nombre="AP RED 4", sub="4 salidas de 10 A · 250 V~", rot=90, red="250 V~", leds_abajo=True, etiqueta=False,
                 leds=[("1", "verde"), ("2", "verde"), ("3", "verde"), ("4", "verde")],
                 txt={"J1": "IN", "J2": "OUT", "J3": "24 V", "J4": "1", "J5": "2", "J6": "3", "J7": "4"}),
}

def preparar(nombre, placa):
    cfg = dict(PRODUCTOS[nombre])
    x0, y0, w, h = placa["x0"], placa["y0"], placa["w"], placa["h"]
    if cfg["rot"] == 90:                          # el borde derecho de la placa (bornes de red) queda abajo
        Wu, Hv = h, w
        loc = lambda x, y: (y0 + h - y, x - x0)
        T = np.array([[0, 1, 0, x0], [-1, 0, 0, -(y0 + h)], [0, 0, 1, 0], [0, 0, 0, 1]], float)   # (u, v) -> (x, -y)
        # x = x0 + v ; y = y0 + h - u  ->  X = x, Y = -y
        T = np.array([[0, 1, 0, x0], [1, 0, 0, -(y0 + h)], [0, 0, 1, 0], [0, 0, 0, 1]], float)
    else:
        Wu, Hv = w, h
        loc = lambda x, y: (x - x0, y - y0)
        T = np.array([[1, 0, 0, x0], [0, -1, 0, -y0], [0, 0, 1, 0], [0, 0, 0, 1]], float)
    con = []
    for f in placa["fp"]:
        if f["ref"] not in cfg["txt"]:
            continue
        a = loc(f["bx"][0], f["bx"][1]); b = loc(f["bx"][2], f["bx"][3])
        u0, u1 = sorted((a[0], b[0])); v0, v1 = sorted((a[1], b[1]))
        link = "SM04B" in f["fpid"]
        red = "MKDS" in f["fpid"]
        if link:
            u0, u1 = (u0 + u1) / 2 - 4.5, (u0 + u1) / 2 + 4.5
            v0, v1 = (v0 + v1) / 2 - 2.6, (v0 + v1) / 2 + 2.6
        n = len(f["pth"]) or 4
        con.append(dict(ref=f["ref"], u0=u0, v0=v0, u1=u1, v1=v1, n=n, tipo="link" if link else "red" if red else "bajo",
                        lado="arriba" if (v0 + v1) / 2 < Hv / 2 else "abajo", txt=cfg["txt"][f["ref"]]))
    cfg.update(Wu=Wu, Hv=Hv, conectores=con)
    return cfg, T

if __name__ == "__main__":
    placas = json.load(open(sys.argv[1]))
    sal = sys.argv[2]
    os.makedirs(sal, exist_ok=True)
    hechos = {}
    for nombre in sys.argv[3:] or PRODUCTOS:
        cfg, T = preparar(nombre, placas[nombre])
        P, (u0, v0, u1, v1, vc) = construir(cfg, placas[nombre])
        escribir_wrl(P, T, os.path.join(sal, "caja_%s.wrl" % nombre))
        escribir_wrl({"riel": riel(u0 - 40, u1 + 40, vc)}, T, os.path.join(sal, "riel_%s.wrl" % nombre))
        cuerpo = a_trimesh(P["cuerpo"]); cuerpo.export(os.path.join(sal, "%s_cuerpo.stl" % nombre))
        hechos[nombre] = (P, u0, u1, vc)
        print(nombre, "carcasa %.1f x %.1f x %.1f mm" % (u1 - u0, v1 - v0, Z2 - ZB), "conectores", len(cfg["conectores"]),
              "estanca" if cuerpo.is_watertight else "NO estanca")

    # familia en un riel: AP RED 4 | AP UNO | AP FOCO 127, alineados con la placa del AP UNO (x0, y0)
    if all(k in hechos for k in ("uno", "red4", "foco127")):
        x0, y0 = placas["uno"]["x0"], placas["uno"]["y0"]
        vcu = hechos["uno"][3]
        partes, u = {}, None
        orden = ["red4", "uno", "foco127"]
        pos = {}
        cur = hechos["uno"][1]                    # el AP UNO queda en su lugar; los demás, a los lados
        pos["uno"] = 0.0
        pos["red4"] = hechos["uno"][1] - 0.6 - hechos["red4"][2]
        pos["foco127"] = hechos["uno"][2] + 0.6 - hechos["foco127"][1]
        for k in orden:
            P, a, b, vc = hechos[k]
            T = np.array([[1, 0, 0, x0 + pos[k]], [0, -1, 0, -(y0 - vc + vcu)], [0, 0, 1, 0], [0, 0, 0, 1]], float)
            escribir_wrl(P, T, os.path.join(sal, "familia_%s.wrl" % k))
        a = pos["red4"] + hechos["red4"][1] - 14; b = pos["foco127"] + hechos["foco127"][2] + 14
        T = np.array([[1, 0, 0, x0], [0, -1, 0, -y0], [0, 0, 1, 0], [0, 0, 0, 1]], float)
        escribir_wrl({"riel": riel(a, b, vcu)}, T, os.path.join(sal, "familia_riel.wrl"))
        print("familia en riel lista")
