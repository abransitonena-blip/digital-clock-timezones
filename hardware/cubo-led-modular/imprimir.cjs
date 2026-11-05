// Pasa documento.html a cubo_ap_sistema.pdf (carta).
const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + __dirname + '/documento.html');
  await p.pdf({ path: __dirname + '/cubo_ap_sistema.pdf', format: 'Letter', preferCSSPageSize: true, printBackground: true });
  await b.close(); console.log('ok'); })();
