// Pasa los HTML públicos a PDF tamaño carta. Uso: NODE_PATH=$(npm root -g) node pdf.cjs
const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  for (const n of ['hd_cubo_ap', 'hd_nodo_ap', 'manual_usuario_ap', 'garantia_ap']) {
    await p.goto('file://' + path.join(__dirname, n + '.html')); await p.waitForTimeout(200);
    await p.pdf({ path: path.join(__dirname, n + '.pdf'), format: 'Letter', preferCSSPageSize: true, printBackground: true });
    console.log(n + '.pdf');
  }
  await b.close();
})();
