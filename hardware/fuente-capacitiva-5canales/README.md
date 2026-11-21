# Fuente capacitiva de 5 canales independientes (placa de una cara)

El mismo circuito repetido 5 veces: cada salida tiene su capacitor X2, su resistencia de 150 Ω, su puente rectificador en línea (KBP307) y su electrolítico. Cada salida lleva la corriente que marque **su** capacitor, aunque las demás tengan otra cantidad de LED o estén desconectadas.

> ⚠ **No está aislada de la red.** Toda la placa y los LED quedan a 127 V. Caja de plástico cerrada y primera prueba con foco de 60 W en serie.

- `fuente_5canales_placa.pdf`: pistas 1:1 para planchar (sin invertir), acomodo de piezas, lista de material y tabla de capacitores.
- `generar.py`: genera los SVG y revisa separaciones (≥ 1.5 mm) y que cada conexión quede completa. `hacer_pdf.cjs` arma el PDF.

Placa: 110 × 93 mm, sin puentes de alambre. La línea N pasa entre las patas de los X2 y de las resistencias de 1 MΩ.

| LED por salida | Blanco/azul/verde | Rojo/amarillo |
|---|---|---|
| 1 | 394J | 394J |
| 3–10 | 474J | 474J |
| 15 | 564J | 474J |
| 20 | 564J | 564J |
| 25 | 684J | 564J |
| 30 | 824J | 564J |
| 35 (máx.) | 105J | 684J |
