# AP ELECTRIC: «Una base. Muchas posibilidades.» · Instala. Identifica. Mantén. Amplía.

Este documento conecta la propuesta de marca **AP ELECTRIC** con lo que ya está diseñado en este repositorio.

> **Estado:** propuesta y primer prototipo. Todas las placas pasan las revisiones de diseño (ERC/DRC 0 y reglas de JLCPCB), pero **ninguna se ha fabricado ni probado todavía**. No hay prestaciones ni certificaciones comprobadas. La resistencia al agua (IP) no se declara hasta probar el conjunto completo.

## La idea

- **La base se queda instalada; los módulos amplían sus funciones.**
- Lo universal es la **interfaz entre módulos**, la **programación** y el **formato**. La **potencia** tiene variantes según la carga.
- **Para México:**
  - mando a **24 V DC**;
  - app y documentación en español;
  - funciona **sin internet**: tiene su propia red Wi-Fi de configuración, horarios con reloj propio (DS3231 opcional) y órdenes por la red local;
  - montaje en **riel DIN**.
- **Seguridad, que no cambia:** la red de 127/220 V no entra a ninguna placa. Las cargas de red se mandan con contactores o relevadores de estado sólido de riel DIN certificados.

## Familias: de la propuesta al hardware

| Familia | Función | Qué existe hoy | Estado |
|---|---|---|---|
| **AP BASE** | Potencia y protecciones propias, sin Wi-Fi | `ap1-base`: 12-24 V, 4 canales de 8 A, 2 focos de corriente constante, AUX; corte por hardware ante sobrecorriente, sobrevoltaje y 85 °C | Diseñada (4 capas) |
| **AP CORE** | Programación local: horarios, escenas, secuencias | `ap1-prog`: ESP32-C3, horarios, 10 modos, escenas, grupos, OTA, etiquetas por circuito; funciona sin internet | Diseñado; programa 2.0 |
| **AP INPUT** | Pulsadores y sensores | **`ap1-in`:** 8 entradas de 12-24 V aisladas, con reglas por entrada. **`ap1-ai4`:** 4 entradas analógicas 0-10 V / 4-20 mA con umbrales | Diseñados |
| **AP OUTPUT** | Actuadores, relevadores, contactores | **`ap1-out` = AP PRO DO8:** 8 salidas de 24 V DC **protegidas** (NCV8406A: 1.5 A por salida, corto y temperatura) para bobinas y válvulas | Diseñado (reemplaza a la versión de 7 salidas con ULN2003) |
| **AP LIGHT** | Iluminación según el driver o foco | **`ap1-pwm4`** (4 × 6 A atenuables de 12-24 V, aislado), **`ap1-ao4`** (4 circuitos 0-10 V + contactor), `ap1-pix` (pixeles), `ap1-dmx` (DMX512), `ap1-ind` (0-10 V aislado), corriente constante en la base; **horario solar** en el programa 2.0 | Diseñados |
| **AP METER** | Medición y diagnóstico | Medidor INA238 en la base: V, A, W, kWh, diagnóstico por salida | Dentro de la base; módulo propio pendiente |
| **AP LINK** | Ethernet, Wi-Fi, inalámbrico, bus de campo | Wi-Fi en el CORE; **AP NODE** (`ap1-node`) con **AP BUS 24 V + CAN** para nodos remotos ([AP_BUS.md](AP_BUS.md)) | AP NODE diseñado; Ethernet pendiente |
| **AP GATE** | PLC, aplicaciones, otros ecosistemas | MQTT, **Home Assistant**, API HTTP, **Art-Net/sACN**; placa **`ap1-gate`**: RS-485 / **Modbus RTU** (medidores de energía, variadores, PLC) + AP BUS | Diseñada; programa 2.0 |
| **AP FIELD** | Gabinete para exteriores | `ap1-gabinete`: gabinete imprimible para interior y **soporte DIN** | Exterior pendiente (junta, prensaestopas, UV, condensación y pruebas IP) |

## Líneas de producto

| Línea | Para quién | Qué la forma hoy | Lo que falta |
|---|---|---|---|
| **AP CASA**: control y automatización del hogar | Casas, departamentos, negocios pequeños | CORE + **BASE 4** (`ap1-base`: 4 circuitos de LED de 12-24 V) + AP INPUT (apagadores y sensores) + DO8. **BASE 8** = BASE 4 + DO8, o dos BASE | Caja de escritorio o pared con **etiquetas por circuito** (ya en el programa) y tapas de colores |
| **AP PRO**: control y E/S para proyectos exigentes | Talleres, bombeo, riego, naves | **DI8** = AP INPUT (`ap1-in`); **DO8** = AP PRO DO8 (`ap1-out`, 8 salidas protegidas); 0-10 V aislado = `ap1-ind` | **AI4 hecho** (`ap1-ai4`: 0-10 V / 4-20 mA con umbrales); **Modbus RTU hecho** (`ap1-gate`) |
| **AP FIT**: accesorios para instalar | Instaladores | Soporte DIN imprimible (`ap1-gabinete/din`), guías de cableado por módulo | Kit físico: conectores, punteras, clips DIN, prensaestopas, portafusibles |
| **AP SIGN**: letras luminosas, cajas de luz, neón LED | Letreros | BASE (canales de 8 A, efectos), **PIX** (pixeles), **DMX**, **DIST 4** (4 ramas protegidas con diagnóstico), **PWM4** (más canales de potencia), horario solar | "SIGN COLOR" como módulo dedicado (hoy: PIX o DMX con decodificador) |
| **AP LIGHT**: alumbrado | Alumbrado público y de estacionamientos, naves, bodegas, fachadas, oficinas | **AO4** (luminarias de red con driver 0-10 V + contactor), **PWM4** (luminarias LED de 24 V), **horario solar** (ocaso/amanecer sin fotocelda), medidor de energía por Modbus (AP GATE) | DALI (pendiente: necesita fuente de bus DALI) |
| **AP LINK / GATE**: comunicación | Varios tableros, equipos de terceros | **AP NODE** (AP BUS 24 V + CAN), **AP GATE** (+ RS-485 Modbus RTU), Wi-Fi, MQTT, Home Assistant | Ethernet |

## Modelos: combinaciones listas por rama

Cada modelo es una lista de placas que se piden juntas y se programan igual.
- **Lo que va en la placa:** solo 12-24 V DC.
- **La red:** la conmutan aparatos certificados de riel DIN. Cuáles y cómo se dimensionan: [ACTUADORES_DE_POTENCIA.md](ACTUADORES_DE_POTENCIA.md).

### Hogar (AP CASA)

| Modelo | Placas | Para |
|---|---|---|
| **CASA 4 LED** | CORE + BASE | 4 circuitos de iluminación LED de 12-24 V con atenuación, escenas y horarios |
| **CASA 8 RED** | CORE + DO8 + AP INPUT + 8 contactores modulares | Focos y contactos de 127 V por contactor; apagadores de 24 V en la pared |
| **CASA CLIMA** | CORE + DO8 + AI4 | Ventiladores, extractores y calentador por temperatura (transmisor 0-10 V) |

### Industrial (AP PRO)

| Modelo | Placas | Para |
|---|---|---|
| **PRO BOMBEO** | GATE + AI4 + DO8 + AP INPUT | Cisterna y tinaco: nivel 4-20 mA → bomba por contactor; flotador y térmico como entradas; variador o medidor por Modbus |
| **PRO NAVE** | GATE + AO4 + DO8 + AP INPUT | Alumbrado atenuable de la nave, extractores, sensores de presencia y medición de energía por Modbus |
| **PRO ENERGÍA** | GATE + DO8 | Medidores Modbus; con umbrales (`MU`) se desconectan cargas cuando la demanda pasa del límite |
| **PRO REMOTO** | NODE (maestro) + NODE por tablero + DO8 / AP INPUT | Entradas y salidas en varios tableros, hasta 250 m, con un solo cable |

### Letreros (AP SIGN)

| Modelo | Placas | Para |
|---|---|---|
| **SIGN LETRAS** | CORE + BASE (o + PWM4) + DIST 4 | Letras corpóreas y cajas de luz por canales, con efectos y ramas protegidas |
| **SIGN PIXEL** | CORE + PIX + DIST 4 | Letras en secuencia y animaciones con pixeles direccionables |
| **SIGN SHOW** | CORE + DMX (o PIX) | Reflectores RGB/RGBW y control en vivo con Art-Net/sACN (xLights, QLC+) |

Todos los letreros pueden encender al **ocaso** y apagar a una hora fija o al **amanecer** (horario solar, sin fotocelda).

### Alumbrado (AP LIGHT)

| Modelo | Placas | Para |
|---|---|---|
| **LIGHT CALLE** | GATE + AO4 + contactores AC-5b + supresor de picos | Alumbrado público, privadas y estacionamientos: enciende al ocaso, baja al 50 % a media noche, apaga al amanecer; consumo medido por Modbus |
| **LIGHT NAVE** | CORE + AO4 (hasta 4 = 16 circuitos) | Naves y bodegas con luminarias de red atenuables 0-10 V |
| **LIGHT DC** | CORE + PWM4 (hasta 4 = 16 canales) | Luminarias, reflectores y tiras de 24 V DC, hasta 20 A por PWM4 |
| **LIGHT FACHADA** | CORE + PWM4 o DMX + horario solar | Iluminación arquitectónica con escenas y colores |

### AP CASA y la red de la casa (seguridad)

Los circuitos de la propuesta (SALA, COCINA, ENTRADA, PATIO) **no pueden ser circuitos de 127 V dentro de la caja AP CASA**. Las placas siguen sin llevar tensión de red. Hay dos formas seguras:

1. **Iluminación LED de 12/24 V** (tiras, empotrados, perfiles): BASE 4 las maneja directo, cada canal con su etiqueta.
2. **Focos y contactos de 127 V:** el DO8 manda **relevadores o contactores de riel DIN certificados** en el centro de carga, instalados por un electricista. La caja AP CASA solo lleva 24 V DC.

### Control ≠ Potencia (AP FIT)

- **Idea de la propuesta:** conectores de control pequeños y conectores de potencia más grandes y de **otra forma**, para que **no se puedan cruzar**. Es una buena regla.
- **Hecho: AP CONNECT.** Ya no hay borneras de tornillo. Todo se conecta con cables armados, de familias que no se pueden cruzar:

| Familia | Uso | Paso / corriente |
|---|---|---|
| **Qwiic** (JST SH) | Bus I2C entre CORE y módulos | 1.0 mm |
| **JST XH** 2-4 patas | Control: entradas, salidas de 24 V, 0-10 V, DMX, sensores, focos de 1 A | 2.5 mm, 3 A |
| **JST VH** 2-4 patas | Potencia: canales, pixeles, ramas, entradas de módulos | 3.96 mm, 10 A por pata |
| **XT60** | Entrada de mucha corriente (DIST 4) | 30 A |

  Todos tienen seguro o forma con polaridad y código LCSC. Detalle en `tools/conectores.py` y [FABRICANTES.md](FABRICANTES.md).

### Mantenimiento sencillo

| Propuesta | Estado |
|---|---|
| Borneras extraíbles para servicio | **Hecho:** conectores con cable (AP CONNECT): se desconecta el cable y sale la placa |
| Etiquetas por circuito | **Hecho en el programa 1.6:** `ET S3 Cocina` o desde la app; salen en Home Assistant |
| Tapas mate reemplazables | Gabinete imprimible; tapas de color: pendiente |
| Diagnóstico | Medición y prueba de salidas en la BASE; ramas y fusibles en la DIST 4; protección propia por salida en el DO8 |

### "AP BUS"

El **AP BUS** ya existe: **24 V DC + CAN** a 250 kbit/s en un cable de 4 hilos, hasta 250 m (especificación en [AP_BUS.md](AP_BUS.md)).
- En el **mismo tablero** siguen el conector LL 2×8 (módulo de potencia) y el **Qwiic** (DO8, AP INPUT, AI4, DIST 4).
- **En otro tablero o a más de 1 m:** un **AP NODE** (`ap1-node`) en cada punto, con sus módulos por Qwiic. El maestro ve sus entradas y salidas como propias (S33-S128, E33-E128).
- Si un nodo pierde al maestro, **apaga sus salidas en 1 s** (falla segura).
- Se eligió CAN y no RS-485 por el arbitraje y la verificación por hardware, y porque el ESP32-C3 ya trae el controlador.

## Primer prototipo recomendado: AP BASE DC + AP CORE + AP INPUT + AP PRO DO8

```
 Fuente DIN 24 V ──┬──► AP BASE (ap1-base) ── luces LED de 24 V (canales 1-4)
                   │        ▲ zócalo LL 2x8
                   │     AP CORE (ap1-prog) ── Wi-Fi, app, horarios
                   │        │ cable Qwiic (I2C, 3.3 V)
                   │     AP INPUT (ap1-in, 0x24) ◄── pulsador (I1), flotador (I2), sensor de presencia (I3)
                   │        │ cable Qwiic
                   └──► AP PRO DO8 (ap1-out, 0x20) ──► Q1: electroválvula 24 V DC
                                                     Q2: bobina de contactor ──► bomba 127/220 V (lado de red: contactor)
```

**Programación de la demostración** (en la app, o por órdenes):

| Orden | Qué hace |
|---|---|
| `EA 1 8 0` | El pulsador I1 enciende y apaga las luces |
| `EA 2 5 1 1` | Mientras el flotador I2 esté activo, la válvula Q1 está abierta |
| `EA 3 1 0 1` | Mientras haya presencia en I3, las luces encienden |
| `A 0 127 07:00 5 2` | Todos los días a las 7:00 enciende la bomba (Q2) |
| `A 1 127 07:30 6 2` | A las 7:30 la apaga |

Todo funciona **sin internet**. Con Wi-Fi, además aparece en Home Assistant: luz, entradas, salidas y medición.

## Cómo se conectan los módulos

| Enlace | Para qué | Detalle |
|---|---|---|
| **Conector LL 2×8** | CORE sobre un módulo de potencia (BASE, IND, PIX, DMX) | Uno por CORE; el módulo se identifica con su memoria |
| **Qwiic (I2C)** | Módulos de E/S en cadena: AP INPUT, DO8, AI4 y DIST 4 | Hasta 4 en el rango de entradas (0x24-0x27: AP INPUT o DIST 4) y 4 de salidas (0x20-0x23). Cable total **corto**: 1 m como máximo, lejos de cables de potencia |
| **AP BUS (24 V + CAN)** | Nodos remotos AP NODE en otro tablero, hasta 250 m | 1 maestro + 3 nodos; falla segura en 1 s. Ver [AP_BUS.md](AP_BUS.md) |
| **Wi-Fi** | Entre equipos y con apps | Grupos, MQTT, Home Assistant, Art-Net |

## Montaje en riel DIN

- `ap1-gabinete/din/soporte_din_88x56.stl` y `soporte_din_72x56.stl`: charola con insertos M3, gancho arriba y seguro flexible abajo, para riel TS35.
- Las placas de 72 mm ocupan 4 módulos DIN de ancho.
- **Prototipo:** imprime uno y pruébalo con un tramo de riel antes de imprimir en serie.

## Carcasas personalizables (propuesta)

- Mismo soporte y misma tapa en **grafito, blanco, verde, azul y naranja**, con placa de identificación intercambiable.
- Las **etiquetas eléctricas** (conectores, tensiones, advertencias) van **grabadas o impresas de forma permanente**, del mismo color neutro en todas las versiones, para que se lean siempre.

## Lo que falta para acercarse a "tipo PLC"

1. **Fabricar y probar** el primer prototipo, con las pruebas de cada guía.
2. **Ciclo de prueba en tablero:** ruido de contactores, temperatura y horas encendido.
3. **Salidas con protección contra cortos:** cambiar el ULN2003 por MOSFET de 40-60 V con limitación, en cuanto se confirme una pieza con hoja de datos.
4. **Comportamiento ante fallas definido:** qué hacen las salidas si el CORE se reinicia (hoy se quedan como estaban; se puede agregar un vigilante por hardware).
5. **Bus para distancias mayores:** RS-485 (AP LINK) en lugar de I2C cuando los módulos estén en otro tablero.
6. **AP FIELD para exteriores:** diseño de caja con junta, pruebas de agua y polvo, y manejo de condensación, antes de declarar una clasificación IP.
7. **Certificación:** lo que aplique en México para equipos de control de baja tensión, con un laboratorio.

## Nota sobre el nombre

Las placas nuevas (AP INPUT, DO8, AI4, AP NODE y AP SIGN DIST 4) ya llevan **AP ELECTRIC** en la serigrafía. Las anteriores conservan el nombre LetreroLab y se pueden cambiar todas juntas cuando la marca quede definida.
