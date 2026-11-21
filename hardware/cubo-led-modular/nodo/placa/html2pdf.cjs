// uso: node html2pdf.cjs entrada.html salida.pdf [captura.png]
const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const [inp, pdf, png] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1600, height: 1100 } });
  await p.goto('file://' + path.resolve(inp)); await p.pdf({ path: pdf, format: 'A3', landscape: true, printBackground: true });
  if (png) await p.screenshot({ path: png, fullPage: true });
  await b.close();
})();
