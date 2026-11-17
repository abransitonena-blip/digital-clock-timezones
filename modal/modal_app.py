"""AP Model 3D Foto en Modal: la misma pagina web del notebook, con GPU A100,
URL fija y los modelos guardados en un volumen (se descargan una sola vez).

Uso (desde la raiz del repositorio):
    modal run modal/modal_app.py::descargar_modelos      # 1a vez: ~80 GB al volumen
    modal deploy modal/modal_app.py                      # publica la pagina
    modal serve modal/modal_app.py                       # (opcional) modo prueba

Secreto (Modal > Secrets), nombre "ap3d":
    PASSWORD=...   contrasena de la pagina (usuario "ap")
    HF_TOKEN=...   opcional, para FLUX en texto a 3D (sin el se usa HunyuanDiT)
"""
import os
import pathlib

import modal

AQUI = pathlib.Path(__file__).resolve().parent
AP3D_LOCAL = AQUI.parent / "colab" / "ap3d"

CUDA_ARCH = "8.0"                 # A100
HF = "/root/.cache/huggingface"
SALIDAS = "/data/salidas"

imagen = (
    modal.Image.from_registry("nvidia/cuda:12.4.1-devel-ubuntu22.04", add_python="3.11")
    .apt_install("git", "wget", "xz-utils", "build-essential", "libxi6", "libxkbcommon0",
                 "libsm6", "libxrender1", "libxxf86vm1", "libxfixes3", "libgl1", "libegl1",
                 "libglu1-mesa", "libopengl0", "libglib2.0-0")
    .pip_install("torch==2.5.1", "torchvision==0.20.1",
                 index_url="https://download.pytorch.org/whl/cu124")
    .pip_install("gradio>=5.9,<6", "diffusers==0.32.2", "transformers==4.49.0",
                 "accelerate>=1.2,<1.6", "einops", "omegaconf", "trimesh", "pymeshlab",
                 "pygltflib", "xatlas", "rembg", "onnxruntime-gpu", "opencv-python-headless",
                 "ninja", "pybind11", "psutil", "hf_transfer", "huggingface_hub>=0.25",
                 "sentencepiece", "protobuf", "scipy", "fastapi", "peft", "jaxtyping",
                 "typeguard", "scikit-image")
    .env({"TORCH_CUDA_ARCH_LIST": CUDA_ARCH, "MAX_JOBS": "8", "FORCE_CUDA": "1"})
    .run_commands(
        # Hunyuan3D-2 + piezas compiladas (rasterizador CUDA y mesh painter)
        "mkdir -p /content && git clone -q --depth 1 https://github.com/Tencent/Hunyuan3D-2 /content/Hunyuan3D-2",
        "cd /content/Hunyuan3D-2 && pip install -q -e . --no-deps",
        "cd /content/Hunyuan3D-2/hy3dgen/texgen/custom_rasterizer && pip install -q . --no-build-isolation --no-deps",
        "cd /content/Hunyuan3D-2/hy3dgen/texgen/differentiable_renderer && "
        "c++ -O3 -Wall -shared -std=c++11 -fPIC $(python -m pybind11 --includes) mesh_processor.cpp "
        "-o mesh_processor$(python3-config --extension-suffix 2>/dev/null || python -c "
        "\"import sysconfig;print(sysconfig.get_config_var('EXT_SUFFIX'))\")",
        # Blender 4.5 LTS
        "wget -q https://download.blender.org/release/Blender4.5/blender-4.5.3-linux-x64.tar.xz -O /tmp/b.tar.xz "
        "&& tar -xf /tmp/b.tar.xz -C /content && mv /content/blender-4.5.3-linux-x64 /content/blender "
        "&& rm /tmp/b.tar.xz",
        # TripoSG (opcional: si diso no compila, el programa sigue con Hunyuan3D)
        "git clone -q --depth 1 https://github.com/VAST-AI-Research/TripoSG /content/TripoSG",
        "pip install -q --no-build-isolation diso || "
        "pip install -q --no-build-isolation git+https://github.com/SarahWeiii/diso || true",
    )
    .env({"AP3D_OUT": SALIDAS, "AP3D_ROOT": "/content/ap3d", "AP3D_BLENDER": "/content/blender/blender",
          "HF_HOME": HF, "HF_HUB_ENABLE_HF_TRANSFER": "1", "U2NET_HOME": f"{HF}/u2net",
          "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"})
    .add_local_dir(str(AP3D_LOCAL), "/content/ap3d_app/ap3d")
)

app = modal.App("ap3d", image=imagen)
vol_hf = modal.Volume.from_name("ap3d-modelos", create_if_missing=True)
vol_out = modal.Volume.from_name("ap3d-salidas", create_if_missing=True)
VOLS = {HF: vol_hf, "/data": vol_out}


def _secretos():
    # Un solo secreto "ap3d": PASSWORD (obligatoria) y HF_TOKEN (opcional, para FLUX)
    return [modal.Secret.from_name("ap3d")]


@app.function(volumes=VOLS, timeout=3 * 3600, cpu=8, memory=32768, secrets=_secretos())
def descargar_modelos(triposg: bool = True, texto: bool = True):
    """Llena el volumen con los pesos (una sola vez; despues arranca rapido)."""
    import time
    from huggingface_hub import snapshot_download
    t = time.time()
    snapshot_download("tencent/Hunyuan3D-2", max_workers=16, allow_patterns=[
        "hunyuan3d-dit-v2-0-turbo/*", "hunyuan3d-dit-v2-0/*", "hunyuan3d-vae-v2-0-turbo/*",
        "hunyuan3d-paint-v2-0-turbo/*", "hunyuan3d-paint-v2-0/*", "hunyuan3d-delight-v2-0/*"])
    print(f"Hunyuan3D-2 ({time.time() - t:.0f}s)")
    snapshot_download("tencent/Hunyuan3D-2mv", max_workers=16,
                      allow_patterns=["hunyuan3d-dit-v2-mv-turbo/*", "hunyuan3d-dit-v2-mv/*"])
    print(f"Hunyuan3D-2mv ({time.time() - t:.0f}s)")
    if triposg:
        snapshot_download("VAST-AI/TripoSG", local_dir=f"{HF}/triposg/TripoSG", max_workers=16)
        snapshot_download("briaai/RMBG-1.4", local_dir=f"{HF}/triposg/RMBG-1.4", max_workers=16)
        print(f"TripoSG ({time.time() - t:.0f}s)")
    if texto:
        try:
            snapshot_download("black-forest-labs/FLUX.1-schnell", max_workers=16,
                              ignore_patterns=["flux1-schnell.safetensors", "ae.safetensors", "*.md"])
            print("FLUX listo")
        except Exception as e:
            print("FLUX sin acceso (falta HF_TOKEN o aceptar la licencia):", str(e)[:120])
            snapshot_download("Tencent-Hunyuan/HunyuanDiT-v1.1-Diffusers-Distilled", max_workers=16)
            print("HunyuanDiT listo")
    vol_hf.commit()
    print(f"Modelos en el volumen en {time.time() - t:.0f}s")


@app.function(gpu="A100-80GB", cpu=12, memory=98304, volumes=VOLS, timeout=24 * 3600,
              scaledown_window=15 * 60, max_containers=1, secrets=_secretos())
@modal.concurrent(max_inputs=50)
@modal.asgi_app()
def web():
    """La pagina del estudio. Con max_containers=1 todos ven los mismos modelos
    y la GPU se reparte por la cola de la app."""
    import sys
    import threading
    import time
    sys.path.insert(0, "/content/ap3d_app")
    sys.path.insert(0, "/content/Hunyuan3D-2")
    os.makedirs(SALIDAS, exist_ok=True)
    # TripoSG espera sus pesos dentro de su carpeta: enlace al volumen
    tw = "/content/TripoSG/pretrained_weights"
    if os.path.isdir(f"{HF}/triposg") and not os.path.exists(tw):
        os.symlink(f"{HF}/triposg", tw)
    if not os.environ.get("HF_TOKEN"):
        os.environ["AP3D_T2I"] = "hunyuan"

    import gradio as gr
    from fastapi import FastAPI
    from ap3d import app as ap_app
    from ap3d.engine import get_engine

    eng = get_engine()
    eng.preload_weights()
    eng.load(want_mv=True, want_paint=True, want_turbo=True, want_quality=True)
    if os.path.isdir(tw):
        eng.load_triposg()

    # guardar resultados y lo aprendido en el volumen cada minuto
    def _guardar():
        while True:
            time.sleep(60)
            try:
                vol_out.commit()
            except Exception:
                pass
    threading.Thread(target=_guardar, daemon=True).start()

    demo = ap_app.build_ui()
    pw = os.environ.get("PASSWORD", "")
    return gr.mount_gradio_app(FastAPI(), demo, path="/",
                               auth=("ap", pw) if pw else None,
                               auth_message="AP Model 3D Foto",
                               allowed_paths=[SALIDAS, "/content/Hunyuan3D-2/assets"])


@app.local_entrypoint()
def main():
    print("1) modal run modal/modal_app.py::descargar_modelos   (una vez)")
    print("2) modal deploy modal/modal_app.py                   (publica la pagina)")
