import { LINEAS } from '../datos/catalogo'
import { planificar } from '../lib/led'

export default function Lineas() {
  return (<>
    <h1>Líneas de producto</h1>
    <p className="mut" style={{ maxWidth: 760, marginTop: 8 }}>El mismo Cubo AP se adapta a cada mercado cambiando el cartucho, la tarjeta y el tipo de tira. Cada línea trae una configuración de partida y un ejemplo calculado.</p>
    <div className="rejilla dos seccion" style={{ marginTop: 22 }}>
      {LINEAS.map(l => {
        const p = planificar(l.ejemplo)
        return (
          <article className="tarjeta" key={l.id} id={l.id}>
            <div className="entre"><h2>{l.icono} {l.nombre}</h2></div>
            <p className="mut">{l.resumen}</p>
            <div className="rejilla" style={{ gridTemplateColumns: '1fr 1fr', marginTop: 12 }}>
              <div><b className="peq">Tiras recomendadas</b><ul className="lista peq">{l.tiras.map(t => <li key={t}>{t}</li>)}</ul></div>
              <div><b className="peq">Funciones clave</b><ul className="lista peq">{l.funciones.map(t => <li key={t}>{t}</li>)}</ul></div>
            </div>
            <p className="peq" style={{ marginTop: 10 }}><b>Configuración:</b> {l.config}</p>
            <div className="dato" style={{ marginTop: 10 }}>
              <span>Ejemplo: {l.ejemplo.cantidad} × {l.ejemplo.nombre} a {l.ejemplo.v} V {l.ejemplo.a} A</span>
              <div className="peq" style={{ marginTop: 4 }}>
                {p.errores.length ? <span style={{ color: 'var(--bad)' }}>{p.errores.join(' · ')}</span> :
                  <>{p.cubos} cubo(s) · cartucho {p.cartucho.id} ({p.cartucho.w} W) · tarjeta {p.tarjeta.nombre}{p.tarjeta.personal ? ` (R_B ${p.tarjeta.rb} Ω)` : ''} · cable {p.awg} AWG</>}
              </div>
            </div>
            <a className="boton" style={{ marginTop: 12 }} href={`#/configurador?v=${l.ejemplo.v}&a=${l.ejemplo.a}&n=${l.ejemplo.cantidad}&nombre=${encodeURIComponent(l.ejemplo.nombre)}`}>Usar en un pedido</a>
          </article>)
      })}
    </div>
  </>)
}
