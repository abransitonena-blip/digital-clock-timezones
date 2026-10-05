"""Soporte imprimible para montar las placas AP ELECTRIC / AP-1 en riel DIN de 35 mm (TS35, EN 60715).

- Charola de 3 mm con postes de 5.5 mm para inserto de latón M3 (D 4.2 x 5.7) en los agujeros de la placa: las patas
  de las piezas THT (3.4 mm) no tocan la charola.
- Atrás: 2 ganchos fijos arriba (se apoyan sobre el borde superior del riel) y un seguro flexible abajo, una viga de
  18 x 1.5 mm con rampa: se monta inclinando el módulo, enganchando arriba y empujando abajo hasta que suene "clic".
  Para quitarlo, empuja la viga hacia abajo con un desarmador plano por la parte de abajo y gira el módulo.
- Se genera para las dos medidas del ecosistema:
    88 x 56 mm (BASE, IND, PIX, DMX, PLANTILLA): el riel queda horizontal y la placa ocupa 5 módulos DIN de ancho;
    72 x 56 mm (AP INPUT, AP OUTPUT): 4 módulos DIN.
- Imprimir en PETG o ASA, con la cara de atrás (ganchos) hacia arriba, 4 paredes y 40 % de relleno.
  PROTOTIPO: el ajuste del seguro se prueba con un tramo de riel antes de imprimir en serie.

Se ejecuta en el anfitrión:  pip install manifold3d trimesh matplotlib ; python3 ap1-gabinete/gen/soporte_din.py
Salida en ap1-gabinete/din/: soporte_din_88x56.stl, soporte_din_72x56.stl, vista_soporte_din.png
"""
import os
import numpy as np
import manifold3d as m3
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "din")
SEG = 48

PLACAS = {
    "88x56": (88.0, 56.0, [(3.5, 3.5), (84.5, 39.5), (84.5, 52.5)]),
    "72x56": (72.0, 56.0, [(3.5, 3.5), (68.5, 3.5), (68.5, 38.5)]),
}
TP = 3.0                 # charola
POSTE, POSTE_D, INS = 5.5, 7.0, 4.0
RIEL, ALA, ESP = 35.0, 5.0, 1.0      # riel TS35: 35 mm de alto, alas de 5 mm y 1 mm de grueso
HOL = 0.3                # holgura con el riel
PROF = 2.6               # qué tanto salen ganchos y seguro hacia atrás
LABIO = 1.3              # grueso del labio que queda detrás del ala


def box(x0, y0, z0, x1, y1, z1):
    return m3.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def cyl(x, y, z0, z1, d):
    return m3.Manifold.cylinder(z1 - z0, d / 2, d / 2, SEG).translate([x, y, z0])


def _prisma_x(x0, x1, perfil):
    """Extruye a lo largo de x un perfil [(y, z), ...] (en cualquier sentido de giro)."""
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(perfil, perfil[1:] + perfil[:1]))
    m = m3.Manifold.extrude(m3.CrossSection([perfil if area > 0 else perfil[::-1]]), x1 - x0)          # (u, v, w) con u = y, v = z, w = x
    me = m.to_mesh()
    v = np.asarray(me.vert_properties)[:, :3]
    v = np.c_[v[:, 2] + x0, v[:, 0], v[:, 1]]                            # permutación cíclica: no voltea las caras
    return m3.Manifold(m3.Mesh(vert_properties=np.ascontiguousarray(v, dtype=np.float32),
                               tri_verts=np.ascontiguousarray(me.tri_verts, dtype=np.uint32)))


def soporte(W, H, holes):
    # coordenadas: x a lo largo del riel, y hacia abajo (como en KiCad), z hacia la placa (atrás de la charola: z < 0)
    yc = H / 2.0
    top, bot = yc - RIEL / 2, yc + RIEL / 2               # bordes del riel
    s = box(0, 0, 0, W, H, TP)
    for x, y in holes:
        s = s + cyl(x, y, TP, TP + POSTE, POSTE_D)
    for x, y in holes:
        s = s - cyl(x, y, TP + POSTE - 5.7, TP + POSTE + 0.1, INS)
    # ganchos fijos arriba (dos tramos): poste fuera del ala y labio detrás de ella
    for x0, x1 in ((6.0, 22.0), (W - 22.0, W - 6.0)):
        s = s + _prisma_x(x0, x1, [(top - HOL - 2.0, 0.5), (top - HOL - 2.0, -PROF), (top + 2.5, -PROF),
                                   (top + 2.5, -PROF + LABIO - 0.2), (top - HOL, -ESP - HOL), (top - HOL, 0.5)])
    # seguro flexible abajo: viga a lo largo de x, anclada a la derecha, libre a la izquierda con rampa
    xa0, xa1 = W / 2 + 8.0, W / 2 + 12.0                  # ancla
    xl = W / 2 - 10.0                                     # punta libre
    yb0, yb1 = bot + HOL + 0.2, bot + HOL + 1.7           # viga de 1.5 mm (se dobla en y)
    s = s - box(xl - 1.0, bot + HOL, -0.01, xa0, yb1 + 2.5, TP + 0.01)    # ranura: la viga no toca la charola
    s = s + box(xl, yb0, -PROF, xa1, yb1, 0.0)            # viga
    s = s + box(xa0, yb0, -PROF, xa1, yb1 + 2.5, TP)      # ancla unida a la charola
    s = s + _prisma_x(xl, xl + 6.0, [(yb0 + 0.5, -PROF), (yb0 + 0.5, -ESP - HOL), (bot - 2.5, -ESP - HOL), (yb0, -PROF)])   # labio con rampa
    return s


def save(man, path):
    mesh = man.to_mesh()
    tm = trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts))
    tm.export(path)
    return tm


def riel(W, H):
    yc = H / 2.0
    r = box(-6, yc - RIEL / 2, -ESP, W + 6, yc - RIEL / 2 + ALA, 0) + box(-6, yc + RIEL / 2 - ALA, -ESP, W + 6, yc + RIEL / 2, 0)
    r = r + box(-6, yc - RIEL / 2 + ALA - ESP, -7.5, W + 6, yc - RIEL / 2 + ALA, 0)
    r = r + box(-6, yc + RIEL / 2 - ALA, -7.5, W + 6, yc + RIEL / 2 - ALA + ESP, 0)
    r = r + box(-6, yc - RIEL / 2 + ALA - ESP, -7.5, W + 6, yc + RIEL / 2 - ALA + ESP, -7.5 + ESP)
    return r


def main():
    os.makedirs(OUT, exist_ok=True)
    piezas = []
    for nombre, (W, H, holes) in PLACAS.items():
        s = soporte(W, H, holes)
        r = riel(W, H)
        choque = (s ^ r).volume()
        assert choque < 1e-6, "%s: el soporte choca con el riel (%.3f mm3)" % (nombre, choque)
        assert s.num_tri() > 0 and s.genus() >= 0 and s.status() == m3.Error.NoError
        tm = save(s, os.path.join(OUT, "soporte_din_%s.stl" % nombre))
        print("%s: %.0f x %.0f x %.1f mm, %.1f cm3, cerrado: %s" % (nombre, *tm.extents, tm.volume / 1000, tm.is_watertight))
        piezas.append((nombre, s, r))
    vista(piezas)


def vista(piezas):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import importlib.util
    spec = importlib.util.spec_from_file_location("caja", os.path.join(HERE, "caja.py"))
    caja = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(caja)
    fig, ax = plt.subplots(1, 2, figsize=(12, 5))
    for k, (nombre, s, r) in enumerate(piezas):
        def tm(m):
            me = m.to_mesh()
            v = np.asarray(me.vert_properties)[:, :3] * [1, 1, -1]            # espejo en z: se ve la cara de atrás
            return trimesh.Trimesh(vertices=v, faces=np.asarray(me.tri_verts)[:, ::-1])
        img = caja.render([(tm(s), (0.25, 0.27, 0.30)), (tm(r), (0.75, 0.77, 0.80))], 50, -150, size=(620, 480))
        ax[k].imshow(img); ax[k].axis("off"); ax[k].set_title("Soporte DIN %s mm, visto por detrás (gris claro: riel TS35)" % nombre)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "vista_soporte_din.png"), dpi=110)


if __name__ == "__main__":
    main()
