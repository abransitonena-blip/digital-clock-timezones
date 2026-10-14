# 2. Plantilla de piloto de 30 días (AP Monitor 24)

> Fecha: 14-oct-2026. **Plantilla, no un piloto en curso.** No existen placas fabricadas ni medidas. Este documento solo se usa cuando se cumplan las condiciones de la **puerta B** de `ANALISIS_ECOSISTEMA.md` §7: las etapas A-D de `PUESTA_EN_MARCHA.md` superadas en 2 placas, corrida de 72 h en máquina propia sin fallas no explicadas, etiqueta/aviso de «no es seguridad, sin certificación» y contrato B2B corto revisado por un abogado. Hoy esas condiciones **no se cumplen**; la plantilla se ensaya en papel y con el cliente para afinarla.
> El piloto **no promete** precio, fecha de entrega futura ni certificación. No es función de seguridad.

## 0. Ficha del piloto (llenar una por cliente)
| Campo | Valor |
|---|---|
| Folio (web) / id del CSV | |
| Empresa y planta | |
| Contacto de mantenimiento / producción (acompañante) | |
| Máquina (tipo, año, fabricante), turnos por día | |
| Señales disponibles: sensores (PNP / NPN / contacto seco), torre de luz, tensión de control | |
| Fecha de inicio acordada (la fija el cliente y depende de la unidad probada) | |
| Versión de placa y firmware (de `?` y `TEST`) | |
| Aviso de prototipo firmado (fecha) | |
| Persona de AP en la instalación | |

## 1. Objetivos medibles (se acuerdan antes; sin ellos no hay éxito que evaluar)
Se marcan como **hipótesis** hasta tener datos reales; el objetivo es *aprender*, no demostrar una ganancia.

| # | Objetivo | Cómo se mide | Meta propuesta `[H]` |
|---|---|---|---|
| O1 | Funcionamiento: el equipo registra sin intervención | Días con registro continuo / días del piloto; reinicios no explicados | Registro continuo en al menos 90% de los turnos operados; cero eventos que afecten la operación de la máquina |
| O2 | Exactitud del conteo | Conteo del equipo vs. conteo manual independiente en 5 turnos distintos | Diferencia dentro de la tolerancia pactada con el cliente (propuesta inicial: 1%, `PD`) |
| O3 | Exactitud de estados y paros | Hora de inicio y fin de 10 paros anotados a mano vs. los del equipo | Coincidencia de los paros mayores a 5 min; diferencias explicadas |
| O4 | Causa de paro capturada | % de paros con causa registrada | Al menos 70% con causa en la semana 3 (si el operador la captura) |
| O5 | Utilidad: el dato se usó | Número de decisiones o acciones tomadas por el cliente con el dato (anotadas) | Al menos 1 decisión documentada; el cliente lo describe en sus palabras |
| O6 | Tiempo de instalación y facilidad | Horas de instalación, de capacitación, llamadas de soporte | Registrar; sin meta (se aprende) |
| O7 | Disposición a pagar y qué lo impide | Respuesta en la reunión de cierre (ver §7) | Registrar con rango propio del cliente |

## 2. Línea base: cómo medir OEE y paros a mano **antes** de instalar
**Duración:** mínimo 5 turnos de producción en la misma máquina (idealmente 10 días hábiles, o los 5 turnos más representativos). **Quién:** el acompañante del cliente, con apoyo de AP. **Qué:** hoja de turno (§2.1) y resumen (§2.2).

### 2.1 Hoja de turno (una por turno)
| Dato | Valor |
|---|---|
| Fecha, turno, máquina, producto/molde/pieza, operador | |
| Tiempo planeado de producción del turno (min), excluyendo descansos y mantenimiento planeado | |
| Ciclo nominal (seg/pieza) acordado con el cliente (de su ficha de proceso; si no la tiene, tomar 10 ciclos cronometrados en operación normal y usar el mediano; anotar cómo se obtuvo) | |
| Piezas totales producidas (contador de la máquina o conteo manual al final del turno) | |
| Piezas defectuosas (rechazo y retrabajo, separados) | |
| Bitácora de paros (cada uno: hora de inicio, hora de fin, causa en su vocabulario) | |

Para registrar paros sin interrumpir al operador: una hoja en la máquina con casillas de causa predefinidas (avería, cambio, ajuste, falta de material, falta de operador, calidad, otra) y hora; el acompañante revisa dos veces por turno. Los **microparos** (de menos de 2-3 ciclos, que casi nadie anota) no se registran bien a mano: se anota que **la línea base subestima microparos**, no se inventa su cantidad. Las categorías de causa del equipo (1 avería, 2 cambio, 3 microparo, 4 velocidad reducida, 5 defectos, 6 arranque, 7 planeado, 8 externa; ver `PACKML.md`) se usan como lista para que sean comparables.

### 2.2 Cálculo (misma definición que el equipo, para poder comparar)
Definición **de AP Electric** (`PACKML.md`, pendiente de confirmar contra ISO 22400-2):
- **Disponibilidad** = tiempo en producción / (tiempo en producción + paros no planeados, retenciones, abortos y arranques). A mano: (tiempo planeado − paros no planeados) / tiempo planeado, aclarando qué paros se excluyeron como «planeados».
- **Desempeño** = piezas × ciclo nominal / tiempo en producción, con tope de 100%.
- **Calidad** = (piezas − defectuosas) / piezas.
- **OEE** = disponibilidad × desempeño × calidad.
La fórmula clásica de OEE y las seis grandes pérdidas se describen en la guía de Vorne: https://www.vorne.com/pdf/fast-guide-to-oee.pdf `[V]` (consultado 14-oct-2026 solo a nivel de resultado de búsqueda). Las metas «de clase mundial» que circulan (por ejemplo 85%) son referencia de la bibliografía, **no una meta para este cliente**.

Resumen de línea base (una vez): OEE promedio y rango de los turnos, 3 principales causas de paro por tiempo y por frecuencia, y la lista de **qué no se pudo medir**. Si hay menos de 5 turnos o falta el ciclo nominal, el OEE queda «no calculable» (igual que el equipo, que lo marca 65535) y se dice así.

## 3. Plan de instalación acompañada

### 3.1 Antes del día de instalación
1. Revisión del alcance con el cliente: sensores identificados y **todos PNP o contacto seco**; si hay NPN directo, **no se instala** (rev B no lo soporta) y se registra como hallazgo.
2. El cliente entrega: permiso de trabajo según su procedimiento, lugar en riel DIN, fuente de 24 V CC certificada (de terceros; no se incluye) y protección propia (fusible o termomagnético), y esquema o fotos del tablero.
3. AP confirma por escrito qué se conecta y **qué no**: ver §3.3.
4. Unidad probada de nuevo en banco el día anterior: `TEST` sin errores, reloj con hora, configuración de entradas cargada (`PK ENT …`). Respaldo de la configuración guardado.
5. Presentes el día de la instalación: la persona de mantenimiento del cliente (quien ejecuta o autoriza el trabajo eléctrico), y AP como apoyo.

### 3.2 Checklist de seguridad (todo se marca; si algo falla, se detiene)
Esto es una lista propuesta, **no sustituye** el procedimiento de la planta ni la asesoría de un responsable de seguridad. Referencias normativas a verificar con el texto oficial: [NOM-004-STPS-1999](https://www.gob.mx/cms/uploads/attachment/file/680125/NOM-004-STPS-1999.pdf) (maquinaria y equipo; vigente según la STPS, consultado 14-oct-2026) y [NOM-029-STPS-2011](https://platiica.economia.gob.mx/normalizacion/nom-029-stps-2011/) (mantenimiento de instalaciones eléctricas, vigente; las cláusulas de bloqueo no se leyeron aquí).

| ✔ | Punto |
|---|---|
| ☐ | Trabajo ejecutado o autorizado por **personal competente del cliente**; AP no energiza ni desenergiza equipos ajenos |
| ☐ | Máquina **detenida** en estado seguro y producción avisada |
| ☐ | **Desenergizar** la sección de trabajo y aplicar **bloqueo y etiquetado (LOTO)** del cliente, con su candado y etiqueta personal |
| ☐ | **Verificar ausencia de tensión** con instrumento adecuado (probar antes y después en una fuente conocida) |
| ☐ | Descargar energía almacenada (condensadores del variador, aire, resortes) según el procedimiento del cliente |
| ☐ | Trabajo **solo en 24 V CC**. **Nada de 127/220 V** conectado al equipo (el SKU CA está en pausa) |
| ☐ | **Ningún cable del equipo toca circuitos de seguridad**: paro de emergencia, guardas con enclavamiento, cortinas, relé o PLC de seguridad, contactores de seguridad. No se deriva ni se comparte señal de esos circuitos |
| ☐ | Las salidas de relé del equipo **no** se conectan en serie con el paro ni con el permisivo de la máquina durante el piloto; solo torre de luz y andon. La salida de «habilitación de proceso» **no se usa** para detener la máquina en este piloto `[H]` (se valorará después) |
| ☐ | Entradas conectadas solo a sensores **PNP** o contactos secos de 24 V; no se deriva una señal ya usada sin que mantenimiento verifique que no se carga el circuito (carga de entrada del equipo: `PD`, sin medir) |
| ☐ | Cableado separado de potencia (variadores, motores); sin pasar junto a cables de 127/220 V; tierra del tablero respetada |
| ☐ | Etiqueta visible en la unidad: «Prototipo de ingeniería. Sin certificación. **No es función de seguridad.**» |
| ☐ | Fuente de 24 V certificada, con su protección de sobrecorriente, antes de conectar |
| ☐ | Las salidas y la configuración dejan el estado seguro por defecto: el equipo arranca en STOPPED y no reanuda solo tras un corte (`PACKML.md`) |
| ☐ | Fotos del antes y después, y croquis de lo conectado, firmados por quien autorizó |
| ☐ | Persona del cliente informada de **cómo apagar y retirar** el equipo (quitar los 24 V) sin herramientas especiales |

### 3.3 Secuencia de instalación (después del checklist)
1. Montar en riel DIN y conectar tierra/0 V, **sin 24 V**.
2. Conectar las entradas (sensor o botón de pieza buena, pieza mala, torre de luz si se usa). Revisar la polaridad con la máquina desenergizada.
3. Conectar el 24 V del cliente; encender; conectar la computadora por USB y abrir la consola (`web/consola.html`).
4. `TEST` y revisión de entradas: activar cada sensor a mano y ver el cambio en la consola.
5. Configurar: `PK ENT` (qué entrada cuenta qué), ciclo nominal, hora (`PK HORA` o botón de la consola), Modbus si aplica, y **Guardar configuración**.
6. Retirar el LOTO según el procedimiento del cliente, solo por quien lo colocó; arrancar la máquina con producción real; observar 30 min.
7. Capacitar al acompañante 30-45 min: qué muestra la consola, cómo capturar causa de paro, qué hacer si algo falla y cómo retirarlo.

### 3.4 Riesgos del piloto y mitigaciones
| Riesgo | Efecto | Mitigación |
|---|---|---|
| Prototipo sin pruebas de EMC, temperatura ni vida de relés (todo `PD`) | Reinicios o lecturas erróneas en un entorno ruidoso | Primeras 72 h con supervisión; criterio de salida por reinicios; no instalar junto a variadores grandes sin separación |
| Sensor NPN o niveles de señal no compatibles | Conteo erróneo | Verificar en visita y banco; si no es PNP, no instalar |
| Cableado mal hecho en un tablero ajeno | Falla de la máquina o riesgo eléctrico | Solo personal del cliente conecta; checklist firmado |
| El cliente lo percibe como seguridad | Falsa sensación de protección | Etiqueta, aviso firmado y explicación verbal; la lista de «qué no es» entregada por escrito |
| Pérdida de datos por corte de energía o batería del reloj | Pérdida de la hora | Batería del RTC verificada; respaldo semanal exportado (consola o Modbus) |
| Datos del cliente mal usados | Reclamo de confidencialidad | Acuerdo de uso de datos por escrito (abogado), mínimo necesario, sin nube |
| Dependencia de una sola persona de AP para soporte | Paros sin respuesta | Horario de respuesta acordado `PD` en el contrato; la persona del cliente sabe retirar el equipo |
| Responsabilidad por daños | Reclamación | Contrato de piloto y seguro: temas para el abogado (`empresa/legal_marca/`) |

## 4. Calendario de 30 días (días naturales desde la instalación)
| Día | Actividad | Entregable |
|---|---|---|
| -14 a -1 | Línea base manual (5 turnos mínimo) | Hojas de turno y resumen §2.2 |
| 0 | Instalación acompañada y capacitación | Checklist §3.2 firmado, fotos, croquis |
| 1-3 | Supervisión estrecha (llamada diaria de 10 min) | Registro de incidencias |
| 7 | Revisión semana 1: ¿registra?, ¿se entiende?, ajustes de configuración | Nota de 1 página |
| 14 | Comparación equipo vs. conteo manual en 5 turnos (O2, O3) | Tabla de diferencias y explicación |
| 21 | Revisión de uso: ¿qué decisión se tomó?; captura de causas (O4, O5) | Nota; primeras citas textuales |
| 28-30 | Reunión de cierre de 45 min; exportar datos; retirar o dejar el equipo según acuerdo | Reporte final §6 |

## 5. Criterios de éxito y de salida
**Éxito del piloto** (se necesita todo): (a) O1 y O2 dentro de lo pactado; (b) el cliente puede describir en sus palabras una acción que tomó con el dato; (c) respondió la reunión de cierre con rango de pago o motivo claro de no pago; (d) no hubo incidente de seguridad.

**Éxito parcial:** funciona, pero el cliente no tomó decisiones con el dato o no da número de pago: se registra como aprendizaje, no como venta.

**Salida anticipada (cualquiera detiene el piloto y se retira el equipo):**
1. Cualquier **incidente de seguridad** o sospecha de que el equipo afecte un circuito de seguridad.
2. Reinicios o fallas inexplicadas que afecten la producción del cliente (más de 2 reinicios no explicados en 72 h `[H]`).
3. Sensor o señal incompatible descubierta durante la instalación.
4. El cliente deja de acompañar durante 10 días o lo solicita.
5. Datos erróneos que el cliente ya usa para decidir (mejor retirar que arriesgar una decisión mala).

## 6. Reporte final (plantilla de 2 páginas)
1. Resumen en 5 líneas: qué se hizo, qué pasó, qué decide el cliente.
2. Datos del piloto (ficha §0, versión, días de registro).
3. Línea base vs. piloto: OEE, disponibilidad, desempeño, calidad, 3 causas de paro (con las limitaciones y **sin extrapolar** a otras máquinas).
4. Exactitud: tabla de conteo y paros, diferencias y causas.
5. Incidentes, reinicios, tiempo de soporte (horas de AP).
6. Lo que el cliente dijo (citas textuales con permiso).
7. Qué faltó o sobró; lo pedido (NPN, Ethernet, pantalla…).
8. Disposición a pagar y condiciones (en sus palabras).
9. Estado en el CSV (`Cerrada` / `En lista de espera` / `No viable`) y siguiente paso.
10. Decisión de AP: continuar con este cliente / aprender y cerrar / parar.

## 7. Reunión de cierre (preguntas)
Preguntas 18-25 de `01_PLAYBOOK_DESCUBRIMIENTO.md`, más: ¿volvería a usarlo si el piloto terminara hoy?, ¿qué haría falta para dejarlo instalado de forma permanente?, ¿lo recomendaría y a quién?, ¿qué pagaría hoy por esto (rango), sabiendo que es prototipo? **No se firma ni se cobra nada en la reunión** (puerta C cerrada).

## Fuentes
- `PREVENTA_AP_MONITOR.md`, `ANALISIS_ECOSISTEMA.md` §7, `PUESTA_EN_MARCHA.md`, `PACKML.md` (repositorio).
- Vorne, guía rápida de OEE: https://www.vorne.com/pdf/fast-guide-to-oee.pdf (14-oct-2026)
- NOM-004-STPS-1999: https://www.gob.mx/cms/uploads/attachment/file/680125/NOM-004-STPS-1999.pdf
- NOM-029-STPS-2011: https://platiica.economia.gob.mx/normalizacion/nom-029-stps-2011/
