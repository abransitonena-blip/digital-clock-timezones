// Genera fuente_5canales_v3.pdf (carta, escala 1:1).
const { chromium } = require('playwright');
const fs = require('fs');
const cu = fs.readFileSync('cobre_planchar.svg', 'utf8');
const co = fs.readFileSync('componentes.svg', 'utf8');
const cab = fs.readFileSync('cableado.svg', 'utf8');
const tabla = JSON.parse(fs.readFileSync('tabla.json', 'utf8'));
const big = co.replace('width="124mm" height="109mm"', 'width="186mm" height="163.5mm"');
const bar = `<svg width="50mm" height="6mm" viewBox="0 0 50 6"><rect x="0" y="2" width="50" height="1.2"/><rect x="0" y="0" width="0.6" height="6"/><rect x="49.4" y="0" width="0.6" height="6"/></svg>`;
const bom = [
  ['C1–C5', '5', 'Capacitor <b>X2 275 VAC</b>, uno por salida, según la tabla (lo normal: 474J; 564J o 684J para muchos LED). Compra 1–2 extra', 'Fija la corriente de su salida'],
  ['TC1–TC5', '5', 'Bornera de tornillo de <b>3 polos KF301</b> (paso 5 mm). <b>Corta la pata de en medio</b> antes de soldarla', 'Cambiar el capacitor sin soldar'],
  ['RD1–RD5', '5', 'Resistencia <b>1 MΩ ½ W</b>', 'Descarga el capacitor X2'],
  ['RS1–RS5', '5', 'Resistencia <b>150 Ω 1 W antiflama</b>', 'Frena el pico al encender'],
  ['BR1–BR5', '5', 'Puente rectificador en línea <b>KBP307</b> (o KBP310, KBP206, 2KBP10)', 'Convierte AC en DC'],
  ['CE1–CE5', '5', 'Electrolítico <b>47 µF 250 V</b>, 13 mm, patas a 5 mm', 'Luz fija, sin parpadeo'],
  ['ZD1–ZD5', '5', 'Diodo <b>zener de 5 W serie 1N53xxB</b>, del voltaje de la tabla', 'Protege al conectar LED y si la salida queda vacía'],
  ['RC1–RC5', '5', 'Resistencia <b>220 kΩ ½ W</b>', 'Descarga el electrolítico'],
  ['RO1–RO5', '5', 'Resistencia <b>100 Ω ½ W</b>', 'Suaviza el golpe al conectar LED'],
  ['LT1–LT5', '5', '<b>LED rojo de 3 mm</b> (o de 5 mm)', 'Testigo: prende si esa salida trabaja'],
  ['RV1', '1', 'Varistor <b>10D241K</b>', 'Absorbe picos de la línea'],
  ['J0–J5', '6', 'Bornera de tornillo de <b>2 polos KF301</b>', 'Entrada y 5 salidas'],
  ['Caja', '1', '<b>Portafusible de chasis 5×20</b> + 2 fusibles <b>lentos 500 mA</b>', 'Se cambia el fusible sin abrir la caja'],
  ['Caja', '1', '<b>Interruptor de balancín iluminado 250 V, 3 patas</b> (tipo KCD3 con luz)', 'Encendido con luz piloto'],
  ['Caja', '4', 'Tornillo M3 con poste separador de 10 mm', 'Fijar la placa'],
  ['—', '1', 'Placa fenólica <b>de una cara 15 × 15 cm</b> (se corta a 124 × 109 mm)', ''],
  ['—', '1', '<b>Barniz para circuitos</b> (o esmalte de uñas transparente)', 'Protege el cobre de humedad'],
  ['—', '—', 'Caja de plástico, cable de uso rudo con clavija, cloruro férrico, plumón, brocas de 1, 1.2 y 3 mm, soldadura, termofit', ''],
];
const css = `@page{size:letter;margin:12mm}body{font-family:Arial,Helvetica,sans-serif;margin:0;color:#000}
h1{font-size:15pt;margin:0 0 2mm}h2{font-size:12pt;margin:4mm 0 2mm}p,li{font-size:9.5pt;margin:1mm 0}
.pg{page-break-after:always}table{border-collapse:collapse;width:100%;font-size:8.8pt}th,td{border:0.3mm solid #999;padding:1.3mm 2mm;text-align:left;vertical-align:top}th{background:#eee}`;
const html = `<!doctype html><meta charset="utf-8"><style>${css}</style>
<div class="pg">
<h1>Fuente 5 canales V3 · PISTAS PARA PLANCHAR (1:1)</h1>
<p><b>Imprime en LÁSER al 100 % ("tamaño real")</b>. <b>NO lo inviertas.</b> El letrero sale al revés en el papel a propósito: al planchar queda derecho. Imprime 2 hojas por si una no pega bien.</p>
<p>Comprobación: la barra mide 50 mm y la placa 124 × 109 mm. Los 4 círculos grandes son los agujeros de montaje: brócalos a 3 mm.</p>
<div>${bar} <span style="font-size:9pt">50 mm</span></div>
<div style="margin-top:4mm">${cu}</div>
</div>
<div class="pg">
<h1>Acomodo de componentes (vista desde arriba, 1:1)</h1>
<div>${co}</div>
<ul>
<li><b>TC1–TC5</b> (bornera de 3 polos del capacitor): <b>corta la pata de en medio</b> (marcada ⊗ en rojo), porque ahí pasa la línea N. El capacitor X2 se atornilla en los dos polos de las orillas.</li>
<li><b>Puente BR</b>: la pata + (esquina recortada) a la izquierda. <b>CE</b>: la franja (−) a la derecha. <b>ZD</b>: la franja del zener a la izquierda (hacia el +).</li>
<li><b>LT</b> (testigo): pata larga a la izquierda. Si no quieres testigo, pon un puente de alambre en su lugar.</li>
<li>No necesita puentes de alambre. Broca de 1 mm para todo, 1.2 mm para las borneras y 3 mm para los agujeros de montaje.</li>
</ul>
</div>
<div class="pg">
<h1>Lista de material</h1>
<table><tr><th>Ref</th><th>Cant.</th><th>Cómo pedirlo en mostrador</th><th>Para qué sirve</th></tr>
${bom.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join('')}</tr>`).join('')}</table>
</div>
<div class="pg">
<h1>Capacitor y zener de cada salida</h1>
<p>127 V, LED de 5 mm, unos 16–19 mA. Cada salida es independiente: elige su fila según cuántos LED le pongas.</p>
<table><tr><th>LED en la salida</th><th>Blanco/azul/verde: capacitor</th><th>zener 5 W</th><th>Rojo/amarillo: capacitor</th><th>zener 5 W</th></tr>
${tabla.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join('')}</tr>`).join('')}</table>
<p>Máximo 30 LED blancos por salida. <b>Salida que no uses: quita su capacitor de la bornera</b> y ese canal queda apagado. Si la dejas sin LED pero con capacitor, el zener se entibia (hasta 1.7 W en uno de 5 W).</p>
<h2>Conexión en la caja: fusible e interruptor</h2>
${cab}
<h2>Seguridad</h2>
<ul><li>No está aislada: toda la placa y los LED quedan a 127 V. Caja de plástico cerrada.</li>
<li>Aunque el zener y la resistencia de 100 Ω suavizan el golpe, <b>conecta y desconecta LED con la fuente apagada</b>.</li>
<li>Primera prueba con un foco de 60 W en serie. Si el foco brilla fuerte, hay un corto.</li>
<li>Al terminar, pon barniz del lado del cobre, sin tapar los tornillos de las borneras.</li></ul>
</div>
<div><h1>Acomodo ampliado (para ver mejor, no es para planchar)</h1>${big}</div>`;
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.setContent(html);
  await p.pdf({ path: 'fuente_5canales_v3.pdf', format: 'Letter', printBackground: true, preferCSSPageSize: true });
  await b.close();
  console.log('ok');
})();
