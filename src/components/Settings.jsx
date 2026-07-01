import { useState } from 'react'
import useClockStore from '../store'
import { THEMES } from '../constants'
import './Settings.css'

function Settings() {
  const { theme, setTheme, soundEnabled, toggleSound } = useClockStore()
  const [customColor, setCustomColor] = useState(theme.primaryColor)

  const handleThemeSelect = (selectedTheme) => {
    setTheme(selectedTheme)
    setCustomColor(selectedTheme.primaryColor)
  }

  const handleCustomColor = () => {
    setTheme({
      name: 'custom',
      primaryColor: customColor,
      secondaryColor: customColor,
      backgroundColor: '#0f0f0f',
      accentColor: customColor
    })
  }

  return (
    <div className="settings-container" style={{ '--primary': theme.primaryColor }}>
      <div className="settings-section">
        <h3>🎨 Temas</h3>
        <div className="themes-grid">
          {THEMES.map(t => (
            <button
              key={t.id}
              className={`theme-button ${theme.name === t.id ? 'active' : ''}`}
              onClick={() => handleThemeSelect(t)}
              style={{
                background: `linear-gradient(135deg, ${t.primaryColor} 0%, ${t.secondaryColor} 100%)`
              }}
              title={t.name}
            >
              <span className="theme-label">{t.name}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="settings-section">
        <h3>🎨 Color Personalizado</h3>
        <div className="custom-color-control">
          <input
            type="color"
            value={customColor}
            onChange={(e) => setCustomColor(e.target.value)}
            className="color-picker"
          />
          <button className="btn-apply" onClick={handleCustomColor}>
            Aplicar Color
          </button>
        </div>
      </div>

      <div className="settings-section">
        <h3>🔊 Sonido</h3>
        <div className="sound-control">
          <button
            className={`sound-toggle ${soundEnabled ? 'on' : 'off'}`}
            onClick={toggleSound}
          >
            {soundEnabled ? '🔊 Sonido Activado' : '🔇 Sonido Desactivado'}
          </button>
        </div>
      </div>

      <div className="settings-section">
        <h3>ℹ️ Información</h3>
        <div className="info-box">
          <p><strong>Versión:</strong> 1.0.0</p>
          <p><strong>Tema Actual:</strong> {theme.name}</p>
          <p><strong>Sonido:</strong> {soundEnabled ? 'Activado' : 'Desactivado'}</p>
          <p><strong>Almacenamiento:</strong> Datos guardados localmente</p>
        </div>
      </div>
    </div>
  )
}

export default Settings
