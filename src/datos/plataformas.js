// Referencias para integrar el controlador como CHIP en la placa (sin módulos ni tarjetas de desarrollo).
// Datos de hojas de datos y guías públicas de cada fabricante; precios orientativos, verificar antes de comprar.

export const CHIPS = [
  { chip: 'ESP32-C3FH4', marca: 'Espressif (China)', radio: 'Wi-Fi 4 + BLE 5', nucleo: 'RISC-V 160 MHz, 4 MB flash interna', enc: 'QFN32 5×5',
    uso: 'Cubo AP v3 (hecho): el mismo firmware de la v2, sin módulo.', fuente: 'https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/schematic-checklist.html' },
  { chip: 'ESP32-C6FH4', marca: 'Espressif (China)', radio: 'Wi-Fi 6 + BLE 5 + 802.15.4 (Thread/Zigbee)', nucleo: 'RISC-V 160 MHz, 4 MB flash interna', enc: 'QFN40 5×5',
    uso: 'Siguiente: Cubo Matter (Wi-Fi o Thread). Su guía recomienda filtro CLCCL en RF, útil en iluminación con fuentes conmutadas.', fuente: 'https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c6/esp-hardware-design-guidelines-en-master-esp32c6.pdf' },
  { chip: 'ESP32-H2', marca: 'Espressif (China)', radio: '802.15.4 + BLE 5 (sin Wi-Fi)', nucleo: 'RISC-V 96 MHz', enc: 'QFN32 4×4',
    uso: 'Lámparas Thread/Zigbee de bajo consumo que dependen de un hub.', fuente: 'https://esp32.co.uk/best-esp32-matter-thread-zigbee-c6-h2-h21-h4-c5/' },
  { chip: 'CH32V003', marca: 'WCH (China)', radio: '—', nucleo: 'RISC-V 48 MHz, 16 KB flash, 2 KB RAM', enc: 'SOP8 a QFN20',
    uso: 'Nodo esclavo de ~0.10 USD: recibe DMX/UART y genera PWM en tiras o focos; 1 controlador maestro por instalación.', fuente: 'https://cnx-software.com/2022/10/22/10-cents-ch32v003-risc-v-mcu-offers-2kb-sram-16kb-flash-in-sop8-to-qfn20-packages/?amp=1' },
  { chip: 'CH32V208', marca: 'WCH (China)', radio: 'BLE 5 + Ethernet 10 M con PHY integrado', nucleo: 'RISC-V 144 MHz', enc: 'QFN (varias versiones)',
    uso: 'Variante cableada: Art-Net/sACN por Ethernet sin chip externo.', fuente: 'https://www.olimex.com/Products/RISC-V/WCH/' },
  { chip: 'RP2350', marca: 'Raspberry Pi (Reino Unido)', radio: '— (necesita chip de radio aparte)', nucleo: '2× Cortex-M33 / Hazard3 150 MHz, PIO', enc: 'QFN60 / QFN80',
    uso: 'Muchas salidas direccionables por PIO; requiere flash QSPI externa y cristal de 12 MHz.', fuente: 'https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008280-DS-2-hardware-design-with-rp2350.pdf' },
  { chip: 'EFR32MG24', marca: 'Silicon Labs (EE. UU.)', radio: 'Thread/Zigbee/BLE (Matter)', nucleo: 'Cortex-M33 78 MHz', enc: 'QFN40/48',
    uso: 'Referencia estadounidense para Matter sobre Thread; ecosistema y certificación maduros.', fuente: 'https://silabs.com/wireless/zigbee/efr32mg24-series-2-socs' },
  { chip: 'nRF54L15', marca: 'Nordic (Noruega)', radio: 'BLE 6 / Thread / Matter', nucleo: 'Cortex-M33 128 MHz', enc: 'QFN48 / WLCSP',
    uso: 'Muy bajo consumo; útil en controles remotos o sensores que acompañan al cubo.', fuente: 'https://esp32.co.uk/best-esp32-matter-thread-zigbee-c6-h2-h21-h4-c5/' },
  { chip: 'BK7231N / BL602', marca: 'Beken / Bouffalo (China)', radio: 'Wi-Fi + BLE', nucleo: 'ARM / RISC-V', enc: 'QFN32 (módulos Tuya CB3S, WB3S…)',
    uso: 'Lo que traen los focos y controladores Tuya baratos: referencia de costo mínimo; se pueden regrabar con OpenBeken.', fuente: 'https://www.elektroda.com/rtvforum/topic4021621.html' },
]

export const PRODUCTOS = [
  { nombre: 'QuinLED Dig-Quad', origen: 'Países Bajos', idea: 'ESP32 con 4 salidas direccionables, fusibles por salida y convertidor de nivel; diseño abierto pensado para WLED.', fuente: 'https://quinled.info/quinled-dig-quad' },
  { nombre: 'Gledopto GL-C-615WL', origen: 'China', idea: 'Controlador comercial ESP32 con WLED de fábrica, 5–24 V, 2 salidas; muestra el formato de producto terminado.', fuente: 'https://www.domadoo.fr/en/wifi-led-strip-controller/9664-gledopto-gl-c-615wl-esp32-wled-led-controller-524v-dc-15a-2x800-ics.html' },
  { nombre: 'WLED All-in-one', origen: 'Comunidad (GitHub)', idea: 'Placa abierta con fuente, MOSFET y salidas en un solo PCB.', fuente: 'https://github.com/Hasenpups/WLED_All-in-one_Controller' },
  { nombre: 'YAWL / codm wled-controller', origen: 'Comunidad', idea: 'Diseños abiertos compactos: ejemplos de protección y conectores para tiras.', fuente: 'https://github.com/codm/wled-controller' },
  { nombre: 'Focos Tuya (BK7231N / CB3S)', origen: 'China', idea: 'Desarmados documentados: radio + driver de corriente constante en una tarjeta mínima.', fuente: 'https://www.elektroda.com/news/news3968216.html' },
  { nombre: 'SM2135 / SM16703P', origen: 'China (Sunmoon)', idea: 'Drivers de LED integrados: corriente constante RGBCW por bus de 2 hilos, y canal direccionable tipo WS2811.', fuente: 'https://esphome.io/components/output/sm2135/' },
]

export const NIVELES = [
  { nivel: 'Nodo', chip: 'CH32V003', que: 'Esclavo de 1–4 canales PWM por DMX/UART, para luminarias repetidas en serie.', estado: 'Propuesta' },
  { nivel: 'Cubo', chip: 'ESP32-C3FH4', que: 'Controlador completo: Wi-Fi, BLE, Art-Net/sACN, DMX por cable, 5 canales, grupos firmados.', estado: 'Placa v3 diseñada (sin probar)' },
  { nivel: 'Cubo Matter', chip: 'ESP32-C6FH4', que: 'Igual al cubo, más Thread/Matter para Apple Home, Google y Alexa sin nube.', estado: 'Siguiente' },
  { nivel: 'Cubo cableado', chip: 'CH32V208', que: 'Art-Net/sACN por Ethernet para escenarios y fachadas.', estado: 'Propuesta' },
]
