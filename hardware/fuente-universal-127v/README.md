# Fuente universal 127 V → 1.2–20 V · 2 A en una sola placa (AP)

Como un cargador: entra 127 V~ y sale el voltaje que ajustes con el trimpot.
- Etapa 1: flyback aislado UC3844 + 4N60 + transformador EE25 (98:22:14 vueltas, embobinado a mano) → ≈ 25 V,
  retroalimentación TL431 + PC817, recortador FR107 + P6KE200A, entrada con fusible, NTC, varistor y X2, capacitor Y1.
- Etapa 2: el regulador LM2596S-ADJ del `modulo-universal-ajustable` (se importa de ahí).
- Placa de una cara 170 × 84 mm, ranura de aislamiento bajo el transformador.

`placa.py` define pads, pistas y la revisión de reglas (127 V ↔ lado seguro ≥ 5.5 mm, alto voltaje ≥ 1.2 mm, conexiones,
cuerpos). `dibujos.py` genera cobre, serigrafía y montaje; `hacer_manual.py` + `imprimir.cjs` el PDF.
Regenerar: `python3 dibujos.py && python3 hacer_manual.py && NODE_PATH=$(npm root -g) node imprimir.cjs`.

Supuestos a verificar: carrete EE25 de patas a 5 mm y filas a 20 mm. Diseño calculado, sin probar físicamente.
