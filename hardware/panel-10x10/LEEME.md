# Panel de 10 × 10 cm: placas A + B en una sola fenólica

- **Placa A** (izquierda, 50 × 60 mm, `../flechas-127v/`): secuenciador de 3 salidas, 100 → 010 → 001. Lleva NE555, CD4017 y 3 SCR, más su propia fuente capacitiva para las flechas.
- **Placa B** (derecha, 50 × 50 mm, `../fuente3-127v/`): fuente de 3 salidas para letreros fijos.

## Cómo hacerlo

1. Imprime `panel_1_cobre_para_planchado_1a1.pdf` al 100 % en impresora láser, sobre papel couché. Mide la regla de 100 mm.
2. Plancha sobre una fenólica de una cara de 10 × 10 cm, ataca con cloruro férrico y quita el tóner.
3. Corta por la línea central.
4. Perfora con ayuda de `panel_4_plantilla_perforaciones_1a1.pdf`.

Para regenerar el panel: `python3 hardware/panel-10x10/panel.py`.
