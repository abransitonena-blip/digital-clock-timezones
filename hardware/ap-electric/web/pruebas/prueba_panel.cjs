// Pruebas en navegador (Playwright) del Panel AP: demostración, diseñador, consignas, alarmas y contrato con el JSON real del firmware.
const { chromium } = require('playwright');
const path = require('path'); const fs = require('fs');
const base = 'file://' + path.resolve(__dirname, '..') + '/';
let fallas = 0;
const ok = (c, m) => { if (!c) { console.log('  falla: ' + m); fallas++; } };
(async () => {
  let b; try { b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' }); } catch (e) { b = await chromium.launch(); }
  const errs = [];
  const nueva = async (init) => { const p = await b.newPage({ viewport: { width: 1200, height: 900 } }); p.on('pageerror', e => errs.push(String(e))); p.on('dialog', d => d.accept('Prueba')); if (init) await p.addInitScript(init); return p; };

  let p = await nueva();
  await p.goto(base + 'panel.html');
  await p.evaluate(() => { try { localStorage.clear(); } catch (e) {} });
  await p.click('#bDemo'); await p.waitForTimeout(800);
  ok(await p.$$eval('#tabs .tab', e => e.length) === 2, 'panel: 2 páginas de ejemplo');
  ok(await p.$$eval('#lienzo .w', e => e.length) >= 12, 'panel: el ejemplo trae los elementos');
  ok((await p.innerText('.w-modulos')).includes('M1') && (await p.innerText('.w-modulos')).includes('M3'), 'panel: el widget de módulos lista los 3 módulos de la cadena');
  ok((await p.innerText('.w-modulos')).includes('AI8') && (await p.innerText('.w-modulos')).includes('IN16'), 'panel: reconoce los tipos de módulo');
  // botón de salida: Q1 alterna
  await p.click('.w-boton:has-text("Bomba")'); await p.waitForTimeout(500);
  ok(await p.$eval('.w-boton:has-text("Bomba")', e => e.classList.contains('on')), 'panel: el botón Bomba enciende Q1');
  ok(await p.$eval('.w-boton:has-text("Bomba")', e => e.getAttribute('aria-pressed')) === 'true', 'panel: aria-pressed');
  await p.click('.w-boton:has-text("Ventilador")'); await p.waitForTimeout(500);   // pide confirmación (la prueba acepta)
  ok(await p.$eval('.w-boton:has-text("Ventilador")', e => e.classList.contains('on')), 'panel: botón con confirmación');
  // valor analógico del módulo AI8 (A1) y su barra
  ok(/\d/.test(await p.innerText('.w-valor:has-text("Presión") .v')), 'panel: la presión analógica muestra un número');
  ok(await p.$eval('.w-valor:has-text("Presión") .barra i', e => parseFloat(e.style.width) > 0), 'panel: barra con valor');
  // consigna: R1
  await p.fill('.w-consigna input', '7.5'); await p.press('.w-consigna input', 'Enter'); await p.waitForTimeout(500);
  ok((await p.innerText('.w-consigna .v')).startsWith('7.5'), 'panel: la consigna R1 = 7.5 llega al equipo y vuelve');
  // interruptor de marca M5
  await p.click('.w-marca'); await p.waitForTimeout(500);
  ok(await p.$eval('.w-marca', e => e.getAttribute('aria-checked')) === 'true', 'panel: la marca M5 se enciende');
  // PLC: cargar programa, RUN
  ok(await p.$eval('#sPrograma', e => !e.classList.contains('hidden')), 'panel: aparece el programa PLC');
  await p.fill('#tPlc', 'LD I9\nOUT Q1\nLD A1 > 6\nOUT Q4'); await p.click('#bPlcCargar'); await p.waitForTimeout(500);
  await p.click('#bPlcRun'); await p.waitForTimeout(500);
  ok((await p.innerText('#cPlc')).startsWith('RUN'), 'panel: PLC en RUN');
  ok((await p.innerText('.w-plc')).includes('RUN'), 'panel: el widget PLC dice RUN');
  await p.fill('#tPlc', 'OUT Q1'); await p.click('#bPlcCargar'); await p.waitForTimeout(500);
  ok((await p.innerText('#mPlc')).includes('rechaz') || (await p.innerText('#cPlc')).includes('renglon'), 'panel: un programa con error se rechaza y se muestra');
  // diseñador
  await p.click('#bEditar'); await p.waitForTimeout(300);
  ok(await p.$eval('#lateral', e => !e.classList.contains('hidden')), 'diseñador: aparece la barra lateral');
  const n0 = await p.$$eval('#lienzo .w', e => e.length);
  await p.click('#paleta button[data-tipo="luz"]'); await p.waitForTimeout(300);
  ok(await p.$$eval('#lienzo .w', e => e.length) === n0 + 1, 'diseñador: agregar una luz');
  await p.fill('#pp_ref', 'I2'); await p.press('#pp_ref', 'Tab'); await p.fill('#pp_etq', 'Entrada 2'); await p.press('#pp_etq', 'Tab'); await p.waitForTimeout(300);
  ok((await p.innerText('.w.sel')).includes('Entrada 2'), 'diseñador: la etiqueta se edita');
  // mover con el ratón
  const w0 = await p.$eval('.w.sel', e => e.style.gridColumn);
  const box = await p.$eval('.w.sel', e => { const r = e.getBoundingClientRect(); return { x: r.x + 30, y: r.y + 20 }; });
  await p.mouse.move(box.x, box.y); await p.mouse.down(); await p.mouse.move(box.x + 300, box.y + 90, { steps: 8 }); await p.mouse.up(); await p.waitForTimeout(300);
  ok(await p.$eval('.w.sel', e => e.style.gridColumn) !== w0, 'diseñador: arrastrar mueve el elemento');
  await p.fill('#pp_w', '99'); await p.press('#pp_w', 'Tab'); await p.waitForTimeout(200);
  ok((await p.$eval('#pp_w', e => +e.value)) <= 12, 'diseñador: el ancho se limita a la cuadrícula');
  await p.click('#bBorrarW'); await p.waitForTimeout(300);
  ok(await p.$$eval('#lienzo .w', e => e.length) === n0, 'diseñador: borrar el elemento');
  // exportar e importar
  await p.click('#bExp'); const js = await p.$eval('#tJson', e => e.value);
  ok(JSON.parse(js).paginas.length === 2, 'diseñador: exportar trae las páginas');
  await p.fill('#tJson', '{"v":1,"paginas":[{"nombre":"x","widgets":[{"tipo":"hackeado","x":1,"y":1,"w":1,"h":1}]}]}'); await p.click('#bImp'); await p.waitForTimeout(300);
  ok((await p.innerText('#mDis')).includes('No se pudo importar'), 'diseñador: un diseño con tipo desconocido se rechaza');
  await p.fill('#tJson', '{"v":1,"nombre":"mío","paginas":[{"id":"z","nombre":"Mi página","widgets":[{"id":"q","tipo":"boton","x":1,"y":1,"w":2,"h":1,"etq":"<img src=x onerror=window.__xss=1>","ref":"Q2"}]}]}');
  await p.click('#bImp'); await p.waitForTimeout(300);
  ok(await p.$$eval('#tabs .tab', e => e.length) === 1 && await p.evaluate(() => !window.__xss), 'diseñador: importar funciona y el texto no ejecuta código');
  await p.click('#bEditar');
  // el diseño se recuerda al recargar
  await p.reload(); await p.click('#bDemo'); await p.waitForTimeout(600);
  ok((await p.innerText('#tabs')).includes('Mi página'), 'diseñador: el diseño se recuerda en el navegador');
  await p.close();

  // móvil: 6 columnas y sin desborde horizontal
  p = await nueva(); await p.setViewportSize({ width: 390, height: 800 });
  await p.goto(base + 'panel.html'); await p.evaluate(() => { try { localStorage.clear(); } catch (e) {} }); await p.reload(); await p.click('#bDemo'); await p.waitForTimeout(600);
  ok(await p.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 2), 'móvil: sin desborde horizontal');
  await p.close();

  // contrato: el panel frente al JSON REAL de AP Rack (2 módulos y con PLC)
  for (const [ruta, mods] of [['/tmp/json_rack_2mod.txt', 2], ['/tmp/json_rack_plc.txt', 3]]) {
    if (!fs.existsSync(ruta)) { console.log('  (contrato omitido: falta ' + ruta + ')'); continue; }
    const real = fs.readFileSync(ruta, 'utf8').trim();
    const falso = `(function(){const enc=new TextEncoder(),dec=new TextDecoder();let ctl,buf='';window.__rx=[];
      const port={open:async()=>{},close:async()=>{},readable:new ReadableStream({start(c){ctl=c}}),
      writable:new WritableStream({write(chunk){buf+=dec.decode(chunk);let i;while((i=buf.indexOf('\\n'))>=0){const l=buf.slice(0,i).trim();buf=buf.slice(i+1);window.__rx.push(l);ctl.enqueue(enc.encode(window.__json+'\\r\\n'))}}})};
      window.__json=${JSON.stringify(real)};Object.defineProperty(navigator,'serial',{value:{requestPort:async()=>port},configurable:true});})();`;
    p = await nueva(falso); await p.goto(base + 'panel.html'); await p.evaluate(() => { try { localStorage.clear(); } catch (e) {} }); await p.reload();
    await p.click('#bUsb'); await p.waitForTimeout(1500);
    ok((await p.innerText('.w-modulos')).includes('M' + mods), 'contrato ' + ruta + ': el panel lista ' + mods + ' módulos con el JSON real');
    await p.click('.w-boton:has-text("Bomba")'); await p.waitForTimeout(400);
    ok(await p.evaluate(() => window.__rx.includes('C 1 2')), 'contrato ' + ruta + ': el botón manda «C 1 2»');
    await p.close();
  }
  ok(errs.length === 0, 'errores de página: ' + errs.slice(0, 3).join(' | '));
  await b.close();
  console.log(fallas ? 'Panel: ' + fallas + ' fallas' : 'Panel AP: todo bien');
  process.exit(fallas ? 1 : 0);
})();
