import { useEffect, useMemo, useState } from 'react'
import { planificar, resumenLote, cotizar, COSTOS_EJEMPLO } from '../lib/led'

const EJEMPLO = [
  { nombre: 'Cliente A · letreros', cantidad: 20, v: 12, a: 5, cable: 2 },
  { nombre: 'Cliente B', cantidad: 1, v: 12, a: 1, cable: 2 },
  { nombre: 'Cliente C', cantidad: 1, v: 15, a: 1, cable: 2 },
]
const leer = () => { try { return JSON.parse(localStorage.getItem('pedidosAP')) || EJEMPLO } catch { return EJEMPLO } }

function desdeEnlace(lista) {        // #/configurador?v=12&a=1&n=20&nombre=...
  const q = new URLSearchParams(location.hash.split('?')[1] || '')
  if (!q.get('v')) return lista
  history.replaceState(null, '', '#configurador')
  return [...lista, { nombre: q.get('nombre') || 'Nuevo', cantidad: +q.get('n') || 1, v: +q.get('v'), a: +q.get('a') || 1, cable: 2 }]
}

const NOMBRES_COSTO = [['S', 'Cartucho S'], ['M', 'Cartucho M'], ['L', 'Cartucho L'], ['placa', 'Placa ensamblada + ESP32'], ['caja80', 'Caja 80 mm impresa'],
  ['caja100', 'Caja 100 mm aluminio'], ['tarjeta', 'Tarjeta (2 resistencias)'], ['accesorios', 'Prensaestopas, membrana, tornillos'], ['manoObra', 'Mano de obra por cubo']]
const leerJson = (k, def) => { try { return { ...def, ...JSON.parse(localStorage.getItem(k)) } } catch { return def } }
const mxn = v => v.toLocaleString('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 })

function Cotizador({ pedidos }) {
  const [costos, setCostos] = useState(() => leerJson('costosAP', COSTOS_EJEMPLO))
  const [cfg, setCfg] = useState(() => leerJson('cotizaAP', { margen: 35, iva: 16 }))
  useEffect(() => { try { localStorage.setItem('costosAP', JSON.stringify(costos)); localStorage.setItem('cotizaAP', JSON.stringify(cfg)) } catch { /* privado */ } }, [costos, cfg])
  const q = cotizar(pedidos.map(p => ({ ...p, v: +p.v, a: +p.a, cantidad: +p.cantidad, metrosCable: +p.cable })), costos, { margen: cfg.margen / 100, iva: cfg.iva / 100 })
  const ejemplo = NOMBRES_COSTO.every(([k]) => costos[k] === COSTOS_EJEMPLO[k])
  return (
    <section className="seccion rejilla dos">
      <div className="tarjeta">
        <h2>Cotización</h2>
        {ejemplo && <div className="aviso" style={{ margin: '8px 0' }}>Los costos son de ejemplo: cámbialos por los tuyos (se guardan en este navegador).</div>}
        <table className="tabla" style={{ marginTop: 8 }}>
          <thead><tr><th>Pedido</th><th>Cubos</th><th>Costo</th><th>Precio sin IVA</th></tr></thead>
          <tbody>{q.detalle.map((d, i) => <tr key={i}><td>{d.nombre}</td><td>{d.plan.errores.length ? '—' : d.plan.cubos}</td><td>{mxn(d.costo)}</td><td>{mxn(d.precio)}</td></tr>)}</tbody>
        </table>
        <div className="datos" style={{ marginTop: 12 }}>
          <div className="dato"><b>{mxn(q.costo)}</b><span>costo</span></div>
          <div className="dato"><b>{mxn(q.ganancia)}</b><span>ganancia</span></div>
          <div className="dato"><b>{mxn(q.total)}</b><span>total con IVA</span></div>
        </div>
      </div>
      <div className="tarjeta no-imprimir">
        <h2>Tus costos por pieza (MXN)</h2>
        <div className="rejilla" style={{ gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          {NOMBRES_COSTO.map(([k, t]) => <div key={k}><label className="campo">{t}</label><input type="number" min="0" value={costos[k]} onChange={e => setCostos(c => ({ ...c, [k]: +e.target.value }))} /></div>)}
          <div><label className="campo">Margen %</label><input type="number" min="0" value={cfg.margen} onChange={e => setCfg(c => ({ ...c, margen: +e.target.value }))} /></div>
          <div><label className="campo">IVA %</label><input type="number" min="0" value={cfg.iva} onChange={e => setCfg(c => ({ ...c, iva: +e.target.value }))} /></div>
        </div>
        <button className="boton" style={{ marginTop: 10 }} onClick={() => setCostos(COSTOS_EJEMPLO)}>Restaurar ejemplo</button>
      </div>
    </section>)
}

export default function Configurador() {
  const [pedidos, setPedidos] = useState(() => desdeEnlace(leer()))
  useEffect(() => { try { localStorage.setItem('pedidosAP', JSON.stringify(pedidos)) } catch { /* privado */ } }, [pedidos])
  const planes = useMemo(() => pedidos.map(p => planificar({ v: +p.v, a: +p.a, cantidad: +p.cantidad, metrosCable: +p.cable })), [pedidos])
  const lote = useMemo(() => resumenLote(pedidos.map(p => ({ v: +p.v, a: +p.a, cantidad: +p.cantidad, metrosCable: +p.cable }))), [pedidos])
  const cambiar = (i, k, v) => setPedidos(ps => ps.map((p, j) => j === i ? { ...p, [k]: v } : p))
  const csv = () => {
    const filas = [['Pedido', 'Cantidad', 'V', 'A', 'Cubos', 'Cartucho', 'Tarjeta', 'R_B (ohm)', 'R_ID (ohm)', 'Cable AWG', 'Notas']]
    pedidos.forEach((p, i) => { const pl = planes[i]; filas.push([p.nombre, p.cantidad, p.v, p.a, pl.cubos, pl.cartucho?.id || '', pl.tarjeta?.nombre || '', pl.tarjeta?.rb || '', pl.tarjeta?.rid || '', pl.awg || '', [...pl.errores, ...pl.avisos].join(' / ')]) })
    const blob = new Blob(['﻿' + filas.map(f => f.map(x => `"${String(x).replace(/"/g, '""')}"`).join(',')).join('\n')], { type: 'text/csv' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'pedido_cubo_ap.csv'; a.click(); URL.revokeObjectURL(a.href)
  }
  return (<>
    <div className="cab"><div><h1>Configurador de pedidos</h1>
      <p className="mut" style={{ marginTop: 8, maxWidth: 760 }}>Escribe lo que pide cada cliente (voltaje y corriente por letrero). Te digo cuántos cubos, qué cartucho, qué tarjeta con sus resistencias y qué cable, y armo la lista de compra del lote.</p></div>
      <div className="fila no-imprimir"><button className="boton" onClick={() => setPedidos(EJEMPLO)}>Ejemplo</button><button className="boton" onClick={csv}>Descargar CSV</button><button className="boton" onClick={() => print()}>Imprimir</button></div>
    </div>

    <div className="tarjeta desliza seccion" style={{ marginTop: 18 }}>
      <table className="tabla">
        <thead><tr><th>Pedido</th><th>Cant.</th><th>V</th><th>A</th><th>Cable (m)</th><th>Resultado</th><th className="no-imprimir"></th></tr></thead>
        <tbody>{pedidos.map((p, i) => { const pl = planes[i]; return (
          <tr key={i}>
            <td style={{ minWidth: 150 }}><input value={p.nombre} onChange={e => cambiar(i, 'nombre', e.target.value)} aria-label="Nombre del pedido" /></td>
            <td style={{ width: 80 }}><input type="number" min="1" value={p.cantidad} onChange={e => cambiar(i, 'cantidad', e.target.value)} aria-label="Cantidad" /></td>
            <td style={{ width: 84 }}><input type="number" step="0.1" value={p.v} onChange={e => cambiar(i, 'v', e.target.value)} aria-label="Voltaje" /></td>
            <td style={{ width: 84 }}><input type="number" step="0.1" value={p.a} onChange={e => cambiar(i, 'a', e.target.value)} aria-label="Corriente" /></td>
            <td style={{ width: 84 }}><input type="number" step="0.5" value={p.cable} onChange={e => cambiar(i, 'cable', e.target.value)} aria-label="Metros de cable" /></td>
            <td style={{ minWidth: 300 }} className="peq">
              {pl.errores.length ? <span style={{ color: 'var(--bad)' }}>{pl.errores.join(' · ')}</span> : <>
                <b>{pl.cubos} cubo(s)</b>{pl.cubosPorLetrero > 1 ? ` (${pl.cubosPorLetrero} por letrero)` : ''} · cartucho <b>{pl.cartucho.id}</b> · {pl.wCubo.toFixed(0)} W/cubo<br />
                Tarjeta <b>{pl.tarjeta.nombre}</b>{pl.tarjeta.personal ? ` ${pl.tarjeta.vmax} V` : ''}: R_B {pl.tarjeta.rb} Ω, R_ID {pl.tarjeta.rid / 1000}k · cable {pl.awg ?? '—'} AWG · app {pl.vMin?.toFixed(1)}–{pl.tarjeta.vmax} V
                {pl.avisos.map(a => <div key={a} style={{ color: 'var(--warn)' }}>⚠ {a}</div>)}
              </>}
            </td>
            <td className="no-imprimir"><button className="boton" onClick={() => setPedidos(ps => ps.filter((_, j) => j !== i))} aria-label="Quitar">✕</button></td>
          </tr>) })}</tbody>
      </table>
      <button className="boton no-imprimir" style={{ marginTop: 10 }} onClick={() => setPedidos(ps => [...ps, { nombre: 'Nuevo pedido', cantidad: 1, v: 12, a: 1, cable: 2 }])}>+ Agregar pedido</button>
    </div>

    <div className="rejilla dos seccion">
      <div className="tarjeta">
        <h2>Lista de compra del lote</h2>
        <div className="datos" style={{ margin: '10px 0' }}>
          <div className="dato"><b>{lote.total}</b><span>cubos</span></div>
          <div className="dato"><b>{lote.w.toFixed(0)}</b><span>W de salida</span></div>
          <div className="dato"><b>{(lote.w / 0.9 / 127).toFixed(1)}</b><span>A de la red 127 V</span></div>
        </div>
        <table className="tabla"><tbody>
          {Object.entries(lote.cubos).map(([k, n]) => <tr key={k}><td>Cartucho {k}</td><td>{n}</td></tr>)}
          {Object.entries(lote.tarjetas).map(([k, n]) => <tr key={k}><td>Tarjeta {k}</td><td>{n}</td></tr>)}
          {lote.total > 0 && <><tr><td>Placa de control + ESP32-C3 SuperMini</td><td>{lote.total}</td></tr>
            <tr><td>Prensaestopas M16 (entrada y salida)</td><td>{lote.total * 2}</td></tr><tr><td>Membrana de ventilación M12</td><td>{lote.total}</td></tr></>}
        </tbody></table>
      </div>
      <div className="tarjeta">
        <h2>Cómo decide</h2>
        <ul className="lista peq">
          <li>Un cubo da hasta 5 A; si el letrero pide más, se reparte en varios cubos.</li>
          <li>Cartucho: potencia de salida ÷ 90 % de eficiencia + 10 % de margen. Avisa si trabaja arriba del 85 %.</li>
          <li>Tarjeta estándar si existe con el mismo voltaje (±3 %) y corriente suficiente; si no, PERSONAL con R_B E96 calculada.</li>
          <li>Cable: calibre mínimo para que la caída sea ≤3 % (ida y vuelta).</li>
          <li>Salidas mayores a 22.8 V necesitan cartucho de 28–36 V.</li>
        </ul>
      </div>
    </div>
    <Cotizador pedidos={pedidos} />
  </>)
}
