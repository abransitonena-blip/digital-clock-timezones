// Tabla: LED en serie (una sola cadena, tipo letrero) × capacitor X2 = corriente. 127 V / 60 Hz.
const { chromium } = require('playwright');
const caps = [0.22, 0.27, 0.33, 0.39, 0.47, 0.56, 0.68, 0.82, 1.0, 1.2, 1.5];
const code = u => { let pf = Math.round(u * 1e6), e = 0; while (pf >= 100) { pf /= 10; e++; } return `${Math.round(pf)}${e}`; };
const I = (c, vo, v = 127) => Math.max(0, 240 * c * 1e-6 * (v * Math.SQRT2 - 1.4 - vo)) * 1000;
const cls = ma => ma > 25 ? 'q' : ma > 22 ? 'a' : ma >= 17 ? 'i' : ma >= 10 ? 'm' : 'b';
function tabla(titulo, vf, ns) {
  const head = `<tr><th>LED en serie</th><th>Volts de la cadena</th>${caps.map(c => `<th>${code(c)}<br><small>${c} µF</small></th>`).join('')}<th>Mejor para 20 mA</th></tr>`;
  const rows = ns.map(n => {
    const vo = n * vf;
    const ok = caps.filter(c => I(c, vo, 139.7) <= 24);
    const best = ok.length ? ok.reduce((a, b) => Math.abs(I(b, vo) - 20) < Math.abs(I(a, vo) - 20) ? b : a) : null;
    return `<tr><td class="n">${n}</td><td>${vo.toFixed(0)} V</td>${caps.map(c => { const v = I(c, vo); return `<td class="${cls(v)}${c === best ? ' best' : ''}">${v.toFixed(1)}</td>`; }).join('')}<td class="bc">${best ? `${code(best)} → ${I(best, vo).toFixed(1)} mA` : '—'}</td></tr>`;
  }).join('');
  return `<h2>${titulo}</h2><table>${head}${rows}</table>`;
}
const css = `@page{size:letter landscape;margin:8mm}body{font-family:Arial,Helvetica,sans-serif;color:#111;margin:0}
h1{font-size:18pt;margin:0 0 1.5mm}h2{font-size:13pt;margin:3mm 0 1.5mm}p{font-size:10pt;margin:1mm 0;line-height:1.4}
table{border-collapse:collapse;width:100%}th,td{border:0.25mm solid #999;padding:1.5mm 0.8mm;text-align:center;font-size:9.2pt}
th{background:#e8efe9;font-size:10pt}th small{font-weight:400;color:#555;font-size:7.5pt}td.n{font-weight:700;font-size:12pt;background:#f4f6f4}
.b{color:#999}.m{color:#333}.i{background:#d9f0e0;font-weight:700}.a{background:#ffe9c4}.q{background:#f8d4d0;color:#9b1c14}
td.best{outline:0.6mm solid #1d6b3a;outline-offset:-0.6mm}.bc{font-weight:700;white-space:nowrap}
.ley{display:flex;gap:4mm;font-size:9pt;margin:2mm 0}.ley span{padding:0.8mm 2.5mm;border:0.25mm solid #999}.pg{page-break-after:always}`;
const intro = `<p>Todos los LED en <b>una sola cadena en serie</b>, conectada a la fuente capacitiva (como un letrero de LED). Red de <b>127 V</b>. La corriente es la misma en todos los LED de la cadena. Valores en <b>mA</b>.</p>
<div class="ley"><span class="i">17–22 mA: ideal para LED de 5 mm</span><span class="a">22–25 mA: alto</span><span class="q">más de 25: quema el LED</span><span class="m">10–17: brillo medio/bajo</span><span class="b">menos de 10: muy poco</span></div>`;
const html = `<!doctype html><meta charset="utf-8"><style>${css}</style>
<div class="pg"><h1>LED en serie × capacitor = corriente</h1>${intro}
${tabla('LED rojos, naranjas o amarillos (≈2.0 V cada uno)', 2.0, [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65])}</div>
<div class="pg"><h1>LED en serie × capacitor = corriente</h1>${intro}
${tabla('LED blancos, azules, verdes o rosas (≈3.1 V cada uno)', 3.1, [3, 5, 8, 10, 12, 15, 18, 20, 25, 30, 35, 40])}</div>
<div><h1>Cómo usar la tabla</h1>
<p>1. Cuenta cuántos LED lleva tu cadena. 2. Busca la fila. 3. La casilla con <b>borde verde</b> es el capacitor que da más cerca de 20 mA (la columna "Mejor para 20 mA" lo dice directo).</p>
<p><b>Ejemplo:</b> un letrero con 40 LED rojos en serie → <b>684</b> (0.68 µF) da unos 16 mA y <b>824</b> da unos 19 mA.</p>
<p><b>Límite:</b> la cadena no debe pasar de unos 130 V en total (unos 65 LED rojos o 40 blancos). Cerca de ese límite, la corriente cambia mucho cuando sube o baja la luz, y los LED pueden parpadear.</p>
<p><b>Si mezclas colores</b> en la misma cadena, suma los volts: rojo 2.0 V, blanco/azul/verde 3.1 V. Busca la fila con ese total en la columna "Volts de la cadena".</p>
<p>En serie, si un LED se funde, se apaga toda la cadena. El capacitor siempre <b>X2 de 275 VAC</b>. Cuando la luz viene alta (+10 %), la corriente sube entre 2 y 5 mA; la columna "Mejor" ya lo toma en cuenta.</p>
<p>La fuente no está aislada: los LED quedan conectados a 127 V. No los toques con la fuente conectada.</p></div>`;
(async () => { const b = await chromium.launch(); const p = await b.newPage(); await p.setContent(html);
  await p.pdf({ path: 'leds_en_serie_capacitor.pdf', printBackground: true, preferCSSPageSize: true }); await b.close(); console.log('ok'); })();
