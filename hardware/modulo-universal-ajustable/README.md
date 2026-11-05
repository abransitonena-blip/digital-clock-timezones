# Módulo universal ajustable 1.2–24 V · 2 A (AP)

LM2596S-ADJ (SMD) con trimpot multivuelta 3296W 20 kΩ y R3 1 kΩ: Vout = 1.23 × (1 + TP1/1 kΩ).
Entrada por puente KBP307 + 2 × 1000 µF 50 V: 8–35 V DC sin polaridad o 6–22 V~ de transformador.
Basado en `fuente-12v-1.7a-127v`, con el regulador corrido 8 mm para meter el ajuste; C3 sube a 35 V y R1 a 3.3 k 1206.
El manual incluye guía de consumo de tiras LED de 12 V y cómo evitar que se calienten.

DRC del generador: separación mínima 0.55 mm, redes completas, cuerpos de piezas de patitas sin encimarse.
Archivos: `cobre_planchar.svg`, `serigrafia_planchar.svg`, `montaje.svg`, `manual_modulo_universal.pdf`.
Regenerar: `python3 generar.py && python3 hacer_manual.py && NODE_PATH=$(npm root -g) node imprimir.cjs`.
Sin armar físicamente todavía.
