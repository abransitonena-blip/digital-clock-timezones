// uso: node svg2png.cjs entrada.svg salida.png [ancho_px]
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const [svgf, pngf, ancho] = process.argv.slice(2); const svg = fs.readFileSync(svgf, 'utf8');
  const m = svg.match(/width="([\d.]+)[a-z]*" height="([\d.]+)/); const w = +(ancho || 1400), h = Math.round(w * m[2] / m[1]);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: w, height: h } });
  await p.setContent(`<html><body style="margin:0">${svg.replace(/<svg /, `<svg style="width:${w}px;height:${h}px" `)}</body></html>`);
  await p.screenshot({ path: pngf }); await b.close();
})();
