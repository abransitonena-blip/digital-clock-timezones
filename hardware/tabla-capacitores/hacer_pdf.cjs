// Genera base_datos_capacitores_led.pdf (carta horizontal).
const { chromium } = require('playwright');
const fs = require('fs');
const d = JSON.parse(fs.readFileSync('datos.json', 'utf8'));
const colors = d.leds.map(l => l[0]);
const cell = (c, n) => d.rows.find(r => r.color === c && r.n === n);
const matriz = (cap, ma) => `<table class="m"><tr><th>LED por salida</th>${colors.map(c => `<th>${c}</th>`).join('')}</tr>
${d.ns.map(n => `<tr><td class="n">${n}</td>${colors.map(c => { const r = cell(c, n); return `<td>${r ? `<b>${r[cap]}</b><small>${r[ma]} mA</small>` : '<span class="x">—</span>'}</td>`; }).join('')}</tr>`).join('')}</table>`;
const hoja = `<table class="db hd"><tr><th>Color</th><th>Longitud de onda</th><th>Vf mín (V)</th><th>Vf típico (V)</th><th>Vf máx (V)</th><th>Corriente normal</th><th>Corriente máx. continua</th><th>Brillo típico (mcd, transparente)</th><th>Nota</th></tr>
${d.leds.map(l => `<tr><td><b>${l[0]}</b></td><td>${l[1]}</td><td>${l[2]}</td><td><b>${l[3]}</b></td><td>${l[4]}</td><td>20 mA</td><td>30 mA</td><td>${l[5]}</td><td>${l[6]}</td></tr>`).join('')}</table>`;
const head = ['ID', 'Color', 'Vf', 'LED', 'V total', 'Bajo ≈10 mA', 'mA', 'Medio ≈15 mA', 'mA', 'Alto ≈20 mA', 'mA', 'mA red +10 %', 'mA en V1/V2', 'Exacto 20 mA (2 en paralelo)', 'mA', 'Zener 5 W (V3)', 'W LED'];
const db = `<table class="db"><thead><tr>${head.map(h => `<th>${h}</th>`).join('')}</tr></thead><tbody>
${d.rows.map(r => `<tr><td>${r.id}</td><td class="l">${r.color}</td><td>${r.vf}</td><td><b>${r.n}</b></td><td>${r.v_total}</td><td><b>${r.cap_bajo}</b></td><td>${r.ma_bajo}</td><td><b>${r.cap_medio}</b></td><td>${r.ma_medio}</td><td class="hl"><b>${r.cap_alto}</b></td><td class="hl">${r.ma_alto}</td><td>${r.ma_alto_red_alta}</td><td>${r.ma_alto_v1v2}</td><td>${r.exacto_20mA}</td><td>${r.ma_exacto}</td><td>${r.zener_v3}</td><td>${r.watts_led}</td></tr>`).join('')}</tbody></table>`;
const inv = `<table class="db"><tr><th>Código X2</th><th>µF</th>${d.vs.map(v => `<th>${v} V</th>`).join('')}</tr>
${d.inversa.map(r => `<tr><td><b>${r[0]}</b></td><td>${r[1]}</td>${r.slice(2).map(v => `<td class="${v > 24 ? 'hi' : (v >= 18 ? 'ok' : '')}">${v}</td>`).join('')}</tr>`).join('')}</table>`;
const css = `@page{size:letter landscape;margin:9mm}body{font-family:Arial,Helvetica,sans-serif;color:#111;margin:0}
h1{font-size:16pt;margin:0 0 1.5mm}h2{font-size:12pt;margin:3.5mm 0 1.5mm}p,li{font-size:9.5pt;margin:0.8mm 0;line-height:1.35}
.pg{page-break-after:always}.cols{display:flex;gap:8mm}.cols>div{flex:1}
table{border-collapse:collapse;width:100%}th,td{border:0.25mm solid #aaa;padding:1mm 1.4mm;text-align:center}th{background:#e8efe9;font-size:8pt}
.m td{font-size:9pt}.m td b{display:block}.m small{color:#666;font-size:7pt}.m td.n{font-weight:700;background:#f4f6f4}
.x{color:#bbb}.db{font-size:7.6pt}.db thead{display:table-header-group}.db tr{page-break-inside:avoid}.db tbody tr:nth-child(even){background:#f6f8f6}
.hd{font-size:9pt}.l{text-align:left}.hl{background:#fff4d6!important}.hi{color:#b3261e;font-weight:700}.ok{background:#e6f2ec;font-weight:700}
.box{border:0.4mm solid #b3261e;padding:2mm 3mm;margin-top:2mm}.code{font-family:Consolas,monospace;font-size:11pt;background:#f1f1f1;padding:0.3mm 1.4mm}`;
const html = `<!doctype html><meta charset="utf-8"><style>${css}</style>
<div class="pg">
<h1>Base de datos: capacitor X2 según el color y la cantidad de LED</h1>
<p>Red de <b>127 V / 60 Hz</b> · LED de 5 mm y 3 mm · fuente capacitiva de 5 canales (un capacitor por salida).</p>
<div class="cols"><div>
<h2>Cómo usarla</h2>
<ol>
<li>Busca el color y cuántos LED van <b>en esa salida</b>.</li>
<li>Elige el brillo: <b>bajo ≈10 mA</b> (los LED duran más), <b>medio ≈15 mA</b> o <b>alto ≈20 mA</b>, que es el brillo de la hoja de datos.</li>
<li>Si quieres exactamente 20 mA, usa la columna de <b>2 capacitores en paralelo</b>: los dos van en la misma bornera.</li>
<li>Con la luz alta (+10 %), el nivel alto nunca pasa de 24 mA. El LED aguanta 30 mA continuos.</li>
</ol>
<h2>Ejemplo</h2>
<p>3 LED rojos (2.0 V típico, 2.3 V a alto brillo) en alto brillo: capacitor <b>474</b> = 0.47 µF → 19 mA. Para 20 mA exactos: <b>104 + 394</b> en paralelo.</p>
</div><div>
<h2>El código del capacitor</h2>
<p><span class="code">474</span> = 47 × 10<sup>4</sup> pF = <b>0.47 µF</b>, no 47 faradios. <span class="code">394</span> = 0.39 µF · <span class="code">564</span> = 0.56 µF · <span class="code">684</span> = 0.68 µF · <span class="code">105</span> = 1 µF.</p>
<p>La letra que sigue (J ±5 %, K ±10 %) es la tolerancia. Las dos sirven. "275 V~" es el voltaje, no el valor.</p>
<h2>Fórmula</h2>
<p><b>I ≈ 4 · f · C · (V<sub>pico</sub> − V<sub>LED</sub>)</b>, con V<sub>pico</sub> ≈ 178 V. Ya incluye el LED testigo y la resistencia de 100 Ω de la versión 3. En las versiones 1 y 2 da unos 0.5 mA más; viene en su propia columna.</p>
<div class="box"><p><b>Siempre capacitor X2 de 275 VAC.</b> Nunca cerámico ni de poliéster común.</p>
<p>Las celdas "—" no son posibles en una salida (demasiados LED). No sirve para LED de 1 W ni para RGB automáticos.</p></div>
</div></div></div>
<div class="pg"><h1>Hoja de datos por color (LED de 5 mm, valores típicos)</h1>${hoja}
<p style="margin-top:2mm">Valores típicos de LED comerciales; cambian un poco según la marca. La base de datos usa el Vf típico para la corriente y el Vf máximo para elegir el zener. Un LED de 3 mm tiene los mismos voltajes y la misma corriente.</p></div>
<div class="pg"><h1>Consulta rápida · brillo ALTO (≈20 mA)</h1>${matriz('cap_alto', 'ma_alto')}</div>
<div class="pg"><h1>Consulta rápida · brillo MEDIO (≈15 mA)</h1>${matriz('cap_medio', 'ma_medio')}</div>
<div class="pg"><h1>Consulta rápida · brillo BAJO (≈10 mA, larga vida)</h1>${matriz('cap_bajo', 'ma_bajo')}</div>
<div class="pg"><h1>Consulta rápida · 20 mA exactos con 2 capacitores en paralelo</h1>${matriz('exacto_20mA', 'ma_exacto')}</div>
<div class="pg"><h1>Tabla inversa · corriente (mA) de cada capacitor según el voltaje que suman los LED</h1>
<p>Suma los volts de los LED de la salida (por ejemplo, 5 rojos × 2.0 = 10 V) y busca la columna. En verde: 18–24 mA (alto brillo). En rojo: más de 24 mA, demasiado para LED de 5 mm.</p>${inv}</div>
<div><h1>Base de datos completa (${d.rows.length} combinaciones)</h1>${db}
<p style="margin-top:2mm">Archivo para Excel: <b>base_datos_capacitores_led.csv</b>.</p></div>`;
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  await p.setContent(html);
  await p.pdf({ path: 'base_datos_capacitores_led.pdf', printBackground: true, preferCSSPageSize: true });
  await b.close(); console.log('ok');
})();
