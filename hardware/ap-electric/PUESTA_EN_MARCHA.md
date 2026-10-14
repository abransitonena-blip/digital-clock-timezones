# Puesta en marcha del 7R Tour rev B: primer prototipo

> **Estado: procedimiento propuesto, sin ejecutar.** Todavía no existe ninguna placa física. Esta guía sirve para recibir la primera tanda de JLCPCB, probarla de menos a más riesgo y anotar qué falló. Ningún valor medido aquí es del producto hasta que se registre en `PLAN_VERIFICACION.md`.

## 1. Qué cambió en la rev B

Cambios de la placa respecto a la rev A, todos para el plan industrial (OEE, andon, trazabilidad) y para no perder un prototipo por falta de acceso a las señales:

| Cambio | Para qué | Riesgo que agrega |
|---|---|---|
| IO0 recibe la entrada 1 e IO20 la entrada 2 (conteo rápido por interrupción) | Contar piezas hasta ~500 por segundo sin pasar por el ciclo de 5 ms | Casi nulo: solo une dos redes que ya existían |
| Reloj PCF8563T + cristal + OR de batería + conector de batería de 2 pines | Hora de cada evento sin red | Un circuito nuevo en el bus I2C. Si falla, se arma una variante sin él |
| 11 puntos de prueba (24 V, 5 V, 3.3 V, 2 × 0 V, SDA, SCL, TX, RX, DE, EN) | Medir con el osciloscopio durante la puesta en marcha | Ninguno (no entran al BOM) |
| 7 resistencias de 10 kΩ a 0 V en las entradas del ULN2003A (RD1-RD7) | Los relés no se mueven mientras el programa arranca: el TCA9554 trae 100 kΩ a 3.3 V al encender | Casi nulo: 7 piezas básicas |
| Firmware: conteo rápido, reloj, ajuste de hora por Modbus, autoprueba `TEST` | Probar la placa sin instrumentos y saber qué falló | Solo software |

**Sin cambios, pero conviene saberlo antes de comprar:**
- Las entradas son de tipo **PNP / sumidero** (la corriente entra por IN y sale por COMI). Un sensor **NPN** (el más común en máquinas japonesas y chinas viejas) **no funciona** conectado directo. Habría que usar un optoacoplador de entrada bipolar. **Ojo:** el LTV-814S no tiene la misma huella (es de 9.53 mm); una alternativa en SOP-4 es el LTV-354T o el EL354, con la huella por verificar. Además, mezclar PNP y NPN en una misma placa pide dos comunes separados (COMA y COMB). Ver `empresa/hardware/ESTUDIO_REV_C.md`.
- No hay Ethernet: el ESP32-C3 no tiene los pines libres. Para Modbus TCP se usa Wi-Fi o un AP GATE.
- El cobre es de **2 oz** (dice el subtítulo de la placa): hay que elegirlo al cotizar. JLCPCB lo ofrece, pero **no se confirmó que también se pueda en ensamble**; verlo en la cotización antes de pagar.

## 2. Qué pedir (primera tanda)

| Concepto | Recomendación |
|---|---|
| Cantidad | 5 placas. Ensamblar solo 2 o 3 y dejar el resto sin piezas por si hay que corregir |
| Variante | Empezar con **7R Tour 24DC** (sin la parte de red): es la menos peligrosa de probar |
| Archivos | `fabricacion/jlcpcb/AP_7R_TOUR_gerber_JLCPCB.zip`, `AP_7R_TOUR_24DC_BOM_JLCPCB.csv` y `AP_7R_TOUR_24DC_CPL_JLCPCB.csv` |
| Piezas de patas (relés, bornes, DIP, conector de batería) | Para la primera tanda usar los archivos `_solo_SMD` y soldar a mano lo demás: se ahorra el cargo por tipo Extended y se pueden revisar los relés |
| Cobre | 2 oz; grosor 1.6 mm; acabado HASL con plomo o ENIG (el ENIG cuesta más y no es necesario) |
| Antes de pagar | 1) correr `python3 tools/revisar_pedido.py ap-electric/7r-tour AP_7R_TOUR 24DC`; 2) en la pantalla «Component Placement» de JLCPCB revisar la **orientación** de cada pieza con polaridad (diodos, LED, U1-U11, relés, J15 USB-C) y 3) confirmar que todas las piezas tienen existencias |
| Pieza que no se arma en JLCPCB | La **batería** del reloj y su cable: se compra aparte (CR2032 con portapilas y cable, o CR1220 con cable) |

## 3. Qué comprar aparte

- Fuente de **24 V CC** de al menos 1 A, certificada (por ejemplo, una Mean Well de riel DIN) y su fusible o termomagnético.
- Cable USB-C de datos.
- Un **adaptador USB a RS-485** y una computadora con `mbpoll` o `pymodbus`.
- Multímetro y, si se puede, osciloscopio.
- Para las entradas: un botón o un sensor **PNP** y una fuente de 24 V. Una lámpara de 24 V para probar los contactos.
- **No** conectar red de 127/220 V a ninguna prueba de esta guía. El SKU CA se prueba después, con un transformador de aislamiento y un termomagnético, por una persona competente.

## 4. Secuencia de pruebas (de menos a más riesgo)

Anotar cada resultado con fecha y número de placa. Si un paso falla, **parar** y no seguir.

### Etapa A: placa apagada (sin energía)
1. Inspección visual: puentes de soldadura en U1, U2-U5, U6, U11, U9; orientación de diodos y LED; relés derechos.
2. Con multímetro en continuidad, **sin energía**: 24 V contra 0 V, 5 V contra 0 V y 3.3 V contra 0 V no deben estar en corto (más de ~1 kΩ en cada par).
3. Verificar que **no** hay continuidad entre los bornes de red (J1-J7, solo contactos) y la parte de baja tensión (0 V, USB).

### Etapa B: alimentación (solo USB, sin 24 V)
4. Conectar el USB-C. Medir 5 V en TP2 (V5) y 3.3 V en TP3. Corriente de la computadora normal.
5. Debe aparecer el puerto serie. Abrir la consola (115200 baudios): debe escribir la línea de arranque con la versión.
6. Escribir `TEST`. Sin 24 V es esperable que reporte «no contesta el expansor de retroalimentación» o bobinas sin energía según el caso; lo importante son los demás expansores y el reloj.

### Etapa C: 24 V
7. Con la fuente de 24 V en 0 V de salida y **sin cargas**, subir lentamente a 24 V mirando la corriente: en reposo debe ser de unas decenas de mA. Medir 24 V en TP1 (después del diodo) y 5 V en TP2.
8. `TEST`: todos los expansores (0x20, 0x21, 0x22, 0x23) deben contestar, la identificación debe ser 7R Tour y no debe haber bobinas con tensión.
9. `TEST RELES` y luego `TEST RELES SI` (**sin cargas conectadas**): cada relé hace clic y su bobina se detecta. Un «no se energizó» apunta al ULN2003, al divisor o a la soldadura del relé.
10. Interruptor DIP 1: debe forzar el relé 1 aunque el programa no lo pida y el programa debe verlo como «forzado» (`?` en la consola, campo `fz`).

### Etapa D: entradas, conteo y reloj
11. Con 24 V en la entrada 1 (respecto a COMI), debe encenderse su LED y la consola mostrar la entrada activa.
12. Conteo rápido: `PK ENT 1 2 0 0` (entrada 1 = pieza buena, 2 = mala), `PK RESET`, `PK START` y dar pulsos a la entrada 1. El campo `n` de `?` debe subir uno por pulso. Probar pulsos rápidos (hasta unos 100 Hz con un generador, o con un botón comprobar que no se pierden).
13. Reloj: `PK HORA <segundos desde 1970>` (por ejemplo `date +%s` en Linux). Quitar el USB y el 24 V, esperar 1 minuto y volver a conectar: la hora debe conservarse con la batería puesta.
14. Con la batería **quitada**, apagar y encender: el reloj debe perder la hora y `TEST` debe avisarlo, sin impedir el uso del resto del equipo.

### Etapa E: Modbus y PackML
15. Conectar el adaptador RS-485 (A, B y 0 V aislado) con la terminación de 120 Ω cerrada en los extremos si es necesario. Leer los registros de entrada 100, 101 y 153 y escribir el 300 con 1 (Reset): debe **rechazarlo** (excepción 04) porque falta el permiso local.
16. Probar los demás pasos de `PACKML.md` (estados, paros, microparos, OEE).

### Etapa F: contactos con carga de 24 V
17. Con una lámpara de 24 V en un canal, probar encendido y apagado. Medir temperatura de los bornes.

### Qué anotar
Fecha, número de placa, resultado de cada paso, mediciones (24 V, 5 V, 3.3 V, corriente en reposo y con 7 relés) y fotos. Pasarlo a `PLAN_VERIFICACION.md`.

## 4 bis. Hacerlo con la consola en vez de la terminal

La [consola AP Base](web/consola.html) (Chrome o Edge) hace por USB lo mismo que la terminal serie, con botones:
1. Abrir `web/consola.html`, **Conectar por USB** y elegir el puerto de la placa (115200 baudios). Si no contesta en unos segundos: cable de datos, otro puerto, o que corra AP Control.
2. **Autoprueba (TEST)**: el resultado aparece en el registro de la parte de abajo (Avanzado). **Probar relés** pide confirmar que no hay cargas.
3. En **Salidas** alterna cada canal y mira «Bobina con tensión»; en **Entradas** comprueba cada una con un sensor o un botón de 24 V.
4. En **Comunicaciones** pon la dirección y los baudios de Modbus y la hora de la computadora.
5. Antes de apagar: **Guardar configuración en la placa**, y **Copiar respaldo** para tener la lista de órdenes.
Es origen *local*: puede reanudar la máquina y dar el permiso remoto. Por red local solo acepta Stop, Hold y Abort. **Aún no se ha probado con una placa real**: anota en `PLAN_VERIFICACION.md` cualquier diferencia.

## 5. Si algo sale mal

| Síntoma | Qué revisar primero |
|---|---|
| No aparece el puerto USB | Soldadura de J15 (USB-C), R9/R10 (5.1 kΩ), U10 y la orientación del ESP32; probar otro cable |
| El expansor 0x22 o 0x23 no contesta | Pull-ups R3/R4, direcciones A0-A2, soldadura del TSSOP |
| El reloj no contesta | U11, Y1 (orientación no importa), D12 (SOT-23) y que no haya corto en el bus I2C; con el reloj quitado el resto debe funcionar |
| `TEST RELES`: no se energiza ningún relé | 24 V presente en V24; U1 (ULN2003A) y la orientación de D1 |
| Corriente alta en reposo | Buscar el componente caliente: D1 o D2 en corto, U7 (buck) o U9 |

## 6. Después de la primera tanda

1. Corregir en el generador (`7r-tour/gen/make.py`), regenerar y repetir el cierre.
2. Mejoras ya identificadas para la rev C: entradas bipolares (NPN/PNP), una memoria para bitácoras largas, y una variante con Ethernet (otro módulo).
3. Solo después de medir, fijar los límites de corriente por canal y pasar a laboratorio (ver `ARQUITECTURA.md`).
