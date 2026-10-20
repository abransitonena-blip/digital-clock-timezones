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
  await p.click('#cPaleta .mod-btn[data-t=plc]'); await p.waitForTimeout(200);
  ok(await nmod() === 4 && await p.evaluate(() => window.__ap.mapa().q) === q0 + 12, 'cadena: agregar un AP PLC C24 suma 12 salidas');
  await p.click('#cQuitar'); await p.waitForTimeout(200);
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
  await p.click('#cPaleta .mod-btn[data-t=ao4]'); await p.waitForTimeout(300);
  ok(await p.$$eval('#hBril input[type=range]', e => e.length) === 4, 'AO4: cuatro controles de nivel');
  await p.click('#cQuitar'); await p.waitForTimeout(300);
  // PLC en RUN
  await p.click('#hRun'); await p.waitForTimeout(800);
  ok(await p.$eval('#hRun', e => e.getAttribute('aria-pressed')) === 'true', 'panel: PLC en RUN');
  ok(await p.$$eval('#hTiles .loseta:disabled', e => e.length) > 0, 'panel: el PLC se queda con sus salidas');
  await p.click('#hRun'); await p.waitForTimeout(300);
  // visor 3D: cinco placas; sin red (prueba en archivo) debe quedarse con el render fijo sin errores
  ok(await p.$$eval('#mTabs button', e => e.length) === 14, '3D: siete placas, la caja, la placa con su cable y cinco piezas más para elegir');
  await p.evaluate(() => document.getElementById('modelos').scrollIntoView()); await p.waitForTimeout(1500);
  ok((await p.innerText('#mNota')).includes('render fijo') || await p.evaluate(() => !!window.__visor), '3D: o carga el modelo o muestra el render fijo');
  await p.click('#mTabs button[data-m=rl4]'); await p.waitForTimeout(600);
  ok((await p.innerText('#mTitulo')).includes('AP Rack RL4'), '3D: elegir RL4 cambia el título');
  // materiales y diseño generativo
  ok(await p.$$eval('#materiales .tabla-mat tbody tr', e => e.length) === 11, 'materiales: once filas en la tabla');
  ok((await p.innerText('#materiales .tabla-mat')).includes('AgSnO2') && (await p.innerText('#materiales .tabla-mat')).includes('CuCrZr'), 'materiales: contactos de plata y cobre de alta resistencia en la tabla');
  ok((await p.innerText('#materiales')).includes('Límites') && (await p.innerText('#materiales')).includes('Nada está impreso'), 'materiales: dice los límites');
  // acabados: siete, cambian la imagen y el nombre
  ok(await p.$$eval('#aTabs button', e => e.length) === 7, 'acabados: siete para elegir');
  await p.click('#aTabs button[data-a=fibra_carbono]'); await p.waitForTimeout(200);
  ok((await p.getAttribute('#aImg', 'src')).includes('acabado_fibra_carbono') && (await p.innerText('#aNombre')).includes('carbono'), 'acabados: elegir carbono cambia la imagen y el nombre');
  ok(await p.$$eval('#acabados .formatos-img figure', e => e.length) === 4, 'acabados: cuatro formatos de imagen');
  ok(await p.$$eval('#portada h1, #nosotros h2, #dos-mundos .mundo, #electronica-plc h2, #contacto-marca h2', e => e.length) === 6, 'marca: portada, historia, dos mundos, electrónica PLC y contacto');
  ok(await p.$$eval('#portada img, #nosotros img, #dos-mundos img, #electronica-plc img', es => Promise.all(es.map(i => { i.loading = 'eager'; return i.complete ? i.naturalWidth > 0 : new Promise(r => { i.onload = () => r(true); i.onerror = () => r(false); }); }))).then(a => a.every(Boolean)), 'marca: todas las imágenes cargan');
  await p.click('details.mas summary'); ok(await p.$eval('details.mas', e => e.open), 'menú: Ingeniería se abre');
  await p.click('.mas-p a[href="#cadena"]'); ok(!(await p.$eval('details.mas', e => e.open)), 'menú: se cierra al elegir una sección');
  ok(await p.$$eval('#preguntas details', e => e.length) === 5 && await p.$$eval('#como-trabajamos .pasos > div', e => e.length) === 4, 'marca: cuatro pasos y cinco preguntas');
  ok(await p.$$eval('#home .producto', e => e.length) === 3, 'home: Plug, Switch y la versión en dos piezas');
  ok(await p.$$eval('#rustico .rustico-gal img', e => e.length) === 6, 'rústico: seis fotos del taller');
  ok(await p.$$eval('#rustico img', es => Promise.all(es.map(i => i.complete ? i.naturalWidth > 0 : new Promise(r => { i.onload = () => r(true); i.onerror = () => r(false); i.loading = 'eager'; })))).then(a => a.every(Boolean)), 'rústico: las fotos cargan');
  await p.click('#mTabs button[data-m=caja]'); await p.waitForTimeout(500);
  ok(await p.$$eval('#mAcabTabs button', e => e.length) === 7, '3D: siete acabados para la caja en el visor');
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
