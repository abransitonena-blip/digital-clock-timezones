"""Ruteador de una sola capa (B.Cu) sobre rejilla, con A* y reintentos.

Pensado para PCB de una cara fabricadas por transferencia de tóner:
- pistas a 0°/45°/90°,
- separación mínima configurable (se añade un margen de seguridad),
- sin vías; si una red no puede rutearse, se informa para resolverla con
  un puente de alambre o reubicando componentes.
"""
import heapq, math, random
import numpy as np

GRID = 0.3175  # mm (1/80 de pulgada): todos los pads caen en esta rejilla

DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


class Pad:
    def __init__(self, ref, num, net, x, y, shape, w, h):
        self.ref, self.num, self.net = ref, num, net
        self.x, self.y, self.shape, self.w, self.h = x, y, shape, w, h

    def dist(self, X, Y):
        """Distancia (vectorizada) desde los puntos X, Y al borde de cobre del pad (0 dentro)."""
        dx, dy = np.abs(X - self.x), np.abs(Y - self.y)
        if self.shape == "circle":
            return np.maximum(0, np.hypot(dx, dy) - self.w / 2)
        if self.shape == "rect":
            ex, ey = np.maximum(0, dx - self.w / 2), np.maximum(0, dy - self.h / 2)
            return np.hypot(ex, ey)
        # óvalo (estadio)
        if self.w >= self.h:
            r, L = self.h / 2, (self.w - self.h) / 2
            return np.maximum(0, np.hypot(np.maximum(0, dx - L), dy) - r)
        r, L = self.w / 2, (self.h - self.w) / 2
        return np.maximum(0, np.hypot(dx, np.maximum(0, dy - L)) - r)

    def half_extent(self):
        return max(self.w, self.h) / 2


class Router:
    def __init__(self, W, H, pads, widths, clearance=0.6, margin=0.08, edge=1.0, keepouts=(), bodies=(),
                 jumper_lengths=(7.62, 10.16), jumper_cost=60.0, pad_d=2.4, pre=None):
        self.W, self.H = W, H
        self.nx, self.ny = int(round(W / GRID)) + 1, int(round(H / GRID)) + 1
        self.X, self.Y = np.meshgrid(np.arange(self.nx) * GRID, np.arange(self.ny) * GRID, indexing="ij")
        self.pads = pads
        self.widths = widths            # red -> ancho de pista
        self.clr = clearance + margin
        self.edge = edge
        self.keepouts = keepouts        # [(x, y, r)] círculos sin cobre (barrenos)
        self.nets = sorted(set(p.net for p in pads if p.net))
        self.tracks = {}                # red -> lista de polilíneas [(x, y), ...]
        self.jumpers = []               # (red, (x1, y1), (x2, y2))
        self.pre = pre or {}            # red -> polilíneas pre-ruteadas (buses)
        self.jl = [int(round(L / GRID)) for L in jumper_lengths]
        self.jcost = jumper_cost
        self.pad_d = pad_d
        # celdas cubiertas por cuerpos de componentes (un puente no puede pasar sobre ellos)
        self.body = np.zeros((self.nx, self.ny), bool)
        for (x0, y0, x1, y1) in bodies:
            self.body[(self.X > x0) & (self.X < x1) & (self.Y > y0) & (self.Y < y1)] = True

    # ---------------- ocupación ----------------
    def _reset(self):
        self.wclasses = sorted(set(self.widths.get(n, 0.8) for n in self.nets) | {self.pad_d})
        self.total = {w: np.zeros((self.nx, self.ny), np.int16) for w in self.wclasses}
        self.own = {w: {} for w in self.wclasses}
        self.hard = {w: np.zeros((self.nx, self.ny), bool) for w in self.wclasses}
        for w in self.wclasses:
            m = self.hard[w]
            e = self.edge + w / 2
            m[self.X < e] = True
            m[self.X > self.W - e] = True
            m[self.Y < e] = True
            m[self.Y > self.H - e] = True
            for (kx, ky, kr) in self.keepouts:
                m[np.hypot(self.X - kx, self.Y - ky) < kr + w / 2] = True
            for p in self.pads:
                self._cover(w, p.net or ("_" + p.ref + p.num), p.dist, p.x, p.y, p.half_extent())
        self.tracks = {}
        self.jumpers = []
        self._jp_done = set()
        self.fail_info = {}
        for net, polys in self.pre.items():
            w = self.widths.get(net, 0.8)
            for pl in polys:
                for a, b in zip(pl[:-1], pl[1:]):
                    self._add_segment(net, a, b, w)

    def _window(self, x, y, R):
        i0, i1 = max(0, int((x - R) / GRID) - 1), min(self.nx, int((x + R) / GRID) + 2)
        j0, j1 = max(0, int((y - R) / GRID) - 1), min(self.ny, int((y + R) / GRID) + 2)
        return i0, i1, j0, j1

    def _cover(self, w, net, distf, cx, cy, ext, extra=0.0):
        R = ext + w / 2 + self.clr + extra + GRID
        i0, i1, j0, j1 = self._window(cx, cy, R)
        X, Y = self.X[i0:i1, j0:j1], self.Y[i0:i1, j0:j1]
        m = distf(X, Y) < (w / 2 + self.clr + extra)
        own = self.own[w].setdefault(net, np.zeros((self.nx, self.ny), bool))
        sub = own[i0:i1, j0:j1]
        new = m & ~sub
        self.total[w][i0:i1, j0:j1] += new
        sub |= m

    def _add_segment(self, net, a, b, tw):
        (x1, y1), (x2, y2) = a, b

        def dseg(X, Y):
            vx, vy = x2 - x1, y2 - y1
            L2 = vx * vx + vy * vy
            if L2 == 0:
                return np.maximum(0, np.hypot(X - x1, Y - y1) - tw / 2)
            t = np.clip(((X - x1) * vx + (Y - y1) * vy) / L2, 0, 1)
            return np.maximum(0, np.hypot(X - (x1 + t * vx), Y - (y1 + t * vy)) - tw / 2)
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        ext = math.hypot(x2 - x1, y2 - y1) / 2 + tw / 2
        for w in self.wclasses:
            self._cover(w, net, dseg, cx, cy, ext)

    def _cover_pad(self, net, x, y):
        key = (net, round(x, 3), round(y, 3))
        if key in self._jp_done:
            return
        self._jp_done.add(key)
        r = self.pad_d / 2
        f = lambda X, Y: np.maximum(0, np.hypot(X - x, Y - y) - r)
        for w in self.wclasses:
            self._cover(w, net, f, x, y, r)

    def blocked(self, net, w):
        own = self.own[w].get(net)
        b = self.total[w] > 0
        if own is not None:
            b = (self.total[w] - own.astype(np.int16)) > 0
        return b | self.hard[w]

    # ---------------- A* ----------------
    def _astar(self, starts, targets, blk, bend=0.6, blkpad=None):
        nx, ny = self.nx, self.ny
        tlist = np.argwhere(targets)
        if len(tlist) == 0:
            return None
        tx, ty = tlist[:, 0], tlist[:, 1]
        # heurística: distancia octil al objetivo más cercano (muestra acotada)
        if len(tlist) > 400:
            idx = np.linspace(0, len(tlist) - 1, 400).astype(int)
            tx, ty = tx[idx], ty[idx]

        def h(i, j):
            dx, dy = np.abs(tx - i), np.abs(ty - j)
            return float(np.min(np.maximum(dx, dy) + 0.4142 * np.minimum(dx, dy)))
        openh = []
        g = {}
        came = {}
        for (i, j) in starts:
            for d in range(8):
                g[(i, j, d)] = 0.0
                heapq.heappush(openh, (h(i, j), 0.0, i, j, d))
                came[(i, j, d)] = None
        seen = set()
        while openh:
            f, gc, i, j, d = heapq.heappop(openh)
            key = (i, j, d)
            if key in seen:
                continue
            seen.add(key)
            if targets[i, j]:
                path = []
                k = key
                while k is not None:
                    path.append((k[0], k[1], k[2] >= 8))
                    k = came[k]
                return path[::-1]
            for nd, (di, dj) in enumerate(DIRS):
                ni, nj = i + di, j + dj
                if ni < 0 or nj < 0 or ni >= nx or nj >= ny or blk[ni, nj]:
                    continue
                if di and dj and (blk[i + di, j] or blk[i, j + dj]):
                    continue  # no cortar esquinas en diagonal
                step = 1.4142 if (di and dj) else 1.0
                turn = 0.0
                if came[key] is not None and nd != d % 8:
                    a = DIRS[d % 8]
                    dot = a[0] * di + a[1] * dj
                    turn = bend if dot > 0 else bend * 4
                ng = gc + step + turn
                nk = (ni, nj, nd)
                if ng < g.get(nk, 1e18):
                    g[nk] = ng
                    came[nk] = key
                    heapq.heappush(openh, (ng + h(ni, nj), ng, ni, nj, nd))
            # saltos con puente de alambre (solo ortogonales)
            if blkpad is not None and not blkpad[i, j]:
                for nd in range(4):
                    di, dj = DIRS[nd]
                    for L in self.jl:
                        ni, nj = i + di * L, j + dj * L
                        if ni < 0 or nj < 0 or ni >= nx or nj >= ny or blkpad[ni, nj]:
                            continue
                        if di:
                            a, b = sorted((i, ni))
                            if self.body[a + 4:b - 3, j].any():
                                continue
                        else:
                            a, b = sorted((j, nj))
                            if self.body[i, a + 4:b - 3].any():
                                continue
                        ng = gc + L + self.jcost
                        nk = (ni, nj, nd + 8)
                        if ng < g.get(nk, 1e18):
                            g[nk] = ng
                            came[nk] = key
                            heapq.heappush(openh, (ng + h(ni, nj), ng, ni, nj, nd + 8))
        return None

    def cell(self, x, y):
        return int(round(x / GRID)), int(round(y / GRID))

    def route_net(self, net):
        w = self.widths.get(net, 0.8)
        pads = [p for p in self.pads if p.net == net]
        if len(pads) < 2 and net not in self.pre:
            return True
        blk = self.blocked(net, w)
        blkpad = self.blocked(net, self.pad_d) if self.jcost is not None else None
        tgt = np.zeros((self.nx, self.ny), bool)
        polylines = [list(map(tuple, pl)) for pl in self.pre.get(net, [])]
        if polylines:
            for pl in polylines:
                for (x1, y1), (x2, y2) in zip(pl[:-1], pl[1:]):
                    n = int(max(abs(x2 - x1), abs(y2 - y1)) / (GRID / 2)) + 1
                    for k in range(n + 1):
                        t = k / n
                        tgt[self.cell(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)] = True
            conn = []
            rest = list(pads)
        else:
            conn = [pads[0]]
            rest = pads[1:]
            i, j = self.cell(pads[0].x, pads[0].y)
            tgt[i, j] = True
        while rest:
            if conn:
                rest.sort(key=lambda p: min(math.hypot(p.x - q.x, p.y - q.y) for q in conn))
            p = rest.pop(0)
            s = self.cell(p.x, p.y)
            if tgt[s]:
                conn.append(p)
                continue
            path = self._astar([s], tgt, blk, blkpad=blkpad)
            if path is None:
                self.fail_info[net] = "%s.%s (%.2f, %.2f)" % (p.ref, p.num, p.x, p.y)
                self.tracks[net] = polylines
                return False
            # dividir en tramos de cobre separados por puentes
            segs, cur = [], [path[0][:2]]
            for (a, b, jump) in path[1:]:
                if jump:
                    segs.append(cur)
                    j0 = cur[-1]
                    self.jumpers.append((net, (j0[0] * GRID, j0[1] * GRID), (a * GRID, b * GRID)))
                    cur = [(a, b)]
                else:
                    cur.append((a, b))
            segs.append(cur)
            for cells in segs:
                pts = [(a * GRID, b * GRID) for a, b in cells]
                poly = [pts[0]]
                for k in range(1, len(pts) - 1):
                    (x0, y0), (x1, y1), (x2, y2) = pts[k - 1], pts[k], pts[k + 1]
                    if abs((x1 - x0) * (y2 - y1) - (y1 - y0) * (x2 - x1)) > 1e-9:
                        poly.append(pts[k])
                poly.append(pts[-1])
                if len(poly) > 1:
                    polylines.append(poly)
                for a, b in zip(poly[:-1], poly[1:]):
                    self._add_segment(net, a, b, w)
            for (a, b, jump) in path:
                tgt[a, b] = True
            for (_n, p1, p2) in self.jumpers:
                if _n == net:
                    for (px, py) in (p1, p2):
                        self._cover_pad(net, px, py)
            # la ocupación propia cambió; los bloqueos de otras redes no
            conn.append(p)
            ci, cj = self.cell(p.x, p.y)
            tgt[ci, cj] = True
        self.tracks[net] = polylines
        return True

    def route_all(self, order=None, iters=30, seed=1, log=print, first=(), last=()):
        rnd = random.Random(seed)
        first = [n for n in first if n in self.nets]
        last = [n for n in last if n in self.nets]
        if order is None:
            def span(n):
                ps = [p for p in self.pads if p.net == n]
                xs, ys = [p.x for p in ps], [p.y for p in ps]
                return (max(xs) - min(xs)) + (max(ys) - min(ys))
            order = first + sorted([n for n in self.nets if n not in first and n not in last], key=span) + last
        best = None
        for it in range(iters):
            self._reset()
            failed = []
            for n in order:
                if not self.route_net(n):
                    failed.append(n)
            L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for ps in self.tracks.values() for pl in ps
                    for a, b in zip(pl[:-1], pl[1:]))
            score = (len(failed), len(self.jumpers), L)
            log("iter %d: %d sin rutear %s, %d puentes, %.0f mm" % (it, len(failed), failed, len(self.jumpers), L))
            log("   fallas: %s" % self.fail_info)
            if best is None or score < best[0]:
                best = (score, failed, dict(self.tracks), list(self.jumpers), list(order))
            if best[0][0] == 0 and best[0][1] == 0:
                break
            # búsqueda local: partir del mejor orden y adelantar redes problemáticas
            order = list(best[4])
            nf = len(first)
            head, tail = order[:nf], order[nf:]
            probl = list(best[1]) + [j[0] for j in best[3]]
            for n in set(probl):
                if n in tail and rnd.random() < 0.8:
                    tail.remove(n)
                    tail.insert(rnd.randrange(0, max(1, len(tail) // 3)), n)
            for _ in range(rnd.randrange(0, 4)):
                a, b = rnd.randrange(len(tail)), rnd.randrange(len(tail))
                tail[a], tail[b] = tail[b], tail[a]
            if head and rnd.random() < 0.3:
                a, b = rnd.randrange(len(head)), rnd.randrange(len(head))
                head[a], head[b] = head[b], head[a]
            order = head + tail
        score, failed, self.tracks, self.jumpers, order = best
        return failed, order


class NegotiatedRouter(Router):
    """Ruteo por negociación de congestión (estilo PathFinder).

    Los pads de otras redes, bordes, barrenos y buses pre-ruteados son bloqueos duros;
    las pistas de otras redes son un costo que crece en cada iteración hasta que
    ninguna red se superpone con otra.
    """

    def _reset_pf(self):
        self._reset()
        # separar: 'hardtot' = pads + pre-ruteo (duro); pistas negociables aparte
        self.hardtot = {w: self.total[w].copy() for w in self.wclasses}
        self.hardown = {w: {n: m.copy() for n, m in self.own[w].items()} for w in self.wclasses}
        self.soft = {w: np.zeros((self.nx, self.ny), np.int16) for w in self.wclasses}
        self.softown = {w: {} for w in self.wclasses}
        self.routes = {}          # red -> (polylines, jumpers, celdas centrales)
        self.hist = np.zeros((self.nx, self.ny), np.float32)

    def _soft_cover(self, net, sign, polylines, jumpers):
        for w in self.wclasses:
            m = self.softown[w].setdefault(net, np.zeros((self.nx, self.ny), np.int16))
        # reconstruir la máscara blanda de la red desde cero
        for w in self.wclasses:
            self.soft[w] -= self.softown[w][net]
            self.softown[w][net][:] = 0
        if sign > 0:
            saved_total, saved_own = self.total, self.own
            self.total = {w: np.zeros((self.nx, self.ny), np.int16) for w in self.wclasses}
            self.own = {w: {} for w in self.wclasses}
            wd = self.widths.get(net, 0.8)
            for pl in polylines:
                for a, b in zip(pl[:-1], pl[1:]):
                    self._add_segment(net, a, b, wd)
            for (_n, p1, p2) in jumpers:
                for (px, py) in (p1, p2):
                    r = self.pad_d / 2
                    f = lambda X, Y, px=px, py=py: np.maximum(0, np.hypot(X - px, Y - py) - r)
                    for w in self.wclasses:
                        self._cover(w, net, f, px, py, r)
            for w in self.wclasses:
                m = self.own[w].get(net)
                if m is not None:
                    self.softown[w][net][:] = m
                    self.soft[w] += self.softown[w][net]
            self.total, self.own = saved_total, saved_own

    def _hard_blocked(self, net, w):
        own = self.hardown[w].get(net)
        b = self.hardtot[w] > 0
        if own is not None:
            b = (self.hardtot[w] - own.astype(np.int16)) > 0
        return b | self.hard[w]

    def _astar_cost(self, starts, targets, blk, cost, blkpad=None, bend=0.6):
        nx, ny = self.nx, self.ny
        tlist = np.argwhere(targets)
        tx, ty = tlist[:, 0], tlist[:, 1]
        if len(tlist) > 400:
            idx = np.linspace(0, len(tlist) - 1, 400).astype(int)
            tx, ty = tx[idx], ty[idx]

        def h(i, j):
            dx, dy = np.abs(tx - i), np.abs(ty - j)
            return float(np.min(np.maximum(dx, dy) + 0.4142 * np.minimum(dx, dy)))
        openh, g, came, seen = [], {}, {}, set()
        for (i, j) in starts:
            for d in range(8):
                g[(i, j, d)] = 0.0
                came[(i, j, d)] = None
                heapq.heappush(openh, (h(i, j), 0.0, i, j, d))
        while openh:
            f, gc, i, j, d = heapq.heappop(openh)
            key = (i, j, d)
            if key in seen:
                continue
            seen.add(key)
            if targets[i, j]:
                path, k = [], key
                while k is not None:
                    path.append((k[0], k[1], k[2] >= 8))
                    k = came[k]
                return path[::-1]
            for nd, (di, dj) in enumerate(DIRS):
                ni, nj = i + di, j + dj
                if ni < 0 or nj < 0 or ni >= nx or nj >= ny or blk[ni, nj]:
                    continue
                if di and dj and (blk[i + di, j] or blk[i, j + dj]):
                    continue
                step = (1.4142 if (di and dj) else 1.0) * cost[ni, nj]
                turn = 0.0
                if came[key] is not None and nd != d % 8:
                    a = DIRS[d % 8]
                    turn = bend if (a[0] * di + a[1] * dj) > 0 else bend * 4
                ng = gc + step + turn
                nk = (ni, nj, nd)
                if ng < g.get(nk, 1e18):
                    g[nk] = ng
                    came[nk] = key
                    heapq.heappush(openh, (ng + h(ni, nj), ng, ni, nj, nd))
            recent = False
            if blkpad is not None and not blkpad[i, j] and d < 8:
                k2, steps = came.get(key), 0
                while k2 is not None and steps < 16:
                    if k2[2] >= 8 or came.get(k2) is None:
                        if abs(k2[0] - i) + abs(k2[1] - j) < 16:   # < ~5 mm de otro extremo de puente
                            recent = True
                        break
                    k2, steps = came.get(k2), steps + 1
            if blkpad is not None and not blkpad[i, j] and d < 8 and not recent:
                for nd in range(4):
                    di, dj = DIRS[nd]
                    for L in self.jl:
                        ni, nj = i + di * L, j + dj * L
                        if ni < 0 or nj < 0 or ni >= nx or nj >= ny or blkpad[ni, nj]:
                            continue
                        if di:
                            a0, a1 = sorted((i, ni))
                            if self.nearhole[a0 + 5:a1 - 4, j].any():
                                continue
                        else:
                            b0, b1 = sorted((j, nj))
                            if self.nearhole[i, b0 + 5:b1 - 4].any():
                                continue
                        if targets[ni, nj] and not targets[i, j]:
                            pass
                        ng = gc + L + self.jcost * cost[ni, nj] * cost[i, j]
                        nk = (ni, nj, nd + 8)
                        if ng < g.get(nk, 1e18):
                            g[nk] = ng
                            came[nk] = key
                            heapq.heappush(openh, (ng + h(ni, nj), ng, ni, nj, nd + 8))
        return None

    def _route_net_pf(self, net, pres):
        w = self.widths.get(net, 0.8)
        pads = [p for p in self.pads if p.net == net]
        if len(pads) < 2 and net not in self.pre:
            return True
        blk = self._hard_blocked(net, w)
        blkpad = self._hard_blocked(net, self.pad_d)
        # blando: pistas de otras redes (incluye pads de puentes de otras redes)
        own = self.softown[w].get(net)
        other = self.soft[w] - (own if own is not None else 0)
        otherp = self.soft[self.pad_d] - (self.softown[self.pad_d].get(net, 0))
        blkpad = blkpad | (otherp > 0) | self.nopad
        cost = (1.0 + self.hist) * (1.0 + pres * (other > 0))
        tgt = np.zeros((self.nx, self.ny), bool)
        polylines = [list(map(tuple, pl)) for pl in self.pre.get(net, [])]
        if polylines:
            for pl in polylines:
                for (x1, y1), (x2, y2) in zip(pl[:-1], pl[1:]):
                    n = int(max(abs(x2 - x1), abs(y2 - y1)) / (GRID / 2)) + 1
                    for k in range(n + 1):
                        t = k / n
                        tgt[self.cell(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)] = True
            conn, rest = [], list(pads)
        else:
            conn, rest = [pads[0]], pads[1:]
            tgt[self.cell(pads[0].x, pads[0].y)] = True
        newpolys, jumpers, cells = [], [], []
        while rest:
            if conn:
                rest.sort(key=lambda p: min(math.hypot(p.x - q.x, p.y - q.y) for q in conn))
            p = rest.pop(0)
            s = self.cell(p.x, p.y)
            if tgt[s]:
                conn.append(p)
                continue
            path = self._astar_cost([s], tgt, blk, cost, blkpad=blkpad)
            if path is None:
                self.fail_info[net] = "%s.%s" % (p.ref, p.num)
                return False
            segs, cur = [], [path[0][:2]]
            for (a, b, jump) in path[1:]:
                if jump:
                    segs.append(cur)
                    j0 = cur[-1]
                    jumpers.append((net, (j0[0] * GRID, j0[1] * GRID), (a * GRID, b * GRID)))
                    cur = [(a, b)]
                else:
                    cur.append((a, b))
            segs.append(cur)
            for cl in segs:
                pts = [(a * GRID, b * GRID) for a, b in cl]
                poly = [pts[0]]
                for k in range(1, len(pts) - 1):
                    (x0, y0), (x1, y1), (x2, y2) = pts[k - 1], pts[k], pts[k + 1]
                    if abs((x1 - x0) * (y2 - y1) - (y1 - y0) * (x2 - x1)) > 1e-9:
                        poly.append(pts[k])
                poly.append(pts[-1])
                if len(poly) > 1:
                    newpolys.append(poly)
            for (a, b, jump) in path:
                tgt[a, b] = True
                cells.append((a, b))
            conn.append(p)
        self.routes[net] = (newpolys, jumpers, cells)
        self._soft_cover(net, +1, newpolys, jumpers)
        return True

    def route_negotiated(self, iters=40, order=None, log=print, first=(), last=()):
        self._reset_pf()
        # los extremos de un puente no pueden caer sobre (ni junto a) otro pad: cada uno necesita su barreno
        self.nopad = np.zeros((self.nx, self.ny), bool)
        self.nearhole = np.zeros((self.nx, self.ny), bool)
        for p in self.pads:
            d = np.hypot(self.X - p.x, self.Y - p.y)
            self.nopad |= d < (max(p.w, p.h) / 2 + self.pad_d / 2 + 0.3)
            # el alambre del puente no puede pasar por encima de un pad/pata (riesgo de corto)
            self.nearhole |= d < float(__import__("os").environ.get("NEARHOLE", "1.2"))
        def span(n):
            ps = [p for p in self.pads if p.net == n]
            xs, ys = [p.x for p in ps], [p.y for p in ps]
            return (max(xs) - min(xs)) + (max(ys) - min(ys)) if ps else 0
        order = order or ([n for n in first if n in self.nets] +
                          sorted([n for n in self.nets if n not in first and n not in last], key=span) +
                          [n for n in last if n in self.nets])
        pres = 0.5
        best = None
        for it in range(iters):
            self.fail_info = {}
            failed = []
            for n in order:
                if n in self.routes:
                    self._soft_cover(n, -1, [], [])
                    del self.routes[n]
                if not self._route_net_pf(n, pres):
                    failed.append(n)
            # conflictos: celdas centrales de una red cubiertas por pistas de otra
            conflicts = 0
            over = np.zeros((self.nx, self.ny), bool)
            for n, (polys, jumps, cells) in self.routes.items():
                w = self.widths.get(n, 0.8)
                own = self.softown[w].get(n)
                other = self.soft[w] - (own if own is not None else 0)
                for (a, b) in cells:
                    if other[a, b] > 0:
                        over[a, b] = True
                        conflicts += 1
            nj = sum(len(r[1]) for r in self.routes.values())
            log("PF iter %d: %d sin rutear %s, %d conflictos, %d puentes" % (it, len(failed), failed, conflicts, nj))
            if not failed and conflicts == 0:
                score = (0, nj)
                if best is None or score < best[0]:
                    best = (score, {n: r for n, r in self.routes.items()})
                    log("   * mejor hasta ahora: %d puentes" % nj)
                if nj <= int(__import__("os").environ.get("PF_TARGET_J", "0")):
                    break
                # presión sobre los puentes: penalizar las pistas ajenas que obligan a saltar
                for n, (polys, jumps, cells) in self.routes.items():
                    for (_n, (x1, y1), (x2, y2)) in jumps:
                        i1, j1 = self.cell(x1, y1)
                        i2, j2 = self.cell(x2, y2)
                        a0, a1 = sorted((i1, i2))
                        b0, b1 = sorted((j1, j2))
                        span = np.zeros((self.nx, self.ny), bool)
                        span[max(0, a0 - 2):a1 + 3, max(0, b0 - 2):b1 + 3] = True
                        w = self.widths.get(n, 0.8)
                        own = self.softown[w].get(n)
                        other = self.soft[w] - (own if own is not None else 0)
                        self.hist[span & (other > 0)] += 0.7
                self.jcost *= 1.15
            self.hist[over] += 1.0
            # difundir la historia a las celdas vecinas para abrir canales
            pres *= 1.6
        if best is None:
            best = ((len(failed), 0), {n: r for n, r in self.routes.items()})
        self.tracks = {n: [list(map(tuple, pl)) for pl in self.pre.get(n, [])] + r[0] for n, r in best[1].items()}
        for n, pls in self.pre.items():
            if n not in self.tracks:
                self.tracks[n] = [list(map(tuple, pl)) for pl in pls]
        self.jumpers = [j for r in best[1].values() for j in r[1]]
        return ([] if best[0][0] == 0 else failed), order
