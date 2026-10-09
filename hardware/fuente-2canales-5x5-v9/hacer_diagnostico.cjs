// Imprime diagnostico.html a diagnostico_canal_5x5_v9.pdf (carta).
const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + __dirname + '/diagnostico.html');
  await p.pdf({ path: __dirname + '/diagnostico_canal_5x5_v9.pdf', format: 'Letter', preferCSSPageSize: true, printBackground: true });
  await b.close(); console.log('ok'); })();
