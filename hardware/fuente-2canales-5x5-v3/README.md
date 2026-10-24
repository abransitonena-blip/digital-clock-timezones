# Fuente capacitiva de 2 canales, placa 5 × 5 cm, v3 (con serigrafía)

Mismo circuito y piezas que la v2. Cambios:
- Cobre más ordenado: pistas de 1.8 mm, rectas o a 45°, borne de salida alineado con su pista, etiquetas en el cobre ("127V~ 2CH", "S1", "S2").
- Serigrafía para el lado de componentes (`serigrafia_planchar.svg`, ya en espejo): contorno, silueta y valor de cada pieza, polaridades, L/N, salidas, aviso de 127 V, recuadro para nombre y fecha, y círculos en cada agujero para alinear al planchar.
- `fuente_2canales_5x5_v3.pdf`: hoja con 3 cobres + 3 serigrafías a 1:1, vista final, lista de material y seguridad.
- `generar.py` revisa separaciones (≥ 1.5 mm), conexiones completas y que el texto del cobre quede a ≥ 1 mm de todo.
