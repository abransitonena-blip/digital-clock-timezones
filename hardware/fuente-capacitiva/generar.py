"""Genera el PCB (una cara) de la fuente capacitiva de 5 salidas LED.
Coordenadas en mm, vistas desde el lado de componentes.
Salida: cobre_planchar.svg (imprimir SIN espejo), componentes.svg, y chequeo de reglas."""
import math, itertools, sys, os

W, H = 95, 72          # tamaño de la placa (mm)
PAD = 3.0              # diámetro de pad
DRILL = 0.8            # punto blanco guía para la broca
TW = 1.8               # ancho de pista
CLEAR = 1.5            # separación mínima entre redes distintas

pads = []   # (ref, pin, x, y, net)
def pad(ref, pin, x, y, net): pads.append((ref, pin, x, y, net))

# J0 entrada 127 V (bornera KF301, paso 5 mm)
pad("J0", "L", 6, 12, "L"); pad("J0", "N", 6, 17, "N")
# C1 X2: un lado fijo, el otro con dos agujeros (paso 15 o 22.5 mm)
pad("C1", "1", 16, 12, "L"); pad("C1", "2", 31, 12, "B"); pad("C1", "2b", 38.5, 12, "B")
# R1 1 MΩ (descarga de C1), paso 15 mm
pad("R1", "1", 16, 22, "L"); pad("R1", "2", 31, 22, "B")
# R2 150 Ω 1 W, paso 17.78 mm
pad("R2", "1", 35, 22, "B"); pad("R2", "2", 52.78, 22, "AC1")
# Puente con 4× 1N4007 (paso 10.16 mm)
pad("D1", "A", 66, 14, "AC1");   pad("D1", "K", 76.16, 14, "P")
pad("D3", "K", 63, 17, "AC1");   pad("D3", "A", 63, 27.16, "M")
pad("D2", "K", 79, 17, "P");     pad("D2", "A", 79, 27.16, "N")
pad("D4", "A", 66, 30, "M");     pad("D4", "K", 76.16, 30, "N")
# C2 47 µF 250 V (paso 5 mm)
pad("C2", "-", 61, 40, "M"); pad("C2", "+", 66, 40, "P")
# R3 220 kΩ (descarga de C2), paso 10 mm
pad("R3", "-", 61, 52, "M"); pad("R3", "+", 71, 52, "P")
# 5 salidas en serie (borneras KF301 juntas, paso 5 mm)
chain = ["P", "S1", "S1", "S2", "S2", "S3", "S3", "S4", "S4", "M"]
xs = [71, 66, 61, 56, 51, 46, 41, 36, 31, 26]
for i, (x, n) in enumerate(zip(xs, chain)):
    pad(f"J{i//2+1}", "+" if i % 2 == 0 else "-", x, 60, n)

traces = [  # (net, [(x,y),...])
    ("L",  [(6, 12), (16, 12), (16, 22)]),
    ("B",  [(31, 12), (38.5, 12)]),
    ("B",  [(31, 12), (31, 22), (35, 22)]),
    ("AC1", [(52.78, 22), (58, 22), (63, 17), (66, 14)]),
    ("P",  [(76.16, 14), (79, 17)]),
    ("P",  [(76.16, 14), (71, 22), (71, 60)]),
    ("P",  [(66, 40), (71, 40)]),
    ("N",  [(76.16, 30), (79, 27.16), (89, 27.16), (89, 67), (6, 67), (6, 17)]),
    ("M",  [(63, 27.16), (66, 30), (61, 35), (61, 52), (26, 52), (26, 60)]),
    ("S1", [(66, 60), (61, 60)]), ("S2", [(56, 60), (51, 60)]),
    ("S3", [(46, 60), (41, 60)]), ("S4", [(36, 60), (31, 60)]),
]

# ---------- chequeo de reglas (DRC) y de conexiones ----------
def seg_pt(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx-ax, by-ay; L2 = dx*dx+dy*dy
    t = 0 if L2 == 0 else max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/L2))
    return math.hypot(px-(ax+t*dx), py-(ay+t*dy))
def seg_seg(a, b, c, d):
    def ccw(p, q, r): return (r[1]-p[1])*(q[0]-p[0]) - (q[1]-p[1])*(r[0]-p[0])
    if (ccw(a,b,c)*ccw(a,b,d) < 0) and (ccw(c,d,a)*ccw(c,d,b) < 0): return 0
    return min(seg_pt(a,c,d), seg_pt(b,c,d), seg_pt(c,a,b), seg_pt(d,a,b))
shapes = []  # (net, kind, geom, radius)
for r, pn, x, y, n in pads: shapes.append((n, f"{r}.{pn}", ((x, y), (x, y)), PAD/2))
for n, pts in traces:
    for a, b in zip(pts, pts[1:]): shapes.append((n, f"pista {n}", (a, b), TW/2))
errors = []
for s1, s2 in itertools.combinations(shapes, 2):
    d = seg_seg(*s1[2], *s2[2]) - s1[3] - s2[3]
    if s1[0] != s2[0] and d < CLEAR:
        errors.append(f"separación {d:.2f} mm entre {s1[1]} y {s2[1]}")
# cada red debe quedar en una sola pieza
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
if errors:
    print("\n".join(errors)); sys.exit(1)
print(f"DRC OK: {len(pads)} pads, {sum(len(p)-1 for _,p in traces)} tramos, separación mínima ≥ {CLEAR} mm")

# ---------- SVG ----------
def path_d(pts): return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts)
def copper_svg(scale_bar=True):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">',
         f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fff" stroke="#000" stroke-width="0.3"/>']
    for n, pts in traces:
        o.append(f'<path d="{path_d(pts)}" fill="none" stroke="#000" stroke-width="{TW}" stroke-linecap="round" stroke-linejoin="round"/>')
    for r, pn, x, y, n in pads:
        o.append(f'<circle cx="{x}" cy="{y}" r="{PAD/2}" fill="#000"/>')
    for r, pn, x, y, n in pads:
        o.append(f'<circle cx="{x}" cy="{y}" r="{DRILL/2}" fill="#fff"/>')
    # texto en espejo: al planchar queda derecho sobre el cobre
    o.append(f'<g transform="translate(46 0) scale(-1 1)"><text x="0" y="42" font-family="Arial,Helvetica,sans-serif" font-weight="700" font-size="3.2" fill="#000">FUENTE 127V 5 SAL</text></g>')
    o.append('</svg>')
    return "\n".join(o)

values = {"J0": "127V~", "C1": "X2 564J 275VAC", "R1": "1M ½W", "R2": "150Ω 1W",
          "D1": "1N4007", "D2": "1N4007", "D3": "1N4007", "D4": "1N4007",
          "C2": "47µF 250V", "R3": "220k ½W"}
def comp_svg():
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}" font-family="Arial,Helvetica,sans-serif">',
         f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fff" stroke="#000" stroke-width="0.3"/>']
    for n, pts in traces:  # pistas vistas "a través" de la placa
        o.append(f'<path d="{path_d(pts)}" fill="none" stroke="#e8c9a8" stroke-width="{TW}" stroke-linecap="round" stroke-linejoin="round"/>')
    S = 'fill="none" stroke="#000" stroke-width="0.35"'
    T = lambda x, y, s, sz=2.2, a="middle", w="700": f'<text x="{x}" y="{y}" font-size="{sz}" text-anchor="{a}" font-weight="{w}">{s}</text>'
    # cuerpos
    o.append(f'<rect x="1.5" y="9" width="8" height="11" {S}/>' + T(5.5, 7.6, "J0") + T(2.5, 13, "L", 1.8, "start") + T(2.5, 18, "N", 1.8, "start"))
    o.append(f'<rect x="13" y="7.5" width="28.5" height="9" rx="1" {S}/>' + T(27, 11, "C1", 2.6) + T(27, 15.5, values["C1"], 1.7, w="400"))
    o.append(f'<rect x="19.5" y="20.6" width="8" height="2.8" rx="1.2" {S}/>' + T(23.5, 19.6, "R1 " + values["R1"], 1.7, w="400"))
    o.append(f'<rect x="38.5" y="20.3" width="11" height="3.4" rx="1.5" {S}/>' + T(44, 19.4, "R2 " + values["R2"], 1.7, w="400"))
    for ref, (a, b) in {"D1": ((66, 14), (76.16, 14)), "D3": ((63, 17), (63, 27.16)),
                        "D2": ((79, 17), (79, 27.16)), "D4": ((66, 30), (76.16, 30))}.items():
        A = next((x, y) for r, p, x, y, n in pads if r == ref and p == "A")
        K = next((x, y) for r, p, x, y, n in pads if r == ref and p == "K")
        mx, my = (A[0]+K[0])/2, (A[1]+K[1])/2
        ux, uy = (K[0]-A[0])/10.16, (K[1]-A[1])/10.16
        px, py = -uy, ux
        o.append(f'<path d="M{mx-2.6*ux-1.3*px} {my-2.6*uy-1.3*py} L{mx+2.6*ux-1.3*px} {my+2.6*uy-1.3*py} L{mx+2.6*ux+1.3*px} {my+2.6*uy+1.3*py} L{mx-2.6*ux+1.3*px} {my-2.6*uy+1.3*py} Z" {S}/>')
        bx, by = mx+1.8*ux, my+1.8*uy  # franja del cátodo
        o.append(f'<path d="M{bx-1.3*px} {by-1.3*py} L{bx+1.3*px} {by+1.3*py}" stroke="#000" stroke-width="0.9"/>')
        lx, ly = (mx+3.4*px, my+3.4*py) if ref in ("D1", "D4") else ((mx-3.2*px, my-3.2*py) if ref == "D3" else (mx+3.4, my))
        o.append(T(lx, ly+0.8, ref, 2))
    o.append(T(71, 23.5, "4×1N4007", 1.6, w="400") + T(71, 25.5, "franja = cátodo", 1.4, w="400"))
    o.append(f'<circle cx="63.5" cy="40" r="6.5" {S}/><path d="M61 33.6 A6.5 6.5 0 0 0 61 46.4" stroke="#000" stroke-width="0.35" fill="#ddd"/>')
    o.append(T(63.5, 37, "C2", 2.2) + T(63.5, 44.5, values["C2"], 1.5, w="400") + T(55.5, 40.8, "−", 2.6) + T(68.4, 40.8, "+", 2.4))
    o.append(f'<rect x="62.5" y="50.6" width="7" height="2.8" rx="1.2" {S}/>' + T(66, 49.6, "R3 " + values["R3"], 1.6, w="400"))
    for k in range(5):
        x0 = xs[2*k+1] - 2.5
        o.append(f'<rect x="{x0}" y="56.5" width="10" height="7.5" {S}/>')
        o.append(T(x0+5, 66.5, f"SAL{k+1}", 1.9) + T(xs[2*k], 58.2, "+", 1.8) + T(xs[2*k+1], 58.2, "−", 1.8))
    o.append(T(48, 70.6, "salidas en serie: misma corriente en las 5", 1.6, w="400"))
    o.append(T(W/2, 3.8, "VISTA DE COMPONENTES (lado sin cobre)", 2, w="700"))
    for r, pn, x, y, n in pads:
        o.append(f'<circle cx="{x}" cy="{y}" r="0.55" fill="#000"/>')
    o.append('</svg>')
    return "\n".join(o)

here = os.path.dirname(os.path.abspath(__file__))
open(os.path.join(here, "cobre_planchar.svg"), "w").write(copper_svg())
open(os.path.join(here, "componentes.svg"), "w").write(comp_svg())
print("SVG escritos")
