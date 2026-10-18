#!/usr/bin/env python3
"""Diseño generativo HÍBRIDO de piezas AP Electric: partes paramétricas (ganchos de riel DIN, bosses de tornillo) unidas a formas generadas por algoritmo.

  ménsula en A  : optimización topológica 2D (SIMP, topologia.py) de la ménsula que cuelga el módulo AP Rack del riel DIN, extruida y unida al gancho paramétrico
  tapa ventilada: ventanas de una tapa AP Rack generadas por un mapa de calor (Voronoi relajado): más y más grandes donde están las piezas que calientan

    python3 generativo/generar.py            (desde hardware/ap-electric)   ->   generativo/salida/*.stl, *.glb, informe.json y vistas

Las cargas, el material y el mapa de calor son SUPUESTOS DE DISEÑO [H] (módulo de 0.3 kg, PETG impreso con E ≈ 1500 MPa): no hay análisis 3D por elementos finitos,
simulación térmica ni ensayo de ninguna pieza impresa. Sirve para proponer la forma; hay que validarla antes de usarla.
"""
import json, math, os, sys
import numpy as np
import trimesh
from manifold3d import Manifold as M, Mesh as MMesh
from shapely.geometry import Polygon, Point, MultiPolygon, box as sbox
from shapely.ops import unary_union
from skimage import measure
from scipy.ndimage import zoom, gaussian_filter
from scipy.spatial import Voronoi

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI); sys.path.insert(0, os.path.join(AQUI, "..", "accesorios"))
import topologia  # noqa: E402
import accesorios as A  # noqa: E402

SALIDA = os.path.join(AQUI, "salida")
os.makedirs(SALIDA, exist_ok=True)


def a_manifold(t):
    return M(MMesh(vert_properties=np.array(t.vertices, dtype=np.float32), tri_verts=np.array(t.faces, dtype=np.uint32)))


def poligonos_de_densidad(rho, mm_por_elem, x0_mm, z_top_mm, umbral=0.5, ampliar=4):
    """Contornos de la densidad (ny, nx) a polígonos shapely en mm: x hacia la derecha, z hacia arriba (la fila 0 está arriba)."""
    ny, nx = rho.shape
    r = gaussian_filter(zoom(rho, ampliar, order=1), 1.2)
    r = np.pad(r, 2, constant_values=0.0)
    cs = measure.find_contours(r, umbral)
    paso = mm_por_elem / ampliar
    polys = []
    for c in cs:
        if len(c) < 8: continue
        pts = [(x0_mm + (cj - 2 + 0.5) * paso, z_top_mm - (ci - 2 + 0.5) * paso) for ci, cj in c]
        p = Polygon(pts)
        if p.is_valid and p.area > 0.5: polys.append(p)
        elif p.buffer(0).area > 0.5: polys.append(p.buffer(0))
    polys.sort(key=lambda p: -p.area)
    sol = None                                                       # par/impar: los contornos interiores son huecos
    for p in polys:
        sol = p if sol is None else sol.symmetric_difference(p)
    return sol


def ménsula():
    mm = 0.5                                         # tamaño de elemento
    ancho, alto, espesor = 60.0, 30.0, 8.0           # dominio x z (mm) y espesor de la ménsula (eje y)
    nx, ny = int(ancho / mm), int(alto / mm)
    F_total = 30.0                                   # N: módulo de 0.3 kg con un factor 10 de vibración [H]
    bosses = [(-24.0, 25.0), (24.0, 25.0)]           # centros de los tornillos del módulo (x, z desde la base de la ménsula) [H]
    r_boss, r_tornillo = 5.5, 1.7
    solido = np.zeros((ny, nx), bool); vacio = np.zeros((ny, nx), bool)
    xs = (np.arange(nx) + 0.5) * mm - ancho / 2; zs = alto - (np.arange(ny) + 0.5) * mm
    X, Z = np.meshgrid(xs, zs)
    for bx, bz in bosses:
        d = np.hypot(X - bx, Z - bz)
        solido |= d < r_boss; vacio |= d < r_tornillo
    solido &= ~vacio
    solido[:, : int(1.5 / mm)] |= False
    fijos = [(ix, ny, "xy") for ix in range(int((ancho / 2 - 20) / mm), int((ancho / 2 + 20) / mm) + 1)]   # base apoyada sobre los 40 mm centrales del gancho
    cargas = []
    for bx, bz in bosses:                           # la carga del tornillo se reparte en 8 nodos del anillo sólido (radio 2.8 mm), nunca en el hueco
        for ang in np.arange(8) * math.pi / 4:
            ix = int(round((bx + ancho / 2 + 2.8 * math.cos(ang)) / mm)); iy = int(round((alto - bz - 2.8 * math.sin(ang)) / mm))
            cargas.append((ix, iy, 0.0, -F_total / 2 / 8))
    rho, hist, umax = topologia.optimizar(nx, ny, 0.38, 3.0, fijos, cargas, solido=solido, vacio=vacio, iteraciones=110)
    # línea base: la misma placa llena (E completo) y la placa con la misma masa pero densidad uniforme (rigidez ∝ densidad)
    rho1, hist1, umax1 = topologia.optimizar(nx, ny, 1.0, 3.0, fijos, cargas, solido=None, vacio=vacio, iteraciones=1)
    c_opt, c_lleno = hist[-1], hist1[0]
    fraccion = float(rho.mean())
    c_uniforme = c_lleno / fraccion
    E_mpa = 1500.0
    u_mm = umax / (E_mpa * espesor)
    pol = poligonos_de_densidad(rho, mm, -ancho / 2, alto)
    if pol is None or pol.is_empty: raise SystemExit("la optimización no dejó material")
    pol = pol.buffer(-0.35).buffer(0.35).simplify(0.06)                       # sin filos de menos de 0.7 mm
    if isinstance(pol, MultiPolygon):
        pol = max(pol.geoms, key=lambda g: g.area)
    t = trimesh.creation.extrude_polygon(pol, espesor)
    # (x, y_poly, z_ext) -> (x, z_ext - espesor/2, y_poly + z0): la ménsula se apoya en la plataforma del gancho (z = 3)
    T = np.array([[1, 0, 0, 0], [0, 0, 1, -espesor / 2], [0, 1, 0, 3.0], [0, 0, 0, 1]], float)
    t.apply_transform(T)
    gen = a_manifold(t)
    # parte paramétrica: gancho DIN TS35 con su plataforma, y bosses completos alrededor de los tornillos
    gancho = A.gancho_din(30.0, 0.0)
    param = gancho
    for bx, bz in bosses:
        param = param + A.cyl_y(r_boss, espesor + 0.8, -espesor / 2 - 0.4, bx, bz + 3.0)      # arandela de 0.4 mm a cada lado: apoyo plano para el tornillo
    for bx, bz in bosses:
        param = param - A.cyl_y(r_tornillo, espesor + 2, -espesor / 2 - 1, bx, bz + 3.0)
    hibrida = gen + param
    for bx, bz in bosses:
        hibrida = hibrida - A.cyl_y(r_tornillo, espesor + 2, -espesor / 2 - 1, bx, bz + 3.0)
    info = {"pieza": "soporte_riel_generativo", "dominio_mm": [ancho, alto, espesor], "elementos": [nx, ny], "carga_N": F_total, "E_MPa_supuesto": E_mpa,
            "fraccion_volumen": round(fraccion, 3), "flexibilidad_optimizada": round(c_opt, 3), "flexibilidad_placa_llena": round(c_lleno, 3),
            "flexibilidad_misma_masa_uniforme": round(c_uniforme, 3), "mejora_rigidez_vs_uniforme": round(c_uniforme / c_opt, 2),
            "desplazamiento_maximo_mm_modelo": round(u_mm, 3), "iteraciones": len(hist)}
    return hibrida, gen, param, rho, info


def tapa_ventilada(semilla=7):
    W, H = 176.0, 100.0
    OW, OH = A._caja_dims()[2:]
    ext = A.CAJA_HOLG + A.CAJA_PARED
    placa = sbox(0, 0, W, H)
    # fuentes de calor en coordenadas de placa (x, y hacia abajo en KiCad): reguladores, inductores, MOSFET de salida
    POS = json.load(open(os.path.join(AQUI, "posiciones_rack16.json")))      # posiciones de las piezas del Rack 16 (de rack16/gen/make.py; se vuelcan con KiCad)
    fuentes = [(POS[r][0], POS[r][1], w) for r, w in (("U1", 1.0), ("L1", 0.9), ("U2", 1.0), ("L2", 0.8), ("D1", 0.7), ("F1", 0.5)) if r in POS]
    fuentes += [(POS["Q%d" % k][0], POS["Q%d" % k][1], 0.45) for k in range(1, 17) if "Q%d" % k in POS]
    fuentes = [(x, H - y, w) for x, y, w in fuentes]                                # a la vista desde arriba: y hacia arriba
    xs, ys = np.meshgrid(np.linspace(0, W, 177), np.linspace(0, H, 101))
    calor = np.zeros_like(xs)
    for fx, fy, w in fuentes:
        calor += w * np.exp(-((xs - fx) ** 2 + (ys - fy) ** 2) / (2 * 11.0 ** 2))
    calor /= calor.max()
    rng = np.random.default_rng(semilla)
    # semillas con probabilidad proporcional al calor + una base mínima; descartes de zonas prohibidas
    prohibido = unary_union([Point(hx, hy).buffer(7.0) for hx, hy in ((3.5, 3.5), (172.5, 3.5), (3.5, 96.5), (172.5, 96.5))] +
                            [Point(bx, by).buffer(6.0) for bx, by in [(p[0] - ext - A.CAJA_HOLG, p[1]) for p in A._tornillos_tapa()]] +
                            [sbox(124, 80, 170, 87).buffer(4.0)])
    pts = []
    while len(pts) < 70:
        x, y = rng.uniform(4, W - 4), rng.uniform(4, H - 4)
        p = 0.10 + 0.9 * calor[int(y), int(x)]
        if rng.uniform() < p and not prohibido.contains(Point(x, y)): pts.append((x, y))
    pts = np.array(pts)
    for _ in range(4):                                              # relajación de Lloyd (celdas más regulares)
        far = np.array([[-500, -500], [-500, 600], [700, -500], [700, 600]])
        vor = Voronoi(np.vstack([pts, far]))
        nuevos = []
        for i in range(len(pts)):
            reg = vor.regions[vor.point_region[i]]
            if -1 in reg or not reg: nuevos.append(pts[i]); continue
            c = Polygon(vor.vertices[reg]).intersection(placa.buffer(-3)).centroid
            nuevos.append((c.x, c.y) if not c.is_empty else pts[i])
        pts = np.array(nuevos)
    vor = Voronoi(np.vstack([pts, far]))
    huecos = []
    pared = 1.8                                                      # nervio mínimo entre ventanas
    for i in range(len(pts)):
        reg = vor.regions[vor.point_region[i]]
        if -1 in reg or not reg: continue
        celda = Polygon(vor.vertices[reg]).intersection(placa.buffer(-3.0))
        if celda.is_empty or not isinstance(celda, Polygon): continue
        c = celda.centroid
        q = calor[min(100, int(c.y)), min(176, int(c.x))]
        if q < 0.18 or prohibido.intersects(celda.buffer(-pared / 2)): continue      # solo ventila donde hay calor
        v = celda.buffer(-(pared / 2 + 0.4 * (1 - q) * 3)).buffer(0.6).buffer(-0.6)
        if not v.is_empty and v.area > 14.0 and isinstance(v, Polygon): huecos.append(v)
    t = A.rbox(OW, OH, 2.4, 4.0, W / 2, H / 2, 0)
    for (bx, by) in A._tornillos_tapa():
        t = t - A.tornillo_avellanado(1.7, 3.2, 2.4, bx, by)
    t = t - A.bb(124.0, 170.0, 80.0, 87.0, -1, 3.4)
    for v in huecos:
        mesh = trimesh.creation.extrude_polygon(v, 4.0); mesh.apply_translation([0, 0, -1.0])
        t = t - a_manifold(mesh)
    info = {"pieza": "tapa_ventilada_generativa", "ventanas": len(huecos), "area_ventilada_cm2": round(sum(v.area for v in huecos) / 100, 1),
            "fuentes_de_calor_modeladas": len(fuentes), "semilla": semilla}
    return t, huecos, calor, info


def a_tri(m):
    mm = m.to_mesh()
    return trimesh.Trimesh(vertices=np.array(mm.vert_properties)[:, :3], faces=np.array(mm.tri_verts), process=True)


def guardar(nombre, m, color):
    t = a_tri(m)
    t.export(os.path.join(SALIDA, nombre + ".stl"))
    t.visual = trimesh.visual.ColorVisuals(t, vertex_colors=np.tile(list(color) + [255], (len(t.vertices), 1)).astype(np.uint8))
    return t


if __name__ == "__main__":
    informe = {}
    h, gen, par, rho, info = ménsula()
    t = guardar("soporte_riel_generativo", h, (232, 93, 4))
    info.update({"volumen_cm3": round(float(t.volume) / 1000, 2), "solido_valido": bool(t.is_watertight and t.volume > 0), "dimensiones_mm": [round(float(v), 1) for v in t.bounding_box.extents]})
    volumen_llano = 60.0 * 30.0 * 8.0 / 1000
    info["volumen_placa_llena_cm3"] = volumen_llano
    informe["soporte_riel_generativo"] = info
    # partes por material: generativa (grafito) y paramétrica (naranja) en un GLB
    esc = trimesh.Scene()
    for nombre, m, col in (("generativa", gen, (60, 62, 70)), ("parametrica", par, (232, 93, 4))):
        tt = a_tri(m); tt.export(os.path.join(SALIDA, "soporte_%s.stl" % nombre)); tt.visual = trimesh.visual.ColorVisuals(tt, vertex_colors=np.tile(list(col) + [255], (len(tt.vertices), 1)).astype(np.uint8)); esc.add_geometry(tt, node_name=nombre)
    esc.export(os.path.join(SALIDA, "soporte_riel_generativo.glb"))
    from PIL import Image
    Image.fromarray((255 - np.clip(rho, 0, 1) * 255).astype(np.uint8)).resize((rho.shape[1] * 6, rho.shape[0] * 6), Image.NEAREST).save(os.path.join(SALIDA, "soporte_densidad.png"))
    tv, huecos, calor, info2 = tapa_ventilada()
    t2 = guardar("tapa_ventilada_generativa", tv, (232, 93, 4))
    info2.update({"volumen_cm3": round(float(t2.volume) / 1000, 2), "solido_valido": bool(t2.is_watertight and t2.volume > 0), "dimensiones_mm": [round(float(v), 1) for v in t2.bounding_box.extents]})
    informe["tapa_ventilada_generativa"] = info2
    esc2 = trimesh.Scene(); esc2.add_geometry(t2, node_name="tapa"); esc2.export(os.path.join(SALIDA, "tapa_ventilada_generativa.glb"))
    Image.fromarray((np.clip(calor, 0, 1) * 255).astype(np.uint8)).resize((177 * 4, 101 * 4)).save(os.path.join(SALIDA, "tapa_mapa_calor.png"))
    with open(os.path.join(SALIDA, "informe.json"), "w", encoding="utf-8") as f:
        json.dump(informe, f, ensure_ascii=False, indent=1)
    print(json.dumps(informe, ensure_ascii=False, indent=1))
