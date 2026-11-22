"""Esquemático por bloques, generado de la MISMA lista de conexiones que la placa (diseno.py): no pueden diferir.
Cada componente se dibuja con etiquetas de red en sus pines (estilo hoja con etiquetas). Salida: esquema.html -> PDF/PNG."""
import html
import schemdraw
import schemdraw.elements as e
import diseno as D
schemdraw.use("svg")

PINES_IC = {
    "CH32V003F4P6": ([("PD6 / URX", "3", "left"), ("VDD", "9", "left"), ("VSS", "7", "left"), ("PD1 / SWIO", "18", "left"),
                      ("PC2", "12", "left"), ("PC1", "11", "left")],
                     [("PD2 / T1CH1", "19", "right"), ("PA1 / T1CH2", "5", "right"), ("PC3 / T1CH3", "13", "right"), ("PC4 / T1CH4", "14", "right")]),
    "MAX485": ([("DI", "4", "left"), ("DE", "3", "left"), ("/RE", "2", "left"), ("GND", "5", "left")],
               [("RO", "1", "right"), ("A", "6", "right"), ("B", "7", "right"), ("VCC", "8", "right")]),
    "78L05": ([("IN", "3", "left"), ("GND", "2", "left")], [("OUT", "1", "right")]),
}
FUNCION_GPIO = {"GPIO4": "EN reductor", "GPIO3": "NTC", "GPIO1": "Vin÷11", "GPIO0": "ID tarjeta", "GPIO5": "PWM G", "GPIO6": "PWM B",
                "GPIO7": "PWM W", "GPIO8": "SDA", "GPIO9": "SCL / BOOT", "GPIO10": "WS2812 / PWM CW", "GPIO2": "DMX RX", "GPIO20": "LED", "GPIO21": "PWM R"}
_V2_GPIO = {"IO4": "EN reductor", "IO3": "NTC", "IO1": "Vin÷11", "IO0": "ID tarjeta", "IO5": "PWM G",
                "IO6": "PWM B", "IO7": "PWM W", "IO8": "SDA", "IO9": "SCL", "IO10": "datos WS2812 / PWM CW", "IO2": "DMX RX", "IO20": "LED", "IO21": "PWM R"}
SECCIONES = [
    ("1 · Entrada 12–24 V, fusible y 5 V (78L05)", ["J1", "F1", "D1", "C1", "U3", "C2"]),
    ("2 · CH32V003, botón de aprendizaje, LED y programación", ["U1", "C3", "SW1", "LED1", "R6", "J5"]),
    ("3 · DMX512 por cable (RS-485, solo recepción) con entrada y salida en paralelo", ["U2", "C4", "D2", "R5", "JP1", "J3", "J4"]),
    ("4 · Cuatro salidas PWM con MOSFET de nivel lógico", ["J2", "Q1", "Q2", "Q3", "Q4", "R1", "R2", "R3", "R4", "R11", "R12", "R13", "R14"]),
]
PART = {p["ref"]: p for p in D.P}

def red(d, punto, n, lado="top"):
    if n == "GND":
        d.add(e.Ground().at(punto).down() if lado != "top" else e.Ground().at(punto).down())
    elif n.startswith("NC"):
        d.add(e.Label().at(punto).label("×", fontsize=11))
    else:
        d.add(e.Dot(radius=0.06).at(punto).label(n, loc={"top": "top", "bot": "bottom", "left": "left", "right": "right"}[lado], fontsize=10, color="#1a5fb4"))

def dos(d, cls, p, x, y, n_arriba, n_abajo, etiqueta=None):
    el = d.add(cls().at((x, y)).down().length(2.2).label(etiqueta or f"{p['ref']}\n{p['val']}", loc="bottom", fontsize=9, ofst=0.25))
    red(d, el.start, n_arriba, "top")
    if n_abajo == "GND": d.add(e.Ground().at(el.end))
    else: red(d, el.end, n_abajo, "bot")

def ic(d, p, x, y):
    izq, der = PINES_IC[p["val"]]
    pins = [e.IcPin(name=n, pin=num, side=s, anchorname=f"p{num}") for n, num, s in izq + der]
    alto = max(len(izq), len(der)) * 0.75 + 0.6
    el = d.add(e.Ic(pins=pins, size=(6.4 if p["fp"] == "QFN32" else 4.6, alto), pinspacing=0.75, edgepadH=0.4).at((x, y)).anchor("center"))
    d.add(e.Label().at((x, y - alto / 2 - 0.55)).label(f"{p['ref']} · {p['val']}", fontsize=10.5))
    for n, num, s in izq + der:
        a = getattr(el, f"p{num}")
        net = p["nets"].get(num, "NC (flash interna)" if p["fp"] == "QFN32" else "NC")
        dx = -0.7 if s == "left" else 0.7
        ln = d.add(e.Line().at(a).right(dx) if dx > 0 else e.Line().at(a).left(-dx))
        etiqueta = net + (f"  ({FUNCION_GPIO[n]})" if p["fp"] == "QFN32" and n in FUNCION_GPIO else "")
        d.add(e.Dot(radius=0.06).at(ln.end).label(etiqueta, loc="left" if s == "left" else "right", fontsize=10,
                                                 color="#1a5fb4" if net != "GND" else "#555"))
    return alto

def mos(d, p, x, y):
    n = p["nets"]
    if p["fp"] == "SO8-PMOS":
        el = d.add(e.PFet().at((x, y)).label(f"{p['ref']} · P-MOSFET", loc="bottom", fontsize=9, ofst=0.6))
        red(d, el.drain, n["5"], "top"); red(d, el.source, n["1"], "bot"); red(d, el.gate, n["4"], "left")
    else:
        el = d.add(e.NFet().at((x, y)).label(f"{p['ref']}", loc="right", fontsize=9))
        red(d, el.drain, n.get("D", n.get("3")), "top"); d.add(e.Ground().at(el.source)); red(d, el.gate, n.get("4", n.get("1")), "left")

def conector(d, p, x, y):
    pins = sorted(p["nets"].items(), key=lambda kv: int(kv[0]))
    el = d.add(e.Ic(pins=[e.IcPin(name=str(k), side="right", anchorname=f"p{k}") for k, _ in pins], size=(1.2, len(pins) * 0.75 + 0.4),
                    pinspacing=0.75, label=f"{p['ref']}", lsize=10).at((x, y)).anchor("center"))
    for k, net in pins:
        ln = d.add(e.Line().at(getattr(el, f"p{k}")).right(0.7))
        d.add(e.Dot(radius=0.06).at(ln.end).label(net, loc="right", fontsize=10, color="#1a5fb4" if net != "GND" else "#555"))
    d.add(e.Label().at((x, y - len(pins) * 0.375 - 0.9)).label(p["val"], fontsize=9))

def dibujar(refs):
    d = schemdraw.Drawing(show=False); d.config(fontsize=10, unit=2.2, lw=1.1, font="DejaVu Sans")
    grandes = [r for r in refs if PART[r]["val"] in PINES_IC or PART[r]["fp"].startswith(("BORNE", "HDR", "PROG", "UFL"))]
    chicos = [r for r in refs if r not in grandes]
    x = 0.0; alto_max = 2.0
    for r in grandes:
        p = PART[r]
        if p["val"] in PINES_IC: alto_max = max(alto_max, max(len(PINES_IC[p["val"]][0]), len(PINES_IC[p["val"]][1])) * 0.75 + 0.6)
        else: alto_max = max(alto_max, len(p["nets"]) * 0.75 + 0.4)
    for r in grandes:
        p = PART[r]
        if p["val"] in PINES_IC:
            ic(d, p, x + (8.0 if p["fp"] == "QFN32" else 5.0), 0); x += 14.0 if p["fp"] != "QFN32" else 24.0
        else:
            conector(d, p, x + 1.0, 0); x += 6.5
    col, fila = 0, 0
    y0 = -(alto_max / 2 + 2.2) if grandes else 0
    por_fila = max(6, int(max(x, 30) / 4.2))
    for r in chicos:
        p = PART[r]; n = p["nets"]; X, Y = col * 4.2, y0 - fila * 5.2
        fp = p["fp"]
        if fp in ("SOD123", "SMA", "SMB", "SMC"):
            cls = e.Zener if r == "DZ1" else (e.Schottky if p["val"].startswith(("B1", "B5", "SS")) else e.Diode)
            el = d.add(cls().at((X, Y - 2.2)).up().length(2.2).label(f"{r}\n{p['val']}", loc="bottom", fontsize=9, ofst=0.25))
            red(d, el.end, n["1"], "top")
            if n["2"] == "GND": d.add(e.Ground().at(el.start))
            else: red(d, el.start, n["2"], "bot")
        elif p["val"] == "SM712":  # SM712: TVS de 1 y 2 a GND (pin 3)
            for k, pin in enumerate(("1", "2")):
                el = d.add(e.Zener().at((X + k * 2.0, Y - 2.2)).up().length(2.2).label(f"{r}\n{p['val']}" if k == 0 else "", loc="bottom", fontsize=9, ofst=0.25))
                red(d, el.end, n[pin], "top"); d.add(e.Ground().at(el.start))
            col += 1
        elif fp == "SOT23":       # BAT54: 1 ánodo, 3 cátodo
            el = d.add(e.Schottky().at((X, Y - 2.2)).up().length(2.2).label(f"{r}\n{p['val']}", loc="bottom", fontsize=9, ofst=0.25))
            red(d, el.end, n["3"], "top"); red(d, el.start, n["1"], "bot")
        elif r.startswith("LED"): dos(d, e.LED, p, X, Y, n["1"], n["2"])
        elif r.startswith("L"): dos(d, e.Inductor2, p, X, Y, n["1"], n["2"])
        elif r.startswith("F"): dos(d, e.Fuse, p, X, Y, n["1"], n["2"])
        elif r.startswith("C") and fp.startswith("ELEC"): dos(d, e.CapacitorPolar if hasattr(e, "CapacitorPolar") else e.Capacitor, p, X, Y, n["1"], n["2"])
        elif r.startswith("C"): dos(d, e.Capacitor, p, X, Y, n["1"], n["2"])
        elif r.startswith("TH"): dos(d, e.Thermistor if hasattr(e, "Thermistor") else e.ResistorVar, p, X, Y, n["1"], n["2"])
        elif r.startswith("R"): dos(d, e.Resistor, p, X, Y, n["1"], n["2"])
        elif r.startswith("SW"): dos(d, e.Button, p, X, Y, n["1"], n["2"])
        elif r.startswith("Q"): mos(d, p, X + 0.6, Y - 1.2)
        elif r.startswith("TP"):
            d.add(e.Dot(radius=0.12, open=True).at((X, Y - 0.6)).label(f"{r}: {n['1']}", loc="right", fontsize=9))
        else: dos(d, e.Resistor, p, X, Y, n.get("1", "?"), n.get("2", "?"))
        col += 1
        if col >= por_fila: col, fila = 0, fila + 1
    return d.get_imagedata("svg").decode()

NOTAS = {
 1: "La corriente de las tiras va directo de J1 por F1 (6.3 A) a V+ de J2 por cobre ancho. D1 solo protege la lógica contra polaridad invertida; las tiras de ánodo común no conducen al revés. El 78L05 acepta hasta 30 V: el nodo trabaja con tiras de 12 o 24 V.",
 2: "CH32V003 a 5 V (rango 2.8–5.5 V), reloj interno de 48 MHz, sin cristal. Botón: entra/sale del modo aprender; en ese modo la consola pone UN canal en ≥ 200 y el resto en < 50, y ese canal queda como dirección (3 tramas iguales; se guarda en flash). LED: fijo = recibe, destello = sin señal (mantiene el último valor), rápido = aprendiendo. Programación por SWIO con WCH-LinkE.",
 3: "Transceptor de 5 V fijo en recepción (DE, /RE y DI a GND). SM712 contra descargas. J3 y J4 en paralelo para encadenar nodos; la terminación de 120 Ω (JP1) va solo en el último. Bornera: 1 GND, 2 D−, 3 D+ = pines 1, 2 y 3 del XLR.",
 4: "AO3400A (nivel lógico, 26 mΩ a 4.5 V) manejados directo por el PWM de TIM1 a 3.9 kHz y 10 bit, con curva gamma. 100 Ω amortiguan la compuerta y 100k la mantienen apagada al arrancar. Hasta 3 A por canal y 6 A en total (fusible).",
}

def main():
    partes = []
    for i, (titulo, refs) in enumerate(SECCIONES, 1):
        partes.append(f'<section><h2>{html.escape(titulo)}</h2><div class="svg">{dibujar(refs)}</div><p class="nota">{html.escape(NOTAS[i])}</p></section>')
    doc = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Cubo AP · esquema nodo AP</title>
<style>body{{font-family:'DejaVu Sans',Arial,sans-serif;margin:0;padding:18px 26px;color:#1b1b1b}} h1{{font-size:20px;margin:0 0 4px}}
.sub{{color:#555;font-size:12px;margin-bottom:10px}} section{{page-break-inside:avoid;border-top:2px solid #0b5d36;margin-top:14px;padding-top:6px}}
h2{{font-size:15px;color:#0b5d36;margin:4px 0 6px}} .svg svg{{max-width:100%;height:auto}} .nota{{font-size:11.5px;color:#333;background:#f1f6f3;padding:6px 9px;border-radius:6px}}
@page{{size:A3 landscape;margin:10mm}}</style></head><body>
<h1>Cubo AP · Nodo AP (CH32V003, DMX → RGBW) — esquema</h1>
<div class="sub">Generado de diseno.py (la misma lista de conexiones que la placa). Las etiquetas azules son nombres de red: pines con la misma etiqueta están conectados. Sin probar en hardware.</div>
{''.join(partes)}</body></html>"""
    open("esquema.html", "w").write(doc)
    print("esquema.html listo")

if __name__ == "__main__":
    main()
