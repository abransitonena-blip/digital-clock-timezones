"""BOM y CPL de JLCPCB por SKU a partir de los de la placa completa (con y sin las piezas de patas, «_solo_SMD»).
7R Tour CA = todo; 7R Tour 24DC = sin la entrada de red (J8, F2, RV1, PS1, D3, C3).
Los archivos sin SKU en el nombre (AP_7R_TOUR_BOM_JLCPCB*.csv) son de la placa completa = SKU CA: no usarlos para el 24DC.
python3 variantes.py DIR_JLCPCB"""
import csv, os, sys
D = sys.argv[1]
SOLO_CA = {"J8", "F2", "RV1", "PS1", "D3", "C3"}
for sufijo in ("", "_solo_SMD"):
    for sku, quitar in (("24DC", SOLO_CA), ("CA", set())):
        with open(os.path.join(D, "AP_7R_TOUR_BOM_JLCPCB%s.csv" % sufijo), newline="") as f:
            filas = list(csv.reader(f))
        sal = [filas[0]]
        for r in filas[1:]:
            refs = [x for x in r[1].split(",") if x not in quitar]
            if refs:
                r = list(r); r[1] = ",".join(refs); r[4] = str(len(refs)); sal.append(r)
        with open(os.path.join(D, "AP_7R_TOUR_%s_BOM_JLCPCB%s.csv" % (sku, sufijo)), "w", newline="") as f:
            csv.writer(f).writerows(sal)
        with open(os.path.join(D, "AP_7R_TOUR_CPL_JLCPCB%s.csv" % sufijo), newline="") as f:
            filas = list(csv.reader(f))
        with open(os.path.join(D, "AP_7R_TOUR_%s_CPL_JLCPCB%s.csv" % (sku, sufijo)), "w", newline="") as f:
            csv.writer(f).writerows([filas[0]] + [r for r in filas[1:] if r[0] not in quitar])
        print(sku + sufijo, len(sal) - 1, "partidas")
