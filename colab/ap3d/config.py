"""Detecta la GPU y la RAM y elige el perfil mas alto que cabe.

Con una A100 de 80 GB y 167 GB de RAM se usa el perfil MAXIMO:
todos los modelos se quedan cargados en la GPU a la vez, los pesos
se precargan en la RAM (cache de paginas + /dev/shm) y la malla, la
textura y el video salen a la resolucion mas alta.
"""
import os
import shutil

import psutil

ROOT = os.environ.get("AP3D_ROOT", "/content/ap3d")
OUT_DIR = os.environ.get("AP3D_OUT", "/content/ap3d_salidas")
BLENDER = os.environ.get("AP3D_BLENDER", "/content/blender/blender")


def _gpu():
    try:
        import torch
        if torch.cuda.is_available():
            p = torch.cuda.get_device_properties(0)
            return p.name, p.total_memory / 2**30
    except Exception:
        pass
    return "CPU", 0.0


def ram_disk(min_free_gb=8):
    """Carpeta de trabajo en RAM (/dev/shm) si hay espacio; si no, disco."""
    try:
        free = shutil.disk_usage("/dev/shm").free / 2**30
        if free >= min_free_gb:
            d = "/dev/shm/ap3d_trabajo"
            os.makedirs(d, exist_ok=True)
            return d, free
    except Exception:
        pass
    d = os.path.join(ROOT, "trabajo")
    os.makedirs(d, exist_ok=True)
    return d, 0.0


def detect():
    name, vram = _gpu()
    ram = psutil.virtual_memory().total / 2**30
    cpus = os.cpu_count() or 2
    work, shm_free = ram_disk()

    if vram >= 70:      # A100 80 GB / H100
        p = dict(perfil="MAXIMO", octree=512, steps=50, chunks=400000,
                 faces=150000, tex=4096, render=2048, all_on_gpu=True,
                 offload=False, video_res=1080, samples=64, workers=3)
    elif vram >= 38:    # A100 40 GB
        p = dict(perfil="ALTO", octree=448, steps=50, chunks=200000,
                 faces=120000, tex=4096, render=2048, all_on_gpu=True,
                 offload=False, video_res=1080, samples=48, workers=2)
    elif vram >= 20:    # L4 24 GB
        p = dict(perfil="MEDIO", octree=384, steps=40, chunks=60000,
                 faces=80000, tex=2048, render=2048, all_on_gpu=False,
                 offload=False, video_res=720, samples=32, workers=2)
    else:               # T4 15 GB
        p = dict(perfil="BASICO", octree=256, steps=30, chunks=8000,
                 faces=40000, tex=2048, render=1024, all_on_gpu=False,
                 offload=True, video_res=720, samples=16, workers=1)

    # Con mucha RAM se guardan copias de los modelos en CPU para no
    # volver a leerlos del disco y se permiten mas trabajos de Blender
    # en paralelo (Blender usa CPU + RAM, no compite con la GPU).
    p["ram_cache_models"] = ram >= 60
    p["preload_weights"] = ram >= 40
    if ram >= 120:
        p["workers"] = max(p["workers"], 3)
    p.update(gpu=name, vram_gb=round(vram, 1), ram_gb=round(ram, 1),
             cpus=cpus, work_dir=work, shm_free_gb=round(shm_free, 1))
    return p


def describe(p):
    return (f"GPU {p['gpu']} ({p['vram_gb']} GB) · RAM {p['ram_gb']} GB · "
            f"{p['cpus']} CPU · perfil {p['perfil']} · octree {p['octree']} · "
            f"hasta {p['faces']:,} caras · textura {p['tex']} px · "
            f"trabajo en {p['work_dir']}")
