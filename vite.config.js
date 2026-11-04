import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { copyFileSync } from 'node:fs'

// La versión ligera del panel (la misma que sirve el cubo por Wi-Fi) se copia desde el firmware.
const sincronizarApp = () => ({
  name: 'sincronizar-app-cubo',
  buildStart() { copyFileSync('hardware/cubo-led-modular/app/index.html', 'public/cubo-app.html') },
})

export default defineConfig({
  base: './',
  plugins: [react(), sincronizarApp()],
  server: { port: 3000 },
})
