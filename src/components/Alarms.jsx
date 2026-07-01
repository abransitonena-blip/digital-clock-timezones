import { useState } from 'react'
import useClockStore from '../store'
import { ALARM_SOUNDS, REPEAT_OPTIONS } from '../constants'
import './Alarms.css'

function Alarms() {
  const { alarms, addAlarm, deleteAlarm, toggleAlarm, theme, soundEnabled } = useClockStore()
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    time: '08:00',
    label: '',
    sound: 'bell',
    repeat: 'once',
    enabled: true
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    addAlarm(formData)
    setFormData({
      time: '08:00',
      label: '',
      sound: 'bell',
      repeat: 'once',
      enabled: true
    })
    setShowForm(false)
  }

  const playSound = (soundId) => {
    const sound = ALARM_SOUNDS.find(s => s.id === soundId)
    if (sound && soundEnabled) {
      const audio = new Audio(sound.url)
      audio.play()
    }
  }

  const triggerVibration = () => {
    if (navigator.vibrate) {
      navigator.vibrate([200, 100, 200])
    }
  }

  return (
    <div className="alarms-container" style={{ '--primary': theme.primaryColor }}>
      <div className="alarms-header">
        <h2>🔔 Alarmas</h2>
        <button
          className="btn-add"
          onClick={() => setShowForm(!showForm)}
        >
          + Nueva Alarma
        </button>
      </div>

      {showForm && (
        <form className="alarm-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Hora</label>
            <input
              type="time"
              value={formData.time}
              onChange={(e) => setFormData({ ...formData, time: e.target.value })}
              required
            />
          </div>

          <div className="form-group">
            <label>Descripción</label>
            <input
              type="text"
              placeholder="Ej: Reunión, Ejercicio..."
              value={formData.label}
              onChange={(e) => setFormData({ ...formData, label: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label>Sonido</label>
            <select
              value={formData.sound}
              onChange={(e) => setFormData({ ...formData, sound: e.target.value })}
            >
              {ALARM_SOUNDS.map(sound => (
                <option key={sound.id} value={sound.id}>
                  {sound.name}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Repetir</label>
            <select
              value={formData.repeat}
              onChange={(e) => setFormData({ ...formData, repeat: e.target.value })}
            >
              {REPEAT_OPTIONS.map(opt => (
                <option key={opt.id} value={opt.id}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div className="form-buttons">
            <button type="submit" className="btn-save">Guardar</button>
            <button
              type="button"
              className="btn-cancel"
              onClick={() => setShowForm(false)}
            >
              Cancelar
            </button>
          </div>
        </form>
      )}

      <div className="alarms-list">
        {alarms.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🌙</div>
            <p>Sin alarmas configuradas</p>
          </div>
        ) : (
          alarms.map(alarm => (
            <div key={alarm.id} className={`alarm-item ${alarm.enabled ? 'enabled' : 'disabled'}`}>
              <div className="alarm-info">
                <div className="alarm-time">{alarm.time}</div>
                <div className="alarm-details">
                  <p className="alarm-label">{alarm.label || 'Sin descripción'}</p>
                  <p className="alarm-sound">
                    {ALARM_SOUNDS.find(s => s.id === alarm.sound)?.name}
                  </p>
                </div>
              </div>
              <div className="alarm-actions">
                <button
                  className="btn-test"
                  onClick={() => {
                    playSound(alarm.sound)
                    triggerVibration()
                  }}
                  title="Probar sonido y vibración"
                >
                  🔊
                </button>
                <button
                  className={`btn-toggle ${alarm.enabled ? 'on' : 'off'}`}
                  onClick={() => toggleAlarm(alarm.id)}
                >
                  {alarm.enabled ? '✓' : '✕'}
                </button>
                <button
                  className="btn-delete"
                  onClick={() => deleteAlarm(alarm.id)}
                >
                  🗑️
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default Alarms
