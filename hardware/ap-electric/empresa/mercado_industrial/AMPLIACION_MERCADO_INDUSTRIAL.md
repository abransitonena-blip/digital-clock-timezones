# Ampliación del estudio de mercado industrial: AP Monitor 24

> **Estado: estudio de escritorio, consulta del 14-oct-2026.** Amplía `ESTUDIO_MERCADO_INDUSTRIAL.md` y `ANALISIS_ECOSISTEMA.md` sin repetirlos. Nada de AP Electric está fabricado, medido ni certificado. AP Monitor 24 no es función de seguridad.
>
> **Limitación de método (leer primero).** En esta sesión `WebFetch` no pudo abrir ninguna página (el proxy rechazó los dominios). Todo lo de abajo sale de **extractos devueltos por WebSearch**, no de la lectura completa de cada página. Por eso cada cifra lleva su URL, pero conviene abrir el enlace antes de citarla fuera de AP. Las páginas de proveedores, agregadores y foros están marcadas como tales.
>
> Marcas: **[V]** dato visto en el extracto de la fuente enlazada (consulta 14-oct-2026) · **[V-prov]** afirmación de un proveedor o de un agregador, no independiente · **[CG]** conocimiento general sin verificar · **[H]** hipótesis por validar · **[C]** cálculo con supuestos explícitos · «no encontrado» = no apareció en las búsquedas hechas.
>
> Tipo de cambio de referencia: 18 MXN/USD (el mismo del estudio previo) **[H]**.

## 0. Resumen en diez líneas

1. **PNP contra NPN no tiene dato cuantitativo público.** Las fuentes de fabricantes coinciden en que Europa y Norteamérica usan PNP y Asia usa NPN; otras fuentes se contradicen (§1.2). Para AP Monitor 24 rev B (entradas solo PNP) el riesgo es real en máquinas asiáticas y solo se cierra con fotos de máquinas reales.
2. **Muchos PLC aceptan los dos tipos** por cableado del común (Mitsubishi FX con terminal S/S, [V] oficial). Eso significa que el sensor que trae una máquina asiática puede ser de cualquiera de los dos tipos, y AP no puede suponer nada.
3. **Competidores locales con presencia real:** Pulsar (Monterrey y CDMX, suscripción, sin precio), Monitor App (Irapuato, Guanajuato, sin precio), JoonX (CDMX, sin precio ni producto claro). Ninguno publica precios.
4. **Corrección al estudio previo:** Evocon hoy aparece en Capterra con €159 / €209 / €269 por mes (§3.2); los US$189-319 del estudio previo vienen de una página antigua. Las cifras de Evocon, sin hardware, son solo anclas.
5. **El valor de un punto de OEE** en una línea chica de Tier 2 (supuestos §7) es del orden de **MXN 16,000 a 96,000 al año**; un microparo de 20 min por turno equivale a ~4.2 puntos [C, con supuestos]. Con ese rango, el precio objetivo de MXN 5,000-7,000 se paga con una fracción de un punto; **pero eso depende de que el cliente de verdad recupere esa capacidad y la venda**.
6. **No encontré un apoyo público específico para comprar equipo de OEE o andon.** Lo aplicable es la deducción inmediata del Plan México (hasta sep-2030, con constancia de un comité) y crédito de Nafin/Bancomext para activo fijo (§6).
7. **TI/OT:** no encontré el reglamento de una planta automotriz concreta. Lo que sí hay son marcos (IEC 62443, NIST 800-82, TISAX/VDA ISA 6.0) y una lista práctica de lo que TI va a pedir (§5). La salida más limpia es operar **sin salida a internet y sin Wi-Fi** en el piloto.
8. **Los constructores de máquinas (OEM) son un canal más que un cliente:** la maquinaria de empaque importada pesa 89 % de la demanda (PMMI vía The Food Tech), así que el OEM mexicano es chico y las máquinas importadas llegan con su propio control.
9. **Perfil ideal del piloto:** taller o Tier 2 del Bajío con 5-20 máquinas con torre de luz, sin MES, decisión en una persona (§8).
10. **Lo que más cambiaría el rumbo:** que la mayoría de las máquinas visitadas tenga sensores NPN o señales de torre no tomables, o que TI prohíba cualquier dispositivo nuevo (§10).

---

## 1. Constructores de máquinas (OEM) y talleres en México

### 1.1 Quién construye y quién importa

| Dato | Valor | Fuente | Marca |
|---|---|---|---|
| Maquinaria de empaque: peso de la importada en la demanda mexicana | 89 % de la demanda total; la producción nacional se concentra en equipos básicos y volúmenes bajos | PMMI citado por [The Food Tech](https://thefoodtech.com/maquinaria-para-envasado-y-procesamiento/el-mercado-de-maquinaria-de-envasado-en-mexico-en-2023-estos-son-los-pronosticos/) (año del informe: no confirmado) | [V] |
| Máquinas de inyección vendidas en México | Alemania US$74.8 M; Japón US$72.2 M; China fuerte en baja capacidad (fecha de la nota no visible) | [Mexico Industry](https://mexicoindustry.com/noticia/la-industria-del-plstico-crece-paulatinamente) citando a Expo Plásticos | [V], fecha por confirmar |
| Importación de máquinas de taladrar, escariar, fresar o roscar (partida 84.58, excl. tornos), 2024 | Alemania US$23 M; China US$22.7 M; EE. UU. US$22.5 M; España US$15.3 M; Japón US$12.6 M | [DataMéxico, Sec. de Economía](https://www.economia.gob.mx/datamexico/es/profile/product/machines-including-units-machines-for-drilling-boring-threading-or-tapping-threading-metal-removing-material-other-than-lathes-including-turning-centers-of-heading-8458) | [V] |
| Partes de máquinas-herramienta para metal con arranque, 2024 | EE. UU. US$80.8 M; Alemania US$61.2 M; Japón US$35.2 M; China US$24 M | [DataMéxico](https://www.economia.gob.mx/datamexico/es/profile/product/parts-and-accessories-of-machine-tools-for-working-metals) | [V] |
| Número de OEM mexicanos de maquinaria | **No encontrado** | — | — |
| Edad del parque instalado de inyectoras, prensas, CNC | **No encontrado** | — | — |
| Recolección de datos en inyección | Un artículo de la UABC dice que los datos se suelen recopilar de forma manual, con fallas u omisiones | [Redalyc](https://www.redalyc.org/journal/5122/512267931001/512267931001.pdf) | [V], un estudio |

**Lectura.** El parque es mixto: Alemania y Japón empatan en inyección, y China pesa en máquinas chicas. En maquinados hay Alemania, China, EE. UU. y Japón. **No hay una procedencia dominante**, así que no se puede suponer un tipo de sensor por país de la máquina **[H]**.

**OEM y talleres mencionados en directorios (autodeclarados, sin verificar; sirven para armar lista de prospectos, no como dato de mercado):**

| Empresa | Qué dice de sí misma | Fuente |
|---|---|---|
| MexiMaq | Maquinaria de empaque automática y semiautomática, desde 1966 | [MexiMaq](https://www.meximaq.com/) vía búsqueda |
| MOCE Ingeniería | Estaciones de trabajo para líneas de ensamble (automotriz, alimentos, metalurgia) | [Dirind](https://www.dirind.com/dim/robotica-lineas-ensamble1.html) |
| Teratronix | Automatización de maquinaria de empaque | [El Empaque](https://www.elempaque.com/mexico/proveedores/plc-y-hmi-para-control-de-l%C3%ADneas-de-empaque) |
| RIC Manufacturing (León, Gto.), Macimex, Santinel CNC | Talleres CNC del Bajío | [Lewei Precision](https://leweiprecision.com/top-cnc-machining-companies-in-mexico-2026-nearshoring-profiles-and-how-to-choose/), guía de un fabricante chino que vende a la competencia |

### 1.2 PNP contra NPN: lo que hay y lo que no

**Resumen: no existe una estadística pública de participación de PNP y NPN por región.** Hay descripciones cualitativas de fabricantes y cifras de blogs sin fuente.

| Fuente | Qué afirma | Calidad |
|---|---|---|
| [Balluff (guía en español, México)](https://my.balluff.com/assets/services/basics/pdfs/es/03_Fundamentals-of-Automation_NPN-vs-PNP_mx_es_LTR.pdf) | PNP es común en Europa y Norteamérica; NPN es común en Asia | [V], fabricante de sensores, sin cifras |
| [Autosen](https://autosen.com/en/Worth-knowing/Applications-solutions/PNP-or-NPN) | PNP se usa sobre todo en Europa; NPN todavía se usa en parte en Asia | [V-prov] |
| [Viox](https://viox.com/npn-vs-pnp-proximity-sensors) | Una versión dice que Norteamérica usa PNP y que Asia y Europa usan NPN en automotriz; otra afirma lo contrario para Europa | [V-prov], se contradice |
| [Lambdageeks](https://lambdageeks.com/?p=249468) | ~90 % de salidas asiáticas NPN, ~90 % de europeas PNP, EE. UU. ~60/40 NPN-PNP | Sin fuente de datos; no usar |
| [Industrial Monitor Direct](https://industrialmonitordirect.com/blogs/knowledgebase/pnp-vs-npn-transistor-outputs-european-plc-preference) | PNP ~98-100 % de las instalaciones nuevas en Europa; NPN en equipo japonés antiguo | Blog de un distribuidor, sin fuente; no usar |
| [Zbotic](https://zbotic.in/photoelectric-sensor-wiring-npn-vs-pnp-output-types/) | Muchos PLC de marcas asiáticas (Mitsubishi, Keyence, Omron) usan entradas NPN | Blog, sin verificar |

**Qué dicen las entradas de los PLC (esto importa más que el sensor):**

- **Mitsubishi FX3U/FX3UC:** la terminal S/S cambia el tipo de entrada: a 0 V para fuente (sensor PNP) y a 24 V para sumidero (sensor NPN) ([FAQ oficial de Mitsubishi](https://fa-faq.mitsubishielectric.com/faq/show/22255)) **[V]**. Es decir, la misma máquina puede estar cableada de cualquiera de las dos formas.
- **Omron CP1E/CP1L:** varios distribuidores listan «PNP/NPN input» en modelos concretos ([RS](https://uk.rs-online.com/web/p/plcs-programmable-logic-controllers/2158797)) **[V-prov]**; el manual de Omron no apareció.
- **Siemens S7-300/400:** la documentación oficial habla de módulos «P-lesend» (lee PNP) y «M-lesend» (lee NPN), con la mayoría P-lesend ([Siemens](https://www.ad.siemens.com.cn/club/bbs/upload/635046478371096250.pdf)) **[V]**, según el extracto.
- **LOGO! estándar de CC:** un blog afirma que el común va a 0 V, o sea que lee sensores PNP ([IMD](https://industrialmonitordirect.com/blogs/knowledgebase/siemens-logo-input-wiring-pnpnpn-configuration-guide)) **[V-prov]**.
- **Sensores:** varias familias (Omron E3FA, Autonics) existen en ambas versiones por código de pedido ([Misumi](https://in.misumi-ec.com/vona2/detail/221005394815/), [Autonics](https://www.wolfautomation.com/content/autonics-photosensor-orderinfo.pdf)). El tipo se decide al comprar.
- **Máquinas chinas y mexicanas:** **no encontrado** ninguna fuente por origen. Tratar como **[H]**: dentro de una misma planta habrá mezcla.

**Qué implica para AP Monitor 24 rev B [H]:**

1. AP debe tomar de la máquina, sobre todo, la **señal de la torre de luz** y el **fin de ciclo**. Esas señales las genera la salida del PLC de la máquina, que puede ser de tipo fuente (da 24 V) o de tipo sumidero (cierra a 0 V). Con salida tipo sumidero, la entrada solo-PNP **no** lee la señal.
2. Un contacto seco (relé de la máquina) funciona con cualquier tipo: es la opción segura y se debe preguntar por ella.
3. Recomendación para decisión de producto: tratar la **entrada bidireccional (optoacoplador de doble LED, sirve con PNP y NPN)** como la primera mejora, igual que ya dice `ANALISIS_ECOSISTEMA.md`. Esta ampliación **no** cambia esa decisión; solo suma que el riesgo no se puede acotar con datos públicos.
4. Prueba barata en las primeras visitas: foto del sensor de la máquina (etiqueta o código de pedido) y de la regleta de la torre, y medir con multímetro si el cable de la lámpara es +24 V o 0 V cuando está apagado.

### 1.3 Cómo compran (lo que se sabe y lo que no)

| Pregunta | Resultado |
|---|---|
| ¿Cómo compra un OEM mexicano sus sensores y controles? | **No encontrado.** Los directorios (Dirind, El Empaque) muestran que los OEM y los integradores se anuncian junto a distribuidores de PLC y sensores (Allen-Bradley, Siemens, Endress+Hauser, Emerson). Hipótesis: compra por marca y distribuidor, con la marca elegida por el cliente final de la máquina **[H]** |
| ¿Cómo compra un taller de maquinado o inyección? | **No encontrado.** Hipótesis: el dueño o el jefe de mantenimiento compra por distribuidor o Mercado Libre, sin proceso formal de ingeniería **[H]** |
| ¿Qué protocolos exigen? | Para CNC Fanuc, el canal habitual es FOCAS (propietario, Ethernet) y MTConnect (estándar abierto de solo lectura); para equipos sin interfaz digital, la vía es sensor externo o cámara ([MachineMetrics](https://www.machinemetrics.com/connectivity/protocols/focas), [Fabrico](https://www.fabrico.io/es/blog/mtconnect/)) **[V-prov]**. Euromap 63/77 en inyección: **no encontrado**. Exigencia de protocolos por parte de OEM o talleres mexicanos: **no encontrado** |
| Implicación | AP Monitor 24 trabaja con **señales discretas** (torre, fin de ciclo, contacto). No compite en CNC con FOCAS/MTConnect; ahí gana quien lea el control. Hay que declararlo en la ficha **[H]** |

---

## 2. Integradores y distribuidores (canal o competencia)

**Aviso:** todos los listados son autodeclarados en directorios; ninguna autorización de marca fue confirmada con el fabricante. Verificar con el localizador de socios de cada marca antes de contactar.

| Plaza | Empresa | Qué dice de sí misma | Papel probable **[H]** | Fuente |
|---|---|---|---|---|
| Bajío / Centro | HERMOS | Distribuidor Allen-Bradley Bajío; arquitectura de control | Canal (distribuidor); su marca dominante compite con la oferta de AP | [Hermos](https://hermos.com.mx/) |
| Querétaro | Pymatek Automation | Representa Allen-Bradley, ABB, Siemens, Mitsubishi y más de 100 marcas | Canal | [Automa](https://automa.net/business-directory/mexico?page=2) |
| Querétaro | Automatización Industrial Bajío SA de CV | Integrador de automatización y control | Canal | [SDI](https://sdindustrial.com.mx/directorio-integradores/integradores/automatizacion-industrial-bajio-sa-de-cv/) |
| Querétaro | Automatización Industrial Querétaro | PLC, HMI, estaciones, CNC | Canal | [SDI](https://sdindustrial.com.mx/directorio-integradores/integradores/roberto-trejo-munoz/) |
| Querétaro | Integración Total en Automatización | Integrador y distribuidor | Canal | [Guía México](https://guia-queretaro.guiamexico.com.mx/automatizacion-rub/queretaro/empresas-guia.html) |
| Monterrey (y Querétaro) | Integradora de Automatización Industrial (IEC) | PLC, HMI, SCADA, robótica, visión | Canal o competencia en proyectos | [IEC](https://iecautomatizacion.com/integradora-de-automatizacion-industrial-saltillo/) |
| Monterrey / Saltillo | G Monterrey Industrial (Grupo MI) | Distribuidor de Siemens, Mitsubishi Electric, Pilz, Pepperl+Fuchs, Schunk, KUKA | Canal | [Automate](https://www.automate.org/companies/g-monterrey-industrial) |
| Saltillo | SEA Soluciones en Automatización | PLC, robots, ingeniería eléctrica | Canal | [Automa](https://automa.net/es/compania/sea-soluciones-en-automatizacion) |
| Saltillo | Adfee Automatización e Integración; Inteso; JJ Industrial Consulting | Listados como integradores o consultoras | Por verificar | [SDI](https://sdindustrial.com.mx/directorio-integradores/) |
| Edomex | AIOSA | Distribuidor (Allen-Bradley, Omron, Mitsubishi, Schneider, Siemens) | Canal | [Automa](https://automa.net/business-directory/mexico?page=2) |
| Cd. Juárez | PREDICSA | Siemens, Pepperl+Fuchs, Eaton | Fuera del foco del piloto | [Automa](https://automa.net/business-directory/mexico?page=2) |
| Querétaro / Monterrey | Centros FA de Mitsubishi Electric | Anunciados en 2017; **vigencia sin confirmar** | Referencia de marca | [Plant Automation](https://www.plantautomation-technology.com/news/mitsubishi-electric-establishes-fa-service-facilities) |
| CDMX y Guadalajara | **No encontré** integradores con fuente en esta búsqueda | — | Pendiente | — |

**Directorios para construir la lista de prospectos:** [SDI Directorio de integradores](https://sdindustrial.com.mx/directorio-integradores/), [Dirind](https://www.dirind.com/dae/integradores1.html), [Automa](https://automa.net/business-directory/mexico?page=2).

**Lectura.** Los integradores que revenden Allen-Bradley y Siemens ganan en los márgenes del hardware de marca; un equipo barato sin marca aprobada no les mejora el negocio salvo que lo vendan como parte de un servicio (instalación y soporte) **[H]**. Probablemente el primer canal realista sea el integrador chico (5-50 personas) que hoy instala tableros de conteo a medida **[H]**; no hay dato que lo confirme.

---

## 3. Competidores locales y regionales de OEE/andon, con precios publicados

### 3.1 Locales (México)

| Empresa | Qué se sabe | Precio publicado | Fuente |
|---|---|---|---|
| **Pulsar** (Monterrey y CDMX; también Palo Alto y Miami) | Monitoreo OEE, paros y andon digital con sensores IoT, instalación sin cambios en el PLC; hardware más software por suscripción; clientes citados por un tercero: Femsa, Sigma, Gruma, Cemex; Serie A de ~US$8 M en feb-2024 según el mismo tercero | **No encontrado** (contacto comercial) | [Pulsar](https://www.pulsarml.com/en/machine-monitoring-system), [Descubre](https://www.descubre.vc/pulsar), [Cathay Capital](https://www.cathaycapital.com/behind-the-term-sheet-meet-pulsar-the-ai-startup-out-to-optimize-manufacturing-in-latam-the-us/) |
| **Monitor App** (Irapuato, Gto.; fundada en 2019) | SaaS de monitoreo y OEE con sensores no invasivos; más de 30 KPI; 38 clientes y más de 100 proyectos en 2023 según una nota; caso Walor Mex (el cliente declara 15 % menos paros y retorno en el primer mes: afirmación del propio cliente en nota promocional) | **No encontrado** | [Cluster Industrial](https://clusterindustrial.com.mx/walor-mex-apuesta-por-la-industria-4-0/), [Mexico Industry](https://mexicoindustry.com/noticia/monitor-app-expandira-su-presencia-a-nivel-global-con-reciente-financiacion), [Software Advice](https://www.softwareadvice.com.au/software/360063/monitorapp) |
| **JoonX** (CDMX) | Perfil delgado: IoT, software y minería de datos para producción, mantenimiento y trazabilidad | **No encontrado**; producto de OEE específico, no confirmado | [Village](https://village.ai/company/joonx) |
| **BeOEE** | MES y OEE «para PyME sin inversión inicial», planes por número de máquinas y usuarios según su página; **país de origen no confirmado** | **No encontrado** | [BeOEE](https://beoee.com/), [GoodFirms](https://www.goodfirms.co/software/beoee) |
| **Smart Andon** (smartandon.mx) | Sistema de OEE en tiempo real integrable con MES/ERP; origen no confirmado | **No encontrado** | [Smart Andon](http://smartandon.mx/sistemas-oee.html) |
| Andon Store / XL Lean Tools | Tableros andon y OEE de catálogo; teléfono de Monterrey | **No encontrado** | [Jimdo](https://andon1.jimdofree.com/) |
| Pulsar Srl (Italia) | **No es la misma empresa** que Pulsar de Monterrey (software de OEE para líneas de papel tisú sobre Rockwell) | — | [Rockwell](https://rockwellautomation.com/en-nz/company/news/magazines/pulsar-develops-oee-measurement-solution-to-help-users.html) |

### 3.2 Regionales y globales con precio de referencia

| Producto | Precio | Fuente | Marca |
|---|---|---|---|
| **Evocon** (licencia sin hardware) | Capterra y G2: €159 / €209 / €269 por máquina y mes (Basic / Professional / Enterprise). Página antigua de Evocon: US$189 / 249 / 319. Fabrico estima US$99-149. **El estudio previo usó los US$189-319; hoy conviene citar el rango €159-269** | [Capterra](https://www.capterra.com/p/187341/Evocon/pricing/), [Evocon (antigua)](https://evocon.com/pricing-old/), [Fabrico](https://www.fabrico.io/blog/oee-software-pricing-guide-2026/) | [V-prov], precios contradictorios |
| Evocon, qué excluye | Dispositivo IIoT, sensores, cables, pantallas, envío, integraciones, visitas, desarrollo a medida | [Evocon KB](https://evocon.com/kb/evocons-oee-software-price-what-to-know/) | [V] |
| **Tractian** | Desde ~US$35 por sensor instalado al mes (agregador); sin precio oficial en México | [ZoftwareHub](https://zoftwarehub.com/products/tractian/pricing), [Capterra](https://www.capterra.com/p/230505/Tractian/pricing) | [V-prov] |
| Rango de mercado OEE (proveedor TeepTrak, competidor) | €30-150 por máquina y mes + €200-2,000 de hardware por máquina | [TeepTrak](https://teeptrak.com/es/precio-software-oee/) | [V-prov] |
| MachineMetrics (nivel medio) | US$200-450 por máquina y mes; implementación el primer año US$10,000-30,000 | [Fabrico](https://www.fabrico.io/blog/oee-software-pricing-guide-2026/) | [V-prov] |

**Lectura.** Con un OEE de €30-150 al mes por máquina más hardware, el costo a 3 años de una máquina es de ~€1,300-7,400 (€30×36 + €200 hasta €150×36 + €2,000) **[C]**. El pago único de MXN 5,000-7,000 (US$280-390) queda por debajo incluso del extremo bajo, **pero AP vende menos función** (sin nube, sin analítica avanzada, sin soporte instalado); la comparación de precio sola no basta **[H]**.

---

## 4. Alternativas de bajo costo que ya usa un taller y por qué fallan

Lo que sigue es, en su mayor parte, **hipótesis a validar en entrevista**: la evidencia pública de «por qué fallan» es de foros y blogs, no de estudios.

| Alternativa | Precio ancla | Por qué se queda corta **[H]** salvo nota | Fuente |
|---|---|---|---|
| **Contador digital de panel** (Autonics CT6, Omron H7CX) | CT6S-2P2: US$183 en una tabla de distribuidor; CT6S-2P4: €148.59; CT6S-1P2: US$140. Entrada NPN/PNP, 10 kHz. **Precio en pesos: no encontrado** | Cuenta, pero no sabe si la máquina estaba produciendo, parada o en cambio de molde; no hay causa de paro ni hora; el operador anota a mano | [TME México](https://www.tme.com/mx/en/details/ct6s-2p2/impulse-counters/autonics/), [Novapart](https://novapart.co/products/CT6S-2P4/counter-timer-prog-6-digit-100-240vac) |
| **Relé programable** (LOGO!, Zelio, CLIC02) | Ver estudio previo §5.1 | Sin tablero, sin registro histórico y sin enlace a otras máquinas; requiere a alguien que lo programe | Estudio previo |
| **PLC chino** (Delta DVP, Fatek, Xinje, Inovance) | DVP-SS de 24 V a US$50 por 5+ piezas en un listado sin verificar; existencia de lead time de 42 semanas en un DVP-S «no almacenado» en Mouser. **Distribuidor y precio en MXN: no encontrado** | Barato pero depende de la persona que lo programó; sin aplicación de OEE; soporte y software de programación variables | [Global Sources](https://www.globalsources.com/product/electronic-control-modules_1206434277f.htm), [Mouser](https://www.mouser.hk/en/c/industrial-automation/controllers/programmable-logic-controllers-plcs/?pg=41) |
| **Tablero casero con ESP32** | Placas de US$55-88 (estudio previo §5.1) | Foros: la conmutación de relés con carga inductiva genera EMI que puede colgar el ESP32; es frecuente atribuir los reinicios a la fuente; quien lo usa en fábrica cita aislamiento galvánico y filtrado de alimentación como la diferencia; ningún sello industrial | [esp32.com](https://esp32.com/viewtopic.php?p=36443), [esp32.com](https://esp32.com/viewtopic.php?p=13313) **[V-prov, foro]** |
| **Tablero andon de catálogo / torre de luz sola** | Torretas LED de 12-30 V CC IP65 existen (Sesa); **precio en MXN: no encontrado** | Avisa pero no mide ni acumula; nadie sabe cuántos minutos se perdieron | [Sesa](https://www.sesa-systems.com/en-eu/collections/andon-en.oembed), [Cosmos](https://www.cosmos.com.mx/producto/torretas-de-luz-ljtw/) |
| **Papel, pizarrón, hoja de cálculo** | Costo directo ~0 | El operador registra lo que recuerda; los microparos casi no se registran (ver §7) | [Reliable](https://reliamag.com/?p=266375) |

**Dato útil sobre el producto casero:** el DIY existe y es barato, pero casi todos los fallos citados son de alimentación, ruido y falta de aislamiento. Eso es justo lo que AP puede demostrar con ensayos reales (EMC, aislamiento) antes de vender; hoy no hay mediciones **[M: ninguna]**.

---

## 5. TI y ciberseguridad al conectar un equipo nuevo en una planta automotriz

**Lo que no encontré:** el procedimiento de homologación de dispositivos de TI/OT de una armadora o de un Tier 1 concreto, ni una encuesta mexicana sobre segmentación TI/OT.

### 5.1 Marcos y datos de contexto

| Tema | Qué dice | Fuente | Marca |
|---|---|---|---|
| IEC 62443, roles | Tres roles: dueño del activo, proveedor de servicios de integración y **proveedor de producto** (el rol de AP); las partes 4-x apuntan al proveedor | [Control Engineering](https://www.controleng.com/structure-of-iec-62443), [ISAGCA](https://gca.isa.org/hubfs/21-29%20-%20ISAGCA/ISAGCA-IACS%20Roles%20and%20Responsibilities.pdf) | [V] |
| Niveles | SL 1 = protección contra violación casual o accidental; el nivel objetivo se fija por zona, no para toda la planta | [Presencis](https://presencis.com/regulations/iec-62443/article-1-3-security-levels/) | [V-prov] |
| Zonas y conductos | Zona = activos con la misma necesidad de seguridad; conducto = enlace controlado entre zonas; cruce planta-empresa por una DMZ (nivel 3.5 de Purdue) | [Trout](https://www.trout.software/solutions/ot-network-security), [IMD](https://industrialmonitordirect.com/blogs/knowledgebase/otit-network-segmentation-in-industrial-plants-purdue) | [V-prov] |
| Inventario de activos | PLC, RTU, sensores inteligentes y dispositivos de campo deben entrar al inventario cuando llegan; reglas de firewall sin dueño documentado se marcan como brecha | [Manifestly](https://app.manifest.ly/public/checklists/32c95d6885b8186d7e41992c7dae0afc?modal=true) | [V-prov] |
| TISAX / VDA ISA 6.0 | Vigente desde el 1-abr-2024; mejora el enfoque en TI y OT. Hay plantas mexicanas con etiqueta TISAX (por ejemplo Puebla y Edomex) | [DNV](https://www.dnv.us/news/2023/bag_2023q4_tisax_vda_update/), [Kirchhoff](https://kirchhoff-automotive.com/wp-content/uploads/2025/07/Tisax_Puebla-.pdf), [Kiekert](https://www.kiekert.com/wp-content/uploads/2026/06/kiekert-tisax-assessment-kmx-en.pdf) | [V] |
| TISAX y OT | Las constancias muestran alcance, **no** controles de dispositivos de piso; requisitos de OEM no alemanes: **no encontrado** | [KPMG México](https://kpmg.com/mx/es/home/servicios/asesoria/administracion-de-riesgos/gestion-de-riesgo-tecnologico/cumplimiento-regulatorio-de-ti/trusted-information-security-assessment-exchange.html) | [V] |
| Wi-Fi industrial | Para WLAN de planta, EAP-TLS con servidor RADIUS en el nivel 3; los dispositivos simples que no soportan 802.1X suelen pasar por «MAC authentication bypass» (descripción de un proveedor) | [Control Engineering](https://www.controleng.com/securing-industrial-wireless-networks/), [IronWiFi](https://www.ironwifi.com/manufacturing) | [V-prov] |
| Aislamiento de IoT | VLAN dedicada para dispositivos IoT, separada de la corporativa | [Purple](https://www.purple.ai/hi-IN/guides/iot-device-segmentation-wifi) | [V-prov] |
| Incidentes | 47 % de los encuestados en Latinoamérica tuvo al menos una brecha en OT el año pasado (Fortinet, regional); la manufactura es el principal blanco del cibercrimen en México con ~30 % de los ataques (Kaspersky vía Mexico Business News); los ataques a manufactura subieron de 937 (2024) a 1,466 (2025) | [Automate](https://www.automate.org/robotics/industry-insights/ciberseguridad-industrial-como-proteger-una-planta), [The Logistics World](https://thelogisticsworld.com/manufactura/ciberseguridad-industrial-el-nuevo-frente-de-riesgo-para-manufactura-y-logistica/), [Rockwell](https://www.rockwellautomation.com/es-ar/company/news/blogs/ot-cyber-trends-2026.html) | [V-prov], regionales o globales |

### 5.2 En términos prácticos: qué va a preguntar TI **[CG/H]**

Esto no es un reglamento; es la lista que conviene tener resuelta antes de tocar la red de una planta, armada con los marcos de arriba:

1. **¿Alguna conexión a la red de planta?** Respuesta objetivo del piloto: **no**. El AP Monitor se queda en modo aislado, con su propio punto de acceso o una pantalla local y exportación CSV por USB o descarga manual. Es lo más fácil de aprobar.
2. **Si hay red, ¿cable o Wi-Fi?** Muchas plantas tienen política de no admitir Wi-Fi no gestionado en el piso **[H]**. El hardware actual (Wi-Fi y RS-485) no tiene Ethernet. Un gateway por cable es la alternativa y ya está en la hoja de ruta.
3. **Identidad del equipo:** MAC registrada, IP fija, nombre, dueño, VLAN de destino.
4. **Servicios abiertos:** lista de puertos y protocolos; sin telnet ni servicios sin autenticación; sin salida a internet (sin nube).
5. **Credenciales:** única por equipo, sin contraseña por defecto (ya en el estudio previo §7.6).
6. **Actualización de firmware:** cómo, quién, con qué firma; sin OTA automática en producción.
7. **Si se usa Wi-Fi empresarial:** si el ESP32 soporta WPA2/WPA3-Enterprise con certificados (EAP-TLS) **[CG, verificar en la documentación del fabricante del chip]**, que se pueda presentar a TI; si no, PSK en VLAN aislada.
8. **Documento de una página («ficha de TI»):** flujos de datos, puertos, qué escribe y qué no escribe en la máquina (**no escribe en la máquina**), versión de firmware, contacto del responsable.

**Qué se afirma y qué no.** AP no tiene certificación IEC 62443. El estudio previo ya fija un SL1-SL2 como meta de diseño; aquí solo se agrega que el cliente (dueño del activo) evaluará el dispositivo en su propio análisis de zonas y conductos y que **la primera barrera comercial puede ser TI y no el precio** **[H]**.

---

## 6. Apoyos y financiamiento para digitalización de pymes

**Resultado central: no encontré un programa público vigente que pague o subsidie específicamente equipo de OEE o andon.** Lo aplicable está en la tabla.

| Programa | Qué ofrece | Estado y límites | Fuente |
|---|---|---|---|
| **Plan México, decreto fiscal (DOF 21-ene-2025)** | Deducción inmediata de bienes nuevos de activo fijo adquiridos del 22-ene-2025 al 30-sep-2030, para empresas de cualquier tamaño | Porcentajes entre 35 % y 91 % según el activo y la actividad (41-91 % en 2025-2026; 35-89 % en 2027-2030, según un análisis); hay que mantener el bien en uso 2 años y obtener **constancia de un Comité de Evaluación**; **no encontré si un equipo de monitoreo calificaría ni su porcentaje** | [IDC Online](https://idconline.mx/fiscal-contable/2025/03/21/deduccion-inmediata-y-capacitacion-reglas-del-plan-mexico), [EY](https://www.ey.com/content/dam/ey-unified-site/ey-com/es-mx/technical/tax/documents/ey-tax-flash-incentivos-fiscales-plan-mexico.pdf), [PwC](https://www.pwc.com/mx/es/impuestos/archivo/novedades-fiscales/2025/202501-decreto-del-plan-mexico.pdf) |
| Polos de Desarrollo Económico para el Bienestar (DOF 22-may-2025) | Estímulos para empresas dentro de los polos (por ejemplo Celaya, Gto.; Juárez, Chih.) | Aplica por polo asignado; monto total citado de MXN 30 mil millones (verificar en DOF) | [Proyectos México](https://www.proyectosmexico.gob.mx/proyecto_inversion/polos-de-desarrollo-economico-para-el-bienestar/), [El Contribuyente](https://www.elcontribuyente.mx/2025/05/presenta-gobierno-estimulos-fiscales-para-polos-de-bienestar/) |
| **Nafin** | MX$120 mil M para mipymes en 2026 y convenio con Caintra para proveedores (estudio previo); crédito de hasta MXN 500 mil para microempresas formales con 12+ meses (capital de trabajo, gracia de hasta 6 meses) | Historia: los créditos de Nafin con Cofipyme financian activo fijo o capital humano, y el software queda fuera de los programas típicos (nota sin fecha, ~2021-2022) | [Expansión](https://expansion.mx/finanzas-personales/2026/09/14/3-bancos-tramitar-creditos-hasta-500-000-pesos-para-pymes), [DPL News](https://dplnews.com/?p=101157) |
| Nafin con estados (ejemplo) | Hidalgo 2026-2027: bolsa de MXN 700 M+, créditos hasta MXN 5 M, tasa fija máxima 14.75 %, hasta 60 meses | **Solo Hidalgo**; sirve como ancla de tasas, no como programa de AP | [La Razón](https://www.razon.com.mx/estados/2026/07/14/hidalgo-impulsa-mipymes-creditos-nafin-crecen-10-veces-y-crean-empleos/) |
| **Nafin–Bancomext, cadena automotriz** | Ficha de 2023: hasta MXN 30 M, hasta 3 años capital de trabajo o 15 años activo fijo, proveedores Tier I a III | Ficha del sector eléctrico-electrónico; **vigencia no confirmada** | [AMF](https://amf.org.mx/wp-content/uploads/2023/04/1.%20Carga/Dia%201/1500%20-%201545%20Herramientas%20financieras%20NAFIN-BANCOMEXT/NAFIN-BMXT%202023%20.pdf) |
| **Bancomext** | MXN 190 mil M en créditos nuevos en 2026; productos: PYMEX, arrendamiento financiero y puro, proveedores maquila | Sin condiciones vigentes encontradas para automatización; el arrendamiento es la vía más cercana a equipo | [Expansión](https://expansion.mx/economia/2026/02/02/bancomext-preve-colocar-190-000-mdp-en-nuevos-creditos-en-2026) |
| **IFC / INA / Sec. de Economía** | Nueva fase (ago-2025) del Programa de Desarrollo de Proveedores: capacitación, mentoría y acceso a financiamiento de Nafin y Bancomext para pymes automotrices | Detalle de fases y plazos: verificar con INA | [IFC](https://www.ifc.org/es/pressroom/2025/ifc-ina-y-la-secretar-a-de-econom-a-anuncian-nueva-fase-del-programa-de-desarrollo) |
| **SE, «PyMEs Digitales» / MiPyMEX** | Autodiagnóstico, catálogo de soluciones, financiamiento con bancos y fintechs (fuente de 2024) | Estado en 2026 no confirmado; no se encontraron reglas de operación | [Cluster Industrial](https://clusterindustrial.com.mx/secretaria-de-economia-y-microsoft-mexico-impulsaran-desarrollo-de-mipymes/) |
| Clústeres: CLAUT (Nuevo León) | Evento Proveedor Automotriz, 27-28 may-2026, Cintermex, ~70 compradoras; su director liga productividad con automatización y digitalización | Vinculación comercial, **no** subsidio | [Mexico Industry](https://mexicoindustry.com/noticia/tmec-podria-detonar-nueva-ola-de-inversiones-automotrices-en-nuevo-leon) |
| Guanajuato, «Conexión Industrial» | 10 reuniones de negocio en 2026: 447 proveedores, 16 compradoras, ventas estimadas > MXN 264 M | Vinculación, no subsidio | [Cluster Industrial](https://clusterindustrial.com.mx/conexion-industrial-impulsa-mas-de-264-mdp-en-ventas-y-fortalece-la-proveeduria-en-guanajuato/) |
| Querétaro | Acuerdo de AMSDE con Microsoft para asesoría gratuita en políticas de uso de tecnología (2023) | Asesoría, no financiamiento | [Mexico Industry](https://mexicoindustry.com/noticia/microsoft-y-amsde-impulsan-digitalizacion-de-pymes) |
| Coahuila (Sedesu) | **No encontrado** | — | — |
| «Crece tu Pyme con Pagos Digitales» (SE) | Terminales de pago | **No aplica** a este caso | [DPL News](https://dplnews.com/?p=299351) |

**Implicaciones [H]:**

- **Pago único contra suscripción.** Un equipo pagado una vez puede entrar como activo fijo, mientras que una suscripción de OEE es gasto. Por eso la deducción inmediata y el crédito de activo fijo favorecen el modelo de AP. Hay que confirmar con un contador si un equipo de monitoreo califica y con qué porcentaje.
- Los apoyos financian montos grandes; con tickets de MXN 5,000-7,000 por máquina el financiamiento importa poco. Lo que sí importa es que **el comprador pueda aprobar el gasto sin concurso**. Preguntar el tope de compra directa de cada cliente.
- Los clústeres sirven como puerta para entrevistas y para presentar el piloto.

---

## 7. Valor económico de un punto de OEE y de un microparo

### 7.1 Punto de partida con fuente

| Método | Resultado de ejemplo | Fuente | Marca |
|---|---|---|---|
| Línea: horas planificadas × unidades por hora demostradas × margen de contribución por unidad × 1 % | ~€41,500 por punto y año (llenadora de detergente); ~€20,700 (línea de papel tisú) | [Fabrico](https://www.fabrico.io/blog/value-of-one-oee-point-methodology/) | [V-prov] |
| Por utilidad: utilidad en juego entre OEE actual y 100 %, dividida por los puntos | ~€43,750 por punto (OEE 64 %, precio €0.75, costo variable €0.50, costo fijo €2 M) | [Evocon](https://evocon.com/articles/oee-as-a-financial-kpi-and-its-use-in-product-costing/) | [V-prov] |
| Escalar la producción | De 70 % a 75 %: ~US$210,000 de utilidad, ~US$42,000 por punto | [Zapium](https://www.zapium.com/blog/oee-cost-savings-and-roi-in-maintenance/) | [V-prov] |

Cautelas de Fabrico: usar horas planificadas (no 8,760), velocidad demostrada (no de placa) y recordar que **si la demanda es el límite, la capacidad recuperada es costo evitado (horas extra, inversión diferida), no venta nueva**. Los primeros puntos suelen ser más baratos que los últimos.

Los tres ejemplos son de líneas con márgenes europeos o estadounidenses; sirven de orden de magnitud, no de dato mexicano.

### 7.2 Modelo propio para una línea típica de Tier 2 (supuestos explícitos)

Supuestos **[H]**, todos por validar en entrevista:

| Supuesto | Valor | Notas |
|---|---|---|
| Horas planificadas por año | 4,000 h | 16 h/día (2 turnos) × 250 días |
| Velocidad ideal | 100, 300 o 600 piezas/h | Rango para estampado o inyección de pieza chica |
| Margen de contribución por pieza | MXN 2, 4 u 8 | Precio menos costo variable; **no encontrado** dato público |
| Demanda | No limitada | Si está limitada, el valor es costo evitado |
| Tipo de cambio | 18 MXN/USD | Referencia del estudio previo |

**Fórmula [C]:** valor de 1 punto = 4,000 h × 1 % × velocidad × margen = 40 × velocidad × margen.

| Velocidad (pzas/h) \ Margen (MXN/pza) | 2 | 4 | 8 |
|---|---|---|---|
| 100 | 8,000 | 16,000 | 32,000 |
| 300 | 24,000 | **48,000** | 96,000 |
| 600 | 48,000 | 96,000 | 192,000 |

(MXN por punto de OEE y año. El caso central es 300 pzas/h y MXN 4: MXN 48,000, equivalente a US$2,667.)

**Valor de la hora perdida por costo evitado [H]:** si en lugar de venta nueva se evita tiempo extra, 1 punto = 40 h. A MXN 600 por hora-máquina de costo variable (supuesto) son MXN 24,000 por punto y año **[C]**. El cálculo de salario por hora no pudo cerrarse: solo encontré 6.37 USD/hora en manufactura en 2025 ([UNAM, con datos de EMIM y BLS](https://pued.unam.mx/export/sites/default/archivos/SUCS/2026/SAET130526.pdf)) **[V-prov]**, sin cuotas ni prestaciones.

### 7.3 Microparos

| Dato | Valor | Fuente | Marca |
|---|---|---|---|
| Umbral de microparo | Menos de 2, 5 o 10 min según la fuente; AP debe fijarlo configurable | [Fabrico](https://www.fabrico.io/blog/micro-stops/), [Oxmaint](https://oxmaint.com/industries/fmcg/minor-stoppages-hidden-oee-killer-fmcg-packaging) | [V-prov] |
| Pérdida por velocidad (que incluye microparos) | 9-15 % del OEE según una síntesis de Evocon que no pude abrir | [Fabrico](https://www.fabrico.io/blog/micro-stops/) | [V-prov], sin verificar |
| Subregistro | Un caso revisado por pares: 319.4 h anuales de paros menores estimadas contra 106.2 h registradas en la categoría de pérdidas | [Reliable](https://reliamag.com/?p=266375) | [V] (un caso) |
| Cuántos microparos hay por turno en México | **No encontrado** | — | — |

**Ejemplo [C] con supuestos [H]:** 30 microparos por turno de 40 s = 20 min por turno. Con 500 turnos al año son 10,000 min = 167 h, o **4.2 puntos de OEE** sobre 4,000 h. En el caso central (MXN 48,000 por punto) son ~MXN 200,000 al año por máquina; en el caso bajo (8,000 por punto), ~MXN 33,000.

**Comparación con el precio objetivo [C]:** a MXN 5,000-7,000 por máquina, un solo punto recuperado en el caso central paga el equipo en ~1.3-1.8 meses (7,000 / 48,000 × 12 = 1.75). **Eso supone que el equipo mide y que el cliente actúa sobre lo medido**: medir no recupera nada por sí solo. La captura real es la variable que más falta saber.

### 7.4 Costos de paro: por qué las cifras grandes no sirven para este cliente

- Siemens: hora de paro de **US$2.3 M** en una planta automotriz grande ([Siemens TCOD 2024](https://assets.new.siemens.com/siemens/assets/api/uuid:1b43afb5-2d07-47f7-9eb7-893fe7d0bc59/TCOD-2024_original.pdf)) **[V]**, de 181 entrevistas a empresas grandes. No aplica a un Tier 2 de 5-20 máquinas.
- TeepTrak: US$900-2,100 por minuto en un Tier 1 de EE. UU. «según estimaciones típicas de la industria», sin fuente ([TeepTrak](https://teeptrak.com/en/automotive-manufacturing-downtime/)) **[V-prov, no usar]**.
- Un taller Tier 2 sufre sobre todo por **penalizaciones y paro de la línea del cliente** si no entrega a tiempo, no por el costo directo de su propia máquina. **No encontré cifras de penalizaciones** en México **[H]**.

### 7.5 Referencia de OEE típico

OEE medio de ~60 % y de clase mundial 85 % en manufactura discreta ([TeepTrak](https://teeptrak.com/en/world-class-oee-benchmark/), [Fabrico](https://www.fabrico.io/blog/oee-benchmark/)) **[V-prov]**; blogs de proveedores de OEE, sin estudio independiente. **OEE típico de plantas mexicanas: no encontrado.** La mejor medida será la línea base del propio piloto.

---

## 8. Perfil de cliente ideal para el piloto (3 perfiles)

| # | Perfil | Por qué | Condición de entrada | Cómo se mide el éxito |
|---|---|---|---|---|
| **A** | **Taller Tier 2 de estampado, inyección o maquinado en el Bajío** (Guanajuato o Querétaro), 30-150 personas, 5-20 máquinas con torre de luz, proveedor de un Tier 1 | Sin MES, mide a mano; el dueño o gerente decide y compra sin concurso; los clústeres ofrecen puerta de entrada; coincide con el hueco de precio | Dispuesto a dejar el equipo sin red; permite fotografiar sensores y torres; una máquina con paros frecuentes | Línea base de OEE y microparos en 4 semanas, contra registro manual; cuántos minutos por turno aparecen que nadie anotaba |
| **B** | **Integrador o constructor de máquinas chico** (5-50 personas) en Querétaro, Monterrey o Saltillo, que arma tableros de conteo a medida | Es canal: instala en varios clientes y define la especificación; trae acceso a PLC y sensores | Instala 2-3 equipos en clientes propios y comparte tiempos de instalación y problemas | Horas de instalación por máquina; si repetiría; qué margen espera |
| **C** | **Planta con ingeniería de mantenimiento y política de TI definida** (Tier 1 o Tier 2 grande), una línea piloto | Es la prueba de aprobación de TI y de la ficha de ciberseguridad; sin ella, la ruta al canal automotriz queda sin evidencia | Aprobación de TI para un equipo aislado y fuera de la línea de seguridad; sponsor de mantenimiento | Tiempo y requisitos de aprobación; qué documentos pidió TI |

**Descalificadores comunes [H]:** máquinas sin señal de torre accesible; cliente que exige marca aprobada o certificado desde el día uno; cliente que solo acepta nube; sin quien instale con seguridad eléctrica; cualquier uso que roce una función de seguridad (se rechaza).

---

## 9. Diez preguntas adicionales para entrevistas

1. ¿Qué sensores usan sus máquinas: PNP, NPN o contacto seco? ¿Puede mostrarme la etiqueta de uno y la regleta de la torre? (§1.2)
2. En la torre de luz de esta máquina, ¿el cable de cada color queda en +24 V o en 0 V cuando está apagado? ¿Alguien lo ha medido?
3. ¿Quién decide y aprueba la compra de un equipo de MXN 5,000-7,000 por máquina, y hasta qué monto compra sin cotizaciones comparadas?
4. ¿Cuántos minutos por turno cree que se pierden hoy en paros de menos de 5 minutos? ¿Cómo lo sabe y quién lo anota?
5. Si el equipo le muestra que pierde 2 horas por turno, ¿qué haría distinto el lunes y quién lo haría? (captura real, §7.3)
6. ¿Su cliente (Tier 1 o armadora) le exige algún indicador (OEE, PPM, trazabilidad) en un formato específico?
7. ¿Qué tendría que firmar TI o quien administre la red para instalar un dispositivo aislado? ¿Admiten Wi-Fi en el piso, o solo cable? (§5.2)
8. ¿Qué haría hoy si quisiera contar piezas sin comprar nada nuevo? ¿Probó un contador, un relé programable o un ESP32? ¿Qué falló? (§4)
9. ¿Prefiere pagar una sola vez o por mes? ¿Cómo lo registra su contador: activo fijo o gasto? ¿Ha usado la deducción inmediata del Plan México? (§6)
10. ¿Quién instalaría el equipo (su mantenimiento, un integrador, nosotros) y cuánto tiempo de máquina parada tolera para hacerlo?

---

## 10. Qué evidencia haría cambiar el rumbo

| Evidencia | Umbral sugerido **[H]** | Efecto |
|---|---|---|
| Fotos y mediciones de máquinas reales muestran que muchas señales de torre o sensores son tipo sumidero (NPN) o no accesibles | Más de 1 de cada 3 de las primeras 15 máquinas | **Adelantar la entrada bidireccional** a antes del piloto, o usar contacto seco con un relé adaptador; revisar el precio |
| TI de 2 o más plantas objetivo prohíbe cualquier dispositivo nuevo sin certificación o sin Ethernet | 2 de 3 plantas consultadas | Pasar al perfil A y B (talleres sin TI fuerte), o priorizar Ethernet y el gateway antes que más funciones |
| El cliente no puede ni quiere actuar sobre los datos (captura cercana a cero) | Ninguno de 5 pilotos cambia una decisión en 4 semanas | Revisar el valor de la propuesta: pasar de «medir» a «avisar y escalar» (andon) |
| Un competidor local (Pulsar, Monitor App) publica precio o plan de entrada por debajo de MXN 1,000 por máquina al mes sin hardware | Precio publicado | Dejar de competir en el costo de 3 años; competir en pago único y modo sin nube, o replantear |
| Los clientes aceptan pagar menos de lo que cuesta fabricar (precio ≥ 3 × costo directo no se cumple, según `ANALISIS_ECOSISTEMA.md` §6) | Costo real de la cotización | Subir precio o recortar funciones; si no cuadra, detener |
| Los integradores no ven margen y no lo venden | 3 de 3 entrevistados | Reemplazar el canal por venta directa y Mercado Libre; reducir el peso de la ruta del integrador |
| Un cliente o proveedor de relevancia exige certificaciones (NOM, UL, CE) antes de cualquier piloto | Mayoría de las visitas | Adelantar certificación o detener ventas; mantener solo prototipos de laboratorio |
| El apoyo público realmente aplicable aparece (convocatoria que cubra equipo de monitoreo) | Convocatoria vigente | Vender con subsidio; ajustar el calendario al ciclo de la convocatoria |
| Las mediciones de EMC o de relés de la primera tanda fallan | Cualquier falla de aislamiento o reinicios repetidos | Es el mismo problema que mata al ESP32 casero (§4): rediseñar antes de visitar plantas |

---

## Hallazgos (por relevancia para la decisión)

1. **Riesgo de entrada NPN/PNP sin dato público:** hay que medirlo en campo (§1.2).
2. **Competencia local sin precios publicados:** Pulsar, Monitor App y JoonX venden por cotización; la referencia pública de precio sigue siendo Evocon (hoy €159-269 por mes) y Tractian (~US$35 por sensor al mes, agregador).
3. **No hay subsidio específico para equipo de OEE:** lo aplicable es la deducción inmediata (con constancia del comité) y crédito de activo fijo (§6).
4. **TI/OT puede ser un freno antes que el precio:** la ruta más limpia es modo aislado y ficha de una página (§5).
5. **Valor de un punto de OEE:** MXN 16,000-96,000 por máquina y año en el rango del modelo, con el supuesto central de MXN 48,000; depende de que el cliente recupere capacidad y la venda (§7).

## Qué falta saber

- Estadística de PNP y NPN por región y por tipo de máquina; el manual oficial de Omron (CP1E/CP1L) y de LOGO!.
- Cuántos OEM mexicanos hay, cómo compran, y edad del parque de inyectoras y prensas.
- Precios en MXN de Pulsar, Monitor App, JoonX, BeOEE, Smart Andon; precio en pesos de contadores, PLC chinos y torretas.
- Procedimiento real de homologación de TI en las armadoras y Tier 1 (Nissan, GM, Stellantis, VW, Toyota, Honda, etc.).
- Si un equipo de monitoreo califica para la deducción inmediata y con qué porcentaje.
- Margen por pieza, microparos por turno y penalizaciones en un Tier 2 típico.
- Todo lo de integradores en CDMX y Guadalajara.
- Las páginas completas de las fuentes: abrir cada enlace antes de citar.

## Siguiente paso recomendado

1. Entrevistar a 5 talleres del Bajío (perfil A) y 2 integradores (perfil B) con las preguntas de §9; llevar fotos de sensores y torres como primer entregable.
2. Pedir cotización de lista a Pulsar y Monitor App como cliente anónimo de pyme, para tener precio real.
3. Con un contador, resolver el tratamiento fiscal de un equipo de monitoreo bajo el decreto del Plan México.
4. Preparar la ficha de TI de una página (§5.2) con el estado real de cada punto.
5. Pasar el asunto de la entrada bidireccional a `ap-hardware` y `ap-producto` como decisión, sin tocar archivos de otras áreas.

## Fuentes

Todas están enlazadas en el texto. Consulta del 14-oct-2026 por extracto de búsqueda (WebFetch no disponible en esta sesión). Las páginas de proveedores, agregadores (Capterra, ZoftwareHub, Software Advice), blogs y foros se usaron solo como señal y están marcadas [V-prov].
