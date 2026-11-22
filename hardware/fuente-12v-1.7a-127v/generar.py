"""Fuente 12 V / 1.7 A desde 127 V: transformador 18 V~ (fuera de la placa) → puente KBP307 → filtro 2×1000 µF
→ LM2596S-12 (SMD). Placa de una cara 72 × 50 mm para planchar.
Coordenadas en mm, VISTA DESDE EL LADO DEL COBRE (ahí van las piezas SMD). Las piezas de patitas
(puente, capacitores grandes, borneras) van del otro lado."""
import math, itertools, sys, os
W, H = 72, 50
CLEAR = 0.5
pads, traces = [], []
def smd(ref, pin, x, y, net, w, h): pads.append((ref, pin, x, y, net, "r", w, h))
def tht(ref, pin, x, y, net, d=3.0): pads.append((ref, pin, x, y, net, "o", d, d))
def tr(net, w, *pts): traces.append((net, w, list(pts)))
# ---------- entrada: bornera 18 V~, puente y filtro ----------
tht("J1", "~1", 68.5, 15.31, "A1"); tht("J1", "~2", 68.5, 20.39, "A2")
for pin, y, n in (("+", 12, "P"), ("~1", 15.9, "A1"), ("~2", 19.8, "A2"), ("-", 23.7, "G")): tht("BR1", pin, 62, y, n, 2.4)
smd("C5", "1", 65.5, 16.25, "A1", 1.8, 1.75); smd("C5", "2", 65.5, 19.45, "A2", 1.8, 1.75)     # 100 nF 1206
tht("C6", "+", 52, 15, "P", 2.4); tht("C6", "-", 52, 20, "G", 2.4)                               # 1000 µF 50 V
tht("C7", "+", 52, 31, "P", 2.4); tht("C7", "-", 52, 36, "G", 2.4)                               # 1000 µF 50 V
smd("R2", "1", 45.5, 29.4, "P", 1.8, 1.75); smd("R2", "2", 45.5, 32.6, "LB", 1.8, 1.75)          # 10 k 1206
smd("LED1", "A", 45.5, 35.2, "LB", 1.4, 1.2); smd("LED1", "K", 45.5, 37.4, "G", 1.4, 1.2)        # LED rojo 0805
# ---------- regulador ----------
UX = {5: 24.6, 4: 26.3, 3: 28.0, 2: 29.7, 1: 31.4}
UN = {1: "P", 2: "SW", 3: "G", 4: "VO", 5: "G"}
for p, x in UX.items(): smd("U1", str(p), x, 12, UN[p], 1.1, 3.5)
smd("U1", "TAB", 28, 22.45, "G", 10.8, 9.6)
smd("C1", "+", 41, 17.2, "P", 2.6, 4.0); smd("C1", "-", 41, 25.8, "G", 2.6, 4.0)                 # 220 µF 50 V
smd("C2", "1", 34.6, 15.2, "P", 1.8, 1.75); smd("C2", "2", 34.6, 18.4, "G", 1.8, 1.75)           # 1 µF 1206
smd("D1", "K", 5, 10.6, "SW", 3.3, 2.5); smd("D1", "A", 5, 17.4, "G", 3.3, 2.5)                  # SS54
smd("L1", "1", 15, 11.6, "SW", 5.0, 3.2); smd("L1", "2", 15, 21.4, "VO", 5.0, 3.2)               # 47 µH
smd("C3", "+", 8, 27.3, "VO", 2.6, 4.0); smd("C3", "-", 8, 35.7, "G", 2.6, 4.0)                  # 470 µF 25 V
smd("C4", "1", 14.4, 28.0, "VO", 1.8, 1.75); smd("C4", "2", 14.4, 31.2, "G", 1.8, 1.75)          # 10 µF 25 V 1206
tht("J2", "+", 17.5, 31, "VO"); tht("J2", "-", 17.5, 36.08, "G")
smd("R1", "1", 20.8, 28.2, "VO", 1.4, 1.2); smd("R1", "2", 20.8, 30.4, "LM", 1.4, 1.2)           # 2.2 k 0805
smd("LED2", "A", 20.8, 33.2, "LM", 1.4, 1.2); smd("LED2", "K", 20.8, 35.4, "G", 1.4, 1.2)        # LED verde 0805
for i, (x, y) in enumerate(((3.5, 3.5), (W - 3.5, 3.5), (3.5, H - 3.5), (W - 3.5, H - 3.5))):
    pads.append((f"MH{i+1}", "", x, y, f"MH{i+1}", "o", 3.2, 3.2))
# ---------- pistas ----------
tr("A1", 1.5, (62, 15.9), (68.5, 15.9)); tr("A2", 1.5, (62, 19.8), (68.5, 19.8))
tr("P", 1.5, (31.6, 12), (41, 12), (41, 17.2)); tr("P", 2.0, (41, 12), (62, 12)); tr("P", 1.0, (34.6, 12), (34.6, 15.2))
tr("P", 2.0, (52, 12), (52, 15)); tr("P", 2.0, (48, 12), (48, 31), (52, 31)); tr("P", 0.8, (45.5, 29.4), (48, 29.4))
tr("LB", 0.6, (45.5, 32.6), (45.5, 35.2))
tr("SW", 1.2, (29.7, 12), (29.7, 6.8)); tr("SW", 1.5, (29.7, 6.8), (5, 6.8), (5, 10.6)); tr("SW", 1.5, (15, 6.8), (15, 11.6))
tr("G", 1.0, (28, 12), (28, 18)); tr("G", 1.0, (24.6, 12), (24.6, 18)); tr("G", 1.2, (34.6, 18.4), (33, 18.4))
tr("G", 7.0, (28, 26), (28, 38)); tr("G", 4.0, (3, 40), (60, 40))
tr("G", 2.5, (41, 25.8), (41, 40)); tr("G", 2.5, (8, 35.7), (8, 40)); tr("G", 2.0, (17.5, 36.08), (17.5, 40))
tr("G", 0.8, (20.8, 35.4), (20.8, 39)); tr("G", 0.8, (14.4, 31.2), (14.4, 38.5)); tr("G", 0.8, (45.5, 37.4), (45.5, 39))
tr("G", 2.5, (5, 17.4), (5, 19.5), (2.2, 19.5), (2.2, 40))
tr("G", 2.5, (60, 23.7), (60, 40)); tr("G", 2.0, (62, 23.7), (60, 23.7))
tr("G", 1.5, (52, 20), (55.5, 20), (55.5, 25), (60, 25)); tr("G", 2.0, (52, 36), (60, 36))
tr("VO", 2.0, (15, 21.4), (15, 25)); tr("VO", 2.0, (8, 25), (20.8, 25)); tr("VO", 2.0, (17.5, 25), (17.5, 31))
tr("VO", 0.8, (20.8, 25), (20.8, 28.2)); tr("VO", 0.8, (14.4, 25), (14.4, 28.0))
tr("VO", 0.8, (21, 25), (21, 9), (26.3, 9), (26.3, 11))          # FB
tr("LM", 0.6, (20.8, 30.4), (20.8, 33.2))
CU_TEXT = [(35.8, 31.2, 2.4, "AP"), (35.8, 35.0, 1.1, "12V 1.7A"), (66, 27.2, 1.6, "18V~")]
def text_box(x, y, h, t): w = 0.62*h*len(t); return (x - w/2, y - h*0.8, x + w/2, y + h*0.05)
# ---------- revisión de reglas ----------
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
    for a, b in zip(pts, pts[1:]): shapes.append((n, f"pista {n}", [(a, b)], w/2, None))
errors, worst = [], 99
for s1, s2 in itertools.combinations(shapes, 2):
    if s1[0] == s2[0]: continue
    d = dist(s1, s2); worst = min(worst, d)
    if d < CLEAR - 1e-6: errors.append(f"separación {d:.2f} mm entre {s1[1]} y {s2[1]}")
for net in set(s[0] for s in shapes):
    ss = [s for s in shapes if s[0] == net]; seen = {0}; st = [0]
    while st:
        i = st.pop()
        for j in range(len(ss)):
            if j not in seen and dist(ss[i], ss[j]) <= 1e-9: seen.add(j); st.append(j)
    if len(seen) != len(ss): errors.append(f"red {net} cortada: " + ", ".join(ss[k][1] for k in range(len(ss)) if k not in seen))
for s in shapes:
    for g in s[2]:
        for (x, y) in g:
            if x - s[3] < 0.8 or x + s[3] > W - 0.8 or y - s[3] < 0.8 or y + s[3] > H - 0.8: errors.append(f"{s[1]} muy cerca de la orilla")
for (x, y, h, t) in CU_TEXT:
    box = rect_shape("T", t, *text_box(x, y, h, t))
    for sh in shapes:
        d = dist(box, sh)
        if d < 1.0: errors.append(f"texto '{t}' a {d:.2f} mm de {sh[1]}")
# piezas de patitas: que sus cuerpos (lado de arriba) no choquen entre sí
CUERPOS = {"BR1": ("r", 60.2, 10.3, 63.8, 25.4), "C6": ("c", 52, 17.5, 6.4), "C7": ("c", 52, 33.5, 6.4),
           "J1": ("r", 64.4, 12.6, 72.0, 23.1), "J2": ("r", 13.7, 28.4, 21.3, 38.7)}
def caja(b): return (b[1]-b[3], b[2]-b[3], b[1]+b[3], b[2]+b[3]) if b[0] == "c" else b[1:]
for (a, ba), (b, bb) in itertools.combinations(CUERPOS.items(), 2):
    A, B = caja(ba), caja(bb)
    if A[0] < B[2] and B[0] < A[2] and A[1] < B[3] and B[1] < A[3]:
        if ba[0] == "c" and bb[0] == "c" and math.hypot(ba[1]-bb[1], ba[2]-bb[2]) >= ba[3]+bb[3]: continue
        errors.append(f"cuerpos de {a} y {b} se enciman")
if errors: print("\n".join(sorted(set(errors))[:40])); sys.exit(1)
print(f"DRC OK: placa {W}×{H} mm, {len(pads)} pads, separación mínima real {worst:.2f} mm")

# ---------- dibujos ----------
def pts_d(pts): return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts)
def head(k=1.0): return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W*k:.1f}mm" height="{H*k:.1f}mm" viewBox="0 0 {W} {H}" font-family="Arial,Helvetica,sans-serif">'
def cobre(espejo=False):
    o = [head(), f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fff" stroke="#000" stroke-width="0.25"/>',
         f'<g transform="translate({W} 0) scale(-1 1)">' if espejo else '<g>']
    for n, w, pts in traces: o.append(f'<path d="{pts_d(pts)}" fill="none" stroke="#000" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')
    for r, pn, x, y, n, f, w, h in pads:
        if r.startswith("MH"): o.append(f'<circle cx="{x}" cy="{y}" r="{w/2+0.3}" fill="none" stroke="#000" stroke-width="0.4"/><circle cx="{x}" cy="{y}" r="0.4"/>'); continue
        if f == "r": o.append(f'<rect x="{x-w/2:.2f}" y="{y-h/2:.2f}" width="{w}" height="{h}" rx="0.2"/>')
        else: o.append(f'<circle cx="{x}" cy="{y}" r="{w/2}"/><circle cx="{x}" cy="{y}" r="0.5" fill="#fff"/>')
    for x, y, h, t in CU_TEXT: o.append(f'<text x="{x}" y="{y}" text-anchor="middle" font-weight="700" font-size="{h}">{t}</text>')
    o.append('</g></svg>'); return "\n".join(o)

def T(x, y, s, sz=1.3, a="middle", w="700", c="#111", rot=None):
    tf = f' transform="rotate({rot} {x} {y})"' if rot is not None else ""
    return f'<text x="{x}" y="{y}" font-size="{sz}" text-anchor="{a}" font-weight="{w}" fill="{c}"{tf}>{s}</text>'
L = 'fill="none" stroke="#111" stroke-width="0.3" stroke-linejoin="round"'
D = 'fill="none" stroke="#2563eb" stroke-width="0.3" stroke-dasharray="1 0.7"'
def base_cobre(o, CU="#ead0b3", PAD="#d9a877"):
    for n, w, pts in traces: o.append(f'<path d="{pts_d(pts)}" fill="none" stroke="{CU}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')
    for r, pn, x, y, n, f, w, h in pads:
        if r.startswith("MH"): o.append(f'<circle cx="{x}" cy="{y}" r="1.6" fill="#fff" stroke="#999" stroke-width="0.3"/>'); continue
        o.append(f'<rect x="{x-w/2:.2f}" y="{y-h/2:.2f}" width="{w}" height="{h}" rx="0.2" fill="{PAD}"/>' if f == "r" else
                 f'<circle cx="{x}" cy="{y}" r="{w/2}" fill="{PAD}"/><circle cx="{x}" cy="{y}" r="0.55" fill="#fff"/>')
def ecap_smd(cx, cy, ref, val):
    a, c = 5.15, 1.6
    d_ = f"M{cx-a+c} {cy-a} H{cx+a-c} L{cx+a} {cy-a+c} V{cy+a} H{cx-a} V{cy-a+c} Z"
    return (f'<path d="{d_}" {L}/><circle cx="{cx}" cy="{cy}" r="4.6" {L}/><path d="M{cx-4.3} {cy+1.7} A4.6 4.6 0 0 0 {cx+4.3} {cy+1.7} Z" fill="#111"/>'
            + T(cx, cy - 0.6, ref, 1.5) + T(cx, cy + 0.9, val, 0.95, w="400") + T(cx - 4.0, cy - 3.0, "+", 1.6))

def montaje(k=1.0):
    """Lado del cobre: piezas SMD con su forma; en azul punteado lo que va del otro lado."""
    o = [head(k), f'<rect x="0" y="0" width="{W}" height="{H}" rx="1" fill="#fbf8f2" stroke="#555" stroke-width="0.3"/>']
    base_cobre(o)
    o.append(f'<rect x="22.9" y="15.4" width="10.2" height="9.4" rx="0.4" {L}/>')
    for p, x in UX.items(): o.append(f'<path d="M{x} 11.2 V15.4" stroke="#111" stroke-width="0.5"/>')
    o.append(f'<circle cx="31.4" cy="16.6" r="0.45" fill="#111"/>' + T(28, 20.6, "U1", 1.6) + T(28, 22.4, "LM2596S-12", 1.05, w="400"))
    o.append(T(31.4, 8.0, "1", 0.9, w="400") + T(24.6, 8.0, "5", 0.9, w="400"))
    o.append(f'<rect x="2.3" y="9.4" width="5.4" height="9.2" rx="0.5" {L}/><rect x="2.3" y="9.4" width="5.4" height="1.3" fill="#111"/>' + T(5, 13.8, "D1", 1.2) + T(5, 15.2, "SS54", 0.9, w="400"))
    o.append(f'<rect x="9" y="10.5" width="12" height="12" rx="1.5" {L}/><circle cx="15" cy="16.5" r="4.2" {L}/>' + T(15, 16.4, "L1", 1.5) + T(15, 18.0, "47µH", 1.0, w="400"))
    o.append(ecap_smd(41, 21.5, "C1", "220µF 50V") + ecap_smd(8, 31.5, "C3", "470µF 25V"))
    o.append(f'<rect x="33.5" y="14.0" width="2.2" height="5.6" rx="0.3" {L}/>' + T(34.6, 21.3, "C2", 0.9) + T(34.6, 22.4, "1µF", 0.75, w="400"))
    o.append(f'<rect x="13.3" y="26.8" width="2.2" height="5.6" rx="0.3" {L}/>' + T(14.4, 25.9 - 1.6, "", 0.8))
    o.append(T(12.2, 39.0, "C4 10µF", 0.8, "start"))
    o.append(f'<rect x="19.9" y="27.5" width="1.8" height="3.6" rx="0.3" {L}/>' + T(22.4, 29.6, "R1 2.2k", 0.85, "start"))
    o.append(f'<rect x="19.9" y="32.5" width="1.8" height="3.6" rx="0.3" {L}/><path d="M20.1 35.6 H21.5" stroke="#111" stroke-width="0.35"/>' + T(22.4, 34.6, "LED2", 0.85, "start") + T(22.4, 35.7, "verde", 0.7, "start", "400"))
    o.append(f'<rect x="44.4" y="28.2" width="2.2" height="5.6" rx="0.3" {L}/>' + T(44.0, 30.7, "R2", 0.85, "end") + T(44.0, 31.8, "10k", 0.75, "end", "400"))
    o.append(f'<rect x="44.6" y="34.4" width="1.8" height="3.6" rx="0.3" {L}/><path d="M44.8 37.8 H46.2" stroke="#111" stroke-width="0.35"/>' + T(44.0, 36.0, "LED1", 0.85, "end") + T(44.0, 37.1, "rojo", 0.7, "end", "400"))
    o.append(f'<rect x="64.4" y="15.1" width="2.2" height="5.5" rx="0.3" {L}/>' + T(65.5, 23.4, "C5", 0.85) + T(65.5, 24.5, "100nF", 0.7, w="400"))
    # piezas del otro lado (contorno azul punteado)
    for ref, b in CUERPOS.items():
        if b[0] == "c": o.append(f'<circle cx="{b[1]}" cy="{b[2]}" r="{b[3]-0.15}" {D}/>')
        else: o.append(f'<rect x="{b[1]}" y="{b[2]}" width="{b[3]-b[1]}" height="{b[4]-b[2]}" rx="0.6" {D}/>')
    o.append(T(52, 26.4, "C6", 1.2, c="#2563eb") + T(52, 28.6, "C7", 1.2, c="#2563eb"))
    o.append(T(51.0, 16.0, "+", 1.5, "end", c="#c00") + T(51.0, 32.0, "+", 1.5, "end", c="#c00"))
    o.append(T(58.6, 12.6, "+", 1.4, c="#c00") + T(58.6, 26.0, "−", 1.6) + T(62, 33.4, "BR1", 1.1, c="#2563eb") + T(62, 34.7, "KBP307", 0.8, c="#2563eb", w="400"))
    o.append(T(68.3, 10.6, "18V~", 1.1, c="#2563eb") + T(17.5, 34.1, "+", 1.3, c="#c00") + T(15.6, 26.4, "", 1))
    o.append(T(17.5, 27.6, "12V", 0.9, c="#2563eb"))
    o.append('</svg>'); return "\n".join(o)

def lado_piezas(espejo_para_planchar=False):
    """Lado SIN cobre (donde van puente, capacitores grandes y borneras): serigrafía."""
    o = [head(), f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fff"/>']
    # la vista del lado de piezas es el espejo de la del cobre; para planchar se vuelve a invertir
    g = '<g>' if espejo_para_planchar else f'<g transform="translate({W} 0) scale(-1 1)">'
    o.append(g)
    o.append(f'<rect x="0.7" y="0.7" width="{W-1.4}" height="{H-1.4}" rx="2" {L}/>')
    for r, pn, x, y, n, f, w, h in pads:
        if f == "o": o.append(f'<circle cx="{x}" cy="{y}" r="{1.6 if r.startswith("MH") else 0.8}" {L}/>')
    def txt(x, y, s, sz=1.3, w="700"):   # texto que se lee derecho en el lado de piezas
        return f'<g transform="translate({x} {y}) scale(-1 1)"><text x="0" y="0" font-size="{sz}" text-anchor="middle" font-weight="{w}">{s}</text></g>'
    o.append(f'<path d="M60.4 11.8 L61.4 10.4 H63.6 V25.3 H60.4 Z" {L}/>' + txt(62, 9.4, "BR1", 1.0) + txt(62, 27.0, "KBP307", 0.8, "400"))
    for cy, ref in ((17.5, "C6"), (33.5, "C7")):
        o.append(f'<circle cx="52" cy="{cy}" r="6.25" {L}/><path d="M{52-3.6} {cy+5.11} A6.25 6.25 0 0 0 {52+3.6} {cy+5.11}" stroke="#000" stroke-width="1.2" fill="none"/>')
        o.append(txt(52, cy + 0.6, ref, 1.6) + txt(52, cy - 4.0, "1000µF 50V", 0.95, "400") + txt(49.6, cy - 1.9, "+", 1.6))
    o.append(f'<rect x="64.4" y="12.6" width="7.0" height="10.5" rx="0.6" {L}/>' + txt(68.0, 25.4, "18V~", 1.3))
    o.append(f'<rect x="13.7" y="28.4" width="7.6" height="10.3" rx="0.6" {L}/>' + txt(17.5, 27.3, "12V 1.7A", 1.1) + txt(15.0, 31.6, "+", 1.6) + txt(15.0, 36.8, "−", 1.8))
    o.append(txt(32, 30, "AP", 6.0) + txt(32, 34.5, "FUENTE 12 V · 1.7 A", 1.3))
    o.append(txt(32, 9.5, "Las piezas SMD van del otro lado", 1.0, "400"))
    o.append('</g></svg>'); return "\n".join(o)

here = os.path.dirname(os.path.abspath(__file__))
for name, txt_ in (("cobre_planchar.svg", cobre(True)), ("cobre_vista.svg", cobre()), ("montaje.svg", montaje()),
                   ("serigrafia_planchar.svg", lado_piezas(True)), ("serigrafia_vista.svg", lado_piezas(False))):
    open(os.path.join(here, name), "w").write(txt_)
print("SVG escritos")
