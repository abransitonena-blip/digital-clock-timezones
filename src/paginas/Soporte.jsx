import { useState } from 'react'
import F from '../datos/fichas.json'

// Soporte público: hojas de datos, manual, garantía, avisos del LED y solución de problemas.
// Todo sale de src/datos/fichas.json, que genera hardware/cubo-led-modular/documentos/hacer_publicos.py (misma fuente que los PDF).

function Curva() {
  const T = F.curva.temperaturas, W = 560, H = 210, x0 = 44, y0 = 16, ancho = W - x0 - 46, alto = H - y0 - 34
  const px = t => x0 + (ancho * (t - T[0])) / (T[T.length - 1] - T[0])
  const py = p => y0 + alto * (1 - p / 100)
  const pyW = w => y0 + alto * (1 - w / 20)
  const linea = (vals, f) => vals.map((v, i) => `${i ? 'L' : 'M'}${px(T[i]).toFixed(1)},${f(v).toFixed(1)}`).join(' ')
  const colores = ['var(--ac)', '#1971c2']
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ maxWidth: 760, display: 'block' }} role="img" aria-label="Carga continua máxima contra temperatura ambiente">
      {[0, 25, 50, 75, 100].map(p => <g key={p}><line x1={x0} x2={x0 + ancho} y1={py(p)} y2={py(p)} stroke="var(--ln)" />
        <text x={x0 - 6} y={py(p) + 4} fontSize="11" textAnchor="end" fill="var(--mut)">{p} %</text>
        <text x={x0 + ancho + 6} y={py(p) + 4} fontSize="11" fill="#a86b12">{p / 5} W</text></g>)}
      {T.map(t => <text key={t} x={px(t)} y={H - 14} fontSize="11" textAnchor="middle" fill="var(--mut)">{t} °C</text>)}
      {Object.entries(F.curva.aluminio).map(([k, v], i) => <path key={k} d={linea(v, py)} fill="none" stroke={colores[i]} strokeWidth="2.2" />)}
      <path d={linea(F.curva.plastico_w, pyW)} fill="none" stroke="#a86b12" strokeWidth="2.2" strokeDasharray="6 4" />
    </svg>
  )
}

function Ficha({ P }) {
  return (<>
    <p style={{ maxWidth: 820 }}>{P.resumen}</p>
    <div className="rejilla dos" style={{ marginTop: 12 }}>
      {P.versiones.map(([v, u]) => <div key={v} className="tarjeta"><b>{v}</b><div className="mut peq">{u}</div></div>)}
    </div>
    <div className="rejilla dos" style={{ marginTop: 14, alignItems: 'start' }}>
      {P.secciones.map(([t, filas]) => (
        <div key={t} className="tarjeta">
          <h3>{t}</h3>
          <table className="tabla"><tbody>{filas.map(([a, b]) => <tr key={a}><td className="mut" style={{ width: '42%' }}>{a}</td><td>{b}</td></tr>)}</tbody></table>
        </div>))}
    </div>
    {P.perfiles && <div className="tarjeta" style={{ marginTop: 14 }}>
      <h3>Perfiles de tarjeta</h3>
      <div className="desliza"><table className="tabla"><thead><tr><th>Tarjeta</th><th>Voltaje máx.</th><th>Corriente máx.</th><th>Potencia</th><th>Uso</th></tr></thead>
        <tbody>{P.perfiles.map(f => <tr key={f[0]}>{f.map((c, i) => <td key={i}>{c}</td>)}</tr>)}</tbody></table></div>
    </div>}
    <ul className="lista peq mut" style={{ marginTop: 10 }}>{P.notas.map(n => <li key={n}>{n}</li>)}</ul>
  </>)
}

export default function Soporte() {
  const [prod, setProd] = useState('cubo')
  return (<>
    <h1>Soporte</h1>
    <p className="mut" style={{ marginTop: 8, maxWidth: 820 }}>
      Hojas de datos, manual de usuario y garantía del Cubo AP y del Nodo AP: qué entra, qué sale, cómo se instala y qué hacer si algo falla.
      Versión {F.version} del {F.fecha}: valores de diseño, preliminares hasta terminar las pruebas y certificaciones.
    </p>

    <section className="seccion">
      <h2>Documentos</h2>
      <div className="rejilla" style={{ marginTop: 10 }}>
        {F.documentos.map(([a, t]) => (
          <a key={a} className="tarjeta" href={'docs/' + a} target="_blank" rel="noreferrer" style={{ textDecoration: 'none', color: 'inherit' }}>
            <div className="entre"><b>{t}</b><span className="etiqueta">PDF</span></div>
            <div className="mut peq" style={{ marginTop: 4 }}>{a}</div>
          </a>))}
      </div>
    </section>

    <section className="seccion">
      <div className="cab"><h2>Especificaciones</h2>
        <nav className="pestanas" role="tablist" style={{ minWidth: 260 }}>
          {[['cubo', 'Cubo AP'], ['nodo', 'Nodo AP']].map(([k, t]) => <button key={k} role="tab" aria-selected={prod === k} className={'pestana' + (prod === k ? ' sel' : '')} onClick={() => setProd(k)}>{t}</button>)}
        </nav>
      </div>
      <Ficha P={F[prod]} />
    </section>

    {prod === 'cubo' && <section className="seccion">
      <h2>Cuerpo de aluminio con aletas</h2>
      <p className="mut peq" style={{ maxWidth: 820 }}>Para potencias altas y exteriores: aletas verticales con canal ancho para que el aire suba, y una costilla interna que toca la zona caliente de la placa a través de una almohadilla térmica aislante.</p>
      <div className="rejilla dos" style={{ marginTop: 10 }}>
        <img className="foto" src="img/cubo_aluminio.jpg" alt="Cubo AP con cuerpo de aluminio y aletas" loading="lazy" />
        <img className="foto" src="img/cubo_aluminio_interior.jpg" alt="Interior del cuerpo de aluminio con la costilla y la almohadilla térmica" loading="lazy" />
      </div>
    </section>}

    {prod === 'cubo' && <section className="seccion tarjeta">
      <h2>Carga máxima contra temperatura</h2>
      <p className="mut peq">El cubo es sellado: saca su calor por las paredes. Arriba de la curva baja el brillo solo para protegerse y lo recupera al enfriarse.</p>
      <Curva />
      <div className="fila peq" style={{ gap: 16 }}>
        {Object.keys(F.curva.aluminio).map((k, i) => <span key={k}><i style={{ display: 'inline-block', width: 18, height: 3, background: ['var(--ac)', '#1971c2'][i], verticalAlign: 'middle', marginRight: 6 }} />Aluminio · {k}</span>)}
        <span><i style={{ display: 'inline-block', width: 18, borderTop: '3px dashed #a86b12', verticalAlign: 'middle', marginRight: 6 }} />Cuerpo ASA · watts máximos (eje derecho)</span>
      </div>
    </section>}

    <section className="seccion">
      <h2>Avisos del LED del Cubo AP</h2>
      <div className="desliza"><table className="tabla"><thead><tr><th>LED</th><th>Significa</th><th>Qué hacer</th></tr></thead>
        <tbody>{F.fallas.map(f => <tr key={f[0]}>{f.map((c, i) => <td key={i}>{c}</td>)}</tr>)}</tbody></table></div>
    </section>

    <section className="seccion">
      <h2>Solución de problemas</h2>
      <div className="rejilla dos" style={{ marginTop: 10 }}>
        {F.problemas.map(([s, q]) => <div key={s} className="tarjeta"><b>{s}</b><p className="mut peq" style={{ marginTop: 4 }}>{q}</p></div>)}
      </div>
    </section>

    <section className="seccion tarjeta">
      <h2>Garantía</h2>
      <p className="peq">12 meses contra defectos de fabricación y funcionamiento, en piezas y mano de obra, incluidos el cartucho y la tarjeta entregados con el producto.
        Se hace efectiva con la póliza o con el comprobante de compra. No aplica por uso fuera de lo indicado en la hoja de datos y el manual, ni si el equipo fue abierto o reparado por terceros.</p>
      <p className="aviso" style={{ marginTop: 8 }}>La póliza es un borrador: faltan los datos del responsable y su revisión legal (LFPC y NOM-024-SCFI-2013) antes de entregarla al público.</p>
    </section>
  </>)
}
