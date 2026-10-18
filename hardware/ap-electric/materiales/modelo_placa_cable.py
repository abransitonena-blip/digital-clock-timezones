#!/usr/bin/env python3
"""Placa AP Rack 16 con su cable de alimentación de 24 V unido al conector J1 (cabecera + carcasa + dos hilos con puntera).

    python3 materiales/modelo_placa_cable.py     (desde hardware/ap-electric)   ->   web/modelos3d/AP_RACK16_CABLE24V.glb

Parte de web/modelos3d/AP_RACK16.glb (misma posición de J1: x 0.111 m, z 0.109 m en el GLB). Conector tipo JST VH y hilo de 16 AWG: medidas de dibujo [H];
nada se ha fabricado ni medido. Los materiales son los de modelos_cables.py (cobre estañado, PVC, PA66).
"""
import math, os, sys
import numpy as np
import trimesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modelos_cables import pieza, MAT

AQUI = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(AQUI, "..", "web", "modelos3d")
J1 = np.array([0.111, 0.0016, 0.109])      # x, y (arriba), z del GLB


def tubo(pts, r, sec=14):
    pts = np.asarray(pts, float)
    ms = []
    for a, b in zip(pts[:-1], pts[1:]):
        L = np.linalg.norm(b - a)
        if L < 1e-9: continue
        c = trimesh.creation.cylinder(radius=r, height=L, sections=sec)
        z = np.array([0, 0, 1.0]); d = (b - a) / L
        T = trimesh.geometry.align_vectors(z, d); T[:3, 3] = (a + b) / 2
        c.apply_transform(T); ms.append(c)
    for p in (pts[0], pts[-1]):
        s = trimesh.creation.icosphere(subdivisions=1, radius=r); s.apply_translation(p); ms.append(s)
    return trimesh.util.concatenate(ms)


def catmull(P, n=14):
    P = [np.array(p, float) for p in P]; P = [P[0]] + P + [P[-1]]; out = []
    for i in range(1, len(P) - 2):
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * P[i]) + (-P[i - 1] + P[i + 1]) * t + (2 * P[i - 1] - 5 * P[i] + 4 * P[i + 1] - P[i + 2]) * t * t + (-P[i - 1] + 3 * P[i] - 3 * P[i + 1] + P[i + 2]) * t ** 3))
    out.append(P[-2]); return np.array(out)


def caja(dx, dy, dz, c):
    m = trimesh.creation.box((dx, dy, dz)); m.apply_translation(c); return m


def main():
    esc = trimesh.load(os.path.join(WEB, "AP_RACK16.glb"))
    pa = MAT["pa66_blanco"]
    # cabecera VH (negra en la realidad se deja en PA66 natural como los demás conectores) y carcasa de acoplamiento
    esc.add_geometry(pieza(caja(0.0100, 0.0090, 0.0082, J1 + [0, 0.0045, 0]), "pa66_blanco"), node_name="cabecera_VH")
    esc.add_geometry(pieza(caja(0.0108, 0.0125, 0.0080, J1 + [0, 0.0090 + 0.0063, 0]), "pa66_blanco"), node_name="carcasa_VH")
    pines = [tubo([J1 + [0, -0.002, s * 0.0020], J1 + [0, 0.012, s * 0.0020]], 0.0006, 8) for s in (-1, 1)]
    esc.add_geometry(pieza(trimesh.util.concatenate(pines), "bronce_fosforado"), node_name="contactos_CuSn5")
    # hilos: salen por arriba de la carcasa, se doblan hacia -x (fuera de la placa) y bajan a la mesa
    for s, color, nom in ((-1, "pvc_rojo", "positivo"), (1, "pvc_negro", "negativo")):
        z0 = J1[2] + s * 0.0020
        ruta = catmull([[J1[0], J1[1] + 0.0155, z0], [J1[0], J1[1] + 0.030, z0], [J1[0] - 0.020, J1[1] + 0.036, z0 + s * 0.004],
                        [J1[0] - 0.050, J1[1] + 0.020, z0 + s * 0.008], [J1[0] - 0.085, J1[1] + 0.004, z0 + s * 0.010], [J1[0] - 0.115, J1[1] + 0.004, z0 + s * 0.010]])
        fin = ruta[-1]
        esc.add_geometry(pieza(tubo(ruta[:-1], 0.0015, 14), color), node_name="aislante_" + nom)
        esc.add_geometry(pieza(tubo([ruta[-2], fin + [-0.003, 0, 0]], 0.0006, 8), "cobre_estanado"), node_name="hilos_" + nom)
        esc.add_geometry(pieza(tubo([fin + [-0.003, 0, 0], fin + [-0.011, 0, 0]], 0.00105, 14), "cobre_estanado"), node_name="puntera_" + nom)
        esc.add_geometry(pieza(tubo([fin, fin + [-0.006, 0, 0]], 0.0016, 14), "pa_collar_rojo"), node_name="collar_" + nom)
    ruta = os.path.join(WEB, "AP_RACK16_CABLE24V.glb")
    esc.export(ruta)
    print("%s  %.0f KB  partes nuevas: cabecera/carcasa VH, contactos, 2 hilos con puntera y collar" % (ruta, os.path.getsize(ruta) / 1024))


if __name__ == "__main__":
    main()
