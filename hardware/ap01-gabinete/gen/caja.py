"""Gabinete de seguridad imprimible (PETG/ASA V-0) para LetreroLab AP-0.1: 2 placas de 90 x 80 mm apiladas
(POTENCIA abajo sobre postes de 6 mm, CABEZAL arriba sobre separadores M3 de 25 mm).

- Tapa con 4 tornillos de seguridad M3 (Torx con pin): solo abre quien tiene la punta. Hueco para sello de garantía.
- Prensaestopas PG7: atrás = entrada de red (2 hilos), izquierda = contacto del relevador (focos), frente = salidas LED.
- Frente: 2 barrenos de 5.5 mm para el receptor IR y el sensor de luz (LDR) asomados.
- Sin ventilas: la electrónica disipa ~1.5 W (fuente HLK de 10 W con 80 % de eficiencia a carga completa).

Se ejecuta en el anfitrión:  pip install manifold3d trimesh matplotlib ; python3 gen/caja.py
Salida: gabinete/caja_base.stl, gabinete/caja_tapa.stl, gabinete/vista_caja.png, gabinete/plantilla_caja_metalica_1a1.pdf
"""
import os
import numpy as np
import manifold3d as m3
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "gabinete")

# --- medidas (mm) ---
PW, PH = 90.0, 80.0                      # placas
HOLES = [(3.5, 3.5), (PW - 3.5, 3.5), (3.5, PH - 3.5), (PW - 3.5, PH - 3.5)]
T, TF, TL = 2.5, 2.5, 3.0                # pared, piso, tapa
P, G = 8.0, 1.0                          # columna de esquina, holgura placa-columna
IH = 72.0                                # potencia (6+1.6) + separadores 25 + cabezal 1.6 + modulo BLE parado (~36) + aire
STAND = 6.0                              # altura de los postes de la placa
INS = 4.0                                # barreno para inserto de latón M3 (D 4.2 x 5.7)
IX, IY = PW + 2 * (P + G), PH + 2 * (P + G)
X, Y, Z = IX + 2 * T, IY + 2 * T, TF + IH
BX, BY, BZ = T + P + G, T + P + G, TF + STAND          # esquina de la placa dentro de la caja
GLAND = 12.5                             # barreno para prensaestopa PG7 (cable 3-6.5 mm)
GZ = BZ + 1.6 + 5.0                      # altura de las clemas de la placa de potencia
GLANDS = [("SALIDAS LED", BX + 52.0)]    # frente (centro de J3)
GLAND_BACK = ("ENTRADA 127 V", BX + 13.5)   # atrás (J1)
GLAND_LEFT = ("FOCOS (contacto)", BY + 57.5)   # izquierda (J4)
SENS = [("IR", BX + 70.0), ("LUZ", BX + 78.0)]  # frente, arriba (receptor IR y LDR con cable)
SZ = Z - 8.0
PILLARS = [(T + P / 2, T + P / 2), (X - T - P / 2, T + P / 2), (T + P / 2, Y - T - P / 2), (X - T - P / 2, Y - T - P / 2)]
SEG = 48


def box(x0, y0, z0, x1, y1, z1):
    return m3.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def cyl(x, y, z0, z1, d):
    return m3.Manifold.cylinder(z1 - z0, d / 2, d / 2, SEG).translate([x, y, z0])


def cyl_y(x, z, y0, y1, d):          # cilindro a lo largo de Y (barreno en la pared del frente)
    return m3.Manifold.cylinder(y1 - y0, d / 2, d / 2, SEG).rotate([-90, 0, 0]).translate([x, y0, z])


def base():
    b = box(0, 0, 0, X, Y, Z) - box(T, T, TF, X - T, Y - T, Z + 1)
    for px, py in PILLARS:                                   # columnas de la tapa
        b += box(px - P / 2, py - P / 2, 0, px + P / 2, py + P / 2, Z)
        b -= cyl(px, py, Z - 8, Z + 1, INS)
    for hx, hy in HOLES:                                     # postes de la placa
        b += cyl(BX + hx, BY + hy, 0, BZ, 7.5)
        b -= cyl(BX + hx, BY + hy, BZ - 6, BZ + 1, INS)
    for _, gx in GLANDS:                                     # prensaestopas en el frente
        b -= cyl_y(gx, GZ, Y - T - 1, Y + 1, GLAND)
    b -= cyl_y(GLAND_BACK[1], GZ, -1, T + 1, GLAND)          # atrás: red
    b -= m3.Manifold.cylinder(T + 2, GLAND / 2, GLAND / 2, SEG).rotate([0, 90, 0]).translate([-1, GLAND_LEFT[1], GZ])
    for _, sx in SENS:                                       # IR y LDR
        b -= cyl_y(sx, SZ, Y - T - 1, Y + 1, 5.5)
    for side in (-1, 1):                                     # orejas de montaje
        x0 = -14 if side < 0 else X
        ear = box(x0, Y / 2 - 10, 0, x0 + 14, Y / 2 + 10, 3)
        ear -= cyl(x0 + (7 if side < 0 else 7), Y / 2, -1, 4, 4.5)
        b += ear
    return b


def lid():
    lt = box(0, 0, 0, X, Y, TL)
    lip = box(T + 0.3, T + 0.3, -2.0, X - T - 0.3, Y - T - 0.3, 0.01) - \
        box(T + 1.8, T + 1.8, -3, X - T - 1.8, Y - T - 1.8, 1)
    for px, py in PILLARS:
        lip -= box(px - P / 2 - 0.5, py - P / 2 - 0.5, -3, px + P / 2 + 0.5, py + P / 2 + 0.5, 1)
    lt += lip
    for px, py in PILLARS:
        lt -= cyl(px, py, -3, TL + 1, 3.4)                   # paso M3
        lt -= cyl(px, py, TL - 1.6, TL + 1, 6.6)             # caja para la cabeza del tornillo
    lt -= box(X / 2 - 22, Y / 2 - 9, TL - 0.4, X / 2 + 22, Y / 2 + 9, TL + 1)   # hueco para etiqueta/sello
    return lt


def save(man, name):
    mesh = man.to_mesh()
    tm = trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts))
    tm.export(os.path.join(OUT, name))
    return tm


def render(parts, elev, azim, size=(700, 520)):
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
            if nn < 1e-9:
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


def preview(tb, tl):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    pcb = trimesh.creation.box(extents=(PW, PH, 1.6))
    pcb.apply_translation((BX + PW / 2, BY + PH / 2, BZ + 0.8))
    parts = [(pcb, (0.15, 0.55, 0.25))]
    for x0, y0, x1, y1, h in ((24, 10, 74, 41, 23), (40, 54, 86, 60, 20), (13, 52, 33, 68, 16), (37, 68, 67, 80, 10),
                              (0, 1, 22, 12, 10)):
        c = trimesh.creation.box(extents=(x1 - x0, y1 - y0, h))   # volúmenes aproximados: MOSFET, Nano, clemas
        c.apply_translation((BX + (x0 + x1) / 2, BY + (y0 + y1) / 2, BZ + 1.6 + h / 2))
        parts.append((c, (0.2, 0.2, 0.22)))
    tl2 = tl.copy()
    tl2.apply_translation((0, 0, Z + 25))
    imgs = [render([(tb, (0.62, 0.66, 0.72))] + parts, -55, 25),
            render([(tb, (0.62, 0.66, 0.72)), (tl2, (0.75, 0.78, 0.82))], -60, -30)]
    fig, axs = plt.subplots(1, 2, figsize=(13, 5.2), dpi=110)
    for ax_, im, ttl in zip(axs, imgs, ("Base con la placa de potencia (fuente, MOSFET, relevador, clemas)",
                                        "Tapa con 4 tornillos de seguridad y hueco para el sello")):
        ax_.imshow(np.clip(im, 0, 1)); ax_.set_title(ttl, fontsize=10); ax_.axis("off")
    fig.suptitle("Gabinete de seguridad LetreroLab AP-0.1 - %.0f x %.0f x %.0f mm + tapa %.0f mm  |  3 prensaestopas PG7 + IR + luz"
                 % (X, Y, Z, TL))
    fig.savefig(os.path.join(OUT, "vista_caja.png"), bbox_inches="tight")


def plantilla():
    """Plantilla 1:1 para usar una caja METALICA comprada: barrenos de la placa y de los prensaestopas."""
    import pymupdf as fitz
    MM = 72 / 25.4
    doc = fitz.open()
    pg = doc.new_page(width=210 * MM, height=297 * MM)
    t = ["PLANTILLA 1:1 PARA CAJA (LetreroLab AP-0.1, 2 placas 90 x 80 apiladas)",
         "Imprimir al 100 %. Verificar la regla. Pegar con cinta en el fondo de la caja y marcar con punzon.",
         "Fondo: 4 barrenos de 3.2 mm (separadores de nylon M3). Caja METALICA: conectar a tierra fisica. Frente: 2 barrenos de 12.5 mm (prensaestopas PG7).",
         "Caja minima interior: %.0f x %.0f mm de fondo y %.0f mm de alto (o cualquiera mas grande)." % (PW + 12, PH + 12, IH)]
    y = 14
    for i, s in enumerate(t):
        pg.insert_text((15 * MM, y * MM), s, fontsize=10 if i == 0 else 7.5, fontname="hebo" if i == 0 else "helv")
        y += 6 if i == 0 else 4.2
    ox, oy = 30, 45                                          # contorno de la placa
    pg.draw_rect(fitz.Rect(ox * MM, oy * MM, (ox + PW) * MM, (oy + PH) * MM), width=0.4, dashes="[2 2] 0")
    pg.insert_text(((ox + 2) * MM, (oy + PH / 2) * MM), "contorno de la placa (lado componentes)", fontsize=6)
    pg.insert_text(((ox + 12) * MM, (oy + PH - 3) * MM), "FRENTE (clemas)", fontsize=6)
    for hx, hy in HOLES:
        cx, cy = (ox + hx) * MM, (oy + hy) * MM
        pg.draw_circle((cx, cy), 1.6 * MM, width=0.4)
        pg.draw_line((cx - 3 * MM, cy), (cx + 3 * MM, cy), width=0.2)
        pg.draw_line((cx, cy - 3 * MM), (cx, cy + 3 * MM), width=0.2)
    pg.insert_text((ox * MM, (oy + PH + 6) * MM), "Separacion entre barrenos: %.1f x %.1f mm" % (PW - 7, PH - 7),
                   fontsize=8, fontname="hebo")
    fx, fz = 30, 150                                          # frente de la caja (vista exterior)
    pg.insert_text((fx * MM, (fz - 4) * MM), "FRENTE de la caja (visto desde afuera); la linea de abajo = fondo interior",
                   fontsize=8, fontname="hebo")
    pg.draw_line((fx * MM, (fz + 30) * MM), ((fx + PW) * MM, (fz + 30) * MM), width=0.6)
    for name, gx in GLANDS:
        cx, cz = (fx + gx - BX) * MM, (fz + 30 - (GZ - TF)) * MM
        pg.draw_circle((cx, cz), GLAND / 2 * MM, width=0.4)
        pg.draw_line((cx - 2 * MM, cz), (cx + 2 * MM, cz), width=0.2)
        pg.draw_line((cx, cz - 2 * MM), (cx, cz + 2 * MM), width=0.2)
        pg.insert_text((cx - 8 * MM, cz + 10 * MM), name, fontsize=7)
    pg.insert_text((fx * MM, (fz + 36) * MM),
                   "Centro de los prensaestopas a %.1f mm sobre el fondo (separadores de %.0f mm; con separadores de 8 mm, %.1f mm)."
                   % (GZ - TF, STAND, GZ - TF + 8 - STAND), fontsize=7)
    x0, yr = 40, 270
    pg.draw_line((x0 * MM, yr * MM), ((x0 + 100) * MM, yr * MM), width=0.6)
    for i in range(101):
        h = 3.0 if i % 10 == 0 else (2.0 if i % 5 == 0 else 1.2)
        pg.draw_line(((x0 + i) * MM, yr * MM), ((x0 + i) * MM, (yr - h) * MM), width=0.3)
        if i % 10 == 0:
            pg.insert_text(((x0 + i) * MM - 3, (yr + 3.5) * MM), str(i), fontsize=6)
    doc.save(os.path.join(OUT, "plantilla_caja_metalica_1a1.pdf"))


def main():
    os.makedirs(OUT, exist_ok=True)
    b, l = base(), lid()
    assert b.status() == m3.Error.NoError and l.status() == m3.Error.NoError
    tb, tl = save(b, "caja_base.stl"), save(l, "caja_tapa.stl")
    print("base %.0f x %.0f x %.0f mm, volumen %.1f cm3 ; tapa volumen %.1f cm3; estancas:" % (X, Y, Z, b.volume() / 1000,
          l.volume() / 1000), tb.is_watertight, tl.is_watertight)
    preview(tb, tl)
    plantilla()


if __name__ == "__main__":
    main()
