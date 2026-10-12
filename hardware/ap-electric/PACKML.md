# Unidad PackML de AP Control (estado, OEE y causas de paro)

> **Estado: CONCEPTO / prototipo de programa.** Compila y pasa sus pruebas en la PC. No se ha probado en un equipo ni en una máquina real.
> - **No es una función de seguridad.** Paro de emergencia, guardas y cortinas van a un relé o PLC de seguridad (NOM-004-STPS, ISO 13849-1, IEC 60204-1). Esta unidad solo informa el estado y puede pedir paro o retención.
> - **[CG]** = conocimiento general. La numeración de estados y comandos y los estados habilitados por modo están por confirmar con el texto oficial de ANSI/ISA-TR88.00.02-2022 u OMAC.
> - Definición de OEE propia de AP Electric; falta confirmarla contra ISO 22400-2.

Código: `firmware/APControl/unidad_packml.h` · Pruebas: `firmware/pruebas/prueba_packml.cpp` (`bash tools/probar_apbus.sh`).
Contexto de mercado y decisiones: [ESTUDIO_MERCADO_INDUSTRIAL.md](ESTUDIO_MERCADO_INDUSTRIAL.md).

## Qué hace

- Mantiene el **estado de la máquina** con una tabla propia de transiciones (estado × comando), sin dependencias externas.
- Acumula el **tiempo en cada estado**, cuenta piezas buenas y defectuosas y calcula disponibilidad, desempeño, calidad y OEE.
- Guarda la **causa de paro** (categoría × 100 + causa) y detecta **microparos**.
- Ante una falla del controlador pide ABORT (falla grave) o HOLD (falla leve, solo en EXECUTE).
- Lleva una bitácora de las últimas 16 transiciones y rechazos.

## Estados y comandos (numeración propuesta [CG])

| N.º | Estado | Tipo | | N.º | Comando |
|---|---|---|---|---|---|
| 1 | Clearing | actuando | | 1 | Reset |
| 2 | Stopped | espera | | 2 | Start |
| 3 | Starting | actuando | | 3 | Stop |
| 4 | Idle | espera | | 4 | Hold |
| 5 | Suspended | espera | | 5 | Unhold |
| 6 | Execute | dual | | 6 | Suspend |
| 7 | Stopping | actuando | | 7 | Unsuspend |
| 8 | Aborting | actuando | | 8 | Abort |
| 9 | Aborted | espera | | 9 | Clear |
| 10 | Holding | actuando | | | |
| 11 | Held | espera | | | |
| 12 | Unholding | actuando | | | |
| 13 | Suspending | actuando | | | |
| 14 | Unsuspending | actuando | | | |
| 15 | Resetting | actuando | | | |
| 16 | Completing | actuando | | | |
| 17 | Complete | espera | | | |

Ciclo normal: **Stopped → (Reset) Resetting → Idle → (Start) Starting → Execute → Completing → Complete → (Reset)**.
Los estados «actuando» terminan solos al siguiente paso. Si el estado debe esperar a la aplicación (por ejemplo, el motor a velocidad), se llama `esperarAplicacion(estado)` y luego `completar()`.

Modos: 1 producción, 2 mantenimiento, 3 manual. En mantenimiento y manual no existen Suspend ni Completing/Complete (propuesta). El modo solo cambia en Stopped o Aborted.

## Reglas de seguridad funcional

1. **Arranca en STOPPED.** Nada se reanuda solo tras un corte de energía.
2. **Origen remoto (Modbus, web, red):** Stop, Hold y Abort siempre se aceptan. Reset, Start, Unhold, Unsuspend y Clear se **rechazan** salvo que alguien en el equipo habilite `PK REMOTO 1` por la consola USB. Un maestro Modbus no puede darse ese permiso (el registro 305 es de solo lectura).
3. **Una falla que causó ABORT y sigue activa bloquea** Clear, Reset y Start. La falla por reinicio del vigilante pide ABORT al arrancar y exige un Clear explícito.
4. `procesoHabilitado()` es verdadero solo en EXECUTE. Sirve para mirar o apagar una salida de proceso; no es un enclavamiento de seguridad.
5. Las cargas de **proceso** de AP Control siguen arrancando apagadas y apagándose al perder la comunicación (ver `ap_control.h`).

## OEE (definición AP, en milésimas)

| Valor | Cálculo |
|---|---|
| Disponibilidad | EXECUTE / (EXECUTE + HOLDING + HELD + UNHOLDING + SUSPENDING + SUSPENDED + UNSUSPENDING + ABORTING + ABORTED + CLEARING) |
| Desempeño | piezas × ciclo nominal / tiempo en EXECUTE, tope 1000 |
| Calidad | (piezas − defectuosas) / piezas |
| OEE | disponibilidad × desempeño × calidad |

65535 = no calculable (falta el ciclo nominal o no hay piezas). **Microparo:** EXECUTE sin piezas durante más de 3 ciclos nominales (mínimo 2 s); solo se detecta con ciclo nominal configurado. Stopped, Idle, Complete, Starting, Resetting, Stopping y Completing no cuentan como pérdida (se consideran planeados o de transición): es una propuesta por validar con un cliente.

**Causas de paro:** categoría × 100 + causa (0-99). Categorías: 1 avería, 2 cambio, 3 microparo, 4 velocidad reducida, 5 defectos, 6 arranque, 7 planeado, 8 externa. Las fallas del controlador la llenan solas (por ejemplo, comunicación perdida = 8xx).

## Mapa Modbus «PackTags v1»

Direcciones del protocolo, base 0. Sin unidad PackML los registros no existen (excepción 02).

| Tipo | Dirección | Contenido |
|---|---|---|
| Entradas discretas | 48 · 49 · 50 | Microparo · proceso habilitado (EXECUTE) · comandos remotos que reanudan permitidos |
| Registros de entrada | 100 | Versión del mapa (1) |
| | 101 · 102 · 103 · 104 | StateCurrent · UnitModeCurrent · StopReason · último comando aceptado |
| | 105-106 · 107-108 | ProdProcessedCount · ProdDefectiveCount (32 bits: bajo, alto) |
| | 110-143 | Segundos acumulados en cada estado 1-17 (estado n en 110 + 2(n − 1), 32 bits) |
| | 150 · 151 · 152 · 153 | Disponibilidad · desempeño · calidad · OEE (milésimas) |
| | 154 · 155-156 | Microparo · segundos en microparo |
| Registros de retención | 300 | CntrlCmd: escribir 1-9. Excepción 04 si el estado, el modo o el origen no lo permiten; 03 si el valor no existe |
| | 301 | UnitMode (1-3), solo en STOPPED o ABORTED |
| | 302 | StopReason (0-999) |
| | 303 | 1 = contar pieza buena · 2 = defectuosa (solo en EXECUTE o COMPLETING) |
| | 304 | Ciclo nominal en ms (0 = sin ciclo) |
| | 305 | Solo lectura: comandos remotos que reanudan |
| | 306 · 307 · 308 · 309 | Entrada de pieza buena · de pieza mala · de andon · de reanudar (0-8; 0 = ninguna; no se puede repetir una entrada: excepción 03) |

## Entradas de la máquina (origen automático de piezas)

Cada entrada puede tener **una** función. Se detecta el flanco de subida de la entrada ya estable (con su antirrebote).

| Función | Qué hace |
|---|---|
| Pieza buena | Cuenta una pieza (solo en EXECUTE o COMPLETING) |
| Pieza mala | Cuenta una pieza defectuosa |
| Andon | En EXECUTE pide HOLD con la causa 190 («llamado de andon») |
| Reanudar | Botón junto a la máquina: sale de HOLD. Se considera origen local |

Una entrada que ya estaba activa al arrancar no cuenta ni pide nada. Con una torreta de luz o un sensor de ciclo se usa la entrada de pieza buena; con un botón de la estación, andon y reanudar.

**Memoria:** la función de cada entrada, el ciclo nominal y el modo se guardan con la orden de guardar (`GUARDAR` o el registro 200 = 0xA55A) y se cargan solo si la firma y el CRC son correctos. Los contadores de piezas se guardan con límite de escrituras (1 min sin cambios y como máximo cada 10 min). Los tiempos por estado no se guardan: empiezan en cero al encender. «Valores de fábrica» borra todo.

## Órdenes locales

Por la consola USB (con permiso para reanudar) o por `/api?c=` (sin él):

| Orden | Qué hace |
|---|---|
| `PK RESET` · `START` · `STOP` · `HOLD` · `UNHOLD` · `SUSPEND` · `UNSUSPEND` · `ABORT` · `CLEAR` | Comando de la máquina de estados |
| `PK SC` | Fin del estado «actuando» o de EXECUTE |
| `PK BUENA` · `PK MALA` | Cuenta una pieza |
| `PK MODO n` · `PK MOTIVO n` · `PK CICLO ms` | Modo, causa de paro y ciclo nominal |
| `PK ENT ciclo mala andon reanuda` | Qué entrada (1-8) hace cada cosa; 0 = ninguna. Ver «Entradas de la máquina» |
| `PK REMOTO 0/1` | **Solo por la consola USB.** Permite o no que Modbus y la web reanuden |

Los bits **S11-S27** del PLC valen 1 cuando la unidad está en el estado S − 10 (por ejemplo, `LD S16` = EXECUTE). `/api` devuelve el bloque `pk` con estado, modo, causa, piezas, disponibilidad, desempeño, calidad y OEE.

## Lo que falta

1. Confirmar con el texto de ISA-TR88.00.02-2022 los estados, comandos, modos y estados habilitados por modo.
2. Hora real de cada evento y bitácora en memoria flash (los tiempos por estado se reinician al encender).
3. Entrada de conteo rápido: hoy la cuenta pasa por el ciclo de 5 ms y el antirrebote, así que no sirve para más de unas decenas de piezas por segundo.
4. El tablero OEE completo en AP Studio (la página del equipo ya muestra estado, piezas y OEE).
5. Probarlo con una máquina real y validar la definición de OEE con un cliente.
