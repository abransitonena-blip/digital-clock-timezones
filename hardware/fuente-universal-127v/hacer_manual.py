"""Manual de la fuente universal 127 V (flyback + LM2596-ADJ). Escribe manual.html."""
import os, re
here = os.path.dirname(os.path.abspath(__file__))
rd = lambda f: open(os.path.join(here, f)).read()
cu, silk, mont = rd("cobre_planchar.svg"), rd("serigrafia_planchar.svg"), rd("montaje.svg")
fit = lambda s, w: re.sub(r'width="[0-9.]+mm" height="[0-9.]+mm"', f'width="{w}mm" height="{w*84/170:.1f}mm"', s, count=1)
S = 'fill="none" stroke="#000" stroke-width="0.4" stroke-linecap="round" stroke-linejoin="round"'
def res_v(x, y1, y2, lab="", val=""):
    m = (y1+y2)/2
    return (f'<path d="M{x} {y1} V{m-3.5} M{x} {m+3.5} V{y2}" {S}/><rect x="{x-1.5}" y="{m-3.5}" width="3" height="7" {S}/>'
            f'<text x="{x+2.3}" y="{m}" font-size="2.3">{lab}</text><text x="{x+2.3}" y="{m+2.6}" font-size="2">{val}</text>')
def res_h(x1, x2, y, lab="", val=""):
    m = (x1+x2)/2
    return (f'<path d="M{x1} {y} H{m-3.5} M{m+3.5} {y} H{x2}" {S}/><rect x="{m-3.5}" y="{y-1.5}" width="7" height="3" {S}/>'
            f'<text x="{m}" y="{y-2.3}" font-size="2.3" text-anchor="middle">{lab} {val}</text>')
def cap_v(x, y1, y2, lab="", val="", pol=False):
    m = (y1+y2)/2
    low = f'<path d="M{x-3} {m+1.6} Q{x} {m+0.4} {x+3} {m+1.6}" {S} stroke-width="0.7"/>' if pol else f'<path d="M{x-3} {m+1} H{x+3}" {S} stroke-width="0.7"/>'
    plus = f'<text x="{x-4.6}" y="{m-1.6}" font-size="2.4">+</text>' if pol else ""
    return (f'<path d="M{x} {y1} V{m-1} M{x} {m+1} V{y2}" {S}/><path d="M{x-3} {m-1} H{x+3}" {S} stroke-width="0.7"/>' + low + plus +
            f'<text x="{x+3.6}" y="{m}" font-size="2.3">{lab}</text><text x="{x+3.6}" y="{m+2.6}" font-size="2">{val}</text>')
def dio_v(x, y1, y2, lab="", val="", up=True, zener=False):      # up: cátodo arriba
    m = (y1+y2)/2; a, k = (m+2, m-2) if up else (m-2, m+2)
    bar = f'<path d="M{x-2.2} {k} H{x+2.2}" {S}/>' + (f'<path d="M{x-2.2} {k} l-0.8 {"-" if up else ""}0.8 M{x+2.2} {k} l0.8 {"" if up else "-"}0.8" {S}/>' if zener else "")
    return (f'<path d="M{x} {y1} V{min(a,k)} M{x} {max(a,k)} V{y2}" {S}/><path d="M{x-2.2} {a} H{x+2.2} L{x} {k} Z" {S}/>' + bar +
            f'<text x="{x+3}" y="{m}" font-size="2.3">{lab}</text><text x="{x+3}" y="{m+2.6}" font-size="2">{val}</text>')
def dio_h(x1, x2, y, lab="", val=""):        # ánodo a la izquierda
    m = (x1+x2)/2
    return (f'<path d="M{x1} {y} H{m-2} M{m+2} {y} H{x2}" {S}/><path d="M{m-2} {y-2.2} V{y+2.2} L{m+2} {y} Z M{m+2} {y-2.2} V{y+2.2}" {S}/>'
            f'<text x="{m}" y="{y-3}" font-size="2.3" text-anchor="middle">{lab} {val}</text>')
def coil_v(x, y1, y2, left=True):
    n = 4; h = (y2-y1)/n; s = -1 if left else 1
    d = f"M{x} {y1}" + "".join(f" q{2.8*s} {h/2} 0 {h}" for _ in range(n))
    return f'<path d="{d}" {S}/>'
dot = lambda x, y: f'<circle cx="{x}" cy="{y}" r="0.75"/>'
nodo = lambda x, y: f'<circle cx="{x}" cy="{y}" r="0.7"/>'
term = lambda x, y: f'<circle cx="{x}" cy="{y}" r="1.3" fill="#fff" stroke="#000" stroke-width="0.4"/>'
def ln(*pts): return f'<path d="M{pts[0][0]} {pts[0][1]}' + "".join(f" L{x} {y}" for x, y in pts[1:]) + f'" {S}/>'
def lab(x, y, t, sz=2.3, a="start", w="400", c="#000"): return f'<text x="{x}" y="{y}" font-size="{sz}" text-anchor="{a}" font-weight="{w}" fill="{c}">{t}</text>'
def boxr(x1, y, x2, label=""):   # resistencia horizontal entre x1 y x2
    m = (x1+x2)/2; return ln((x1, y), (m-3, y)) + f'<rect x="{m-3}" y="{y-1.3}" width="6" height="2.6" {S}/>' + ln((m+3, y), (x2, y)) + lab(m, y-2, label, 2.0, "middle")
def boxv(x, y1, y2, label="", val=""):
    m = (y1+y2)/2; return ln((x, y1), (x, m-3)) + f'<rect x="{x-1.3}" y="{m-3}" width="2.6" height="6" {S}/>' + ln((x, m+3), (x, y2)) + lab(x+2, m-0.3, label, 2.1) + lab(x+2, m+2.2, val, 1.9)
def capv(x, y1, y2, label="", val="", pol=False, izq=False):
    m = (y1+y2)/2
    if izq:
        lx, an = x-3.2, "end"
    else:
        lx, an = x+3.2, "start"
    low = f'<path d="M{x-2.6} {m+1.5} Q{x} {m+0.4} {x+2.6} {m+1.5}" {S}/>' if pol else ln((x-2.6, m+1), (x+2.6, m+1))
    return ln((x, y1), (x, m-1)) + ln((x-2.6, m-1), (x+2.6, m-1)) + low + ln((x, m+1), (x, y2)) + (lab(x-4.2 if not izq else x+2.6, m-1.4, "+", 2.2) if pol else "") + lab(lx, m-0.3, label, 2.1, an) + lab(lx, m+2.2, val, 1.9, an)
def diov(x, ya, yk, label="", val="", tvs=False, izq=False):   # ánodo en ya, cátodo en yk (cátodo arriba si yk < ya)
    s_ = -1 if yk < ya else 1; t0, t1 = (ya+yk)/2 - 1.8*s_, (ya+yk)/2 + 1.8*s_
    bar = ln((x-2, t1), (x+2, t1)) + (ln((x-2, t1), (x-2.7, t1-0.8*s_)) + ln((x+2, t1), (x+2.7, t1+0.8*s_)) if tvs else "")
    return ln((x, ya), (x, t0)) + f'<path d="M{x-2} {t0} L{x+2} {t0} L{x} {t1} Z" {S}/>' + bar + ln((x, t1), (x, yk)) + (lab(x-3, (ya+yk)/2, label, 2.1, "end") + lab(x-3, (ya+yk)/2+2.4, val, 1.9, "end") if izq else lab(x+3, (ya+yk)/2, label, 2.1) + lab(x+3, (ya+yk)/2+2.4, val, 1.9))
def dioh(xa, xk, y, label=""):
    s_ = 1 if xk > xa else -1; m = (xa+xk)/2; t0, t1 = m-1.8*s_, m+1.8*s_
    return ln((xa, y), (t0, y)) + f'<path d="M{t0} {y-2} L{t0} {y+2} L{t1} {y} Z" {S}/>' + ln((t1, y-2), (t1, y+2)) + ln((t1, y), (xk, y)) + lab(m, y-2.8, label, 2.0, "middle")
def coil(x, y1, y2, right=True):
    n = 4; h = (y2-y1)/n; k = 2.6 if right else -2.6
    return f'<path d="M{x} {y1}' + "".join(f" q{k} {h/2} 0 {h}" for _ in range(n)) + f'" {S}/>'
N = lambda x, y: f'<circle cx="{x}" cy="{y}" r="0.65"/>'
def GND(x, y): return ln((x, y), (x, y+1.2)) + ln((x-1.8, y+1.2), (x+1.8, y+1.2)) + ln((x-1.1, y+1.9), (x+1.1, y+1.9)) + ln((x-0.4, y+2.6), (x+0.4, y+2.6))
DOT = lambda x, y: f'<circle cx="{x}" cy="{y}" r="0.8"/>'
TER = lambda x, y: f'<circle cx="{x}" cy="{y}" r="1.2" fill="#fff" stroke="#000" stroke-width="0.4"/>'
HVY, PGY, PY, GY = 12, 58, 12, 40
e = []
# entrada
e += [TER(4, 20), TER(4, 44), lab(1, 16, "J1 127 V~", 2.2, w="700"), lab(1, 54, "J1: arriba fase (L), abajo neutro (N)", 1.7)]
e += [ln((5.2, 20), (9, 20)), f'<rect x="9" y="18.7" width="8" height="2.6" {S}/>', ln((9, 20), (17, 20)), lab(9, 17, "F1 1 A lento", 1.9)]
e += [ln((5.2, 44), (9, 44)), f'<rect x="9" y="42.7" width="8" height="2.6" {S}/>', ln((8, 46.5), (18, 41.5)), lab(9, 49, "TH1 NTC 5D-9", 1.9)]
e += [ln((17, 20), (33, 20), (33, 26), (36, 26)), ln((17, 44), (33, 44), (33, 38), (36, 38))]
e += [capv(23, 20, 44, "CX", "100n X2"), N(23, 20), N(23, 44)]
e += [ln((29, 20), (29, 28)), f'<rect x="27.7" y="28" width="2.6" height="8" {S}/>', ln((29, 36), (29, 44)), ln((26.5, 37), (31.5, 27)), N(29, 20), N(29, 44), lab(28, 25.5, "RV1", 1.9, "end")]
e += [f'<rect x="36" y="22" width="10" height="20" rx="0.8" {S}/>', f'<path d="M41 28 L44 32 L41 36 L38 32 Z" {S} stroke-width="0.3"/>', lab(37, 27.6, "~", 2.8), lab(37, 39.6, "~", 2.8), lab(43.4, 27.3, "+", 2.2), lab(43.4, 39.3, "−", 2.2), lab(41, 45, "BR1 KBP307", 1.9, "middle")]
e += [ln((46, 26), (50, 26), (50, HVY), (88, HVY)), ln((46, 38), (50, 38), (50, PGY)), ln((14, PGY), (86, PGY))]
e += [capv(56, HVY, PGY, "C12", "100µF 250V", True, izq=True), N(56, HVY), N(56, PGY), N(50, HVY), N(50, PGY)]
e += [boxv(64, HVY, 21, "R14", "39k"), boxv(64, 21, 30, "R15", "39k"), boxv(64, 30, 39, "R16", "39k"), N(64, HVY), ln((64, 39), (64, 64))]
e += [lab(56, 9, "HV ≈ 170 V", 2.0), lab(11, 59, "PG", 2.0, w="700")]
# transformador, recortador, MOSFET
e += [ln((84, HVY), (84, 16)), coil(84, 16, 34, True), ln((84, 34), (84, 39)), DOT(86.6, 16.5), lab(82, 17, "H", 1.9, "end"), lab(82, 34, "D", 1.9, "end")]
e += [f'<path d="M89.5 14 V36 M90.6 14 V36" {S}/>', lab(90, 12.8, "T1", 2.0, "middle", "700")]
e += [ln((84, 36), (74, 36)), diov(74, 36, 27, "D3", ""), diov(74, 27, HVY, "D5", "TVS", tvs=True), N(84, 36), N(74, HVY), lab(66.5, 26, "", 1)]
e += [ln((84, 39), (84, 41)), f'<path d="M80 42 V50 M84 41 V42 H81 M84 50 V49 H81 M81 46 H84 V50" {S}/>', f'<path d="M78 43.5 V48.5" {S}/>', '<path d="M81.6 45.3 L83 46 L81.6 46.7 Z"/>']
e += [lab(86, 45, "Q1", 2.1, w="700"), lab(86, 47.5, "4N60", 1.9), ln((78, 46), (76, 46), (76, 74))]
e += [ln((84, 50), (84, 51)), boxv(84, 51, PGY, "R12", "0.47Ω"), N(84, 51), N(84, PGY), ln((84, 51), (89, 51), (89, 82))]
# barrera
e += [f'<path d="M92.5 5 V109" stroke="#c00" stroke-width="0.45" stroke-dasharray="1.6 1.1" fill="none"/>', lab(93.5, 108.5, "barrera de aislamiento (ranura)", 1.9, c="#c00")]
# secundario
e += [coil(96, 16, 34, False), DOT(93.6, 33.5), lab(98, 17, "S1", 1.9), lab(98, 34, "S0", 1.9)]
e += [ln((96, 16), (96, PY), (101, PY)), dioh(101, 110, PY, "D2 SR5100"), ln((110, PY), (178, PY)), ln((96, 34), (96, GY), (178, GY))]
e += [capv(116, PY, GY, "C6", "1000µF", True), capv(125, PY, GY, "C7", "1000µF", True), N(116, PY), N(125, PY), N(116, GY), N(125, GY)]
e += [boxv(134, PY, 26, "R2", "10k"), ln((134, 26), (134, 30)), f'<path d="M132 30 L136 30 L134 34 Z" {S}/>', ln((132, 34), (136, 34)), ln((134, 34), (134, GY)), lab(136.5, 33, "LED1", 1.8), N(134, PY), N(134, GY)]
e += [boxv(142, PY, 26, "R4", "20k"), boxv(142, 26, GY, "R5", "2.2k"), N(142, PY), N(142, 26), N(142, GY)]
e += [ln((142, 26), (146, 26), (146, 32), (149.6, 32)), f'<path d="M150 35 L154 35 L152 31 Z" {S}/>', ln((150, 31), (154, 31)), ln((154, 31), (154.7, 30.3)), ln((152, 31), (152, 28)), ln((152, 35), (152, GY)), lab(155, 34, "U3 TL431", 1.9), N(152, GY)]
e += [ln((152, 28), (152, 23), (150.5, 23)), f'<rect x="146.5" y="21.8" width="4" height="2.4" {S}/>', ln((146.5, 23), (146, 23), (146, 26)), lab(148.5, 20.6, "R7+C8", 1.8, "middle")]
e += [boxv(162, PY, 20, "R6", "1k"), N(162, PY), N(162, 20), f'<path d="M160 21 L164 21 L162 25 Z" {S}/>', ln((160, 25), (164, 25)), ln((162, 20), (162, 21)), ln((162, 25), (162, 28), (152, 28)), N(162, 28), N(152, 28)]
e += [ln((162, 20), (170, 20)), boxv(170, 20, 28, "R8", "1k"), ln((170, 28), (162, 28)), f'<path d="M165 22 l2 -1.5 M165 24 l2 -1.5" {S} stroke-width="0.35"/>', lab(158, 31, "U2 LED", 1.8, "end")]
e += [lab(178, 10.5, "≈ 25 V", 2.0, "end", "700"), lab(185, 15, "→ etapa 2", 2.0, "end"), lab(185, 43, "→ etapa 2", 2.0, "end"), lab(112, 46, "Vsal = 2.495 × (1 + R4/R5) ≈ 25 V", 1.9)]
e += [ln((104, GY), (104, 48)), capv(104, 48, 58, "CY", "2.2n Y1"), ln((104, 58), (104, 62)), lab(106, 64, "va al HV del primario", 1.8), N(104, GY)]
# control
e += [f'<rect x="40" y="68" width="26" height="32" rx="1" {S}/>', lab(53, 83, "U4", 2.4, "middle", "700"), lab(53, 86, "UC3844", 2.0, "middle")]
e += [lab(41, 74.7, "1 COMP", 1.8), lab(41, 82.7, "2 VFB", 1.8), lab(65, 74.7, "6 OUT", 1.8, "end"), lab(65, 82.7, "3 CS", 1.8, "end"), lab(65, 90.7, "4 RT/CT", 1.8, "end"), lab(65, 96.7, "8 VREF", 1.8, "end"), lab(53, 71, "7 VCC", 1.8, "middle"), lab(53, 98.5, "5 GND", 1.8, "middle")]
e += [ln((53, 70), (53, 64), (84, 64)), ln((46, 64), (53, 64)), N(64, 64), N(53, 64), ln((46, 64), (46, 62)), ln((43.4, 62), (48.6, 62)), f'<path d="M43.4 59.6 Q46 60.8 48.6 59.6" {S}/>', ln((46, 60), (46, PGY)), N(46, PGY), lab(48.6, 63.6, "+", 2.2), lab(41.5, 61.6, "C10 47µF", 1.9, "end")]
e += [dioh(84, 76, 64, "D4"), ln((84, 64), (84, 70)), coil(84, 70, 84, True), ln((84, 84), (84, 85)), GND(84, 85), DOT(86.6, 83.5), lab(82, 72, "A", 1.9, "end"), lab(82, 84, "B", 1.9, "end"), lab(88, 77, "T1 aux", 1.9)]
e += [boxr(66, 74, 76, "R11 22Ω"), ln((89, 82), (80, 82)), boxr(80, 82, 70, ""), lab(75, 80, "R13 1k", 1.9, "middle"), ln((70, 82), (66, 82)), N(72, 82)]
e += [capv(72, 82, 87, "C11", "470p"), GND(72, 87)]
e += [ln((66, 90), (69, 90)), ln((66, 96), (69, 96)), boxv(69, 96, 90, "", ""), lab(66.5, 93.6, "R9", 1.8, "end"), N(69, 90)]
e += [ln((69, 90), (76, 90)), capv(76, 90, 97, "C9", "1.2n"), GND(76, 97)]
e += [ln((53, 100), (53, 101)), GND(53, 101), ln((40, 82), (36, 82), (36, 84)), GND(36, 84)]
e += [ln((40, 74), (30, 74), (30, 77)), f'<path d="M26 77 V85 M26 79 L30 77 M26 83 L30 85 V87" {S}/>', '<path d="M28.6 84 L30 85 L28.4 85.3 Z"/>', GND(30, 87), f'<path d="M20 78 l3 1.5 M20 81 l3 1.5" {S} stroke-width="0.35"/>', lab(12, 76, "U2 foto-", 1.8), lab(12, 78.3, "transistor", 1.8)]
e += [GND(30, PGY), lab(40, 105, "⏚ = tierra del primario (PG), toda unida", 1.9)]
esq1 = '<svg width="186mm" height="110mm" viewBox="0 0 186 110" font-family="Arial,Helvetica,sans-serif">' + "".join(e) + '</svg>'
# ---------- tablas ----------
def fila(r): return "<tr>" + "".join(f"<td{' class=r' if i == 0 else ''}>{c}</td>" for i, c in enumerate(r)) + "</tr>"
PRI = [("J1", "1", "Bornera 2 tornillos 5.08 mm", "Entrada 127 V"),
       ("F1", "1", "Fusible de vidrio 5×20 <b>1 A lento</b> con patitas (o portafusible)", "Nunca más grande"),
       ("TH1", "1", "Termistor NTC <b>5D-9</b> (5 Ω)", "Limita el golpe al conectar"),
       ("RV1", "1", "Varistor <b>10D201K</b>", "Contra picos de la red"),
       ("CX", "1", "Capacitor <b>100 nF 275 V~ X2</b>, paso 10 mm", "Ruido hacia la red"),
       ("BR1", "1", "Puente <b>KBP307</b>", ""),
       ("C12", "1", "Electrolítico <b>100 µF 250 V</b> (o 400 V), 16 mm, paso 7.5 mm", "Filtro de alto voltaje"),
       ("U4", "1", "<b>UC3844</b> DIP-8 (con base)", "No UC3842: ese no limita a 50 %"),
       ("Q1", "1", "MOSFET <b>4N60</b> (4 A 600 V, TO-220) + disipador chico de clip", ""),
       ("T1", "1", "Núcleo <b>EE25</b> + carrete horizontal de 10 patas", "Ver la receta"),
       ("D3", "1", "Diodo rápido <b>FR107</b> (o UF4007)", "Recortador"),
       ("D5", "1", "TVS <b>P6KE200A</b>", "Recortador"),
       ("D4", "1", "<b>1N4148W</b> (SOD-123)", "Auxiliar"),
       ("R12", "1", "<b>0.47 Ω 1 W</b>, 2512", "Sensor de corriente"),
       ("R14–R16", "3", "<b>39 kΩ</b> 1206", "Arranque (en serie)"),
       ("R9, R10, R11, R13", "4", "10 kΩ (RT), 0 Ω (puente), 22 Ω (compuerta), 1 kΩ (CS) · 1206", ""),
       ("C9, C10, C11", "3", "1.2 nF (CT) 1206 · 47 µF 50 V SMD 6.3 mm · 470 pF 1206", ""),
       ("CY", "1", "Capacitor <b>2.2 nF 400 V~ Y1</b> (azul), paso 10 mm", "Debe decir Y1"),
       ("JP2", "1", "Cable forrado delgado (≈ 6 cm)", "Arranque")]
SEC = [("U2", "1", "Optoacoplador <b>PC817</b>", "Cruza la barrera"),
       ("U3", "1", "<b>TL431</b> TO-92", "Referencia"),
       ("D2", "1", "Schottky <b>SR5100</b> (5 A 100 V)", "Rectificador de salida"),
       ("C6, C7", "2", "Electrolítico <b>1000 µF 35 V</b> bajo ESR, 12.5 mm", ""),
       ("R4, R5, R6, R7, R8", "5", "20 kΩ · 2.2 kΩ · 1 kΩ · 10 kΩ · 1 kΩ (1206)", "Retroalimentación"),
       ("C8", "1", "100 nF 1206", ""),
       ("JP1", "1", "Puente de alambre", ""),
       ("Etapa 2", "—", "La misma lista del módulo universal: LM2596S-ADJ, SS54, 47 µH, 220 µF 50 V, 470 µF 35 V, trimpot 20 k, etc.", "Ver manual del módulo")]
TRA = [("Núcleo", "EE25 de ferrita (2 mitades E) y su carrete horizontal 5 + 5 patas"),
       ("Primario (H → D)", "<b>98 vueltas</b> de alambre magneto <b>0.35 mm</b> (AWG 27), en 3–4 capas, con 1 capa de cinta entre capas"),
       ("Aislamiento", "<b>3 capas</b> de cinta de poliéster (amarilla) o kapton"),
       ("Secundario (S0 → S1)", "<b>22 vueltas</b> de <b>2 hilos de 0.45 mm juntos</b> (AWG 25). Mejor: alambre triple aislado de 0.6 mm"),
       ("Aislamiento", "<b>3 capas</b> de cinta. Si el secundario es magneto normal, deja 3 mm de cinta de margen a cada lado"),
       ("Auxiliar (B → A)", "<b>14 vueltas</b> de 0.2 mm, repartidas a lo ancho"),
       ("Cierre", "2 capas de cinta, mete las dos E y sujétalas con cinta"),
       ("Entrehierro", "Separador de <b>0.25–0.3 mm</b> entre las dos mitades (3 hojas de papel bond). Si tienes medidor LCR: primario <b>0.85–0.95 mH</b>"),
       ("Sentido", "Todos los devanados en el <b>mismo sentido</b> y empezando en la pata indicada (H, S0, B): así queda la fase correcta del flyback")]
tra = "".join(f"<tr><td class=r>{a}</td><td>{b}</td></tr>" for a, b in TRA)
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page {{ size: letter; margin: 10mm 11mm; }}
body {{ font-family: Arial, Helvetica, sans-serif; font-size: 9.4pt; color: #111; margin: 0; }}
h1 {{ font-size: 19pt; margin: 0; }} h2 {{ font-size: 12pt; margin: 4mm 0 1.6mm; border-bottom: 1.5px solid #111; padding-bottom: 0.5mm; }}
.sub {{ color: #444; margin: 0.8mm 0 2.5mm; }}
.specs {{ display: flex; gap: 2.5mm; margin-bottom: 2mm; }} .spec {{ flex: 1; border: 1.5px solid #111; border-radius: 2.5mm; padding: 1.6mm 2.2mm; }}
.spec b {{ display: block; font-size: 12.5pt; }} .spec span {{ color: #555; font-size: 8.3pt; }}
.peligro {{ border: 2.5px solid #c00; background: #fff0f0; border-radius: 2.5mm; padding: 2mm 3mm; margin: 2mm 0; }}
.nota {{ border-left: 3px solid #e8590c; background: #fff4ec; padding: 1.5mm 3mm; margin: 2mm 0; }}
table {{ border-collapse: collapse; width: 100%; font-size: 8.8pt; }} th, td {{ border: 1px solid #999; padding: 1mm 1.6mm; vertical-align: top; text-align: left; }}
th {{ background: #eee; }} td.r {{ font-weight: 700; white-space: nowrap; }}
ol, ul {{ margin: 1mm 0; padding-left: 5.5mm; }} li {{ margin: 0.8mm 0; }}
.pb {{ page-break-before: always; }} .fig {{ text-align: center; }} .cap {{ font-size: 8pt; color: #555; text-align: center; }}
</style></head><body>
<h1>Fuente universal 127 V · 1.2 – 20 V · 2 A</h1>
<div class="sub">Una sola placa, como un cargador: entra 127 V y sale el voltaje que ajustes. Flyback aislado (UC3844 + transformador EE25 hecho por ti) + regulador LM2596S-ADJ. Placa de una cara 17 × 8.4 cm para planchar. Diseño AP.</div>
<div class="specs">
<div class="spec"><b>127 V~</b><span>entrada directa, 60 Hz</span></div>
<div class="spec"><b>1.2 – 20 V</b><span>salida ajustable con trimpot</span></div>
<div class="spec"><b>2 A</b><span>hasta 12 V (máx. 24 W)</span></div>
<div class="spec"><b>Aislada</b><span>transformador + optoacoplador</span></div></div>
<div class="peligro"><b>⚠ Peligro de muerte.</b> Todo el lado derecho de la placa (lado de 127 V) tiene <b>hasta 200 V de corriente directa</b>,
y el capacitor C12 la guarda <b>hasta un minuto después de desconectar</b>. Nunca lo toques conectado. Prueba siempre con un foco en serie
(sección 7), trabaja con una sola mano y, si puedes, con un transformador de aislamiento 1:1. Si no tienes experiencia con fuentes conmutadas,
pide ayuda para la primera prueba.</div>
<h2>Cómo funciona</h2>
<p style="margin:1mm 0">127 V → fusible, NTC, varistor y filtro X2 → puente → <b>C12 (≈ 170 V DC)</b>. El UC3844 prende y apaga el MOSFET 72 000 veces por segundo;
el transformador guarda energía y la pasa al lado seguro, <b>aislado</b>, donde D2 y C6/C7 dan ≈ 25 V. El TL431 compara esos 25 V y, por el
optoacoplador, le dice al UC3844 cuánto dar. Después, el <b>LM2596S-ADJ</b> (el mismo módulo universal) baja a lo que ajustes con el trimpot.
D3 + D5 recortan los picos del transformador; R12 limita la corriente; el devanado auxiliar alimenta al UC3844 una vez arrancado.</p>
<h2>1 · Esquema de la etapa 1 (flyback)</h2>
<div class="fig">{esq1}</div>
<div class="cap">Los puntos en T1 marcan dónde EMPIEZA cada devanado (H, B, S0). La etapa 2 es idéntica al módulo universal ajustable.</div>
<h2 class="pb">2 · Receta del transformador T1 (EE25)</h2>
<table><tr><th>Paso</th><th>Qué hacer</th></tr>{tra}</table>
<div class="nota">Patas del carrete: <b>H, D, B, A</b> del lado de 127 V y <b>S1, S0</b> del lado seguro (vienen marcadas en la serigrafía). Las patas
que no se usan se cortan antes de montar. La placa supone un carrete de <b>patas a 5 mm y filas a 20 mm</b>: antes de grabar, pon tu carrete
sobre la hoja impresa; si no coincide, mándame esas dos medidas y regenero la placa.</div>
<p style="margin:1.5mm 0">Por qué estos números: entrada mínima ≈ 140 V en C12, 24 W de salida, 72 kHz, ciclo máx. 45 %. Pico en el primario ≈ 1.1 A,
inductancia ≈ 0.87 mH, relación 98 : 22 (4.45), voltaje reflejado ≈ 114 V. El MOSFET ve ≈ 200 V + 114 V + pico recortado a ≈ 250 V: lejos de sus 600 V.</p>
<h2>3 · Material</h2>
<table><tr><th>Ref.</th><th>Cant.</th><th>Lado de 127 V</th><th>Nota</th></tr>{"".join(fila(r) for r in PRI)}</table>
<table style="margin-top:2mm"><tr><th>Ref.</th><th>Cant.</th><th>Lado seguro</th><th>Nota</th></tr>{"".join(fila(r) for r in SEC)}</table>
<h2 class="pb">4 · Hoja para planchar — cobre (1:1, ya en espejo)</h2>
<div class="fig">{cu}</div>
<div class="fig" style="margin:1mm 0"><svg width="170mm" height="4mm" viewBox="0 0 170 4"><rect y="1.5" width="170" height="1"/><rect width="0.6" height="4"/><rect x="169.4" width="0.6" height="4"/></svg>
<div class="cap">esta barra debe medir 170 mm — imprime al 100 %</div></div>
<h2>Serigrafía para el lado de piezas (opcional, también en espejo)</h2>
<div class="fig">{silk}</div>
<ol>
<li>Lija, limpia, plancha el cobre y graba con cloruro. Revisa a contraluz que no haya puentes, sobre todo entre las patas del UC3844.</li>
<li><b>Corta la ranura</b> marcada (2 mm de ancho, bajo el transformador): con segueta fina o mototool. Es parte del aislamiento: no la omitas.</li>
<li>Barrenos: 0.8 mm para el trimpot, 1.0 mm para casi todo, 1.3 mm para D2, BR1, F1 y borneras, 3.2 mm en las esquinas.</li>
</ol>
<h2 class="pb">5 · Montaje (visto desde el lado del cobre)</h2>
<div class="fig">{fit(mont, 186)}</div>
<div class="cap">Negro = piezas SMD (lado del cobre). Azul punteado = piezas de patitas (del otro lado). Rosa = pistas del lado de 127 V.</div>
<ol>
<li><b>SMD primero</b>, todas del lado del cobre: LM2596 (etapa 2), luego las del primario (R9–R16, C9–C11, D4) y del secundario (R4–R8, C8).
R10 es un 0 Ω que salta una pista: es normal.</li>
<li><b>Patitas</b>: puentes JP1 (alambre) y JP2 (cable forrado), U4 en su base (muesca/pata 1 marcada), U2 (pata 1 marcada), U3 (cara plana
hacia arriba de la placa), D2/D3/D5 (franja = |), Q1 (cara impresa hacia el UC3844, disipador hacia abajo), BR1, C12, C6, C7, CX, CY, RV1, TH1, F1, J1.</li>
<li><b>T1 al final</b>, ya embobinado y con las patas sobrantes cortadas: H, D, B, A al lado de 127 V; S1, S0 al lado seguro.</li>
<li>Limpia el flux y revisa con lupa. Barniz en el lado de 127 V cuando todo funcione.</li>
</ol>
<h2 class="pb">6 · Antes de conectar</h2>
<ul>
<li>Multímetro en Ω máximo entre <b>cualquier punto del lado seguro y cualquier punto del lado de 127 V</b>: debe marcar <b>OL</b> (abierto). Si marca algo, no conectes.</li>
<li>Entre + y − de C12: no debe marcar corto. Entre D y S de Q1: no debe marcar corto.</li>
<li><b>Prueba la etapa 2 sola</b>: conecta un eliminador de 24 V DC directo a C6 (+) y tierra del secundario, ajusta el trimpot y mide la salida. Así sabes que esa parte está bien.</li>
</ul>
<h2>7 · Primera conexión a 127 V (con foco en serie)</h2>
<ol>
<li>Pon un <b>foco incandescente de 60–100 W en serie</b> con la fase (un socket en el cable). Sin carga en la salida.</li>
<li>Conecta: el foco destella y se apaga o queda apenas naranja = bien. <b>Si el foco prende fuerte y se queda, desconecta</b>: hay un corto (BR1, C12, Q1 o T1 al revés).</li>
<li>Con una mano, mide en C6: <b>23–27 V</b>. LED rojo prendido. Ajusta la salida con el trimpot (LED verde).</li>
<li>Desconecta, espera 1 minuto, quita el foco y conecta directo. Prueba con carga: foco de 12 V 21 W a 12 V. Debe mantenerse.</li>
<li>Después de 10 minutos con carga: Q1, T1 y R12 tibios-calientes, se pueden tocar un momento (con la placa DESCONECTADA).</li>
</ol>
<h2>8 · Si algo falla</h2>
<table><tr><th>Síntoma</th><th>Revisa</th></tr>
<tr><td>Se funde F1 o el foco prende fuerte</td><td>BR1 o C12 al revés, Q1 en corto (mide D–S), T1 con primario en corto, D3/D5 al revés.</td></tr>
<tr><td>No arranca (0 V en C6)</td><td>R14–R16 o JP2 (debe llegar ≈ 12–16 V a la pata 7 del UC3844), C10, UC3844 al revés, CT/RT, pata 5 a tierra.</td></tr>
<tr><td>Hace «tic-tic-tic» y no sube</td><td>Devanado auxiliar al revés o sin conectar (B y A), D4, o salida en corto.</td></tr>
<tr><td>C6 sube a más de 30 V</td><td>Retroalimentación: U2, U3, R4/R5, R6, JP1. <b>Desconecta</b>.</td></tr>
<tr><td>Sale muy poco voltaje y Q1 se calienta</td><td>Secundario al revés (S0/S1 cambiados) o entrehierro muy chico.</td></tr>
<tr><td>Zumbido fuerte</td><td>Entrehierro flojo (pega bien las E), o T1 trabajando al límite.</td></tr>
</table>
<p style="color:#555;font-size:8.3pt;margin-top:3mm">Revisión por programa: 127 V ↔ lado seguro ≥ 5.8 mm más ranura, pistas de alto voltaje ≥ 1.3 mm, todas las conexiones verificadas,
cuerpos de piezas sin encimarse. Diseño calculado, <b>todavía no probado físicamente</b>: la primera prueba debe ser con foco en serie.</p>
</body></html>"""
open(os.path.join(here, "manual.html"), "w").write(html)
print("manual.html escrito")
