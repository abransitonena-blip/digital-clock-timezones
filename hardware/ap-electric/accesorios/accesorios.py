#!/usr/bin/env python3
"""AP Electric · complementos 3D (bridas, abrazaderas, anclajes, soportes y modelos de referencia de cables y conectores).

PROTOTIPOS DE DISEÑO PARA IMPRESIÓN 3D. Ninguna pieza se ha impreso ni probado con las piezas reales: las medidas de los
componentes comprados (bornes KF128, USB-C, pila, prensaestopas, sensores) son de dibujo o de catálogo y deben comprobarse
con la pieza en la mano antes de imprimir un lote. Ver LEEME.md.

    python3 accesorios.py            genera stl/ (imprimibles), ref/ (modelos de referencia, no imprimibles) y catalogo.json

Unidades: mm. Cada pieza se apoya en z = 0 (orientación de impresión). Usa manifold3d (sólidos válidos) y trimesh (STL/GLB).
"""
import json, math, os, sys
import numpy as np
import trimesh
from manifold3d import Manifold as M

HERE = os.path.dirname(os.path.abspath(__file__))
TOL = 0.25            # holgura de ajuste por lado entre piezas impresas y piezas compradas (FDM 0.4 mm) [H]
SEG = 48

# ---------------------------------------------------------------- primitivas
def box(w, d, h, x=0.0, y=0.0, z=0.0):
    """Prisma con la base en z y centrado en (x, y)."""
    return M.cube([w, d, h]).translate([x - w / 2, y - d / 2, z])

def cyl(r, h, x=0.0, y=0.0, z=0.0, seg=SEG):
    return M.cylinder(h, r, r, seg).translate([x, y, z])

def cyl_x(r, l, x0=0.0, y=0.0, z=0.0):
    """Cilindro con eje a lo largo de X, desde x0 hasta x0 + l."""
    return M.cylinder(l, r, r, SEG).rotate([0, 90, 0]).translate([x0, y, z])

def cyl_y(r, l, y0=0.0, x=0.0, z=0.0):
    """Cilindro con eje a lo largo de Y, desde y0 hasta y0 + l."""
    return M.cylinder(l, r, r, SEG).rotate([-90, 0, 0]).translate([x, y0, z])

def bb(x0, x1, y0, y1, z0, z1):
    """Prisma por límites."""
    return M.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])

def rbox(w, d, h, r, x=0.0, y=0.0, z=0.0):
    """Prisma de esquinas redondeadas (casco de 4 cilindros)."""
    r = min(r, w / 2 - 0.01, d / 2 - 0.01)
    pts = [cyl(r, h, x + sx * (w / 2 - r), y + sy * (d / 2 - r), z, 24) for sx in (-1, 1) for sy in (-1, 1)]
    return M.batch_hull(pts)

def tornillo_avellanado(r, r_cab, h, x, y, z=0.0):
    """Barreno pasante con avellanado en la cara superior (cabeza plana)."""
    return cyl(r, h + 2, x, y, z - 1) + M.cylinder(r_cab - r + 0.01, r, r_cab, SEG).translate([x, y, z + h - (r_cab - r)])

# ---------------------------------------------------------------- constantes de componentes comprados
DIN_ANCHO = 35.0          # riel TS35 (EN 60715): ancho 35 mm
DIN_LABIO = 1.0           # espesor de la lámina del riel [CG]; el de 1.5 mm también existe
DIN_PROF = 7.5            # riel TS35x7.5
KF_PASO = 5.08            # bornera KF128-5.08 [E]: paso
KF_ALTO = 11.0            # alto del cuerpo de la bornera [H: medir la pieza]
KF_FONDO = 9.0            # fondo del cuerpo de la bornera [H: medir la pieza]
USBC_RECEP = (8.94, 3.26) # abertura del receptáculo USB-C (especificación USB-C) [CG]
USBC_PLUG = (8.4, 2.6)    # cuerpo metálico del conector USB-C [CG]
CR2032 = (20.0, 3.2)      # diámetro, grueso
CR1220 = (12.5, 2.0)
PLACA_7R = (176.0, 90.0)
AGUJEROS_7R = [(3.5, 38.0), (128.0, 38.0), (61.5, 86.5), (145.2, 86.4)]   # gen/make.py de la placa 7R Tour

# ---------------------------------------------------------------- piezas imprimibles
# Convención: cada pieza se imprime en la orientación indicada, apoyada en z = 0, sin soportes salvo que se diga lo contrario.
def clip_cable(d):
    """Abrazadera omega para cable de d mm, a tornillo (M3). Abierta arriba: el cable entra a presión."""
    ri = d / 2 + 0.15
    ro = ri + 2.2
    ancho = 9.0
    zc = 2.4 + ri - 0.2
    pieza = box(2 * (ro + 9.0), ancho, 2.4) + cyl_y(ro, ancho, -ancho / 2, 0, zc)
    pieza = pieza - cyl_y(ri, ancho + 2, -ancho / 2 - 1, 0, zc) - box(d * 0.78, ancho + 2, ri + ro, 0, 0, zc)
    for sx in (-1, 1):
        pieza = pieza - tornillo_avellanado(1.7, 3.2, 2.4, sx * (ro + 5.0), 0)
    return pieza

def base_brida(ancho_brida=4.8):
    """Base para brida de plástico de hasta 4.8 mm de ancho: túnel de 2.2 mm de alto; 2 tornillos M3 (o cinta de doble cara)."""
    w = ancho_brida + 0.6
    pieza = rbox(24, 24, 2.6, 2.5) + bb(-7, 7, -5, 5, 0, 5.6)
    pieza = pieza - bb(-9, 9, -w / 2, w / 2, 2.6, 4.8)
    for sy in (-1, 1):
        pieza = pieza - tornillo_avellanado(1.7, 3.2, 2.6, 0, sy * 8.2)
    return pieza

def hebilla_velcro(ancho=20.0):
    """Hebilla de paso para cinta de gancho y felpa de 20 mm (la cinta se compra aparte)."""
    return rbox(ancho + 8, 12, 3.0, 2.0) - bb(-(ancho + 0.8) / 2, (ancho + 0.8) / 2, -3.7, -1.1, -1, 4) - bb(-(ancho + 0.8) / 2, (ancho + 0.8) / 2, 1.1, 3.7, -1, 4)

def peine_cables(n=8, paso=6.0, ancho_diente=1.4):
    """Peine organizador de n+1 dientes para conductores de hasta 4 mm; 2 tornillos M3."""
    largo = n * paso + 6.0
    pieza = rbox(largo, 16, 3.0, 2.0)
    for i in range(n + 1):
        pieza = pieza + box(ancho_diente, 10, 11, -n * paso / 2 + i * paso, 3.0, 3.0)
    for sx in (-1, 1):
        pieza = pieza - tornillo_avellanado(1.7, 3.2, 3.0, sx * (largo / 2 - 3.2), -5.5)
    return pieza

def gancho_din(L, z0):
    """Base de ganchos para riel DIN TS35 (EN 60715). Marco de impresión: las funciones de la pieza quedan DEBAJO de z0 (sobre la cama);
    arriba van la plataforma (z0..z0+3) y los ganchos, cuyos dientes entran bajo los labios del riel (labio de 1.0 mm) [H]."""
    gap = DIN_ANCHO + 2 * TOL
    pieza = box(gap + 6.0, L, 3.0, 0, 0, z0)
    for sx in (-1, 1):
        pieza = pieza + box(3.0, L, 5.7, sx * (gap / 2 + 1.5), 0, z0)
        pieza = pieza + box(2.0, L, 1.4, sx * (gap / 2 - 1.0), 0, z0 + 4.3)
    return pieza

def clip_riel_cable(n=3, d=6.0):
    """Sujetacables para riel DIN: n nidos abiertos para cables de d mm. Los nidos se imprimen con la boca sobre la cama."""
    L = 22.0
    ro = d / 2 + 2.15
    zc = ro - 0.3
    pieza = gancho_din(L, 2 * ro - 0.6)
    paso = 2 * ro - 0.8
    for i in range(n):
        x = (i - (n - 1) / 2) * paso
        pieza = pieza + cyl_y(ro, L, -L / 2, x, zc)
        pieza = pieza - cyl_y(d / 2 + 0.15, L + 2, -L / 2 - 1, x, zc) - bb(x - d * 0.35, x + d * 0.35, -L / 2 - 1, L / 2 + 1, -1, zc)
    return pieza

def tope_riel():
    """Tope final de riel DIN: columna de 24 mm y un tornillo M4 vertical (rosca en el plástico) que aprieta sobre el labio del riel."""
    L, h = 12.0, 24.0
    gap = DIN_ANCHO + 2 * TOL
    xt = gap / 2 - 1.2
    pieza = gancho_din(L, h) + bb(xt - 4.0, xt + 4.0, -L / 2, L / 2, 0, h)
    return pieza - cyl(1.65, h + 8.0, xt, 0, -1)

def etiquetero_riel(ancho=30.0, alto=12.0):
    """Portaetiquetas para riel DIN: etiqueta de ancho x alto mm que entra deslizando por el extremo +X. Se imprime de canto."""
    L = 14.0
    z0 = alto + 2.0
    pieza = gancho_din(L, z0) + bb(-(ancho + 5) / 2, (ancho + 5) / 2, L / 2 - 1.0, L / 2 + 3.0, 0, z0 + 3.0)
    pieza = pieza - bb(-ancho / 2 - 0.3, ancho / 2 + 10.0, L / 2 + 0.3, L / 2 + 1.7, 1.0, 1.0 + alto + 0.6)
    pieza = pieza - bb(-(ancho - 3) / 2, (ancho - 3) / 2, L / 2 + 1.7, L / 2 + 4.0, 2.5, 2.5 + alto - 3.0)
    return pieza

def cubierta_bornera(polos=3):
    """Cubierta de protección para bornera KF128-5.08 de N polos; se imprime con el techo en la cama. Ajuste por fricción."""
    w = polos * KF_PASO + 0.4 + 2 * TOL
    d = KF_FONDO + 2 * TOL
    h = KF_ALTO + 1.4
    pared = 1.6
    pieza = rbox(w + 2 * pared, d + 2 * pared, h + pared, 1.2) - bb(-w / 2, w / 2, -d / 2, d / 2, pared, h + pared + 1)
    for i in range(polos):
        x = (i - (polos - 1) / 2) * KF_PASO
        pieza = pieza - cyl(1.9, pared + 2, x, 0, -1)                                    # acceso al tornillo con destornillador
        pieza = pieza - cyl_y(1.6, pared + 2, -(d / 2 + pared) - 1, x, pared + 3.0)      # entrada del conductor
    return pieza

def alivio_usbc(cable=3.6):
    """Alivio de tensión (bota) para un cable USB-C con conector sobremoldeado, impreso acostado."""
    w, e = USBC_PLUG[0] + 1.6, USBC_PLUG[1] + 1.4
    largo = 30.0
    cuerpo = rbox(w + 4.0, largo, e + 4.0, 1.8)
    hueco = bb(-w / 2, w / 2, -largo / 2 - 1, -largo / 2 + 0.45 * largo, 2.0, 2.0 + e)
    return cuerpo - hueco - cyl_y(cable / 2 + 0.2, largo + 2, -largo / 2 - 1, 0, (e + 4.0) / 2)

def tapon_usbc():
    """Tapón antipolvo para el receptáculo USB-C del 7R Tour: el cuerpo entra sin forzar y la cabeza queda por fuera."""
    ancho, grueso = USBC_RECEP[0] - 0.5, USBC_RECEP[1] - 0.5
    return rbox(ancho + 4.0, grueso + 4.0, 1.6, 1.4) + rbox(ancho, grueso, 6.0, 0.8, 0, 0, 1.6)

def portapila(tipo=CR2032):
    """Alojamiento para pila de botón con salida de cable hacia el conector de batería de 2 pines. Sin contactos (los cables se sueldan
    a una pila con lengüetas o se compra el portapila metálico y esta pieza lo aloja). Túnel inferior para una brida."""
    d, g = tipo
    D = d + 2 * 1.2
    piso, tapa = 3.0, 0.8
    alto = piso + g + 0.4 + tapa
    caja = rbox(D + 3.0, D + 3.0, alto, 3.0)
    pieza = caja - cyl(d / 2 + 0.2, g + 0.4 + 0.01, 0, 0, piso) - cyl(d / 2 - 1.5, alto + 2, 0, 0, piso)
    pieza = pieza - bb(-d * 0.35, d * 0.35, -(D + 3) / 2 - 1, 0, piso, piso + g + 0.4)
    pieza = pieza - bb(-2.7, 2.7, 0, (D + 3) / 2 + 1, piso, piso + g + 0.4)
    return pieza - bb(-(D + 4) / 2, (D + 4) / 2, -2.6, 2.6, 0.6, 2.2)

def separador_m3(h=8.0, od=8.0, id_=3.2):
    """Separador M3 de 8 mm con asiento hexagonal para tuerca (5.5 mm entre caras) en la base."""
    return cyl(od / 2, h) - cyl(id_ / 2, h + 2, 0, 0, -1) - M.cylinder(2.6, 3.2, 3.2, 6).translate([0, 0, -0.01])

def bandeja_7r():
    """Bandeja de banco para la placa 7R Tour (176 x 90) vista desde arriba: 4 postes en los agujeros de gen/make.py (y espejado,
    porque KiCad cuenta Y hacia abajo), ranuras de pared para M4 y túneles para bridas. Pruebas de la primera tanda; NO es un gabinete."""
    W, H = PLACA_7R
    m = 14.0
    P = rbox(W + 2 * m, H + 2 * m, 3.0, 5.0, W / 2, H / 2, 0)
    for (hx, hy) in AGUJEROS_7R:
        P = P + cyl(3.4, 8.0, hx, H - hy, 2.5)
    for (hx, hy) in AGUJEROS_7R:
        P = P - cyl(1.35, 12.0, hx, H - hy, 1.0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = W / 2 + sx * (W / 2 + 8.0), H / 2 + sy * (H / 2 + 8.0)
            P = P - bb(cx - 5.2, cx + 5.2, cy - 2.2, cy + 2.2, -1, 5)
    for i in range(4):
        P = P - bb(25.0 + i * 42.0 - 6.0, 25.0 + i * 42.0 + 6.0, H / 2 - 2.6, H / 2 + 2.6, -1, 4)
    return P

def pasacables(d_cable=6.0, d_agujero=12.5):
    """Pasacables flexible (TPU 95A) para agujero de panel de d_agujero mm (PG7 = 12.5) y cable de d_cable mm; garganta de 1.6 mm para el panel."""
    p = cyl(d_agujero / 2 + 2.4, 1.4) + cyl(d_agujero / 2 - 0.1, 4.0) + cyl(d_agujero / 2 + 0.5, 1.0, 0, 0, 3.0)
    p = p - cyl(d_cable / 2 - 0.4, 8.0, 0, 0, -1)
    return p - bb(-0.4, 0.4, 0, d_agujero / 2 + 4.0, -1, 6)

def soporte_sensor(d=12.0):
    """Escuadra para sensor cilíndrico roscado M12 (M8: d = 8): agujero pasante en la pared y 2 tornillos M4 a la máquina."""
    t = 4.0
    L = bb(-15, 15, -11, 11, 0, t) + bb(-15, 15, -11, -11 + t, 0, 26)
    L = L - cyl_y(d / 2 + 0.25, t + 2, -12, 0, 15.0)
    for sx in (-1, 1):
        L = L - tornillo_avellanado(2.15, 4.0, t, sx * 10.0, 4.0)
    return L

def bandeja_rack():
    """Bandeja para los módulos AP Rack (176 x 100 mm): 4 postes M3 en los agujeros de la placa (esquinas a 3.5 mm del borde, Y espejado) y
    2 pares de ranuras de 4.4 mm para atornillar dos clips de riel DIN por detrás (separados 100 mm). Pruebas de banco y riel; NO es un gabinete."""
    W, H = 176.0, 100.0
    m = 8.0
    P = rbox(W + 2 * m, H + 2 * m, 3.0, 5.0, W / 2, H / 2, 0)
    pts = [(3.5, 3.5), (172.5, 3.5), (3.5, 96.5), (172.5, 96.5)]
    for (hx, hy) in pts:
        P = P + cyl(3.4, 8.0, hx, hy, 2.5)
    for (hx, hy) in pts:
        P = P - cyl(1.35, 12.0, hx, hy, 1.0)
    for y in (H / 2 - 50.0, H / 2 + 50.0):
        for x in (W / 2 - 25.0, W / 2 + 25.0):
            P = P - cyl(1.7, 6.0, x, y, -1)
    return P

# ---- gabinete de los módulos AP Rack (176 x 100 mm): caja, tapa y unión entre dos cajas
CAJA_PARED = 2.4
CAJA_HOLG = 0.8                      # holgura alrededor de la placa por lado [H]
CAJA_POSTE = 6.0                     # altura de los postes bajo la placa
CAJA_ALTO_INT = 30.0                 # espacio sobre la placa: bornas KF128 (≈11 mm), relé G2RL (≈16 mm) [H: medir con las piezas]
def _caja_dims():
    W, H = 176.0, 100.0
    return W, H, W + 2 * (CAJA_HOLG + CAJA_PARED), H + 2 * (CAJA_HOLG + CAJA_PARED)

def _tornillos_tapa():
    W, H, _, _ = _caja_dims()
    # bosses en el interior de las paredes largas, lejos de las esquinas y de los postes de la placa
    return [(W * f, y) for f in (0.33, 0.67) for y in (-0.3, H + 0.3)]

def caja_rack():
    """Caja de impresión para un módulo AP Rack (176 x 100 mm): placa sobre 4 postes M3 (agujeros reales), paredes de 2.4 mm, 4 bosses para atornillar la tapa
    (tornillo autorroscante M3 en agujero de 2.6 mm), ranuras de 4.4 mm para clips de riel DIN por detrás y ventanas en las dos paredes largas para las bornas de
    salida y las bornas de entrada, el USB-C y los dos conectores AP LINK. Las ventanas son aproximadas: comprobar con la placa real."""
    W, H, OW, OH = _caja_dims()
    ext = CAJA_HOLG + CAJA_PARED
    alto = 3.0 + CAJA_POSTE + 1.6 + CAJA_ALTO_INT
    cuerpo = rbox(OW, OH, alto, 4.0, W / 2, H / 2, 0)
    hueco = rbox(OW - 2 * CAJA_PARED, OH - 2 * CAJA_PARED, alto, 2.5, W / 2, H / 2, 3.0)
    P = cuerpo - hueco
    for (hx, hy) in [(3.5, 3.5), (172.5, 3.5), (3.5, 96.5), (172.5, 96.5)]:
        P = P + cyl(3.4, CAJA_POSTE + 0.5, hx, hy, 2.5)
        P = P - cyl(1.35, 12.0, hx, hy, 1.0)
    for (bx, by) in _tornillos_tapa():
        P = P + cyl(2.9, alto - 3.0 - 3.0, bx, by, 2.5)                      # boss en la pared (entra 2.6 mm sobre el borde de la placa); llega 3 mm por debajo del borde
        P = P - cyl(1.3, 12.0, bx, by, alto - 13.0)
    z0 = 3.0 + CAJA_POSTE + 1.6                                             # cara superior de la placa
    # paredes largas: y = -ext (inferior) y y = H + ext (superior)
    for yc in (-ext + CAJA_PARED / 2, H + ext - CAJA_PARED / 2):
        P = P - bb(28.0, 172.0, yc - CAJA_PARED, yc + CAJA_PARED, z0, z0 + 14.0)    # bornas de salida (ventana continua)
    P = P - bb(2.0, 57.0, H + ext - CAJA_PARED - 1, H + ext + 1, z0, z0 + 14.0)      # bornas de entrada del otro lado
    P = P - bb(58.0, 112.0, -ext - 1, -ext + CAJA_PARED + 1, z0 - 1.0, z0 + 9.0)     # AP LINK y USB-C
    for y in (H / 2 - 50.0, H / 2 + 50.0):
        for x in (W / 2 - 25.0, W / 2 + 25.0):
            P = P - cyl(1.7, 6.0, x, y, -1)
    return P

def tapa_caja_rack():
    """Tapa de la caja del módulo AP Rack: 4 agujeros avellanados M3 sobre los bosses y una ventana de 46 x 7 mm para los LED del panel (RUN, FALLA, COM, CABEZA)."""
    W, H, OW, OH = _caja_dims()
    t = 2.4
    P = rbox(OW, OH, t, 4.0, W / 2, H / 2, 0)
    for (bx, by) in _tornillos_tapa():
        P = P - tornillo_avellanado(1.7, 3.2, t, bx, by)
    P = P - bb(124.0, 170.0, 80.0, 87.0, -1, t + 1)
    return P

def union_cajas_rack():
    """Puente de 2 piezas de ancho para unir dos cajas AP Rack lado a lado (las paredes cortas quedan a 12 mm) con un canal de 10 x 5 mm para el cable AP LINK
    entre el conector SIGUE de una y el ENTRA de la siguiente. Se atornilla con 4 tornillos M3 a las paredes (tuercas en las ranuras)."""
    P = rbox(40.0, 28.0, 3.0, 3.0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            P = P - cyl(1.7, 6.0, sx * 14.0, sy * 9.0, -1)
    P = P - bb(-5.0, 5.0, -14.0, 14.0, 1.5, 3.1)                      # canal de 1.5 mm de fondo para el cable
    return P

def clip_din_atornillable():
    """Clip de riel DIN TS35 que se atornilla (2 x M3) a una bandeja; se imprime plano con los ganchos hacia arriba."""
    L = 20.0
    pieza = gancho_din(L, 0.0)
    for sx in (-1, 1):
        pieza = pieza - cyl(1.7, 8.0, sx * 25.0, 0, -1)
    return pieza

def riel_demo(longitud=60.0):
    """Tramo de riel TS35x7.5 de pruebas de ajuste, impreso al revés (labios sobre la cama). NO soporta carga."""
    y0, y1 = -longitud / 2, longitud / 2
    pieza = bb(-17.5, 17.5, y0, y1, 0, 1.0)                                        # labios (el riel real los tiene arriba)
    pieza = pieza + bb(-13.5, -12.5, y0, y1, 0, DIN_PROF) + bb(12.5, 13.5, y0, y1, 0, DIN_PROF)
    pieza = pieza + bb(-13.5, 13.5, y0, y1, DIN_PROF - DIN_LABIO, DIN_PROF)         # alma
    return pieza - bb(-12.5, 12.5, y0 - 1, y1 + 1, -1, 1.01)

def placa_pulsadores(n=1):
    """Tapa de pared para chalupa sencilla (caja de 2 x 4 pulgadas; tornillos a 82.55 mm [CG]) con n = 1, 2 o 3 pulsadores
    de 16 mm y una ventana de luz de 3 mm junto a cada uno. Para los pulsadores de AP Home (entradas remotas de bajo voltaje)."""
    W, H, t = 70.0, 115.0, 3.0
    pieza = rbox(W, H, t, 4.0)
    for sy in (-1, 1):
        pieza = pieza - tornillo_avellanado(1.9, 3.6, t, 0, sy * 41.275)
    paso = 30.0
    for i in range(n):
        y = (i - (n - 1) / 2) * paso
        pieza = pieza - cyl(8.15, t + 2, 0, y, -1) - cyl(1.6, t + 2, 0, y + 12.0, -1)
    return pieza

def caja_registro_home(ancho=60.0, alto=85.0):
    """Soporte para fijar la placa AP Home (55 x 80 mm, 2 agujeros M3) dentro de una caja de registro: base con 2 postes en los
    agujeros reales de la placa (gen/make.py de home: (51.5, 3.5) y (3.6, 76.2), Y espejado) y 4 orejas de tornillo."""
    P = rbox(alto + 10, ancho + 10, 2.4, 3.0, alto / 2, ancho / 2, 0)
    for (hx, hy) in ((51.5, 3.5), (3.6, 76.2)):
        P = P + cyl(3.4, 6.0, hx + 2.5, hy + 2.5, 2.0)
    for (hx, hy) in ((51.5, 3.5), (3.6, 76.2)):
        P = P - cyl(1.35, 10.0, hx + 2.5, hy + 2.5, 1.0)
    for sx in (-1, 1):
        P = P - tornillo_avellanado(2.15, 4.0, 2.4, alto / 2 + sx * (alto / 2 + 1.0), ancho / 2 + sx * 0)
    return P

# ---------------------------------------------------------------- modelos de referencia (no imprimibles): cables y conectores
def ref_cable_usbc(largo=120.0):
    return {"cable": cyl_y(1.8, largo, 0.0, 0, USBC_PLUG[1] / 2),
            "conector": bb(-USBC_PLUG[0] / 2, USBC_PLUG[0] / 2, -18.0, 0, 0, USBC_PLUG[1]),
            "bota": rbox(USBC_PLUG[0] + 3.0, 22.0, USBC_PLUG[1] + 3.0, 1.4, 0, 7.0, -1.5)}

def ref_cable_sensor_m8(largo=150.0):
    return {"cable": cyl_y(2.0, largo + 9.0, -9.0, 0, 5.0),
            "conector": cyl_y(5.0, 9.0, -18.0, 0, 5.0) + cyl_y(4.2, 14.0, -32.0, 0, 5.0)}

def ref_cable_24v(largo=100.0):
    return {"rojo": cyl_y(1.6, largo, 0, -2.0, 1.6), "negro": cyl_y(1.6, largo, 0, 2.0, 1.6),
            "punteras": cyl_y(1.2, 8.0, -8.0, -2.0, 1.6) + cyl_y(1.2, 8.0, -8.0, 2.0, 1.6)}

def ref_cable_aplink(largo=200.0):
    """Cable AP LINK de 4 hilos con conector JST XH en cada extremo (modelo visual, 1 a 1)."""
    z = 3.0
    hilos = sum((cyl_y(0.6, largo, 0, x, z) for x in (-3.75, -1.25, 1.25, 3.75)), M())
    forro = rbox(12.0, largo * 0.9, 5.0, 1.5, 0, largo / 2, z - 2.5)
    c1 = bb(-5.5, 5.5, -12.0, 0, 0, 7.0)
    c2 = bb(-5.5, 5.5, largo, largo + 12.0, 0, 7.0)
    return {"hilos": hilos, "forro": forro, "conector_entra": c1, "conector_sigue": c2}

def ref_borne_enchufable(polos=3):
    cuerpo = rbox(polos * KF_PASO, KF_FONDO, KF_ALTO, 0.8)
    for i in range(polos):
        cuerpo = cuerpo - box(2.6, 2.6, 3.0, (i - (polos - 1) / 2) * KF_PASO, KF_FONDO / 2 - 0.5, 2.0)
    return {"cuerpo": cuerpo, "tornillos": sum((cyl(1.6, 1.0, (i - (polos - 1) / 2) * KF_PASO, 0, KF_ALTO) for i in range(polos)), M())}

def ref_bateria_cr2032():
    return {"pila": cyl(CR2032[0] / 2, CR2032[1])}

# ---------------------------------------------------------------- catálogo
IMPRIMIBLES = [
    # id, nombre, función, constructor, material sugerido, notas
    ("AP-ACC-001", "clip_cable_4mm", "Abrazadera omega a tornillo para cable de 4 mm", lambda: clip_cable(4.0), "PETG o ABS", "M3 avellanada"),
    ("AP-ACC-002", "clip_cable_6mm", "Abrazadera omega a tornillo para cable de 6 mm", lambda: clip_cable(6.0), "PETG o ABS", "M3 avellanada"),
    ("AP-ACC-003", "clip_cable_8mm", "Abrazadera omega a tornillo para cable de 8 mm", lambda: clip_cable(8.0), "PETG o ABS", "M3 avellanada"),
    ("AP-ACC-004", "base_brida", "Base para brida de plástico de hasta 4.8 mm de ancho", base_brida, "PETG o ABS", "2 tornillos M3 o cinta de doble cara"),
    ("AP-ACC-005", "hebilla_velcro_20", "Hebilla de paso para cinta de gancho y felpa de 20 mm", hebilla_velcro, "PETG", "reusable"),
    ("AP-ACC-006", "peine_cables_8", "Peine organizador de 8 conductores de hasta 4 mm", peine_cables, "PETG o ABS", "2 tornillos M3"),
    ("AP-ACC-007", "clip_riel_3cables", "Sujetacables de riel DIN TS35 para 3 cables de 6 mm", clip_riel_cable, "PETG o ABS", "encaja a presión; verificar el diente con el riel real"),
    ("AP-ACC-008", "tope_riel_din", "Tope final de riel DIN TS35 con tornillo M4", tope_riel, "PETG o ABS", "el tornillo M4 aprieta contra el riel"),
    ("AP-ACC-009", "etiquetero_riel", "Portaetiquetas de riel DIN (etiqueta de 30 x 12 mm)", etiquetero_riel, "PETG", "etiqueta de papel o PET en la ranura"),
    ("AP-ACC-010", "cubierta_bornera_2p", "Cubierta para bornera KF128-5.08 de 2 polos", lambda: cubierta_bornera(2), "PETG o ABS", "medidas de la bornera por confirmar con la pieza"),
    ("AP-ACC-011", "cubierta_bornera_3p", "Cubierta para bornera KF128-5.08 de 3 polos", lambda: cubierta_bornera(3), "PETG o ABS", "medidas de la bornera por confirmar con la pieza"),
    ("AP-ACC-012", "alivio_usbc", "Alivio de tensión (bota) para cable USB-C", alivio_usbc, "TPU 95A o PETG", "se pega al conector con adhesivo flexible"),
    ("AP-ACC-013", "tapon_usbc", "Tapón antipolvo para el receptáculo USB-C", tapon_usbc, "TPU 95A", "ajuste por fricción"),
    ("AP-ACC-014", "portapila_cr2032", "Portapila CR2032 con canal para el cable del conector de batería", portapila, "PETG", "se sujeta con brida; no es un portapila con contactos"),
    ("AP-ACC-015", "portapila_cr1220", "Portapila CR1220 con canal para el cable del conector de batería", lambda: portapila(CR1220), "PETG", "se sujeta con brida"),
    ("AP-ACC-016", "separador_m3_8mm", "Separador M3 de 8 mm con asiento hexagonal", separador_m3, "PETG o ABS", "para pruebas de banco"),
    ("AP-ACC-017", "bandeja_7r_banco", "Bandeja de banco para la placa 7R Tour con 4 postes M3", bandeja_7r, "PETG o ABS", "los 4 postes están en los agujeros reales de la placa; no es un gabinete"),
    ("AP-ACC-018", "pasacables_pg7", "Pasacables flexible para agujero de 12.5 mm y cable de 6 mm", pasacables, "TPU 95A", "con rendija para meter el cable"),
    ("AP-ACC-019", "soporte_sensor_m12", "Escuadra para sensor cilíndrico M12", soporte_sensor, "PETG o ABS", "para M8 usar d = 8"),
    ("AP-ACC-021", "placa_pulsadores_1", "Tapa de pared de chalupa con 1 pulsador de 16 mm y ventana de luz", lambda: placa_pulsadores(1), "PETG o ABS", "chalupa de 2 x 4 pulgadas; tornillos a 82.55 mm por confirmar"),
    ("AP-ACC-022", "placa_pulsadores_2", "Tapa de pared de chalupa con 2 pulsadores", lambda: placa_pulsadores(2), "PETG o ABS", "para Home Switch de varios circuitos (un módulo por pulsador)"),
    ("AP-ACC-023", "placa_pulsadores_3", "Tapa de pared de chalupa con 3 pulsadores", lambda: placa_pulsadores(3), "PETG o ABS", "idem"),
    ("AP-ACC-024", "soporte_home_registro", "Base para fijar la placa AP Home dentro de una caja de registro", caja_registro_home, "PETG o ABS", "postes en los agujeros de la placa; no sustituye la caja ni la tapa certificadas"),
    ("AP-ACC-025", "bandeja_rack", "Bandeja para un módulo AP Rack (176 x 100) con 4 postes M3 y ranuras para clips DIN", bandeja_rack, "PETG o ABS", "los postes están en los agujeros de la placa; no es un gabinete"),
    ("AP-ACC-026", "clip_din_atornillable", "Clip de riel DIN TS35 atornillable (2 x M3)", clip_din_atornillable, "PETG o ABS", "encaje por probar con el riel real"),
    ("AP-ACC-027", "caja_rack", "Caja para un módulo AP Rack (176 x 100) con postes M3, bosses de tapa y ventanas de bornas, USB-C y AP LINK", caja_rack, "PETG o ABS", "ventanas aproximadas; comprobar con la placa; no es un gabinete certificado"),
    ("AP-ACC-028", "tapa_caja_rack", "Tapa de la caja AP Rack con 4 tornillos M3 y ventana de los LED del panel", tapa_caja_rack, "PETG o ABS", "se imprime plana"),
    ("AP-ACC-029", "union_cajas_rack", "Puente para unir dos cajas AP Rack con canal para el cable AP LINK", union_cajas_rack, "PETG o ABS", "4 tornillos M3; posiciones por confirmar al montar las cajas"),
    ("AP-ACC-020", "riel_demo_60", "Tramo de riel DIN TS35 de 60 mm para pruebas de ajuste", riel_demo, "PLA o PETG", "no soporta carga: solo para probar el ajuste"),
]
REFERENCIAS = [
    ("AP-REF-001", "ref_cable_usbc", "Cable USB-C con conector y bota (modelo visual)", ref_cable_usbc),
    ("AP-REF-002", "ref_cable_sensor_m8", "Cable de sensor con conector M8 de 3 hilos (modelo visual)", ref_cable_sensor_m8),
    ("AP-REF-003", "ref_cable_24v", "Cable de alimentación de 24 V con punteras (modelo visual)", ref_cable_24v),
    ("AP-REF-007", "ref_cable_aplink", "Cable AP LINK de 4 hilos con conectores JST XH (modelo visual)", ref_cable_aplink),
    ("AP-REF-004", "ref_borne_3p", "Borne enchufable de 3 polos, paso 5.08 (modelo visual)", lambda: ref_borne_enchufable(3)),
    ("AP-REF-005", "ref_borne_2p", "Borne enchufable de 2 polos, paso 5.08 (modelo visual)", lambda: ref_borne_enchufable(2)),
    ("AP-REF-006", "ref_pila_cr2032", "Pila CR2032 (modelo visual)", ref_bateria_cr2032),
]
IMPRIMIBLES.sort(key=lambda x: x[0])
REFERENCIAS.sort(key=lambda x: x[0])
COLORES = [(232, 93, 4), (60, 60, 64), (200, 200, 205), (40, 120, 200), (30, 160, 80), (180, 40, 40)]


def a_trimesh(m):
    mm = m.to_mesh()
    return trimesh.Trimesh(vertices=np.array(mm.vert_properties)[:, :3], faces=np.array(mm.tri_verts), process=True)


def generar(destino=HERE):
    os.makedirs(os.path.join(destino, "stl"), exist_ok=True)
    os.makedirs(os.path.join(destino, "ref"), exist_ok=True)
    catalogo = {"version": 1, "estado": "PROTOTIPO DE DISEÑO: nada impreso ni probado con las piezas reales", "unidades": "mm",
                "holgura_por_lado_mm": TOL, "imprimibles": [], "referencias": []}
    for sku, nombre, funcion, f, material, nota in IMPRIMIBLES:
        m = f()
        if m.is_empty():
            raise SystemExit("pieza vacía: %s" % nombre)
        t = a_trimesh(m)
        t.export(os.path.join(destino, "stl", nombre + ".stl"))
        ext = [round(float(v), 2) for v in t.bounding_box.extents]
        catalogo["imprimibles"].append({"sku": sku, "archivo": "stl/%s.stl" % nombre, "nombre": nombre, "funcion": funcion, "material": material,
                                        "nota": nota, "dimensiones_mm": ext, "volumen_cm3": round(float(t.volume) / 1000.0, 2),
                                        "solido_valido": bool(t.is_watertight and t.volume > 0)})
    for sku, nombre, funcion, f in REFERENCIAS:
        partes = f()
        escena = trimesh.Scene()
        for k, (pn, pm) in enumerate(partes.items()):
            t = a_trimesh(pm)
            t.visual = trimesh.visual.ColorVisuals(t, vertex_colors=np.tile(list(COLORES[k % len(COLORES)]) + [255], (len(t.vertices), 1)).astype(np.uint8))
            escena.add_geometry(t, node_name=pn)
        escena.export(os.path.join(destino, "ref", nombre + ".glb"))
        trimesh.util.concatenate([a_trimesh(pm) for pm in partes.values()]).export(os.path.join(destino, "ref", nombre + ".stl"))
        catalogo["referencias"].append({"sku": sku, "archivo": "ref/%s.glb" % nombre, "nombre": nombre, "funcion": funcion, "imprimible": False})
    with open(os.path.join(destino, "catalogo.json"), "w", encoding="utf-8") as fh:
        json.dump(catalogo, fh, ensure_ascii=False, indent=1)
    return catalogo


if __name__ == "__main__":
    c = generar()
    for p in c["imprimibles"]:
        print("%-12s %-26s %s mm  %6.2f cm3  %s" % (p["sku"], p["nombre"], p["dimensiones_mm"], p["volumen_cm3"], "ok" if p["solido_valido"] else "NO VÁLIDO"))
    print(len(c["imprimibles"]), "piezas imprimibles y", len(c["referencias"]), "modelos de referencia")
