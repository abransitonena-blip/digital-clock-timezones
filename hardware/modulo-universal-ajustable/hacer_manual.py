"""Escribe manual.html (imprimir.cjs lo pasa a manual_modulo_universal.pdf)."""
import os, re
here = os.path.dirname(os.path.abspath(__file__))
rd = lambda f: open(os.path.join(here, f)).read()
cu, silk, mont = rd("cobre_planchar.svg"), rd("serigrafia_planchar.svg"), rd("montaje.svg")
big = lambda s, k: re.sub(r'width="[0-9.]+mm" height="[0-9.]+mm"', f'width="{80*k:.1f}mm" height="{50*k:.1f}mm"', s, count=1)
S = 'fill="none" stroke="#000" stroke-width="0.45" stroke-linecap="round" stroke-linejoin="round"'
def cap_e(x, y1, y2):
    m = (y1 + y2) / 2
    return (f'<path d="M{x} {y1} V{m-1.5} M{x} {m+1.5} V{y2}" {S}/><path d="M{x-3.5} {m-1.5} H{x+3.5}" {S} stroke-width="0.8"/>'
            f'<path d="M{x-3.5} {m+1.8} Q{x} {m+0.6} {x+3.5} {m+1.8}" {S} stroke-width="0.8"/><text x="{x-5}" y="{m-2}" font-size="2.6">+</text>')
def cap_c(x, y1, y2):
    m = (y1 + y2) / 2
    return f'<path d="M{x} {y1} V{m-1} M{x} {m+1} V{y2}" {S}/><path d="M{x-3} {m-1} H{x+3} M{x-3} {m+1} H{x+3}" {S} stroke-width="0.8"/>'
def res(x, y1, y2, var=False):
    m = (y1 + y2) / 2
    a = f'<path d="M{x-4} {m+4} L{x+4} {m-4} l-1.6 0.3 M{x+4} {m-4} l-0.3 1.6" {S} stroke-width="0.4"/>' if var else ""
    return f'<path d="M{x} {y1} V{m-4} M{x} {m+4} V{y2}" {S}/><rect x="{x-1.8}" y="{m-4}" width="3.6" height="8" {S}/>' + a
def led(x, y1, y2):
    m = (y1 + y2) / 2
    return (f'<path d="M{x} {y1} V{m-2.5} M{x} {m+2.5} V{y2}" {S}/><path d="M{x-3} {m-2.5} H{x+3} L{x} {m+2.5} Z M{x-3} {m+2.5} H{x+3}" {S}/>'
            f'<path d="M{x+3.5} {m-1} l2.2 -1.6 M{x+3.5} {m+1} l2.2 -1.6" {S} stroke-width="0.35"/>')
dot = lambda x, y: f'<circle cx="{x}" cy="{y}" r="0.8"/>'
term = lambda x, y: f'<circle cx="{x}" cy="{y}" r="1.4" fill="#fff" stroke="#000" stroke-width="0.45"/>'
B, G = 14, 64
esq = f"""<svg width="184mm" height="74mm" viewBox="0 0 184 74" font-family="Arial,Helvetica,sans-serif" font-size="2.7">
<path d="M5 31 H18 M5 43 H18" {S}/>{term(4,31)}{term(4,43)}<text x="0.5" y="27.5">J1</text><text x="0.5" y="49.5">ENTRADA</text>
{cap_c(11, 31, 43)}<text x="13" y="36.5">C5</text>
<rect x="18" y="26" width="14" height="22" rx="1" {S}/><text x="19.5" y="24.5">BR1 KBP307</text>
<text x="19" y="32">~</text><text x="19" y="44">~</text><text x="29" y="32">+</text><text x="29.2" y="44">−</text>
<path d="M25 33 L28.5 37 L25 41 L21.5 37 Z" {S} stroke-width="0.35"/>
<path d="M32 31 H36 V{B} H88 M32 43 H34 V{G} M4 {G} H180" {S}/>
{cap_e(44, B, G)}<text x="46" y="35">C6</text><text x="46" y="44" font-size="2.3">1000µF</text>
{cap_e(54, B, G)}<text x="56" y="35">C7</text><text x="56" y="44" font-size="2.3">1000µF</text>
{res(63, B, 39)}{led(63, 39, G)}<text x="65.5" y="27">R2 10k</text><text x="66" y="52">LED1</text>
{cap_e(74, B, G)}<text x="76" y="35">C1</text>{cap_c(82, B, G)}<text x="84" y="47">C2</text>
<rect x="88" y="8" width="30" height="34" rx="1" {S}/><text x="96" y="22" font-weight="700">U1</text><text x="91" y="26" font-size="2.5">LM2596S-ADJ</text>
<text x="89.5" y="15">1 VIN</text><text x="106" y="15">2 OUT</text><text x="109.5" y="31">4 FB</text><text x="89.5" y="35">5 ON/OFF</text><text x="98" y="40.5">3 GND</text>
<path d="M88 34 H85 V{G} M103 42 V{G} M118 {B} H130 M118 30 H148" {S}/>
<path d="M125 {B} V35 M125 43 V{G}" {S}/><path d="M121 43 H129 L125 35 Z M121 35 H129" {S}/><text x="127" y="47">D1</text>
<path d="M130 {B} q2.5 -5 5 0 q2.5 -5 5 0 q2.5 -5 5 0 q2.5 -5 5 0 M150 {B} H180" {S}/><text x="132" y="8">L1 47µH</text>
{res(148, B, 30, True)}{res(148, 30, G)}<text x="137" y="23" font-size="2.4">TP1 20k</text><text x="150" y="50" font-size="2.4">R3 1k</text><text x="135" y="28.6" font-size="2.3">FB</text>
{cap_e(158, B, G)}<text x="160" y="35">C3</text>{cap_c(166, B, G)}<text x="168" y="47">C4</text>
{res(173, B, 39)}{led(173, 39, G)}
{term(181, B)}{term(181, G)}<text x="183" y="10" text-anchor="end">J2 SALIDA +</text><text x="183" y="71" text-anchor="end">−</text>
<text x="175" y="27" font-size="2.3">R1</text><text x="176.5" y="52" font-size="2.3">LED2</text>
{dot(36,B)}{dot(44,B)}{dot(54,B)}{dot(63,B)}{dot(74,B)}{dot(82,B)}{dot(125,B)}{dot(148,B)}{dot(158,B)}{dot(166,B)}{dot(173,B)}{dot(148,30)}
{dot(34,G)}{dot(44,G)}{dot(54,G)}{dot(63,G)}{dot(74,G)}{dot(82,G)}{dot(85,G)}{dot(103,G)}{dot(125,G)}{dot(148,G)}{dot(158,G)}{dot(166,G)}{dot(173,G)}
<text x="40" y="11" font-size="2.4">VIN filtrado</text><text x="112" y="71" font-size="2.6" font-weight="700">Vout = 1.23 × (1 + TP1 / 1 kΩ)</text>
</svg>"""
def fila(r): return "<tr>" + "".join(f"<td{' class=r' if i == 0 else ''}>{c}</td>" for i, c in enumerate(r)) + "</tr>"
BOM = [
 ("U1", "1", "<b>LM2596S-ADJ</b> (ajustable), TO-263-5", "Esta vez SÍ la ADJ"),
 ("TP1", "1", "Trimpot multivuelta <b>3296W 20 kΩ</b> («203»)", "Patas en línea a 2.54 mm"),
 ("R3", "1", "<b>1 kΩ 1 %</b> 0805", "Divisor del voltaje"),
 ("BR1", "1", "Puente <b>KBP307</b> (3 A, 700 V)", "Entrada sin polaridad"),
 ("C6, C7", "2", "Electrolítico <b>1000 µF 50 V</b> de patitas, 12.5 mm, paso 5 mm, 105 °C", ""),
 ("C1", "1", "Electrolítico SMD <b>220 µF 50 V</b>, 10 × 10.5 mm", ""),
 ("C3", "1", "Electrolítico SMD <b>470 µF 35 V</b>, 10 × 10.5 mm, bajo ESR", "35 V porque la salida llega a 24 V"),
 ("C2", "1", "Cerámico <b>1 µF 50 V</b> X7R, 1206", ""),
 ("C4", "1", "Cerámico <b>4.7 µF 50 V</b> X7R, 1206", ""),
 ("C5", "1", "Cerámico <b>100 nF 50 V</b>, 1206", ""),
 ("D1", "1", "Schottky <b>SS54</b>, SMC", ""),
 ("L1", "1", "Bobina SMD <b>47 µH ≥ 3 A</b>, 12 × 12 mm", ""),
 ("R1", "1", "<b>3.3 kΩ</b> 1206", "LED de salida (sirve de 3 a 24 V)"),
 ("R2", "1", "<b>10 kΩ</b> 1206", "LED de entrada + descarga"),
 ("LED1, LED2", "2", "LED SMD 0805 rojo y verde", ""),
 ("J1, J2", "2", "Bornera 2 tornillos, paso 5.08 mm", ""),
]
VOL = [("3.3 V", "1.7 kΩ", "Arduino 3.3 V, ESP32, sensores"), ("5 V", "3.1 kΩ", "Arduino, USB, servos chicos"),
       ("9 V", "6.3 kΩ", "Pedales, radios, módulos de 9 V"), ("12 V", "8.8 kΩ", "Tiras LED de 12 V, ventiladores, relevadores"),
       ("11.2 V", "8.1 kΩ", "Tira LED de 12 V «suave»: menos calor"), ("19 V", "14.4 kΩ", "Laptop chica (sin pasar de 2 A)")]
volt = "".join(fila(r) for r in VOL)
ENT = [("Eliminador o cargador de laptop <b>19 V</b> (≥ 2.5 A)", "hasta 16 V", "El más fácil y seguro: es una fuente tipo cargador ya aislada"),
       ("Eliminador <b>24 V</b> (≥ 2 A)", "hasta 21 V", "Ideal para todo, incluso 12 V a 2 A"),
       ("Transformador <b>18 V~</b> 3 A (con fusible en el primario)", "hasta 14 V a 2 A", "El de la fuente anterior"),
       ("Eliminador <b>12 V</b>", "hasta 9 V", "No sirve para sacar 12 V"),]
ent = "".join(fila(r) for r in ENT)
TIRA = [("1 tramo de 3 LED 2835 / 3528", "≈ 20 mA", "7 tramos ≈ <b>0.14 A</b> (1.7 W)"),
        ("1 tramo de 3 LED 5050", "≈ 60 mA", "7 tramos ≈ <b>0.42 A</b> (5 W)"),
        ("1 metro 2835, 60 LED/m (20 tramos)", "≈ 0.4 A", "7 m ≈ <b>2.8 A</b> (34 W) ✗ excede 2 A"),
        ("1 metro 5050, 60 LED/m (20 tramos)", "≈ 1.2 A", "7 m ≈ <b>8.4 A</b> ✗ necesita otra fuente")]
tira = "".join(fila(r) for r in TIRA)
PASOS = [
 ("Estaña los pads", "Capa delgada de soldadura con flux en todos los pads SMD."),
 ("U1 · LM2596S-ADJ", "Primero. Pata 1 a la derecha (junto a C2), pestaña sobre el pad grande. Fija una pata, alinea, suelda las 5 y al final la pestaña con cautín de 60 W o pistola de calor."),
 ("D1 · SS54", "Franja hacia arriba, hacia la pista larga del borde."),
 ("Piezas chicas", "R3 (1 kΩ) junto al LM2596, C2, C4, C5, R1, R2. En los LED el cátodo (marca verde o «T» del reverso) va hacia abajo, hacia la tierra."),
 ("L1, C1 y C3", "L1 sin polaridad. En C1 y C3 las esquinas cortadas de la base son el + (hacia arriba)."),
 ("Del otro lado: TP1, BR1, C6, C7, J1, J2", "Entran por el lado sin cobre según la serigrafía y se sueldan del lado del cobre. TP1: el tornillito queda arriba, para girarlo con desarmador. Si tu trimpot trae las patas en triángulo, endereza la de en medio para que entre en línea."),
 ("Limpieza", "Alcohol isopropílico y revisa con lupa entre las patas del LM2596."),
]
pasos = "".join(f"<li><b>{a}.</b> {b}</li>" for a, b in PASOS)
bar = '<svg width="80mm" height="5mm" viewBox="0 0 80 5"><rect x="0" y="2" width="80" height="1"/><rect x="0" y="0" width="0.6" height="5"/><rect x="79.4" y="0" width="0.6" height="5"/></svg>'
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
th {{ background: #eee; }} td.r {{ font-weight: 700; white-space: nowrap; }}
ol, ul {{ margin: 1mm 0; padding-left: 5.5mm; }} li {{ margin: 0.9mm 0; }}
.pb {{ page-break-before: always; }} .fig {{ text-align: center; }} .cap {{ font-size: 8pt; color: #555; text-align: center; }}
</style></head><body>
<h1>Módulo universal ajustable · 1.2 – 24 V · 2 A</h1>
<div class="sub">Un solo módulo para tus prototipos: giras el trimpot y eliges el voltaje. LM2596S-ADJ (SMD), placa de una cara 8 × 5 cm para planchar. Diseño AP.</div>
<div class="specs">
<div class="spec"><b>8 – 35 V</b><span>entrada DC sin polaridad, o 6–22 V~</span></div>
<div class="spec"><b>1.2 – 24 V</b><span>salida ajustable con trimpot</span></div>
<div class="spec"><b>2 A</b><span>continuos (pico 3 A, con límite propio)</span></div>
<div class="spec"><b>≈ 85–90 %</b><span>eficiencia: casi no calienta</span></div></div>
<h2>Qué le conectas en la entrada</h2>
<table><tr><th>Fuente de entrada</th><th>Voltaje máximo de salida</th><th>Nota</th></tr>{ent}</table>
<div class="nota">Regla: la entrada debe ser al menos <b>3 V más alta</b> que la salida que quieres. Para 127 V lo más práctico y seguro es un
<b>cargador de laptop de 19 V</b> o un eliminador de 24 V: ya es la «fuente tipo cargador» en una sola caja, aislada y probada, y este módulo
hace el resto. Si usas transformador, el fusible y el varistor van en su primario, nunca en esta placa.</div>
<h2>Qué voltaje elegir · resistencia del trimpot</h2>
<table><tr><th>Salida</th><th>TP1 (entre sus patas 1 y 2)</th><th>Para qué</th></tr>{volt}</table>
<p style="margin:1.5mm 0">No necesitas medir el trimpot: <b>ajusta mirando el multímetro en la salida</b>. La tabla es solo de referencia
(Vout = 1.23 × (1 + TP1 / 1 kΩ)). Girar a la derecha sube el voltaje en el 3296 normal; si en el tuyo baja, es al revés, no pasa nada.</p>
<div class="peligro"><b>Ajusta SIEMPRE sin nada conectado.</b> Enciende sin carga, mide, gira hasta el voltaje que quieres y hasta entonces conecta la tira o el circuito.
Si conectas una tira de 12 V con el trimpot en 20 V, se quema en segundos.</div>
<h2 class="pb">Tiras LED de 12 V: cuánto consumen y por qué se calientan</h2>
<p style="margin:1mm 0">Una tira de 12 V está hecha de <b>tramos</b> (entre cada marca de corte): 3 LED + 1 resistencia. Todos los tramos van en paralelo,
así que la corriente total es <b>número de tramos × corriente de un tramo</b>.</p>
<table><tr><th>Tipo de tramo</th><th>Corriente por tramo</th><th>Tus «7 filas»</th></tr>{tira}</table>
<p style="margin:1.5mm 0">Si tus 7 filas son 7 tramos cortos, gastan entre 0.14 y 0.42 A y el módulo va sobradísimo. Si son 7 tiras de 1 m, ya pasan de 2 A
y hay que dividirlas en dos fuentes. Para saberlo exacto: cuenta las marcas de corte, o mide con el multímetro en amperes una sola fila.</p>
<h2>Para que la tira no se caliente</h2>
<ul>
<li><b>Baja el voltaje un poco:</b> a 11–11.5 V en lugar de 12 V la tira consume ≈ 20–30 % menos y se calienta mucho menos; la luz baja apenas. Con este módulo es solo girar el trimpot.</li>
<li><b>Ponla sobre aluminio</b> (perfil o lámina): el adhesivo solo, sobre madera o plástico, no saca el calor.</li>
<li><b>Alimenta por los dos extremos</b> si es larga, para que no se caliente el principio.</li>
<li>Que la fuente dé al menos <b>20 % más corriente</b> que la tira.</li>
</ul>
<h2>¿Y una resistencia de 1 MΩ en serie?</h2>
<p style="margin:1mm 0"><b>No:</b> con 12 V pasarían 12 / 1 000 000 = 0.000012 A (0.012 mA); la tira ni prende. Si quieres limitar con resistencia,
se calcula R = voltaje que quieres quitar ÷ corriente: por ejemplo, para quitar 0.5 V a una tira de 0.42 A, R = 0.5 / 0.42 ≈ <b>1.2 Ω de 1 W</b>.
Funciona, pero tira energía en calor y cambia si cambias la tira. Con el módulo ajustable no la necesitas.</p>
<h2 class="pb">1 · Hojas para planchar (1:1)</h2>
<div class="hoja">{cu}{cu}</div><div class="cap">Cobre — ya va en espejo; las piezas SMD se sueldan de este lado</div>
<div class="hoja">{silk}{silk}</div><div class="cap">Serigrafía para el lado sin cobre — también en espejo</div>
<div class="fig" style="margin-top:2mm">{bar} <span style="font-size:8pt">esta barra debe medir 80 mm</span></div>
<div class="nota">Láser al <b>100 %</b>. Barrenos: <b>0.8 mm</b> trimpot, <b>1.0 mm</b> C6/C7, <b>1.2 mm</b> BR1 y borneras, <b>3.2 mm</b> esquinas.
Revisa a contraluz entre las patas del LM2596 (0.6 mm).</div>
<h2>2 · Esquema</h2>
<div class="fig">{esq}</div>
<h2 class="pb">3 · Material</h2>
<table><tr><th>Ref.</th><th>Cant.</th><th>Pieza</th><th>Nota</th></tr>{"".join(fila(r) for r in BOM)}</table>
<h2>4 · Montaje (visto desde el lado del cobre)</h2>
<div class="fig">{big(mont, 2.2)}</div>
<div class="cap">Café = cobre. Negro = SMD de este lado. Azul punteado = piezas de patitas del otro lado.</div>
<ol>{pasos}</ol>
<h2 class="pb">5 · Pruebas</h2>
<ol>
<li><b>Sin corriente:</b> continuidad entre + y − de J2 y de la entrada filtrada (C6): no deben quedarse pitando.</li>
<li><b>Trimpot al mínimo:</b> gíralo unas 20 vueltas a la izquierda (es multivuelta, no tiene tope duro).</li>
<li><b>Enciende sin carga:</b> prenden LED1 y LED2; la salida marca ≈ 1.2–2 V. Gira a la derecha mirando el multímetro hasta el voltaje que quieres.</li>
<li><b>Con carga:</b> conecta la tira o el circuito; el voltaje casi no debe cambiar. Con 2 A el LM2596 y la bobina se ponen tibios-calientes, pero se pueden tocar un momento.</li>
<li>Marca con plumón en la placa el voltaje que dejaste ajustado.</li>
</ol>
<h2>6 · Si algo falla</h2>
<table><tr><th>Síntoma</th><th>Revisa</th></tr>
<tr><td>El voltaje no cambia al girar</td><td>Patas de TP1 o R3 sin soldar, pata 4 sin soldar. Si se queda en ≈ 1.2 V: TP1 en cero o abierto entre patas 1–2.</td></tr>
<tr><td>Sale el voltaje de entrada</td><td>Pata 2 en corto con la 1, o FB (pata 4) sin conexión al trimpot. <b>Desconecta la carga.</b></td></tr>
<tr><td>Baja con carga</td><td>Entrada menos de 3 V arriba de la salida, eliminador de poca corriente, bobina de menos de 3 A.</td></tr>
<tr><td>No prende nada</td><td>Fuente de entrada, J1, BR1, pata 5 del LM2596 (va a tierra).</td></tr>
</table>
<p style="color:#555;font-size:8.5pt;margin-top:3mm">Diseño revisado por programa: separación mínima 0.55 mm, todas las conexiones verificadas, cuerpos de las piezas de patitas sin encimarse. Aún no se ha armado físicamente.</p>
</body></html>"""
open(os.path.join(here, "manual.html"), "w").write(html)
print("manual.html escrito")
