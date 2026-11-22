"""Escribe manual.html (imprimir.cjs lo pasa a manual_fuente_12v_1.7a.pdf)."""
import os, re
here = os.path.dirname(os.path.abspath(__file__))
rd = lambda f: open(os.path.join(here, f)).read()
cu, silk, mont = rd("cobre_planchar.svg"), rd("serigrafia_planchar.svg"), rd("montaje.svg")
big = lambda s, k: re.sub(r'width="[0-9.]+mm" height="[0-9.]+mm"', f'width="{72*k:.1f}mm" height="{50*k:.1f}mm"', s, count=1)
S = 'fill="none" stroke="#000" stroke-width="0.45" stroke-linecap="round" stroke-linejoin="round"'
def cap_e(x, y1, y2):   # electrolítico vertical entre y1 (arriba, +) y y2
    m = (y1 + y2) / 2
    return (f'<path d="M{x} {y1} V{m-1.5} M{x} {m+1.5} V{y2}" {S}/><path d="M{x-4} {m-1.5} H{x+4}" {S} stroke-width="0.8"/>'
            f'<path d="M{x-4} {m+1.8} Q{x} {m+0.6} {x+4} {m+1.8}" {S} stroke-width="0.8"/><text x="{x-5.5}" y="{m-2}" font-size="2.6">+</text>')
def cap_c(x, y1, y2):
    m = (y1 + y2) / 2
    return f'<path d="M{x} {y1} V{m-1} M{x} {m+1} V{y2}" {S}/><path d="M{x-3.5} {m-1} H{x+3.5} M{x-3.5} {m+1} H{x+3.5}" {S} stroke-width="0.8"/>'
def res(x, y1, y2):
    m = (y1 + y2) / 2
    return f'<path d="M{x} {y1} V{m-4} M{x} {m+4} V{y2}" {S}/><rect x="{x-1.8}" y="{m-4}" width="3.6" height="8" {S}/>'
def led(x, y1, y2):
    m = (y1 + y2) / 2
    return (f'<path d="M{x} {y1} V{m-2.5} M{x} {m+2.5} V{y2}" {S}/><path d="M{x-3} {m-2.5} H{x+3} L{x} {m+2.5} Z M{x-3} {m+2.5} H{x+3}" {S}/>'
            f'<path d="M{x+3.5} {m-1} l2.2 -1.6 M{x+3.5} {m+1} l2.2 -1.6" {S} stroke-width="0.35"/>')
dot = lambda x, y: f'<circle cx="{x}" cy="{y}" r="0.8"/>'
term = lambda x, y: f'<circle cx="{x}" cy="{y}" r="1.4" fill="#fff" stroke="#000" stroke-width="0.45"/>'
B, G = 14, 64
esq = f"""<svg width="184mm" height="74mm" viewBox="0 0 184 74" font-family="Arial,Helvetica,sans-serif" font-size="2.7">
<path d="M5 31 H18 M5 43 H18" {S}/>{term(4,31)}{term(4,43)}<text x="1" y="27.5">J1</text><text x="0.5" y="49">18 V~</text>
{cap_c(11, 31, 43)}<text x="13" y="36">C5</text><text x="13" y="39">100n</text>
<rect x="18" y="26" width="14" height="22" rx="1" {S}/><text x="19.5" y="24.5">BR1 KBP307</text>
<text x="19" y="32">~</text><text x="19" y="44">~</text><text x="29" y="32">+</text><text x="29.2" y="44">−</text>
<path d="M25 33 L28.5 37 L25 41 L21.5 37 Z" {S} stroke-width="0.35"/>
<path d="M32 31 H36 V{B} H88 M32 43 H34 V{G} M4 {G} H180" {S}/>
{cap_e(44, B, G)}<text x="46" y="35">C6</text><text x="46" y="44" font-size="2.3">1000µF</text>
{cap_e(54, B, G)}<text x="56" y="35">C7</text><text x="56" y="44" font-size="2.3">1000µF</text>
{res(63, B, 39)}{led(63, 39, G)}<text x="65.5" y="27">R2 10k</text><text x="66" y="52">LED1</text>
{cap_e(74, B, G)}<text x="76" y="35">C1</text><text x="76" y="44" font-size="2.3">220µF</text>
{cap_c(82, B, G)}<text x="84" y="47">C2</text>
<rect x="88" y="8" width="30" height="34" rx="1" {S}/><text x="96" y="22" font-weight="700">U1</text><text x="93" y="26" font-size="2.5">LM2596S-12</text>
<text x="89.5" y="15">1 VIN</text><text x="106" y="15">2 OUT</text><text x="109.5" y="31">4 FB</text><text x="89.5" y="35">5 ON/OFF</text><text x="98" y="40.5">3 GND</text>
<path d="M88 34 H85 V{G} M103 42 V{G} M118 {B} H130 M118 30 H152 V{B}" {S}/>
<path d="M125 {B} V35 M125 43 V{G}" {S}/><path d="M121 43 H129 L125 35 Z M121 35 H129" {S}/><text x="127" y="47">D1 SS54</text>
<path d="M130 {B} q2.5 -5 5 0 q2.5 -5 5 0 q2.5 -5 5 0 q2.5 -5 5 0 M150 {B} H180" {S}/><text x="132" y="8">L1 47µH</text>
<text x="128" y="28.5" font-size="2.3">FB</text>
{cap_e(158, B, G)}<text x="160" y="35">C3</text><text x="160" y="44" font-size="2.3">470µF</text>
{cap_c(166, B, G)}<text x="168" y="47">C4</text>
{res(173, B, 39)}{led(173, 39, G)}
{term(181, B)}{term(181, G)}<text x="183" y="10" text-anchor="end">J2 12 V</text><text x="183" y="71" text-anchor="end">1.7 A −</text>
<text x="175" y="27" font-size="2.3">R1</text><text x="176.5" y="52" font-size="2.3">LED2</text>
{dot(36,B)}{dot(44,B)}{dot(54,B)}{dot(63,B)}{dot(74,B)}{dot(82,B)}{dot(125,B)}{dot(152,B)}{dot(158,B)}{dot(166,B)}{dot(173,B)}
{dot(34,G)}{dot(44,G)}{dot(54,G)}{dot(63,G)}{dot(74,G)}{dot(82,G)}{dot(85,G)}{dot(103,G)}{dot(125,G)}{dot(158,G)}{dot(166,G)}{dot(173,G)}
<text x="40" y="11" font-size="2.4">24–28 V DC</text><text x="152" y="11" font-size="2.4">12 V</text>
</svg>"""
caja = f"""<svg width="184mm" height="42mm" viewBox="0 0 184 42" font-family="Arial,Helvetica,sans-serif" font-size="2.8">
<g {S}>
<path d="M14 10 H34 M14 32 H96"/><rect x="2" y="6" width="12" height="30" rx="2"/>
<path d="M34 10 L42 6 M42 10 H50"/><circle cx="34" cy="10" r="0.9"/><circle cx="42" cy="10" r="0.9"/>
<rect x="50" y="7.5" width="14" height="5" rx="2.5"/><path d="M64 10 H96"/>
<path d="M76 10 V17 M76 25 V32"/><rect x="73" y="17" width="6" height="8"/><path d="M71 26 L81 16"/>
<path d="M96 10 q3 3 0 5.5 q3 3 0 5.5 q3 3 0 5.5 q3 3 0 5.5"/><path d="M103 8 V34 M105 8 V34" stroke-width="0.6"/>
<path d="M112 10 q-3 3 0 5.5 q-3 3 0 5.5 q-3 3 0 5.5 q-3 3 0 5.5"/>
<path d="M112 10 H150 M112 32 H150"/><rect x="150" y="4" width="32" height="34" rx="2"/>
</g>
<text x="3.5" y="4">Clavija</text><text x="5" y="22" font-size="3.4" font-weight="700">127 V</text><text x="15" y="8.5">L (fase)</text><text x="15" y="30.5">N (neutro)</text>
<text x="33" y="4">S1 interruptor</text><text x="48" y="17">F1 fusible 1 A lento</text>
<text x="82" y="22">RV1</text><text x="82" y="25.5" font-size="2.4">10D201K</text>
<text x="92" y="40">T1 primario 127 V</text><text x="110" y="4">secundario 18 V</text><text x="113" y="21" font-size="2.4">2–3 A</text>
<text x="154" y="18" font-weight="700">Placa AP</text><text x="154" y="22">entra a J1 (18V~)</text><text x="154" y="26">sin polaridad</text>
</svg>"""
BOM = [
 ("U1", "1", "<b>LM2596S-12</b> (fija de 12 V), TO-263-5", "La ADJ no sirve en esta placa"),
 ("BR1", "1", "Puente rectificador <b>KBP307</b> (3 A, 700 V), en línea", "El que ya usas en las otras placas"),
 ("C6, C7", "2", "Electrolítico <b>1000 µF 50 V</b> de patitas, 12.5 mm, paso 5 mm, 105 °C", "Filtro principal"),
 ("C1", "1", "Electrolítico SMD <b>220 µF 50 V</b>, 10 × 10.5 mm, bajo ESR", "Junto al LM2596"),
 ("C3", "1", "Electrolítico SMD <b>470 µF 25 V</b>, 10 × 10.5 mm, bajo ESR", "Salida"),
 ("C2", "1", "Cerámico <b>1 µF 50 V</b> X7R, 1206", ""),
 ("C4", "1", "Cerámico <b>10 µF 25 V</b> X5R/X7R, 1206", "Baja el rizo de salida"),
 ("C5", "1", "Cerámico <b>100 nF 50 V</b>, 1206", "Quita ruido en la entrada de alterna"),
 ("D1", "1", "Diodo Schottky <b>SS54</b> (5 A, 40 V), SMC", "No sirve un diodo normal"),
 ("L1", "1", "Bobina SMD <b>47 µH, ≥ 3 A</b>, 12 × 12 mm (CD127 «470»)", "33 a 68 µH también"),
 ("R1", "1", "<b>2.2 kΩ</b> 0805", "LED de salida"),
 ("R2", "1", "<b>10 kΩ</b> 1206", "LED de entrada y descarga de C6/C7"),
 ("LED1", "1", "LED SMD 0805 <b>rojo</b>", "Hay voltaje en el filtro"),
 ("LED2", "1", "LED SMD 0805 <b>verde</b>", "Hay 12 V en la salida"),
 ("J1, J2", "2", "Bornera de 2 tornillos, paso 5.08 mm", ""),
 ("—", "1", "Placa fenólica de una cara 7.2 × 5 cm", ""),
]
CAJA = [
 ("T1", "1", "Transformador <b>127 V → 18 V</b>, <b>2 A mínimo (3 A recomendado)</b>", "Uno de 12 V no alcanza"),
 ("F1", "1", "Portafusible de chasis + fusible 5 × 20 mm <b>1 A lento</b>", "Siempre antes de todo"),
 ("S1", "1", "Interruptor de 127 V (con luz, opcional)", ""),
 ("RV1", "1", "Varistor <b>10D201K</b> (o 14D201K)", "Contra picos de la red"),
 ("—", "1", "Cable con clavija, termofit, caja, 4 separadores M3 de 15 mm", "Las piezas SMD quedan abajo"),
]
fila = lambda r: f"<tr><td class=r>{r[0]}</td><td class=c>{r[1]}</td><td>{r[2]}</td><td class=g>{r[3]}</td></tr>"
PASOS = [
 ("Estaña los pads", "Capa delgada de soldadura con flux en todos los pads SMD."),
 ("U1 · LM2596S-12", "Primero. Pata 1 a la derecha (junto a C2), pestaña sobre el pad grande. Fija una pata, alinea, suelda las 5 y al final la pestaña con cautín de 60 W o más (o pistola de calor)."),
 ("D1 · SS54", "Franja hacia arriba, hacia la pista larga del borde."),
 ("Piezas chicas", "C2, C4, C5, R1 y R2 no tienen polaridad. En LED1 y LED2 el cátodo (marca verde o la «T» del reverso) va hacia abajo, hacia la pista ancha de tierra."),
 ("L1 · 47 µH", "Sin polaridad; calienta bien los dos pads."),
 ("C1 y C3", "Esquinas cortadas de la base = + (hacia arriba en los dos). Franja negra = −."),
 ("Del otro lado: BR1, C6, C7, J1, J2", "Entran por el lado sin cobre, siguiendo la serigrafía, y se sueldan del lado del cobre. BR1: la esquina cortada (+) hacia la orilla de arriba. C6 y C7: pata larga (+) donde dice +, franja hacia abajo."),
 ("Limpieza", "Quita el flux con alcohol isopropílico y revisa con lupa que no haya puentes entre las patas del LM2596."),
]
pasos = "".join(f"<li><b>{a}.</b> {b}</li>" for a, b in PASOS)
bar = '<svg width="72mm" height="5mm" viewBox="0 0 72 5"><rect x="0" y="2" width="72" height="1"/><rect x="0" y="0" width="0.6" height="5"/><rect x="71.4" y="0" width="0.6" height="5"/></svg>'
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page {{ size: letter; margin: 11mm 12mm; }}
body {{ font-family: Arial, Helvetica, sans-serif; font-size: 9.6pt; color: #111; margin: 0; }}
h1 {{ font-size: 19pt; margin: 0; }} h2 {{ font-size: 12pt; margin: 4.5mm 0 1.8mm; border-bottom: 1.5px solid #111; padding-bottom: 0.6mm; }}
.sub {{ color: #444; margin: 0.8mm 0 3mm; }}
.specs {{ display: flex; gap: 3mm; margin-bottom: 2mm; }} .spec {{ flex: 1; border: 1.5px solid #111; border-radius: 2.5mm; padding: 1.8mm 2.5mm; }}
.spec b {{ display: block; font-size: 13pt; }} .spec span {{ color: #555; font-size: 8.5pt; }}
.hoja {{ display: flex; gap: 6mm; justify-content: center; margin: 1.5mm 0; }}
.nota {{ border-left: 3px solid #e8590c; background: #fff4ec; padding: 1.5mm 3mm; margin: 2mm 0; }}
.peligro {{ border: 2px solid #c00; background: #fff0f0; border-radius: 2.5mm; padding: 2mm 3mm; margin: 2mm 0; }}
table {{ border-collapse: collapse; width: 100%; font-size: 9pt; }} th, td {{ border: 1px solid #999; padding: 1.1mm 1.8mm; vertical-align: top; text-align: left; }}
th {{ background: #eee; }} td.r {{ font-weight: 700; white-space: nowrap; }} td.c {{ text-align: center; }} td.g {{ color: #444; }}
ol, ul {{ margin: 1mm 0; padding-left: 5.5mm; }} li {{ margin: 0.9mm 0; }}
.pb {{ page-break-before: always; }} .fig {{ text-align: center; }} .cap {{ font-size: 8pt; color: #555; text-align: center; }}
</style></head><body>
<h1>Fuente 12 V · 1.7 A desde 127 V</h1>
<div class="sub">Transformador + puente + filtro + regulador conmutado LM2596S-12 (SMD). Placa de una cara de 7.2 × 5 cm para planchar. Diseño AP.</div>
<div class="specs">
<div class="spec"><b>127 V~</b><span>entrada, con transformador 18 V</span></div>
<div class="spec"><b>12 V</b><span>salida fija ± 4 %</span></div>
<div class="spec"><b>1.7 A</b><span>continuos (máx. 2 A)</span></div>
<div class="spec"><b>Aislada</b><span>los 127 V no tocan la placa</span></div></div>
<h2>Cómo se conecta todo</h2>
<div class="fig">{caja}</div>
<div class="peligro"><b>127 V solo en la caja, nunca en la placa.</b> Fusible F1 primero que todo. Cubre con termofit cada unión del primario
(clavija, interruptor, fusible, varistor, transformador). Si la caja es metálica, conecta la tierra física de la clavija al metal.
No toques el primario con la clavija conectada.</div>
<p style="margin:1.5mm 0">El transformador baja a 18 V y aísla; BR1 y C6/C7 lo convierten en 24–28 V de corriente directa; el LM2596 lo baja a 12 V
con ≈ 88 % de eficiencia (se calienta poco). LED rojo: hay voltaje en el filtro. LED verde: hay 12 V.
El LM2596 trae límite de corriente y apagado por temperatura, así que un corto en la salida no lo destruye.</p>
<h2>Por qué 18 V y no 12 V</h2>
<p style="margin:1mm 0">A 1.7 A, el filtro baja en cada valle unos 4.5 V. Con 18 V~ el valle queda en ≈ 18 V y el regulador tiene de sobra;
con 12 V~ caería a ≈ 11 V y la salida se vendría abajo. Sin carga y con la red alta, el filtro sube a ≈ 30 V: dentro del límite de 40 V del LM2596.</p>
<h2 class="pb">1 · Hojas para planchar (1:1)</h2>
<div class="hoja">{cu}{cu}</div>
<div class="cap">Cobre — ya va en espejo; las piezas SMD se sueldan de este lado</div>
<div class="hoja">{silk}{silk}</div>
<div class="cap">Serigrafía para el lado sin cobre (opcional) — también en espejo</div>
<div class="fig" style="margin-top:2mm">{bar} <span style="font-size:8pt">esta barra debe medir 72 mm</span></div>
<div class="nota">Láser al <b>100 %</b>, sin «ajustar a página». Plancha el cobre, grabas, barrenas, y luego plancha la serigrafía del otro lado alineando con los barrenos.</div>
<ol>
<li>Lija y limpia con alcohol. Plancha 3–4 min, remoja y retira el papel. Cloruro férrico; quita el tóner con thinner.</li>
<li>Barrenos: <b>1.0 mm</b> para C6 y C7, <b>1.2 mm</b> para BR1 y borneras, <b>3.2 mm</b> en las 4 esquinas.</li>
<li>Revisa a contraluz que no haya puentes de cobre entre las patas del LM2596 (0.6 mm entre ellas).</li>
</ol>
<h2 class="pb">2 · Esquema de la placa</h2>
<div class="fig">{esq}</div>
<h2>3 · Material de la placa</h2>
<table><tr><th>Ref.</th><th>Cant.</th><th>Pieza</th><th>Nota</th></tr>{"".join(fila(r) for r in BOM)}</table>
<h2>4 · Material de la caja (127 V)</h2>
<table><tr><th>Ref.</th><th>Cant.</th><th>Pieza</th><th>Nota</th></tr>{"".join(fila(r) for r in CAJA)}</table>
<h2 class="pb">5 · Montaje (visto desde el lado del cobre)</h2>
<div class="fig">{big(mont, 2.45)}</div>
<div class="cap">Café = cobre. Negro = piezas SMD de este lado. Azul punteado = piezas de patitas que van del otro lado.</div>
<ol>{pasos}</ol>
<h2 class="pb">6 · Pruebas (en este orden)</h2>
<ol>
<li><b>Sin corriente:</b> continuidad entre + y − de J2 y entre + de C6 y tierra: no deben quedarse pitando (un pitido corto es el capacitor cargando).</li>
<li><b>Solo el transformador:</b> con la caja armada y la placa desconectada, mide el secundario: 18–21 V de alterna.</li>
<li><b>Primera conexión, sin carga:</b> conecta el secundario a J1 y enciende. Prende LED1 (rojo) y LED2 (verde).
En C6 debe haber 24–30 V de directa; en J2, <b>11.5–12.5 V</b>.</li>
<li><b>Con carga:</b> foco de auto 12 V 21 W (≈ 1.75 A) o tu tira LED. La salida se queda arriba de 11.5 V.</li>
<li><b>10 minutos con carga:</b> LM2596 y bobina tibios-calientes (hasta ≈ 70 °C) pero se pueden tocar un momento; transformador y puente tibios.</li>
<li><b>Al apagar:</b> LED1 se apaga en unos segundos; R2 descarga C6 y C7.</li>
</ol>
<h2>7 · Si algo falla</h2>
<table><tr><th>Síntoma</th><th>Revisa</th></tr>
<tr><td>Se funde F1 al encender</td><td>BR1 al revés o en corto, C6/C7 al revés, corto entre + y tierra del filtro. <b>No pongas un fusible más grande.</b></td></tr>
<tr><td>No prende ningún LED</td><td>F1, interruptor, transformador (mide el secundario), bornera J1, soldaduras de BR1.</td></tr>
<tr><td>Rojo sí, verde no</td><td>Patas 1 o 5 del LM2596 sin soldar (la 5 va a tierra), D1 al revés, LED2 al revés.</td></tr>
<tr><td>Salen más de 13 V (18–28 V)</td><td>Pata 1 y 2 en corto o pusiste la versión ADJ. <b>Desconecta enseguida.</b></td></tr>
<tr><td>La salida baja con carga</td><td>Transformador de 12 V o de poca corriente (mide en C6: no debe bajar de 16 V), pata 4 sin soldar, bobina de menos de 3 A.</td></tr>
<tr><td>El transformador zumba y se calienta mucho</td><td>Es muy chico para la carga: usa uno de 18 V 3 A.</td></tr>
</table>
<p style="color:#555;font-size:8.5pt;margin-top:3mm">Diseño revisado por programa: separación mínima entre pistas de 0.55 mm, todas las conexiones verificadas y cuerpos de las piezas de patitas sin encimarse. Esta placa aún no se ha armado físicamente.</p>
</body></html>"""
open(os.path.join(here, "manual.html"), "w").write(html)
print("manual.html escrito")
