import Panel from '../cubo/Panel'
const B = import.meta.env.BASE_URL

const SPECS = [
  ['Entrada', '12–36 V DC (cartucho 127 V, batería o fuente)'], ['Salida', '5–24.3 V, hasta 5 A por cubo'],
  ['Canales', '4 PWM de 5 A (R, G, B, W) + datos WS2812/SK6812/WS2811/WS2815'], ['Control', 'ESP32-C3: Bluetooth LE + Wi-Fi 2.4 GHz'],
  ['Medición', 'Voltaje, corriente, potencia, temperatura y voltaje de entrada'], ['Protecciones', 'Corte por hardware 1 ms, polaridad, TVS, térmica, reintento'],
  ['Caja', '80 mm IP67 de diseño (100 mm de aluminio para 75 W)'], ['Integraciones', 'Alexa local, WLED (básico), Home Assistant'],
]

export default function Cubo() {
  return (<>
    <section className="heroe">
      <div>
        <h1>Cubo AP</h1>
        <p className="mut" style={{ fontSize: 18, marginTop: 10 }}>Módulo de alimentación y control para tiras LED, impermeable y configurable por pieza o por app.</p>
        <table className="tabla" style={{ marginTop: 16 }}><tbody>{SPECS.map(([k, v]) => <tr key={k}><th style={{ width: 130 }}>{k}</th><td>{v}</td></tr>)}</tbody></table>
      </div>
      <img src={B + 'img/cubo_render_corte.jpg'} alt="Corte del Cubo AP: cartucho abajo y placa de control arriba" />
    </section>

    <section className="seccion">
      <div className="cab"><div><h2>Panel de control</h2><p className="mut">Conecta un cubo por Bluetooth (Chrome o Edge) o prueba la demo sin hardware.</p></div>
        <a className="boton" href={B + 'cubo-app.html'} target="_blank" rel="noreferrer">Abrir versión ligera</a></div>
      <Panel />
    </section>

    <section className="seccion rejilla dos">
      <div className="tarjeta">
        <h2>Así se configura</h2>
        <ol className="lista">
          <li><b>Cartucho</b> según la potencia: S 25 W, M 40 W o L 75 W.</li>
          <li><b>Tarjeta</b> de dos resistencias: R_B fija el voltaje máximo y R_ID dice el perfil. Para cualquier otro voltaje, la tarjeta PERSONAL (R_ID 220k) con R_B calculada en el <a href="#configurador">configurador</a>.</li>
          <li><b>Tipo de tira y efectos</b> desde la app; el cubo rechaza conectar una tira de 5 V con tarjeta de 12 V.</li>
          <li><b>Wi-Fi opcional</b>: página propia en <code>cuboap-xxxx.local</code>, horario por internet y, si los activas, WLED y Alexa.</li>
        </ol>
      </div>
      <div className="tarjeta">
        <h2>Placa de control</h2>
        <img className="foto" src={B + 'img/placa_control_arriba.jpg'} alt="Placa de control de 68 por 64 milímetros" loading="lazy" />
        <div className="fila" style={{ marginTop: 10 }}>
          <a className="boton" href={B + 'docs/esquema_placa_control.pdf'}>Esquema</a>
          <a className="boton" href={B + 'docs/cubo_ap_control_gerbers.zip'}>Gerber</a>
          <a className="boton" href={B + 'docs/bom.csv'}>BOM</a>
          <a className="boton" href={B + 'docs/cubo_ap_sistema.pdf'}>Sistema</a>
        </div>
      </div>
    </section>
  </>)
}
