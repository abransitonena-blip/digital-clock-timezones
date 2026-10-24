// Genera fuente_2canales_5x5.pdf (carta, escala 1:1).
const { chromium } = require('playwright');
const fs = require('fs');
const rd = f => fs.readFileSync(f, 'utf8');
const cu = rd('cobre_planchar.svg'), top = rd('componentes_arriba.svg'), bot = rd('smd_lado_cobre.svg');
const cab = rd('../fuente-5canales-v3/cableado.svg');
const z = (s, k) => s.replace('width="50mm" height="50mm"', `width="${50 * k}mm" height="${50 * k}mm"`);
const bar = `<svg width="50mm" height="6mm" viewBox="0 0 50 6"><rect x="0" y="2" width="50" height="1.2"/><rect x="0" y="0" width="0.6" height="6"/><rect x="49.4" y="0" width="0.6" height="6"/></svg>`;
const bom = [
  ['C1, C2', '2', '<b>X2 275 VAC</b>, según tus LED (lo normal: 474J; ver tabla en la base de datos)', 'De patitas, en bornera'],
  ['TC1, TC2', '2', 'Bornera <b>KF301 de 3 polos</b> (pata central cortada)', 'De patitas'],
  ['RD', '4', 'Resistencia SMD <b>1206 de 1 MΩ</b> (105)', 'SMD, lado del cobre'],
  ['RS1, RS2', '2', 'Resistencia SMD <b>2512 de 150 Ω 1 W</b> (151)', 'SMD, lado del cobre'],
  ['D', '8', 'Diodo SMD <b>M7</b> (1N4007 en SMA)', 'SMD, lado del cobre; franja = cátodo'],
  ['CE1, CE2', '2', 'Electrolítico <b>47 µF 250 V</b>, 13 mm, patas a 5 mm', 'De patitas'],
  ['RC1, RC2', '2', 'Resistencia <b>220 kΩ ½ W</b>', 'De patitas'],
  ['J1, J2', '2', 'Bornera <b>KF301 de 3 polos</b> (pata central cortada)', 'De patitas'],
  ['J0', '1', 'Bornera <b>KF301 de 2 polos</b>', 'De patitas'],
  ['RV1', '1', 'Varistor <b>10D241K</b>', 'De patitas; levántalo 2 mm de la placa'],
  ['—', '2', 'Tornillo M3 con poste separador de 10 mm', 'Agujeros de 3 mm'],
];
const tr = rows => rows.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join('')}</tr>`).join('');
const css = `@page{size:letter;margin:11mm}body{font-family:Arial,Helvetica,sans-serif;margin:0;color:#000}
h1{font-size:15pt;margin:0 0 2mm}h2{font-size:12pt;margin:4mm 0 2mm}p,li{font-size:9.5pt;margin:1mm 0;line-height:1.35}
.pg{page-break-after:always}.g{display:grid;grid-template-columns:repeat(3,50mm);gap:8mm;margin-top:4mm}
.row{display:flex;gap:8mm;align-items:flex-start;margin-top:3mm}.cap{font-size:8.5pt;color:#444;margin-top:1mm}
table{border-collapse:collapse;width:100%;font-size:9pt}th,td{border:0.3mm solid #999;padding:1.4mm 2mm;text-align:left;vertical-align:top}th{background:#eee}`;
const html = `<!doctype html><meta charset="utf-8"><style>${css}</style>
<div class="pg"><h1>Fuente de 2 canales · placa 5 × 5 cm · PISTAS PARA PLANCHAR (1:1)</h1>
<p><b>Imprime en LÁSER al 100 %</b> y <b>no lo inviertas</b> (el "127V" sale al revés en el papel a propósito). Cada cuadro es una placa de 50 × 50 mm con 2 salidas. Para 5 salidas necesitas 3 placas (te sobra 1 salida). Aquí van 6 copias.</p>
<p>Los rectángulos sin punto blanco son pads SMD: no se perforan.</p>
<div>${bar} <span style="font-size:9pt">50 mm</span></div>
<div class="g">${cu.repeat(6)}</div></div>
<div class="pg"><h1>Dónde va cada pieza</h1>
<div class="row"><div>${top}<div class="cap">Lado de componentes, 1:1</div></div><div>${bot}<div class="cap">Lado del cobre (SMD), 1:1</div></div></div>
<div class="row"><div>${z(top, 1.8)}<div class="cap">Lado de componentes, ampliado</div></div><div>${z(bot, 1.8)}<div class="cap">Lado del cobre (SMD), ampliado. Suelda esto primero</div></div></div>
<ul><li><b>Diodos M7</b>: franja gris = cátodo, exactamente como en el dibujo.</li>
<li>Las borneras del capacitor (arriba) y de salida (abajo) son de 3 polos: <b>corta la pata de en medio</b> (✗ rojo).</li>
<li><b>CE</b>: la franja (−) arriba a la derecha. Va encima de los 4 diodos SMD, que quedan del otro lado.</li></ul></div>
<div><h1>Lista de material (por placa de 2 canales)</h1>
<table><tr><th>Ref</th><th>Cant.</th><th>Cómo pedirlo</th><th>Nota</th></tr>${tr(bom)}</table>
<p>Para 5 salidas multiplica por 3 (3 placas). En la caja, una sola vez: portafusible de chasis con fusible <b>lento de 500 mA</b> e interruptor iluminado, conectados así:</p>
${cab}
<h2>Seguridad (sin zener)</h2>
<ul><li>Esta placa no lleva zener. Una salida sin LED deja su electrolítico cargado a unos 200 V (aguanta 250 V) y la de 220 kΩ lo descarga en unos 10 segundos.</li>
<li>Por eso: <b>conecta y desconecta LED siempre con la fuente apagada</b> y espera 10 segundos. Conectarlos en caliente quema los LED.</li>
<li>No está aislada: placa y LED quedan a 127 V. Caja de plástico cerrada. Primera prueba con foco de 60 W en serie.</li></ul></div>`;
(async () => { const b = await chromium.launch(); const p = await b.newPage(); await p.setContent(html);
  await p.pdf({ path: 'fuente_2canales_5x5.pdf', format: 'Letter', printBackground: true, preferCSSPageSize: true }); await b.close(); console.log('ok'); })();
