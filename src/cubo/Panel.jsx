import { useEffect, useRef, useState } from 'react'
import useCubo, { FALLAS, DIRECCIONABLES } from './useCubo'
import { rbParaVoltaje } from '../lib/led'

const MODOS = [['FIJO', 'Fijo'], ['RESPIRA', 'Respira'], ['ARCOIRIS', 'Arcoíris'], ['FUEGO', 'Fuego'], ['COMETA', 'Cometa']]
const TIRAS = [['RGBW', 'RGBW (4 canales)'], ['RGB', 'RGB 5050'], ['CCT', 'Blanco dual CCT'], ['MONO', 'Un color'],
  ['WS2812B', 'WS2812B · 5 V'], ['SK6812', 'SK6812 RGBW · 5 V'], ['WS2811', 'WS2811 · 12 V'], ['WS2815', 'WS2815 · 12 V'], ['RGBCCT', 'RGB + CCT · 5 canales (placa v2)']]
const MUESTRAS = ['#ffffff', '#ff3b30', '#ff9500', '#ffd60a', '#34c759', '#0a84ff', '#bf5af2', '#ff2d92']
const hhmm = m => String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0')
const hex = c => '#' + c.slice(0, 3).map(x => x.toString(16).padStart(2, '0')).join('')

function useRetardo(fn, ms) {                     // evita inundar el Bluetooth al mover deslizadores
  const t = useRef(null)
  return v => { clearTimeout(t.current); t.current = setTimeout(() => fn(v), ms) }
}

export default function Panel() {
  const { estado: s, red, modo, nombre, mensaje, setMensaje, enviar, conectarBle, demo } = useCubo()
  const [brillo, setBrillo] = useState(60), [volt, setVolt] = useState(12), [cct, setCct] = useState(4000)
  const [color, setColor] = useState('#ffffff'), [w, setW] = useState(0)
  const [hon, setHon] = useState('18:30'), [hoff, setHoff] = useState('01:00')
  const [esc, setEsc] = useState(1), [dmxp, setDmxp] = useState('ARTNET'), [dmxu, setDmxu] = useState(1), [dmxd, setDmxd] = useState(1)
  const [pv, setPv] = useState(13), [pi, setPi] = useState(2), [ssid, setSsid] = useState(''), [clave, setClave] = useState('')
  const editando = useRef(false)
  useEffect(() => {
    if (!s || editando.current) return
    setBrillo(s.brillo); setVolt(s.vset); if (s.cct) setCct(s.cct)
    if (s.rgbw) { setColor(hex(s.rgbw)); setW(s.rgbw[3]) }
  }, [s])
  const tocar = () => { editando.current = true; clearTimeout(tocar.t); tocar.t = setTimeout(() => { editando.current = false }, 1500) }
  const enviarBrillo = useRetardo(v => enviar('BRILLO ' + v), 90)
  const enviarVolt = useRetardo(v => enviar('V ' + v), 160)
  const enviarCct = useRetardo(v => enviar('CCT ' + v), 110)
  const enviarColor = useRetardo(([c, ww]) => enviar(`RGBW ${parseInt(c.slice(1, 3), 16)} ${parseInt(c.slice(3, 5), 16)} ${parseInt(c.slice(5, 7), 16)} ${ww}`), 90)
  const conectado = modo !== 'ninguno'
  const sin = !s || s.perfil === '-'
  const carga = s && s.imax ? Math.min(100, (100 * s.i) / s.imax) : 0
  const rb = rbParaVoltaje(+pv)
  const horaLocal = () => Math.floor(Date.now() / 1000) - new Date().getTimezoneOffset() * 60

  return (
    <div className="panel">
      <div className="tarjeta">
        <div className="entre">
          <div>
            <div className="mut peq">{conectado ? nombre : 'Sin conectar'}</div>
            <div style={{ fontSize: 26, fontWeight: 800 }}>{s ? (sin ? 'Sin tarjeta' : s.perfil) : 'Cubo AP'}</div>
            <div className="mut peq">{s && !sin ? (s.vmax ? `Máx ${s.vmax.toFixed(2)} V · ${s.imax.toFixed(1)} A · ${(s.vmax * s.imax).toFixed(0)} W` : 'Programa los límites de la tarjeta personal') : 'Conecta por Bluetooth o prueba la demo'}</div>
          </div>
          <div className="fila">
            <button className="boton" onClick={demo}>Demo</button>
            <button className="boton pri" onClick={conectarBle}>Conectar Bluetooth</button>
            <button className={'boton'} disabled={!conectado || sin} onClick={() => enviar(s?.on ? 'OFF' : 'ON')}
              style={{ width: 46, height: 46, borderRadius: '50%', justifyContent: 'center', fontSize: 20, background: s?.on ? 'var(--ac)' : undefined, color: s?.on ? 'var(--ac-tx)' : undefined }} aria-label="Encender o apagar">⏻</button>
          </div>
        </div>
        <div className="datos" style={{ marginTop: 14 }}>
          <div className="dato"><b>{s ? s.v.toFixed(2) : '–'}</b><span>V salida</span></div>
          <div className="dato"><b>{s ? s.i.toFixed(2) : '–'}</b><span>A</span></div>
          <div className="dato"><b>{s ? s.w.toFixed(1) : '–'}</b><span>W</span></div>
          <div className="dato"><b>{s ? s.t.toFixed(0) : '–'}</b><span>°C internos</span></div>
          <div className="dato"><b>{s ? s.vin.toFixed(1) : '–'}</b><span>V entrada</span></div>
        </div>
        <div style={{ height: 6, borderRadius: 3, background: 'var(--bg2)', marginTop: 10, overflow: 'hidden' }} title="Corriente respecto al límite">
          <div style={{ height: '100%', width: carga + '%', background: carga > 85 ? 'var(--warn)' : 'var(--ac)', transition: 'width .3s' }} />
        </div>
        {mensaje && <div className={mensaje.tipo === 'error' ? 'error' : 'okmsg'} style={{ marginTop: 10 }} onClick={() => setMensaje(null)}>{mensaje.texto}</div>}
        {s && s.falla !== 'ninguna' && <div className="error" style={{ marginTop: 10 }}>{FALLAS[s.falla] || s.falla} <button className="boton" style={{ marginLeft: 8, padding: '3px 10px' }} onClick={() => enviar('RESET')}>Reiniciar</button></div>}
      </div>

      <fieldset disabled={!conectado} style={{ border: 0, opacity: conectado ? 1 : 0.55 }}>
        <div className="rejilla dos" style={{ marginTop: 14 }}>
          <div className="tarjeta">
            <h3>Luz</h3>
            <div className="entre"><label className="campo">Brillo</label><b>{brillo} %</b></div>
            <input type="range" min="0" max="100" value={brillo} onChange={e => { tocar(); setBrillo(+e.target.value); enviarBrillo(e.target.value) }} />
            <label className="campo">Efecto</label>
            <div className="chips">{MODOS.map(([k, t]) => <button key={k} className={'chip' + (s?.modo === k.toLowerCase() ? ' sel' : '')} onClick={() => enviar('MODO ' + k)}>{t}</button>)}</div>
            {(s?.tira === 'CCT' || s?.tira === 'RGBCCT') && <>
              <div className="entre"><label className="campo">Temperatura de blanco</label><b>{cct} K</b></div>
              <input type="range" min="2700" max="6500" step="100" value={cct} onChange={e => { tocar(); setCct(+e.target.value); enviarCct(e.target.value) }} />
              <div style={{ height: 8, borderRadius: 4, background: 'linear-gradient(90deg,#ffb15e,#fff3e0,#cfe3ff)' }} />
            </>}
            {s?.tira !== 'CCT' && s?.tira !== 'MONO' && <>
              <label className="campo">Color</label>
              <div className="fila">
                <input type="color" value={color} onChange={e => { tocar(); setColor(e.target.value); enviarColor([e.target.value, w]) }} aria-label="Color" />
                <span className="mut peq">Blanco W</span>
                <input type="range" min="0" max="255" value={w} style={{ flex: 1, width: 'auto' }} onChange={e => { tocar(); setW(+e.target.value); enviarColor([color, e.target.value]) }} />
              </div>
              <div className="fila" style={{ marginTop: 8, gap: 6 }}>
                {MUESTRAS.map(m => <button key={m} aria-label={'Color ' + m} onClick={() => { setColor(m); enviarColor([m, w]) }} style={{ flex: 1, height: 26, borderRadius: 7, border: '1px solid var(--ln)', background: m, cursor: 'pointer' }} />)}
              </div>
            </>}
          </div>

          <div className="tarjeta">
            <h3>Tira y voltaje</h3>
            <label className="campo">Tipo de tira</label>
            <select value={s?.tira || 'RGBW'} onChange={e => enviar('TIRA ' + e.target.value)}>{TIRAS.map(([k, t]) => <option key={k} value={k}>{t}</option>)}</select>
            {DIRECCIONABLES.includes(s?.tira) && <>
              <label className="campo">Número de LEDs</label>
              <input type="number" min="1" max="600" defaultValue={60} onBlur={e => enviar('LEDS ' + e.target.value)} />
            </>}
            <div className="entre"><label className="campo">Voltaje de salida</label><b>{(+volt).toFixed(2)} V</b></div>
            <input type="range" min={s?.vmin || 10} max={s?.vmax || 12} step="0.05" value={volt} disabled={sin || !s?.vmax}
              onChange={e => { tocar(); setVolt(+e.target.value); enviarVolt(e.target.value) }} />
            <p className="mut peq">La tarjeta fija el máximo por hardware; aquí solo se baja. A 11–11.5 V una tira de 12 V calienta mucho menos.</p>
          </div>

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
            <h3>Red e integraciones</h3>
            <div className="rejilla" style={{ gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              <input placeholder="Red Wi-Fi" value={ssid} onChange={e => setSsid(e.target.value)} />
              <input placeholder="Contraseña" type="password" value={clave} onChange={e => setClave(e.target.value)} />
            </div>
            <div className="entre" style={{ marginTop: 8 }}>
              <span className="mut peq">{red ? (red.wifi ? `Conectado · ${red.ip}` : 'Sin Wi-Fi') : '—'}</span>
              <button className="boton" onClick={() => { if (!ssid.trim() || /\s/.test(ssid.trim())) { setMensaje({ tipo: 'error', texto: 'Escribe la red sin espacios' }); return } enviar(`WIFI ${ssid.trim()} ${clave}`) }}>Conectar Wi-Fi</button>
            </div>
            <div className="entre" style={{ marginTop: 10 }}>
              <span className="mut peq">WLED · Home Assistant · Alexa {red ? (red.integraciones ? '(activas)' : '(apagadas)') : ''}</span>
              <div className="fila" style={{ flexWrap: "nowrap" }}><button className="boton" onClick={() => enviar("INTEGRACIONES OFF")}>Apagar</button><button className="boton" onClick={() => enviar('INTEGRACIONES ON')}>Activar</button></div>
            </div>
          </div>

          <div className="tarjeta">
            <h3>Escenas</h3>
            <div className="chips" style={{ marginTop: 6 }}>
              {[1, 2, 3, 4, 5, 6, 7, 8].map(i => { const ok = (s?.escenas >> (i - 1)) & 1; return <button key={i} className={'chip' + (ok ? ' sel' : '')} disabled={!ok} onClick={() => enviar('ESCENA ' + i)}>Escena {i}</button> })}
            </div>
            <div className="entre" style={{ marginTop: 10 }}>
              <span className="mut peq">Guardar la luz actual en</span>
              <div className="fila" style={{ flexWrap: 'nowrap' }}><select value={esc} onChange={e => setEsc(e.target.value)} style={{ width: 'auto' }}>{[1, 2, 3, 4, 5, 6, 7, 8].map(i => <option key={i} value={i}>Escena {i}</option>)}</select>
                <button className="boton" onClick={() => enviar('ESCENA GUARDAR ' + esc)}>Guardar</button></div>
            </div>
          </div>

          <div className="tarjeta">
            <h3>DMX</h3>
            <div className="rejilla" style={{ gridTemplateColumns: '1.3fr 1fr 1fr', gap: 8 }}>
              <div><label className="campo">Protocolo</label><select value={dmxp} onChange={e => setDmxp(e.target.value)}><option value="ARTNET">Art-Net</option><option value="SACN">sACN (E1.31)</option><option value="CABLE">Cable DMX512 (v2)</option></select></div>
              <div><label className="campo">Universo</label><input type="number" min="0" value={dmxu} disabled={dmxp === 'CABLE'} onChange={e => setDmxu(e.target.value)} /></div>
              <div><label className="campo">Dirección</label><input type="number" min="1" max="512" value={dmxd} onChange={e => setDmxd(e.target.value)} /></div>
            </div>
            <div className="entre" style={{ marginTop: 8 }}>
              <span className="mut peq">{!s?.dmx || s.dmx === 'off' ? 'Sin DMX' : `${s.dmx === 'cable' ? 'Cable' : s.dmx === 'artnet' ? 'Art-Net U' + s.univ : 'sACN U' + s.univ} @${s.dir} · ${s.dmx_vivo ? 'recibiendo' : 'sin señal'}`}</span>
              <div className="fila" style={{ flexWrap: 'nowrap' }}><button className="boton" onClick={() => enviar('DMX OFF')}>Apagar</button><button className="boton pri" onClick={() => enviar(dmxp === 'CABLE' ? `DMX CABLE ${dmxd}` : `DMX ${dmxp} ${dmxu} ${dmxd}`)}>Aplicar</button></div>
            </div>
            <p className="mut peq" style={{ marginTop: 6 }}>Analógicas: atenuador + R, G, B, W (RGB+CCT: + blanco frío). Direccionables: 3 o 4 canales por LED. Para consolas, xLights, QLC+, Resolume o MadMapper.</p>
          </div>

          {s?.perfil === 'PERSONAL' && <div className="tarjeta">
            <h3>Tarjeta personalizada</h3>
            <div className="rejilla" style={{ gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              <div><label className="campo">Voltaje máximo (V)</label><input type="number" step="0.1" value={pv} onChange={e => setPv(e.target.value)} /></div>
              <div><label className="campo">Corriente máxima (A)</label><input type="number" step="0.1" value={pi} onChange={e => setPi(e.target.value)} /></div>
            </div>
            <div className="entre" style={{ marginTop: 8 }}>
              <span className="mut peq">{rb ? `R_B = ${rb.rb} Ω (1 %) → ${rb.vreal.toFixed(2)} V` : 'Fuera de 3–24.4 V'}</span>
              <button className="boton pri" disabled={!rb} onClick={() => enviar(`LIMITES ${rb.vreal.toFixed(2)} ${pi}`)}>Programar</button>
            </div>
          </div>}
        </div>
      </fieldset>
    </div>
  )
}
