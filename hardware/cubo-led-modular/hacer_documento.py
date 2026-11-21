"""Documento del sistema Cubo AP → documento.html (imprimir.cjs → cubo_ap_sistema.pdf)."""
import os, base64
here = os.path.dirname(os.path.abspath(__file__))
img = lambda f, w: f'<img src="data:image/png;base64,{base64.b64encode(open(os.path.join(here, f), "rb").read()).decode()}" style="width:{w}mm;border-radius:2mm">'
def tabla(cab, filas): return "<table><tr>" + "".join(f"<th>{c}</th>" for c in cab) + "</tr>" + "".join("<tr>" + "".join(f"<td>{c}</td>" for c in f) + "</tr>" for f in filas) + "</table>"
capas = """<svg width="186mm" height="58mm" viewBox="0 0 186 58" font-family="Arial,Helvetica,sans-serif">
<defs><marker id="f" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6 Z" fill="#333"/></marker></defs>
<g font-size="3.2">
<rect x="2" y="16" width="22" height="22" rx="3" fill="#fde2e2" stroke="#c00"/><text x="13" y="26" text-anchor="middle" font-weight="700">127 V~</text><text x="13" y="31" text-anchor="middle" font-size="2.6">red</text>
<rect x="34" y="8" width="40" height="38" rx="3" fill="#fff4ec" stroke="#e8590c"/><text x="54" y="15" text-anchor="middle" font-weight="700">1 · Cartucho de potencia</text>
<text x="54" y="22" text-anchor="middle" font-size="2.7">S 25 W · M 40 W · L 75 W</text><text x="54" y="27.5" text-anchor="middle" font-size="2.7">fusible, varistor, aislamiento</text><text x="54" y="33" text-anchor="middle" font-size="2.7">→ bus de 24 V DC</text><text x="54" y="40" text-anchor="middle" font-size="2.5" fill="#555">se elige según el cliente</text>
<rect x="84" y="8" width="44" height="38" rx="3" fill="#e8f1fe" stroke="#2563eb"/><text x="106" y="15" text-anchor="middle" font-weight="700">2 · Regulación configurable</text>
<text x="106" y="22" text-anchor="middle" font-size="2.7">reductor 3–24 V, hasta 5 A</text><text x="106" y="27.5" text-anchor="middle" font-size="2.7">voltaje + límite de corriente</text><text x="106" y="33" text-anchor="middle" font-size="2.7">tarjeta de configuración</text><text x="106" y="40" text-anchor="middle" font-size="2.5" fill="#555">o ajuste desde la app</text>
<rect x="138" y="8" width="46" height="38" rx="3" fill="#e9f7ee" stroke="#2f8f4e"/><text x="161" y="15" text-anchor="middle" font-weight="700">3 · Control</text>
<text x="161" y="22" text-anchor="middle" font-size="2.7">ESP32-C3: Bluetooth + Wi-Fi</text><text x="161" y="27.5" text-anchor="middle" font-size="2.7">4 canales PWM (R G B W)</text><text x="161" y="33" text-anchor="middle" font-size="2.7">salida datos WS2812</text><text x="161" y="40" text-anchor="middle" font-size="2.5" fill="#555">mide V, A y temperatura</text>
</g>
<path d="M24 27 H33" stroke="#333" stroke-width="0.7" marker-end="url(#f)"/><path d="M74 27 H83" stroke="#333" stroke-width="0.7" marker-end="url(#f)"/><path d="M128 27 H137" stroke="#333" stroke-width="0.7" marker-end="url(#f)"/>
<text x="161" y="54" text-anchor="middle" font-size="3" font-weight="700">→ tira LED</text><path d="M161 46 V50" stroke="#333" stroke-width="0.7" marker-end="url(#f)"/>
</svg>"""
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page {{ size: letter; margin: 11mm 12mm; }}
body {{ font-family: Arial, Helvetica, sans-serif; font-size: 9.6pt; color: #111; margin: 0; }}
h1 {{ font-size: 20pt; margin: 0; }} h2 {{ font-size: 12.5pt; margin: 4.5mm 0 1.8mm; border-bottom: 1.5px solid #111; padding-bottom: 0.6mm; }}
.sub {{ color: #444; margin: 1mm 0 3mm; }} .fig {{ text-align: center; }} .cap {{ font-size: 8pt; color: #555; text-align: center; margin-top: 1mm; }}
.fila {{ display: flex; gap: 3mm; justify-content: center; }}
.specs {{ display: flex; gap: 2.5mm; margin: 2mm 0; }} .spec {{ flex: 1; border: 1.5px solid #111; border-radius: 2.5mm; padding: 1.6mm 2.2mm; }}
.spec b {{ display: block; font-size: 12pt; }} .spec span {{ color: #555; font-size: 8.3pt; }}
table {{ border-collapse: collapse; width: 100%; font-size: 9pt; margin: 1mm 0; }} th, td {{ border: 1px solid #999; padding: 1.2mm 1.8mm; text-align: left; vertical-align: top; }} th {{ background: #eee; }}
.nota {{ border-left: 3px solid #e8590c; background: #fff4ec; padding: 1.6mm 3mm; margin: 2mm 0; }}
ul, ol {{ margin: 1mm 0; padding-left: 5.5mm; }} li {{ margin: 0.8mm 0; }} .pb {{ page-break-before: always; }}
</style></head><body>
<h1>Cubo AP · módulo LED modular</h1>
<div class="sub">Un solo cubo para todos los letreros: impermeable, resistente y configurable por cliente (voltaje, corriente y tipo de tira), con apagado y control por Bluetooth. Concepto de sistema y modelo 3D. Diseño AP.</div>
<div class="fig">{img("render_armado.png", 120)}</div>
<div class="specs">
<div class="spec"><b>80 mm</b><span>cubo de 80 × 80 × 80 mm</span></div>
<div class="spec"><b>IP67</b><span>de diseño: empaque, prensaestopas y ventila</span></div>
<div class="spec"><b>3–24 V · 5 A</b><span>configurable por tarjeta o app</span></div>
<div class="spec"><b>BLE + Wi-Fi</b><span>apagado, brillo, color, escenas</span></div></div>
<h2>1 · El sistema híbrido: tres capas</h2>
<div class="fig">{capas}</div>
<p style="margin:1mm 0"><b>Híbrido</b> quiere decir que el mismo cubo se adapta de dos maneras: <b>por pieza</b> (cambias el cartucho de potencia y la tarjeta
de configuración) y <b>por programa</b> (ajustas desde el teléfono). La carcasa, la placa de control y el firmware son siempre los mismos;
solo cambia lo que el cliente pide.</p>
<ul>
<li><b>Capa 1 · Cartucho de potencia</b> (127 V → 24 V): define cuántos watts aguanta. Para productos que vas a vender recomiendo módulos AC-DC
<b>certificados</b> (tipo Mean Well IRM / LRS): te quitan el riesgo legal y de seguridad del lado de 127 V. El flyback que diseñamos sirve como cartucho S para prototipos.</li>
<li><b>Capa 2 · Regulación configurable</b>: un reductor de hasta 5 A con voltaje y límite de corriente ajustables. La <b>tarjeta de configuración</b>
(una plaquita con 2 resistencias que se enchufa) fija el <b>máximo</b> de voltaje y corriente; la app solo puede ajustar <b>por debajo</b> de ese máximo.
Así, aunque alguien mueva la app, nunca se quema una tira de 12 V.</li>
<li><b>Capa 3 · Control</b>: ESP32-C3 con Bluetooth y Wi-Fi, 4 salidas PWM con MOSFET (R, G, B, W o monocolor), salida de datos para tiras
direccionables, medición de voltaje, corriente y temperatura, LED de estado y actualizaciones por aire.</li>
</ul>
<h2 class="pb">2 · Tus ejemplos de clientes</h2>
{tabla(["Pedido", "Potencia", "Cartucho", "Tarjeta", "Notas"], [
 ["20 letreros a 12 V 5 A", "60 W", "L (75 W)", "12 V / 5 A", "Pierde ≈ 8 W en calor: cuerpo de aluminio o base metálica"],
 ["12 V a 1 A", "12 W", "S (25 W)", "12 V / 1 A", "Carcasa impresa sin problema"],
 ["15 V a 1 A", "15 W", "S (25 W)", "15 V / 1 A", "Mismo cubo que el anterior, otra tarjeta"]])}
<div class="nota">Regla: el cartucho debe dar <b>al menos 25 % más</b> que lo que pide el cliente. Las tiras de 12 V son de <b>voltaje constante</b>:
el «amperaje» que te piden es la <b>capacidad</b> de la fuente y el <b>límite de protección</b>, no algo que se le fuerce a la tira.</div>
<h2>3 · Tipos de tira que acepta</h2>
{tabla(["Tipo", "Cables", "Cómo lo maneja el cubo"], [
 ["Monocolor 5 / 12 / 24 V", "+ y −", "1 canal PWM: encendido, apagado y brillo"],
 ["CCT (blanco cálido / frío)", "+, C, W", "2 canales PWM"],
 ["RGB (ánodo común)", "+, R, G, B", "3 canales PWM: color y escenas"],
 ["RGBW", "+, R, G, B, W", "4 canales PWM"],
 ["Direccionable WS2812 / SK6812 / WS2815", "+, −, datos", "Salida de datos; cada LED con su color"]])}
<p style="margin:1mm 0">La bornera de salida tiene <b>6 contactos</b>: +V, R, G, B, W y DATOS (con −). El tipo de tira se elige en la app.</p>
<h2>4 · Funciones desde la app</h2>
<ul>
<li>Encender y apagar a distancia (Bluetooth de cerca; Wi-Fi en red o con horario).</li>
<li>Brillo, color, escenas y horarios (prender al anochecer, apagar a la 1 a. m.).</li>
<li>Ver voltaje, corriente, watts y temperatura; aviso si una tira está en corto o se calienta.</li>
<li>Configurar el voltaje de salida y el límite de corriente, siempre dentro de lo que permite la tarjeta.</li>
<li>Agrupar los 20 cubos de un cliente y controlarlos juntos.</li>
</ul>
<h2 class="pb">5 · La carcasa (modelo en Blender)</h2>
<div class="fila">{img("render_explotado.png", 92)}{img("render_corte.png", 92)}</div>
<div class="cap">Izquierda: explotado (tapa, empaque naranja, placas). Derecha: corte a la mitad (pared, empaque en su ranura, postes).</div>
{tabla(["Parte", "Medidas y detalle"], [
 ["Cuerpo", "80 × 80 × 66 mm, pared 4 mm, fondo 3.5 mm, esquinas R7; logo AP grabado; 2 orejas de montaje con ranura"],
 ["Tapa", "80 × 80 × 14 mm, 4 tornillos M3 a insertos de latón; guía de luz para el LED de estado; zona delgada como ventana de la antena"],
 ["Empaque", "Cordón de silicón de 2.5 mm en ranura de 2.4 × 1.7 mm (≈ 25 % de compresión)"],
 ["Prensaestopas", "2 × M16 IP68: uno para 127 V (izquierda) y uno para la tira (derecha)"],
 ["Ventila", "Membrana M12 (tipo Gore) atrás: deja respirar y evita que entre agua o se condense"],
 ["Interior", "Postes M3 a 60 × 60 mm para la placa de control; espacio para un cartucho de hasta ≈ 52 × 44 × 24 mm (talla S). Para el cartucho L de 75 W haz la versión de 100 mm: <code>L = 100</code> en cubo.py"]])}
<h2>6 · Reglas para que sea impermeable y resistente</h2>
<ul>
<li>Imprimir en <b>ASA o PETG</b> (aguantan sol y calor), con 4 perímetros y 100 % de relleno en paredes; barniz o resina por fuera si es para exterior.</li>
<li>Apretar los 4 tornillos en cruz y parejo, para que el empaque comprima igual en todo el contorno.</li>
<li>Nada de metal sobre la antena del ESP32: la ventana delgada de la tapa queda justo encima.</li>
<li>Cartucho L (60–75 W): la caja cerrada debe sacar ≈ 8 W de calor. Usar <b>cuerpo de aluminio</b> (o base de aluminio con pasta térmica). En plástico, máximo ≈ 25 W.</li>
<li>Opcional: barnizar o encapsular (potting) la placa de control para máxima protección.</li>
<li>Prueba de cada lote: 30 minutos sumergido a 1 m (IP67) o chorro de manguera (IP65); abrir y revisar que no haya humedad.</li>
</ul>
<h2>7 · Archivos</h2>
<ul>
<li><b>cubo_ap.blend</b>: ábrelo en Blender 4.x (tiene cuerpo, tapa, empaque, prensaestopas y placas de referencia).</li>
<li><b>cuerpo.stl, tapa.stl, empaque.stl</b>: listos para imprimir, en milímetros y con la malla cerrada (revisada).</li>
<li><b>cubo.py</b>: el modelo paramétrico; cambia el lado <code>L</code>, el alto, la pared o los barrenos, corre el script y se regenera todo.</li>
</ul>
<h2>8 · Siguientes pasos</h2>
<ol>
<li>Elegir los cartuchos S y L (módulos certificados) y medirlos, para ajustar el interior.</li>
<li>Diseñar la placa de control: ESP32-C3, reductor de 5 A configurable, 4 MOSFET y medición, a la medida de los postes de 60 × 60 mm.</li>
<li>Firmware y app por Bluetooth (configuración, escenas, grupos).</li>
<li>Imprimir un prototipo, probar la impermeabilidad y la temperatura con 60 W.</li>
</ol>
</body></html>"""
open(os.path.join(here, "documento.html"), "w").write(html); print("documento.html escrito")
