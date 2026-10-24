# Cubo AP · módulo LED modular (concepto + modelo 3D)

Cubo impermeable (IP67 de diseño) de 80 mm para letreros: cartucho de potencia intercambiable (S/M/L),
regulación configurable por tarjeta de resistencias o por app (la tarjeta fija el máximo), control ESP32-C3
con Bluetooth/Wi-Fi y 4 canales PWM + datos para tiras direccionables.

- `cubo.py`: modelo paramétrico para Blender 4.x (bpy). Genera `cubo_ap.blend` y `cuerpo.stl`, `tapa.stl`, `empaque.stl` (mallas cerradas).
- `render.py`: renders armado / explotado / corte con Cycles.
- `hacer_documento.py` + `imprimir.cjs`: `cubo_ap_sistema.pdf` con la arquitectura y las reglas de diseño.

Regenerar: `python3 cubo.py && python3 render.py && python3 hacer_documento.py && NODE_PATH=$(npm root -g) node imprimir.cjs`.
