import { useState, useEffect } from 'react'
import useClockStore from '../store'
import './Widget.css'

function Widget() {
  const { timezones, theme } = useClockStore()
  const [time, setTime] = useState(new Date().toLocaleTimeString('es-MX'))
  const [isDragging, setIsDragging] = useState(false)
  const [position, setPosition] = useState({ x: 20, y: 20 })
  const [isMinimized, setIsMinimized] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })

  useEffect(() => {
    const interval = setInterval(() => {
      setTime(new Date().toLocaleTimeString('es-MX'))
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  const handleMouseDown = (e) => {
    if (e.target.closest('.widget-close')) return
    setIsDragging(true)
    setDragStart({
      x: e.clientX - position.x,
      y: e.clientY - position.y
    })
  }

  const handleMouseMove = (e) => {
    if (!isDragging) return
    setPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    })
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleMouseUp)
      return () => {
        window.removeEventListener('mousemove', handleMouseMove)
        window.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDragging, position, dragStart])

  return (
    <div
      className={`widget ${isMinimized ? 'minimized' : ''}`}
      style={{
        '--primary': theme.primaryColor,
        left: `${position.x}px`,
        top: `${position.y}px`
      }}
      onMouseDown={handleMouseDown}
    >
      <div className="widget-header">
        <span className="widget-title">⏰ Clock</span>
        <div className="widget-controls">
          <button
            className="widget-minimize"
            onClick={() => setIsMinimized(!isMinimized)}
          >
            {isMinimized ? '📋' : '−'}
          </button>
          <button className="widget-close">×</button>
        </div>
      </div>

      {!isMinimized && (
        <div className="widget-content">
          <div className="widget-main-time">{time}</div>
          <div className="widget-timezones">
            {timezones.slice(0, 3).map(tz => {
              const formatter = new Intl.DateTimeFormat('es-MX', {
                timeZone: tz.id,
                hour: '2-digit',
                minute: '2-digit',
                hour12: true
              })
              return (
                <div key={tz.id} className="widget-tz">
                  <span className="tz-city">{tz.city}</span>
                  <span className="tz-time">{formatter.format(new Date())}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

export default Widget
