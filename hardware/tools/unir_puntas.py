"""Une las puntas sueltas de pista con la punta de la misma red más cercana (a menos de 1 mm, o la que se dé), como cuando el
ruteador deja su pista a unas décimas del tramo fijo (PRE). Uso en el contenedor: python3 unir_puntas.py placa.kicad_pcb"""
import sys
import pcbnew

p = sys.argv[1]
b = pcbnew.LoadBoard(p)
MAX = pcbnew.FromMM(float(sys.argv[2]) if len(sys.argv) > 2 else 1.0)   # 2o argumento: distancia máxima en mm
pistas = [t for t in b.Tracks() if t.Type() != pcbnew.PCB_VIA_T]
cuenta = {}
for t in pistas:
    for q in (t.GetStart(), t.GetEnd()):
        cuenta[(t.GetNetCode(), t.GetLayer(), q.x, q.y)] = cuenta.get((t.GetNetCode(), t.GetLayer(), q.x, q.y), 0) + 1
pads = [(pd.GetNetCode(), pd) for fp in b.GetFootprints() for pd in fp.Pads()]
vias = [(v.GetNetCode(), v.GetPosition()) for v in b.Tracks() if v.Type() == pcbnew.PCB_VIA_T]


def tocada(net, lay, q):
    if cuenta[(net, lay, q.x, q.y)] > 1:
        return True
    if any(n == net and pd.IsOnLayer(lay) and pd.HitTest(q) for n, pd in pads):
        return True
    return any(n == net and v == q for n, v in vias)


sueltas = [(t, q) for t in pistas for q in (t.GetStart(), t.GetEnd())
           if not tocada(t.GetNetCode(), t.GetLayer(), q)]
unidas = 0
for t, q in sueltas:
    mejor, d = None, MAX
    for u in pistas:
        if u is t or u.GetNetCode() != t.GetNetCode() or u.GetLayer() != t.GetLayer():
            continue
        for r in (u.GetStart(), u.GetEnd()):
            dd = (r - q).EuclideanNorm()
            if 0 < dd < d:
                mejor, d = r, dd
    if mejor is not None:
        n = pcbnew.PCB_TRACK(b)
        n.SetStart(q); n.SetEnd(mejor); n.SetWidth(min(t.GetWidth(), pcbnew.FromMM(0.6))); n.SetLayer(t.GetLayer())
        n.SetNet(t.GetNet()); b.Add(n); unidas += 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(p)
print("puntas unidas:", unidas)
