"""Fuente capacitiva de 2 canales en placa de 5 × 5 cm (una cara, híbrida SMD, sin zener).\nCoordenadas en mm, vistas desde el lado de componentes."""
import math, itertools, sys, os

N_CH, P, X0 = 2, 20, 10.5
S = 12.0
PAD, DRILL, TW, CLEAR = 3.0, 0.8, 1.6, 1.5
MH_R = 2.2
LY = 2.75
W, H = 50, 50
pads = []
traces = []
def tht(ref, pin, x, y, net): pads.append((ref, pin, x, y, net, "o", PAD, PAD))
def smd(ref, pin, x, y, net, w, h): pads.append((ref, pin, x, y, net, "r", w, h))
def tr(net, *pts): traces.append((net, list(pts)))
DA, DW = 2.15, (2.4, 1.9)
R12 = (2.0, 1.6)
R25h = (2.0, 3.4)               # 2512 acostado: pads de 2.0 × 3.4 a 6.8 mm
OY = 21.0; NB = 48.0
for k in range(N_CH):
    s = str(k + 1); ox = X0 + k * P + 1.5
    B, A1, PP, M = "B"+s, "AC"+s, "P"+s, "M"+s
    xt, xr, oy, m = ox + 3.5, ox + 10, OY, S / 2
    tht("TC"+s, "1", xt, LY, "L"); tht("TC"+s, "3", xt, 12.75, B)
    smd("RDa"+s, "1", xr, 4.9, "L", *R12); smd("RDa"+s, "2", xr, 8.2, "D"+s, *R12)
    smd("RDb"+s, "1", xr, 9.6, "D"+s, *R12); smd("RDb"+s, "2", xr, 12.9, B, *R12)
    tr("L", (xr, LY), (xr, 4.9)); tr("D"+s, (xr, 8.2), (xr, 9.6))
    smd("RS"+s, "2", ox + 0.6, 16.6, A1, *R25h); smd("RS"+s, "1", ox + 7.4, 16.6, B, *R25h)
    tr(B, (xt, 12.75), (ox + 7.4, 14.5), (ox + 7.4, 16.6)); tr(B, (xr, 12.9), (ox + 7.4, 14.5))
    tr(A1, (ox + 0.6, 16.6), (ox, oy))
    smd("DT"+s, "K", ox + m - DA, oy, A1, *DW);       smd("DT"+s, "A", ox + m + DA, oy, M, *DW)
    smd("DL"+s, "A", ox, oy + m - DA, A1, *DW[::-1]); smd("DL"+s, "K", ox, oy + m + DA, PP, *DW[::-1])
    smd("DB"+s, "K", ox + m - DA, oy + S, PP, *DW);   smd("DB"+s, "A", ox + m + DA, oy + S, "N", *DW)
    smd("DR"+s, "A", ox + S, oy + m - DA, M, *DW[::-1]); smd("DR"+s, "K", ox + S, oy + m + DA, "N", *DW[::-1])
    tr(A1, (ox + m - DA, oy), (ox, oy), (ox, oy + m - DA))
    tr(M, (ox + m + DA, oy), (ox + S, oy), (ox + S, oy + m - DA))
    tr("N", (ox + S, oy + m + DA), (ox + S, oy + S), (ox + m + DA, oy + S))
    tr(PP, (ox, oy + m + DA), (ox, oy + S), (ox + m - DA, oy + S))
    cp, cm = (ox + m - 1.9, oy + m + 1.55), (ox + m + 1.9, oy + m - 1.55)
    tht("CE"+s, "+", *cp, PP); tht("CE"+s, "-", *cm, M)
    tr(PP, cp, (ox + m - DA, oy + S)); tr(M, cm, (ox + m + DA, oy))
    xm = ox + S + 3.5
    tr(M, (ox + S, oy), (xm, oy), (xm, 39.0), (ox + S/2 + 5 + DA, 42.7))
    tr(PP, (ox, oy + S), (ox, 39.0), (ox + S/2 - 5 + DA, 42.7))
    tht("RC"+s, "+", ox, 36.9, PP); tht("RC"+s, "-", xm, 36.9, M)
    tht("J"+s, "+", ox + S/2 - 5 + DA, 42.7, PP); tht("J"+s, "-", ox + S/2 + 5 + DA, 42.7, M)
    tr("N", (ox + m + DA, oy + S), (ox + m + DA, NB))
last_ox = X0 + (N_CH - 1) * P + 1.5
tht("J0", "L", 4.0, 8, "L"); tht("J0", "N", 4.0, 13, "N")
tr("L", (4.0, 8), (4.0, LY), (last_ox + 10, LY))
tr("N", (4.0, 13), (4.0, 38.5), (9.5, 44), (9.5, NB), (last_ox + S/2 + DA, NB))
tht("RV1", "1", 9.3, LY, "L"); tht("RV1", "2", 9.3, LY + 7.5, "N")
tr("N", (9.3, LY + 7.5), (6.5, 13), (4.0, 13))
for i, (x, y) in enumerate([(3.6, 46.4), (46.8, 6.2)]):
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
    o.append(f'<g transform="translate(28.6 9.6) scale(-1 1)"><text x="-3.4" y="0" font-family="Arial,Helvetica,sans-serif" font-weight="700" font-size="2.4" fill="#000">127V</text></g>')
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
    o.append(f'<rect x="0.3" y="5.5" width="7.4" height="10" {S_}/>' + T(4.0, 18.5, "J0", 2.0) + T(4.0, 20.6, "127V", 1.3, w="400"))
    o.append(f'<rect x="6.9" y="0.8" width="4.8" height="11.4" rx="1.5" {S_}/>' + T(9.9, 6.5, "RV1", 1.4, rot=-90))
    for k in range(N_CH):
        s = str(k+1); ox = X0 + k*P + 1.5; xt = ox + 3.5; xm = ox + S + 3.5; m = S/2
        o.append(f'<rect x="{xt-3.6}" y="0.4" width="7.2" height="14.8" {S_}/>')
        o.append(f'<path d="M{xt-1} 6.75 L{xt+1} 8.75 M{xt+1} 6.75 L{xt-1} 8.75" stroke="#c00" stroke-width="0.4"/>' + T(xt, 10.2, "C"+s, 1.5) + T(xt, 5.4, "X2", 1.2, w="400"))
        o.append(f'<circle cx="{ox+m}" cy="{OY+m}" r="6.5" {S_}/><path d="M{ox+m+2.6} {OY+m-6} A6.5 6.5 0 0 1 {ox+m+6.3} {OY+m+1.5}" stroke="#000" stroke-width="1.6" fill="none" opacity="0.35"/>')
        o.append(T(ox+m, OY+m+5, "CE"+s, 1.6) + T(ox+m-3.3, OY+m+2.6, "+", 2.2) + T(ox+m+3.6, OY+m-0.6, "−", 2.2))
        o.append(f'<rect x="{ox+4}" y="35.6" width="7.5" height="2.6" rx="1.1" {S_}/>' + T(ox+7.75, 35.0, "RC 220k", 1.2, w="400"))
        o.append(f'<rect x="{ox+S/2-5+DA-2.8}" y="39.1" width="15.6" height="7.4" {S_}/>')
        o.append(f'<path d="M{ox+S/2+DA-1} 41.7 L{ox+S/2+DA+1} 43.7 M{ox+S/2+DA+1} 41.7 L{ox+S/2+DA-1} 43.7" stroke="#c00" stroke-width="0.4"/>')
        o.append(T(ox+S/2-5+DA, 40.9, "+", 1.6) + T(ox+S/2+5+DA, 40.9, "−", 1.6) + T(ox+S/2+DA, 49.4, "SAL "+s, 1.4))
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
        s = str(k+1); ox = X0 + k*P + 1.5; m = S/2; oy = OY; xr = ox + 10
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
        o.append(f'<rect x="{mx(ox+4)-3.2}" y="15.0" width="6.4" height="3.2" fill="#222"/>' + T(mx(ox+4), 17.1, "151", 1.4, c="#fff") + T(mx(ox+4)-4.2, 17.1, "RS", 1.1, "end"))
        for yy, lab in ((6.55, "105"), (11.25, "105")):
            o.append(f'<rect x="{mx(xr)-0.85}" y="{yy-1.6}" width="1.7" height="3.2" fill="#222"/>')
        o.append(T(mx(xr)-1.6, 9.3, "RD 1M", 1.1, "end"))
        o.append(T(mx(ox+S/2+DA), 49.4, "SAL "+s, 1.4))
    o.append(T(W/2, 1.9, "LADO DEL COBRE (SMD) · visto de frente", 1.2, w="400"))
    o.append('</svg>'); return "\n".join(o)

here = os.path.dirname(os.path.abspath(__file__))
for name, fn in (("cobre_planchar.svg", copper_svg), ("componentes_arriba.svg", top_svg), ("smd_lado_cobre.svg", bottom_svg)):
    open(os.path.join(here, name), "w").write(fn())
print("SVG escritos")
