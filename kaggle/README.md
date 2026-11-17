# AP Model 3D Foto en Kaggle (gratis)

El mismo estudio del notebook de Colab, adaptado a Kaggle: GPU **T4**
(15 GB), unos 29 GB de RAM y 30 horas de GPU gratis por semana.

## Cómo usarlo

1. En https://www.kaggle.com/code pulsa **New Notebook** y luego
   **File › Import Notebook**, y sube `AP_Model_3D_Foto_Kaggle.ipynb`.
2. En el panel derecho, **Session options**:
   - **Accelerator**: `GPU T4 x2`
   - **Internet**: On (Kaggle pide verificar el teléfono una vez)
   - **Persistence**: `Files only` (conserva Blender, lo compilado y tus modelos)
3. Ejecuta las celdas **1, 2, 3**, después la **3b** (prueba) y la **4**
   (página web con contraseña, usuario `ap`).
4. Tus modelos están en `/kaggle/working/ap3d_salidas`: panel **Output** → descargar.

La celda 1 baja la última versión del código desde GitHub (rama
`claude/practical-gates-go63pg`). Si no puede, usa la copia incrustada.

## Qué cambia frente a Colab con A100

| | Colab A100 | Kaggle T4 |
|---|---|---|
| Perfil | MÁXIMO | BÁSICO (octree 256, hasta 40 000 caras) |
| Forma | Turbo y 50 pasos | Solo Turbo (5 pasos) |
| Textura | En la GPU | Paint por partes entre GPU y RAM (más lenta) |
| Multivista, texto a 3D | Activados | Desactivados (se activan en la celda 3; HunyuanDiT, no FLUX) |
| TripoSG | Sí | No (no cabe junto a Hunyuan) |
| Segunda GPU | — | Sin usar |

## Si algo falla

- **«502 Bad gateway» en trycloudflare.com**: la página aún no arrancaba o
  la sesión de Kaggle se detuvo. La celda 4 espera a que responda antes de
  dar el enlace. Si la sesión se detuvo, vuelve a ejecutar 1 → 3 y 4.
- **Avisos «dependency conflicts» de pip** (numba, cudf, bigframes, ydf…):
  son paquetes de Kaggle que este proyecto no usa. Se pueden ignorar.
- **«Ya se importó transformers»**: menú **Run › Restart & clear outputs** y
  vuelve a empezar desde la celda 1.
- **Falta memoria (CUDA out of memory)**: usa el preajuste Turbo y menos caras.

Para regenerar el notebook después de cambiar `colab/ap3d/`:

```bash
python3 kaggle/build_kaggle.py
```
