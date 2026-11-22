# Regulador 12 V · 2 A · SMD (LM2596S-12)

Convertidor reductor (buck) en placa de una cara de 50 × 44 mm para hacer por planchado. Piezas SMD del lado del cobre.

- Entrada 16–35 V DC (24 V ideal), salida 12 V fija, 2 A continuos.
- D1 (SS54) protege contra entrada invertida; el LM2596 trae límite de corriente y apagado por temperatura.
- DRC del generador: separación mínima 0.55 mm, todas las redes conectadas.

Archivos: `cobre_planchar.svg` (espejo, para planchar), `cobre_vista.svg`, `montaje.svg`, `manual_regulador_12v_2a.pdf`.
Regenerar: `python3 generar.py && python3 hacer_manual.py && NODE_PATH=$(npm root -g) node imprimir.cjs`.
Sin armar físicamente todavía.
