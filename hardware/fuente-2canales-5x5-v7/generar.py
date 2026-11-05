"""Fuente capacitiva de 2 canales en placa de 5 × 5 cm, con las piezas medidas por el usuario:
KBP307 (patas a ~4 mm), X2 con patas a 15 mm, electrolítico de 17 mm (patas a 5 mm), resistencias paradas.
Dos filas, la de abajo es espejo de la de arriba. Coordenadas en mm, vistas desde el lado de componentes."""
import math, itertools, sys, os
W, H = 50, 50
PAD, DRILL, TW, CLEAR = 3.0, 0.8, 1.8, 1.5
MH_R = 2.2
KP = 3.9                        # paso del KBP307
KW, KH = 3.4, 2.2               # pad ovalado del KBP (acostado)
R12 = (2.0, 1.6)                # 1206 vertical: pads 2.0 ancho × 1.6 alto a 3.3 mm
pads, traces = [], []
def tht(ref, pin, x, y, net): pads.append((ref, pin, x, y, net, "o", PAD, PAD))
def smd(ref, pin, x, y, net, w, h): pads.append((ref, pin, x, y, net, "r", w, h))
def tr(net, *pts): traces.append((net, list(pts)))
XL, XN = 3.0, 8.0               # línea L y línea N (verticales)
def canal(s, f):
    """f(y) convierte la coordenada de la fila de arriba a la de esta fila (espejo para la de abajo)."""
    Y = f
    B, A1, PP, M, D = "B"+s, "AC"+s, "P"+s, "M"+s, "R"+s
    tht("RD"+s, "L", 8.5, Y(4.5), "L"); tht("RD"+s, "B", 13.5, Y(4.5), B)     # 1 MΩ parada
    tht("C"+s, "L", XL, Y(12), "L"); tht("C"+s, "B", 18, Y(12), B)            # X2, patas a 15 mm
    tr("L", (XL, Y(12)), (8.5, Y(4.5))); tr(B, (13.5, Y(4.5)), (18, Y(4.5)), (18, Y(12)))
    tht("RS"+s, "B", 21, Y(12), B); tht("RS"+s, "A", 25.6, Y(10), A1)          # 150 Ω parada
    tr(B, (18, Y(12)), (21, Y(12)))
    ky = [6.15, 10.05, 13.95, 17.85]
    nets = [PP, A1, "N", M]
    for i in range(4): pads.append(("BR"+s, ["+", "~1", "~2", "-"][i], 30, Y(ky[i]), nets[i], "r", KW, KH))
    tr(A1, (25.6, Y(10)), (30, Y(10.05)))
    tr("N", (XN, Y(19)), (25.9, Y(19)), (25.9, Y(13.95)), (30, Y(13.95)))
    # + : al borne y al electrolítico
    tht("J"+s, "+", 38.5, Y(3.5), PP); tht("J"+s, "-", 43.5, Y(3.5), M)
    tht("CE"+s, "+", 38.5, Y(16), PP); tht("CE"+s, "-", 43.5, Y(16), M)
    tr(PP, (30, Y(6.15)), (38.5, Y(6.15)), (38.5, Y(3.5))); tr(PP, (38.5, Y(6.15)), (38.5, Y(16)))
    tr(M, (43.5, Y(3.5)), (43.5, Y(16))); tr(M, (30, Y(17.85)), (32.75, Y(20.6)), (43.5, Y(20.6)), (43.5, Y(16)))
    # descarga del electrolítico: 220 kΩ de patitas, acostada a la izquierda del puente
    # (pasa por encima de las pistas AC y N, como un puente de cable)
    tht("RC"+s, "+", 26.6, Y(4.4), PP); tht("RC"+s, "-", 27.4, Y(22.6), M)
    tr(PP, (26.6, Y(4.4)), (30, Y(6.15))); tr(M, (27.4, Y(22.6)), (31.2, Y(19.05)))
canal("1", lambda y: y)
canal("2", lambda y: H - y)
pads.append(("WL", "", XL, 31.2, "L", "o", 3.5, 3.5)); pads.append(("WN", "", 12.2, 25, "N", "o", 3.5, 3.5))
tht("RV1", "1", XL, 21.3, "L"); tht("RV1", "2", XN, 26.8, "N")
tr("L", (XL, 12), (XL, 38)); tr("N", (XN, 19), (XN, 31)); tr("N", (XN, 25), (12.2, 25))
for i, y in enumerate((3.4, H - 3.4)): pads.append(("MH"+str(i+1), "", 3.4, y, "MH"+str(i+1), "o", 2*MH_R, 2*MH_R))
# texto en el cobre: (x, y, alto, texto); se dibuja en espejo y se revisa como rectángulo
CU_TEXT = [(19.5, 26.0, 1.8, "AP 127V"), (47.4, 4.4, 2.2, "S1"), (47.4, 47.0, 2.2, "S2")]
def text_box(x, y, h, t): w = 0.62*h*len(t); return (x - w/2, y - h*0.8, x + w/2, y + h*0.05)
# ---------- chequeo de reglas ----------
def seg_pt(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx-ax, by-ay; L2 = dx*dx+dy*dy
    t = 0 if L2 == 0 else max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/L2))
    return math.hypot(px-(ax+t*dx), py-(ay+t*dy))
def seg_seg(a, b, c, d):
    def ccw(p, q, r): return (r[1]-p[1])*(q[0]-p[0]) - (q[1]-p[1])*(r[0]-p[0])
    if (ccw(a,b,c)*ccw(a,b,d) < 0) and (ccw(c,d,a)*ccw(c,d,b) < 0): return 0
    return min(seg_pt(a,c,d), seg_pt(b,c,d), seg_pt(c,a,b), seg_pt(d,a,b))
def shape(p):
    r, pn, x, y, n, f, w, h = p
    if f == "r":
        rad = min(w, h)/2; L = (max(w, h) - min(w, h))/2
        g = ((x-L, y), (x+L, y)) if w >= h else ((x, y-L), (x, y+L))
        return (n, f"{r}.{pn}", g, rad)
    return (n, f"{r}.{pn}", ((x, y), (x, y)), w/2)
shapes = [shape(p) for p in pads]
for n, pts in traces:
    for a, b in zip(pts, pts[1:]): shapes.append((n, f"pista {n}", (a, b), TW/2))
errors, worst = [], 99
for s1, s2 in itertools.combinations(shapes, 2):
    if s1[0] == s2[0]: continue
    d = seg_seg(*s1[2], *s2[2]) - s1[3] - s2[3]; worst = min(worst, d)
    if d < CLEAR - 1e-6: errors.append(f"separación {d:.2f} mm entre {s1[1]} y {s2[1]}")
for net in set(s[0] for s in shapes):
    ss = [s for s in shapes if s[0] == net]; seen = {0}; st = [0]
    while st:
        i = st.pop()
        for j in range(len(ss)):
            if j not in seen and seg_seg(*ss[i][2], *ss[j][2]) <= ss[i][3]+ss[j][3]: seen.add(j); st.append(j)
    if len(seen) != len(ss): errors.append(f"red {net} cortada: " + ", ".join(ss[k][1] for k in range(len(ss)) if k not in seen))
for p in pads:
    r, pn, x, y, n, f, w, h = p
    if x - w/2 < 1 or x + w/2 > W - 1 or y - h/2 < 1 or y + h/2 > H - 1: errors.append(f"{r}.{pn} fuera de la placa")
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
def pad_svg(p, fill):
    r, pn, x, y, n, f, w, h = p
    if f == "r": return f'<rect x="{x-w/2:.2f}" y="{y-h/2:.2f}" width="{w}" height="{h}" rx="{min(w,h)/2}" fill="{fill}"/>'
    return f'<circle cx="{x}" cy="{y}" r="{w/2}" fill="{fill}"/>'
def head(): return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}" font-family="Arial,Helvetica,sans-serif">',
                    f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fff" stroke="#000" stroke-width="0.3"/>']
def T(x, y, s, sz=1.6, a="middle", w="700", rot=None, c="#000"):
    tf = f' transform="rotate({rot} {x} {y})"' if rot is not None else ""
    return f'<text x="{x:.2f}" y="{y:.2f}" font-size="{sz}" text-anchor="{a}" font-weight="{w}" fill="{c}"{tf}>{s}</text>'
S_ = 'fill="none" stroke="#000" stroke-width="0.35"'
def is_hole(p): return p[5] == "o" or p[0].startswith("BR")
def copper_svg():
    o = head()
    for n, pts in traces: o.append(f'<path d="{path_d(pts)}" fill="none" stroke="#000" stroke-width="{TW}" stroke-linecap="round" stroke-linejoin="round"/>')
    for p in pads: o.append(pad_svg(p, "#000"))
    for p in pads:
        if is_hole(p): o.append(f'<circle cx="{p[2]}" cy="{p[3]}" r="{1.6 if p[0].startswith("MH") else DRILL/2}" fill="#fff"/>')
    for (x, y, h, t) in CU_TEXT:
        o.append(f'<g transform="translate({x} {y}) scale(-1 1)"><text x="0" y="0" text-anchor="middle" font-weight="700" font-size="{h}" fill="#000">{t}</text></g>')
    o.append('</svg>'); return "\n".join(o)
def top_svg():
    o = head()
    for n, pts in traces: o.append(f'<path d="{path_d(pts)}" fill="none" stroke="#efdcc6" stroke-width="{TW}" stroke-linecap="round" stroke-linejoin="round"/>')
    for p in pads:
        if not is_hole(p): o.append(f'<rect x="{p[2]-p[6]/2:.2f}" y="{p[3]-p[7]/2:.2f}" width="{p[6]}" height="{p[7]}" rx="{min(p[6],p[7])/2}" fill="#e6e6e6"/>')
    o.append(f'<rect x="1.0" y="21.3" width="9" height="7.4" {S_}/>' + T(13.5, 25.6, "J0 127V", 1.4, "start"))
    for s, f in (("1", lambda y: y), ("2", lambda y: H - y)):
        Y = f
        o.append(f'<rect x="1.5" y="{min(Y(7),Y(17)):.2f}" width="18" height="10" rx="1" {S_}/>' + T(10.5, Y(12)+0.6, "C"+s+" X2", 1.7))
        o.append(f'<rect x="8" y="{Y(4)-1.25:.2f}" width="5" height="2.5" rx="1" {S_}/>' + T(10.5, Y(4)+(-1.8 if s == "1" else 2.9), "RD 1M", 1.2, w="400"))
        o.append(f'<circle cx="21" cy="{Y(12)}" r="1.7" {S_}/>' + T(23.3, Y(13.6) if s == "1" else Y(13.6)+1.2, "RS", 1.2))
        o.append(f'<rect x="28" y="{min(Y(4.5),Y(19.5)):.2f}" width="4" height="15" rx="0.5" {S_}/>')
        o.append(f'<path d="M28 {Y(4.5)} L29.4 {Y(4.5)+(1.4 if s == "1" else -1.4)}" stroke="#000" stroke-width="0.35"/>')
        o.append(T(30, Y(2.9) if s == "1" else Y(2.9)+1, "BR"+s, 1.3) + T(30, Y(6.15)+0.6, "+", 1.8) + T(30, Y(17.85)+0.6, "−", 1.8))
        o.append(f'<circle cx="41" cy="{Y(16)}" r="8.5" {S_}/><path d="M43.5 {Y(16)-7.6} A8.5 8.5 0 0 1 43.5 {Y(16)+7.6}" stroke="#000" stroke-width="2" fill="none" opacity="0.3"/>')
        o.append(T(41, Y(16)+(4.5 if s == "1" else -3.5), "CE"+s, 1.7) + T(36.7, Y(16)+0.7, "+", 2.2) + T(45.6, Y(16)+0.7, "−", 2.2))
        o.append(f'<rect x="35.5" y="{min(Y(0),Y(7.4)):.2f}" width="10" height="7.4" {S_}/>' + T(48.6, Y(3.5)+0.5, "S"+s, 1.4) + T(38, Y(3.5)+(2.6 if s == "1" else -1.6), "+", 1.4) + T(43, Y(3.5)+(2.6 if s == "1" else -1.6), "−", 1.4))
    for p in pads:
        if is_hole(p): o.append(f'<circle cx="{p[2]}" cy="{p[3]}" r="0.55" fill="#000"/>')
    o.append('</svg>'); return "\n".join(o)
def bottom_svg():
    mx = lambda x: W - x
    o = head()
    for n, pts in traces: o.append(f'<path d="{path_d([(mx(x), y) for x, y in pts])}" fill="none" stroke="#d9a877" stroke-width="{TW}" stroke-linecap="round" stroke-linejoin="round"/>')
    for p in pads:
        r, pn, x, y, n, f, w, h = p
        o.append(pad_svg((r, pn, mx(x), y, n, f, w, h), "#c98b4e"))
        if is_hole(p): o.append(f'<circle cx="{mx(x)}" cy="{y}" r="0.5" fill="#fff"/>')
    for s, f in (("1", lambda y: y), ("2", lambda y: H - y)):
        for yy in (10.25, 15.25):
            o.append(f'<rect x="{mx(34.4)-0.85}" y="{f(yy)-1.6:.2f}" width="1.7" height="3.2" fill="#222"/>')
        o.append(T(mx(34.4)+1.6, f(12.8)+0.5, "RC 104 ×2", 1.2, "start"))
    o.append(T(W/2, 25.6, "LADO DEL COBRE · visto de frente", 1.3, w="400"))
    o.append('</svg>'); return "\n".join(o)

def silk_svg(espejo=False, c="#000"):
    """Serigrafía del lado de componentes, con símbolo electrónico en cada pieza. espejo=True para planchar."""
    LW = 0.3
    L = f'fill="none" stroke="{c}" stroke-width="{LW}" stroke-linecap="round" stroke-linejoin="round"'
    def t(x, y, s_, sz=1.4, a="middle", w="700", rot=None):
        tf = f' transform="rotate({rot} {x:.2f} {y:.2f})"' if rot is not None else ""
        return f'<text x="{x:.2f}" y="{y:.2f}" font-size="{sz}" text-anchor="{a}" font-weight="{w}" fill="{c}"{tf}>{s_}</text>'
    def g(x, y, body, rot=0, k=1.0): return f'<g transform="translate({x:.2f} {y:.2f}) rotate({rot}) scale({k})">{body}</g>'
    # símbolos (centrados en 0,0; ~4 mm de largo)
    RES = f'<path d="M-2.2 0 H-1.2 M1.2 0 H2.2" {L}/><rect x="-1.2" y="-0.5" width="2.4" height="1" {L}/>'
    CAP = f'<path d="M-2 0 H-0.35 M0.35 0 H2 M-0.35 -1.1 V1.1 M0.35 -1.1 V1.1" {L}/>'
    ECAP = f'<path d="M-2 0 H-0.4 M0.5 0 H2 M-0.4 -1.2 V1.2" {L}/><path d="M0.9 -1.2 Q0.3 0 0.9 1.2" {L}/><path d="M-1.4 -1.3 h0.8 M-1.0 -1.7 v0.8" {L}/>'
    VAR = RES + f'<path d="M-1.6 0.9 L1.2 -0.9 L1.7 -0.9" {L}/>'
    LED = (f'<path d="M-2 0 H-0.6 M0.6 0 H2 M0.6 -0.8 V0.8" {L}/><path d="M-0.6 -0.8 L0.6 0 L-0.6 0.8 Z" fill="{c}"/>'
           f'<path d="M-0.1 -1.0 l0.7 -0.7 M0.5 -1.0 l0.7 -0.7" {L}/><path d="M0.6 -1.7 l-0.3 0.05 l0.25 0.25 z M1.2 -1.7 l-0.3 0.05 l0.25 0.25 z" fill="{c}"/>')
    BRIDGE = (f'<path d="M0 -1.8 L1.8 0 L0 1.8 L-1.8 0 Z" {L}/>'
              f'<path d="M-0.5 -0.3 L0.4 -0.3 L-0.05 0.4 Z" fill="{c}"/><path d="M-0.5 0.4 H0.4" {L}/>'
              f'<text x="-2.6" y="0.5" font-size="1.2" text-anchor="middle" fill="{c}">~</text><text x="2.6" y="0.5" font-size="1.2" text-anchor="middle" fill="{c}">~</text>')
    AC = f'<circle cx="0" cy="0" r="1.2" {L}/><path d="M-0.7 0 Q-0.35 -0.6 0 0 T0.7 0" {L}/>'
    WARN = f'<path d="M0 -1.6 L1.6 1.2 H-1.6 Z" {L}/><path d="M0.15 -0.8 L-0.35 0.25 H0.1 L-0.15 0.9 L0.4 -0.1 H-0.05 Z" fill="{c}"/>'
    def esq(x0, y0, x1, y1, k=1.8):
        """Solo las cuatro esquinas de un rectángulo (en lugar de la caja completa)."""
        x0, x1 = min(x0, x1), max(x0, x1); y0, y1 = min(y0, y1), max(y0, y1)
        d_ = (f"M{x0} {y0+k} V{y0} H{x0+k} M{x1-k} {y0} H{x1} V{y0+k} "
              f"M{x1} {y1-k} V{y1} H{x1-k} M{x0+k} {y1} H{x0} V{y1-k}")
        return f'<path d="{d_}" {L}/>'
    def traza(pts, end=True):
        d_ = "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts)
        r = f'<path d="{d_}" fill="none" stroke="{c}" stroke-width="0.22" stroke-linecap="round" stroke-linejoin="round"/>'
        if end: r += f'<circle cx="{pts[-1][0]}" cy="{pts[-1][1]}" r="0.45" fill="none" stroke="{c}" stroke-width="0.22"/>'
        return r
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}" font-family="Arial,Helvetica,sans-serif">',
         f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fff"/>',
         f'<g transform="translate({W} 0) scale(-1 1)">' if espejo else '<g>']
    o.append(f'<rect x="0.7" y="0.7" width="{W-1.4}" height="{H-1.4}" rx="2.2" {L}/>')
    for p in pads:
        if is_hole(p):
            o.append(f'<circle cx="{p[2]}" cy="{p[3]}" r="{2.0 if p[0].startswith("MH") else 0.85}" {L}/>')
    for s_, f in (("1", lambda y: y), ("2", lambda y: H - y)):
        Y = f; up = s_ == "1"; d = 1 if up else -1
        # X2
        o.append(esq(1.6, Y(7.2), 19.4, Y(16.8)))
        o.append(g(10.5, Y(10.6), CAP, 0, 1.1) + t(6.0, Y(11.0)+0.5, "C"+s_, 1.5, "start") + t(15.0, Y(11.0)+0.5, "X2", 1.2, "end", "400"))
        o.append(t(10.5, Y(14.4)+0.45, "474J · 275V~", 1.05, w="400"))
        # R descarga (parada)
        o.append(f'<circle cx="8.5" cy="{Y(4.5)}" r="1.7" {L}/><circle cx="8.5" cy="{Y(4.5)}" r="0.5" fill="{c}"/>')
        o.append(g(18.6, Y(4.5), RES, 0, 0.85) + t(15.3, Y(4.5)+0.45, "R"+s_, 1.2, "start") + t(18.6, Y(6.3)+0.4 if up else Y(6.3)+0.4, "1MΩ", 1.0, w="400"))
        # R limitadora (parada)
        o.append(f'<circle cx="21" cy="{Y(12)}" r="1.8" {L}/><circle cx="21" cy="{Y(12)}" r="0.5" fill="{c}"/>')
        o.append(g(21.6, Y(15.6), RES, 0, 0.8) + t(21.6, Y(17.4)+(0.45 if up else 0.45), "150Ω 1W", 1.0, w="400"))
        # puente
        o.append(f'<rect x="28" y="{min(Y(4.6),Y(19.4)):.2f}" width="4" height="14.8" rx="2" {L}/>')
        o.append(t(30, Y(3.4)+0.55, "+", 1.5) + t(30, Y(20.7)+0.55, "−", 1.7))
        o.append(g(22.9, Y(2.5), BRIDGE, 0, 0.6) + t(23.0, Y(6.0)+0.4, "BR"+s_, 0.95))
        o.append(f'<rect x="25.8" y="{min(Y(10.2),Y(16.6)):.2f}" width="2.2" height="6.4" rx="1" {L}/>')
        o.append(f'<path d="M26.6 {Y(4.4)+1.5*d:.2f} L26.9 {Y(10.2):.2f} M26.9 {Y(16.6):.2f} L27.4 {Y(22.6)-1.5*d:.2f}" {L}/>')
        o.append(t(24.7, Y(13.4)+0.4, "220k", 0.95, rot=-90))
        # electrolítico
        o.append(f'<circle cx="41" cy="{Y(16)}" r="8.5" {L}/>')
        o.append(f'<path d="M44.6 {Y(16)-7.7:.2f} A8.5 8.5 0 0 1 44.6 {Y(16)+7.7:.2f} L44.05 {Y(16)+6.3:.2f} A7.0 7.0 0 0 0 44.05 {Y(16)-6.3:.2f} Z" fill="{c}"/>')
        o.append(t(36.4, Y(16)+0.8, "+", 2.4))
        o.append(g(41, Y(16)+5.0*d, ECAP, 0, 0.95) + t(41, Y(16)-4.1*d+0.45, "CE"+s_, 1.4))
        o.append(t(41, Y(16)+7.4*d+0.4, "47µF 250V", 1.0, w="400"))
        # salida con símbolo de LED
        o.append(esq(36, Y(0.6), 46, Y(7.2), 1.4))
        o.append(t(38.5, Y(6.2)+0.5, "+", 1.5) + t(43.5, Y(6.2)+0.5, "−", 1.7))
        o.append(g(47.9, Y(3.2), LED, 270, 0.8) + t(47.9, Y(6.6)+0.45, "S"+s_, 1.2))
    # entrada
    o.append(f'<ellipse cx="5.5" cy="24.05" rx="6.6" ry="2.0" transform="rotate(47.7 5.5 24.05)" {L}/>')
    o.append(g(5.9, 24.3, VAR, 47.7, 0.75))
    o.append(t(XL, 28.9, "L", 1.4) + t(12.2, 28.9, "N", 1.4) + g(8.6, 32.0, AC, 0, 0.9) + t(10.4, 32.45, "127V", 1.0, "start", "400"))
    # recuadro AP y aviso
    o.append(t(20.9, 27.1, "AP", 5.4))
    o.append(traza([(17.4, 22.6), (16.0, 22.6)]) + traza([(17.0, 25.3), (14.8, 25.3)]) + traza([(17.4, 28.0), (16.0, 28.0)]))
    o.append(traza([(24.4, 22.6), (25.8, 22.6)]) + traza([(24.8, 25.3), (27.0, 25.3)]) + traza([(24.4, 28.0), (25.8, 28.0)]))
    o.append(g(15.4, 19.7, WARN, 0, 0.8) + t(16.9, 20.15, "127 V · NO TOCAR", 1.0, "start"))
    o.append(t(19.8, 31.1, "FUENTE LED · 2 CANALES", 0.95))
    o.append('</g></svg>'); return "\n".join(o)

here = os.path.dirname(os.path.abspath(__file__))
for name, fn in (("cobre_planchar.svg", copper_svg), ("componentes_arriba.svg", top_svg), ("smd_lado_cobre.svg", bottom_svg), ("serigrafia_planchar.svg", lambda: silk_svg(True)), ("serigrafia_vista.svg", lambda: silk_svg(False))):
    open(os.path.join(here, name), "w").write(fn())
print("SVG escritos")

# ---------- imágenes de montaje paso a paso (pieza resaltada) ----------
def resaltar(base, prefijos, espejo=False, color="#e8590c"):
    marcas = []
    for p in pads:
        if any(p[0].startswith(px) for px in prefijos):
            x = W - p[2] if espejo else p[2]
            if p[5] == "r" and not p[0].startswith("BR"):
                marcas.append(f'<rect x="{x-p[6]/2-0.9:.2f}" y="{p[3]-p[7]/2-0.9:.2f}" width="{p[6]+1.8}" height="{p[7]+1.8}" rx="1" fill="{color}" fill-opacity="0.45" stroke="{color}" stroke-width="0.4"/>')
            else:
                marcas.append(f'<circle cx="{x:.2f}" cy="{p[3]:.2f}" r="2.5" fill="{color}" fill-opacity="0.45" stroke="{color}" stroke-width="0.4"/>')
    return base.replace("</svg>", "".join(marcas) + "</svg>")
PASOS = [
    ("01_rc", ["RC"], False),
    ("02_rd", ["RD"], False),
    ("03_rs", ["RS"], False),
    ("04_rv", ["RV1"], False),
    ("05_br", ["BR"], False),
    ("06_c", ["C1", "C2"], False),
    ("07_ce", ["CE"], False),
    ("08_j", ["J1", "J2"], False),
    ("09_in", ["WL", "WN"], False),
]
os.makedirs(os.path.join(here, "pasos"), exist_ok=True)
for nombre, pre, cobre in PASOS:
    base = bottom_svg() if cobre else silk_svg(False)
    open(os.path.join(here, "pasos", nombre + ".svg"), "w").write(resaltar(base, pre, espejo=cobre))
print("imágenes de pasos escritas")
