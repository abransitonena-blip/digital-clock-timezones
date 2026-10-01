"""Genera la biblioteca de huellas del proyecto (ControladorFlechas.pretty).

Parte de las huellas estándar de KiCad 9 (se conservan serigrafía, fab y
courtyard) y reemplaza los pads por pads grandes aptos para transferencia de
tóner en una PCB de una sola cara (cobre solo en B.Cu).
"""
import os, sys, uuid
sys.path.insert(0, os.path.dirname(__file__))
from sexpr import parse, dump, Sym, find, find1

KFP = os.environ.get("KICAD_FP", "/usr/share/kicad/footprints")
LIB = "ControladorFlechas"

# nombre: (origen, {pad: (x, y)}, forma, (w, h), taladro, forma_pad1, modelo_3d)
RND = "circle"
OVV = "oval"
FOOTPRINTS = {
    "R_Axial_P10.16mm": ("Resistor_THT/R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal", {}, RND, (2.4, 2.4), 0.8, None,
                         "Resistor_THT/R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"),
    "R_Vertical_P5.08mm": ("Resistor_THT/R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical", {}, RND, (2.4, 2.4), 0.8, None,
                           "Resistor_THT/R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical"),
    "D_DO-41_P10.16mm": ("Diode_THT/D_DO-41_SOD81_P10.16mm_Horizontal", {}, RND, (2.4, 2.4), 1.0, "rect",
                         "Diode_THT/D_DO-41_SOD81_P10.16mm_Horizontal"),
    "D_DO-35_P7.62mm": ("Diode_THT/D_DO-35_SOD27_P7.62mm_Horizontal", {}, RND, (2.4, 2.4), 0.8, "rect",
                        "Diode_THT/D_DO-35_SOD27_P7.62mm_Horizontal"),
    "D_DO-15_P12.70mm": ("Diode_THT/D_DO-15_P12.70mm_Horizontal", {}, RND, (2.6, 2.6), 1.0, "rect",
                         "Diode_THT/D_DO-15_P12.70mm_Horizontal"),
    "C_Disc_P5.08mm": ("Capacitor_THT/C_Disc_D5.0mm_W2.5mm_P5.00mm", {"2": (5.08, 0)}, RND, (2.4, 2.4), 0.8, None,
                       "Capacitor_THT/C_Disc_D5.0mm_W2.5mm_P5.00mm"),
    "CP_Radial_D8.0mm_P3.81mm": ("Capacitor_THT/CP_Radial_D8.0mm_P3.50mm", {"2": (3.81, 0)}, RND, (2.4, 2.4), 0.8, "rect",
                                 "Capacitor_THT/CP_Radial_D8.0mm_P3.50mm"),
    "CP_Radial_D5.0mm_P2.54mm": ("Capacitor_THT/CP_Radial_D5.0mm_P2.50mm", {"2": (2.54, 0)}, OVV, (1.6, 2.6), 0.8, "rect",
                                 "Capacitor_THT/CP_Radial_D5.0mm_P2.50mm"),
    "LED_D3.0mm": ("LED_THT/LED_D3.0mm", {}, OVV, (1.6, 2.6), 0.8, "rect", "LED_THT/LED_D3.0mm"),
    "DIP-8_W7.62mm": ("Package_DIP/DIP-8_W7.62mm", {}, OVV, (2.6, 1.6), 0.8, "rect", "Package_DIP/DIP-8_W7.62mm"),
    "DIP-16_W7.62mm": ("Package_DIP/DIP-16_W7.62mm", {}, OVV, (2.6, 1.6), 0.8, "rect", "Package_DIP/DIP-16_W7.62mm"),
    "TO-92_2N7000": ("Package_TO_SOT_THT/TO-92_Inline_Wide", {}, OVV, (1.6, 2.6), 0.8, "rect",
                     "Package_TO_SOT_THT/TO-92_Inline_Wide"),
    "TO-92_LM317L": ("Package_TO_SOT_THT/TO-92_Inline_Wide", {}, OVV, (1.6, 2.6), 0.8, "rect",
                     "Package_TO_SOT_THT/TO-92_Inline_Wide"),
    "TO-220-3_Vertical": ("Package_TO_SOT_THT/TO-220-3_Vertical", {}, OVV, (1.8, 3.0), 1.1, "rect",
                          "Package_TO_SOT_THT/TO-220-3_Vertical"),
    "Clema_2P_P5.08mm": ("TerminalBlock_Phoenix/TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal", {}, RND,
                         (3.0, 3.0), 1.3, "rect",
                         "TerminalBlock_Phoenix/TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal"),
    "Clema_4P_P5.08mm": ("TerminalBlock_Phoenix/TerminalBlock_Phoenix_MKDS-1,5-4-5.08_1x04_P5.08mm_Horizontal", {}, RND,
                         (3.0, 3.0), 1.3, "rect",
                         "TerminalBlock_Phoenix/TerminalBlock_Phoenix_MKDS-1,5-4-5.08_1x04_P5.08mm_Horizontal"),
    "PTC_Radial_P5.08mm": ("Capacitor_THT/C_Disc_D7.5mm_W5.0mm_P5.00mm", {"2": (5.08, 0)}, RND, (2.4, 2.4), 0.8, None,
                           "Capacitor_THT/C_Disc_D7.5mm_W5.0mm_P5.00mm"),
    "Trimpot_3296W": ("Potentiometer_THT/Potentiometer_Bourns_3296W_Vertical", {}, OVV, (1.6, 2.6), 0.8, None,
                      "Potentiometer_THT/Potentiometer_Bourns_3296W_Vertical"),
    "Boton_6mm": ("Button_Switch_THT/SW_PUSH_6mm", None, RND, (2.4, 2.4), 1.0, None, "Button_Switch_THT/SW_PUSH_6mm"),
    "DIPSW_1_W7.62mm": ("Button_Switch_THT/SW_DIP_SPSTx01_Slide_9.78x4.72mm_W7.62mm_P2.54mm", {}, RND, (2.4, 2.4), 0.8,
                        "rect", "Button_Switch_THT/SW_DIP_SPSTx01_Slide_9.78x4.72mm_W7.62mm_P2.54mm"),
}

PIN_TEXT = {"TO-92_2N7000": "S G D", "TO-92_LM317L": "A O I", "TO-220-3_Vertical": "ADJ OUT IN"}

BOTON_PADS = [("1", 0, 0), ("1", 6.35, 0), ("2", 0, 4.445), ("2", 6.35, 4.445)]


def uid():
    return Sym(str(uuid.uuid4()))


def pad(num, shape, x, y, size, drill):
    return [Sym("pad"), num, Sym("thru_hole"), Sym(shape), [Sym("at"), x, y], [Sym("size"), size[0], size[1]],
            [Sym("drill"), drill], [Sym("layers"), "B.Cu", "B.Mask"], [Sym("remove_unused_layers"), Sym("no")],
            [Sym("uuid"), str(uuid.uuid4())]]


def build(name, spec):
    src, moves, shape, size, drill, p1, model = spec
    fp = parse(open(os.path.join(KFP, src.split("/")[0] + ".pretty", src.split("/")[1] + ".kicad_mod")).read())
    fp[1] = name
    out = []
    old_pads = []
    for e in fp:
        if isinstance(e, list) and e and e[0] == "pad":
            old_pads.append(e)
            continue
        if isinstance(e, list) and e and e[0] == "model":
            continue
        if isinstance(e, list) and e and e[0] == "property" and e[1] == "Value":
            e[2] = name
        if isinstance(e, list) and e and e[0] == "descr":
            e[1] = e[1] + " (pads ampliados para transferencia de toner, cobre solo en B.Cu)"
        out.append(e)
    if moves is None:
        pads = [(n, x, y) for n, x, y in BOTON_PADS]
    else:
        pads = []
        for p in old_pads:
            at = find1(p, "at")
            n = p[1]
            x, y = float(at[1]), float(at[2])
            if n in moves:
                x, y = moves[n]
            pads.append((n, x, y))
    for i, (n, x, y) in enumerate(pads):
        shp = p1 if (n == "1" and p1 and i == 0) else shape
        out.append(pad(n, shp, x, y, size, drill))
    if name in PIN_TEXT:
        out.append([Sym("fp_text"), Sym("user"), PIN_TEXT[name], [Sym("at"), 2.54, 3.4 if "TO-92" in name else 3.6, 0],
                    [Sym("layer"), "F.SilkS"], [Sym("uuid"), str(uuid.uuid4())],
                    [Sym("effects"), [Sym("font"), [Sym("size"), 0.8, 0.8], [Sym("thickness"), 0.15]]]])
    mdl = "${KIPRJMOD}/3d/" + model.split("/")[1] + ".step"
    out.append([Sym("model"), mdl, [Sym("offset"), [Sym("xyz"), 0, 0, 0]], [Sym("scale"), [Sym("xyz"), 1, 1, 1]],
                [Sym("rotate"), [Sym("xyz"), 0, 0, 0]]])
    return out


def build_jumper(P=7.62, name=None, bridged=True):
    """Puente de alambre desnudo (paso P mm). bridged=True: une sus pads (misma red)."""
    L = []
    s = lambda *a: [Sym(a[0])] + list(a[1:])
    fp = [Sym("footprint"), name or ("Puente_Alambre_P%.2fmm" % P), s("version", Sym("20241229")), s("generator", "pcbnew"),
          s("generator_version", "9.0"), s("layer", "F.Cu"),
          s("descr", "Puente de alambre desnudo, paso %.2f mm, pads para toner" % P),
          [Sym("property"), "Reference", "JP**", s("at", P / 2, -2.2, 0), s("layer", "F.SilkS"),
           s("uuid", str(uuid.uuid4())), s("effects", s("font", s("size", 1, 1), s("thickness", 0.15)))],
          [Sym("property"), "Value", "Puente", s("at", P / 2, 2.2, 0), s("layer", "F.Fab"),
           s("uuid", str(uuid.uuid4())), s("effects", s("font", s("size", 1, 1), s("thickness", 0.15)))],
          s("attr", Sym("through_hole")),
          [Sym("fp_line"), s("start", 1.6, 0), s("end", P - 1.6, 0), s("stroke", s("width", 0.3), s("type", Sym("dash"))),
           s("layer", "F.SilkS"), s("uuid", str(uuid.uuid4()))],
          pad("1", RND, 0, 0, (2.4, 2.4), 0.8), pad("2", RND, P, 0, (2.4, 2.4), 0.8)]
    return fp


def build_hole():
    fp = parse(open(os.path.join(KFP, "MountingHole.pretty", "MountingHole_3.2mm_M3.kicad_mod")).read())
    fp[1] = "Barreno_M3_3.2mm"
    return fp


def main(outdir):
    d = os.path.join(outdir, LIB + ".pretty")
    os.makedirs(d, exist_ok=True)
    for name, spec in FOOTPRINTS.items():
        open(os.path.join(d, name + ".kicad_mod"), "w").write(dump(build(name, spec)) + "\n")
    open(os.path.join(d, "Enlace_Opcional_P7.62mm.kicad_mod"), "w").write(
        dump(build_jumper(7.62, "Enlace_Opcional_P7.62mm", bridged=False)) + "\n")
    for P in (7.62, 10.16, 12.7, 15.24, 20.32, 25.4, 30.48):
        open(os.path.join(d, "Puente_Alambre_P%.2fmm.kicad_mod" % P), "w").write(dump(build_jumper(P)) + "\n")
    open(os.path.join(d, "Barreno_M3_3.2mm.kicad_mod"), "w").write(dump(build_hole()) + "\n")
    models = sorted(set(v[6] for v in FOOTPRINTS.values()))
    return models


if __name__ == "__main__":
    for m in main(sys.argv[1]):
        print(m)
