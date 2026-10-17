// Pruebas en navegador (Playwright) de la consola AP Base (en demostración) y de la web de la empresa (catálogo y solicitudes).
// Uso: bash tools/probar_web.sh   (requiere Node y Playwright con Chromium)
const { chromium } = require('playwright');
const path = require('path');
const base = 'file://' + path.resolve(__dirname, '..') + '/';
let fallas = 0;
const ok = (c, m) => { if (!c) { console.log('  falla: ' + m); fallas++; } };
const stub = `(function(){const st={},subs=[];
 const mk=p=>({get:async()=>({exists:p in st,data:()=>st[p],id:p.split('/').pop()}),set:async d=>{st[p]=JSON.parse(JSON.stringify(d));fire()},
  update:async d=>{if(!(p in st))throw{code:'invalid_argument'};st[p]=Object.assign({},st[p],JSON.parse(JSON.stringify(d)));fire()},
  onSnapshot:f=>{subs.push([p,f]);setTimeout(fire,0);return()=>{}}});
 function fire(){subs.forEach(([p,f])=>{if(p.split('/').length==2)f({exists:p in st,data:()=>st[p],id:p.split('/')[1]});else f({docs:Object.keys(st).filter(k=>k.startsWith(p+'/')).map(k=>({id:k.split('/')[1],data:()=>st[k]}))})})}
 const db={collection:c=>({doc:i=>mk(c+'/'+i),onSnapshot:f=>{subs.push([c,f]);setTimeout(fire,0);return()=>{}}})};
 window.claude={use:async n=>n=='user'?{canEdit:()=>window.__team===true,id:async()=>'u1',isOwner:()=>false,profiles:async()=>({})}:n=='db'?db:null};window.__store=st})();`;
(async () => {
  let b; try { b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' }); } catch (e) { b = await chromium.launch(); }
  const errs = [];
  const nueva = async (init) => { const p = await b.newPage({ viewport: { width: 1100, height: 900 } }); p.on('pageerror', e => errs.push(String(e))); p.on('dialog', d => d.accept()); if (init) await p.addInitScript(init); return p; };

  // --- consola en demostración: 7R Tour ---
  let p = await nueva();
  await p.goto(base + 'consola.html');
  await p.click('#bD7'); await p.waitForTimeout(700);
  ok(await p.$$eval('#canales .canal', e => e.length) === 7, '7 canales en la demostración 7R');
  ok(await p.$$eval('#entradas .chip', e => e.length) === 8, '8 entradas');
  await p.click('#canales .canal:nth-child(2) button'); await p.waitForTimeout(300);
  ok((await p.$eval('#canales .canal:nth-child(2)', e => e.className)).includes('on'), 'el canal 2 enciende');
  await p.evaluate(() => document.querySelectorAll('details').forEach(d => d.open = true));
  await p.selectOption('#cT4', '1'); await p.selectOption('#cA4', '2'); await p.waitForTimeout(300);
  ok(await p.$eval('#cT4', e => e.value) === '1', 'carga de proceso aplicada');
  ok(await p.$eval('#cA4', e => e.value) === '0', 'un canal de proceso rechaza el arranque encendido (como el firmware)');
  await p.click('#pkBt button[data-c=RESET]'); await p.waitForTimeout(1200);
  await p.click('#pkBt button[data-c=START]');
  await p.waitForFunction(() => document.querySelector('#pkEst') && document.querySelector('#pkEst').innerText.includes('En producción'), null, { timeout: 6000 }).catch(() => {});
  ok((await p.innerText('#pkEst')).includes('En producción'), 'PackML llega a En producción');
  await p.click('#perfiles button:first-child'); await p.waitForTimeout(500);
  ok((await p.$$eval('#pkEnt select', s => s.map(x => x.value))).join() === '1,2,3,4', 'perfil Andon aplica las entradas');
  await p.fill('#iCmd', 'PK HOLD'); await p.click('#bCmd'); await p.waitForTimeout(300);
  ok((await p.innerText('#pkEst')).includes('Reteniendo') || (await p.innerText('#pkEst')).includes('Retenida'), 'HOLD acepta');
  const bk = await p.evaluate(() => respaldo()); ok(/GUARDAR/.test(bk) && /PK CICLO/.test(bk) && !/NaN/.test(bk), 'respaldo sin NaN');
  ok(await p.$eval('#bTestR', e => !e.hidden), 'prueba de relés visible con origen local');
  await p.click('#bSalir');
  // --- Home: sin secciones que no existen ---
  await p.click('#bDH'); await p.waitForTimeout(600);
  ok(await p.$$eval('#canales .canal', e => e.length) === 1, 'AP Home: 1 canal');
  ok(await p.$eval('#mbOk', e => e.classList.contains('hidden')), 'AP Home: sin RS-485');
  // --- red en https: se explica ---
  await p.click('#bSalir');
  await p.close();

  // --- web de la empresa, sin base de datos: NO debe prometer que la solicitud llegó ---
  p = await nueva();
  await p.goto(base + 'index.html');
  ok(await p.$$eval('#catLista .item', e => e.length) >= 10, 'catálogo con filas');
  await p.click('#catFiltros button:nth-child(2)');
  ok(await p.$$eval('#catLista .item', e => e.every(x => x.innerText.includes('Industrial'))), 'filtro Industrial');
  await p.click('#catLista .item:first-child button.btn');
  await p.fill('#q_ap-monitor-24', '7'); await p.dispatchEvent('#q_ap-monitor-24', 'change');
  await p.click('#catFiltros button:nth-child(1)'); await p.click('#catLista .item:nth-child(2) button.btn');
  ok(await p.$eval('#q_ap-monitor-24', e => e.value) === '7', 'la cantidad se conserva al agregar otro producto');
  await p.fill('#sCon', 'x@y.mx'); await p.fill('#sMsg', 'Inyectora sin PLC con sensor PNP');
  await p.click('#formSol button[type=submit]');
  ok((await p.innerText('#sMsgEst')).includes('prototipo'), 'exige aceptar el aviso de prototipo');
  await p.click('#sAcepto'); await p.click('#formSol button[type=submit]'); await p.waitForTimeout(300);
  ok((await p.innerText('#sMsgEst')).includes('NO SE ENVIÓ'), 'sin base de datos avisa que NO se envió');
  ok(!/AP-\d{6}-/.test(await p.innerText('#sConf')), 'sin base de datos no entrega folio');
  ok(await p.evaluate(() => { try { return !localStorage.getItem('apSolicitudes'); } catch (e) { return true; } }), 'no guarda el contacto en el navegador');
  ok(await p.$eval('#sMsg', e => e.value.length > 0), 'conserva lo escrito para no perderlo');
  await p.close();

  // --- con base de datos simulada: envío, doble envío, confirmación del equipo, datos malformados, límite ---
  p = await nueva('window.__team=true;' + stub);
  await p.goto(base + 'index.html'); await p.waitForTimeout(400);
  await p.selectOption('#sTipo', 'Lista de interés'); await p.fill('#sMsg', 'Avísenme cuando haya prototipos'); await p.click('#sAcepto');
  await p.evaluate(() => { const f = document.getElementById('formSol'); f.requestSubmit(); f.requestSubmit(); });   // doble envío
  await p.waitForTimeout(500);
  ok(await p.evaluate(() => (window.__store['solicitudes/u1'] || { pedidos: [] }).pedidos.length) === 1, 'el doble envío crea una sola solicitud');
  ok(/AP-\d{6}-[A-Z0-9]{6}/.test(await p.innerText('#sConf')), 'folio generado con base de datos');
  ok((await p.innerText('#sConf')).includes('no se cobra nada'), 'confirmación aclara que no es compra');
  ok(await p.$eval('#sEquipo', e => !e.hidden), 'panel del equipo visible');
  await p.selectOption('#sLista tr:first-child select', 'En revisión'); await p.waitForTimeout(500);
  ok(await p.evaluate(() => JSON.stringify(window.__store['confirmaciones/u1'] || {}).includes('En revisión')), 'confirmación guardada por el equipo');
  ok((await p.innerText('#sMias')).includes('En revisión'), 'el solicitante ve el nuevo estado');
  // un documento malformado de otra cuenta no debe vaciar el panel del equipo
  await p.evaluate(() => { window.__store['solicitudes/evil'] = { pedidos: 'basura' }; window.__store['interes/evil'] = { productos: 'x' }; });
  await p.evaluate(() => { const f = document.getElementById('formSol'); });
  await p.selectOption('#sTipo', 'Lista de interés'); await p.fill('#sMsg', 'Otra solicitud de prueba'); await p.click('#sAcepto');
  await p.click('#formSol button[type=submit]'); await p.waitForTimeout(500);
  ok(await p.$$eval('#sLista tr', e => e.length) >= 2, 'el panel del equipo sigue mostrando solicitudes con un documento malformado');
  // límite de 20: avisa en vez de borrar en silencio
  for (let i = 0; i < 22; i++) {
    await p.selectOption('#sTipo', 'Lista de interés'); await p.fill('#sMsg', 'Solicitud número ' + i + ' de prueba'); await p.check('#sAcepto');
    await p.click('#formSol button[type=submit]'); await p.waitForTimeout(120);
  }
  ok(await p.evaluate(() => window.__store['solicitudes/u1'].pedidos.length) === 20, 'el límite de 20 no descarta solicitudes: se detiene');
  ok((await p.innerText('#sMsgEst')).includes('20 solicitudes'), 'avisa que se llegó al límite');
  await p.close();

  // --- consola: el perfil Andon no se ofrece en AP Home; la clave de red se pide al mandar órdenes ---
  p = await nueva();
  await p.goto(base + 'consola.html'); await p.click('#bDH'); await p.waitForTimeout(500);
  ok((await p.$$eval('#perfiles button', b => b.map(x => x.textContent))).every(t => !/Andon/.test(t)), 'AP Home no ofrece el perfil Andon (1 entrada)');
  await p.close();

  // --- gestos del pulsador (AP Home) ---
  p = await nueva();
  await p.goto(base + 'consola.html'); await p.click('#bDH'); await p.waitForTimeout(500);
  await p.evaluate(() => document.querySelectorAll('details').forEach(d => d.open = true));
  ok(await p.$eval('#eD1', e => e.disabled), 'gestos: doble toque deshabilitado mientras el modo no es gestos');
  await p.selectOption('#eM1', '4'); await p.waitForTimeout(400);
  ok(!(await p.$eval('#eD1', e => e.disabled)), 'gestos: con el modo 4 se habilita el doble toque');
  await p.selectOption('#eD1', '3'); await p.selectOption('#eL1', '2'); await p.waitForTimeout(400);
  ok(await p.$eval('#eD1', e => e.value) === '3' && await p.$eval('#eL1', e => e.value) === '2', 'gestos: doble = apagar todo, largo = apagar');
  await p.selectOption('#eM1', '0'); await p.waitForTimeout(400);
  ok(await p.$eval('#eD1', e => e.value) === '0', 'gestos: al salir del modo gestos las acciones se borran');
  await p.close();

  // --- consola en demostración: AP Rack, cadena de módulos ---
  p = await nueva();
  await p.goto(base + 'consola.html');
  await p.click('#bDR'); await p.waitForTimeout(700);
  ok(await p.$$eval('#mods > .card', e => e.length) === 2, 'rack demo: aparecen 2 módulos');
  ok((await p.innerText('#cadena')).includes('Módulo 1') && (await p.innerText('#cadena')).includes('Módulo 2'), 'rack demo: la cadena nombra los 2 módulos');
  ok(await p.$$eval('#mods .sal', e => e.length) === 32, 'rack demo: 32 salidas');
  ok(await p.$eval('#sSalidas', e => e.classList.contains('hidden')), 'rack demo: se oculta el panel de 7 canales');
  await p.click('#mods .sal[data-ch="17"]'); await p.waitForTimeout(400);
  ok(await p.$eval('#mods .sal[data-ch="17"]', e => e.classList.contains('on')), 'rack demo: el canal 17 (módulo 2, salida 1) enciende');
  ok(await p.$eval('#mods .card[data-p="1"] .sal[data-ch="1"]', e => !e.classList.contains('on')), 'rack demo: el módulo 1 no cambia');
  await p.fill('#iCmd', 'DEMO +'); await p.click('#bCmd'); await p.waitForTimeout(500);
  ok(await p.$$eval('#mods > .card', e => e.length) === 3, 'rack demo: al conectar otro módulo aparece el tercero');
  ok(await p.$$eval('#mods .sal', e => e.length) === 48, 'rack demo: 48 salidas con 3 módulos');
  await p.fill('#iCmd', 'DEMO + AI8'); await p.click('#bCmd'); await p.waitForTimeout(400);
  ok(await p.$$eval('#mods > .card', e => e.length) === 4 && (await p.innerText('#mods')).includes('AP Rack AI8') && /A1 · \d/.test(await p.innerText('#mods')), 'rack demo: un módulo AI8 muestra sus entradas analógicas');
  ok(await p.$$eval('#mods .sal', e => e.length) === 48, 'rack demo: el AI8 no suma salidas');
  await p.fill('#iCmd', 'DEMO + RL4'); await p.click('#bCmd'); await p.waitForTimeout(400);
  ok(await p.$$eval('#mods > .card', e => e.length) === 5 && (await p.innerText('#mods')).includes('AP Rack RL4') && await p.$$eval('#mods .sal', e => e.length) === 52, 'rack demo: un módulo RL4 suma 4 salidas');
  await p.click('#mods .btn:has-text("Apagar este módulo") >> nth=-1'); await p.waitForTimeout(300);
  await p.fill('#iCmd', 'DEMO - '); await p.click('#bCmd'); await p.waitForTimeout(400);
  ok(await p.$$eval('#mods > .card', e => e.length) === 4, 'rack demo: se quita el RL4');
  await p.fill('#iCmd', 'DEMO + AO4'); await p.click('#bCmd'); await p.waitForTimeout(400);
  ok(await p.$$eval('#mods > .card', e => e.length) === 5 && (await p.innerText('#mods')).includes('AP Rack AO4') && await p.$$eval('#mods input.brillo', e => e.length) === 4, 'rack demo: un módulo AO4 trae 4 controles de nivel');
  await p.fill('#iCmd', 'DEMO - '); await p.click('#bCmd'); await p.waitForTimeout(400);
  await p.fill('#iCmd', 'DEMO + LED8'); await p.click('#bCmd'); await p.waitForTimeout(400);
  ok(await p.$$eval('#mods > .card', e => e.length) === 5 && (await p.innerText('#mods')).includes('AP Rack LED8'), 'rack demo: un módulo LED8 aparece');
  ok(await p.$$eval('#mods .sal', e => e.length) === 56 && await p.$$eval('#mods input.brillo', e => e.length) === 8, 'rack demo: el LED8 suma 8 salidas y trae 8 controles de brillo');
  await p.click('#mods .sal[data-ch="50"]'); await p.waitForTimeout(500);
  ok(await p.$eval('#mods .sal[data-ch="50"]', e => e.classList.contains('on')), 'rack demo: la salida 50 (LED8, salida 2) se enciende');
  await p.$eval('#mods input.brillo[data-ch="49"]', (e) => { e.value = 64; e.dispatchEvent(new Event('input', { bubbles: true })); e.dispatchEvent(new Event('change', { bubbles: true })); }); await p.waitForTimeout(1300);
  ok(await p.$eval('#mods input.brillo[data-ch="49"]', e => e.value) === '64' && (await p.innerText('#mods')).includes('Q49 · 25 %'), 'rack demo: el brillo 64 llega (25 %) y vuelve en el JSON');
  await p.fill('#iCmd', 'C 99 1'); await p.click('#bCmd'); await p.waitForTimeout(400);
  ok((await p.innerText('#mAcc')).includes('rechaz'), 'rack demo: un canal inexistente se rechaza');
  await p.click('text=Apagar TODAS las salidas de la cadena'); await p.waitForTimeout(400);
  ok(await p.$$eval('#mods .sal.on', e => e.length) === 0, 'rack demo: apagar todas');
  await p.close();

  // --- prueba de CONTRATO: la consola frente a un puerto serie falso que contesta con el JSON REAL del firmware (extraído de APControl.ino) ---
  const fs = require('fs');
  if (fs.existsSync('/tmp/json_7r.txt')) {
    const real = fs.readFileSync('/tmp/json_7r.txt', 'utf8').trim();
    const falso = `(function(){
      const enc=new TextEncoder(),dec=new TextDecoder();let ctl,buf='';window.__rx=[];
      const port={open:async()=>{},close:async()=>{},
        readable:new ReadableStream({start(c){ctl=c;c.enqueue(enc.encode('ets Jun  8 2016 00:22:57\\r\\nrst:0x1 (POWERON),boot:0x8\\r\\n'))}}),
        writable:new WritableStream({write(chunk){buf+=dec.decode(chunk);let i;while((i=buf.indexOf('\\n'))>=0){const l=buf.slice(0,i).trim();buf=buf.slice(i+1);window.__rx.push(l);
          const ok=l==='?'||/^(C|A|T|P|X|E|MB|PK)\\b/i.test(l)||l==='GUARDAR';ctl.enqueue(enc.encode((ok?window.__json:'?')+'\\r\\n'))}}})};
      window.__json=${JSON.stringify(real)};
      Object.defineProperty(navigator,'serial',{value:{requestPort:async()=>port},configurable:true});})();`;
    p = await nueva(falso);
    await p.goto(base + 'consola.html'); await p.click('#bUsb'); await p.waitForTimeout(1500);
    ok(await p.$$eval('#canales .canal', e => e.length) === 7, 'contrato: la consola dibuja 7 canales con el JSON real del firmware');
    ok(await p.$$eval('#entradas .chip', e => e.length) === 8, 'contrato: 8 entradas');
    ok((await p.innerText('#eqInfo')).includes('7R Tour'), 'contrato: reconoce la placa');
    await p.click('#canales .canal:nth-child(1) button'); await p.waitForTimeout(500);
    ok(await p.evaluate(() => window.__rx.includes('C 1 2')), 'contrato: la orden de alternar llega como «C 1 2»');
    ok(await p.$eval('#cEstado', e => /USB/.test(e.textContent)), 'contrato: el chip dice USB');
    await p.close();
  } else console.log('  (contrato omitido: falta /tmp/json_7r.txt; corre antes tools/probar_apbus.sh)');

  // contrato del AP Rack: la consola frente a un puerto serie falso con el JSON REAL de APRack (ap_rack.h, 2 módulos)
  if (fs.existsSync('/tmp/json_rack_2mod.txt')) {
    const real = fs.readFileSync('/tmp/json_rack_2mod.txt', 'utf8').trim();
    const falso = `(function(){
      const enc=new TextEncoder(),dec=new TextDecoder();let ctl,buf='';window.__rx=[];
      const port={open:async()=>{},close:async()=>{},
        readable:new ReadableStream({start(c){ctl=c}}),
        writable:new WritableStream({write(chunk){buf+=dec.decode(chunk);let i;while((i=buf.indexOf('\\n'))>=0){const l=buf.slice(0,i).trim();buf=buf.slice(i+1);window.__rx.push(l);
          const ok=l==='?'||/^(C|A|M|S)\\b/i.test(l)||l==='GUARDAR';ctl.enqueue(enc.encode((ok?window.__json:'?')+'\\r\\n'))}}})};
      window.__json=${JSON.stringify(real)};
      Object.defineProperty(navigator,'serial',{value:{requestPort:async()=>port},configurable:true});})();`;
    p = await nueva(falso);
    await p.goto(base + 'consola.html'); await p.click('#bUsb'); await p.waitForTimeout(1500);
    ok(await p.$$eval('#mods > .card', e => e.length) === 2, 'contrato rack: 2 módulos con el JSON real del firmware');
    ok(await p.$$eval('#mods .sal', e => e.length) === 32, 'contrato rack: 32 salidas');
    ok(await p.$$eval('#mods .card[data-p="2"] .sal.on', e => e.length) === 4, 'contrato rack: el módulo 2 trae 4 salidas encendidas (0x00F0)');
    await p.click('#mods .sal[data-ch="20"]'); await p.waitForTimeout(500);
    ok(await p.evaluate(() => window.__rx.includes('C 20 2')), 'contrato rack: la orden llega como «C 20 2»');
    ok((await p.innerText('#eqInfo')).includes('AP Rack 16'), 'contrato rack: reconoce la placa');
    await p.close();
  } else console.log('  (contrato rack omitido: falta /tmp/json_rack_2mod.txt)');

  ok(errs.length === 0, 'errores de página: ' + errs.slice(0, 3).join(' | '));
  await b.close();
  console.log(fallas ? 'Web: ' + fallas + ' fallas' : 'Web y consola: todo bien');
  process.exit(fallas ? 1 : 0);
})();
