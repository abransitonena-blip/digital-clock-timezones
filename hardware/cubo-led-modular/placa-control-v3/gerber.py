"""Exporta Gerber RS-274X (X2 básico), Excellon, BOM y CPL a partir de diseno.py + ruteo (fab.py).
Uso: python3.11 gerber.py   (corre fab.py si hace falta)  ->  gerbers/*.gbr, *.drl, cubo_ap_control_v3_gerbers.zip, bom.csv, cpl.csv"""
import os, csv, zipfile, collections, json, datetime, subprocess, sys
import shapely
from shapely.geometry import Polygon, MultiPolygon, LineString, Point, box
from shapely.ops import unary_union, split
from shapely import affinity
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
import diseno as D, geom as G, fab

OX, OY = D.W / 2, D.H / 2          # origen Gerber en la esquina inferior izquierda
SAL = "gerbers"
FUENTE = TTFont("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
GLIFOS, UPEM = FUENTE.getGlyphSet(), FUENTE["head"].unitsPerEm
CMAP = FUENTE.getBestCmap()

# ---------------- texto a polígonos ----------------
class Pluma(BasePen):
    def __init__(self, gs):
        super().__init__(gs); self.contornos = []; self.act = []
    def _moveTo(self, p): self.act = [p]
    def _lineTo(self, p): self.act.append(p)
    def _curveToOne(self, a, b, c):
        p0 = self.act[-1]
        for i in range(1, 9):
            t = i / 8; u = 1 - t
            self.act.append((u**3*p0[0] + 3*u*u*t*a[0] + 3*u*t*t*b[0] + t**3*c[0], u**3*p0[1] + 3*u*u*t*a[1] + 3*u*t*t*b[1] + t**3*c[1]))
    def _qCurveToOne(self, a, b):
        p0 = self.act[-1]
        for i in range(1, 7):
            t = i / 6; u = 1 - t
            self.act.append((u*u*p0[0] + 2*u*t*a[0] + t*t*b[0], u*u*p0[1] + 2*u*t*a[1] + t*t*b[1]))
    def _closePath(self):
        if len(self.act) > 2: self.contornos.append(self.act)
        self.act = []
    _endPath = _closePath

def texto(s, x, y, alto, ancla="m", rot=0):
    """Polígonos del texto; alto = altura de mayúsculas en mm."""
    esc = alto / 1460 * UPEM / UPEM  # DejaVu: altura de mayúscula ≈ 1493/2048 em
    esc = alto / (0.729 * UPEM)
    piezas, cx = [], 0.0
    for ch in s:
        g = CMAP.get(ord(ch))
        if g is None: cx += 600; continue
        pl = Pluma(GLIFOS); GLIFOS[g].draw(pl)
        forma = None
        for c in pl.contornos:
            p = Polygon(c).buffer(0)
            forma = p if forma is None else forma.symmetric_difference(p)
        if forma is not None: piezas.append(affinity.translate(forma, cx, 0))
        cx += GLIFOS[g].width
    if not piezas: return Polygon()
    t = affinity.scale(unary_union(piezas), esc, esc, origin=(0, 0))
    ancho = cx * esc
    dx = {"m": -ancho / 2, "i": 0, "d": -ancho}[ancla]
    t = affinity.translate(t, dx, -alto / 2)
    t = affinity.rotate(t, rot, origin=(0, 0))
    return affinity.translate(t, x, y)

# ---------------- escritura Gerber ----------------
def sin_huecos(g):
    """Parte polígonos con huecos en piezas sin huecos (cortes verticales por cada hueco)."""
    out = []
    pend = list(getattr(g, "geoms", [g]))
    while pend:
        p = pend.pop()
        if p.is_empty or p.area < 1e-6: continue
        if not p.interiors: out.append(p); continue
        h = Polygon(p.interiors[0]); cx = h.representative_point().x
        y0, y1 = p.bounds[1] - 1, p.bounds[3] + 1
        partes = split(p, LineString([(cx, y0), (cx, y1)]))
        pend.extend(q for q in partes.geoms if q.geom_type == "Polygon")
    return out

def gerber(nombre, funcion, polis=(), lineas=(), ancho_linea=0.15, polaridad="Positive"):
    L = ["%TF.GenerationSoftware,CuboAP,fab.py,1*%", f"%TF.CreationDate,{datetime.date.today().isoformat()}T00:00:00*%",
         f"%TF.FileFunction,{funcion}*%", f"%TF.FilePolarity,{polaridad}*%", "%FSLAX46Y46*%", "%MOMM*%", "%LPD*%",
         f"%ADD10C,{ancho_linea:.3f}*%", "G01*"]
    f = lambda v: f"{int(round(v * 1e6))}"
    for g in polis:
        for p in sin_huecos(g):
            cs = list(p.exterior.coords)
            L.append("G36*"); L.append(f"X{f(cs[0][0]+OX)}Y{f(cs[0][1]+OY)}D02*")
            L += [f"X{f(x+OX)}Y{f(y+OY)}D01*" for x, y in cs[1:]]
            L.append("G37*")
    if lineas:
        L.append("D10*")
        for cs in lineas:
            L.append(f"X{f(cs[0][0]+OX)}Y{f(cs[0][1]+OY)}D02*"); L += [f"X{f(x+OX)}Y{f(y+OY)}D01*" for x, y in cs[1:]]
    L.append("M02*")
    open(os.path.join(SAL, nombre), "w").write("\n".join(L) + "\n")

def excellon(nombre, agujeros, plated=True):
    tal = sorted({round(d, 2) for _, _, d in agujeros})
    L = ["M48", "; Cubo AP placa de control", f"; TYPE={'PLATED' if plated else 'NON_PLATED'}", "FMAT,2", "METRIC,TZ"]
    L += [f"T{i+1}C{d:.3f}" for i, d in enumerate(tal)] + ["%", "G90", "G05"]
    for i, d in enumerate(tal):
        L.append(f"T{i+1}")
        L += [f"X{x+OX:.3f}Y{y+OY:.3f}" for x, y, dd in agujeros if round(dd, 2) == d]
    L.append("M30"); open(os.path.join(SAL, nombre), "w").write("\n".join(L) + "\n")

def serigrafia(pads):
    """Contornos, referencias, polaridad y leyendas; recortada fuera de pads."""
    s = []
    lin = []
    for p in D.P:
        x0, y0, x1, y1 = G.patio(p)
        if p["fp"] in ("TP",): continue
        r = box(x0 + 0.15, y0 + 0.15, x1 - 0.15, y1 - 0.15)
        lin.append(r.exterior.buffer(0.075))
        if p["fp"] in ("SOIC8", "HSOP8", "SO8-PMOS", "VSSOP10", "SOT23-5", "SOT23-6", "DFN3x3", "QFN32"):
            q1 = next(q for q in pads if q["ref"] == p["ref"] and q["pin"] == "1")
            vx, vy = q1["x"] - p["x"], q1["y"] - p["y"]; n = max(1e-6, (vx * vx + vy * vy) ** 0.5)
            s.append(Point(q1["x"] + vx / n * 1.0, q1["y"] + vy / n * 1.0).buffer(0.25))
        if p["fp"] in ("ELEC6", "ELEC8"):
            q1 = next(q for q in pads if q["ref"] == p["ref"] and q["pin"] == "1")
            s.append(texto("+", q1["x"] + (q1["x"] - p["x"]) * 0.0, q1["y"] + 1.6, 1.2))
        if p["fp"] in ("SOD123", "SMA", "SMB", "SMC"):         # barra de cátodo junto al pin 1
            q1 = next(q for q in pads if q["ref"] == p["ref"] and q["pin"] == "1")
            vx, vy = q1["x"] - p["x"], q1["y"] - p["y"]
            if abs(vx) > abs(vy): s.append(box(q1["x"] - 0.15 + (0.9 if vx > 0 else -0.9) * 0, y0 + 0.2, q1["x"] + 0.15, y1 - 0.2).buffer(0) if False else
                                         LineString([(x0 + 0.4 if vx < 0 else x1 - 0.4, y0 + 0.3), (x0 + 0.4 if vx < 0 else x1 - 0.4, y1 - 0.3)]).buffer(0.2))
            else: s.append(LineString([(x0 + 0.3, y0 + 0.4 if vy < 0 else y1 - 0.4), (x1 - 0.3, y0 + 0.4 if vy < 0 else y1 - 0.4)]).buffer(0.2))
        alto = 0.9 if len(p["ref"]) <= 3 else 0.8
        t = texto(p["ref"], p["x"], p["y"], alto)
        libre_ = t.difference(unary_union([q["g"] for q in pads]).buffer(0.15))
        if libre_.area > 0.97 * t.area: s.append(t)             # si la referencia queda sobre pads, se omite (ver vista de montaje)
    # leyendas
    for txt, x, y, h, rot in (("V+", 27.0, 17.78, 1.0, 0), ("R", 26.4, 12.7, 1.0, 0), ("G", 26.4, 7.62, 1.0, 0), ("B", 26.4, 2.54, 1.0, 0),
                              ("WW", 26.6, -2.54, 0.9, 0), ("CW", 26.6, -7.62, 0.9, 0), ("DAT", 26.6, -12.7, 0.9, 0), ("GND", 26.6, -17.78, 0.9, 0),
                              ("+12-36V", -29.5, 16.6, 1.0, 0), ("GND", -29.5, 3.6, 1.0, 0),
                              ("FB GND ID", -3.8, 13.9, 0.8, 0),
                              ("DMX", -23.6, -28.4, 1.1, 0), ("GND D- D+", -16.0, -30.9, 0.8, 0), ("TERM", -13.0, -26.6, 0.8, 0),
                              ("AP v3", -27.6, -10.0, 1.3, 0),
                              ("5V   D-   D+  GND  EN  IO9", 10.0, -31.35, 0.6, 0), ("ANT", 0.6, -29.4, 0.9, 0)):
        s.append(texto(txt, x, y, h, rot=rot))
    todo = unary_union(s + lin)
    abiertos = unary_union([q["g"] for q in pads]).buffer(0.15)
    return todo.difference(abiertos).intersection(G.contorno().buffer(-0.2))

def bom_cpl():
    grupos = collections.OrderedDict()
    for p in D.P:
        if p["fp"] == "TP": continue
        k = (p["val"], p["fp"], p["mpn"])
        grupos.setdefault(k, []).append(p["ref"])
    with open("bom.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["Comment", "Designator", "Footprint", "Cantidad", "Descripción / MPN", "LCSC"])
        for (val, fp, mpn), refs in grupos.items(): w.writerow([val, ",".join(refs), fp, len(refs), mpn, ""])
    with open("cpl.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for p in D.P:
            if p["fp"] == "TP": continue
            w.writerow([p["ref"], f"{p['x']+OX:.3f}mm", f"{p['y']+OY:.3f}mm", "Top", p["rot"]])
    return len(grupos)

def main():
    os.makedirs(SAL, exist_ok=True)
    if not os.path.exists(fab.ARCH_COBRE): subprocess.run([sys.executable, "fab.py"], check=True)
    cobre = fab.cargar_cobre(); ru = json.load(open("ruteo.json"))
    pads = G.todos_pads()
    for q in pads: q["g"] = fab.pad_geo(q)
    for l, nom, fun in ((0, "F_Cu.gbr", "Copper,L1,Top"), (1, "B_Cu.gbr", "Copper,L2,Bot")):
        gerber(nom, fun, [unary_union([g for n, g, t in cobre[l]])])
    smd = [q for q in pads if not q["drill"]]; tht = [q for q in pads if q["drill"]]
    gerber("F_Mask.gbr", "Soldermask,Top", [unary_union([q["g"].buffer(0.05) for q in pads])], polaridad="Negative")
    gerber("B_Mask.gbr", "Soldermask,Bot", [unary_union([q["g"].buffer(0.05) for q in tht])], polaridad="Negative")
    gerber("F_Paste.gbr", "Paste,Top", [unary_union([q["g"] for q in smd if q["f"] != "c"])])
    silk = serigrafia(pads); gerber("F_Silkscreen.gbr", "Legend,Top", [silk])
    borde = G.contorno(64)
    gerber("Edge_Cuts.gbr", "Profile,NP", lineas=[list(borde.exterior.coords)], ancho_linea=0.1)
    pth = [(x, y, fab.VIA_TAL) for x, y, n in ru["vias"]] + [(q["x"], q["y"], q["drill"]) for q in tht]
    excellon("PTH.drl", pth, True)
    excellon("NPTH.drl", [(x, y, 3.2) for x, y in D.BARRENOS], False)
    with zipfile.ZipFile("cubo_ap_control_v3_gerbers.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(SAL)): z.write(os.path.join(SAL, f), f)
    n = bom_cpl()
    open("serigrafia.wkb.hex", "w").write(shapely.to_wkb(silk, hex=True))
    print("gerbers:", sorted(os.listdir(SAL)), "| BOM líneas:", n, "| barrenos PTH:", len(pth))

if __name__ == "__main__":
    main()
