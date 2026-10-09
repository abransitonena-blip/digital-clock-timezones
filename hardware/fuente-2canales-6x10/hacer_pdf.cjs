// Genera fuente_2canales_6x10.pdf (carta, 1:1).
const { chromium } = require('playwright');
const fs = require('fs');
const rd = f => fs.readFileSync(f, 'utf8');
const cu = rd('cobre_planchar.svg'), silk = rd('serigrafia_planchar.svg'), silkv = rd('serigrafia_vista.svg');
const tabla = JSON.parse(rd('../fuente-5canales-v3/tabla.json'));
const z = (s, k) => s.replace('width="62mm" height="100mm"', `width="${62*k}mm" height="${100*k}mm"`);
const bar = `<svg width="50mm" height="5mm" viewBox="0 0 50 5"><rect x="0" y="2" width="50" height="1"/><rect x="0" y="0" width="0.6" height="5"/><rect x="49.4" y="0" width="0.6" height="5"/></svg>`;
const bom = [
  ['C1, C2', '2', 'Capacitor <b>X2 275 VAC</b>, patas a 15 mm, según tus LED (ver tabla)'],
  ['RD1, RD2', '2', 'Resistencia <b>1 MΩ ½ W</b>, acostada, patas a 15 mm'],
  ['RS1, RS2', '2', 'Resistencia <b>150 Ω 1 W</b>, parada'],
  ['BR1, BR2', '2', 'Puente <b>KBP307</b> (esquina recortada = +)'],
  ['CE1, CE2', '2', 'Electrolítico <b>47 µF 250 V</b>, 17 mm, patas a 5 mm'],
  ['ZD1, ZD2', '2', '<b>Zener 5 W 1N53xxB</b> según tus LED (ver tabla; para 3 LED: 1N5355B)'],
  ['RC1, RC2', '2', 'Resistencia <b>220 kΩ ½ W</b>, acostada a 15 mm'],
  ['RO1, RO2', '2', 'Resistencia <b>100 Ω ½ W</b>, parada'],
  ['LT1, LT2', '2', '<b>LED rojo de 3 mm</b> (testigo; pata larga a la izquierda)'],
  ['F1', '1', '<b>Fusible 5×20 mm lento 500 mA con patas</b> (o portafusible para placa)'],
  ['RV1', '1', 'Varistor <b>10D241K</b>'],
  ['J0, J1, J2', '3', 'Bornera <b>KF301 de 2 polos</b>'],
  ['—', '4', 'Tornillo M3 con poste separador (de plástico de preferencia)'],
  ['—', '1', 'Placa fenólica de una cara de <b>10 × 15 cm</b> (se corta a 62 × 100 mm)'],
];
const tr = rows => rows.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join('')}</tr>`).join('');
const css = `@page{size:letter;margin:10mm}body{font-family:Arial,Helvetica,sans-serif;margin:0;color:#000}
h1{font-size:14pt;margin:0 0 1.5mm}h2{font-size:12pt;margin:3mm 0 1.5mm}p,li{font-size:9.3pt;margin:0.8mm 0;line-height:1.35}
.pg{page-break-after:always}.g{display:grid;grid-template-columns:repeat(3,62mm);gap:2mm;margin-top:2mm}
.row{display:flex;gap:6mm;align-items:flex-start}.cap{font-size:8.5pt;color:#444}
table{border-collapse:collapse;width:100%;font-size:8.8pt}th,td{border:0.3mm solid #999;padding:1.2mm 2mm;text-align:left;vertical-align:top}th{background:#eee}`;
const html = `<!doctype html><meta charset="utf-8"><style>${css}</style>
<div class="pg"><h1>Fuente LED 2 canales · 6 × 10 cm · HOJA PARA PLANCHAR (1:1)</h1>
<p><b>Láser al 100 %, sin invertir.</b> Arriba: <b>cobre</b>. Abajo: <b>serigrafía</b> (lado de componentes). ${bar} 50 mm</p>
<div class="g">${cu.repeat(3)}${silk.repeat(3)}</div></div>
<div class="pg"><h1>Cómo queda</h1>
<div class="row"><div>${z(silkv, 1.45)}<div class="cap">Lado de componentes con la serigrafía</div></div>
<div><h2>Qué tiene esta versión</h2><ul>
<li><b>Fusible y varistor en la placa</b>, a la entrada.</li>
<li><b>Zener de 5 W</b> por canal: protege si conectas LED con la fuente prendida o si una salida queda vacía.</li>
<li><b>LED testigo</b> por canal y <b>resistencia de 100 Ω</b> de salida.</li>
<li><b>4 agujeros M3</b> con anillo de cobre unido a un <b>marco de cobre</b>, como tu placa. El marco no conecta con nada y queda a 2.5 mm o más de cualquier pista.</li>
<li>Pistas de 2 mm, rectas o a 45°. Letras en el cobre.</li>
<li>Serigrafía con valores, polaridades, mini tabla de capacitores, aviso de 127 V y recuadro de nombre y fecha.</li></ul>
<h2>Orden</h2><ol><li>Plancha el cobre y quema la placa.</li><li>Perfora: 1 mm las piezas, 1.2 mm borneras, fusible y varistor, 3.2 mm las esquinas.</li>
<li>Plancha la serigrafía del otro lado, alineando sus círculos con los agujeros a contraluz.</li>
<li>Suelda de lo más bajo a lo más alto. El electrolítico y el X2 al final.</li></ol></div></div></div>
<div><h1>Lista de material (una placa, 2 salidas)</h1>
<table><tr><th>Ref</th><th>Cant.</th><th>Cómo pedirlo</th></tr>${tr(bom)}</table>
<h2>Capacitor y zener según los LED de cada salida (127 V)</h2>
<table><tr><th>LED en la salida</th><th>Blanco/azul/verde: C</th><th>zener 5 W</th><th>Rojo/amarillo: C</th><th>zener 5 W</th></tr>${tr(tabla)}</table>
<h2>Seguridad</h2><ul><li>No está aislada: placa, tornillos del marco y LED pueden quedar a 127 V si algo falla. Usa caja de plástico y postes de plástico.</li>
<li>Conecta y desconecta LED con la fuente apagada. Primera prueba con foco de 60 W en serie.</li>
<li>Interruptor iluminado en la caja (opcional, como en las versiones anteriores).</li></ul></div>`;
(async () => { const b = await chromium.launch(); const p = await b.newPage(); await p.setContent(html);
  await p.pdf({ path: 'fuente_2canales_6x10.pdf', format: 'Letter', printBackground: true, preferCSSPageSize: true }); await b.close(); console.log('ok'); })();
