# Fuente capacitiva de 2 canales en placa de 5 × 5 cm

Idea del usuario (prototipo hecho a pluma): 2 canales por placa de 50 × 50 mm, sin zener, piezas juntas.
Base de la versión 4 híbrida SMD: 4 diodos M7, 2 resistencias 1206 de 1 MΩ y una 2512 de 150 Ω por canal del lado del cobre; X2 en bornera, electrolítico, 220 kΩ, varistor y borneras de patitas.

- Para 5 salidas se usan 3 placas.
- 2 agujeros M3 (abajo a la izquierda y arriba a la derecha; abajo a la derecha no cabe por la bornera de la salida 2).
- `fuente_2canales_5x5.pdf`: 6 copias de las pistas a 1:1, vistas de los dos lados, lista de material y seguridad.
- `generar.py` revisa separaciones (≥ 1.5 mm) y que cada conexión quede completa.

> ⚠ Sin zener: conectar LED solo con la fuente apagada. No está aislada de la red.
