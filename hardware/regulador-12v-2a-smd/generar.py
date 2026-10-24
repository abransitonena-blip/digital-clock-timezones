"""Regulador conmutado 12 V / 2 A con LM2596S-12 (SMD), placa de una cara para planchar.
Coordenadas en mm, VISTA DESDE EL LADO DEL COBRE (las piezas SMD van soldadas de ese lado).
La hoja para planchar es el espejo de esta vista."""
import math, itertools, sys, os
W, H = 50, 44
CLEAR = 0.5                         # separación mínima entre redes distintas (baja tensión)
pads, traces = [], []
def smd(ref, pin, x, y, net, w, h): pads.append((ref, pin, x, y, net, "r", w, h))
def tht(ref, pin, x, y, net, d=3.0): pads.append((ref, pin, x, y, net, "o", d, d))
def tr(net, w, *pts): traces.append((net, w, list(pts)))
# ---------- piezas ----------
tht("J1", "+", 47, 5, "VR"); tht("J1", "-", 47, 10.08, "G")                      # entrada 16–35 V
smd("D1", "A", 42.9, 5, "VR", 2.5, 3.3); smd("D1", "K", 36.1, 5, "VI", 2.5, 3.3)  # SS54 contra polaridad invertida
UX = {5: 24.6, 4: 26.3, 3: 28.0, 2: 29.7, 1: 31.4}                               # TO-263-5, patas hacia arriba
UN = {1: "VI", 2: "SW", 3: "G", 4: "VO", 5: "G"}
for p, x in UX.items(): smd("U1", str(p), x, 8, UN[p], 1.1, 3.5)
smd("U1", "TAB", 28, 18.45, "G", 10.8, 9.6)
smd("C1", "+", 41, 13.2, "VI", 2.6, 4.0); smd("C1", "-", 41, 21.8, "G", 2.6, 4.0)  # 220 µF 50 V
smd("C2", "1", 34.6, 11.2, "VI", 1.8, 1.75); smd("C2", "2", 34.6, 14.4, "G", 1.8, 1.75)  # 1 µF 1206
smd("D2", "K", 5, 6.6, "SW", 3.3, 2.5); smd("D2", "A", 5, 13.4, "G", 3.3, 2.5)    # SS54 diodo de rueda libre
smd("L1", "1", 15, 7.6, "SW", 5.0, 3.2); smd("L1", "2", 15, 17.4, "VO", 5.0, 3.2) # 47 µH 12×12
smd("C3", "+", 8, 23.3, "VO", 2.6, 4.0); smd("C3", "-", 8, 31.7, "G", 2.6, 4.0)   # 470 µF 25 V
tht("J2", "+", 17.5, 27, "VO"); tht("J2", "-", 17.5, 32.08, "G")                  # salida 12 V
smd("R1", "1", 20.8, 24.2, "VO", 1.4, 1.2); smd("R1", "2", 20.8, 26.4, "LM", 1.4, 1.2)   # 2.2 k 0805
smd("D3", "A", 20.8, 29.2, "LM", 1.4, 1.2); smd("D3", "K", 20.8, 31.4, "G", 1.4, 1.2)    # LED 0805
for i, x in enumerate((3.5, W - 3.5)): pads.append((f"MH{i+1}", "", x, 41, f"MH{i+1}", "o", 3.2, 3.2))
# ---------- pistas ----------
tr("VR", 2.0, (47, 5), (42.9, 5))
tr("VI", 2.0, (36.1, 5), (36.1, 8)); tr("VI", 1.5, (31.6, 8), (41, 8), (41, 13.2)); tr("VI", 1.0, (34.6, 8), (34.6, 11.2))
tr("SW", 1.2, (29.7, 8), (29.7, 2.8)); tr("SW", 1.5, (29.7, 2.8), (5, 2.8), (5, 6.6)); tr("SW", 1.5, (15, 2.8), (15, 7.6))
tr("G", 1.0, (28, 8), (28, 14)); tr("G", 1.0, (24.6, 8), (24.6, 14)); tr("G", 1.2, (34.6, 14.4), (33, 14.4))
tr("G", 8.0, (28, 22), (28, 34)); tr("G", 4.0, (3.0, 36), (47, 36))
tr("G", 2.5, (41, 21.8), (41, 36)); tr("G", 2.5, (47, 10.08), (47, 36)); tr("G", 2.5, (8, 31.7), (8, 36))
tr("G", 2.0, (17.5, 32.08), (17.5, 36)); tr("G", 0.8, (20.8, 31.4), (20.8, 35))
tr("G", 2.5, (5, 13.4), (5, 15.5), (2.2, 15.5), (2.2, 36))
tr("VO", 2.0, (15, 17.4), (15, 21)); tr("VO", 2.0, (8, 21), (20.8, 21)); tr("VO", 2.0, (17.5, 21), (17.5, 27))
tr("VO", 0.8, (20.8, 21), (20.8, 24.2)); tr("VO", 0.8, (21, 21), (21, 5), (26.3, 5), (26.3, 7))   # FB
tr("LM", 0.6, (20.8, 26.4), (20.8, 29.2))
CU_TEXT = [(36, 27.2, 2.4, "AP"), (36, 31.0, 1.4, "12V 2A")]
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
def shape(p):           # (red, nombre, segmentos, radio, rect o None)
    r, pn, x, y, n, f, w, h = p
    if f == "r":
        x0, y0, x1, y1 = x-w/2, y-h/2, x+w/2, y+h/2
        return (n, f"{r}.{pn}", [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))], 0, (x0, y0, x1, y1))
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
    x0, y0, x1, y1 = text_box(x, y, h, t); box = ("T", t, [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))], 0, (x0, y0, x1, y1))
    for sh in shapes:
        d = dist(box, sh)
        if d < 1.0: errors.append(f"texto '{t}' a {d:.2f} mm de {sh[1]}")
if errors: print("\n".join(sorted(set(errors))[:40])); sys.exit(1)
print(f"DRC OK: placa {W}×{H} mm, {len(pads)} pads, separación mínima real {worst:.2f} mm")
# ---------- SVG ----------
def pts_d(pts): return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts)
def cobre(color="#000", fondo="#fff", espejo=False, ancho=None):
    k = ancho or f"{W}mm"; alto = f"{H}mm" if not ancho else f"{float(ancho[:-2])*H/W:.1f}mm"
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{k}" height="{alto}" viewBox="0 0 {W} {H}" font-family="Arial,Helvetica,sans-serif">',
         f'<rect x="0" y="0" width="{W}" height="{H}" fill="{fondo}" stroke="#000" stroke-width="0.25"/>',
         f'<g transform="translate({W} 0) scale(-1 1)">' if espejo else '<g>']
    for n, w, pts in traces: o.append(f'<path d="{pts_d(pts)}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')
    for r, pn, x, y, n, f, w, h in pads:
        if r.startswith("MH"): o.append(f'<circle cx="{x}" cy="{y}" r="{w/2+0.3}" fill="none" stroke="{color}" stroke-width="0.4"/><circle cx="{x}" cy="{y}" r="0.4" fill="{color}"/>'); continue
        if f == "r": o.append(f'<rect x="{x-w/2:.2f}" y="{y-h/2:.2f}" width="{w}" height="{h}" rx="0.2" fill="{color}"/>')
        else: o.append(f'<circle cx="{x}" cy="{y}" r="{w/2}" fill="{color}"/><circle cx="{x}" cy="{y}" r="0.55" fill="{fondo}"/>')
    for x, y, h, t in CU_TEXT: o.append(f'<text x="{x}" y="{y}" text-anchor="middle" font-weight="700" font-size="{h}" fill="{color}">{t}</text>')
    o.append('</g></svg>'); return "\n".join(o)

def montaje(k=1.0):
    """Vista de montaje desde el lado del cobre: cobre tenue y piezas con su forma real."""
    CU = "#e9c9a8"; L = 'fill="none" stroke="#111" stroke-width="0.3" stroke-linejoin="round"'
    def t(x, y, s, sz=1.3, a="middle", w="700", c="#111"): return f'<text x="{x}" y="{y}" font-size="{sz}" text-anchor="{a}" font-weight="{w}" fill="{c}">{s}</text>'
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W*k}mm" height="{H*k}mm" viewBox="0 0 {W} {H}" font-family="Arial,Helvetica,sans-serif">',
         f'<rect x="0" y="0" width="{W}" height="{H}" rx="1" fill="#fbf8f2" stroke="#555" stroke-width="0.3"/>']
    for n, w, pts in traces: o.append(f'<path d="{pts_d(pts)}" fill="none" stroke="{CU}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')
    for r, pn, x, y, n, f, w, h in pads:
        if r.startswith("MH"): o.append(f'<circle cx="{x}" cy="{y}" r="1.6" fill="#fff" stroke="#999" stroke-width="0.3"/>'); continue
        o.append(f'<rect x="{x-w/2:.2f}" y="{y-h/2:.2f}" width="{w}" height="{h}" rx="0.2" fill="#d9a877"/>' if f == "r" else
                 f'<circle cx="{x}" cy="{y}" r="{w/2}" fill="#d9a877"/><circle cx="{x}" cy="{y}" r="0.6" fill="#fff"/>')
    # U1 TO-263-5: cuerpo, patas y pestaña
    o.append(f'<rect x="22.9" y="11.4" width="10.2" height="9.4" rx="0.4" {L} fill-opacity="0"/>')
    for p, x in UX.items(): o.append(f'<path d="M{x} 7.2 V11.4" stroke="#111" stroke-width="0.5"/>')
    o.append(f'<circle cx="31.4" cy="12.6" r="0.45" fill="#111"/>' + t(28, 16.6, "U1", 1.6) + t(28, 18.4, "LM2596S-12", 1.05, w="400"))
    o.append(t(31.4, 4.95, "1", 0.9, w="400") + t(24.6, 4.95, "5", 0.9, w="400"))
    # diodos SS54 con franja del cátodo
    o.append(f'<rect x="35.0" y="2.3" width="9.0" height="5.4" rx="0.5" {L}/><rect x="35.0" y="2.3" width="1.3" height="5.4" fill="#111"/>' + t(39.6, 9.6, "D1 SS54", 1.05))
    o.append(f'<rect x="2.3" y="5.4" width="5.4" height="9.2" rx="0.5" {L}/><rect x="2.3" y="5.4" width="5.4" height="1.3" fill="#111"/>' + t(5, 9.8, "D2", 1.2) + t(5, 11.2, "SS54", 0.9, w="400"))
    # bobina 12×12
    o.append(f'<rect x="9" y="6.5" width="12" height="12" rx="1.5" {L}/><circle cx="15" cy="12.5" r="4.2" {L}/>' + t(15, 12.4, "L1", 1.5) + t(15, 14.0, "47µH", 1.0, w="400"))
    # electrolíticos SMD (base con esquinas cortadas del lado +)
    def ecap(cx, cy, ref, val):
        a = 5.15; c = 1.6
        d_ = f"M{cx-a+c} {cy-a} H{cx+a-c} L{cx+a} {cy-a+c} V{cy+a} H{cx-a} V{cy-a+c} Z"
        return (f'<path d="{d_}" {L}/><circle cx="{cx}" cy="{cy}" r="4.6" {L}/>'
                f'<path d="M{cx-4.3} {cy+1.7} A4.6 4.6 0 0 0 {cx+4.3} {cy+1.7} Z" fill="#111"/>'
                + t(cx, cy - 0.6, ref, 1.5) + t(cx, cy + 0.9, val, 0.95, w="400") + t(cx - 4.0, cy - 3.0, "+", 1.6))
    o.append(ecap(41, 17.5, "C1", "220µF 50V") + ecap(8, 27.5, "C3", "470µF 25V"))
    o.append(f'<rect x="33.5" y="10.0" width="2.2" height="5.6" rx="0.3" {L}/>' + t(34.6, 17.3, "C2", 0.9) + t(34.6, 18.4, "1µF", 0.75, w="400"))
    o.append(f'<rect x="19.9" y="23.5" width="1.8" height="3.6" rx="0.3" {L}/>' + t(22.4, 25.6, "R1 2.2k", 0.9, "start"))
    o.append(f'<rect x="19.9" y="28.5" width="1.8" height="3.6" rx="0.3" {L}/><path d="M20.1 31.6 H21.5" stroke="#111" stroke-width="0.35"/>' + t(22.4, 30.6, "LED", 0.9, "start"))
    # bornes (van del otro lado; aquí se ven sus patas)
    o.append(t(44.6, 5.5, "+", 1.8, c="#c00") + t(44.6, 10.6, "−", 2.0) )
    o.append(t(15.2, 27.5, "+", 1.8, c="#c00") + t(15.2, 32.6, "−", 2.0) + t(17.5, 23.3, "SALIDA", 0.85) + t(17.5, 24.5, "12 V", 0.85))
    o.append('<text x="48.75" y="23" font-size="0.95" text-anchor="middle" font-weight="700" fill="#111" transform="rotate(-90 48.75 23)">ENTRADA 16–35 V</text>')
    for x, y, h, s in CU_TEXT: o.append(t(x, y, s, h, c="#c49a6c"))
    o.append('</svg>'); return "\n".join(o)

here = os.path.dirname(os.path.abspath(__file__))
for name, txt in (("cobre_planchar.svg", cobre(espejo=True)), ("cobre_vista.svg", cobre()), ("montaje.svg", montaje(1.0))):
    open(os.path.join(here, name), "w").write(txt)
print("SVG escritos")
