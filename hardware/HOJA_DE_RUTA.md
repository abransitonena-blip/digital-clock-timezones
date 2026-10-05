# Hoja de ruta LetreroLab: de la placa casera a la fabricación propia

> **Para pedir las placas armadas a JLCPCB:** [PEDIDO_JLCPCB.md](PEDIDO_JLCPCB.md) (archivos en `PEDIDO_JLCPCB/`).

**Idea:** tener circuitos propios, con diagramas, programa, modelo 3D y gabinete que son nuestros. Así no dependemos de placas de terceros como la Radox, y cada módulo se puede replicar, mandar a fabricar y dar con garantía.

**Regla:** empezar con lo básico casero y crecer paso a paso, retroalimentando cada día con pruebas reales.

## Fase 1: casero (ahora)

Lo que ya existe en este repositorio:

| Módulo | Carpeta | Estado |
|---|---|---|
| **Placa base 12 V**: 3 canales MOSFET, Arduino Nano y HC-05 | `base12v/` | Lista para planchar (v1.1, 60 × 72 mm, 4 barrenos M3) |
| **Gabinete de seguridad**: tornillos especiales y sello de garantía | `base12v/gabinete/` | STL para imprimir, o plantilla para caja metálica |
| **Programa**: 7 modos, Bluetooth, memoria EEPROM | `base12v/firmware/` | Escrito, falta probarlo en el Nano |
| Fuentes capacitivas 127 V (OS, 3 salidas, flechas) | `fuente-os-127v/`, `fuente3-127v/`, `flechas-127v/` | Listas. No aisladas: solo dentro del letrero |
| Modelo 3D de la placa | `base12v/fabricacion/3d/` | STEP y renders con componentes |
| **LetreroLab AP-0.1**: placa de potencia (fuente 100-240 V integrada, 4 canales, relevador para focos) + placa cabezal con **chip propio ATmega328P**, Bluetooth, reloj, IR y LDR | `ap01-potencia/`, `ap01-cabezal/`, `ap01-gabinete/`, guía en `LetreroLab_AP01.md` | Listas para planchar (2 placas sin puentes, ERC/DRC 0); programa compilado; app web probada en modo demo |
| **LetreroLab AP-0.2**: una placa SMD para ensamble en fábrica, ESP32-C3 (Wi-Fi), 12-24 V hasta 20 A, 4 canales de 8 A, relevador, USB-C, horarios NTP, control de toda la casa y MQTT | `ap02/` (guía en `ap02/LEEME.md`) | Rev D lista para pedir a JLCPCB (ERC/DRC 0, corte por hardware); programa 1.2 con Home Assistant; falta probar la primera tanda |
| **LetreroLab AP-1** (sistema modular): **base universal** de potencia (12-24 V 20 A, 4 x 8 A, 2 focos de corriente constante, AUX, medidor y memoria con serie) + **programador** ESP32-C3 que se enclava encima + **módulo industrial IND** (0-10 V aislado y contactores para naves y luces de red) + **módulo de pixeles PIX** (WS2812/SK6812, letras en secuencia) + **módulo DMX512** (reflectores y equipos DMX) + **PLANTILLA** para módulos nuevos (conector LL repetido y área de prototipos) | `ap1-base/`, `ap1-prog/`, `ap1-ind/`, `ap1-pix/`, `ap1-plantilla/`, `ap1-dmx/`, `ap1-ensamble/`, `ap1-gabinete/` (guías en `LetreroLab_AP1.md` y `ECOSISTEMA.md`) | Listas para pedir a JLCPCB (ERC/DRC 0 en todas; proyecto completo para PC en `LetreroLab_proyecto_completo.zip` con `LEEME_PC.md`; base de 4 capas con corte por hardware); programa 1.3 con diagnóstico de salidas, pixeles, DMX512 y Home Assistant; gabinete imprimible; falta la primera tanda |

**Tareas de esta fase:**
1. Armar la placa base, cargar el programa y probarla en el letrero BAÑOS.
2. Imprimir el gabinete y validar medidas, temperatura y cableado.
3. Anotar fallas y mejoras. Eso alimenta la v1.2.

## Fase 2: placa fabricada en JLCPCB (pocas semanas después)

La misma placa v1.1 ya tiene su paquete: `base12v/fabricacion/jlcpcb/Base12V_v1.1_gerber_JLCPCB.zip`.

- **Primer pedido:** solo placas (5 o 10 piezas). Las soldamos nosotros con los mismos componentes de la tienda.
- **v1.2 propuesta** (antes de pedir muchas):
  - **Reloj de tiempo real DS3231**, con su pila. Sirve para **programar horarios**, por ejemplo encender a las 8:00 y apagar a las 23:00. Va en el bus I²C (A4/A5), así que hay que mover el Bluetooth a otros pines.
  - Conector para el **sensor de luz (LDR)**, para que el letrero encienda solo de noche.
  - **Número de serie** en la serigrafía y en el programa, para controlar las garantías.

## Fase 3: módulo "industrial" con ensamble en fábrica (PCBA)

> **Ya iniciada con el AP-0.2** (`ap02/`): ESP32-C3, MOSFET SMD, 2 capas con planos de potencia, app web, OTA, BOM y CPL para JLCPCB.

Para que la fábrica arme las placas conviene **rediseñar con componentes SMD** y quitar los módulos enchufables:

| Hoy (casero) | Versión de fábrica |
|---|---|
| Arduino Nano + HC-05 | **ESP32-C3**, un solo chip con **Wi-Fi y Bluetooth**. Es más barato que Nano + HC-05 y toma la hora de internet (NTP), así que no necesita reloj extra |
| IRLZ44N TO-220 | MOSFET SMD (AO3400 o similar, SOT-23 / DFN) |
| Clemas | Clemas o conectores JST con seguro |
| Una cara | 2 capas con plano de tierra (AP-0.2, programador) o **4 capas** con dos planos internos de GND (base AP-1) |

Lo que JLCPCB pide para ensamblar:
1. **Gerber**.
2. **BOM** con el código LCSC de cada pieza (conviene usar sus "basic parts", que no cobran extra). `tools/salidas.py` ya los llena solo con la biblioteca JLCPCB (`tools/descargar_biblioteca_jlcpcb.sh`).
3. **CPL**: posición y giro de cada componente. KiCad lo exporta.

**Programa y aplicación:** el ESP32 permite una **app propia** (o página web en el mismo módulo) con modos, colores, horarios, brillo y escenas. Además se puede **actualizar el programa por Wi-Fi (OTA)**, sin abrir la caja; eso respeta el gabinete sellado.

Ese "programador de funciones especiales" queda como una pantalla de la app: modos personalizados y secuencias guardadas en la memoria del módulo.

**Sobre "módulo propio" e internacional:** para vender en otros países, la parte de radio (Bluetooth o Wi-Fi) debe estar **certificada**: FCC, CE, IFT en México, etc. Certificar un diseño de radio propio cuesta miles de dólares. Por eso las marcas, incluso las grandes, usan un **módulo de radio ya certificado** (BLE o Wi-Fi) soldado en **su propia placa**, con su marca, su programa y su app. Así es el AP-0.1: el cerebro (ATmega328P), la potencia, el programa, la app y el protocolo son nuestros, y el Bluetooth es un módulo enchufable y reemplazable.

## Fase 4: productos propios (focos y lámparas LED, tiras, letreros)

**Vida útil y calor.** Lo que más alarga la vida es **bajar la temperatura**:
- **LED:** se especifica la vida **L70**, el momento en que la luz baja al 70 %. Lo realista es **25 000 a 50 000 horas** con buena disipación. Cifras de "1 millón de horas" son **MTBF estadístico** de la electrónica, no vida del LED, así que no conviene prometerlas al cliente.
- **Corriente:** trabajar los LED **al 60–75 % de su corriente máxima**. Por ejemplo, 13 mA en LED de 5 mm de 20 mA, como ya hacemos.
- **Capacitores electrolíticos:** son lo primero que falla. Hay que usar de **105 °C y larga vida**. Cada 10 °C menos duplican su vida.
- **LED de potencia** (focos, COB): **placa de aluminio (MCPCB)** y disipador. JLCPCB también las fabrica.
- **Validación:** medir la temperatura con termopar en las primeras piezas y hacer una prueba de 72 h encendido antes de entregar.

**Normas en México (a verificar con un especialista antes de vender):**
- Lámparas y focos LED: NOM-030-ENER, de eficacia.
- Seguridad eléctrica de productos conectados a 127 V: NOM-001-SCFI.

Nuestra placa base de 12 V con eliminador ya certificado simplifica mucho este punto. Por eso conviene **preferir 12 V aislado** para productos de venta.

## Logística e importación (JLCPCB → México)

- Los pedidos llegan por paquetería (DHL, FedEx) en unos 5–10 días.
- Al recibir se paga **IVA 16 %** y, según el monto y el tipo de envío, un **arancel o tasa global**. Conviene **confirmar con la paquetería o un agente aduanal** la fracción arancelaria. Como referencia: placas sin componentes, 8534; módulos de control armados, 8537; lámparas LED, 8539.
- Para volumen: juntar pedidos (placas + ensamble + plantillas) en un solo envío y guardar facturas para deducir.

## Cómo trabajamos día a día

1. Cada cambio queda en este repositorio: diagramas KiCad, programa, 3D y documentos.
2. Cada versión lleva número (v1.1, v1.2…) en la placa y en el programa.
3. Cada prueba real (qué funcionó y qué falló) se anota, y la siguiente versión la corrige.
