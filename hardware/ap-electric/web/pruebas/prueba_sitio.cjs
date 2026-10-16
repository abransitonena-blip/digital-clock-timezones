// Pruebas en navegador (Playwright) del constructor de cadena y del panel en vivo de index.html.
const { chromium } = require('playwright');
const path = require('path');
const base = 'file://' + path.resolve(__dirname, '..') + '/';
let fallas = 0;
const ok = (c, m) => { if (!c) { console.log('  falla: ' + m); fallas++; } };
(async () => {
  let b; try { b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' }); } catch (e) { b = await chromium.launch(); }
  const errs = [];
  const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  p.on('pageerror', e => errs.push(String(e)));
  await p.addInitScript(() => { try { localStorage.clear(); } catch (e) {} });
  await p.goto(base + 'index.html'); await p.waitForTimeout(600);
  const nmod = () => p.evaluate(() => window.__ap.estado.mods.length);
  ok(await nmod() === 3, 'cadena: arranca con 3 módulos');
  ok(await p.$$eval('#cCuenta *', e => e.length) > 0, 'cadena: hay totales');
  ok(await p.$$eval('#cMapa tr', e => e.length) === 3, 'cadena: la tabla de direcciones tiene 3 filas');
  const q0 = await p.evaluate(() => window.__ap.mapa().q);
  await p.click('#cPaleta .mod-btn[data-t=rack]'); await p.waitForTimeout(200);
  ok(await nmod() === 4, 'cadena: agregar un Rack 16');
  ok(await p.evaluate(() => window.__ap.mapa().q) === q0 + 16, 'cadena: +16 salidas');
  ok(await p.$$eval('#cMapa tr', e => e.length) === 4, 'cadena: la tabla sigue al cambio');
  await p.click('#cQuitar'); await p.waitForTimeout(200);
  ok(await nmod() === 3, 'cadena: quitar el último');
  // cortar un cable -> alarma
  await p.click('.cable-g >> nth=0'); await p.waitForTimeout(300);
  ok(await p.$eval('.cable-g >> nth=0', e => e.getAttribute('aria-pressed')) === 'true', 'cadena: el cable queda cortado');
  ok((await p.innerText('#hAl')).includes('Faltan'), 'cadena: aviso «Faltan módulos» al cortar');
  await p.click('.cable-g >> nth=0'); await p.waitForTimeout(300);
  ok((await p.innerText('#hAl')).includes('Sin alarmas activas'), 'cadena: al reconectar no quedan alarmas activas');
  // panel: loseta de salida
  await p.click('#hTiles .loseta >> nth=0'); await p.waitForTimeout(200);
  ok(await p.$eval('#hTiles .loseta >> nth=0', e => e.getAttribute('aria-pressed')) === 'true', 'panel: la loseta Q1 enciende');
  // módulo LED8: brillo por salida
  ok(await p.$eval('#hBrilT', e => e.hidden), 'brillo: sin LED8 la tarjeta de brillo no aparece');
  await p.click('#cPaleta .mod-btn[data-t=led8]'); await p.waitForTimeout(300);
  ok(await nmod() === 4 && await p.evaluate(() => window.__ap.mapa().q) === q0 + 8, 'LED8: agrega 8 salidas');
  ok(!(await p.$eval('#hBrilT', e => e.hidden)) && await p.$$eval('#hBril input[type=range]', e => e.length) === 8, 'brillo: aparecen 8 controles');
  const qn = q0 + 1;
  await p.$eval('#hBril input[data-q="' + qn + '"]', e => { e.value = 128; e.dispatchEvent(new Event('input', { bubbles: true })); });
  ok(await p.evaluate(() => window.__ap.estado.mods[3].d[0]) === 128 && (await p.innerText('#hBril')).includes('Q' + qn + ' · 50 %'), 'brillo: el control fija 128 (50 %)');
  await p.click('#cQuitar'); await p.waitForTimeout(300);
  ok(await nmod() === 3 && await p.$eval('#hBrilT', e => e.hidden), 'LED8: al quitarlo desaparece la tarjeta');
  // PLC en RUN
  await p.click('#hRun'); await p.waitForTimeout(800);
  ok(await p.$eval('#hRun', e => e.getAttribute('aria-pressed')) === 'true', 'panel: PLC en RUN');
  ok(await p.$$eval('#hTiles .loseta:disabled', e => e.length) > 0, 'panel: el PLC se queda con sus salidas');
  await p.click('#hRun'); await p.waitForTimeout(300);
  // tema
  const t0 = await p.evaluate(() => document.documentElement.getAttribute('data-theme'));
  await p.click('#tema'); await p.waitForTimeout(150);
  const t1 = await p.evaluate(() => document.documentElement.getAttribute('data-theme'));
  ok(t1 && t1 !== t0, 'tema: el botón cambia el tema');
  // móvil sin desbordamiento horizontal
  await p.setViewportSize({ width: 390, height: 800 }); await p.waitForTimeout(300);
  ok(await p.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), 'móvil: sin desplazamiento horizontal');
  ok(errs.length === 0, 'errores de página: ' + errs.slice(0, 3).join(' | '));
  await b.close();
  console.log(fallas ? 'Sitio: ' + fallas + ' fallas' : 'Sitio: todo bien');
  process.exit(fallas ? 1 : 0);
})();
