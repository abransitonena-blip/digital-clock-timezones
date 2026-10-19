# AP Home CEREBRO rev A (CONCEPTO)

El cerebro de AP Home como placa propia y **solo de baja tensión**: ESP32-C3-WROOM-02 (Wi-Fi y BLE), regulador de 3.3 V, botón, LED verde y rojo y pines de programación. **No toca la red de CA**, así que se puede poner fuera de la caja metálica de la instalación (mejor señal) y es la parte que el usuario ve y toca.

> **Estado: CONCEPTO.** ERC 0, DRC 0, sin pistas sin unir, paridad esquema/placa 0, reglas de fabricación 0 y pedido a JLCPCB «sin errores». **Nada está fabricado ni medido.**

| | |
|---|---|
| Tamaño | **42 × 56 mm**, 2 capas (11 mm de la placa son la zona libre de cobre bajo la antena del módulo) |
| Piezas | 17 tipos, 23 piezas, todas con código LCSC (pedido completo ~15 USD de cargo por 5 tipos Extended; económico ~9 USD con 2 piezas de patas a mano) |
| Entrada | 5 V por el cable de 4 hilos (JST XH) desde AP Home POTENCIA; no tiene otra alimentación (los pines de programación traen 5 V del USB solo para programar **sin** el cable conectado) |
| Cable (1 a 1) | 1 = 5 V · 2 = 0 V · 3 = mando del relé (3.3 V) · 4 = estado del apagador (salida aislada del optoacoplador de la potencia, con pull-up de 100 kΩ aquí) |
| Pines del ESP32 | **Los mismos que la placa AP Home original** (IO4 relé, IO5/IO6 LED, IO7 apagador, IO9 botón): el programa de AP Control para Home sirve sin cambios. `tools/revisar_pines.py` lo comprueba |

Cable: se recomienda de 4 hilos de baja tensión de hasta 1 m (no medido); separado de los cables de red.

## Límites

1. No es un producto: concepto sin fabricar. Falta medir alcance de Wi-Fi y consumo.
2. 42 × 56 mm no es tan chica como podría: el módulo con antena manda. Un módulo ESP32-C3-MINI o una antena de chip en la placa lo reducirían (otro código LCSC por verificar).
3. Con el cable desconectado el relé queda apagado (pull-down de 10 kΩ en la potencia).

Regenerar: `bash ../../tools/rutear.sh ap-electric/home_cerebro AP_HOME_CEREBRO` (desde `hardware/`).
