"""Salidas de fabricación de una placa LetreroLab (se ejecuta dentro del contenedor de KiCad 9).

    python3 tools/salidas.py <carpeta> <PROYECTO>      p. ej.  python3 tools/salidas.py ap1-base AP1_Base

Crea hardware/<carpeta>/fabricacion/ con:
  esquema/  PDF del esquema y netlist
  pcb/      PDF de ensamble (valores y serigrafía)
  gerber/   Gerber RS-274X + Excellon + posiciones
  jlcpcb/   ZIP de Gerber, BOM (con códigos LCSC y clase Basic/Preferred/Extended), CPL y resumen de costo de montaje
  3d/       renders y STEP
  bom/      lista de materiales CSV (KiCad)
  reportes/ ERC y DRC
"""
import os, sys, subprocess, shutil, csv, zipfile, glob
import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jlcpcb  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", sys.argv[1]))
NAME = sys.argv[2]
KI = os.path.join(ROOT, "kicad")
OUT = os.path.join(ROOT, "fabricacion")
PCB = os.path.join(KI, NAME + ".kicad_pcb")
SCH = os.path.join(KI, NAME + ".kicad_sch")



def run(*args):
    r = subprocess.run(list(args), capture_output=True, text=True)
    if r.returncode not in (0, 5):
        print(r.stdout, r.stderr)
        raise SystemExit("falló: " + " ".join(args))
    return r


def mk(*p):
    d = os.path.join(OUT, *p)
    os.makedirs(d, exist_ok=True)
    return d


def jlc_files(jlc):
    """BOM y CPL en columnas de JLCPCB, a partir de la placa."""
    b = pcbnew.LoadBoard(PCB)
    groups, cpl = {}, []
    for f in b.GetFootprints():
        if f.IsExcludedFromBOM() or f.GetReference().startswith(("H", "TP")):
            continue
        ref, val, fpn = f.GetReference(), f.GetValue(), f.GetFPID().GetLibItemName().wx_str()
        groups.setdefault((val, fpn), []).append(ref)
        p = f.GetPosition()
        cpl.append([ref, "%.3fmm" % (pcbnew.ToMM(p.x) - 100), "%.3fmm" % (100 - pcbnew.ToMM(p.y)),
                    "Top" if f.GetLayer() == pcbnew.F_Cu else "Bottom", "%.1f" % f.GetOrientationDegrees()])
    key = lambda r: (r.rstrip("0123456789"), int("0" + r[len(r.rstrip("0123456789")):]))
    clases = {}
    with open(os.path.join(jlc, NAME + "_BOM_JLCPCB.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #", "Cantidad", "Clase JLCPCB"])
        for (val, fpn), refs in sorted(groups.items(), key=lambda kv: key(sorted(kv[1], key=key)[0])):
            refs = sorted(refs, key=key)
            p = jlcpcb.buscar(val, fpn)
            clase = (p["clase"].split()[0] if p else "Extended (elegir en JLCPCB)")
            clases.setdefault(clase, []).append((val, ",".join(refs)))
            w.writerow([val, ",".join(refs), fpn, p["lcsc"] if p else "", len(refs), clase])
    with open(os.path.join(jlc, "RESUMEN_JLCPCB.txt"), "w") as fh:
        ext = sum(len(v) for k, v in clases.items() if k.startswith("Extended"))
        fh.write("%s: %d tipos de pieza. Basic y Preferred no pagan montaje por tipo; cada tipo Extended ~3 USD.\n"
                 % (NAME, sum(len(v) for v in clases.values())))
        fh.write("Cargo estimado por piezas Extended: %d x 3 = ~%d USD por pedido (no por placa).\n" % (ext, 3 * ext))
        fh.write("Incluye clemas, conectores y portafusibles de patas (THT): se pueden quitar del pedido y soldar a mano.\n\n")
        for k in sorted(clases):
            fh.write("%s (%d):\n" % (k, len(clases[k])))
            fh.writelines("  %-22s %s\n" % c for c in clases[k])
    with open(os.path.join(jlc, NAME + "_CPL_JLCPCB.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        w.writerows(sorted(cpl, key=lambda r: key(r[0])))


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    esq, pcbd, ger, d3, bom, rep, jlc = (mk("esquema"), mk("pcb"), mk("gerber"), mk("3d"), mk("bom"),
                                          mk("reportes"), mk("jlcpcb"))

    capas = pcbnew.LoadBoard(PCB).GetCopperLayerCount()
    cobre = "F.Cu," + "".join("In%d.Cu," % i for i in range(1, capas - 1)) + "B.Cu"
    run("kicad-cli", "sch", "export", "pdf", "-o", os.path.join(esq, NAME + "_esquema.pdf"), SCH)
    run("kicad-cli", "sch", "export", "netlist", "-o", os.path.join(esq, NAME + ".net"), SCH)
    run("kicad-cli", "sch", "erc", "--severity-all", "-o", os.path.join(rep, "ERC_" + NAME + ".rpt"), SCH)
    run("kicad-cli", "sch", "export", "bom", "-o", os.path.join(bom, "BOM_KiCad.csv"),
        "--fields", "Reference,Value,Footprint,${QUANTITY},Funcion",
        "--labels", "Referencia,Valor,Huella,Cantidad,Funcion",
        "--group-by", "Value,Footprint", "--ref-range-delimiter", "", SCH)
    run("kicad-cli", "pcb", "drc", "--schematic-parity", "--severity-all", "-o",
        os.path.join(rep, "DRC_" + NAME + ".rpt"), PCB)

    run("kicad-cli", "pcb", "export", "pdf", "-o", os.path.join(pcbd, "ensamble_lado_componentes.pdf"),
        "--layers", "F.Fab,F.SilkS,Edge.Cuts", "--mode-single", "--drill-shape-opt", "2", PCB)
    run("kicad-cli", "pcb", "export", "pdf", "-o", os.path.join(pcbd, "capas_de_cobre.pdf"),
        "--layers", cobre + ",Edge.Cuts", "--mode-multipage", PCB)
    run("kicad-cli", "pcb", "export", "pdf", "-o", os.path.join(pcbd, "lado_inferior.pdf"),
        "--layers", "B.Fab,B.SilkS,Edge.Cuts", "--mode-single", "--mirror", "--drill-shape-opt", "2", PCB)

    run("kicad-cli", "pcb", "export", "gerbers", "-o", ger + "/",
        "--layers", cobre + ",F.SilkS,B.SilkS,F.Mask,B.Mask,F.Paste,Edge.Cuts", "--no-protel-ext",
        "--subtract-soldermask", PCB)
    run("kicad-cli", "pcb", "export", "drill", "-o", ger + "/", "--format", "excellon", "--drill-origin", "absolute",
        "--excellon-units", "mm", "--excellon-separate-th", "--generate-map", "--map-format", "pdf", PCB)
    run("kicad-cli", "pcb", "export", "pos", "-o", os.path.join(ger, "posiciones_componentes.csv"),
        "--format", "csv", "--units", "mm", "--side", "both", "--exclude-dnp", PCB)

    with zipfile.ZipFile(os.path.join(jlc, NAME + "_gerber_JLCPCB.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(glob.glob(os.path.join(ger, "*"))):
            if f.endswith((".gbr", ".drl", ".gbrjob")):
                z.write(f, os.path.basename(f))
    jlc_files(jlc)

    common = ["--quality", "high", "--width", "1600", "--height", "1300", "--background", "opaque"]
    run("kicad-cli", "pcb", "render", "-o", os.path.join(d3, "render_superior.png"), "--side", "top", *common, PCB)
    run("kicad-cli", "pcb", "render", "-o", os.path.join(d3, "render_inferior.png"), "--side", "bottom", *common, PCB)
    run("kicad-cli", "pcb", "render", "-o", os.path.join(d3, "render_perspectiva.png"), "--side", "top",
        "--perspective", "--rotate", "-45,0,20", "--zoom", "0.85", *common, PCB)
    run("kicad-cli", "pcb", "export", "step", "-o", os.path.join(d3, NAME + ".step"), "--subst-models", "--force", PCB)
    print("listo:", OUT)


if __name__ == "__main__":
    main()
