"""Fuente capacitiva de 5 CANALES INDEPENDIENTES (placa de una cara).
Cada salida tiene su propio capacitor X2, su resistencia, su puente en línea (KBP) y su filtro.
Así cada salida lleva la corriente que tú elijas, sin importar cuántos LED tengan las demás.
Coordenadas en mm, vistas desde el lado de componentes."""
import math, itertools, sys, os

N_CH, PITCH, X0 = 5, 19, 14
W, H = X0 + N_CH * PITCH + 1, 93
PAD, DRILL, TW, CLEAR = 3.0, 0.8, 1.8, 1.5
BR_P = 3.81                     # paso del puente en línea KBP
BR_W, BR_H = 2.2, 3.4           # pad ovalado del puente

pads = []      # (ref, pin, x, y, net, forma)  forma: "o" redondo, "v" ovalado vertical
traces = []    # (net, [(x,y),...])
def pad(ref, pin, x, y, net, f="o"): pads.append((ref, pin, x, y, net, f))
def tr(net, *pts): traces.append((net, list(pts)))

LY, NY = 5, 12.5
pad("J0", "L", 5, 5, "L"); pad("J0", "N", 5, 10, "N")
tr("N", (5, 10), (5, NY))
for k in range(N_CH):
    X = X0 + k * PITCH; s = str(k + 1)
    xc, xr, xn = X + 5, X + 11.5, X + 16
    B, A1, P, M = "B" + s, "AC" + s, "P" + s, "M" + s
    # capacitor X2 (pata a 15 o 22.5 mm) y su resistencia de descarga; ambos pasan por encima de la línea N
    pad("C" + s, "1", xc, LY, "L"); pad("C" + s, "2", xc, 20, B); pad("C" + s, "2b", xc, 27.5, B)
    pad("RD" + s, "1", xr, LY, "L"); pad("RD" + s, "2", xr, 20, B)
    tr(B, (xc, 20), (xr, 20)); tr(B, (xc, 20), (xc, 27.5))
    # resistencia de 150 Ω
    pad("RS" + s, "1", xr, 23.5, B); pad("RS" + s, "2", xr, 38.74, A1)
    tr(B, (xr, 20), (xr, 23.5))
    # puente en línea: +  ~  ~  −
    by = 49
    bx = [X + 3, X + 3 + BR_P, X + 3 + 2 * BR_P, X + 3 + 3 * BR_P]
    pad("BR" + s, "+", bx[0], by, P, "v"); pad("BR" + s, "~1", bx[1], by, A1, "v")
    pad("BR" + s, "~2", bx[2], by, "N", "v"); pad("BR" + s, "-", bx[3], by, M, "v")
    tr(A1, (xr, 38.74), (bx[1], 43.5), (bx[1], by))
    tr("N", (xn, NY), (xn, 44.5), (bx[2] + 1.2, 44.5), (bx[2], 46), (bx[2], by))
    # electrolítico, su resistencia de descarga y la bornera
    pad("CE" + s, "+", X + 6.2, 63, P); pad("CE" + s, "-", X + 11.2, 63, M)
    pad("RC" + s, "+", bx[0], 73, P); pad("RC" + s, "-", bx[3], 73, M)
    pad("J" + s, "+", X + 6.2, 85, P); pad("J" + s, "-", X + 11.2, 85, M)
    tr(P, (bx[0], by), (bx[0], 81), (X + 6.2, 85)); tr(P, (bx[0], 63), (X + 6.2, 63))
    tr(M, (bx[3], by), (bx[3], 81), (X + 11.2, 85)); tr(M, (bx[3], 63), (X + 11.2, 63))
last = X0 + (N_CH - 1) * PITCH
tr("L", (5, LY), (last + 11.5, LY))
tr("N", (5, NY), (last + 16, NY))

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
        shapes.append((n, f"{r}.{pn}", ((x, y), (x, y)), PAD/2))
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
    if not (2 < x < W-2 and 2 < y < H-2): errors.append(f"{r}.{pn} fuera de la placa")
if errors: print("\n".join(errors)); sys.exit(1)
print(f"DRC OK: placa {W}×{H} mm, {len(pads)} pads, separación mínima real {worst:.2f} mm")

# ---------- SVG ----------
def path_d(pts): return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts)
def pad_svg(x, y, f, fill, grow=0):
    if f == "v":
        return f'<rect x="{x-BR_W/2-grow:.2f}" y="{y-BR_H/2-grow:.2f}" width="{BR_W+2*grow}" height="{BR_H+2*grow}" rx="{BR_W/2+grow}" fill="{fill}"/>'
    return f'<circle cx="{x}" cy="{y}" r="{PAD/2+grow}" fill="{fill}"/>'
def copper_svg():
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">',
         f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fff" stroke="#000" stroke-width="0.3"/>']
    for n, pts in traces:
        o.append(f'<path d="{path_d(pts)}" fill="none" stroke="#000" stroke-width="{TW}" stroke-linecap="round" stroke-linejoin="round"/>')
    for r, pn, x, y, n, f in pads: o.append(pad_svg(x, y, f, "#000"))
    for r, pn, x, y, n, f in pads: o.append(f'<circle cx="{x}" cy="{y}" r="{DRILL/2}" fill="#fff"/>')
    # texto en espejo, en el margen izquierdo libre
    o.append(f'<g transform="translate(6.5 84) rotate(-90) scale(-1 1)"><text x="-62" y="0" font-family="Arial,Helvetica,sans-serif" font-weight="700" font-size="3.2" fill="#000">5 CANALES 127V</text></g>')
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
    o.append(f'<rect x="1.2" y="2" width="7.6" height="11" {S}/>' + T(5, 16.5, "J0", 2.2) + T(5, 19, "127V~", 1.5, w="400"))
    o.append(T(10.5, 6, "L", 1.8) + T(10.5, 11.5, "N", 1.8))
    for k in range(N_CH):
        X = X0 + k * PITCH; s = str(k + 1)
        xc, xr = X + 5, X + 11.5
        o.append(f'<rect x="{xc-4.3}" y="2.5" width="8.6" height="19.5" rx="1" {S}/>')
        o.append(T(xc, 12.6, "C" + s, 2.2) + T(xc, 15.4, "X2", 1.5, w="400") + T(xc, 17.6, "275VAC", 1.3, w="400"))
        o.append(f'<rect x="{xr-1.3}" y="8.5" width="2.6" height="8" rx="1.1" {S}/>' + T(xr+0.6, 12.5, "1M", 1.5, rot=-90))
        o.append(f'<rect x="{xr-1.8}" y="26" width="3.6" height="10" rx="1.5" {S}/>' + T(xr+0.6, 31, "150Ω", 1.5, rot=-90))
        o.append(T(xc, 31, "RS" + s, 1.6) + T(xc, 33.2, "1W", 1.4, w="400"))
        o.append(f'<rect x="{X+0.9}" y="47.2" width="16.6" height="3.6" rx="0.5" {S}/>')
        o.append(f'<path d="M{X+0.9} 48.4 L{X+2.1} 47.2" stroke="#000" stroke-width="0.35"/>')
        for i, lab in enumerate(["+", "~", "~", "−"]):
            o.append(T(X + 3 + i * BR_P, 46.2, lab, 2.0))
        o.append(T(X + 9.2, 53.3, "BR" + s + " KBP", 1.5, w="400"))
        o.append(f'<circle cx="{X+8.7}" cy="63" r="6.5" {S}/><path d="M{X+11.2} 56.6 A6.5 6.5 0 0 1 {X+11.2} 69.4" stroke="#000" stroke-width="0.35" fill="#ddd"/>')
        o.append(T(X+8.7, 60, "CE" + s, 1.8) + T(X+8.7, 67.5, "47µF 250V", 1.2, w="400") + T(X+4.4, 63.8, "+", 2.2) + T(X+12.9, 63.8, "−", 2.2))
        o.append(f'<rect x="{X+5.2}" y="71.7" width="7" height="2.6" rx="1.1" {S}/>' + T(X+8.7, 77, "220k", 1.4, w="400"))
        o.append(f'<rect x="{X+3.7}" y="81.3" width="10" height="7.4" {S}/>')
        o.append(T(X+6.2, 83.2, "+", 1.8) + T(X+11.2, 83.2, "−", 1.8) + T(X+8.7, 91.6, "SAL " + s, 1.9))
    for r, pn, x, y, n, f in pads: o.append(f'<circle cx="{x}" cy="{y}" r="0.55" fill="#000"/>')
    o.append('</svg>')
    return "\n".join(o)

here = os.path.dirname(os.path.abspath(__file__))
open(os.path.join(here, "cobre_planchar.svg"), "w").write(copper_svg())
open(os.path.join(here, "componentes.svg"), "w").write(comp_svg())
print("SVG escritos")
