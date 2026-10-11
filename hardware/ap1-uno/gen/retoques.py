"""Retoques del AP UNO después del ruteo (se corre en el contenedor de KiCad, desde ap1-uno/):

    python3 gen/retoques.py

Freerouting deja unas pocas uniones sin hacer en esta placa tan llena. Cada retoque se prueba con el DRC y solo se
queda si baja las conexiones pendientes sin agregar violaciones; si una opción no sirve se prueba la siguiente.
Al final las islas de GND de la cara de arriba se unen a los planos internos con una vía."""
import os
import re
import shutil
import subprocess
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
KI = os.path.join(HERE, "..", "kicad")
PCB = os.path.join(KI, "AP_UNO.kicad_pcb")
mm, MM = pcbnew.FromMM, pcbnew.ToMM
P = lambda x, y: pcbnew.VECTOR2I(mm(100 + x), mm(100 + y))
CAPA = {"F": pcbnew.F_Cu, "B": pcbnew.B_Cu}


def drc():
    subprocess.run(["kicad-cli", "pcb", "drc", "--schematic-parity", "--severity-all", "-o", "/tmp/retoque.rpt", PCB],
                   capture_output=True, text=True, cwd=KI)
    t = open("/tmp/retoque.rpt").read()
    v = int(re.search(r"Found (\d+) DRC violations", t).group(1))
    u = int(re.search(r"Found (\d+) unconnected pads", t).group(1))
    return v, u


def poner(b, net, cosas):
    n = b.FindNet("/" + net)
    for c in cosas:
        if c[0] == "via":
            v = pcbnew.PCB_VIA(b); v.SetPosition(P(*c[1])); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(n); b.Add(v)
        else:
            capa, ancho, pts = c
            for a, z in zip(pts, pts[1:]):
                t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*z)); t.SetWidth(mm(ancho))
                t.SetLayer(CAPA[capa]); t.SetNet(n); b.Add(t)


def quitar_via(b, net, x, y):
    for t in list(b.Tracks()):
        if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == "/" + net and \
                abs(MM(t.GetPosition().x) - 100 - x) < 0.05 and abs(MM(t.GetPosition().y) - 100 - y) < 0.05:
            b.Remove(t)


def quitar_pista(b, net, capa, a, z):
    for t in list(b.Tracks()):
        if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != "/" + net or t.GetLayer() != CAPA[capa]:
            continue
        e = [(round(MM(t.GetStart().x) - 100, 2), round(MM(t.GetStart().y) - 100, 2)),
             (round(MM(t.GetEnd().x) - 100, 2), round(MM(t.GetEnd().y) - 100, 2))]
        if sorted(e) == sorted([a, z]):
            b.Remove(t)


def probar(nombre, opciones, igual=False):
    """igual=True: también vale si las pendientes no bajan (la unión cambia una pendiente por otra que se arregla luego)"""
    v0, u0 = drc()
    for k, hacer in enumerate(opciones):
        shutil.copy(PCB, PCB + ".bak")
        b = pcbnew.LoadBoard(PCB)
        hacer(b)
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        b.Save(PCB)
        v, u = drc()
        if v <= v0 and u <= u0 and (v + u < v0 + u0 or igual):
            print("%s: opción %d (violaciones %d -> %d, pendientes %d -> %d)" % (nombre, k + 1, v0, v, u0, u))
            return True
        nuevo = [l for l in open("/tmp/retoque.rpt").read().split("\n[") if "unconnected" not in l[:30]]
        print("  %s, opción %d: violaciones %d, pendientes %d; %s" % (nombre, k + 1, v, u,
              " / ".join(x.split("\n")[0][:70] + " " + " ".join(y.strip()[:60] for y in x.split("\n")[2:4]) for x in nuevo[1:3])))
        shutil.copy(PCB + ".bak", PCB)
    print("%s: ninguna opción sirvió" % nombre)
    return False


# 1) 3.3 V: la salida del regulador (pata 1 de U12, hacia el INA238) y la de la bobina L4 (hacia C25/C26 y el ESP32)
#    se unen por abajo, con un puente en B.Cu por debajo de L4
probar("3V3 de U12 a L4", [
    lambda b, x=x: poner(b, "3V3", [("via", (x, 9.55)), ("B", 0.4, [(x, 9.55), (x, 17.0), (x + 0.6, 17.6), (36.93, 17.6)]),
                                    ("via", (36.93, 17.6))])
    for x in (30.0, 29.4, 30.6)])
# 2) DO2: de la pata 5 del expansor a la compuerta de Q7, en diagonal entre DO1 y DO3
probar("DO2", [
    lambda b, a=a: poner(b, "DO2", [("F", 0.25, [(79.64, 13.53), (a - 13.53, 13.53), (74.69, a - 74.69), (74.69, 20.93)])])
    for a in (92.15, 92.1, 92.2)])
# 3) GND de los capacitores C24 (entrada del 3.3 V) y C28 (expansor de entradas): vía junto a la pata
probar("GND de C24", [
    lambda b, x=x, y=y: poner(b, "GND", [("F", 0.4, [(38.2, 9.025), (x, y)]), ("via", (x, y))])
    for x, y in ((37.0, 9.3), (37.0, 9.0), (36.9, 9.5))], igual=True)
probar("GND de C28", [   # no hay lugar libre fuera de la pata: la vía queda en su esquina (tapada con máscara)
    lambda b, x=x, y=y: poner(b, "GND", [("F", 0.4, [(85.8, 42.03), (x, y)]), ("via", (x, y))])
    for x, y in ((85.6, 41.75), (85.65, 41.7), (85.55, 41.8))])
# 4) GND del regulador de 3.3 V (pata 4 de U12): quedaba en una isla chica sin vía
probar("GND de U12", [
    lambda b, x=x, y=y: poner(b, "GND", [("F", 0.4, [(35.64, 11.45), (x, y)]), ("via", (x, y))])
    for x, y in ((36.75, 11.4), (36.7, 11.45), (36.8, 11.35))])
# 4b) GND del expansor de salidas (patas 1-3 de U13 y R35) y del RS-485 (U15 pata 5 y SM712): islas sin vía
def u13(b, x):
    # IN3 (B.Cu) se recorre 1 mm a la izquierda bajo las patas 1-3 de U13 para dejar lugar a la vía de GND
    quitar_pista(b, "IN3", "B", (79.17, 10.4), (77.4, 8.63))
    quitar_pista(b, "IN3", "B", (79.17, 24.66), (79.17, 10.4))
    poner(b, "IN3", [("B", 0.25, [(77.4, 8.63), (78.2, 9.43), (78.2, 15.0), (79.17, 15.97), (79.17, 24.66)])])
    poner(b, "GND", [("via", (x, 11.58))])


probar("GND de U13", [lambda b, x=x: u13(b, x) for x in (79.15, 79.1, 79.2)], igual=True)
probar("GND del RS-485", [lambda b, x=x: poner(b, "GND", [("via", (x, 45.6))]) for x in (99.0, 98.9, 99.1)], igual=True)
# 5) islas de GND de la cara de arriba
r = subprocess.run([sys.executable, os.path.join(HERE, "islas_gnd.py"), PCB], capture_output=True, text=True)
print(r.stdout.strip(), r.stderr.strip()[-300:] if r.returncode else "")
# 6) los pedazos de relleno que no tocan nada se quitan (las islas con patas o vías se quedan)
b = pcbnew.LoadBoard(PCB)
for z in b.Zones():
    if z.GetNetname() == "/GND" and not z.GetIsRuleArea() and (z.IsOnLayer(pcbnew.F_Cu) or z.IsOnLayer(pcbnew.B_Cu)):
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(PCB)
print("final: violaciones %d, pendientes %d" % drc())
if os.path.exists(PCB + ".bak"):
    os.remove(PCB + ".bak")
