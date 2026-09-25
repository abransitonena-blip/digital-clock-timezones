"""Legalizador de ubicación: elimina traslapes de courtyard/pads moviendo cada
huella a la posición libre más cercana (rejilla de 0.635 mm), respetando el
borde, los barrenos y los buses pre-ruteados.

Escribe gen/placement_final.json, que pcbgen.py usa si existe.
"""
import os, sys, json, math
sys.path.insert(0, os.path.dirname(__file__))
import pcbnew
import design as DZ
import placement as PL
import pcbgen
import numpy as np
from router import Pad

STEP = 0.635
MARGIN = 0.05          # separación mínima entre cajas de courtyard
CLR = 0.7              # separación pad-bus (0.6 + margen)
FIXED_FIRST = ["J1", "J2", "J3", "J4", "J5", "J6", "U1", "U2", "U3", "H1", "H2", "H3", "H4",
               "D7", "R11", "D5", "C8", "R10", "SW2", "R9", "R30", "C6", "RV1", "C5", "R28", "Q4", "R29"]


def boxes_for(fp):
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
    for p in fp.Pads():
        bb.Merge(p.GetBoundingBox())
    return [pcbnew.ToMM(bb.GetLeft()) - pcbgen.OX, pcbnew.ToMM(bb.GetTop()) - pcbgen.OY,
            pcbnew.ToMM(bb.GetRight()) - pcbgen.OX, pcbnew.ToMM(bb.GetBottom()) - pcbgen.OY]


def pads_for(fp):
    out = []
    ang = round(fp.GetOrientationDegrees()) % 180
    for p in fp.Pads():
        pos = p.GetPosition()
        sz = p.GetSize(pcbnew.B_Cu)
        w, h = pcbnew.ToMM(sz.x), pcbnew.ToMM(sz.y)
        if ang == 90:
            w, h = h, w
        shp = {pcbnew.PAD_SHAPE_CIRCLE: "circle", pcbnew.PAD_SHAPE_RECTANGLE: "rect",
               pcbnew.PAD_SHAPE_OVAL: "oval"}.get(p.GetShape(pcbnew.B_Cu), "rect")
        x, y = pcbnew.ToMM(pos.x) - pcbgen.OX, pcbnew.ToMM(pos.y) - pcbgen.OY
        out.append((x, y, max(w, h) / 2, p.GetNetname(), Pad("", "", "", x, y, shp, w, h)))
    return out


def pad_seg_dist(pad, a, b):
    (x1, y1), (x2, y2) = a, b
    n = int(math.hypot(x2 - x1, y2 - y1) / 0.1) + 2
    t = np.linspace(0, 1, n)
    return float(np.min(pad.dist(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)))


def seg_dist(px, py, a, b):
    (x1, y1), (x2, y2) = a, b
    vx, vy = x2 - x1, y2 - y1
    L2 = vx * vx + vy * vy
    t = 0 if L2 == 0 else max(0, min(1, ((px - x1) * vx + (py - y1) * vy) / L2))
    return math.hypot(px - (x1 + t * vx), py - (y1 + t * vy))


def main():
    comps = [c for c in DZ.C if not c["ref"].startswith("W")]
    board, fps, _ = pcbgen.make_board(comps, {})
    spines = []
    for net, polys in PL.PRE.items():
        w = pcbgen.track_width(net)
        for pl in polys:
            for a, b in zip(pl[:-1], pl[1:]):
                spines.append((net, a, b, w))
    order = [r for r in FIXED_FIRST if r in fps] + [r for r in fps if r not in FIXED_FIRST]
    placed = []
    final = {}
    moved = []

    def ok(fp, box):
        x0, y0, x1, y1 = box
        if x0 < 0.2 or y0 < 0.2 or x1 > PL.W - 0.2 or y1 > PL.H - 0.2:
            if not fp.GetReference().startswith(("J", "H")):
                return False
        for (bx0, by0, bx1, by1) in placed:
            if min(x1, bx1) - max(x0, bx0) > -MARGIN and min(y1, by1) - max(y0, by0) > -MARGIN:
                return False
        for (px, py, r, net, pd) in pads_for(fp):
            for (kx, ky, kr) in PL.KEEPOUTS:
                if math.hypot(px - kx, py - ky) < kr + r + 0.3:
                    return False
            for (snet, a, b, w) in spines:
                if snet != net and seg_dist(px, py, a, b) < r + w / 2 + CLR + 2:
                    if pad_seg_dist(pd, a, b) < w / 2 + CLR:
                        return False
        return True

    for ref in order:
        fp = fps[ref]
        x, y, r = PL.POS[ref]
        best = None
        if ref.startswith("H") or ok(fp, boxes_for(fp)):
            best = (x, y)
        else:
            for ring in range(1, 16):
                cands = []
                for i in range(-ring, ring + 1):
                    for j in range(-ring, ring + 1):
                        if max(abs(i), abs(j)) != ring:
                            continue
                        cands.append((math.hypot(i, j), x + i * STEP, y + j * STEP))
                cands.sort()
                for _, nx, ny in cands:
                    fp.SetPosition(pcbgen.P(nx, ny))
                    if ok(fp, boxes_for(fp)):
                        best = (nx, ny)
                        break
                if best:
                    break
            if best is None:
                print("SIN LUGAR:", ref)
                best = (x, y)
            else:
                moved.append((ref, round(best[0] - x, 3), round(best[1] - y, 3)))
        fp.SetPosition(pcbgen.P(*best))
        placed.append(boxes_for(fp))
        final[ref] = (round(best[0], 4), round(best[1], 4), r)
    json.dump(final, open(os.path.join(os.path.dirname(__file__), "placement_final.json"), "w"), indent=0)
    for m in moved:
        print("movido", m)


if __name__ == "__main__":
    main()
