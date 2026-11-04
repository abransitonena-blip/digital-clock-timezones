import { COMPAT } from '../datos/catalogo'
const TXT = { si: 'Compatible', parcial: 'Parcial', plan: 'En camino', no: 'No' }

export default function Compatibilidad() {
  const cuenta = COMPAT.flatMap(g => g.items).reduce((m, [, e]) => ({ ...m, [e]: (m[e] || 0) + 1 }), {})
  return (<>
    <h1>Compatibilidad</h1>
    <p className="mut" style={{ marginTop: 8, maxWidth: 760 }}>Qué tiras, apps, asistentes de voz y fuentes de energía del mercado funcionan con el Cubo AP (firmware v1). “Parcial” indica que funciona con limitaciones o que falta probarlo con el equipo real.</p>
    <div className="fila" style={{ marginTop: 14 }}>{Object.entries(TXT).map(([k, t]) => <span key={k} className={'etiqueta ' + k}>{t}: {cuenta[k] || 0}</span>)}</div>
    {COMPAT.map(g => (
      <section className="seccion tarjeta desliza" key={g.grupo}>
        <h2>{g.grupo}</h2>
        <table className="tabla" style={{ marginTop: 8 }}>
          <thead><tr><th>Dispositivo</th><th style={{ width: 120 }}>Estado</th><th>Notas</th></tr></thead>
          <tbody>{g.items.map(([n, e, nota]) => <tr key={n}><td>{n}</td><td><span className={'etiqueta ' + e}>{TXT[e]}</span></td><td className="mut">{nota}</td></tr>)}</tbody>
        </table>
      </section>))}
    <section className="seccion tarjeta">
      <h2>Cómo conectar con cada ecosistema</h2>
      <ol className="lista">
        <li>Por Bluetooth, en el panel: <code>Conectar Wi-Fi</code> con tu red.</li>
        <li>Activa <b>integraciones</b> (WLED/Alexa) y reinicia el cubo.</li>
        <li><b>Alexa</b>: “Alexa, descubre dispositivos”. Aparece con el nombre del cubo.</li>
        <li><b>Home Assistant</b>: la integración WLED lo detecta por mDNS; también puedes agregarlo por IP.</li>
        <li><b>Google Home / Apple Home</b>: expón la luz desde Home Assistant.</li>
      </ol>
      <p className="mut peq" style={{ marginTop: 8 }}>La API de órdenes nativa (<code>/api/cmd</code>) pide el PIN del cubo. Las integraciones no tienen contraseña, por eso vienen apagadas.</p>
    </section>
  </>)
}
