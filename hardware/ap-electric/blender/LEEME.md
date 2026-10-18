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

## Acabados y formatos de imagen

`render_acabados.py` renderiza la caja AP Rack con la placa dentro en **siete acabados** (color y textura) y en **cuatro formatos de imagen**:

```
blender -b -P blender/render_acabados.py -- --salida blender/renders/acabados
```

| Acabado | Textura (relieve procedural) |
|---|---|
| `petg_naranja` | capas de impresión sutiles |
| `grafito_texturizado` | grano fino mate |
| `blanco_satinado` | liso |
| `azul_industrial` | capas de impresión |
| `fibra_carbono` | tejido diagonal |
| `aluminio_cepillado` | vetas finas, metálico |
| `humo_translucido` | tapa translúcida |

Formatos: `portada` 1920×1080, `cuadrado` 1080×1080, `vertical` 1080×1350 y `banner` 1920×640. Opciones: `--solo carbono`, `--muestras 128`, `--placa AP_RL4` (otra placa dentro de la caja). Las texturas son un efecto visual: la superficie real depende del material y de la impresora.

## Límites

- Son renders de diseño: nada está impreso ni fabricado. Los colores de las placas son solo de apariencia (KiCad exporta las piezas sin material).
- El cuerpo del relé es una caja del tamaño de su contorno, no el modelo del fabricante.
- Las ventanas de la caja son aproximadas: comprueba con la placa real antes de imprimir.
- La caja se renderiza vacía por dentro salvo la placa; no incluye bornas enchufables ni cables.

## Estilo rústico (banco de madera)

`render_rustico.py` arma un taller: tablones de madera, caja negra con la placa AP Rack 16 dentro (salidas encendidas), una fuente de 24 V genérica y el cable de alimentación unido al conector J1 de la placa, con carrete, destornillador, punteras y tornillos de latón. `foto_final.py` le da viñeta, grano y tono cálido y copia los resultados a `web/img/rustico/`.

    /tmp/claude-0/bpyenv/bin/python blender/render_rustico.py -- --res 1400x875 --muestras 64 --rehacer si
    python3 blender/foto_final.py

Escenas: `banco_general`, `cable_union`, `plano_cenital`, `tablero_fuente`. La fuente, el carrete y las herramientas son objetos genéricos de ambientación; las texturas son un efecto visual. Nada está fabricado ni medido. El modelo 3D de la unión está en `web/modelos3d/AP_RACK16_CABLE24V.glb` (`materiales/modelo_placa_cable.py`).

Con `APPLC=1` la misma escena usa el **AP PLC C24** y su caja (`caja_plc.stl`): `APPLC=1 python render_rustico.py -- --salida blender/renders/rustico_plc --solo banco_general` (también `plano_cenital`); `foto_final.py` los copia como `web/img/rustico/plc_*.jpg`.
