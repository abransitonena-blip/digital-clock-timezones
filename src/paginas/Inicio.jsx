import { LINEAS, PROYECTOS } from '../datos/catalogo'
const B = import.meta.env.BASE_URL

export default function Inicio() {
  return (<>
    <section className="heroe">
      <div>
        <span className="etiqueta plan">Nuevo · Cubo AP v1</span>
        <h1 style={{ margin: '12px 0' }}>Un solo módulo LED para cada cliente.</h1>
        <p className="mut" style={{ fontSize: 18 }}>Cambias una tarjeta de dos resistencias y el mismo cubo impermeable entrega 5, 12, 15 o 24 V hasta 5 A.
          Se controla desde el celular por Bluetooth, por Wi-Fi, con Alexa o Home Assistant, y funciona con las tiras más vendidas: RGB, RGBW, CCT, WS2812B, SK6812, WS2811 y WS2815.</p>
        <div className="fila" style={{ marginTop: 18 }}>
          <a className="boton pri" href="#/configurador">Armar un pedido</a>
          <a className="boton" href="#/cubo">Probar el panel</a>
          <a className="boton" href="#/calculadora">Calcular mi tira</a>
        </div>
      </div>
      <img src={B + 'img/cubo_render_explotado.jpg'} alt="Cubo AP abierto: tapa, empaque y placa de control dentro de la caja" />
    </section>

    <section className="seccion">
      <div className="rejilla">
        {[['🔧', 'Configurable por pieza', 'La tarjeta fija el voltaje por hardware: sin tarjeta o al revés, la salida se apaga.'],
          ['📱', 'Bluetooth, Wi-Fi y voz', 'App web sin instalar, página propia del cubo, Alexa local y API compatible con WLED.'],
          ['🛡️', 'Protegido', 'Corte por hardware en 1 ms, recorte térmico, polaridad invertida y reintento automático.'],
          ['💧', 'IP67 por diseño', 'Empaque de silicón, prensaestopas M16 y membrana de ventilación contra condensación.']].map(([i, t, d]) =>
          <div className="tarjeta" key={t}><div style={{ fontSize: 26 }}>{i}</div><h3 style={{ marginTop: 6 }}>{t}</h3><p className="mut peq">{d}</p></div>)}
      </div>
    </section>

    <section className="seccion">
      <div className="cab"><div><h2>Líneas de producto</h2><p className="mut">Una configuración probada para cada mercado.</p></div><a className="boton" href="#/lineas">Ver todas</a></div>
      <div className="rejilla">
        {LINEAS.slice(0, 6).map(l => <a key={l.id} href={'#/lineas'} className="tarjeta" style={{ textDecoration: 'none', color: 'inherit' }}>
          <div style={{ fontSize: 24 }}>{l.icono}</div><h3 style={{ marginTop: 6 }}>{l.nombre}</h3><p className="mut peq">{l.resumen}</p></a>)}
      </div>
    </section>

    <section className="seccion">
      <div className="cab"><div><h2>Proyectos abiertos</h2><p className="mut">Esquemas, placas, manuales y archivos de fabricación.</p></div><a className="boton" href="#/proyectos">Ver proyectos</a></div>
      <div className="rejilla">
        {PROYECTOS.slice(0, 3).map(p => <a key={p.id} href="#/proyectos" className="tarjeta" style={{ textDecoration: 'none', color: 'inherit' }}>
          <img className="foto" src={B + p.img} alt={p.nombre} loading="lazy" /><h3 style={{ marginTop: 10 }}>{p.nombre}</h3><p className="mut peq">{p.estado}</p></a>)}
      </div>
    </section>

    <p className="aviso seccion">Todos los diseños de este sitio están sin fabricar ni certificar. Para productos que se venden, usa fuentes AC-DC certificadas como cartucho de potencia.</p>
  </>)
}
