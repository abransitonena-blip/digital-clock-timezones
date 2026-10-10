# AP BUS: especificación (versión 1)

Bus de campo del ecosistema AP ELECTRIC: **24 V DC + CAN** en un solo cable de 4 hilos. Une el nodo maestro (tablero, Wi-Fi, app, Home Assistant) con los nodos remotos [AP NODE](ap1-node/LEEME.md).

## 1. Capa física

| | |
|---|---|
| Estándar | CAN de alta velocidad (ISO 11898-2), transceptor TJA1051T/3 |
| Velocidad | **250 kbit/s** (hasta 250 m de cable en total) |
| Topología | **Línea** (del maestro al último nodo, entrando y saliendo de cada uno). Sin estrellas |
| Terminación | 120 Ω en **los dos extremos** (JP3 cerrado en el maestro y en el último nodo; abierto en los de en medio) |
| Alimentación | 24 V DC (18-30 V) por el mismo cable; cada nodo con su fusible, diodo serie y supresor |
| Tierra | Común (no aislado): una sola fuente de 24 V o, si hay varias, **solo el 0 V unido** |

### Conector, ahora: JST XH de 4 patas (2.5 mm)

| Pata | Señal |
|---|---|
| 1 | +24 V |
| 2 | CAN_H |
| 3 | CAN_L |
| 4 | 0 V |

- 3 A por pata.
- **J1 = ENTRA, J2 = SIGUE**, unidos en la placa.
- Medir con el bus sin alimentar: entre CAN_H y CAN_L debe haber **60 Ω** (dos terminaciones de 120 Ω en paralelo). 120 Ω = falta una; 40 Ω = sobra una.

### Conector a futuro (AP BUS PRO): RJ45 según CiA 303-1

| Pata | Señal |
|---|---|
| 1 | CAN_H |
| 2 | CAN_L |
| 3 y 7 | CAN_GND (0 V) |
| 6 | Blindaje |
| 8 | V+ (18-30 V) |

- Permite usar cables de red armados (patch cords) y conmutadores de riel DIN.
- **Pendiente:** hay candidatos en LCSC (C25168872 y otros), pero falta una huella verificada contra la hoja del fabricante. Por la regla del proyecto, no se usa hasta verificarla.
- Para ambiente industrial (polvo, agua, vibración) la opción es **M12 de 5 polos codificación A** (como DeviceNet/CANopen), en una placa hermana.

## 2. Tramas (CAN 2.0A, identificadores de 11 bits)

| Identificador | Sentido | Cada | DLC | Contenido |
|---|---|---|---|---|
| `0x100 + id` | nodo → maestro | 100 ms y al cambiar una entrada | 7 | [0] módulos: bits 0-3 = DO8 en 0x20-0x23, bits 4-7 = AP INPUT en 0x24-0x27 · [1-4] entradas de cada AP INPUT · [5] banderas (bit 0 = salidas apagadas por falla segura) · [6] versión = 1 |
| `0x200 + id` | maestro → nodo | 100 ms y al cambiar una salida | 6 | [0-3] salidas de cada DO8 · [4] reservado · [5] versión = 1 |

- `id` = 1, 2 o 3 (nodo remoto).
- Las tramas de otra versión se ignoran: un equipo con programa nuevo no confunde a uno viejo.
- **Carga del bus:** 3 nodos × 2 tramas × 10 por segundo ≈ **2.9 %** de los 250 kbit/s. Queda lugar para tramas futuras (AI4 remotas, mediciones).
- Identificadores reservados para versiones futuras:
  - `0x080`: hora y escena, del maestro a todos;
  - `0x300 + id`: entradas analógicas;
  - `0x400 + id`: mediciones (V, A, temperatura).

## 3. Tiempos y falla segura

| Evento | Qué pasa |
|---|---|
| El nodo no recibe órdenes en **1 s** | Apaga **todas** sus salidas y avisa con la bandera 0. Al volver las órdenes, aplica lo que mande el maestro |
| El maestro no oye a un nodo en **1 s** | Sus módulos desaparecen de la app y de Home Assistant; las reglas que dependen de sus entradas no se disparan |
| Un nodo nuevo aparece | Su estado de entradas inicial **no** dispara reglas (igual que al conectar un AP INPUT local) |
| Errores en el bus (cable en corto) | El controlador TWAI entra en *bus-off* y el programa lo recupera solo cada 0.5 s |

El protocolo está en `ap1-prog/firmware/LetreroLabAP1/apbus.h` y se prueba en la PC con `bash tools/probar_apbus.sh`.

## 4. Por qué CAN y no RS-485, Ethernet o radio

| | CAN (AP BUS) | RS-485 (Modbus) | Ethernet | Radio (Wi-Fi/ESP-NOW) |
|---|---|---|---|---|
| Arbitraje y CRC por hardware | **Sí** | No (lo hace el programa) | Sí | Sí |
| Varios maestros / avisos sin preguntar | **Sí** | No (sondeo) | Sí | Sí |
| Distancia | 250 m a 250 kbit/s | 1200 m | 100 m por tramo | Variable |
| Costo por nodo | Controlador interno del ESP32 + TJA1051 (~1 USD) | Transceptor (~0.3 USD) | PHY + magnéticos (~5 USD) | 0 |
| En nave con motores | **Muy bueno** (diferencial, hecho para autos) | Bueno | Bueno | Malo |
| Alimentación por el mismo cable | Sí (24 V) | Sí | Solo PoE (caro) | — |

- RS-485 se usa para los equipos de terceros: el módulo DMX y la **AP GATE** (Modbus RTU con medidores, variadores y PLC).
- La radio queda para el módulo **LINK** (puente a Home Assistant por MQTT, ya incluido en el CORE por Wi-Fi).
