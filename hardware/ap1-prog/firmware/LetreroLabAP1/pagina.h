// App web de LetreroLab AP-1: se sirve desde el propio módulo (http://<nombre>.local o la IP).
#pragma once
const char PAGINA[] PROGMEM = R"HTML(<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>LetreroLab</title>
<style>
:root{--f:#0f1419;--t:#18202a;--b:#243041;--x:#e8eef5;--s:#8fa3b8;--a:#22c55e;--r:#ef4444;--y:#f59e0b}
*{box-sizing:border-box}body{margin:0;background:var(--f);color:var(--x);font:15px system-ui,sans-serif}
header{display:flex;align-items:center;gap:10px;padding:12px 16px;background:var(--t);border-bottom:1px solid var(--b)}
header b{font-size:17px}header small{color:var(--s);margin-left:auto;text-align:right}
nav{display:flex;background:var(--t);position:sticky;top:0;z-index:2}nav button{flex:1;padding:12px 4px;background:none;border:0;
color:var(--s);font:inherit;border-bottom:2px solid transparent}nav button.on{color:var(--x);border-color:var(--a)}
main{max-width:640px;margin:auto;padding:12px 16px 40px}section{display:none}section.on{display:block}
.card{background:var(--t);border:1px solid var(--b);border-radius:12px;padding:14px;margin:12px 0}
.card h3{margin:0 0 10px;font-size:14px;color:var(--s);font-weight:600;text-transform:uppercase;letter-spacing:.04em}
.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:8px 0}.row>label{min-width:90px;color:var(--s)}
button.b{background:var(--b);color:var(--x);border:0;border-radius:9px;padding:10px 12px;font:inherit;cursor:pointer}
button.b.on{background:var(--a);color:#04210f;font-weight:600}button.b.r{background:var(--r)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:8px}
.big{width:100%;padding:16px;font-size:18px}input,select{background:var(--f);color:var(--x);border:1px solid var(--b);
border-radius:8px;padding:9px;font:inherit;min-width:0}input[type=range]{flex:1;padding:0}input[type=color]{width:52px;height:40px;padding:2px}
.dias label{display:inline-flex;align-items:center;gap:2px;margin-right:6px;color:var(--s)}.dias input{margin:0}
.muted{color:var(--s);font-size:13px}.dev{display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid var(--b)}
.dev span{flex:1}.met{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;text-align:center}.met b{display:block;font-size:22px}
.met span{color:var(--s);font-size:12px}.alerta{background:#3b1414;border:1px solid var(--r);color:#fecaca}
.barra{height:8px;border-radius:99px;background:var(--b);overflow:hidden;margin-top:6px}.barra i{display:block;height:100%;background:var(--a)}
.pill{font-size:12px;padding:2px 8px;border-radius:99px;background:var(--b);color:var(--s)}
#msg{position:fixed;left:50%;bottom:16px;transform:translateX(-50%);background:var(--b);padding:8px 14px;border-radius:9px;display:none}
</style></head><body>
<header><b>LetreroLab</b><span class="pill" id="nom">...</span><small id="hora"></small></header>
<nav><button data-t="ctl" class="on">Control</button><button data-t="sal">Salidas</button><button data-t="hor">Horarios</button><button data-t="casa">Casa</button><button data-t="aj">Ajustes</button></nav>
<main>
<section id="ctl" class="on">
 <div class="card alerta" id="falla" style="display:none"><b>Protección activada: <span id="fn"></span></b>
  <p class="muted" style="color:#fecaca" id="fd"></p><button class="b r" id="fok">Restablecer</button></div>
 <button class="b big" id="pw">...</button>
 <div class="card" id="cons" style="display:none"><h3>Consumo</h3><div class="met">
  <div><b id="mw">0</b><span>watts</span></div><div><b id="ma">0</b><span>amperes</span></div><div><b id="mv">0</b><span>volts</span></div>
  <div><b id="mt">--</b><span>°C tarjeta</span></div><div><b id="mh">0</b><span>kWh hoy</span></div><div><b id="mk">0</b><span>kWh total</span></div></div>
  <div class="barra"><i id="mbar" style="width:0"></i></div><p class="muted" id="mlim"></p></div>
 <div class="card"><h3>Modo</h3><div class="grid" id="modos"></div>
  <div class="row"><label>Velocidad</label><input type="range" min="0" max="9" id="vel"></div>
  <div class="row"><label>Brillo</label><input type="range" min="5" max="100" id="bri"><span id="briv"></span></div></div>
 <div class="card"><h3>Color (modos Color y Vela)</h3>
  <div class="row"><input type="color" id="rgb"><label style="min-width:auto">Blanco</label><input type="range" min="0" max="255" id="w"></div>
  <div class="row"><label>Canales</label><select id="ch"><option value="1">1</option><option value="2">2</option>
  <option value="3">3 (flechas / RGB)</option><option value="4">4 (RGBW)</option></select></div></div>
 <div class="card" id="tpix" style="display:none"><h3>Módulo de pixeles</h3>
  <p class="muted">LED de cada salida (0-600). Los efectos usan el color de arriba; "letras" divide la cadena en partes iguales
  para la secuencia (0 = una por salida).</p>
  <div class="row"><label>Salida 1</label><input type="number" min="0" max="600" id="px1" style="width:80px">
   <label style="min-width:auto">2</label><input type="number" min="0" max="600" id="px2" style="width:80px"></div>
  <div class="row"><label>Salida 3</label><input type="number" min="0" max="600" id="px3" style="width:80px">
   <label style="min-width:auto">4</label><input type="number" min="0" max="600" id="px4" style="width:80px"></div>
  <div class="row"><label>Letras</label><input type="number" min="0" max="64" id="pxs" style="width:80px">
   <select id="pxo"><option value="0">GRB (WS2812B)</option><option value="1">RGB</option><option value="2">BRG</option></select></div>
  <div class="row"><button class="b" id="pxg">Guardar en el módulo</button><span id="pxabl" class="muted"></span></div></div>
 <div class="card" id="tdmx" style="display:none"><h3>Módulo DMX512</h3>
  <p class="muted">Cada equipo DMX (reflector RGB, barra, atenuador) es un "pixel": los efectos usan el color de arriba.
  Pon en cada equipo su dirección: el primero en la dirección inicial y los siguientes de tantos en tantos canales.</p>
  <div class="row"><label>Equipos</label><input type="number" min="0" max="512" id="dmn" style="width:80px">
   <label style="min-width:auto">Dirección</label><input type="number" min="1" max="512" id="dmd" style="width:80px"></div>
  <div class="row"><label>Canales</label><select id="dmc"><option value="1">1 (atenuador)</option><option value="3">3 (RGB)</option>
   <option value="4">4 (RGBW)</option></select><select id="dmo"><option value="1">RGB</option><option value="0">GRB</option><option value="2">BRG</option></select></div>
  <div class="row"><label>Grupos</label><input type="number" min="0" max="255" id="dms" style="width:80px">
   <span class="muted">para la secuencia (0 = cada equipo)</span></div>
  <div class="row"><button class="b" id="dmg">Guardar en el módulo</button><span id="dmf" class="muted"></span></div></div>
 <div class="card"><h3>Control en vivo (Art-Net / sACN)</h3>
  <p class="muted">Para animar desde xLights, QLC+, Jinx! o Resolume. Mientras lleguen datos mandan ellos; 2.5 s sin datos vuelven los efectos.
  Pixeles: 170 LED por universo. Base/IND: canales 1-4 = salidas, 5-6 = focos. En el programa usa la IP de este equipo (unicast).</p>
  <div class="row"><label><input type="checkbox" id="vvon"> Activo</label><label style="min-width:auto">Universo</label>
   <input type="number" min="0" max="32767" id="vvu" style="width:90px"><button class="b" id="vvg">Guardar</button></div>
  <p class="muted" id="vvst"></p></div>
 <div class="card" id="tio" style="display:none"><h3>Entradas y salidas (AP INPUT / AP PRO DO8)</h3>
  <p class="muted">Salidas de 24 V: toca para encender o apagar. Las cargas de red se mandan con un contactor.</p>
  <p class="muted" id="iobus" style="display:none"></p>
  <div class="row" id="iosal"></div>
  <div class="row" id="ioent"></div>
  <p class="muted">Qué hace cada entrada al activarse ("mientras": al soltar hace lo contrario).</p>
  <div class="row"><select id="ion"></select><select id="ioa"></select>
   <input type="number" min="0" max="100" id="iov" style="width:70px" title="valor: salida 1-28, escena 0-3, brillo %, AUX 0/1">
   <label><input type="checkbox" id="iom"> mientras</label><button class="b" id="iog">Guardar</button></div></div>
 <div class="card" id="tai" style="display:none"><h3>Entradas analógicas (AP PRO AI4)</h3>
  <div id="ailist"></div>
  <p class="muted">Umbral: al pasar del valor hace la acción ("mientras": al bajar, lo contrario). Ej. nivel bajo de cisterna → encender bomba.</p>
  <div class="row"><select id="ain"></select><input type="number" step="0.01" id="aiu" style="width:90px" title="umbral (V o mA)">
   <select id="aia"></select><input type="number" min="0" max="100" id="aiv" style="width:70px" title="valor">
   <label><input type="checkbox" id="aim"> mientras</label><button class="b" id="aig">Guardar</button></div></div>
 <div class="card" id="tmb" style="display:none"><h3>Modbus RTU (AP GATE)</h3>
  <p class="muted" id="mbest"></p>
  <div id="mblist"></div>
  <p class="muted">Punto: esclavo, función (3 holding / 4 input), registro desde 0 (el 40001 del manual es el 0), tipo y escala.</p>
  <div class="row"><select id="mbn"></select><input type="number" min="1" max="247" id="mbe" style="width:64px" title="esclavo">
   <select id="mbf"><option value="3">3 holding</option><option value="4">4 input</option></select>
   <input type="number" min="0" max="65535" id="mbr" style="width:80px" title="registro">
   <select id="mbt"><option value="0">u16</option><option value="1">s16</option><option value="2">u32</option><option value="3">s32</option>
   <option value="4">float</option><option value="5">float CDAB</option></select>
   <input type="number" step="any" id="mbx" value="1" style="width:70px" title="escala"><button class="b" id="mbg">Guardar</button>
   <button class="b" id="mbb">Borrar</button></div>
  <div class="row"><label>Escribir</label><input type="number" min="1" max="247" id="mwe" style="width:64px" placeholder="esclavo">
   <input type="number" min="0" max="65535" id="mwr" style="width:80px" placeholder="registro">
   <input type="number" min="0" max="65535" id="mwv" style="width:80px" placeholder="valor"><button class="b" id="mwg">Registro</button>
   <button class="b" id="mcg1">Bobina ON</button><button class="b" id="mcg0">Bobina OFF</button></div>
  <p class="muted">Umbral: al pasar del valor hace la acción ("mientras": al bajar, lo contrario). Ej. potencia alta → apagar una salida.</p>
  <div class="row"><select id="mun"></select><input type="number" step="any" id="muu" style="width:90px" title="umbral">
   <select id="mua"></select><input type="number" min="0" max="255" id="muv" style="width:70px" title="valor">
   <label><input type="checkbox" id="mum"> mientras</label><button class="b" id="mug">Guardar</button></div></div>
 <div class="card" id="tlu" style="display:none"><h3>Luminarias (AP LIGHT)</h3>
  <p class="muted">PWM4: L1-L16 (12-24 V atenuable). AO4: L17-L32 (0-10 V + contactor). "Sigue" = obedece a la luz principal.</p>
  <div id="lulist"></div>
  <div class="row"><label>Rampa</label><input type="number" min="0" max="60" step="0.5" id="lur" style="width:80px"><span class="muted">segundos</span>
   <button class="b" id="lurg">Guardar</button></div></div>
 <div class="card"><h3>Etiquetas por circuito</h3>
  <p class="muted">Ponle nombre a cada canal, salida o entrada (SALA, COCINA, BOMBA...). Sale en la app y en Home Assistant.</p>
  <div class="row"><select id="etx"></select><input id="ett" maxlength="16" placeholder="nombre" style="flex:1">
   <button class="b" id="etg">Guardar</button></div></div>
 <div class="card" id="tind" style="display:none"><h3>Módulo industrial (0-10 V)</h3>
  <p class="muted">Los canales 1-4 son salidas 0-10 V aisladas: el brillo y los efectos atenúan los drivers de las luminarias.
  El contactor 1 enciende la alimentación de las luces junto con el letrero; el 2 es manual o por horario.</p>
  <div class="row"><button class="b" id="k2">...</button></div>
  <p class="muted">Las luces de 127/240 V se conectan al contactor, nunca a la placa.</p></div>
 <div class="card" id="tcc"><h3>Focos de corriente constante</h3>
  <div class="row"><label>Foco 1</label><input type="range" min="0" max="100" id="cc1"><span id="cc1v"></span></div>
  <div class="row"><label>Foco 2</label><input type="range" min="0" max="100" id="cc2"><span id="cc2v"></span></div>
  <p class="muted">Salidas de 1 A con corriente fija (sin resistencias). Cada foco va solo entre su + y su -.</p></div>
 <div class="card" id="taux"><h3>Salida AUX 12 V</h3><div class="row"><button class="b" id="foco">...</button>
  <select id="ym"><option value="0">Relevador o contactor (manual)</option><option value="1">Ventilador automático (45 °C)</option></select></div>
  <p class="muted">Para focos de 127/240 V use un relevador o contactor externo: la red eléctrica no entra a la placa.</p></div>
 <div class="card"><h3>Ahorro y sensor de luz</h3>
  <div class="row"><button class="b" id="eco">Ahorro</button><button class="b" id="ldr">Solo de noche</button></div>
  <div class="row"><label>Umbral</label><input type="range" min="1" max="200" id="umb"><span class="muted" id="lv"></span></div></div>
 <div class="card"><h3>Escenas</h3><div class="row" id="esc"></div><p class="muted">Toque = cargar. Mantener = guardar la actual.</p></div>
</section>

<section id="sal">
 <div class="card"><h3>Base conectada</h3><p id="binfo" class="muted"></p>
  <div class="row"><label>Modelo</label><input id="bmod" maxlength="16" style="flex:1"><button class="b" id="bmodok">Guardar</button></div></div>
 <div class="card"><h3>Diagnóstico de salidas</h3>
  <div class="row"><button class="b on" id="dgo">Probar salidas</button><button class="b" id="apr">Aprender valores normales</button></div>
  <p class="muted">Prueba una salida a la vez con el medidor de la base (primero al 5 % para descubrir cortos sin riesgo).
  Las luces parpadean unos 8 segundos. Haga "Aprender" con la instalación funcionando bien: desde entonces se detectan tramos fundidos.</p>
  <div id="dgest" class="muted"></div><div id="dgtab"></div></div>
</section>

<section id="hor">
 <div class="card"><h3>Hora del equipo</h3><div class="row"><span id="hora2" style="flex:1"></span>
  <button class="b" id="usarHora">Usar la hora del teléfono</button></div>
  <p class="muted">Con internet se ajusta sola (NTP). Con reloj DS3231 se conserva aunque se vaya la luz.</p></div>
 <div class="card"><h3>Ventana diaria</h3><div class="row"><label>Encender</label><input type="time" id="von">
  <label style="min-width:auto">Apagar</label><input type="time" id="voff"></div>
  <div class="row"><button class="b" id="vok">Guardar</button><button class="b" id="vno">Sin ventana</button></div>
  <p class="muted">Fuera de la ventana todo queda apagado. Puede cruzar la medianoche (19:00 a 02:00).</p></div>
 <div class="card"><h3>Horario solar</h3>
  <div class="row"><label>Ubicación</label><input type="number" step="0.0001" id="glat" placeholder="latitud" style="width:110px">
   <input type="number" step="0.0001" id="glon" placeholder="longitud" style="width:110px"><button class="b" id="gok">Guardar</button></div>
  <p class="muted" id="solt">Sin ubicación. Ciudad de México: 19.4326 -99.1332 (búscala en un mapa).</p>
  <div class="row"><button class="b" id="noche">Luz principal solo de noche</button></div>
  <p class="muted">Como una fotocelda, pero sin sensor: enciende al ocaso y apaga al amanecer. Abajo, acciones con desfase (ej. 15 min antes del ocaso).</p>
  <div id="soles"></div></div>
 <div class="card"><h3>Horarios (8)</h3><div id="progs"></div></div>
</section>

<section id="casa">
 <div class="card"><h3>Toda la casa</h3>
  <div class="row"><button class="b big" style="flex:1" data-g="@* P1">Encender todo</button>
  <button class="b big r" style="flex:1" data-g="@* P0">Apagar todo</button></div>
  <div class="row"><button class="b" data-g="@* X1">Focos: encender todos</button><button class="b" data-g="@* X0">Focos: apagar todos</button></div></div>
 <div class="card"><h3>Mi grupo: <span id="gnom"></span></h3>
  <div class="row"><button class="b" id="gon">Encender grupo</button><button class="b" id="goff">Apagar grupo</button></div></div>
 <div class="card"><h3>Equipos en la red</h3><div id="devs" class="muted">Buscando...</div></div>
</section>

<section id="aj">
 <div class="card"><h3>Equipo</h3>
  <div class="row"><label>Nombre</label><input id="fnom" placeholder="sala"><button class="b" id="snom">Guardar</button></div>
  <div class="row"><label>Grupo</label><input id="fgr" placeholder="planta-alta"><button class="b" id="sgr">Guardar</button></div>
  <p class="muted">Solo letras, números y guiones. El nombre también da la dirección http://nombre.local</p></div>
 <div class="card"><h3>Wi-Fi</h3>
  <div class="row"><label>Red</label><select id="redes" style="flex:1"><option value="">(buscar...)</option></select><button class="b" id="buscar">Buscar</button></div>
  <div class="row"><label>Clave</label><input id="wcl" type="password" style="flex:1"></div>
  <div class="row"><button class="b on" id="wok">Conectar</button><span class="muted" id="wst"></span></div></div>
 <div class="card"><h3>Zona horaria</h3><div class="row"><select id="tz" style="flex:1"></select><button class="b" id="tzok">Guardar</button></div></div>
 <div class="card"><h3>Control fuera de casa (MQTT)</h3>
  <div class="row"><label>Servidor</label><input id="mq" style="flex:1" placeholder="mqtts://xxxx.hivemq.cloud:8883"></div>
  <div class="row"><label>Usuario</label><input id="mqu" style="flex:1"></div>
  <div class="row"><label>Clave</label><input id="mqc" type="password" style="flex:1"></div>
  <div class="row"><button class="b" id="mqok">Guardar</button><button class="b" id="mqno">Quitar</button><span class="muted" id="mqst"></span></div>
  <p class="muted">Temas: letrerolab/&lt;nombre&gt;/cmd (órdenes), /estado (respuesta), letrerolab/todos/cmd, letrerolab/grupo/&lt;grupo&gt;/cmd</p></div>
 <div class="card"><h3>Protección de potencia</h3>
  <div class="row"><label>Límite</label><input type="range" min="1" max="25" id="lim"><span id="limv"></span></div>
  <p class="muted">Corriente total máxima (todas las salidas). Al pasarla se apagan las salidas y reintenta a los 10 s;
  tras 3 disparos en 5 min queda apagado hasta "Restablecer". Usa un fusible del mismo valor o mayor.</p>
  <div class="row"><button class="b" id="ureset">Reiniciar contador de kWh</button></div></div>
 <div class="card"><h3>Seguridad</h3><div class="row"><label>Clave app</label><input id="kc" type="password" style="flex:1">
  <button class="b" id="kok">Guardar</button></div><p class="muted">Usuario: letrerolab. Vacía = sin clave (no recomendado).</p></div>
 <div class="card"><h3>Actualizar programa</h3><div class="row"><input type="file" id="bin" accept=".bin" style="flex:1">
  <button class="b" id="ota">Subir</button></div><p class="muted" id="otast"></p></div>
 <div class="card"><h3>Información</h3><p class="muted" id="info"></p><button class="b r" id="reini">Reiniciar</button></div>
</section>
</main><div id="msg"></div>
<script>
const $=i=>document.getElementById(i),MOD=["Fijo","Secuencia","Parpadeo","Respirar","Sec. suave","Alternado","Color","Arcoíris","Flash","Vela"],
DIAS="DLMMJVS",DN=["dom","lun","mar","mié","jue","vie","sáb"],ACC=["Apagar todo","Encender todo","Salida AUX","Escena","Brillo","Encender salida","Apagar salida","Alternar salida","Alternar luz","Encender luminaria","Apagar luminaria","Alternar luminaria"];let E={},cambiando=0;
const TZ=[["CST6","México centro (CDMX, GDL, MTY)"],["EST5","Cancún / Quintana Roo"],["MST7","Sonora / Mazatlán"],
["PST8PDT,M3.2.0,M11.1.0","Tijuana"],["CST6CDT,M3.2.0,M11.1.0","Frontera norte / Chicago"],["EST5EDT,M3.2.0,M11.1.0","Nueva York"],
["PST8PDT,M3.2.0,M11.1.0","Los Ángeles"],["COT5","Colombia"],["PET5","Perú"],["ECT5","Ecuador"],["VET4","Venezuela"],
["<-03>3","Argentina / Uruguay"],["<-04>4<-03>,M9.1.6/24,M4.1.6/24","Chile"],["CST6","Centroamérica"],
["CET-1CEST,M3.5.0,M10.5.0/3","España"],["UTC0","UTC"]];
function msg(t){const m=$("msg");m.textContent=t;m.style.display="block";clearTimeout(msg.t);msg.t=setTimeout(()=>m.style.display="none",2200)}
async function api(c){try{const r=await fetch("/api"+(c?"?c="+encodeURIComponent(c):""));E=await r.json();pinta()}catch(e){msg("Sin conexión")}}
const hm=m=>m<0?"--:--":String(m/60|0).padStart(2,"0")+":"+String(m%60).padStart(2,"0");
function pinta(){
 $("nom").textContent=E.nom;$("gnom").textContent=E.g;$("hora").textContent=E.t>=0?DN[E.wd]+" "+hm(E.t):"sin hora";
 $("hora2").textContent=E.t>=0?"Ahora: "+hm(E.t)+(E.rtc?" (con DS3231)":""):"Sin hora todavía";
 const pw=$("pw");pw.textContent=E.p?"Encendido":"Apagado";pw.className="b big"+(E.p?" on":"");
 document.querySelectorAll("#modos button").forEach((b,i)=>b.className="b"+(i==E.m?" on":""));
 if(!cambiando){$("vel").value=E.s;$("bri").value=E.b;$("umb").value=E.u;$("ch").value=E.ch;$("w").value=E.c[3];
  $("rgb").value="#"+E.c.slice(0,3).map(v=>v.toString(16).padStart(2,"0")).join("")}
 $("briv").textContent=E.b+"%";$("lv").textContent=E.lux==null?"sin sensor de luz":"luz "+E.lux+" lux";
 $("tind").style.display=E.ind?"":"none";$("tpix").style.display=E.px&&!E.dmx?"":"none";io();ai();mb();lu();solar();etiquetas();
 if(E.vivo){if(document.activeElement.id!="vvu")$("vvu").value=E.vivo.u;$("vvon").checked=!!E.vivo.on;
  $("vvst").textContent=!E.vivo.on?"Apagado":E.vivo.rx?`Recibiendo (${E.vivo.p} paquetes) en ${E.ip||"esta IP"}`:`Esperando datos en ${E.ip||"esta IP"}, Art-Net 6454 / sACN 5568`}$("tdmx").style.display=E.dmx?"":"none";
 if(E.dmx&&E.pix&&document.activeElement.tagName!="INPUT"&&document.activeElement.tagName!="SELECT"){$("dmn").value=E.pix.n[0];$("dmd").value=E.pix.d;$("dmc").value=E.pix.ch;$("dmo").value=E.pix.o;$("dms").value=E.pix.s}
 if(E.dmx&&E.pix)$("dmf").textContent=` ${E.pix.fr} cuadros enviados`;
 if(E.px&&E.pix&&document.activeElement.tagName!="INPUT"){for(let k=0;k<4;k++)$("px"+(k+1)).value=E.pix.n[k];$("pxs").value=E.pix.s;$("pxo").value=E.pix.o}
 if(E.px&&E.pix)$("pxabl").textContent=E.pix.abl<100?` Brillo limitado al ${E.pix.abl}% por corriente`:"";$("tcc").style.display=$("taux").style.display=E.ind?"none":"";
 $("k2").textContent=E.cc[0]?"Contactor 2 encendido":"Contactor 2 apagado";$("k2").className="b"+(E.cc[0]?" on":"");
 if(!cambiando){$("cc1").value=E.cc[0];$("cc2").value=E.cc[1]}$("cc1v").textContent=E.cc[0]+"%";$("cc2v").textContent=E.cc[1]+"%";
 if(document.activeElement!==$("ym"))$("ym").value=E.ym;salidas();
 $("foco").textContent=E.ym?(E.av?"Ventilador encendido":"Ventilador en espera"):(E.x?"AUX encendida":"AUX apagada");$("foco").className="b"+((E.ym?E.av:E.x)?" on":"");
 $("eco").className="b"+(E.e?" on":"");$("ldr").className="b"+(E.l?" on":"");
 if(document.activeElement.tagName!="INPUT"){$("fnom").value=E.nom;$("fgr").value=E.g;$("tz").value=E.tz;
  if(E.on>=0){$("von").value=hm(E.on);$("voff").value=hm(E.off)}}
 $("mqst").textContent=["sin MQTT","conectando...","conectado"][E.mq];
 $("wst").textContent=E.ap?"Modo configuración":(E.red?"Conectado a "+E.red+" ("+E.rssi+" dBm)":"");
 $("info").textContent=E.v+" · IP "+E.ip+" · http://"+E.nom+".local"+(E.k?" · con clave":" · SIN clave");
 if(!document.querySelector("#progs :focus"))progs();
 $("cons").style.display=E.med?"block":"none";$("falla").style.display=E.f?"block":"none";
 $("fn").textContent=E.fn;$("fd").textContent=`Medido: ${E.vin} V, ${E.i} A, ${E.tc??"--"} °C. `+(E.f==1?"Revisa cortos o la carga total.":E.f==2?"Mejora la ventilación; vuelve sola al enfriarse.":"Revisa la fuente (máx. 26 V).");
 $("mw").textContent=Math.round(E.w);$("ma").textContent=E.i.toFixed(1);$("mv").textContent=E.vin.toFixed(1);
 $("mt").textContent=E.tc==null?"--":E.tc.toFixed(0);$("mh").textContent=E.hoy.toFixed(2);$("mk").textContent=E.kwh.toFixed(1);
 $("mbar").style.width=Math.min(100,E.i/E.lim*100)+"%";$("mbar").style.background=E.i>E.lim*.85?"var(--r)":E.i>E.lim*.6?"var(--y)":"var(--a)";
 $("mlim").textContent=`Límite ${E.lim} A`+(E.fp<100&&E.p&&!E.f?` · brillo limitado al ${E.fp}% (arranque o temperatura)`:"");
 if(!cambiando)$("lim").value=E.lim;$("limv").textContent=E.lim+" A";
}
function io(){const I=E.io;if(!I)return;$("tio").style.display=I.o||I.i||(E.bus||{}).m?"":"none";let h="";
 const B=E.bus||{m:0};$("iobus").style.display=B.m?"":"none";
 if(B.m==1){const n=[1,2,3].filter(k=>B.n>>k&1);$("iobus").textContent="AP BUS maestro · nodos en línea: "+(n.length?n.map(k=>k+" (S"+(32*k+1)+"-S"+(32*k+32)+")").join(", "):"ninguno")}
 else if(B.m==2)$("iobus").textContent="AP BUS nodo "+B.id+(B.fs?" · SIN MAESTRO: salidas apagadas":" · conectado al maestro");
 for(let m=0;m<16;m++)if(I.o>>m&1)for(let b=0;b<8;b++){const n=m*8+b+1;h+=`<button class="b${I.s[m]>>b&1?" on":""}" data-sa="${n}">S${n}${et("s",n)}</button>`}
 $("iosal").innerHTML=h||'<span class="muted">Sin AP PRO DO8</span>';h="";
 for(let m=0;m<16;m++)if(I.i>>m&1)for(let b=0;b<8;b++){const n=m*8+b+1,a=I.e[m]>>b&1;h+=`<span class="pill" style="${a?"background:var(--a);color:#000":""}">E${n}${et("e",n)}</span>`}
 $("ioent").innerHTML=h||'<span class="muted">Sin AP INPUT</span>';
 if(!document.querySelector("#tio :focus")){const c=$("ion").value;$("ion").innerHTML=I.r.map(r=>`<option value="${r[0]}">Entrada ${r[0]}${et("e",r[0])}</option>`).join("");
  if(c&&I.r.some(r=>r[0]==c))$("ion").value=c;regla()}}
function ai(){const A=E.ai;if(!A)return;$("tai").style.display=A.m?"":"none";if(!A.m)return;let h="",o="";
 for(let n=0;n<8;n++){if(!(A.m>>(n>>2)&1))continue;const u=A.t[n]?"mA":"V",v=A.v[n];
  h+=`<div class="row"><label>A${n+1}${et("a",n+1)}</label><b style="min-width:80px">${v==null?"--":v.toFixed(2)} ${u}</b>
  <button class="b" data-ai="${n+1}" data-m="${A.t[n]?0:1}">${A.t[n]?"4-20 mA":"0-10 V"}</button></div>`;
  o+=`<option value="${n+1}">A${n+1}${et("a",n+1)}</option>`}
 $("ailist").innerHTML=h;if(!document.querySelector("#tai :focus")){const c=$("ain").value;$("ain").innerHTML=o;if(c&&[...$("ain").options].some(x=>x.value==c))$("ain").value=c;umbral()}}
const MBERR={1:"sin respuesta",2:"error de CRC",3:"respuesta equivocada",11:"función no válida",12:"registro no válido",13:"valor no válido",14:"falla del equipo"};
function mb(){const M=E.mb;if(!M)return;$("tmb").style.display=M.b?"":"none";if(!M.b)return;
 $("mbest").textContent=`${M.b} baudios · ${["8N1","8E1","8O1","8N2"][M.pa]} · respuestas bien: ${M.ok} · con falla: ${M.f}`;let h="",o="";
 M.p.forEach((p,i)=>{const n=i+1;o+=`<option value="${n}">Punto ${n}${et("m",n)}</option>`;if(!p[0])return;
  h+=`<div class="row"><label>M${n}${et("m",n)}</label><b style="min-width:90px">${p[6]?"--":(+p[5]).toFixed(2)}</b>
  <span class="muted">esclavo ${p[0]} · f${p[1]} · reg ${p[2]}${p[6]?" · "+(MBERR[p[6]]||"error "+p[6]):""}</span></div>`});
 $("mblist").innerHTML=h||'<span class="muted">Sin puntos: agrega uno abajo.</span>';
 if(!document.querySelector("#tmb :focus")){const c=$("mbn").value,d=$("mun").value;$("mbn").innerHTML=o;$("mun").innerHTML=o;if(c)$("mbn").value=c;if(d)$("mun").value=d;mbpunto();mbumbral()}}
function mbumbral(){const u=(E.mb.u||[])[+$("mun").value-1];if(!u)return;$("muu").value=u[0];$("mua").value=u[1]==255?"-":u[1];$("muv").value=u[2];$("mum").checked=!!u[3]}
function mbpunto(){const p=(E.mb.p||[])[+$("mbn").value-1];if(!p||!p[0])return;$("mbe").value=p[0];$("mbf").value=p[1];$("mbr").value=p[2];$("mbt").value=p[3];$("mbx").value=p[4]}
function lu(){const L=E.lu;if(!L)return;$("tlu").style.display=L.m?"":"none";if(!L.m)return;
 if(document.querySelector("#tlu :focus")&&document.activeElement.type=="range")return;let h="";
 for(let n=0;n<32;n++){const m=n<16?n>>2:4+((n-16)>>2);if(!(L.m>>m&1))continue;const on=L.o>>>n&1,sg=L.s>>>n&1;
  h+=`<div class="row"><label>L${n+1}${et("l",n+1)}</label><input type="range" min="0" max="100" value="${L.n[n]}" data-lu="${n+1}" style="flex:1">
  <span class="muted" style="min-width:42px">${L.n[n]}%</span><button class="b${on?" on":""}" data-lo="${n+1}">${on?"Encendida":"Apagada"}</button>
  <label><input type="checkbox" data-ls="${n+1}" ${sg?"checked":""}> sigue</label></div>`}
 $("lulist").innerHTML=h;if(!document.querySelector("#lur:focus"))$("lur").value=L.r}
function hm2(m){return m<0?"--:--":String(m/60|0).padStart(2,"0")+":"+String(m%60).padStart(2,"0")}
function solar(){if(document.querySelector("#tsol :focus,#soles :focus,#glat:focus,#glon:focus"))return;const G=E.geo;
 if(G){$("glat").value=G[0];$("glon").value=G[1];$("solt").textContent=`Hoy: amanecer ${hm2(E.solh[1])} · ocaso ${hm2(E.solh[0])}`}
 $("noche").className="b"+(E.noche?" on":"");let h="";
 (E.sol||[]).forEach((o,i)=>{h+=`<div class="row" data-si="${i}"><select data-k="ev"><option value="0" ${o[1]==0?"selected":""}>Ocaso</option><option value="1" ${o[1]==1?"selected":""}>Amanecer</option></select>
  <input type="number" min="-180" max="180" value="${o[2]}" data-k="de" style="width:70px" title="minutos (+ después, - antes)">
  <select data-k="ac">${ACC.map((a,j)=>`<option value="${j}" ${j==o[3]?"selected":""}>${a}</option>`).join("")}</select>
  <input type="number" min="0" max="255" value="${o[4]}" data-k="va" style="width:60px" title="valor">
  <button class="b${o[0]?" on":""}" data-sg="${i}">${o[0]?"Guardado":"Guardar"}</button><button class="b" data-sx="${i}">Borrar</button></div>`});
 $("soles").innerHTML=h}
function umbral(){const n=+$("ain").value,u=(E.ai.u||[])[n-1];if(!u)return;$("aiu").value=u[0];$("aia").value=u[1]==255?"-":u[1];$("aiv").value=u[2];$("aim").checked=!!u[3]}
function et(t,n){const v=(E.et||{})[t+n];return v?" · "+v.replace(/[<>&]/g,""):""}
function etiquetas(){if(document.querySelector("#etx:focus,#ett:focus"))return;const I=E.io||{o:0,i:0},c=$("etx").value;let o="";
 for(let n=1;n<=4;n++)o+=`<option value="C${n}">Canal ${n}${et("c",n)}</option>`;
 const M=(E.ai||{}).m||0;for(let n=1;n<=8;n++)if(M>>((n-1)>>2)&1)o+=`<option value="A${n}">Analógica ${n}${et("a",n)}</option>`;
 const B=E.mb||{b:0,p:[]};if(B.b)B.p.forEach((p,i)=>{if(p[0])o+=`<option value="M${i+1}">Modbus ${i+1}${et("m",i+1)}</option>`});
 const LM=(E.lu||{}).m||0;for(let n=0;n<32;n++){const m=n<16?n>>2:4+((n-16)>>2);if(LM>>m&1)o+=`<option value="L${n+1}">Luminaria ${n+1}${et("l",n+1)}</option>`}
 for(let m=0;m<16;m++){if(I.o>>m&1)for(let b=0;b<8;b++){const n=m*8+b+1;o+=`<option value="S${n}">Salida ${n}${et("s",n)}</option>`}
  if(I.i>>m&1)for(let b=0;b<8;b++){const n=m*8+b+1;o+=`<option value="E${n}">Entrada ${n}${et("e",n)}</option>`}}
 $("etx").innerHTML=o;if(c&&[...$("etx").options].some(x=>x.value==c))$("etx").value=c}
function regla(){const r=(E.io.r||[]).find(x=>x[0]==$("ion").value);if(!r)return;$("ioa").value=r[1]==255?"-":r[1];$("iov").value=r[2];$("iom").checked=!!r[3]}
function progs(){let h="";E.a.forEach((p,i)=>{h+=`<div class="card" style="margin:8px 0"><div class="row dias">${[...DIAS].map((d,j)=>
 `<label><input type="checkbox" data-d="${j}" ${p[1]>>j&1?"checked":""}>${d}</label>`).join("")}</div>
 <div class="row"><input type="time" value="${hm(p[2]*60+p[3])}"><select>${ACC.map((a,j)=>`<option value="${j}" ${j==p[4]?"selected":""}>${a}</option>`).join("")}</select>
 <input type="number" min="0" max="100" value="${p[5]}" style="width:70px" title="valor: focos 0/1, escena 0-3, brillo %">
 <button class="b${p[0]?" on":""}" data-i="${i}">${p[0]?"Guardado":"Guardar"}</button><button class="b" data-x="${i}">Borrar</button></div></div>`});
 $("progs").innerHTML=h;
 $("progs").querySelectorAll("[data-i]").forEach(b=>b.onclick=()=>{const c=b.closest(".card");let d=0;
  c.querySelectorAll("[data-d]").forEach(x=>{if(x.checked)d|=1<<x.dataset.d});const t=c.querySelector("[type=time]").value||"00:00";
  api(`A ${b.dataset.i} ${d||127} ${t} ${c.querySelector("select").value} ${c.querySelector("[type=number]").value||0}`);msg("Horario guardado")});
 $("progs").querySelectorAll("[data-x]").forEach(b=>b.onclick=()=>api(`A ${b.dataset.x} -`));
}
document.querySelectorAll("nav button").forEach(b=>b.onclick=()=>{document.querySelectorAll("nav button,section").forEach(x=>x.classList.remove("on"));
 b.classList.add("on");$(b.dataset.t).classList.add("on");if(b.dataset.t=="casa")vecinos()});
MOD.forEach((m,i)=>{const b=document.createElement("button");b.className="b";b.textContent=m;b.onclick=()=>api("M "+i);$("modos").append(b)});
for(let i=0;i<4;i++){const b=document.createElement("button");b.className="b";b.textContent="Escena "+(i+1);let t;
 b.onpointerdown=()=>t=setTimeout(()=>{t=0;api("S "+i);msg("Escena guardada")},800);b.onpointerup=()=>{if(t){clearTimeout(t);api("R "+i)}};$("esc").append(b)}
const desliza=(id,f)=>{const e=$(id);e.oninput=()=>{cambiando=1};e.onchange=()=>{cambiando=0;api(f(e.value))}};
desliza("vel",v=>"V "+v);desliza("lim",v=>"J "+v);desliza("bri",v=>"B "+v);desliza("umb",v=>"L "+E.l+" "+v);desliza("w",()=>colorCmd());
const colorCmd=()=>{const h=$("rgb").value;return`C ${parseInt(h.substr(1,2),16)} ${parseInt(h.substr(3,2),16)} ${parseInt(h.substr(5,2),16)} ${$("w").value}`};
$("rgb").onchange=()=>api(colorCmd());$("ch").onchange=()=>api("N "+$("ch").value);
$("pw").onclick=()=>api("P "+(E.p?0:1));
$("pxg").onclick=async()=>{await api(`PX ${$("px1").value} ${$("px2").value} ${$("px3").value} ${$("px4").value}`);await api("PS "+$("pxs").value);api("PO "+$("pxo").value)};$("ioa").innerHTML='<option value="-">Nada</option>'+ACC.map((a,j)=>`<option value="${j}">${a}</option>`).join("");
$("iosal").onclick=e=>{const n=e.target.dataset.sa;if(n)api(`SA ${n} 2`)};$("ion").onchange=regla;
$("iog").onclick=()=>{const n=$("ion").value,a=$("ioa").value;if(n)api(a=="-"?`EA ${n} -`:`EA ${n} ${a} ${$("iov").value||0} ${$("iom").checked?1:0}`)};
$("aia").innerHTML='<option value="-">Nada</option>'+ACC.map((a,j)=>`<option value="${j}">${a}</option>`).join("");
$("ailist").onclick=e=>{const d=e.target.dataset;if(d.ai)api(`AI ${d.ai} ${d.m}`)};$("ain").onchange=umbral;
$("mbn").onchange=mbpunto;$("mun").onchange=mbumbral;
$("mua").innerHTML='<option value="-">Nada</option>'+ACC.map((a,j)=>`<option value="${j}">${a}</option>`).join("");
$("mug").onclick=()=>{const n=$("mun").value,a=$("mua").value;api(a=="-"?`MU ${n} -`:`MU ${n} ${$("muu").value||0} ${a} ${$("muv").value||0} ${$("mum").checked?1:0}`)};
$("lulist").addEventListener("change",e=>{const t=e.target;if(t.dataset.lu)api(`LU ${t.dataset.lu} ${t.value}`);if(t.dataset.ls)api(`LS ${t.dataset.ls} ${t.checked?1:0}`)});
$("lulist").addEventListener("click",e=>{const t=e.target.closest("[data-lo]");if(t)api(`LO ${t.dataset.lo} 2`)});
$("lurg").onclick=()=>api("LR "+($("lur").value||0));
$("gok").onclick=()=>api(`GEO ${$("glat").value} ${$("glon").value}`);
$("noche").onclick=()=>api("NOCHE "+(E.noche?0:1));
$("soles").addEventListener("click",e=>{const g=e.target.closest("[data-sg]"),x=e.target.closest("[data-sx]");
 if(x)return api(`SOL ${x.dataset.sx} -`);if(!g)return;const r=g.closest("[data-si]"),v=k=>r.querySelector(`[data-k=${k}]`).value;
 api(`SOL ${g.dataset.sg} ${v("ev")} ${v("de")||0} ${v("ac")} ${v("va")||0}`)});
$("mbg").onclick=()=>api(`MP ${$("mbn").value} ${$("mbe").value||1} ${$("mbf").value} ${$("mbr").value||0} ${$("mbt").value} ${$("mbx").value||1}`);
$("mbb").onclick=()=>api(`MP ${$("mbn").value} -`);
$("mwg").onclick=()=>api(`MW ${$("mwe").value||1} ${$("mwr").value||0} ${$("mwv").value||0}`);
$("mcg1").onclick=()=>api(`MC ${$("mwe").value||1} ${$("mwr").value||0} 1`);
$("mcg0").onclick=()=>api(`MC ${$("mwe").value||1} ${$("mwr").value||0} 0`);
$("aig").onclick=()=>{const n=$("ain").value,a=$("aia").value;if(n)api(a=="-"?`AU ${n} -`:`AU ${n} ${$("aiu").value||0} ${a} ${$("aiv").value||0} ${$("aim").checked?1:0}`)};
$("etg").onclick=()=>{api(`ET ${$("etx").value} ${$("ett").value}`);$("ett").value=""};
$("vvg").onclick=async()=>{await api("UNI "+$("vvu").value);api("VIVO "+($("vvon").checked?1:0))};$("dmg").onclick=async()=>{await api(`PD ${$("dmd").value} ${$("dmc").value}`);await api("PX "+$("dmn").value);await api("PS "+$("dms").value);api("PO "+$("dmo").value)};$("k2").onclick=()=>api("O "+(E.cc[0]?0:100));$("foco").onclick=()=>{if(!E.ym)api("X "+(E.x?0:1))};
desliza("cc1",v=>`O ${v} ${E.cc[1]}`);desliza("cc2",v=>`O ${E.cc[0]} ${v}`);$("ym").onchange=()=>api("Y "+$("ym").value);
$("dgo").onclick=()=>{api("DIAG");msg("Probando salidas...")};$("apr").onclick=()=>{api("APRENDER");msg("Aprendiendo...")};
$("bmodok").onclick=()=>{api("MODELO "+$("bmod").value);msg("Modelo guardado en la base")};
const SAL=["Canal 1","Canal 2","Canal 3","Canal 4","Foco CC 1","Foco CC 2"],EST=["sin probar","OK","sin carga","CORTO","baja (¿tramo fundido?)","alta"],
 COL=["var(--s)","var(--a)","var(--y)","var(--r)","var(--y)","var(--y)"];
function salidas(){const B=E.base||{};
 $("binfo").textContent=B.ok?`Modelo ${B.mod||"-"} · serie ${B.sn||"-"} · ${B.h} h de uso`:"No se detecta la base (¿programador solo en el USB?)";
 if(document.activeElement!==$("bmod"))$("bmod").value=B.mod||"";
 $("dgest").textContent=E.dg>=0?`Probando ${SAL[E.dg]}...`:(E.aviso?"Aviso: "+E.aviso:"");
 $("dgtab").innerHTML=E.pr.map((r,i)=>`<div class="dev"><span>${SAL[i]}</span><span class="pill" style="color:${COL[r[0]]}">${EST[r[0]]}</span>
 <span class="muted" style="flex:0 0 120px;text-align:right">${r[0]?(r[1]/1000).toFixed(2)+" A":""}${B.n&&B.n[i]?" / "+(B.n[i]/1000).toFixed(2):""}</span></div>`).join("")}
$("eco").onclick=()=>api("E "+(E.e?0:1));$("ldr").onclick=()=>api("L "+(E.l?0:1)+" "+E.u);
$("usarHora").onclick=()=>{const d=new Date(),p=n=>String(n).padStart(2,"0");
 api(`T ${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`);msg("Hora puesta")};
$("vok").onclick=()=>api(`H ${$("von").value} ${$("voff").value}`);$("vno").onclick=()=>api("H -");
document.querySelectorAll("[data-g]").forEach(b=>b.onclick=()=>{api(b.dataset.g);msg("Enviado a toda la casa")});
$("gon").onclick=()=>api(`@${E.g} P1`);$("goff").onclick=()=>api(`@${E.g} P0`);
async function vecinos(){try{const l=await(await fetch("/vecinos")).json();
 $("devs").innerHTML=l.length?l.map(v=>`<div class="dev"><span><b>${v.nom}</b> <span class="pill">${v.g}</span></span>
 <button class="b" onclick="otro('${v.ip}','P1')">On</button><button class="b" onclick="otro('${v.ip}','P0')">Off</button>
 <a class="b" style="text-decoration:none;padding:10px;color:var(--x)" href="http://${v.ip}/">Abrir</a></div>`).join(""):"No se ven otros equipos (deben estar en la misma red Wi-Fi).";
}catch(e){$("devs").textContent="Error"}}
function otro(ip,c){fetch(`http://${ip}/api?c=${c}`,{mode:"no-cors"}).then(()=>msg("Enviado"))}
TZ.forEach(([v,n])=>{const o=document.createElement("option");o.value=v;o.textContent=n;$("tz").append(o)});
$("tzok").onclick=()=>api("Z "+$("tz").value);
$("snom").onclick=()=>{api("D "+$("fnom").value);msg("Reiniciando con el nuevo nombre...")};$("sgr").onclick=()=>api("G "+$("fgr").value);
$("buscar").onclick=async()=>{$("buscar").textContent="...";try{const l=await(await fetch("/redes")).json();
 $("redes").innerHTML=l.map(r=>`<option>${r.r}</option>`).join("")}catch(e){}$("buscar").textContent="Buscar"};
$("wok").onclick=()=>{const r=$("redes").value;if(!r)return msg("Elige una red");api(`W ${r},${$("wcl").value}`);
 msg("Conectando... busca el equipo en tu red como "+E.nom+".local")};
$("mqok").onclick=()=>api(`Q ${$("mq").value},${$("mqu").value},${$("mqc").value}`);$("mqno").onclick=()=>api("Q -");
$("kok").onclick=()=>{api("K "+$("kc").value);msg("Clave guardada")};
$("fok").onclick=()=>api("F 0");$("ureset").onclick=()=>{if(confirm("¿Poner en cero los kWh?"))api("U 0")};
$("reini").onclick=()=>{if(confirm("¿Reiniciar el equipo?"))api("!")};
$("ota").onclick=async()=>{const f=$("bin").files[0];if(!f)return;const d=new FormData();d.append("f",f);$("otast").textContent="Subiendo...";
 try{$("otast").textContent=await(await fetch("/ota",{method:"POST",body:d})).text()}catch(e){$("otast").textContent="Error"}};
api();setInterval(()=>{if(!document.hidden&&!cambiando)api()},3000);
</script></body></html>)HTML";
