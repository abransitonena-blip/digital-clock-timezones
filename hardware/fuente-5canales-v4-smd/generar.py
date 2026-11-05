"""Fuente capacitiva de 5 canales, versión 4 híbrida SMD (placa de una cara).
SMD (van del lado del cobre): 4 diodos M7 por canal, resistencias 1206 y 2512.
De patitas (del lado sin cobre): bornera del X2, electrolítico, zener 5 W, 220 kΩ, LED testigo,
borneras, varistor. Coordenadas en mm, vistas desde el lado de componentes (arriba)."""
import math, itertools, sys, os

N_CH, P, X0 = 5, 20, 14.5
S = 12.0                       # lado del cuadrado del puente de diodos
PAD, DRILL, TW, CLEAR = 3.0, 0.8, 1.6, 1.5
MH_R = 3.0
LY = 4                          # línea L (arriba)
pads = []   # (ref, pin, x, y, net, forma, w, h)   forma: o redondo THT, r SMD (rectángulo redondeado), m montaje
traces = []
def tht(ref, pin, x, y, net): pads.append((ref, pin, x, y, net, "o", PAD, PAD))
def smd(ref, pin, x, y, net, w, h): pads.append((ref, pin, x, y, net, "r", w, h))
def tr(net, *pts): traces.append((net, list(pts)))
DA, DW = 2.15, (2.4, 1.9)       # diodo SMA (M7): pads a ±2.15 mm, 2.4 × 1.9
R12 = (2.0, 1.6)                # 1206 vertical: pads 2.0 × 1.6 a 3.3 mm
R25 = (3.4, 2.0)                # 2512 vertical: pads 3.4 × 2.0 a 6.8 mm

for k in range(N_CH):
    s = str(k + 1); X = X0 + k * P; ox = X + 1.5
    B, A1, PP, M, O, T = "B"+s, "AC"+s, "P"+s, "M"+s, "O"+s, "T"+s
    xt, xr = ox + 3.5, ox + 10
    # bornera de 3 polos del X2 (pata central cortada) y 2 resistencias 1206 de 1 MΩ en serie
    tht("TC"+s, "1", xt, LY, "L"); tht("TC"+s, "3", xt, 14, B)
    smd("RDa"+s, "1", xr, 6.0, "L", *R12); smd("RDa"+s, "2", xr, 9.3, "D"+s, *R12)
    smd("RDb"+s, "1", xr, 10.9, "D"+s, *R12); smd("RDb"+s, "2", xr, 14.2, B, *R12)
    tr("L", (xr, LY), (xr, 6.0)); tr("D"+s, (xr, 9.3), (xr, 10.9)); tr(B, (xt, 14), (xr, 14.2))
    # resistencia 150 Ω 1 W en 2512
    oy = 27.0
    smd("RS"+s, "1", ox + 2, oy - 8.6, B, *R25); smd("RS"+s, "2", ox + 2, oy - 1.8, A1, *R25)
    tr(B, (xt, 14), (ox + 2, 16.5), (ox + 2, oy - 8.6))
    # puente con 4 diodos M7 en cuadrado: esquinas AC1 (arriba izq.), − (arriba der.), N (abajo der.), + (abajo izq.)
    m = S / 2
    smd("DT"+s, "K", ox + m - DA, oy, A1, *DW);      smd("DT"+s, "A", ox + m + DA, oy, M, *DW)
    smd("DL"+s, "A", ox, oy + m - DA, A1, *DW[::-1]); smd("DL"+s, "K", ox, oy + m + DA, PP, *DW[::-1])
    smd("DB"+s, "K", ox + m - DA, oy + S, PP, *DW);   smd("DB"+s, "A", ox + m + DA, oy + S, "N", *DW)
    smd("DR"+s, "A", ox + S, oy + m - DA, M, *DW[::-1]); smd("DR"+s, "K", ox + S, oy + m + DA, "N", *DW[::-1])
    tr(A1, (ox + 2, oy - 1.8), (ox + m - DA, oy)); tr(A1, (ox + m - DA, oy), (ox, oy), (ox, oy + m - DA))
    tr(M, (ox + m + DA, oy), (ox + S, oy), (ox + S, oy + m - DA))
    tr("N", (ox + S, oy + m + DA), (ox + S, oy + S), (ox + m + DA, oy + S))
    tr(PP, (ox, oy + m + DA), (ox, oy + S), (ox + m - DA, oy + S))
    # electrolítico dentro del cuadrado (va arriba de los diodos, del otro lado de la placa)
    cp, cm = (ox + m - 1.9, oy + m + 1.55), (ox + m + 1.9, oy + m - 1.55)
    tht("CE"+s, "+", *cp, PP); tht("CE"+s, "-", *cm, M)
    tr(PP, cp, (ox + m - DA, oy + S)); tr(M, cm, (ox + m + DA, oy))
    # troncales + (izquierda) y − (derecha)
    xm = ox + S + 3.5
    tr(M, (ox + S, oy), (xm, oy), (xm, 72), (ox + S + 1.15, 76))
    tr(PP, (ox, oy + S), (ox, 58.3))
    tht("ZD"+s, "K", ox, 45, PP); tht("ZD"+s, "A", xm, 45, M)
    tht("RC"+s, "+", ox, 52, PP); tht("RC"+s, "-", xm, 52, M)
    smd("RO"+s, "1", ox, 58.3, PP, *R12); smd("RO"+s, "2", ox, 61.6, O, *R12)
    tht("LT"+s, "A", ox, 65.5, O); tht("LT"+s, "K", ox, 70.58, T)
    tr(O, (ox, 61.6), (ox, 65.5))
    # bornera de salida de 3 polos: + y − en las orillas, la central se corta y por ahí sube N
    tht("J"+s, "+", ox + S/2 - 5 + DA, 76, T); tht("J"+s, "-", ox + S/2 + 5 + DA, 76, M)
    tr(T, (ox, 70.58), (ox + S/2 - 5 + DA, 76))
    tr("N", (ox + m + DA, oy + S), (ox + m + DA, 83))
NB = 83
last_ox = X0 + (N_CH - 1) * P + 1.5
W = round(last_ox + S + 3.5 + 10.5)
H = 87
tht("J0", "L", 4.5, 12, "L"); tht("J0", "N", 4.5, 17, "N")
tr("L", (4.5, 12), (4.5, LY), (last_ox + 10, LY))
tr("N", (4.5, 17), (4.5, NB), (last_ox + S/2 + DA, NB))
tht("RV1", "1", 9, 30, "L"); tht("RV1", "2", 9, 37.5, "N")
tr("L", (9, LY), (9, 30)); tr("N", (9, 37.5), (4.5, 37.5))
for i, (x, y) in enumerate([(10.0, 62), (W - 4.5, 12), (W - 4.5, 62)]):
    pads.append(("MH"+str(i+1), "", x, y, "MH"+str(i+1), "m", 2*MH_R, 2*MH_R))

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
    if d < CLEAR: errors.append(f"separación {d:.2f} mm entre {s1[1]} y {s2[1]}")
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
if errors: print("\n".join(errors[:40])); sys.exit(1)
print(f"DRC OK: placa {W}×{H} mm, {len(pads)} pads, separación mínima real {worst:.2f} mm")

# ---------- SVG ----------
def path_d(pts): return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts)
def pad_svg(p, fill):
    r, pn, x, y, n, f, w, h = p
    if f == "r": return f'<rect x="{x-w/2:.2f}" y="{y-h/2:.2f}" width="{w}" height="{h}" rx="{min(w,h)/2}" fill="{fill}"/>'
    if f == "m": return f'<circle cx="{x}" cy="{y}" r="{MH_R-0.6}" fill="none" stroke="{fill}" stroke-width="1.2"/>'
    return f'<circle cx="{x}" cy="{y}" r="{w/2}" fill="{fill}"/>'
def copper_svg():
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">',
         f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fff" stroke="#000" stroke-width="0.3"/>']
    for n, pts in traces: o.append(f'<path d="{path_d(pts)}" fill="none" stroke="#000" stroke-width="{TW}" stroke-linecap="round" stroke-linejoin="round"/>')
    for p in pads: o.append(pad_svg(p, "#000"))
    for p in pads:
        if p[5] != "r": o.append(f'<circle cx="{p[2]}" cy="{p[3]}" r="{DRILL/2}" fill="{"#000" if p[5] == "m" else "#fff"}"/>')
    o.append(f'<g transform="translate({W-2.5} 70) rotate(-90) scale(-1 1)"><text x="-50" y="0" font-family="Arial,Helvetica,sans-serif" font-weight="700" font-size="2.8" fill="#000">V4 SMD 127V</text></g>')
    o.append('</svg>'); return "\n".join(o)

def T(x, y, s, sz=2.0, a="middle", w="700", rot=None, c="#000"):
    tf = f' transform="rotate({rot} {x} {y})"' if rot is not None else ""
    return f'<text x="{x:.2f}" y="{y:.2f}" font-size="{sz}" text-anchor="{a}" font-weight="{w}" fill="{c}"{tf}>{s}</text>'
S_ = 'fill="none" stroke="#000" stroke-width="0.35"'
def top_svg():
    """Lado de componentes de patitas (sin cobre)."""
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}" font-family="Arial,Helvetica,sans-serif">',
         f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fff" stroke="#000" stroke-width="0.3"/>']
    for n, pts in traces: o.append(f'<path d="{path_d(pts)}" fill="none" stroke="#efdcc6" stroke-width="{TW}" stroke-linecap="round" stroke-linejoin="round"/>')
    for p in pads:
        if p[5] == "r": o.append(f'<rect x="{p[2]-p[6]/2:.2f}" y="{p[3]-p[7]/2:.2f}" width="{p[6]}" height="{p[7]}" rx="{min(p[6],p[7])/2}" fill="#e6e6e6"/>')
    o.append(f'<rect x="0.8" y="9.5" width="7.6" height="10" {S_}/>' + T(4.5, 22.5, "J0", 2.2) + T(4.5, 24.8, "127V", 1.4, w="400"))
    o.append(f'<rect x="6.6" y="27.5" width="4.8" height="12.5" rx="1.5" {S_}/>' + T(9.6, 33.8, "RV1", 1.5, rot=-90))
    for k in range(N_CH):
        s = str(k+1); X = X0 + k*P; ox = X + 1.5; xt = ox + 3.5; xm = ox + S + 3.5; m = S/2
        o.append(f'<rect x="{xt-3.8}" y="1.5" width="7.6" height="15" {S_}/>')
        o.append(f'<path d="M{xt-1} 8 L{xt+1} 10 M{xt+1} 8 L{xt-1} 10" stroke="#c00" stroke-width="0.4"/>' + T(xt, 19.5, "C"+s+" X2", 1.7))
        o.append(f'<circle cx="{ox+m}" cy="{27+m}" r="6.5" {S_}/><path d="M{ox+m+2.6} {27+m-6} A6.5 6.5 0 0 1 {ox+m+6.3} {27+m+1.5}" stroke="#000" stroke-width="1.6" fill="none" opacity="0.35"/>')
        o.append(T(ox+m, 27+m+5, "CE"+s, 1.6) + T(ox+m-3.3, 27+m+2.6, "+", 2.2) + T(ox+m+3.6, 27+m-0.6, "−", 2.2))
        o.append(f'<rect x="{ox+3.5}" y="42.4" width="9.5" height="5.2" rx="2" {S_}/><path d="M{ox+4.8} 42.4 V47.6" stroke="#000" stroke-width="0.9"/>' + T(ox+8.6, 45.8, "ZD"+s, 1.5))
        o.append(f'<rect x="{ox+4.5}" y="50.7" width="7.5" height="2.6" rx="1.1" {S_}/>' + T(ox+8.2, 56, "RC 220k", 1.3, w="400"))
        o.append(f'<circle cx="{ox}" cy="68.04" r="1.9" {S_}/><path d="M{ox-1.4} 69.6 H{ox+1.4}" stroke="#000" stroke-width="0.4"/>' + T(ox+3.2, 68.6, "LT"+s, 1.3))
        o.append(f'<rect x="{ox+S/2-5+DA-2.8}" y="72.4" width="15.6" height="7.4" {S_}/>')
        o.append(f'<path d="M{ox+S/2+DA-1} 75 L{ox+S/2+DA+1} 77 M{ox+S/2+DA+1} 75 L{ox+S/2+DA-1} 77" stroke="#c00" stroke-width="0.4"/>')
        o.append(T(ox+S/2-5+DA, 74.2, "+", 1.8) + T(ox+S/2+5+DA, 74.2, "−", 1.8) + T(ox+S/2+DA, 86, "SAL "+s, 1.7))
    for p in pads:
        if p[5] == "m": o.append(f'<circle cx="{p[2]}" cy="{p[3]}" r="1.6" {S_}/>')
        elif p[5] == "o": o.append(f'<circle cx="{p[2]}" cy="{p[3]}" r="0.55" fill="#000"/>')
    o.append('</svg>'); return "\n".join(o)

def bottom_svg():
    """Lado del cobre visto de frente (espejo): dónde van las piezas SMD."""
    mx = lambda x: W - x
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}" font-family="Arial,Helvetica,sans-serif">',
         f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fff" stroke="#000" stroke-width="0.3"/>']
    for n, pts in traces: o.append(f'<path d="{path_d([(mx(x), y) for x, y in pts])}" fill="none" stroke="#d9a877" stroke-width="{TW}" stroke-linecap="round" stroke-linejoin="round"/>')
    for p in pads:
        r, pn, x, y, n, f, w, h = p
        if f == "r": o.append(f'<rect x="{mx(x)-w/2:.2f}" y="{y-h/2:.2f}" width="{w}" height="{h}" rx="{min(w,h)/2}" fill="#c98b4e"/>')
        elif f == "o": o.append(f'<circle cx="{mx(x)}" cy="{y}" r="{w/2}" fill="#c98b4e"/><circle cx="{mx(x)}" cy="{y}" r="0.5" fill="#fff"/>')
    for k in range(N_CH):
        s = str(k+1); X = X0 + k*P; ox = X + 1.5; m = S/2; oy = 27; xr = ox + 10
        def diodo(ax, ay, kx, ky, lab):
            cx, cy = (mx(ax)+mx(kx))/2, (ay+ky)/2
            if ay == ky:
                o.append(f'<rect x="{cx-2.2}" y="{cy-1.3}" width="4.4" height="2.6" fill="#333"/>')
                bx = cx + (1.5 if mx(kx) > mx(ax) else -1.5)
                o.append(f'<rect x="{bx-0.35}" y="{cy-1.3}" width="0.7" height="2.6" fill="#ddd"/>')
            else:
                o.append(f'<rect x="{cx-1.3}" y="{cy-2.2}" width="2.6" height="4.4" fill="#333"/>')
                by = cy + (1.5 if ky > ay else -1.5)
                o.append(f'<rect x="{cx-1.3}" y="{by-0.35}" width="2.6" height="0.7" fill="#ddd"/>')
        diodo(ox+m+DA, oy, ox+m-DA, oy, "DT"); diodo(ox, oy+m-DA, ox, oy+m+DA, "DL")
        diodo(ox+m+DA, oy+S, ox+m-DA, oy+S, "DB"); diodo(ox+S, oy+m-DA, ox+S, oy+m+DA, "DR")
        o.append(T(mx(ox+m), oy+m+0.7, "M7 ×4", 1.4))
        o.append(f'<rect x="{mx(ox+2)-2.4}" y="{oy-5.2-2.6}" width="4.8" height="5.2" fill="#222"/>' + T(mx(ox+2), oy-4.6, "151", 1.4, c="#fff"))
        o.append(T(mx(ox+2)+(-4 if True else 4), oy-4.6, "RS", 1.3, "end"))
        for yy, lab in ((7.65, "105"), (12.55, "105")):
            o.append(f'<rect x="{mx(xr)-0.85}" y="{yy-1.6}" width="1.7" height="3.2" fill="#222"/>')
        o.append(T(mx(xr)-1.6, 10.6, "RD 1M", 1.2, "end"))
        o.append(f'<rect x="{mx(ox)-0.85}" y="{59.95-1.6}" width="1.7" height="3.2" fill="#222"/>' + T(mx(ox)-1.6, 60.5, "RO 100Ω", 1.2, "end"))
        o.append(T(mx(ox+S/2+DA), 86, "SAL "+s, 1.7))
    o.append(T(W/2, 2.6, "LADO DEL COBRE (piezas SMD) · visto de frente", 1.8))
    o.append('</svg>'); return "\n".join(o)

here = os.path.dirname(os.path.abspath(__file__))
for name, fn in (("cobre_planchar.svg", copper_svg), ("componentes_arriba.svg", top_svg), ("smd_lado_cobre.svg", bottom_svg)):
    open(os.path.join(here, name), "w").write(fn())
print("SVG escritos")
