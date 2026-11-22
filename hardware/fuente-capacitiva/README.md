# Fuente capacitiva para 5 salidas de LED (placa de una cara)

Fuente sin transformador para 5 salidas de LED de 5 mm en serie (3 LED por salida), a 127 V / 60 Hz.

> ⚠ **No está aislada de la red.** Toda la placa y los LED quedan conectados a 127 V. Ármala dentro de una caja de plástico cerrada y haz la primera prueba con un foco de 60 W en serie.

## Archivos

| Archivo | Qué es |
|---|---|
| `fuente_capacitiva_placa.pdf` | **Para imprimir.** Página 1: pistas para planchar a escala 1:1 (dos copias). Página 2: acomodo de piezas. Página 3: acomodo ampliado. |
| `cobre_planchar.svg` | Pistas de cobre, 95 × 72 mm. |
| `componentes.svg` | Vista de componentes. |
| `generar.py` | Genera los SVG y revisa que las pistas no se toquen (separación ≥ 1.5 mm) y que cada conexión quede completa. |
| `hacer_pdf.cjs` | Arma el PDF con Chromium (Playwright). |

**Planchado:** imprime en impresora láser al 100 % y **sin invertir**. El letrero sale al revés en el papel a propósito y queda derecho sobre el cobre. La barra de 50 mm sirve para comprobar la escala.

## Material

| Ref | Pieza |
|---|---|
| C1 | Capacitor X2 275 VAC 0.56 µF (564J). Si no hay, 0.47 µF (474J). Tiene agujeros para patas a 15 o 22.5 mm |
| R1 | 1 MΩ ½ W |
| R2 | 150 Ω 1 W antiflama |
| D1–D4 | 1N4007 |
| C2 | Electrolítico 47 µF 250 V, 13 mm, patas a 5 mm |
| R3 | 220 kΩ ½ W |
| J0–J5 | Bornera KF301 de 2 polos, paso 5 mm (6 piezas) |
| F1 | Portafusible de cable + fusible 5×20 mm lento de 500 mA (va en el cable de fase) |

Corriente: I ≈ 4·f·C·(V<sub>pico</sub> − V<sub>LED total</sub>). Con 564J y 15 LED blancos da unos 17.7 mA, y unos 20 mA con la red al +10 %.

Para regenerar: `python3 generar.py && node hacer_pdf.cjs`
