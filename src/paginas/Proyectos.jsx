import { PROYECTOS, DOCS_REFERENCIA } from '../datos/catalogo'
const B = import.meta.env.BASE_URL

export default function Proyectos() {
  return (<>
    <h1>Proyectos</h1>
    <p className="mut" style={{ marginTop: 8, maxWidth: 760 }}>Diseños abiertos de fuentes y controladores LED: manuales, esquemas y archivos de fabricación. El código y los generadores están en la carpeta <code>hardware/</code> del repositorio.</p>
    <div className="rejilla seccion" style={{ marginTop: 20 }}>
      {PROYECTOS.map(p => (
        <article className="tarjeta" key={p.id}>
          <img className="foto" src={B + p.img} alt={p.nombre} loading="lazy" />
          <h3 style={{ marginTop: 10 }}>{p.nombre}</h3>
          <span className={'etiqueta ' + (p.estado.startsWith('Construida') ? 'parcial' : 'plan')}>{p.estado}</span>
          <p className="mut peq" style={{ marginTop: 8 }}>{p.texto}</p>
          <div className="fila" style={{ marginTop: 10 }}>{p.docs.map(([t, u]) => <a key={u} className="boton" href={B + u}>{t}</a>)}</div>
        </article>))}
    </div>
    <section className="seccion tarjeta">
      <h2>Referencia</h2>
      <ul className="lista">{DOCS_REFERENCIA.map(([t, u]) => <li key={u}><a href={B + u}>{t}</a></li>)}</ul>
    </section>
  </>)
}
