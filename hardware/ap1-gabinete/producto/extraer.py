import pcbnew, json, sys
out = {}
for nombre, ruta in [("uno", "/work/hardware/ap1-uno/kicad/AP_UNO.kicad_pcb"), ("red4", "/work/hardware/ap1-red4/kicad/AP_RED4.kicad_pcb"),
                     ("foco127", "/work/hardware/ap1-foco127/kicad/AP_FOCO127.kicad_pcb"), ("foco", "/work/hardware/ap1-foco/kicad/AP_FOCO.kicad_pcb"),
                     ("7r", "/work/hardware/ap-electric/7r-tour/kicad/AP_7R_TOUR.kicad_pcb"),
                     ("home", "/work/hardware/ap-electric/home/kicad/AP_HOME.kicad_pcb")]:
    b = pcbnew.LoadBoard(ruta)
    bb = b.GetBoardEdgesBoundingBox()
    d = {"x0": pcbnew.ToMM(bb.GetX()), "y0": pcbnew.ToMM(bb.GetY()), "w": pcbnew.ToMM(bb.GetWidth()), "h": pcbnew.ToMM(bb.GetHeight()), "fp": []}
    for f in b.GetFootprints():
        ref = f.GetReference()
        if not (ref.startswith("J") or ref.startswith("D") or ref.startswith("LED") or ref.startswith("SW") or ref.startswith("PS") or ref.startswith("K") or ref.startswith("F")):
            continue
        cy = f.GetCourtyard(pcbnew.F_CrtYd).BBox() if f.GetCourtyard(pcbnew.F_CrtYd).OutlineCount() else f.GetBoundingBox(False)
        pads = [(pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)) for p in f.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
        d["fp"].append({"ref": ref, "val": f.GetValue(), "fpid": str(f.GetFPID().GetLibItemName()), "x": pcbnew.ToMM(f.GetPosition().x), "y": pcbnew.ToMM(f.GetPosition().y),
                        "rot": f.GetOrientationDegrees(), "bx": [pcbnew.ToMM(cy.GetX()), pcbnew.ToMM(cy.GetY()), pcbnew.ToMM(cy.GetRight()), pcbnew.ToMM(cy.GetBottom())],
                        "pth": pads, "n": len(f.Pads())})
    out[nombre] = d
json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else "/scratch/caja/placas.json", "w"), indent=1)
