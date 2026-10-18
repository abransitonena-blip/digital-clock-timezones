"""Lee el informe de DRC (kicad-cli pcb drc) de una placa con ruteo parcial y escribe gen/rutas_auto.json con una ruta por cada unión pendiente
(las toma make.py como RUTAS_AUTO; las traza tools/ruta_auto.py).   python3 gen/pendientes.py /tmp/d2.rpt"""
import json, os, re, sys
t = open(sys.argv[1], encoding="utf-8").read()
rutas = []
for bl in t.split("\n["):
    if not bl.startswith("unconnected_items"):
        continue
    pts = re.findall(r"@\(([\d.]+) mm, ([\d.]+) mm\): (.*)", bl)
    if len(pts) != 2:
        continue
    red = re.search(r"\[/([^\]]+)\]", pts[0][2])
    if not red:
        continue
    def p(m):
        capa = "F" if "F.Cu" in m[2] else "B" if "B.Cu" in m[2] else None
        return (round(float(m[0]) - 100.0, 3), round(float(m[1]) - 100.0, 3), capa)
    rutas.append([red.group(1), p(pts[0]), p(pts[1])])
json.dump(rutas, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rutas_auto.json"), "w"), indent=0)
print(len(rutas), "rutas pendientes")
