"""Modelo 3D del conjunto AP-1: la base con el programador enclavado encima (solo para ver y diseñar la caja).

    python3 ap1-ensamble/ensamble.py      (dentro del contenedor de KiCad, desde hardware/)

Copia la placa de la base y le agrega una "huella" sin cobre cuyo modelo 3D es el programador completo
(AP1_Programador_modelo.step, exportado con origen en su esquina) a 11 mm de altura:
zócalo de 8.5 mm + plástico del conector macho de 2.5 mm.
"""
import os, pcbnew

AQUI = os.path.dirname(os.path.abspath(__file__))
b = pcbnew.LoadBoard(os.path.join(AQUI, "..", "ap1-base", "kicad", "AP1_Base.kicad_pcb"))
for fp in b.GetFootprints():                       # modelos de la base: rutas absolutas a su carpeta 3d
    ms = list(fp.Models())
    for m in ms:
        m.m_Filename = m.m_Filename.replace("${KIPRJMOD}", "${KIPRJMOD}/../ap1-base/kicad")   # relativo: abre en cualquier PC
    fp.Models().clear()
    for m in ms:
        fp.Add3DModel(m)
fp = pcbnew.FOOTPRINT(b)
fp.SetReference("PROG"); fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(136.0), pcbnew.FromMM(100.0)))   # esquina del programador sobre la base
fp.SetBoardOnly(True); fp.SetExcludedFromBOM(True); fp.SetExcludedFromPosFiles(True)
m = pcbnew.FP_3DMODEL()
m.m_Filename = "${KIPRJMOD}/AP1_Programador_modelo.step"
m.m_Offset = pcbnew.VECTOR3D(0, 0, 11.0)
fp.Add3DModel(m)
b.Add(fp)
b.Save(os.path.join(AQUI, "AP1_Ensamble.kicad_pcb"))
print("ensamble listo")
