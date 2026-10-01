"""Construye la PCB sin rutear (o con ruteo), informa traslapes y genera una imagen de revisión."""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(__file__))
import pcbnew, pcbgen
import placement as PL
out = sys.argv[1]
route = "--route" in sys.argv
pcbgen.build(out, route=route)
b = pcbnew.LoadBoard(out)
boxes = []
for fp in b.GetFootprints():
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
    for p in fp.Pads():
        bb.Merge(p.GetBoundingBox())
    x0, y0 = pcbnew.ToMM(bb.GetLeft()) - 50, pcbnew.ToMM(bb.GetTop()) - 50
    x1, y1 = pcbnew.ToMM(bb.GetRight()) - 50, pcbnew.ToMM(bb.GetBottom()) - 50
    boxes.append((fp.GetReference(), x0, y0, x1, y1))
    if x0 < 0 or y0 < 0 or x1 > PL.W or y1 > PL.H:
        print("FUERA:", fp.GetReference(), round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2))
for i in range(len(boxes)):
    for j in range(i + 1, len(boxes)):
        a, b2 = boxes[i], boxes[j]
        ox = min(a[3], b2[3]) - max(a[1], b2[1])
        oy = min(a[4], b2[4]) - max(a[2], b2[2])
        if ox > -0.3 and oy > -0.3:
            print("TRASLAPE:", a[0], b2[0], round(ox, 2), round(oy, 2))
