"""Genera AP_Model_3D_Foto_MaxRAM.ipynb con el codigo de ap3d/ incrustado.

    python3 build_notebook.py
"""
import base64
import json
import os
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = ["__init__.py", "config.py", "engine.py", "blender_rig.py", "app.py", "estudio.html"]


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(True)}


def code(text, form=True):
    meta = {"cellView": "form"} if form else {}
    return {"cell_type": "code", "metadata": meta, "execution_count": None,
            "outputs": [], "source": text.strip("\n").splitlines(True)}


payload = {}
for f in SRC:
    data = open(os.path.join(HERE, "ap3d", f), "rb").read()
    payload[f] = base64.b64encode(zlib.compress(data, 9)).decode()
blob = json.dumps(payload)

INTRO = r"""
# AP Model 3D Foto MAX: usa toda la GPU y la RAM (A100 / L4 / T4)

Foto → modelo 3D con textura HD, **esqueleto automático compatible con Mixamo**,
**pesos sin huecos**, **6 animaciones**, piezas por hueso y exportación a
**Blender (.blend) / FBX / GLB animado / OBJ / STL / video MP4**.

**Qué hace distinto esta versión**
* Se ajusta sola al equipo. Con una **A100 de 80 GB + 167 GB de RAM** usa el perfil **MÁXIMO**: forma octree 512, hasta 150 000 caras (antes ~25 000), textura de 4096 px y video de 1080p.
* **Usa la RAM a fondo**: carga en la RAM los pesos de los modelos (cerca de 30 GB) y deja **todos los modelos cargados a la vez** en la GPU (1 foto, varias vistas y textura). Trabaja en `/dev/shm`, un disco en RAM, guarda en caché los resultados y deja que Blender corra **en paralelo** con la siguiente generación.
* **Pesos sin manchas**: los calcula Blender (método de calor) sobre una copia cerrada de la malla y los pasa al modelo real. Cada hueso mueve su zona completa, no solo una banda.
* **Turbo**: forma con 5 pasos + FlashVDM, textura turbo y Blender en dos procesos a la vez (archivos y videos). Barra con **porcentaje y tiempo restante** y **monitor en vivo** de GPU/VRAM/RAM/CPU/temperatura que se pone **en rojo** si algo se satura o hay cola.
* **Ves el modelo antes**: el estudio se abre en cuanto está el GLB animado, mientras los videos siguen renderizándose. El visor usa un **GLB ligero** (Draco + JPEG) que carga mucho más rápido en el celular. La GPU se **precalienta** al cargar y los tiempos aprendidos se guardan entre sesiones.
* **Esqueleto detallado (66 huesos)**: dedos de las manos (5 × 3 falanges, nombres de Mixamo), dedos de los pies, ojos y mandíbula, colocados midiendo la malla. Animaciones nuevas **Manos** y **Hablar**; los dedos se relajan o cierran en las demás.
* **Por etapas, de más a menos**: primero la malla completa de la IA en alta resolución (`malla_alta.glb`, pestaña *Alta*), luego se reduce a las caras pedidas para la textura y el esqueleto.
* **Física de telas**: túnicas, capas, mangas y faldas se liberan de piernas y brazos y cuelgan de la cadera o la espalda, para que no se rasguen al animar. Los vértices duplicados se sueldan y los pesos se calculan con hasta 3 intentos.
* **Piezas con nombre**: Cabeza, Torso, Brazo izq., Mano der., Dedos pie izq.…
* **Malla reparada**: quita trozos sueltos, cierra agujeros y orienta las caras.
* **Cero vértices sin peso**: si alguno queda suelto, copia el peso de su vecino; el informe dice cuántos vértices mueve cada hueso.
* **LOD para juegos**: además del modelo completo, versiones al 50 % y 15 % con el mismo esqueleto y animaciones.
* **Visor web** (`visor.html` en el ZIP): botones para cada animación, cambio de calidad y modo AR en el celular.
* **Multivista**: si subes espalda o perfiles (o una hoja de vistas), usa Hunyuan3D-2mv y pinta también la espalda.

## Cómo usarlo
1. *Entorno de ejecución › Cambiar tipo de entorno de ejecución* → **GPU (A100 recomendado)** y **RAM alta**.
2. Ejecuta las celdas **1, 2 y 3** en orden (la primera vez tardan unos minutos).
3. **Opcional pero recomendado:** ejecuta la **3b**. Genera un modelo de ejemplo sin página web y muestra los tiempos. Si esa celda termina con "LISTO", el motor funciona.
4. Abre la **5. Página web** (o la 4 dentro del notebook). Verás tres pestañas que se llenan en orden: **1 · Malla → 2 · Textura → 3 · Estudio animado**.
5. Para no perder tus modelos, usa la **6. Guardar en Drive**.

**Para actualizar a un notebook nuevo sin reiniciar:** ejecuta la celda **1** (cambia el código y conserva los modelos cargados) y después la **5**.
"""

CELL1 = r'''
# @title 1. Proyecto (código incluido: no necesita Drive ni subir nada)
import base64, json, os, subprocess, sys, zlib
APP = "/content/ap3d_app"
os.makedirs(f"{APP}/ap3d", exist_ok=True)
_FILES = json.loads(r"""__BLOB__""")
for _n, _d in _FILES.items():
    open(f"{APP}/ap3d/{_n}", "wb").write(zlib.decompress(base64.b64decode(_d)))
if APP not in sys.path:
    sys.path.insert(0, APP)
# Si ya habia una version cargada, se cambia por la nueva SIN perder los
# modelos que ya estan en la GPU (antes Colab seguia usando el codigo viejo).
_old = sys.modules.get("ap3d.engine")
_eng = getattr(_old, "_ENGINE", None)
_app = sys.modules.get("ap3d.app")
if _app is not None:
    for _k in ("inline", "web"):
        try:
            _app._SERVERS.pop(_k).close()
        except Exception:
            pass
    try:
        _app._SERVERS.pop("tunnel").terminate()
    except Exception:
        pass
for _m in [m for m in sys.modules if m == "ap3d" or m.startswith("ap3d.")]:
    del sys.modules[_m]
if _eng is not None:
    from ap3d import engine as _e
    _eng.__class__ = _e.Engine
    _eng._ensure()
    _e._ENGINE = _eng
    print("Código actualizado; los modelos siguen cargados en la GPU.")
print(subprocess.run("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader",
                     shell=True, capture_output=True, text=True).stdout.strip() or "SIN GPU: cambia el entorno a GPU")
import psutil
print(f"RAM del sistema: {psutil.virtual_memory().total/2**30:.0f} GB · CPU: {os.cpu_count()}")
print("Proyecto listo en", APP)
'''

CELL2 = r'''
# @title 2. Instalar dependencias, Hunyuan3D-2 y Blender 4.2 LTS
USAR_CACHE_EN_DRIVE = False  # @param {type:"boolean"}
# @markdown Si lo activas, las piezas compiladas se guardan en Drive y la próxima sesión se instalan en segundos.
import os, subprocess, sys, glob, shutil, time
t0 = time.time()

def sh(cmd, check=True):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-3000:], r.stderr[-3000:])
        if check:
            raise RuntimeError("Fallo: " + cmd)
    return r.stdout

# --- sistema (Blender sin ventana necesita estas librerias)
sh("apt-get -qq update && apt-get -qq install -y libxi6 libxkbcommon0 libsm6 libxrender1 "
   "libxxf86vm1 libxfixes3 libgl1 libegl1 libglu1-mesa libopengl0 > /dev/null", check=False)

# --- Python
sh(f"{sys.executable} -m pip install -q 'gradio>=5.9,<6' 'diffusers==0.32.2' 'transformers==4.49.0' 'accelerate>=1.2,<1.6' "
   "einops omegaconf trimesh pymeshlab pygltflib xatlas rembg onnxruntime-gpu "
   "opencv-python-headless ninja pybind11 psutil hf_transfer 'huggingface_hub>=0.25'")
print(f"Paquetes listos ({time.time()-t0:.0f}s)")

# --- Hunyuan3D-2
if not os.path.exists("/content/Hunyuan3D-2"):
    sh("git clone -q --depth 1 https://github.com/Tencent/Hunyuan3D-2 /content/Hunyuan3D-2")
sh(f"cd /content/Hunyuan3D-2 && {sys.executable} -m pip install -q -e . --no-deps")

import torch
cap = "%d.%d" % torch.cuda.get_device_capability(0) if torch.cuda.is_available() else "8.0"
os.environ["TORCH_CUDA_ARCH_LIST"] = cap            # compila solo para tu GPU: mas rapido
os.environ["MAX_JOBS"] = str(os.cpu_count())
tag = f"py{sys.version_info.major}{sys.version_info.minor}_torch{torch.__version__.split('+')[0]}_sm{cap}"
cache = None
if USAR_CACHE_EN_DRIVE:
    from google.colab import drive
    drive.mount("/content/drive")
    cache = f"/content/drive/MyDrive/ap3d_cache/{tag}"
    os.makedirs(cache, exist_ok=True)

def have(mod):
    return subprocess.run([sys.executable, "-c", f"import {mod}"], capture_output=True).returncode == 0

if not have("custom_rasterizer"):
    whl = glob.glob(f"{cache}/custom_rasterizer*.whl") if cache else []
    if whl:
        sh(f"{sys.executable} -m pip install -q {whl[0]}")
        print("custom_rasterizer desde la cache de Drive")
    else:
        print("Compilando custom_rasterizer (3-5 min)...")
        d = "/content/Hunyuan3D-2/hy3dgen/texgen/custom_rasterizer"
        sh(f"cd {d} && {sys.executable} -m pip wheel -q . --no-build-isolation --no-deps -w /content/whl")
        w = glob.glob("/content/whl/custom_rasterizer*.whl")[0]
        sh(f"{sys.executable} -m pip install -q {w}")
        if cache:
            shutil.copy(w, cache)

d = "/content/Hunyuan3D-2/hy3dgen/texgen/differentiable_renderer"
if not glob.glob(f"{d}/mesh_processor*.so"):
    so = glob.glob(f"{cache}/mesh_processor*.so") if cache else []
    if so:
        shutil.copy(so[0], d)
    else:
        sh(f"cd {d} && c++ -O3 -Wall -shared -std=c++11 -fPIC "
           f"$({sys.executable} -m pybind11 --includes) mesh_processor.cpp "
           f"-o mesh_processor$({sys.executable}-config --extension-suffix 2>/dev/null || "
           f"python3-config --extension-suffix)", check=False)
        if not glob.glob(f"{d}/mesh_processor*.so"):
            sh(f"cd {d} && {sys.executable} setup.py build_ext --inplace", check=False)
        if cache:
            for f in glob.glob(f"{d}/mesh_processor*.so"):
                shutil.copy(f, cache)
print(f"Hunyuan3D-2 listo ({time.time()-t0:.0f}s)")

# --- Blender 4.2 LTS
if not os.path.exists("/content/blender/blender"):
    url = "https://download.blender.org/release/Blender4.2/blender-4.2.3-linux-x64.tar.xz"
    sh(f"wget -q {url} -O /content/blender.tar.xz && tar -xf /content/blender.tar.xz -C /content "
       "&& mv /content/blender-4.2.3-linux-x64 /content/blender && rm /content/blender.tar.xz")
print(sh("/content/blender/blender -b --version | head -1").strip())
print(f"Instalación lista en {time.time()-t0:.0f}s")
'''

CELL3 = r'''
# @title 3. Comprobar GPU, descargar modelos, precargarlos en la RAM y cargarlos en la GPU
CARGAR_MULTIVISTA = True  # @param {type:"boolean"}
CARGAR_TEXTURA = True  # @param {type:"boolean"}
MODO_CALIDAD_TAMBIEN = True  # @param {type:"boolean"}
# @markdown Turbo (5 pasos + FlashVDM) siempre se carga: la forma sale en segundos. Con la casilla de arriba también queda cargado el modelo de 50 pasos para el preajuste "Maxima".
import os, sys, time
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
sys.path.insert(0, "/content/ap3d_app")
sys.path.insert(0, "/content/Hunyuan3D-2")
# Hunyuan3D-2 necesita transformers 4.49: con versiones nuevas su codificador
# de imagen (DINOv2) no carga ("Missing key(s) ... main_image_encoder").
import importlib.metadata as _md, subprocess
if _md.version("transformers") != "4.49.0" or not _md.version("diffusers").startswith("0.32"):
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "transformers==4.49.0",
                    "diffusers==0.32.2", "accelerate>=1.2,<1.6"], check=True)
    if "transformers" in sys.modules:
        raise SystemExit("Versiones corregidas. Ve a Entorno de ejecución › Reiniciar sesión "
                         "y vuelve a ejecutar la celda 1 y después esta celda 3.")
import torch
from huggingface_hub import snapshot_download
from ap3d import config
from ap3d.engine import get_engine

print("CUDA:", torch.cuda.is_available())
P = config.detect()
print(config.describe(P))

t = time.time()
pats = ["hunyuan3d-dit-v2-0-turbo/*"] + (["hunyuan3d-dit-v2-0/*"] if MODO_CALIDAD_TAMBIEN else [])
if CARGAR_TEXTURA:
    pats += ["hunyuan3d-paint-v2-0-turbo/*", "hunyuan3d-paint-v2-0/*", "hunyuan3d-delight-v2-0/*"]
snapshot_download("tencent/Hunyuan3D-2", allow_patterns=pats, max_workers=16)
if CARGAR_MULTIVISTA:
    snapshot_download("tencent/Hunyuan3D-2mv", allow_patterns=["hunyuan3d-dit-v2-mv-turbo/*"]
                      + (["hunyuan3d-dit-v2-mv/*"] if MODO_CALIDAD_TAMBIEN else []), max_workers=16)
print(f"Modelos descargados ({time.time()-t:.0f}s)")

eng = get_engine()
if P["preload_weights"]:
    eng.preload_weights()          # deja todos los pesos en la RAM
eng.load(want_mv=CARGAR_MULTIVISTA, want_paint=CARGAR_TEXTURA, want_turbo=True,
         want_quality=MODO_CALIDAD_TAMBIEN)
print("Todo listo. Sigue con la celda 4 o 5.")
'''

CELLT = r'''
# @title 3b. Prueba rápida SIN página web (confirma que el motor funciona y mide tiempos)
import glob, sys, time
sys.path.insert(0, "/content/ap3d_app")
from ap3d.engine import get_engine
_img = sorted(glob.glob("/content/Hunyuan3D-2/assets/example_images/*.png"))[0]
_t = time.time()
_r = get_engine().run(_img, steps=5, octree=384, faces=100000, tex=2048, rig="auto",
                      progress=lambda f, m: print(f"{int(f*100):3d}%  {m}", flush=True) if int(f*100) % 10 == 0 else None)
_i = _r["info"]
print(f"\nLISTO en {time.time()-_t:.0f}s  ->  {_r['zip']}")
print("forma", _i.get("segundos_forma"), "s · textura", _i.get("segundos_textura"),
      "s · Blender", _i.get("segundos_blender"), "s · avisos:", _i.get("avisos"))
'''

CELL4 = r'''
# @title 4. Estudio (dentro del notebook)
import sys; sys.path.insert(0, "/content/ap3d_app")
from ap3d.app import launch_inline
launch_inline(port=7860)
'''

CELL5 = r'''
# @title 5. Abrir la página web con contraseña (para el celular)
CONTRASENA = ""  # @param {type:"string"}
# @markdown Déjala vacía para generar una al azar. El usuario es **ap**. La página deja de funcionar al cerrar la sesión de Colab.
import sys; sys.path.insert(0, "/content/ap3d_app")
from ap3d.app import launch_web
url, user, pw = launch_web(CONTRASENA, user="ap", port=7861)
print("Página web:", url)
print("Usuario:", user, "· Contraseña:", pw)
'''

CELL6 = r'''
# @title 6. Guardar todos los resultados en Google Drive
CARPETA = "AP_Model_3D"  # @param {type:"string"}
import os, shutil, glob
from google.colab import drive
if not os.path.exists("/content/drive/MyDrive"):
    drive.mount("/content/drive")
dst = f"/content/drive/MyDrive/{CARPETA}"
os.makedirs(dst, exist_ok=True)
n = 0
for z in glob.glob("/content/ap3d_salidas/*.zip"):
    if not os.path.exists(os.path.join(dst, os.path.basename(z))):
        shutil.copy(z, dst); n += 1
print(f"{n} modelos nuevos copiados a {dst}")
'''

CELL7 = r'''
# @title 7. (Opcional) Liberar GPU / ver uso de memoria
LIBERAR_MODELOS = False  # @param {type:"boolean"}
import gc, torch, psutil, sys
sys.path.insert(0, "/content/ap3d_app")
from ap3d.engine import get_engine
e = get_engine()
if LIBERAR_MODELOS:
    e.shape = e.shape_mv = e.paint = None; e.ready = False
    gc.collect(); torch.cuda.empty_cache()
e.log_mem()
'''

nb = {
    "nbformat": 4, "nbformat_minor": 0,
    "metadata": {
        "accelerator": "GPU",
        "colab": {"gpuType": "A100", "machine_shape": "hm", "provenance": [],
                  "name": "AP_Model_3D_Foto_MaxRAM.ipynb"},
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "cells": [
        md(INTRO),
        md("## 1. Proyecto (código incluido: no necesita Drive ni subir nada)"),
        code(CELL1.replace("__BLOB__", blob)),
        md("## 2. Instalar dependencias y Blender 4.2 LTS"),
        code(CELL2),
        md("## 3. Comprobar GPU, Blender y modelos de IA (carga todo en RAM y GPU)"),
        code(CELL3),
        md("## 3b. Prueba rápida sin página web (opcional)"),
        code(CELLT),
        md("## 4. Estudio"),
        code(CELL4),
        md("## 5. Abrir la página web con contraseña"),
        code(CELL5),
        md("## 6. Guardar en Drive"),
        code(CELL6),
        md("## 7. Memoria"),
        code(CELL7),
    ],
}
out = os.path.join(HERE, "AP_Model_3D_Foto_MaxRAM.ipynb")
json.dump(nb, open(out, "w"), indent=1, ensure_ascii=False)
print("escrito", out, os.path.getsize(out) // 1024, "KB")
