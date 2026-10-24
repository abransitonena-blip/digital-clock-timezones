"""Fuente universal 127 V~ → 1.2–20 V ajustable, 2 A (máx. 24 W), en UNA placa de una cara.
Etapa 1: flyback aislado (UC3844 + 4N60 + transformador EE25 embobinado a mano) → ≈ 25 V.
Etapa 2: reductor LM2596S-ADJ ajustable (la misma etapa del módulo universal).
Coordenadas en mm, VISTA DESDE EL LADO DEL COBRE. Las piezas de patitas se ven en espejo desde aquí."""
import math, itertools, sys, os, runpy
here = os.path.dirname(os.path.abspath(__file__))
W, H = 170, 84
# ---------------- etapa 2 (secundario): se toma del módulo universal ----------------
_u = runpy.run_path(os.path.join(here, "..", "modulo-universal-ajustable", "generar.py"))
QUITAR = {"J1", "BR1", "C5", "MH1", "MH2", "MH3", "MH4"}
pads = [p for p in _u["pads"] if p[0] not in QUITAR]
traces = [t for t in _u["traces"] if t[0] not in ("A1", "A2") and t[2] != [(70, 23.7), (68, 23.7)]]
CUERPOS = {k: v for k, v in _u["CUERPOS"].items() if k not in ("BR1", "J1")}
CU_TEXT = [t for t in _u["CU_TEXT"] if t[3] != "IN~"]
def smd(ref, pin, x, y, net, w, h): pads.append((ref, pin, x, y, net, "r", w, h))
def tht(ref, pin, x, y, net, d=2.4): pads.append((ref, pin, x, y, net, "o", d, d))
def tr(net, w, *pts): traces.append((net, w, list(pts)))
def r1206v(ref, x, y, n1, n2): smd(ref, "1", x, y, n1, 1.8, 1.75); smd(ref, "2", x, y + 3.2, n2, 1.8, 1.75)
def r1206h(ref, x, y, n1, n2): smd(ref, "1", x, y, n1, 1.75, 1.8); smd(ref, "2", x + 3.2, y, n2, 1.75, 1.8)
# ---------------- secundario del flyback y retroalimentación ----------------
tht("D2", "K", 70, 15.5, "P", 2.6); tht("D2", "A", 82.7, 15.5, "S1", 2.6)             # SR5100
tr("P", 2.0, (70, 12), (70, 15.5)); tr("S1", 2.0, (82.7, 15.5), (82.7, 18), (86, 18))
TX_S, TX_P = 86, 106                                                                   # filas de patas del EE25
tht("T1", "S1", TX_S, 18, "S1"); tht("T1", "S0", TX_S, 38, "G")
tr("G", 2.0, (86, 38), (86, 40)); tr("G", 2.5, (68, 40), (88, 40))
# TL431 (TO-92): visto del cobre R-A-K de izquierda a derecha
tht("U3", "R", 73.46, 9.4, "REF", 1.5); tht("U3", "A", 76, 9.4, "G", 1.5); tht("U3", "K", 78.54, 9.4, "KT", 1.5)
tr("G", 1.0, (76, 9.4), (76, 30), (68, 30))
tr("P", 0.8, (63.4, 12), (63.4, 2.4))
r1206h("R4", 65.0, 6.4, "P", "REF"); tr("P", 0.8, (63.4, 6.4), (65.0, 6.4))            # 20 k
tr("REF", 0.6, (68.2, 6.4), (73.46, 6.4), (73.46, 9.4))
r1206h("R5", 73.46, 13.4, "REF", "G"); tr("REF", 0.6, (73.46, 9.4), (73.46, 13.4))      # 2.2 k
r1206h("R6", 65.0, 2.4, "P", "OA"); tr("P", 0.8, (63.4, 2.4), (65.0, 2.4))              # 1 k LED del opto
tr("OA", 0.6, (68.2, 2.4), (88, 2.4))
tht("JP1", "a", 88, 2.4, "OA", 1.8); tht("JP1", "b", 88, 10.02, "OA", 1.8)               # puente de alambre
tr("OA", 0.6, (88, 10.02), (92.2, 10.02))
r1206h("R7", 71.4, 4.4, "REF", "MID"); tr("REF", 0.6, (71.4, 6.4), (71.4, 4.4))         # 10 k compensación
r1206h("C8", 76.4, 4.4, "MID", "KT"); tr("MID", 0.6, (74.6, 4.4), (76.4, 4.4))          # 100 nF
tr("KT", 0.6, (79.6, 4.4), (79.6, 7)); tr("KT", 0.6, (78.54, 9.4), (78.54, 7), (92.2, 7))
r1206v("R8", 85, 3.6, "OA", "KT"); tr("OA", 0.6, (85, 2.4), (85, 3.6))                  # 1 k polarización
# optoacoplador PC817 cruzando la barrera (visto del cobre)
tht("U2", "2", 92.2, 7, "KT", 1.8); tht("U2", "1", 92.2, 9.54, "OA", 1.8)
tht("U2", "3", 99.82, 7, "PG", 1.8); tht("U2", "4", 99.82, 9.54, "COMP", 1.8)
# capacitor Y entre tierras
tht("CY", "S", 91, 66, "G", 2.0); tht("CY", "P", 101, 66, "HV", 2.0)
tr("G", 1.0, (88, 40), (88, 66), (91, 66))
CUERPOS.update({"D2": ("r", 72.5, 12.8, 80.2, 18.2), "U3": ("r", 72.0, 8.0, 80.0, 11.5), "U2": ("r", 91.0, 5.6, 101.0, 10.9),
                "T1": ("r", 83.0, 13.5, 109.0, 42.5), "CY": ("r", 89.5, 63.5, 102.5, 68.5)})
SLOT = (95.0, 3.0, 97.0, 47.0)
# ---------------- primario (127 V) ----------------
# transformador, lado primario (las patas que no se usan se cortan; no llevan pad)
tht("T1", "AUX", TX_P, 18, "AUX"); tht("T1", "PG", TX_P, 23, "PG"); tht("T1", "DR", TX_P, 33, "DR"); tht("T1", "HV", TX_P, 38, "HV")
# UC3844 (DIP-8, del otro lado). Visto del cobre: fila de arriba 1-2-3-4, fila de abajo 8-7-6-5
UCX, UCY = 116, 6.0
for i, (pin, net) in enumerate((("1", "COMP"), ("2", "PG"), ("3", "CS"), ("4", "RTCT"))):
    tht("U4", pin, UCX + 2.54 * i, UCY, net, 1.6)
for i, (pin, net) in enumerate((("8", "VREF"), ("7", "VCC"), ("6", "OUT"), ("5", "PG"))):
    tht("U4", pin, UCX + 2.54 * i, UCY + 7.62, net, 1.6)
# optoacoplador → UC: emisor a VFB (tierra del primario), colector a COMP
tr("PG", 0.6, (99.82, 7), (99.82, 3.6), (118.54, 3.6), (118.54, 6))
tr("COMP", 0.4, (99.82, 9.54), (114, 9.54), (114, 6), (116, 6))
# dentro del zócalo: CT (RTCT→tierra), RT (RTCT→VREF) y VFB→tierra pasando entre las patas de RT
smd("C9", "1", 123.62, 8.21, "RTCT", 1.8, 1.75); smd("C9", "2", 123.62, 11.41, "PG", 1.8, 1.75)   # CT 1.2 nF
tr("RTCT", 0.4, (123.62, 6), (123.62, 8.21)); tr("PG", 0.4, (123.62, 11.41), (123.62, 13.62))
r1206h("R9", 118.0, 9.6, "VREF", "RTCT")                                                            # RT 10 k
tr("RTCT", 0.4, (121.2, 9.6), (122.0, 9.6), (122.0, 8.21), (122.72, 8.21))
tr("VREF", 0.4, (118.0, 9.6), (116.6, 9.6), (116.6, 13.0))
tr("PG", 0.4, (118.54, 6), (118.54, 7.6), (119.6, 7.6), (119.6, 11.41), (122.72, 11.41))
# tierra del lado izquierdo: 0 Ω que salta la pista COMP
r1206v("R10", 102.4, 7.95, "PG", "PG"); tr("PG", 0.6, (102.4, 3.6), (102.4, 7.95)); tr("PG", 0.8, (102.4, 11.15), (102.4, 23), (106, 23))
# VCC: diodo del devanado auxiliar + capacitor
smd("D4", "A", 108.0, 18, "AUX", 1.0, 1.2); smd("D4", "K", 111.3, 18, "VCC", 1.0, 1.2)            # 1N4148W
tr("AUX", 0.6, (106, 18), (108.0, 18))
smd("C10", "+", 113.5, 17.4, "VCC", 2.0, 2.8); smd("C10", "-", 113.5, 22.6, "PG", 2.0, 2.8)         # 47 µF 50 V
tr("VCC", 0.6, (111.3, 18), (112.5, 18)); tr("VCC", 0.6, (118.54, 13.62), (118.54, 17), (114.5, 17))
tr("PG", 0.8, (113.5, 23.4), (106, 23.4))
# MOSFET 4N60 (TO-220 parado, cara impresa hacia arriba): visto del cobre G-D-S
tht("Q1", "G", 116.5, 24, "GATE", 1.6); tht("Q1", "D", 119.04, 24, "DR", 1.6); tht("Q1", "S", 121.58, 24, "S", 1.6)
r1206h("R11", 117.6, 20, "GATE", "OUT")                                                                # Rg 22 Ω
tr("OUT", 0.6, (121.08, 13.62), (121.08, 19.1)); tr("GATE", 0.6, (117.6, 20), (116.5, 20), (116.5, 24))
tr("DR", 1.2, (106, 33), (119.04, 33), (119.04, 24))
# resistencia de corriente y tierra de potencia
smd("R12", "1", 126, 24, "S", 1.6, 3.4); smd("R12", "2", 132, 24, "PG", 1.6, 3.4)                    # 0.47 Ω 2512
tr("S", 1.2, (121.58, 24), (125.2, 24))
tr("PG", 0.4, (123.62, 13.62), (123.62, 16.5), (132, 16.5), (132, 22.3))
r1206v("R13", 126, 14.9, "CS", "S"); tr("S", 0.6, (126, 18.1), (126, 22.3))                         # Rcs 1 k (puentea la tierra)
tr("CS", 0.4, (126, 14.9), (126, 2.6), (121.08, 2.6), (121.08, 6))
smd("C11", "1", 129, 13.0, "CS", 1.8, 1.75); smd("C11", "2", 129, 16.2, "PG", 1.8, 1.75)            # 470 pF
tr("CS", 0.4, (126, 13.0), (129, 13.0))
# recortador del pico del drenador: FR107 + P6KE200A
tht("D3", "A", 110.5, 33, "DR", 2.0); tht("D3", "K", 110.5, 40.62, "SN", 2.0)
tht("D5", "A", 114, 44, "SN", 2.2); tht("D5", "K", 124.16, 44, "HV", 2.2)
tr("SN", 0.8, (110.5, 40.62), (110.5, 44), (114, 44))
tr("HV", 1.5, (106, 38), (106, 47.5), (136, 47.5), (136, 33.9)); tr("HV", 1.0, (124.16, 44), (124.16, 47.5))
# filtro principal y puente
tht("C12", "-", 136, 26.25, "PG", 2.4); tht("C12", "+", 136, 33.75, "HV", 2.4)                     # 100 µF 250 V
for pin, y, n in (("-", 22.2, "PG"), ("~2", 26.1, "AN"), ("~1", 30.0, "AL"), ("+", 33.9, "HV")): tht("BR1", pin, 150, y, n, 2.4)
tr("HV", 1.5, (150, 33.9), (136, 33.9))
tr("PG", 1.5, (132, 24), (136, 24), (136, 26.25)); tr("PG", 1.5, (136, 24), (136, 22.2), (150, 22.2))
CUERPOS.update({"U4": ("r", 115.0, 6.6, 124.6, 13.0), "Q1": ("r", 114.0, 21.5, 124.2, 39.5), "D3": ("r", 109.2, 34.0, 111.8, 39.6),
                "D5": ("r", 115.0, 42.2, 123.2, 45.8), "C12": ("c", 136, 30, 8.2), "BR1": ("r", 148.2, 20.5, 151.8, 35.6)})
# arranque: 3 × 39 k desde el filtro hasta VCC (el último tramo es un cable forrado JP2)
tr("HV", 1.0, (106, 47.5), (104, 47.5), (104, 50))
smd("R14", "1", 104, 50.0, "HV", 1.8, 1.75); smd("R14", "2", 104, 53.2, "ST1", 1.8, 1.75)
smd("R15", "1", 104, 54.6, "ST1", 1.8, 1.75); smd("R15", "2", 104, 57.8, "ST2", 1.8, 1.75)
smd("R16", "1", 104, 59.2, "ST2", 1.8, 1.75); smd("R16", "2", 104, 62.4, "VCC", 1.8, 1.75)
tr("VCC", 0.6, (104, 62.4), (107, 62.4)); tht("JP2", "a", 107, 62.4, "VCC", 1.6)
tht("JP2", "b", 111.3, 15.4, "VCC", 1.6); tr("VCC", 0.6, (111.3, 15.4), (111.3, 18))
# capacitor Y: lado primario al + del filtro (para la alterna es lo mismo que la tierra del primario)
tr("HV", 0.8, (101, 66), (101, 47.5), (104, 47.5))
# ---------------- entrada de 127 V ----------------
tr("AN", 1.5, (150, 26.1), (163, 26.1), (163, 52)); tr("AL", 1.5, (150, 30), (155, 30), (155, 52))
tht("CX", "N", 159, 26.1, "AN", 2.4); tht("CX", "L", 159, 36.1, "AL", 2.4); tr("AL", 1.2, (159, 36.1), (155, 36.1))   # 100 nF X2
tht("RV1", "L", 155.5, 44, "AL", 2.4); tht("RV1", "N", 163, 44, "AN", 2.4)                                           # 10D201K
tht("F1", "a", 155, 52, "AL", 2.6); tht("F1", "b", 155, 74.86, "L", 2.6)                                              # 1 A lento
tht("TH1", "a", 163, 52, "AN", 2.4); tht("TH1", "b", 163, 57.08, "N", 2.4)                                           # NTC 5D-9
tht("J1", "L", 155, 79.5, "L", 3.0); tht("J1", "N", 160.08, 79.5, "N", 3.0)
tr("L", 1.5, (155, 74.86), (155, 79.5)); tr("N", 1.5, (163, 57.08), (163, 72), (160.08, 72), (160.08, 79.5))
CUERPOS.update({"CX": ("r", 156.0, 24.6, 162.0, 37.6), "RV1": ("r", 153.2, 41.6, 165.3, 46.4), "F1": ("r", 152.5, 54.0, 157.5, 73.0),
                "TH1": ("r", 160.6, 49.6, 165.4, 59.6), "J1": ("r", 151.0, 75.8, 164.2, 83.6)})
for i, (x, y) in enumerate(((3.5, 3.5), (W - 3.5, 3.5), (3.5, H - 3.5), (W - 3.5, H - 3.5))):
    pads.append((f"MH{i+1}", "", x, y, f"MH{i+1}", "o", 3.2, 3.2))
CU_TEXT += [(122, 58, 2.6, "127V"), (122, 61.5, 1.3, "PELIGRO")]
# ---------------- revisión de reglas ----------------
PUENTES = {"JP1", "JP2", "R10"}         # cable o 0 Ω: conectan sus dos pads por arriba
PRIM = {"AUX", "PG", "DR", "HV", "COMP", "RTCT", "VREF", "VCC", "OUT", "GATE", "S", "CS", "SN", "ST1", "ST2", "AL", "AN", "L", "N"}
ALTA = {"DR", "HV", "SN", "AL", "AN", "L", "N", "ST1", "ST2"}
def lado(n): return "M" if n.startswith("MH") else ("P" if n in PRIM else "S")
def regla(a, b):
    if lado(a) == "M" or lado(b) == "M": return 3.0 if (a in ALTA or b in ALTA) else 0.5
    if lado(a) != lado(b): return 5.5
    if a in ALTA or b in ALTA: return 1.2
    return 0.5
def seg_pt(p, a, b):
    ax, ay = a; bx, by = b; px, py = p; dx, dy = bx-ax, by-ay; L2 = dx*dx+dy*dy
    t = 0 if L2 == 0 else max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/L2))
    return math.hypot(px-(ax+t*dx), py-(ay+t*dy))
def seg_seg(a, b, c, d):
    def ccw(p, q, r): return (r[1]-p[1])*(q[0]-p[0]) - (q[1]-p[1])*(r[0]-p[0])
    if ccw(a, b, c)*ccw(a, b, d) < 0 and ccw(c, d, a)*ccw(c, d, b) < 0: return 0
    return min(seg_pt(a, c, d), seg_pt(b, c, d), seg_pt(c, a, b), seg_pt(d, a, b))
def rect_shape(n, name, x0, y0, x1, y1):
    return (n, name, [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))], 0, (x0, y0, x1, y1))
def shape(p):
    r, pn, x, y, n, f, w, h = p
    if f == "r": return rect_shape(n, f"{r}.{pn}", x-w/2, y-h/2, x+w/2, y+h/2)
    return (n, f"{r}.{pn}", [((x, y), (x, y))], w/2, None)
def inside(pt, rc): return rc and rc[0] <= pt[0] <= rc[2] and rc[1] <= pt[1] <= rc[3]
def dist(s1, s2):
    if any(inside(a, s2[4]) for sg in s1[2] for a in sg) or any(inside(a, s1[4]) for sg in s2[2] for a in sg): return -1
    return min(seg_seg(*g1, *g2) for g1 in s1[2] for g2 in s2[2]) - s1[3] - s2[3]
shapes = [shape(p) for p in pads]
for n, w, pts in traces:
    for a, b in zip(pts, pts[1:]): shapes.append((n, f"pista {n} {a}", [(a, b)], w/2, None))
def drc():
    errors, worst = [], {}
    for s1, s2 in itertools.combinations(shapes, 2):
        if s1[0] == s2[0]: continue
        need = regla(s1[0], s2[0])
        if need == 1.2 and (s1[1].startswith("Q1.") or s2[1].startswith("Q1.")): need = 0.9
        d = dist(s1, s2)
        k = (lado(s1[0]), lado(s2[0]), need); worst[k] = min(worst.get(k, 99), d)
        if d < need - 1e-6: errors.append(f"{d:.2f} < {need} mm: {s1[1]} ↔ {s2[1]}")
    for net in set(s[0] for s in shapes):
        ss = [s for s in shapes if s[0] == net]; seen = {0}; st = [0]
        while st:
            i = st.pop()
            for j in range(len(ss)):
                puente = ss[i][1].split(".")[0] == ss[j][1].split(".")[0] and ss[i][1].split(".")[0] in PUENTES
                if j not in seen and (puente or dist(ss[i], ss[j]) <= 1e-9): seen.add(j); st.append(j)
        if len(seen) != len(ss): errors.append(f"red {net} cortada: " + ", ".join(ss[k][1] for k in range(len(ss)) if k not in seen))
    ranura = rect_shape("RANURA", "ranura", *SLOT)
    for s in shapes:
        if dist(ranura, s) < 0.6: errors.append(f"{s[1]} toca la ranura")
        for g in s[2]:
            for (x, y) in g:
                if x - s[3] < 0.8 or x + s[3] > W - 0.8 or y - s[3] < 0.8 or y + s[3] > H - 0.8: errors.append(f"{s[1]} muy cerca de la orilla")
    for (x, y, h, t) in CU_TEXT:
        w = 0.62*h*len(t); box = rect_shape("T", t, x - w/2, y - h*0.8, x + w/2, y + h*0.05)
        for sh in shapes:
            if dist(box, sh) < 1.0: errors.append(f"texto '{t}' cerca de {sh[1]}")
    def caja(b): return (b[1]-b[3], b[2]-b[3], b[1]+b[3], b[2]+b[3]) if b[0] == "c" else b[1:]
    for (a, ba), (b, bb) in itertools.combinations(CUERPOS.items(), 2):
        A, B = caja(ba), caja(bb)
        if A[0] < B[2] and B[0] < A[2] and A[1] < B[3] and B[1] < A[3]:
            if ba[0] == "c" and bb[0] == "c" and math.hypot(ba[1]-bb[1], ba[2]-bb[2]) >= ba[3]+bb[3]: continue
            errors.append(f"cuerpos de {a} y {b} se enciman")
    return errors, worst
if __name__ == "__main__":
    errors, worst = drc()
    if errors: print("\n".join(sorted(set(errors))[:80])); print(len(set(errors)), "errores"); sys.exit(1)
    print(f"DRC OK: placa {W}×{H} mm, {len(pads)} pads")
    for k, v in sorted(worst.items()): print("  ", k, f"{v:.2f}")
