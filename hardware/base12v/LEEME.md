# Placa base LetreroLab 12 V: 3 canales, Arduino Nano y Bluetooth

Una sola placa base sirve para **todos los letreros**: LED de 5 mm, tiras LED de 12 V y tiras RGB. Lo que cambia es el programa, no la placa.

- **Bajo voltaje aislado** (eliminador de 12 V): **se puede tocar sin peligro**. En esta placa no hay 127 V.
- **Cerebro enchufable:** Arduino Nano clon en 2 tiras hembra. Se quita y se reprograma.
- **Bluetooth opcional:** el módulo HC-05 o HC-06 se enchufa **directo** en su zócalo J3 de 6 pines.
- **3 canales de potencia** con MOSFET IRLZ44N. Cada uno da hasta 2 A sin disipador.
- **Placa de 50 × 60 mm, una cara, sin puentes**, hecha para planchado de tóner. ERC y DRC sin errores.

## Distribución

```
 ┌──────────────────────────────────────────────┐
 │ [HC-05: EN VCC GND TX RX STATE]  R7   [MODO] │  arriba: Bluetooth y botón
 │ ┌──────────────── ARDUINO NANO ───────────┐  │
 │ │                                     USB ►│  │  el USB queda en el borde derecho
 │ └─────────────────────────────────────────┘  │
 │   R1      R2      R3                         │
 │   Q1      Q2      Q3          C1   D1        │  MOSFET IRLZ44N (G D S)
 │   R4      R5      R6                         │
 │ [+12  CH1  CH2  CH3]      F1   [+12V  GND]   │  abajo: salidas J2 y entrada J1
 └──────────────────────────────────────────────┘
```

## Conexión para el letrero BAÑOS (3 salidas: verde y amarillo pálido)

```
Eliminador 12 V ─► J1 (+12V / GND)
J2:  +12 ──► + común de las 3 tiras (ánodos)
     CH1 ──► − tira 1
     CH2 ──► − tira 2
     CH3 ──► − tira 3
```

A 12 V, una tira de 9 LED en serie (unos 27 V) **no enciende**. Hay que **recablear cada tira en grupos conectados en paralelo**, cada grupo con su resistencia:

| LED | Grupo a 12 V | Resistencia por grupo | Corriente |
|---|---|---|---|
| **Verde** (≈ 3 V) | 3 LED en serie | **220 Ω ¼ W** | ≈ 13 mA |
| **Amarillo pálido / blanco cálido** (≈ 3 V) | 3 LED en serie | **220 Ω ¼ W** | ≈ 13 mA |
| Ámbar, amarillo intenso, rojo (≈ 2 V) | 5 LED en serie | 100 Ω ¼ W (180 Ω si el grupo es de 4) | ≈ 16 mA |
| Tira LED de 12 V | Directa | Ya la trae | — |

**Ejemplo, flecha de 9 LED verdes:** 3 grupos de 3 LED, cada grupo con su resistencia de 220 Ω. Los 3 grupos van en paralelo entre +12 y CH1.

```
+12 ─┬─ 220Ω ─►|─►|─►|─┐
     ├─ 220Ω ─►|─►|─►|─┤
     └─ 220Ω ─►|─►|─►|─┴─ CH1
```

Si una tira no es múltiplo de 3, el grupo que sobra de 2 LED lleva **470 Ω**, y un LED solo lleva **680 Ω**.

**Consumo:** cada grupo gasta unos 13 mA. Con un eliminador de **12 V 1 A** sobra para todo el letrero. Para tiras LED usa uno de 2–3 A.

## Programa (`firmware/LetreroBase/LetreroBase.ino`)

Ábrelo en el Arduino IDE. Elige la placa "Arduino Nano" y el procesador "ATmega328P (Old Bootloader)", que es el de casi todos los clones CH340, y súbelo por USB. El HC-05 puede quedarse puesto porque usa A5/A2 y no los pines D0/D1 del USB.

> **Aviso:** no pude compilar el programa aquí porque no tengo el IDE de Arduino. Si al subirlo aparece algún error, mándame el mensaje y lo corrijo.

| Pin del Nano | Función |
|---|---|
| D9 / D10 / D11 | Canales 1 / 2 / 3 (PWM) |
| A0 | Botón MODO, conectado a GND |
| A5 ← TXD | Bluetooth: recibe |
| A2 → 1 kΩ → RXD | Bluetooth: transmite |
| VIN / GND / 5V | 12 V de la placa / tierra / alimentación del HC-05 |

| Modo | Efecto |
|---|---|
| 0 | Fijo |
| 1 | **Secuencia 100 → 010 → 001** (flechas). Es el modo con el que arranca |
| 2 | Parpadeo |
| 3 | Respirar (sube y baja suave) |
| 4 | Secuencia suave |
| 5 | Alternado 1+3 / 2 |
| 6 | Cambio de color, para tira RGB |

- **Botón MODO** (pulsador en los pads "MODO", o con 2 cables hasta el frente del letrero): un toque pasa al siguiente modo; mantenerlo 1 s cambia la velocidad.
- **Bluetooth:** desde una app tipo "Serial Bluetooth Terminal" (9600 baudios, PIN 1234 del HC-05):
  - `0`–`6` cambian el modo.
  - `+` y `-` cambian la velocidad.
  - `a`–`j` ajustan el brillo de 10 % a 100 %.
  - `?` muestra el estado.
- El modo, la velocidad y el brillo **se guardan** aunque se desconecte.

## Lista de materiales para comprar

Los precios son aproximados, en pesos mexicanos.

| Cant | Pieza | Ref | Precio aprox. |
|---|---|---|---|
| 1 | **Arduino Nano clon (CH340)**, con pines ya soldados, y su cable USB (mini-USB o USB-C, según el modelo) | A1 | $110–160 |
| 1 | **Tira de pines hembra 1×40, paso 2.54**: de ahí cortas 2 de 15 para el Nano y 1 de 6 para el HC-05 | — | $15–25 |
| 3 | **MOSFET IRLZ44N** (TO-220). La "L" es importante: el IRFZ44N sin L **no** sirve con 5 V | Q1–Q3 | $15–25 c/u |
| 3 | Resistencia 220 Ω ¼ W (compuertas) | R1–R3 | $1 c/u |
| 3 | Resistencia 10 kΩ ¼ W | R4–R6 | $1 c/u |
| 1 | Resistencia 1 kΩ ¼ W | R7 | $1 |
| 1 | Fusible rearmable **PTC 2.5 A** (MF-R250 o RXEF250). También sirve uno de 1.1 A si solo vas a usar LED de 5 mm | F1 | $5–10 |
| 1 | Diodo 1N4007 | D1 | $2 |
| 1 | Capacitor electrolítico **220 µF 25 V** (de 8 mm de diámetro) | C1 | $4–6 |
| 3 | Clema de 2 polos de 5.08 mm: una para la entrada y dos enganchadas para las 4 salidas | J1, J2 | $8 c/u |
| 1 | Botón pulsador de 2 patas, o uno de panel con 2 cables | J4 | $3–10 |
| 1 | **Eliminador switching de 12 V 1 A regulado** (2–3 A si vas a usar tiras) | — | $70–150 |
| 1 | Placa fenólica de una cara de 10×10 (alcanza para 2 placas base) | — | $25–35 |
| ~10 | Resistencias de 220 Ω ¼ W para los grupos de LED de las tiras (una por cada grupo de 3) | — | $1 c/u |
| *Opcional* | Módulo Bluetooth **HC-05** (o HC-06) | J3 | $90–130 |

**Total sin Bluetooth: unos $300–450 MXN**, contando el eliminador.

**Para el planchado:**
- Papel couché o de revista.
- Cloruro férrico o persulfato.
- Plancha.
- Fibra o lija fina.
- Marcador indeleble para retoques.
- Brocas de 0.8, 1.0, 1.1 y 1.3 mm.

## Fabricación

Todo está en `fabricacion/`:

**`imprimir/Base12V_cobre_4copias_A4.pdf`: la hoja para planchar.**
- Trae 4 copias 1:1 con regla de 100 mm.
- Imprímela en láser al **100 %**, sin "Ajustar a la página".
- El texto "LETREROLAB 12V" debe verse **al revés** en el papel.
- `imprimir/Base12V_cobre_1200ppp.png` es la misma imagen en alta resolución.

**`pcb/`**
- `1_cobre_para_planchado_1a1.pdf`: el cobre en espejo, igual que la hoja de 4 copias.
- `3_lado_componentes_1a1.pdf`: lado de componentes.
- `4_plantilla_perforaciones_1a1.pdf`: plantilla de perforaciones.
- `5_ensamble_componentes_con_valores.pdf`: guía de ensamble.

**Otros:** esquema (`esquema/`), BOM, Gerber, 3D y reportes ERC/DRC (0 errores, el esquema coincide con la placa).

**Brocas:**

| Broca | Cantidad | Para |
|---|---|---|
| 0.8 mm | 18 | Resistencias, C1 y PTC |
| 1.0 mm | 38 | Tiras hembra del Nano y del HC-05, y diodo |
| 1.1 mm | 9 | MOSFET |
| 1.3 mm | 8 | Clemas y pads MODO |

**Orden de armado:**
1. Resistencias. Van **paradas**, con el cuerpo sobre el círculo de la serigrafía.
2. Diodo D1 parado, con la **franja (K)** en el pad cuadrado marcado "K".
3. PTC y capacitor. La pata **larga (+)** del capacitor va en el pad cuadrado "+".
4. Tiras hembra: 2 de 15 para el Nano y 1 de 6 para el HC-05.
5. MOSFET, con la cara de las letras hacia las clemas. El orden de las patas es G-D-S, como en la serigrafía.
6. Clemas, con las entradas de cable hacia el borde.
7. Botón MODO o sus 2 cables.
8. Al final, enchufa el Nano con el **USB hacia el borde derecho**. El HC-05 va con su pin **EN** del lado marcado "EN" (los nombres coinciden con los de su tira de pines).

**Prueba:**
1. Sin el Nano, conecta 12 V y mide que J2 "+12" tenga unos 12 V.
2. Desconecta, pon el Nano y vuelve a conectar. Las 3 salidas deben correr 1 → 2 → 3.

## Regenerar

```
docker exec -w /work/hardware/base12v kc python3 gen/make.py --manual   # esquema + PCB con las pistas a mano
docker exec -w /work/hardware/base12v kc python3 gen/outputs.py         # PDF, Gerber, BOM, ERC/DRC
python3 gen/pdf_post.py && python3 gen/imprimir.py                      # notas, regla y hoja de 4 copias
```
