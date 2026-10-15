"""AP Electric Industrial · 7R Tour (rev B, CONCEPTO): 7 salidas por relé, 8 entradas de 24 V, Modbus RTU aislado.

Una placa para dos SKU:
- 7R Tour 24DC: se alimenta con 24 V CC de una fuente certificada externa (J9). No se montan J8, F2, RV1, PS1, D3, C3.
- 7R Tour CA: con la fuente encapsulada Mean Well IRM-20-24 (85-264 VCA, certificada por su fabricante) en la placa.

Bloques:
- 7 relés Omron G2RL-1A-E DC24 (16 A 250 VCA resistivo según la hoja; bobina 24 V 16.7 mA), contacto NA seco por canal
  con su propio común (bornera KF128 de 2 polos por canal). Límite de producto por canal: POR DETERMINAR (meta 10 A).
- Bobinas por ULN2003A (7 canales, diodos de las bobinas a COM = 24 V) desde un TCA9554 (0x20).
- Mando manual por hardware: DIP de 8 posiciones; la 1-7 une el lado bajo de la bobina a 0 V (relé encendido aunque el
  microcontrolador esté detenido); la 8 = "Wi-Fi apagado" (la lee el programa). LED de bobina en paralelo: indica tensión
  en la bobina venga de donde venga. Divisor 100k/15k por bobina a un TCA9554 (0x22): el programa sabe si la bobina
  está energizada (incluido el forzado manual). NO detecta un contacto soldado.
- 8 entradas de 24 V optoaisladas (LTV-217-B), tipo 1/3 de IEC 61131-2 como meta de diseño: 2 x 2.2k + LED + 2.2k en
  paralelo al LED del opto; diodo en antiparalelo contra polaridad invertida; común de entradas propio (COMI).
- 7 botones de canal (TCA9554 0x23), MODO y RESET; LED RUN, FALLA y COM.
- RS-485 aislado CA-IS3092W (5 kVrms, fuente aislada integrada; SEL a GNDB = 3.3 V del lado del bus), SM712,
  terminación de 120 ohm y polarización por puente. Bornera A, B, GNDB. Todo el lado del bus va trazado a mano
  dentro de la zona GNDB; al rutear, una zona prohibida de 1.6 mm deja la lógica fuera (regla del DRC: 1.5 mm).
- 24 V: fusible 3 A, diodo serie, supresor SMBJ33A; LMR16006 (60 V) a 5 V; AP63203 a 3.3 V. USB-C para programar
  (sin 24 V las bobinas no tienen alimentación).
- Aislamiento: la red (contactos y fuente) solo arriba de y = 32 mm; sin relleno de cobre allí; regla del DRC de 6.4 mm en
  el aire y 6.4 mm por la superficie entre la red y lo demás; 2.0 mm en el aire y 2.4 mm por la superficie entre redes de red distintas
  (2.48 mm entre las dos patas de una bornera de 5.08 mm: el contacto abierto).

    bash ../../tools/rutear.sh ap-electric/7r-tour AP_7R_TOUR
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
import placa  # noqa: E402
import conectores  # noqa: E402

PROJECT = "AP_7R_TOUR"
NS = uuid.UUID("7a1e9c3b-5d2f-4b8a-9e6c-1f3a5b7d9e20")
ROOT_UUID = "3c5e7a9b-1d2f-4a6c-8e0b-2d4f6a8c0e71"
R06, R08, R12 = "Resistor_SMD:R_0603_1608Metric", "Resistor_SMD:R_0805_2012Metric", "Resistor_SMD:R_1206_3216Metric"
C06, C08, C12 = "Capacitor_SMD:C_0603_1608Metric", "Capacitor_SMD:C_0805_2012Metric", "Capacitor_SMD:C_1206_3216Metric"
R, C = "Device:R", "Device:C"
LED06 = "LED_SMD:LED_0603_1608Metric"
SMA, SMB = "Diode_SMD:D_SMA", "Diode_SMD:D_SMB"
TSSOP = "Package_SO:TSSOP-16_4.4x5mm_P0.65mm"
BTN = "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A"
KF2 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal"
KF3 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3-5.08_1x03_P5.08mm_Horizontal"
SJO = "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm"
SJB = "Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm"
XC = [14.0 + 17.0 * k for k in range(7)]          # eje de cada canal
YB = 44.0                                         # patas de la bobina; contactos 13 en y = 24, 14 en y = 19
XI = [5.0 + 5.9 * k for k in range(8)]            # columnas de las entradas


def tca(ref, a, pines, func):
    """TCA9554: a = (A0, A1, A2) en '3V3'/'GND'; pines = 8 redes P0-P7 (None = sin conectar)."""
    p = {"1": a[0], "2": a[1], "3": a[2], "8": "GND", "13": None, "14": "SCL", "15": "SDA", "16": "3V3"}
    for num, red in zip(("4", "5", "6", "7", "9", "10", "11", "12"), pines):
        p[num] = red
    return (ref, "TCA9554PWR", "Interface_Expansion:TCA9554PW", TSSOP, p, func)


C_ = [
    # --- 24 V y fuentes ---
    ("J9", "KF128-5.08-2P", "Connector:Screw_Terminal_01x02", KF2, {"1": "VIN_RAW", "2": "GND"},
     "Alimentación 24 V CC (fuente certificada externa): 1 = +24 V, 2 = 0 V"),
    ("F1", "3A", "Device:Fuse", "Fuse:Fuse_1206_3216Metric", {"1": "VIN_RAW", "2": "VF"}, "Fusible rápido de la placa"),
    ("D2", "SMBJ33A", "Device:D_TVS", SMB, {"1": "VF", "2": "GND"}, "Supresor de picos (33 V de trabajo)"),
    ("D1", "SS34", "Device:D_Schottky", SMA, {"1": "V24", "2": "VF"}, "Polaridad invertida (en serie)"),
    ("C1", "10uF 50V", C, C12, {"1": "V24", "2": "GND"}, "Reserva de 24 V"),
    ("C2", "10uF 50V", C, C12, {"1": "V24", "2": "GND"}, "Reserva de 24 V"),
    ("U7", "LMR16006XDDC", "Regulator_Switching:LMR16006YQ", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "BST", "2": "GND", "3": "FB", "4": "V24", "5": "V24", "6": "SW"}, "Buck 60 V a 5 V"),
    ("L1", "47uH", "Device:L", "Inductor_SMD:L_Changjiang_FNR4030S", {"1": "V5", "2": "SW"}, "Bobina del buck de 5 V"),
    ("D6", "SS210", "Device:D_Schottky", SMA, {"1": "SW", "2": "GND"}, "Rueda libre del buck"),
    ("C10", "100nF", C, C06, {"1": "BST", "2": "SW"}, "Bootstrap"),
    ("C11", "10uF 50V", C, C12, {"1": "V24", "2": "GND"}, "Entrada del buck"),
    ("C12", "22uF 25V", C, C12, {"1": "V5", "2": "GND"}, "Salida 5 V"),
    ("RB1", "56k", R, R06, {"1": "V5", "2": "FB"}, "Divisor: 0.765 V x 6.6 = 5.05 V"),
    ("RB2", "10k", R, R06, {"1": "FB", "2": "GND"}, "Divisor"),
    ("D7", "B5819W", "Device:D_Schottky", "Diode_SMD:D_SOD-123", {"1": "V5", "2": "VBUS"}, "5 V del USB (programar)"),
    ("U8", "AP63203WU", "Regulator_Switching:AP63203WU", "Package_TO_SOT_SMD:TSOT-23-6",
     {"1": "3V3", "2": "V5", "3": "V5", "4": "GND", "5": "SWP", "6": "BSTP"}, "Buck 3.3 V (síncrono)"),
    ("L2", "4.7uH", "Device:L", "Inductor_SMD:L_Changjiang_FNR4030S", {"1": "SWP", "2": "3V3"}, "Bobina 3.3 V"),
    ("C13", "100nF", C, C06, {"1": "BSTP", "2": "SWP"}, "Bootstrap"),
    ("C14", "10uF 50V", C, C12, {"1": "V5", "2": "GND"}, "Entrada del buck de 3.3 V"),
    ("C15", "22uF", C, C08, {"1": "3V3", "2": "GND"}, "Salida 3.3 V"),
    ("C16", "22uF", C, C08, {"1": "3V3", "2": "GND"}, "Salida 3.3 V"),
    # --- SKU 7R Tour CA: fuente de red en la placa (en 7R Tour 24DC no se monta) ---
    ("J8", "KF128-5.08-2P", "Connector:Screw_Terminal_01x02", KF2, {"1": "N", "2": "L"},
     "Solo 7R Tour CA: red 85-264 VCA. 1 = N, 2 = L (fase)"),
    ("F2", "T2A 250VCA", "Device:Fuse", "LetreroLab:Fuse_2410_6125Metric", {"1": "L", "2": "LF"},
     "Solo CA: fusible de retardo 2 A de la fuente"),
    ("RV1", "10D471K", "Device:Varistor", "Varistor:RV_Disc_D12mm_W5mm_P7.5mm", {"1": "LF", "2": "N"},
     "Solo CA: varistor de la entrada de la fuente"),
    ("PS1", "IRM-20-24", "Converter_ACDC:IRM-20-24", "Converter_ACDC:Converter_ACDC_MeanWell_IRM-20-xx_THT",
     {"1": "LF", "2": "N", "3": "GND", "4": "VIRM"}, "Solo CA: Mean Well 24 V 0.9 A, aislada y certificada"),
    ("D3", "SS34", "Device:D_Schottky", SMA, {"1": "V24", "2": "VIRM"}, "Solo CA: une la fuente interna al 24 V"),
    ("C3", "10uF 50V", C, C12, {"1": "VIRM", "2": "GND"}, "Solo CA: salida de la fuente"),
    # --- cerebro ---
    ("U9", "ESP32-C3-WROOM-02", "RF_Module:ESP32-C3-WROOM-02", "LetreroLab:ESP32-C3-WROOM-02_JLC",
     {"1": "3V3", "2": "EN", "3": "INT", "4": "LRUN", "5": "LFAL", "6": "LCOM", "7": "SCL", "8": "BOOT",
      "9": "GND", "10": "RS_DE", "11": "E2", "12": None, "13": "USB_DN", "14": "USB_DP", "15": "RS_RX",
      "16": "SDA", "17": "RS_TX", "18": "E1", "19": "GND"},
     "Wi-Fi opcional; IO2/IO8 = I2C, IO1/IO3/IO10 = RS-485, IO4 = interrupción de entradas y botones; IO0 e IO20 = conteo rápido de las entradas 1 y 2"),
    ("C17", "10uF", C, C08, {"1": "3V3", "2": "GND"}, "Desacoplo del módulo"),
    ("C18", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo del módulo"),
    ("R1", "10k", R, R06, {"1": "3V3", "2": "EN"}, "Pull-up EN"),
    ("C19", "1uF", C, C06, {"1": "EN", "2": "GND"}, "Arranque retardado"),
    ("R2", "10k", R, R06, {"1": "3V3", "2": "BOOT"}, "Pull-up IO9"),
    ("SW8", "MODO", "Switch:SW_Push", BTN, {"1": "BOOT", "2": "GND"}, "MODO; mantenido al conectar el USB = programar"),
    ("SW9", "RESET", "Switch:SW_Push", BTN, {"1": "EN", "2": "GND"}, "Reinicio"),
    ("R3", "4.7k", R, R06, {"1": "3V3", "2": "SDA"}, "Pull-up I2C"),
    ("R4", "4.7k", R, R06, {"1": "3V3", "2": "SCL"}, "Pull-up I2C"),
    ("R5", "10k", R, R06, {"1": "3V3", "2": "INT"}, "Pull-up de la interrupción (U3, U5)"),
    ("R6", "1k", R, R06, {"1": "LRUN", "2": "LRA"}, "LED RUN"),
    ("D8", "VERDE", "Device:LED", LED06, {"1": "GND", "2": "LRA"}, "RUN"),
    ("R7", "1k", R, R06, {"1": "LFAL", "2": "LFA"}, "LED FALLA"),
    ("D9", "ROJO", "Device:LED", LED06, {"1": "GND", "2": "LFA"}, "FALLA"),
    ("R8", "1k", R, R06, {"1": "LCOM", "2": "LCA"}, "LED COM"),
    ("D10", "AMARILLO", "Device:LED", LED06, {"1": "GND", "2": "LCA"}, "Actividad del RS-485"),
    # --- USB-C (programar y probar) ---
    ("J15", "USB-C", "Connector:USB_C_Receptacle_USB2.0_16P", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
     {"A1": "GND", "A4": "VBUS", "A5": "CC1U", "A6": "USB_DP", "A7": "USB_DN", "A8": None, "A9": "VBUS",
      "B1": "GND", "B4": "VBUS", "B5": "CC2U", "B6": "USB_DP", "B7": "USB_DN", "B8": None, "B9": "VBUS",
      "S1": "GND", "A12": "GND", "B12": "GND"}, "USB-C: programar y probar"),
    ("R9", "5.1k", R, R06, {"1": "CC1U", "2": "GND"}, "CC1"),
    ("R10", "5.1k", R, R06, {"1": "CC2U", "2": "GND"}, "CC2"),
    ("U10", "USBLC6-2SC6", "Power_Protection:USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "USB_DN", "2": "GND", "3": "USB_DP", "4": "USB_DP", "5": "VBUS", "6": "USB_DN"}, "ESD del USB"),
    # --- rev B: reloj de tiempo real con batería externa (hora de cada evento sin red) ---
    ("U11", "PCF8563T/5,518", "Timer_RTC:PCF8563T", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": "OSCI", "2": "OSCO", "3": None, "4": "GND", "5": "SDA", "6": "SCL", "7": None, "8": "VRTC"},
     "Reloj de tiempo real I2C 0x51; INT y CLKO sin usar"),
    ("Y1", "32.768kHz 12.5pF", "Device:Crystal", "Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm", {"1": "OSCI", "2": "OSCO"},
     "Cristal del reloj (la hoja del PCF8563 admite 7-12.5 pF; sin capacitores externos)"),
    ("D12", "BAT54C", "Diode:BAT54C", "Package_TO_SOT_SMD:SOT-23", {"1": "3V3", "2": "VBAT", "3": "VRTC"},
     "OR de 3.3 V y batería para el reloj (fuga baja)"),
    ("C28", "100nF", C, C06, {"1": "VRTC", "2": "GND"}, "Desacoplo del reloj"),
    ("J16", "BAT", "Connector_Generic:Conn_01x02", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
     {"1": "VBAT", "2": "GND"}, "Batería de respaldo externa 3 V (CR1220/CR2032 con cable): 1 = +, 2 = -. Sin batería el reloj pierde la hora al apagar"),
    # --- salidas ---
    tca("U2", ("GND", "GND", "GND"), ["DO1", "DO2", "DO3", "DO4", "DO5", "DO6", "DO7", "ID"],
        "0x20: P0-P6 = bobinas 1-7; P7 = identificación (0 = 7R Tour)"),
    ("C20", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U2"),
    ("R11", "10k", R, R06, {"1": "ID", "2": "GND"}, "Identificación de placa"),
    ("U1", "ULN2003ADR", "Transistor_Array:ULN2003", "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
     dict({str(k): "DO%d" % k for k in range(1, 8)}, **{"8": "GND", "9": "V24"},
          **{str(17 - k): "BOB%d" % k for k in range(1, 8)}),
     "Excita las 7 bobinas; COM a 24 V = diodo de cada bobina"),
    tca("U4", ("GND", "3V3", "GND"), ["SEN%d" % k for k in range(1, 8)] + ["WIFIOFF"],
        "0x22: P0-P6 = bobina energizada (divisor); P7 = DIP 8 Wi-Fi apagado"),
    ("C21", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U4"),
    ("SW1", "DSWB08LHGET", "Switch:SW_DIP_x08", "Button_Switch_THT:SW_DIP_SPSTx08_Slide_9.78x22.5mm_W7.62mm_P2.54mm",
     dict({str(k): "BOB%d" % k for k in range(1, 8)}, **{"8": "WIFIOFF"}, **{str(k): "GND" for k in range(9, 17)}),
     "Mando manual por hardware: 1-7 = forzar relé encendido; 8 = Wi-Fi apagado"),
    tca("U5", ("3V3", "3V3", "GND"), ["BT%d" % k for k in range(1, 8)] + [None],
        "0x23: P0-P6 = botones de canal"),
    ("C22", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U5"),
    # --- entradas ---
    tca("U3", ("3V3", "GND", "GND"), ["E%d" % k for k in range(1, 9)], "0x21: P0-P7 = entradas 1-8 (0 = activa)"),
    ("C23", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo U3"),
    ("J11", "KF128-5.08-3P", "Connector:Screw_Terminal_01x03", KF3, {"1": "IN1", "2": "IN2", "3": "IN3"}, "Entradas 1-3"),
    ("J12", "KF128-5.08-3P", "Connector:Screw_Terminal_01x03", KF3, {"1": "IN4", "2": "IN5", "3": "IN6"}, "Entradas 4-6"),
    ("J13", "KF128-5.08-3P", "Connector:Screw_Terminal_01x03", KF3, {"1": "IN7", "2": "IN8", "3": "COMI"},
     "Entradas 7-8 y común de entradas (0 V del sensor)"),
    # --- RS-485 aislado ---
    ("U6", "CA-IS3092W", "Interface_UART:ISO3082DW", "Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm",
     {"1": "3V3", "2": "GND", "3": "RS_RX", "4": "RS_DE", "5": "RS_DE", "6": "RS_TX", "7": "GND", "8": "GND",
      "9": "GNDB", "10": "GNDB", "11": None, "12": "RSA", "13": "RSB", "14": None, "15": "GNDB", "16": "VISO"},
     "RS-485 aislado 5 kVrms con fuente aislada integrada; 10 = SEL a GNDB (VISO = 3.3 V); 16 = VISO"),
    ("C24", "10uF", C, C08, {"1": "3V3", "2": "GND"}, "VCC del lado lógico"),
    ("C25", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "VCC del lado lógico"),
    ("C26", "10uF", C, C08, {"1": "VISO", "2": "GNDB"}, "VISO del lado del bus"),
    ("C27", "100nF", C, C06, {"1": "VISO", "2": "GNDB"}, "VISO del lado del bus"),
    ("R12", "10k", R, R06, {"1": "RS_DE", "2": "GND"}, "Recibir al arrancar"),
    ("D11", "SM712", "Diode:SM712_SOT23", "Package_TO_SOT_SMD:SOT-23", {"1": "RSA", "2": "RSB", "3": "GNDB"},
     "Protección de la línea"),
    ("R13", "120", R, R12, {"1": "RSA", "2": "TERM"}, "Terminación"),
    ("JP1", "120R", "Jumper:SolderJumper_2_Open", SJO, {"1": "TERM", "2": "RSB"}, "Cerrar en los extremos de la línea"),
    ("R14", "680", R, R06, {"1": "PA", "2": "RSA"}, "Polarización A"),
    ("R15", "680", R, R06, {"1": "RSB", "2": "PB"}, "Polarización B"),
    ("JP2", "POL A", "Jumper:SolderJumper_2_Bridged", SJB, {"1": "VISO", "2": "PA"}, "Polarización (cortar si ya hay)"),
    ("JP3", "POL B", "Jumper:SolderJumper_2_Bridged", SJB, {"1": "PB", "2": "GNDB"}, "Polarización (cortar si ya hay)"),
    ("J14", "KF128-5.08-3P", "Connector:Screw_Terminal_01x03", KF3, {"1": "RSA", "2": "RSB", "3": "GNDB"},
     "AP LINK / Modbus RTU: 1 = A (+), 2 = B (-), 3 = 0 V aislado (malla)"),
]
for k in range(1, 8):
    C_ += [
        ("K%d" % k, "G2RL-1A-E DC24", "Relay:Relay_SPST-NO", "Relay_THT:Relay_SPST_Omron_G2RL-1A-E",
         {"A1": "V24", "A2": "BOB%d" % k, "13": "C%d" % k, "14": "N%d" % k},
         "Canal %d: Omron G2RL-1A-E 24 V (16 A 250 VCA resistivo, hoja del fabricante)" % k),
        ("J%d" % k, "KF128-5.08-2P", "Connector:Screw_Terminal_01x02", KF2, {"1": "C%d" % k, "2": "N%d" % k},
         "Canal %d: 1 = común (llega la fase), 2 = NA (sale a la carga)" % k),
        ("RL%d" % k, "10k", R, R06, {"1": "V24", "2": "LA%d" % k}, "LED de bobina %d (2.2 mA)" % k),
        ("RD%d" % k, "10k", R, R06, {"1": "DO%d" % k, "2": "GND"},
         "Pull-down de la entrada %d del ULN2003A: el TCA9554 arranca con 100 kΩ a 3.3 V y sin esto el relé podría excitarse hasta que el programa lo configure" % k),
        ("LD%d" % k, "VERDE", "Device:LED", LED06, {"1": "BOB%d" % k, "2": "LA%d" % k}, "Bobina %d con tensión" % k),
        ("RSA%d" % k, "100k", R, R06, {"1": "BOB%d" % k, "2": "SEN%d" % k}, "Divisor de la bobina %d" % k),
        ("RSB%d" % k, "15k", R, R06, {"1": "SEN%d" % k, "2": "GND"}, "Divisor: 24 V -> 3.1 V"),
        ("SB%d" % k, "CANAL %d" % k, "Switch:SW_Push", BTN, {"1": "BT%d" % k, "2": "GND"},
         "Botón del canal %d (mando por programa)" % k),
    ]
for k in range(1, 9):
    C_ += [
        ("RA%d" % k, "2.2k", R, R08, {"1": "IN%d" % k, "2": "IA%d" % k}, "Entrada %d (1 de 2)" % k),
        ("RB%d" % (k + 2), "2.2k", R, R08, {"1": "IA%d" % k, "2": "IB%d" % k}, "Entrada %d (2 de 2)" % k),
        ("LI%d" % k, "VERDE", "Device:LED", LED06, {"1": "IL%d" % k, "2": "IB%d" % k}, "Entrada %d activa" % k),
        ("RS%d" % k, "2.2k", R, R06, {"1": "IL%d" % k, "2": "COMI"}, "Umbral: apagada por debajo de ~5 V"),
        ("DI%d" % k, "1N4148W", "Device:D", "Diode_SMD:D_SOD-123", {"1": "IB%d" % k, "2": "COMI"},
         "Entrada %d: protección contra polaridad invertida" % k),
        ("OK%d" % k, "LTV-217-B", "Isolator:PC817", "Package_SO:SOP-4_4.4x2.6mm_P1.27mm",
         {"1": "IL%d" % k, "2": "COMI", "3": "GND", "4": "E%d" % k}, "Optoacoplador de la entrada %d" % k),
        ("RP%d" % k, "10k", R, R06, {"1": "3V3", "2": "E%d" % k}, "Pull-up de la entrada %d" % k),
    ]

# --- puntos de prueba para la puesta en marcha (no entran al BOM ni al CPL) ---
TP = "TestPoint:TestPoint_Pad_D1.5mm"
TPS = [("TP1", "V24", 105.5, 70.0, "24V"), ("TP2", "V5", 121.0, 72.5, "5V"), ("TP3", "3V3", 140.0, 56.0, "3V3"),
       ("TP4", "GND", 101.5, 68.5, "GND"), ("TP5", "GND", 136.5, 58.0, "GND"), ("TP6", "SDA", 70.0, 63.0, "SDA"),
       ("TP7", "SCL", 58.5, 72.0, "SCL"), ("TP8", "RS_TX", 87.5, 55.0, "TX"), ("TP9", "RS_RX", 87.5, 51.0, "RX"),
       ("TP10", "RS_DE", 91.5, 55.0, "DE"), ("TP11", "EN", 136.5, 65.0, "EN")]
for ref, red, x, y, txt in TPS:
    C_.append((ref, "TP " + txt, "Connector:TestPoint", TP, {"1": red}, "Punto de prueba %s" % txt))

W, H = 176.0, 90.0
RADIO_ESQUINA = 2.0
HOLES = [(3.5, 38.0), (128.0, 38.0), (61.5, 86.5), (145.2, 86.4)]
POS = {
    # 24 V: bornera abajo, protecciones encima
    "J9": (93.0, 83.5, 0), "F1": (93.0, 74.5, 90), "D2": (97.5, 73.5, 90), "D1": (102.0, 74.0, 90),
    "C1": (105.5, 74.0, 90), "C2": (109.0, 74.0, 90),
    # 5 V (LMR16006)
    "U7": (114.0, 84.0, 0), "L1": (120.0, 84.0, 0), "D6": (114.0, 78.5, 0), "C10": (110.5, 84.0, 90),
    "C11": (108.0, 79.5, 90), "C12": (124.5, 84.0, 90), "RB1": (117.0, 88.6, 0), "RB2": (111.5, 88.6, 0),
    "D7": (127.5, 79.0, 90),
    # 3.3 V (AP63203)
    "U8": (132.5, 72.0, 0), "L2": (132.5, 66.0, 0), "C13": (129.2, 74.8, 90), "C14": (136.5, 72.5, 90),
    "C15": (135.0, 61.5, 90), "C16": (137.1, 61.5, 90),
    # SKU CA (red)
    "J8": (137.0, 7.0, 180), "F2": (132.0, 17.5, 270), "RV1": (137.5, 23.0, 90),
    "PS1": (168.0, 6.0, 270), "D3": (155.2, 58.0, 0), "C3": (148.5, 58.0, 0),
    # cerebro
    "U9": (156.0, 75.0, 270), "C17": (147.0, 66.0, 90), "C18": (147.0, 70.0, 90),
    "R1": (145.5, 74.0, 90), "C19": (147.5, 74.0, 90), "R2": (145.5, 78.0, 90),
    "SW8": (142.0, 60.5, 0), "SW9": (142.0, 67.0, 0),
    "R3": (68.0, 66.5, 90), "R4": (70.0, 66.5, 90), "R5": (68.0, 70.5, 90),
    "R6": (122.5, 50.2, 90), "D8": (122.5, 53.8, 90), "R7": (125.5, 50.2, 90), "D9": (125.5, 53.8, 90),
    "R8": (128.5, 50.2, 90), "D10": (128.5, 53.8, 90),
    "J15": (136.0, 85.5, 0), "R9": (127.5, 84.5, 90), "R10": (127.5, 88.0, 90), "U10": (136.0, 77.3, 0),
    # salidas
    "U1": (63.0, 60.5, 90), "U2": (63.0, 68.5, 90), "C20": (59.0, 68.5, 90), "R11": (67.0, 74.5, 90),
    "RD1": (55.2, 74.3, 0), "RD2": (58.6, 74.3, 0), "RD3": (62.0, 74.3, 0),
    "RD4": (52.0, 76.2, 0), "RD5": (55.4, 76.2, 0), "RD6": (58.8, 76.2, 0), "RD7": (62.2, 76.2, 0),
    "SW1": (89.5, 65.5, 90),
    "U4": (116.0, 60.0, 0), "C21": (121.5, 60.0, 90), "U5": (127.0, 60.0, 0), "C22": (132.5, 59.0, 90),
    # entradas
    "U3": (54.5, 61.5, 90), "C23": (54.5, 67.5, 90),
    "J11": (6.0, 83.5, 0), "J12": (22.4, 83.5, 0), "J13": (38.8, 83.5, 0),
    # RS-485 aislado
    "U6": (79.0, 64.5, 270), "C24": (75.5, 57.3, 0), "C25": (79.5, 57.3, 0), "R12": (83.0, 57.3, 0),
    # lado del bus en dos filas encadenadas, VISO-JP2-PA-R14-RSA-R13-TERM-JP1-RSB-R15-PB-JP3-GNDB; trazado a mano (PRE)
    "D11": (77.3, 72.4, 0), "C27": (82.6, 72.0, 180), "C26": (85.9, 72.0, 180), "JP2": (89.3, 72.0, 0),
    "R13": (72.9, 75.6, 0), "JP1": (76.95, 75.6, 0), "R15": (80.2, 75.6, 0), "JP3": (83.48, 75.6, 0),
    "R14": (86.75, 75.6, 180), "J14": (74.0, 83.5, 0),
}
for k, xc in enumerate(XC, start=1):
    POS.update({
        "K%d" % k: (xc + 3.75, YB, 180), "J%d" % k: (xc + 2.54, 7.0, 180),
        "RL%d" % k: (xc - 2.0, 48.3, 0), "LD%d" % k: (xc + 1.6, 48.3, 0),
        "SB%d" % k: (xc, 52.6, 0),
    })
for k in range(1, 8):                              # divisores de las bobinas, en fila junto a U4
    POS["RSA%d" % k] = (112.5 + 2.6 * (k - 1), 65.5, 90)
    POS["RSB%d" % k] = (112.5 + 2.6 * (k - 1), 69.0, 90)
for k, xi in enumerate(XI, start=1):
    POS.update({
        "RP%d" % k: (xi + 1.0, 57.0, 90), "OK%d" % k: (xi + 1.0, 63.2, 90),
        "LI%d" % k: (xi, 69.3, 90), "RS%d" % k: (xi + 2.7, 69.3, 90),
        "RB%d" % (k + 2): (xi, 73.0, 90), "DI%d" % k: (xi + 2.7, 73.25, 90), "RA%d" % k: (xi + 0.6, 76.7, 0),
    })

# rev B: reloj con batería (zona libre a la derecha de K7) y puntos de prueba
POS.update({"U11": (139.0, 49.5, 0), "Y1": (135.2, 44.5, 0), "D12": (132.0, 54.5, 0), "C28": (140.8, 44.8, 0),
            "J16": (131.5, 47.5, 0)})
for _ref, _red, _x, _y, _t in TPS:
    POS[_ref] = (_x, _y, 0)

RED_NETS = ["C%d" % k for k in range(1, 8)] + ["N%d" % k for k in range(1, 8)] + ["L", "N", "LF"]
NETCLASS = {
    "Red": (2.0, 2.0, RED_NETS),
    "Media": (0.6, 0.25, ["VIN_RAW", "VF", "V24", "VIRM", "SW", "V5"]),
    "Bus": (0.3, 0.25, ["RSA", "RSB", "GNDB", "VISO", "TERM", "PA", "PB"]),
}
# --- red: trazada a mano en las dos caras; toda arriba de y = 26 mm ---
PRE = []
for k, xc in enumerate(XC, start=1):
    for capa in ("F", "B"):
        PRE += [
            ("N%d" % k, 2.0, [(xc - 3.75, 19.0), (xc + 3.75, 19.0)], capa),
            ("N%d" % k, 2.0, [(xc - 3.75, 19.0), (xc - 3.75, 10.5), (xc - 2.54, 9.0), (xc - 2.54, 7.0)], capa),
            ("C%d" % k, 2.0, [(xc - 3.75, 24.0), (xc + 8.4, 24.0), (xc + 8.4, 10.5), (xc + 5.0, 7.0), (xc + 2.54, 7.0)], capa),
        ]
PRE += [   # solo SKU CA: entrada de red a la fuente
    ("L", 1.0, [(131.92, 7.0), (132.0, 9.0), (132.0, 14.7)]),
    ("LF", 1.0, [(132.0, 20.3), (132.0, 23.0), (168.0, 23.0), (168.0, 6.0)]),
    ("N", 1.0, [(137.0, 7.0), (139.7, 9.7), (139.7, 15.5)]),
    ("N", 1.0, [(137.0, 7.0), (145.7, 7.0), (147.2, 6.0)]),
]
DRU = ('(rule "aislamiento_red" (condition "A.NetClass == \'Red\' && B.NetClass != \'Red\' && B.NetName != \'unconnected-*\'") '
       '(constraint clearance (min 6.4mm)) (constraint creepage (min 6.4mm)))\n'
       '(rule "entre_canales" (condition "A.NetClass == \'Red\' && B.NetClass == \'Red\' && A.NetName != B.NetName") '
       '(constraint clearance (min 2.0mm)) (constraint creepage (min 2.4mm)))\n'
       '(rule "bus_aislado" (condition "A.NetClass == \'Bus\' && B.NetClass != \'Bus\' && B.NetName != \'unconnected-*\'") '
       '(constraint clearance (min 1.5mm)))\n')
SIN_RELLENO = [[(0.3, 0.3), (175.7, 0.3), (175.7, 31.0), (0.3, 31.0)]]
SIN_COBRE = [[(163.0, 61.0), (175.7, 61.0), (175.7, 89.7), (163.0, 89.7)]]       # antena del ESP32
# --- bus RS-485 aislado: todo su cobre dentro de _ZB, trazado a mano; la lógica queda fuera de _ZB + 1.6 mm ---
_ZB = [(70.2, 70.4), (73.9, 70.4), (73.9, 67.8), (84.1, 67.8), (84.1, 70.4), (90.7, 70.4), (90.7, 77.6), (88.5, 77.6),
       (88.5, 89.7), (70.2, 89.7)]
# redes largas que el ruteador automático deja sin unir (de un punto de cobre al otro; capa F o B; el destino es un pad del ESP32; la poda quita las ramas sin salida que deja el ruteador)
RUTAS_AUTO = [("INT", (68.0, 69.675, "F"), (159.0, 66.25, "F")),
              ("RS_DE", (91.5, 55.0, "F"), (150.0, 83.75, "F")),
              ("RS_RX", (87.5, 51.0, "F"), (157.5, 83.75, "F"))]
ZONAS_FINALES = [("GNDB", _ZB), ("GNDB", _ZB, "B")]


def _agrandar(pts, d):
    """Polígono de lados horizontales y verticales agrandado d mm hacia afuera."""
    n = len(pts)
    s = 1 if sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n)) > 0 else -1
    def normal(a, c):
        dx, dy = c[0] - a[0], c[1] - a[1]; L = (dx * dx + dy * dy) ** 0.5
        return (s * dy / L, -s * dx / L)
    out = []
    for i in range(n):
        n1, n2 = normal(pts[i - 1], pts[i]), normal(pts[i], pts[(i + 1) % n])
        out.append((round(pts[i][0] + d * (n1[0] + n2[0]), 3), round(pts[i][1] + d * (n1[1] + n2[1]), 3)))
    return out


RUTEO_PROHIBIDO = [_agrandar(_ZB, 1.6)]
_W = 0.3
PRE += [
    ("RSA", _W, [(78.37, 69.15), (78.37, 70.3), (77.22, 71.45), (76.36, 71.45), (75.0, 71.45)]),
    ("RSA", _W, [(75.0, 71.45), (73.0, 73.45), (73.0, 79.5), (74.0, 80.5), (74.0, 83.5)], "B"),
    ("RSA", _W, [(73.0, 77.3), (71.44, 77.3)], "B"),
    ("RSA", _W, [(71.44, 77.3), (71.44, 75.6)]),
    ("RSA", _W, [(73.0, 79.5), (83.6, 79.5), (85.925, 77.2)], "B"),
    ("RSA", _W, [(85.925, 77.2), (85.925, 75.6)]),
    ("RSB", _W, [(79.63, 69.15), (79.63, 73.9), (77.0, 73.9), (76.36, 73.35)]),
    ("RSB", _W, [(79.63, 73.9), (79.375, 75.6), (79.375, 76.8), (79.08, 77.1), (79.08, 83.5)]),
    ("RSB", _W, [(77.6, 75.6), (79.375, 75.6)]),
    ("TERM", _W, [(74.36, 75.6), (76.3, 75.6)]),
    ("PB", _W, [(81.025, 75.6), (82.83, 75.6)]),
    ("PA", _W, [(89.95, 72.0), (89.95, 74.0), (88.35, 75.6), (87.575, 75.6)]),
    ("VISO", 0.4, [(83.44, 69.15), (83.38, 72.0)]),
    ("VISO", 0.4, [(83.44, 70.6), (86.85, 70.6), (86.85, 72.0), (88.65, 72.0)]),
    ("GNDB", 0.4, [(82.18, 69.15), (81.82, 72.0)]),
]
PREVIAS = [("RSA", 75.0, 71.45), ("RSA", 71.44, 77.3), ("RSA", 85.925, 77.2),
           ("GNDB", 74.0, 71.0), ("GNDB", 81.82, 73.4), ("GNDB", 85.25, 73.5)]
SILK = [("CANAL %d" % k, xc, 30.0, 1.0, "F") for k, xc in enumerate(XC, 1)] + \
       [("NA%d   C%d" % (k, k), xc, 14.5, 0.9, "F") for k, xc in enumerate(XC, 1)] + [
    ("PELIGRO: contactos y fuente a tension de red", 60.0, 27.5, 1.0, "F"),
    ("N    L   (solo 7R Tour CA)", 134.0, 14.5, 0.8, "F"),
    ("I1   I2   I3   I4   I5   I6   I7   I8   COM", 27.0, 89.3, 0.8, "F"),
    ("+24V   0V", 95.5, 89.3, 0.8, "F"), ("A    B    0V aisl.", 79.0, 89.3, 0.8, "F"),
    ("DIP 1-7: forzar rele   8: Wi-Fi apagado", 98.5, 55.8, 0.8, "F"),
    ("BAT + / -", 128.5, 52.6, 0.8, "F"),
    ("AP ELECTRIC INDUSTRIAL  7R TOUR  rev B", 60.0, 36.5, 1.4, "F"),
    ("AP Electric Industrial 7R Tour rev B - CONCEPTO, sin certificar. Desconectar la red antes de abrir.", 88.0, 88.5, 0.9, "B"),
]
FLAGS = [("VRTC", 172.72, 20.32), ("VIN_RAW", 20.32, 20.32), ("V24", 50.8, 20.32), ("3V3", 66.04, 20.32), ("VF", 35.56, 30.48),
         ("V5", 81.28, 20.32), ("VISO", 96.52, 20.32), ("GNDB", 111.76, 20.32), ("COMI", 127.0, 20.32),
         ("LF", 142.24, 20.32), ("N", 157.48, 20.32)]
NOTES = [(150.0, 15.0, "AP Electric Industrial · 7R Tour rev B (CONCEPTO): 7 x G2RL-1A-E 24 V, ULN2003A, 4 x TCA9554 (0x20-0x23),\n"
                       "8 entradas 24 V LTV-217, CA-IS3092W RS-485 aislado, ESP32-C3. SKU CA: IRM-20-24 + T2A + 10D471K.\n"
                       "Rev B: conteo rápido en IO0/IO20 (entradas 1 y 2), reloj PCF8563T con batería externa, 11 puntos de prueba.")]
TITLE = "AP Electric Industrial · 7R Tour rev B - 7 relés, 8 entradas, Modbus aislado (CONCEPTO)"
SUBTITLES = ["Placa de 2 capas, 2 oz (JLCPCB)", "Estado: concepto. Límites del producto por determinar por ensayo"]
COMPANY = "PCB 176 x 90 mm, 2 capas, 2 oz"
OCULTAR_REF = tuple(["RL%d" % k for k in range(1, 8)] + ["RD%d" % k for k in range(1, 8)] + ["RSA%d" % k for k in range(1, 8)] + ["RSB%d" % k for k in range(1, 8)])

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
