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
DIAS="DLMMJVS",DN=["dom","lun","mar","mié","jue","vie","sáb"],ACC=["Apagar todo","Encender todo","Salida AUX","Escena","Brillo"];let E={},cambiando=0;
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
 $("tind").style.display=E.ind?"":"none";$("tpix").style.display=E.px&&!E.dmx?"":"none";
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
$("pxg").onclick=async()=>{await api(`PX ${$("px1").value} ${$("px2").value} ${$("px3").value} ${$("px4").value}`);await api("PS "+$("pxs").value);api("PO "+$("pxo").value)};$("vvg").onclick=async()=>{await api("UNI "+$("vvu").value);api("VIVO "+($("vvon").checked?1:0))};$("dmg").onclick=async()=>{await api(`PD ${$("dmd").value} ${$("dmc").value}`);await api("PX "+$("dmn").value);await api("PS "+$("dms").value);api("PO "+$("dmo").value)};$("k2").onclick=()=>api("O "+(E.cc[0]?0:100));$("foco").onclick=()=>{if(!E.ym)api("X "+(E.x?0:1))};
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
