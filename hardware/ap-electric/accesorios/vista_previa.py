#!/usr/bin/env python3
"""Genera vista_previa.png: hoja de contacto isométrica de todas las piezas imprimibles (matplotlib, sin GPU)."""
import os
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import accesorios as A

cat = A.generar()
piezas = cat["imprimibles"]
cols = 5
filas = (len(piezas) + cols - 1) // cols
fig = plt.figure(figsize=(cols * 3.6, filas * 3.7), dpi=110)
luz = np.array([0.4, -0.5, 0.75]); luz /= np.linalg.norm(luz)
for i, p in enumerate(piezas):
    t = trimesh.load(os.path.join(A.HERE, p["archivo"]))
    ax = fig.add_subplot(filas, cols, i + 1, projection="3d")
    tri = t.vertices[t.faces]
    sombra = 0.35 + 0.65 * np.clip(t.face_normals @ luz, 0, 1)
    color = np.outer(sombra, [0.91, 0.36, 0.02]); color = np.clip(color, 0, 1)
    ax.add_collection3d(Poly3DCollection(tri, facecolors=color, edgecolors=(0, 0, 0, 0.05), linewidths=0.2))
    c = t.bounds.mean(axis=0); r = (t.bounds[1] - t.bounds[0]).max() / 2
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=28, azim=-55); ax.set_axis_off()
    ax.set_title("%s\n%s" % (p["sku"], p["nombre"]), fontsize=8)
fig.suptitle("AP Electric · complementos 3D (prototipos de diseño; nada impreso ni probado)", fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig(os.path.join(A.HERE, "vista_previa.png"))
print("vista_previa.png")
