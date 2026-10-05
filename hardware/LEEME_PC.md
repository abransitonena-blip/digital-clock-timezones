# LetreroLab: proyecto completo para trabajar en la PC

Este paquete (`LetreroLab_proyecto_completo.zip`) trae **todo** el ecosistema AP-1 y la placa única AP-0.2:
- los proyectos de KiCad que se pueden editar;
- los generadores;
- el programa del ESP32 (código y binarios);
- el gabinete para imprimir;
- los archivos listos para pedir las placas **armadas** a JLCPCB.

## Qué hay en cada carpeta

| Carpeta | Qué es |
|---|---|
| `PEDIDO_JLCPCB/` | **Lo que se sube a JLCPCB** (Gerber, BOM y CPL de cada placa). Instrucciones en `PEDIDO_JLCPCB/LEEME_COMO_PEDIR.md` |
| `ap1-base/` | Base universal (4 capas): 4 canales de 8 A, 2 focos de corriente constante, AUX |
| `ap1-prog/` | Programador ESP32-C3. En `firmware/` están el código (`LetreroLabAP1/`) y los binarios (`binarios/`) |
| `ap1-ind/` | Módulo industrial: 4 × 0-10 V aislados y 2 contactores |
| `ap1-pix/` | Módulo de pixeles WS2812/SK6812/WS2815 |
| `ap1-in/`, `ap1-out/` | **AP ELECTRIC** AP INPUT (8 entradas aisladas) y AP OUTPUT (7 salidas de 24 V), por Qwiic. Mapa del ecosistema en `AP_ELECTRIC.md` |
| `ap1-dmx/` | Módulo DMX512: controlador DMX con Wi-Fi para reflectores RGB/RGBW y equipos DMX. Guía en `ap1-dmx/LEEME.md` |
| `ap1-plantilla/` | **Base para módulos nuevos**: entrada, fuente de 12 V, memoria, conector LL y área de prototipos. Guía en `ap1-plantilla/LEEME.md` |
| `ap1-gabinete/` | Gabinete para impresión 3D (`gabinete/*.stl`) y soportes para riel DIN (`din/*.stl`) |
| `ap1-ensamble/` | Modelo 3D de base + programador (STEP) |
| `ap02/` | AP-0.2 rev D, placa única |
| `tools/` | Generador de placas (`placa.py`), salidas para JLCPCB, librería de huellas propia (`huellas/LetreroLab.pretty`) |
| `fuente-os-127v/gen`, `controlador-flechas-36v/gen` | Solo código que usan los generadores (esquemático y huellas). **No** son placas para fabricar |

Dentro de cada placa:
- `kicad/`: proyecto de KiCad (`.kicad_pro`, `.kicad_sch`, `.kicad_pcb`, reglas, modelos 3D en `3d/`);
- `gen/make.py`: el generador (la "fuente" de la placa);
- `fabricacion/`: Gerber, BOM, CPL, renders, STEP y esquemático en PDF.

## 1. Abrir las placas en KiCad

1. Instala **KiCad 9** (kicad.org, gratis para Windows, Mac y Linux).
2. **Descomprime el zip completo** sin cambiar la estructura de carpetas. La librería de huellas propia se encuentra por ruta relativa (`../../tools/huellas/LetreroLab.pretty`).
3. Abre `ap1-xxx/kicad/AP1_xxx.kicad_pro`.
   - El esquema y la placa abren sin más, y los modelos 3D están en `kicad/3d/`.
   - Si KiCad pregunta por la tabla de librerías, elige **"Copiar la tabla predeterminada global"**.
4. Para revisar: **Inspeccionar → Comprobador de reglas de diseño (DRC)** debe dar 0 errores. Las reglas de JLCPCB ya están en el archivo `.kicad_dru` de cada placa.

**Ojo:** si editas a mano en KiCad, ese cambio se pierde la próxima vez que corras `gen/make.py`. Puedes:
- editar solo en KiCad (y ya no usar el generador para esa placa); o
- cambiar el `gen/make.py` y volver a generar (recomendado; así se hicieron todas).

## 2. Volver a generar o crear placas (opcional, usuarios avanzados)

Los generadores usan el Python de KiCad (`pcbnew`) y Freerouting.
- **Linux o WSL:** instala KiCad 9 y Java 21, descarga `freerouting.jar` (versión 2.x, de github.com/freerouting) y corre desde esta carpeta:
  ```bash
  FR=/ruta/freerouting.jar bash tools/rutear.sh ap1-plantilla AP1_Plantilla    # genera, rutea, ERC/DRC
  python3 tools/salidas.py ap1-plantilla AP1_Plantilla                         # archivos para JLCPCB
  bash tools/pedido_jlcpcb.sh                                                  # vuelve a juntar PEDIDO_JLCPCB/
  ```
  Usa el Python que trae KiCad (en Linux, el `python3` del sistema con el paquete `kicad`).
- **Windows:** usa la "KiCad 9 Command Prompt" (trae Python con `pcbnew`) o WSL.

Guía paso a paso para un módulo nuevo: `ap1-plantilla/LEEME.md`.

## 3. Programa del ESP32 (programador AP-1)

**Para grabar sin compilar:**
- Sin cables: si el equipo ya tiene programa, abre la app → **Actualizar** y sube `ap1-prog/firmware/binarios/LetreroLabAP1_actualizacion_OTA.bin`.
- Por USB-C, la primera vez:
  1. abre https://espressif.github.io/esptool-js/ en Chrome o Edge;
  2. conecta el programador y elige su puerto;
  3. dirección **0x0**, archivo `LetreroLabAP1_completo_0x0.bin`;
  4. pulsa Program.

**Para modificar el código con Arduino IDE 2:**
1. Preferencias → URL adicionales de tarjetas: `https://espressif.github.io/arduino-esp32/package_esp32_index.json`.
2. Gestor de tarjetas → **esp32 de Espressif, versión 3.1.1**.
3. Abre `ap1-prog/firmware/LetreroLabAP1/LetreroLabAP1.ino`.
4. Configura la tarjeta:
   - **ESP32C3 Dev Module**;
   - USB CDC On Boot: **Enabled**;
   - Partition Scheme: **Minimal SPIFFS (1.9MB APP with OTA)**;
   - Flash Size: 4MB.
5. No necesita librerías extra: todo usa el núcleo del ESP32.
6. Sube el programa.

Desde Linux también se puede usar `bash tools/compilar_esp32.sh ap1`, que descarga arduino-cli y compila.

## 4. Pedir las placas armadas

Abre `PEDIDO_JLCPCB/LEEME_COMO_PEDIR.md`. En resumen, para cada placa:
1. sube el `1_..._GERBER.zip`;
2. activa **PCB Assembly**;
3. sube la BOM (`2_...`) y el CPL (`3_...`) de `ensamble_economico_solo_SMD/` (recomendado) o de `ensamble_completo/`;
4. revisa el giro de las piezas en la vista previa contra `vista_superior.png`.

**Sistema mínimo:** 1 BASE + 1 PROGRAMADOR. Para probar ideas nuevas: 1 PLANTILLA + 1 PROGRAMADOR.

## Seguridad (no cambia)

- Ninguna placa LetreroLab lleva tensión de red (127/240 V). Todo funciona con **12-24 V DC** de una fuente certificada.
- Las luces de red se encienden con un **contactor o relevador de estado sólido de riel DIN certificado**, instalado por un electricista. La placa solo mueve su bobina de 12-24 V.
