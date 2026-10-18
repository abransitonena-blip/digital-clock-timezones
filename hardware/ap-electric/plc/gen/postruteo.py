"""Después de tools/rutear_rapido.sh: ensancha a 0.15 mm las pistas que el ruteador dejó más finas que el mínimo de la placa, rellena los planos
y vuelve a escribir el proyecto.   (en el contenedor)  cd ap-electric/plc && python3 gen/postruteo.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
import pcbnew, make, placa
ruta = os.path.join(HERE, "..", "kicad", make.PROJECT + ".kicad_pcb")
b = pcbnew.LoadBoard(ruta)
n = 0
for t in b.GetTracks():
    if t.GetClass() == "PCB_TRACK" and pcbnew.ToMM(t.GetWidth()) < 0.149:
        t.SetWidth(pcbnew.FromMM(0.15)); n += 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(ruta)
placa._defaults(make); placa.write_project(make)
print("pistas ensanchadas:", n)
