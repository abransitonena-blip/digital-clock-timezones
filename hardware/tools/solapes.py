"""Choques de cortesía (courtyard) y piezas fuera del contorno de una placa: docker exec -w /work/hardware kc python3 tools/solapes.py ap-electric/plc/kicad/AP_PLC_C24.kicad_pcb 200 100"""
import pcbnew, sys, itertools
b = pcbnew.LoadBoard(sys.argv[1]); W=float(sys.argv[2]); H=float(sys.argv[3])
bb=[]
for fp in b.GetFootprints():
    lay = pcbnew.B_CrtYd if fp.GetLayer()==pcbnew.B_Cu else pcbnew.F_CrtYd
    c = fp.GetCourtyard(lay).BBox()
    if c.GetWidth()==0: continue
    r=[pcbnew.ToMM(v)-100 for v in (c.GetX(),c.GetY(),c.GetRight(),c.GetBottom())]
    bb.append((fp.GetReference(),r))
    if r[0]<-0.01 or r[1]<-0.01 or r[2]>W+0.01 or r[3]>H+0.01: print("FUERA",fp.GetReference(),[round(x,1) for x in r])
for (a,ra),(c_,rc) in itertools.combinations(bb,2):
    if ra[0]<rc[2]-0.05 and rc[0]<ra[2]-0.05 and ra[1]<rc[3]-0.05 and rc[1]<ra[3]-0.05: print("CHOCA",a,c_,[round(x,1) for x in ra],[round(x,1) for x in rc])
