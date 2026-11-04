"""Fuente única de verdad del circuito: componentes, valores, huellas y redes.

El esquema (.kicad_sch), la PCB (.kicad_pcb) y la lista de materiales se
generan a partir de esta tabla, de modo que siempre son consistentes entre sí.
"""

LIB = "ControladorFlechas"

# Bloques del esquema: (id, título, x, y) en mm sobre hoja A3
BLOCKS = {
    "PWR": ("1. ENTRADA 36 V Y PROTECCIONES (zona de potencia)", 15, 20, 185, 70),
    "REG": ("2. REGULADOR LÓGICO 36 V -> 11.5 V (LM317T)", 205, 20, 125, 70),
    "OSC": ("3. OSCILADOR NE555 (0.24-1.6 s por paso)", 15, 95, 120, 90),
    "CNT": ("4. CONTADOR CD4017, RESET DE ENCENDIDO, PAUSA Y REINICIO", 140, 95, 270, 90),
    "OUT": ("5. SALIDAS DE LAS FLECHAS: MOSFET + FUENTE DE CORRIENTE 9 mA", 15, 190, 260, 97),
    "OPT": ("6. SALIDAS OPCIONALES (NO CONECTAR hasta medir las series)", 280, 190, 130, 68),
    "JMP": ("7. PUENTES DE ALAMBRE (PCB)", 335, 20, 75, 70),
}

# Banderas PWR_FLAG: red -> (bloque, x, y)
FLAGS = {"+36V": ("PWR", 150, 8), "GND": ("PWR", 165, 8), "F1N": ("OUT", 5, 55), "F2N": ("OUT", 5, 63),
         "F3N": ("OUT", 5, 71)}

# Cada componente:
# ref, valor, símbolo KiCad, huella (biblioteca del proyecto), {pin: red},
# bloque, (x, y, rot) relativo al bloque en el esquema, función, dnp
C = []


def add(ref, val, sym, fp, pins, blk, pos, func, dnp=False, desc=""):
    C.append(dict(ref=ref, val=val, sym=sym, fp=fp, pins=pins, blk=blk, pos=pos, func=func, dnp=dnp, desc=desc))


R, CAP, CP, LED, D, DZ = "Device:R", "Device:C", "Device:C_Polarized", "Device:LED", "Device:D", "Device:D_Zener"
RAX, DISC, CP8, CP5, LED3 = "R_Axial_P10.16mm", "C_Disc_P5.08mm", "CP_Radial_D8.0mm_P3.81mm", "CP_Radial_D5.0mm_P2.54mm", "LED_D3.0mm"
T2, T4 = "Connector:Screw_Terminal_01x02", "Connector:Screw_Terminal_01x04"
TB2, TB4 = "Clema_2P_P5.08mm", "Clema_4P_P5.08mm"

# ---------------- 1. Entrada y protecciones ----------------
add("J1", "36V ENTRADA", T2, TB2, {"1": "GND", "2": "VIN"}, "PWR", (0, 15, 0),
    "Entrada de la fuente aislada de 36 VCC (pin 2 = 36V+, pin 1 = GND)")
add("J2", "INTERRUPTOR", T2, TB2, {"1": "VIN", "2": "VSW"}, "PWR", (0, 40, 0),
    "Interruptor de encendido externo (palanca/balancín). Si no se usa, puentear con alambre")
add("F1", "RXEF025 0.25A", "Device:Polyfuse", "PTC_Radial_P5.08mm", {"1": "VSW", "2": "VF"}, "PWR", (30, 15, 0),
    "Fusible rearmable PTC 0.25 A hold / 0.5 A trip, 72 V")
add("D1", "1N4007", D, "D_DO-41_P10.16mm", {"1": "+36V", "2": "VF"}, "PWR", (55, 6, 180),
    "Protección contra inversión de polaridad (diodo serie)")
add("D2", "P6KE47A", DZ, "D_DO-15_P12.70mm", {"1": "+36V", "2": "GND"}, "PWR", (80, 15, 270),
    "TVS unidireccional 40.2 V standoff, supresión de transitorios en 36 V")
add("C1", "100uF 63V", CP, CP8, {"1": "+36V", "2": "GND"}, "PWR", (100, 15, 0),
    "Capacitor electrolítico de entrada (volumen)")
add("C2", "100nF 100V", CAP, DISC, {"1": "+36V", "2": "GND"}, "PWR", (118, 15, 0),
    "Desacoplo cerámico de 36 V")
add("R1", "33k", R, RAX, {"1": "+36V", "2": "LED1A"}, "PWR", (138, 10, 0), "Limitador del LED indicador de 36 V (1 mA)")
add("LED1", "ROJO 3mm 36V", LED, LED3, {"1": "GND", "2": "LED1A"}, "PWR", (138, 32, 90), "Indicador: 36 V presentes")

# ---------------- 2. Regulador lógico ----------------
add("U3", "LM317T", "Regulator_Linear:LM317_TO-220", "TO-220-3_Vertical", {"3": "+36V", "2": "+12V", "1": "ADJ12"},
    "REG", (15, 22, 0), "Regulador lineal 36 V -> 11.5 V para la lógica (reemplaza al módulo LM2596)")
add("R2", "1k", R, RAX, {"1": "+12V", "2": "ADJ12"}, "REG", (45, 25, 0), "Divisor del LM317T (R1 de la fórmula)")
add("R3", "8.2k", R, RAX, {"1": "ADJ12", "2": "GND"}, "REG", (30, 45, 0), "Divisor del LM317T: Vout = 1.25(1+8.2k/1k) = 11.5 V")
add("C3", "100uF 63V", CP, CP8, {"1": "+12V", "2": "GND"}, "REG", (55, 25, 0), "Capacitor electrolítico de 12 V")

# ---------------- 3. Oscilador NE555 ----------------
add("U1", "NE555P", "Timer:NE555P", "DIP-8_W7.62mm",
    {"1": "GND", "2": "TIM", "3": "CLK555", "4": "RST555", "5": "CV", "6": "TIM", "7": "DIS", "8": "+12V"},
    "OSC", (50, 35, 0), "Oscilador astable: define la velocidad de la secuencia")
add("C4", "100nF", CAP, DISC, {"1": "+12V", "2": "GND"}, "OSC", (85, 10, 0), "Desacoplo de U1 (junto al pin 8)")
add("R5", "4.7k", R, RAX, {"1": "+12V", "2": "DIS"}, "OSC", (5, 10, 0), "RA del 555")
add("R6", "15k", R, RAX, {"1": "DIS", "2": "RB"}, "OSC", (5, 32, 0), "RB fija del 555 (velocidad máxima)")
add("RV1", "100k", "Device:R_Potentiometer_Trim", "Trimpot_3296W", {"1": "RB", "2": "TIM", "3": "TIM"}, "OSC",
    (10, 62, 0), "Ajuste de velocidad 0.24-1.6 s por paso (reóstato)")
add("C5", "10uF 50V", CP, CP5, {"1": "TIM", "2": "GND"}, "OSC", (35, 55, 0), "Capacitor de temporización")
add("C6", "100nF", CAP, DISC, {"1": "CV", "2": "GND"}, "OSC", (50, 55, 0), "Filtro del pin CONT (5)")
add("R7", "1k", R, RAX, {"1": "CLK555", "2": "CLK"}, "OSC", (80, 42, 90), "Resistencia serie del reloj hacia el CD4017")
add("R8", "10k", R, RAX, {"1": "CLK555", "2": "LED6A"}, "OSC", (95, 52, 0), "Limitador del LED de pulso")
add("LED6", "ROJO 3mm PULSO", LED, LED3, {"1": "GND", "2": "LED6A"}, "OSC", (95, 70, 90), "Indicador del pulso del 555 / CENTROS")

# ---------------- 4. Contador ----------------
add("U2", "CD4017BE", "4xxx:4017", "DIP-16_W7.62mm",
    {"14": "CLK", "13": "INH", "15": "RST", "16": "+12V", "8": "GND", "3": "Q0", "2": "Q1", "4": "Q2", "7": "Q3",
     "10": None, "1": None, "5": None, "6": None, "9": None, "11": None, "12": None},
    "CNT", (85, 28, 0), "Contador Johnson: Q0-Q2 = flechas 1-3, Q3 -> RESET (3 pasos)")
add("C7", "100nF", CAP, DISC, {"1": "+12V", "2": "GND"}, "CNT", (115, 2, 0), "Desacoplo de U2 (junto al pin 16)")
add("R9", "100k", R, RAX, {"1": "INH", "2": "GND"}, "CNT", (35, 25, 0), "CLOCK INHIBIT (pin 13) a GND a través de 100k (conteo siempre habilitado)")
add("R30", "10k", R, RAX, {"1": "+12V", "2": "RST555"}, "OSC", (60, 72, 90), "Pull-up del RESET del 555 (pin 4 a +12 V a través de 10k)")
add("C8", "10uF 50V", CP, CP5, {"1": "+12V", "2": "POR"}, "CNT", (0, 38, 0), "Reset de encendido (POR), tau = 1 s")
add("R10", "100k", R, RAX, {"1": "POR", "2": "GND"}, "CNT", (0, 60, 0), "Descarga del POR")
add("D5", "1N4148", D, "D_DO-35_P7.62mm", {"1": "RST", "2": "POR"}, "CNT", (25, 50, 0), "OR de reset: POR -> RESET")
add("D7", "1N4148", D, "D_DO-35_P7.62mm", {"1": "RST", "2": "Q3"}, "CNT", (120, 48, 180), "OR de reset: Q3 -> RESET (3 pasos)")
add("R11", "100k", R, RAX, {"1": "RST", "2": "GND"}, "CNT", (45, 60, 0), "Pull-down de RESET")
add("SW2", "REINICIO", "Switch:SW_Push", "Boton_6mm", {"1": "+12V", "2": "POR"}, "CNT", (60, 74, 0),
    "Botón REINICIO: descarga C8 y repite el reset de encendido (vuelve a la flecha 1)")
add("R13", "10k", R, RAX, {"1": "Q0", "2": "LED3A"}, "CNT", (135, 12, 90), "Limitador del LED de prueba F1")
add("R14", "10k", R, RAX, {"1": "Q1", "2": "LED4A"}, "CNT", (135, 24, 90), "Limitador del LED de prueba F2")
add("R15", "10k", R, RAX, {"1": "Q2", "2": "LED5A"}, "CNT", (135, 36, 90), "Limitador del LED de prueba F3")
add("LED3", "ROJO 3mm F1", LED, LED3, {"1": "GND", "2": "LED3A"}, "CNT", (168, 12, 180), "LED de prueba: flecha 1 activa")
add("LED4", "ROJO 3mm F2", LED, LED3, {"1": "GND", "2": "LED4A"}, "CNT", (168, 24, 180), "LED de prueba: flecha 2 activa")
add("LED5", "ROJO 3mm F3", LED, LED3, {"1": "GND", "2": "LED5A"}, "CNT", (168, 36, 180), "LED de prueba: flecha 3 activa")

# ---------------- 5. Salidas de flechas ----------------
for n, q, x in ((1, "Q0", 30), (2, "Q1", 105), (3, "Q2", 180)):
    rg, rp = 16 + (n - 1) * 2, 17 + (n - 1) * 2
    ra, rb = 22 + (n - 1) * 2, 23 + (n - 1) * 2
    add("R%d" % rg, "1k", R, RAX, {"1": q, "2": "G%d" % n}, "OUT", (x + 5, 55, 90), "Resistencia de compuerta flecha %d" % n)
    add("R%d" % rp, "100k", R, RAX, {"1": "G%d" % n, "2": "GND"}, "OUT", (x + 22, 62, 0), "Pull-down de compuerta flecha %d" % n)
    add("Q%d" % n, "2N7000", "Transistor_FET:2N7000", "TO-92_2N7000", {"1": "GND", "2": "G%d" % n, "3": "DRN%d" % n},
        "OUT", (x + 38, 53, 0), "MOSFET interruptor de la flecha %d (lado bajo)" % n)
    add("U%d" % (n + 3), "LM317LZ", "Regulator_Linear:LM317L_TO92", "TO-92_LM317L",
        {"3": "F%dN" % n, "2": "I%dA" % n, "1": "DRN%d" % n}, "OUT", (x + 30, 15, 0),
        "Fuente de corriente constante 9 mA flecha %d" % n)
    add("R%d" % ra, "68 1%", R, RAX, {"1": "I%dA" % n, "2": "I%dB" % n}, "OUT", (x + 55, 18, 0),
        "Programación de corriente flecha %d (68+68 = 136 ohm)" % n)
    add("R%d" % rb, "68 1%", R, RAX, {"1": "I%dB" % n, "2": "DRN%d" % n}, "OUT", (x + 55, 38, 0),
        "Programación de corriente flecha %d (68+68 = 136 ohm)" % n)
add("J3", "FLECHAS", T4, TB4, {"1": "+36V", "2": "F1N", "3": "F2N", "4": "F3N"}, "OUT", (8, 20, 0),
    "Salida a las 3 flechas: pin 1 = +36V (ánodo común), 2 = F1-, 3 = F2-, 4 = F3-")

# ---------------- 6. Opcionales ----------------
add("R28", "1k", R, RAX, {"1": "CLK555", "2": "G4"}, "OPT", (0, 30, 90), "Resistencia de compuerta CENTROS")
add("R29", "100k", R, RAX, {"1": "G4", "2": "GND"}, "OPT", (15, 40, 0), "Pull-down de compuerta CENTROS")
add("Q4", "2N7000", "Transistor_FET:2N7000", "TO-92_2N7000", {"1": "GND", "2": "G4", "3": "CENT_D"}, "OPT", (30, 30, 0),
    "MOSFET de la salida CENTROS (parpadeo con el 555). Máx. 150 mA")
add("JP2", "NO MONTAR", "Jumper:Jumper_2_Open", "Enlace_Opcional_P7.62mm", {"1": "+36V", "2": "V_FLOR"}, "OPT", (40, 5, 0),
    "Habilita +36V en FLORES. Montar solo después de medir la serie", dnp=True)
add("JP3", "NO MONTAR", "Jumper:Jumper_2_Open", "Enlace_Opcional_P7.62mm", {"1": "+36V", "2": "V_BANO"}, "OPT", (80, 5, 0),
    "Habilita +36V en BAÑOS. Montar solo después de medir la serie", dnp=True)
add("J4", "CENTROS", T2, TB2, {"1": "GND", "2": "CENT_D"}, "OPT", (55, 28, 0),
    "Salida opcional CENTROS: pin 2 = retorno conmutado (-), pin 1 = GND de referencia. El + de las ramas se toma de J3 +36V")
add("J5", "FLORES", T2, TB2, {"1": "V_FLOR", "2": "GND"}, "OPT", (90, 24, 0),
    "Salida fija opcional FLORES (pin 1 = +, pin 2 = GND), resistencias en el panel")
add("J6", "BAÑOS", T2, TB2, {"1": "V_BANO", "2": "GND"}, "OPT", (90, 38, 0),
    "Salida fija opcional BAÑOS (pin 1 = +, pin 2 = GND), resistencias en el panel")

for i in range(1, 5):
    add("H%d" % i, "M3", "Mechanical:MountingHole", "Barreno_M3_3.2mm", {}, "REG", (75 + i * 12, 10, 0),
        "Barreno de montaje M3")

# Puentes de alambre calculados por el ruteador (route_result.json).
# Cada puente W une dos tramos de cobre de la misma señal; el tramo secundario recibe
# un nombre propio (p. ej. +12V_W1) para que el esquema y el DRC reflejen el puente.
import json as _json, os as _os
_RR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "route_result.json")
JUMPERS, NETSPLIT = [], {}
if _os.path.exists(_RR) and not _os.environ.get("NO_JUMPERS"):
    _d = _json.load(open(_RR))
    JUMPERS = _d.get("jumpers", [])
    NETSPLIT = _d.get("netsplit", {})
for _k, (_net, _p1, _p2) in enumerate(JUMPERS):
    _L = abs(_p2[0] - _p1[0]) + abs(_p2[1] - _p1[1])
    add("W%d" % (_k + 1), "PUENTE", "Jumper:Jumper_2_Bridged", "Puente_Alambre_P%.2fmm" % _L, {"1": _net, "2": _net},
        "JMP", (2 + (_k % 3) * 24, 14 + (_k // 3) * 16, 0), "Puente de alambre desnudo (red %s), lado componentes" % _net)
for _c in C:
    for _pn in list(_c["pins"]):
        _key = "%s.%s" % (_c["ref"], _pn)
        if _key in NETSPLIT:
            _c["pins"][_pn] = NETSPLIT[_key]

# Nombres de las patas sin conexión del CD4017 (como los genera el esquema)
NC_PIN_NAMES = {("U2", "1"): "Q5", ("U2", "5"): "Q6", ("U2", "6"): "Q7", ("U2", "9"): "Q8",
                ("U2", "10"): "Q4", ("U2", "11"): "Q9", ("U2", "12"): "Cout"}

# Resistencias montadas de pie (paso 5.08 mm) para ahorrar espacio
STANDING = {"R22", "R23", "R24", "R25", "R26", "R27", "R17", "R19", "R21", "R13", "R14", "R15",
            "R5", "R6", "R8", "R10", "R11", "R29", "R1", "R2", "R3", "R28"}
for _c in C:
    if _c["ref"] in STANDING:
        _c["fp"] = "R_Vertical_P5.08mm"

# Redes de potencia (se dibujan con símbolos de alimentación en el esquema)
POWER = {"+36V": "power:+36V", "+12V": "power:+12V", "GND": "power:GND"}
# Redes que requieren PWR_FLAG para el ERC (alimentadas desde conectores/diodos)
PWR_FLAGS = ["+36V", "GND", "F1N", "F2N", "F3N"]
# tramos separados por puentes que alimentan pines power_in: también llevan PWR_FLAG
_PWR_OUT = {("U3", "2"), ("U4", "2"), ("U5", "2"), ("U6", "2")}
for _key, _n in NETSPLIT.items():
    _r, _p = _key.split(".")
    if _n not in PWR_FLAGS and not any((_r2, _p2) in _PWR_OUT for _k2, _n2 in NETSPLIT.items()
                                        if _n2 == _n for _r2, _p2 in [tuple(_k2.split("."))]):
        PWR_FLAGS.append(_n)

# Redes con pista de alimentación de 1.2 mm (el resto usa 0.8 mm)
POWER_NETS_W = {"VIN", "VSW", "VF", "+36V", "GND", "+12V", "V_FLOR", "V_BANO", "CENT_D"}


def by_ref():
    return {c["ref"]: c for c in C}


def nets():
    out = {}
    for c in C:
        for p, n in c["pins"].items():
            if n:
                out.setdefault(n, []).append((c["ref"], p))
    return out


if __name__ == "__main__":
    for n, pins in sorted(nets().items()):
        print(n, pins)
    print(len(C), "componentes")
