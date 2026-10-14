#!/usr/bin/env python3
"""Revisión previa al pedido a JLCPCB: comprueba por software lo que más veces hace fallar un primer pedido.

Uso (desde hardware/):  python3 tools/revisar_pedido.py ap-electric/7r-tour AP_7R_TOUR [24DC|CA]
Sin tercer argumento revisa los archivos de la placa completa.

Qué mira:
  1. Cada fila del BOM tiene un código LCSC con forma C + dígitos, y el código está en la tabla verificada (tools/jlcpcb.py).
  2. La cantidad de cada fila coincide con sus designadores; ningún designador se repite.
  3. BOM y CPL tienen exactamente los mismos designadores.
  4. Todas las piezas del CPL están dentro del contorno de la placa y en una capa válida.
  5. El ZIP de Gerber trae las capas y los taladros que pide JLCPCB.
  6. Ningún código aparece con descripciones distintas (mismo código, valores diferentes).
Lo que NO puede ver: la orientación real de cada pieza contra la vista previa de JLCPCB (hay que revisarla en su pantalla
«Component Placement» antes de pagar), ni la existencia de piezas en su almacén en esa fecha.
"""
import csv, os, re, sys, zipfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO, "tools"))


def codigos_verificados():
    """Códigos LCSC que están en la tabla de jlcpcb.py (los que se comprobaron en lcsc.com / jlcpcb.com)."""
    txt = open(os.path.join(REPO, "tools", "jlcpcb.py"), encoding="utf-8").read()
    cods = set(re.findall(r'"(C\d{3,10})"', txt))
    cat = os.path.join(REPO, "tools", "jlcpcb_catalogo.csv")          # resistencias, capacitores, LED y diodos básicos
    if os.path.exists(cat):
        cods |= set(re.findall(r"\bC\d{3,10}\b", open(cat, encoding="utf-8").read()))
    return cods


def main():
    if len(sys.argv) < 3:
        print(__doc__); return 2
    carpeta, nombre = sys.argv[1], sys.argv[2]
    sku = sys.argv[3] if len(sys.argv) > 3 else ""
    jlc = os.path.join(REPO, carpeta, "fabricacion", "jlcpcb")
    pre = nombre + ("_" + sku if sku else "")
    bom_f, cpl_f = os.path.join(jlc, pre + "_BOM_JLCPCB.csv"), os.path.join(jlc, pre + "_CPL_JLCPCB.csv")
    zip_f = os.path.join(jlc, nombre + "_gerber_JLCPCB.zip")
    errores, avisos = [], []
    ver = codigos_verificados()

    with open(bom_f, newline="", encoding="utf-8") as f:
        bom = list(csv.DictReader(f))
    with open(cpl_f, newline="", encoding="utf-8") as f:
        cpl = list(csv.DictReader(f))

    # 1, 2, 6: BOM
    todos = []
    por_codigo = {}
    for r in bom:
        refs = [x.strip() for x in r["Designator"].split(",") if x.strip()]
        cod = r["LCSC Part #"].strip()
        if not re.fullmatch(r"C\d{3,10}", cod):
            errores.append("BOM: «%s» (%s) no tiene código LCSC válido: «%s»" % (r["Comment"], r["Designator"], cod))
        elif cod not in ver:
            avisos.append("BOM: el código %s de «%s» no está en la tabla verificada de tools/jlcpcb.py" % (cod, r["Comment"]))
        if str(len(refs)) != r["Cantidad"].strip():
            errores.append("BOM: «%s» dice cantidad %s pero lista %d designadores" % (r["Comment"], r["Cantidad"], len(refs)))
        todos += refs
        por_codigo.setdefault(cod, set()).add((r["Comment"], r["Footprint"]))
    rep = {x for x in todos if todos.count(x) > 1}
    if rep:
        errores.append("BOM: designadores repetidos: %s" % ", ".join(sorted(rep)))
    for cod, descr in por_codigo.items():
        if len(descr) > 1:
            avisos.append("BOM: el código %s aparece con %d descripciones distintas: %s" % (cod, len(descr), sorted(descr)))

    # 3: BOM contra CPL
    en_cpl = [r["Designator"] for r in cpl]
    if len(set(en_cpl)) != len(en_cpl):
        errores.append("CPL: designadores repetidos")
    solo_bom, solo_cpl = set(todos) - set(en_cpl), set(en_cpl) - set(todos)
    if solo_bom:
        errores.append("En el BOM pero no en el CPL: %s" % ", ".join(sorted(solo_bom)))
    if solo_cpl:
        errores.append("En el CPL pero no en el BOM: %s" % ", ".join(sorted(solo_cpl)))

    # 4: posiciones dentro de la placa, en las mismas coordenadas que los Gerber (X, Y de Gerber; el CPL de salidas.py las usa tal cual)
    gbr = os.path.join(REPO, carpeta, "fabricacion", "gerber")
    caja = None; ancho = alto = None
    for f in os.listdir(gbr) if os.path.isdir(gbr) else []:
        if f.endswith("Edge_Cuts.gbr"):
            xs, ys = [], []
            for l in open(os.path.join(gbr, f), encoding="utf-8", errors="ignore"):
                m = re.match(r"X(-?\d+)Y(-?\d+)D0[123]\*", l)
                if m:
                    xs.append(int(m.group(1)) / 1e6); ys.append(int(m.group(2)) / 1e6)
            if xs:
                caja = (min(xs), min(ys), max(xs), max(ys)); ancho, alto = caja[2] - caja[0], caja[3] - caja[1]
    for r in cpl:
        if r["Layer"] not in ("Top", "Bottom"):
            errores.append("CPL: %s tiene capa «%s»" % (r["Designator"], r["Layer"]))
        try:
            x = float(r["Mid X"].replace("mm", "")); y = float(r["Mid Y"].replace("mm", ""))
            float(r["Rotation"])
        except ValueError:
            errores.append("CPL: %s tiene posición o giro ilegibles" % r["Designator"]); continue
        if caja and not (caja[0] - 1 <= x <= caja[2] + 1 and caja[1] - 1 <= y <= caja[3] + 1):
            errores.append("CPL: %s en (%.1f, %.1f) queda fuera del contorno de los Gerber (%.1f..%.1f, %.1f..%.1f): origen distinto" %
                           (r["Designator"], x, y, caja[0], caja[2], caja[1], caja[3]))

    # 5: Gerber
    if not os.path.exists(zip_f):
        errores.append("Falta el ZIP de Gerber: %s" % zip_f)
    else:
        nombres = zipfile.ZipFile(zip_f).namelist()
        for sufijo in ("F_Cu.gbr", "B_Cu.gbr", "F_Mask.gbr", "B_Mask.gbr", "F_Silkscreen.gbr", "Edge_Cuts.gbr", "PTH.drl"):
            if not any(n.endswith(sufijo) for n in nombres):
                errores.append("El ZIP de Gerber no trae «%s»" % sufijo)
        if not any(n.endswith("F_Paste.gbr") for n in nombres):
            avisos.append("El ZIP de Gerber no trae F_Paste (JLCPCB arma sus propias plantillas)")

    print("Revisión del pedido: %s%s" % (nombre, (" " + sku) if sku else ""))
    print("  %d filas de BOM · %d piezas · %d en el CPL%s" % (len(bom), len(todos), len(cpl),
          (" · placa de %.1f x %.1f mm" % (ancho, alto)) if ancho else ""))
    for e in errores:
        print("  ERROR: " + e)
    for a in avisos:
        print("  aviso: " + a)
    print("  RESULTADO: " + ("hay %d errores" % len(errores) if errores else "sin errores"))
    print("  Falta revisar a mano en JLCPCB: la orientación de cada pieza polarizada en «Component Placement» y las existencias.")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
