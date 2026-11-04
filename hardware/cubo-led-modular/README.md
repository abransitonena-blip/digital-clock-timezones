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
- `firmware/test/test_nucleo.cpp`: **215 pruebas** que corren en PC. Comando:
  `cd firmware/test && g++ -std=c++17 -I../src test_nucleo.cpp ../src/nucleo.cpp -o t && ./t`
- `firmware/src/main.cpp`: código del ESP32-C3. Usa Arduino-ESP32 3.x, NimBLE-Arduino 2.x y Adafruit NeoPixel. Compila con `pio run`.
  Usa Espalexa para Alexa. Solo se verificó la sintaxis contra cabeceras simuladas (`test/stubs`). `gen_pagina.py` mete `app/index.html` en `src/pagina.h`; PlatformIO lo corre solo al compilar. **Falta compilarlo con el toolchain real y probarlo en placa.**
- `app/index.html`: app web con Bluetooth seguro (Chrome/Edge en Android o PC), servida por HTTPS (p. ej., GitHub Pages).
  Tiene un botón **Demo** para probarla sin hardware.

### Seguridad por diseño (no depende del software)
1. **La tarjeta fija el voltaje máximo por hardware.** La tarjeta lleva R_B, la resistencia *inferior* del divisor; la superior (29.4k) va en la placa.
   - Sin tarjeta, o con la tarjeta floja: FB = Vout y la salida se cae a ~0.8 V.
   - Tarjeta al revés: también da un voltaje bajo (≤3.2 V) y el ID resulta inválido.
   - El DAC inyecta corriente al FB a través de un diodo, así que **solo puede bajar** el voltaje. Si el ESP32 se cuelga, la salida se queda en el máximo de la tarjeta y nunca lo pasa.
2. **Corte rápido por hardware.** El ALERT del INA226 (enclavado, a 1.6 × Imax) tira a GND el EN del reductor en ~1 ms. El firmware lo detecta y reintenta cada 5 s, hasta 3 veces.
3. **Protección por firmware.** Limitación suave: baja el brillo antes de cortar. Sobrecorriente o corto a 1.5 × Imax por 50 ms. Recorte térmico de 70 a 90 °C. Subvoltaje del cartucho. Tarjeta que no coincide con el voltaje medido.
4. **Bluetooth.** Vinculación con PIN de 6 dígitos único por equipo (va en la etiqueta), con MITM y cifrado. Mantener el botón 6 s borra los vínculos.

### Tarjeta de configuración
Conector de 3 pines: 1 FB · 2 GND · 3 ID. Lleva dos resistencias de 1 %: R_B entre los pines 1 y 2, y R_ID entre los pines 3 y 2. Vout = 0.8 × (1 + 29.4k / R_B).

| Perfil | R_ID | R_B | Vmax | Rango con app |
|---|---|---|---|---|
| 5V 3A | 10k | 5.62k | 4.98 V | 3.6–4.98 V |
| 12V 1A / 2A / 5A | 15k / 22k / 33k | 2.10k | 12.0 V | 10.6–12.0 V |
| 15V 1A / 3A | 47k / 68k | 1.65k | 15.05 V | 13.7–15.05 V |
| 24V 2A / 3A | 100k / 150k | 1.00k | 24.3 V | 22.9–24.3 V |

El cartucho debe dar al menos Vout + 1.2 V. Para 12 V y 15 V se usa el de 24 V; para 24 V, uno de 28–36 V.

### Pines ESP32-C3 (SuperMini enchufable)
| GPIO | Función | | GPIO | Función |
|---|---|---|---|---|
| 0 | ADC tarjeta (R_ID, pull-up 47k) | | 5 / 6 / 7 | PWM G / B / W (19 kHz, 12 bit) |
| 1 | ADC Vin ÷ 11 | | 8 / 9 | I2C SDA / SCL (INA226 0x40, MCP4725 0x60) |
| 2 | Botón | | 10 | Datos WS2812 (vía 74AHCT1G125) |
| 3 | ADC NTC 10k | | 20 | LED de estado (tubo de luz de la tapa) |
| 4 | EN del reductor (+ ALERT del INA226) | | 21 | PWM R |

## Placa de control (`placa-control/`)
Placa de 2 capas, 68 × 64 mm, hecha para fabricarse y ensamblarse (JLCPCB o similar). Detalles en `placa-control/README.md`.

### Tiras, efectos e integraciones (firmware)
- **Tiras:**
  - analógicas: RGBW, RGB, CCT (cálido en R, frío en G) y MONO (salida W);
  - direccionables: WS2812B y SK6812 a 5 V; WS2811 y WS2815 a 12 V.

  El cubo **rechaza una tira direccionable si la tarjeta no da su voltaje** (por ejemplo, WS2812B con tarjeta de 12 V).
- **Efectos:** fijo, respira, arcoíris, fuego y cometa. En las tiras direccionables son por pixel.
- **Horario diario:** enciende y apaga solo. La hora la manda la app, o la toma de internet (NTP) con Wi-Fi, en la zona `ZONA` (UTC-6 por defecto).
- **Tarjeta PERSONAL** (R_ID 220k): sirve para cualquier voltaje de 3 a 24.4 V. La R_B se calcula en la web; después se mandan los límites con `LIMITES v i`. Sin límites no enciende.
- **Wi-Fi** (`WIFI red clave`):
  - página de control propia en `http://cuboap-xxxx.local`;
  - API `/api/cmd` que pide el PIN en la cabecera `X-PIN`;
  - `/api/estado`.
- **Integraciones** (`INTEGRACIONES ON`, apagadas de fábrica porque no llevan contraseña):
  - API JSON tipo WLED (`/json/state`, `/json/info`) con anuncio mDNS `_wled._tcp`;
  - Alexa local con Espalexa.

  Home Assistant lo usa con la integración WLED. Solo se implementó un subconjunto (encendido, brillo y color); **falta probarlo con las apps reales**.
- **DMX por red** (`DMX ARTNET universo dirección`, `DMX SACN universo dirección`, `DMX OFF`). Es el control profesional que usan las consolas, xLights, QLC+, Resolume y MadMapper.
  - **Tiras analógicas:** 5 canales (atenuador, R, G, B, W).
  - **Tiras direccionables:** 3 o 4 canales por LED.
  - Si dejan de llegar paquetes durante 2.5 s, el cubo vuelve a su modo normal. Las protecciones siguen activas.
  - sACN se recibe por multicast (239.255.x.x) y por unicast.
  - Los paquetes se probaron armados según la norma y con datos basura; **falta probarlo con una consola real**.
- **Escenas:** 8 escenas guardadas en memoria (`ESCENA GUARDAR n`, `ESCENA n`). Cada una guarda color, brillo, efecto y temperatura de blanco.
- **Actualización OTA:** se sube el `.bin` desde la página del cubo, que pide el PIN. Mientras se escribe la memoria, la salida se apaga.
- **Bluetooth:** las respuestas se mandan en trozos de 180 bytes terminados en salto de línea, así no se cortan con MTU chicos.

### Protocolo (BLE, Nordic UART, o USB a 115200 baudios)
- **Luz:** `ON`, `OFF`, `BRILLO 0-100`, `RGBW r g b w`, `V 11.5`, `MODO FIJO|RESPIRA|ARCOIRIS|FUEGO|COMETA`, `RESET`.
- **Tira:** `TIRA RGBW|RGB|CCT|MONO|WS2812B|SK6812|WS2811|WS2815`, `CCT 2700-6500`, `LEDS n`.
- **Horario:** `HORA epoch_local`, `PROG 18:30 01:00` (o `PROG OFF`), `ZONA -6`.
- **Escenas y DMX:** `ESCENA n`, `ESCENA GUARDAR n`, `DMX ARTNET|SACN universo dirección`, `DMX OFF`.
- **Tarjeta y red:** `LIMITES v i`, `WIFI red clave` (o `WIFI OFF`), `NOMBRE x`, `INTEGRACIONES ON|OFF`.
- **Consulta:** `RED` y `ESTADO` responden en JSON.
