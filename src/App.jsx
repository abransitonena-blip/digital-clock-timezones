import { useEffect, useState } from 'react'
import Inicio from './paginas/Inicio'
import Lineas from './paginas/Lineas'
import Cubo from './paginas/Cubo'
import Configurador from './paginas/Configurador'
import Calculadora from './paginas/Calculadora'
import Compatibilidad from './paginas/Compatibilidad'
import Proyectos from './paginas/Proyectos'
import Reloj from './paginas/Reloj'
import Instalar from './paginas/Instalar'
import Plataformas from './paginas/Plataformas'
import './sitio.css'

export const RUTAS = [
  ['', 'Inicio', Inicio],
  ['lineas', 'Líneas', Lineas],
  ['cubo', 'Cubo AP', Cubo],
  ['configurador', 'Pedidos', Configurador],
  ['calculadora', 'Calculadora', Calculadora],
  ['compatibilidad', 'Compatibilidad', Compatibilidad],
  ['proyectos', 'Proyectos', Proyectos],
  ['instalar', 'Instalar', Instalar],
  ['plataformas', 'Chips', Plataformas],
  ['reloj', 'Reloj', Reloj],
]

const rutaActual = () => (location.hash.replace(/^#\/?/, '').split('?')[0] || '')   // acepta #cubo y #/cubo

export function ir(ruta) { location.hash = ruta }

export default function App() {
  const [ruta, setRuta] = useState(rutaActual())
  const [tema, setTema] = useState(() => { try { return localStorage.getItem('tema') || '' } catch { return '' } })
  useEffect(() => {
    const f = () => { setRuta(rutaActual()); window.scrollTo(0, 0) }
    window.addEventListener('hashchange', f); return () => window.removeEventListener('hashchange', f)
  }, [])
  useEffect(() => {
    if (tema) document.documentElement.dataset.tema = tema; else delete document.documentElement.dataset.tema
    try { localStorage.setItem('tema', tema) } catch { /* sin almacenamiento */ }
  }, [tema])
  const [, titulo, Pagina] = RUTAS.find(r => r[0] === ruta) || RUTAS[0]
  useEffect(() => { document.title = ruta ? `${titulo} · AP` : 'AP · Iluminación LED inteligente' }, [ruta, titulo])
  const oscuro = tema === 'oscuro' || (!tema && matchMedia('(prefers-color-scheme: dark)').matches)
  return (
    <div className="sitio">
      <header className="barra">
        <div className="barra-in">
          <a className="marca" href="#"><i>AP</i>AP</a>
          <nav className="menu" aria-label="Secciones">
            {RUTAS.map(([r, t]) => <a key={r} href={'#' + r} className={r === ruta ? 'activo' : ''}>{t}</a>)}
          </nav>
          <button className="tema" onClick={() => setTema(oscuro ? 'claro' : 'oscuro')} title="Cambiar tema" aria-label="Cambiar tema">{oscuro ? '☀️' : '🌙'}</button>
        </div>
      </header>
      <main className="contenido"><Pagina /></main>
      <footer className="pie"><div>
        <span>AP · Iluminación LED inteligente · diseños abiertos, sin fabricar ni certificar todavía</span>
        <span><a href="#compatibilidad">Compatibilidad</a> · <a href="#proyectos">Documentos</a> · <a href="#reloj">Reloj</a></span>
      </div></footer>
    </div>
  )
}
