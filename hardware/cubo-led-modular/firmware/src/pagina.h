// Generado por gen_pagina.py desde app/index.html. No editar a mano.
#pragma once
#include <pgmspace.h>
static const char PAGINA_HTML[] PROGMEM = R"PAGINA(<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#0b5d36">
<title>Cubo AP</title>
<style>
:root{--bg:#f3f5f4;--card:#fff;--tx:#131917;--mut:#5b6762;--ln:#dbe2de;--ac:#0b7d55;--ac2:#e3f3ec;--bad:#c0392b;--warn:#b7791f}
@media (prefers-color-scheme:dark){:root{--bg:#0d1311;--card:#151d1a;--tx:#e6eeea;--mut:#93a39c;--ln:#26322d;--ac:#2fc28f;--ac2:#12302a;--bad:#ff6b5b;--warn:#f0b44c}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.4 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:540px;margin:0 auto;padding:16px}
header{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:4px 0 14px;flex-wrap:wrap}
h1{font-size:20px;margin:0}h1 b{color:var(--ac)}
h2{font-size:14px;margin:0 0 8px;color:var(--mut);font-weight:600;text-transform:uppercase;letter-spacing:.06em}
.sub{color:var(--mut);font-size:13px}
.card{background:var(--card);border:1px solid var(--ln);border-radius:14px;padding:14px;margin-bottom:12px}
.row{display:flex;align-items:center;justify-content:space-between;gap:10px}
button,select,input[type=text],input[type=password],input[type=number],input[type=time]{font:inherit;border:1px solid var(--ln);background:var(--card);color:var(--tx);border-radius:10px;padding:8px 12px}
button{cursor:pointer}button.pri{background:var(--ac);border-color:var(--ac);color:#fff;font-weight:600}
button:disabled{opacity:.45;cursor:default}
.power{width:62px;height:62px;border-radius:50%;font-size:26px;display:grid;place-items:center;padding:0}
.power.on{background:var(--ac);color:#fff;border-color:var(--ac)}
.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:12px}
.m{background:var(--bg);border-radius:10px;padding:8px;text-align:center}
.m b{display:block;font-size:18px;font-variant-numeric:tabular-nums}.m span{font-size:11px;color:var(--mut)}
label{display:block;font-size:13px;color:var(--mut);margin:10px 0 4px}
input[type=range]{width:100%;accent-color:var(--ac)}
.val{font-variant-numeric:tabular-nums;font-weight:600}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chips button{padding:6px 11px;font-size:13px}
.chips button.sel{background:var(--ac2);border-color:var(--ac);color:var(--ac);font-weight:600}
.sw{display:flex;gap:6px;margin-top:8px}.sw i{flex:1;height:28px;border-radius:8px;border:1px solid var(--ln);cursor:pointer}
.estado{font-size:13px;padding:8px 10px;border-radius:10px;background:var(--ac2);color:var(--ac);margin-top:10px}
.estado.bad{background:color-mix(in srgb,var(--bad) 14%,transparent);color:var(--bad)}
.lim{font-size:12px;color:var(--mut);margin-top:4px}
.bar{height:6px;border-radius:3px;background:var(--bg);overflow:hidden;margin-top:6px}
.bar i{display:block;height:100%;background:var(--ac);width:0;transition:width .3s}.bar i.hot{background:var(--warn)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.cct{height:10px;border-radius:5px;background:linear-gradient(90deg,#ffb15e,#fff3e0,#cfe3ff);margin-top:4px}
.hide{display:none!important}
footer{color:var(--mut);font-size:12px;text-align:center;margin:16px 0}
</style>
</head>
<body>
<main>
  <header>
    <div><h1>Cubo <b>AP</b></h1><div class="sub" id="dev">Sin conectar</div></div>
    <div class="row">
      <button id="demo">Demo</button>
      <button class="pri" id="con">Bluetooth</button>
    </div>
  </header>

  <section class="card">
    <div class="row">
      <div>
        <div class="sub">Tarjeta</div>
        <div style="font-size:22px;font-weight:700" id="perfil">—</div>
        <div class="lim" id="lims">Conecta por Bluetooth, Wi-Fi o prueba la demo</div>
      </div>
      <button class="power" id="pwr" disabled title="Encender / apagar">⏻</button>
    </div>
    <div class="metrics">
      <div class="m"><b id="mv">–</b><span>V salida</span></div>
      <div class="m"><b id="mi">–</b><span>A</span></div>
      <div class="m"><b id="mw">–</b><span>W</span></div>
      <div class="m"><b id="mt">–</b><span>°C</span></div>
    </div>
    <div class="bar" title="Corriente respecto al límite de la tarjeta"><i id="carga"></i></div>
    <div class="estado" id="est">Listo</div>
  </section>

  <section class="card">
    <div class="row"><h2 style="margin:0">Luz</h2><label style="margin:0;display:flex;gap:6px;align-items:center"><input type="checkbox" id="todos"> Aplicar a todo el grupo</label></div>
    <div class="row"><label style="margin:0">Brillo</label><span class="val" id="bv">60 %</span></div>
    <input type="range" id="brillo" min="0" max="100" value="60">
    <label>Efecto</label>
    <div class="chips" id="modos">
      <button data-m="FIJO" class="sel">Fijo</button><button data-m="RESPIRA">Respira</button>
      <button data-m="ARCOIRIS">Arcoíris</button><button data-m="FUEGO">Fuego</button><button data-m="COMETA">Cometa</button>
    </div>
    <div id="bloqueColor">
      <label>Color</label>
      <div class="row"><input type="color" id="col" value="#ffffff" style="width:56px;height:36px;border:0;background:none;padding:0"><span class="sub">Blanco (W)</span><input type="range" id="w" min="0" max="255" value="0" style="width:45%"></div>
      <div class="sw" id="sw"></div>
    </div>
    <div id="bloqueCCT" class="hide">
      <div class="row"><label style="margin:10px 0 4px">Temperatura de blanco</label><span class="val" id="cctv">4000 K</span></div>
      <input type="range" id="cct" min="2700" max="6500" step="100" value="4000"><div class="cct"></div>
    </div>
  </section>

  <section class="card">
    <h2>Tira</h2>
    <div class="grid2">
      <div><label>Tipo</label>
        <select id="tira" style="width:100%">
          <option value="RGBW">RGBW (4 canales)</option><option value="RGB">RGB 5050</option><option value="CCT">Blanco dual CCT</option>
          <option value="MONO">Un color</option><option value="WS2812B">WS2812B · 5 V</option><option value="SK6812">SK6812 RGBW · 5 V</option>
          <option value="WS2811">WS2811 · 12 V</option><option value="WS2815">WS2815 · 12 V</option><option value="RGBCCT">RGB + CCT · 5 canales (placa v2)</option>
        </select></div>
      <div id="bloqueLeds"><label>LEDs direccionables</label><input id="nleds" type="number" min="1" max="600" value="60" style="width:100%"></div>
    </div>
    <div class="row" style="margin-top:10px"><label style="margin:0">Voltaje de salida</label><span class="val" id="vv">—</span></div>
    <input type="range" id="volt" min="10" max="12" step="0.05" value="12" disabled>
    <div class="lim">La tarjeta fija el máximo por hardware; aquí solo se puede bajar (la tira calienta menos).</div>
  </section>

  <section class="card">
    <h2>Horario diario</h2>
    <div class="grid2">
      <div><label>Encender</label><input type="time" id="hon" value="18:30" style="width:100%"></div>
      <div><label>Apagar</label><input type="time" id="hoff" value="01:00" style="width:100%"></div>
    </div>
    <div class="row" style="margin-top:10px">
      <span class="sub" id="progtxt">Sin horario</span>
      <div class="row"><button id="progoff">Quitar</button><button class="pri" id="progon">Guardar</button></div>
    </div>
    <div class="lim">Al guardar se envía también la hora de este teléfono. Con Wi-Fi el cubo la toma de internet.</div>
  </section>

  <section class="card">
    <h2>Escenas</h2>
    <div class="chips" id="escenas"></div>
    <div class="row" style="margin-top:10px"><span class="sub">Toca para aplicar; guarda la luz actual en:</span>
      <div class="row"><select id="escSel"></select><button id="escGuardar">Guardar</button></div></div>
  </section>

  <section class="card">
    <h2>DMX</h2>
    <div class="grid2">
      <div><label>Protocolo</label><select id="dmxp" style="width:100%"><option value="OFF">Apagado</option><option value="ARTNET">Art-Net</option><option value="SACN">sACN (E1.31)</option><option value="CABLE">Cable DMX512 (placa v2)</option></select></div>
      <div class="grid2"><div><label>Universo</label><input id="dmxu" type="number" min="0" value="1" style="width:100%"></div><div><label>Dirección</label><input id="dmxd" type="number" min="1" max="512" value="1" style="width:100%"></div></div>
    </div>
    <div class="row" style="margin-top:8px"><span class="sub" id="dmxtxt">—</span><button id="dmxok">Aplicar</button></div>
    <div class="lim">Analógicas: atenuador + R G B W (RGB+CCT: + blanco frío). Direccionables: 3 o 4 canales por LED. Art-Net y sACN por Wi-Fi; cable DMX512 en la placa v2.</div>
  </section>

  <section class="card" id="cardPersonal">
    <h2>Tarjeta personalizada</h2>
    <div class="grid2">
      <div><label>Voltaje máximo (V)</label><input id="pv" type="number" min="3" max="24.4" step="0.1" value="13" style="width:100%"></div>
      <div><label>Corriente máxima (A)</label><input id="pi" type="number" min="0.2" max="5" step="0.1" value="2" style="width:100%"></div>
    </div>
    <div class="row" style="margin-top:8px"><span class="sub" id="rbtxt"></span><button id="lim">Programar</button></div>
    <div class="lim">Solo con la tarjeta PERSONAL (R_ID = 220k). Pon en la tarjeta la R_B que indica aquí, 1 %.</div>
  </section>

  <section class="card">
    <h2>Red e integraciones</h2>
    <div class="grid2">
      <input id="ssid" type="text" placeholder="Red Wi-Fi (sin espacios)">
      <input id="clave" type="password" placeholder="Contraseña">
    </div>
    <div class="row" style="margin-top:8px"><span class="sub" id="redtxt">—</span><button id="wifi">Conectar Wi-Fi</button></div>
    <div class="row" style="margin-top:10px">
      <span class="sub">WLED, Home Assistant y Alexa en tu red</span>
      <div class="row"><button id="intoff">Desactivar</button><button id="inton">Activar</button></div>
    </div>
    <div class="grid2" style="margin-top:10px">
      <input id="gnom" type="text" placeholder="Grupo (p. ej. tienda-centro)">
      <input id="gclave" type="password" placeholder="Clave del grupo (8+)">
    </div>
    <div class="row" style="margin-top:8px"><span class="sub" id="gtxt">Sin grupo</span><div class="row"><button id="goff">Quitar</button><button id="gok">Guardar grupo</button></div></div>
    <div class="row" style="margin-top:10px"><span class="sub">Reconocer falla</span><button id="reset">Reiniciar falla</button></div>
    <div id="ota" class="hide" style="margin-top:10px">
      <div class="row"><input id="bin" type="file" accept=".bin" style="width:60%"><button id="otaok">Actualizar firmware</button></div>
      <div class="lim" id="otatxt">Archivo .bin de PlatformIO. La salida se apaga mientras se actualiza.</div>
    </div>
  </section>

  <footer>Bluetooth seguro con PIN de 6 dígitos (en la etiqueta). Por Wi-Fi abre http://cuboap-xxxx.local en la misma red.</footer>
</main>

<script>
const SVC='6e400001-b5a3-f393-e0a9-e50e24dcca9e', RX='6e400002-b5a3-f393-e0a9-e50e24dcca9e', TX='6e400003-b5a3-f393-e0a9-e50e24dcca9e';
const $=id=>document.getElementById(id);
const FALLAS={sin_tarjeta:'Sin tarjeta de configuración',tarjeta_inconsistente:'La tarjeta no coincide con el voltaje medido',sobrecorriente:'Sobrecorriente: revisa la tira o baja el brillo',sobretemperatura:'Temperatura alta: se apagó para protegerse',subvoltaje_entrada:'El cartucho no da voltaje suficiente',corto:'Corto en la salida'};
let est=null, enlace=null, cola=Promise.resolve(), demo=null, buf='';
const enc=new TextEncoder(), dec=new TextDecoder();
const DIREC=['WS2812B','SK6812','WS2811','WS2815'];

// ---------- enlaces: Bluetooth, Wi-Fi (página servida por el cubo) o demo ----------
const DE_GRUPO=/^(ON|OFF|BRILLO|RGBW|MODO|CCT|ESCENA \d)\b/i;
function enviar(cmd){
  if($('todos')&&$('todos').checked&&DE_GRUPO.test(cmd))cmd='TODOS '+cmd;
  if(demo) return Promise.resolve(recibir(demo.cmd(cmd)));
  if(!enlace) return Promise.resolve();
  cola=cola.then(()=>enlace.enviar(cmd)).catch(e=>msg('Error: '+e.message,true));
  return cola;
}
function http(){
  let pin=localStorage.getItem('cuboPin')||'';
  const post=async c=>{
    if(!pin){pin=prompt('PIN de 6 dígitos (etiqueta del cubo)')||'';localStorage.setItem('cuboPin',pin)}
    const r=await fetch('/api/cmd',{method:'POST',headers:{'X-PIN':pin},body:c});
    if(r.status===401){localStorage.removeItem('cuboPin');pin='';msg('PIN incorrecto',true);return}
    recibir(await r.text());
  };
  return {enviar:post};
}
async function bluetooth(){
  const dev=await navigator.bluetooth.requestDevice({filters:[{namePrefix:'CuboAP'}],optionalServices:[SVC]});
  dev.addEventListener('gattserverdisconnected',()=>{enlace=null;$('dev').textContent='Desconectado';msg('Conexión perdida',true)});
  const g=await dev.gatt.connect(), s=await g.getPrimaryService(SVC);
  const rx=await s.getCharacteristic(RX), tx=await s.getCharacteristic(TX);
  await tx.startNotifications();
  tx.addEventListener('characteristicvaluechanged',e=>{buf+=dec.decode(e.target.value);let k;while((k=buf.indexOf('\n'))>=0){recibir(buf.slice(0,k));buf=buf.slice(k+1)}});
  $('dev').textContent=dev.name;
  return {enviar:c=>rx.writeValueWithResponse(enc.encode(c+'\n'))};
}
$('con').onclick=async()=>{
  if(!navigator.bluetooth){msg('Este navegador no tiene Bluetooth web. Usa Chrome en Android o PC, Wi-Fi, o la demo.',true);return}
  try{enlace=await bluetooth();demo=null;enviar('ESTADO');enviar('RED')}catch(e){msg('No se conectó: '+e.message,true)}
};
if(location.protocol==='http:'&&location.hostname){enlace=http();$('dev').textContent='Wi-Fi · '+location.hostname;setInterval(()=>enviar('ESTADO'),1500);enviar('ESTADO');enviar('RED')}

// ---------- pantalla ----------
function msg(t,bad){const e=$('est');e.textContent=t;e.classList.toggle('bad',!!bad)}
const hhmm=m=>String(Math.floor(m/60)).padStart(2,'0')+':'+String(m%60).padStart(2,'0');
function pintar(s){
  est=s; const sin=s.perfil==='-';
  $('perfil').textContent=sin?'Sin tarjeta':s.perfil;
  $('lims').textContent=sin?'Inserta la tarjeta':(s.vmax?`Máx ${s.vmax.toFixed(2)} V · ${s.imax.toFixed(1)} A · ${(s.vmax*s.imax).toFixed(0)} W`:'Programa sus límites abajo');
  $('mv').textContent=s.v.toFixed(2);$('mi').textContent=s.i.toFixed(2);$('mw').textContent=s.w.toFixed(1);$('mt').textContent=s.t.toFixed(0);
  const p=s.imax?Math.min(100,100*s.i/s.imax):0;$('carga').style.width=p+'%';$('carga').classList.toggle('hot',p>85);
  $('pwr').disabled=sin;$('pwr').classList.toggle('on',!!s.on);
  const v=$('volt');v.disabled=sin||!s.vmax;v.min=s.vmin;v.max=s.vmax;if(document.activeElement!==v)v.value=s.vset;$('vv').textContent=(+s.vset).toFixed(2)+' V';
  if(document.activeElement!==$('brillo')){$('brillo').value=s.brillo;$('bv').textContent=s.brillo+' %'}
  document.querySelectorAll('#modos button').forEach(b=>b.classList.toggle('sel',b.dataset.m.toLowerCase()===s.modo));
  if(s.tira&&document.activeElement!==$('tira'))$('tira').value=s.tira;
  $('bloqueCCT').classList.toggle('hide',s.tira!=='CCT'&&s.tira!=='RGBCCT');$('bloqueColor').classList.toggle('hide',s.tira==='CCT'||s.tira==='MONO');
  $('bloqueLeds').classList.toggle('hide',!DIREC.includes(s.tira));
  if(s.cct&&document.activeElement!==$('cct')){$('cct').value=s.cct;$('cctv').textContent=s.cct+' K'}
  $('progtxt').textContent=s.prog?`Enciende ${hhmm(s.on_min)} · apaga ${hhmm(s.off_min)}`+(s.hora<0?' (falta la hora)':''):'Sin horario';
  $('cardPersonal').classList.toggle('hide',s.perfil!=='PERSONAL');
  if('escenas' in s)document.querySelectorAll('#escenas button').forEach((b,i)=>{const ok=s.escenas>>i&1;b.disabled=!ok;b.classList.toggle('sel',!!ok)});
  if(s.dmx){if(document.activeElement!==$('dmxp'))$('dmxp').value=s.dmx.toUpperCase();$('dmxtxt').textContent=s.dmx==='off'?'Sin DMX':(s.dmx==='cable'?`Cable @${s.dir} · `:`${s.dmx==='artnet'?'Art-Net':'sACN'} U${s.univ} @${s.dir} · `)+(s.dmx_vivo?'recibiendo':'sin señal')}
  if(s.falla!=='ninguna')msg(FALLAS[s.falla]||s.falla,true);else msg(s.on?`Encendido · entrada ${s.vin.toFixed(1)} V`:'Apagado');
}
function recibir(t){
  t=(t||'').trim();if(!t)return;
  if(t[0]==='{'){try{const j=JSON.parse(t);if('wifi' in j)red(j);else pintar(j)}catch(e){}}
  else if(t.startsWith('ERR'))msg(t.replace('ERR','Rechazado:'),true);
  else if(t.startsWith('OK')&&!demo)setTimeout(()=>enviar('ESTADO'),60);
}
function red(j){$('redtxt').textContent=j.wifi?`Conectado · ${j.ip}`:'Sin Wi-Fi';$('gtxt').textContent=j.grupo?`Grupo: ${j.grupo}`:'Sin grupo';}

// ---------- controles ----------
$('pwr').onclick=()=>enviar(est&&est.on?'OFF':'ON');
let tb;$('brillo').oninput=e=>{$('bv').textContent=e.target.value+' %';clearTimeout(tb);tb=setTimeout(()=>enviar('BRILLO '+e.target.value),80)};
let tv;$('volt').oninput=e=>{$('vv').textContent=(+e.target.value).toFixed(2)+' V';clearTimeout(tv);tv=setTimeout(()=>enviar('V '+e.target.value),150)};
document.querySelectorAll('#modos button').forEach(b=>b.onclick=()=>enviar('MODO '+b.dataset.m));
function color(){const h=$('col').value;enviar(`RGBW ${parseInt(h.slice(1,3),16)} ${parseInt(h.slice(3,5),16)} ${parseInt(h.slice(5,7),16)} ${$('w').value}`)}
let tc;$('col').oninput=$('w').oninput=()=>{clearTimeout(tc);tc=setTimeout(color,80)};
['#ffffff','#ff3b30','#ff9500','#ffd60a','#34c759','#0a84ff','#bf5af2','#ff2d92'].forEach(h=>{const i=document.createElement('i');i.style.background=h;i.onclick=()=>{$('col').value=h;color()};$('sw').appendChild(i)});
let tk;$('cct').oninput=e=>{$('cctv').textContent=e.target.value+' K';clearTimeout(tk);tk=setTimeout(()=>enviar('CCT '+e.target.value),100)};
$('tira').onchange=e=>enviar('TIRA '+e.target.value);
$('nleds').onchange=e=>enviar('LEDS '+e.target.value);
const horaLocal=()=>Math.floor(Date.now()/1000)-new Date().getTimezoneOffset()*60;
$('progon').onclick=()=>{enviar('HORA '+horaLocal());enviar(`PROG ${$('hon').value} ${$('hoff').value}`)};
$('progoff').onclick=()=>enviar('PROG OFF');
function rb(){const v=+$('pv').value;const r=29400/(v/0.8-1);$('rbtxt').textContent=v>=3&&v<=24.4?`R_B = ${(r/1000).toFixed(3)} kΩ`:'Fuera de rango'}
$('pv').oninput=rb;rb();
$('lim').onclick=()=>enviar(`LIMITES ${$('pv').value} ${$('pi').value}`);
$('wifi').onclick=()=>{const s=$('ssid').value.trim(),c=$('clave').value;if(!s||/\s/.test(s)){msg('Escribe la red sin espacios',true);return}enviar(`WIFI ${s} ${c}`)};
$('inton').onclick=()=>enviar('INTEGRACIONES ON');$('intoff').onclick=()=>enviar('INTEGRACIONES OFF');
$('reset').onclick=()=>enviar('RESET');
$('gok').onclick=()=>{const g=$('gnom').value.trim(),k=$('gclave').value;if(!/^[\w-]{1,24}$/.test(g)||k.length<8||/\s/.test(k)){msg('Grupo: letras, números, - o _; clave de 8+ caracteres sin espacios',true);return}enviar(`GRUPO ${g} ${k}`);setTimeout(()=>enviar('RED'),300)};
$('goff').onclick=()=>{enviar('GRUPO OFF');setTimeout(()=>enviar('RED'),300)};
for(let i=1;i<=8;i++){const b=document.createElement('button');b.textContent=i;b.disabled=true;b.onclick=()=>enviar('ESCENA '+i);$('escenas').appendChild(b);$('escSel').add(new Option('Escena '+i,i))}
$('escGuardar').onclick=()=>enviar('ESCENA GUARDAR '+$('escSel').value);
$('dmxok').onclick=()=>{const p=$('dmxp').value;enviar(p==='OFF'?'DMX OFF':p==='CABLE'?`DMX CABLE ${$('dmxd').value}`:`DMX ${p} ${$('dmxu').value} ${$('dmxd').value}`)};
if(location.protocol==='http:'&&location.hostname){$('ota').classList.remove('hide');$('otaok').onclick=async()=>{
  const f=$('bin').files[0];if(!f){msg('Elige el archivo .bin',true);return}
  if(!confirm('¿Actualizar el firmware? La salida se apagará unos segundos.'))return;
  const d=new FormData();d.append('firmware',f,f.name);$('otatxt').textContent='Subiendo…';
  try{const r=await fetch('/update',{method:'POST',headers:{'X-PIN':localStorage.getItem('cuboPin')||''},body:d});$('otatxt').textContent=await r.text()}catch(e){$('otatxt').textContent='Error: '+e.message}}}

// ---------- demo: simula un cubo 12 V 5 A ----------
$('demo').onclick=()=>{
  const s={on:1,perfil:'12V 5A',vmax:12,vmin:10.62,imax:5,vset:12,v:12,i:0,w:0,vin:24.1,t:38,brillo:60,rgbw:[255,255,255,0],modo:'fijo',falla:'ninguna',tira:'RGBW',cct:4000,prog:false,on_min:0,off_min:0,hora:-1,dmx:'off',univ:1,dir:1,dmx_vivo:false,escenas:0};const esc={};
  demo={cmd(c){const [k,...a]=c.trim().split(/\s+/);const K=k.toUpperCase();
    if(K==='ON')s.on=1;else if(K==='OFF')s.on=0;else if(K==='BRILLO')s.brillo=+a[0];else if(K==='V')s.vset=Math.max(s.vmin,Math.min(s.vmax,+a[0]));
    else if(K==='RGBW')s.rgbw=a.map(Number);else if(K==='MODO')s.modo=a[0].toLowerCase();else if(K==='RESET')s.falla='ninguna';
    else if(K==='TIRA'){if(['WS2812B','SK6812'].includes(a[0]))return 'ERR '+a[0]+' necesita tarjeta de 5 V';s.tira=a[0]}
    else if(K==='CCT')s.cct=+a[0];else if(K==='PROG'){if(a[0]==='OFF')s.prog=false;else{const f=x=>{const[h,m]=x.split(':');return h*60+ +m};s.prog=true;s.on_min=f(a[0]);s.off_min=f(a[1])}}
    else if(K==='HORA')s.hora=Math.floor(+a[0]/60)%1440;
    else if(K==='ESCENA'){if(a[0]==='GUARDAR'){esc[a[1]]={rgbw:[...s.rgbw],brillo:s.brillo,modo:s.modo};s.escenas|=1<<(a[1]-1)}else if(esc[a[0]])Object.assign(s,esc[a[0]]);else return 'ERR escena vacía'}
    else if(K==='DMX'){if(a[0]==='OFF')s.dmx='off';else if(a[0]==='CABLE'){s.dmx='cable';s.univ=0;s.dir=+a[1]}else{s.dmx=a[0].toLowerCase();s.univ=+a[1];s.dir=+a[2]}}else if(K==='RED')return JSON.stringify({wifi:false,ip:'',nombre:'CuboAP-DEMO',integraciones:false,grupo:s.grupo||''});
    else if(K==='GRUPO'){s.grupo=a[0]==='OFF'?'':a[0]}
    else if(K==='TODOS'){if(!s.grupo)return 'ERR configura GRUPO nombre clave';return demo.cmd(a.join(' '))}
    tick();return 'OK'}};
  function tick(){const c=s.rgbw.reduce((x,y)=>x+y,0)/(3*255);s.v=s.on?s.vset-0.02:0;s.i=s.on?+(4.2*s.brillo/100*Math.min(1,c||1)*(s.vset/12)**2).toFixed(2):0;s.w=+(s.v*s.i).toFixed(1);s.t=+(30+s.w*0.35).toFixed(1);pintar({...s})}
  enlace=null;$('dev').textContent='CuboAP-DEMO (simulado)';tick();clearInterval(window._d);window._d=setInterval(tick,1000);red({wifi:false});
};
</script>
</body>
</html>
)PAGINA";
