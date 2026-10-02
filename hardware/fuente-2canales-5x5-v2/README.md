# Fuente capacitiva de 2 canales, placa 5 × 5 cm, v2 (piezas de patitas medidas por el usuario)

- Puente KBP307 parado (patas a ~4 mm; el footprint usa 3.9 mm con pads ovalados).
- X2 con patas a 15 mm, electrolítico de 17 mm (patas a 5 mm), RS de 1 W parada, RD de 1 MΩ acostada.
- Lo único SMD: 2 resistencias 1206 de 100 kΩ por canal (descarga del electrolítico), del lado del cobre, debajo del electrolítico.
- La fila de abajo es espejo de la de arriba. Sin zener, sin agujeros de montaje (los electrolíticos ocupan las esquinas) y el varistor va en la bornera de entrada.
- `generar.py` revisa separaciones (≥ 1.5 mm) y conexiones completas.
