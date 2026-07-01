import { useState } from 'react'
import useClockStore from './store'
import Clock from './components/Clock'
import Alarms from './components/Alarms'
import Settings from './components/Settings'
import Widget from './components/Widget'
import './App.css'

function App() {
  const { theme } = useClockStore()
  const [activeTab, setActiveTab] = useState('clock')

  return (
    <div
      className="app"
      style={{
        '--primary': theme.primaryColor,
        '--secondary': theme.secondaryColor,
        '--background': theme.backgroundColor
      }}
    >
      <Widget />

      <header className="app-header">
        <div className="header-content">
          <h1>🕐 Digital Clock Pro</h1>
          <p>Multiple Time Zones • Alarms • Custom Themes</p>
        </div>
      </header>

      <nav className="app-nav">
        <button
          className={`nav-btn ${activeTab === 'clock' ? 'active' : ''}`}
          onClick={() => setActiveTab('clock')}
        >
          🕐 Reloj
        </button>
        <button
          className={`nav-btn ${activeTab === 'alarms' ? 'active' : ''}`}
          onClick={() => setActiveTab('alarms')}
        >
          🔔 Alarmas
        </button>
        <button
          className={`nav-btn ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          ⚙️ Configuración
        </button>
      </nav>

      <main className="app-main">
        {activeTab === 'clock' && <Clock />}
        {activeTab === 'alarms' && <Alarms />}
        {activeTab === 'settings' && <Settings />}
      </main>

      <footer className="app-footer">
        <p>🚀 Digital Clock Pro v1.0.0 • Hecho con ❤️</p>
      </footer>
    </div>
  )
}

export default App
