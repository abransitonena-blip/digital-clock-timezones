// Genera fuente_2canales_5x5_v5.pdf (carta, escala 1:1).
const { chromium } = require('playwright');
const fs = require('fs');
const rd = f => fs.readFileSync(f, 'utf8');
const cu = rd('cobre_planchar.svg'), top = rd('componentes_arriba.svg'), bot = rd('smd_lado_cobre.svg'), silk = rd('serigrafia_planchar.svg'), silkv = rd('serigrafia_vista.svg');
const cab = rd('../fuente-5canales-v3/cableado.svg');
const z = (s, k) => s.replace('width="50mm" height="50mm"', `width="${50 * k}mm" height="${50 * k}mm"`);
const bar = `<svg width="50mm" height="6mm" viewBox="0 0 50 6"><rect x="0" y="2" width="50" height="1.2"/><rect x="0" y="0" width="0.6" height="6"/><rect x="49.4" y="0" width="0.6" height="6"/></svg>`;
const bom = [
  ['C1, C2', '2', 'Capacitor <b>X2 275 VAC</b>, patas a 15 mm, según tus LED (lo normal: 474J)', 'Soldado directo'],
  ['RD1, RD2', '2', 'Resistencia <b>1 MΩ ½ W</b>, <b>parada</b>', 'Arriba (canal 1) y abajo (canal 2), en la esquina'],
  ['RS1, RS2', '2', 'Resistencia <b>150 Ω 1 W</b>, <b>parada</b> (patas a 5 mm)', 'Frena el pico al conectar'],
  ['BR1, BR2', '2', 'Puente <b>KBP307</b> (patas a ~4 mm). La esquina recortada (+) va donde marca el dibujo', 'Parado'],
  ['CE1, CE2', '2', 'Electrolítico <b>47 µF 250 V</b>, 17 mm de diámetro, patas a 5 mm', 'Parado'],
  ['RC1–RC4', '4', 'Resistencia <b>SMD 1206 de 100 kΩ</b> (dice 104), 2 por canal', 'Lado del cobre, debajo del electrolítico'],
  ['J1, J2', '2', 'Bornera <b>KF301 de 2 polos</b>', 'Salidas'],
  ['RV1', '1', 'Varistor <b>10D241K</b>', 'Entre L y N, a la izquierda'],
  ['L, N', '—', 'Cable de uso rudo 2×18 AWG <b>soldado directo</b> en los pads L y N', 'Entrada 127 V (pasa por el fusible de la caja)'],
  ['—', '2', 'Tornillo M3 con poste de plástico', 'Esquinas izquierdas'],
];
const tr = rows => rows.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join('')}</tr>`).join('');
const css = `@page{size:letter;margin:11mm}body{font-family:Arial,Helvetica,sans-serif;margin:0;color:#000}
h1{font-size:15pt;margin:0 0 2mm}h2{font-size:12pt;margin:4mm 0 2mm}p,li{font-size:9.5pt;margin:1mm 0;line-height:1.35}
.pg{page-break-after:always}.g{display:grid;grid-template-columns:repeat(3,50mm);gap:8mm;margin-top:4mm}
.row{display:flex;gap:8mm;align-items:flex-start;margin-top:3mm}.cap{font-size:8.5pt;color:#444;margin-top:1mm}
table{border-collapse:collapse;width:100%;font-size:9pt}th,td{border:0.3mm solid #999;padding:1.4mm 2mm;text-align:left;vertical-align:top}th{background:#eee}`;
const html = `<!doctype html><meta charset="utf-8"><style>${css}</style>
<div class="pg"><h1>Fuente de 2 canales 5 × 5 cm (v5) · HOJA PARA PLANCHAR (1:1)</h1>
<p><b>Imprime en LÁSER al 100 %</b>. No inviertas nada: cada dibujo ya viene listo. Fila de arriba: <b>cobre</b> (lado de pistas). Fila de abajo: <b>serigrafía</b> (lado de componentes).</p>
<div>${bar} <span style="font-size:9pt">50 mm</span></div>
<div class="g">${cu.repeat(3)}${silk.repeat(3)}</div>
<p style="margin-top:4mm"><b>Orden:</b> 1) plancha el cobre y quema la placa en cloruro; 2) perfora; 3) plancha la serigrafía del otro lado, alineando sus círculos con los agujeros (mira la placa a contraluz); 4) suelda.</p>
<p>Los 4 rectángulos chicos sin punto blanco son las resistencias SMD de 100 kΩ (lado del cobre). El texto del cobre y de la serigrafía sale al revés en el papel a propósito.</p></div>
<div class="pg"><h1>Dónde va cada pieza</h1>
<div class="row"><div>${z(silkv, 1.8)}<div class="cap">Así se ve la serigrafía ya planchada (lado de componentes)</div></div><div>${z(bot, 1.8)}<div class="cap">Lado del cobre visto de frente. Suelda primero las 4 resistencias 1206</div></div></div>

<ul><li><b>BR</b> (KBP307): la pata + (esquina recortada) arriba en el canal 1 y abajo en el canal 2, como en el dibujo.</li>
<li><b>CE</b>: la franja (−) hacia la orilla derecha. <b>Todas las resistencias van paradas</b>: el cuerpo sobre el pad con círculo doble y la pata doblada al otro.</li>
<li>La fila de abajo es el espejo de la de arriba.</li></ul></div>
<div><h1>Lista de material (por placa de 2 canales)</h1>
<table><tr><th>Ref</th><th>Cant.</th><th>Cómo pedirlo</th><th>Nota</th></tr>${tr(bom)}</table>
<p>Para 5 salidas multiplica por 3 (3 placas). En la caja, una sola vez: portafusible de chasis con fusible <b>lento de 500 mA</b>, interruptor iluminado y el <b>el varistor ya va en la placa</b>. Conexión:</p>
${cab}
<h2>Seguridad (sin zener)</h2><p>Lleva 2 agujeros M3 en las esquinas izquierdas; las derechas las ocupan los electrolíticos de 17 mm.</p>
<ul><li>Esta placa no lleva zener. Una salida sin LED deja su electrolítico cargado a unos 200 V (aguanta 250 V) y la de 220 kΩ lo descarga en unos 10 segundos.</li>
<li>Por eso: <b>conecta y desconecta LED siempre con la fuente apagada</b> y espera 10 segundos. Conectarlos en caliente quema los LED.</li>
<li>No está aislada: placa y LED quedan a 127 V. Caja de plástico cerrada. Primera prueba con foco de 60 W en serie.</li></ul></div>`;
(async () => { const b = await chromium.launch(); const p = await b.newPage(); await p.setContent(html);
  await p.pdf({ path: 'fuente_2canales_5x5_v5.pdf', format: 'Letter', printBackground: true, preferCSSPageSize: true }); await b.close(); console.log('ok'); })();
