# Renders con Blender

`render_blender.py` genera con Blender (motor Cycles, luz de estudio de tres puntos) las imágenes de todo el hardware:

| Carpeta de salida | Qué trae |
|---|---|
| `renders/piezas/` | Las 29 piezas imprimibles ([accesorios](../accesorios/LEEME.md)), una imagen por pieza, en naranja AP Electric (las de TPU en negro, los rieles en metal) |
| `renders/placas/` | Las seis placas AP Rack y la caja ([modelos 3D](../web/modelos3d/LEEME.md)), con sus piezas |
| `renders/ensambles/` | La caja AP Rack con la placa dentro y la tapa levantada (Rack 16, RL4, AO4 y LED8) |

## Cómo usarlo en tu computadora

Necesitas Blender 4.1 o posterior (con 3.x también funciona, pero no se probó). Abre una terminal en la carpeta `hardware/ap-electric` del repositorio y ejecuta:

```
blender -b -P blender/render_blender.py -- --salida blender/renders
```

En Windows, `blender` suele ser `"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"`. Opciones útiles (después de `--`):

| Opción | Para qué |
|---|---|
| `--solo caja` | Solo lo que contenga ese texto en el nombre (`clip`, `AP_RL4`, `ensamble_ao4`…) |
| `--res 1920x1200` | Resolución de la imagen (por omisión 1280x800) |
| `--muestras 128` | Calidad de Cycles: más muestras, menos ruido y más tiempo |
| `--motor EEVEE` | Más rápido, con menos realismo (necesita tarjeta gráfica) |

También funciona con el módulo de Python: `pip install bpy==4.2.0` y luego `python blender/render_blender.py ...`.

Los STL y GLB se leen de `accesorios/stl/` y `web/modelos3d/`; si cambias el diseño, vuelve a generarlos (`python3 accesorios/accesorios.py`, `bash tools/exportar_modelos3d.sh`) y renderiza de nuevo.

## Límites

- Son renders de diseño: nada está impreso ni fabricado. Los colores de las placas son solo de apariencia (KiCad exporta las piezas sin material).
- El cuerpo del relé es una caja del tamaño de su contorno, no el modelo del fabricante.
- Las ventanas de la caja son aproximadas: comprueba con la placa real antes de imprimir.
- La caja se renderiza vacía por dentro salvo la placa; no incluye bornas enchufables ni cables.
