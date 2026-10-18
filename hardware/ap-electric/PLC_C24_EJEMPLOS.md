# AP PLC C24: programas de ejemplo

Seis programas de AP Lógica que **corren en la prueba de la PC** (`firmware/pruebas/prueba_ejemplos_plc.cpp`, 20 comprobaciones) sobre un AP PLC C24 simulado. No se han probado en una placa. Se cargan desde AP Studio (pestaña Lógica) o por la consola con `PLC TXT renglón|renglón|...` y `PLC RUN`. I1-I12 y Q1-Q12 son las del PLC; las de un módulo AP Rack siguen seguidas (I13, Q13...). Referencia del lenguaje: [PLC_RACK.md](PLC_RACK.md) y el encabezado de `firmware/APRack/logica.h`.

| # | Qué hace | Programa |
|---|---|---|
| 1 | **Arranque y paro con sello.** I1 arranca, I2 para (un paro real se cablea normalmente cerrado: invierte el contacto) | `LD I1` `OR Q1` `ANDN I2` `OUT Q1` |
| 2 | **Intermitente de 1 s** con el pulso del sistema | `LD S2` `OUT Q2` |
| 3 | **Retardo a la conexión.** El motor (Q3) arranca 3 s después de pulsar I3 | `LD I3` `TON T1 3000` `LD T1` `OUT Q3` |
| 4 | **Contador de piezas.** I4 cuenta; a la 5.ª enciende Q4; I5 reinicia | `LD I4` `CTU C1 5` `LD C1` `OUT Q4` `LD I5` `RST C1` |
| 5 | **Aviso de módulo perdido.** Q5 se enciende si un módulo AP Rack deja de contestar | `LD S6` `OUT Q5` |
| 6 | **Entre módulos.** La entrada 1 del Rack 16 que sigue (I13) enciende Q1; I1 enciende su salida 1 (Q13) | `LD I13` `OUT Q1` `LD I1` `OUT Q13` |

Notas:
- Los tiempos van en milisegundos. Desde esta revisión valen también los de 4 o más cifras (`TON T1 3000`, `CTU C1 1000`): **antes se cortaban a 3 cifras y `TON T1 3000` valía 300 ms**, error que apareció al escribir estos ejemplos y ya está corregido en los tres programas que comparten el motor (AP Rack, AP Control y el programador AP-1) y probado en C++ y en AP Studio.
- Las salidas que nombra un programa en RUN son suyas: la consola y Modbus no las pueden cambiar mientras corre (Modbus responde la excepción 04).
- Esto no es una función de seguridad: un paro de emergencia se hace con un circuito cableado de seguridad, no con un programa de este PLC.
