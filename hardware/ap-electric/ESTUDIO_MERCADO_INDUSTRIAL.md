# Estudio de mercado: AP Electric Industrial en México

> **Estado: estudio de escritorio (octubre de 2026).** Se hizo con búsqueda web y lectura del repositorio. No incluye entrevistas ni pilotos.
> - Cada cifra lleva su fuente y año. Lo que viene de proveedores o prensa comercial está marcado como tal.
> - **[CG]** = conocimiento general: no pude confirmarlo con la norma o el documento original.
> - Los hallazgos de mercado **no** son una decisión de producto. La disposición a pagar sigue sin medirse.
> - Nada del hardware descrito se ha fabricado, medido ni certificado.

## 1. Resumen ejecutivo

**Qué encontramos**
- La industria mexicana es enorme y está presionada: aranceles, reglas de origen del T-MEC, escasez de técnicos y pérdida de empleo en maquila.
- Las pymes proveedoras (Tier 2 y 3) tienen máquinas viejas sin datos y poca trazabilidad, y no pagan los precios actuales de OEE en la nube.
- **Hueco de mercado:** nadie ofrece «andon + OEE en una caja» ni un «supervisor poka-yoke» a precio de relé programable, con soporte local en español y sin nube obligatoria.

**Qué recomendamos construir primero (con el hardware que ya existe)**

| # | Producto | Por qué |
|---|---|---|
| 1 | **AP Monitor**: OEE, andon, conteo y e-kanban | Máquinas viejas sin datos; hueco de precio y de nube; reutiliza AP UNO y AP INPUT; riesgo bajo |
| 2 | **AP Energía**: demanda y factor de potencia (GDMTH), solar, aire comprimido | Costo evitable en el recibo de CFE; AP GATE más medidor de terceros; riesgo bajo |
| 3 | **AP Gateway**: Modbus a MQTT Sparkplug y, después, OPC UA | Los integradores lo necesitan; reutiliza AP GATE; es la ruta de datos de todo lo demás |
| 4 | **AP Lab**: kit educativo para CONALEP y universidades tecnológicas | Canal de bajo riesgo para validar y formar técnicos |
| 5 | **AP Poka-Yoke**: secuencia, presencia, torque OK y bitácora | Trazabilidad IATF 16949. **No es función de seguridad** |

**PackML no es un producto aparte.** Es la capa de estado común de todos los anteriores: los tiempos por estado alimentan el OEE.

**Antes de vender cualquier cosa:** fabricar y medir las placas y cerrar `PLAN_VERIFICACION.md`.

## 2. Mercado

### 2.1 Tamaño de la manufactura

| Dato | Valor | Fuente |
|---|---|---|
| Establecimientos manufactureros | 634,248 | [Censos Económicos 2024, INEGI](https://www.inegi.org.mx/programas/ce/2024/) |
| Personas ocupadas en manufactura | 7.19 millones | [Boletín CE2024](https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2025/ce/CE2024_def.pdf) |
| Aporte al valor agregado censal | 34.4 % | Mismo boletín |
| Empresas IMMEX (mar-2025) | 6,525 | [INEGI vía N+](https://www.nmas.com.mx/economia/immex-menos-empleo-empresas-crecen-salarios-inegi/) |
| Empleo IMMEX (ago-2025) | 3.18 millones, −3.4 % anual | [CEFP](https://www.cefp.gob.mx/ixDOCs/2017/226-251022.pdf) |

### 2.2 Segmentos

| Segmento | Tamaño (año, fuente) | Dónde | Calidad del dato |
|---|---|---|---|
| Vehículos | 3.9 M en 2025; exportó 3.39 M, −2.7 % ([AMIA vía Mexico Industry](https://mexicoindustry.com/noticia/sector-automotriz-en-mexico-consolida-su-desempeno-en-2025-y-avanza-en-la-transicion-tecnologica)) | Coahuila, Guanajuato, Nuevo León, SLP, Aguascalientes, Puebla, Sonora | Gremial |
| Autopartes (Tier 1-3) | US$119 mil M en 2025, −2.2 % ([INA](https://mexicoindustry.com/noticia/industria-de-autopartes-en-mexico-cerro-2025-con-produccion-de-119-000-millones-de-dolares-2)); más de 2,000 plantas y ~880-900 mil empleos (cifras de 2024) | Bajío 35.9 %, norte 44 % ([Guanajuato](https://puertointerior.guanajuato.gob.mx/blog/2026/09/22/la-revision-del-t-mec-empuja-a-la-industria-automotriz-mas-alla-del-tier-1/)) | Gremial; el empleo de 2025 no está verificado |
| Proveedores | Más de 300 Tier 1 y ~1,000 Tier 2/3, con debilidad en los niveles bajos ([SE vía FUNDESA](https://fundesa.org.gt/content/files/publicaciones/pcoe/1_Automotriz_-_Internacional.pdf)) | Todo el país | Oficial citado por tercero |
| Arneses | Aptiv: más de 75 mil empleos y 29 plantas ([Vanguardia](https://vanguardia.com.mx/dinero/acelera-industria-automotriz-en-coahuila-invierten-en-region-centro-NG2787483)); Lear Matamoros: 4,000 empleos en arneses para VE ([Cluster Industrial](https://clusterindustrial.com.mx/lear-inaugura-nueva-planta-en-coahuila-con-una-inversion-de-34-mdd/)) | Chihuahua, Coahuila, Sonora, Tamaulipas, Guanajuato | Datos de las propias empresas |
| Robots instalados | ~5,600 en 2024 (−4 %); parque de 59,300, ~63 % en automotriz ([IFR vía Mexico Industry](https://mexicoindustry.com/noticia/mexico-instalo-5-600-robots-industriales-y-acelera-la-automatizacion-de-sus-fabricas)) | Nuevo León, Querétaro, Guanajuato | Secundaria |
| Vehículos eléctricos y baterías | 68,444 eléctricos de batería en ene-may 2026, −32 %; 495 empresas en la cadena ([Cluster Industrial](https://clusterindustrial.com.mx/cluster-industrial-b2b-presenta-el-mapeo-de-electromovilidad-en-mexico-2026/)) | Coahuila, SLP, Nuevo León | Comercial y parte proyección |
| Aeroespacial | 386 empresas en 19 estados; exportaciones de US$13.6 mil M en 2025 ([FEMIA vía AIG](https://hub.americanindustriesgroup.com/news/aerospace-exports-from-mexicos-closed-2025-at-a-record-13-6-billion-cementing-the-countrys-position-as-the-worlds-fourth-largest-exporter/)) | Querétaro, Baja California, Sonora, Chihuahua | Las fuentes no coinciden en el empleo |
| Dispositivos médicos | ~230 plantas, más del 60 % en Baja California ([El Financiero](https://www.elfinanciero.com.mx/empresas/2025/11/07/mexico-diversifica-sus-exportaciones-de-dispositivos-medicos/)) | Tijuana, Chihuahua, Sonora | Gremial |
| Plásticos e inyección | ~5,200 empresas y más de 300 mil empleos ([ANIPAC vía Milenio](https://www.milenio.com/negocios/industria-plastico-registra-crecimiento-2-5-2025-anipac)); 689 inyectores entre 947 proveedores automotrices ([Cluster Industrial](https://clusterindustrial.com.mx/cluster-industrial-b2b-detecta-a-947-proveedores-de-plasticos-que-consolidan-la-cadena-automotriz-en-mexico/)) | Edomex, Jalisco, Nuevo León, Guanajuato, Querétaro | Gremial |
| Agua y bombeo municipal | 2,922 organismos operadores; solo el 53.3 % de las tomas tiene medidor ([BBVA Research 2026](https://www.bbvaresearch.com/wp-content/uploads/2026/08/2026-08-03-Nota-situacion-del-agua-2026.pdf)); la electricidad pesa del 36.5 al 60 % de su costo ([BDAN](https://www.nadb.org/uploads/content/files/UMI%20Seminars/Eficiencia_energtica_sesion_1_23_sept_2021.pdf)) | Todo el país | Datos de 2021 en parte |
| Agricultura protegida | Más de 48,000 ha según la SMEAP; las cifras oficiales discrepan ([Imagen Agropecuaria](https://imagenagropecuaria.com/etiqueta/agricultura-protegida/)) | Jalisco, Sinaloa, Baja California, Michoacán | Inconsistente |
| Naves y parques | 463 parques y 90 M m² (dic-2024) ([AMPIP](https://mexicobusiness.news/infrastructure/news/ampip-sees-2026-industrial-park-investment-37)) | Norte y Bajío | Gremial |
| Alimentos, empaque, metalmecánica | **No encontré cifras 2025 por subsector.** Habría que consultar la EAIM o la EMIM del INEGI | — | Pendiente |

## 3. Tendencias y lo que piden

| Tendencia | Dato | Necesidad de automatización |
|---|---|---|
| Nearshoring | IED récord de US$40,871 M en 2025 ([SE vía Por Esto](https://www.poresto.com/mexico/2026/2/25/mexico-rompe-record-historico-de-inversion-extranjera-directa-en-2025-con-40871-mdd.amp.html)); la IED manufacturera no es clara ([Expansión](https://expansion.mx/economia/2026/04/01/mexico-vende-mas-pero-inversion-industrial-pierde-cae)) | Arranque rápido de líneas, datos desde el primer día |
| Aranceles y T-MEC | Sección 232 vigente en autos y autopartes; las exportaciones de equipo de transporte cayeron 7 % en 2025 ([Expansión](https://expansion.mx/economia/2026/01/07/aranceles-232-que-son-y-por-que-mexico-ya-paga-la-factura)) | Productividad y evidencia de origen |
| Electromovilidad | Producción de eléctricos a la baja, híbridos al alza; plantas de baterías (BMW en SLP, Kia en NL, Hyundai Mobis) | Pruebas eléctricas, monitoreo de celdas |
| Centros de datos | 279 MW instalados, 72 % en Querétaro; más de 1,300 MW previstos a 2031 ([CICM](https://cicm.org.mx/wp-content/uploads/22JUN26-BOLETIN-CENTROS-DE-DATOS.pdf)) | Medición de energía y temperatura de tableros |
| Solar distribuida | 5.16 GW al cierre de 2025 ([pv magazine](https://www.pv-magazine.com/2026/06/03/mexico-supera-en-2025-los-5-gw-solares-en-generacion-distribuida/)) | Medición en el punto de conexión, gestión de demanda |
| Tarifa eléctrica | Factor de potencia mínimo de 0.95 desde 2024 ([Circutor](https://circutor.com/mx/wp-json/wp/v2/posts/54071)); alzas de 8-12 % en GDMTH en 2025 ([Energy21](https://energy21.com.mx/?p=650153)) | Monitor de demanda y factor de potencia |

## 4. Dolores del cliente

| Problema | Evidencia | Solidez |
|---|---|---|
| Paros no programados | Una hora de paro cuesta US$2.3 M en una planta automotriz grande y US$36 mil en bienes de consumo ([Siemens TCOD 2024](https://assets.new.siemens.com/siemens/assets/api/uuid:1b43afb5-2d07-47f7-9eb7-893fe7d0bc59/TCOD-2024_original.pdf)) | Global y comercial |
| Escasez de técnicos | 146 mil técnicos de mantenimiento en el 1T 2026, −5.26 % trimestral; 81 % de los empleadores automotrices tienen dificultad para contratar ([Cluster Industrial](https://clusterindustrial.com.mx/mexico-registra-caida-de-5-26-en-tecnicos-de-mantenimiento-industrial/)) | Media |
| Rotación y pérdida de empleo | Cd. Juárez perdió ~57,500 empleos de maquila entre 2023 y 2025 ([Dallas Fed](https://www.dallasfed.org/research/swe/2026/swe2607)). La última tasa de rotación publicada es de 1996 ([Colmex](https://estudiossociologicos.colmex.mx/index.php/es/article/download/671/671/671)) | **Hueco de información** |
| Trazabilidad de Tier 2/3 | La mayoría de las pymes no califica como proveedora por falta de trazabilidad digital ([Automate](https://www.automate.org/robotics/industry-insights/automatizacion-para-pymes-mexicanas), fuente comercial); incorporación tecnológica lenta en Tier 2 de Nuevo León ([UANL](https://revistainnovaciones.uanl.mx/index.php/revin/article/viewFile/304/285)) | Media |
| Costo eléctrico | CFE cobra recargo si el factor de potencia baja de 90 % ([CONUEE](https://www.gob.mx/cms/uploads/attachment/file/831924/DOCUMENTO-VF1.pdf)) | Oficial parcial |
| Seguridad de máquinas | NOM-004-STPS exige resguardos, paro de emergencia y análisis de riesgo ([guía STPS](https://www.gob.mx/cms/uploads/attachment/file/807655/GUIA_INFORMATIVA_NOM-004.pdf)) | Oficial. Sin datos de inspecciones |
| OEE bajo, aire comprimido, mantenimiento reactivo | Sin estadísticas mexicanas públicas. Las fugas del 10 al 30 % del aire son cifras de proveedores ([Mexico Industry](https://mexicoindustry.com/noticia/mejore-la-eficiencia-en-sus-procesos-y-reduzca-el-consumo-de-energia-con-el-monitoreo-del-aire-comprimido)) | **Hueco**: requiere entrevistas |

### Adopción y financiamiento
- No existe una encuesta nacional reciente con porcentajes de adopción de Industria 4.0 en pymes. El BID habla de una «brecha notable» entre grandes empresas y pymes ([BID](https://publications.iadb.org/publications/spanish/document/Prioridades-para-la-digitalizacion-empresarial-en-America-Latina-y-el-Caribe.pdf)).
- Barreras citadas en estudios mexicanos: infraestructura limitada, costo, talento y resistencia al cambio ([Ciencia ergo-sum, 2025](https://cienciaergosum.uaemex.mx/article/view/24636)).

| Programa | Qué ofrece | Fuente |
|---|---|---|
| Plan México | Deducción acelerada de activo fijo nuevo hasta sep-2030 | [Holland & Knight](https://www.hklaw.com/en/insights/publications/2025/01/nuevos-estimulos-fiscales-como-parte-del-plan-mexico) |
| Nafin 2026 | Hasta MX$120 mil M para mipymes; convenio con Caintra para proveedores | [Nafin](https://www.nafin.com/portalnf/files/secciones/sala-prensa/comunicados-pdf/2026/2-Comunicado_Impulso_a_la_Inversion.pdf) |
| Bancomext 2026 | MX$190 mil M en créditos nuevos | [Expansión](https://expansion.mx/economia/2026/02/02/bancomext-preve-colocar-190-000-mdp-en-nuevos-creditos-en-2026) |
| Sello «Hecho en México» | Meta de 50 % de compras públicas nacionales | [DOF](https://sidof.segob.gob.mx/notas/docFuente/5797479) |

## 5. Competencia y precios

Fecha de consulta: 12-oct-2026. Tipo de cambio de referencia: ~18 MXN/USD. Los precios en USD son de distribuidores extranjeros y no incluyen IVA, aranceles ni flete. Un agregador no oficial reporta ~27.7 % de tasa efectiva para PLC importados ([Wove](https://tariffs.wove.com/us/tariff/8537.10.91.60/delta-dvp-es2-plc)); hay que confirmarlo con un agente aduanal.

### 5.1 Relés programables y micro-PLC

| Producto | Precio | Fuente |
|---|---|---|
| Siemens LOGO! 8 (8 E / 4 relés) | ~$3,750-4,560 MXN | [Mercado Libre](https://listado.mercadolibre.com.mx/siemens-logo-8), [Gastelum](https://www.gastelum.com.mx/logos-y-complementos) |
| Schneider Zelio SR2 | 276-383 USD; sin precio MXN | [CESCO](https://WWW.CESCO.COM/industrial-automation-and-control/motor-control/electrical-relays-and-accessories/control-relay/control-relay/compact-smart-relay-zelio-logic-sr2-sr3-12-io-24v-dc-clock-display-4-relay-outputs) |
| WEG CLIC02 | 246 USD; en México solo por cotización | [MROSupply](https://www.mrosupply.com/products/96649541/as-markdown/) |
| Allen-Bradley Micro820 | 514-1,224 USD | [Gerrie](https://www.gerrie.com/Product/Allen-Bradley-2080-LC20-20QBB) |
| Arduino Opta Lite / WiFi | 146-184 USD | [Arduino US](https://store-usa.arduino.cc/opta-lite) |
| Industrial Shields ESP32 PLC 21 | €239 | [Industrial Shields](https://www.industrialshields.com/shop/esp32-plc-21-2801) |
| Norvi IIOT-AE01-R / Kincony KC868-A8 | 88 USD / 55 USD; sin soporte local | [Norvi](https://shop.norvi.lk/products/norvi-iiot-ae01-r), [Kincony](https://shop.kincony.com/products/kc868-a8-esp32-8-channel-relay-module) |

### 5.2 OEE, andon y monitoreo

| Producto | Modelo y precio | Fuente |
|---|---|---|
| Evocon | 189-319 USD por máquina al mes, en la nube | [Evocon](https://evocon.com/pricing-old/) |
| TeepTrak | Hardware €2,031 más licencia anual | [RS](https://benl.rs-online.com/web/p/condition-monitoring/1830023) |
| Ignition + Sepasoft OEE | Ignition desde 3,018 USD; Sepasoft 22,000-22,700 USD por sitio | [Inductive Automation](https://inductiveautomation.com/pricing), [Sepasoft](https://www.sepasoft.com/?p=32859) |
| Tulip | 100-250 USD por interfaz al mes | [PricingSaaS](https://pricingsaas.com/companies/tulip) |
| Werma WIN, Patlite, Banner | Torres de luz y receptores de €80 a €2,700 | [RS](https://benl.rs-online.com/web/p/signal-tower-components/1845123) |
| Pulsar (Monterrey), JoonX (CDMX) | Locales; sin precio público | [Pulsar](https://pulsarml.com/en/hardware-industrial-sensors-manufacturing), [JoonX](https://joonx.org/iot-industrial) |
| Tractian | Monitoreo de condición; sin precio público | [Mexico Industry](https://mexicoindustry.com/noticia/tractian-la-startup-industrial-de-mayor-crecimiento-de-america-latina-llega-a-mexico-) |

Diez máquinas con Evocon cuestan unos 23,000-38,000 USD al año, casi siempre con nube obligatoria.

### 5.3 Poka-yoke y torque

| Producto | Precio | Fuente |
|---|---|---|
| Mountz MDC-22 / MDC-32 (conteo de tornillos) | 4,835 / 7,615 USD | [Omegatec](https://omegatec.net/?p=101487) |
| Kolver más controlador | 4,390 USD | [TestEquity](https://www.testequity.com/product/10039496-175115) |
| Banner PTL110 (pick-to-light, por nodo) | 182-266 USD | [Powermatic](https://www.powermatic.net/part/banner/ptl110s-t-qp150/1875961) |
| Atlas Copco, Desoutter | Sin precio público | [Atlas Copco](https://atlascopco.com/en-ca/itba/products/assembly-solutions/electric-assembly-systems/power-focus-6000-sku8436180002) |

### 5.4 Gateways y energía

| Producto | Precio | Fuente |
|---|---|---|
| Moxa MGate MB3170 | €518 | [RS](https://pt.rs-online.com/web/p/gateways-iot/2552505?gb=s) |
| Teltonika TRB246 | €176 | [RS](https://befr.rs-online.com/web/p/routers/0735304) |
| Eastron SDM630 (medidor trifásico Modbus) | €123-146 | [Invibit](https://invibitshop.com/products/eastron-sdm630mct-mod-mid-3-phase-ct-energy-meter-with-modbus-rtu-mid-certified) |
| Schneider PowerLogic PM5110 | $7,459 MXN | [Cyberpuerta](https://www.cyberpuerta.mx/Energia/Control-Industrial/Analizadores-de-Energia-y-Potencia/Schneider-Electric-Medidor-de-Potencia-Energia-PowerLogic-PM5110-90-450V-5A-Gris.html) |

El esquema usual (medidor + gateway + plataforma en la nube) es caro y fragmentado. El OPC UA local sin nube solo aparece en equipos caros o de configuración compleja.

### 5.5 Canal
- Marca → distribuidor autorizado o multimarca → integrador local (5 a 50 personas; Querétaro, Bajío, Monterrey, Saltillo) → planta. El integrador suele decidir la especificación.
- Mercado Libre y Cyberpuerta ya venden LOGO! y PM5110, así que existe un canal directo para compras chicas.
- No hay cifras públicas confiables de participación por marca ni por canal.

## 6. Huecos y posicionamiento

**Huecos**
1. **Precio.** OEE de 10 máquinas pasa de 20,000 USD al año con SaaS; una estación de torque con conteo, de 4,800 USD.
2. **Idioma y soporte.** Los equipos baratos no tienen soporte local; los locales no publican precios.
3. **Nube.** Muchas plantas automotrices restringen la salida a internet. Una app web local es un diferenciador.
4. **Licencias.** Ignition y Sepasoft licencian por módulo y por sitio.
5. **Tiempos de entrega.** LOGO! en DigiKey: 4 semanas y 0 en stock; Advantech WISE en Farnell: 15 semanas.
6. **Vertical.** Nadie vende «andon + OEE en una caja» ni un «supervisor poka-yoke» listo para usar.

**Propuesta:** *«Hecho en México, sin nube y sin licencias: equipos de 24 V para riel DIN que ya traen la aplicación de planta.»* Se vende la **solución**, no un PLC genérico, para no competir contra LOGO! y equipos chinos de 55 USD.

**Precios objetivo (hipótesis a validar con clientes, no medidos):**

| Línea | Ancla competitiva | Objetivo sugerido |
|---|---|---|
| AP Monitor, por máquina | LOGO! ~$4,500 MXN; Evocon 189 USD al mes | $5,000-7,000 MXN, pago único; tablero local gratis |
| AP Poka-Yoke, por estación | Mountz 4,835-7,615 USD; Banner ~200 USD por nodo | $12,000-25,000 MXN; recibe la señal OK/NOK de la herramienta existente |
| AP Gateway | Moxa €518 más medidor y nube | $4,000-6,000 MXN; kit con medidor ~$8,000 MXN |

**Cómo llegar al mercado**
1. Integradores del Bajío y el norte, con margen de distribuidor y kits demo.
2. Pilotos en Tier 2 y 3 automotriz con máquinas sin PLC; exportación CSV y MQTT para que TI acepte el equipo.
3. Venta directa en Mercado Libre para el gateway y el monitor básico.
4. Evidencia mínima para automotriz: pruebas EMC, aislamiento RS-485 real, ciberseguridad básica y garantía local. Sin certificación, solo se vende como prototipo.

**Riesgos:** Opta y LOGO! ya ofrecen web y MQTT en parte; los compradores automotrices exigen marcas aprobadas; Pulsar y JoonX son locales y tienen capital de riesgo.

## 7. Normas y mejores prácticas

### 7.1 PackML y máquinas de estados
- **ANSI/ISA-TR88.00.02-2022** define tipos de estado, modos, el modelo de estados y el conjunto mínimo de PackTags ([Control Engineering](https://www.controleng.com/articles/updated-packml-standard-released/)). **OPC 30050** lo lleva a OPC UA ([OPC Foundation](https://reference.opcfoundation.org/PackML)).
- **[CG]** Los 17 estados: Stopped, Starting, Idle, Execute, Completing, Complete, Resetting, Holding, Held, Unholding, Suspending, Suspended, Unsuspending, Stopping, Aborting, Aborted y Clearing. Comandos: Reset, Start, Stop, Hold, Unhold, Suspend, Unsuspend, Abort y Clear. Modos base: Production, Maintenance y Manual. Las fuentes de la búsqueda no listan los nombres de forma coincidente: confirmar con el texto de ISA u OMAC.
- **GRAFCET (IEC 60848) y SFC (IEC 61131-3)** **[CG]**: GRAFCET especifica, SFC ejecuta. Agregar SFC a AP Lógica es mucho trabajo.
- **IEC 61499 (4diac FORTE)** es EPL-2.0 y no tiene port oficial al ESP32 ([4diac](https://github.com/eclipse-4diac/4diac-forte)). **QP/C** es GPLv3 o comercial ([QP/C](https://github.com/QuantumLeaps/qpc)).
- **Recomendación:** tabla propia de transiciones (estado × comando → estado) en C++, sin dependencias, con un subconjunto de estados según el modo.

**Mapa a OEE [CG]**

| Término de OEE | De dónde sale |
|---|---|
| Tiempo productivo | Tiempo en Execute |
| Paros no planeados | Tiempo en Held, Suspended y Aborted |
| Desempeño | `ProdProcessedCount` contra la velocidad nominal |
| Calidad | `ProdDefectiveCount` |
| Causa del paro | `StopReason` |

### 7.2 OEE, causas de paro y andon
- OEE = disponibilidad × desempeño × calidad. ISO 22400-2:2014 la define como KPI de MES, pero es de pago y varios autores señalan inconsistencias ([TeepTrak](https://teeptrak.com/en/how-to-calculate-oee-industrial-production-2026/)). Documentar la fórmula exacta que use AP Electric.
- **[CG]** Catálogo de causas en dos niveles (categoría y causa) sobre las 6 grandes pérdidas de Nakajima; microparos con umbral configurable (típico menor de 2 a 5 minutos), detectados sin pedir causa al operador.
- **[CG]** Andon con escalamiento por temporizador (líder, supervisor, mantenimiento o calidad). El aviso por MQTT sale del gateway, nunca del lazo de control.

### 7.3 Trazabilidad y poka-yoke (IATF 16949)
- **8.5.2.1:** plan de trazabilidad por producto, proceso y planta; segregar producto sospechoso; registros. **10.2.4:** proceso documentado para decidir dónde usar error-proofing ([AIAG](https://blog.aiag.org/core-tools-and-iatf-169492016-overview); detalle de cláusulas en [Elsmar](https://elsmar.com/elsmarqualityforum/threads/iatf-8-5-2-1-identification-and-traceability.92260/), un foro). Los textos oficiales son de pago.
- **[CG]** Verificación periódica del poka-yoke con piezas «conejo rojo» y registro de cada falla.
- Los requisitos específicos de cada armadora varían ([ejemplo: Suzuki](https://suppliers.motherson.com/storage/supplier-expectations/vision/Appendix_M-Suzuki_CSR_R02.pdf)).
- GS1 DataMatrix se basa en ISO/IEC 16022 ([GS1](https://www.gs1.org/docs/events/2016/Healthcare%20Conference%20Dubai/Day%202/GS1%20DataMatrix_Ask%20the%20experts_Chuck%20Biss_Dubai19April.pdf)). La calificación de marcado directo con ISO/IEC 29158 debe confirmarse: un catálogo la marca como anulada ([Keyence](https://www.keyence.com/ss/products/auto_id/codereader/code_verification/tr-29158.jsp)).
- **Diseño de estación:** enclavamiento local (la salida de liberación solo se activa si lectura válida, presencia y paso anterior están bien); bitácora encadenada con hash (número de serie, hora, resultado, operador, versión de receta); envío al gateway con acuse de recibo.

### 7.4 Comunicaciones
Orden recomendado:
1. **Modbus RTU** con un mapa de registros de PackTags estable y versionado (ya existe el esclavo RTU).
2. **Modbus TCP y MQTT con Sparkplug B** en AP GATE. Sparkplug 3.0 es la norma ISO/IEC 20237 ([ARC](https://www.arcweb.com/blog/sparkplug-now-official-isoiec-standard)); Eclipse Tahu es EPL-2.0 ([GitHub](https://github.com/eclipse-tahu/tahu)).
3. **OPC UA** con el modelo OPC 30050 en un gateway Linux con open62541, MPL-2.0 ([GitHub](https://github.com/open62541/open62541)). En el ESP32 solo hay ports de la comunidad ([Hackaday](https://hackaday.io/project/176627-open-source-opc-ua-server-running-on-esp32)).
4. **EtherNet/IP y PROFINET** solo con gateways de terceros. No hay datos específicos de México; HMS reporta EtherNet/IP dominante en Norteamérica y PROFINET exigido en automotriz ([HMS](https://cdn.hms-networks.com/tech-blog/blogpost/hms-blog/2025/07/10/how-much-are-you-losing-on-industrial-networks)).
5. **IO-Link:** no hay pila abierta madura para ESP32 ([TEConcept](https://www.st.com/ja/partner-products-and-services/teconcept-io-link-master-software-stack.html)). Fuera de la primera etapa.

### 7.5 Seguridad de máquina: lo que AP Control no debe hacer
- Normas: [NOM-004-STPS-1999](https://platiica.economia.gob.mx/normalizacion/nom-004-stps-1999/) (vigente; existe un proyecto PROY-NOM-004-STPS-2020, hay que verificar en el DOF), [NOM-029-STPS-2011](https://platiica.economia.gob.mx/normalizacion/nom-029-stps-2011/), [ISO 13849-1](https://www.pilz.com/en-INT/support/law-standards-norms/functional-safety/en-iso-13849-1/index.html), IEC 60204-1 e ISO 13850 ([resumen](https://www.motorcontrolwarehouse.co.uk/media/pdf/E-Stop%20safety%20measures%20-%20MCW.pdf)).
- Reglas de diseño:
  1. AP Control **no** ejecuta funciones de seguridad. Paro de emergencia, guardas y cortinas van a un relé o PLC de seguridad; AP Control solo lee su estado.
  2. No rearma paros ni guardas por software, Modbus o MQTT.
  3. El modo Maintenance de PackML no sustituye el bloqueo y etiquetado (LOTO).
  4. Al arrancar o perder comunicación, las salidas de proceso van a estado seguro (apagadas). `ARR_ULTIMO` y `COM_MANTENER` deben estar prohibidos en cargas de proceso.
  5. El vigilante y el STOP del PLC son diagnóstico, no seguridad. Los manuales dirán «no certificado como dispositivo de seguridad».

### 7.6 Ciberseguridad mínima (IEC 62443-4-2, SL1-SL2)
Ver el [resumen de INCIBE-CERT](https://www.incibe.es/en/incibe-cert/blog/iec-62443-4-2-need-secure-components). Lista mínima:
- credenciales únicas por equipo, sin contraseña por defecto;
- MQTT con TLS y autenticación;
- escritura Modbus deshabilitada por defecto o limitada a registros permitidos;
- OTA firmada, Secure Boot y cifrado de flash del ESP32-C3 **[CG]**;
- puerto de diagnóstico bloqueado en producción;
- bitácora de cambios de configuración y de modo, con su `Origen`.

### 7.7 Código abierto
| Proyecto | Licencia | ¿Se puede usar en un producto cerrado? | Recomendación |
|---|---|---|---|
| open62541 | MPL-2.0 | Sí | Usar en el gateway |
| Eclipse Tahu | EPL-2.0 | Sí | Usar |
| Node-RED | Apache-2.0 | Sí | Gateway y prototipos |
| FUXA | MIT | Sí | HMI web para demos |
| OpenPLC v4 | MIT, solo Linux | Sí | Referencia para el gateway, no el ESP32 |
| 4diac FORTE | EPL-2.0 | Sí, con cuidado | Opción futura |
| ROS-Industrial `packml_sm` | Apache-2.0 (ROS 1) | Sí | Referencia de la máquina de estados |
| matiec, Beremiz (runtime C++), ESPHome, Tasmota, QP/C | GPL o dual con GPL | No dentro del producto | Evitar |
| IoTaWatt, OpenMES | No confirmada | Sin verificar | Solo referencia |

Regla: el firmware solo incluye código propio o con licencia MIT, BSD, Apache, MPL o EPL. Revisar el archivo LICENSE de cada repositorio antes de usarlo.

## 8. Qué existe ya en el repositorio

| Parte | Reutilizable para | Qué falta |
|---|---|---|
| **AP Control** (`firmware/APControl`): orígenes de cada orden, fallas, bitácora de eventos, Modbus RTU esclavo, vigilante | Estado, causas de paro, mapa Modbus | Modelo de unidad (PackML), hora real y bitácora en flash |
| **AP Lógica** (escalera e IL, ciclo de 10 ms) | Lógica de usuario, condiciones de poka-yoke | Exponer el estado PackML en el área S; no tiene SFC |
| **7R Tour** (7 relés, 8 entradas de 24 V, RS-485 aislado) | Salidas, entradas, esclavo Modbus | Fabricarlo y medirlo |
| **AP UNO, AP INPUT (DI8), AP PRO DO8, AP AI4** | Entradas de torreta y de ciclo, balizas, 4-20 mA | Entrada de conteo rápido |
| **AP GATE** (maestro Modbus RTU) y **AP NODE/AP BUS** | Gateway, medidores de terceros, varias máquinas | Ethernet, Modbus TCP, MQTT Sparkplug, OPC UA |
| **AP Studio** (app web con editor de escalera) | Tablero local, configuración | Tablero OEE y causas de paro |

Huecos técnicos que comparten casi todos los productos: hora de cada evento y bitácora en memoria flash, Ethernet y Modbus TCP, entrada de conteo rápido, transformadores de corriente de CA y homologación del módulo de radio. **Nada del hardware está fabricado ni medido.**

## 9. Oportunidades priorizadas

Escala de 1 a 5. Impacto (I) y reutilización (R): 5 es mejor. Esfuerzo (E) y riesgo (Rg): 5 es peor. Son estimaciones de escritorio.

| # | Oportunidad | Cliente | MVP con lo existente | I | E | R | Rg |
|---|---|---|---|---|---|---|---|
| 1 | Monitor OEE y andon con torre de luces | Tier 2/3, inyectoras, maquinados | AP UNO + AP INPUT + contadores + tablero en AP Studio | 5 | 2 | 5 | 1 |
| 2 | Demanda y factor de potencia GDMTH | Naves en GDMTH | AP GATE + medidor Modbus de terceros; alarma por DO8 | 5 | 2 | 5 | 2 |
| 3 | Gateway Modbus RTU a MQTT | Integradores, mantenimiento | AP GATE + AP Control | 4 | 2 | 5 | 2 |
| 4 | Contador de piezas y e-kanban | Líneas de ensamble y arnés | AP INPUT + DO8 + escalera | 4 | 2 | 5 | 1 |
| 5 | Poka-yoke de estación | Ensamble automotriz | AP INPUT + DO8 + 7R Tour con lógica | 4 | 3 | 4 | 3 |
| 6 | Probador de continuidad de arnés (64-256 puntos) | Talleres de arnés | Placa nueva de matriz; reutiliza ESP32 y app | 5 | 4 | 2 | 2 |
| 7 | Kit educativo AP Lab | CONALEP, universidades tecnológicas | 7R Tour 24DC + E/S + AP Studio | 4 | 2 | 5 | 1 |
| 8 | Tablero de bombeo y cisterna | Organismos operadores, condominios | AI4 + DO8 o RED4 con contactor + AP GATE | 4 | 3 | 5 | 3 |
| 9 | Aire comprimido y fugas fuera de turno | Plantas con compresor | AI4 (presión 4-20 mA) + medición del compresor | 4 | 2 | 4 | 1 |
| 10 | Registro de temperatura en cuarto frío | Alimentos, farmacias, CEDIS | AI4 + alarma + bitácora; exigirá calibración trazable | 3 | 2 | 4 | 3 |
| 11 | Invernadero: riego y ventilación | Productores medianos | DO8 + AI4 + horario solar | 3 | 2 | 5 | 1 |
| 12 | Solar en nave: monitoreo e inyección cero | Instaladores | AP GATE leyendo inversor y medidor | 3 | 3 | 4 | 4 |
| 13 | Predictivo «lite» (corriente y temperatura) | Mantenimiento en pymes | AI4 + transformadores de corriente + RTD | 4 | 3 | 3 | 1 |
| 14 | Vibración | Igual que la anterior | Falta cabezal con acelerómetro MEMS | 4 | 4 | 2 | 1 |
| 15 | Retrofit de prensas, inyectoras y hornos (solo supervisión) | 689 inyectores | Gateway + monitor OEE; **no** sustituir el control de seguridad | 4 | 4 | 3 | 5 |
| 16 | Habilitar la máquina con RFID | Plantas que auditan NOM-004 | Lector por Qwiic + relé de habilitación **fuera** del circuito de seguridad | 3 | 3 | 3 | 4 |
| 17 | Lectura de DataMatrix | Trazabilidad Tier 2 | Lector comercial conectado al gateway | 3 | 4 | 1 | 1 |
| 18 | Banco de fin de línea de baterías y VE | Proveedores de paquetes | Solo secuenciador; la medición es de instrumentos certificados | 3 | 5 | 2 | 5 |

Evidencia de apoyo: probadores de arnés caseros con ESP32 y multiplexores ya circulan ([AAC](https://forum.allaboutcircuits.com/threads/cable-harness-tester-with-3-connectors-30-test-points.205985/post-1975061)); guías de OEE casero con ESP32 ([IMD](https://industrialmonitordirect.com/ru/blogs/knowledgebase/diy-oee-monitoring-with-esp32-protocol-based-vs-io-collection-methods)); Tractian reporta casos en México con cifras autorreportadas ([Tractian](https://tractian.com/es/casos-de-estudio/grupo-mexico)); la SEP abre 15 especialidades técnicas, entre ellas Robótica y Automatización ([Infobae](https://www.infobae.com/mexico/2025/09/24/la-sep-actualizara-plan-de-estudios-de-15-carreras-tecnicas-enfocadas-en-ia-y-semiconductores/)).

## 10. Familias y submarcas propuestas

**AP Electric Industrial**
- **AP Monitor**: OEE, andon, conteo y e-kanban (1, 4).
- **AP Energía**: demanda, factor de potencia, solar y aire comprimido (2, 9, 12).
- **AP Gateway**: AP GATE y AP NODE, Modbus a MQTT, Modbus TCP después (3).
- **AP Poka-Yoke**: estaciones de error-proofing (5, 16), con la leyenda «no es un dispositivo de seguridad».
- **AP Test**: probador de arnés y secuenciador de fin de línea (6, 18). Es la única línea que pide una placa nueva y la que más diferencia.
- **AP Predict**: corriente, temperatura y, más adelante, vibración (13, 14).

**Otras líneas:** AP Electric Home (residencial), AP LED (letreros y luminarias), **AP Agua**, **AP Agro**, **AP Frío**, **AP Lab / AP Studio** (educación y app).

Los nombres no están registrados: cada uno necesita su búsqueda en MARCia del IMPI antes de imprimirse.

## 11. Hoja de ruta propuesta

| Etapa | Qué | Condición para pasar |
|---|---|---|
| 0 | Fabricar y medir 3 prototipos del 7R Tour 24DC, AP INPUT, DO8, AI4 y AP GATE | `PLAN_VERIFICACION.md` cerrado |
| 1 | **PackML en AP Control**: tabla de estados, tiempos por estado, causas de paro, mapa Modbus de PackTags, bitácora con hora | Pruebas en la PC y en banco |
| 2 | **AP Monitor** y **AP Energía** con tablero local en AP Studio; **AP Lab** | 3 pilotos en Tier 2/3 y 1 integrador |
| 3 | **AP Gateway** con MQTT Sparkplug B (TLS, escritura restringida) y OPC UA en gateway Linux | Pruebas con SCADA real |
| 4 | **AP Poka-Yoke** y **AP Agua** | Revisión de riesgos y matriz de causas |
| 5 | **AP Test** y, solo con socio y evaluación de riesgos, retrofit, RFID y fin de línea | Certificaciones y responsabilidad definidas |

Orden de certificación: pruebas de seguridad eléctrica (NOM-003-SCFI con un organismo acreditado) y homologación del radio (IFT-017-2023) antes de cualquier venta.

## 12. Pendientes y preguntas abiertas

Qué **no** sabemos y cómo cerrarlo:
1. Texto oficial de PackML (17 estados, comandos, modos): comprar o consultar ISA-TR88.00.02-2022 u OMAC.
2. ISO/IEC 29158 y los textos de IATF 16949 y ISO 22400-2: confirmar con los documentos originales.
3. Factor de potencia de 0.97 en 2026 y vigencia de PROY-NOM-004-STPS-2020: verificar en el DOF.
4. Disposición a pagar: 3 a 5 entrevistas o pilotos (Tier 2/3 del Bajío y el norte, un integrador, un organismo de agua).
5. OEE típico, rotación actual, inspecciones de la STPS: no hay datos públicos.
6. Cifras 2025 de alimentos, empaque y metalmecánica: consultar la EAIM y la EMIM del INEGI.
7. Precios MXN de Zelio, WEG CLIC02, Opta, Teltonika y Moxa: solo hay precios en USD o EUR de distribuidores extranjeros.
8. Tasa efectiva de importación de PLC: confirmar con un agente aduanal.
9. Búsqueda en MARCia de los nombres de submarcas.

## 13. Fuentes
Todas las fuentes están enlazadas en el texto. Las páginas de proveedores, prensa comercial y foros se usaron solo como señales y están marcadas como tales; los precios de distribuidores extranjeros no incluyen impuestos ni flete.
