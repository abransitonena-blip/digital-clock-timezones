// Genera tabla_capacitores_led.pdf (carta horizontal).
const { chromium } = require('playwright');
const fs = require('fs');
const d = JSON.parse(fs.readFileSync('datos.json', 'utf8'));
const colors = d.leds.map(l => l[0]);
const cell = (color, n) => d.rows.find(r => r.color === color && r.n === n);
const matriz = (key) => `<table class="m"><tr><th>LED por salida</th>${colors.map(c => `<th>${c}</th>`).join('')}</tr>
${d.ns.map(n => `<tr><td class="n">${n}</td>${colors.map(c => { const r = cell(c, n); return `<td>${r ? `<b>${r[key]}</b><small>${key === 'cap_normal' ? r.ma_normal : r.ma_vida} mA</small>` : '<span class="x">—</span>'}</td>`; }).join('')}</tr>`).join('')}</table>`;
const head = ['ID', 'Color', 'Vf (V)', 'LED', 'V total', 'Capacitor normal', 'mA', 'mA red +10 %', 'Capacitor larga vida', 'mA', 'Zener 5 W (V3)', 'Potencia LED (W)'];
const db = `<table class="db"><thead><tr>${head.map(h => `<th>${h}</th>`).join('')}</tr></thead><tbody>
${d.rows.map(r => `<tr><td>${r.id}</td><td>${r.color}</td><td>${r.vf}</td><td>${r.n}</td><td>${r.v_total}</td><td><b>${r.cap_normal}</b> (${r.uf_normal} µF)</td><td>${r.ma_normal}</td><td>${r.ma_alta}</td><td><b>${r.cap_vida}</b></td><td>${r.ma_vida}</td><td>${r.zener}</td><td>${r.watts}</td></tr>`).join('')}</tbody></table>`;
const inv = `<table class="db"><tr><th>Código X2</th><th>µF</th><th>LED suman 10 V</th><th>25 V</th><th>50 V</th><th>75 V</th><th>100 V</th></tr>
${d.inversa.map(r => `<tr><td><b>${r[0]}</b></td>${r.slice(1).map((v, i) => `<td>${i ? (v > 21.5 ? `<span class="hi">${v} mA</span>` : v + ' mA') : v}</td>`).join('')}</tr>`).join('')}</table>`;
const css = `@page{size:letter landscape;margin:10mm}body{font-family:Arial,Helvetica,sans-serif;color:#111;margin:0}
h1{font-size:17pt;margin:0 0 1mm}h2{font-size:12.5pt;margin:4mm 0 2mm}p,li{font-size:9.5pt;margin:1mm 0;line-height:1.35}
.pg{page-break-after:always}.cols{display:flex;gap:8mm}.cols>div{flex:1}
table{border-collapse:collapse;width:100%}th,td{border:0.25mm solid #aaa;padding:1.1mm 1.6mm;text-align:center}th{background:#e8efe9;font-size:8.5pt}
.m td{font-size:9pt}.m td b{display:block}.m small{color:#666;font-size:7pt}.m td.n{font-weight:700;background:#f4f6f4}
.x{color:#bbb}.db{font-size:8pt}.db thead{display:table-header-group}.db tr{page-break-inside:avoid}.db tbody tr:nth-child(even){background:#f6f8f6}
.hi{color:#b3261e;font-weight:700}.box{border:0.4mm solid #b3261e;padding:2mm 3mm;margin-top:3mm}
.code{font-family:Consolas,monospace;font-size:11pt;background:#f1f1f1;padding:0.5mm 1.5mm}`;
const html = `<!doctype html><meta charset="utf-8"><style>${css}</style>
<div class="pg">
<h1>Capacitores X2 para fuente capacitiva según el LED</h1>
<p>Base de datos para LED de 5 mm y 3 mm a 127 V / 60 Hz. Sirve para la placa de 5 canales: un capacitor por salida.</p>
<div class="cols">
<div>
<h2>Cómo usar las tablas</h2>
<ol>
<li>Busca el color de tus LED y cuántos van <b>en esa salida</b>.</li>
<li><b>Capacitor normal:</b> unos 17–19 mA, buen brillo. Con la luz alta (+10 %) no pasa de 21.5 mA.</li>
<li><b>Capacitor larga vida:</b> unos 12–14 mA. Brilla un poco menos y los LED duran años más.</li>
<li>Si usas la versión 3, pon también el <b>zener de 5 W</b> de la tabla.</li>
</ol>
<h2>Cómo se lee el código del capacitor</h2>
<p><span class="code">474J</span> = 47 × 10<sup>4</sup> pF = 470 000 pF = <b>0.47 µF</b>. La letra J es tolerancia de ±5 % y la K de ±10 %. Las dos sirven.</p>
<p><span class="code">564</span> = 0.56 µF · <span class="code">684</span> = 0.68 µF · <span class="code">105</span> = 1 µF · <span class="code">334</span> = 0.33 µF</p>
<p>Si el capacitor dice <b>275 V~</b>, ese es su voltaje, no su valor.</p>
</div>
<div>
<h2>Fórmula</h2>
<p><b>I ≈ 4 · f · C · (V<sub>pico</sub> − V<sub>LED</sub>)</b>, con V<sub>pico</sub> = 127 × 1.414 − 1.4 ≈ 178 V y f = 60 Hz.</p>
<p>Los cálculos incluyen el LED testigo y la resistencia de 100 Ω de la versión 3 (+3.8 V). En las versiones 1 y 2 el mismo capacitor da unos 0.5 mA más.</p>
<p>Un capacitor más grande da más corriente. Muchos LED en la misma salida la bajan un poco, porque restan voltaje.</p>
<div class="box">
<p><b>Siempre capacitor X2 de 275 VAC.</b> Nunca uses capacitores cerámicos ni de poliéster común.</p>
<p>Máximo unos 35–40 LED por salida. Las celdas con "—" no son posibles en una sola salida.</p>
<p>No sirve para LED de potencia (1 W o más) ni para LED RGB que cambian de color solos.</p>
</div>
</div>
</div>
</div>
<div class="pg"><h1>Consulta rápida · capacitor normal (≈17–19 mA)</h1>${matriz('cap_normal')}</div>
<div class="pg"><h1>Consulta rápida · capacitor larga vida (≈12–14 mA)</h1>${matriz('cap_vida')}</div>
<div class="pg"><h1>Tabla inversa · qué corriente da cada capacitor</h1>
<p>Suma el voltaje de todos los LED de la salida (por ejemplo, 8 blancos × 3.1 V ≈ 25 V) y busca la columna. En rojo: demasiada corriente para un LED de 5 mm.</p>${inv}</div>
<div><h1>Base de datos completa (${d.rows.length} combinaciones)</h1>${db}
<p style="margin-top:3mm">También viene como archivo <b>tabla_capacitores.csv</b>, que se abre en Excel.</p></div>`;
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  await p.setContent(html);
  await p.pdf({ path: 'tabla_capacitores_led.pdf', printBackground: true, preferCSSPageSize: true });
  await b.close(); console.log('ok');
})();
