# Formatos de los modelos 3D de AP Electric

Los mismos modelos en los formatos que se usan en diseño mecánico, impresión 3D, Blender y motores de juego o de visualización.

| Qué | Formatos | Dónde |
|---|---|---|
| **Piezas imprimibles** (29: clips, cubiertas, caja, tapa…) | **STL** · **3MF** · OBJ · FBX | STL en [`../accesorios/stl/`](../accesorios/stl/) · 3MF, OBJ y FBX en `3mf/`, `obj/` y `fbx/` |
| **Placas AP Rack** (Rack 16, IN16, AI8, LED8, RL4, AO4) con sus piezas | **STEP** · **GLB** · FBX · .blend | STEP en `step/` · GLB en [`../web/modelos3d/`](../web/modelos3d/LEEME.md) · FBX en `fbx/` · .blend en `blend/` |
| **Caja AP Rack** (caja, tapa y unión juntas) | GLB · FBX · .blend | `AP_CAJA_RACK` en las mismas carpetas |
| **Escena de piezas** | .blend | `blend/AP_Electric_piezas.blend`: las 29 piezas ordenadas en una cuadrícula, con materiales |

## Cuál usar

| Si vas a… | Usa |
|---|---|
| Imprimir en 3D (Cura, PrusaSlicer, Bambu Studio, OrcaSlicer) | **3MF** (lleva unidades y se abre sin escalar) o STL. Las piezas están en milímetros y apoyadas en z = 0, listas para imprimir |
| Abrir las placas en un programa de CAD mecánico (FreeCAD, Fusion, SolidWorks, Onshape) | **STEP** de `step/`: la placa con sus componentes y los modelos de KiCad |
| Renderizar o animar en Blender | **.blend** (ya trae materiales) o el script de [`../blender/`](../blender/LEEME.md) |
| Llevarlo a Unity, Unreal, Godot u otra herramienta de visualización | **FBX** o GLB (el GLB es el más ligero y funciona en cualquier visor de glTF) |
| Meterlo en un modelador que solo lee mallas | **OBJ** (solo piezas imprimibles; las placas en OBJ pesan unos 5 MB cada una y no se incluyeron) |

## Unidades y orientación

- 3MF y OBJ de las piezas: **milímetros**. FBX y .blend: metros (convención de Blender), Z hacia arriba.
- Las placas (GLB, FBX, .blend) vienen en metros; el STEP en milímetros.
- Los colores de las placas son solo de apariencia (KiCad no exporta materiales); el cuerpo del relé G2RL-1A-E es una caja del tamaño del contorno de la huella, no el modelo del fabricante.

## Cómo se regeneran

`bash tools/exportar_formatos.sh` (desde `hardware/`). El STEP necesita el contenedor de KiCad; los demás formatos necesitan Blender como módulo de Python (`pip install bpy==4.2.0 trimesh`) o se ejecutan dentro de Blender: `blender -b -P formatos/exportar_formatos.py`.

## Límites

- Son modelos de diseño: nada está fabricado ni impreso. Las medidas de los componentes comprados son de dibujo o de catálogo y se deben comprobar con la pieza en la mano.
- Las piezas son mallas triangulares: en STEP solo hay placas, no piezas imprimibles (el diseño paramétrico original está en `../accesorios/accesorios.py`).
