# Fuente capacitiva 2 canales · 5 × 5 cm · v9

Igual que la v8 (todo de patitas, sin SMD), con estas correcciones:

- **Pistas sin cruces aparentes:** alrededor del puente todo va en tramos rectos (horizontal/vertical).
  Ya no hay uniones en diagonal que parezcan pistas chocando. La revisión de reglas (DRC) da ≥ 1.5 mm entre redes distintas.
- **R5/R6 (220 kΩ) separadas de R3/R4:** la pata de la R3/R4 parada se movió para que no quede
  junto al alambre de la R5/R6 acostada (antes había ~0.35 mm entre ellas, ahora ~2.5 mm).
- **Serigrafía con la forma real de cada pieza:** el X2 es un rectángulo de 18 × 9 mm, el KBP307 un rectángulo con esquina
  (lado +), y el varistor un disco visto de canto. Las resistencias paradas se dibujan como círculo + pata, la 220 kΩ acostada
  con su cuerpo y patas, y el electrolítico con la franja del lado −.
- Quitados los adornos junto a "AP" que parecían pads.

Archivos: `cobre_planchar.svg`, `serigrafia_planchar.svg` (espejo), `serigrafia_vista.svg`, `manual_montaje_5x5_v9.pdf`.
Regenerar: `python3 generar.py` y luego `NODE_PATH=$(npm root -g) node hacer_manual.cjs`.
