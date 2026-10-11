"""Une a los planos internos las islas de GND de F.Cu y de B.Cu que no tienen vía ni pata THT: pone una vía donde la
isla tiene relleno con margen y la otra cara no tiene cobre de otra red cerca. Uso (en el contenedor): python3 islas_gnd.py placa.kicad_pcb"""
import sys
import pcbnew

p = sys.argv[1]
b = pcbnew.LoadBoard(p)
mm, MM = pcbnew.FromMM, pcbnew.ToMM
gnd = b.FindNet("/GND")
pcbnew.ZONE_FILLER(b).Fill(b.Zones())


def rellenos(layer):
    out = []
    for z in b.Zones():
        if z.GetNetCode() == gnd.GetNetCode() and z.IsOnLayer(layer) and not z.GetIsRuleArea():
            out.append(z.GetFilledPolysList(layer))
    return out


F, Bk = rellenos(pcbnew.F_Cu), rellenos(pcbnew.B_Cu)
anclas = [v.GetPosition() for v in b.Tracks() if v.Type() == pcbnew.PCB_VIA_T and v.GetNetCode() == gnd.GetNetCode()]
anclas += [pd.GetPosition() for fp in b.GetFootprints() for pd in fp.Pads()
           if pd.GetNetCode() == gnd.GetNetCode() and pd.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
R = mm(0.5)                     # radio de la vía (0.3) + margen
ANILLO = [(R, 0), (-R, 0), (0, R), (0, -R), (int(R * .7), int(R * .7)), (-int(R * .7), int(R * .7)),
          (int(R * .7), -int(R * .7)), (-int(R * .7), -int(R * .7))]


def dentro(sets, pt):
    return any(s.Contains(pt) for s in sets)


# en la otra cara basta con que no haya pistas, patas ni vías de otra red cerca (un plano de otra red se rellena alrededor)
CARA = {"F": pcbnew.B_Cu, "B": pcbnew.F_Cu}          # isla en F.Cu: se revisa B.Cu, y al revés
OTROS, PATAS = [], []


def preparar(otra):
    OTROS[:] = [t for t in b.Tracks() if t.GetNetCode() != gnd.GetNetCode() and
                (t.Type() == pcbnew.PCB_VIA_T or t.GetLayer() == otra)]
    PATAS[:] = [pd for fp in b.GetFootprints() for pd in fp.Pads()
                if pd.GetNetCode() != gnd.GetNetCode() and pd.IsOnLayer(otra)]
SEP = mm(0.3 + 0.25)                 # radio de la vía + separación


def _dist_seg(p, a, c):
    ax, ay, cx, cy, px, py = a.x, a.y, c.x, c.y, p.x, p.y
    dx, dy = cx - ax, cy - ay
    L = dx * dx + dy * dy
    k = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return ((ax + k * dx - px) ** 2 + (ay + k * dy - py) ** 2) ** 0.5


def abajo_libre(pt):
    for t in OTROS:
        if t.Type() == pcbnew.PCB_VIA_T:
            if (t.GetPosition() - pt).EuclideanNorm() < SEP + mm(0.3):
                return False
        elif _dist_seg(pt, t.GetStart(), t.GetEnd()) < SEP + t.GetWidth() / 2:
            return False
    for pd in PATAS:
        bb = pd.GetBoundingBox()
        bb.Inflate(SEP)
        if bb.Contains(pt):
            return False
    return True


def libre(pt, propia):
    return all(dentro(propia, pcbnew.VECTOR2I(pt.x + dx, pt.y + dy)) for dx, dy in ANILLO + [(0, 0)]) and abajo_libre(pt)


puestas = 0


def unir(cara, propia):
    global puestas
    preparar(CARA[cara])
    for s in propia:
        for i in range(s.OutlineCount()):
            ol = s.Outline(i)
            if any(ol.PointInside(a) for a in anclas):
                continue
            bb = ol.BBox()
            y = bb.GetTop() + R
            while y < bb.GetBottom() - R:
                x = bb.GetLeft() + R
                while x < bb.GetRight() - R:
                    pt = pcbnew.VECTOR2I(x, y)
                    if ol.PointInside(pt) and libre(pt, propia):
                        v = pcbnew.PCB_VIA(b)
                        v.SetPosition(pt); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(gnd)
                        b.Add(v); anclas.append(pt); puestas += 1
                        print(cara, "vía en %.2f %.2f" % (MM(x) - 100, MM(y) - 100))
                        break
                    x += mm(0.25)
                else:
                    y += mm(0.25)
                    continue
                break
            else:
                print(cara, "isla sin lugar: %.2f %.2f - %.2f %.2f (%.2f mm2)" % (
                    MM(bb.GetLeft()) - 100, MM(bb.GetTop()) - 100, MM(bb.GetRight()) - 100, MM(bb.GetBottom()) - 100,
                    ol.Area() / 1e12))


unir("F", F)
unir("B", Bk)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(p)
print("vías nuevas:", puestas)
