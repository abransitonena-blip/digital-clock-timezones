const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  await p.setContent(fs.readFileSync('fichas.html', 'utf8'));
  await p.pdf({ path: 'fichas_componentes.pdf', format: 'Letter', printBackground: true, preferCSSPageSize: true });
  await b.close(); console.log('ok');
})();
