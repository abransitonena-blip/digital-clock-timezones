# AP PLC C24 rev B (EN CURSO: colocada, sin rutear)

Rev B del [AP PLC C24](../plc/LEEME.md) con **ESP32-S3-WROOM-1 (N8)** para quitar los límites de la rev A:

| | Rev A (ESP32-C3) | Rev B (ESP32-S3) |
|---|---|---|
| Tensión de entrada | no se mide (IO0 es el CS del W5500) | **se mide** (IO7, divisor 100 k / 10 k) |
| Reloj | sin reloj con pila (solo NTP) | **PCF8563T con batería externa** (I2C 0x51), como el 7R Tour rev B; se fija la hora del sistema al arrancar y se corrige con NTP cada hora |
| W5500 | sin INT; reset por RC | **INT en IO38 y RST en IO2** manejados por el programa (el RC queda como respaldo) |
| Modbus | TCP por Ethernet | TCP **y RTU** por un **segundo RS-485** independiente de AP LINK (SP3485, borne A, B, 0 V; IO4 RX, IO5 TX, IO6 DE; terminación por puente JP4) |
| Pines evitados | — | IO0 solo para MODO; IO3, IO45, IO46 (arranque) y IO26-IO37 (memoria) |

## Estado, sin adornos

- **Hecho y probado por software:** generador `gen/make.py` (esquema, placa colocada y sin choques de cortesía), mapa de pines del módulo contra el programa (`tools/revisar_pines.py`, con una prueba de que detecta un pin cambiado), **programa compilado para el ESP32-S3** (`bash tools/compilar_esp32.sh aprack_s3`; 32 % de la memoria; deja `firmware/binarios/APPLC_C24B_*.bin`), conversión del reloj PCF8563 y Modbus RTU en la PC (19 comprobaciones).
- **Sin hacer: el ruteo.** El ruteador automático (Freerouting, 2 capas) dejó entre 3 y 9 uniones pendientes en las mejores corridas (INT, ETH_MISO, tramas de LED, GND/3V3 del módulo). La ruta asistida propia (`tools/ruta_auto.py`) cerró algunas pero **creó cortos junto al USB-C**, así que no se usó. Con 4 capas con planos internos el resultado fue peor (52 pendientes). Por eso **no hay Gerber, BOM ni CPL de la rev B** y no se ha pasado ERC/DRC.
- **Qué lo desatora (ideas, no probadas):** acercar al módulo los expansores y las redes largas (INT va de IO10 a cinco expansores repartidos por toda la placa), mover el RS-485 de Modbus junto al módulo en vez de arriba, y bajar a un ruteo con una capa de señal más (planos solo en 3V3/GND con 4 capas pero con estrategia de pistas en ambas caras interiores).
- **Códigos LCSC:** el ESP32-S3-WROOM-1-N8 es C2913198 según una réplica de datos de LCSC (no confirmado en lcsc.com): falta agregarlo a `tools/jlcpcb.py` y confirmarlo antes de pedir. El reloj reutiliza los códigos ya verificados del 7R Tour rev B.
- **Antena:** el módulo queda en el borde derecho con su antena asomada 0.75 mm fuera de la placa y una zona sin cobre bajo la antena (x ≥ 193.4 mm); sus esquinas GND (pines 1 y 40) quedan justo al lado de esa zona.

## Qué del programa ya sirve en las dos revisiones

`firmware/APRack` compila para ESP32-C3 (rev A y los módulos AP Rack) y para ESP32-S3 (rev B) con el mismo código: el bloque `#if CONFIG_IDF_TARGET_ESP32S3` de `APRack.ino` fija los pines de la rev B; `rtc_pcf8563.h` y `modbusRtu()` (en `modbus_tcp.h`) son portables y están probados en la PC (`firmware/pruebas/prueba_rtc_rtu.cpp`).
