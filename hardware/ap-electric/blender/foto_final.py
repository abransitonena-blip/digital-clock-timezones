#!/usr/bin/env python3
"""Acabado de foto para los renders rústicos: viñeta suave, grano fino y un tono cálido leve.

    python3 blender/foto_final.py        (desde hardware/ap-electric)  ->  blender/renders/rustico/*.jpg  se copian a  web/img/rustico/*.jpg
"""
import glob, os
import numpy as np
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
ENTRADA = os.path.join(AQUI, "renders", "rustico")
SALIDA = os.path.join(AQUI, "..", "web", "img", "rustico")


def foto(ruta, destino, semilla=7):
    a = np.asarray(Image.open(ruta).convert("RGB"), np.float32) / 255.0
    h, w, _ = a.shape
    y, x = np.mgrid[0:h, 0:w]; d = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h / 2) / (h / 2)) ** 2)
    a *= (1.0 - 0.28 * np.clip(d - 0.45, 0, 1) ** 1.5)[..., None]          # viñeta
    a *= np.array([1.03, 1.0, 0.95], np.float32)                           # tono cálido
    a = a + np.random.default_rng(semilla).normal(0, 0.012, a.shape)       # grano
    a = np.clip(a, 0, 1) ** (1 / 1.04)
    Image.fromarray((a * 255 + 0.5).astype(np.uint8)).save(destino, quality=88, optimize=True)


if __name__ == "__main__":
    os.makedirs(SALIDA, exist_ok=True)
    for i, r in enumerate(sorted(glob.glob(os.path.join(ENTRADA, "*.jpg")))):
        foto(r, os.path.join(SALIDA, os.path.basename(r)), 7 + i); print("foto:", os.path.basename(r))
