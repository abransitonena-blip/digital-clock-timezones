#!/usr/bin/env python3
"""Pasa los GLB de generativo/salida (mm, z arriba) a los de la web (metros, y arriba) en web/modelos3d, igual que las placas."""
import math, os
import trimesh
AQUI = os.path.dirname(os.path.abspath(__file__))
for origen, destino in (("soporte_riel_generativo.glb", "AP_SOPORTE_GENERATIVO.glb"), ("tapa_ventilada_generativa.glb", "AP_TAPA_VENTILADA.glb")):
    esc = trimesh.load(os.path.join(AQUI, "salida", origen))
    esc.apply_scale(0.001)
    esc.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0]))
    ruta = os.path.join(AQUI, "..", "web", "modelos3d", destino)
    esc.export(ruta)
    print(destino, round(os.path.getsize(ruta) / 1024), "KB")
