# Modelos 3D de las placas AP Rack

Archivos GLB (glTF binario, en metros) de las cinco placas de la cadena AP Rack tal como salen del diseño en KiCad, y de la caja imprimible:

| Archivo | Qué es |
|---|---|
| `AP_RACK16.glb` | AP Rack 16 (16 salidas, 8 entradas) |
| `AP_IN16.glb` | AP Rack IN16 (16 entradas) |
| `AP_AI8.glb` | AP Rack AI8 (8 analógicas) |
| `AP_LED8.glb` | AP Rack LED8 (8 salidas con brillo) |
| `AP_RL4.glb` | AP Rack RL4 (4 relés de contacto seco) |
| `AP_CAJA_RACK.glb` | Caja, tapa y unión impresas en 3D ([accesorios](../../accesorios/LEEME.md), piezas AP-ACC-027 a 029) |

Se ven con el visor de la web (`../index.html`, sección «Modelos 3D»), con Blender o con cualquier visor de glTF.

Cómo se generan: `bash tools/exportar_modelos3d.sh` exporta los GLB con `kicad-cli` y `tools/colorear_glb.py` les pone color por tipo de pieza (KiCad los exporta sin material en las piezas). Los colores son solo de apariencia.

**Límites:** son modelos de diseño. El cuerpo del relé G2RL-1A-E es una caja del tamaño del contorno de la huella (`tools/modelos_propios/`), no el modelo del fabricante; las bornas y los conectores usan los modelos de la librería de KiCad. Nada está fabricado ni medido.
