"""LetreroLab AP-1 PROGRAMADOR: el cerebro que se enclava sobre la BASE universal (conector 2x8 + 1 tornillo).

- ESP32-C3-WROOM-02 (Wi-Fi + BLE certificado), antena sobre la zona sin cobre de la base.
- USB-C: programar, probar sin base y alimentar en el taller; protección ESD.
- Fuente conmutada AP63203 (3.3 V) desde los 12 V de la base o desde el USB (diodos en OR).
- Botones MODO/BOOT y RESET, LED de estado (verde) y LED de FALLA por hardware (rojo, sigue a la línea ALERTA).
- Receptor IR TSOP382 y conector J4 para ojo IR y botón externos; conector Qwiic (I2C) para pantalla OLED,
  sensor de luz o reloj, sin soldar.
- Pull-down en los 4 PWM: las salidas de 8 A no se encienden mientras arranca el ESP32.

Coordenadas: el programador ocupa la zona x 36-88, y 0-42 de la base (mismo sistema menos 36 en x).
"""
import os, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import placa  # noqa: E402

PROJECT = "AP1_Programador"
NS = uuid.UUID("7c2d4e61-8f9a-4b0c-9d1e-2f3a4b5c6d72")
ROOT_UUID = "c2d3e4f5-a6b7-4c8d-9e0f-1a2b3c4d5e6f"
R06, C06, C08, C12 = ("Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric",
                      "Capacitor_SMD:C_0805_2012Metric", "Capacitor_SMD:C_1206_3216Metric")
R, C = "Device:R", "Device:C"
ESP = {"1": "3V3", "2": "EN", "3": "PWM1", "4": "PWM2", "5": "PWM3", "6": "PWM4", "7": "SCL", "8": "BOOT",
       "9": "GND", "10": "CC1", "11": "ALERT", "12": "LEDV", "13": "USB_DN", "14": "USB_DP", "15": "IR", "16": "SDA",
       "17": "AUX", "18": "CC2", "19": "GND"}
C_ = [
    ("U1", "ESP32-C3-WROOM-02", "RF_Module:ESP32-C3-WROOM-02", "RF_Module:ESP32-C3-WROOM-02", ESP,
     "Wi-Fi + Bluetooth LE (módulo certificado). IO21 = LED verde: su registro de arranque solo hace parpadear el LED"),
    ("C1", "10uF", C, C08, {"1": "3V3", "2": "GND"}, "Desacoplo del módulo"),
    ("C2", "100nF", C, C06, {"1": "3V3", "2": "GND"}, "Desacoplo del módulo"),
    ("R1", "10k", R, R06, {"1": "3V3", "2": "EN"}, "Pull-up EN"),
    ("C3", "1uF", C, C06, {"1": "EN", "2": "GND"}, "Arranque retardado"),
    ("R2", "10k", R, R06, {"1": "3V3", "2": "BOOT"}, "Pull-up IO9 (arranque normal)"),
    ("SW1", "MODO / BOOT", "Switch:SW_Push", "Button_Switch_SMD:SW_SPST_TL3342", {"1": "BOOT", "2": "GND"},
     "MODO; mantenido al conectar el USB = modo programación"),
    ("SW2", "RESET", "Switch:SW_Push", "Button_Switch_SMD:SW_SPST_TL3342", {"1": "EN", "2": "GND"}, "Reinicio"),
    # USB-C
    ("J2", "USB-C", "Connector:USB_C_Receptacle_USB2.0_16P", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
     {"A1": "GND", "A4": "VBUS", "A5": "CC1U", "A6": "USB_DP", "A7": "USB_DN", "A8": None, "A9": "VBUS",
      "B1": "GND", "B4": "VBUS", "B5": "CC2U", "B6": "USB_DP", "B7": "USB_DN", "B8": None, "B9": "VBUS",
      "S1": "GND", "A12": "GND", "B12": "GND"}, "USB-C: programar y probar"),
    ("R3", "5.1k", R, R06, {"1": "CC1U", "2": "GND"}, "CC1 (dispositivo)"),
    ("R4", "5.1k", R, R06, {"1": "CC2U", "2": "GND"}, "CC2"),
    ("U3", "USBLC6-2SC6", "Power_Protection:USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "USB_DN", "2": "GND", "3": "USB_DP", "4": "USB_DP", "5": "VBUS", "6": "USB_DN"}, "ESD del USB"),
    # fuente 3.3 V
    ("D1", "B5819W", "Device:D_Schottky", "Diode_SMD:D_SOD-123", {"1": "VLOG", "2": "V12"}, "12 V de la base"),
    ("D2", "B5819W", "Device:D_Schottky", "Diode_SMD:D_SOD-123", {"1": "VLOG", "2": "VBUS"}, "5 V del USB"),
    ("U2", "AP63203WU", "Regulator_Switching:AP63203WU", "Package_TO_SOT_SMD:TSOT-23-6",
     {"1": "3V3", "2": "VLOG", "3": "VLOG", "4": "GND", "5": "SWP", "6": "BSTP"}, "Buck 3.3 V 2 A (síncrono)"),
    ("L1", "4.7uH", "Device:L", "Inductor_SMD:L_Changjiang_FNR4030S", {"1": "SWP", "2": "3V3"}, "Bobina 3.3 V"),
    ("C4", "100nF", C, C06, {"1": "BSTP", "2": "SWP"}, "Bootstrap"),
    ("C5", "10uF 25V", C, C12, {"1": "VLOG", "2": "GND"}, "Entrada buck"),
    ("C6", "22uF", C, C08, {"1": "3V3", "2": "GND"}, "Salida 3.3 V"),
    ("C7", "22uF", C, C08, {"1": "3V3", "2": "GND"}, "Salida 3.3 V"),
    # I2C, alerta y LED
    ("R5", "4.7k", R, R06, {"1": "3V3", "2": "SDA"}, "Pull-up I2C (IO2 en alto al arrancar)"),
    ("R6", "4.7k", R, R06, {"1": "3V3", "2": "SCL"}, "Pull-up I2C (IO8 en alto al arrancar)"),
    ("R7", "10k", R, R06, {"1": "3V3", "2": "ALERT"}, "Pull-up de la línea de alerta (INA238 + TMP1075)"),
    ("R8", "1k", R, R06, {"1": "3V3", "2": "LEDRA"}, "LED de falla"),
    ("D3", "ROJO", "Device:LED", "LED_SMD:LED_0603_1608Metric", {"1": "ALERT", "2": "LEDRA"},
     "FALLA: enciende por hardware cuando la base activa ALERTA"),
    ("R9", "1k", R, R06, {"1": "LEDV", "2": "LEDVA"}, "LED de estado"),
    ("D4", "VERDE", "Device:LED", "LED_SMD:LED_0603_1608Metric", {"1": "GND", "2": "LEDVA"}, "Estado"),
    ("R10", "10k", R, R06, {"1": "PWM1", "2": "GND"}, "PWM1 apagado al arrancar"),
    ("R11", "10k", R, R06, {"1": "PWM2", "2": "GND"}, "PWM2 apagado al arrancar"),
    ("R12", "10k", R, R06, {"1": "PWM3", "2": "GND"}, "PWM3 apagado al arrancar"),
    ("R13", "10k", R, R06, {"1": "PWM4", "2": "GND"}, "PWM4 apagado al arrancar"),
    # IR, Qwiic, expansión
    ("U4", "TSOP38238", "Interface_Optical:TSOP382xx", "OptoDevice:Vishay_MINICAST-3Pin",
     {"1": "IR", "2": "GND", "3": "IRV"}, "Receptor IR 38 kHz"),
    ("R14", "100", R, R06, {"1": "3V3", "2": "IRV"}, "Filtro de alimentación del IR (Vishay)"),
    ("C8", "4.7uF", C, C06, {"1": "IRV", "2": "GND"}, "Filtro de alimentación del IR"),
    ("J3", "QWIIC", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal",
     {"1": "GND", "2": "3V3", "3": "SDA", "4": "SCL", "MP": "GND"},
     "I2C Qwiic/STEMMA QT: pantalla OLED SSD1306, sensor de luz, reloj"),
    ("J4", "EXT", "Connector:Conn_01x04_Pin", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
     {"1": "3V3", "2": "GND", "3": "IR", "4": "BOOT"}, "Ojo IR y botón MODO externos (en la tapa de la caja)"),
    # conector a la base (abajo)
    ("J1", "BASE", "Connector_Generic:Conn_02x08_Odd_Even", "Connector_PinHeader_2.54mm:PinHeader_2x08_P2.54mm_Vertical",
     {"1": "V12", "2": "V12", "3": "GND", "4": "GND", "5": "PWM1", "6": "PWM2", "7": "PWM3", "8": "PWM4",
      "9": "CC1", "10": "CC2", "11": "SDA", "12": "SCL", "13": "ALERT", "14": "AUX", "15": "3V3", "16": "GND"},
     "Conector macho hacia la base (lado inferior)"),
    ("TP1", "3V3", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "3V3"}, "Prueba: 3.3 V"),
    ("TP2", "GND", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "GND"}, "Prueba: tierra"),
    ("TP3", "EN", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "EN"}, "Prueba: reinicio"),
    ("TP4", "IO9", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", {"1": "BOOT"}, "Prueba: modo programación"),
]

W, H = 52.0, 42.0
RADIO_ESQUINA = 2.0
HOLES = [(48.5, 39.5)]                    # = agujero (84.5, 39.5) de la base: separador de 11 mm
POS = {
    "J1": (11.0, 6.0, 0, "B"),
    "U1": (33.0, 16.0, 270),
    "J2": (19.5, 4.2, 180), "U3": (19.5, 12.4, 0), "R3": (23.6, 11.6, 90), "R4": (15.4, 11.6, 90),
    "SW1": (19.5, 17.6, 0), "SW2": (19.5, 24.4, 0),
    "R10": (4.0, 11.0, 0), "R11": (4.0, 12.8, 0), "R12": (4.0, 14.6, 0), "R13": (4.0, 16.4, 0),
    "TP1": (3.0, 20.0, 0), "TP2": (3.0, 23.0, 0), "TP3": (3.0, 26.0, 0), "TP4": (3.0, 37.5, 0),
    "C4": (10.0, 28.3, 0), "U2": (10.0, 31.0, 0), "L1": (15.0, 31.2, 0), "C5": (6.0, 31.0, 90),
    "C6": (15.0, 35.6, 0), "C7": (15.0, 38.2, 0), "D1": (8.5, 35.2, 0), "D2": (8.5, 38.2, 0),
    "C1": (21.5, 30.0, 0), "C2": (21.5, 32.4, 0), "R1": (21.5, 34.6, 0), "C3": (21.5, 36.6, 0), "R2": (21.5, 38.6, 0),
    "J4": (27.0, 33.0, 90), "J3": (41.0, 33.65, 180), "U4": (26.5, 37.8, 0), "R14": (34.5, 36.0, 0),
    "C8": (34.5, 37.8, 0), "R5": (38.0, 37.8, 0), "R6": (41.5, 37.8, 0),
    "R8": (34.5, 39.4, 0), "R9": (38.0, 39.4, 0), "R7": (41.5, 39.4, 0),
    "D3": (34.5, 41.0, 0), "D4": (38.0, 41.0, 0),
}
NETCLASS = {"Media": (0.5, 0.2, ["V12", "VLOG", "VBUS", "3V3", "SWP"])}
SILK = [
    ("LetreroLab AP-1", 11.0, 41.0, 1.0, "F"),
    ("MODO", 19.5, 21.2, 0.8, "F"), ("RESET", 19.5, 28.0, 0.8, "F"),
    ("FALLA", 30.6, 41.0, 0.7, "F"), ("OK", 41.5, 41.0, 0.7, "F"),
    ("3V3 GND IR MODO", 30.8, 30.9, 0.6, "F"),
    ("LetreroLab AP-1 PROGRAMADOR", 26.0, 39.0, 1.0, "B"),
    ("Tornillo y separador de NYLON (antena)", 26.0, 36.8, 0.8, "B"),
]
FLAGS = [("V12", 20.32, 20.32), ("GND", 35.56, 20.32), ("VBUS", 50.8, 20.32), ("VLOG", 66.04, 20.32),
         ("3V3", 81.28, 20.32), ("IRV", 96.52, 20.32)]
NOTES = [(150.0, 15.0, "LetreroLab AP-1 PROGRAMADOR. PWM1-4 = IO4-IO7, CC1 = IO10, CC2 = IO0, AUX = IO1, IR = IO3,\n"
                       "SDA/SCL = IO2/IO8, MODO = IO9, ALERTA = IO20, LED verde = IO21, USB = IO18/IO19.")]
TITLE = "LetreroLab AP-1 - programador (ESP32-C3)"
SUBTITLES = ["Se enclava sobre la base universal (2x8 + tornillo)", "Wi-Fi, USB-C, IR, Qwiic, LEDs de estado y falla"]
COMPANY = "PCB 52 x 42 mm, 2 capas"

if __name__ == "__main__":
    if "--cajas" in sys.argv:
        placa.cajas(sys.modules[__name__])
    else:
        placa.main(sys.modules[__name__])
