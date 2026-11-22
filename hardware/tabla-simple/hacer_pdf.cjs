// Tabla simple: capacitor X2 -> corriente de salida, fuente en serie (versión 1), 127 V / 60 Hz.
const { chromium } = require('playwright');
const caps = [0.1, 0.15, 0.22, 0.27, 0.33, 0.39, 0.47, 0.56, 0.68, 0.82, 1.0, 1.2, 1.5];
const code = u => { let pf = Math.round(u * 1e6), e = 0; while (pf >= 100) { pf /= 10; e++; } return `${Math.round(pf)}${e}J`; };
const I = (c, vo) => Math.max(0, 240 * c * 1e-6 * (127 * Math.SQRT2 - 1.4 - vo)) * 1000;
const VB = 15 * 3.1, VR = 15 * 2.0;   // 5 salidas × 3 LED
const uso = ma => ma < 8 ? ['muy bajo', '#888'] : ma < 13 ? ['bajo', '#555'] : ma < 17 ? ['medio', '#1d6b3a'] : ma <= 22 ? ['IDEAL (≈20 mA)', '#1d6b3a'] : ma <= 25 ? ['alto, acorta la vida', '#b26b00'] : ['NO: quema el LED', '#b3261e'];
const rows = caps.map(c => { const b = I(c, VB), r = I(c, VR), u = uso(b);
  return `<tr class="${u[0].startsWith('IDEAL') ? 'best' : ''}"><td class="c">${code(c)}</td><td>${c} µF</td><td class="ma">${b.toFixed(1)} mA</td><td class="ma">${r.toFixed(1)} mA</td><td style="color:${u[1]};font-weight:700">${u[0]}</td></tr>`; }).join('');
const html = `<!doctype html><meta charset="utf-8"><style>
@page{size:letter;margin:14mm}body{font-family:Arial,Helvetica,sans-serif;color:#111;margin:0}
h1{font-size:20pt;margin:0 0 2mm}p{font-size:10.5pt;margin:1.5mm 0;line-height:1.4}
table{border-collapse:collapse;width:100%;margin:5mm 0}th,td{border:0.3mm solid #999;padding:2.6mm 3mm;text-align:center;font-size:12pt;white-space:nowrap}th{white-space:normal}
th{background:#e8efe9;font-size:10.5pt}.c{font-family:Consolas,monospace;font-size:15pt;font-weight:700}.ma{font-size:14pt;font-weight:700}
tr.best td{background:#e3f3e8}.box{border:0.4mm solid #b3261e;padding:3mm 4mm;margin-top:4mm}</style>
<h1>Capacitor → corriente de salida</h1>
<p>Fuente capacitiva con las <b>5 salidas en serie</b> (versión 1) a <b>127 V</b>. En serie la corriente es <b>la misma en todas las salidas</b>: el capacitor que pongas es la corriente que recibe cada salida.</p>
<p>Calculado para 5 salidas con 3 LED cada una (15 LED en total).</p>
<table><tr><th>Capacitor X2 275 VAC</th><th>Valor</th><th>Salida con LED blancos, azules o verdes</th><th>Salida con LED rojos o amarillos</th><th>Uso (con LED blancos)</th></tr>${rows}</table>
<p><b>El ideal para este proyecto es el 684J</b> (unos 21 mA con LED blancos) o el <b>564J</b> (unos 18 mA), que deja margen cuando la luz viene alta. Con LED rojos usa el 564J.</p>
<p>Si pones más LED, la corriente baja un poco; si pones menos, sube un poco. Cuando la luz viene alta (+10 %), sube unos 2 mA.</p>
<div class="box"><p><b>Recuerda:</b> como van en serie, si se funde un LED o se desconecta una salida, se apagan todas. Siempre capacitor <b>X2 de 275 VAC</b>. La fuente no está aislada: no la toques conectada.</p></div>`;
(async () => { const b = await chromium.launch(); const p = await b.newPage(); await p.setContent(html);
  await p.pdf({ path: 'capacitor_corriente_serie.pdf', printBackground: true, preferCSSPageSize: true }); await b.close(); console.log('ok'); })();
