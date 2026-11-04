import { useCallback, useEffect, useRef, useState } from 'react'

// Conexión con el Cubo AP: Bluetooth LE (Nordic UART) o demo simulada. Mismo protocolo de texto que el firmware.
const SVC = '6e400001-b5a3-f393-e0a9-e50e24dcca9e', RX = '6e400002-b5a3-f393-e0a9-e50e24dcca9e', TX = '6e400003-b5a3-f393-e0a9-e50e24dcca9e'
export const FALLAS = {
  sin_tarjeta: 'Sin tarjeta de configuración', tarjeta_inconsistente: 'La tarjeta no coincide con el voltaje medido',
  sobrecorriente: 'Sobrecorriente: revisa la tira o baja el brillo', sobretemperatura: 'Temperatura alta: se apagó para protegerse',
  subvoltaje_entrada: 'El cartucho no da voltaje suficiente', corto: 'Corto en la salida',
}
export const DIRECCIONABLES = ['WS2812B', 'SK6812', 'WS2811', 'WS2815']

function simulador() {
  const s = { on: 1, perfil: '12V 5A', vmax: 12, vmin: 10.62, imax: 5, vset: 12, v: 12, i: 0, w: 0, vin: 24.1, t: 38, brillo: 60, rgbw: [255, 180, 90, 0], modo: 'fijo', falla: 'ninguna', tira: 'RGBW', cct: 4000, prog: false, on_min: 0, off_min: 0, hora: -1 }
  const paso = () => {
    const c = s.tira === 'CCT' || s.tira === 'MONO' ? 1 : Math.min(1, s.rgbw.reduce((x, y) => x + y, 0) / (3 * 255) || 1)
    s.v = s.on ? +(s.vset - 0.02).toFixed(2) : 0
    s.i = s.on ? +(4.2 * s.brillo / 100 * c * (s.vset / 12) ** 2).toFixed(2) : 0
    s.w = +(s.v * s.i).toFixed(1); s.t = +(30 + s.w * 0.35).toFixed(1)
    const d = new Date(); s.hora = s.hora >= 0 ? d.getHours() * 60 + d.getMinutes() : -1
    return { ...s }
  }
  const cmd = c => {
    const [k, ...a] = c.trim().split(/\s+/); const K = k.toUpperCase()
    if (K === 'ON') s.on = 1; else if (K === 'OFF') s.on = 0
    else if (K === 'BRILLO') s.brillo = +a[0]
    else if (K === 'V') s.vset = Math.max(s.vmin, Math.min(s.vmax, +a[0]))
    else if (K === 'RGBW') s.rgbw = a.map(Number)
    else if (K === 'MODO') s.modo = a[0].toLowerCase()
    else if (K === 'TIRA') { if (['WS2812B', 'SK6812'].includes(a[0])) return `ERR ${a[0]} necesita tarjeta de 5 V`; s.tira = a[0] }
    else if (K === 'CCT') s.cct = +a[0]
    else if (K === 'HORA') s.hora = 0
    else if (K === 'PROG') { if (a[0] === 'OFF') s.prog = false; else { const f = x => { const [h, m] = x.split(':'); return h * 60 + +m }; s.prog = true; s.on_min = f(a[0]); s.off_min = f(a[1]) } }
    else if (K === 'RESET') s.falla = 'ninguna'
    else if (K === 'RED') return JSON.stringify({ wifi: false, ip: '', nombre: 'CuboAP-DEMO', integraciones: false, zona: -6 })
    else if (K === 'ESTADO') return JSON.stringify(paso())
    return 'OK'
  }
  return { cmd, paso }
}

export default function useCubo() {
  const [estado, setEstado] = useState(null)
  const [red, setRed] = useState(null)
  const [modo, setModo] = useState('ninguno')     // ninguno | ble | demo
  const [nombre, setNombre] = useState('')
  const [mensaje, setMensaje] = useState(null)
  const enlace = useRef(null), cola = useRef(Promise.resolve()), buf = useRef(''), sim = useRef(null), reloj = useRef(null)

  const recibir = useCallback(t => {
    t = (t || '').trim(); if (!t) return
    if (t[0] === '{') { try { const j = JSON.parse(t); if ('wifi' in j) setRed(j); else setEstado(j) } catch { /* trozo incompleto */ } }
    else if (t.startsWith('ERR')) setMensaje({ tipo: 'error', texto: t.replace(/^ERR\s*/, 'Rechazado: ') })
  }, [])

  const enviar = useCallback(c => {
    if (sim.current) { const r = sim.current.cmd(c); recibir(r); if (r.startsWith('OK')) recibir(JSON.stringify(sim.current.paso())); return Promise.resolve() }
    if (!enlace.current) return Promise.resolve()
    cola.current = cola.current.then(() => enlace.current.enviar(c)).then(() => {
      if (!/^ESTADO|^RED/i.test(c)) return enlace.current?.enviar('ESTADO')
    }).catch(e => setMensaje({ tipo: 'error', texto: 'Error: ' + e.message }))
    return cola.current
  }, [recibir])

  const conectarBle = useCallback(async () => {
    if (!navigator.bluetooth) { setMensaje({ tipo: 'error', texto: 'Este navegador no tiene Bluetooth web. Usa Chrome o Edge en Android, Windows o macOS, o prueba la demo.' }); return }
    try {
      const dev = await navigator.bluetooth.requestDevice({ filters: [{ namePrefix: 'CuboAP' }], optionalServices: [SVC] })
      dev.addEventListener('gattserverdisconnected', () => { enlace.current = null; setModo('ninguno'); setMensaje({ tipo: 'error', texto: 'Conexión perdida' }) })
      const g = await dev.gatt.connect(), s = await g.getPrimaryService(SVC)
      const rx = await s.getCharacteristic(RX), tx = await s.getCharacteristic(TX)
      await tx.startNotifications()
      const dec = new TextDecoder(), enc = new TextEncoder()
      tx.addEventListener('characteristicvaluechanged', e => {
        buf.current += dec.decode(e.target.value); let k
        while ((k = buf.current.indexOf('\n')) >= 0) { recibir(buf.current.slice(0, k)); buf.current = buf.current.slice(k + 1) }
      })
      sim.current = null; clearInterval(reloj.current)
      enlace.current = { enviar: c => rx.writeValueWithResponse(enc.encode(c + '\n')) }
      setNombre(dev.name); setModo('ble'); setMensaje(null)
      enviar('ESTADO'); enviar('RED')
    } catch (e) { if (e.name !== 'NotFoundError') setMensaje({ tipo: 'error', texto: 'No se conectó: ' + e.message }) }
  }, [enviar, recibir])

  const demo = useCallback(() => {
    enlace.current = null; sim.current = simulador(); setNombre('CuboAP-DEMO (simulado)'); setModo('demo'); setMensaje(null)
    recibir(sim.current.cmd('ESTADO')); recibir(sim.current.cmd('RED'))
    clearInterval(reloj.current); reloj.current = setInterval(() => sim.current && recibir(JSON.stringify(sim.current.paso())), 1000)
  }, [recibir])

  useEffect(() => () => clearInterval(reloj.current), [])
  return { estado, red, modo, nombre, mensaje, setMensaje, enviar, conectarBle, demo }
}
