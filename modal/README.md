# AP Model 3D Foto en Modal

La misma página web (Gradio) del notebook de Colab, pero en **Modal**, con una
**URL fija** y una GPU **A100-80GB**. No hay que ejecutar celdas: abres la URL
y, si el servidor estaba apagado, arranca solo.

- `modal_app.py`: imagen (CUDA 12.4, Python 3.11, la receta de las celdas 2 y 3
  del notebook), volúmenes, secretos y la web.
- El código del proyecto sigue en `colab/ap3d/` (el mismo que usa Colab).

## Qué se crea en tu cuenta de Modal

| Nombre | Tipo | Para qué |
|---|---|---|
| `ap-model-3d-foto` | App | La web y las funciones |
| `ap3d-cache` | Volumen | Pesos de IA (unos 80 GB, se bajan una vez) |
| `ap3d-salidas` | Volumen | Modelos generados, `aprendizaje.json`, `tiempos.json` |
| `ap3d-web` | Secreto | Usuario y contraseña de la página |
| `ap3d-hf` | Secreto | Token de Hugging Face (FLUX, opcional) |

## 1. Instalar Modal e iniciar sesión (una vez)

En tu computadora, con Python 3.10 o más nuevo:

```bash
pip install -U modal
```

```bash
modal token new
```

Se abre el navegador; entra con tu cuenta y elige el workspace `ap9871888`.
**No pegues el token en ningún chat.**

Desde **Colab**, en una celda:

```
!pip install -q -U modal
!modal token new
```

La celda muestra un enlace: ábrelo, autoriza y vuelve.

## 2. Crear los secretos (una vez)

Contraseña de la página (el usuario por defecto es `ap`):

```bash
modal secret create ap3d-web AP3D_PASSWORD='elige-una-contraseña-larga' AP3D_USER=ap
```

Token de Hugging Face para **FLUX.1-schnell** (texto a 3D). Antes acepta la
licencia en https://huggingface.co/black-forest-labs/FLUX.1-schnell:

```bash
modal secret create ap3d-hf HF_TOKEN='hf_...'
```

Si **no** tienes token, crea el secreto igual con un valor de relleno. Se usará
HunyuanDiT, que no pide nada:

```bash
modal secret create ap3d-hf HF_TOKEN=ninguno
```

También se pueden crear desde el panel: https://modal.com/secrets

## 3. Clonar el repositorio

```bash
git clone -b claude/practical-gates-go63pg https://github.com/abransitonena-blip/digital-clock-timezones
```

```bash
cd digital-clock-timezones
```

## 4. Descargar los modelos al volumen (una vez, 20-40 min)

```bash
modal run modal/modal_app.py::descargar_modelos
```

La primera vez también **construye la imagen** (unos 20-30 min: compila
`custom_rasterizer`, `mesh_processor` y `diso`, y baja Blender 4.5). Las
siguientes veces se reutiliza.

Opciones: `--no-triposg`, `--no-texto-a-3d`, `--no-calidad` (sin los modelos de
50 pasos, unos 15 GB menos).

## 5. (Recomendado) Prueba sin página web

Es la celda 3b del notebook: genera un modelo de ejemplo e imprime los tiempos.

```bash
modal run modal/modal_app.py::prueba
```

Al final debe mostrar `Tiempos: forma … s · textura … s · Blender … s`.

## 6. Publicar la página

```bash
modal deploy modal/modal_app.py
```

La URL aparece al final del comando y en el panel
(https://modal.com/apps/ap9871888/main → `ap-model-3d-foto` → `Estudio.web`).
Será:

```
https://ap9871888--ap3d.modal.run
```

Entra con el usuario `ap` y tu contraseña. **La URL no cambia** aunque vuelvas
a desplegar.

Para probar cambios sin tocar la URL fija (URL temporal, se apaga con Ctrl+C):

```bash
modal serve modal/modal_app.py
```

### Cómo se comporta

- **Arranque en frío**: si nadie la usó en los últimos 15 min, el contenedor
  está apagado. Al abrir la URL arranca y carga los modelos en la GPU
  (unos 2-4 min). Mientras tanto la página tarda en responder.
- **Apagado automático**: tras 15 min sin peticiones se apaga y deja de cobrar.
  Si la pestaña queda abierta, el monitor sigue pidiendo datos y la mantiene
  encendida: **cierra la pestaña cuando termines**.
- **Un solo contenedor** (`max_containers=1`): la cola y los trabajos de Gradio
  viven en memoria, así que todos los usuarios comparten la misma GPU.
- Los modelos generados quedan en el volumen `ap3d-salidas` (pestaña *Mis
  modelos*). Para bajarlos a tu computadora:

```bash
modal volume get ap3d-salidas salidas ./mis_modelos
```

## Ajustes al desplegar

Variables de entorno **en tu computadora** al ejecutar `modal deploy`:

| Variable | Por defecto | Qué cambia |
|---|---|---|
| `AP3D_GPU` | `A100-80GB` | GPU (`A100-40GB`, `L40S`, `H100`…) |
| `AP3D_CPU` | `8` | Núcleos reservados |
| `AP3D_MEM_GB` | `96` | RAM reservada (con 60 o más se guardan copias de los modelos en RAM) |
| `AP3D_APAGAR_MIN` | `15` | Minutos sin uso antes de apagarse |

Ejemplo:

```bash
AP3D_APAGAR_MIN=5 modal deploy modal/modal_app.py
```

## Cuánto cuesta

Modal cobra **por segundo** mientras el contenedor está encendido (también
durante el arranque y los 15 min de espera antes de apagarse). Apagado no
cobra, salvo el almacenamiento de los volúmenes.

Precios de referencia de Modal (sin verificar: no pude abrir
modal.com/pricing desde este entorno; confírmalos en
https://modal.com/pricing):

| Recurso | Por segundo | Por hora aprox. |
|---|---|---|
| GPU A100 80 GB | $0.000694 | **$2.50** |
| CPU (por núcleo) × 8 | $0.0000131 × 8 | $0.38 |
| RAM (por GiB) × 96 | $0.00000222 × 96 | $0.77 |
| **Total encendido** | | **≈ $3.65 / hora** |

- Con `AP3D_MEM_GB=64` y `AP3D_CPU=4` baja a unos $3.20 por hora.
- El plan Starter incluía $30 de crédito gratis al mes (unas 8 horas así).
- Construir la imagen usa una A10G unos minutos (alrededor de $1.10 por hora).
- Revisa el gasto en https://modal.com/settings/usage y pon un límite en
  *Settings › Usage › Spend limit*.

## Si algo falla

| Síntoma | Qué hacer |
|---|---|
| `Secret 'ap3d-web' not found` | Haz el paso 2 |
| La página se queda cargando la primera vez | Es el arranque en frío. Mira los logs: `modal app logs ap-model-3d-foto` |
| `FLUX no disponible, se usa HunyuanDiT` | Falta el token o aceptar la licencia de FLUX. Funciona igual con HunyuanDiT |
| `TripoSG no disponible` | `diso` no compiló o no bajaste sus pesos. Hunyuan3D sigue funcionando |
| Archivos o visor que no cargan (enlaces `http://`) | Añade `AP3D_ROOT_URL=https://ap9871888--ap3d.modal.run` al secreto `ap3d-web` y vuelve a desplegar |
| Quieres apagarla ya | `modal app stop ap-model-3d-foto` (vuelve con `modal deploy`) |

## Diferencias con Colab

- No hay túnel de Cloudflare: Modal da la URL con HTTPS.
- No hay Google Drive: la memoria de aprendizaje y los resultados quedan en el
  volumen `ap3d-salidas`.
- Los repositorios están en `/opt/` en lugar de `/content/`. El código los lee
  de las variables `AP3D_HY3D`, `AP3D_TRIPOSG` y `AP3D_TRIPOSG_PESOS`. En Colab
  siguen valiendo `/content/...` por defecto, así que el notebook no cambia.
