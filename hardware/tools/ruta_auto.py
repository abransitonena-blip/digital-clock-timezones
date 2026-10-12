"""Ruta a mano asistida: une grupos de cobre de una red con un buscador de caminos (A*) sobre una rejilla de 0.2 mm,
2 capas y vías. Sirve para cerrar las pocas redes que el ruteador automático deja sin unir (largas y en zona densa).
Respeta: cobre de otras redes (holgura 0.2 mm), huecos y ranuras, Edge_Cuts, zonas sin cobre, 6.4 mm a la red (clase Red),
1.5 mm al bus aislado. Las zonas de relleno no se consideran (el relleno se aparta de las pistas); la verificación es el DRC.
"""
import heapq, math
import numpy as np
import pcbnew

G = 0.2          # paso de la rejilla, mm
ANCHO = 0.25     # ancho de pista
HOLG = 0.2       # holgura de la clase Default
VIA_D = 0.6
COSTO_VIA = 12.0


def _mm(v):
    return v / 1e6


def _loc(p):
    return _mm(p.x) - 100.0, _mm(p.y) - 100.0


class Rejilla:
    def __init__(self, W, H):
        self.nx, self.ny = int(W / G) + 1, int(H / G) + 1
        self.t = [np.zeros((self.ny, self.nx), bool) for _ in range(2)]     # pistas
        self.v = [np.zeros((self.ny, self.nx), bool) for _ in range(2)]     # vías

    def _caja(self, x0, y0, x1, y1):
        return (max(int(x0 / G), 0), min(int(math.ceil(x1 / G)) + 1, self.nx),
                max(int(y0 / G), 0), min(int(math.ceil(y1 / G)) + 1, self.ny))

    def sello_seg(self, cap, x1, y1, x2, y2, ancho_item, extra=0.0):
        """Marca lo que una pista/borde ocupa; r_p para pistas y r_v para vías."""
        for mask, rr in ((self.t[cap], ANCHO / 2), (self.v[cap], VIA_D / 2)):
            r = ancho_item / 2 + HOLG + rr + 0.03 + extra
            ia, ib, ja, jb = self._caja(min(x1, x2) - r, min(y1, y2) - r, max(x1, x2) + r, max(y1, y2) + r)
            if ia >= ib or ja >= jb:
                continue
            X, Y = np.meshgrid(np.arange(ia, ib) * G, np.arange(ja, jb) * G)
            dx, dy = x2 - x1, y2 - y1
            L2 = dx * dx + dy * dy
            u = np.zeros_like(X) if L2 == 0 else np.clip(((X - x1) * dx + (Y - y1) * dy) / L2, 0, 1)
            d = np.hypot(X - (x1 + u * dx), Y - (y1 + u * dy))
            mask[ja:jb, ia:ib] |= d <= r

    def sello_caja(self, cap, x0, y0, x1, y1, extra=0.0):
        for mask, rr in ((self.t[cap], ANCHO / 2), (self.v[cap], VIA_D / 2)):
            r = HOLG + rr + 0.03 + extra
            ia, ib, ja, jb = self._caja(x0 - r, y0 - r, x1 + r, y1 + r)
            mask[ja:jb, ia:ib] = True

    def sello_poligono(self, cap, pts, extra=0.0):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        ia, ib, ja, jb = self._caja(min(xs), min(ys), max(xs), max(ys))
        X, Y = np.meshgrid(np.arange(ia, ib) * G, np.arange(ja, jb) * G)
        dentro = np.zeros(X.shape, bool)
        n = len(pts)
        for i in range(n):
            (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % n]
            if ya == yb:
                continue
            cruza = ((ya > Y) != (yb > Y)) & (X < (xb - xa) * (Y - ya) / (yb - ya) + xa)
            dentro ^= cruza
        self.t[cap][ja:jb, ia:ib] |= dentro
        self.v[cap][ja:jb, ia:ib] |= dentro


def _capa(l):
    return 0 if l == pcbnew.F_Cu else 1


def construir(S, b, libre_red):
    """Rejilla con todo el cobre que no es de `libre_red` (nombre de red sin '/')."""
    R = Rejilla(S.W, S.H)
    rojas = set(S.NETCLASS.get("Red", (0, 0, []))[2])
    bus = set(S.NETCLASS.get("Bus", (0, 0, []))[2])

    def extra_de(nombre):
        n = nombre.lstrip("/")
        return 6.4 - HOLG if n in rojas else (1.5 - HOLG if n in bus else 0.0)

    for t in b.GetTracks():
        if t.GetNetname().lstrip("/") == libre_red:
            continue
        ex = extra_de(t.GetNetname())
        if t.GetClass() == "PCB_VIA":
            x, y = _loc(t.GetPosition())
            for cap in (0, 1):
                R.sello_seg(cap, x, y, x, y, _mm(t.GetWidth()), ex)
        else:
            cap = _capa(t.GetLayer())
            (x1, y1), (x2, y2) = _loc(t.GetStart()), _loc(t.GetEnd())
            R.sello_seg(cap, x1, y1, x2, y2, _mm(t.GetWidth()), ex)
    for p in b.GetPads():
        if p.GetNetname().lstrip("/") == libre_red:
            continue
        ex = extra_de(p.GetNetname())
        bb = p.GetBoundingBox()
        x0, y0 = _mm(bb.GetX()) - 100.0, _mm(bb.GetY()) - 100.0
        x1, y1 = x0 + _mm(bb.GetWidth()), y0 + _mm(bb.GetHeight())
        caps = [c for c, l in ((0, pcbnew.F_Cu), (1, pcbnew.B_Cu)) if p.IsOnLayer(l)]
        if p.GetDrillSize().x > 0:
            caps = [0, 1]
        for cap in caps:
            R.sello_caja(cap, x0, y0, x1, y1, ex)
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts:
            bb = d.GetBoundingBox()
            x0, y0 = _mm(bb.GetX()) - 100.0, _mm(bb.GetY()) - 100.0
            x1, y1 = x0 + _mm(bb.GetWidth()), y0 + _mm(bb.GetHeight())
            for cap in (0, 1):
                if d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
                    (xa, ya), (xb, yb) = _loc(d.GetStart()), _loc(d.GetEnd())
                    R.sello_seg(cap, xa, ya, xb, yb, 0.1, 0.35)
                else:
                    R.sello_caja(cap, x0, y0, x1, y1, 0.35)
    for pol in list(S.RUTEO_PROHIBIDO) + list(S.SIN_COBRE):
        for cap in (0, 1):
            R.sello_poligono(cap, pol)
    return R


def ruta(R, a, bpt):
    """a, bpt = (x, y, capa 0/1 o None). None = cualquier capa (una vía existente). Devuelve lista de (x, y, capa) por celda."""
    (ax, ay, ac), (bx, by, bc) = a, bpt
    sa, sb = (int(round(ax / G)), int(round(ay / G))), (int(round(bx / G)), int(round(by / G)))
    # libera un entorno de 0.5 mm en los extremos (el pad propio ya cumple la holgura con sus vecinos)
    libres = []
    for (ix, iy), caps in ((sa, (0, 1) if ac is None else (ac,)), (sb, (0, 1) if bc is None else (bc,))):
        for cap in caps:
            libres.append((cap, ix, iy))
    rad = 2
    guardado = []
    for cap, ix, iy in libres:
        for dy in range(-rad, rad + 1):
            for dx in range(-rad, rad + 1):
                x, y = ix + dx, iy + dy
                if 0 <= x < R.nx and 0 <= y < R.ny:
                    guardado.append((cap, x, y, R.t[cap][y, x], R.v[cap][y, x]))
                    R.t[cap][y, x] = False; R.v[cap][y, x] = False
    inicio = [(cap, sa[0], sa[1]) for cap in ((0, 1) if ac is None else (ac,))]
    meta = {(cap, sb[0], sb[1]) for cap in ((0, 1) if bc is None else (bc,))}
    h = lambda x, y: (lambda dx, dy: (dx + dy) + (1.414 - 2) * min(dx, dy))(abs(x - sb[0]), abs(y - sb[1]))
    INF = 1e18
    dist = {}
    padre = {}
    pq = []
    for s in inicio:
        dist[s] = 0.0
        heapq.heappush(pq, (h(s[1], s[2]), 0.0, s))
    fin = None
    pasos = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    while pq:
        f, g, s = heapq.heappop(pq)
        if g > dist.get(s, INF):
            continue
        if s in meta:
            fin = s; break
        cap, x, y = s
        for dx, dy, c in pasos:
            nx_, ny_ = x + dx, y + dy
            if not (0 <= nx_ < R.nx and 0 <= ny_ < R.ny) or R.t[cap][ny_, nx_]:
                continue
            if dx and dy and (R.t[cap][y, nx_] or R.t[cap][ny_, x]):
                continue
            t = (cap, nx_, ny_)
            ng = g + c
            if ng < dist.get(t, INF):
                dist[t] = ng; padre[t] = s
                heapq.heappush(pq, (ng + h(nx_, ny_), ng, t))
        o = 1 - cap
        if not R.v[0][y, x] and not R.v[1][y, x]:
            t = (o, x, y)
            ng = g + COSTO_VIA
            if ng < dist.get(t, INF):
                dist[t] = ng; padre[t] = s
                heapq.heappush(pq, (ng + h(x, y), ng, t))
    for cap, x, y, tt, vv in guardado:
        R.t[cap][y, x] = tt; R.v[cap][y, x] = vv
    if fin is None:
        return None
    cam = [fin]
    while cam[-1] in padre:
        cam.append(padre[cam[-1]])
    return cam[::-1]


def marcar(R, cam):
    """Agrega el camino encontrado a la rejilla (para que la siguiente red lo respete)."""
    for (c1, x1, y1), (c2, x2, y2) in zip(cam, cam[1:]):
        if c1 == c2:
            R.sello_seg(c1, x1 * G, y1 * G, x2 * G, y2 * G, ANCHO)
        else:
            for cap in (0, 1):
                R.sello_seg(cap, x1 * G, y1 * G, x1 * G, y1 * G, VIA_D)


def escribir(b, red, cam, extremos, capa_a, capa_b):
    """Pistas y vías en la placa. extremos = ((ax, ay), (bx, by)) coordenadas reales para el primer y el último tramo."""
    net = b.FindNet("/" + red)
    P = lambda x, y: pcbnew.VECTOR2I(int(round((100 + x) * 1e6)), int(round((100 + y) * 1e6)))
    pts = [(c, x * G, y * G) for c, x, y in cam]
    # tramos por capa, uniendo puntos colineales
    seg = []
    ini = 0
    for i in range(1, len(pts) + 1):
        if i == len(pts) or pts[i][0] != pts[ini][0]:
            seg.append(pts[ini:i]); ini = i
    n_seg = n_via = 0
    for k, s in enumerate(seg):
        ps = [(x, y) for _, x, y in s]
        if k == 0:
            ps = [extremos[0]] + ps
        if k == len(seg) - 1:
            ps = ps + [extremos[1]]
        sim = [ps[0]]
        for i in range(1, len(ps) - 1):
            a, c = sim[-1], ps[i + 1]
            if abs((ps[i][0] - a[0]) * (c[1] - ps[i][1]) - (ps[i][1] - a[1]) * (c[0] - ps[i][0])) > 1e-6:
                sim.append(ps[i])
        sim.append(ps[-1])
        lay = pcbnew.F_Cu if s[0][0] == 0 else pcbnew.B_Cu
        for (x1, y1), (x2, y2) in zip(sim, sim[1:]):
            if (x1, y1) == (x2, y2):
                continue
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(P(x1, y1)); t.SetEnd(P(x2, y2)); t.SetWidth(int(ANCHO * 1e6)); t.SetLayer(lay); t.SetNet(net)
            b.Add(t); n_seg += 1
    for (c1, x1, y1), (c2, x2, y2) in zip(cam, cam[1:]):
        if c1 != c2:
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(P(x1 * G, y1 * G)); v.SetWidth(int(VIA_D * 1e6)); v.SetDrill(int(0.3 * 1e6)); v.SetNet(net)
            b.Add(v); n_via += 1
    return n_seg, n_via


def rutas(S, b, lista):
    """lista = [(red, (x, y, capa|None), (x, y, capa|None))], capa 'F'/'B'/None."""
    cap = {"F": 0, "B": 1, None: None}
    for red, a, c in lista:
        R = construir(S, b, red)
        cam = ruta(R, (a[0], a[1], cap[a[2]]), (c[0], c[1], cap[c[2]]))
        if cam is None:
            print("ruta %s: SIN CAMINO %s -> %s" % (red, a, c)); continue
        s, v = escribir(b, red, cam, ((a[0], a[1]), (c[0], c[1])), cap[a[2]], cap[c[2]])
        print("ruta %s: %d pistas, %d vías, %.1f mm" % (red, s, v, len(cam) * G))
    print("limpieza: %d elementos quitados" % limpiar(b, {r for r, _, _ in lista}))


def limpiar(b, redes):
    """Quita las vías de esas redes que quedaron unidas por una sola cara y las pistas de menos de 0.05 mm sobrantes del ruteador."""
    quitar = []
    pistas = [t for t in b.GetTracks() if t.GetClass() != "PCB_VIA"]
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            if t.GetNetname().lstrip("/") not in redes:
                continue
            caras = set()
            for p in pistas:
                if p.GetNetCode() == t.GetNetCode() and (p.HitTest(t.GetPosition())):
                    caras.add(p.GetLayer())
            for p in b.GetPads():
                if p.GetNetCode() == t.GetNetCode() and p.HitTest(t.GetPosition()):
                    caras |= {pcbnew.F_Cu, pcbnew.B_Cu} if p.GetDrillSize().x > 0 else {l for l in (pcbnew.F_Cu, pcbnew.B_Cu) if p.IsOnLayer(l)}
            if len(caras) < 2:
                quitar.append(t)
        elif _mm(t.GetLength()) < 0.05:
            quitar.append(t)
    for t in quitar:
        b.Remove(t)
    return len(quitar)
