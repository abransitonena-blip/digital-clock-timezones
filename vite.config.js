import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { copyFileSync, existsSync, readFileSync, writeFileSync } from 'node:fs'

// La versión ligera del panel (la misma que sirve el cubo por Wi-Fi) se copia desde el firmware.
const sincronizarApp = () => ({
  name: 'sincronizar-app-cubo',
  buildStart() {
    copyFileSync('hardware/cubo-led-modular/app/index.html', 'public/cubo-app.html')
    // imágenes completas del firmware para el instalador web, sin el relleno 0xFF del final (graba más rápido)
    for (const v of [1, 2]) {
      const src = `hardware/cubo-led-modular/firmware/binarios/CuboAP_placa_v${v}_completo_0x0.bin`
      if (!existsSync(src)) continue
      const b = readFileSync(src); let n = b.length
      while (n > 0 && b[n - 1] === 0xff) n--
      writeFileSync(`public/firmware/CuboAP_placa_v${v}.bin`, b.subarray(0, (n + 4095) & ~4095))
    }
  },
})

export default defineConfig({
  base: './',
  plugins: [react(), sincronizarApp()],
  server: { port: 3000 },
})
