"""Genera la PCB (.kicad_pcb) a partir de design.py + placement.py y la rutea.

Uso (dentro del contenedor de KiCad 9):
    python3 gen/pcbgen.py kicad/ControladorFlechas.kicad_pcb
"""
import os, sys, json, math, uuid
sys.path.insert(0, os.path.dirname(__file__))
import pcbnew
import design as DZ
import placement as PL
from router import Router, NegotiatedRouter, Pad, GRID

HERE = os.path.dirname(os.path.abspath(__file__))
LIBDIR = os.path.join(HERE, "..", "kicad", DZ.LIB + ".pretty")
OX, OY = 50.0, 50.0          # origen de la placa en la hoja
NS = uuid.UUID("0b6a6d2e-5a0f-4f53-9d6e-3f1a2b4c5d6e")

SIG_W, PWR_W, CLR = 0.8, 1.2, 0.6


def mm(v):
    return pcbnew.FromMM(v)


def P(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


def sym_uuid(ref):
    return str(uuid.uuid5(NS, ref))


def kname(n):
    """Nombre de red en KiCad: las etiquetas locales del esquema llevan prefijo '/'."""
    return n if (n in DZ.POWER or n.startswith("/")) else "/" + n


def dname(n):
    return n[1:] if n.startswith("/") else n


def track_width(net):
    import re
    base = re.sub(r"_(W|I)\d+$", "", dname(net))
    return PWR_W if base in DZ.POWER_NETS_W else SIG_W


def jumper_pos(p1, p2):
    (x1, y1), (x2, y2) = p1, p2
    if abs(y2 - y1) < 1e-6:
        return (x1, y1, 0) if x2 > x1 else (x1, y1, 180)
    return (x1, y1, 270) if y2 > y1 else (x1, y1, 90)


def build(outpath, route=True, iters=int(os.environ.get("ITERS", "40"))):
    rr = os.path.join(HERE, "route_result.json")
    if route:
        # 1) placa sin puentes ni redes separadas para rutear
        import importlib
        os.environ["NO_JUMPERS"] = "1"
        importlib.reload(DZ)
        del os.environ["NO_JUMPERS"]
        comps = [c for c in DZ.C if not c["ref"].startswith("W")]
        board, fps, netobj = make_board(comps, {})
        failed, tracks, jumpers, order = do_route(board, fps, iters)
        tracks, netsplit = split_nets(fps, tracks, jumpers)
        json.dump({"failed": failed, "order": order, "tracks": tracks, "jumpers": jumpers, "netsplit": netsplit},
                  open(rr, "w"), indent=0)
        import importlib
        importlib.reload(DZ)
    if os.environ.get("RESPLIT"):
        d0 = json.load(open(rr))
        import importlib
        os.environ["NO_JUMPERS"] = "1"
        importlib.reload(DZ)
        del os.environ["NO_JUMPERS"]
        comps = [c for c in DZ.C if not c["ref"].startswith("W")]
        board, fps, netobj = make_board(comps, {})
        merged = {}
        for k, v in d0["tracks"].items():
            merged.setdefault(kname(__import__("re").sub(r"_(W|I)\d+$", "", dname(k))), []).extend(v)
        d0["tracks"], d0["netsplit"] = split_nets(fps, merged, d0["jumpers"])
        json.dump(d0, open(rr, "w"), indent=0)
        import importlib
        importlib.reload(DZ)
    data = json.load(open(rr))
    jpos = {"W%d" % (k + 1): jumper_pos(p1, p2) for k, (n, p1, p2) in enumerate(data["jumpers"])}
    board, fps, netobj = make_board(DZ.C, jpos)
    for net, polys in data["tracks"].items():
        for poly in polys:
            for a, b in zip(poly[:-1], poly[1:]):
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(P(*a))
                t.SetEnd(P(*b))
                t.SetWidth(mm(track_width(net)))
                t.SetLayer(pcbnew.B_Cu)
                t.SetNet(netobj[net])
                board.Add(t)
    prune_dangling(board)
    split_tjunctions(board)
    board.Save(outpath)
    return data["failed"]


def split_tjunctions(board):
    """Parte una pista donde otra de la misma red termina sobre su eje (unión en T)."""
    import math
    changed = True
    while changed:
        changed = False
        tracks = list(board.GetTracks())
        ends = [(t.GetNetCode(), p) for t in tracks for p in (t.GetStart(), t.GetEnd())]
        for t in tracks:
            a, b = t.GetStart(), t.GetEnd()
            ax, ay, bx, by = a.x, a.y, b.x, b.y
            L2 = (bx - ax) ** 2 + (by - ay) ** 2
            if L2 == 0:
                continue
            for net, p in ends:
                if net != t.GetNetCode():
                    continue
                u = ((p.x - ax) * (bx - ax) + (p.y - ay) * (by - ay)) / L2
                if u <= 1e-6 or u >= 1 - 1e-6:
                    continue
                qx, qy = ax + u * (bx - ax), ay + u * (by - ay)
                if math.hypot(p.x - qx, p.y - qy) < 2000:      # 2 µm
                    t2 = pcbnew.PCB_TRACK(board)
                    t2.SetStart(p)
                    t2.SetEnd(b)
                    t2.SetWidth(t.GetWidth())
                    t2.SetLayer(t.GetLayer())
                    t2.SetNet(t.GetNet())
                    t.SetEnd(p)
                    board.Add(t2)
                    changed = True
                    break
            if changed:
                break


def prune_dangling(board):
    """Elimina tramos de pista con un extremo sin conectar (restos del ruteo)."""
    removed = 0
    while True:
        tracks = list(board.GetTracks())
        pads = [p for f in board.GetFootprints() for p in f.Pads()]
        victims = []
        for t in tracks:
            for pt in (t.GetStart(), t.GetEnd()):
                ok = False
                for p in pads:
                    if p.GetNetCode() == t.GetNetCode() and p.HitTest(pt):
                        ok = True
                        break
                if not ok:
                    for t2 in tracks:
                        if t2 is not t and t2.GetNetCode() == t.GetNetCode() and t2.HitTest(pt, 0):
                            ok = True
                            break
                if not ok:
                    victims.append(t)
                    break
        if not victims:
            break
        for t in victims:
            board.Remove(t)
            removed += 1
    if removed:
        print("tramos colgantes eliminados:", removed)


def positions():
    f = os.path.join(HERE, "placement_final.json")
    if os.path.exists(f) and not os.environ.get("RAW_PLACEMENT"):
        pos = dict(PL.POS)
        pos.update({k: tuple(v) for k, v in json.load(open(f)).items()})
        return pos
    return PL.POS


def make_board(comps, jpos):
    POSN = positions()
    board = pcbnew.BOARD()
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    # redes
    netobj = {}
    for n in sorted(DZ.nets().keys()):
        ni = pcbnew.NETINFO_ITEM(board, kname(n))
        board.Add(ni)
        netobj[n] = ni
        netobj[kname(n)] = ni
    # contorno
    W, H = PL.W, PL.H
    pts = [(0, 0), (W, 0), (W, H), (0, H)]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(P(*a))
        s.SetEnd(P(*b))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.15))
        board.Add(s)
    # huellas
    fps = {}
    for c in comps:
        ref = c["ref"]
        x, y, r = jpos[ref] if ref in jpos else POSN[ref]
        fp = pcbnew.FootprintLoad(LIBDIR, c["fp"])
        fp.SetFPID(pcbnew.LIB_ID(DZ.LIB, c["fp"]))
        fp.SetReference(ref)
        fp.SetValue(c["val"])
        fp.SetPosition(P(x, y))
        fp.SetOrientationDegrees(r)
        fp.SetPath(pcbnew.KIID_PATH("/" + sym_uuid(ref)))
        if c["dnp"]:
            fp.SetDNP(True)
        board.Add(fp)
        for pad in fp.Pads():
            n = c["pins"].get(pad.GetNumber())
            if n:
                pad.SetNet(netobj[n])
            elif (ref, pad.GetNumber()) in DZ.NC_PIN_NAMES:
                nn = "unconnected-(%s-%s-Pad%s)" % (ref, DZ.NC_PIN_NAMES[(ref, pad.GetNumber())], pad.GetNumber())
                ni = pcbnew.NETINFO_ITEM(board, nn)
                board.Add(ni)
                pad.SetNet(ni)
        fps[ref] = fp
    # ajustes de la serigrafía de referencias
    for ref, (dx, dy, ang) in PL.REF_POS.items():
        fp = fps[ref]
        t = fp.Reference()
        t.SetPosition(P(POSN[ref][0] + dx, POSN[ref][1] + dy))
        t.SetTextAngleDegrees(ang)
    for fp in fps.values():
        fp.Value().SetVisible(False) if hasattr(fp.Value(), "SetVisible") else None
    # textos de serigrafía
    for (s, x, y, size, ang, layer) in PL.TEXTS:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(s)
        t.SetPosition(P(x, y))
        t.SetLayer(pcbnew.F_SilkS if layer == "F.SilkS" else pcbnew.B_Cu)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
        t.SetTextThickness(mm(max(0.15, size * 0.15)))
        t.SetTextAngleDegrees(ang)
        if layer == "B.Cu":
            t.SetMirrored(True)
        board.Add(t)
    for (x1, y1, x2, y2, wdt) in PL.LINES:
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(P(x1, y1))
        s.SetEnd(P(x2, y2))
        s.SetLayer(pcbnew.F_SilkS)
        s.SetWidth(mm(wdt))
        board.Add(s)

    return board, fps, netobj


def split_nets(fps, tracks, jumpers):
    """Separa en redes distintas los tramos de cobre unidos solo por puentes W."""
    import numpy as np
    from router import Pad as RP
    jnets = set(dname(n) for n, a, b in jumpers)
    pads = {}
    for ref, fp in fps.items():
        ang = round(fp.GetOrientationDegrees()) % 180
        for p in fp.Pads():
            n = dname(p.GetNetname())
            if n in jnets:
                sz = p.GetSize(pcbnew.B_Cu)
                w, h = pcbnew.ToMM(sz.x), pcbnew.ToMM(sz.y)
                if ang == 90:
                    w, h = h, w
                shp = {pcbnew.PAD_SHAPE_CIRCLE: "circle", pcbnew.PAD_SHAPE_RECTANGLE: "rect",
                       pcbnew.PAD_SHAPE_OVAL: "oval"}.get(p.GetShape(pcbnew.B_Cu), "rect")
                pads.setdefault(n, []).append(("%s.%s" % (ref, p.GetNumber()),
                                               RP(ref, p.GetNumber(), n, pcbnew.ToMM(p.GetPosition().x) - OX,
                                                  pcbnew.ToMM(p.GetPosition().y) - OY, shp, w, h)))
    newtracks, netsplit = {}, {}
    for k, (n, p1, p2) in enumerate(jumpers):
        for q, pt in ((1, p1), (2, p2)):
            pads.setdefault(n, []).append(("W%d.%d" % (k + 1, q), RP("W", "", n, pt[0], pt[1], "circle", 2.4, 2.4)))
    for net, polys in tracks.items():
        n = dname(net)
        if n not in jnets:
            newtracks[net] = polys
            continue
        segs = [(a, b) for pl in polys for a, b in zip(pl[:-1], pl[1:])]
        items = len(segs) + len(pads[n])
        par = list(range(items))

        def f(a):
            while par[a] != a:
                par[a] = par[par[a]]
                a = par[a]
            return a

        def pts(s, m=40):
            (x1, y1), (x2, y2) = s
            t = np.linspace(0, 1, m)
            return x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
        w = track_width(n)
        for i in range(len(segs)):
            X, Y = pts(segs[i])
            for j in range(i + 1, len(segs)):
                (a, b), (c, d) = segs[j]
                vx, vy = c - a, d - b
                L2 = vx * vx + vy * vy or 1e-12
                t = np.clip(((X - a) * vx + (Y - b) * vy) / L2, 0, 1)
                if float(np.min(np.hypot(X - (a + t * vx), Y - (b + t * vy)))) <= w + 1e-3:
                    par[f(i)] = f(j)
        for k, (nm, pd) in enumerate(pads[n]):
            for i, sg in enumerate(segs):
                X, Y = pts(sg)
                if float(np.min(pd.dist(X, Y))) <= w / 2 + 1e-3:
                    par[f(len(segs) + k)] = f(i)
        groups = {}
        for k, (nm, pd) in enumerate(pads[n]):
            groups.setdefault(f(len(segs) + k), []).append(nm)
        seggroups = {}
        for i in range(len(segs)):
            seggroups.setdefault(f(i), []).append(segs[i])
        # isla principal: la que contiene más pads reales (sin puentes)
        order = sorted(groups, key=lambda g: -sum(1 for nm in groups[g] if not nm.startswith("W")))
        names, used = {}, set()
        for gi, g in enumerate(order):
            if gi == 0:
                names[g] = n
            else:
                wref = sorted(set(nm.split(".")[0] for nm in groups[g] if nm.startswith("W")))
                cand = [c for c in wref if "%s_%s" % (n, c) not in used] or ["I%d" % gi]
                names[g] = "%s_%s" % (n, cand[0])
            used.add(names[g])
        for g, nms in groups.items():
            for nm in nms:
                if names[g] != n:
                    netsplit[nm] = names[g]
        for g, sgs in seggroups.items():
            nn = kname(names.get(g, n))
            newtracks.setdefault(nn, []).extend([[list(a), list(b)] for a, b in sgs])
    return newtracks, netsplit


def chain_polys(fps):
    """Convierte PL.CHAINS en polilíneas usando la posición real de los pads."""
    pre = {k: [list(pl) for pl in v] for k, v in PL.PRE.items()}

    def pad_xy(tok):
        ref, num = tok.split(".")
        for p in fps[ref].Pads():
            if p.GetNumber() == num:
                q = p.GetPosition()
                return (round(pcbnew.ToMM(q.x) - OX, 4), round(pcbnew.ToMM(q.y) - OY, 4))
        raise KeyError(tok)
    for net, toks in getattr(PL, "CHAINS", []):
        pts = []
        for t in toks:
            if isinstance(t, tuple) and t[0] == "BUS":
                pts.append((PL.BUS_X, pts[-1][1]))
            elif isinstance(t, tuple) and t[0] == "VX":
                pts.append((t[1], pts[-1][1]))
            elif isinstance(t, tuple):
                pts.append(t)
            else:
                pts.append(pad_xy(t))
        pre.setdefault(net, []).append(pts)
    return {kname(k): v for k, v in pre.items()}


def do_route(board, fps, iters):
    W, H = PL.W, PL.H
    if True:
        pads = []
        for fp in fps.values():
            for pad in fp.Pads():
                pos = pad.GetPosition()
                x, y = pcbnew.ToMM(pos.x) - OX, pcbnew.ToMM(pos.y) - OY
                sz = pad.GetSize(pcbnew.B_Cu) if hasattr(pad, "GetSize") else pad.GetSize()
                w, h = pcbnew.ToMM(sz.x), pcbnew.ToMM(sz.y)
                ang = round(fp.GetOrientationDegrees()) % 180
                if ang == 90:
                    w, h = h, w
                shp = {pcbnew.PAD_SHAPE_CIRCLE: "circle", pcbnew.PAD_SHAPE_RECTANGLE: "rect",
                       pcbnew.PAD_SHAPE_OVAL: "oval"}.get(pad.GetShape(pcbnew.B_Cu), "rect")
                net = pad.GetNetname() or None
                if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    continue
                pads.append(Pad(fp.GetReference(), pad.GetNumber(), net, x, y, shp, w, h))
        keep = [(x, y, r) for (x, y, r) in PL.KEEPOUTS]
        widths = {kname(n): track_width(n) for n in DZ.nets()}
        bodies = []
        for fp in fps.values():
            cy = fp.GetCourtyard(pcbnew.F_CrtYd)
            bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
            bodies.append((pcbnew.ToMM(bb.GetLeft()) - OX, pcbnew.ToMM(bb.GetTop()) - OY,
                           pcbnew.ToMM(bb.GetRight()) - OX, pcbnew.ToMM(bb.GetBottom()) - OY))
        if os.environ.get("JUMP_OVER_BODIES", "1") == "1":
            bodies = []
        RC = NegotiatedRouter if os.environ.get("PF") else Router
        R = RC(W, H, pads, widths, clearance=CLR, margin=0.1, edge=1.0, keepouts=keep, bodies=bodies,
                   jumper_lengths=(7.62, 10.16, 12.7, 15.24, 20.32, 25.4, 30.48),
                   jumper_cost=float(os.environ.get("JCOST", "60")), pre=chain_polys(fps))
        if os.environ.get("PF"):
            failed, order = R.route_negotiated(iters=iters, first=[kname(n) for n in getattr(PL, "FIRST", ())],
                                               last=[kname(n) for n in getattr(PL, "LAST", ())])
        else:
            failed, order = R.route_all(order=PL.ORDER or None, iters=iters, first=getattr(PL, "FIRST", ()),
                                        last=getattr(PL, "LAST", ()))
        tracks = {n: [[list(p) for p in pl] for pl in pls] for n, pls in R.tracks.items()}
        jumpers = [[dname(n), list(a), list(b)] for (n, a, b) in R.jumpers]
        return failed, tracks, jumpers, order


if __name__ == "__main__":
    out = sys.argv[1]
    route = "--noroute" not in sys.argv
    if not route and not os.path.exists(os.path.join(HERE, "route_result.json")):
        json.dump({"failed": [], "order": [], "tracks": {}, "jumpers": []}, open(os.path.join(HERE, "route_result.json"), "w"))
    f = build(out, route=route)
    print("FALLIDAS:", f)
