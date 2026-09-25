import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
os.environ["NO_JUMPERS"] = "1"
import pcbnew, pcbgen, legalize as LG
import placement as PL
import design as DZ
comps = [c for c in DZ.C if not c["ref"].startswith("W")]
os.environ["RAW_PLACEMENT"] = "1"
board, fps, _ = pcbgen.make_board(comps, {})
spines = []
for net, polys in PL.PRE.items():
    for pl in polys:
        for a, b in zip(pl[:-1], pl[1:]):
            spines.append((net, a, b, pcbgen.track_width(net)))
boxes = {r: LG.boxes_for(f) for r, f in fps.items()}
for ref in sys.argv[1:]:
    fp = fps[ref]; x0, y0, x1, y1 = boxes[ref]
    print(ref, [round(v, 2) for v in boxes[ref]])
    for r2, (a0, b0, a1, b1) in boxes.items():
        if r2 == ref: continue
        if min(x1, a1) - max(x0, a0) > -LG.MARGIN and min(y1, b1) - max(y0, b0) > -LG.MARGIN:
            print("   caja con", r2, [round(v, 2) for v in (a0, b0, a1, b1)])
    for (px, py, r, net, pd) in LG.pads_for(fp):
        for (snet, a, b, w) in spines:
            if snet != net and LG.pad_seg_dist(pd, a, b) < w / 2 + LG.CLR:
                print("   pad", net, (round(px,2), round(py,2)), "choca bus", snet, a, b)
