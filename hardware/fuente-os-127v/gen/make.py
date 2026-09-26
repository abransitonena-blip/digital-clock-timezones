"""Fuente capacitiva (tipo Radox, NO aislada) para la palabra "OS": 20 LED amarillos en serie a 127 VCA.

Genera el proyecto KiCad 9 completo (huellas, esquema, PCB ruteada a mano de 50 x 50 mm, una cara).
Se ejecuta dentro del contenedor de KiCad 9:

    python3 gen/make.py

Reutiliza sexpr.py, fplib.py y sch.py del proyecto controlador-flechas-36v.
"""
import os, sys, json, shutil, uuid, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
KI = os.path.join(ROOT, "kicad")
sys.path.insert(0, os.path.join(ROOT, "..", "controlador-flechas-36v", "gen"))
from sexpr import dump, Sym  # noqa: E402
import fplib  # noqa: E402
import sch  # noqa: E402

PROJECT = "FuenteOS"
LIB = "FuenteOS"
NS = uuid.UUID("5d1f3c7a-2e4b-4a6c-9b8d-0f1e2d3c4b5a")
ROOT_UUID = "9a2b7c4d-1e3f-4a5b-8c6d-7e8f9a0b1c2d"
KMOD = "/usr/share/kicad/3dmodels"

# ---------------------------------------------------------------- huellas
RND, OVV = "circle", "oval"
FOOTPRINTS = {
    "Clema_2P_P5.08mm": ("TerminalBlock_Phoenix/TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal", {}, RND,
                         (3.0, 3.0), 1.3, "rect",
                         "TerminalBlock_Phoenix/TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal"),
    "R_1W_P15.24mm": ("Resistor_THT/R_Axial_DIN0411_L9.9mm_D3.6mm_P15.24mm_Horizontal", {}, RND, (2.6, 2.6), 1.0, None,
                      "Resistor_THT/R_Axial_DIN0411_L9.9mm_D3.6mm_P15.24mm_Horizontal"),
    "R_Axial_P15.24mm": ("Resistor_THT/R_Axial_DIN0207_L6.3mm_D2.5mm_P15.24mm_Horizontal", {}, RND, (2.4, 2.4), 0.8,
                         None, "Resistor_THT/R_Axial_DIN0207_L6.3mm_D2.5mm_P15.24mm_Horizontal"),
    "C_Poliester_P15mm": ("Capacitor_THT/C_Rect_L18.0mm_W6.0mm_P15.00mm_FKS3_FKP3", {}, RND, (2.6, 2.6), 1.0, None,
                          "Capacitor_THT/C_Rect_L18.0mm_W6.0mm_P15.00mm_FKS3_FKP3"),
    "Varistor_D7mm_P5mm": ("Varistor/RV_Disc_D7mm_W3.4mm_P5mm", {}, RND, (2.4, 2.4), 1.0, None,
                           "Varistor/RV_Disc_D7mm_W3.4mm_P5mm"),
    "D_DO-41_P10.16mm": ("Diode_THT/D_DO-41_SOD81_P10.16mm_Horizontal", {}, RND, (2.4, 2.4), 1.0, "rect",
                         "Diode_THT/D_DO-41_SOD81_P10.16mm_Horizontal"),
}

# ---------------------------------------------------------------- circuito
# ref, valor, símbolo, huella, {pin: red}, (x, y, rot) en el esquema, función
C = [
    ("J1", "127 VCA", "Connector:Screw_Terminal_01x02", "Clema_2P_P5.08mm", {"1": "L", "2": "N"}, (35.56, 76.2, 180),
     "Entrada de red 127 VCA (pin 1 = L fase, pin 2 = N neutro). Tomar del mismo cable que la placa Radox"),
    ("R1", "220R 1W fusible", "Device:R", "R_1W_P15.24mm", {"1": "L", "2": "A"}, (60.96, 60.96, 90),
     "Resistencia fusible (flameproof): limita el pico al enchufar (180 V / 220 = 0.8 A) y actúa como fusible"),
    ("RV1", "07D201K", "Device:Varistor", "Varistor_D7mm_P5mm", {"1": "N", "2": "A"}, (76.2, 91.44, 0),
     "Varistor 200 V (MOV): recorta picos de la red. Va después de R1 para que R1 lo proteja"),
    ("C1", "334J 400V", "Device:C", "C_Poliester_P15mm", {"1": "A", "2": "AC1"}, (99.06, 60.96, 90),
     "Capacitor de poliéster 0.33 uF 400 V: fija la corriente de los LED (~11 mA)"),
    ("R2", "1M 1/2W", "Device:R", "R_Axial_P15.24mm", {"1": "A", "2": "AC1"}, (99.06, 76.2, 90),
     "Descarga C1 al desenchufar (tau = 1M x 0.33uF = 0.33 s)"),
    ("D1", "1N4007", "Device:D", "D_DO-41_P10.16mm", {"1": "OS+", "2": "AC1"}, (137.16, 55.88, 0),
     "Puente rectificador (1000 V 1 A)"),
    ("D2", "1N4007", "Device:D", "D_DO-41_P10.16mm", {"1": "OS+", "2": "N"}, (137.16, 71.12, 0),
     "Puente rectificador (1000 V 1 A)"),
    ("D3", "1N4007", "Device:D", "D_DO-41_P10.16mm", {"1": "AC1", "2": "OS-"}, (137.16, 86.36, 0),
     "Puente rectificador (1000 V 1 A)"),
    ("D4", "1N4007", "Device:D", "D_DO-41_P10.16mm", {"1": "N", "2": "OS-"}, (137.16, 101.6, 0),
     "Puente rectificador (1000 V 1 A)"),
    ("J2", "SALIDA OS", "Connector:Screw_Terminal_01x02", "Clema_2P_P5.08mm", {"1": "OS+", "2": "OS-"},
     (180.34, 78.74, 0), "Salida a la palabra OS: 20 LED amarillos en serie (pin 1 = + ánodo, pin 2 = - cátodo)"),
]

NOTES = [
    (20.32, 20.32,
     "FUENTE CAPACITIVA NO AISLADA - PALABRA 'OS' (20 LED AMARILLOS EN SERIE) - 127 VCA 60 Hz\n"
     "PELIGRO: TODO el circuito (placa, cables y LED) queda a potencial de red. No tocar con la placa enchufada.\n"
     "Montar dentro de la caja del letrero, LED detrás del acrílico, sin partes metálicas accesibles."),
    (20.32, 120.65,
     "CÁLCULO (I = 4 f C (Vpico - Vtira)):\n"
     "  Vpico = 127 x 1.414 = 180 V      Vtira = 20 x 2.0 V = 40 V (38-44 V con Vf 1.9-2.2 V)\n"
     "  C1 = 334J (0.33 uF):  I = 240 x 0.33e-6 x (180 - 40) = 11.1 mA\n"
     "  Red 115 V / Vf alto:  I = 240 x 0.33e-6 x (162 - 44) =  9.3 mA\n"
     "  Red 140 V / Vf bajo:  I = 240 x 0.33e-6 x (198 - 38) = 12.7 mA   (LED 5 mm: máx 20 mA)\n"
     "  Alternativas: 224J -> 7.4 mA (más tenue)   474J -> 15.8 mA (más brillante)   224J + 104 en paralelo -> 10.8 mA\n"
     "  Potencia: LED 40 V x 11 mA = 0.44 W (22 mW c/u)   R1: (15 mA rms)^2 x 220 = 0.05 W   C1: ~0 W (reactiva)\n"
     "SIN electrolítico a la salida (igual que Radox): si la tira se abre no hay nada que reviente."),
]

POS = {  # (x, y, rot) del pad 1 en la PCB, mm desde la esquina superior izquierda
    "J1": (6.0, 11.0, 270),
    "R1": (15.0, 6.0, 0),
    "C1": (30.24, 14.0, 0),
    "R2": (30.0, 20.0, 0),
    "RV1": (16.0, 19.0, 0),
    "D4": (6.0, 28.0, 0),
    "D3": (45.24, 28.0, 180),
    "D2": (16.16, 36.0, 180),
    "D1": (35.08, 36.0, 0),
    "J2": (21.0, 44.0, 0),
}
HOLES = [(3.5, 3.5), (46.5, 3.5), (3.5, 46.5), (46.5, 46.5)]
W, H = 50.0, 50.0
TW = 1.2  # ancho de pista
TRACKS = {
    "L": [[(6.0, 11.0), (11.0, 6.0), (15.0, 6.0)]],
    "N": [[(6.0, 16.08), (6.0, 36.0)], [(6.0, 19.0), (16.0, 19.0)]],
    "A": [[(30.24, 6.0), (30.24, 14.0), (30.0, 20.0)], [(21.0, 20.3), (30.0, 20.0)]],
    "AC1": [[(45.24, 14.0), (45.24, 36.0)]],
    "OS-": [[(16.16, 28.0), (40.16, 28.0), (40.16, 41.0), (26.08, 41.0), (26.08, 44.0)]],
    "OS+": [[(16.16, 36.0), (35.08, 36.0)], [(21.0, 36.0), (21.0, 44.0)]],
}
TEXTS = [  # (texto, x, y, tamaño, ángulo, capa)
    ("L", 9.8, 11.0, 1.2, 0, "F.SilkS"),
    ("N", 9.8, 16.1, 1.2, 0, "F.SilkS"),
    ("127 VCA", 6.8, 21.2, 1.0, 0, "F.SilkS"),
    ("PELIGRO 127V NO TOCAR", 26.0, 24.3, 1.1, 0, "F.SilkS"),
    ("+", 17.6, 44.0, 1.6, 0, "F.SilkS"),
    ("-", 29.6, 44.0, 1.6, 0, "F.SilkS"),
    ("OS: 20 LED", 36.0, 45.6, 1.0, 0, "F.SilkS"),
    ("AMARILLOS", 36.0, 47.4, 1.0, 0, "F.SilkS"),
    ("FUENTE OS 127V v1", 26.0, 32.0, 1.4, 0, "B.Cu"),
]


def uid(ref):
    return str(uuid.uuid5(NS, ref))


def kname(n):
    return "/" + n


# ---------------------------------------------------------------- 1. huellas
def make_footprints():
    d = os.path.join(KI, LIB + ".pretty")
    os.makedirs(d, exist_ok=True)
    for name, spec in FOOTPRINTS.items():
        open(os.path.join(d, name + ".kicad_mod"), "w").write(dump(fplib.build(name, spec)) + "\n")
    open(os.path.join(d, "Barreno_M3_3.2mm.kicad_mod"), "w").write(dump(fplib.build_hole()) + "\n")
    d3 = os.path.join(KI, "3d")
    os.makedirs(d3, exist_ok=True)
    for spec in FOOTPRINTS.values():
        lib, name = spec[6].split("/")
        src = os.path.join(KMOD, lib + ".3dshapes", name + ".step")
        if os.path.exists(src):
            shutil.copy(src, d3)
    open(os.path.join(KI, "fp-lib-table"), "w").write(
        '(fp_lib_table\n  (version 7)\n  (lib (name "%s")(type "KiCad")(uri "${KIPRJMOD}/%s.pretty")(options "")'
        '(descr "Huellas THT con pads para transferencia de toner"))\n)\n' % (LIB, LIB))


# ---------------------------------------------------------------- 2. esquema
def make_schematic():
    sch.PROJECT, sch.ROOT_UUID, sch.NS = PROJECT, ROOT_UUID, NS
    sh = sch.Sheet()
    for ref, val, sym, fp, pins, (x, y, th), func in C:
        pp = sh.symbol(sym, ref, val, x, y, th, fp=LIB + ":" + fp, props_extra={"Funcion": func}, desc=func)
        for pn, (px, py, ux, uy) in pp.items():
            ex, ey = px + ux * 2.54, py + uy * 2.54
            sh.wire(px, py, ex, ey)
            sh.label(pins[pn], ex, ey, ux, uy)
    for x, y, s in NOTES:
        sh.text(s, x, y, 1.27)
    sh.text("Bloque: entrada y limitación", 45.72, 45.72, 1.8, bold=True)
    sh.text("Bloque: puente rectificador (4 x 1N4007)", 124.46, 43.18, 1.8, bold=True)
    sh.text("Bloque: salida a la tira", 167.64, 66.04, 1.8, bold=True)
    tb = sch.S("title_block", sch.S("title", "Fuente capacitiva 127 VCA para la palabra OS (20 LED amarillos)"),
               sch.S("date", datetime.date.today().isoformat()), sch.S("rev", "1.0"),
               sch.S("company", "PCB 50 x 50 mm, una cara, THT, transferencia de toner"),
               sch.S("comment", 1, "NO AISLADA: todo el circuito queda a potencial de red (igual que la placa Radox)"),
               sch.S("comment", 2, "I LED = 11 mA con C1 = 334J 400V"))
    doc = [Sym("kicad_sch"), sch.S("version", Sym("20250114")), sch.S("generator", "eeschema"),
           sch.S("generator_version", "9.0"), sch.S("uuid", ROOT_UUID), sch.S("paper", "A4"), tb,
           [Sym("lib_symbols")] + list(sh.libs.values())]
    doc += sh.items
    doc.append(sch.S("sheet_instances", sch.S("path", "/", sch.S("page", "1"))))
    doc.append(sch.S("embedded_fonts", Sym("no")))
    open(os.path.join(KI, PROJECT + ".kicad_sch"), "w").write(dump(doc) + "\n")


# ---------------------------------------------------------------- 3. PCB
def make_pcb():
    import pcbnew
    OX, OY = 100.0, 100.0
    mm = pcbnew.FromMM

    def P(x, y):
        return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))

    board = pcbnew.BOARD()
    board.GetDesignSettings().SetCopperLayerCount(2)
    nets = {}
    for n in sorted({n for c in C for n in c[4].values()}):
        ni = pcbnew.NETINFO_ITEM(board, kname(n))
        board.Add(ni)
        nets[n] = ni
    pts = [(0, 0), (W, 0), (W, H), (0, H)]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(P(*a))
        s.SetEnd(P(*b))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.15))
        board.Add(s)
    libdir = os.path.join(KI, LIB + ".pretty")
    for ref, val, sym, fpn, pins, _, func in C:
        x, y, r = POS[ref]
        fp = pcbnew.FootprintLoad(libdir, fpn)
        fp.SetFPID(pcbnew.LIB_ID(LIB, fpn))
        fp.SetReference(ref)
        fp.SetValue(val)
        fp.SetPosition(P(x, y))
        fp.SetOrientationDegrees(r)
        fp.SetPath(pcbnew.KIID_PATH("/" + uid(ref)))
        fp.Value().SetVisible(False)
        board.Add(fp)
        for pad in fp.Pads():
            pad.SetNet(nets[pins[pad.GetNumber()]])
    for i, (x, y) in enumerate(HOLES):
        fp = pcbnew.FootprintLoad(libdir, "Barreno_M3_3.2mm")
        fp.SetFPID(pcbnew.LIB_ID(LIB, "Barreno_M3_3.2mm"))
        fp.SetReference("H%d" % (i + 1))
        fp.SetPosition(P(x, y))
        fp.SetBoardOnly(True)
        fp.SetExcludedFromBOM(True)
        fp.SetExcludedFromPosFiles(True)
        fp.Reference().SetVisible(False)
        board.Add(fp)
    for n, paths in TRACKS.items():
        for path in paths:
            for a, b in zip(path, path[1:]):
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(P(*a))
                t.SetEnd(P(*b))
                t.SetWidth(mm(TW))
                t.SetLayer(pcbnew.B_Cu)
                t.SetNet(nets[n])
                board.Add(t)
    for s, x, y, size, ang, layer in TEXTS:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(s)
        t.SetPosition(P(x, y))
        t.SetLayer(pcbnew.F_SilkS if layer == "F.SilkS" else pcbnew.B_Cu)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
        t.SetTextThickness(mm(max(0.18, size * 0.16)))
        t.SetTextAngleDegrees(ang)
        if layer == "B.Cu":
            t.SetMirrored(True)
        board.Add(t)
    board.Save(os.path.join(KI, PROJECT + ".kicad_pcb"))


# ---------------------------------------------------------------- 4. proyecto y reglas
def make_project():
    pro = json.load(open("/usr/share/kicad/template/kicad.kicad_pro"))
    ds = pro.setdefault("board", {}).setdefault("design_settings", {})
    ds.setdefault("rules", {}).update({
        "min_clearance": 1.5, "min_track_width": 1.2, "min_copper_edge_clearance": 1.0,
        "min_through_hole_diameter": 0.8, "min_hole_to_hole": 0.5, "min_hole_clearance": 0.25,
        "min_via_diameter": 0.8, "min_via_annular_width": 0.3, "min_connection": 0.0,
        "min_silk_clearance": 0.0, "min_text_height": 0.8, "min_text_thickness": 0.12,
        "allow_blind_buried_vias": False, "allow_microvias": False})
    ds.setdefault("rule_severities", {}).update({
        "silk_over_copper": "ignore", "silk_overlap": "ignore", "silk_edge_clearance": "ignore",
        "lib_footprint_mismatch": "ignore", "lib_footprint_issues": "ignore",
        "text_height": "ignore", "text_thickness": "ignore"})
    ds["track_widths"] = [0.0, 1.2]
    ns = pro.setdefault("net_settings", {})
    for c in ns.get("classes", []):
        if c.get("name") == "Default":
            c.update({"clearance": 1.5, "track_width": 1.2})
    pro.setdefault("meta", {})["filename"] = PROJECT + ".kicad_pro"
    json.dump(pro, open(os.path.join(KI, PROJECT + ".kicad_pro"), "w"), indent=2)
    open(os.path.join(KI, PROJECT + ".kicad_dru"), "w").write(
        '(version 1)\n'
        '(rule "Red 127 V: separacion minima 1.5 mm"\n  (constraint clearance (min 1.5mm)))\n'
        '(rule "Pistas >= 1.2 mm"\n  (condition "A.Type == \'track\'")\n  (constraint track_width (min 1.2mm)))\n')


if __name__ == "__main__":
    os.makedirs(KI, exist_ok=True)
    make_footprints()
    make_schematic()
    make_pcb()
    make_project()
    print("ok")
