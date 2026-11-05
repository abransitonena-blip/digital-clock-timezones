"""Escribe manual.html (luego imprimir.cjs lo pasa a manual_regulador_12v_2a.pdf)."""
import os
here = os.path.dirname(os.path.abspath(__file__))
rd = lambda f: open(os.path.join(here, f)).read()
cu = rd("cobre_planchar.svg"); mont = rd("montaje.svg")
import re
big = lambda s, k: re.sub(r'width="[0-9.]+mm" height="[0-9.]+mm"', f'width="{50*k}mm" height="{44*k}mm"', s, count=1)
esq = """<svg width="182mm" height="70mm" viewBox="0 0 182 70" font-family="Arial,Helvetica,sans-serif" font-size="3">
<g fill="none" stroke="#000" stroke-width="0.45" stroke-linecap="round" stroke-linejoin="round">
<path d="M6 14 H20 M30 14 H62 M6 58 H174"/>
<path d="M20 10 V18 L30 14 Z M30 10 V18"/>
<path d="M42 14 V30 M42 36 V58"/><path d="M38 30 H46" stroke-width="0.8"/><path d="M38 36 Q42 33 46 36" stroke-width="0.8"/>
<path d="M52 14 V31 M52 35 V58"/><path d="M48.5 31 H55.5 M48.5 35 H55.5" stroke-width="0.8"/>
<rect x="62" y="8" width="32" height="34" rx="1"/>
<path d="M62 34 H58 V58 M78 42 V58"/>
<path d="M94 14 H136 M94 30 H140 V14"/>
<path d="M106 14 V30" stroke="none"/>
<path d="M104 14 V33 M104 41 V58"/><path d="M100 41 H108 L104 33 Z M100 33 H108"/>
<path d="M112 14 q2.5 -5 5 0 q2.5 -5 5 0 q2.5 -5 5 0 q2.5 -5 5 0"/>
<path d="M146 14 V30 M146 36 V58"/><path d="M142 30 H150" stroke-width="0.8"/><path d="M142 36 Q146 33 150 36" stroke-width="0.8"/>
<path d="M158 14 V22 M158 31 V40 M158 46 V58"/><rect x="156" y="22" width="4" height="9"/>
<path d="M155 40 H161 L158 46 Z M155 46 H161"/>
<path d="M140 14 H170"/>
</g>
<path d="M104 33 L100 41 H108 Z" fill="#fff"/>
<g fill="#000"><circle cx="42" cy="14" r="0.8"/><circle cx="52" cy="14" r="0.8"/><circle cx="104" cy="14" r="0.8"/><circle cx="140" cy="14" r="0.8"/>
<circle cx="146" cy="14" r="0.8"/><circle cx="158" cy="14" r="0.8"/><circle cx="42" cy="58" r="0.8"/><circle cx="52" cy="58" r="0.8"/><circle cx="78" cy="58" r="0.8"/>
<circle cx="104" cy="58" r="0.8"/><circle cx="146" cy="58" r="0.8"/><circle cx="158" cy="58" r="0.8"/></g>
<circle cx="6" cy="14" r="1.4" fill="#fff" stroke="#000" stroke-width="0.45"/><circle cx="6" cy="58" r="1.4" fill="#fff" stroke="#000" stroke-width="0.45"/>
<circle cx="174" cy="14" r="1.4" fill="#fff" stroke="#000" stroke-width="0.45"/><circle cx="174" cy="58" r="1.4" fill="#fff" stroke="#000" stroke-width="0.45"/>
<path d="M170 14 H172.6" stroke="#000" stroke-width="0.45"/><path d="M160 6" />
<text x="2" y="9.5">ENTRADA +</text><text x="2" y="65">16–35 V  −</text>
<text x="20" y="8">D1 SS54</text><text x="33" y="24">C1</text><text x="31" y="28" font-size="2.5">220µF 50V</text>
<text x="54" y="26">C2</text><text x="54" y="29" font-size="2.5">1µF</text>
<text x="66" y="22" font-weight="700">U1</text><text x="66" y="26" font-size="2.6">LM2596S-12</text>
<text x="63.5" y="15">1 VIN</text><text x="80" y="15">2 OUT</text><text x="82" y="31">4 FB</text><text x="63.5" y="35">5 ON/OFF</text><text x="72" y="40.5">3 GND</text>
<text x="96" y="12" font-size="2.5">SW</text><text x="108" y="38">D2</text><text x="108" y="41.5" font-size="2.5">SS54</text>
<text x="113" y="9">L1 47µH</text><text x="110" y="28" font-size="2.5">FB (retroalimentación)</text>
<text x="149" y="26">C3</text><text x="147" y="40" font-size="2.5">470µF</text><text x="147" y="43" font-size="2.5">25V</text>
<text x="161" y="28">R1 2.2k</text><text x="162" y="45">LED</text>
<text x="180" y="9.5" text-anchor="end">SALIDA 12 V +</text><text x="180" y="65" text-anchor="end">2 A  −</text>
<text x="38" y="12" font-size="2.5">VIN</text><text x="136" y="12" font-size="2.5">12 V</text>
</svg>"""
BOM = [
 ("U1", "1", "<b>LM2596S-12</b> (versión fija de 12 V), encapsulado TO-263-5 (D2PAK)", "No uses la LM2596S-ADJ: esta placa no tiene divisor de voltaje"),
 ("D1, D2", "2", "Diodo Schottky <b>SS54</b> (5 A, 40 V), SMC/DO-214AB", "D1 protege si conectas la entrada al revés"),
 ("L1", "1", "Bobina SMD <b>47 µH, ≥ 3 A</b>, 12 × 12 mm (tipo CD127 / CDRH127 «470»)", "33 a 68 µH también funciona"),
 ("C1", "1", "Electrolítico SMD <b>220 µF 50 V</b>, 10 × 10.5 mm, bajo ESR", "Entrada"),
 ("C3", "1", "Electrolítico SMD <b>470 µF 25 V</b>, 10 × 10.5 mm, bajo ESR", "Salida"),
 ("C2", "1", "Cerámico <b>1 µF 50 V</b> X7R, 1206", "Junto a la pata 1 del LM2596"),
 ("R1", "1", "Resistencia <b>2.2 kΩ</b> 0805", "Para el LED (≈ 5 mA)"),
 ("LED", "1", "LED SMD 0805 (verde o rojo)", "Indica que hay 12 V"),
 ("J1, J2", "2", "Bornera de 2 tornillos, paso 5.08 mm (o cables soldados)", "Única pieza de patitas"),
 ("—", "1", "Placa fenólica de una cara 5 × 4.4 cm, 2 tornillos M3", ""),
 ("—", "1", "Eliminador de <b>24 V ≥ 1.5 A</b> (o 19 V ≥ 1.8 A de laptop)", "Fuente de entrada"),
]
bom = "".join(f"<tr><td class=r>{a}</td><td class=c>{b}</td><td>{c}</td><td class=g>{d}</td></tr>" for a, b, c, d in BOM)
PASOS = [
 ("Estaña los pads", "Pon una capa delgada de soldadura en todos los pads con flux. Así cada pieza SMD se pega con solo recalentar."),
 ("U1 · LM2596S-12", "Primero que nada. Pata 1 a la derecha (junto a C2), pestaña hacia abajo sobre el pad grande. Fija una pata, alinea, suelda las 5 patas y al final la pestaña: necesita cautín de 60 W o más (o pistola de calor) y bastante soldadura para que pase el calor."),
 ("D1 y D2 · SS54", "La franja del diodo va hacia el lado marcado: D1 franja hacia el LM2596, D2 franja hacia arriba (hacia la pista larga)."),
 ("C2, R1 y LED", "C2 y R1 no tienen polaridad. En el LED, la marca verde o la «T» del reverso es el cátodo: va hacia abajo (hacia la tierra)."),
 ("L1 · bobina 47 µH", "No tiene polaridad. Calienta bien los dos pads grandes."),
 ("C1 y C3 · electrolíticos", "La base de plástico tiene dos esquinas cortadas: ese lado es el + (hacia arriba en los dos). La franja negra del bote es el −."),
 ("Bornes J1 y J2", "Entran por el lado SIN cobre y se sueldan del lado del cobre. Entrada a la derecha, salida al centro-izquierda."),
]
pasos = "".join(f"<li><b>{a}.</b> {b}</li>" for a, b in PASOS)
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page {{ size: letter; margin: 11mm 12mm; }}
body {{ font-family: Arial, Helvetica, sans-serif; font-size: 9.6pt; color: #111; margin: 0; }}
h1 {{ font-size: 19pt; margin: 0; }} h2 {{ font-size: 12pt; margin: 4.5mm 0 1.8mm; border-bottom: 1.5px solid #111; padding-bottom: 0.6mm; }}
.sub {{ color: #444; margin: 0.8mm 0 3mm; }}
.specs {{ display: flex; gap: 3mm; margin-bottom: 2mm; }} .spec {{ flex: 1; border: 1.5px solid #111; border-radius: 2.5mm; padding: 1.8mm 2.5mm; }}
.spec b {{ display: block; font-size: 13pt; }} .spec span {{ color: #555; font-size: 8.5pt; }}
.hoja {{ display: flex; gap: 6mm; justify-content: center; margin: 2mm 0; }}
.nota {{ border-left: 3px solid #e8590c; background: #fff4ec; padding: 1.5mm 3mm; margin: 2mm 0; }}
table {{ border-collapse: collapse; width: 100%; font-size: 9pt; }} th, td {{ border: 1px solid #999; padding: 1.2mm 1.8mm; vertical-align: top; text-align: left; }}
th {{ background: #eee; }} td.r {{ font-weight: 700; white-space: nowrap; }} td.c {{ text-align: center; }} td.g {{ color: #444; }}
ol, ul {{ margin: 1mm 0; padding-left: 5.5mm; }} li {{ margin: 0.9mm 0; }}
.pb {{ page-break-before: always; }} .fig {{ text-align: center; }}
</style></head><body>
<h1>Regulador 12 V · 2 A · SMD</h1>
<div class="sub">Convertidor reductor con LM2596S-12 en placa de una cara de 5 × 4.4 cm, para hacer por planchado. Diseño AP.</div>
<div class="specs">
<div class="spec"><b>16 – 35 V</b><span>entrada DC (24 V ideal)</span></div>
<div class="spec"><b>12 V</b><span>salida fija ± 4 %</span></div>
<div class="spec"><b>2 A</b><span>continuos (pico 3 A)</span></div>
<div class="spec"><b>≈ 88 %</b><span>eficiencia; se calienta poco</span></div></div>
<p style="margin:1mm 0">Es conmutado, no lineal: un 7812 con 24 V de entrada a 2 A tiraría 24 W de calor; el LM2596 tira unos 3 W
repartidos entre el chip, los diodos y la bobina. Trae protección de corriente y de temperatura, y D1 lo protege si conectas la entrada al revés.</p>
<h2>1 · Hoja para planchar (1:1, ya va en espejo)</h2>
<div class="hoja">{cu}{cu}{cu}</div>
<div class="fig"><svg width="50mm" height="5mm" viewBox="0 0 50 5"><rect x="0" y="2" width="50" height="1"/><rect x="0" y="0" width="0.6" height="5"/><rect x="49.4" y="0" width="0.6" height="5"/></svg> <span style="font-size:8pt">esta barra debe medir 50 mm</span></div>
<div class="nota">Imprime en <b>láser al 100 %</b> (sin «ajustar a página»). Las piezas SMD van <b>del lado del cobre</b>: por eso la hoja ya viene en espejo y, ya planchada, «AP 12V 2A» se lee derecho.</div>
<ol>
<li>Lija el cobre con fibra y límpialo con alcohol. Plancha 3–4 min, remoja y retira el papel.</li>
<li>Cloruro férrico hasta que se vaya el cobre sobrante. Quita el tóner con thinner.</li>
<li>Barrenos: <b>1.2 mm</b> en los 4 pads de las borneras y <b>3.2 mm</b> en las 2 esquinas para tornillos. Las piezas SMD no llevan barreno.</li>
<li>Revisa a contraluz que no haya puentes de cobre entre las patas del LM2596 (están a 0.6 mm).</li>
</ol>
<h2 class="pb">2 · Esquema</h2>
<div class="fig">{esq}</div>
<h2>3 · Lista de material</h2>
<table><tr><th>Ref.</th><th>Cant.</th><th>Pieza</th><th>Nota</th></tr>{bom}</table>
<h2>4 · Herramienta</h2>
<ul><li>Cautín de punta fina (30 W) para lo chico y uno de 60 W o más (o pistola de calor) para la pestaña del LM2596.</li>
<li>Soldadura delgada 0.5–0.8 mm, flux en pasta, pinzas, malla desoldadora y multímetro.</li></ul>
<h2 class="pb">5 · Montaje (visto desde el lado del cobre)</h2>
<div class="fig">{big(mont, 2.6)}</div>
<ol>{pasos}</ol>
<h2 class="pb">6 · Pruebas</h2>
<ol>
<li><b>Sin corriente:</b> continuidad entre + y − de la entrada (no debe pitar) y entre + y − de la salida (puede pitar un instante mientras carga C3, luego no).</li>
<li><b>Primera conexión sin carga:</b> conecta el eliminador. Debe prender el LED y medir <b>11.5 – 12.5 V</b> en la salida.</li>
<li><b>Prueba de carga:</b> conecta un foco de auto de 12 V 21 W (≈ 1.75 A) o una tira LED de 12 V. El voltaje debe quedarse arriba de 11.5 V.</li>
<li><b>Temperatura:</b> después de 10 min con carga, el LM2596 puede estar tibio-caliente (hasta ≈ 70 °C) pero debe poder tocarse un momento. Si quema, pégale un disipador chico encima con silicón térmico.</li>
<li><b>Polaridad:</b> si conectas la entrada al revés no pasa nada (D1 bloquea): solo no prende.</li>
</ol>
<h2>7 · Si algo falla</h2>
<table><tr><th>Síntoma</th><th>Revisa</th></tr>
<tr><td>No hay voltaje ni LED</td><td>Entrada al revés, D1 al revés, pata 5 sin soldar (debe ir a tierra), soldadura fría en la pata 1.</td></tr>
<tr><td>Sale el voltaje de entrada (24 V) en la salida</td><td>Pata 2 en corto con la pata 1, o pusiste la versión ADJ en lugar de la -12. <b>Desconecta enseguida.</b></td></tr>
<tr><td>Sale menos de 12 V o baja con carga</td><td>Entrada menor a 16 V, eliminador de poca corriente, pata 4 (FB) sin soldar, bobina saturada (menos de 3 A).</td></tr>
<tr><td>Zumbido o mucho calor en la bobina</td><td>Bobina de menos corriente que la necesaria o de menos de 33 µH.</td></tr>
<tr><td>D2 muy caliente</td><td>D2 al revés o no es Schottky (un 1N4007 no sirve aquí).</td></tr>
</table>
<p style="color:#555;font-size:8.5pt;margin-top:3mm">Diseño revisado por programa: separación mínima entre pistas de 0.55 mm y todas las conexiones verificadas. Esta placa aún no se ha armado físicamente.</p>
</body></html>"""
open(os.path.join(here, "manual.html"), "w").write(html)
print("manual.html escrito")
