"""AP Model 3D Foto en Modal (https://modal.com).

Reproduce en una imagen de Modal la instalacion de las celdas 2 y 3 del
notebook de Colab (colab/build_notebook.py) y sirve la misma pagina Gradio
(colab/ap3d/app.py) en una URL fija, con GPU A100-80GB.

Uso (desde la raiz del repositorio):

    modal run modal/modal_app.py::descargar_modelos   # una sola vez (~80 GB)
    modal deploy modal/modal_app.py                   # URL fija
    modal serve modal/modal_app.py                    # pruebas (URL temporal)
    modal run modal/modal_app.py::prueba              # modelo de prueba sin web

Secretos (se crean una vez, ver modal/README.md):
    ap3d-web : AP3D_PASSWORD (obligatorio) y AP3D_USER (opcional, por defecto "ap")
    ap3d-hf  : HF_TOKEN (para FLUX). Si no tienes token, crea HF_TOKEN=ninguno.

Ajustes al desplegar (variables de entorno locales, opcionales):
    AP3D_GPU (A100-80GB), AP3D_CPU (8), AP3D_MEM_GB (96), AP3D_APAGAR_MIN (15)
"""
import os
import pathlib

import modal

APP_NAME = "ap-model-3d-foto"
HERE = pathlib.Path(__file__).resolve().parent
AP3D_SRC = HERE.parent / "colab" / "ap3d"

GPU = os.environ.get("AP3D_GPU", "A100-80GB")
CPU = float(os.environ.get("AP3D_CPU", "8"))
MEM_MB = int(float(os.environ.get("AP3D_MEM_GB", "96")) * 1024)
APAGAR_SEG = int(float(os.environ.get("AP3D_APAGAR_MIN", "15")) * 60)
PORT = 7860

# ---------------------------------------------------------------- rutas
CACHE = "/cache"                      # volumen: pesos de Hugging Face, u2net, TripoSG
DATA = "/data"                        # volumen: modelos generados + aprendizaje.json
HY3D = "/opt/Hunyuan3D-2"
TRIPOSG = "/opt/TripoSG"
BLENDER_DIR = "/opt/blender"
APP_DIR = "/opt/ap3d_app"             # colab/ap3d se copia en /opt/ap3d_app/ap3d

ENV = {
    "HF_HOME": f"{CACHE}/hf",
    "HF_HUB_ENABLE_HF_TRANSFER": "1",
    "U2NET_HOME": f"{CACHE}/u2net",   # rembg
    "AP3D_ROOT": "/root/ap3d",
    "AP3D_OUT": f"{DATA}/salidas",
    "AP3D_BLENDER": f"{BLENDER_DIR}/blender",
    "AP3D_HY3D": HY3D,
    "AP3D_TRIPOSG": TRIPOSG,
    "AP3D_TRIPOSG_PESOS": f"{CACHE}/triposg",
    "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
    "PYTHONPATH": f"{APP_DIR}:{HY3D}",
    "GRADIO_ANALYTICS_ENABLED": "False",
}

# Arquitecturas CUDA: A100 (8.0), A10G/L4 (8.6/8.9), H100 (9.0)
CUDA_ENV = {"TORCH_CUDA_ARCH_LIST": "8.0;8.6;8.9;9.0", "FORCE_CUDA": "1", "MAX_JOBS": "8"}

# ---------------------------------------------------------------- imagen
image = (
    modal.Image.from_registry("nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04", add_python="3.11")
    .entrypoint([])
    # Sistema: compiladores + librerias que Blender necesita sin ventana
    .apt_install(
        "git", "wget", "xz-utils", "build-essential", "ninja-build",
        "libxi6", "libxkbcommon0", "libsm6", "libxrender1", "libxxf86vm1", "libxfixes3",
        "libx11-6", "libxext6", "libgl1", "libegl1", "libglu1-mesa", "libopengl0",
        "libglib2.0-0", "libgomp1",
    )
    # PyTorch para CUDA 12.4
    .pip_install("torch==2.5.1", "torchvision==0.20.1",
                 index_url="https://download.pytorch.org/whl/cu124")
    # Mismas versiones fijas que el notebook (celda 2)
    .pip_install(
        "gradio>=5.9,<6", "diffusers==0.32.2", "transformers==4.49.0", "accelerate>=1.2,<1.6",
        "einops", "omegaconf", "trimesh", "pymeshlab", "pygltflib", "xatlas", "rembg",
        "onnxruntime-gpu", "opencv-python-headless", "ninja", "pybind11", "psutil",
        "hf_transfer", "huggingface_hub>=0.25,<1.0", "sentencepiece", "protobuf", "scipy",
        "numpy<2", "fastapi", "setuptools<81", "wheel",
        # TripoSG
        "peft", "jaxtyping", "typeguard", "scikit-image",
    )
    # Hunyuan3D-2
    .run_commands(
        f"git clone -q --depth 1 https://github.com/Tencent/Hunyuan3D-2 {HY3D}",
        f"cd {HY3D} && pip install -q -e . --no-deps",
    )
    # Extensiones CUDA: se compilan aqui, con GPU, para no hacerlo en cada arranque
    .env(CUDA_ENV)
    .run_commands(
        f"cd {HY3D}/hy3dgen/texgen/custom_rasterizer && pip install -q . --no-build-isolation --no-deps",
        # mesh_processor (pybind11, C++): mismo comando que el notebook
        f"cd {HY3D}/hy3dgen/texgen/differentiable_renderer && "
        "(c++ -O3 -Wall -shared -std=c++11 -fPIC $(python -m pybind11 --includes) mesh_processor.cpp "
        "-o mesh_processor$(python -c 'import sysconfig;print(sysconfig.get_config_var(\"EXT_SUFFIX\"))') "
        "|| python setup.py build_ext --inplace)",
        # TripoSG (opcional): si diso no compila, el motor sigue con Hunyuan3D
        f"git clone -q --depth 1 https://github.com/VAST-AI-Research/TripoSG {TRIPOSG}",
        "pip install -q --no-build-isolation diso || "
        "pip install -q --no-build-isolation git+https://github.com/SarahWeiii/diso || "
        "echo 'AVISO: diso no compilo, TripoSG quedara desactivado'",
        gpu="A10G",
    )
    # Blender 4.5 LTS (4.2.3 de respaldo)
    .run_commands(
        "set -e; for v in 4.5.3:4.5 4.5.2:4.5 4.5.1:4.5 4.2.3:4.2; do "
        "ver=${v%%:*}; serie=${v##*:}; "
        "if wget -q https://download.blender.org/release/Blender$serie/blender-$ver-linux-x64.tar.xz "
        "-O /tmp/b.tar.xz; then tar -xf /tmp/b.tar.xz -C /opt && "
        f"mv /opt/blender-$ver-linux-x64 {BLENDER_DIR} && rm -f /tmp/b.tar.xz && break; fi; done; "
        f"{BLENDER_DIR}/blender -b --factory-startup --version | head -1",
    )
    .env(ENV)
    # Comprobacion: si algo critico falta, la imagen no se construye
    .run_commands(
        "python -c \"import torch, gradio, diffusers, transformers, hy3dgen, custom_rasterizer; "
        "print('torch', torch.__version__, 'gradio', gradio.__version__)\"",
        f"ls {HY3D}/hy3dgen/texgen/differentiable_renderer/mesh_processor*.so",
        gpu="A10G",                   # custom_rasterizer necesita el driver de CUDA para importarse
    )
    # El codigo del proyecto va al final: cambiarlo no reconstruye lo de arriba
    .add_local_dir(str(AP3D_SRC), f"{APP_DIR}/ap3d", ignore=["__pycache__", "*.pyc"])
)

app = modal.App(APP_NAME)
cache_vol = modal.Volume.from_name("ap3d-cache", create_if_missing=True)
data_vol = modal.Volume.from_name("ap3d-salidas", create_if_missing=True)
VOLS = {CACHE: cache_vol, DATA: data_vol}
SECRET_WEB = modal.Secret.from_name("ap3d-web", required_keys=["AP3D_PASSWORD"])
SECRET_HF = modal.Secret.from_name("ap3d-hf", required_keys=["HF_TOKEN"])


# ---------------------------------------------------------------- utilidades
def _token_hf():
    """Deja HF_TOKEN solo si parece un token real: uno falso hace que Hugging
    Face rechace incluso las descargas publicas (401)."""
    t = (os.environ.get("HF_TOKEN") or "").strip()
    if not t.startswith("hf_"):
        os.environ.pop("HF_TOKEN", None)
        return None
    return t


def _flux_disponible():
    try:
        from huggingface_hub import hf_hub_download
        hf_hub_download("black-forest-labs/FLUX.1-schnell", "model_index.json")
        return True
    except Exception:
        return False


# ---------------------------------------------------------------- descarga
@app.function(image=image, volumes=VOLS, secrets=[SECRET_HF], cpu=8, memory=16384,
              timeout=4 * 3600)
def descargar_modelos(triposg: bool = True, texto_a_3d: bool = True, calidad: bool = True):
    """Llena el volumen ap3d-cache con todos los pesos (celda 3 del notebook)."""
    import time
    from huggingface_hub import snapshot_download

    t0 = time.time()
    _token_hf()
    W = 16

    def paso(nombre, fn):
        t = time.time()
        print(f"▶ {nombre}...", flush=True)
        try:
            r = fn()
            print(f"  ✓ {nombre} en {time.time() - t:.0f} s", flush=True)
            return r
        except Exception as e:
            print(f"  ⚠ {nombre}: {e}", flush=True)
            return None
        finally:
            cache_vol.commit()          # lo descargado queda guardado aunque algo falle despues

    pats = ["hunyuan3d-dit-v2-0-turbo/*", "hunyuan3d-paint-v2-0-turbo/*",
            "hunyuan3d-paint-v2-0/*", "hunyuan3d-delight-v2-0/*"]
    if calidad:
        pats.append("hunyuan3d-dit-v2-0/*")
    paso("Hunyuan3D-2", lambda: snapshot_download("tencent/Hunyuan3D-2", allow_patterns=pats,
                                                   max_workers=W))
    mv = ["hunyuan3d-dit-v2-mv-turbo/*"] + (["hunyuan3d-dit-v2-mv/*"] if calidad else [])
    paso("Hunyuan3D-2mv", lambda: snapshot_download("tencent/Hunyuan3D-2mv", allow_patterns=mv,
                                                     max_workers=W))
    if triposg:
        pw = ENV["AP3D_TRIPOSG_PESOS"]
        paso("TripoSG", lambda: snapshot_download("VAST-AI/TripoSG", local_dir=f"{pw}/TripoSG",
                                                  max_workers=W))
        paso("RMBG-1.4", lambda: snapshot_download("briaai/RMBG-1.4", local_dir=f"{pw}/RMBG-1.4",
                                                   max_workers=W))
    if texto_a_3d:
        if _flux_disponible():
            paso("FLUX.1-schnell", lambda: snapshot_download(
                "black-forest-labs/FLUX.1-schnell", max_workers=W,
                ignore_patterns=["flux1-schnell.safetensors", "ae.safetensors", "*.md"]))
        else:
            print("FLUX sin acceso (falta HF_TOKEN o aceptar la licencia): se usa HunyuanDiT")
        # HunyuanDiT siempre: es el respaldo si FLUX falla
        paso("HunyuanDiT", lambda: snapshot_download(
            "Tencent-Hunyuan/HunyuanDiT-v1.1-Diffusers-Distilled", max_workers=W))

    def _u2net():
        from rembg import new_session
        new_session("u2net")
    paso("rembg u2net", _u2net)

    import subprocess
    subprocess.run(["du", "-sh", *[str(p) for p in pathlib.Path(CACHE).iterdir()]], check=False)
    print(f"Descarga completa en {(time.time() - t0) / 60:.1f} min")


# ---------------------------------------------------------------- motor
def _cargar_motor(log=print):
    """Celda 3 del notebook: perfil, precarga en RAM y modelos en la GPU."""
    import sys
    import time
    for p in (APP_DIR, HY3D):
        if p not in sys.path:
            sys.path.insert(0, p)
    if not _token_hf() or not _flux_disponible():
        os.environ["AP3D_T2I"] = "hunyuan"
    from ap3d import config
    from ap3d.engine import get_engine

    t = time.time()
    P = config.detect()
    log(config.describe(P))
    eng = get_engine()
    if P.get("preload_weights"):
        eng.preload_weights()
    eng.load(want_mv=True, want_paint=True, want_turbo=True, want_quality=True)
    if os.path.isdir(os.path.join(ENV["AP3D_TRIPOSG_PESOS"], "TripoSG")):
        eng.load_triposg()
    log(f"Motor listo en {time.time() - t:.0f} s")
    return eng


def lanzar_web(port=PORT, user=None, password=None):
    """Lanza la misma pagina que launch_web() del notebook, sin tunel:
    Modal ya da la URL publica con HTTPS."""
    from ap3d import config
    from ap3d.app import EXAMPLES_DIR, build_ui

    user = user or os.environ.get("AP3D_USER") or "ap"
    password = password or os.environ.get("AP3D_PASSWORD")
    if not password:
        raise RuntimeError("Falta AP3D_PASSWORD (secreto ap3d-web)")
    os.makedirs(config.OUT_DIR, exist_ok=True)
    demo = build_ui()
    # Opcional: URL publica completa si Gradio genera enlaces http:// detras del proxy
    root = os.environ.get("AP3D_ROOT_URL") or None
    demo.launch(root_path=root, server_name="0.0.0.0", server_port=port, share=False, auth=(user, password),
                auth_message="AP Model 3D Foto", prevent_thread_lock=True, show_error=True,
                allowed_paths=[config.OUT_DIR, EXAMPLES_DIR], max_file_size="25mb")
    return demo


@app.cls(
    image=image,
    gpu=GPU,
    cpu=CPU,
    memory=MEM_MB,
    volumes=VOLS,
    secrets=[SECRET_WEB, SECRET_HF],
    timeout=24 * 3600,               # una sesion puede durar todo el dia
    scaledown_window=APAGAR_SEG,     # se apaga (y deja de cobrar) tras X min sin uso
    max_containers=1,                # Gradio guarda la cola y los trabajos en memoria
    min_containers=0,
)
@modal.concurrent(max_inputs=200)    # muchas peticiones HTTP a la vez en el mismo contenedor
class Estudio:
    @modal.enter()
    def cargar(self):
        self.eng = _cargar_motor()

    @modal.web_server(PORT, startup_timeout=600, label="ap3d")
    def web(self):
        self.demo = lanzar_web(PORT)

    @modal.exit()
    def guardar(self):
        data_vol.commit()


# ---------------------------------------------------------------- prueba
@app.function(image=image, gpu=GPU, cpu=CPU, memory=MEM_MB, volumes=VOLS,
              secrets=[SECRET_HF], timeout=3600)
def prueba():
    """Celda 3b: genera un modelo de ejemplo sin pagina web y mide los tiempos."""
    import glob
    import time
    eng = _cargar_motor()
    img = sorted(glob.glob(f"{HY3D}/assets/example_images/*.png"))[0]
    t = time.time()
    ultimo = [None]

    def prog(f, m):
        if m != ultimo[0]:
            ultimo[0] = m
            print(f"[{time.time() - t:5.0f} s] {int(f * 100):3d}%  {m}", flush=True)

    r = eng.run(img, steps=5, octree=384, faces=60000, tex=2048, rig="auto",
                tex_rapida=True, progress=prog)
    i = r["info"]
    print(f"\nListo en {time.time() - t:.0f} s -> {r['zip']}")
    print(f"Tiempos: forma {i.get('segundos_forma')} s · textura {i.get('segundos_textura')} s · "
          f"Blender {i.get('segundos_blender')} s")
    print(f"Detectado: {(i.get('clasificacion') or {}).get('tipo', i.get('rig'))} · "
          f"huesos {i.get('huesos')} · caras {i.get('caras')}")
    print("Avisos:", i.get("avisos") or "ninguno")
    data_vol.commit()
    return {k: i.get(k) for k in ("segundos_forma", "segundos_textura", "segundos_blender",
                                  "segundos_total")}
