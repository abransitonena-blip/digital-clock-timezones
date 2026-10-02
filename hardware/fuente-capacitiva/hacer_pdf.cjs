// Genera fuente_capacitiva_placa.pdf (tamaño carta, escala 1:1) y vistas PNG.
const { chromium } = require('playwright');
const fs = require('fs');
const cu = fs.readFileSync('cobre_planchar.svg', 'utf8');
const co = fs.readFileSync('componentes.svg', 'utf8');
const big = co.replace('width="95mm" height="72mm"', 'width="190mm" height="144mm"');
const bar = `<svg width="50mm" height="6mm" viewBox="0 0 50 6"><rect x="0" y="2" width="50" height="1.2" fill="#000"/><rect x="0" y="0" width="0.6" height="6"/><rect x="49.4" y="0" width="0.6" height="6"/></svg>`;
const html = `<!doctype html><meta charset="utf-8"><style>
@page{size:letter;margin:12mm}
body{font-family:Arial,Helvetica,sans-serif;margin:0;color:#000}
h1{font-size:15pt;margin:0 0 2mm} p{font-size:9.5pt;margin:1mm 0} .row{display:flex;gap:10mm;margin:5mm 0}
.pg{page-break-after:always}
</style>
<div class="pg">
<h1>Fuente capacitiva 5 salidas · PISTAS PARA PLANCHAR (escala 1:1)</h1>
<p><b>Imprime en impresora LÁSER al 100 % ("tamaño real", sin "ajustar a página")</b> en papel couché o de revista. <b>NO lo inviertas</b>: ya está listo. Si el letrero sale al revés en el papel es correcto: al planchar queda derecho sobre el cobre.</p>
<p>Comprobación: la barra mide exactamente 50 mm y la placa 95 × 72 mm. Si no mide eso, revisa la escala de la impresora.</p>
<div>${bar} <span style="font-size:9pt">50 mm</span></div>
<div class="row" style="flex-direction:column;gap:8mm">${cu}${cu}</div>
<p>Dos copias por si la primera no se transfiere bien. Los puntos blancos marcan dónde perforar (broca de 0.8 a 1 mm; 1.2 mm para las borneras).</p>
</div>
<div class="pg">
<h1>Acomodo de componentes (vista desde arriba, 1:1)</h1>
<p>Los componentes van del lado SIN cobre y se sueldan del lado del cobre. El color café es la pista vista a través de la placa.</p>
<div class="row">${co}</div>
<p><b>C1</b> tiene 3 agujeros: usa el de 15 mm o el de 22.5 mm según el tamaño de tu capacitor. <b>Fusible</b>: va en el cable de entrada (portafusible de cable, 500 mA lento).</p>
</div>
<div class="pg">
<h1>Lista de material (versión 1, 5 salidas en serie)</h1>
<table style="border-collapse:collapse;width:100%;font-size:9.5pt" border="1" cellpadding="6">
<tr style="background:#eee"><th>Ref</th><th>Cant.</th><th>Cómo pedirlo en mostrador</th></tr>
<tr><td>C1</td><td>1</td><td>Capacitor <b>X2 275 VAC 0.56 µF (564J)</b>. Si no hay, 0.47 µF (474J)</td></tr>
<tr><td>R1</td><td>1</td><td>Resistencia <b>1 MΩ ½ W</b></td></tr>
<tr><td>R2</td><td>1</td><td>Resistencia <b>150 Ω 1 W antiflama</b></td></tr>
<tr><td>D1–D4</td><td>4</td><td>Diodo <b>1N4007</b></td></tr>
<tr><td>C2</td><td>1</td><td>Electrolítico <b>47 µF 250 V</b> (13 mm, patas a 5 mm)</td></tr>
<tr><td>R3</td><td>1</td><td>Resistencia <b>220 kΩ ½ W</b></td></tr>
<tr><td>J0–J5</td><td>6</td><td>Bornera de 2 polos <b>KF301 paso 5 mm</b></td></tr>
<tr><td>F1</td><td>1+1</td><td>Portafusible de cable + fusible 5×20 <b>lento 500 mA</b></td></tr>
<tr><td>LED</td><td>15</td><td>LED de 5 mm (3 por salida)</td></tr>
<tr><td>—</td><td>1</td><td>Placa fenólica de una cara 10×10 cm, cloruro férrico, plumón, fibra verde</td></tr>
<tr><td>—</td><td>1</td><td>Caja de plástico, cable con clavija, termofit, soldadura; foco de 60 W para probar</td></tr>
</table>
<p style="font-size:9.5pt">En esta versión las 5 salidas van en serie: todas llevan la misma corriente. Si una se desconecta, se apagan todas. Si quieres salidas independientes, usa la versión de 5 canales.</p>
</div>
<div><h1>Acomodo ampliado 2× (para ver mejor, no es para planchar)</h1>${big}</div>`;
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.setContent(html);
  await p.pdf({ path: 'fuente_capacitiva_placa.pdf', format: 'Letter', printBackground: true, preferCSSPageSize: true });
  for (const [f, s] of [['cobre_planchar', cu], ['componentes', co]]) {
    const q = await b.newPage({ deviceScaleFactor: 1 });
    await q.setContent(`<body style="margin:0;background:#fff">${s.replace(/width="95mm" height="72mm"/, 'width="950" height="720"')}</body>`);
    await q.setViewportSize({ width: 950, height: 720 });
    await q.screenshot({ path: f + '.png' });
  }
  await b.close();
  console.log('ok');
})();
