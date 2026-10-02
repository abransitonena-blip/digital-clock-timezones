"""Librería compartida para generar placas LetreroLab con KiCad 9 (se ejecuta dentro del contenedor de KiCad).

Cada placa es un módulo de datos ("spec") con sus piezas, posiciones, planos de cobre y reglas, y llama a
placa.main(spec). Flujo completo (lo maneja tools/rutear.sh):

    python3 gen/make.py               esquema + placa sin rutear + <PROYECTO>.dsn para Freerouting
    python3 gen/make.py --import k    importa la pasada k del ruteador y exporta la pasada k+1
    python3 gen/make.py --final k     importa la última pasada, quita las áreas de ruteo, rellena planos y serigrafía

Atributos del spec (los opcionales tienen valor por omisión en _defaults):
  PROJECT, HERE (carpeta gen/), NS (uuid), ROOT_UUID, C_ [(ref, valor, símbolo, huella, {pata: red}, función)],
  POS {ref: (x, y, giro)} o (x, y, giro, "B") para el lado de abajo, W, H, HOLES [(x, y)],
  NETCLASS {nombre: (ancho, separación, [redes])}, POWER_ZONES [(red, polígono)], KEEPOUT_NETS,
  PRE [(red, ancho, [puntos], "B"?)], PREVIAS [(red, x, y)], VIAS [(x, y)] de GND,
  SIN_COBRE [polígonos sin cobre en ambas capas, p. ej. bajo una antena], RETORNO [polígonos de la capa inferior
  sin pistas: camino de regreso de la corriente fuerte], SILK [(texto, x, y, alto, "F"/"B")],
  FLAGS, NOTES, TITLE, SUBTITLES, COMPANY, PAPER, DRU (texto de reglas propias), RED_HV (clase que se aleja
  5 mm al rutear), DESCONECTAR [(ref, pata)] (patas con red solo para el ruteador), RADIO_ESQUINA.
"""
import os, sys, json, uuid

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fuente-os-127v", "gen"))
import comun  # noqa: E402
import pcbnew  # noqa: E402

FPL = "/usr/share/kicad/footprints"
HUELLAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "huellas")   # huellas propias (LetreroLab.pretty)
mm = pcbnew.FromMM


def _defaults(S):
    for k, v in dict(HOLES=[], NETCLASS={}, POWER_ZONES=[], KEEPOUT_NETS=(), PRE=[], PREVIAS=[], VIAS=[],
                     SIN_COBRE=[], RETORNO=[], SILK=[], FLAGS=[], NOTES=[], SUBTITLES=[], COMPANY="", PAPER="A3", DRU="",
                     RED_HV=None, DESCONECTAR=[], RADIO_ESQUINA=0.0, MODELOS={}, CAPAS=2, COSTURA=0.0, SIN_PISTAS=[], SIN_RELLENO=[], ZONAS_FINALES=[],
                     PLANOS=[("GND", "In1"), ("GND", "In2")]).items():
        if not hasattr(S, k):
            setattr(S, k, v)
    S.ROOT = os.path.abspath(os.path.join(S.HERE, ".."))
    S.KI = os.path.join(S.ROOT, "kicad")


def P(x, y):
    return pcbnew.VECTOR2I(mm(100 + x), mm(100 + y))


def _contorno(S, b):
    """Rectángulo W x H, con esquinas redondeadas si RADIO_ESQUINA > 0 (cajas más seguras al tacto)."""
    W, H, r = S.W, S.H, S.RADIO_ESQUINA
    segs = [((r, 0), (W - r, 0)), ((W, r), (W, H - r)), ((W - r, H), (r, H)), ((0, H - r), (0, r))]
    for a, c in segs:
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(P(*a)); s.SetEnd(P(*c)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); b.Add(s)
    if r > 0:
        k = r * (1 - 0.5 ** 0.5)
        for a, m, c in (((0, r), (k, k), (r, 0)), ((W - r, 0), (W - k, k), (W, r)),
                        ((W, H - r), (W - k, H - k), (W - r, H)), ((r, H), (k, H - k), (0, H - r))):
            s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_ARC)
            s.SetArcGeometry(P(*a), P(*m), P(*c))
            s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); b.Add(s)


def build_board(S):
    b = pcbnew.BOARD()
    b.GetDesignSettings().SetCopperLayerCount(S.CAPAS)
    for l in _internas(S):
        b.SetLayerType(l, pcbnew.LT_POWER)    # planos: Freerouting no rutea en ellos, solo llega con vías
    nets = {}
    for c in S.C_:
        for n in c[4].values():
            if n and n not in nets:
                nets[n] = pcbnew.NETINFO_ITEM(b, "/" + n)
                b.Add(nets[n])
    _contorno(S, b)
    for ref, val, sym, f, pins, func in S.C_:
        lib, name = f.split(":")
        carpeta = os.path.join(HUELLAS, lib + ".pretty") if lib == "LetreroLab" else os.path.join(FPL, lib + ".pretty")
        fp = pcbnew.FootprintLoad(carpeta, name)
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref); fp.SetValue(val)
        pos = S.POS[ref]
        fp.SetPosition(P(pos[0], pos[1])); fp.SetOrientationDegrees(pos[2])
        fp.SetPath(pcbnew.KIID_PATH("/" + str(uuid.uuid5(S.NS, ref))))
        fp.Value().SetVisible(False)
        b.Add(fp)
        if len(pos) > 3 and pos[3] == "B":
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        for pad in fp.Pads():
            num = pad.GetNumber()
            if not num:
                continue
            n = pins.get(num)
            if n:
                pad.SetNet(nets[n])
            else:
                nm = comun.pin_names(sym).get(num, "")
                nm = "" if nm in ("", "~") else nm.replace("/", "{slash}") + "-"
                ni = pcbnew.NETINFO_ITEM(b, "unconnected-(%s-%sPad%s)" % (ref, nm, num))
                b.Add(ni); pad.SetNet(ni)
        if ref in getattr(S, "OCULTAR_REF", ()):   # bornes con etiquetas propias en la serigrafía
            fp.Reference().SetVisible(False)
        if ref.startswith("TP"):
            fp.SetExcludedFromBOM(False)
            fp.Reference().SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))     # mínimo de JLCPCB
            fp.Reference().SetTextThickness(mm(0.15))
    for i, (x, y) in enumerate(S.HOLES):
        fp = pcbnew.FootprintLoad(os.path.join(FPL, "MountingHole.pretty"), "MountingHole_3.2mm_M3")
        fp.SetFPID(pcbnew.LIB_ID("MountingHole", "MountingHole_3.2mm_M3"))
        fp.SetReference("H%d" % (i + 1)); fp.SetPosition(P(x, y)); fp.SetBoardOnly(True)
        fp.SetExcludedFromBOM(True); fp.SetExcludedFromPosFiles(True); fp.Reference().SetVisible(False)
        b.Add(fp)
    ns = b.GetDesignSettings().m_NetSettings
    for cname, (w, clr, members) in S.NETCLASS.items():
        nc = pcbnew.NETCLASS(cname)
        nc.SetTrackWidth(mm(w)); nc.SetClearance(mm(clr)); nc.SetViaDiameter(mm(0.8 if w >= 1 else 0.6))
        nc.SetViaDrill(mm(0.4 if w >= 1 else 0.3))
        ns.SetNetclass(cname, nc)
        for m in members:
            ns.SetNetclassPatternAssignment("/" + m, cname)
    dflt = ns.GetDefaultNetclass()
    dflt.SetTrackWidth(mm(0.25)); dflt.SetClearance(mm(0.2)); dflt.SetViaDiameter(mm(0.6)); dflt.SetViaDrill(mm(0.3))
    b.GetDesignSettings().m_MinThroughDrill = mm(0.2)
    return b


def _internas(S):
    return [pcbnew.In1_Cu, pcbnew.In2_Cu][:max(0, S.CAPAS - 2)]


def _cobre(S):
    return [pcbnew.F_Cu, pcbnew.B_Cu] + _internas(S)


def _planos(S, b):
    """4 capas: planos internos completos (In1 = GND de referencia, In2 según PLANOS), presentes desde el ruteo."""
    capa = {"In1": pcbnew.In1_Cu, "In2": pcbnew.In2_Cu}
    for net, nom in S.PLANOS[:len(_internas(S))]:
        add_zone(b, net, capa[nom], [(0.3, 0.3), (S.W - 0.3, 0.3), (S.W - 0.3, S.H - 0.3), (0.3, S.H - 0.3)],
                 prio=0, clearance=0.3, solid=False)


def _costura(S, b, red="GND"):
    """Vías de costura GND: cada isla de GND de F.Cu baja a los planos (y una rejilla de COSTURA mm en toda la placa).
    Solo se colocan donde hay GND rellenado en F.Cu y B.Cu con holgura, lejos de agujeros y otras vías."""
    gnd = b.FindNet("/" + red)
    llenos = {}
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != "/" + red:
            continue
        for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
            if z.IsOnLayer(lay):
                ps = z.GetFilledPolysList(lay).CloneDropTriangulation()
                ps.Deflate(mm(0.45), pcbnew.CORNER_STRATEGY_CHAMFER_ALL_CORNERS, mm(0.01))
                llenos.setdefault(lay, []).append(ps)
    dentro = lambda lay, pt: any(ps.Contains(pt) for ps in llenos.get(lay, []))
    ocupado = [(p.GetPosition(), max(p.GetDrillSize().x, p.GetSize().x) / 2 + mm(0.8))
               for f in b.GetFootprints() for p in f.Pads() if p.GetDrillSize().x > 0]
    ocupado += [(t.GetPosition(), mm(1.0)) for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
    prohibido = [z for z in b.Zones() if z.GetIsRuleArea() and (z.GetDoNotAllowVias() or z.GetDoNotAllowTracks())]
    libre = lambda pt: all((pt - c).EuclideanNorm() > r for c, r in ocupado) and \
        not any(z.Outline().Contains(pt) for z in prohibido)
    puestas = []

    def poner(pt):
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pt); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(gnd); v.SetIsFree(True)
        b.Add(v); ocupado.append((pt, mm(1.0))); puestas.append(pt)

    ok = lambda pt: dentro(pcbnew.F_Cu, pt) and dentro(pcbnew.B_Cu, pt) and libre(pt)
    if S.COSTURA:
        n = int(S.COSTURA * 10)
        for x in range(20, int(S.W * 10) - 10, n):
            for y in range(20, int(S.H * 10) - 10, n):
                pt = P(x / 10, y / 10)
                if ok(pt):
                    poner(pt)
    for ps in llenos.get(pcbnew.F_Cu, []):           # islas de F.Cu que quedaron sin vía
        for i in range(ps.OutlineCount()):
            o = ps.Outline(i)
            if any(o.PointInside(q) for q in puestas):
                continue
            bb = o.BBox()
            for x in range(bb.GetX(), bb.GetRight(), mm(0.25)):
                hecho = False
                for y in range(bb.GetY(), bb.GetBottom(), mm(0.25)):
                    pt = pcbnew.VECTOR2I(x, y)
                    if o.PointInside(pt) and ok(pt):
                        poner(pt); hecho = True
                        break
                if hecho:
                    break
    return len(puestas)


def add_zone(b, net, layer, pts, prio=0, clearance=0.3, solid=True):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(b.FindNet("/" + net))
    ol = z.Outline(); ol.NewOutline()
    for x, y in pts:
        ol.Append(mm(100 + x), mm(100 + y))
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(mm(clearance))
    z.SetMinThickness(mm(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if solid else pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetIsFilled(False)
    b.Add(z)
    return z


def _regla(b, pts, nombre, layers, tracks=True, vias=True, pour=False):
    k = pcbnew.ZONE(b)
    k.SetIsRuleArea(True)
    ls = pcbnew.LSET()
    for l in layers:
        ls.AddLayer(l)
    k.SetLayerSet(ls)
    ol = k.Outline(); ol.NewOutline()
    for x, y in pts:
        ol.Append(x, y)
    k.SetDoNotAllowTracks(tracks); k.SetDoNotAllowVias(vias); k.SetDoNotAllowCopperPour(pour)
    k.SetDoNotAllowPads(False); k.SetDoNotAllowFootprints(False); k.SetZoneName(nombre)
    b.Add(k)


def add_power(S, b):
    for item in S.PRE:
        net, w, pts = item[:3]
        lay = pcbnew.B_Cu if len(item) > 3 and item[3] == "B" else pcbnew.F_Cu
        for a, c in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(P(*a)); t.SetEnd(P(*c))
            t.SetWidth(mm(w)); t.SetLayer(lay); t.SetNet(b.FindNet("/" + net)); t.SetLocked(True)
            b.Add(t)
    for z in S.POWER_ZONES:
        net, pts = z[:2]
        lay = pcbnew.B_Cu if len(z) > 2 and z[2] == "B" else pcbnew.F_Cu
        add_zone(b, net, lay, pts, prio=10, clearance=0.3, solid=True)
    for x, y in S.VIAS:
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(P(x, y)); v.SetWidth(mm(0.8)); v.SetDrill(mm(0.4)); v.SetNet(b.FindNet("/GND"))
        v.SetIsFree(True)
        b.Add(v)
    for net, x, y in S.PREVIAS:
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(P(x, y)); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(b.FindNet("/" + net))
        v.SetLocked(True)
        b.Add(v)
    for z in S.POWER_ZONES:                   # solo para rutear: se quitan antes del relleno final
        net, pts = z[:2]
        if net not in S.KEEPOUT_NETS:
            continue
        lay = pcbnew.B_Cu if len(z) > 2 and z[2] == "B" else pcbnew.F_Cu
        ps = pcbnew.SHAPE_POLY_SET(); ps.NewOutline()
        for x, y in pts:
            ps.Append(mm(100 + x), mm(100 + y))
        ps.Deflate(mm(0.8), pcbnew.CORNER_STRATEGY_CHAMFER_ALL_CORNERS, mm(0.01))
        o = ps.Outline(0)
        _regla(b, [(o.CPoint(i).x, o.CPoint(i).y) for i in range(o.PointCount())], "ruteo_" + net, [lay])
    _sin_cobre(S, b)


def _sin_cobre(S, b):
    for i, pts in enumerate(S.SIN_COBRE):    # permanente: sin pistas, vías ni planos (p. ej. bajo una antena)
        _regla(b, [(mm(100 + x), mm(100 + y)) for x, y in pts], "sin_cobre_%d" % i, _cobre(S),
               pour=True)
    for i, pts in enumerate(S.SIN_PISTAS):   # sin pistas ni vías, con relleno (p. ej. cruce de un módulo aislado)
        _regla(b, [(mm(100 + x), mm(100 + y)) for x, y in pts], "sin_pistas_%d" % i, _cobre(S))
    for i, pts in enumerate(S.SIN_RELLENO):  # solo sin relleno: guarda distancia entre dos tierras
        _regla(b, [(mm(100 + x), mm(100 + y)) for x, y in pts], "sin_relleno_%d" % i, _cobre(S),
               tracks=False, vias=False, pour=True)
    for i, pts in enumerate(S.RETORNO):      # permanente: plano inferior sin pistas donde regresa la corriente fuerte
        _regla(b, [(mm(100 + x), mm(100 + y)) for x, y in pts], "retorno_%d" % i, [pcbnew.B_Cu], vias=False)


def write_project(S):
    rules = {"min_clearance": 0.2, "min_track_width": 0.15, "min_copper_edge_clearance": 0.3,
             "min_through_hole_diameter": 0.2, "min_hole_to_hole": 0.25, "min_hole_clearance": 0.2,
             "min_via_diameter": 0.45, "min_via_annular_width": 0.1, "min_connection": 0.0,
             "min_silk_clearance": 0.0, "min_text_height": 0.6, "min_text_thickness": 0.1,
             "allow_blind_buried_vias": False, "allow_microvias": False}
    pro = json.load(open("/usr/share/kicad/template/kicad.kicad_pro"))
    ds = pro.setdefault("board", {}).setdefault("design_settings", {})
    ds.setdefault("rules", {}).update(rules)
    ds.setdefault("rule_severities", {}).update({
        "silk_over_copper": "ignore", "silk_overlap": "ignore", "silk_edge_clearance": "ignore",
        "lib_footprint_mismatch": "ignore", "lib_footprint_issues": "ignore", "text_height": "ignore",
        "text_thickness": "ignore", "footprint_type_mismatch": "ignore", "isolated_copper": "ignore",
        "starved_thermal": "ignore"})
    ds["track_widths"] = [0.0, 0.25, 0.6, 1.0, 2.0]
    ds["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.6, "drill": 0.3},
                            {"diameter": 0.8, "drill": 0.4}]
    base = {"bus_width": 12, "clearance": 0.2, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25,
            "diff_pair_width": 0.2, "line_style": 0, "microvia_diameter": 0.3, "microvia_drill": 0.1,
            "name": "Default", "pcb_color": "rgba(0, 0, 0, 0.000)", "priority": 2147483647,
            "schematic_color": "rgba(0, 0, 0, 0.000)", "track_width": 0.25, "via_diameter": 0.6,
            "via_drill": 0.3, "wire_width": 6}
    classes, pats = [base], []
    for i, (cname, (w, clr, members)) in enumerate(S.NETCLASS.items()):
        c = dict(base)
        c.update({"name": cname, "clearance": clr, "track_width": w, "priority": i,
                  "via_diameter": 0.8 if w >= 1 else 0.6, "via_drill": 0.4 if w >= 1 else 0.3})
        classes.append(c)
        pats += [{"netclass": cname, "pattern": "/" + m} for m in members]
    pro["net_settings"] = {"classes": classes, "meta": {"version": 4}, "netclass_patterns": pats}
    pro.setdefault("meta", {})["filename"] = S.PROJECT + ".kicad_pro"
    json.dump(pro, open(os.path.join(S.KI, S.PROJECT + ".kicad_pro"), "w"), indent=2)
    open(os.path.join(S.KI, S.PROJECT + ".kicad_dru"), "w").write("(version 1)\n" + S.DRU)
    rel = os.path.relpath(os.path.join(HUELLAS, "LetreroLab.pretty"), S.KI)   # huellas propias para KiCad
    open(os.path.join(S.KI, "fp-lib-table"), "w").write(
        '(fp_lib_table\n  (version 7)\n  (lib (name "LetreroLab")(type "KiCad")(uri "${KIPRJMOD}/%s")(options "")'
        '(descr "Huellas propias de LetreroLab"))\n)\n' % rel)


def schematic(S):
    comps = []
    cols = 9 if S.PAPER == "A2" else 7
    for i, (ref, val, sym, f, pins, func) in enumerate(S.C_):
        pins = {k: (None if (ref, k) in S.DESCONECTAR else v) for k, v in pins.items()}
        x, y = 30.48 + (i % cols) * 43.18, 40.64 + (i // cols) * 38.1
        comps.append((ref, val, sym, f, pins, (round(x / 2.54) * 2.54, round(y / 2.54) * 2.54, 0), func))
    comun.make_schematic(S.KI, S.PROJECT, S.PROJECT, S.ROOT_UUID, S.NS, comps, S.NOTES, [], S.TITLE, S.SUBTITLES,
                         paper=S.PAPER, flags=S.FLAGS, company=S.COMPANY)


def finish(S, b):
    """Modelos 3D locales (kicad/3d) y textos de serigrafía."""
    d3 = os.path.join(S.KI, "3d")
    for fp in b.GetFootprints():
        if fp.GetReference() in getattr(S, "OCULTAR_REF", ()):
            fp.Reference().SetVisible(False)
        ms = list(fp.Models())
        for m in ms:
            for clave, sustituto in S.MODELOS.items():
                if clave in m.m_Filename:
                    m.m_Filename = "${KICAD9_3DMODEL_DIR}/Resistor_SMD.3dshapes/" + sustituto
            f = os.path.basename(m.m_Filename)
            if os.path.exists(os.path.join(d3, f)):
                m.m_Filename = "${KIPRJMOD}/3d/" + f
        fp.Models().clear()
        for m in ms:
            fp.Add3DModel(m)
    for txt, x, y, h, side in S.SILK:
        t = pcbnew.PCB_TEXT(b)
        t.SetText(txt); t.SetPosition(P(x, y))
        t.SetTextSize(pcbnew.VECTOR2I(mm(h), mm(h))); t.SetTextThickness(mm(h * 0.15))
        t.SetLayer(pcbnew.F_SilkS if side == "F" else pcbnew.B_SilkS)
        if side == "B":
            t.SetMirrored(True)
        b.Add(t)


def _clase_hv(S, b):
    if S.RED_HV:
        b.GetDesignSettings().m_NetSettings.GetNetClassByName(S.RED_HV).SetClearance(mm(5.0))


def main(S):
    _defaults(S)
    os.makedirs(S.KI, exist_ok=True)
    write_project(S)
    schematic(S)
    b = build_board(S)
    path = os.path.join(S.KI, S.PROJECT + ".kicad_pcb")
    dsn, ses = os.path.join(S.KI, S.PROJECT + ".dsn"), os.path.join(S.KI, S.PROJECT + ".ses")
    suf = lambda k: "" if k == 1 else "_%d" % k
    if "--import" in sys.argv:
        k = int(sys.argv[sys.argv.index("--import") + 1])
        b = pcbnew.LoadBoard(path)
        pcbnew.ImportSpecctraSES(b, ses.replace(".ses", suf(k) + ".ses"))
        b.Save(path)
        b = pcbnew.LoadBoard(path)
        _clase_hv(S, b)
        pcbnew.ExportSpecctraDSN(b, dsn.replace(".dsn", suf(k + 1) + ".dsn"))
        write_project(S)                   # guardar la placa reescribe el .kicad_pro con severidades por defecto
        print("pasada %d importada; dsn %d" % (k, k + 1))
        return
    if "--final" in sys.argv:
        k = int(sys.argv[sys.argv.index("--final") + 1])
        b = pcbnew.LoadBoard(path)
        pcbnew.ImportSpecctraSES(b, ses.replace(".ses", suf(k) + ".ses"))
        for ref, num in S.DESCONECTAR:
            for pad in b.FindFootprintByReference(ref).Pads():
                if pad.GetNumber() == num:
                    ni = pcbnew.NETINFO_ITEM(b, "unconnected-(%s-Pad%s)" % (ref, num))
                    b.Add(ni); pad.SetNet(ni)
        for z in list(b.Zones()):
            if z.GetIsRuleArea() and z.GetZoneName().startswith("ruteo_"):
                b.Remove(z)
        for z in S.ZONAS_FINALES:          # planos que el ruteador trató como pistas normales (p. ej. tierra aislada)
            add_zone(b, z[0], pcbnew.B_Cu if len(z) > 2 and z[2] == "B" else pcbnew.F_Cu, z[1], prio=10, clearance=0.3,
                     solid=False)
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            add_zone(b, "GND", layer, [(0.3, 0.3), (S.W - 0.3, 0.3), (S.W - 0.3, S.H - 0.3), (0.3, S.H - 0.3)],
                     prio=0, clearance=0.3, solid=False)
        finish(S, b)
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        if S.CAPAS > 2 or S.COSTURA:
            for red in getattr(S, "COSTURA_REDES", ("GND",)):
                print("vías de costura %s:" % red, _costura(S, b, red))
            pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        b.Save(path)
        write_project(S)
        print("importado y rellenado", path)
        return
    b.Save(path)
    b = pcbnew.LoadBoard(path)
    add_power(S, b)
    _planos(S, b)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(path)
    _clase_hv(S, b)
    pcbnew.ExportSpecctraDSN(b, dsn)
    write_project(S)
    print("placa", path, "dsn", dsn)


def cajas(S, refs=None):
    """Imprime el rectángulo de cortesía (courtyard) de cada pieza: sirve para acomodar sin choques."""
    _defaults(S)
    b = pcbnew.LoadBoard(os.path.join(S.KI, S.PROJECT + ".kicad_pcb"))
    for fp in b.GetFootprints():
        r = fp.GetReference()
        if refs and r not in refs:
            continue
        lay = pcbnew.B_CrtYd if fp.GetLayer() == pcbnew.B_Cu else pcbnew.F_CrtYd
        bb = fp.GetCourtyard(lay).BBox()
        if bb.GetWidth() == 0:
            continue
        print("%-5s x %6.2f-%6.2f  y %6.2f-%6.2f" % (r, pcbnew.ToMM(bb.GetX()) - 100, pcbnew.ToMM(bb.GetRight()) - 100,
                                                   pcbnew.ToMM(bb.GetY()) - 100, pcbnew.ToMM(bb.GetBottom()) - 100))
