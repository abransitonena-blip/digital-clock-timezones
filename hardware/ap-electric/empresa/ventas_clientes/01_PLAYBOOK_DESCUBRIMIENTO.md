# 1. Playbook de descubrimiento de AP Monitor 24

> Fecha: 14-oct-2026. Estado real: **no hay placas fabricadas ni medidas, nada certificado, no es función de seguridad, sin precio ni fecha comprometidos.** Este playbook sirve para **validar antes de gastar**: aprender si existe un problema que alguien pague por resolver. No es un guion para vender.
> Marcas: `[V]` con fuente y fecha · `[CG]` conocimiento general sin verificar · `[H]` hipótesis · `PD` por determinar. No hay cifras de disposición a pagar hasta que existan entrevistas registradas en `seguimiento_plantilla.csv`.

## 0. Reglas de conducta en toda conversación
1. Se habla de **su vida y su planta**, no de nuestra idea. Se preguntan hechos pasados y específicos («la última vez que se paró la línea…»), no opiniones sobre el futuro ni «¿lo usaría?». Fuente de método: *The Mom Test* de Rob Fitzpatrick, resumido en [koji.so](https://www.koji.so/docs/mom-test-user-interviews) `[V]` (consultado 14-oct-2026; es un resumen de terceros, no el libro).
2. Estructura de preguntas Situación, Problema, Implicación y Beneficio (SPIN, Neil Rackham, 1988), pensada para ventas técnicas complejas: [Close](https://close.com/sales/glossary/spin-selling) y [Lucid](https://lucid.co/blog/the-4-steps-to-spin-selling) `[V]` (consultados 14-oct-2026, resúmenes de terceros).
3. Se dice desde el minuto uno: «prototipo de ingeniería en validación, sin certificación, no es de seguridad, sin precio ni fecha». Frase fija: *«Todavía no vendemos nada; estamos aprendiendo cómo se resuelve esto en plantas reales.»*
4. **No se menciona el precio de referencia** ($5,000 a $7,000 MXN por máquina, `[H]` de `PREVENTA_AP_MONITOR.md`) antes de que el cliente diga su número (pregunta 18). Anclar sesga la respuesta.
5. Se anota **lo que dijo, no lo que se interpretó**, con fecha y nombre del registro. Cortesía («suena interesante») **no es evidencia**.
6. No se pide información confidencial de producción (cifras de clientes, planos). Se acuerda por escrito qué se puede anotar. Los datos de contacto son datos personales: pedir permiso y avisar para qué se usan (lista de verificación para abogado en `empresa/legal_marca/`, no es asesoría).
7. Nunca se sugiere usar el equipo para proteger a una persona ni conectarlo a un paro de emergencia o guarda.

## 1. Tres perfiles de cliente ideal (hipótesis `[H]` a validar)

| | Perfil A: taller o planta con máquinas sin datos | Perfil B: integrador o servicio de automatización | Perfil C: OEM o constructor de máquinas |
|---|---|---|---|
| Quién | Taller de maquinado CNC convencional, inyección de plástico, estampado, ensamble; típico Tier 2/3 o proveedor de manufactura | Empresa que instala, repara o moderniza máquinas y tableros en varias plantas | Fabricante de máquinas especiales o de línea que las entrega a clientes |
| Dolor probable `[H]` | No sabe cuánto paran sus máquinas ni por qué; el conteo se anota a mano; el cliente (Tier 1 o OEM) pide indicadores | Cada cliente pide «un tablero de producción» y no tiene una caja barata, abierta y documentada | Sus clientes piden datos de la máquina (estado, conteo, causa de paro) y su controlador no los entrega |
| Quién decide | Dueño, gerente de planta, jefe de mantenimiento o de producción | Dueño o ingeniero de proyectos | Ingeniería de producto |
| Canal | Venta directa o vía integrador | **Canal**: un integrador instala en varios clientes | Se incorpora como opción de la máquina |
| Señal de buen ajuste | Máquinas sin PLC o con PLC cerrado, sensores PNP, 24 V CC, gente de mantenimiento que pueda acompañar | Ya usa Modbus RTU/RS-485 y riel DIN; hace instalaciones propias | Controlador con salidas/entradas 24 V; acepta módulo externo |
| Riesgo | Poco presupuesto; interés sin pago | Prefiere marcas conocidas; pide soporte que no podemos dar aún | Ciclos de decisión largos; exige certificaciones |
| Prioridad para el piloto | Alta (donde está el dolor) | Alta (multiplicador y quién validará la instalación) | Media (después) |

Descartados para el piloto: cualquier cliente que quiera usarlo como **función de seguridad**; clientes con sensores **NPN directos** (la rev B no los soporta) salvo que acepten esperar a la rev C o usar interfaz de terceros; instalaciones que exijan **red de 127/220 V** (en pausa).

## 2. Cómo encontrar a 10 prospectos (sin inventar nombres)

**Meta:** 10 conversaciones de descubrimiento con mezcla sugerida: 4 del perfil A (2 maquinado, 2 inyección o estampado), 3 integradores (B), 2 Tier 2/3 de autopartes (A) y 1 OEM (C). Una sola ronda de 10 es una muestra pequeña: sirve para detectar patrones fuertes, no para estimar mercado.

### 2.1 Criterios de selección (todos obligatorios salvo el último)
- Planta en México donde se pueda visitar o hacer llamada por video.
- Al menos **una máquina de producción sin PLC, o con PLC que no entrega datos**, y con tablero de 24 V CC o espacio para una fuente de riel DIN.
- Conteo de piezas o paros anotado a mano, en hoja o en pizarrón (señal de necesidad).
- Contacto con quien **instala o mantiene** (no solo quien compra).
- Deseable: pidió datos o indicadores un cliente grande (presión externa).

### 2.2 Dónde buscar (fuentes reales; verificar que cada portal siga vigente)
| Fuente | Para qué | URL | Estado de verificación |
|---|---|---|---|
| **DENUE de INEGI** | Listar unidades económicas por actividad (SCIAN), tamaño y municipio; sirve para encontrar talleres de maquinado, inyección de plástico, estampado de la zona | Guía: [consulta_denue.pdf](https://www.inegi.org.mx/contenidos/temas/MapaDigital/Doc/consulta_denue.pdf) · Boletín: [denue2024_05.pdf](https://inegi.org.mx/contenidos/saladeprensa/boletines/2024/denue/denue2024_05.pdf) | `[V]` documentos existen (14-oct-2026); la edición hallada tiene 6,097,675 unidades (datos a marzo de 2025). Portal de consulta en línea: buscar «DENUE» en inegi.org.mx (no se verificó la URL directa) |
| **SIEM** (Sistema de Información Empresarial Mexicano, Secretaría de Economía) | Registro federal de empresas, de consulta pública | Descripción: [gob.mx](https://www.gob.mx/cms/uploads/attachment/file/435405/2.5.3_Sistema_de_Informaci_n_Empresarial_Mexicano.pdf) | `[V]` existe; no se confirmó el portal de búsqueda actual |
| **Clústeres automotrices** (Nuevo León, Guanajuato, Jalisco, otros) | Eventos de proveeduría, conocer Tier 2/3 en desarrollo | Cobertura: [clusterindustrial.com.mx, CLAUT Proveedor Automotriz](https://clusterindustrial.com.mx/inicia-proveedor-automotriz-2022-de-claut-generara-mas-de-700-citas-de-negocio/); [CLAUGTO foros de proveeduría](https://clusterindustrial.com.mx/claugto-presento-conferencias-en-foros-am/) | `[V]` notas de 2019-2022; **revisar edición vigente** antes de ir |
| **Directorio Automotriz** (plataforma B2B comercial) | Buscar proveedores por especialidad | Alianza con el clúster de Jalisco: [clusterindustrial.com.mx](https://clusterindustrial.com.mx/cluster-automotriz-de-jalisco-y-directorio-automotriz-firman-alianza-estrategica/) | `[V]` existía según esa nota (reportó ~3,400 empresas; fecha de la nota no verificada). Plataforma comercial, no oficial |
| **INA** (Industria Nacional de Autopartes) | Contexto y programas de Tier 2/3; pedir el padrón a la asociación | Notas: [clusterindustrial.com.mx, desarrollo de proveedores](https://clusterindustrial.com.mx/gabriel-padilla-destaca-crecimiento-inversion-y-transformacion-de-la-industria-de-autopartes/); [S&P Global: INA y Tier 2](https://autotechinsight.spglobal.com/news/27487/mexicos-ina-pushes-for-stronger-tier-2-supplier-base) | `[V]` las notas dicen que INA impulsa Tier 2/3 y un Programa de Desarrollo de Proveedores con IFC; **no se encontró un padrón público de socios** |
| **Meximold** (moldes y herramentales, Querétaro; organizan Gardner Business Media y AMMMT) | Talleres de moldes e inyección | [liderempresarial.com, Meximold 2025](https://www.liderempresarial.com/queretaro-epicentro-de-la-industria-de-moldes-y-troqueles-con-meximold-2025/) | `[V]` nota; la cifra de ~300 empresas del sector sale de esa nota, no verificada |
| **Cámaras**: CANACINTRA, CAINTRA, etc. | Afiliados locales | PD: sitio de la cámara de su ciudad | `[H]` sin URL verificada |
| **Asociación del plástico (ANIPAC)** | Convertidores e inyectores | PD | No se encontró su directorio de socios en la búsqueda; contactar a la asociación |
| **LinkedIn y recomendaciones** | Jefes de mantenimiento e integradores | linkedin.com (búsqueda por cargo y ciudad) | `[CG]` método habitual; respetar sus condiciones de uso |
| **La solicitud de la propia página** | Quien ya pidió piloto o muestra | `web/index.html` | Folios en `seguimiento_plantilla.csv` |

Nota: estas fuentes dan **criterios y listas**, no personas. Cada nombre real debe agregarse al CSV solo cuando exista un contacto con permiso.

### 2.3 Cómo abordar (embudo de contacto)
1. **Pedir una recomendación** a un contacto común (ingeniero, proveedor de refacciones, instructor): respuesta más probable que un correo frío `[H]`.
2. Si es frío: mensaje corto de `04_MENSAJES_TIPO.md`, al **jefe de mantenimiento o producción**, no a ventas.
3. Pedir **20 minutos**, no una venta. Máximo 3 intentos espaciados (día 0, 4, 10) y se cierra con cortesía.
4. Registrar cada intento en el CSV (`etapa_descubrimiento`).
5. Por cada 10 contactos se espera hablar con pocos: no se sabe la tasa `[H]`; medirla es parte del aprendizaje (ver `06_METRICAS_Y_REGLAS.md`).

## 3. Guion de llamada de 20 minutos

| Min | Qué | Texto o pregunta |
|---|---|---|
| 0-2 | Apertura | «Gracias por el tiempo. Estoy investigando cómo las plantas miden paros y producción en máquinas sin PLC. No vendo nada hoy: tenemos un prototipo en validación, sin certificación, sin precio ni fecha. ¿Le parece si le hago unas preguntas y puedo anotar sus respuestas, sin su nombre en nada público?» |
| 2-9 | Situación y práctica actual | Preguntas 1 a 6 del §5 |
| 9-14 | Problema e implicación | Preguntas 7 a 12 (la última vez que se paró la línea; qué costó) |
| 14-17 | Restricciones | Preguntas 13 a 17 (sensores, TI, quién decide, certificados) |
| 17-19 | Presentación mínima (solo si hay interés real) | 2 frases: «Es una caja de riel DIN de 24 V que agrega estado, conteo, causa de paro y OEE, sin nube. Es prototipo.» Preguntar 22 y 23 |
| 19-20 | Cierre | Pedir **un compromiso concreto**: visita de 60 min, ver una máquina en foto, o presentar a quien decide (preguntas 24 y 25). Resumir lo oído en una frase y confirmar |

Después de la llamada (10 min, el mismo día): llenar el CSV, marcar semáforo (§6), anotar 3 citas textuales.

## 4. Guion de visita de 60 minutos

| Min | Qué | Notas |
|---|---|---|
| 0-5 | Seguridad y acuerdos | Cumplir las reglas de ingreso de la planta (EPP, registro). **No tocar equipos ni abrir tableros.** Aclarar que no se medirá ni modificará nada en esta visita |
| 5-15 | Recorrido en la máquina candidata | Fotografiar (si lo permiten) tablero, sensores, torre de luz, espacio en riel, fuente de 24 V, rotulación. Preguntar: ¿qué señales están disponibles? |
| 15-30 | Cómo registran hoy | Ver la hoja o pizarrón real, pedir un ejemplo de la semana pasada (sin datos confidenciales si no quieren). Preguntas 2, 3, 9, 10 |
| 30-40 | Tipo de sensores y señales | Confirmar **PNP/NPN/contacto seco**. Si el sensor es NPN: registrar y explicar la limitación honestamente |
| 40-50 | Quién decide y qué sigue | Preguntas 7 a 8, 15 a 17, 18 a 21 |
| 50-58 | Propuesta de piloto (si hay señal verde o amarilla) | Describir `02_PLANTILLA_PILOTO_30_DIAS.md` en 5 puntos: línea base manual, instalación acompañada, 30 días, retroalimentación obligatoria, sin costo o a costo `PD` |
| 58-60 | Cierre | Confirmar el siguiente paso con fecha del cliente (no nuestra) |

**Lista de datos a salir con ellos de la visita:** tipo de máquina, tensión de control, tipo y número de sensores, si hay torre de luz, espacio en riel DIN, ambiente (polvo, aceite, temperatura aparente), WiFi disponible o no, quién acompañaría, qué horario y qué turnos.

## 5. Las 25 preguntas del estudio, y qué se aprende de cada una

Las primeras 10 son las de `ANALISIS_ECOSISTEMA.md` §10 (marcadas «§10»); se amplían a 25. Hacer en orden aproximado; no leerlas como cuestionario.

| # | Pregunta | Qué se aprende |
|---|---|---|
| 1 §10 | ¿Cuántas máquinas sin PLC o sin datos tiene y de qué tipo? | Tamaño de la oportunidad por cliente; si el perfil encaja |
| 2 §10 | ¿Cómo registra hoy las piezas y los paros? ¿Quién lo captura? | Costo oculto de la práctica actual; si hay dolor real o solo comodidad |
| 3 §10 | ¿Qué sensores usan (PNP, NPN, contacto seco, torre de luz)? | Compatibilidad real con la rev B (solo PNP directo) |
| 4 §10 | ¿Puede sacar datos a internet? ¿TI aceptaría un equipo con Wi-Fi? | Si el diseño «sin nube» es ventaja o irrelevante; barreras de TI |
| 5 §10 | ¿Qué paga hoy por un servicio similar, o por qué no lo ha contratado? | Presupuesto existente o su ausencia; sustitutos |
| 6 §10 | ¿Qué precio por máquina lo haría probarlo, y cuál lo haría dudar? | Rango de disposición a pagar (se pregunta tarde, ver regla 4) |
| 7 §10 | ¿Qué certificados exige su planta para conectar un equipo nuevo? | Si el prototipo es viable en esa planta (puerta de entrada) |
| 8 §10 | ¿Quién decide la compra: mantenimiento, producción, calidad o un integrador? | Quién es el comprador y quién el usuario |
| 9 §10 | ¿Aceptaría un piloto de 30 días con equipo de prototipo? | Voluntad real; mirar cómo condiciona |
| 10 §10 | ¿Qué tendría que hacer el equipo para que lo recomiende? | Criterio de éxito en sus palabras |
| 11 | Cuénteme la última vez que se detuvo una máquina inesperadamente: ¿qué pasó, cuánto duró, quién se enteró? | Frecuencia y costo real de paros con un caso concreto (no promedios inventados) |
| 12 | ¿Cómo supo ese día cuánto se perdió? ¿Después lo calcularon? | Si existe cultura de medir o solo se sufre |
| 13 | ¿Qué decisiones tomaron con esos números en los últimos 6 meses? | Si el dato cambia decisiones; sin decisiones no hay pago |
| 14 | ¿Su cliente (Tier 1 u OEM) le pide indicadores como OEE, paros o trazabilidad? | Presión externa, el mejor motor de compra `[H]` |
| 15 | ¿Qué tableros o sistemas de producción ha probado o descartado, y por qué? | Competencia real y motivos de rechazo |
| 16 | ¿Quién instalaría un equipo así (su gente, un integrador, nosotros)? | Canal y carga de soporte |
| 17 | ¿Cuánto tarda en aprobar una compra de este tamaño y qué pasos hay? | Ciclo de venta y umbral de autorización |
| 18 | ¿Qué presupuesto o rubro cubriría algo así (mantenimiento, mejora continua, proyecto)? | De dónde sale el dinero; sin rubro no hay compra |
| 19 | ¿Qué le preocuparía de instalar un equipo de prototipo en su máquina? | Objeciones reales (garantía, paro de línea, seguridad) |
| 20 | ¿Qué haría con los datos: pantalla en piso, reporte semanal, enlace a su ERP? | Funciones prioritarias; si Modbus/AP Studio bastan |
| 21 | ¿Qué le obliga a mantener el equipo (soporte, refacciones, garantía) para considerarlo? | Qué debe existir antes de la puerta C |
| 22 | (Tras mostrar la descripción) ¿Qué parte no le sirve o le sobra? | Recorte de funciones; claridad de la propuesta |
| 23 | ¿Qué le haría decir que no, aunque funcione? | Causa de rechazo oculta |
| 24 | ¿Qué le parece si ponemos una fecha para ver su máquina y, si procede, un piloto de 30 días? ¿Quién más debe estar? | Compromiso real: fecha y persona. Lo importante es **qué hace**, no qué opina |
| 25 | ¿A quién más me recomienda que le haga las mismas preguntas? | Calidad de la relación y siguiente contacto (el interés genuino sí recomienda) |

## 6. Señales verde, amarilla y roja

Se califica cada conversación con la **suma de evidencias**, no con una respuesta. Registrar en la columna `semaforo`.

| Pregunta | Verde | Amarilla | Roja |
|---|---|---|---|
| 2, 11 | Describe un caso concreto reciente con costo o con quién se enteró; hay hoja o pizarrón | Reconoce el problema pero sin ejemplo | «No tenemos problema» o no recuerda un paro |
| 3 | PNP o contacto seco, 24 V CC | Mezcla; algunos NPN o sensores por revisar | Todo NPN directo o 127/220 V sin interfaz, sin disposición a esperar |
| 4 | Datos locales; no requiere nube | TI debe revisar; Wi-Fi posible | Prohíbe radio inalámbrico y exige cableado a su red (la rev B no tiene Ethernet) |
| 5, 6, 18 | Menciona un rubro y un rango propio (aun si es bajo) | Dice «depende» pero acepta hablar de número tras el piloto | «Nada»; solo lo quiere gratis y permanente |
| 7 | No exige certificado para un piloto aislado o lo gestiona con una carta | Exige revisión de seguridad o aprobación de marca (es un proceso) | Exige UL, NOM o CE del producto antes de cualquier prueba |
| 8, 17 | Identifica al decisor y se compromete a presentarlo | Decisor lejano o con ciclo largo | No sabe, o dice que «lo ve el corporativo» sin acceso |
| 9, 24 | Fecha concreta, máquina y persona de acompañamiento | «Más adelante» pero responde mensajes | No fija fecha; solo «mándame información» |
| 14 | Su cliente se lo pide | Lo desea para mejorar internamente | Sin presión alguna ni interés propio |
| 19, 23 | Preocupaciones atendibles (tiempo de instalación, respaldo) | Preocupaciones sobre soporte que no podemos cubrir aún (decirlo con honestidad) | Quiere usarlo como seguridad o para controlar procesos críticos |
| 25 | Nombra a alguien y lo presenta | Promete pero no presenta | No recomienda a nadie |

**Regla de semáforo de la conversación:**
- **Verde:** problema concreto reciente + tipo de sensor compatible + decisor identificado + compromiso con fecha (visita o piloto). Mínimo 4 de 4.
- **Amarillo:** problema real, pero falta 1 o 2 de los otros (por ejemplo, sensor por confirmar o decisor desconocido).
- **Rojo:** no hay problema concreto, o se exige certificación previa, o quiere seguridad funcional, o solo quiere gratis sin retroalimentación.

Una señal verde **no es una venta**: es permiso para proponer el piloto.

## 7. Qué hacer con lo aprendido
- Cada semana (viernes), correr `python3 resumen_embudo.py seguimiento_plantilla.csv` y actualizar `06_METRICAS_Y_REGLAS.md`.
- Si 3 o más clientes piden lo mismo (por ejemplo, NPN, Ethernet), pasa a la lista de mejoras de `ap-producto` con las citas textuales.
- Nada de lo aprendido se publica como cifra de mercado hasta tener al menos 10 conversaciones registradas.

## Fuentes (consultadas 14-oct-2026, solo se leyeron los resultados de búsqueda, no los textos completos)
- INEGI, guía DENUE: https://www.inegi.org.mx/contenidos/temas/MapaDigital/Doc/consulta_denue.pdf
- INEGI, boletín DENUE 2024: https://inegi.org.mx/contenidos/saladeprensa/boletines/2024/denue/denue2024_05.pdf
- SIEM: https://www.gob.mx/cms/uploads/attachment/file/435405/2.5.3_Sistema_de_Informaci_n_Empresarial_Mexicano.pdf
- Clúster Industrial (CLAUT, CLAUGTO, Directorio Automotriz, INA): enlaces en la tabla
- S&P Global, INA y Tier 2: https://autotechinsight.spglobal.com/news/27487/mexicos-ina-pushes-for-stronger-tier-2-supplier-base
- Meximold: https://www.liderempresarial.com/queretaro-epicentro-de-la-industria-de-moldes-y-troqueles-con-meximold-2025/
- The Mom Test (resumen): https://www.koji.so/docs/mom-test-user-interviews
- SPIN selling (resúmenes): https://close.com/sales/glossary/spin-selling · https://lucid.co/blog/the-4-steps-to-spin-selling
