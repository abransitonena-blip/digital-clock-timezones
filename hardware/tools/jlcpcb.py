"""Catálogo de piezas Basic/Preferred de JLCPCB (sin cargo de montaje por tipo) y asignación de códigos LCSC.

El catálogo (jlcpcb_catalogo.csv) sale de la biblioteca JLCPCB-KiCad-Library de CDFER (MIT), que trae cada pieza con su
código LCSC, clase, existencias y precio. Se actualiza con:  bash tools/descargar_biblioteca_jlcpcb.sh

    from jlcpcb import buscar
    buscar("10uF 50V", "C_1206_3216Metric")  ->  {"lcsc": "C13585", "clase": "Basic Component", ...}  o  None
"""
import csv, os, re

_CAT = None
_UNID = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "m": 1e-3, "k": 1e3, "M": 1e6, "": 1.0}


# Piezas que no vienen en el catálogo Basic/Preferred (casi todas "Extended": ~3 USD de montaje por tipo).
# Códigos conocidos; confirmar existencias en jlcpcb.com/parts antes de pedir.
CONOCIDOS = {
    ("ESP32-C3-WROOM-02", "ESP32-C3-WROOM-02"): ("C2934560", "Extended"),
    ("USBLC6-2SC6", "SOT-23-6"): ("C7519", "Extended"),
    ("USB-C", "USB_C_Receptacle_HRO_TYPE-C-31-M-12"): ("C165948", "Extended"),
    ("AP63203WU", "TSOT-23-6"): ("C780769", "Extended"),
    ("VERDE", "LED_0603_1608Metric"): ("C72043", "Basic Component"),
}


def catalogo():
    global _CAT
    if _CAT is None:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "jlcpcb_catalogo.csv"), newline="") as f:
            _CAT = list(csv.DictReader(f))
    return _CAT


def _num(txt):
    """'4.7k' -> 4700, '0R1' -> 0.1, '100nF' -> 1e-7, '10kΩ' -> 1e4, '100mΩ' -> 0.1."""
    t = txt.strip().replace("Ω", "").replace("F", "").replace("ohm", "")
    m = re.match(r"^(\d+)R(\d+)$", t)
    if m:
        return float(m.group(1) + "." + m.group(2))
    m = re.match(r"^(\d+(?:\.\d+)?)\s*([pnuµmkM]?)$", t)
    if m:
        return float(m.group(1)) * _UNID[m.group(2)]
    m = re.match(r"^(\d+)([pnuµkM])(\d+)$", t)          # 4k7, 2u2
    if m:
        return float(m.group(1) + "." + m.group(3)) * _UNID[m.group(2)]
    return None


def _encapsulado(huella):
    m = re.search(r"_(0201|0402|0603|0805|1206|1210|2010|2512)_", huella + "_")
    return m.group(1) if m else None


def _voltaje(desc):
    m = re.match(r"^(\d+(?:\.\d+)?)V\b", desc)
    return float(m.group(1)) if m else 0.0


def _orden(r):
    return (0 if r["clase"].startswith("Basic") else 1, -int(r["stock"] or 0))


_PAQ = {"D_SMA": "SMA", "D_SMB": "SMB", "D_SOD-123": "SOD-123", "SOT-23": "SOT-23", "SOT-23-6": "SOT-23-6",
        "SOT-23-5": "SOT-23-5", "LED_0603": "0603", "LED_0805": "0805"}


def buscar(valor, huella):
    cat = catalogo()
    v = valor.strip()
    if (v, huella) in CONOCIDOS:
        lcsc, clase = CONOCIDOS[(v, huella)]
        return {"lcsc": lcsc, "clase": clase, "parte": v, "huella": huella, "descripcion": "lista CONOCIDOS"}
    enc = _encapsulado(huella)
    if huella.startswith("R_") and enc:                              # resistencias
        x = _num(v.split()[0])
        if x is None:
            return None
        c = [r for r in cat if r["categoria"].startswith("Resistors") and r["huella"] == "R_" + enc
             and _num(r["valor"]) is not None and abs(_num(r["valor"]) - x) <= 0.005 * max(x, 1e-6)]
        return sorted(c, key=_orden)[0] if c else None
    if huella.startswith("C_") and enc:                              # capacitores cerámicos
        partes = v.split()
        x = _num(partes[0])
        vmin = float(partes[1].rstrip("V")) if len(partes) > 1 and partes[1].endswith("V") else 10.0
        if x is None:
            return None
        c = [r for r in cat if r["categoria"].startswith("Capacitors") and r["huella"] == "C_" + enc
             and _num(r["valor"]) is not None and abs(_num(r["valor"]) - x) <= 0.01 * x
             and _voltaje(r["descripcion"]) >= vmin]
        return sorted(c, key=lambda r: (_orden(r)[0], _voltaje(r["descripcion"]), _orden(r)[1]))[0] if c else None
    if huella.startswith("LED_") and enc:                            # LED indicadores por color
        color = {"ROJO": "Red", "VERDE": "Green", "LED": "Red", "AZUL": "Blue", "AMARILLO": "Yellow"}.get(v.upper())
        c = [r for r in cat if r["huella"].endswith(enc) and "LED" in r["descripcion"]
             and color and (color in r["descripcion"] or (color == "Green" and "Emerald" in r["descripcion"]))]
        return sorted(c, key=_orden)[0] if c else None
    paq = next((p for k, p in _PAQ.items() if huella.startswith(k)), None)   # semiconductores por número de parte
    v = v.split()[0]                                                 # "MMSZ5242B 12V" -> "MMSZ5242B"
    c = [r for r in cat if r["parte"].upper() == v.upper() and (paq is None or paq in r["huella"])]
    return sorted(c, key=_orden)[0] if c else None


def construir(carpeta_simbolos, salida=None):
    """Rehace jlcpcb_catalogo.csv desde los .kicad_sym de la biblioteca JLCPCB-KiCad-Library (una fila por pieza)."""
    import glob
    salida = salida or os.path.join(os.path.dirname(os.path.abspath(__file__)), "jlcpcb_catalogo.csv")
    filas = []
    for f in sorted(glob.glob(os.path.join(carpeta_simbolos, "*.kicad_sym"))):
        for bloque in re.split(r'\n\t\(symbol "', open(f, encoding="utf-8").read())[1:]:
            pr = dict(re.findall(r'\(property "([^"]+)" "([^"]*)"', bloque))
            if not pr.get("LCSC"):
                continue
            filas.append([pr["LCSC"], pr.get("Class", ""), pr.get("Part", ""), pr.get("Manufacturer", ""),
                          pr.get("Value", ""), pr.get("Footprint", "").split(":")[-1], pr.get("Stock", "0"),
                          pr.get("Price", ""), pr.get("Category", ""), pr.get("Description", "")])
    with open(salida, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["lcsc", "clase", "parte", "fabricante", "valor", "huella", "stock", "precio", "categoria",
                    "descripcion"])
        w.writerows(filas)
    return len(filas)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "construir":
        print(construir(sys.argv[2]), "piezas")
    elif len(sys.argv) > 2:
        print(buscar(sys.argv[1], sys.argv[2]))
    else:
        print("uso: python3 jlcpcb.py construir <carpeta symbols>  |  python3 jlcpcb.py <valor> <huella>")
