// Pasa manual.html a manual_regulador_12v_2a.pdf (carta).
const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + __dirname + '/manual.html');
  await p.pdf({ path: __dirname + '/manual_regulador_12v_2a.pdf', format: 'Letter', preferCSSPageSize: true, printBackground: true });
  await b.close(); console.log('ok'); })();
