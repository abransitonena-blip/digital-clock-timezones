"""Dibuja cobre (planchar y vista), montaje (lado cobre) y serigrafía (lado de piezas) de placa.py."""
import os, sys, re
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import placa as P
errors, _ = P.drc()
if errors: print("\n".join(errors)); sys.exit(1)
W, H = P.W, P.H
VAL = {"U4": "UC3844", "Q1": "4N60", "T1": "EE25", "U2": "PC817", "U3": "TL431", "D2": "SR5100", "D3": "FR107", "D5": "P6KE200A",
       "C12": "100µF 250V", "BR1": "KBP307", "CX": "100nF X2", "RV1": "10D201K", "F1": "1A lento", "TH1": "NTC 5D-9", "J1": "127V~",
       "CY": "2.2nF Y1", "JP1": "puente", "JP2": "cable", "C6": "1000µF 35V", "C7": "1000µF 35V", "J2": "SALIDA", "TP1": "AJUSTE",
       "R4": "20k", "R5": "2.2k", "R6": "1k", "R7": "10k", "R8": "1k", "C8": "100nF", "C9": "1.2nF", "R9": "10k", "R10": "0Ω",
       "D4": "1N4148W", "C10": "47µF 50V", "R11": "22Ω", "R12": "0.47Ω 1W", "R13": "1k", "C11": "470pF", "R14": "39k", "R15": "39k", "R16": "39k",
       "U1": "LM2596S-ADJ", "L1": "47µH", "D1": "SS54", "C1": "220µF 50V", "C2": "1µF", "C3": "470µF 35V", "C4": "4.7µF", "R1": "3.3k",
       "R2": "10k", "R3": "1k", "LED1": "rojo", "LED2": "verde"}
THT = sorted({p[0] for p in P.pads if p[5] == "o" and not p[0].startswith("MH")})
SMD = sorted({p[0] for p in P.pads if p[5] == "r"})
def head(k=1.0): return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W*k:.1f}mm" height="{H*k:.1f}mm" viewBox="0 0 {W} {H}" font-family="Arial,Helvetica,sans-serif">'
def d_(pts): return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts)
def T(x, y, s, sz=1.2, a="middle", w="700", c="#111", rot=None):
    tf = f' transform="rotate({rot} {x:.2f} {y:.2f})"' if rot is not None else ""
    return f'<text x="{x:.2f}" y="{y:.2f}" font-size="{sz}" text-anchor="{a}" font-weight="{w}" fill="{c}"{tf}>{s}</text>'
def cobre(espejo=False):
    o = [head(), f'<rect width="{W}" height="{H}" fill="#fff" stroke="#000" stroke-width="0.25"/>',
         f'<g transform="translate({W} 0) scale(-1 1)">' if espejo else '<g>']
    for n, w, pts in P.traces: o.append(f'<path d="{d_(pts)}" fill="none" stroke="#000" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')
    for r, pn, x, y, n, f, w, h in P.pads:
        if r.startswith("MH"): o.append(f'<circle cx="{x}" cy="{y}" r="{w/2+0.3}" fill="none" stroke="#000" stroke-width="0.4"/><circle cx="{x}" cy="{y}" r="0.4"/>'); continue
        o.append(f'<rect x="{x-w/2:.2f}" y="{y-h/2:.2f}" width="{w}" height="{h}" rx="0.15"/>' if f == "r" else
                 f'<circle cx="{x}" cy="{y}" r="{w/2}"/><circle cx="{x}" cy="{y}" r="0.45" fill="#fff"/>')
    for x, y, h, t in P.CU_TEXT: o.append(T(x, y, t, h, c="#000"))
    o.append('</g></svg>'); return "\n".join(o)
def caja_pads(ref, m=0.5):
    ps = [p for p in P.pads if p[0] == ref]
    return (min(p[2]-p[6]/2 for p in ps)-m, min(p[3]-p[7]/2 for p in ps)-m, max(p[2]+p[6]/2 for p in ps)+m, max(p[3]+p[7]/2 for p in ps)+m)
def montaje(k=1.0):
    o = [head(k), f'<rect width="{W}" height="{H}" rx="1" fill="#fbf8f2" stroke="#555" stroke-width="0.3"/>']
    x0, y0, x1, y1 = P.SLOT
    o.append(f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="#fff" stroke="#c00" stroke-width="0.3" stroke-dasharray="0.8 0.5"/>')
    o.append(f'<path d="M96 {P.SLOT[1]} V{H} " stroke="#c00" stroke-width="0.25" stroke-dasharray="0.5 1.5"/>')
    for n, w, pts in P.traces:
        c = "#f3c9c0" if n in P.PRIM else "#ead0b3"
        o.append(f'<path d="{d_(pts)}" fill="none" stroke="{c}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')
    for r, pn, x, y, n, f, w, h in P.pads:
        if r.startswith("MH"): o.append(f'<circle cx="{x}" cy="{y}" r="1.6" fill="#fff" stroke="#999" stroke-width="0.3"/>'); continue
        o.append(f'<rect x="{x-w/2:.2f}" y="{y-h/2:.2f}" width="{w}" height="{h}" rx="0.15" fill="#d9a877"/>' if f == "r" else
                 f'<circle cx="{x}" cy="{y}" r="{w/2}" fill="#d9a877"/><circle cx="{x}" cy="{y}" r="0.5" fill="#fff"/>')
    for ref in SMD:
        a, b, c, d = caja_pads(ref, 0.25)
        o.append(f'<rect x="{a:.2f}" y="{b:.2f}" width="{c-a:.2f}" height="{d-b:.2f}" rx="0.3" fill="none" stroke="#111" stroke-width="0.22"/>')
        o.append(T((a+c)/2, b - 0.35, ref, 1.15))
    for ref, bb in P.CUERPOS.items():
        if bb[0] == "c": o.append(f'<circle cx="{bb[1]}" cy="{bb[2]}" r="{bb[3]-0.2}" fill="none" stroke="#2563eb" stroke-width="0.3" stroke-dasharray="1 0.7"/>')
        else: o.append(f'<rect x="{bb[1]}" y="{bb[2]}" width="{bb[3]-bb[1]}" height="{bb[4]-bb[2]}" rx="0.5" fill="none" stroke="#2563eb" stroke-width="0.3" stroke-dasharray="1 0.7"/>')
    for ref, bb in P.CUERPOS.items():
        cx, cy = (bb[1], bb[2]) if bb[0] == "c" else ((bb[1]+bb[3])/2, (bb[2]+bb[4])/2)
        if ref not in ("J2", "TP1"): o.append(T(cx, cy + 0.5, ref, 1.5, c="#2563eb"))
    o.append(T(96, 50.5, "RANURA", 1.0, c="#c00") + T(96, 52.0, "(cortar)", 0.8, c="#c00", w="400"))
    o.append(T(48, 47.5, "LADO SEGURO (12 V)", 1.6, c="#2f6b2f") + T(132, 81.8, "LADO DE 127 V · NO TOCAR CONECTADO", 1.6, c="#c00"))
    o.append('</svg>'); return "\n".join(o)
def serigrafia(planchar=False):
    """Lado SIN cobre: contornos de las piezas de patitas, la ranura y avisos."""
    o = [head(), f'<rect width="{W}" height="{H}" fill="#fff"/>',
         '<g>' if planchar else f'<g transform="translate({W} 0) scale(-1 1)">']
    L = 'fill="none" stroke="#000" stroke-width="0.3"'
    def txt(x, y, s, sz=1.1, w="700"): return f'<g transform="translate({x:.2f} {y:.2f}) scale(-1 1)"><text x="0" y="0" font-size="{sz}" text-anchor="middle" font-weight="{w}">{s}</text></g>'
    o.append(f'<rect x="0.7" y="0.7" width="{W-1.4}" height="{H-1.4}" rx="2" {L}/>')
    x0, y0, x1, y1 = P.SLOT
    o.append(f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="#000"/>')
    o.append(f'<path d="M96 {y1+1} V{H-1}" stroke="#000" stroke-width="0.3" stroke-dasharray="1 1"/>')
    for r, pn, x, y, n, f, w, h in P.pads:
        if f == "o": o.append(f'<circle cx="{x}" cy="{y}" r="{1.6 if r.startswith("MH") else 0.75}" {L}/>')
    for ref, bb in P.CUERPOS.items():
        if bb[0] == "c":
            o.append(f'<circle cx="{bb[1]}" cy="{bb[2]}" r="{bb[3]-0.2}" {L}/>'); cx, cy = bb[1], bb[2]
        else:
            o.append(f'<rect x="{bb[1]}" y="{bb[2]}" width="{bb[3]-bb[1]}" height="{bb[4]-bb[2]}" rx="0.5" {L}/>'); cx, cy = (bb[1]+bb[3])/2, (bb[2]+bb[4])/2
        if ref in ("J2", "TP1", "C6", "C7"): continue        # ya rotulados por la etapa 2
        o.append(txt(cx, cy + 0.4, ref, 1.0) + txt(cx, cy + 1.6, VAL.get(ref, ""), 0.7, "400"))
    for (ref, pin), lab in {("C12", "+"): "+", ("C6", "+"): "+", ("C7", "+"): "+", ("BR1", "+"): "+", ("BR1", "-"): "−",
                            ("D2", "K"): "|", ("D3", "K"): "|", ("D5", "K"): "|", ("J1", "L"): "L", ("J1", "N"): "N",
                            ("U2", "1"): "1", ("U4", "1"): "1", ("T1", "S1"): "S1", ("T1", "S0"): "S0", ("T1", "AUX"): "A",
                            ("T1", "PG"): "B", ("T1", "DR"): "D", ("T1", "HV"): "H", ("Q1", "G"): "G", ("Q1", "S"): "S", ("J2", "+"): "+", ("J2", "-"): "−"}.items():
        p = next(p for p in P.pads if p[0] == ref and p[1] == pin)
        o.append(txt(p[2] + (2.2 if ref != "T1" else (-2.6 if pin.startswith("S") else 2.6)), p[3] + 0.45, lab, 1.1))
    o.append(txt(60, 25.9, "C6 1000µF", 0.8, "400") + txt(60, 41.9, "C7 1000µF", 0.8, "400") + txt(17.5, 27.0, "SALIDA", 1.1) + txt(26, 15.4, "AJUSTE V", 1.0))
    o.append(txt(48, 74, "AP", 6) + txt(48, 78.5, "FUENTE UNIVERSAL 127 V → 1.2–20 V · 2 A", 1.3))
    o.append(txt(132, 72, "⚠ 127 V · NO TOCAR CONECTADA", 1.6) + txt(96, 2.2, "← 12 V │ 127 V →", 1.1))
    o.append('</g></svg>'); return "\n".join(o)
for name, s in (("cobre_planchar.svg", cobre(True)), ("cobre_vista.svg", cobre()), ("montaje.svg", montaje()),
                ("serigrafia_planchar.svg", serigrafia(True)), ("serigrafia_vista.svg", serigrafia(False))):
    open(os.path.join(here, name), "w").write(s)
print("SVG escritos")
