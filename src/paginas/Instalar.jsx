import { useEffect, useState } from 'react'
const B = import.meta.env.BASE_URL

// Instalador por USB desde el navegador (Web Serial + ESP Web Tools, empaquetado en el sitio: sin CDN).
export default function Instalar() {
  const [placa, setPlaca] = useState('v2')
  const [listo, setListo] = useState(false)
  const fw = placa === 'v3' ? 'v2' : placa            // la v3 usa el mismo mapa de pines y firmware que la v2
  const soportado = typeof navigator !== 'undefined' && 'serial' in navigator
  useEffect(() => { import('esp-web-tools').then(() => setListo(true)).catch(() => setListo(false)) }, [])
  return (<>
    <h1>Instalar firmware</h1>
    <p className="mut" style={{ marginTop: 8, maxWidth: 760 }}>Graba el firmware del Cubo AP desde el navegador, sin instalar programas. Funciona en Chrome o Edge de computadora (Windows, macOS, Linux, ChromeOS).</p>
    <div className="rejilla dos seccion" style={{ marginTop: 20 }}>
      <div className="tarjeta">
        <h2>1 · Elige la placa</h2>
        <div className="chips" style={{ margin: '10px 0' }}>
          <button className={'chip' + (placa === 'v2' ? ' sel' : '')} onClick={() => setPlaca('v2')}>Placa v2 · DMX + 5 canales</button>
          <button className={'chip' + (placa === 'v1' ? ' sel' : '')} onClick={() => setPlaca('v1')}>Placa v1 · con botón</button>
          <button className={'chip' + (placa === 'v3' ? ' sel' : '')} onClick={() => setPlaca('v3')}>Placa v3 · chip soldado</button>
        </div>
        <h2 style={{ marginTop: 14 }}>2 · Conecta y graba</h2>
        <ol className="lista peq" style={{ margin: '8px 0 14px' }}>
          {placa === 'v3'
            ? <li>Conecta el adaptador de puntas pogo a los pads J5 (5V · D− · D+ · GND · EN · IO9). Con el chip nuevo, une IO9 a GND al conectar para entrar en modo descarga.</li>
            : <li>Conecta el ESP32-C3 SuperMini por USB-C (con o sin la placa).</li>}
          <li>Pulsa el botón de abajo y elige el puerto (suele llamarse “USB JTAG/serial debug unit”).</li>
          <li>Si no aparece: desconecta, mantén presionado <b>BOOT</b>, conecta y suelta.</li>
        </ol>
        {soportado
          ? (listo ? <esp-web-install-button key={placa} manifest={`${B}firmware/manifest_${fw}.json`}>
              <button slot="activate" className="boton pri">Instalar Cubo AP ({placa})</button>
            </esp-web-install-button> : <span className="mut">Cargando instalador…</span>)
          : <div className="aviso">Este navegador no permite USB desde la web (Web Serial). Usa Chrome o Edge en computadora. En celulares no está disponible.</div>}
      </div>
      <div className="tarjeta">
        <h2>Después de instalar</h2>
        <ul className="lista peq">
          <li>Abre la sección <a href="#cubo">Cubo AP</a> y conecta por Bluetooth: el PIN de 6 dígitos sale por el USB al arrancar y va en la etiqueta.</li>
          <li>Configura el Wi-Fi para tener la página del cubo, horario por internet y grupos.</li>
          <li>Las siguientes actualizaciones pueden ir por Wi-Fi (OTA) con el archivo <code>CuboAP_placa_{fw}_OTA.bin</code> de la carpeta <code>firmware/binarios</code> del repositorio.</li>
          <li>“Borrar el dispositivo” durante la instalación quita también el Wi-Fi, escenas y vínculos Bluetooth guardados.</li>
        </ul>
        <p className="aviso" style={{ marginTop: 10 }}>Firmware compilado con el núcleo oficial ESP32 3.1.1, sin probar todavía en una placa real.</p>
      </div>
    </div>
  </>)
}
