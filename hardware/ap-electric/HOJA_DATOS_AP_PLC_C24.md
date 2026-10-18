# AP PLC C24 · hoja de datos (rev A, CONCEPTO)

PLC compacto de CC para tablero: **12 entradas, 12 salidas protegidas, Ethernet y el enlace AP LINK** para sumarle módulos AP Rack (IN16, AI8, LED8, RL4, AO4, Rack 16). Programación en escalera y texto con AP Lógica / AP Studio, Modbus TCP y consola web.

> **Estado: CONCEPTO.** La placa cierra por software (ERC, DRC y paridad esquema/placa; ver [plc/LEEME.md](plc/LEEME.md)) y el programa pasa 29 pruebas de Modbus TCP más las de la cadena en la PC y compila para el ESP32-C3. **Nada está fabricado ni medido.** No hay certificación (ni CE, ni UL, ni IEC 61131-2) ni límites de corriente validados. **No es una función de seguridad.**

## Qué es y a qué se parece

La idea es el formato de un PLC compacto tipo Omron CP1E (una sola caja con CPU, entradas y salidas, bornas arriba y abajo, LED de estado, puerto de programación) con la comunicación de uno modular tipo Eaton XC300 (Ethernet, RS-485, expansión), pero abierto, en español y con el mismo ecosistema que el resto de AP Electric Industrial.

| | CP1E-N30S1DT1-D (según la ficha de la tienda) | AP PLC C24 rev A |
|---|---|---|
| Entradas | 18 a 24 V CC | **12** a 12-30 V CC, optoaisladas (LTV-217), LED por entrada |
| Salidas | 12 a transistor PNP | **12** de lado bajo NCV8406A (65 V, protección propia), diodo de bobina y LED por salida. La carga va entre +V y la salida |
| Alimentación | 24 V CC | **12-30 V CC** (supresor SMBJ33A, fusible, buck de 60 V) |
| Comunicación | 2 puertos seriales | **Ethernet 10/100** (W5500), **AP LINK RS-485** a 250 kbit/s (hasta 16 módulos), USB-C, Wi-Fi del ESP32-C3 |
| Expansión | módulos propios de la marca | AP Rack IN16, AI8, LED8, RL4, AO4 y Rack 16 por AP LINK (entradas y salidas numeradas seguidas) |
| Estado | RUN/ERR/ALM... | LED de energía, enlace Ethernet, RUN, FALLA, COM, NET y 4 LED de usuario que mueve el programa; botón **RUN/STOP** |
| Programación | CX-Programmer | AP Lógica (escalera y texto), AP Studio, consola |
| Certificaciones | las de la marca | **ninguna** |

Las columnas de otras marcas salen de las capturas de pantalla que mostró el usuario (una tienda y un buscador de imágenes); confirmar con la hoja del fabricante antes de citarlas.

## Elementos de la placa

| Bloque | Piezas |
|---|---|
| Potencia | JST VH (hasta 10 A por pata), portafusible mini de auto (de fábrica **3 A**), SMBJ33A, LMR16006 a 5 V, AP63203 a 3.3 V (2 A) |
| Salidas | 12 × NCV8406A, 12 × SS14, 3 × 74HCT125, TCA9554 0x20 (salidas 1-8) y 0x21 (9-12), 6 borneras de 3 polos (salida, +V, salida) |
| Entradas | 12 × LTV-217, TCA9554 0x22 (1-8, con interrupción) y 0x24 (9-12), 4 borneras de 3 polos y una de comunes (COMI) |
| Ethernet | W5500 (SPI), cristal de 25 MHz, RJ45 con magnéticos HR911105A, terminaciones 49.9 Ω según el diseño de referencia [CG: confirmar contra el esquema de WIZnet] |
| AP LINK | SP3485 sin aislar, SM712, JST XH4 ENTRA y SIGUE, terminación y polarización por puentes de soldadura (cerrar JP2 y JP3 en el PLC, que es la cabeza) |
| Panel | TCA9554 0x23: RUN, FALLA, COM, NET y U1-U4; LED de energía; LED de enlace Ethernet; botón RUN/STOP en el 0x24 |
| Cerebro | ESP32-C3-WROOM-02, USB-C, botones MODO y RESET, 10 puntos de prueba |

Tamaño 200 × 100 mm, 2 capas, 2 oz, 4 agujeros M3. Caja imprimible `caja_plc` y `tapa_caja_plc` en `accesorios/` (206 × 106 × 41 mm; ventanas aproximadas).

## Cambios con respecto a AP Rack 16 y sus consecuencias

1. **Sin medición de la tensión de entrada.** El ESP32-C3-WROOM-02 no tiene pines libres: IO0 pasó a ser el CS del W5500, y el SPI usa IO7, IO20 e IO21. El programa informa 0 V y no avisa de baja o alta tensión.
2. **El W5500 no usa INT** (el programa consulta) y su reset es un RC (10 kΩ y 100 nF).
3. **Sin reloj con pila** en esta revisión: la hora llega por NTP (UTC) en cuanto hay Ethernet y se lee en los registros de entrada 9-11 por Modbus. Sin red al encender, la hora queda sin ajustar. Programado y compilado, sin probar con una red real.
4. El programa detecta la placa por los chips que contestan por I2C: TCA 0x24 **y** 0x20 = AP PLC C24 (el AP Rack IN16 tiene 0x24 pero no 0x20).
5. UART0 (IO20/IO21) ya no sirve para depurar: se usa el USB-C.

## Modbus TCP (puerto 502)

Funciones 01, 02, 03, 04, 05, 06, 15 y 16 sobre **todas** las entradas y salidas de la cadena. Bobinas = salidas globales (la 1 es la salida 1 del PLC; el primer módulo AP Rack sigue en la 13). Entradas discretas = entradas globales. Registros de entrada: versión, módulos, salidas, entradas, RUN, falla, segundos y analógicas desde la 100. Registros 4x: 0 = modo (1 RUN, 0 STOP), 1-16 = consignas R1-R16. Si el programa del PLC maneja una salida, escribirla por Modbus devuelve la excepción 04. Mapa completo en [firmware/APRack/modbus_tcp.h](firmware/APRack/modbus_tcp.h).

Modbus TCP **no tiene autenticación ni cifrado**: usar en una red de planta aislada o detrás de un cortafuegos.

Programas de ejemplo (arranque con sello, intermitente, retardos, contador, aviso de módulo perdido): [PLC_C24_EJEMPLOS.md](PLC_C24_EJEMPLOS.md).

## Qué falta antes de ofrecerlo

Fabricar y medir (corriente por salida, tiempos de entrada y salida, caída de tensión, enlace Ethernet a 100 Mbit/s, EMC), confirmar la terminación del Ethernet con la referencia de WIZnet, revisar a mano la orientación de las piezas polarizadas en JLCPCB, probar el AP LINK con un módulo real y completar NTP, reloj con pila y la medición de tensión (rev B con un ESP32-S3). Ver [PLAN_VERIFICACION.md](PLAN_VERIFICACION.md).
