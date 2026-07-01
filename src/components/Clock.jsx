import { useState, useEffect } from 'react'
import useClockStore from '../store'
import './Clock.css'

function Clock() {
  const { theme, timezones } = useClockStore()
  const [times, setTimes] = useState({})
  const [dayNight, setDayNight] = useState({})

  useEffect(() => {
    const updateTimes = () => {
      const newTimes = {}
      const newDayNight = {}

      timezones.forEach(tz => {
        const formatter = new Intl.DateTimeFormat('es-MX', {
          timeZone: tz.id,
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: true
        })
        newTimes[tz.id] = formatter.format(new Date())

        const hourFormatter = new Intl.DateTimeFormat('es-MX', {
          timeZone: tz.id,
          hour: '2-digit',
          hour12: false
        })
        const hour = parseInt(hourFormatter.format(new Date()))
        newDayNight[tz.id] = hour >= 6 && hour < 18 ? 'day' : 'night'
      })

      setTimes(newTimes)
      setDayNight(newDayNight)
    }

    updateTimes()
    const interval = setInterval(updateTimes, 1000)
    return () => clearInterval(interval)
  }, [timezones])

  return (
    <div className="clock-container" style={{ '--primary': theme.primaryColor, '--secondary': theme.secondaryColor }}>
      <div className="clock-grid">
        {timezones.map(tz => (
          <div key={tz.id} className={`clock-card ${dayNight[tz.id]}`}>
            <div className="clock-indicator">
              {dayNight[tz.id] === 'day' ? '☀️' : '🌙'}
            </div>
            <div className="clock-time">
              {times[tz.id] || '00:00:00'}
            </div>
            <div className="clock-city">
              {tz.city}
            </div>
            <div className="clock-timezone">
              {tz.id}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Clock
