# Fuente capacitiva de 5 canales, versión 4 híbrida SMD (placa de una cara)

Mismo circuito que la versión 3. Lo que se pudo pasar a SMD va del lado del cobre: 4 diodos M7 por canal como puente, resistencias 2512 y 1206. Lo grande sigue de patitas: X2 en bornera, electrolítico, zener de 5 W, varistor y borneras.

- Placa: 122 × 87 mm (la V3 mide 124 × 109), sin puentes de alambre.
- Las borneras del X2 y de salida son de 3 polos con la pata central cortada: por ahí pasa la línea N.
- `fuente_5canales_v4_smd.pdf`: pistas 1:1 para planchar (sin invertir), vista SMD del lado del cobre, vista de componentes, lista de material y cableado.
- `generar.py`: genera los SVG y revisa separaciones (≥ 1.5 mm) y que cada conexión quede completa.

> ⚠ No está aislada de la red. Caja de plástico cerrada, conectar LED con la fuente apagada, primera prueba con foco de 60 W en serie.

La tabla de capacitor y zener por salida es la misma que la de la V3 (`../fuente-5canales-v3/tabla.json`); `hacer_pdf.cjs` la lee de ahí.
