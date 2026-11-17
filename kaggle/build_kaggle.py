"""Genera AP_Model_3D_Foto_Kaggle.ipynb: el mismo estudio del notebook de
Colab, adaptado a Kaggle (2x T4 de 15 GB, ~29 GB de RAM, /kaggle/working).

    python3 kaggle/build_kaggle.py

La celda 1 baja la ultima version del codigo (colab/ap3d) desde GitHub; si no
puede, usa la copia que va incrustada en el notebook.
"""
import base64
import json
import os
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(HERE, "..", "colab", "ap3d")
SRC = ["__init__.py", "config.py", "engine.py", "blender_rig.py", "escena.py", "app.py",
       "memoria.py", "estudio.html"]
REPO = "abransitonena-blip/digital-clock-timezones"
RAMA = "claude/practical-gates-go63pg"


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(True)}


def code(text):
    return {"cell_type": "code", "metadata": {"trusted": True}, "execution_count": None,
            "outputs": [], "source": text.strip("\n").splitlines(True)}


payload = {}
for f in SRC:
    data = open(os.path.join(SRC_DIR, f), "rb").read()
    payload[f] = base64.b64encode(zlib.compress(data, 9)).decode()
blob = json.dumps(payload)

INTRO = r"""
# AP Model 3D Foto en Kaggle (gratis: GPU T4)

Foto → modelo 3D con textura, esqueleto compatible con Mixamo, animaciones y
exportación a GLB / FBX / .blend / OBJ / STL. Es el mismo estudio del notebook
de Colab, adaptado a Kaggle.

## Antes de ejecutar (panel derecho → **Session options**)
1. **Accelerator: `GPU T4 x2`** (se usa una T4; la segunda queda libre).
2. **Internet: On** (hay que verificar el teléfono en tu cuenta de Kaggle).
3. **Persistence: `Files only`** (recomendado). Así `/kaggle/working` se
   conserva entre sesiones: Blender, las piezas compiladas y tus modelos no se
   vuelven a bajar ni a compilar. Sin esto todo empieza de cero cada vez.
4. (Opcional) **Add-ons → Secrets**: `HF_TOKEN` con tu token de Hugging Face.
   No es obligatorio: todos los modelos que usa este notebook son públicos.

## Orden
Ejecuta las celdas **1 → 2 → 3**, luego la **3b** (prueba corta) y la **4**
(página web). La primera vez tarda unos 15-20 min; con persistencia, después
unos 5-8 min (los pesos de IA se bajan en cada sesión, pero con hf_transfer es rápido).

**Límites de Kaggle**: 30 h de GPU por semana, sesiones de hasta 12 h. La
página se apaga cuando se detiene la sesión: **deja abierta la pestaña del
editor de Kaggle** mientras la usas.
"""

CELL1 = r'''
# 1. Proyecto, rutas y equipo
RAMA = "__RAMA__"     # rama de GitHub con el codigo ("" = usar la copia incrustada)
import base64, io, json, os, subprocess, sys, tarfile, urllib.request, zlib

W = "/kaggle/working"
CACHE = f"{W}/ap3d_cache"                 # Blender y piezas compiladas (se conservan con persistencia)
APP = "/root/ap3d_app"
os.environ.update({
    "AP3D_ROOT": "/root/ap3d",
    "AP3D_OUT": f"{W}/ap3d_salidas",          # modelos y aprendizaje: aparecen en Output
    "AP3D_BLENDER": f"{CACHE}/blender/blender",
    "AP3D_HY3D": "/root/Hunyuan3D-2",
    "AP3D_TRIPOSG": "/root/TripoSG",
    "AP3D_CLOUDFLARED": f"{CACHE}/cloudflared",
    "HF_HUB_ENABLE_HF_TRANSFER": "1",
    "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
    "GRADIO_ANALYTICS_ENABLED": "False",
})
for d in (CACHE, APP + "/ap3d", os.environ["AP3D_OUT"]):
    os.makedirs(d, exist_ok=True)

origen = "copia incrustada"
if RAMA:
    try:
        url = f"https://codeload.github.com/__REPO__/tar.gz/refs/heads/{RAMA}"
        tar = tarfile.open(fileobj=io.BytesIO(urllib.request.urlopen(url, timeout=60).read()))
        n = 0
        for m in tar.getmembers():
            p = m.name.split("/", 1)[-1]
            if m.isfile() and p.startswith("colab/ap3d/") and p.count("/") == 2:
                open(f"{APP}/ap3d/{os.path.basename(p)}", "wb").write(tar.extractfile(m).read())
                n += 1
        if n >= 6:
            origen = f"GitHub ({RAMA}, {n} archivos)"
    except Exception as e:
        print("GitHub no disponible, uso la copia incrustada:", str(e)[:100])
if origen == "copia incrustada":
    for _n, _d in json.loads(r"""__BLOB__""").items():
        open(f"{APP}/ap3d/{_n}", "wb").write(zlib.decompress(base64.b64decode(_d)))
if APP not in sys.path:
    sys.path.insert(0, APP)
for _m in [m for m in sys.modules if m == "ap3d" or m.startswith("ap3d.")]:
    del sys.modules[_m]

print("Código:", origen)
print(subprocess.run("nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader",
                     shell=True, capture_output=True, text=True).stdout.strip()
      or "SIN GPU: en Session options elige Accelerator = GPU T4 x2")
import psutil
print(f"RAM {psutil.virtual_memory().total/2**30:.0f} GB · CPU {os.cpu_count()} · "
      f"disco libre {psutil.disk_usage('/').free/2**30:.0f} GB · "
      f"/kaggle/working libre {psutil.disk_usage(W).free/2**30:.0f} GB")
'''

CELL2 = r'''
# 2. Instalar dependencias, Hunyuan3D-2 y Blender 4.5 LTS
INSTALAR_TRIPOSG = False   # TripoSG casi no cabe en una T4 junto a Hunyuan; dejalo en False
import glob, os, shutil, subprocess, sys, time
t0 = time.time()
CACHE = "/kaggle/working/ap3d_cache"
HY3D = os.environ["AP3D_HY3D"]

def sh(cmd, check=True):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-3000:])
        if check:
            raise RuntimeError("Falló: " + cmd[:120])
    return r.stdout

if "transformers" in sys.modules or "diffusers" in sys.modules:
    raise SystemExit("Ya se importó transformers/diffusers en esta sesión. Ve a Run › Restart & clear "
                     "outputs y ejecuta de nuevo las celdas 1 y 2.")

# --- sistema: librerias para Blender sin ventana (los avisos de apt no importan)
sh("apt-get -qq update > /dev/null 2>&1; apt-get -qq install -y libxi6 libxkbcommon0 libsm6 "
   "libxrender1 libxxf86vm1 libxfixes3 libgl1 libegl1 libglu1-mesa libopengl0 > /dev/null 2>&1",
   check=False)

# --- Python. Se deja el torch de Kaggle. Gradio 5 + transformers 4.49 + diffusers 0.32 son las
# versiones que necesita Hunyuan3D-2; huggingface_hub < 1.0 hace que encajen entre si.
# Pip mostrara "dependency conflicts" de paquetes de Kaggle que no se usan (numba, cudf, bigframes...).
sh(f"{sys.executable} -m pip install -q 'gradio>=5.9,<6' 'diffusers==0.32.2' 'transformers==4.49.0' "
   "'accelerate>=1.2,<1.6' 'huggingface_hub>=0.28,<1.0' einops omegaconf trimesh pymeshlab pygltflib "
   "xatlas rembg onnxruntime-gpu opencv-python-headless ninja pybind11 psutil hf_transfer "
   "sentencepiece protobuf scipy")
print(f"Paquetes listos ({time.time()-t0:.0f} s)")

# --- Hunyuan3D-2
if not os.path.exists(HY3D):
    sh(f"git clone -q --depth 1 https://github.com/Tencent/Hunyuan3D-2 {HY3D}")
sh(f"cd {HY3D} && {sys.executable} -m pip install -q -e . --no-deps")
if HY3D not in sys.path:
    sys.path.insert(0, HY3D)

import torch
assert torch.cuda.is_available(), "Sin GPU: en Session options elige Accelerator = GPU T4 x2"
cap = "%d.%d" % torch.cuda.get_device_capability(0)
os.environ["TORCH_CUDA_ARCH_LIST"] = cap
os.environ["MAX_JOBS"] = str(os.cpu_count())
if not shutil.which("nvcc") and os.path.exists("/usr/local/cuda/bin/nvcc"):
    os.environ["PATH"] = "/usr/local/cuda/bin:" + os.environ["PATH"]
    os.environ.setdefault("CUDA_HOME", "/usr/local/cuda")
tag = f"py{sys.version_info.major}{sys.version_info.minor}_torch{torch.__version__.split('+')[0]}_sm{cap}"
cc = f"{CACHE}/compilado/{tag}"
os.makedirs(cc, exist_ok=True)

def have(mod):
    return subprocess.run([sys.executable, "-c", f"import torch, {mod}"], capture_output=True).returncode == 0

if not have("custom_rasterizer"):
    whl = glob.glob(f"{cc}/custom_rasterizer*.whl")
    if whl:
        print("custom_rasterizer: desde la caché")
    else:
        assert shutil.which("nvcc"), "No encuentro nvcc (CUDA) para compilar custom_rasterizer"
        print("Compilando custom_rasterizer (5-8 min la primera vez)...")
        sh(f"cd {HY3D}/hy3dgen/texgen/custom_rasterizer && {sys.executable} -m pip wheel -q . "
           f"--no-build-isolation --no-deps -w {cc}")
        whl = glob.glob(f"{cc}/custom_rasterizer*.whl")
    sh(f"{sys.executable} -m pip install -q --force-reinstall --no-deps {whl[0]}")

d = f"{HY3D}/hy3dgen/texgen/differentiable_renderer"
if not glob.glob(f"{d}/mesh_processor*.so"):
    so = glob.glob(f"{cc}/mesh_processor*.so")
    if not so:
        suf = sh(f"{sys.executable} -c \"import sysconfig;print(sysconfig.get_config_var('EXT_SUFFIX'))\"").strip()
        sh(f"cd {d} && c++ -O3 -Wall -shared -std=c++11 -fPIC $({sys.executable} -m pybind11 --includes) "
           f"mesh_processor.cpp -o {cc}/mesh_processor{suf}")
        so = glob.glob(f"{cc}/mesh_processor*.so")
    shutil.copy(so[0], d)
print(f"Hunyuan3D-2 listo ({time.time()-t0:.0f} s)")

# --- Blender 4.5 LTS (4.2 de respaldo), guardado en /kaggle/working/ap3d_cache
B = os.environ["AP3D_BLENDER"]
if not os.path.exists(B):
    for ver, serie in (("4.5.3", "4.5"), ("4.5.2", "4.5"), ("4.2.3", "4.2")):
        url = f"https://download.blender.org/release/Blender{serie}/blender-{ver}-linux-x64.tar.xz"
        r = subprocess.run(f"wget -q {url} -O /tmp/b.tar.xz && tar -xf /tmp/b.tar.xz -C {CACHE} && "
                           f"rm -rf {CACHE}/blender && mv {CACHE}/blender-{ver}-linux-x64 {CACHE}/blender",
                           shell=True)
        subprocess.run("rm -f /tmp/b.tar.xz", shell=True)
        if r.returncode == 0 and os.path.exists(B):
            break

# --- TripoSG (opcional)
if INSTALAR_TRIPOSG:
    T = os.environ["AP3D_TRIPOSG"]
    if not os.path.exists(T):
        sh(f"git clone -q --depth 1 https://github.com/VAST-AI-Research/TripoSG {T}", check=False)
    sh(f"{sys.executable} -m pip install -q peft jaxtyping typeguard scikit-image", check=False)
    os.environ["FORCE_CUDA"] = "1"
    r = sh(f"{sys.executable} -m pip install -q --no-build-isolation diso", check=False)

print(sh(f"{B} -b --factory-startup --version | head -1").strip())
ok = have("custom_rasterizer") and glob.glob(f"{d}/mesh_processor*.so") and os.path.exists(B)
print(("✅" if ok else "⚠️"), f"Instalación lista en {time.time()-t0:.0f} s")
'''

CELL3 = r'''
# 3. Modo de esta página y modelos
# "Optimizar": NO carga la IA. Sube un .glb/.fbx/.obj que ya tienes (por ejemplo
#   del Colab A100) y aquí se reduce de polígonos, se repara, se hace Roblox y QA.
#   Arranca en segundos y deja la T4 libre.
# "Generar": carga la IA Turbo (forma + textura) como en Colab, más lento en la T4.
MODO = "Optimizar"  # @param ["Optimizar", "Generar"]
CARGAR_MULTIVISTA = False   # varias fotos (espalda, perfiles): +5 GB de disco y ~6 GB de RAM
CARGAR_TEXTO_A_3D = False   # texto -> imagen -> 3D con HunyuanDiT (FLUX no cabe en una T4 con 29 GB de RAM)
import os, sys, time
sys.path.insert(0, "/root/ap3d_app"); sys.path.insert(0, os.environ["AP3D_HY3D"])
try:
    from kaggle_secrets import UserSecretsClient
    os.environ["HF_TOKEN"] = UserSecretsClient().get_secret("HF_TOKEN") or ""
except Exception:
    pass
if not os.environ.get("HF_TOKEN", "").startswith("hf_"):
    os.environ.pop("HF_TOKEN", None)          # un token vacio o falso bloquea las descargas publicas
os.environ["AP3D_T2I"] = "hunyuan"            # FLUX (12B) no cabe en la T4
import logging, warnings
warnings.filterwarnings("ignore")
import torch
from huggingface_hub import snapshot_download
from ap3d import config
from ap3d.engine import get_engine

t0 = time.time()
P = config.detect()
print(config.describe(P))

def paso(nombre, fn):
    t = time.time()
    print(f"▶ {nombre}...", flush=True)
    try:
        r = fn()
        print(f"  ✓ {nombre} en {time.time()-t:.0f} s", flush=True)
        return r
    except Exception as e:
        print(f"  ⚠ {nombre}: {e}", flush=True)

os.environ["AP3D_MODO"] = MODO.lower()
if MODO == "Optimizar":
    eng = get_engine()
    print("Modo Optimizar listo: sin modelos de IA. Sigue con la celda 4 (página web) y usa "
          "la pestaña «Optimizar».")
else:
    # En la T4 solo se usan los modelos Turbo (5 pasos): los de 50 pasos no caben junto a la textura.
    paso("Hunyuan3D-2 (forma Turbo + textura)", lambda: snapshot_download("tencent/Hunyuan3D-2", max_workers=16,
         allow_patterns=["hunyuan3d-dit-v2-0-turbo/*", "hunyuan3d-vae-v2-0-turbo/*",
                         "hunyuan3d-paint-v2-0-turbo/*", "hunyuan3d-paint-v2-0/*", "hunyuan3d-delight-v2-0/*"]))
    if CARGAR_MULTIVISTA:
        paso("Hunyuan3D-2mv Turbo", lambda: snapshot_download("tencent/Hunyuan3D-2mv", max_workers=16,
             allow_patterns=["hunyuan3d-dit-v2-mv-turbo/*", "hunyuan3d-vae-v2-mv-turbo/*"]))
    if CARGAR_TEXTO_A_3D:
        paso("HunyuanDiT", lambda: snapshot_download("Tencent-Hunyuan/HunyuanDiT-v1.1-Diffusers-Distilled",
                                                     max_workers=16))

    eng = get_engine()
    paso("Cargar modelos en la GPU", lambda: eng.load(want_mv=CARGAR_MULTIVISTA, want_paint=True,
                                                       want_turbo=True, want_quality=False))
    if os.path.isdir(os.path.join(config.TRIPOSG_PESOS, "TripoSG")):
        paso("TripoSG", eng.load_triposg)
    print(f"\nGPU {P['gpu']} · VRAM usada {torch.cuda.memory_allocated()/2**30:.1f} GB · "
          f"textura IA {'sí' if eng.paint is not None else 'NO'} · total {time.time()-t0:.0f} s")
    print("Listo. Sigue con la 3b (prueba) o la 4 (página web).")
'''

CELLT = r'''
# 3b. Prueba corta SIN página web: confirma que todo funciona y mide tiempos
import glob, os, time
from ap3d.engine import get_engine
_img = sorted(glob.glob(os.path.join(os.environ["AP3D_HY3D"], "assets/example_images/*.png")))[0]
print("Imagen de prueba:", os.path.basename(_img))
_t = time.time(); _last = [None]
def _p(f, m):
    if m != _last[0]:
        _last[0] = m
        print(f"[{time.time()-_t:5.0f} s] {int(f*100):3d}%  {m}", flush=True)
_r = get_engine().run(_img, steps=5, octree=256, faces=40000, tex=2048, rig="auto",
                      tex_rapida=True, progress=_p)
_i = _r["info"]
print("\n======== RESULTADO (mándame esto para revisar) ========")
print(f"Listo en {time.time()-_t:.0f} s  ->  {_r['zip']}")
print(f"Tiempos: forma {_i.get('segundos_forma')} s · textura {_i.get('segundos_textura')} s · "
      f"Blender {_i.get('segundos_blender')} s")
print(f"Detectado: {(_i.get('clasificacion') or {}).get('tipo', _i.get('rig'))} · huesos {_i.get('huesos')} · "
      f"malla IA {_i.get('caras_alta')} -> {_i.get('caras')} caras")
print("Avisos:", _i.get("avisos") or "ninguno")
'''

CELL4 = r'''
# 4. Página web con contraseña (se abre en el celular)
CONTRASENA = ""   # vacía = se genera una al azar. Usuario: ap
import time, urllib.request, urllib.error
from ap3d.app import launch_web
url, user, pw = launch_web(CONTRASENA, user="ap", port=7861)

# Espera a que la página responda a traves del tunel (evita abrirla y ver "502 Bad gateway")
estado = "sin respuesta"
for _ in range(30):
    try:
        urllib.request.urlopen(url + "/config", timeout=10)
        estado = "ok"
    except urllib.error.HTTPError as e:
        estado = "ok" if e.code in (401, 403) else f"HTTP {e.code}"   # 401 = pide contraseña: funciona
    except Exception as e:
        estado = str(e)[:60]
    if estado == "ok":
        break
    time.sleep(3)
print("Página web:", url, "✅" if estado == "ok" else f"⚠️ ({estado}; espera 1 min y recarga)")
print("Usuario:", user, "· Contraseña:", pw)
print("Deja abierta la pestaña de Kaggle: si la sesión se detiene, la página deja de funcionar.")
'''

CELL5 = r'''
# 5. Tus modelos: están en /kaggle/working/ap3d_salidas (panel Output → descargar)
import glob, os
zs = sorted(glob.glob("/kaggle/working/ap3d_salidas/*.zip"), key=os.path.getmtime, reverse=True)
for z in zs[:30]:
    print(f"{os.path.getsize(z)/2**20:7.1f} MB  {os.path.basename(z)}")
print(f"{len(zs)} modelos. Con Persistence = Files only se conservan para la próxima sesión.")
'''

CELL6 = r'''
# 6. (Si algo falla) memoria y estado
from ap3d.engine import get_engine
get_engine().log_mem()
'''

nb = {
    "nbformat": 4, "nbformat_minor": 4,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
        "kaggle": {"accelerator": "nvidiaTeslaT4", "isInternetEnabled": True,
                   "isGpuEnabled": True, "language": "python"},
    },
    "cells": [
        md(INTRO),
        md("## 1. Proyecto"),
        code(CELL1.replace("__BLOB__", blob).replace("__REPO__", REPO).replace("__RAMA__", RAMA)),
        md("## 2. Instalar (la primera vez 10-15 min)"),
        code(CELL2),
        md("## 3. Modelos de IA"),
        code(CELL3),
        md("## 3b. Prueba rápida sin página web (recomendada)"),
        code(CELLT),
        md("## 4. Página web"),
        code(CELL4),
        md("## 5. Descargar tus modelos"),
        code(CELL5),
        md("## 6. Diagnóstico"),
        code(CELL6),
    ],
}
out = os.path.join(HERE, "AP_Model_3D_Foto_Kaggle.ipynb")
json.dump(nb, open(out, "w"), indent=1, ensure_ascii=False)
print("escrito", out, os.path.getsize(out) // 1024, "KB")
