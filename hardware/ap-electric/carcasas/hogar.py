"""AP Electric · cajas de AP Home: Home Plug (enchufable) y Home Switch (instalación fija). CONCEPTO de diseño.

Usa las herramientas de ../../ap1-gabinete/producto/carcasa.py. Salida: VRML con colores para el render de KiCad (sobre la
placa AP_HOME) y STL del cuerpo para un prototipo impreso.

    python3 hogar.py SALIDA_DIR

Home Plug: la clavija NEMA 5-15P (con tierra) atrás y el receptáculo NEMA 5-15R al frente son piezas compradas,
certificadas, encerradas en la caja; la tierra pasa directo de la clavija al receptáculo sin tocar la placa.
Las medidas de las ranuras aquí son de dibujo; las reales salen del componente que se compre.
"""
import os, sys, importlib.util
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("carcasa", os.path.join(HERE, "..", "..", "ap1-gabinete", "producto", "carcasa.py"))
K = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(K)
from manifold3d import Manifold  # noqa: E402

K.COL.update({"caja": ((0.95, 0.95, 0.94), 0.45, 0.6, 0.0),        # blanco brillante del hogar
              "anillo": ((1.0, 0.62, 0.25), 0.9, 0.9, 0.0)})
W, H = 55.0, 80.0                                                   # placa AP_HOME


def partes():
    return {k: Manifold() for k in K.COL}


def plug():
    P = partes()
    def add(c, m): P[c] = P[c] + m
    u0, v0, u1, v1, zb, zt = -3.5, -3.5, W + 3.5, H + 3.5, -7.0, 31.0
    cuerpo = K.losa(K.redondo(u0, v0, u1, v1, 9.0), zb, zt - zb - 3.0)
    cuerpo = cuerpo + K.losa(K.redondo(u0 + 1.5, v0 + 1.5, u1 - 1.5, v1 - 1.5, 7.5), zt - 3.0, 3.0)
    add("caja", cuerpo)
    zf = zt
    # receptáculo NEMA 5-15R en una placa gris clara
    cu, cv = W / 2, H / 2 + 6
    add("gris", K.losa(K.redondo(cu - 15, cv - 15, cu + 15, cv + 15, 7), zf - 0.2, 0.8))
    for du, lv in ((-6.35, 8.0), (6.35, 6.4)):                        # neutro más largo, fase más corto
        add("oscuro", K.caja(cu + du - 0.9, cv - 3 - lv / 2, zf + 0.0, cu + du + 0.9, cv - 3 + lv / 2, zf + 0.7))
    add("oscuro", K.cilindro(cu, cv + 7.0, zf + 0.0, 0.7, 2.3) - K.caja(cu - 3, cv + 7.0, zf - 1, cu + 3, cv + 10, zf + 2))
    add("oscuro", K.caja(cu - 2.3, cv + 7.0, zf + 0.0, cu + 2.3, cv + 8.8, zf + 0.7))
    # botón con anillo de luz (LED verde por dentro) y LED de falla
    bu, bv = W / 2, 8.5
    add("anillo", K.cilindro(bu, bv, zf - 0.2, 1.0, 5.6) - K.cilindro(bu, bv, zf - 1, 3, 4.8))
    add("caja", K.cilindro(bu, bv, zf - 0.2, 1.6, 4.6))
    add("oscuro", K.texto("I/O", 1.6, bu, bv + 0.8, zf + 1.4, 0.2, "centro"))
    add("rojo", K.cilindro(bu + 11, bv, zf - 0.2, 1.0, 0.9))
    add("texto", K.texto("FALLA", 1.2, bu + 11, bv + 3.6, zf + 0.8, 0.2, "centro"))
    # marca
    add("naranja", K.losa(K.redondo(4, H - 9, 13, H, 2.0), zf + 0.8, 0.4))
    add("blanco", K.texto("AP", 3.6, 8.5, H - 2.9, zf + 1.2, 0.25, "centro"))
    add("texto", K.texto("AP ELECTRIC  HOME PLUG", 2.4, 16, H - 4.0, zf + 0.8, 0.25, ancho_max=W - 20))
    add("texto", K.texto("127 V~  carga: ver etiqueta", 1.6, 16, H - 0.9, zf + 0.8, 0.2, negrita=False))
    # clavija atrás (hojas y tierra), salen por la cara de abajo
    for du in (-6.35, 6.35):
        add("metal", K.caja(cu + du - 0.8, cv - 3 - 3.2, zb - 15.9, cu + du + 0.8, cv - 3 + 3.2, zb + 0.2))
    add("metal", K.cilindro(cu, cv + 7.5, zb - 18.5, 18.7, 2.4))
    return P


def switch():
    P = partes()
    def add(c, m): P[c] = P[c] + m
    u0, v0, u1, v1, zb, zt = -2.5, -2.5, W + 2.5, H + 2.5, -6.0, 26.0
    cuerpo = K.losa(K.redondo(u0, v0, u1, v1, 4.0), zb, zt - zb)
    # bornes: tornillo por un agujero de arriba, cable por la cara del borde (como un módulo de riel)
    for (x, txt) in ((6.0, "N"), (11.08, "L"), (30.92, "SW"), (36.0, "LS")):
        cuerpo = cuerpo - K.cilindro(x, 6.0, 12.0, zt + 1 - 12.0, 2.2)
        cuerpo = cuerpo - K.caja(x - 1.9, -3.5, 3.0, x + 1.9, 2.0, 8.5)
    add("caja", cuerpo)
    for (x, txt) in ((6.0, "N"), (11.08, "L"), (30.92, "SW"), (36.0, "LS")):
        add("gris", K.caja(x - 2.4, 0.4, 2, x + 2.4, 11.2, 12.5))
        add("metal", K.cilindro(x, 6.0, 12.4, 1.0, 1.7))
        add("oscuro", K.caja(x - 1.4, 5.75, 13.3, x + 1.4, 6.25, 13.5))
        add("oscuro", K.caja(x - 1.5, 0.3, 3.5, x + 1.5, 0.45, 8.0))
        add("texto", K.texto(txt, 1.7, x, 13.2, zt, 0.25, "centro"))
    zf = zt
    add("rojo", K.texto("RED 127 V~", 1.8, 47.5, 7.0, zf, 0.25, "centro"))
    add("texto", K.texto("SW = entrada de red, no contacto seco", 1.5, 21.0, 18.0, zf, 0.2, "centro", negrita=False))
    # botón y LED
    add("gris", K.cilindro(30.0, 40.0, zf - 0.3, 1.5, 3.2))
    add("verde", K.cilindro(38.5, 45.5, zf - 0.3, 1.0, 1.0)); add("rojo", K.cilindro(42.5, 45.5, zf - 0.3, 1.0, 1.0))
    add("naranja", K.losa(K.redondo(6, 56, 19, 69, 3.0), zf, 0.5))
    add("blanco", K.texto("AP", 5.2, 12.5, 65.3, zf + 0.5, 0.25, "centro"))
    add("texto", K.texto("AP ELECTRIC", 3.0, 22, 61.5, zf, 0.25))
    add("texto", K.texto("HOME SWITCH", 3.0, 22, 66.5, zf, 0.25))
    add("texto", K.texto("Instalación fija · con neutro · 127 V~", 1.6, 22, 70.5, zf, 0.2, negrita=False))
    add("blanco", K.losa(K.redondo(6, 73, 49, 78.5, 0.8), zf, 0.2))
    return P


if __name__ == "__main__":
    sal = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(sal, exist_ok=True)
    T = np.array([[1, 0, 0, 100.0], [0, -1, 0, -100.0], [0, 0, 1, 0], [0, 0, 0, 1]], float)   # placa en (100, 100)
    for nombre, f in (("plug", plug), ("switch", switch)):
        P = f()
        K.escribir_wrl(P, T, os.path.join(sal, "caja_home_%s.wrl" % nombre))
        c = K.a_trimesh(P["caja"]); c.export(os.path.join(sal, "home_%s_cuerpo.stl" % nombre))
        print(nombre, "estanca" if c.is_watertight else "NO estanca")
