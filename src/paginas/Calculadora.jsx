import { useMemo, useState } from 'react'
import { TIRAS } from '../datos/catalogo'
import { consumo, planificar, caidaCable, awgMinimo, rbParaVoltaje, vMinApp, AWG } from '../lib/led'

export default function Calculadora() {
  const [id, setId] = useState('2835-60-12'), [metros, setMetros] = useState(7), [uso, setUso] = useState(100)
  const [cable, setCable] = useState(3), [awg, setAwg] = useState(18), [vp, setVp] = useState(13)
  const tira = TIRAS.find(t => t.id === id)
  const c = useMemo(() => consumo(tira, +metros, uso / 100), [tira, metros, uso])
  const plan = planificar({ v: tira.v, a: c.aPorCubo, cantidad: c.cubos, metrosCable: +cable })
  const caida = caidaCable(c.aPorCubo, +cable, +awg)
  const minimo = awgMinimo(c.aPorCubo, +cable, tira.v)
  const rb = rbParaVoltaje(+vp)
  return (<>
    <h1>Calculadora de tiras LED</h1>
    <p className="mut" style={{ marginTop: 8, maxWidth: 760 }}>Consumo, número de cubos, reinyección de corriente y cable para las tiras más vendidas. Valores típicos: confirma con la ficha de tu rollo.</p>
    <div className="rejilla dos seccion" style={{ marginTop: 20 }}>
      <div className="tarjeta">
        <h2>Tu instalación</h2>
        <label className="campo">Tira</label>
        <select value={id} onChange={e => setId(e.target.value)}>{TIRAS.map(t => <option key={t.id} value={t.id}>{t.nombre} — {t.wm} W/m</option>)}</select>
        <p className="mut peq" style={{ marginTop: 4 }}>{tira.uso} · tipo {tira.tipo} · reinyectar cada {tira.tramoMax} m</p>
        <div className="rejilla" style={{ gridTemplateColumns: '1fr 1fr', gap: 10 }}>
          <div><label className="campo">Metros de tira (suma de filas)</label><input type="number" min="0.1" step="0.1" value={metros} onChange={e => setMetros(e.target.value)} /></div>
          <div><label className="campo">Brillo / uso: {uso} %</label><input type="range" min="10" max="100" value={uso} onChange={e => setUso(+e.target.value)} /></div>
          <div><label className="campo">Cable del cubo a la tira (m)</label><input type="number" min="0.1" step="0.5" value={cable} onChange={e => setCable(e.target.value)} /></div>
          <div><label className="campo">Calibre</label><select value={awg} onChange={e => setAwg(e.target.value)}>{Object.keys(AWG).map(g => <option key={g} value={g}>{g} AWG</option>)}</select></div>
        </div>
        <p className="mut peq" style={{ marginTop: 8 }}>Ejemplo: 7 filas de 1 m en paralelo = 7 m. Blanco al 100 % es el peor caso; los efectos de color suelen usar 40–60 %.</p>
      </div>
      <div className="tarjeta">
        <h2>Resultado</h2>
        <div className="datos" style={{ margin: '10px 0' }}>
          <div className="dato"><b>{c.w.toFixed(1)}</b><span>W</span></div>
          <div className="dato"><b>{c.a.toFixed(2)}</b><span>A a {tira.v} V</span></div>
          <div className="dato"><b>{c.cubos}</b><span>cubo(s)</span></div>
          <div className="dato"><b>{c.inyecciones}</b><span>reinyecciones</span></div>
        </div>
        {plan.errores.length ? <div className="error">{plan.errores.join(' · ')}</div> : <table className="tabla"><tbody>
          <tr><th>Por cubo</th><td>{c.aPorCubo.toFixed(2)} A · {c.wPorCubo.toFixed(1)} W</td></tr>
          <tr><th>Cartucho</th><td>{plan.cartucho.id} ({plan.cartucho.w} W) · {plan.cartucho.cubo}</td></tr>
          <tr><th>Tarjeta</th><td>{plan.tarjeta.nombre}{plan.tarjeta.personal ? ` ${plan.tarjeta.vmax} V` : ''} · R_B {plan.tarjeta.rb} Ω · R_ID {plan.tarjeta.rid / 1000}k</td></tr>
          <tr><th>Cable</th><td>Caída {caida.v.toFixed(2)} V ({(100 * caida.v / tira.v).toFixed(1)} %) con {awg} AWG · mínimo recomendado {minimo ?? '—'} AWG</td></tr>
          <tr><th>Calor en cable</th><td>{caida.w.toFixed(2)} W</td></tr>
        </tbody></table>}
        {plan.avisos.map(a => <div className="aviso" key={a} style={{ marginTop: 8 }}>⚠ {a}</div>)}
        {tira.v === 5 && c.a > 3 && <div className="aviso" style={{ marginTop: 8 }}>Las tiras de 5 V pierden voltaje rápido: alimenta por ambos extremos y cada {tira.tramoMax} m.</div>}
      </div>
    </div>

    <div className="rejilla dos seccion">
      <div className="tarjeta">
        <h2>Tarjeta a la medida</h2>
        <p className="mut peq">Para cualquier voltaje entre 3 y 24.4 V: tarjeta PERSONAL (R_ID 220k) y esta R_B; luego programa los límites desde el panel.</p>
        <label className="campo">Voltaje máximo deseado (V)</label>
        <input type="number" step="0.1" value={vp} onChange={e => setVp(e.target.value)} />
        {rb ? <div className="okmsg" style={{ marginTop: 10 }}>R_B = <b>{rb.rb} Ω</b> (1 %, ideal {rb.ideal.toFixed(0)} Ω) → {rb.vreal.toFixed(2)} V. La app podrá bajarlo hasta {vMinApp(rb.vreal).toFixed(2)} V.</div>
          : <div className="error" style={{ marginTop: 10 }}>Fuera de 3–24.4 V</div>}
      </div>
      <div className="tarjeta">
        <h2>¿Una resistencia en serie?</h2>
        <p className="peq">Con 1 MΩ en serie una tira de 12 V recibe ~12 µA: no prende. Para que dure y caliente menos, mejor <b>baja el voltaje a 11–11.5 V</b> desde el panel (el consumo cae 20–40 %) o limita la corriente con la tarjeta. En tiras de 12 V cada segmento ya trae su resistencia: no hace falta otra.</p>
      </div>
    </div>
  </>)
}
