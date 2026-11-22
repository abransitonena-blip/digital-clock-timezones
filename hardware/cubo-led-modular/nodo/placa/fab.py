"""Cubo AP · placa de control: enrutado automático (A* en rejilla, 2 capas), vias de GND, planos, DRC y exportación.
Uso: python3.11 fab.py   ->  ruteo.json, vistas SVG, gerbers/ , BOM y CPL para ensamblado.
Reglas: pista mínima 0.2 mm, separación 0.2 mm (planos 0.3 mm), via 0.6/0.3 mm. Todo dentro de lo estándar de JLCPCB."""
import heapq, json, math, os, sys, collections, time
import numpy as np
from scipy import ndimage
import shapely
from shapely.geometry import Point, LineString, Polygon, MultiPolygon, box
from shapely.ops import unary_union
import diseno as D, geom as G

RES = 0.1                     # mm por celda
CLR, CLR_PLANO = 0.2, 0.3
W_SEN = 0.2
VIA_D, VIA_TAL = 0.6, 0.3
COSTO_CAPA = (1.0, 1.8)       # abajo cuesta más: preservar el plano de GND
COSTO_VIA = 12.0
NX, NY = int(round(D.W / RES)), int(round(D.H / RES))
XS = -D.W / 2 + RES / 2 + np.arange(NX) * RES
YS = -D.H / 2 + RES / 2 + np.arange(NY) * RES
GX, GY = np.meshgrid(XS, YS)
BORDE = G.contorno()
EXCLUIR = unary_union([Point(h).buffer(2.2) for h in D.BARRENOS])
# zona fina: alrededor del QFN las pistas se angostan a W_FINO (paso 0.5 mm); fuera conservan su ancho
ZONA_FINA = getattr(D, "ZONA_FINA", None)
W_FINO = getattr(D, "W_FINO", 0.15)
EN_ZONA = shapely.contains_xy(ZONA_FINA, GX, GY) if ZONA_FINA is not None else np.zeros_like(GX, bool)
VEDA = getattr(D, "VEDA", [])                 # [(capas, polígono)]: sin pistas ni vias de señal (GND sólido bajo RF y cristal)
CLR_PLANO_RED = getattr(D, "CLR_PLANO_RED", {})

def ancho(n): return D.ANCHO.get(n, W_SEN)
def pad_geo(q):
    if q["f"] == "c": return Point(q["x"], q["y"]).buffer(q["w"] / 2, 24)
    if q["f"] == "rr":
        r = 0.25 * min(q["w"], q["h"])
        return box(q["x"] - q["w"] / 2 + r, q["y"] - q["h"] / 2 + r, q["x"] + q["w"] / 2 - r, q["y"] + q["h"] / 2 - r).buffer(r, 8)
    return box(q["x"] - q["w"] / 2, q["y"] - q["h"] / 2, q["x"] + q["w"] / 2, q["y"] + q["h"] / 2)

class Placa:
    def __init__(self):
        self.cobre = [[], []]                     # por capa: (red, geom, tipo)
        self.vias = []                            # (x, y, red)
        self.dueno = np.zeros((2, NY, NX), np.int32)
        self.idred = {}
        self.pads = G.todos_pads(); self.pistas = []
        for q in self.pads:
            q["g"] = pad_geo(q)
            for l in ((0, 1) if q["drill"] else (0,)):
                self.agregar(l, q["net"], q["g"], "pad")
        # zonas de potencia recortadas contra pads de otras redes
        for n, z in D.ZONAS.items():
            otros = unary_union([q["g"] for q in self.pads if q["net"] != n]).buffer(CLR_PLANO)
            zz = z.difference(otros).intersection(BORDE.buffer(-0.3))
            self.agregar(0, n, zz, "zona")
        for t in getattr(D, "PISTAS", []):          # pistas fijas (RF, cristal, desacoplo): trazadas a mano, el ruteador no las toca
            ls = LineString(t["pts"])
            self.agregar(t.get("capa", 0), t["red"], ls.buffer(t["w"] / 2, 8, cap_style="flat" if t.get("plana") else "round"), "fija")
            self.pistas.append(dict(red=t["red"], capa=t.get("capa", 0), w=t["w"], pts=t["pts"], fija=True))
        for x, y, n in getattr(D, "VIAS", []): self.agregar_via(x, y, n)

    def id(self, n):
        if n not in self.idred: self.idred[n] = len(self.idred) + 1
        return self.idred[n]

    def pintar(self, l, n, g):
        x0, y0, x1, y1 = g.bounds
        i0, i1 = max(0, int((x0 + D.W / 2) / RES) - 1), min(NX, int((x1 + D.W / 2) / RES) + 2)
        j0, j1 = max(0, int((y0 + D.H / 2) / RES) - 1), min(NY, int((y1 + D.H / 2) / RES) + 2)
        if i0 >= i1 or j0 >= j1: return
        m = shapely.contains_xy(g, GX[j0:j1, i0:i1], GY[j0:j1, i0:i1])
        self.dueno[l, j0:j1, i0:i1][m] = self.id(n)

    def agregar(self, l, n, g, tipo):
        if g.is_empty: return
        self.cobre[l].append((n, g, tipo)); self.pintar(l, n, g)

    def agregar_via(self, x, y, n):
        self.vias.append((x, y, n))
        for l in (0, 1): self.agregar(l, n, Point(x, y).buffer(VIA_D / 2, 16), "via")

    # ---------- islas de una red ----------
    def islas(self, n):
        piezas = [(l, g) for l in (0, 1) for (m, g, t) in self.cobre[l] if m == n]
        enlaces = [Point(q["x"], q["y"]) for q in self.pads if q["net"] == n and q["drill"]] + \
                  [Point(x, y) for x, y, m in self.vias if m == n]
        uf = list(range(len(piezas)))
        def f(i):
            while uf[i] != i: uf[i] = uf[uf[i]]; i = uf[i]
            return i
        for i in range(len(piezas)):
            for j in range(i + 1, len(piezas)):
                li, gi = piezas[i]; lj, gj = piezas[j]
                if li == lj and gi.intersects(gj): uf[f(i)] = f(j)
                elif li != lj and any(gi.contains(p) and gj.contains(p) for p in enlaces): uf[f(i)] = f(j)
        grupos = collections.defaultdict(list)
        for i, p in enumerate(piezas): grupos[f(i)].append(p)
        return list(grupos.values())

    # ---------- búsqueda A* ----------
    def celdas(self, isla, w):
        out = set()
        for l, g in isla:
            for gg in (g.buffer(-w / 2), g):
                if gg.is_empty: continue
                x0, y0, x1, y1 = gg.bounds
                i0, i1 = max(0, int((x0 + D.W / 2) / RES)), min(NX, int((x1 + D.W / 2) / RES) + 1)
                j0, j1 = max(0, int((y0 + D.H / 2) / RES)), min(NY, int((y1 + D.H / 2) / RES) + 1)
                if i0 >= i1 or j0 >= j1: continue
                m = shapely.contains_xy(gg, GX[j0:j1, i0:i1], GY[j0:j1, i0:i1])
                js, is_ = np.nonzero(m)
                if len(js):
                    out |= {(l, j0 + a, i0 + b) for a, b in zip(js, is_)}
                    break
        return out

    def rutear(self, n, origen, destino, ventana=None):
        w = ancho(n); idn = self.id(n); wf = min(w, W_FINO)
        margen = RES * 0.9
        bloq, bloq_via = [], []
        for l in (0, 1):
            otro = (self.dueno[l] != 0) & (self.dueno[l] != idn)
            d = ndimage.distance_transform_edt(~otro) * RES
            bloq.append(np.where(EN_ZONA, d < (wf / 2 + CLR + margen), d < (w / 2 + CLR + margen)))
            bloq_via.append(d < (VIA_D / 2 + CLR + margen))
        fuera = ~shapely.contains_xy(BORDE.buffer(-(w / 2 + 0.3)), GX, GY) | shapely.contains_xy(EXCLUIR.buffer(w / 2 + 0.2), GX, GY)
        for l in (0, 1): bloq[l] = bloq[l] | fuera
        via_no = bloq_via[0] | bloq_via[1] | fuera | ~shapely.contains_xy(BORDE.buffer(-0.8), GX, GY)
        for capas, pol in VEDA:
            m = shapely.contains_xy(pol.buffer(w / 2 + CLR), GX, GY)
            for l in capas: bloq[l] = bloq[l] | m
            via_no = via_no | m
        src = self.celdas(origen, w); dst = self.celdas(destino, w)
        def utiles(cs):
            ok = {c for c in cs if not bloq[c[0]][c[1], c[2]]}
            return ok if ok else cs
        src, dst = utiles(src), utiles(dst)
        for c in src | dst: bloq[c[0]][c[1], c[2]] = False
        if not src or not dst: return None
        dl = np.array([[c[1], c[2]] for c in dst])
        ty, tx = dl.mean(0)
        INF = 1e18
        g = {}; prev = {}; pq = []
        for c in src: g[c] = 0.0; heapq.heappush(pq, (math.hypot(c[1] - ty, c[2] - tx) * 0.9, c))
        dirs = [(0, 1, 1.0), (1, 0, 1.0), (0, -1, 1.0), (-1, 0, 1.0), (1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (-1, -1, 1.4142)]
        fin = None; exp = 0
        while pq:
            f, c = heapq.heappop(pq)
            gc = g[c]
            if c in dst: fin = c; break
            exp += 1
            if exp > 1500000: break
            l, j, i = c
            for dj, di, k in dirs:
                jj, ii = j + dj, i + di
                if not (0 <= jj < NY and 0 <= ii < NX) or bloq[l][jj, ii]: continue
                if ventana and not (ventana[0] <= ii <= ventana[2] and ventana[1] <= jj <= ventana[3]): continue
                if dj and di and (bloq[l][j, ii] or bloq[l][jj, i]): continue
                nc = (l, jj, ii); ng = gc + k * COSTO_CAPA[l]
                if ng < g.get(nc, INF):
                    g[nc] = ng; prev[nc] = c
                    heapq.heappush(pq, (ng + math.hypot(jj - ty, ii - tx) * 0.9, nc))
            if not via_no[j, i]:
                nc = (1 - l, j, i); ng = gc + COSTO_VIA
                if not bloq[1 - l][j, i] and ng < g.get(nc, INF):
                    g[nc] = ng; prev[nc] = c; heapq.heappush(pq, (ng + math.hypot(j - ty, i - tx) * 0.9, nc))
        if fin is None: return None
        camino = [fin]
        while camino[-1] in prev: camino.append(prev[camino[-1]])
        return camino[::-1]

    def trazar(self, n, camino):
        w = ancho(n)
        def xy(c): return (XS[c[2]], YS[c[1]])
        tramo = [camino[0]]
        geoms = []
        for a, b in zip(camino, camino[1:]):
            if a[0] != b[0]:
                if len(tramo) > 1: geoms.append((tramo[0][0], [xy(c) for c in tramo]))
                self.agregar_via(*xy(a), n); tramo = [b]
            else: tramo.append(b)
        if len(tramo) > 1: geoms.append((tramo[0][0], [xy(c) for c in tramo]))
        for l, pts in geoms:
            ls = LineString(pts).simplify(RES * 0.3)
            if ZONA_FINA is not None and ls.intersects(ZONA_FINA) and w > W_FINO:
                g = unary_union([ls.difference(ZONA_FINA).buffer(w / 2, 8), ls.intersection(ZONA_FINA).buffer(W_FINO / 2, 8)])
            else: g = ls.buffer(w / 2, 8)
            self.agregar(l, n, g, "pista")
            self.pistas.append(dict(red=n, capa=l, w=w, pts=[(round(x, 3), round(y, 3)) for x, y in ls.coords]))

    def conectar_red(self, n):
        for intento in range(40):
            isl = self.islas(n)
            if len(isl) <= 1: return True
            base = max(isl, key=lambda s: sum(g.area for _, g in s))
            otras = [s for s in isl if s is not base]
            ub = unary_union([g for _, g in base])
            otras.sort(key=lambda s: unary_union([g for _, g in s]).distance(ub))
            ok = False
            for o in otras[:3] if n != "GND" else otras:
                bb = unary_union([g for _, g in base] + [g for _, g in o]).bounds
                v = (max(0, int((bb[0] + D.W / 2 - 6) / RES)), max(0, int((bb[1] + D.H / 2 - 6) / RES)),
                     min(NX, int((bb[2] + D.W / 2 + 6) / RES)), min(NY, int((bb[3] + D.H / 2 + 6) / RES)))
                cam = self.rutear(n, base, o, v) or self.rutear(n, base, o)
                if cam: self.trazar(n, cam); ok = True; break
            if not ok and n == "GND":
                return False
            if not ok:
                self.ult_par = (ub, unary_union([g for _, g in otras[0]]))
                return False
        return False

    def repintar(self):
        self.dueno[:] = 0
        for l in (0, 1):
            for n, g, t in self.cobre[l]: self.pintar(l, n, g)

    def arrancar(self, n):
        for l in (0, 1): self.cobre[l] = [c for c in self.cobre[l] if not (c[0] == n and c[2] in ("pista", "via"))]
        self.vias = [v for v in self.vias if v[2] != n]
        self.pistas = [p for p in self.pistas if p["red"] != n or p.get("fija")]
        for x, y, m in getattr(D, "VIAS", []):
            if m == n: self.agregar_via(x, y, m)                 # las vias fijas no se arrancan
        self.repintar()

    def estorbos(self, n):
        a, b = self.ult_par
        pa, pb = shapely.ops.nearest_points(a, b)
        corr = LineString([pa, pb]).buffer(3.0)
        cuenta = collections.Counter()
        for l in (0, 1):
            for m, g, t in self.cobre[l]:
                if m != n and m != "GND" and t in ("pista", "via") and g.intersects(corr): cuenta[m] += g.intersection(corr).area
        return [m for m, _ in cuenta.most_common()]

    # ---------- GND: vias junto a cada pad y planos ----------
    def libre(self, g, l, n, clr):
        for m, h, t in self.cobre[l]:
            if m != n and h.distance(g) < clr: return False
        return True

    def vias_gnd(self):
        for q in self.pads:
            if q["net"] != "GND" or q["drill"]: continue
            area = q["w"] * q["h"]
            puestos = 0
            if area >= 2.0:                                      # via en el pad (pads grandes de potencia)
                nx_, ny_ = max(1, int(q["w"] / 1.1)), max(1, int(q["h"] / 1.1))
                for a in range(nx_):
                    for b in range(ny_):
                        x = q["x"] - q["w"] / 2 + q["w"] * (a + 0.5) / nx_; y = q["y"] - q["h"] / 2 + q["h"] * (b + 0.5) / ny_
                        v = Point(x, y).buffer(VIA_D / 2)
                        if self.libre(v, 1, "GND", CLR) and self.libre(v, 0, "GND", CLR) and not EXCLUIR.intersects(v):
                            self.agregar_via(x, y, "GND"); puestos += 1
            if puestos: continue
            r0 = max(q["w"], q["h"]) / 2 + VIA_D / 2 + 0.25
            mejor = None
            for r in (r0, r0 + 0.3, r0 + 0.6, r0 + 1.0, r0 + 1.5, r0 + 2.2):
                for k in range(36):
                    a = 2 * math.pi * k / 36
                    x, y = q["x"] + r * math.cos(a), q["y"] + r * math.sin(a)
                    v = Point(x, y).buffer(VIA_D / 2); t = LineString([(q["x"], q["y"]), (x, y)]).buffer(0.125)
                    if BORDE.buffer(-0.6).contains(v) and not EXCLUIR.intersects(v) and \
                       self.libre(v, 0, "GND", CLR) and self.libre(v, 1, "GND", CLR) and self.libre(t, 0, "GND", CLR):
                        mejor = (x, y, t); break
                if mejor: break
            if mejor:
                self.agregar_via(mejor[0], mejor[1], "GND"); self.agregar(0, "GND", mejor[2], "pista")
                self.pistas.append(dict(red="GND", capa=0, w=0.25, pts=[(q["x"], q["y"]), (round(mejor[0], 3), round(mejor[1], 3))]))
            else: print("  sin via de GND para", q["ref"], q["pin"])

    def planos(self):
        for l in (0, 1):
            otros = unary_union([g.buffer(CLR_PLANO_RED.get(n, CLR_PLANO)) for n, g, t in self.cobre[l] if n != "GND"])
            area = BORDE.buffer(-0.4).difference(otros).difference(EXCLUIR)
            area = area.buffer(-0.13).buffer(0.13)            # quita astillas
            gnd = unary_union([g for n, g, t in self.cobre[l] if n == "GND"])
            partes = getattr(area, "geoms", [area])
            buenas = [p for p in partes if p.area > 1.0 and p.intersects(gnd)]
            if l == 0:                                        # islas sin GND: coserlas al plano inferior con una via
                abajo = unary_union([g for n, g, t in self.cobre[1] if n != "GND"]).buffer(CLR + VIA_D / 2)
                for p in partes:
                    if p.area > 3.0 and not p.intersects(gnd):
                        dentro = p.buffer(-(VIA_D / 2 + 0.05)).difference(abajo)
                        if not dentro.is_empty:
                            c = dentro.representative_point()
                            self.agregar_via(c.x, c.y, "GND"); buenas.append(p)
            self.agregar(l, "GND", unary_union(buenas), "plano")

    # ---------- DRC ----------
    def drc(self):
        err = []
        for l in (0, 1):
            por = collections.defaultdict(list)
            for n, g, t in self.cobre[l]: por[n].append(g)
            u = {n: unary_union(v) for n, v in por.items()}
            ns = sorted(u)
            arbol = shapely.STRtree([u[n] for n in ns])
            for i, n in enumerate(ns):
                for j in arbol.query(u[n].buffer(CLR)):
                    if j <= i: continue
                    d = u[n].distance(u[ns[j]])
                    if d < CLR - 0.005:
                        p = shapely.ops.nearest_points(u[n], u[ns[j]])[0]
                        err.append(f"capa {'TB'[l]}: {n}–{ns[j]} a {d:.3f} mm en ({p.x:.1f}, {p.y:.1f})")
            todo = unary_union(list(u.values()))
            if not BORDE.buffer(-0.25).contains(todo.difference(unary_union([q["g"] for q in self.pads if q["drill"]]).buffer(0.01))):
                err.append(f"capa {'TB'[l]}: cobre a menos de 0.25 mm del borde")
            for h in D.BARRENOS:
                if todo.distance(Point(h)) < 1.6 + 0.3: err.append(f"capa {'TB'[l]}: cobre cerca del barreno {h}")
        # conectividad
        redes = sorted({q["net"] for q in self.pads if not q["net"].startswith("NC")})
        abiertas = []
        for n in redes:
            isl = self.islas(n)
            pads_n = [q for q in self.pads if q["net"] == n]
            comp = []
            for q in pads_n:
                p = Point(q["x"], q["y"])
                k = next((i for i, s in enumerate(isl) if any(l == 0 and g.intersects(q["g"]) for l, g in s)), None)
                comp.append(k)
            if len(set(comp)) > 1 or None in comp:
                abiertas.append(f"{n}: " + ", ".join(f"{q['ref']}.{q['pin']}→{c}" for q, c in zip(pads_n, comp)))
        return err, abiertas

ARCH_COBRE = "cobre.json"
def guardar_cobre(cobre):     # geometrías como WKB hexadecimal (sin pickle)
    json.dump([[(n, shapely.to_wkb(g, hex=True), t) for n, g, t in capa] for capa in cobre], open(ARCH_COBRE, "w"))
def cargar_cobre():
    return [[(n, shapely.from_wkb(w), t) for n, w, t in capa] for capa in json.load(open(ARCH_COBRE))]

def correr():
    t0 = time.time()
    P = Placa()
    redes = sorted({q["net"] for q in P.pads if q["net"] != "GND" and not q["net"].startswith("NC")})
    def tam(n):
        ps = [(q["x"], q["y"]) for q in P.pads if q["net"] == n]
        xs, ys = zip(*ps); return (max(xs) - min(xs)) + (max(ys) - min(ys))
    prio = ["FB", "COMP", "CC", "RT", "BOOT", "EN", "SW5", "CB", "FB5", "QG"]
    chip = {q["net"] for q in P.pads if q["ref"] == "U3"} - {"GND", "3V3"}
    redes.sort(key=lambda n: (n not in prio, n not in chip, -tam(n)))
    P.vias_gnd()                                             # primero reservar las salidas de GND
    fallas = []
    for n in redes:
        ok = P.conectar_red(n)
        print(f"  {'ok ' if ok else 'FALLA'} {n}  ({time.time() - t0:.0f} s)"); sys.stdout.flush()
        if not ok: fallas.append(n)
    arrancadas = collections.Counter()
    for ronda in range(30):                                   # arrancar y rehacer
        if not fallas: break
        n = fallas.pop(0)
        if not P.conectar_red(n):
            quitar = [m for m in P.estorbos(n) if arrancadas[m] < 3][:3]
            for m in quitar: P.arrancar(m); arrancadas[m] += 1
            ok = P.conectar_red(n)
            print(f"  ronda {ronda}: {n} {'ok' if ok else 'FALLA'} (quité {', '.join(quitar)})")
            if not ok: fallas.append(n)
            for m in quitar:
                if not P.conectar_red(m): fallas.append(m); print("    se cayó", m)
        else: print("  ok (reintento)", n)
    P.planos()
    if len(P.islas("GND")) > 1:                              # pads de GND aislados: rutearlos al plano
        for l in (0, 1): P.cobre[l] = [c for c in P.cobre[l] if c[2] != "plano"]
        P.repintar()
        P.planos(); ok = P.conectar_red("GND"); print("  GND aislados:", "ok" if ok else "FALLA")
        for l in (0, 1): P.cobre[l] = [c for c in P.cobre[l] if c[2] != "plano"]
        P.repintar(); P.planos()
    err, abiertas = P.drc()
    return P, fallas, err, abiertas

if __name__ == "__main__":
    P, fallas, err, abiertas = correr()
    json.dump(dict(pistas=P.pistas, vias=P.vias), open("ruteo.json", "w"), indent=0)
    guardar_cobre(P.cobre)
    print("vias:", len(P.vias), " pistas:", len(P.pistas))
    print("DRC:", len(err), "errores"); [print("  ", e) for e in err[:40]]
    print("Abiertas:", len(abiertas)); [print("  ", a) for a in abiertas]
