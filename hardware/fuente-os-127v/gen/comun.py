"""Piezas comunes de las placas de 127 VCA del letrero (fuente OS y secuenciador de flechas).

Construye huellas, esquema, PCB (pistas a mano o con el ruteador de una cara) y reglas del
proyecto a partir de una lista de componentes. Se ejecuta dentro del contenedor de KiCad 9.
Reutiliza sexpr.py, fplib.py, sch.py y router.py del proyecto controlador-flechas-36v.
"""
import os, sys, json, shutil, uuid, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
GEN36 = os.path.abspath(os.path.join(HERE, "..", "..", "controlador-flechas-36v", "gen"))
sys.path.insert(0, GEN36)
from sexpr import dump, Sym  # noqa: E402
import fplib  # noqa: E402
import sch  # noqa: E402

KMOD = "/usr/share/kicad/3dmodels"
RND, OVV = "circle", "oval"

# nombre: (origen, {pad: (x, y)}, forma, (w, h), taladro, forma_pad1, modelo_3d)
FOOTPRINTS = {
    "Clema_2P_P5.08mm": fplib.FOOTPRINTS["Clema_2P_P5.08mm"],
    "Clema_4P_P5.08mm": fplib.FOOTPRINTS["Clema_4P_P5.08mm"],
    "R_1W_P15.24mm": ("Resistor_THT/R_Axial_DIN0411_L9.9mm_D3.6mm_P15.24mm_Horizontal", {}, RND, (2.6, 2.6), 1.0, None,
                      "Resistor_THT/R_Axial_DIN0411_L9.9mm_D3.6mm_P15.24mm_Horizontal"),
    "R_1W_Vertical_P7.62mm": ("Resistor_THT/R_Axial_DIN0411_L9.9mm_D3.6mm_P7.62mm_Vertical", {}, RND, (2.6, 2.6), 1.0,
                              None, "Resistor_THT/R_Axial_DIN0411_L9.9mm_D3.6mm_P7.62mm_Vertical"),
    "R_Axial_P15.24mm": ("Resistor_THT/R_Axial_DIN0207_L6.3mm_D2.5mm_P15.24mm_Horizontal", {}, RND, (2.4, 2.4), 0.8,
                         None, "Resistor_THT/R_Axial_DIN0207_L6.3mm_D2.5mm_P15.24mm_Horizontal"),
    "R_Axial_P10.16mm": fplib.FOOTPRINTS["R_Axial_P10.16mm"],
    "R_Vertical_P5.08mm": fplib.FOOTPRINTS["R_Vertical_P5.08mm"],
    "C_Poliester_P10-15mm": ("Capacitor_THT/C_Rect_L18.0mm_W6.0mm_P15.00mm_FKS3_FKP3", {}, RND, (2.6, 2.6), 1.0, None,
                             "Capacitor_THT/C_Rect_L18.0mm_W6.0mm_P15.00mm_FKS3_FKP3"),
    "Varistor_D7mm_P5mm": ("Varistor/RV_Disc_D7mm_W3.4mm_P5mm", {}, RND, (2.4, 2.4), 1.0, None,
                           "Varistor/RV_Disc_D7mm_W3.4mm_P5mm"),
    # 2W10 / W10M redondo: + y - en diagonal, ~ en la otra diagonal (pines = símbolo D_Bridge_+-AA)
    "Puente_2W10": ("Diode_THT/Diode_Bridge_Round_D9.8mm", {"2": (5.08, 5.08), "3": (0.0, 5.08)}, RND, (2.4, 2.4),
                    1.0, "rect", "Diode_THT/Diode_Bridge_Round_D9.8mm"),
    "D_DO-41_P10.16mm": fplib.FOOTPRINTS["D_DO-41_P10.16mm"],
    "D_DO-35_P7.62mm": fplib.FOOTPRINTS["D_DO-35_P7.62mm"],
    "C_Disc_P5.08mm": fplib.FOOTPRINTS["C_Disc_P5.08mm"],
    "CP_Radial_D8.0mm_P3.81mm": fplib.FOOTPRINTS["CP_Radial_D8.0mm_P3.81mm"],
    "CP_Radial_D5.0mm_P2.54mm": fplib.FOOTPRINTS["CP_Radial_D5.0mm_P2.54mm"],
    "DIP-8_W7.62mm": fplib.FOOTPRINTS["DIP-8_W7.62mm"],
    "DIP-16_W7.62mm": fplib.FOOTPRINTS["DIP-16_W7.62mm"],
    "TO-92_SCR": ("Package_TO_SOT_THT/TO-92_Inline_Wide", {}, OVV, (1.6, 2.6), 0.8, "rect",
                  "Package_TO_SOT_THT/TO-92_Inline_Wide"),
    "Trimpot_3296W": fplib.FOOTPRINTS["Trimpot_3296W"],
}
PIN_TEXT = {"TO-92_SCR": "K G A"}
fplib.PIN_TEXT.update(PIN_TEXT)


def _silk(text, x, y, size=1.0):
    return [Sym("fp_text"), Sym("user"), text, [Sym("at"), x, y, 0], [Sym("layer"), "F.SilkS"],
            [Sym("uuid"), str(uuid.uuid4())],
            [Sym("effects"), [Sym("font"), [Sym("size"), size, size], [Sym("thickness"), 0.18]]]]


def build_cables(n, P=5.08):
    """Pads para soldar cables (columna de n pads, paso P): más chico que una clema."""
    S = lambda *a: [Sym(a[0])] + list(a[1:])
    L = (n - 1) * P
    fp = [Sym("footprint"), "Cables_%dP_P5.08mm" % n, S("version", Sym("20241229")), S("generator", "pcbnew"),
          S("generator_version", "9.0"), S("layer", "F.Cu"),
          S("descr", "%d pads para soldar cable (1.3 mm), paso %.2f mm, pads para toner" % (n, P)),
          [Sym("property"), "Reference", "J**", S("at", 0, -3.0, 0), S("layer", "F.SilkS"),
           S("uuid", str(uuid.uuid4())), S("effects", S("font", S("size", 1, 1), S("thickness", 0.15)))],
          [Sym("property"), "Value", "Cables", S("at", 0, L + 3.0, 0), S("layer", "F.Fab"),
           S("uuid", str(uuid.uuid4())), S("effects", S("font", S("size", 1, 1), S("thickness", 0.15)))],
          S("attr", Sym("through_hole")),
          [Sym("fp_rect"), S("start", -2.0, -2.0), S("end", 2.0, L + 2.0), S("stroke", S("width", 0.12), S("type", Sym("solid"))),
           S("fill", Sym("no")), S("layer", "F.SilkS"), S("uuid", str(uuid.uuid4()))],
          [Sym("fp_rect"), S("start", -2.25, -2.25), S("end", 2.25, L + 2.25), S("stroke", S("width", 0.05), S("type", Sym("solid"))),
           S("fill", Sym("no")), S("layer", "F.CrtYd"), S("uuid", str(uuid.uuid4()))]]
    for i in range(n):
        fp.append(fplib.pad(str(i + 1), "rect" if i == 0 else RND, 0, i * P, (3.0, 3.0), 1.3))
    return fp


def build_jumper_bottom(L, name):
    """Puente de cable forrado soldado del lado del cobre: dos pads sin barreno en B.Cu (no se perfora)."""
    S = lambda *a: [Sym(a[0])] + list(a[1:])

    def smd(num, x):
        return [Sym("pad"), num, Sym("smd"), Sym("circle"), S("at", x, 0), S("size", 2.4, 2.4),
                S("layers", "B.Cu", "B.Mask"), S("uuid", str(uuid.uuid4()))]
    return [Sym("footprint"), name, S("version", Sym("20241229")), S("generator", "pcbnew"),
            S("generator_version", "9.0"), S("layer", "F.Cu"),
            S("descr", "Puente de cable forrado del lado del cobre, %.2f mm, sin barrenos" % L),
            [Sym("property"), "Reference", "W**", S("at", L / 2, -1.8, 0), S("layer", "F.SilkS"),
             S("uuid", str(uuid.uuid4())), S("effects", S("font", S("size", 0.9, 0.9), S("thickness", 0.15)))],
            [Sym("property"), "Value", "Puente abajo", S("at", L / 2, 1.8, 0), S("layer", "F.Fab"),
             S("uuid", str(uuid.uuid4())), S("effects", S("font", S("size", 0.8, 0.8), S("thickness", 0.12)))],
            S("attr", Sym("smd")),
            [Sym("fp_line"), S("start", 1.4, 0), S("end", L - 1.4, 0), S("stroke", S("width", 0.3), S("type", Sym("dash"))),
             S("layer", "F.SilkS"), S("uuid", str(uuid.uuid4()))],
            smd("1", 0), smd("2", L)]


def build_fp(name):
    if name.startswith("Cables_"):
        return build_cables(int(name.split("_")[1][0]))
    fp = fplib.build(name, FOOTPRINTS[name])
    if name == "C_Poliester_P10-15mm":
        # segundo barreno para el pin 2 a 10 mm: sirve para capacitores de paso 10 mm o 15 mm
        idx = max(i for i, e in enumerate(fp) if isinstance(e, list) and e and e[0] == "pad")
        fp.insert(idx + 1, fplib.pad("2", RND, 10.0, 0.0, (2.6, 2.6), 1.0))
        fp.insert(idx + 2, _silk("10", 10.0, 2.2, 0.8))
        fp.insert(idx + 3, _silk("15", 15.0, 2.2, 0.8))
    if name == "Puente_2W10":
        for t, x, y in (("+", -2.2, -1.2), ("-", 7.3, 6.3), ("~", -2.2, 6.3), ("~", 7.3, -1.2)):
            fp.insert(-1, _silk(t, x, y, 1.2))
    return fp


def make_footprints(ki, lib, names):
    d = os.path.join(ki, lib + ".pretty")
    os.makedirs(d, exist_ok=True)
    for name in names:
        open(os.path.join(d, name + ".kicad_mod"), "w").write(dump(build_fp(name)) + "\n")
    open(os.path.join(d, "Barreno_M3_3.2mm.kicad_mod"), "w").write(dump(fplib.build_hole()) + "\n")
    d3 = os.path.join(ki, "3d")
    os.makedirs(d3, exist_ok=True)
    for name in names:
        if name not in FOOTPRINTS:
            continue
        libn, m = FOOTPRINTS[name][6].split("/")
        for base in (KMOD,):
            src = os.path.join(base, libn + ".3dshapes", m + ".step")
            if os.path.exists(src):
                shutil.copy(src, d3)
    open(os.path.join(ki, "fp-lib-table"), "w").write(
        '(fp_lib_table\n  (version 7)\n  (lib (name "%s")(type "KiCad")(uri "${KIPRJMOD}/%s.pretty")(options "")'
        '(descr "Huellas THT con pads para transferencia de toner"))\n)\n' % (lib, lib))


def make_schematic(ki, project, lib, root_uuid, ns, comps, notes, texts, title, comments, paper="A4", flags=(),
                   company="PCB 50 x 50 mm, una cara, THT, transferencia de toner"):
    """comps: (ref, valor, símbolo, huella, {pin: red|None}, (x, y, rot), función)."""
    sch.PROJECT, sch.ROOT_UUID, sch.NS = project, root_uuid, ns
    sh = sch.Sheet()
    for ref, val, sym, fp, pins, (x, y, th), func in comps:
        pp = sh.symbol(sym, ref, val, x, y, th, fp=lib + ":" + fp, props_extra={"Funcion": func}, desc=func)
        for pn, (px, py, ux, uy) in pp.items():
            net = pins.get(pn)
            if net is None:
                sh.noconn(px, py)
                continue
            ex, ey = px + ux * 2.54, py + uy * 2.54
            sh.wire(px, py, ex, ey)
            sh.label(net, ex, ey, ux, uy)
    saved = dict(sch.DZ.POWER)
    sch.DZ.POWER.clear()          # sin símbolos de alimentación globales: todas las redes son etiquetas locales
    for net, x, y in flags:
        sh.flag(net, x, y)
    sch.DZ.POWER.update(saved)
    for x, y, s in notes:
        sh.text(s, x, y, 1.27)
    for x, y, s in texts:
        sh.text(s, x, y, 1.8, bold=True)
    tb = sch.S("title_block", sch.S("title", title), sch.S("date", datetime.date.today().isoformat()),
               sch.S("rev", "1.0"), sch.S("company", company),
               *[sch.S("comment", i + 1, c) for i, c in enumerate(comments)])
    doc = [Sym("kicad_sch"), sch.S("version", Sym("20250114")), sch.S("generator", "eeschema"),
           sch.S("generator_version", "9.0"), sch.S("uuid", root_uuid), sch.S("paper", paper), tb,
           [Sym("lib_symbols")] + list(sh.libs.values())]
    doc += sh.items
    doc.append(sch.S("sheet_instances", sch.S("path", "/", sch.S("page", "1"))))
    doc.append(sch.S("embedded_fonts", Sym("no")))
    open(os.path.join(ki, project + ".kicad_sch"), "w").write(dump(doc) + "\n")


def pin_names(lib_id):
    """{número: nombre} de los pines de un símbolo (para nombrar las redes sin conexión como el esquema)."""
    from sexpr import find1
    out = {}

    def walk(e):
        for x in e:
            if isinstance(x, list) and x:
                if x[0] == "pin":
                    out[find1(x, "number")[1]] = find1(x, "name")[1]
                else:
                    walk(x)
    walk(sch.lib_symbol(lib_id))
    return out


class Board:
    """PCB de W x H mm con origen en (100, 100) de la hoja."""
    OX, OY = 100.0, 100.0

    def __init__(self, W, H, lib, ki, ns, comps, pos, holes=()):
        import pcbnew
        self.pcbnew, self.W, self.H, self.lib, self.ki = pcbnew, W, H, lib, ki
        mm = pcbnew.FromMM
        self.mm = mm
        b = self.board = pcbnew.BOARD()
        b.GetDesignSettings().SetCopperLayerCount(2)
        self.nets = {}
        for n in sorted({n for c in comps for n in c[4].values() if n}):
            ni = pcbnew.NETINFO_ITEM(b, "/" + n)
            b.Add(ni)
            self.nets[n] = ni
        pts = [(0, 0), (W, 0), (W, H), (0, H)]
        for a, c in zip(pts, pts[1:] + pts[:1]):
            s = pcbnew.PCB_SHAPE(b)
            s.SetShape(pcbnew.SHAPE_T_SEGMENT)
            s.SetStart(self.P(*a))
            s.SetEnd(self.P(*c))
            s.SetLayer(pcbnew.Edge_Cuts)
            s.SetWidth(mm(0.15))
            b.Add(s)
        libdir = os.path.join(ki, lib + ".pretty")
        self.fps = {}
        for ref, val, sym, fpn, pins, _, func in comps:
            x, y, r = pos[ref]
            fp = pcbnew.FootprintLoad(libdir, fpn)
            fp.SetFPID(pcbnew.LIB_ID(lib, fpn))
            fp.SetReference(ref)
            fp.SetValue(val)
            fp.SetPosition(self.P(x, y))
            fp.SetOrientationDegrees(r)
            fp.SetPath(pcbnew.KIID_PATH("/" + str(uuid.uuid5(ns, ref))))
            fp.Value().SetVisible(False)
            b.Add(fp)
            for pad in fp.Pads():
                n = pins.get(pad.GetNumber())
                if n:
                    pad.SetNet(self.nets[n])
                else:
                    nm = pin_names(sym).get(pad.GetNumber(), "")
                    nm = "" if nm in ("", "~") else nm + "-"
                    ni = pcbnew.NETINFO_ITEM(b, "unconnected-(%s-%sPad%s)" % (ref, nm, pad.GetNumber()))
                    b.Add(ni)
                    pad.SetNet(ni)
            self.fps[ref] = fp
        for i, (x, y) in enumerate(holes):
            fp = pcbnew.FootprintLoad(libdir, "Barreno_M3_3.2mm")
            fp.SetFPID(pcbnew.LIB_ID(lib, "Barreno_M3_3.2mm"))
            fp.SetReference("H%d" % (i + 1))
            fp.SetPosition(self.P(x, y))
            fp.SetBoardOnly(True)
            fp.SetExcludedFromBOM(True)
            fp.SetExcludedFromPosFiles(True)
            fp.Reference().SetVisible(False)
            b.Add(fp)

    def P(self, x, y):
        return self.pcbnew.VECTOR2I(self.mm(self.OX + x), self.mm(self.OY + y))

    def pad_xy(self, tok):
        ref, num = tok.split(".")
        for p in self.fps[ref].Pads():
            if p.GetNumber() == num:
                q = p.GetPosition()
                return (round(self.pcbnew.ToMM(q.x) - self.OX, 4), round(self.pcbnew.ToMM(q.y) - self.OY, 4))
        raise KeyError(tok)

    def add_tracks(self, tracks, widths):
        pcbnew = self.pcbnew
        for n, paths in tracks.items():
            n0 = n[1:] if n.startswith("/") else n
            for path in paths:
                for a, c in zip(path, path[1:]):
                    if tuple(a) == tuple(c):
                        continue
                    t = pcbnew.PCB_TRACK(self.board)
                    t.SetStart(self.P(*a))
                    t.SetEnd(self.P(*c))
                    t.SetWidth(self.mm(widths.get(n0, 0.8)))
                    t.SetLayer(pcbnew.B_Cu)
                    t.SetNet(self.nets[n0])
                    self.board.Add(t)

    def pads_geom(self):
        """Pads como objetos router.Pad (coordenadas de la placa)."""
        from router import Pad
        pcbnew = self.pcbnew
        out = []
        for fp in self.fps.values():
            ang = round(fp.GetOrientationDegrees()) % 180
            for pad in fp.Pads():
                pos = pad.GetPosition()
                sz = pad.GetSize(pcbnew.B_Cu)
                w, h = pcbnew.ToMM(sz.x), pcbnew.ToMM(sz.y)
                if ang == 90:
                    w, h = h, w
                shp = {pcbnew.PAD_SHAPE_CIRCLE: "circle", pcbnew.PAD_SHAPE_RECTANGLE: "rect",
                       pcbnew.PAD_SHAPE_OVAL: "oval"}.get(pad.GetShape(pcbnew.B_Cu), "rect")
                net = pad.GetNetname()
                net = net if (net and not net.startswith("unconnected")) else None
                out.append(Pad(fp.GetReference(), pad.GetNumber(), net, pcbnew.ToMM(pos.x) - self.OX,
                               pcbnew.ToMM(pos.y) - self.OY, shp, w, h))
        return out

    def route(self, widths, clearance, iters=40, pre=None, keepouts=(), first=(), last=(), log=print,
              jumpers=(), jcost=60.0):
        """Rutea en B.Cu con el ruteador de una cara. jumpers = largos permitidos de puente de alambre
        (vacío = sin puentes). Devuelve (fallidas, pistas, puentes)."""
        from router import NegotiatedRouter, Pad
        pcbnew = self.pcbnew
        pads = []
        for fp in self.fps.values():
            ang = round(fp.GetOrientationDegrees()) % 180
            for pad in fp.Pads():
                pos = pad.GetPosition()
                sz = pad.GetSize(pcbnew.B_Cu)
                w, h = pcbnew.ToMM(sz.x), pcbnew.ToMM(sz.y)
                if ang == 90:
                    w, h = h, w
                shp = {pcbnew.PAD_SHAPE_CIRCLE: "circle", pcbnew.PAD_SHAPE_RECTANGLE: "rect",
                       pcbnew.PAD_SHAPE_OVAL: "oval"}.get(pad.GetShape(pcbnew.B_Cu), "rect")
                net = pad.GetNetname()
                net = net if (net and not net.startswith("unconnected")) else None
                pads.append(Pad(fp.GetReference(), pad.GetNumber(), net, pcbnew.ToMM(pos.x) - self.OX,
                                pcbnew.ToMM(pos.y) - self.OY, shp, w, h))
        R = NegotiatedRouter(self.W, self.H, pads, {"/" + k: v for k, v in widths.items()}, clearance=clearance,
                             margin=0.1, edge=1.0, keepouts=list(keepouts), jumper_lengths=tuple(jumpers),
                             jumper_cost=jcost,
                             pre={"/" + k: v for k, v in (pre or {}).items()})
        failed, order = R.route_negotiated(iters=iters, first=["/" + n for n in first], last=["/" + n for n in last],
                                           log=log)
        self.router = R
        return failed, R.tracks, [(n, tuple(a), tuple(b)) for n, a, b in R.jumpers]

    def texts(self, texts):
        pcbnew = self.pcbnew
        for s, x, y, size, ang, layer in texts:
            t = pcbnew.PCB_TEXT(self.board)
            t.SetText(s)
            t.SetPosition(self.P(x, y))
            t.SetLayer(pcbnew.F_SilkS if layer == "F.SilkS" else pcbnew.B_Cu)
            t.SetTextSize(pcbnew.VECTOR2I(self.mm(size), self.mm(size)))
            t.SetTextThickness(self.mm(max(0.18, size * 0.16)))
            t.SetTextAngleDegrees(ang)
            if layer == "B.Cu":
                t.SetMirrored(True)
            self.board.Add(t)

    def ref_pos(self, refpos):
        for ref, (x, y, ang) in refpos.items():
            t = self.fps[ref].Reference()
            t.SetPosition(self.P(x, y))
            t.SetTextAngleDegrees(ang)

    def save(self, project):
        self.board.Save(os.path.join(self.ki, project + ".kicad_pcb"))


def make_project(ki, project, red_nets, clr_red=1.5, clr=0.6, track=0.8):
    pro = json.load(open("/usr/share/kicad/template/kicad.kicad_pro"))
    ds = pro.setdefault("board", {}).setdefault("design_settings", {})
    ds.setdefault("rules", {}).update({
        "min_clearance": clr, "min_track_width": track, "min_copper_edge_clearance": 0.8,
        "min_through_hole_diameter": 0.8, "min_hole_to_hole": 0.5, "min_hole_clearance": 0.25,
        "min_via_diameter": 0.8, "min_via_annular_width": 0.3, "min_connection": 0.0,
        "min_silk_clearance": 0.0, "min_text_height": 0.8, "min_text_thickness": 0.12,
        "allow_blind_buried_vias": False, "allow_microvias": False})
    ds.setdefault("rule_severities", {}).update({
        "silk_over_copper": "ignore", "silk_overlap": "ignore", "silk_edge_clearance": "ignore",
        "lib_footprint_mismatch": "ignore", "lib_footprint_issues": "ignore",
        "text_height": "ignore", "text_thickness": "ignore"})
    ds["track_widths"] = [0.0, track, 1.2]
    ns = pro.setdefault("net_settings", {})
    base = {"bus_width": 12, "clearance": clr, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25,
            "diff_pair_width": 0.2, "line_style": 0, "microvia_diameter": 0.3, "microvia_drill": 0.1,
            "name": "Default", "pcb_color": "rgba(0, 0, 0, 0.000)", "priority": 2147483647,
            "schematic_color": "rgba(0, 0, 0, 0.000)", "track_width": track, "via_diameter": 1.6,
            "via_drill": 0.8, "wire_width": 6}
    red = dict(base)
    red.update({"name": "Red127V", "clearance": clr_red, "track_width": 1.2, "priority": 0})
    ns["classes"] = [base, red]
    ns["netclass_patterns"] = [{"netclass": "Red127V", "pattern": "/" + n} for n in sorted(red_nets)]
    ns["meta"] = {"version": 4}
    pro.setdefault("meta", {})["filename"] = project + ".kicad_pro"
    json.dump(pro, open(os.path.join(ki, project + ".kicad_pro"), "w"), indent=2)
    open(os.path.join(ki, project + ".kicad_dru"), "w").write(
        '(version 1)\n'
        '(rule "Red 127 V: separacion minima %.1f mm"\n  (condition "A.NetClass == \'Red127V\'")\n'
        '  (constraint clearance (min %.1fmm)))\n'
        '(rule "Pistas >= %.1f mm"\n  (condition "A.Type == \'track\'")\n  (constraint track_width (min %.1fmm)))\n'
        % (clr_red, clr_red, track, track))


def split_jumper_nets(pads, tracks, jumpers, widths):
    """Separa en redes distintas los tramos de cobre unidos solo por un puente de alambre.

    pads: router.Pad; tracks: {"/red": [polilínea]}; jumpers: [("/red", (x, y), (x, y))].
    Devuelve (pistas renombradas, {"REF.pin": red_nueva}, [(ref_puente, red_a, red_b, p_a, p_b)]).
    """
    import numpy as np
    from router import Pad
    out_tracks = {k: [list(map(tuple, pl)) for pl in v] for k, v in tracks.items()}
    netsplit, wires = {}, []
    for k, (net, pa, pb) in enumerate(jumpers):
        n0 = net[1:]
        w = widths.get(n0, 0.8)
        segs = [(tuple(a), tuple(b)) for pl in out_tracks.get(net, []) for a, b in zip(pl[:-1], pl[1:])]
        items = [("S", s) for s in segs] + [("P", p) for p in pads if p.net == net] + \
                [("J", Pad("W", str(q), net, x, y, "circle", 2.4, 2.4)) for q, (x, y) in ((1, pa), (2, pb))]
        par = list(range(len(items)))

        def f(a):
            while par[a] != a:
                par[a] = par[par[a]]
                a = par[a]
            return a

        def pts(sg, m=60):
            (x1, y1), (x2, y2) = sg
            t = np.linspace(0, 1, m)
            return x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
        for i, (ti, a) in enumerate(items):
            for j in range(i + 1, len(items)):
                tj, b = items[j]
                if ti == "S" and tj == "S":
                    X, Y = pts(a)
                    (c, d), (e, g) = b
                    vx, vy = e - c, g - d
                    L2 = vx * vx + vy * vy or 1e-12
                    t = np.clip(((X - c) * vx + (Y - d) * vy) / L2, 0, 1)
                    hit = float(np.min(np.hypot(X - (c + t * vx), Y - (d + t * vy)))) <= w + 1e-3
                elif ti == "S" or tj == "S":
                    sg, pd = (a, b) if ti == "S" else (b, a)
                    X, Y = pts(sg)
                    hit = float(np.min(pd.dist(X, Y))) <= w / 2 + 1e-3
                else:
                    continue
                if hit:
                    par[f(i)] = f(j)
        groups = {}
        for i, (ti, it) in enumerate(items):
            groups.setdefault(f(i), []).append((ti, it))
        # isla principal: la que tiene más pads reales
        order = sorted(groups, key=lambda g: -sum(1 for t, it in groups[g] if t == "P"))
        main, other = order[0], order[1] if len(order) > 1 else None
        if other is None:
            continue
        new = "%s_W%d" % (n0, k + 1)
        side_a = any(t == "J" and it.num == "1" for t, it in groups[main])
        for t, it in groups[other]:
            if t == "P":
                netsplit["%s.%s" % (it.ref, it.num)] = new
        keep, moved = [], []
        for pl in out_tracks.get(net, []):
            gs = {f(items.index(("S", (tuple(a), tuple(b))))) for a, b in zip(pl[:-1], pl[1:])}
            (moved if other in gs else keep).append(pl)
        out_tracks[net] = keep
        out_tracks["/" + new] = moved
        wires.append(("W%d" % (k + 1), n0, new, pa if side_a else pb, pb if side_a else pa))
    return out_tracks, netsplit, wires
