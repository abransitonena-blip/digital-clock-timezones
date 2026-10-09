// Manual de montaje completo: manual_montaje_5x5_v9.pdf (carta).
const { chromium } = require('playwright');
const fs = require('fs');
const rd = f => fs.readFileSync(f, 'utf8');
const cu = rd('cobre_planchar.svg'), silk = rd('serigrafia_planchar.svg'), silkv = rd('serigrafia_vista.svg'), bot = rd('smd_lado_cobre.svg');
const tabla = JSON.parse(rd('../fuente-5canales-v3/tabla.json'));
const z = (s, k) => s.replace('width="50mm" height="50mm"', `width="${50*k}mm" height="${50*k}mm"`);
const paso = n => z(rd(`pasos/${n}.svg`), 1.25);
const bar = `<svg width="50mm" height="5mm" viewBox="0 0 50 5"><rect x="0" y="2" width="50" height="1"/><rect x="0" y="0" width="0.6" height="5"/><rect x="49.4" y="0" width="0.6" height="5"/></svg>`;
const esquema = `<svg width="180mm" height="62mm" viewBox="0 0 180 62" font-family="Arial,Helvetica,sans-serif" font-size="3">
<g fill="none" stroke="#000" stroke-width="0.5" stroke-linecap="round">
<path d="M8 12 H34 M8 50 H120"/>
<path d="M16 12 V26 M16 36 V50"/><rect x="13" y="26" width="6" height="10"/><path d="M11 37 L21 25"/>
<path d="M34 12 V8 H48 M60 8 H74 V12 M34 12 V16 H50 M58 16 H74 V12"/>
<path d="M50 12 V20 M58 12 V20" transform="translate(0 0)"/>
<rect x="48" y="5" width="12" height="6"/>
<path d="M50.5 14 V18 M57.5 14 V18" stroke-width="0.9"/><path d="M50.5 16 H48 M57.5 16 H60"/>
<path d="M74 12 H82"/><rect x="82" y="9.5" width="12" height="5"/><path d="M94 12 H104 V19"/>
<path d="M104 19 L114 29 L104 39 L94 29 Z"/><path d="M104 39 V50"/>
<path d="M114 29 H128 V12 H170 M94 29 H90 V56 H170"/>
<path d="M140 12 V27 M140 33 V56"/><path d="M135 27 H145" stroke-width="0.9"/><path d="M135 33 Q140 30 145 33" stroke-width="0.9"/>
<path d="M155 12 V26 M155 38 V56"/><rect x="152.5" y="26" width="5" height="12"/>
<circle cx="170" cy="12" r="1.4"/><circle cx="170" cy="56" r="1.4"/>
</g>
<path d="M101 27 L107 27 L104 31 Z"/><path d="M101 31.5 H107" stroke="#000" stroke-width="0.5"/>
<circle cx="8" cy="12" r="1.4" fill="#fff" stroke="#000" stroke-width="0.5"/><circle cx="8" cy="50" r="1.4" fill="#fff" stroke="#000" stroke-width="0.5"/>
<text x="3" y="13">L</text><text x="3" y="51">N</text><text x="21" y="32">RV1 10D241K</text>
<text x="48" y="4">R1 1MΩ</text><text x="46" y="23">C1 X2 474J</text><text x="81" y="7">R3 150Ω 1W</text>
<text x="109" y="22">BR1 KBP307</text><text x="117" y="10">+</text><text x="85" y="58">−</text>
<text x="132" y="24">+</text><text x="128" y="44">CE1 47µF</text><text x="128" y="48">250V</text><text x="159" y="31">R5 220k</text>
<text x="173" y="13">S1 +</text><text x="173" y="57">S1 −</text>
<text x="10" y="61" font-size="2.6" fill="#555">Un canal. El canal 2 es igual y comparte L, N y el varistor. Fusible 500 mA lento e interruptor van en la caja, antes de L.</text>
</svg>`;
const bom = [
  ['C1, C2', '2', 'Capacitor <b>X2 275 VAC</b>, patas a 15 mm (474J para 1–10 LED; ver tabla)', 'No tiene polaridad'],
  ['R1, R2', '2', 'Resistencia <b>1 MΩ ½ W</b> (café-negro-verde)', 'Parada'],
  ['R3, R4', '2', 'Resistencia <b>150 Ω 1 W</b> (café-verde-café)', 'Parada'],
  ['R5, R6', '2', 'Resistencia <b>220 kΩ ¼ W</b> (rojo-rojo-amarillo), de cuerpo delgado', 'Acostada, a la izquierda del puente'],
  ['BR1, BR2', '2', 'Puente rectificador <b>KBP307</b>', '<b>+</b> en la esquina recortada'],
  ['CE1, CE2', '2', 'Electrolítico <b>47 µF 250 V</b>, 17 mm, patas a 5 mm', '<b>Franja − a la derecha</b>'],
  ['RV1', '1', 'Varistor <b>10D241K</b>', 'No tiene polaridad'],
  ['S1, S2', '2', 'Bornera <b>KF301 2 polos</b> o cables soldados directo', '+ a la izquierda (círculo con +)'],
  ['L, N', '—', 'Cable de uso rudo 2×18 AWG', 'Soldado directo'],
  ['Caja', '1+1', 'Portafusible de chasis + fusible <b>lento 500 mA</b>; interruptor iluminado', 'En la fase (L)'],
  ['—', '2', 'Tornillo M3 con poste de plástico', 'Esquinas izquierdas'],
  ['—', '1', 'Placa fenólica de una cara 5 × 5 cm o mayor', ''],
];
const pasos = [
  ['01_rc', 'R5 y R6 · 220 kΩ', 'Acostadas, pegadas a la placa, a la izquierda del puente. Pasan por encima de dos pistas como un puente de cable. Dobla las patas a la medida y deja el cuerpo hacia la izquierda para que no choque con el puente. Descargan el electrolítico al desconectar.'],
  ['02_rd', 'R1 y R2 · 1 MΩ', 'Paradas: el cuerpo sobre el pad con círculo doble y la pata doblada al otro pad. Descargan el capacitor X2 al desconectar.'],
  ['03_rs', 'R3 y R4 · 150 Ω 1 W', 'Paradas, junto al X2. Deja el cuerpo 2 mm separado de la placa para que ventile.'],
  ['04_rv', 'Varistor RV1', 'En diagonal a la izquierda, entre L y N. No tiene polaridad. Levántalo 2 mm.'],
  ['05_br', 'Puentes BR1 y BR2 · KBP307', 'La pata <b>+</b> (esquina recortada) va donde dice + en la serigrafía: arriba en el canal 1, abajo en el canal 2. Si se pone al revés, los LED no prenden.'],
  ['06_c', 'Capacitores X2 · C1 y C2', 'Sin polaridad. Verifica que digan X2 y 275 VAC y el valor que elegiste según tus LED.'],
  ['07_ce', 'Electrolíticos CE1 y CE2', '<b>La franja (−) hacia la orilla derecha</b>, donde está la media luna negra de la serigrafía. Al revés pueden reventar.'],
  ['08_j', 'Salidas S1 y S2', 'Bornera o cable soldado directo, como en tu primera placa. El + es el pad del círculo con +. Usa cable rojo para + y negro para −.'],
  ['09_in', 'Cables de entrada L y N', 'Suelda el cable de la clavija: la fase (L) pasa antes por el fusible y el interruptor de la caja. Haz un nudo o usa un cincho como seguro para que no se jale la soldadura.'],
];
const tr = rows => rows.map(r => `<tr>${r.map(c => `<td>${c}</td>`).join('')}</tr>`).join('');
const css = `@page{size:letter;margin:12mm}body{font-family:Arial,Helvetica,sans-serif;margin:0;color:#111}
h1{font-size:17pt;margin:0 0 2mm}h2{font-size:12.5pt;margin:4mm 0 2mm;border-bottom:0.4mm solid #333;padding-bottom:1mm}
p,li{font-size:9.6pt;margin:1mm 0;line-height:1.4}.pg{page-break-after:always}.mut{color:#555}
.g{display:grid;grid-template-columns:repeat(3,50mm);gap:8mm;margin-top:3mm}
table{border-collapse:collapse;width:100%;font-size:9pt}th,td{border:0.3mm solid #999;padding:1.4mm 2mm;text-align:left;vertical-align:top}th{background:#eee}
.steps{display:grid;grid-template-columns:1fr 1fr;gap:5mm 8mm}.st{display:flex;gap:3mm;break-inside:avoid}.st h3{font-size:10.5pt;margin:0 0 1mm}
.num{font-size:15pt;font-weight:700;width:9mm;flex:none}.chk li{list-style:"☐  "}.cover{display:flex;gap:10mm;align-items:center}
.big{font-size:44pt;font-weight:800;letter-spacing:2pt;margin:0}.warn{border:0.5mm solid #b3261e;padding:3mm;margin-top:4mm}.warn b{color:#b3261e}`;
const html = `<!doctype html><meta charset="utf-8"><style>${css}</style>
<div class="pg"><div class="cover"><div>${z(silkv, 2.0)}</div><div>
<p class="big">AP</p><h1>Fuente LED de 2 canales</h1><p>Fuente capacitiva · 127 V~ · placa de 5 × 5 cm · una cara</p>
<p class="mut">Manual de montaje</p>
<h2>Datos</h2><ul><li>2 salidas independientes para cadenas de LED en serie.</li><li>Corriente por salida según el capacitor X2: con 474J ≈ 18–19 mA.</li>
<li>Protección: varistor, resistencia de 150 Ω, descarga de capacitores; fusible en la caja.</li><li>Todas las piezas de patitas (sin SMD). Sin zener: conectar LED solo con la fuente apagada.</li></ul>
<h2>Contenido</h2><ol><li>Hoja para planchar</li><li>Diagrama</li><li>Lista de material</li><li>Montaje paso a paso</li><li>Revisión antes de conectar</li><li>Primera prueba y fallas</li><li>Tabla de capacitores</li></ol></div></div>
<div class="warn"><b>⚠ Peligro: 127 V.</b> Esta fuente no está aislada de la red. Toda la placa y los LED quedan conectados a la luz. Ármala dentro de una caja de plástico y nunca la toques conectada.</div></div>

<div class="pg"><h1>1 · Hoja para planchar (1:1)</h1>
<p><b>Láser al 100 %, sin invertir.</b> Arriba: cobre. Abajo: serigrafía (lado de componentes). ${bar} 50 mm</p>
<div class="g">${cu.repeat(3)}${silk.repeat(3)}</div>
<h2>Hacer la placa</h2><ol><li>Lija el cobre con fibra y límpialo con alcohol.</li><li>Plancha el cobre 3–4 min, sin vapor. Remoja y retira el papel.</li>
<li>Cloruro férrico hasta que se vaya el cobre sobrante. Quita el tóner con thinner.</li>
<li>Perfora: 1 mm las piezas, 1.2 mm borneras, puente y varistor, 1.5 mm los pads L y N, 3.2 mm los tornillos.</li>
<li>Plancha la serigrafía del otro lado alineando sus círculos con los agujeros a contraluz.</li></ol></div>

<div class="pg"><h1>2 · Diagrama</h1>${esquema}
<h1 style="margin-top:6mm">3 · Lista de material (una placa)</h1><table><tr><th>Ref</th><th>Cant.</th><th>Pieza</th><th>Montaje</th></tr>${tr(bom)}</table>
<p class="mut">Para 5 salidas se usan 3 placas (sobra una salida).</p></div>

<div class="pg"><h1>4 · Montaje paso a paso</h1><p>De lo más bajo a lo más alto. En naranja, dónde va la pieza de cada paso. Todas las piezas son de patitas y van del lado de componentes.</p>
<div class="steps">${pasos.map((p, i) => `<div class="st"><div class="num">${i + 1}</div><div>${paso(p[0])}<h3>${p[1]}</h3><p>${p[2]}</p></div></div>`).join('')}</div></div>

<div class="pg"><h1>5 · Revisión antes de conectar</h1>
<ul class="chk"><li>Ningún puente de soldadura entre pads vecinos (revisa con lupa, sobre todo en el puente rectificador).</li>
<li>BR1 y BR2: la pata + donde dice + en la serigrafía.</li><li>CE1 y CE2: franja (−) hacia la orilla derecha.</li>
<li>C1 y C2 dicen X2 y 275 VAC.</li><li>Con el multímetro en continuidad: L y N <b>no</b> deben pitar entre sí.</li>
<li>En cada salida, + y − <b>no</b> deben pitar (al principio puede marcar algo mientras carga el electrolítico; luego unos 200 kΩ).</li>
<li>Los LED conectados con su pata larga (+) hacia el + de la bornera.</li><li>Fusible de 500 mA lento puesto en la caja.</li></ul>
<h1>6 · Primera prueba</h1><ol><li>Conecta un foco incandescente de 40–60 W en serie con la clavija.</li><li>Conecta los LED en S1 y S2 con todo desconectado.</li>
<li>Enchufa. El foco debe quedar apagado o apenas tibio y los LED encendidos parejo.</li><li>Si todo bien, desconecta, espera 10 s y quita el foco.</li>
<li>Opcional: mide la corriente poniendo el multímetro (mA) en serie con una cadena, siempre conectando con la fuente apagada.</li></ol>
<h2>Si algo falla</h2><table><tr><th>Qué pasa</th><th>Causa probable</th><th>Qué hacer</th></tr>
${tr([['El foco prende fuerte', 'Corto: soldadura unida, X2 dañado o puente al revés', 'Desconecta y revisa soldaduras y BR'],
['No prende ningún LED', 'Fusible abierto, cadena de LED al revés o puente al revés', 'Revisa fusible, polaridad de la cadena y BR'],
['Un canal sí y otro no', 'Falla solo en ese canal (BR, X2, RS o soldadura)', 'Compara pieza por pieza con el canal que sí funciona'],
['LED muy débiles', 'Capacitor X2 chico para esos LED', 'Usa el valor de la tabla'],
['LED parpadean', 'Electrolítico mal soldado o al revés', 'Revisa CE y su franja'],
['Se calienta RS', 'Corto en la salida o capacitor muy grande', 'Revisa la cadena y el valor del X2']])}</table></div>

<div><h1>7 · Tabla de capacitores (127 V)</h1>
<table><tr><th>LED en la salida</th><th>Blanco/azul/verde</th><th>Rojo/amarillo</th></tr>${tr(tabla.map(r => [r[0], r[1], r[3]]))}</table>
<div class="warn"><b>Recuerda:</b> conecta y desconecta LED con la fuente apagada y espera 10 segundos. Una salida sin LED se queda cargada a unos 200 V.</div></div>`;
(async () => { const b = await chromium.launch(); const p = await b.newPage(); await p.setContent(html);
  await p.pdf({ path: 'manual_montaje_5x5_v9.pdf', format: 'Letter', printBackground: true, preferCSSPageSize: true }); await b.close(); console.log('ok'); })();
