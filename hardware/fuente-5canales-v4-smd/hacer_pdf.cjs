// Genera fuente_5canales_v4_smd.pdf (carta, escala 1:1).
const { chromium } = require('playwright');
const fs = require('fs');
const rd = f => fs.readFileSync(f, 'utf8');
const cu = rd('cobre_planchar.svg'), top = rd('componentes_arriba.svg'), bot = rd('smd_lado_cobre.svg'), cab = rd('../fuente-5canales-v3/cableado.svg');
const tabla = JSON.parse(rd('../fuente-5canales-v3/tabla.json'));
const zoom = s => s.replace('width="122mm" height="87mm"', 'width="183mm" height="130.5mm"');
const bar = `<svg width="50mm" height="6mm" viewBox="0 0 50 6"><rect x="0" y="2" width="50" height="1.2"/><rect x="0" y="0" width="0.6" height="6"/><rect x="49.4" y="0" width="0.6" height="6"/></svg>`;
const smd = [
  ['D1–D20', '20', 'Diodo rectificador <b>M7</b> (es el 1N4007 en SMD, encapsulado SMA)', 'Puente de cada canal (4 por canal)', 'Franja = cátodo'],
  ['RS1–RS5', '5', 'Resistencia <b>SMD 2512 de 150 Ω 1 W</b> (dice 151)', 'Frena el pico al encender', ''],
  ['RD1–RD10', '10', 'Resistencia <b>SMD 1206 de 1 MΩ</b> (dice 105)', 'Descarga del X2 (2 en serie por canal)', ''],
  ['RO1–RO5', '5', 'Resistencia <b>SMD 1206 de 100 Ω</b> (dice 101)', 'Suaviza el golpe al conectar LED', ''],
];
const tht = [
  ['C1–C5', '5', 'Capacitor <b>X2 275 VAC</b> según la tabla (lo normal: 474J)', 'Fija la corriente de su salida'],
  ['TC1–TC5', '5', 'Bornera <b>KF301 de 3 polos</b>: se <b>corta la pata de en medio</b>', 'El capacitor se cambia sin soldar'],
  ['CE1–CE5', '5', 'Electrolítico <b>47 µF 250 V</b>, 13 mm, patas a 5 mm', 'Luz fija'],
  ['ZD1–ZD5', '5', '<b>Zener de 5 W 1N53xxB</b> según la tabla', 'Protección al conectar y sin carga'],
  ['RC1–RC5', '5', 'Resistencia <b>220 kΩ ½ W</b> de patitas', 'Descarga el electrolítico'],
  ['LT1–LT5', '5', '<b>LED rojo de 3 mm</b>', 'Testigo de cada salida'],
  ['RV1', '1', 'Varistor <b>10D241K</b>', 'Picos de la línea'],
  ['J0', '1', 'Bornera <b>KF301 de 2 polos</b>', 'Entrada de 127 V'],
  ['J1–J5', '5', 'Bornera <b>KF301 de 3 polos</b>: se <b>corta la pata de en medio</b>', 'Salidas (+ y − en las orillas)'],
  ['Caja', '1+1+1', 'Portafusible de chasis 5×20 con fusible <b>lento 500 mA</b>, interruptor de balancín iluminado, 3 tornillos M3 con poste', ''],
  ['—', '1', 'Placa fenólica <b>de una cara 15 × 10 cm</b> (se corta a 122 × 87 mm), barniz, cloruro férrico, pasta para soldar o flux', ''],
];
const tr = rows => rows.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join('')}</tr>`).join('');
const css = `@page{size:letter;margin:11mm}body{font-family:Arial,Helvetica,sans-serif;margin:0;color:#000}
h1{font-size:15pt;margin:0 0 2mm}h2{font-size:12pt;margin:4mm 0 2mm}p,li{font-size:9.5pt;margin:1mm 0;line-height:1.35}
.pg{page-break-after:always}table{border-collapse:collapse;width:100%;font-size:8.6pt;table-layout:fixed}td,th{overflow-wrap:anywhere}.bom td:first-child,.bom th:first-child{width:16mm}.bom td:nth-child(2),.bom th:nth-child(2){width:11mm}th,td{border:0.3mm solid #999;padding:1.3mm 2mm;text-align:left;vertical-align:top}th{background:#eee}`;
const html = `<!doctype html><meta charset="utf-8"><style>${css}</style>
<div class="pg"><h1>Fuente 5 canales V4 híbrida SMD · PISTAS PARA PLANCHAR (1:1)</h1>
<p><b>Imprime en LÁSER al 100 %</b> y <b>no lo inviertas</b>. El letrero sale al revés en el papel a propósito. La placa mide <b>122 × 87 mm</b> (la V3 medía 124 × 109).</p>
<p>Los rectángulos redondeados sin punto blanco son pads SMD: <b>no se perforan</b>. Los círculos con punto blanco sí se perforan (1 mm; 1.2 mm las borneras; 3 mm los agujeros de montaje).</p>
<div>${bar} <span style="font-size:9pt">50 mm</span></div><div style="margin-top:4mm">${cu}</div></div>
<div class="pg"><h1>Paso 1 · Piezas SMD (van del lado del COBRE)</h1>
<p>Este dibujo es el lado del cobre <b>visto de frente</b>. Suelda primero todo lo SMD, antes que lo de patitas.</p>${bot}
<ul><li><b>Diodos M7</b>: la franja gris es el cátodo. Ponla exactamente como en el dibujo. Son 4 por canal y forman un cuadrito.</li>
<li><b>RS 151</b> (2512, 1 W): es la resistencia grande. <b>RD 105</b>: dos por canal, en fila. <b>RO 101</b>: una por canal, junto al testigo.</li>
<li>Pon un poco de soldadura en un pad, coloca la pieza con pinzas, suelda ese lado y luego el otro.</li></ul></div>
<div class="pg"><h1>Paso 2 · Piezas de patitas (lado SIN cobre)</h1>${top}
<ul><li><b>Bornera del capacitor (arriba)</b> y <b>bornera de salida (abajo)</b> son de 3 polos: <b>corta la pata de en medio</b> (marcada ✗ en rojo). Por ahí pasan pistas.</li>
<li><b>CE</b> va encima del cuadrito de diodos SMD (están del otro lado). El + del electrolítico va abajo a la izquierda.</li>
<li><b>ZD</b>: franja a la izquierda. <b>LT</b>: pata larga arriba. Las piezas gris claro del dibujo son las SMD del otro lado, solo como referencia.</li></ul></div>
<div class="pg"><h1>Lista de material</h1>
<h2>SMD (lado del cobre)</h2><table class="bom"><tr><th>Ref</th><th>Cant.</th><th>Cómo pedirlo</th><th>Para qué</th><th>Ojo</th></tr>${tr(smd)}</table>
<h2>De patitas (lado sin cobre)</h2><table class="bom"><tr><th>Ref</th><th>Cant.</th><th>Cómo pedirlo</th><th>Para qué</th></tr>${tr(tht)}</table>
<h2>Capacitor y zener de cada salida (igual que la V3)</h2>
<table><tr><th>LED en la salida</th><th>Blanco/azul/verde: capacitor</th><th>zener 5 W</th><th>Rojo/amarillo: capacitor</th><th>zener 5 W</th></tr>${tr(tabla)}</table></div>
<div class="pg"><h1>Conexión en la caja y seguridad</h1>${cab}
<ul><li>No está aislada: toda la placa y los LED quedan a 127 V. Caja de plástico cerrada.</li>
<li>Conecta y desconecta LED con la fuente apagada. Primera prueba con foco de 60 W en serie.</li>
<li>Salida que no uses: quita su capacitor de la bornera.</li>
<li>Al final, barniz del lado del cobre (cubre también las piezas SMD), sin tapar los tornillos.</li></ul>
<h2>Qué cambió respecto a la V3</h2>
<ul><li>Puente: 4 diodos M7 SMD por canal, en vez del KBP307.</li><li>Resistencias de 150 Ω, 1 MΩ y 100 Ω en SMD.</li>
<li>Las borneras de salida ahora son de 3 polos (pata central cortada) para que la línea N pase entre sus patas.</li>
<li>Placa 122 × 87 mm: unos 20 % menos área. Lo que no deja achicar más son los 5 electrolíticos de 13 mm y las borneras.</li></ul></div>
<div class="pg"><h1>Ampliado · lado del cobre (SMD)</h1>${zoom(bot)}</div>
<div><h1>Ampliado · lado de componentes</h1>${zoom(top)}</div>`;
(async () => { const b = await chromium.launch(); const p = await b.newPage(); await p.setContent(html);
  await p.pdf({ path: 'fuente_5canales_v4_smd.pdf', format: 'Letter', printBackground: true, preferCSSPageSize: true }); await b.close(); console.log('ok'); })();
