import { CHIPS, PRODUCTOS, NIVELES } from '../datos/plataformas'

// Referencias: chips para integrar directo en la placa y productos existentes de los que se toman ideas.
const Fuente = ({ url }) => <a href={url} target="_blank" rel="noreferrer">fuente</a>

export default function Plataformas() {
  return (<>
    <h1>Plataformas y chips</h1>
    <p className="mut" style={{ marginTop: 8, maxWidth: 800 }}>
      El controlador deja de depender de módulos (ESP32 SuperMini, Pico): el chip va soldado en la placa con sus componentes de referencia.
      Aquí están las opciones evaluadas, de China, Estados Unidos y Europa, y los productos existentes que sirven de referencia.
    </p>

    <section className="seccion">
      <h2>Familia propuesta</h2>
      <div className="rejilla dos" style={{ marginTop: 10 }}>
        {NIVELES.map(n => (
          <div key={n.nivel} className="tarjeta">
            <div className="entre"><b>{n.nivel}</b><span className="etiqueta">{n.estado}</span></div>
            <div className="mut peq" style={{ margin: '4px 0' }}>{n.chip}</div>
            <div className="peq">{n.que}</div>
          </div>
        ))}
      </div>
    </section>

    <section className="seccion">
      <h2>Chips para integrar en la placa</h2>
      <div style={{ overflowX: 'auto' }}>
        <table className="tabla">
          <thead><tr><th>Chip</th><th>Fabricante</th><th>Radio</th><th>Núcleo</th><th>Encapsulado</th><th>Uso en AP</th><th></th></tr></thead>
          <tbody>{CHIPS.map(c => (
            <tr key={c.chip}><td><b>{c.chip}</b></td><td>{c.marca}</td><td>{c.radio}</td><td>{c.nucleo}</td><td>{c.enc}</td><td>{c.uso}</td><td><Fuente url={c.fuente} /></td></tr>
          ))}</tbody>
        </table>
      </div>
    </section>

    <section className="seccion">
      <h2>Productos y diseños de referencia</h2>
      <div className="rejilla dos" style={{ marginTop: 10 }}>
        {PRODUCTOS.map(p => (
          <div key={p.nombre} className="tarjeta">
            <div className="entre"><b>{p.nombre}</b><span className="mut peq">{p.origen}</span></div>
            <p className="peq" style={{ margin: '6px 0' }}>{p.idea}</p>
            <Fuente url={p.fuente} />
          </div>
        ))}
      </div>
    </section>

    <section className="seccion tarjeta">
      <h2>Placa v3: el chip soldado</h2>
      <ul className="lista peq">
        <li>ESP32-C3FH4 (QFN32, flash de 4 MB dentro del chip) con el circuito de la guía de hardware de Espressif: cristal de 40 MHz ±10 ppm, 24 nH en serie en XTAL_P, LC en la alimentación de RF y RC en CHIP_EN.</li>
        <li>Antena externa por U.FL (sale por la pared del cubo) con red de acople CLC junto al chip.</li>
        <li>Regulador propio de 3.3 V (AP2112K) y programación por el USB nativo del chip en 6 pads.</li>
        <li>Mismo mapa de pines que la v2: usa el mismo firmware y el mismo instalador.</li>
      </ul>
      <p className="aviso" style={{ marginTop: 10 }}>Sin fabricar ni probar. La red de RF y los capacitores del cristal se tienen que ajustar en la placa real con analizador de redes y prueba de tono.</p>
    </section>
  </>)
}
