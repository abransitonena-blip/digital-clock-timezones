"""Fuente capacitiva de 2 canales, versión completa en placa de 6 × 10 cm (una cara).
Entrada: bornera, fusible 5×20 con patas, varistor. Por canal: X2 (patas a 15 mm), 1 MΩ, 150 Ω 1 W parada,
KBP307, electrolítico de 17 mm, zener 5 W, 220 kΩ, 100 Ω parada, LED testigo y bornera.
4 agujeros M3 con anillo y marco de cobre. Coordenadas en mm, vistas desde el lado de componentes."""
import math, itertools, sys, os
W, H = 62, 100
PAD, DRILL, TW, CLEAR, CLEAR_FR = 3.0, 0.8, 2.0, 1.5, 2.5
BR_P, BR_W, BR_H = 3.9, 2.2, 3.4
MH = [(4.5, 4.5), (W-4.5, 4.5), (4.5, H-4.5), (W-4.5, H-4.5)]
FR = 1.6                                   # marco de cobre (línea al centro)
pads, traces = [], []
def pad(ref, pin, x, y, net, f="o", w=PAD, h=PAD): pads.append((ref, pin, x, y, net, f, w, h))
def tr(net, *pts): traces.append((net, list(pts)))
LY, NY = 8.5, 14.5
XL, XN = 6.5, 12.5                          # bajadas de L y N en la columna izquierda
# ---- entrada: J0 → F1 → L ; J0 → N ; varistor entre L y N
pad("J0", "L", XL, 62, "LIN"); pad("J0", "N", XL, 67, "N")
pad("F1", "1", XL, 47, "LIN"); pad("F1", "2", XL, 21.6, "L")
tr("LIN", (XL, 62), (XL, 47))
tr("L", (XL, 21.6), (XL, 12.5), (XL + 4, LY))
tr("N", (XL, 67), (XN, 67), (XN, NY))
pad("RV1", "1", XL, 16.6, "L"); pad("RV1", "2", XN, 21.3, "N")
for k in range(2):
    s = str(k+1); X = 16 + k*22
    xc, xr, xn = X + 5, X + 11.5, X + 17
    B, A1, P, M, O, T = "B"+s, "AC"+s, "P"+s, "M"+s, "O"+s, "T"+s
    pad("C"+s, "1", xc, LY, "L"); pad("C"+s, "2", xc, LY + 15, B)          # X2 a 15 mm, pasa sobre N
    pad("RD"+s, "1", xr, LY, "L"); pad("RD"+s, "2", xr, LY + 15, B)        # 1 MΩ acostada a 15 mm
    tr(B, (xc, LY + 15), (xr, LY + 15))
    pad("RS"+s, "1", xr, 27, B); pad("RS"+s, "2", xr, 32, A1)               # 150 Ω 1 W parada
    tr(B, (xr, LY + 15), (xr, 27))
    by = 42
    bx = [X + 3.2 + i*BR_P for i in range(4)]
    for i, (pn, n) in enumerate((("+", P), ("~1", A1), ("~2", "N"), ("-", M))):
        pad("BR"+s, pn, bx[i], by, n, "v", BR_W, BR_H)
    tr(A1, (xr, 32), (bx[1], 36.8), (bx[1], by))
    tr("N", (xn, NY), (xn, 37.8), (bx[2] + 1.5, 37.8), (bx[2], 39.3), (bx[2], by))
    xp, xm = X + 1.5, X + 16.5
    tr(P, (bx[0], by), (bx[0], 45.5), (xp, 47.2), (xp, 73))
    tr(M, (bx[3], by), (bx[3], 45.5), (xm, 47.6), (xm, 84), (X + 11.2, 88.5))
    cy = 53.5
    pad("CE"+s, "+", X + 6.5, cy, P); pad("CE"+s, "-", X + 11.5, cy, M)
    tr(P, (xp, cy), (X + 6.5, cy)); tr(M, (xm, cy), (X + 11.5, cy))
    pad("ZD"+s, "K", xp, 65, P); pad("ZD"+s, "A", xm, 65, M)                # zener 5 W a 15 mm
    pad("RC"+s, "+", xp, 70, P); pad("RC"+s, "-", xm, 70, M)                # 220 kΩ a 15 mm
    pad("RO"+s, "1", xp, 73, P); pad("RO"+s, "2", xp, 78, O)                # 100 Ω parada
    pad("LT"+s, "A", xp, 82.5, O); pad("LT"+s, "K", X + 6.58, 82.5, T)      # LED testigo 3 mm
    tr(O, (xp, 78), (xp, 82.5))
    pad("J"+s, "+", X + 6.2, 88.5, T); pad("J"+s, "-", X + 11.2, 88.5, M)
    tr(T, (X + 6.58, 82.5), (X + 6.2, 88.5))
tr("L", (XL + 4, LY), (16 + 22 + 11.5, LY))
tr("N", (XN, NY), (16 + 22 + 17, NY))
for i, (x, y) in enumerate(MH): pad("MH"+str(i+1), "", x, y, "FRAME", "m", 5.0, 5.0)
FRAME = [((FR, FR), (W-FR, FR)), ((W-FR, FR), (W-FR, H-FR)), ((W-FR, H-FR), (FR, H-FR)), ((FR, H-FR), (FR, FR))]
FW = 0.8
CU_TEXT = [(36.0, 96.4, 2.2, "FUENTE LED 2CH 127V"), (9.5, 91.0, 2.0, "V1")]
def text_box(x, y, h, t): w = 0.6*h*len(t); return (x - w/2, y - h*0.8, x + w/2, y + h*0.05)

# ---------- chequeo de reglas ----------
def seg_pt(p, a, b):
    ax, ay = a; bx_, by_ = b; px, py = p
    dx, dy = bx_-ax, by_-ay; L2 = dx*dx+dy*dy
    t = 0 if L2 == 0 else max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/L2))
    return math.hypot(px-(ax+t*dx), py-(ay+t*dy))
def seg_seg(a, b, c, d):
    def ccw(p, q, r): return (r[1]-p[1])*(q[0]-p[0]) - (q[1]-p[1])*(r[0]-p[0])
    if (ccw(a,b,c)*ccw(a,b,d) < 0) and (ccw(c,d,a)*ccw(c,d,b) < 0): return 0
    return min(seg_pt(a,c,d), seg_pt(b,c,d), seg_pt(c,a,b), seg_pt(d,a,b))
def shape(p):
    r, pn, x, y, n, f, w, h = p
    if f == "v": L = (h - w)/2; return (n, f"{r}.{pn}", ((x, y-L), (x, y+L)), w/2)
    return (n, f"{r}.{pn}", ((x, y), (x, y)), w/2)
shapes = [shape(p) for p in pads]
for n, pts in traces:
    for a, b in zip(pts, pts[1:]): shapes.append((n, f"pista {n}", (a, b), TW/2))
for a, b in FRAME: shapes.append(("FRAME", "marco", (a, b), FW/2))
for (mx_, my_) in MH:   # unión anillo-marco en la esquina
    cx, cy_ = (FR if mx_ < W/2 else W-FR), (FR if my_ < H/2 else H-FR)
    shapes.append(("FRAME", "marco", ((mx_, my_), (cx, cy_)), 1.0))
errors, worst = [], 99
for s1, s2 in itertools.combinations(shapes, 2):
    if s1[0] == s2[0]: continue
    d = seg_seg(*s1[2], *s2[2]) - s1[3] - s2[3]; worst = min(worst, d)
    lim = CLEAR_FR if "FRAME" in (s1[0], s2[0]) else CLEAR
    if d < lim - 1e-6: errors.append(f"separación {d:.2f} mm entre {s1[1]} y {s2[1]}")
for net in set(s[0] for s in shapes):
    ss = [s for s in shapes if s[0] == net]; seen = {0}; st = [0]
    while st:
        i = st.pop()
        for j in range(len(ss)):
            if j not in seen and seg_seg(*ss[i][2], *ss[j][2]) <= ss[i][3]+ss[j][3]: seen.add(j); st.append(j)
    if len(seen) != len(ss): errors.append(f"red {net} cortada: " + ", ".join(ss[k][1] for k in range(len(ss)) if k not in seen))
for (x, y, h, t) in CU_TEXT:
    x0, y0, x1, y1 = text_box(x, y, h, t)
    edges = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
    for sh in shapes:
        (a, b), rr = sh[2], sh[3]
        inside = x0 <= a[0] <= x1 and y0 <= a[1] <= y1
        d = 0 if inside else min(seg_seg(a, b, *e) for e in edges) - rr
        if d < 1.0: errors.append(f"texto '{t}' a {d:.2f} mm de {sh[1]}")
if errors: print("\n".join(errors[:40])); sys.exit(1)
print(f"DRC OK: placa {W}×{H} mm, {len(pads)} pads, separación mínima real {worst:.2f} mm")

# ---------- SVG ----------
def path_d(pts): return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts)
def head(): return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}" font-family="Arial,Helvetica,sans-serif">',
                    f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fff" stroke="#999" stroke-width="0.2"/>']
def pad_svg(p, fill):
    r, pn, x, y, n, f, w, h = p
    if f == "v": return f'<rect x="{x-w/2:.2f}" y="{y-h/2:.2f}" width="{w}" height="{h}" rx="{w/2}" fill="{fill}"/>'
    return f'<circle cx="{x}" cy="{y}" r="{w/2}" fill="{fill}"/>'
def copper_svg():
    o = head()
    o.append(f'<rect x="{FR}" y="{FR}" width="{W-2*FR}" height="{H-2*FR}" rx="2" fill="none" stroke="#000" stroke-width="{FW}"/>')
    for (mx_, my_) in MH:
        cx, cy_ = (FR if mx_ < W/2 else W-FR), (FR if my_ < H/2 else H-FR)
        o.append(f'<path d="M{mx_} {my_} L{cx} {cy_}" stroke="#000" stroke-width="2"/>')
    for n, pts in traces: o.append(f'<path d="{path_d(pts)}" fill="none" stroke="#000" stroke-width="{TW}" stroke-linecap="round" stroke-linejoin="round"/>')
    for p in pads: o.append(pad_svg(p, "#000"))
    for p in pads:
        rr = 1.6 if p[5] == "m" else DRILL/2
        o.append(f'<circle cx="{p[2]}" cy="{p[3]}" r="{rr}" fill="#fff"/>')
    for (x, y, h, t) in CU_TEXT:
        o.append(f'<g transform="translate({x} {y}) scale(-1 1)"><text x="0" y="0" text-anchor="middle" font-weight="700" font-size="{h}" fill="#000">{t}</text></g>')
    o.append('</svg>'); return "\n".join(o)

def silk_svg(espejo=False, c="#000"):
    L = f'fill="none" stroke="{c}" stroke-width="0.35"'
    def t(x, y, s_, sz=1.5, a="middle", w="700", rot=None):
        tf = f' transform="rotate({rot} {x} {y})"' if rot is not None else ""
        return f'<text x="{x:.2f}" y="{y:.2f}" font-size="{sz}" text-anchor="{a}" font-weight="{w}" fill="{c}"{tf}>{s_}</text>'
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}" font-family="Arial,Helvetica,sans-serif">',
         f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fff"/>',
         f'<g transform="translate({W} 0) scale(-1 1)">' if espejo else '<g>']
    o.append(f'<rect x="0.8" y="0.8" width="{W-1.6}" height="{H-1.6}" rx="2.5" {L}/>')
    for p in pads:
        o.append(f'<circle cx="{p[2]}" cy="{p[3]}" r="{2.0 if p[5] == "m" else 0.9}" {L}/>')
    # entrada
    o.append(f'<rect x="2.6" y="58.6" width="7.8" height="11.8" rx="0.6" {L}/>' + t(6.5, 57.6, "127V~", 1.3) + t(11.6, 62.6, "L", 1.4) + t(11.6, 67.6, "N", 1.4))
    o.append(f'<rect x="{XL-2.6}" y="25" width="5.2" height="20.6" rx="2.4" {L}/>' + t(XL+0.5, 35.3, "F1 T500mA", 1.2, rot=-90))
    o.append(f'<path d="M{XL+1.4} 14.6 L{XN+1.8} 19.6 L{XN-1.4} 23.3 L{XL-1.8} 18.3 Z" {L}/>' + t(XN-0.8, 26.4, "RV1", 1.2, "start") + t(XN-0.8, 28.0, "10D241K", 0.95, "start", "400"))
    for k in range(2):
        s_ = str(k+1); X = 16 + k*22; xc, xr, xp, xm = X+5, X+11.5, X+1.5, X+16.5
        o.append(f'<rect x="{xc-4.5}" y="{LY-1.5}" width="9" height="18" rx="1" {L}/>')
        o.append(t(xc, LY+7.2, "C"+s_, 1.7) + t(xc, LY+9.2, "X2", 1.2, w="400") + t(xc, LY+11, "474J", 1.1, w="400"))
        o.append(f'<rect x="{xr-1.3}" y="{LY+5}" width="2.6" height="5" rx="1.1" {L}/>' + t(xr+0.5, LY+3.6, "1M", 1.1, w="400"))
        o.append(f'<circle cx="{xr}" cy="27" r="1.8" {L}/>' + t(xr+3.6, 29.8, "150Ω", 1.1, w="400") + t(xr+3.6, 31.4, "1W", 1.0, w="400"))
        o.append(f'<path d="M{X+1.6} 40.2 h15.4 v3.6 h-15.4 z M{X+1.6} 41.4 L{X+2.8} 40.2" {L}/>')
        o.append(t(X+3.2, 39.3, "+", 1.6) + t(X+3.2+3*BR_P, 39.3, "−", 1.6))
        o.append(f'<circle cx="{X+9}" cy="53.5" r="8.5" {L}/><path d="M{X+12.5} {53.5-7.75} A8.5 8.5 0 0 1 {X+12.5} {53.5+7.75}" stroke="{c}" stroke-width="1.6" fill="none"/>')
        o.append(t(X+4.4, 54.3, "+", 2.2) + t(X+9, 58.6, "47µF", 1.2, w="400") + t(X+9, 60.2, "250V", 1.2, w="400") + t(X+9, 49.6, "CE"+s_, 1.4))
        o.append(f'<rect x="{X+4.3}" y="62.4" width="9.5" height="5.2" rx="2" {L}/><path d="M{X+5.6} 62.4 V67.6" stroke="{c}" stroke-width="0.9"/>' + t(X+9.6, 65.6, "ZD"+s_, 1.3))
        o.append(f'<rect x="{X+5.5}" y="68.8" width="7" height="2.4" rx="1" {L}/>' + t(X+9, 73.7, "220k", 1.1, w="400"))
        o.append(f'<circle cx="{xp}" cy="73" r="1.6" {L}/>' + t(xp+2.2, 76.2, "100Ω", 1.0, "start", "400"))
        o.append(f'<circle cx="{X+4.04}" cy="82.5" r="1.9" {L}/><path d="M{X+5.94} 81.1 V83.9" stroke="{c}" stroke-width="0.35"/>' + t(X+11.5, 82.0, "testigo", 1.0, w="400"))
        o.append(f'<rect x="{X+3.7}" y="85.3" width="10" height="7" rx="0.5" {L}/>' + t(X+6.2, 84.6, "+", 1.5) + t(X+11.2, 84.6, "−", 1.5) + t(X+8.7, 94.0, "SALIDA "+s_, 1.3))
    # mini tabla y recuadro de nombre en la columna izquierda
    o.append(f'<rect x="2.4" y="71.4" width="11.6" height="10.6" rx="0.6" {L}/>' + t(8.2, 73.4, "C (X2) · LED", 1.0))
    for i, (cc, ll) in enumerate((("474", "1–10"), ("564", "15–20"), ("684", "25"), ("824", "30"))):
        o.append(t(3.4, 75.5 + i*1.7, cc, 1.0, "start") + t(13.2, 75.5 + i*1.7, ll, 1.0, "end", "400"))
    o.append(f'<rect x="2.4" y="83.0" width="11.6" height="8.6" rx="0.6" {L}/>' + t(3.2, 85.0, "Nombre:", 0.95, "start", "400") + t(3.2, 89.6, "Fecha:", 0.95, "start", "400"))
    o.append(f'<path d="M3.2 87.6 H13.4 M8 89.8 H13.4" stroke="{c}" stroke-width="0.2"/>')
    o.append(t(36, 3.6, "FUENTE LED 2 CANALES · 127 V", 1.6) + t(36, 97.2, "PELIGRO: 127 V · NO TOCAR CONECTADA", 1.25))
    o.append(f'<path d="M18.3 95.0 l-1.0 1.9 h0.9 l-0.6 1.5 l1.6 -2.1 h-0.9 l0.7 -1.3 z" fill="{c}"/>')
    o.append('</g></svg>'); return "\n".join(o)

here = os.path.dirname(os.path.abspath(__file__))
open(os.path.join(here, "cobre_planchar.svg"), "w").write(copper_svg())
open(os.path.join(here, "serigrafia_planchar.svg"), "w").write(silk_svg(True))
open(os.path.join(here, "serigrafia_vista.svg"), "w").write(silk_svg(False))
print("SVG escritos")
