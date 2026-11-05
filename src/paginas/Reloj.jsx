import { useState } from 'react'
import useClockStore from '../store'
import Clock from '../components/Clock'
import Alarms from '../components/Alarms'
import Settings from '../components/Settings'
import Widget from '../components/Widget'
import '../App.css'

// El reloj original (zonas horarias, alarmas, temas) como una sección más del sitio.
export default function Reloj() {
  const { theme } = useClockStore()
  const [tab, setTab] = useState('clock')
  return (
    <div className="app reloj" style={{ '--primary': theme.primaryColor, '--secondary': theme.secondaryColor, '--background': theme.backgroundColor, borderRadius: 18, overflow: 'hidden', minHeight: 'auto' }}>
      <Widget />
      <header className="app-header"><div className="header-content"><h1>🕐 Reloj mundial</h1><p>Zonas horarias • Alarmas • Temas</p></div></header>
      <nav className="app-nav">
        {[['clock', '🕐 Reloj'], ['alarms', '🔔 Alarmas'], ['settings', '⚙️ Configuración']].map(([k, t]) =>
          <button key={k} className={`nav-btn ${tab === k ? 'active' : ''}`} onClick={() => setTab(k)}>{t}</button>)}
      </nav>
      <main className="app-main">
        {tab === 'clock' && <Clock />}{tab === 'alarms' && <Alarms />}{tab === 'settings' && <Settings />}
      </main>
    </div>
  )
}
