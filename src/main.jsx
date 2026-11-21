import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

// Sitio instalable y sin conexión (solo en producción y en contexto seguro)
if (import.meta.env.PROD && 'serviceWorker' in navigator && isSecureContext) {
  addEventListener('load', () => navigator.serviceWorker.register('./sw.js').catch(() => {}))
}
