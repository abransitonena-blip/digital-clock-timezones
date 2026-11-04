# AP · Iluminación LED inteligente

Sitio web (React + Vite) y diseños abiertos de electrónica para iluminación LED.

## Secciones del sitio
| Ruta | Qué hace |
|---|---|
| `#/` Inicio | Presentación del Cubo AP, líneas de producto y proyectos |
| `#/lineas` | 7 líneas de producto con configuración recomendada y ejemplo calculado. Líneas: letreros, arquitectura, hogar, comercio, eventos, solar y vehículos |
| `#/cubo` | Ficha del Cubo AP y **panel de control**: Bluetooth (Chrome/Edge) o demo simulada |
| `#/configurador` | Pedidos por cliente (V, A, cantidad), con exportación a CSV e impresión. Calcula: cubos, cartucho, tarjeta con R_B/R_ID, cable y lista de compra del lote |
| `#/calculadora` | Consumo, reinyección, cubos y caída en cable para 15 tiras del mercado. Incluye la tarjeta a la medida (R_B E96) |
| `#/compatibilidad` | Compatibilidad con tiras, apps, asistentes de voz y fuentes de energía |
| `#/proyectos` | Todos los proyectos de `hardware/`, con manuales, esquemas, Gerber y BOM |
| `#/reloj` | El reloj mundial original (zonas horarias, alarmas, temas) |

```
npm install
npm run dev      # http://localhost:3000
npm test         # pruebas de los cálculos (src/lib/led.test.js)
npm run build    # sitio estático en dist/ (rutas relativas: sirve en GitHub Pages o cualquier hosting)
```
- `src/lib/led.js` tiene los cálculos, sin React. Sus perfiles de tarjeta son los mismos del firmware.
- `src/datos/catalogo.js` tiene las tiras, las líneas de producto, la compatibilidad y los proyectos.
- `public/cubo-app.html` es el panel ligero; se copia al compilar desde `hardware/cubo-led-modular/app/index.html`, y es la misma página que el cubo sirve por Wi-Fi.

Los diseños están sin fabricar ni certificar. Los consumos de tiras son típicos: confírmalos con la ficha del fabricante.
