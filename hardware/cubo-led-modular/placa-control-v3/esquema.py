"""Esquemático por bloques, generado de la MISMA lista de conexiones que la placa (diseno.py): no pueden diferir.
Cada componente se dibuja con etiquetas de red en sus pines (estilo hoja con etiquetas). Salida: esquema.html -> PDF/PNG."""
import html
import schemdraw
import schemdraw.elements as e
import diseno as D
schemdraw.use("svg")

PINES_IC = {
    "TPS54560DDA": ([("BOOT", "1", "left"), ("VIN", "2", "left"), ("EN", "3", "left"), ("RT/CLK", "4", "left")],
                    [("SW", "8", "right"), ("GND", "7", "right"), ("COMP", "6", "right"), ("FB", "5", "right"), ("PAD", "9", "right")]),
    "LMR14006": ([("VIN", "5", "left"), ("SHDN", "4", "left"), ("GND", "2", "left")], [("CB", "1", "right"), ("SW", "6", "right"), ("FB", "3", "right")]),
    "INA226": ([("IN+", "10", "left"), ("IN−", "9", "left"), ("VBUS", "8", "left"), ("VS", "6", "left"), ("GND", "7", "left")],
               [("SDA", "4", "right"), ("SCL", "5", "right"), ("ALERT", "3", "right"), ("A0", "2", "right"), ("A1", "1", "right")]),
    "MCP4725A0": ([("VDD", "3", "left"), ("VSS", "2", "left"), ("A0", "6", "left")], [("SDA", "4", "right"), ("SCL", "5", "right"), ("VOUT", "1", "right")]),
    "UCC27524": ([("INA", "2", "left"), ("INB", "4", "left"), ("ENA", "1", "left"), ("ENB", "8", "left")],
                 [("OUTA", "7", "right"), ("OUTB", "5", "right"), ("VDD", "6", "right"), ("GND", "3", "right")]),
    "RS-485 3.3 V": ([("DI", "4", "left"), ("DE", "3", "left"), ("/RE", "2", "left"), ("GND", "5", "left")],
                     [("RO", "1", "right"), ("A", "6", "right"), ("B", "7", "right"), ("VCC", "8", "right")]),
    "UCC27517": ([("IN+", "3", "left"), ("IN−", "4", "left"), ("GND", "2", "left")], [("OUT", "5", "right"), ("VDD", "1", "right")]),
    "74AHCT1G125": ([("A", "2", "left"), ("OE", "1", "left"), ("GND", "3", "left")], [("Y", "4", "right"), ("VCC", "5", "right")]),
    "ESP32-C3FH4": ([("LNA_IN", "1", "left"), ("VDD3P3", "2", "left"), ("VDD3P3", "3", "left"), ("VDDA", "31", "left"), ("VDDA", "32", "left"),
                     ("VDD3P3_RTC", "11", "left"), ("VDD3P3_CPU", "17", "left"), ("VDD_SPI", "18", "left"), ("CHIP_EN", "7", "left"),
                     ("XTAL_P", "30", "left"), ("XTAL_N", "29", "left"), ("GPIO18/D−", "25", "left"), ("GPIO19/D+", "26", "left"), ("GND (EP)", "33", "left")],
                    [("GPIO0", "4", "right"), ("GPIO1", "5", "right"), ("GPIO2", "6", "right"), ("GPIO3", "8", "right"), ("GPIO4", "9", "right"),
                     ("GPIO5", "10", "right"), ("GPIO6", "12", "right"), ("GPIO7", "13", "right"), ("GPIO8", "14", "right"), ("GPIO9", "15", "right"),
                     ("GPIO10", "16", "right"), ("GPIO20", "27", "right"), ("GPIO21", "28", "right"), ("SPI 19–24", "19", "right")]),
    "AP2112K-3.3": ([("VIN", "1", "left"), ("EN", "3", "left"), ("GND", "2", "left")], [("VOUT", "5", "right"), ("NC", "4", "right")]),
    "40 MHz": ([("XIN", "1", "left"), ("GND", "2", "left")], [("XOUT", "3", "right"), ("GND", "4", "right")]),
}
FUNCION_GPIO = {"GPIO4": "EN reductor", "GPIO3": "NTC", "GPIO1": "Vin÷11", "GPIO0": "ID tarjeta", "GPIO5": "PWM G", "GPIO6": "PWM B",
                "GPIO7": "PWM W", "GPIO8": "SDA", "GPIO9": "SCL / BOOT", "GPIO10": "WS2812 / PWM CW", "GPIO2": "DMX RX", "GPIO20": "LED", "GPIO21": "PWM R"}
_V2_GPIO = {"IO4": "EN reductor", "IO3": "NTC", "IO1": "Vin÷11", "IO0": "ID tarjeta", "IO5": "PWM G",
                "IO6": "PWM B", "IO7": "PWM W", "IO8": "SDA", "IO9": "SCL", "IO10": "datos WS2812 / PWM CW", "IO2": "DMX RX", "IO20": "LED", "IO21": "PWM R"}
SECCIONES = [
    ("1 · Entrada del cartucho y protección", ["J1", "F1", "Q1", "DZ1", "R1", "D1", "C1", "TP1"]),
    ("2 · Reductor principal 5 A (TPS54560) y tarjeta de configuración",
     ["U1", "C2", "C3", "C4", "C5", "C6", "R2", "R3", "R4", "R5", "C7", "C8", "L1", "D2", "C10", "C11", "C12", "R6", "C9", "J3", "R8", "D5", "RS", "D3"]),
    ("3 · Medición y ajuste: INA226, DAC MCP4725, ID, Vin y temperatura", ["U4", "C13", "R9", "R10", "U5", "C14", "R11", "C15", "R12", "R13", "C19", "TH1", "R14"]),
    ("4 · 5 V auxiliar (LMR14006) y 3.3 V (AP2112K)", ["U2", "C16", "R17", "C17", "D4", "L2", "R18", "R19", "C18", "D6", "TP2", "U11", "C30", "C31", "TP3"]),
    ("5 · ESP32-C3FH4 soldado: alimentación, reset, cristal, RF, programación y LED",
     ["U3", "Y1", "J5", "J6", "L3", "C35", "C34", "C36", "C43", "C42", "C44", "C45", "C47", "R32", "C48", "L5", "C49", "C50", "C40", "L4", "C41", "LED1", "R16", "TP4"]),
    ("6 · Cinco canales PWM (UCC27524 ×2 + UCC27517 + MOSFET), datos WS2812 y salida", ["U6", "U7", "U10", "C20", "C21", "C24", "Q2", "Q3", "Q4", "Q5", "Q6"] +
     [f"R{i}" for i in range(20, 25)] + [f"R{i}" for i in range(40, 45)] + ["U8", "C22", "R28", "J2"]),
    ("7 · DMX512 por cable (RS-485, solo recepción)", ["U9", "C23", "R30", "D7", "R31", "JP3", "J4"]),
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
        red(d, el.drain, n["D"], "top"); d.add(e.Ground().at(el.source)); red(d, el.gate, n["4"], "left")

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
            cls = e.Zener if r == "DZ1" else (e.Schottky if r in ("D2", "D4", "D6") else e.Diode)
            el = d.add(cls().at((X, Y - 2.2)).up().length(2.2).label(f"{r}\n{p['val']}", loc="bottom", fontsize=9, ofst=0.25))
            red(d, el.end, n["1"], "top")
            if n["2"] == "GND": d.add(e.Ground().at(el.start))
            else: red(d, el.start, n["2"], "bot")
        elif r == "D7":           # SM712: TVS de 1 y 2 a GND (pin 3)
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
 1: "Q1 protege contra inversión de polaridad (el diodo interno conduce y luego el canal se enciende). DZ1 limita Vgs a 12 V. D1 recorta transitorios del cartucho.",
 2: "Vout = 0.8 V × (1 + 29.4k / R_B). R_B vive en la tarjeta (J3 pin 1–2): sin tarjeta, FB = Vout y la salida se cae a ~0.8 V. El DAC solo inyecta corriente al FB a través de D5: solo puede BAJAR el voltaje. Compensación tipo II para cruce ≈ 15 kHz a 12 V (verificar con la herramienta de TI). RS = 5 mΩ, sentido Kelvin al INA226.",
 3: "INA226 en 0x40 (A0 = A1 = GND), DAC en 0x60. ALERT del INA226 está en la red EN: al dispararse tira el EN del reductor a GND por hardware (~1 ms). Pull-up de ID = 47k (R_ID de la tarjeta: 10k…150k).",
 4: "5 V para drivers y buffer WS2812; el AP2112K-3.3 (600 mA) da 3.3 V al ESP32-C3 y a los sensores (antes lo hacía el módulo). D6 evita alimentar al USB de la PC al programar con la placa conectada.",
 5: "Chip ESP32-C3FH4 soldado (sin módulo), circuito según la guía de hardware de Espressif: VDD3P3 con 2.0 nH + 1/10/0.1 µF, VDDA 1 µF + 10 nF, RTC/CPU 0.1 µF, VDD_SPI 1 µF (alimenta la flash interna), CHIP_EN con RC 10k/1 µF. Cristal 40 MHz ±10 ppm con 24 nH en serie en XTAL_P y cargas de 12 pF (C = 2·(CL − Cparásita), ajustar con prueba de tono hasta ±10 ppm). RF: red CLC (C40/L4/C41) junto al chip, por sintonizar con analizador de redes; arranca con L4 = 0 Ω y C40/C41 sin poblar; tramo de 2 mm hasta el U.FL (0.8 mm con GND a 0.2 mm: coplanar ≈ 57 Ω en FR4 de 1.6 mm, muy corto frente a λ) y antena externa. Programación por el USB nativo del C3 (pads pogo J5); IO9 a GND durante el reset = modo descarga. Mismo mapa de GPIO que la v2: el firmware de la v2 corre sin cambios.",
 7: "Transceptor fijo en recepción (DE y /RE a GND, DI a 3.3 V). SM712 protege A/B contra descargas (−7/+12 V). La terminación de 120 Ω solo se pone (JP3) en el último equipo. Bornera: 1 GND, 2 D−, 3 D+ = pines 1, 2 y 3 del XLR.",
 6: "5.º canal (blanco frío) con UCC27517; su entrada comparte IO10 con los datos WS2812: el firmware no deja activar tiras RGB+CCT y direccionables a la vez. Drivers de 5 A: conmutación de ~20 ns a 19 kHz, sin calentar los MOSFET. R20–R24 amortiguan la compuerta; R40–R44 la mantienen apagada si falta 5 V. Ánodo común (V+) para tiras RGBW; GND y DAT para tiras direccionables.",
}

def main():
    partes = []
    for i, (titulo, refs) in enumerate(SECCIONES, 1):
        partes.append(f'<section><h2>{html.escape(titulo)}</h2><div class="svg">{dibujar(refs)}</div><p class="nota">{html.escape(NOTAS[i])}</p></section>')
    doc = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Cubo AP · esquema placa de control v3</title>
<style>body{{font-family:'DejaVu Sans',Arial,sans-serif;margin:0;padding:18px 26px;color:#1b1b1b}} h1{{font-size:20px;margin:0 0 4px}}
.sub{{color:#555;font-size:12px;margin-bottom:10px}} section{{page-break-inside:avoid;border-top:2px solid #0b5d36;margin-top:14px;padding-top:6px}}
h2{{font-size:15px;color:#0b5d36;margin:4px 0 6px}} .svg svg{{max-width:100%;height:auto}} .nota{{font-size:11.5px;color:#333;background:#f1f6f3;padding:6px 9px;border-radius:6px}}
@page{{size:A3 landscape;margin:10mm}}</style></head><body>
<h1>Cubo AP · Placa de control v3 (ESP32-C3 soldado) — esquema</h1>
<div class="sub">Generado de diseno.py (la misma lista de conexiones que la placa). Las etiquetas azules son nombres de red: pines con la misma etiqueta están conectados. Sin probar en hardware.</div>
{''.join(partes)}</body></html>"""
    open("esquema.html", "w").write(doc)
    print("esquema.html listo")

if __name__ == "__main__":
    main()
