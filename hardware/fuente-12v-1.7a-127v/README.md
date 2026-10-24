# Fuente 12 V · 1.7 A desde 127 V (AP)

Transformador 127 V → 18 V (fuera de la placa, con fusible 1 A lento, interruptor y varistor 10D201K en la caja)
→ puente KBP307 → filtro 2 × 1000 µF 50 V → regulador conmutado LM2596S-12 (SMD) → 12 V 1.7 A.

Placa de una cara 72 × 50 mm: piezas SMD del lado del cobre; puente, capacitores grandes y borneras del otro lado.
Mejoras sobre `regulador-12v-2a-smd`: puente y filtro en la placa (entrada sin polaridad), LED rojo de filtro + descarga
de C6/C7 (R2), cerámico de 10 µF en la salida, 100 nF en la entrada de alterna, 4 barrenos M3 y serigrafía del lado de piezas.

DRC del generador: separación mínima 0.55 mm, redes completas, cuerpos de piezas de patitas sin encimarse.
Archivos: `cobre_planchar.svg`, `serigrafia_planchar.svg`, `montaje.svg`, `manual_fuente_12v_1.7a.pdf`.
Regenerar: `python3 generar.py && python3 hacer_manual.py && NODE_PATH=$(npm root -g) node imprimir.cjs`.
Sin armar físicamente todavía.
