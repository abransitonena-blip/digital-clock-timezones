# Ecosistema LetreroLab AP-1: un programador, módulos para cada tipo de luz

**Idea:** un solo **programador** (el cerebro, con Wi-Fi) y **módulos de potencia** intercambiables (los músculos).
Todos los módulos tienen:
- la misma medida, 88 × 56 mm;
- el mismo **conector LL de 16 patas**;
- los mismos agujeros;
- una **memoria de identidad**.

El programador se enclava en cualquiera de ellos, lee la memoria y **sabe solo qué módulo tiene debajo**. No hay que configurar nada.

```
                 ┌─────────────────────────────┐
                 │  PROGRAMADOR AP-1 (ESP32-C3) │  Wi-Fi, app, horarios, Home Assistant, MQTT, IR, OTA
                 └──────────────┬──────────────┘
                     conector LL 2x8: enclavado (11 mm) o cable plano IDC de hasta 1 m
        ┌───────────────────────┼────────────────────────┐
┌───────┴────────┐     ┌────────┴────────┐      ┌────────┴────────┐
│ AP-1 BASE      │     │ AP-1 IND        │      │ (próximos)      │
│ 4 x 8 A PWM    │     │ 4 x 0-10 V      │      │ PIXEL, DALI,    │
│ 2 x 1 A CC     │     │   aislados      │      │ RS-485, CC 60 V │
│ AUX 12 V       │     │ 2 contactores   │      │                 │
└────────────────┘     └─────────────────┘      └─────────────────┘
```

## Qué módulo usar con cada luz

| Tipo de luz | Ejemplos | Módulo | Qué hace la placa |
|---|---|---|---|
| **Letreros y tiras LED de 12/24 V** | letreros de acrílico, tiras, módulos LED, flechas secuenciales, RGBW | **BASE** | Conmuta el negativo de cada canal con MOSFET (8 A c/u, 20 A en total), con efectos y secuencias |
| **Focos LED de corriente constante** | COB, LED de 1-3 W en serie, reflectores sin driver | **BASE** (salidas CC) | Da 1 A constante y atenuable a cada foco, sin driver externo |
| **Luces de red de 127/240 V, solo encender y apagar** | focos normales, lámparas, letreros con su propia fuente | **IND** (o el AUX de la BASE) | Mueve la **bobina** de un contactor o relevador de estado sólido de riel DIN certificado, con horarios, app y Home Assistant |
| **Naves industriales y oficinas** | campanas LED, paneles, reflectores con driver **dimeable 0-10 V / 1-10 V** | **IND** | Atenúa hasta 4 grupos de drivers por 0-10 V aislado, y enciende o apaga su alimentación con el contactor |
| **Todo en una sola placa, sin módulos** | letrero sencillo con relevador | **AP-0.2** | Placa única de 90 × 70 mm |
| **Letreros de pixeles (WS2812/SK6812)** | animaciones, texto que corre | *PIXEL (propuesto)* | 4 salidas de datos a 5 V con buffer y fusibles |
| **Sistemas DALI** | edificios con DALI | *DALI (propuesto)* | Bus DALI aislado |

## Cómo se conectan

1. **Enclavado:** el programador va encima del módulo con separadores de 11 mm y tornillo de nylon. Entra en el gabinete `ap1-gabinete`, que sirve para la BASE y para el IND.
2. **Con cable:** cable plano **IDC de 16 hilos** (2×8, paso de 2.54 mm) de hasta **1 m**. El programador puede ir en el frente de un tablero o junto a la ventana para mejor Wi-Fi, y el módulo junto a la fuente.
3. **Sin cables, entre equipos:** cada programador maneja su módulo. Varios equipos se coordinan por **grupos de Wi-Fi** (`G grupo` y `@grupo orden`), por **MQTT** o por **Home Assistant**. Ejemplo: toda una nave encendiendo al mismo tiempo, o letreros en secuencia por grupos.
4. **Encontrarlo:** cada equipo se anuncia en la red como `nombre.local` y responde a `?` con su estado y su **tipo de módulo** (`"ind":1` y `"base":{"mod":"LL-IND"}`). En Home Assistant aparece solo, con las entidades que corresponden a su módulo.

### Conector LL (igual en todos los módulos)

| Pata | Señal | Pata | Señal |
|---|---|---|---|
| 1, 2 | +12 V del módulo al programador | 3, 4, 16 | GND |
| 5-8 | PWM 1-4 (BASE: MOSFET · IND: 0-10 V) | 9, 10 | CTRL 1-2 (BASE: focos CC · IND: contactor 2) |
| 11, 12 | SDA, SCL (memoria y sensores) | 13 | ALERTA (corte por hardware en la BASE) |
| 14 | AUX (BASE: relevador · IND: contactor 1) | 15 | 3.3 V del programador a los sensores |

### Cómo sabe el programador qué módulo tiene

- La memoria de 256 bytes (M24C02, dirección 0x50) guarda `"LL"`, la versión, el **modelo**, el número de serie, las horas de uso y la calibración.
- Un módulo nuevo se formatea solo la primera vez:
  - si tiene medidor de corriente (INA238), es una BASE: `AP-1 universal`;
  - si no lo tiene, es un IND: `LL-IND`.
- Con `MODELO texto` se puede poner el modelo a mano. Lo que empieza con `LL-IND` activa el modo industrial.

## Reglas de seguridad del ecosistema (no cambian)

1. **La red de 127/240 V no entra a ninguna placa LetreroLab.** Las luces de red se encienden con un **contactor o relevador de estado sólido de riel DIN certificado**, instalado por un electricista. La placa solo mueve la bobina de 12-24 V.
2. **Todo lo que entra a las placas es 12-24 V DC** (máximo 26 V), de una fuente certificada.
3. **Las líneas de atenuación 0-10 V van aisladas**: optoacopladores de 3 kV y convertidor de 1.5 kV, con franja de 3 mm sin cobre. Úsalas solo con drivers cuya entrada de atenuación sea de baja tensión aislada (SELV o "Class 2"), como piden las normas de los drivers.
4. **Protección por hardware:** en la BASE, sobrecorriente, sobrevoltaje y 85 °C apagan los MOSFET aunque el programa falle.

## Ejemplo: nave industrial con 24 campanas LED dimeables

```
  Tablero:  interruptor termomagnético ──► CONTACTOR (bobina 24 V DC) ──► drivers de las campanas (127/220 V)
                                               ▲ bobina
  Fuente DIN 24 V ──► AP-1 IND ── K1 ──────────┘
                         │
                         ├── 0-10 V canal 1 ──► DIM+/DIM- de las 8 campanas del pasillo 1
                         ├── 0-10 V canal 2 ──► DIM+/DIM- de las 8 campanas del pasillo 2
                         └── 0-10 V canal 3 ──► DIM+/DIM- de las 8 campanas del área de carga
```

- **Horarios:** 6:00 al 100 %, 22:00 al 30 %, 23:00 apagado (el contactor abre).
- **Luz natural:** con el sensor de luz Qwiic (BH1750), atenúa cuando entra el sol.
- **Home Assistant:** encender, apagar y atenuar desde el tablero de control de la planta.
- **Cuántas campanas por canal:** cada salida da o absorbe hasta 10 mA. Con drivers típicos (0.1-1 mA cada uno) caben de 10 a 50 drivers por canal. Revisa la corriente de atenuación en la hoja del driver.

## Módulos propuestos (no diseñados todavía)

| Módulo | Para qué | Idea de circuito |
|---|---|---|
| **PIXEL** | Letreros de pixeles WS2812/SK6812 a 5, 12 o 24 V | PWM 1-4 como datos (RMT del ESP32-C3), buffer 74AHCT1G125 a 5 V por salida, fusible por salida, como el QuinLED Dig-Quad |
| **DALI** | Edificios con drivers DALI | Fuente de bus DALI de 16 V limitada a 250 mA y transceptor aislado con optoacopladores |
| **RS-485** | Módulos a cientos de metros con cable de red (CAT5) | Extensor del conector LL por RS-485 (Modbus RTU) con autodescubrimiento por dirección |
| **CC 60 V** | Focos de corriente constante con más LED en serie | AL8862 (60 V, 1 A) en lugar del AL8860 (42 V) |

Cada uno se diseña con la misma librería (`tools/placa.py`), la misma medida, el mismo conector y la misma memoria. Así el programador y el gabinete siguen siendo los mismos.
