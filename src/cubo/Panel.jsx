import { useEffect, useRef, useState } from 'react'
import useCubo, { FALLAS, DIRECCIONABLES } from './useCubo'
import { rbParaVoltaje } from '../lib/led'

const MODOS = [['FIJO', 'Fijo'], ['RESPIRA', 'Respira'], ['ARCOIRIS', 'Arcoíris'], ['FUEGO', 'Fuego'], ['COMETA', 'Cometa']]
const TIRAS = [['RGBW', 'RGBW (4 canales)'], ['RGB', 'RGB 5050'], ['CCT', 'Blanco dual CCT'], ['MONO', 'Un color'],
  ['WS2812B', 'WS2812B · 5 V'], ['SK6812', 'SK6812 RGBW · 5 V'], ['WS2811', 'WS2811 · 12 V'], ['WS2815', 'WS2815 · 12 V'], ['RGBCCT', 'RGB + CCT · 5 canales (placa v2/v3)']]
const MUESTRAS = ['#ffffff', '#ffb86b', '#ff3b30', '#ff9500', '#ffd60a', '#34c759', '#00c7be', '#0a84ff', '#5e5ce6', '#bf5af2', '#ff2d92']
const PESTANAS = [['luz', 'Luz'], ['tira', 'Tira y voltaje'], ['tiempo', 'Horario y escenas'], ['red', 'Red y hogar'], ['dmx', 'DMX'], ['avanzado', 'Avanzado']]
// Recorte térmico del firmware: lineal de 70 a 90 °C medido junto al inductor; a 90 °C apaga.
const T_RECORTE = 70, T_CORTE = 90

const hhmm = m => String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0')
const hex = c => '#' + c.slice(0, 3).map(x => x.toString(16).padStart(2, '0')).join('')
const rgb = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16))
function kelvin(k) {                               // aproximación de Tanner Helland, 1000–40000 K
  const t = k / 100
  const r = t <= 66 ? 255 : 329.7 * (t - 60) ** -0.1332
  const g = t <= 66 ? 99.47 * Math.log(t) - 161.1 : 288.1 * (t - 60) ** -0.0755
  const b = t >= 66 ? 255 : t <= 19 ? 0 : 138.5 * Math.log(t - 10) - 305.0
  return [r, g, b].map(v => Math.max(0, Math.min(255, Math.round(v))))
}
function estadoTermico(t) {
  if (t == null) return { txt: '—', cls: '' }
  if (t >= T_CORTE) return { txt: 'Apagado por temperatura', cls: 'mal' }
  if (t >= T_RECORTE) return { txt: `Recortando brillo (${Math.round(100 - (100 * (t - T_RECORTE)) / (T_CORTE - T_RECORTE))} % máx.)`, cls: 'alerta' }
  if (t >= T_RECORTE - 10) return { txt: 'Templado', cls: 'alerta' }
  return { txt: 'Normal', cls: 'bien' }
}

function useRetardo(fn, ms) {                     // evita inundar el Bluetooth al mover deslizadores
  const t = useRef(null)
  return v => { clearTimeout(t.current); t.current = setTimeout(() => fn(v), ms) }
}

function Medidor({ valor, max, unidad, etiqueta, dec = 1, alerta, mal }) {
  const f = max ? Math.max(0, Math.min(1, (valor ?? 0) / max)) : 0
  const R = 30, C = 2 * Math.PI * R
  const cls = valor == null ? '' : mal != null && valor >= mal ? 'mal' : alerta != null && valor >= alerta ? 'alerta' : 'bien'
  return (
    <div className="medidor" role="meter" aria-valuenow={valor ?? 0} aria-valuemax={max} aria-label={etiqueta}>
      <svg viewBox="0 0 76 76" aria-hidden="true">
        <circle cx="38" cy="38" r={R} className="fondo" />
        {f > 0.005 && <circle cx="38" cy="38" r={R} className={'arco ' + cls} strokeDasharray={`${f * C} ${C}`} transform="rotate(-90 38 38)" />}
      </svg>
      <div className="medidor-val"><b>{valor == null ? '–' : valor.toFixed(dec)}</b><span>{unidad}</span></div>
      <div className="medidor-et">{etiqueta}</div>
    </div>
  )
}

export default function Panel() {
  const { estado: s, red, matter, modo, nombre, mensaje, setMensaje, enviar, conectarBle, demo, todos, setTodos } = useCubo()
  const [tab, setTab] = useState(() => { try { return localStorage.getItem('cubo-tab') || 'luz' } catch { return 'luz' } })
  const [gnom, setGnom] = useState(''), [gclave, setGclave] = useState('')
  const [brillo, setBrillo] = useState(60), [volt, setVolt] = useState(12), [cct, setCct] = useState(4000)
  const [color, setColor] = useState('#ffffff'), [w, setW] = useState(0)
  const [hon, setHon] = useState('18:30'), [hoff, setHoff] = useState('01:00')
  const [esc, setEsc] = useState(1), [dsal, setDsal] = useState('ESPEJO'), [dgru, setDgru] = useState(8), [dmxp, setDmxp] = useState('ARTNET'), [dmxu, setDmxu] = useState(1), [dmxd, setDmxd] = useState(1)
  const [pv, setPv] = useState(13), [pi, setPi] = useState(2), [ssid, setSsid] = useState(''), [clave, setClave] = useState('')
  const editando = useRef(false)
  useEffect(() => {
    if (!s || editando.current) return
    setBrillo(s.brillo); setVolt(s.vset); if (s.cct) setCct(s.cct)
    if (s.rgbw) { setColor(hex(s.rgbw)); setW(s.rgbw[3]) }
  }, [s])
  const elegir = k => { setTab(k); try { localStorage.setItem('cubo-tab', k) } catch { /* sin almacenamiento */ } }
  const tocar = () => { editando.current = true; clearTimeout(tocar.t); tocar.t = setTimeout(() => { editando.current = false }, 1500) }
  const enviarBrillo = useRetardo(v => enviar('BRILLO ' + v), 90)
  const enviarVolt = useRetardo(v => enviar('V ' + v), 160)
  const enviarCct = useRetardo(v => enviar('CCT ' + v), 110)
  const enviarColor = useRetardo(([c, ww]) => { const [r, g, b] = rgb(c); enviar(`RGBW ${r} ${g} ${b} ${ww}`) }, 90)
  const conectado = modo !== 'ninguno'
  const sin = !s || s.perfil === '-'
  const rb = rbParaVoltaje(+pv)
  const horaLocal = () => Math.floor(Date.now() / 1000) - new Date().getTimezoneOffset() * 60
  const term = estadoTermico(s?.t)

  // vista previa: color de la luz (RGB + blanco, o temperatura CCT) atenuado por el brillo
  const encendida = !!s?.on && brillo > 0
  const base = s?.tira === 'CCT' ? kelvin(cct) : s?.tira === 'MONO' ? [255, 244, 229] : rgb(color).map(v => Math.min(255, v + (w * 0.8)))
  const nivel = encendida ? 0.25 + 0.75 * (brillo / 100) : 0
  const luz = `rgb(${base.map(v => Math.round(v * nivel + 28 * (1 - nivel))).join(',')})`

  return (
    <div className="panel">
      <section className="tarjeta panel-cab">
        <div className="panel-luz">
          <button className={'orbe' + (encendida ? ' on' : '')} style={{ '--luz': luz }} disabled={!conectado || sin}
            onClick={() => enviar(s?.on ? 'OFF' : 'ON')} aria-label={s?.on ? 'Apagar' : 'Encender'} aria-pressed={!!s?.on}>
            <span>⏻</span>
          </button>
          <div className="panel-id">
            <div className="fila" style={{ gap: 6 }}>
              <span className={'punto ' + (modo === 'ble' ? 'bien' : modo === 'demo' ? 'alerta' : '')} />
              <span className="mut peq">{conectado ? nombre : 'Sin conectar'}</span>
            </div>
            <div className="panel-perfil">{s ? (sin ? 'Sin tarjeta' : s.perfil) : 'Cubo AP'}</div>
            <div className="mut peq">{s && !sin ? (s.vmax ? `Máx ${s.vmax.toFixed(2)} V · ${s.imax.toFixed(1)} A · ${(s.vmax * s.imax).toFixed(0)} W` : 'Programa los límites de la tarjeta personal') : 'Conecta por Bluetooth o prueba la demo'}</div>
            <div className="chips" style={{ marginTop: 8 }}>
              {red && <span className={'etiqueta ' + (red.wifi ? 'si' : '')}>{red.wifi ? `Wi-Fi · ${red.ip}` : 'Sin Wi-Fi'}</span>}
              {s?.dmx && s.dmx !== 'off' && <span className={'etiqueta ' + (s.dmx_vivo ? 'si' : 'parcial')}>DMX {s.dmx_vivo ? 'recibiendo' : 'sin señal'}</span>}
              {s?.dmx_sal && s.dmx_sal !== 'off' && <span className="etiqueta plan">DMX sale: {s.dmx_sal}</span>}
              {s?.prog && <span className="etiqueta">⏰ {hhmm(s.on_min)}–{hhmm(s.off_min)}</span>}
              {red?.grupo && <span className="etiqueta">Grupo {red.grupo}</span>}
            </div>
          </div>
          <div className="fila panel-acciones">
            <button className="boton" onClick={demo}>Demo</button>
            <button className="boton pri" onClick={conectarBle}>Conectar Bluetooth</button>
          </div>
        </div>

        <div className="medidores">
          <Medidor valor={s?.v} max={s?.vmax || 24} unidad="V" etiqueta="Salida" dec={2} />
          <Medidor valor={s?.i} max={s?.imax || 5} unidad="A" etiqueta="Corriente" dec={2} alerta={(s?.imax || 5) * 0.85} mal={(s?.imax || 5) * 0.98} />
          <Medidor valor={s?.w} max={(s?.vmax || 12) * (s?.imax || 5)} unidad="W" etiqueta="Potencia" />
          <Medidor valor={s?.t} max={100} unidad="°C" etiqueta="Temperatura" dec={0} alerta={T_RECORTE - 10} mal={T_RECORTE} />
          <Medidor valor={s?.vin} max={40} unidad="V" etiqueta="Entrada" />
        </div>
        <div className="entre peq" style={{ marginTop: 6 }}>
          <span className="mut">Estado térmico</span><span className={'estado ' + term.cls}>{term.txt}</span>
        </div>
        {mensaje && <div className={mensaje.tipo === 'error' ? 'error' : 'okmsg'} style={{ marginTop: 10 }} onClick={() => setMensaje(null)}>{mensaje.texto}</div>}
        {s && s.falla !== 'ninguna' && <div className="error" style={{ marginTop: 10 }}>{FALLAS[s.falla] || s.falla} <button className="boton" style={{ marginLeft: 8, padding: '3px 10px' }} onClick={() => enviar('RESET')}>Reiniciar</button></div>}
      </section>

      <nav className="pestanas" role="tablist" aria-label="Secciones del panel">
        {PESTANAS.filter(([k]) => k !== 'avanzado' || s?.perfil === 'PERSONAL').map(([k, t]) =>
          <button key={k} role="tab" aria-selected={tab === k} className={'pestana' + (tab === k ? ' sel' : '')} onClick={() => elegir(k)}>{t}</button>)}
      </nav>

      <fieldset disabled={!conectado} className="panel-cuerpo" style={{ opacity: conectado ? 1 : 0.55 }}>
        {tab === 'luz' && <div className="rejilla dos">
          <div className="tarjeta">
            <div className="entre"><h3>Brillo</h3><b className="grande">{brillo} %</b></div>
            <input className="desl" type="range" min="0" max="100" value={brillo} style={{ '--p': brillo + '%' }}
              onChange={e => { tocar(); setBrillo(+e.target.value); enviarBrillo(e.target.value) }} aria-label="Brillo" />
            <div className="chips" style={{ marginTop: 10 }}>
              {[10, 25, 50, 75, 100].map(v => <button key={v} className={'chip' + (brillo === v ? ' sel' : '')} onClick={() => { setBrillo(v); enviar('BRILLO ' + v) }}>{v} %</button>)}
            </div>
            <label className="mut peq fila" style={{ gap: 6, marginTop: 12, flexWrap: 'nowrap' }}>
              <input type="checkbox" checked={todos} onChange={e => setTodos(e.target.checked)} style={{ width: 'auto' }} /> Aplicar a todo el grupo
            </label>
          </div>

          <div className="tarjeta">
            <h3>Efecto</h3>
            <div className="efectos">{MODOS.map(([k, t]) =>
              <button key={k} className={'efecto' + (s?.modo === k.toLowerCase() ? ' sel' : '')} onClick={() => enviar('MODO ' + k)}><i className={'ef ef-' + k.toLowerCase()} aria-hidden="true" />{t}</button>)}
            </div>
          </div>

          {(s?.tira === 'CCT' || s?.tira === 'RGBCCT') && <div className="tarjeta">
            <div className="entre"><h3>Temperatura de blanco</h3><b>{cct} K</b></div>
            <input className="desl cct" type="range" min="2700" max="6500" step="100" value={cct}
              onChange={e => { tocar(); setCct(+e.target.value); enviarCct(e.target.value) }} aria-label="Temperatura de blanco" />
            <div className="entre mut peq"><span>Cálido 2700 K</span><span>Neutro 4000 K</span><span>Frío 6500 K</span></div>
          </div>}

          {s?.tira !== 'CCT' && s?.tira !== 'MONO' && <div className="tarjeta">
            <h3>Color</h3>
            <div className="muestras">
              {MUESTRAS.map(m => <button key={m} aria-label={'Color ' + m} className={'muestra' + (color === m ? ' sel' : '')} onClick={() => { setColor(m); enviarColor([m, w]) }} style={{ background: m }} />)}
              <label className="muestra libre" title="Otro color">
                <input type="color" value={color} onChange={e => { tocar(); setColor(e.target.value); enviarColor([e.target.value, w]) }} aria-label="Otro color" />
              </label>
            </div>
            {s?.tira !== 'RGB' && <>
              <div className="entre" style={{ marginTop: 12 }}><label className="campo" style={{ margin: 0 }}>Blanco (W)</label><b>{Math.round(w / 2.55)} %</b></div>
              <input className="desl blanco" type="range" min="0" max="255" value={w}
                onChange={e => { tocar(); setW(+e.target.value); enviarColor([color, e.target.value]) }} aria-label="Canal blanco" />
            </>}
          </div>}
        </div>}

        {tab === 'tira' && <div className="rejilla dos">
          <div className="tarjeta">
            <h3>Tipo de tira</h3>
            <select value={s?.tira || 'RGBW'} onChange={e => enviar('TIRA ' + e.target.value)}>{TIRAS.map(([k, t]) => <option key={k} value={k}>{t}</option>)}</select>
            {DIRECCIONABLES.includes(s?.tira) && <>
              <label className="campo">Número de LEDs</label>
              <input type="number" min="1" max="600" defaultValue={60} onBlur={e => enviar('LEDS ' + e.target.value)} />
            </>}
            <p className="mut peq" style={{ marginTop: 8 }}>Analógicas: ánodo común (V+ y un negativo por color). Direccionables: V+, datos y GND.</p>
          </div>
          <div className="tarjeta">
            <div className="entre"><h3>Voltaje de salida</h3><b className="grande">{(+volt).toFixed(2)} V</b></div>
            <input className="desl" type="range" min={s?.vmin || 10} max={s?.vmax || 12} step="0.05" value={volt} disabled={sin || !s?.vmax}
              style={{ '--p': s?.vmax ? (100 * (volt - (s.vmin || 0)) / (s.vmax - (s.vmin || 0))) + '%' : '0%' }}
              onChange={e => { tocar(); setVolt(+e.target.value); enviarVolt(e.target.value) }} aria-label="Voltaje de salida" />
            <p className="mut peq" style={{ marginTop: 8 }}>La tarjeta fija el máximo por hardware; aquí solo se baja. Una tira de 12 V a 11–11.5 V calienta bastante menos y dura más.</p>
          </div>
        </div>}

        {tab === 'tiempo' && <div className="rejilla dos">
          <div className="tarjeta">
            <h3>Horario diario</h3>
            <div className="rejilla" style={{ gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              <div><label className="campo">Encender</label><input type="time" value={hon} onChange={e => setHon(e.target.value)} /></div>
              <div><label className="campo">Apagar</label><input type="time" value={hoff} onChange={e => setHoff(e.target.value)} /></div>
            </div>
            <div className="entre" style={{ marginTop: 10 }}>
              <span className="mut peq">{s?.prog ? `Enciende ${hhmm(s.on_min)} · apaga ${hhmm(s.off_min)}` : 'Sin horario'}</span>
              <div className="fila"><button className="boton" onClick={() => enviar('PROG OFF')}>Quitar</button>
                <button className="boton pri" onClick={() => { enviar('HORA ' + horaLocal()); enviar(`PROG ${hon} ${hoff}`) }}>Guardar</button></div>
            </div>
            <p className="mut peq" style={{ marginTop: 6 }}>Se envía la hora de este dispositivo; con Wi-Fi el cubo la toma de internet.</p>
          </div>
          <div className="tarjeta">
            <h3>Escenas</h3>
            <div className="escenas">
              {[1, 2, 3, 4, 5, 6, 7, 8].map(i => { const ok = (s?.escenas >> (i - 1)) & 1; return <button key={i} className={'escena' + (ok ? ' llena' : '')} disabled={!ok} onClick={() => enviar('ESCENA ' + i)}>{i}</button> })}
            </div>
            <div className="entre" style={{ marginTop: 10 }}>
              <span className="mut peq">Guardar la luz actual en</span>
              <div className="fila" style={{ flexWrap: 'nowrap' }}><select value={esc} onChange={e => setEsc(e.target.value)} style={{ width: 'auto' }}>{[1, 2, 3, 4, 5, 6, 7, 8].map(i => <option key={i} value={i}>Escena {i}</option>)}</select>
                <button className="boton" onClick={() => enviar('ESCENA GUARDAR ' + esc)}>Guardar</button></div>
            </div>
          </div>
        </div>}

        {tab === 'red' && <div className="rejilla dos">
          <div className="tarjeta">
            <h3>Wi-Fi</h3>
            <div className="rejilla" style={{ gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              <input placeholder="Red Wi-Fi" value={ssid} onChange={e => setSsid(e.target.value)} aria-label="Red Wi-Fi" />
              <input placeholder="Contraseña" type="password" value={clave} onChange={e => setClave(e.target.value)} aria-label="Contraseña" />
            </div>
            <div className="entre" style={{ marginTop: 8 }}>
              <span className="mut peq">{red ? (red.wifi ? `Conectado · ${red.ip}` : 'Sin Wi-Fi') : '—'}</span>
              <button className="boton pri" onClick={() => { if (!ssid.trim() || /\s/.test(ssid.trim())) { setMensaje({ tipo: 'error', texto: 'Escribe la red sin espacios' }); return } enviar(`WIFI ${ssid.trim()} ${clave}`) }}>Conectar</button>
            </div>
            <h3 style={{ marginTop: 16 }}>Grupo firmado</h3>
            <div className="rejilla" style={{ gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              <input placeholder="Grupo (p. ej. tienda-centro)" value={gnom} onChange={e => setGnom(e.target.value)} aria-label="Nombre del grupo" />
              <input placeholder="Clave del grupo (8+)" type="password" value={gclave} onChange={e => setGclave(e.target.value)} aria-label="Clave del grupo" />
            </div>
            <div className="entre" style={{ marginTop: 8 }}>
              <span className="mut peq">{red?.grupo ? `Grupo: ${red.grupo}` : 'Sin grupo'}</span>
              <div className="fila" style={{ flexWrap: 'nowrap' }}><button className="boton" onClick={() => { enviar('GRUPO OFF'); setTimeout(() => enviar('RED'), 300) }}>Quitar</button>
                <button className="boton" onClick={() => { if (!/^[\w-]{1,24}$/.test(gnom.trim()) || gclave.length < 8 || /\s/.test(gclave)) { setMensaje({ tipo: 'error', texto: 'Grupo: letras, números, - o _; clave de 8+ caracteres sin espacios' }); return } enviar(`GRUPO ${gnom.trim()} ${gclave}`); setTimeout(() => enviar('RED'), 300) }}>Guardar</button></div>
            </div>
          </div>
          <div className="tarjeta">
            <h3>Hogar inteligente</h3>
            <div className="entre" style={{ marginTop: 6 }}>
              <span className="peq">WLED · Home Assistant · Alexa<br /><span className="mut">{red ? (red.integraciones ? 'Activas' : 'Apagadas') : '—'}</span></span>
              <div className="fila" style={{ flexWrap: 'nowrap' }}><button className="boton" onClick={() => enviar('INTEGRACIONES OFF')}>Apagar</button><button className="boton" onClick={() => enviar('INTEGRACIONES ON')}>Activar</button></div>
            </div>
            <div className="entre" style={{ marginTop: 12 }}>
              <span className="peq">Matter (Apple Home, Google Home, Alexa)<br /><span className="mut">{matter ? matter.matter : 'Firmware con Matter'}</span></span>
              <button className="boton" onClick={() => enviar('MATTER')}>Código</button>
            </div>
            {matter?.codigo && <div className="aviso" style={{ marginTop: 8 }}>
              Código de vinculación: <b style={{ letterSpacing: 1 }}>{matter.codigo}</b>. En la app de tu casa: “Agregar accesorio” → “Más opciones” y escribe el código
              {matter.qr && <> (o abre el <a href={matter.qr} target="_blank" rel="noreferrer">código QR</a>)</>}. El cubo debe estar en el mismo Wi-Fi.
            </div>}
          </div>
        </div>}

        {tab === 'dmx' && <div className="rejilla dos">
          <div className="tarjeta">
            <h3>Recibir DMX</h3>
            <div className="rejilla" style={{ gridTemplateColumns: '1.3fr 1fr 1fr', gap: 8 }}>
              <div><label className="campo">Protocolo</label><select value={dmxp} onChange={e => setDmxp(e.target.value)}><option value="ARTNET">Art-Net</option><option value="SACN">sACN (E1.31)</option><option value="CABLE">Cable DMX512</option></select></div>
              <div><label className="campo">Universo</label><input type="number" min="0" value={dmxu} disabled={dmxp === 'CABLE'} onChange={e => setDmxu(e.target.value)} /></div>
              <div><label className="campo">Dirección</label><input type="number" min="1" max="512" value={dmxd} onChange={e => setDmxd(e.target.value)} /></div>
            </div>
            <div className="entre" style={{ marginTop: 8 }}>
              <span className="mut peq">{!s?.dmx || s.dmx === 'off' ? 'Sin DMX' : `${s.dmx === 'cable' ? 'Cable' : s.dmx === 'artnet' ? 'Art-Net U' + s.univ : 'sACN U' + s.univ} @${s.dir} · ${s.dmx_vivo ? 'recibiendo' : 'sin señal'}`}</span>
              <div className="fila" style={{ flexWrap: 'nowrap' }}><button className="boton" onClick={() => enviar('DMX OFF')}>Apagar</button><button className="boton pri" onClick={() => enviar(dmxp === 'CABLE' ? `DMX CABLE ${dmxd}` : `DMX ${dmxp} ${dmxu} ${dmxd}`)}>Aplicar</button></div>
            </div>
            <p className="mut peq" style={{ marginTop: 6 }}>Analógicas: atenuador + R, G, B, W (RGB+CCT: + blanco frío). Direccionables: 3 o 4 canales por LED.</p>
          </div>
          <div className="tarjeta">
            <h3>Enviar DMX a Nodos AP</h3>
            {s?.dmx_tx ? <>
              <div className="fila">
                <select style={{ flex: '1 1 180px', minWidth: 0, width: 'auto' }} value={dsal} onChange={e => setDsal(e.target.value)}><option value="ESPEJO">Espejo: copian este cubo</option><option value="PUENTE">Puente desde Art-Net/sACN</option></select>
                {dsal === 'ESPEJO' && <input type="number" min="1" max="128" value={dgru} onChange={e => setDgru(e.target.value)} title="Nodos (grupos de 4 canales)" style={{ width: 80 }} aria-label="Número de nodos" />}
              </div>
              <div className="entre" style={{ marginTop: 8 }}>
                <span className="mut peq">{s.dmx_sal && s.dmx_sal !== 'off' ? `Transmitiendo: ${s.dmx_sal}` : 'Sin salida DMX'}</span>
                <div className="fila" style={{ flexWrap: 'nowrap' }}><button className="boton" onClick={() => enviar('DMX SALIDA OFF')}>Parar</button>
                  <button className="boton pri" onClick={() => enviar(dsal === 'ESPEJO' ? `DMX SALIDA ESPEJO ${dgru}` : 'DMX SALIDA PUENTE')}>Enviar</button></div>
              </div>
              <p className="mut peq" style={{ marginTop: 6 }}>En espejo, los nodos van en las direcciones 1, 5, 9… (4 canales cada uno).</p>
            </> : <p className="mut peq">Disponible en el Cubo AP v3 con la salida DMX habilitada.</p>}
          </div>
        </div>}

        {tab === 'avanzado' && s?.perfil === 'PERSONAL' && <div className="rejilla dos">
          <div className="tarjeta">
            <h3>Tarjeta personalizada</h3>
            <div className="rejilla" style={{ gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              <div><label className="campo">Voltaje máximo (V)</label><input type="number" step="0.1" value={pv} onChange={e => setPv(e.target.value)} /></div>
              <div><label className="campo">Corriente máxima (A)</label><input type="number" step="0.1" value={pi} onChange={e => setPi(e.target.value)} /></div>
            </div>
            <div className="entre" style={{ marginTop: 8 }}>
              <span className="mut peq">{rb ? `R_B = ${rb.rb} Ω (1 %) → ${rb.vreal.toFixed(2)} V` : 'Fuera de 3–24.4 V'}</span>
              <button className="boton pri" disabled={!rb} onClick={() => enviar(`LIMITES ${rb.vreal.toFixed(2)} ${pi}`)}>Programar</button>
            </div>
          </div>
        </div>}
      </fieldset>
    </div>
  )
}
