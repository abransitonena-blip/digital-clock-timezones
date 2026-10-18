# AP LINK v1: enlace entre módulos AP Electric (estilo DMX)

> **Estado: CONCEPTO, probado solo en simulación en la PC** (`firmware/pruebas/prueba_link.cpp`, 83 comprobaciones; `prueba_rack.cpp`). Nada se ha probado con placas ni con cable real.

Une varios módulos en cadena: un cable de un módulo al siguiente. Los módulos se **numeran solos según el cable** (sin interruptores de dirección), el primero manda (**cabeza**) y el panel o la consola muestran todos como un solo equipo: «Módulo 1, Módulo 2…» con las salidas contadas seguidas (la salida 1 del módulo 2 es el canal 17).

## Capa física

| | |
|---|---|
| Datos | RS-485 de 2 hilos (A, B) a 250 kbit/s, 8N1: la velocidad de DMX512, pero con protocolo propio (no es DMX) |
| Conector | JST XH de 4 patas, **dos por módulo: ENTRA y SIGUE**, con A, B y 0 V unidos en la placa (como el THRU de DMX). Cable 1 a 1 |
| Patas | **1 = SENSE · 2 = B (D−) · 3 = A (D+) · 4 = 0 V**. Adaptador a XLR de 3 patas: 1 = malla (0 V), 2 = D−, 3 = D+ |
| SENSE | No se une entre ENTRA y SIGUE: la pata de ENTRA es la entrada (`SENSE_IN`) y la de SIGUE la salida (`SENSE_OUT`) que maneja el microcontrolador |
| Transceptor | SP3485 a 3.3 V, **sin aislar**: todos los módulos comparten el 0 V por el cable. Diferencia de tierras máxima de diseño ±7 V; para fuentes separadas o tableros distintos hace falta una versión aislada (**pendiente**, ver abajo) |
| Terminación | 120 Ω (puente JP1) **solo en el último módulo**. Polarización 680 Ω (JP2 y JP3) **solo en el primero** |
| Alcance | Meta de diseño: 16 módulos y decenas de metros de par trenzado; sin medir |

**No conectar un cable de AP BUS** (24 V + CAN, también JST XH de 4 patas) a un conector AP LINK: la pata 1 de AP BUS es +24 V y en AP LINK es SENSE. La placa limita la corriente con 10 kΩ en `SENSE_IN` y 1 kΩ en `SENSE_OUT`, lo que **no garantiza** que sobreviva. Se rotula en la placa y se usan carcasas de otro color.

### SENSE: cómo saben el orden

- `SENSE_OUT` tiene 10 kΩ a 0 V: sin programa o sin energía vale 0.
- `SENSE_IN` tiene 100 kΩ a 3.3 V: sin cable (el primero de la cadena) vale 1.
- Un módulo sube `SENSE_OUT` solo **cuando ya tiene dirección**; así el siguiente de la cadena queda habilitado para contestar a la enumeración y los de atrás siguen mudos.

## Capa de enlace

Trama: `A5 · destino · origen · tipo · n · datos… · CRC16 (bajo, alto)` (CRC de Modbus sobre destino…datos). El receptor se resincroniza al siguiente `A5` si el CRC falla.

| Tipo | Quién | Qué |
|---|---|---|
| 1 BALIZA | cabeza → todos, cada 500 ms | uid del cabeza, cuántos módulos hay, prioridad, versión |
| 2 ENUM | cabeza → todos | «¿quién sigue?» (cada 30 ms al formar la cadena, cada 1 s después, para detectar módulos nuevos) |
| 3 HOLA | módulo habilitado por SENSE | su uid y capacidades (tipo, salidas, entradas, analógicas, salidas con brillo) |
| 4 ASIGNA | cabeza | uid + dirección + uid del cabeza |
| 5 ACK | módulo | confirma; sube `SENSE_OUT` |
| 6 POLL | cabeza → módulo | máscara de salidas (16 bits), un byte reservado y, si el módulo tiene PWM, un brillo 0-255 por salida con PWM |
| 7 ESTADO | módulo → cabeza | entradas, salidas aplicadas, fallas, tensión de entrada (mV), bandera «perdí el enlace» |
| 8 RESET | cabeza → todos | los módulos de ese cabeza vuelven a ESPERA |

Cada módulo se consulta cada 50 ms (con 16 módulos, una trama cada 5 ms).

## Tipos de módulo (se anuncian en la enumeración)

| Tipo | Módulo | Salidas | Entradas | Analógicas |
|---|---|---|---|---|
| 1 | [AP Rack 16](rack16/LEEME.md) | 16 | 8 | 0 |
| 2 | [AP Rack IN16](in16/LEEME.md) | 0 | 16 | 0 |
| 3 | [AP Rack AI8](ai8/LEEME.md) | 0 | 0 | 8 (mV o µA, según el canal) |
| 4 | [AP Rack LED8](led8/LEEME.md) | 8 (con brillo PWM) | 8 | 0 |
| 5 | [AP Rack RL4](rl4/LEEME.md) | 4 (relés secos de 24 V) | 8 | 0 |
| 6 | [AP Rack AO4](ao4/LEEME.md) | 4 (nivel 0-255 = 0-10 V) | 8 | 0 |
| 7 | [AP PLC C24](plc/LEEME.md) | 12 | 12 | 0 (con Ethernet y Modbus TCP; va al frente de la cadena) |

Los siete llevan el mismo programa (`firmware/APRack`), que **se reconoce solo** por los chips que contestan en el I2C (ADS1115 = AI8, expansores 0x24 **y** 0x20 = AP PLC C24, expansor 0x24 solo = IN16, PCA9685 0x41 = AO4, PCA9685 0x40 = LED8, expansor 0x20 sin 0x21 = RL4, si no, Rack 16). Los canales se cuentan seguidos en orden de cadena: con un Rack 16, un IN16 y un AI8, las entradas son I1-I8 (Rack) e I9-I24 (IN16), las salidas Q1-Q16 y las analógicas A1-A8. Las analógicas viajan en las tramas de ESTADO (hasta 8 por módulo, 16 bits cada una, más una máscara de canales en mA). El brillo de las salidas con PWM viaja en el POLL (hasta 8 bytes); si el cabeza o el módulo se reinician, el brillo vuelve a 255 (pleno) y la salida se enciende o apaga solo con la máscara. Orden de la consola: `D g v`.

## Roles y qué pasa cuando algo falla

| Situación | Resultado (en simulación) |
|---|---|
| Arranque | Escucha 1.5 s. Si oye baliza: ESPERA. Si no oye nada y `SENSE_IN` vale 1: CABEZA. Si `SENSE_IN` vale 0: ESPERA (hay alguien detrás de quien debe esperar) |
| Orden de encendido | No importa: la posición la fija el cable |
| Módulo nuevo al final | Entra en unos segundos; los demás conservan su posición |
| El cabeza se apaga | Las salidas de los esclavos pasan a su **máscara segura** (de fábrica, todo apagado) en ≤ 1 s. Si vuelve en menos de 3 s, rearma la misma cadena |
| Cable cortado a media cadena | El cabeza ve menos módulos (≈ 1 s); el tramo aislado elige su cabeza tras 3 s + 0.5 s por posición y sigue funcionando como cadena propia |
| Se reconecta | Dos cabezas en el mismo bus: gana la prioridad mayor (el cabeza original) y, si empatan, el uid menor; el perdedor avisa con RESET y todo se renumera en orden |
| Módulo sin energía en medio | Los de atrás no se unen (su `SENSE_IN` vale 0) hasta que vuelva |
| Tramas perdidas o dañadas | Con 4 % perdidas y 4 % dañadas la cadena de 5 se forma y se mantiene 15 s sin perder módulos |
| 17 módulos | El máximo es 16; los demás esperan sin dirección |
| Nadie puede ser cabeza | Nadie manda y las salidas quedan en estado seguro |

**No es una función de seguridad.** El estado seguro por pérdida del enlace evita salidas «colgadas» por una falla de comunicación, pero no sustituye paro de emergencia, guardas ni relés de seguridad, y no se ha validado como tal.

## Qué falta

- Probar con placas y cable reales: tiempos, ruido, terminación, longitudes.
- Versión **aislada** (CA-IS3092W ya verificado, pero SENSE necesitaría un aislador digital de dos canales con salida por defecto en bajo) para tableros con fuentes distintas.
- Protección ESD de SENSE (hoy solo resistencias).
- Que el 7R Tour se una a la cadena: su RS-485 es aislado y habla Modbus; se une como esclavo Modbus a través del cabeza, no por AP LINK (cambio de placa en una revisión C).
- Prioridad y direcciones fijas por configuración, si algún cliente necesita que un módulo concreto sea el cabeza.
