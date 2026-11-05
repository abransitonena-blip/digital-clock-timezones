"""Fichas de referencia de componentes, dibujadas a tamaño real (1 unidad SVG = 1 mm)."""
import os
COL = dict(negro="#111", marron="#7b4a22", rojo="#d0302a", naranja="#f08a1c", amarillo="#f5d000",
           verde="#2c9a3c", azul="#2b62c9", violeta="#8a4fc4", gris="#8a8a8a", blanco="#fafafa", dorado="#c9a23a")
F = 'font-family="Arial,Helvetica,sans-serif"'

def svg(w, h, body, scale=1.0):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w*scale}mm" height="{h*scale}mm" viewBox="0 0 {w} {h}" {F}>{body}</svg>'

def resistor(L, D, bands, body="#e8d2a6", lead=12):
    W = L + 2*lead; H = D + 2
    y = H/2
    b = f'<path d="M0 {y} H{W}" stroke="#999" stroke-width="0.6"/>'
    b += f'<rect x="{lead}" y="{y-D/2}" width="{L}" height="{D}" rx="{D/2.2}" fill="{body}" stroke="#333" stroke-width="0.2"/>'
    n = len(bands); step = L*0.62/(n-1)
    for i, c in enumerate(bands):
        x = lead + L*0.17 + i*step + (L*0.08 if i == n-1 else 0)
        b += f'<rect x="{x:.2f}" y="{y-D/2+0.15}" width="{L*0.07:.2f}" height="{D-0.3}" fill="{COL[c]}" stroke="#0003" stroke-width="0.1"/>'
    return svg(W, H, b)

def text(x, y, s, sz=1.6, c="#fff", a="middle", w="700"):
    return f'<text x="{x}" y="{y}" font-size="{sz}" fill="{c}" text-anchor="{a}" font-weight="{w}">{s}</text>'

def leads(xs, y0, y1, w=0.7):
    return "".join(f'<path d="M{x} {y0} V{y1}" stroke="#999" stroke-width="{w}"/>' for x in xs)

# --- dibujos ---
def x2(w=18, h=14.5, t="474K"):
    b = leads([(w-15)/2+1, (w+15)/2+1], h, h+8)
    b += f'<rect x="1" y="0.5" width="{w}" height="{h}" rx="1" fill="#f2d33a" stroke="#8a7410" stroke-width="0.3"/>'
    b += text(w/2+1, 3.6, "MKP  X2", 2.0, "#222") + text(w/2+1, 6.8, t, 2.4, "#222") + text(w/2+1, 9.8, "275VAC~", 1.9, "#222")
    b += text(w/2+1, 12.6, "ENEC ⓤ VDE", 1.3, "#444", w="400")
    return svg(w+2, h+9, b)
def ceramico():
    b = leads([4, 8], 9, 17) + '<ellipse cx="6" cy="5.2" rx="5.2" ry="4.6" fill="#e8873a" stroke="#8a4410" stroke-width="0.3"/>' + text(6, 6, "474", 2, "#222")
    return svg(12, 17, b)
def gota():
    b = leads([3.5, 8.5], 9, 17) + '<path d="M2 9 Q1 2 6 1 Q11 2 10 9 Z" fill="#2f7d3a" stroke="#174a1e" stroke-width="0.3"/>' + text(6, 5.2, "2A474J", 1.4)
    return svg(12, 17, b)
def cbb():
    b = leads([3, 13], 10, 18) + '<rect x="0.5" y="0.5" width="15" height="10" rx="3" fill="#d9b44a" stroke="#7a611a" stroke-width="0.3"/>' + text(8, 4.6, "CBB21", 1.6, "#222") + text(8, 7.8, "474J 400V", 1.7, "#222")
    return svg(16, 18, b)
def kbp():
    p = 3.81; x0 = 2.0
    b = leads([x0 + i*p for i in range(4)], 12, 20)
    b += '<path d="M0.5 2 L2 0.5 H15 V12 H0.5 Z" fill="#1d1d1d"/>'
    b += text(7.75, 4.8, "KBP307", 2.0) + "".join(text(x0 + i*p, 10.3, s, 2.2) for i, s in enumerate(["+", "~", "~", "−"]))
    return svg(15.5, 20, b)
def redondo():
    b = '<circle cx="5" cy="5" r="4.6" fill="#1d1d1d"/>' + text(5, 5.6, "W10M", 1.6) + leads([3, 4.3, 5.7, 7], 9.4, 16, 0.5)
    return svg(10, 16, b)
def db107():
    b = '<rect x="0.5" y="0.5" width="8.4" height="6.4" fill="#1d1d1d"/>' + text(4.7, 4.4, "DB107", 1.5) + leads([2.3, 7.1], 6.9, 12, 0.5)
    return svg(9.5, 12, b)
def electro(d=13, h=21, t1="47µF", t2="250V", sleeve="#1f2f5a"):
    b = leads([d/2-1.5, d/2+3.5], h, h+6)
    b += f'<rect x="0.5" y="0.5" width="{d}" height="{h}" rx="1.2" fill="{sleeve}"/>'
    b += f'<rect x="{d*0.7}" y="0.5" width="{d*0.22}" height="{h}" fill="#c9cfe0"/>'
    b += "".join(text(d*0.81+0.5, 3 + i*h/4, "−", 2.2, "#1f2f5a") for i in range(4))
    if d >= 10: b += text(d*0.35+0.5, h*0.4, t1, 2.0) + text(d*0.35+0.5, h*0.4+3, t2, 2.0) + text(d*0.35+0.5, h*0.4+6, "105°C", 1.4, w="400")
    else: b += text(d*0.35+0.5, h*0.45, t1, 1.2) + text(d*0.35+0.5, h*0.45+2, t2, 1.2)
    return svg(d+1, h+6, b)
def axial(L, D, label, band="#ddd", body="#1d1d1d", lead=8, sz=1.3):
    W = L + 2*lead; y = D/2 + 0.5
    b = f'<path d="M0 {y} H{W}" stroke="#999" stroke-width="0.6"/>'
    b += f'<rect x="{lead}" y="0.5" width="{L}" height="{D}" rx="0.5" fill="{body}"/>'
    b += f'<rect x="{lead+0.6}" y="0.5" width="{max(0.8, L*0.1)}" height="{D}" fill="{band}"/>'
    b += text(lead + L*0.58, y + sz*0.35, label, sz)
    return svg(W, D + 1, b)
def mov(t="10D241K", c="#2a63b8", r=6):
    b = leads([r-2.5, r+2.5], 2*r-1, 2*r+7) + f'<circle cx="{r}" cy="{r}" r="{r-0.4}" fill="{c}"/>' + text(r, r+0.7, t, 1.9 if len(t) > 4 else 2.4)
    return svg(2*r, 2*r+7, b)
def bornera(n):
    w = 5*n
    b = f'<rect x="0.3" y="0.3" width="{w}" height="10" rx="0.6" fill="#2b70c9" stroke="#174a8a" stroke-width="0.3"/>'
    for i in range(n):
        cx = 2.8 + 5*i
        b += f'<circle cx="{cx}" cy="4" r="1.9" fill="#d6d6d6" stroke="#666" stroke-width="0.2"/><path d="M{cx-1.4} 4 H{cx+1.4}" stroke="#555" stroke-width="0.5"/>'
        b += f'<rect x="{cx-1.6}" y="7" width="3.2" height="2.6" fill="#174a8a"/>'
    return svg(w+0.6, 10.6, b)
def led3():
    b = '<path d="M1 8 V3.5 A2 2 0 0 1 5 3.5 V8 Z" fill="#e33" opacity="0.9"/><rect x="0.6" y="7.6" width="4.8" height="1" fill="#e33"/>'
    b += '<path d="M5.4 7.6 V8.6" stroke="#fff" stroke-width="0.5"/>'
    b += leads([2.1], 8.6, 26, 0.5) + leads([3.9], 8.6, 23, 0.5)
    b += text(1.6, 28, "+ larga", 1.3, "#333", "middle", "400") + text(5, 25, "− corta", 1.3, "#333", "start", "400")
    return svg(11, 29, b)
def fusible(t="T500mA L250V"):
    b = '<rect x="0.5" y="0.5" width="4" height="5" fill="#bbb" stroke="#777" stroke-width="0.2"/><rect x="16" y="0.5" width="4" height="5" fill="#bbb" stroke="#777" stroke-width="0.2"/>'
    b += '<rect x="4.5" y="0.8" width="11.5" height="4.4" fill="#e6f0f5" stroke="#9ab" stroke-width="0.2"/><path d="M4.5 3 C7 1,8 5,10.2 3 S13.5 1,16 3" stroke="#555" stroke-width="0.35" fill="none"/>'
    return svg(20.5, 6, b) + f'<div class="mk">{t}</div>'
def switch():
    b = '<rect x="0.5" y="0.5" width="21" height="15" rx="1.5" fill="#222"/><rect x="3" y="2.5" width="16" height="11" rx="1" fill="#d3332b" opacity="0.92"/><text x="7" y="9.6" font-size="3" fill="#fff" font-weight="700">O</text><text x="13" y="9.6" font-size="3" fill="#fff" font-weight="700">I</text>'
    return svg(22, 16, b)

import re
def zoom(html, k):
    def f(m): return f'width="{float(m.group(1))*k:.1f}mm" height="{float(m.group(2))*k:.1f}mm"'
    return re.sub(r'width="([\d.]+)mm" height="([\d.]+)mm"', f, html)
CARD = []
def card(ref, titulo, img, debe, como, no, escala="Tamaño real 1:1"):
    k = 2.2 if "1:1" in escala else 1.4
    nos = "".join(f'<div class="no"><div class="noimg">{zoom(i, 1.8)}</div><div><b>✗ {t}</b><br>{d} <i>(ampliado)</i></div></div>' for i, t, d in no)
    img = f'<div class="pair"><div>{img}<div class="esc">{escala}</div></div><div>{zoom(img, k)}<div class="esc">Ampliado ×{k}</div></div></div>' if "1:1" in escala else f'{zoom(img, k)}<div class="esc">{escala}</div>'

    CARD.append(f'''<div class="card"><div class="hd"><span class="ref">{ref}</span><h2>{titulo}</h2></div>
<div class="body"><div class="img">{img}</div>
<div class="info"><p class="ok">✓ Debe decir: <b>{debe}</b></p><p>{como}</p></div></div>
{f'<div class="nos">{nos}</div>' if no else ''}</div>''')

def rpair(L, D, b4, b5, body5="#6fa8dc"):
    return (f'<div class="rr">{resistor(L, D, b4)}<span>4 bandas (carbón)</span></div>'
            f'<div class="rr">{resistor(L, D, b5, body5)}<span>5 bandas (película metálica)</span></div>')

card("C1–C5", "Capacitor X2 de 275 VAC", x2(), "X2 · 275VAC (o 275V~ o 310VAC) · el código, por ejemplo 474",
     "Caja rectangular de plástico, casi siempre amarilla, gris o azul, con logotipos de seguridad (VDE, ENEC, UL). El dibujo es el de 0.47 µF con patas a 15 mm; los de 22.5 mm son más largos y también sirven.",
     [(ceramico(), "Cerámico de disco", "Naranja o azul, redondo. Revienta con 127 V."),
      (gota(), "Poliéster de gota (2A474J)", "Verde. El 2A significa 100 V."),
      (cbb(), "CBB21 / MEF de 400 V", "Dice 400V, pero es de corriente directa: no es X2.")])
card("RD", "Resistencia 1 MΩ ½ W", rpair(9, 3.2, ["marron", "negro", "verde", "dorado"], ["marron", "negro", "negro", "amarillo", "marron"]),
     "marrón · negro · verde (4 bandas) o marrón · negro · negro · amarillo (5 bandas)",
     "½ W mide unos 9 mm de largo. Una de ¼ W (6 mm) es demasiado chica para 127 V.",
     [(resistor(6.3, 2.4, ["marron", "negro", "amarillo", "dorado"]), "100 kΩ (marrón negro amarillo)", "Se parece, pero es 10 veces menor.")])
card("RS", "Resistencia 150 Ω 1 W antiflama", rpair(11, 4.5, ["marron", "verde", "marron", "dorado"], ["marron", "verde", "negro", "negro", "marron"], "#9fb4c7"),
     "marrón · verde · marrón (4 bandas) o marrón · verde · negro · negro (5 bandas)",
     "1 W mide unos 11 mm de largo y 4.5 mm de grueso. La antiflama suele ser gris o azul claro, de película metálica. Pide \"antiflama\" o \"flameproof\".",
     [(resistor(6.3, 2.4, ["marron", "verde", "marron", "dorado"]), "La misma de ¼ W", "Mismo color, pero mucho más chica."),
      (resistor(11, 4.5, ["marron", "verde", "negro", "dorado"]), "15 Ω (marrón verde negro)", "Tercera banda negra: 10 veces menos.")])
card("RC", "Resistencia 220 kΩ ½ W", rpair(9, 3.2, ["rojo", "rojo", "amarillo", "dorado"], ["rojo", "rojo", "negro", "naranja", "marron"]),
     "rojo · rojo · amarillo (4 bandas) o rojo · rojo · negro · naranja (5 bandas)", "Mide unos 9 mm (½ W).", [])
card("RO", "Resistencia 100 Ω ½ W", rpair(9, 3.2, ["marron", "negro", "marron", "dorado"], ["marron", "negro", "negro", "negro", "marron"]),
     "marrón · negro · marrón (4 bandas) o marrón · negro · negro · negro (5 bandas)", "Mide unos 9 mm (½ W).", [])
card("BR", "Puente rectificador en línea KBP307", kbp(), "KBP307 (o KBP310, KBP206, 2KBP10) · + ~ ~ −",
     "Plano, negro, con 4 patas en fila a 3.8 mm. La esquina recortada marca la pata +. Las dos ~ quedan juntas en medio.",
     [(redondo(), "Redondo (W10M, 2W10)", "Es puente, pero no entra en la placa."),
      (db107(), "Cuadrado DB107", "Es para la placa de otra versión; no entra aquí.")])
card("CE", "Electrolítico 47 µF 250 V", electro(), "47µF · 250V (o 400V) · 105°C de preferencia",
     "Cilindro de unos 13 mm de diámetro y 20–25 mm de alto, con la franja de signos − en un costado. Las patas van a 5 mm.",
     [(electro(6.3, 11, "47µF", "50V", "#333"), "47 µF 50 V o 63 V", "Mismo valor, pero de bajo voltaje: revienta.")])
card("ZD", "Zener de 5 W (serie 1N53xxB)", axial(9.5, 5.3, "1N5355B", sz=1.5), "1N53 + dos números + B (ejemplo 1N5355B = 18 V)",
     "Negro, de unos 9.5 mm de largo y 5.3 mm de grueso, con franja en el cátodo. Revisa el número en la tabla según tus LED.",
     [(axial(9.5, 5.3, "1N5408", sz=1.5), "1N5408 (o 1N54xx)", "Mismo tamaño, pero es rectificador, NO zener."),
      (axial(5.2, 2.7, "4742A", sz=1.0), "1N47xx (1 W)", "Zener chico de 1 W: se calienta.")])
card("RV1", "Varistor 10D241K", mov(), "10D241K (o 241K 10D) · el 10D es el tamaño y el 241 es el voltaje",
     "Disco de unos 12 mm, casi siempre azul, con patas a 7.5 mm.",
     [(mov("104", "#2a63b8", 4), "Capacitor cerámico azul", "Parecido, pero solo trae un número (104)."),
      (mov("10D471K"), "10D471K", "Es para 220 V. Funciona, pero protege menos a 127 V.")])
card("J, TC", "Borneras KF301 de 2 y 3 polos", f'<div class="rr">{bornera(2)}<span>2 polos (J0–J5)</span></div><div class="rr">{bornera(3)}<span>3 polos (TC, cortar la pata central)</span></div>',
     "KF301 · paso 5.0 mm", "Azules o verdes, con tornillos arriba. Debe ser de paso 5 mm, no de 3.5 mm.", [], "Vista desde arriba, 1:1")
card("LT", "LED testigo rojo de 3 mm", led3(), "LED rojo de 3 mm (difuso o transparente)",
     "La pata larga es + (ánodo). El lado plano del borde es − (cátodo).", [])
card("F1", "Fusible 5 × 20 mm lento", fusible(), "T500mA o T0.5A · 250V (la T es lento)",
     "Tubo de vidrio de 20 mm con tapas metálicas. El lento suele tener el hilo en espiral o más grueso.",
     [(fusible("F500mA"), "F500mA (rápido)", "Se funde al encender por el pico de los capacitores.")])
card("SW", "Interruptor de balancín iluminado", switch(), "250V~ · 3 patas · con luz (tipo KCD3)",
     "Debe tener <b>3 patas</b>: la tercera es la de la lamparita. Si tiene 2, no ilumina. Los de 4 patas son dobles y también sirven.", [], "Escala aproximada")

css = """@page{size:letter;margin:11mm}body{font-family:Arial,Helvetica,sans-serif;color:#111;margin:0}
h1{font-size:17pt;margin:0 0 1mm}.intro{font-size:9.5pt;margin:0 0 4mm}
.grid{display:grid;grid-template-columns:1fr;gap:4mm}.pair{display:flex;gap:6mm;align-items:flex-end}.pair>div{display:flex;flex-direction:column;gap:1mm}
.card{border:0.35mm solid #9aa;border-radius:2mm;padding:2.5mm 3mm;break-inside:avoid;page-break-inside:avoid;display:flex;flex-direction:column;gap:2mm}
.hd{display:flex;align-items:baseline;gap:2mm}.hd h2{font-size:11.5pt;margin:0}.ref{font-family:Consolas,monospace;font-size:8.5pt;background:#e8efe9;padding:0.4mm 1.4mm;border-radius:1mm}
.body{display:flex;gap:6mm;align-items:flex-start}.info{max-width:85mm}.img{flex:0 0 auto;display:flex;flex-direction:column;gap:1.5mm;align-items:flex-start}
.info{font-size:8.6pt;line-height:1.35}.info p{margin:0 0 1.2mm}.ok{color:#1d6b3a}
.esc{font-size:7pt;color:#777}.rr{display:flex;flex-direction:column;gap:0.6mm}.rr span{font-size:7pt;color:#555}
.nos{display:flex;flex-wrap:wrap;gap:3mm 8mm;border-top:0.25mm dashed #ccc;padding-top:1.5mm}
.no{display:flex;gap:2.5mm;max-width:85mm;align-items:center;font-size:8pt;line-height:1.3}.no b{color:#b3261e}.noimg{flex:0 0 auto}
.mk{font-family:Consolas,monospace;font-size:7.5pt;color:#333}"""
html = f"""<!doctype html><meta charset="utf-8"><style>{css}</style>
<h1>Fichas para comprar los componentes</h1>
<p class="intro">Dibujos a <b>tamaño real</b>: pon la pieza encima de la hoja y compara. Imprime al 100 % ("tamaño real"). Revisa siempre lo que viene <b>impreso en el cuerpo</b>, que es lo que no engaña. Los colores de cada marca pueden variar un poco; las medidas y lo impreso no.</p>
<div class="grid">{''.join(CARD)}</div>"""
open("fichas.html", "w").write(html)
print(len(CARD), "fichas")
