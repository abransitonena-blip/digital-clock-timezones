"""Fuente capacitiva de 5 canales, versión 3 (placa de una cara).
Mejoras: varistor de entrada, capacitor X2 en bornera (se cambia sin soldar), zener de 5 W por
canal (protege al conectar LED y limita el voltaje sin carga), resistencia de salida de 100 Ω,
LED testigo por canal y agujeros de montaje. Fusible e interruptor iluminado van en la caja.
Coordenadas en mm, vistas desde el lado de componentes."""
import math, itertools, sys, os

N_CH, PITCH, X0 = 5, 20, 16
W, H = 124, 109
PAD, DRILL, TW, CLEAR = 3.0, 0.8, 1.8, 1.5
BR_P = 3.81
BR_W, BR_H = 2.2, 3.4
MH_R = 3.0                      # anillo de los agujeros de montaje (M3)

pads = []      # (ref, pin, x, y, net, forma)  "o" redondo, "v" ovalado, "m" montaje
traces = []
def pad(ref, pin, x, y, net, f="o"): pads.append((ref, pin, x, y, net, f))
def tr(net, *pts): traces.append((net, list(pts)))

LY, NY = 7, 12
pad("J0", "L", 5, 7, "L"); pad("J0", "N", 5, 12, "N")
pad("RV1", "1", 12, 7, "L"); pad("RV1", "2", 12, 14.5, "N")
tr("N", (12, NY), (12, 14.5))
for k in range(N_CH):
    X = X0 + k * PITCH; s = str(k + 1)
    xc, xr, xn = X + 5, X + 11.5, X + 16
    B, A1, P, M, O, T = "B"+s, "AC"+s, "P"+s, "M"+s, "O"+s, "T"+s
    # bornera de 3 polos para el capacitor X2 (la pata de en medio se corta: ahí pasa N)
    pad("TC"+s, "1", xc, LY, "L"); pad("TC"+s, "3", xc, 17, B)
    pad("RD"+s, "1", xr, LY, "L"); pad("RD"+s, "2", xr, 17, B)
    tr(B, (xc, 17), (xr, 17))
    pad("RS"+s, "1", xr, 20.5, B); pad("RS"+s, "2", xr, 35.74, A1)
    tr(B, (xr, 17), (xr, 20.5))
    by = 46
    bx = [X + 3, X + 3 + BR_P, X + 3 + 2*BR_P, X + 3 + 3*BR_P]
    pad("BR"+s, "+", bx[0], by, P, "v"); pad("BR"+s, "~1", bx[1], by, A1, "v")
    pad("BR"+s, "~2", bx[2], by, "N", "v"); pad("BR"+s, "-", bx[3], by, M, "v")
    tr(A1, (xr, 35.74), (bx[1], 40.5), (bx[1], by))
    tr("N", (xn, NY), (xn, 41.5), (bx[2] + 1.2, 41.5), (bx[2], 43), (bx[2], by))
    xp, xm = X + 1.5, X + 16.5          # troncales + y −, abiertas a 15 mm para el zener de 5 W
    tr(P, (bx[0], by), (bx[0], 50), (xp, 52), (xp, 82))
    tr(M, (bx[3], by), (bx[3], 50), (xm, 52), (xm, 98), (X + 11.2, 102))
    pad("CE"+s, "+", X + 6.2, 60, P); pad("CE"+s, "-", X + 11.2, 60, M)
    tr(P, (xp, 60), (X + 6.2, 60)); tr(M, (xm, 60), (X + 11.2, 60))
    pad("ZD"+s, "K", xp, 71, P); pad("ZD"+s, "A", xm, 71, M)
    pad("RC"+s, "+", xp, 77, P); pad("RC"+s, "-", xm, 77, M)
    # resistencia de salida y LED testigo en serie con la salida +
    pad("RO"+s, "1", xp, 82, P); pad("RO"+s, "2", xp, 92.16, O)
    pad("LT"+s, "A", xp, 96, O); pad("LT"+s, "K", X + 6.58, 96, T)
    tr(O, (xp, 92.16), (xp, 96))
    pad("J"+s, "+", X + 6.2, 102, T); pad("J"+s, "-", X + 11.2, 102, M)
    tr(T, (X + 6.58, 96), (X + 6.2, 102))
last = X0 + (N_CH - 1) * PITCH
tr("L", (5, LY), (last + 11.5, LY))
tr("N", (5, NY), (last + 16, NY))
for i, (x, y) in enumerate([(5.5, 26), (W - 4.5, 4.5), (4.5, H - 4.5), (W - 4.5, H - 4.5)]):
    pad("MH"+str(i+1), "", x, y, "MH"+str(i+1), "m")

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
shapes = []
for r, pn, x, y, n, f in pads:
    if f == "v":
        h = (BR_H - BR_W) / 2
        shapes.append((n, f"{r}.{pn}", ((x, y-h), (x, y+h)), BR_W/2))
    else:
        shapes.append((n, f"{r}.{pn}", ((x, y), (x, y)), MH_R if f == "m" else PAD/2))
for n, pts in traces:
    for a, b in zip(pts, pts[1:]): shapes.append((n, f"pista {n}", (a, b), TW/2))
errors = []
worst = 99
for s1, s2 in itertools.combinations(shapes, 2):
    if s1[0] == s2[0]: continue
    d = seg_seg(*s1[2], *s2[2]) - s1[3] - s2[3]
    worst = min(worst, d)
    if d < CLEAR: errors.append(f"separación {d:.2f} mm entre {s1[1]} y {s2[1]}")
for net in set(s[0] for s in shapes):
    ss = [s for s in shapes if s[0] == net]
    seen = {0}; stack = [0]
    while stack:
        i = stack.pop()
        for j in range(len(ss)):
            if j not in seen and seg_seg(*ss[i][2], *ss[j][2]) <= ss[i][3]+ss[j][3]:
                seen.add(j); stack.append(j)
    if len(seen) != len(ss):
        errors.append(f"red {net} cortada: " + ", ".join(ss[k][1] for k in range(len(ss)) if k not in seen))
for r, pn, x, y, n, f in pads:
    if not (1 < x - (MH_R if f == "m" else 1.5) and x + (MH_R if f == "m" else 1.5) < W-1 and 1 < y - (MH_R if f == "m" else 1.5) and y + (MH_R if f == "m" else 1.5) < H-1): errors.append(f"{r}.{pn} fuera de la placa")
if errors: print("\n".join(errors)); sys.exit(1)
print(f"DRC OK: placa {W}×{H} mm, {len(pads)} pads, separación mínima real {worst:.2f} mm")

# ---------- SVG ----------
def path_d(pts): return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts)
def pad_svg(x, y, f, fill):
    if f == "v":
        return f'<rect x="{x-BR_W/2:.2f}" y="{y-BR_H/2:.2f}" width="{BR_W}" height="{BR_H}" rx="{BR_W/2}" fill="{fill}"/>'
    if f == "m":
        return f'<circle cx="{x}" cy="{y}" r="{MH_R-0.6}" fill="none" stroke="{fill}" stroke-width="1.2"/>'
    return f'<circle cx="{x}" cy="{y}" r="{PAD/2}" fill="{fill}"/>'
def copper_svg():
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">',
         f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fff" stroke="#000" stroke-width="0.3"/>']
    for n, pts in traces:
        o.append(f'<path d="{path_d(pts)}" fill="none" stroke="#000" stroke-width="{TW}" stroke-linecap="round" stroke-linejoin="round"/>')
    for r, pn, x, y, n, f in pads: o.append(pad_svg(x, y, f, "#000"))
    for r, pn, x, y, n, f in pads: o.append(f'<circle cx="{x}" cy="{y}" r="{DRILL/2}" fill="{"#000" if f == "m" else "#fff"}"/>')
    o.append(f'<g transform="translate(7 96) rotate(-90) scale(-1 1)"><text x="-58" y="0" font-family="Arial,Helvetica,sans-serif" font-weight="700" font-size="3.2" fill="#000">5 CANALES V3 127V</text></g>')
    o.append('</svg>')
    return "\n".join(o)

def comp_svg():
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}" font-family="Arial,Helvetica,sans-serif">',
         f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fff" stroke="#000" stroke-width="0.3"/>']
    for n, pts in traces:
        o.append(f'<path d="{path_d(pts)}" fill="none" stroke="#e8c9a8" stroke-width="{TW}" stroke-linecap="round" stroke-linejoin="round"/>')
    S = 'fill="none" stroke="#000" stroke-width="0.35"'
    def T(x, y, s, sz=2.0, a="middle", w="700", rot=None):
        tf = f' transform="rotate({rot} {x} {y})"' if rot is not None else ""
        return f'<text x="{x}" y="{y}" font-size="{sz}" text-anchor="{a}" font-weight="{w}"{tf}>{s}</text>'
    o.append(f'<rect x="1.2" y="4" width="7.6" height="11" {S}/>' + T(5, 18.5, "J0", 2.2) + T(5, 21, "del switch", 1.3, w="400"))
    o.append(f'<rect x="10" y="4.5" width="4" height="12.5" rx="1.5" {S}/>' + T(12.8, 10.8, "RV1", 1.5, rot=-90))
    o.append(T(12, 21, "10D241K", 1.2, w="400"))
    for k in range(N_CH):
        X = X0 + k * PITCH; s = str(k + 1)
        xc, xr, xp, xm = X + 5, X + 11.5, X + 1.5, X + 16.5
        o.append(f'<rect x="{xc-3.8}" y="4.5" width="7.6" height="15" {S}/>')
        o.append(f'<circle cx="{xc}" cy="12" r="1.2" fill="none" stroke="#c00" stroke-width="0.4"/><path d="M{xc-1} 11 L{xc+1} 13 M{xc+1} 11 L{xc-1} 13" stroke="#c00" stroke-width="0.4"/>')
        o.append(T(xc, 23.5, "C" + s + " X2", 1.8) + T(xc, 25.8, "(bornera)", 1.3, w="400"))
        o.append(f'<rect x="{xr-1.3}" y="8" width="2.6" height="8" rx="1.1" {S}/>' + T(xr+0.6, 12, "1M", 1.5, rot=-90))
        o.append(f'<rect x="{xr-1.8}" y="23" width="3.6" height="10" rx="1.5" {S}/>' + T(xr+0.6, 28, "150Ω", 1.5, rot=-90))
        o.append(T(xc, 31, "RS" + s, 1.6) + T(xc, 33.2, "1W", 1.4, w="400"))
        o.append(f'<rect x="{X+0.9}" y="44.2" width="16.6" height="3.6" rx="0.5" {S}/><path d="M{X+0.9} 45.4 L{X+2.1} 44.2" stroke="#000" stroke-width="0.35"/>')
        for i, lab in enumerate(["+", "~", "~", "−"]): o.append(T(X + 3 + i * BR_P, 43.2, lab, 2.0))
        o.append(T(X + 9.2, 50.6, "BR" + s + " KBP", 1.4, w="400"))
        o.append(f'<circle cx="{X+8.7}" cy="60" r="6.5" {S}/><path d="M{X+11.2} 53.6 A6.5 6.5 0 0 1 {X+11.2} 66.4" stroke="#000" stroke-width="0.35" fill="#ddd"/>')
        o.append(T(X+8.7, 57, "CE" + s, 1.8) + T(X+8.7, 64.5, "47µF 250V", 1.2, w="400"))
        o.append(f'<rect x="{X+4.3}" y="68.5" width="8.8" height="5" rx="2" {S}/><path d="M{X+5.6} 68.5 V73.5" stroke="#000" stroke-width="0.9"/>')
        o.append(T(X+9.3, 71.8, "ZD" + s, 1.6) + T(X+8.7, 75.4, "zener 5W", 1.1, w="400"))
        o.append(f'<rect x="{X+5.2}" y="76" width="7" height="2.4" rx="1" {S}/>' + T(X+8.7, 80.6, "220k", 1.3, w="400"))
        o.append(f'<rect x="{xp-1.3}" y="83.4" width="2.6" height="7.4" rx="1.1" {S}/>' + T(xp+0.6, 87.1, "100Ω", 1.4, rot=-90))
        o.append(T(X + 6.6, 87.5, "RO" + s, 1.5))
        o.append(f'<circle cx="{X+4.04}" cy="96" r="1.9" {S}/><path d="M{X+5.94} 94.6 V97.4" stroke="#000" stroke-width="0.35"/>')
        o.append(T(X + 4.04, 92.8, "LT" + s, 1.3) + T(X + 10.5, 95.6, "testigo", 1.1, w="400") + T(X + 10.5, 97.2, "pata larga ←", 1.0, w="400"))
        o.append(f'<rect x="{X+3.7}" y="98.6" width="10" height="7.4" {S}/>')
        o.append(T(X+6.2, 100.4, "+", 1.8) + T(X+11.2, 100.4, "−", 1.8) + T(X+8.7, 107.4, "SAL " + s, 1.6))
    for r, pn, x, y, n, f in pads:
        if f == "m": o.append(f'<circle cx="{x}" cy="{y}" r="1.6" {S}/>')
        else: o.append(f'<circle cx="{x}" cy="{y}" r="0.55" fill="#000"/>')
    o.append('</svg>')
    return "\n".join(o)

here = os.path.dirname(os.path.abspath(__file__))
open(os.path.join(here, "cobre_planchar.svg"), "w").write(copper_svg())
open(os.path.join(here, "componentes.svg"), "w").write(comp_svg())
print("SVG escritos")
