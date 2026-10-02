"""Gabinete imprimible (PETG o ASA) para el conjunto LetreroLab AP-1: base de 88 x 56 mm con el programador enclavado.

- Medido contra el modelo 3D real del conjunto (ap1-ensamble/AP1_Ensamble.step). El script falla si una pieza toca
  la caja o le falta holgura a la tapa.
- Placa sobre 3 postes con inserto de latón M3 (los mismos 3 agujeros de la base; el del programador lleva el
  tornillo de nylon que atraviesa las dos placas).
- Frente: 4 prensaestopas PG7 (focos CC, entrada, canales, AUX) con 16 mm de espacio para la tuerca y el doblez del cable.
- Atrás: ventana para el USB-C del programador (programar y actualizar sin abrir).
- Tapa: ventana para el receptor IR, 2 tubos de luz de 3 mm para los LED (FALLA / Wi-Fi), agujeros para BOOT y
  RESET con un clip, y textos grabados. 4 tornillos M3 en columnas por fuera de la placa.
- Sin metal cerca de la antena: la esquina de atrás a la derecha usa tornillo de nylon (marcado en la tapa).

Se ejecuta en el anfitrión:  pip install manifold3d trimesh matplotlib pymupdf cascadio ; python3 ap1-gabinete/gen/caja.py
Salida en ap1-gabinete/gabinete/: caja_base.stl, caja_tapa.stl, vista_caja.png, plantilla_caja_comprada_1a1.pdf
"""
import os
import numpy as np
import manifold3d as m3
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "gabinete")
STEP = os.path.join(HERE, "..", "..", "ap1-ensamble", "AP1_Ensamble.step")

# --- medidas (mm) ---
PW, PH = 88.0, 56.0                      # base
HOLES = [(3.5, 3.5), (84.5, 39.5), (84.5, 52.5)]     # agujeros M3 de la base (84.5, 39.5 = tornillo del programador)
T, TF, TL = 2.5, 2.5, 2.5                # pared, piso, tapa
G, FG = 1.0, 16.0                        # holgura a los lados y atrás; espacio al frente para prensaestopas
STAND = 6.0                              # postes: las patas THT salen 3.4 mm por abajo
ALTO_PIEZAS = 25.0                       # lo más alto del conjunto sobre la cara inferior de la base (receptor IR)
AIRE = 4.0                               # holgura entre lo más alto y la tapa
INS = 4.0                                # barreno para inserto de latón M3 (D 4.2 x 5.7)
OX, OY = T + G, T + FG                   # esquina de la placa (lado de los conectores = frente)
X, Y = OX + PW + G + T, OY + PH + G + T
ZB = TF + STAND                          # cara inferior de la base
Z = ZB + ALTO_PIEZAS + AIRE              # alto de la caja (sin tapa)
GLAND = 12.5                             # PG7 (cable de 3 a 6.5 mm)
GZ = ZB + 1.6 + 7.0                      # altura de los prensaestopas: a la altura de las entradas de las clemas
GLANDS = [("FOCOS CC", 8.0), ("ENTRADA", 30.0), ("CANALES", 52.0), ("AUX", 76.0)]   # x sobre la placa
POST = 9.0                               # columnas de la tapa (por fuera de la placa)
PILLARS = [(-1.0, -1.0), (X + 1.0, -1.0), (-1.0, Y + 1.0), (X + 1.0, Y + 1.0)]   # columnas hacia afuera
SEG = 48

# piezas del programador que se ven o se tocan desde afuera (coordenadas de la base)
USB = (55.5, ZB + 1.6 + 11.0 + 1.6 + 1.6)          # centro del USB-C: x, z (borde de atrás)
IR = (62.5, 37.8)
LEDS = [("FALLA", 70.5, 41.0), ("WI-FI", 74.0, 41.0)]
BOTONES = [("BOOT", 55.5, 17.6), ("RESET", 55.5, 24.4)]


def P(xb, yb):
    """Coordenadas de la placa (KiCad, y hacia el frente) -> caja (y hacia atrás)."""
    return OX + xb, OY + (PH - yb)


def box(x0, y0, z0, x1, y1, z1):
    return m3.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def cyl(x, y, z0, z1, d):
    return m3.Manifold.cylinder(z1 - z0, d / 2, d / 2, SEG).translate([x, y, z0])


def cyl_y(x, z, y0, y1, d):
    return m3.Manifold.cylinder(y1 - y0, d / 2, d / 2, SEG).rotate([-90, 0, 0]).translate([x, y0, z])


def texto(s, x, y, h, z0, z1, centro=True):
    """Texto grabado/en relieve (contornos de matplotlib extruidos)."""
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    tp = TextPath((0, 0), s, size=h, prop=FontProperties(family="DejaVu Sans", weight="bold"))
    polys = [np.asarray(p) for p in tp.to_polygons() if len(p) > 2]
    cs = m3.CrossSection([p[:, :2].tolist() for p in polys], m3.FillRule.EvenOdd)
    b = tp.get_extents()
    dx = x - (b.x0 + b.x1) / 2 if centro else x
    return m3.Manifold.extrude(cs, z1 - z0).translate([dx, y - (b.y0 + b.y1) / 2, z0])


def stadium_y(x, z, w, h, y0, y1):    # ventana redondeada en la pared de atrás
    r = h / 2
    s = box(x - w / 2 + r, y0, z - r, x + w / 2 - r, y1, z + r)
    return s + cyl_y(x - w / 2 + r, z, y0, y1, h) + cyl_y(x + w / 2 - r, z, y0, y1, h)


def base():
    b = box(0, 0, 0, X, Y, Z) - box(T, T, TF, X - T, Y - T, Z + 1)
    for px, py in PILLARS:                                       # columnas de la tapa, por fuera
        b += cyl(px, py, 0, Z, POST)
        b -= cyl(px, py, Z - 8, Z + 1, INS)
    b -= box(T, T, TF, X - T, Y - T, Z + 1)                      # el interior queda libre
    for hx, hy in HOLES:                                         # postes de la placa
        x, y = P(hx, hy)
        b += cyl(x, y, 0, ZB, 7.0)
        b -= cyl(x, y, ZB - 6, ZB + 1, INS)
    for _, gx in GLANDS:                                         # prensaestopas al frente
        b -= cyl_y(OX + gx, GZ, -1, T + 1, GLAND)
    b -= stadium_y(OX + USB[0], USB[1], 13.0, 7.5, Y - T - 1, Y + 1)   # USB-C atrás
    for side in (-1, 1):                                         # orejas para atornillar a la pared
        x0 = -16.0 if side < 0 else X
        ear = box(x0, Y / 2 - 10, 0, x0 + 16, Y / 2 + 10, 3)
        ear -= cyl(x0 + (7 if side < 0 else 9), Y / 2, -1, 4, 4.5)
        b += ear
    return b


def lid():
    lt = box(0, 0, 0, X, Y, TL)
    for px, py in PILLARS:
        lt += cyl(px, py, 0, TL, POST)
    lip = box(T + 0.3, T + 0.3, -2.0, X - T - 0.3, Y - T - 0.3, 0.01) - \
        box(T + 1.8, T + 1.8, -3, X - T - 1.8, Y - T - 1.8, 1)
    lt += lip
    for px, py in PILLARS:
        lt -= cyl(px, py, -3, TL + 1, 3.4)                       # paso M3
        lt -= cyl(px, py, TL - 1.4, TL + 1, 6.4)                 # caja para la cabeza
    x, y = P(*IR)
    lt -= cyl(x, y, -3, TL + 1, 8.0)                             # ventana IR (pegar un disco de acrílico rojo o humo)
    lt -= cyl(x, y, TL - 0.8, TL + 1, 11.0)                      # asiento del disco de 11 mm
    for nombre, lx, ly in LEDS:                                  # tubos de luz de 3 mm
        x, y = P(lx, ly)
        lt -= cyl(x, y, -3, TL + 1, 3.2)
    for nombre, bx, by in BOTONES:                               # con un clip
        x, y = P(bx, by)
        lt -= cyl(x, y, -3, TL + 1, 2.4)
    G_ = 0.6                                                     # profundidad del grabado
    xi, yi = P(*IR)
    grab = texto("IR", xi, yi - 9.0, 3.2, TL - G_, TL + 1)
    xa, ya = P(LEDS[0][1], LEDS[0][2])
    xb_, yb_ = P(LEDS[1][1], LEDS[1][2])
    grab += texto("!", xa, ya - 4.2, 3.0, TL - G_, TL + 1) + texto("W", xb_, yb_ - 4.2, 3.0, TL - G_, TL + 1)
    for nombre, bx, by in BOTONES:
        x, y = P(bx, by)
        grab += texto(nombre, x - 9.0, y, 2.6, TL - G_, TL + 1)
    for nombre, gx in GLANDS:
        grab += texto(nombre, OX + gx, 6.0, 2.8, TL - G_, TL + 1)
    grab += texto("LetreroLab AP-1", 30.0, Y - 14.0, 5.0, TL - G_, TL + 1)
    grab += texto("12-24 V  20 A", 30.0, Y - 21.0, 3.2, TL - G_, TL + 1)
    grab += texto("nylon", X - 6.5, Y - 7.5, 2.2, TL - G_, TL + 1)   # junto a la antena: tornillo de nylon
    return lt - grab


def save(man, name):
    mesh = man.to_mesh()
    tm = trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts))
    tm.export(os.path.join(OUT, name))
    return tm


def conjunto():
    """Modelo real del conjunto (base + programador) colocado dentro de la caja."""
    sc = trimesh.load(STEP)
    tm = sc.to_geometry() if hasattr(sc, "to_geometry") else sc.dump(concatenate=True)
    v = tm.vertices * 1000.0                                     # el STEP viene en metros, y hacia arriba
    tm.vertices = np.c_[OX + v[:, 0], OY + PH + v[:, 1], ZB + v[:, 2]]
    return tm


def revisar(tb, tl, cj):
    """Choques del conjunto con la caja y holgura a la tapa."""
    lo, hi = cj.bounds
    print("conjunto: x %.1f-%.1f  y %.1f-%.1f  z %.1f-%.1f" % (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    assert lo[0] >= T and hi[0] <= X - T and lo[1] >= T and hi[1] <= Y - T, "el conjunto no cabe entre las paredes"
    assert lo[2] >= TF + 0.5, "las patas tocan el piso"
    tapa = Z - 2.0                                               # el labio de la tapa baja 2 mm
    assert hi[2] <= tapa - 1.0, "poca holgura a la tapa: %.1f mm" % (tapa - hi[2])
    pts = cj.vertices[::3]
    dentro = tb.contains(pts)
    print("puntos del conjunto dentro de las paredes o postes: %d de %d" % (dentro.sum(), len(pts)))
    assert dentro.sum() == 0, "choque con la caja"
    print("holgura a la tapa: %.1f mm" % (tapa - hi[2]))


def render(parts, elev, azim, size=(760, 560)):
    """Rasterizador z-buffer simple (sin OpenGL): parts = [(trimesh, (r, g, b))]."""
    e, a = np.radians(elev), np.radians(azim)
    Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, np.cos(e), -np.sin(e)], [0, np.sin(e), np.cos(e)]])
    R = Rx @ Rz
    allv = np.vstack([tm.vertices for tm, _ in parts]) @ R.T
    lo, hi = allv[:, :2].min(0), allv[:, :2].max(0)
    W_, H_ = size
    sc = 0.9 * min(W_ / (hi[0] - lo[0]), H_ / (hi[1] - lo[1]))
    img = np.ones((H_, W_, 3))
    zb = np.full((H_, W_), -1e9)
    L = np.array([0.35, 0.45, 0.82]); L /= np.linalg.norm(L)
    for tm, colr in parts:
        v = tm.vertices @ R.T
        P2 = np.c_[(v[:, 0] - lo[0]) * sc + 0.05 * W_, H_ - ((v[:, 1] - lo[1]) * sc + 0.05 * H_), v[:, 2]]
        for f in tm.faces:
            t = P2[f]
            n = np.cross(v[f[1]] - v[f[0]], v[f[2]] - v[f[0]])
            nn = np.linalg.norm(n)
            if nn < 1e-12:
                continue
            k = 0.3 + 0.7 * abs(n @ L) / nn
            x0, x1 = int(max(t[:, 0].min(), 0)), int(min(t[:, 0].max() + 1, W_))
            y0, y1 = int(max(t[:, 1].min(), 0)), int(min(t[:, 1].max() + 1, H_))
            if x1 <= x0 or y1 <= y0:
                continue
            xs, ys = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
            (ax_, ay), (bx, by), (cx, cy) = t[0, :2], t[1, :2], t[2, :2]
            d = (by - cy) * (ax_ - cx) + (cx - bx) * (ay - cy)
            if abs(d) < 1e-12:
                continue
            w0 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / d
            w1 = ((cy - ay) * (xs - cx) + (ax_ - cx) * (ys - cy)) / d
            w2 = 1 - w0 - w1
            inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            z = w0 * t[0, 2] + w1 * t[1, 2] + w2 * t[2, 2]
            sub = zb[y0:y1, x0:x1]
            upd = inside & (z > sub)
            sub[upd] = z[upd]
            img[y0:y1, x0:x1][upd] = np.array(colr) * k
    return img


def preview(tb, tl, cj):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    cjs = cj.simplify_quadric_decimation(face_count=60000) if len(cj.faces) > 60000 else cj
    tl_arriba = tl.copy()
    tl_arriba.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0], [X / 2, Y / 2, 0]))
    tl_arriba.apply_translation((0, 0, Z + TL + 30))
    tl_cerrada = tl.copy()
    tl_cerrada.apply_translation((0, 0, Z))
    imgs = [render([(tb, (0.62, 0.66, 0.72)), (cjs, (0.25, 0.45, 0.30))], -58, 20),
            render([(tb, (0.62, 0.66, 0.72)), (tl_cerrada, (0.78, 0.80, 0.84))], -55, 200)]
    fig, axs = plt.subplots(1, 2, figsize=(14, 5.6), dpi=110)
    for ax_, im, ttl in zip(axs, imgs, ("Caja abierta con el conjunto real (base + programador): prensaestopas al frente",
                                        "Cerrada, vista desde atrás: USB-C, ventana IR, tubos de luz, BOOT/RESET")):
        ax_.imshow(np.clip(im, 0, 1)); ax_.set_title(ttl, fontsize=10); ax_.axis("off")
    fig.suptitle("Gabinete LetreroLab AP-1: %.0f x %.0f x %.0f mm + tapa %.1f mm  |  4 PG7 + USB-C + IR" % (X, Y, Z, TL))
    fig.savefig(os.path.join(OUT, "vista_caja.png"), bbox_inches="tight")


def plantilla():
    """Plantilla 1:1 para usar una caja comprada (ABS o policarbonato; sin metal: la antena del Wi-Fi va adentro)."""
    import pymupdf as fitz
    MM = 72 / 25.4
    doc = fitz.open()
    pg = doc.new_page(width=210 * MM, height=297 * MM)
    t = ["PLANTILLA 1:1 PARA CAJA COMPRADA (LetreroLab AP-1, base 88 x 56 con programador encima)",
         "Imprimir al 100 %. Verificar con la regla. Pegar con cinta y marcar con punzon. Caja de PLASTICO: el Wi-Fi va adentro.",
         "Fondo: 3 barrenos de 3.2 mm (separadores de nylon M3 de %.0f mm). Frente: 4 barrenos de 12.5 mm (PG7)." % STAND,
         "Caja minima interior: %.0f x %.0f mm y %.0f mm de alto (o cualquiera mas grande)." % (X - 2 * T, Y - 2 * T, Z - TF)]
    y = 14
    for i, s in enumerate(t):
        pg.insert_text((15 * MM, y * MM), s, fontsize=9.5 if i == 0 else 7.5, fontname="hebo" if i == 0 else "helv")
        y += 6 if i == 0 else 4.2
    ox, oy = 30, 45
    pg.draw_rect(fitz.Rect(ox * MM, oy * MM, (ox + PW) * MM, (oy + PH) * MM), width=0.4, dashes="[2 2] 0")
    pg.insert_text(((ox + 2) * MM, (oy + PH / 2) * MM), "contorno de la base (vista desde arriba)", fontsize=6)
    pg.insert_text(((ox + 12) * MM, (oy + PH - 3) * MM), "FRENTE (clemas)", fontsize=6)
    for hx, hy in HOLES:
        cx, cy = (ox + hx) * MM, (oy + hy) * MM
        pg.draw_circle((cx, cy), 1.6 * MM, width=0.4)
        pg.draw_line((cx - 3 * MM, cy), (cx + 3 * MM, cy), width=0.2)
        pg.draw_line((cx, cy - 3 * MM), (cx, cy + 3 * MM), width=0.2)
    for nombre, (lx, ly) in (("IR (8 mm)", IR),):
        cx, cy = (ox + lx) * MM, (oy + ly) * MM
        pg.draw_circle((cx, cy), 4.0 * MM, width=0.3, dashes="[1 1] 0")
        pg.insert_text((cx + 5 * MM, cy), "tapa: " + nombre, fontsize=6)
    fx, fz = 30, 150
    pg.insert_text((fx * MM, (fz - 4) * MM), "FRENTE de la caja (visto desde afuera); la linea de abajo = fondo interior",
                   fontsize=8, fontname="hebo")
    pg.draw_line((fx * MM, (fz + 30) * MM), ((fx + PW) * MM, (fz + 30) * MM), width=0.6)
    for name, gx in GLANDS:
        cx, cz = (fx + gx) * MM, (fz + 30 - (GZ - TF)) * MM
        pg.draw_circle((cx, cz), GLAND / 2 * MM, width=0.4)
        pg.draw_line((cx - 2 * MM, cz), (cx + 2 * MM, cz), width=0.2)
        pg.draw_line((cx, cz - 2 * MM), (cx, cz + 2 * MM), width=0.2)
        pg.insert_text((cx - 6 * MM, cz + 10 * MM), name, fontsize=7)
    pg.insert_text((fx * MM, (fz + 36) * MM),
                   "Centro de los prensaestopas a %.1f mm sobre el fondo interior, con separadores de %.0f mm." % (GZ - TF, STAND),
                   fontsize=7)
    bz = 205
    pg.insert_text((fx * MM, (bz - 4) * MM), "ATRAS de la caja (visto desde afuera): ventana del USB-C", fontsize=8, fontname="hebo")
    pg.draw_line((fx * MM, (bz + 30) * MM), ((fx + PW) * MM, (bz + 30) * MM), width=0.6)
    ux, uz = (fx + PW - USB[0]) * MM, (bz + 30 - (USB[1] - TF)) * MM          # visto desde atrás: x invertida
    pg.draw_rect(fitz.Rect(ux - 6.5 * MM, uz - 3.75 * MM, ux + 6.5 * MM, uz + 3.75 * MM), width=0.4)
    pg.insert_text((ux + 8 * MM, uz), "USB-C 13 x 7.5 mm, centro a %.1f mm del fondo" % (USB[1] - TF), fontsize=7)
    x0, yr = 40, 275
    pg.draw_line((x0 * MM, yr * MM), ((x0 + 100) * MM, yr * MM), width=0.6)
    for i in range(101):
        h = 3.0 if i % 10 == 0 else (2.0 if i % 5 == 0 else 1.2)
        pg.draw_line(((x0 + i) * MM, yr * MM), ((x0 + i) * MM, (yr - h) * MM), width=0.3)
        if i % 10 == 0:
            pg.insert_text(((x0 + i) * MM - 3, (yr + 3.5) * MM), str(i), fontsize=6)
    doc.save(os.path.join(OUT, "plantilla_caja_comprada_1a1.pdf"))


def main():
    os.makedirs(OUT, exist_ok=True)
    b, l = base(), lid()
    assert b.status() == m3.Error.NoError and l.status() == m3.Error.NoError
    tb, tl = save(b, "caja_base.stl"), save(l, "caja_tapa.stl")
    print("caja %.0f x %.0f x %.0f mm + tapa %.1f mm; volumen %.1f + %.1f cm3; cerradas:" % (
        X, Y, Z, TL, b.volume() / 1000, l.volume() / 1000), tb.is_watertight, tl.is_watertight)
    cj = conjunto()
    revisar(tb, tl, cj)
    preview(tb, tl, cj)
    plantilla()


if __name__ == "__main__":
    main()
