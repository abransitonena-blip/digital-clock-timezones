"""Salidas de fabricación de LetreroLab AP-0.2 (se ejecuta dentro del contenedor de KiCad 9).

    python3 gen/outputs.py

Crea hardware/ap02/fabricacion/ con:
  esquema/  PDF del esquema y netlist
  pcb/      PDF de ensamble (valores y serigrafía)
  gerber/   Gerber RS-274X + Excellon + posiciones
  jlcpcb/   ZIP de Gerber, BOM y CPL en el formato de ensamble (PCBA) de JLCPCB
  3d/       renders y STEP
  bom/      lista de materiales CSV (KiCad)
  reportes/ ERC y DRC
"""
import os, sys, subprocess, shutil, csv, zipfile, glob
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
KI = os.path.join(ROOT, "kicad")
OUT = os.path.join(ROOT, "fabricacion")
PCB = os.path.join(KI, "AP02.kicad_pcb")
SCH = os.path.join(KI, "AP02.kicad_sch")

# Códigos LCSC conocidos. TODOS deben confirmarse en lcsc.com antes de pedir (existencia y precio cambian);
# los que faltan se eligen en la página de JLCPCB al subir la BOM ("basic parts" de preferencia).
LCSC = {
    ("ESP32-C3-WROOM-02", "ESP32-C3-WROOM-02"): "C2934560",
    ("USBLC6-2SC6", "SOT-23-6"): "C7519",
    ("USB-C", "USB_C_Receptacle_HRO_TYPE-C-31-M-12"): "C165948",
    ("AO3400A", "SOT-23"): "C20917",
    ("1N4148W", "D_SOD-123"): "C81598",
    ("SS34", "D_SMA"): "C8678",
    ("AP63203WU", "TSOT-23-6"): "C780769",
    ("10k", "R_0603_1608Metric"): "C25804",
    ("4.7k", "R_0603_1608Metric"): "C23162",
    ("5.1k", "R_0603_1608Metric"): "C23186",
    ("100nF", "C_0603_1608Metric"): "C14663",
    ("10uF", "C_0805_2012Metric"): "C15850",
}


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
    with open(os.path.join(jlc, "AP02_BOM_JLCPCB.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #", "Cantidad"])
        for (val, fpn), refs in sorted(groups.items(), key=lambda kv: key(sorted(kv[1], key=key)[0])):
            refs = sorted(refs, key=key)
            w.writerow([val, ",".join(refs), fpn, LCSC.get((val, fpn), ""), len(refs)])
    with open(os.path.join(jlc, "AP02_CPL_JLCPCB.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        w.writerows(sorted(cpl, key=lambda r: key(r[0])))


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    esq, pcbd, ger, d3, bom, rep, jlc = (mk("esquema"), mk("pcb"), mk("gerber"), mk("3d"), mk("bom"),
                                          mk("reportes"), mk("jlcpcb"))

    run("kicad-cli", "sch", "export", "pdf", "-o", os.path.join(esq, "AP02_esquema.pdf"), SCH)
    run("kicad-cli", "sch", "export", "netlist", "-o", os.path.join(esq, "AP02.net"), SCH)
    run("kicad-cli", "sch", "erc", "--severity-all", "-o", os.path.join(rep, "ERC_AP02.rpt"), SCH)
    run("kicad-cli", "sch", "export", "bom", "-o", os.path.join(bom, "BOM_KiCad.csv"),
        "--fields", "Reference,Value,Footprint,${QUANTITY},Funcion",
        "--labels", "Referencia,Valor,Huella,Cantidad,Funcion",
        "--group-by", "Value,Footprint", "--ref-range-delimiter", "", SCH)
    run("kicad-cli", "pcb", "drc", "--schematic-parity", "--severity-all", "-o",
        os.path.join(rep, "DRC_AP02.rpt"), PCB)

    run("kicad-cli", "pcb", "export", "pdf", "-o", os.path.join(pcbd, "ensamble_lado_componentes.pdf"),
        "--layers", "F.Fab,F.SilkS,Edge.Cuts", "--mode-single", "--drill-shape-opt", "2", PCB)
    run("kicad-cli", "pcb", "export", "pdf", "-o", os.path.join(pcbd, "cobre_superior_e_inferior.pdf"),
        "--layers", "F.Cu,B.Cu,Edge.Cuts", "--mode-multipage", PCB)

    run("kicad-cli", "pcb", "export", "gerbers", "-o", ger + "/",
        "--layers", "F.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,F.Paste,Edge.Cuts", "--no-protel-ext",
        "--subtract-soldermask", PCB)
    run("kicad-cli", "pcb", "export", "drill", "-o", ger + "/", "--format", "excellon", "--drill-origin", "absolute",
        "--excellon-units", "mm", "--excellon-separate-th", "--generate-map", "--map-format", "pdf", PCB)
    run("kicad-cli", "pcb", "export", "pos", "-o", os.path.join(ger, "posiciones_componentes.csv"),
        "--format", "csv", "--units", "mm", "--side", "both", "--exclude-dnp", PCB)

    with zipfile.ZipFile(os.path.join(jlc, "AP02_gerber_JLCPCB.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(glob.glob(os.path.join(ger, "*"))):
            if f.endswith((".gbr", ".drl", ".gbrjob")):
                z.write(f, os.path.basename(f))
    jlc_files(jlc)

    common = ["--quality", "high", "--width", "1600", "--height", "1300", "--background", "opaque"]
    run("kicad-cli", "pcb", "render", "-o", os.path.join(d3, "render_superior.png"), "--side", "top", *common, PCB)
    run("kicad-cli", "pcb", "render", "-o", os.path.join(d3, "render_inferior.png"), "--side", "bottom", *common, PCB)
    run("kicad-cli", "pcb", "render", "-o", os.path.join(d3, "render_perspectiva.png"), "--side", "top",
        "--perspective", "--rotate", "-45,0,20", "--zoom", "0.85", *common, PCB)
    run("kicad-cli", "pcb", "export", "step", "-o", os.path.join(d3, "AP02.step"), "--subst-models", "--force", PCB)
    print("listo:", OUT)


if __name__ == "__main__":
    main()
