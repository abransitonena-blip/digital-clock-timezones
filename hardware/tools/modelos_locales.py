"""Copia local de los modelos 3D de una placa (kicad/3d) y apunta la placa a ellos: el proyecto abre con su 3D
aunque la computadora no tenga instaladas las librerías 3D de KiCad.

    python3 tools/modelos_locales.py ap1-base AP1_Base        (en la computadora, no en el contenedor)
"""
import os, re, sys, subprocess, urllib.parse

URL = "https://gitlab.com/kicad/libraries/kicad-packages3D/-/raw/9.0.0/%s"
SUST = {"R_Shunt_Vishay_WSK2512_6332Metric_T1.19mm.step": "Resistor_SMD.3dshapes/R_2512_6332Metric.step"}
base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", sys.argv[1], "kicad")
pcb = os.path.join(base, sys.argv[2] + ".kicad_pcb")
d3 = os.path.join(base, "3d")
os.makedirs(d3, exist_ok=True)
txt = open(pcb).read()
for ruta in sorted(set(re.findall(r'\(model "\$\{KICAD9_3DMODEL_DIR\}/([^"]+)"', txt))):
    f = os.path.basename(ruta)
    origen, destino = SUST.get(f, ruta), os.path.basename(SUST.get(f, ruta))
    out = os.path.join(d3, destino)
    if not (os.path.exists(out) and os.path.getsize(out) > 1000):
        r = subprocess.run(["curl", "-sSf", "-o", out, URL % urllib.parse.quote(origen)], capture_output=True)
        if r.returncode:
            print("sin modelo:", f)
            if os.path.exists(out):
                os.remove(out)
            continue
    txt = txt.replace('${KICAD9_3DMODEL_DIR}/' + ruta, '${KIPRJMOD}/3d/' + destino)
    print("ok", destino)
open(pcb, "w").write(txt)
