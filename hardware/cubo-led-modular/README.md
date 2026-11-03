# Cubo AP · módulo LED modular (concepto + modelo 3D)

Cubo impermeable (IP67 de diseño) de 80 mm para letreros: cartucho de potencia intercambiable (S/M/L),
regulación configurable por tarjeta de resistencias o por app (la tarjeta fija el máximo), control ESP32-C3
con Bluetooth/Wi-Fi y 4 canales PWM + datos para tiras direccionables.

- `cubo.py`: modelo paramétrico para Blender 4.x (bpy). Genera `cubo_ap.blend` y `cuerpo.stl`, `tapa.stl`, `empaque.stl` (mallas cerradas).
- `render.py`: renders armado / explotado / corte con Cycles.
- `hacer_documento.py` + `imprimir.cjs`: `cubo_ap_sistema.pdf` con la arquitectura y las reglas de diseño.

Regenerar: `python3 cubo.py && python3 render.py && python3 hacer_documento.py && NODE_PATH=$(npm root -g) node imprimir.cjs`.

## Firmware (`firmware/`) y app (`app/`)

- `firmware/src/nucleo.*`: lógica portable. Hace lo siguiente:
  - decodifica la tarjeta;
  - calcula el voltaje y el DAC;
  - aplica el arranque suave, la limitación suave de corriente, el recorte térmico, las fallas con reintento y los efectos;
  - interpreta el protocolo de texto.
- `firmware/test/test_nucleo.cpp`: **124 pruebas** que corren en PC. Comando:
  `cd firmware/test && g++ -std=c++17 -I../src test_nucleo.cpp ../src/nucleo.cpp -o t && ./t`
- `firmware/src/main.cpp`: código del ESP32-C3. Usa Arduino-ESP32 3.x, NimBLE-Arduino 2.x y Adafruit NeoPixel. Compila con `pio run`.
  Solo se verificó la sintaxis contra cabeceras simuladas (`test/stubs`). **Falta compilarlo con el toolchain real y probarlo en placa.**
- `app/index.html`: app web con Bluetooth seguro (Chrome/Edge en Android o PC), servida por HTTPS (p. ej., GitHub Pages).
  Tiene un botón **Demo** para probarla sin hardware.

### Seguridad por diseño (no depende del software)
1. **La tarjeta fija el voltaje máximo por hardware.** R_FB va en la tarjeta. El DAC inyecta corriente al nodo FB a través de un diodo, así que **solo puede bajar** el voltaje. Si el ESP32 se cuelga o el DAC queda en 0 V, la salida queda en el máximo de la tarjeta y nunca más arriba.
2. **Corte rápido por hardware.** El ALERT del INA226 (enclavado, a 1.6 × Imax) tira a GND el EN del reductor en ~1 ms. El firmware lo detecta y reintenta cada 5 s, hasta 3 veces.
3. **Protección por firmware.** Limitación suave: baja el brillo antes de cortar. Sobrecorriente o corto a 1.5 × Imax por 50 ms. Recorte térmico de 70 a 90 °C. Subvoltaje del cartucho. Tarjeta que no coincide con el voltaje medido.
4. **Bluetooth.** Vinculación con PIN de 6 dígitos único por equipo (va en la etiqueta), con MITM y cifrado. Mantener el botón 6 s borra los vínculos.

### Tarjetas de configuración (R_ID con pull-up de 10k; R_FB con Rb = 1k; Vref = 0.8 V)
| Perfil | R_ID | R_FB (1 %) | Vmax | Rango con app |
|---|---|---|---|---|
| 5V 3A | 1k | 5.23k | 4.98 V | 4.4–4.98 V |
| 12V 1A / 2A / 5A | 2.2k / 3.9k / 6.8k | 14.0k | 12.0 V | 10.5–12.0 V |
| 15V 1A / 3A | 10k / 15k | 17.8k | 15.0 V | 13.1–15.0 V |
| 24V 2A / 3A | 22k / 47k | 29.4k | 24.3 V | 21.1–24.3 V |

El cartucho debe dar al menos Vout + 1.2 V. Para 12 V y 15 V se usa el de 24 V; para 24 V, uno de 28–36 V.

### Pines ESP32-C3
| GPIO | Función | | GPIO | Función |
|---|---|---|---|---|
| 0 | ADC tarjeta (R_ID) | | 8 / 9 | I2C SDA / SCL (INA226 0x40, MCP4725 0x60) |
| 1 | ADC Vin ÷ 11 | | 10 | Datos WS2812 (vía 74AHCT1G125) |
| 2 | Botón | | 20 | LED de estado (tubo de luz de la tapa) |
| 3 | ADC NTC 10k | | 21 | EN del reductor (+ ALERT del INA226) |
| 4–7 | PWM R, G, B, W (19 kHz, 12 bit) | | 18 / 19 | USB (programación y consola) |

### Protocolo (BLE, Nordic UART, o USB a 115200 baudios)
`ON`, `OFF`, `BRILLO 0-100`, `RGBW r g b w`, `V 11.5`, `MODO FIJO|RESPIRA|ARCOIRIS|DIREC`, `LEDS n`, `RESET`, `ESTADO` (responde en JSON).
