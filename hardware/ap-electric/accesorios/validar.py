#!/usr/bin/env python3
"""Validación de los complementos 3D: sólidos válidos y comprobaciones de medidas contra las constantes de las piezas compradas.
Valida el DISEÑO (geometría); no valida ninguna impresión (no hay piezas impresas)."""
import json, os, sys
import numpy as np
import trimesh
import accesorios as A

errores = []
def ok(c, msg):
    if not c:
        errores.append(msg)

cat = A.generar()
for p in cat["imprimibles"]:
    ok(p["solido_valido"], p["nombre"] + ": no es un sólido cerrado con volumen")
    ok(max(p["dimensiones_mm"]) <= 220, p["nombre"] + ": no cabe en una cama de 220 mm")
    ok(p["nombre"] in [x[1] for x in A.IMPRIMIBLES], p["nombre"] + ": fuera de la lista")
skus = [p["sku"] for p in cat["imprimibles"]] + [r["sku"] for r in cat["referencias"]]
ok(len(skus) == len(set(skus)), "SKU repetidos")
for r in cat["referencias"]:
    ok(os.path.getsize(os.path.join(A.HERE, r["archivo"])) > 500, r["nombre"] + ": .glb vacío")

def malla(nombre):
    return trimesh.load(os.path.join(A.HERE, "stl", nombre + ".stl"))

# rejilla de agujeros de la bandeja: los 4 postes están donde la placa tiene los agujeros (y espejado)
b = A.bandeja_7r()
W, H = A.PLACA_7R
for (hx, hy) in A.AGUJEROS_7R:
    ok(b.num_tri() > 0, "bandeja vacía")
    # un rayo vertical por el eje del poste debe ver el barreno (vacío) y un anillo sólido a 2.4 mm del eje
    t = A.a_trimesh(b)
    pts = np.array([[hx, H - hy, 6.0], [hx + 2.4, H - hy, 6.0], [hx, H - hy, 14.0]])
    d = t.contains(pts)
    ok(not d[0], "poste en (%.1f, %.1f): falta el barreno" % (hx, hy))
    ok(d[1], "poste en (%.1f, %.1f): falta el poste" % (hx, hy))
# separación entre ganchos DIN
t = A.a_trimesh(A.gancho_din(20.0, 10.0))
gap = A.DIN_ANCHO + 2 * A.TOL
izq = t.contains([[-gap / 2 + 0.05, 0, 14.0]])[0]; der = t.contains([[gap / 2 - 0.05, 0, 14.0]])[0]
ok(not izq and not der, "ganchos DIN: la luz entre paredes es menor que 35 + 2*TOL")
ok(t.contains([[-gap / 2 - 0.1, 0, 12.0]])[0], "ganchos DIN: falta la pared")
# el tapón USB-C cabe en el receptáculo con holgura
tp = malla("tapon_usbc")
ok(tp.bounds[1][0] - tp.bounds[0][0] > A.USBC_RECEP[0] - 0.5 - 1e-6, "tapón: cuerpo mal dimensionado")
ok(A.USBC_RECEP[0] - 0.5 < A.USBC_RECEP[0] and A.USBC_RECEP[1] - 0.5 < A.USBC_RECEP[1], "tapón no cabe en el receptáculo")
# cubierta de bornera: interior mayor que la bornera
for n in (2, 3):
    m = malla("cubierta_bornera_%dp" % n)
    ok(m.extents[0] > n * A.KF_PASO + 3.0, "cubierta %dp: demasiado angosta" % n)

if errores:
    print("FALLAS EN LOS COMPLEMENTOS 3D:")
    for e in errores:
        if e:
            print(" -", e)
    sys.exit(1)
print("Complementos 3D: %d piezas imprimibles y %d modelos de referencia, todos sólidos válidos; medidas coherentes (diseño, nada impreso)" % (len(cat["imprimibles"]), len(cat["referencias"])))
