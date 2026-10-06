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
| **AP CORE** | Programación local: horarios, escenas, secuencias | `ap1-prog`: ESP32-C3, horarios, 10 modos, escenas, grupos, OTA, etiquetas por circuito; funciona sin internet | Diseñado; programa 1.6 |
| **AP INPUT** | Pulsadores y sensores | **`ap1-in` (nuevo):** 8 entradas de 12-24 V aisladas, con reglas por entrada | Diseñado |
| **AP OUTPUT** | Actuadores, relevadores, contactores | **`ap1-out` (nuevo):** 7 salidas de 24 V DC (300 mA) para bobinas y válvulas | Diseñado |
| **AP LIGHT** | Iluminación según el driver o foco | `ap1-pix` (pixeles), `ap1-dmx` (DMX512), `ap1-ind` (0-10 V aislado), corriente constante en la base | Diseñados |
| **AP METER** | Medición y diagnóstico | Medidor INA238 en la base: V, A, W, kWh, diagnóstico por salida | Dentro de la base; módulo propio pendiente |
| **AP LINK** | Ethernet, Wi-Fi, inalámbrico | Wi-Fi en el CORE | Ethernet pendiente |
| **AP GATE** | PLC, aplicaciones, otros ecosistemas | MQTT, **Home Assistant**, API HTTP, **Art-Net/sACN** | En el programa; Modbus/RS-485 pendiente |
| **AP FIELD** | Gabinete para exteriores | `ap1-gabinete`: gabinete imprimible para interior y **soporte DIN** | Exterior pendiente (junta, prensaestopas, UV, condensación y pruebas IP) |

## Líneas de producto

| Línea | Para quién | Qué la forma hoy | Lo que falta |
|---|---|---|---|
| **AP CASA**: control y automatización del hogar | Casas, departamentos, negocios pequeños | CORE + **BASE 4** (`ap1-base`: 4 circuitos de LED de 12-24 V) + AP INPUT (apagadores y sensores) + AP OUTPUT. **BASE 8** = BASE 4 + AP OUTPUT, o dos BASE | Caja de escritorio o pared con **etiquetas por circuito** (ya en el programa) y tapas de colores |
| **AP PRO**: control y E/S para proyectos exigentes | Talleres, bombeo, riego, naves | **DI8** = AP INPUT (`ap1-in`); **DO8** = AP OUTPUT (`ap1-out`, hoy 7 salidas); 0-10 V aislado = `ap1-ind` | **AI4** (entradas analógicas 0-10 V / 4-20 mA), bornes enchufables, RS-485/Modbus |
| **AP FIT**: accesorios para instalar | Instaladores | Soporte DIN imprimible (`ap1-gabinete/din`), guías de cableado por módulo | Kit físico: conectores, punteras, clips DIN, prensaestopas, portafusibles |
| **AP SIGN**: letras luminosas, cajas de luz, neón LED | Letreros | BASE (canales de 8 A, efectos), **PIX** (pixeles), **DMX**, **DIST 4** (nuevo: 4 ramas protegidas con diagnóstico) | "SIGN COLOR" como módulo dedicado (hoy: PIX o DMX con decodificador) |

### AP CASA y la red de la casa (seguridad)

Los circuitos de la propuesta (SALA, COCINA, ENTRADA, PATIO) **no pueden ser circuitos de 127 V dentro de la caja AP CASA**. Las placas siguen sin llevar tensión de red. Hay dos formas seguras:

1. **Iluminación LED de 12/24 V** (tiras, empotrados, perfiles): BASE 4 las maneja directo, cada canal con su etiqueta.
2. **Focos y contactos de 127 V:** AP OUTPUT manda **relevadores o contactores de riel DIN certificados** en el centro de carga, instalados por un electricista. La caja AP CASA solo lleva 24 V DC.

### Control ≠ Potencia (AP FIT)

- **Idea de la propuesta:** conectores de control pequeños y conectores de potencia más grandes y de **otra forma**, para que **no se puedan cruzar**. Es una buena regla.
- **Hoy:** todas las placas usan bornes de tornillo de 5.08 mm (y de 3.5 mm en la base). Las tensiones están separadas por placa, pero el conector es el mismo.
- **Siguiente versión:** bornes **enchufables**, que se desconectan para dar servicio sin quitar los cables:
  - control en paso de 3.5 mm, color verde;
  - potencia en paso de 5.08/7.62 mm, en otro color y con codificación mecánica.

  Hace falta elegir la pieza con su hoja de datos y su código LCSC.

### Mantenimiento sencillo

| Propuesta | Estado |
|---|---|
| Borneras extraíbles para servicio | Pendiente (ver Control ≠ Potencia) |
| Etiquetas por circuito | **Hecho en el programa 1.6:** `ET S3 Cocina` o desde la app; salen en Home Assistant |
| Tapas mate reemplazables | Gabinete imprimible; tapas de color: pendiente |
| Diagnóstico | Medición y prueba de salidas en la BASE; ramas y fusibles en la DIST 4; LED RUN en AP OUTPUT |

### "AP BUS"

En el diagrama de la propuesta, el **AP BUS** une el CORE con los módulos. Hoy son dos cosas:
- el conector LL 2×8 para el módulo de potencia;
- el **bus Qwiic (I2C)** para AP INPUT, AP OUTPUT y DIST 4, en el mismo tablero.

Para módulos a más de 1 m o en otro tablero, el AP BUS tendría que pasar a **RS-485**.

## Primer prototipo recomendado: AP BASE DC + AP CORE + AP INPUT + AP OUTPUT

```
 Fuente DIN 24 V ──┬──► AP BASE (ap1-base) ── luces LED de 24 V (canales 1-4)
                   │        ▲ zócalo LL 2x8
                   │     AP CORE (ap1-prog) ── Wi-Fi, app, horarios
                   │        │ cable Qwiic (I2C, 3.3 V)
                   │     AP INPUT (ap1-in, 0x24) ◄── pulsador (I1), flotador (I2), sensor de presencia (I3)
                   │        │ cable Qwiic
                   └──► AP OUTPUT (ap1-out, 0x20) ──► Q1: electroválvula 24 V DC
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
| **Qwiic (I2C)** | Módulos de E/S en cadena: AP INPUT, AP OUTPUT y DIST 4 | Hasta 4 en el rango de entradas (0x24-0x27: AP INPUT o DIST 4) y 4 de salidas (0x20-0x23). Cable total **corto**: 1 m como máximo, lejos de cables de potencia |
| **Wi-Fi** | Entre equipos y con apps | Grupos, MQTT, Home Assistant, Art-Net |

## Montaje en riel DIN

- `ap1-gabinete/din/soporte_din_88x56.stl` y `soporte_din_72x56.stl`: charola con insertos M3, gancho arriba y seguro flexible abajo, para riel TS35.
- Las placas de 72 mm ocupan 4 módulos DIN de ancho.
- **Prototipo:** imprime uno y pruébalo con un tramo de riel antes de imprimir en serie.

## Carcasas personalizables (propuesta)

- Mismo soporte y misma tapa en **grafito, blanco, verde, azul y naranja**, con placa de identificación intercambiable.
- Las **etiquetas eléctricas** (bornes, tensiones, advertencias) van **grabadas o impresas de forma permanente**, del mismo color neutro en todas las versiones, para que se lean siempre.

## Lo que falta para acercarse a "tipo PLC"

1. **Fabricar y probar** el primer prototipo, con las pruebas de cada guía.
2. **Ciclo de prueba en tablero:** ruido de contactores, temperatura y horas encendido.
3. **Salidas con protección contra cortos:** cambiar el ULN2003 por MOSFET de 40-60 V con limitación, en cuanto se confirme una pieza con hoja de datos.
4. **Comportamiento ante fallas definido:** qué hacen las salidas si el CORE se reinicia (hoy se quedan como estaban; se puede agregar un vigilante por hardware).
5. **Bus para distancias mayores:** RS-485 (AP LINK) en lugar de I2C cuando los módulos estén en otro tablero.
6. **AP FIELD para exteriores:** diseño de caja con junta, pruebas de agua y polvo, y manejo de condensación, antes de declarar una clasificación IP.
7. **Certificación:** lo que aplique en México para equipos de control de baja tensión, con un laboratorio.

## Nota sobre el nombre

Las placas nuevas (AP INPUT, AP OUTPUT y AP SIGN DIST 4) ya llevan **AP ELECTRIC** en la serigrafía. Las anteriores conservan el nombre LetreroLab y se pueden cambiar todas juntas cuando la marca quede definida.
