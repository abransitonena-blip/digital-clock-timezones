# 7. Material de capacitación para un integrador

> Fecha: 14-oct-2026. **Estado: material basado en documentos del repositorio; el equipo aún no se ha probado con una placa real.** Úsese como guía de formación para quien instalará o diagnosticará el AP Monitor 24 en un piloto. Todo cambia si las pruebas encuentran diferencias; las diferencias se anotan en `PLAN_VERIFICACION.md`. No es función de seguridad, sin certificación. Fuentes: `PUESTA_EN_MARCHA.md`, `PACKML.md`, `WEB_Y_PLACA.md`, `PREVENTA_AP_MONITOR.md`.

## Módulo 1 (30 min): qué es y qué no es
- **Es** (diseño, sin medir): caja de riel DIN de 24 V CC; 8 entradas PNP; 7 salidas de relé; RS-485 aislado; Wi-Fi; reloj con batería externa; puntos de prueba; firmware PackML/OEE; consola web por USB. Alimentación: fuente de 24 V certificada de terceros, no incluida.
- **No es**: seguridad (paro de emergencia, guardas, cortinas, relé de seguridad), producto certificado, ni compatible con NPN directo; no tiene Ethernet ni nube.
- **Qué entrega:** estado PackML, conteo bueno/malo, causa de paro, microparos, OEE (disponibilidad × desempeño × calidad, definición de AP pendiente de confirmar con ISO 22400-2) y hora de cada evento.
- **Prueba de comprensión:** ¿puede el cliente usar la salida de relé en serie con el paro de emergencia? **No.**

## Módulo 2 (45 min): conceptos mínimos
1. **PackML:** estados (Stopped, Idle, Execute, Held, Aborted, etc.), comandos (Reset, Start, Stop, Hold, Abort, Clear) y ciclo normal Stopped → Resetting → Idle → Starting → Execute → Completing → Complete. La unidad **arranca en STOPPED** y no reanuda sola.
2. **Origen local vs remoto:** por red/Modbus solo se aceptan Stop, Hold y Abort; reanudar (Reset, Start, Unhold, Clear) exige origen local (USB/botón) o `PK REMOTO 1` por USB. Un maestro Modbus no puede darse ese permiso.
3. **OEE:** definición y límites; con ciclo nominal ausente el OEE es «no calculable» (65535).
4. **Causas de paro:** categoría × 100 + causa: 1 avería, 2 cambio, 3 microparo, 4 velocidad reducida, 5 defectos, 6 arranque, 7 planeado, 8 externa.
5. **PNP vs NPN:** con PNP la corriente entra por IN y sale por COMI; un sensor NPN directo **no funciona**.

## Módulo 3 (45 min): seguridad e instalación
Estudiar y aplicar el checklist de `02_PLANTILLA_PILOTO_30_DIAS.md` §3.2: desenergizar, bloqueo y etiquetado según procedimiento del cliente, verificar ausencia de tensión, solo 24 V, nada del equipo toca circuitos de seguridad, etiqueta de prototipo, retirada fácil. Referencias a leer en texto oficial: [NOM-004-STPS-1999](https://www.gob.mx/cms/uploads/attachment/file/680125/NOM-004-STPS-1999.pdf) y [NOM-029-STPS-2011](https://platiica.economia.gob.mx/normalizacion/nom-029-stps-2011/). Esta capacitación **no certifica** a nadie como persona competente; eso lo determina la empresa.

## Módulo 4 (90 min, con placa): puesta en banco, de menos a más riesgo
Seguir `PUESTA_EN_MARCHA.md` §4 y anotar fecha, número de placa y resultado de cada paso. Si falla, parar.
| Etapa | Qué hace el estudiante | Resultado esperado |
|---|---|---|
| A (apagada) | Inspección visual; continuidad 24 V/5 V/3.3 V contra 0 V (sin cortos, más de ~1 kΩ); sin continuidad entre bornes de red y baja tensión | Sin cortos ni continuidad indebida |
| B (solo USB) | 5 V en TP2, 3.3 V en TP3; abrir consola (115200); línea de arranque con versión | Puerto serie; versión visible |
| C (24 V) | Subir lentamente con fuente limitada, sin cargas; corriente en reposo; `TEST`; `TEST RELES` y luego `TEST RELES SI` (sin cargas); interruptor DIP 1 | Expansores 0x20-0x23 responden; relés hacen clic; DIP fuerza relé 1 |
| D | Entrada 1 con 24 V → LED y consola; conteo `PK ENT 1 2 0 0`, `PK RESET`, `PK START`, pulsos; hora `PK HORA <epoch>`; batería quitada → reloj pierde hora y `TEST` avisa | Cuenta uno por pulso; hora conservada con batería |
| E | Modbus: leer registros de entrada 100, 101 y 153; escribir 300 = 1 (Reset) debe **rechazarse** (excepción 04) | Se respeta el permiso local |
| F | Lámpara de 24 V en un canal; medir temperatura de bornes | Sin calentamiento anormal; anotar |

## Módulo 5 (45 min): la consola
Abrir `web/consola.html` en Chrome o Edge y **Conectar por USB** (115200). Pasos: autoprueba `TEST` (resultado en el registro); **Probar relés** pide confirmar que no hay cargas; Salidas (alternar y ver «bobina con tensión»); Entradas; Comunicaciones (dirección Modbus, baudios, hora de la PC); **Guardar configuración en la placa** y **Copiar respaldo**. La consola muestra solo las secciones que la placa declara en `cap`. Origen USB = local (puede reanudar); por red local solo Stop/Hold/Abort. Aviso: la consola **no se ha probado con una placa real**.

## Módulo 6 (60 min): diagnóstico
| Síntoma | Qué revisar primero (de `PUESTA_EN_MARCHA.md` §5) |
|---|---|
| No aparece el puerto USB | Cable de datos, soldadura de J15, R9/R10, U10, orientación del ESP32 |
| Expansor 0x22/0x23 no contesta | Pull-ups R3/R4, direcciones A0-A2, soldadura del TSSOP |
| Reloj no contesta | U11, Y1, D12, corto en I2C; sin reloj el resto debe funcionar |
| `TEST RELES`: ningún relé se energiza | 24 V en V24; U1 (ULN2003A); orientación de D1 |
| Corriente alta en reposo | Componente caliente: D1/D2 en corto, U7 (buck) o U9 |
| Conteo erróneo en planta | Tipo de sensor (¿NPN?), antirrebote de la entrada, ruido; comparar con conteo manual |
| La máquina no reanuda desde la red | Es lo esperado: Reset/Start exigen origen local o `PK REMOTO 1` por USB |
| OEE «no calculable» | Falta ciclo nominal o piezas |
| Hora incorrecta tras apagar | Batería del reloj; usar `PK HORA` |
Regla: **registrar siempre** síntoma, qué se probó y resultado, y enviarlo a AP para `PLAN_VERIFICACION.md`.

## Módulo 7 (30 min): lo que el integrador debe decir al cliente
Aviso de prototipo, qué no es, qué se mide y qué no, privacidad de los datos, cómo retirar el equipo, a quién llamar. Sin precios, fechas ni certificaciones. Objeciones: `05_OBJECIONES.md`.

## Examen práctico (aprueba/no aprueba, sin certificado oficial)
Lista de verificación para el instructor:
1. Explica en 2 min qué es y qué no es (incluye que no es seguridad). ☐
2. Aplica el checklist de seguridad sin omitir puntos (en simulación). ☐
3. Identifica PNP vs NPN en un esquema y decide si se instala. ☐
4. Hace `TEST` y lee el resultado. ☐
5. Configura entradas, ciclo nominal y hora, y guarda. ☐
6. Verifica que Reset por Modbus se rechaza. ☐
7. Diagnostica dos fallas inyectadas (cable de entrada invertido; batería quitada). ☐
8. Llena el registro de instalación y el reporte. ☐
