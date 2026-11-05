// Genera fuente_5canales_placa.pdf (carta, escala 1:1): pistas, acomodo, lista de material.
const { chromium } = require('playwright');
const fs = require('fs');
const cu = fs.readFileSync('cobre_planchar.svg', 'utf8');
const co = fs.readFileSync('componentes.svg', 'utf8');
const big = co.replace('width="110mm" height="93mm"', 'width="187mm" height="158mm"');
const bar = `<svg width="50mm" height="6mm" viewBox="0 0 50 6"><rect x="0" y="2" width="50" height="1.2"/><rect x="0" y="0" width="0.6" height="6"/><rect x="49.4" y="0" width="0.6" height="6"/></svg>`;
const bom = [
  ['C1–C5', '5', 'Capacitor <b>X2 275 VAC</b>: uno por salida, del valor que te da la tabla (lo normal: <b>474J</b> o <b>564J</b>). Compra 1–2 extra de 474 y 564 para ajustar', 'Fija la corriente de SU salida'],
  ['RD1–RD5', '5', 'Resistencia <b>1 MΩ ½ W</b>', 'Descarga cada C1–C5 al desconectar'],
  ['RS1–RS5', '5', 'Resistencia <b>150 Ω 1 W antiflama</b> (película metálica)', 'Frena el pico al conectar'],
  ['BR1–BR5', '5', 'Puente rectificador <b>en línea de 4 patas</b>: <b>KBP307</b>, KBP310, KBP206 o 2KBP10 (patas a 3.8 mm)', 'Convierte AC en DC'],
  ['CE1–CE5', '5', 'Electrolítico <b>47 µF 250 V</b>, 13 mm de diámetro, patas a 5 mm (105 °C si hay)', 'Luz fija, sin parpadeo'],
  ['RC1–RC5', '5', 'Resistencia <b>220 kΩ ½ W</b>', 'Descarga cada electrolítico'],
  ['J0–J5', '6', 'Bornera de tornillo de 2 polos <b>KF301, paso 5 mm</b>', 'Entrada de 127 V y 5 salidas'],
  ['F1', '1+1', '<b>Portafusible de cable</b> + fusible 5×20 mm <b>lento 500 mA</b>', 'En el cable de fase de la clavija'],
  ['—', '1', 'Placa fenólica <b>de una cara 15 × 10 cm</b> (se corta a 110 × 93 mm)', ''],
  ['—', '—', 'Cloruro férrico, plumón indeleble, fibra verde, thinner, broca de 1 mm y de 1.2 mm', 'Para hacer la placa'],
  ['—', '1', 'Caja de plástico, cable de uso rudo con clavija, termofit, soldadura 60/40', 'Seguridad y armado'],
  ['—', '1', 'Socket con foco incandescente de 40–60 W', 'Primera prueba en serie'],
];
const tabla = [
  ['1', '394J', '394J'], ['3 a 10', '474J', '474J'], ['15', '564J', '474J'], ['20', '564J', '564J'],
  ['25', '684J', '564J'], ['30', '824J', '564J'], ['35 (máximo)', '105J', '684J'],
];
const css = `@page{size:letter;margin:12mm}body{font-family:Arial,Helvetica,sans-serif;margin:0;color:#000}
h1{font-size:15pt;margin:0 0 2mm}h2{font-size:12pt;margin:5mm 0 2mm}p,li{font-size:9.5pt;margin:1mm 0}
.pg{page-break-after:always}table{border-collapse:collapse;width:100%;font-size:9pt}th,td{border:0.3mm solid #999;padding:1.6mm 2mm;text-align:left;vertical-align:top}th{background:#eee}
.col{display:flex;flex-direction:column;gap:6mm;margin:4mm 0}`;
const html = `<!doctype html><meta charset="utf-8"><style>${css}</style>
<div class="pg">
<h1>Fuente capacitiva de 5 canales · PISTAS PARA PLANCHAR (1:1)</h1>
<p><b>Imprime en LÁSER al 100 % ("tamaño real")</b> en papel couché. <b>NO lo inviertas.</b> El letrero sale al revés en el papel a propósito: al planchar queda derecho sobre el cobre.</p>
<p>Comprobación: la barra mide 50 mm y la placa 110 × 93 mm.</p>
<div>${bar} <span style="font-size:9pt">50 mm</span></div>
<div class="col">${cu}${cu}</div>
</div>
<div class="pg">
<h1>Acomodo de componentes (vista desde arriba, 1:1)</h1>
<p>Los componentes van del lado SIN cobre. El café es la pista vista a través de la placa. <b>No necesita puentes de alambre</b>: la línea N pasa por debajo de C1–C5 y de las resistencias de 1 MΩ, entre sus patas.</p>
<div class="col">${co}</div>
<ul>
<li><b>C1–C5</b>: cada uno tiene 3 agujeros. Usa el de 15 mm o el de 22.5 mm según el tamaño de tu capacitor.</li>
<li><b>Puente BR</b>: la pata <b>+</b> (marcada en el puente, normalmente con la esquina recortada) va a la izquierda, donde está la marca.</li>
<li><b>CE</b>: la franja (−) del electrolítico va a la derecha.</li>
<li>Broca de 1 mm para todo y de 1.2 mm para las borneras.</li>
</ul>
</div>
<div class="pg">
<h1>Lista de material</h1>
<table><tr><th>Ref</th><th>Cant.</th><th>Cómo pedirlo en mostrador</th><th>Para qué sirve</th></tr>
${bom.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join('')}</tr>`).join('')}</table>
<h2>Qué capacitor poner en cada salida (127 V, LED de 5 mm, ≈17–19 mA)</h2>
<table><tr><th>LED en esa salida</th><th>Blanco, azul o verde (≈3.1 V)</th><th>Rojo o amarillo (≈2.0 V)</th></tr>
${tabla.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join('')}</tr>`).join('')}</table>
<p>Cada salida es independiente: si pones 20 LED verdes en la SAL 1, las demás siguen igual. Si desconectas una o dos salidas, las otras siguen prendidas. Una salida sin LED se queda cargada a unos 200 V (CE aguanta 250 V) y su resistencia de 220 kΩ la descarga al desconectar.</p>
<h2>Seguridad</h2>
<ul><li>No está aislada: toda la placa y los LED quedan a 127 V. Métela en caja de plástico cerrada.</li>
<li>Primera prueba con foco de 60 W en serie. Si el foco brilla fuerte, hay un corto.</li>
<li>C1–C5 siempre <b>X2 275 VAC</b>. Nunca uses capacitores cerámicos ni de poliéster común.</li></ul>
</div>
<div><h1>Acomodo ampliado (para ver mejor, no es para planchar)</h1>${big}</div>`;
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.setContent(html);
  await p.pdf({ path: 'fuente_5canales_placa.pdf', format: 'Letter', printBackground: true, preferCSSPageSize: true });
  await b.close();
  console.log('ok');
})();
