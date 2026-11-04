# LetreroLab AP-0.1: controlador propio de letreros (2 placas, fuente incluida, app)

Es un sistema completo con diseño, programa y app propios. No depende de tarjetas Arduino, ESP32 ni de la placa Radox: el "cerebro" es un **chip ATmega328P suelto** en nuestra propia placa.

```
              ┌────────── GABINETE CERRADO (tornillos de seguridad + sello de garantía) ──────────┐
127/240 VCA ─►│ PLACA POTENCIA 90×80                                                                │─► LED / tiras 12 V (4 canales)
              │  fusible ► varistor ► fuente HLK-10M12 (12 V, aislada) ► 4 MOSFET + relevador 10 A  │─► focos normales (contacto)
              │        ▲ cable plano de 8 hilos (J5 ↔ J1)                                            │
              │ PLACA CABEZAL 90×80 (arriba, separadores de 25 mm)                                   │◄─ receptor IR / sensor de luz
              │  ATmega328P propio + Bluetooth BLE + reloj DS3231 + LED                              │◄─ app del celular (Bluetooth)
              └─────────────────────────────────────────────────────────────────────────────────────┘
```

Las **dos placas son de una cara, sin puentes de cable**, y pasan la revisión de KiCad sin errores (ERC/DRC 0, el esquema coincide con la placa). Están listas para planchar o para mandar a fabricar.

| Carpeta | Contenido |
|---|---|
| `ap01-potencia/` | Esquema y PCB KiCad 9, PDF 1:1, Gerber + `.zip` para JLCPCB, modelo 3D |
| `ap01-cabezal/` | Lo mismo, más el programa `firmware/LetreroLabAP01` (.ino y .hex compilado) y la **app** `app/index.html` |
| `ap01-gabinete/` | Caja imprimible (STL), vista y **hoja A4 para planchar las 2 placas** (`imprimir/AP01_cobre_planchar_A4.pdf`) |
| `tools/` | `compilar_avr.sh` (compila sin el IDE), `modelos3d.py`, `ap01_impresion.py` |

## Qué hace

| Función | Cómo |
|---|---|
| Letreros de LED de 5 mm (como el de BAÑOS) | 4 canales: secuencia 100 → 010 → 001, parpadeo, respirar, etc. |
| Tiras LED 12 V de un color o **RGB / RGBW** | Los mismos 4 canales con PWM: color fijo, arcoíris, vela, flash |
| **Focos normales** de 127/240 V | Relevador de 10 A con contacto seco (J4): encender y apagar por horario, app o sensor |
| **App en el celular** | Página web con Bluetooth: no se instala nada ni se sube a tiendas |
| Control remoto | Receptor IR + el control de 24 teclas de las tiras RGB |
| Horarios | Reloj DS3231 con pila, por ejemplo encender 19:00 y apagar 02:00. Se acuerda aunque se vaya la luz |
| Solo de noche | Fotorresistencia: el letrero se apaga de día |
| Memoria | Modo, color, brillo, horario y 4 escenas quedan guardados en el chip |

## Ahorro de energía y cuidado del ambiente

- **Fuente conmutada encapsulada** (HLK-10M12, entrada universal de 100 a 240 V): eficiencia de alrededor del 80 % y consumo muy bajo en espera. Sirve en cualquier país.
- La fuente va **directo al bus de 12 V**, sin diodos en serie que desperdicien energía.
- **Horario y sensor de luz**: el letrero no gasta de día ni de madrugada. **Modo ahorro** limita el brillo al 60 %.
- **Corrección de brillo (gamma)**: se ve igual con menos corriente. LED de estado de 3 mA.
- **Gabinete sin ventilas** (la electrónica disipa ~1.5 W): no entra polvo, así que dura más.
- **Componentes de patas y reparables**: el cabezal se cambia completo en garantía y el chip va en zócalo.
- Recomendado: **soldadura sin plomo** (Sn99Cu1 / SAC305) y componentes **RoHS**. El gabinete en PETG se puede reciclar.

## Lista de materiales (precios aproximados en México)

### Placa de POTENCIA

| Cant | Pieza | Ref | Precio aprox. |
|---|---|---|---|
| 1 | **Fuente Hi-Link HLK-10M12** (100-240 VCA → 12 V 10 W) | PS1 | $120–180 |
| 1 | Fusible lento **T2A 250 V** tipo TR5 radial | F1 | $10 |
| 1 | Varistor **07D471K** | RV1 | $5 |
| 1 | Relevador **SRD-12VDC-SL-C** (Songle, 10 A) | K1 | $20 |
| 4 | MOSFET **IRLZ44N** (TO-220, con la L) | Q1–Q4 | $15–25 c/u |
| 1 | MOSFET 2N7000 (TO-92) | Q5 | $3 |
| 1 | Diodo 1N4148 | D3 | $1 |
| 5 | Resistencia 220 Ω ¼ W | R1–R4, R9 | $1 c/u |
| 5 | Resistencia 10 kΩ ¼ W | R5–R8, R10 | $1 c/u |
| 1 | Capacitor electrolítico 100 µF 25 V, de 105 °C | C1 | $3 |
| 2 | Clema de 2 polos de 5.08 mm (red y contacto de focos) | J1, J4 | $8 c/u |
| 1 | Clema de 2 polos + clema de 3 polos de 5.08 mm, enganchadas = 5 polos (salidas) | J3 | $16 |
| 1 | Tira de pines macho 1×8 | J5 | $5 |
| 1 | Placa fenólica de una cara de 10×10 | — | $30 |

### Placa CABEZAL

| Cant | Pieza | Ref | Precio aprox. |
|---|---|---|---|
| 1 | **ATmega328P-PU "con bootloader de Arduino UNO"** (DIP-28) | U1 | $90–130 |
| 1 | Zócalo DIP-28 angosto | — | $8 |
| 1 | **Resonador cerámico 16 MHz de 3 patas** (CSTLS16M0X53 o "resonador 16 MHz 3 pines") | Y1 | $8 |
| 3 | Capacitor cerámico 100 nF (104) | C1, C8, C10 | $1 c/u |
| 1 | Capacitor electrolítico 10 µF 25 V | C2 | $2 |
| 1 | Regulador **LM7805** (TO-220) | U2 | $10 |
| 1 | Resistencia 10 kΩ | R1 | $1 |
| 4 | Resistencia 1 kΩ | R2, R4, R7, R10 | $1 c/u |
| 1 | Resistencia 2 kΩ (o 2.2 kΩ) | R3 | $1 |
| 4 | Resistencia 220 Ω | R5, R6, R8, R9 | $1 c/u |
| 1 | LED de 3 mm | D1 | $2 |
| 1 | Tira hembra **recta** 1×6 (zócalo del Bluetooth) | J3 | $8 |
| 1 | Tira de pines macho 1×40 (de ahí salen 1×8, 1×4, 1×3 y 3 de 1×2) | J1, J2, J4, J6, J7, J8 | $10 |
| 1 | **Módulo Bluetooth BLE** HM-10, AT-09 o JDY-23 (la app web necesita BLE) | J3 | $70–130 |
| 1 | **Módulo reloj DS3231** (ZS-042, con pila CR2032), con 4 cables Dupont hembra-hembra | J6 | $60–90 |
| 1 | Receptor IR **VS1838B** + control de 24 teclas de tira RGB, con 3 cables | J7 | $40 |
| 1 | Fotorresistencia LDR de 5 mm (GL5528), con 2 cables | J8 | $3 |
| 1 | Botón pulsador de panel (para el frente), con 2 cables | J4 | $10 |
| 1 | **Cable plano Dupont hembra-hembra de 8 hilos**, de 10–15 cm (une las dos placas) | — | $15 |
| 1 | Placa fenólica de una cara de 10×10 | — | $30 |
| 1 | **Adaptador USB-serie con pin DTR** (CH340G o FT232RL), para programar. Se usa para todos los equipos | — | $70–100 |

### Gabinete

| Cant | Pieza | Precio aprox. |
|---|---|---|
| 1 | Impresión de `caja_base.stl` y `caja_tapa.stl` en **PETG o ASA** (113 × 103 × 74 mm) | $150–250 |
| 4 | Separadores hexagonales M3 de **25 mm** hembra-hembra (unen las dos placas) | $8 c/u |
| 8 | Insertos de latón M3 + 4 tornillos M3×6 + 4 tornillos M3 | $30 |
| 4 | **Tornillos de seguridad M3 × 10 Torx con pin** + la punta | $40 |
| 3 | **Prensaestopas PG7** | $10 c/u |
| 1 | Sello de garantía (etiqueta "VOID") | $2 |

**Total del prototipo: unos $1,000–1,300 MXN** con Bluetooth, reloj, IR y caja. Sin módulos opcionales baja a unos $700. En pedido de fábrica cuesta mucho menos.

## Armado

1. **Placas:**
   - Imprime `ap01-gabinete/imprimir/AP01_cobre_planchar_A4.pdf` al 100 %. Trae 2 placas de potencia y 2 cabezal; mide antes la regla de 100 mm.
   - Planchar, atacar y perforar. Los diámetros de broca vienen en `fabricacion/pcb/4_plantilla_perforaciones_1a1.pdf` de cada placa.
2. **Potencia:**
   - Primero resistencias, diodo y 2N7000; luego MOSFET, capacitor, clemas y relevador.
   - Al final pon la **fuente HLK**, el varistor y el fusible.
   - Revisa con el multímetro que **no haya continuidad** entre L y N, ni entre la red y los 12 V.
3. **Cabezal:**
   - Pon primero el **zócalo** (sin el chip), luego el resonador, los capacitores, las resistencias, el 7805, el LED y las tiras de pines.
   - Al final enchufa el chip con la **muesca** del lado que marca la serigrafía.
   - El módulo BLE se enchufa en J3 respetando el letrero de la placa: **1 STATE, 2 RXD, 3 TXD, 4 GND, 5 VCC, 6 EN**.
4. **Unir las placas:** separadores de 25 mm en las 4 esquinas y el cable plano de **J5** (potencia) a **J1** (cabezal), **pin 1 con pin 1**. El orden es 1 AUX, 2-3 PWM1-2, 4-5 GND, 6-7 PWM3-4 y 8 +12 V.
5. **Gabinete:**
   - Monta la potencia sobre los postes.
   - Pasa los cables por los prensaestopas: red atrás, focos a la izquierda, LED al frente.
   - Asoma el IR y el LDR por los 2 agujeros chicos del frente.
   - Cierra con los tornillos de seguridad y pega el sello.

> **PELIGRO:** la placa de potencia tiene 127 V en J1, F1, RV1, la entrada de PS1, los contactos del relevador y J4.
> - Nunca la conectes a la red fuera del gabinete cerrado.
> - **Para probar en la mesa**, no conectes la red: alimenta con un eliminador de 12 V en **J5 pin 8 (+12 V) y pin 4 (GND)**. Así trabajas solo con 12 V.
> - Las zonas de red están separadas al menos 5 mm de la parte de 12 V (regla de KiCad verificada).

## Programar el chip

**Ya compilado:** `ap01-cabezal/firmware/LetreroLabAP01/LetreroLabAP01.hex`. Lo compilé aquí sin errores: 12.7 KB de 32 KB.

1. Compra el ATmega328P **con bootloader de Arduino UNO**. Si viene virgen, se le pone el bootloader con el Arduino Nano que ya tienes (ejemplo "ArduinoISP" del IDE, en protoboard).
2. **Quita el módulo Bluetooth** y conecta el adaptador USB-serie con cables Dupont:
   - GND del adaptador → J3 pin 4 (GND).
   - TX → J3 pin 3 (TXD).
   - RX → J3 pin 2 (RXD).
   - **DTR → J2 (DTR)**.
   - Mantén los 12 V conectados.
3. Abre `LetreroLabAP01.ino` en el Arduino IDE, elige **"Arduino Uno"** y el puerto, y súbelo. También puedes subir el `.hex` con XLoader o avrdude.
4. Vuelve a poner el módulo Bluetooth.

## La app

`ap01-cabezal/app/index.html` es una sola página. Se puede publicar en tu sitio de Vercel (`letrerolab.vercel.app`) o abrir desde el celular. La probé en modo demostración y funciona sin errores.

- **Android:** Chrome → "Conectar Bluetooth" → elige el módulo (HMSoft / BT05 / JDY-23).
- **iPhone:** abre la página en la app **Bluefy**, porque Safari no tiene Bluetooth web.
- **Computadora:** Chrome → "USB" con el adaptador conectado como al programar (9600 baudios).
- **Demo:** prueba la app sin equipo.

La app manda texto simple (`M 1`, `B 80`, `C 255 0 0 0`, `H 19:00 02:00`, `X 1`…). Cualquier otra app, o una versión futura con Wi-Fi, puede controlar el letrero con el mismo protocolo, que está documentado al inicio del programa.

## Pines del cabezal

| ATmega328P | Arduino | Uso | Conector |
|---|---|---|---|
| 17 / 16 / 15 / 12 | D11 / D10 / D9 / D6 | PWM1–PWM4 → canales de potencia | J1 |
| 18 | D12 | AUX → relevador | J1 |
| 2 / 3 | D0 / D1 | Bluetooth (con divisor 1k/2k hacia RXD) y programación | J3 |
| 1 | RESET | Auto-reset al programar (100 nF desde DTR) | J2 |
| 23 | A0 | LDR (pull-up interno) | J8 |
| 24 | A1 | Botón MODO | J4 |
| 25 | A2 | Receptor IR (interrupción por cambio) | J7 |
| 26 | A3 | LED de estado | D1 |
| 27 / 28 | A4 / A5 | Reloj DS3231 (SDA / SCL) | J6 |

Cada entrada externa (IR, botón, LDR, reloj) lleva una **resistencia de protección en serie** contra estática y cables largos.

## Para el letrero BAÑOS

- **Flechas:** cada una se recablea en grupos de 3 LED + 220 Ω, igual que en la placa base 12 V. Van a CH1–CH3 con el + común en "+12".
- **Programa:** en la app pon **Canales = 3** y el efecto **Secuencia**.
- **Palabra BAÑOS y flores:** pueden quedarse en su placa Radox o pasar a CH4 (fijo o parpadeo) recableadas a 12 V.
- **Consumo:** el letrero completo gasta mucho menos de los 0.8 A que da la fuente interna.
