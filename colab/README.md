# AP Model 3D Foto MAX (Google Colab)

Subir `AP_Model_3D_Foto_MaxRAM.ipynb` a Colab (Archivo › Subir notebook),
elegir **GPU A100 + RAM alta** y ejecutar las celdas 1 → 5.

- `ap3d/config.py`: detecta GPU/RAM y elige el perfil (MAXIMO en A100 80 GB).
- `ap3d/engine.py`: Hunyuan3D-2 / 2mv (forma), Hunyuan3D-Paint (textura), reparacion de malla, cache en RAM.
- `ap3d/blender_rig.py`: esqueleto Mixamo, pesos por calor sobre proxy voxel, 6 animaciones, exportes y videos.
- `ap3d/app.py`: interfaz Gradio (en el notebook o web con contrasena via Cloudflare).
- `build_notebook.py`: vuelve a generar el .ipynb con el codigo incrustado.
