# Análisis del ecosistema de PLC, placas y controladores, y qué llevar a preventa

> **Estado: análisis de escritorio (12-oct-2026).** Nada de AP Electric está fabricado, medido ni certificado. Este documento decide **qué conservar, qué congelar y qué descartar**, y define **un solo producto** para ofrecer a clientes en un programa piloto. No sustituye entrevistas con clientes ni asesoría legal.
>
> Marcas: **[V]** dato con fuente enlazada · **[CG]** conocimiento general sin verificar · **[H]** hipótesis de AP por validar · **[R]** dato del repositorio.
> Complementa a [ESTUDIO_MERCADO_INDUSTRIAL.md](ESTUDIO_MERCADO_INDUSTRIAL.md) (mercado mexicano, competencia y precios).

## 1. Conclusión en cinco líneas

1. **No competir como «un PLC más».** El mercado de PLC está dominado por pocas marcas; AP gana solo vendiendo una **solución cerrada**: *andon + OEE + conteo en una caja de 24 V, local, sin nube, en español*.
2. **Un solo producto para el piloto: AP Monitor 24**, que es el 7R Tour 24DC rev B con el firmware PackML/OEE y el tablero de AP Studio. Todo lo demás espera.
3. **Se descarta para esta etapa** el SKU de red (127/220 V), la línea residencial, la línea LED, el bus CAN propio y cualquier cosa de seguridad de máquina.
4. **Preventa honesta en tres puertas:** lista de interés sin cobro → kits piloto a costo con avisos de prototipo → preventa con pago, solo después de pasar las condiciones de la sección 7.
5. **Mejora continua:** la primera mejora de hardware es la **entrada NPN/PNP** (hoy un sensor NPN no funciona); se decide con lo que se mida en la primera tanda.

## 2. Mapa del ecosistema

### 2.1 Tamaño y estructura del mercado

| Dato | Valor | Fuente |
|---|---|---|
| Mercado de PLC en México | USD 256.2 millones en 2025; proyección USD 382.4 millones en 2034 (TCAC 4.41 %) | [IMARC](https://www.imarcgroup.com/mexico-programmable-logic-controller-market) [V] |
| Concentración global | Siemens > 20.1 %; los 5 mayores (Siemens, Rockwell, Schneider, Mitsubishi, ABB) ≈ 77 % en 2025 | [Global Market Insights](https://www.gminsights.com/industry-analysis/programmable-logic-controller-market) [V] |
| PLC compactos | Se proyectan creciendo más rápido que los modulares (TCAC 12.3 % en un informe de pago) | [GII](https://m.giikorea.co.kr/report/coh1672811-programmable-logic-controller-market-by.html) [V, definición propia del informe] |
| Micro y nano PLC (global) | USD 9.61 mil millones en 2025, TCAC 9.2 % hasta 2029; Asia-Pacífico ≈ 46 % | [GII/TBRC](https://www.giiresearch.com/report/moi2072577-micro-nano-plc-market-share-analysis-industry.html) [V] |
| Participación por marca en México | **No encontrada** en fuentes públicas | — |

Lectura: es un mercado grande pero **maduro y concentrado**; las firmas de investigación no coinciden en las definiciones (por eso los totales no se suman entre sí). El crecimiento está en los equipos **pequeños y compactos**, que es donde AP puede estar, y en las pymes que necesitan «lógica barata, puesta en marcha rápida y fácil de enseñar» ([GII](https://m.giikorea.co.kr/report/coh1672811-programmable-logic-controller-market-by.html)).

### 2.2 Capas y quién las ocupa

| Capa | Quién | Precio de referencia | Fortaleza | Debilidad que AP puede aprovechar | ¿AP entra? |
|---|---|---|---|---|---|
| PLC modular y de gama alta | Siemens, Rockwell, Mitsubishi, Schneider, ABB | cientos a miles de USD [V, estudio §5.1] | Ecosistema, normas, soporte, marca aprobada por las armadoras | Costo y complejidad para una máquina simple | **No.** Es una guerra perdida de antemano |
| Micro-PLC y relé programable | LOGO! 8, Zelio, WEG CLIC02, Micro820, Delta | LOGO! ≈ $3,750-4,560 MXN; Zelio 276-383 USD; WEG 246 USD [V] | Confianza, canal (Mercado Libre, distribuidores) | Programación propia de cada marca, sin OEE ni tablero, entrega de 4+ semanas [V] | **Solo en precio de referencia**: es el ancla del precio de AP Monitor |
| PLC abiertos con Arduino/ESP32 | Arduino Opta, Industrial Shields, Controllino | Opta 146-184 USD; Industrial Shields ESP32 ≈ £311 sin IVA (modelo de 6 entradas con relés) [V] | Comunidad, programación abierta | Precio alto en Industrial Shields; poca solución de planta lista | **Referencia técnica**, no objetivo |
| Placas ESP32 con relés (clones baratos) | Kincony, Norvi, DFRobot, Waveshare, genéricos | Kincony 55 USD, Norvi 88 USD [V]; DFRobot 10 E/S ≈ AUD 261 [V] | Precio muy bajo | Sin soporte local, sin aislamiento serio, sin documentación de planta, sin software de OEE | **Sí es la competencia directa por precio**: AP debe justificar la diferencia con aislamiento, soporte y la aplicación |
| E/S remotas Modbus | Advantech, Moxa, Wago, genéricos | €100+ | Estándar | Solo E/S, sin lógica ni aplicación | AP Gate/E/S: **después** |
| Gateways Modbus a MQTT/OPC UA | Moxa MGate (€518), Teltonika TRB246 (€176) | [V, estudio §5.4] | Robustez | Precio y configuración | **Después** (etapa 3) |
| Software de OEE y andon | Evocon (≈ €159-269 o 189-319 USD/máquina/mes según la fuente; ver corrección en el estudio §5.2), Tulip, Sepasoft, TeepTrak; locales Pulsar y JoonX | [V, estudio §5.2] | Producto completo | Suscripción en la nube; plantas que no sacan datos a internet | **Es el hueco central de AP** |
| Nube IIoT | AWS, Azure, Tractian | sin precio público | Escala | Dependencia y costo recurrente | **No** |
| Poka-yoke y torque | Mountz, Atlas Copco, Banner | 4,835-7,615 USD por estación [V] | Calidad probada | Precio | **Después**, sobre el mismo hardware |

### 2.3 Qué nos dicen las capas

- **El precio de entrada de una «placa de relés» inteligente ya es muy bajo** (55-88 USD). Competir en precio contra eso solo con un valor claro: aislamiento, documentación en español, soporte local y **la aplicación de OEE incluida**.
- **El valor está en el software y en el caso de uso**, no en los relés. Evocon cobra por máquina al mes; un cliente con 10 máquinas paga cifras de decenas de miles de USD al año [V, estudio §5.2]. Un pago único con tablero local es una propuesta distinta, no solo más barata.
- **El canal ya existe** (integradores, Mercado Libre, Cyberpuerta) [V, estudio §5.5].
- **Lo que no se encontró** y por tanto no se afirma: participación por marca en México, disposición a pagar, OEE típico de las plantas objetivo.

## 3. Criterios para decidir qué conservar

Cada línea del ecosistema AP se calificó con seis preguntas (sí / no / por saber):

1. ¿Resuelve un dolor que el mercado ya paga? (hueco de §2.2)
2. ¿Se puede entregar con lo que ya está diseñado y verificado por software?
3. ¿Se puede vender **sin certificación de seguridad de red** (127/220 V) ni de máquina?
4. ¿Reutiliza la misma placa, firmware y aplicación que las demás líneas?
5. ¿Se puede probar con 2 o 3 placas físicas y una máquina real?
6. ¿Evita competir de frente contra un gigante o contra un clon de 55 USD sin diferenciador?

## 4. Decisión por producto del repositorio

| Producto [R] | Decisión | Razón |
|---|---|---|
| **7R Tour 24DC rev B** + firmware PackML/OEE + AP Studio (Producción) | **CONSERVAR: producto del piloto («AP Monitor 24»)** | Cumple las 6 preguntas; ya cerrado por software (ERC/DRC/DFM en 0, pedido revisado) y con pruebas de firmware; 24 V de una fuente certificada de terceros, sin red en la placa |
| 7R Tour CA (con fuente de red en la placa) | **CONGELAR** hasta tener pruebas de seguridad eléctrica | La NOM-001-SCFI-2018 aplica a equipos electrónicos conectados a la red de hasta 277 V CA ([TÜV SÜD](https://www.tuvsud.com/en-ae/e-ssentials-newsletter/consumer-products-and-retail-essentials/e-ssentials-14-2019/mexico-safety-requirements-and-test-methods-for-electronic-devices-standard)) [V]; sin certificado no se vende. Es riesgo legal y de incendio |
| AP Home (Home Plug / Home Switch, red de 127 V) | **CONGELAR** | Consumo masivo, mercado probablemente saturado de marcas conocidas [CG], certificación obligatoria y riesgo de red; no es el hueco encontrado |
| AP UNO (módulo compacto) | **CONSERVAR como segundo hardware**, no en el piloto | Útil para conteo barato (1 entrada), pero hoy el 7R Tour ya cubre el caso |
| AP GATE (Modbus maestro) | **CONSERVAR para la etapa 3** | Es la ruta a MQTT/OPC UA; hoy no hay demanda comprobada |
| AP INPUT, AP PRO DO8, AP PRO AI4 | **CONSERVAR después** del piloto | Amplían entradas, salidas y analógicas; el piloto no los necesita |
| AP BUS / AP NODE (CAN propio) | **CONGELAR** | Es un protocolo propio que ningún cliente pidió; Modbus RTU y TCP cubren el mercado |
| Líneas AP LED (AP FOCO, PWM4, AO4, letreros, flechas, panel) y AP Home de iluminación | **SEPARAR del plan industrial** | Mercado distinto y otro proveedor; distraen la validación del piloto |
| AP Lógica (PLC en el firmware) | **CONSERVAR, pero como «lógica de apoyo»** | No se vende como PLC general. Sirve para interbloqueos y reglas simples junto al OEE |
| PackML / OEE / andon (firmware) | **CONSERVAR: es el diferenciador** | Cubre el hueco principal |
| AP Studio (aplicación local) | **CONSERVAR** | Es lo que el cliente ve; la pestaña Producción ya existe |
| Probador de arnés (AP Test) | **INVESTIGAR después**, con placa nueva | Mayor diferenciación según el estudio, pero esfuerzo alto |
| Energía (demanda y factor de potencia) | **CONSERVAR como segunda oferta** | Costo evitable en el recibo de CFE; usa AP Gate y medidor de terceros |
| Retrofit de control, RFID de habilitación, bancos de baterías | **DESCARTAR por ahora** | Riesgo de seguridad y de responsabilidad; piden socio y evaluación de riesgos |
| Cualquier «función de seguridad» (paro de emergencia, guardas) | **DESCARTAR siempre** | Debe resolverse con relés o PLC de seguridad certificados |

## 5. El producto del piloto: AP Monitor 24

**Qué es:** una caja de riel DIN de 24 V CC que se conecta a una máquina existente y le agrega: estado de la máquina (modelo PackML), conteo de piezas buenas y malas, causa de paro, microparos, andon, OEE y hora de cada evento. Los datos se ven en una aplicación web local (AP Studio) y se leen por Modbus RTU/TCP-Wi-Fi sin nube.

**Qué trae el hardware (diseño, sin medir) [R]:**
- 7 salidas de relé (torre de luz, andon, habilitación de proceso; **capacidad de contactos por determinar por ensayo**).
- 8 entradas de 24 V tipo **PNP** (sensor de pieza, fin de ciclo, botones).
- RS-485 aislado con Modbus RTU; Wi-Fi.
- Reloj con batería externa; puntos de prueba para el arranque.
- Entrada de 24 V CC desde una fuente certificada de terceros.

**Qué no es (se dice en toda ficha y etiqueta):**
- No es una función de seguridad ni sustituye paro de emergencia, guardas o relé de seguridad.
- No tiene certificación (NOM, UL, CE ni homologación del radio); es un **prototipo de ingeniería**.
- No funciona con sensores **NPN** directos en la rev B.
- No tiene Ethernet; usa Wi-Fi o un gateway.
- No hay valores medidos de EMC, temperatura ni vida de relés.

**Por qué esta elección:**
- Ataca el hueco de «andon + OEE sin nube» [V, estudio §6].
- No requiere red de 127/220 V en la placa.
- Todo el firmware tiene pruebas automáticas y la placa pasó las revisiones de software.
- Si falla algo, la primera tanda de 5 placas lo muestra con poco gasto.

## 6. Precio: lo que se sabe y lo que no

**Anclas [V]:** LOGO! 8 ≈ $3,750-4,560 MXN; Zelio 276-383 USD; Opta 146-184 USD; Kincony/Norvi 55-88 USD; Evocon, entre €159 y 319 USD por máquina al mes según la fuente consultada.

**Hipótesis de precio final [H]:** $5,000-7,000 MXN por máquina, pago único, tablero local sin costo (del estudio, §6). Está por encima de un clon de 55 USD y por debajo de un año de suscripción de OEE.

**Costo de fabricación: aún desconocido.** Solo hay precio de catálogo para piezas básicas (~0.99 USD por placa de resistencias, capacitores, LED y diodos [R]). Faltan los precios de relés, ESP32, aislador RS-485, reguladores, bornes y la placa. Para cerrar el costo hay que:
1. Cotizar en JLCPCB las 5 placas (con y sin ensamble) y anotar el total real.
2. Sumar caja DIN, fuente de 24 V recomendada, etiqueta, empaque, flete, aranceles y garantía.
3. Regla de partida: precio ≥ 3 veces el costo directo; si no se logra, se baja funciones o se sube precio.

**Pendiente:** el precio de lista no se publica hasta tener la cotización real y 3 conversaciones con clientes.

## 7. Cómo hacer preventa sin engañar a nadie

Ninguna de estas puertas cobra hoy; se abren en orden.

| Puerta | Qué se ofrece | Condiciones para abrirla |
|---|---|---|
| **A. Lista de interés** (ya existe en la página web) | Registro sin pago. Se dice «prototipo en validación, sin fecha comprometida» | Ninguna: es información |
| **B. Kit piloto a costo** (5-10 clientes) | Unidades de prototipo con aviso de ingeniería, instalación acompañada, retroalimentación obligatoria | 1) Las 3 etapas A-D de `PUESTA_EN_MARCHA.md` superadas en 2 placas; 2) corrida de 72 h en una máquina propia sin fallas no explicadas; 3) etiqueta y aviso de «no es seguridad, sin certificación»; 4) contrato B2B corto revisado por un abogado |
| **C. Preventa con pago** | Fecha estimada, garantía y devolución definidas | 1) Puerta B superada con al menos 3 clientes; 2) precio validado con ventas reales del piloto; 3) pre-escaneo de EMC y pruebas de seguridad eléctrica hechos; 4) términos de devolución y entrega revisados con un abogado (PROFECO y Código de Comercio no se verificaron aquí); 5) importación y facturación resueltas con un contador y un agente aduanal |

**Reglas que no se rompen:**
- No se afirma que el producto está «listo para vender», «certificado» ni «seguro».
- No se publican especificaciones medidas que no se midieron.
- No se cobra anticipo sin fecha, sin política de devolución escrita y sin que exista al menos una unidad funcional.
- La entrega de la preventa se hace desde lo fabricado y probado, no desde promesas.

## 8. Qué mejorar constantemente (lista priorizada)

| Prioridad | Mejora | Por qué | Cuándo |
|---|---|---|---|
| 1 | Entradas bipolares (NPN y PNP) | El mayor límite técnico para máquinas viejas | Rev C, tras la primera tanda |
| 2 | Caja DIN y etiqueta de producto | Sin caja no hay piloto en planta | Antes de la puerta B |
| 3 | Memoria para bitácora (FRAM o flash externa) | La bitácora hoy se reinicia al apagar | Rev C o firmware |
| 4 | AP Studio: historial por turno y causas de paro | Lo que más ve el cliente | Antes de la puerta B |
| 5 | MQTT con TLS y exportación CSV | Que TI de la planta acepte el equipo | Etapa 3 |
| 6 | Ethernet con otro módulo | Las plantas prefieren cable | Rev C o variante |
| 7 | Pre-escaneo de EMC y pruebas eléctricas | Condición para vender | Antes de la puerta C |
| 8 | Reactivar el SKU de red | Solo con certificado NOM | Después de la puerta C |

**Cada ciclo:** medir en banco → registrar en `PLAN_VERIFICACION.md` → corregir el generador → regenerar y repetir el cierre → reconstruir BOM/CPL.

## 9. Criterios para parar o cambiar de rumbo

- **Menos de 3 de 10 entrevistas** dispuestas a pagar el rango de §6 por una solución así → rediseñar la oferta (más barata, solo conteo y andon) antes de gastar en más placas.
- **Fallos de aislamiento o de alimentación** en la primera tanda → corregir antes de entregar nada a clientes.
- **Los clientes piden NPN en todas las máquinas** → la rev C pasa a ser condición de la puerta B.
- **Un competidor local publica un precio claramente menor** → el diferenciador es la aplicación sin nube y el soporte; si eso no pesa, no vale la pena seguir.

## 10. Guion para las entrevistas (3 a 5 mínimo, antes de fijar precio)

1. ¿Cuántas máquinas sin PLC o sin datos tiene y de qué tipo?
2. ¿Cómo registra hoy las piezas y los paros? ¿Quién lo captura?
3. ¿Qué sensores usan (PNP, NPN, contacto seco, torre de luz)?
4. ¿Puede sacar datos a internet? ¿TI aceptaría un equipo con Wi-Fi?
5. ¿Qué paga hoy por un servicio similar, o por qué no lo ha contratado?
6. ¿Qué precio por máquina lo haría probarlo, y cuál lo haría dudar?
7. ¿Qué certificados exige su planta para conectar un equipo nuevo?
8. ¿Quién decide la compra: mantenimiento, producción, calidad o un integrador?
9. ¿Aceptaría un piloto de 30 días con equipo de prototipo?
10. ¿Qué tendría que hacer el equipo para que lo recomiende?

## 11. Pendientes y límites de este análisis

- No se encontró participación por marca en México ni precios de lista de LOGO!, Opta, Zelio y WEG en pesos; los precios de §2.2 vienen del estudio previo, con IVA, aranceles y flete aparte.
- Los precios de Kincony y Norvi vienen del estudio previo; el de DFRobot es de un revendedor australiano. Son referencias, no cotizaciones para México.
- Los datos de mercado de pago (IMARC, GMI, GII) son estimaciones de firmas de investigación; sus definiciones difieren.
- **No se verificaron** las reglas de PROFECO para preventa ni si la NOM-019-SCFI aplica a este producto. Pedir criterio a un abogado y a un organismo de evaluación (ANCE o NYCE) antes de la puerta C.
- Los costos de fabricación reales no existen hasta cotizar en JLCPCB.
- La capacidad de contactos del relé y cualquier límite de corriente siguen **por determinar por ensayo**.

## Fuentes principales
- [IMARC: mercado de PLC en México](https://www.imarcgroup.com/mexico-programmable-logic-controller-market)
- [Global Market Insights: mercado de PLC](https://www.gminsights.com/industry-analysis/programmable-logic-controller-market)
- [GII: PLC por tipo](https://m.giikorea.co.kr/report/coh1672811-programmable-logic-controller-market-by.html)
- [GII/TBRC: micro y nano PLC](https://www.giiresearch.com/report/moi2072577-micro-nano-plc-market-share-analysis-industry.html)
- [Industrial Shields ESP32 en RS Components](https://uk.rs-online.com/web/p/plcs-programmable-logic-controllers/2768687?gb=s)
- [DFRobot 10 E/S ESP32 (Little Bird)](https://littlebirdelectronics.com.au/products/10-i-os-relay-module-cpu-esp32-relay-output.md)
- [TÜV SÜD: NOM-001-SCFI-2018](https://www.tuvsud.com/en-ae/e-ssentials-newsletter/consumer-products-and-retail-essentials/e-ssentials-14-2019/mexico-safety-requirements-and-test-methods-for-electronic-devices-standard)
- Resto de precios y competencia: [ESTUDIO_MERCADO_INDUSTRIAL.md](ESTUDIO_MERCADO_INDUSTRIAL.md), con sus enlaces.
