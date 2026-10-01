"""Salidas de fabricación de la fuente OS (se ejecuta dentro del contenedor de KiCad 9).

    python3 gen/outputs.py

Crea hardware/fuente-os-127v/fabricacion/ con:
  esquema/  PDF del esquema, reporte ERC
  pcb/      PDF de cobre para planchado (1:1), lado componentes, plantilla de perforaciones
  gerber/   Gerber RS-274X + Excellon (PTH/NPTH) + mapa de perforaciones
  3d/       renders de la placa
  bom/      lista de materiales CSV (KiCad)
  reportes/ ERC y DRC
"""
import os, sys, subprocess, shutil, math, json
sys.path.insert(0, os.path.dirname(__file__))
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
KI = os.path.join(ROOT, "kicad")
OUT = os.path.join(ROOT, "fabricacion")
PCB = os.path.join(KI, "FuenteOS.kicad_pcb")
SCH = os.path.join(KI, "FuenteOS.kicad_sch")


def run(*args):
    r = subprocess.run(list(args), capture_output=True, text=True)
    if r.returncode not in (0, 5):          # 5 = hay violaciones (se revisa el reporte)
        print(r.stdout, r.stderr)
        raise SystemExit("falló: " + " ".join(args))
    return r


def mk(*p):
    d = os.path.join(OUT, *p)
    os.makedirs(d, exist_ok=True)
    return d


def drill_template():
    """Placa temporal con círculos del diámetro real de cada barreno en Dwgs.User."""
    b = pcbnew.LoadBoard(PCB)
    holes = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            d = pcbnew.ToMM(p.GetDrillSize().x)
            if d <= 0:
                continue
            pos = p.GetPosition()
            holes.setdefault(round(d, 2), []).append(pos)
            c = pcbnew.PCB_SHAPE(b)
            c.SetShape(pcbnew.SHAPE_T_CIRCLE)
            c.SetCenter(pos)
            c.SetEnd(pcbnew.VECTOR2I(pos.x + pcbnew.FromMM(d / 2), pos.y))
            c.SetLayer(pcbnew.Dwgs_User)
            c.SetWidth(pcbnew.FromMM(0.12))
            b.Add(c)
            for dx, dy in ((1, 0), (0, 1)):
                L = pcbnew.FromMM(d / 2 + 0.6)
                ln = pcbnew.PCB_SHAPE(b)
                ln.SetShape(pcbnew.SHAPE_T_SEGMENT)
                ln.SetStart(pcbnew.VECTOR2I(pos.x - dx * L, pos.y - dy * L))
                ln.SetEnd(pcbnew.VECTOR2I(pos.x + dx * L, pos.y + dy * L))
                ln.SetLayer(pcbnew.Dwgs_User)
                ln.SetWidth(pcbnew.FromMM(0.08))
                b.Add(ln)
    tmp = os.path.join(KI, "_plantilla_tmp.kicad_pcb")
    b.Save(tmp)
    return tmp, {k: len(v) for k, v in sorted(holes.items())}


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    esq, pcbd, ger, d3, bom, rep = (mk("esquema"), mk("pcb"), mk("gerber"), mk("3d"), mk("bom"), mk("reportes"))

    # ---- esquema y ERC ----
    run("kicad-cli", "sch", "export", "pdf", "-o", os.path.join(esq, "FuenteOS_esquema.pdf"), SCH)
    run("kicad-cli", "sch", "erc", "--severity-all", "-o", os.path.join(rep, "ERC_FuenteOS.rpt"), SCH)
    run("kicad-cli", "sch", "export", "bom", "-o", os.path.join(bom, "BOM_KiCad.csv"),
        "--fields", "Reference,Value,Footprint,${QUANTITY},Funcion",
        "--labels", "Referencia,Valor,Huella,Cantidad,Funcion",
        "--group-by", "Value,Footprint", "--ref-range-delimiter", "", SCH)
    run("kicad-cli", "sch", "export", "netlist", "-o", os.path.join(esq, "FuenteOS.net"), SCH)

    # ---- DRC con paridad ----
    run("kicad-cli", "pcb", "drc", "--schematic-parity", "--severity-all", "-o",
        os.path.join(rep, "DRC_FuenteOS.rpt"), PCB)

    # ---- PDFs 1:1 ----
    run("kicad-cli", "pcb", "export", "pdf", "-o", os.path.join(pcbd, "1_cobre_para_planchado_1a1.pdf"),
        "--layers", "B.Cu,Edge.Cuts", "--mode-single", "--black-and-white", "--drill-shape-opt", "1", PCB)
    run("kicad-cli", "pcb", "export", "pdf", "-o", os.path.join(pcbd, "2_cobre_vista_desde_lado_soldadura_1a1.pdf"),
        "--layers", "B.Cu,Edge.Cuts", "--mode-single", "--black-and-white", "--mirror", "--drill-shape-opt", "1", PCB)
    run("kicad-cli", "pcb", "export", "pdf", "-o", os.path.join(pcbd, "3_lado_componentes_1a1.pdf"),
        "--layers", "F.SilkS,Edge.Cuts", "--mode-single", "--black-and-white", "--drill-shape-opt", "2", PCB)
    run("kicad-cli", "pcb", "export", "pdf", "-o", os.path.join(pcbd, "5_ensamble_componentes_con_valores.pdf"),
        "--layers", "F.Fab,F.SilkS,Edge.Cuts", "--mode-single", "--drill-shape-opt", "2", PCB)
    tmp, counts = drill_template()
    run("kicad-cli", "pcb", "export", "pdf", "-o", os.path.join(pcbd, "4_plantilla_perforaciones_1a1.pdf"),
        "--layers", "Dwgs.User,Edge.Cuts", "--mode-single", "--black-and-white", "--drill-shape-opt", "0", tmp)
    os.remove(tmp)
    json.dump(counts, open(os.path.join(pcbd, "barrenos.json"), "w"), indent=1)

    # ---- Gerber y Excellon ----
    run("kicad-cli", "pcb", "export", "gerbers", "-o", ger + "/",
        "--layers", "B.Cu,F.Cu,F.SilkS,B.Mask,F.Mask,Edge.Cuts", "--no-protel-ext",
        "--subtract-soldermask", PCB)
    run("kicad-cli", "pcb", "export", "drill", "-o", ger + "/", "--format", "excellon", "--drill-origin", "absolute",
        "--excellon-units", "mm", "--excellon-separate-th", "--generate-map", "--map-format", "pdf", PCB)
    run("kicad-cli", "pcb", "export", "pos", "-o", os.path.join(ger, "posiciones_componentes.csv"),
        "--format", "csv", "--units", "mm", "--side", "both", "--exclude-dnp", PCB)

    # ---- renders 3D ----
    common = ["--quality", "basic", "--width", "1400", "--height", "1400", "--background", "transparent"]
    run("kicad-cli", "pcb", "render", "-o", os.path.join(d3, "render_superior.png"), "--side", "top", *common, PCB)
    run("kicad-cli", "pcb", "render", "-o", os.path.join(d3, "render_inferior.png"), "--side", "bottom", *common, PCB)
    run("kicad-cli", "pcb", "render", "-o", os.path.join(d3, "render_perspectiva.png"), "--side", "top",
        "--perspective", "--rotate", "-50,0,25", "--zoom", "0.9", *common, PCB)
    run("kicad-cli", "pcb", "export", "step", "-o", os.path.join(d3, "FuenteOS.step"),
        "--subst-models", "--force", PCB)
    print("barrenos:", counts)


if __name__ == "__main__":
    main()
