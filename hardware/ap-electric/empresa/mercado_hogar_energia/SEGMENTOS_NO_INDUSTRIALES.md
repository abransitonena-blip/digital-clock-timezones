# Segmentos no industriales en México: dónde podría entrar una placa de relés, entradas y Modbus con aplicación local

> **Estado: estudio de escritorio, fecha de consulta 14-oct-2026.** Agente `ap-mercado-hogar-energia`. Complementa `ESTUDIO_MERCADO_INDUSTRIAL.md` y `ANALISIS_ECOSISTEMA.md` (no repite el mercado industrial, los PLC ni los precios ancla de micro-PLC).
> Nada de AP Electric está fabricado, medido ni certificado. Esto **no** es una decisión de producto ni asesoría legal: las secciones de normas son listas para consultar a un organismo acreditado (NYCE, ANCE u otro) o a un abogado.
>
> **Marcas:** `[V]` dato con fuente enlazada y fecha de consulta · `[CG]` conocimiento general sin verificar · `[H]` hipótesis de AP por validar · `[R]` dato del repositorio. «No encontrado» = se buscó y no hay dato público utilizable.
>
> **Limitación del método (importante):** en esta sesión `WebFetch` y `curl` fallaron (DNS/proxy 403), así que **no pude abrir ninguna página completa**. Todas las cifras salen de los resúmenes que devolvió `WebSearch` sobre las URL citadas, y no las contrasté contra el documento original. Por eso casi todo dato con cifra queda `[V]` solo en sentido débil («lo dice el resultado de búsqueda sobre esa URL»); antes de citarlo hacia fuera hay que abrir la fuente. Donde las fuentes se contradicen lo digo.
>
> **Moneda e impuestos:** salvo indicación, MXN. Los precios de tiendas mexicanas son de publicaciones de minoristas y normalmente incluyen IVA (16 %) [CG]; los precios en EUR/USD/GBP son de tiendas extranjeras. Cada precio indica lo que la fuente dice.

## 0. Marco de AP que condiciona todo (del repositorio)

- **Producto candidato único:** AP Monitor 24 = 7R Tour 24DC rev B + firmware PackML/OEE + consola, alimentado a 24 V CC desde una fuente certificada de terceros. Nada de red de 127/220 V en la placa [R, `CONTEXTO_COMPARTIDO.md` reglas 2 y 6].
- **SKU CA y AP Home están en pausa** hasta tener pruebas de seguridad eléctrica con un organismo acreditado [R].
- **Ningún producto de AP es función de seguridad** [R, regla 5].
- Por eso la pregunta clave de cada segmento es: **¿AP puede vender solo la parte de 24 V (lógica, entradas, relés de baja tensión, Modbus) y dejar la potencia de red a un tercero ya certificado (medidor, contactor, fuente, inversor)?** Si sí, el segmento puede empezar sin certificar red; si el valor exige que la placa conmute 127/220 V directamente, no.

### Cuatro reglas de lectura regulatoria (aplican a todos los segmentos) 
1. **NOM-001-SCFI-2018** (aparatos electrónicos): vigente; cubre equipos alimentados de red pública hasta 277 V CA monofásico a 60 Hz y/o trifásicos hasta 480 V CA; en vigor desde 14-may-2020; el primer certificador fue NYCE ([SE, platiica](https://platiica.economia.gob.mx/normalizacion/nom-001-scfi-2018/); [Eleos](https://eleoscompliance.com/en/article/mexico-an-overview-of-nom001scfi2018); consulta 14-oct-2026) `[V]`. Una placa alimentada solo con una fuente externa de 24 V CC no es obviamente «alimentada de red»; **si queda dentro o fuera del alcance lo debe decidir un laboratorio** `[H]`. No encontré criterio oficial publicado para este caso.
2. **NOM-003-SCFI-2014** (seguridad de productos eléctricos): una fuente de terceros la cita como aplicable a apagadores y contactos, pero la fuente es un directorio, no el DOF; costos de certificación aparecen en un documento de la SE ([ocpr-2023-004](https://platiica.economia.gob.mx/wp-content/uploads/sites/5/Tarifas/ocpr-2023-004.pdf); [NEMA](https://www.nema.org/docs/default-source/international-activities-document-library/nom-003-scfi-2014-electrical-products-safety-requirements.pdf); consulta 14-oct-2026) `[V débil]`. No hallé fuente que diga cómo clasifican las autoridades un «apagador inteligente».
3. **Radio (WiFi/Bluetooth, 2.4 y 5 GHz):** NOM-208-SCFI-2016 / disposición IFT-008-2015 exigen aprobación del regulador antes de comercializar equipos de corto alcance, según TÜV ([TÜV](https://tuv.com/market-access-services/en/certification-filter/mexico-radio-telecom-approval-(ifetel).html), consulta 14-oct-2026) `[V débil]`. El estudio industrial ya cita IFT-017-2023; **el IFT fue sustituido por otra autoridad en 2025 [CG]: verificar quién homologa hoy**. Un módulo ESP32 con certificado ajeno a México no prueba homologación local (no encontré constancia IFT de módulos ESP32). Solución de bajo riesgo: **Ethernet/RS-485 sin radio** o módulo ya homologado.
4. **NOM-001-SEDE-2018 (instalaciones eléctricas):** aplica a instalaciones, no a productos; el borrador analizado por Ecija dice que alcanza a inmuebles industriales, comerciales y residenciales; el reglamento exige verificación por una UVIE en alta tensión y lugares de concentración pública ([Ecija](https://ecija.com/en/?p=94570); [DOF/SIDOF](https://sidof.segob.gob.mx/notas/docFuente/5504973); consulta 14-oct-2026) `[V débil]`. No encontré el texto vigente y definitivo en la búsqueda. Implica que **quien instala** (electricista o integrador) responde por la instalación; AP vende la caja de 24 V.

---

## 1. Hogar inteligente y apagadores/lámparas

**Tamaño y tendencia.** IMARC: mercado de hogares inteligentes en México ≈ USD 1,8 mil millones en 2025, proyección USD 4,9 mil millones en 2034, TCAC 10,84 % 2026-2034 ([IMARC](https://www.imarcgroup.com/report/es/mexico-smart-homes-market), consulta 14-oct-2026) `[V débil, informe de pago]`. Otra cifra, USD 647 millones en dispositivos, sin año ([Merca2.0](https://www.merca20.com/?p=763218)) y una regional de Latinoamérica de USD 4,43 mil millones ([Informes de Expertos](https://www.informesdeexpertos.com/informes/mercado-latinoamericano-de-casa-inteligente/toc)) **no son comparables**. Adopción: ≈ 74 % tiene al menos un aparato «smart» (YouGov) y 5 de cada 10 hogares algún dispositivo conectado (Ring); lo más usado son voz 42 %, focos 21 %, cámaras 16 %; Matter «no logra la integración fluida» ([Expansión, 24-nov-2025](https://expansion.mx/tecnologia/2025/11/24/promesa-unificar-dispositivos-inteligentes-hogar-se-estanca)) `[V débil]`. Usuarios de Home Assistant en México: no encontrado.

**Dolores concretos.** Apagadores que dependen de nube y app propia; fragmentación de ecosistemas; instalación sin neutro en cajas antiguas `[CG]`. Ninguna fuente de esta sesión mide estos dolores en México: son `[H]`.

**Quién compra y canal.** Consumidor final en marketplace y tiendas departamentales (Walmart, Bodega Aurrerá, Sears), electricistas e instaladores, y proyectos con integrador. Habitissimo muestra solicitudes de presupuesto de domótica con Lutron, Legrand y Wattstopper, y compras de suministro e instalación por separado ([Habitissimo CDMX](https://www.habitissimo.com.mx/presupuesto/instalar-sistemas-domotica/ciudad-de-mexico), consulta 14-oct-2026) `[V débil]`; su tabla (p. ej. $28,000 iluminación, $84,000 accesibilidad y confort, MXN) no aclara año ni IVA: no usar como precio de proyecto.

**Competencia y precios ancla.**

| Producto | Precio | Moneda / IVA | URL |
|---|---|---|---|
| Steren Apagador Wi-Fi Touch sencillo (Bodega Aurrerá) | $389 | MXN, precio de minorista (IVA incluido [CG]) | [Bodega Aurrerá](https://www.bodegaaurrera.com.mx/browse/ferreteria/electricidad/contactos-y-apagadores/265419_265462_265466) |
| Steren SHOME-110 touch doble (700 W) | $369 | MXN | [Sears](https://www.sears.com.mx/producto/332830/apagador-wi-fi-touch-doble-shome-110) |
| Steren SHOME-170 con dimmer | $489 | MXN | [Walmart MX](https://www.walmart.com.mx/ip/Apagador-Wi-Fi-con-dimmer-Steren-SHOME-170/00750625093790) |
| Sonoff MINIR4 | € 13,27 | EUR con impuestos, tienda España | [Sonoff](https://sonoff.tech/es-es/products/sonoff-mini-extreme-wi-fi-smart-switch-minir4) |
| Sonoff (rango de la categoría) | $289 a $317 | MXN, **no es el MINIR4 específico** | [uelectronics](https://uelectronics.com/etiqueta-producto/sonoff/) |
| Shelly 1PM Mini Gen3 / Plus RGBW PM | € 15,25 / € 21,90 | EUR con IVA, tienda España | [PcComponentes](https://www.pccomponentes.com/brands/shelly/reles-wifi) |

Precio MXN de Shelly en México: no encontrado (hay ficha de Shelly Pro 3EM en [Syscom](https://www.syscom.mx/productosinfo/217257) sin precio visible). Syscom compara Sonoff y Shelly: Shelly 1 con relé aislado, Sonoff en línea ([Syscom blog](https://syscom.mx/blog/sonoff-vs-shelly)) `[V débil]`.

**Regulación.** Un apagador conmuta 127 V: NOM-003-SCFI y probablemente NOM-001-SCFI (si es electrónico), más homologación de radio si es inalámbrico. Un sitio de cumplimiento comercial dice que la vigilancia en importación y certificación se ha endurecido en 2026 (fuente comercial, no oficial). No hay camino sin papeles.

**¿AP puede empezar aquí sin certificación de red? NO.** El producto de hogar es por definición un conmutador de 127 V que va en caja de pared; está en pausa por regla [R]. Además el precio ancla (≈ 370-490 MXN) es un orden de magnitud por debajo de lo que costaría una placa de relés industrial. **Única entrada plausible:** pasarela local en 24 V (Modbus/entradas) para instaladores que ya ponen un apagador certificado de otra marca `[H]`.

---

## 2. Edificios y propiedades (condominios, oficinas, hoteles)

**Tamaño y tendencia.**
- Edificios inteligentes: rango de USD 2,7 a 4,8 mil millones en 2025 según el informe y la definición (MarketsandMarkets ≈ USD 4,76 mil millones en 2025, TCAC 14,2 %; Data Bridge USD 2,71 mil millones en 2024) ([MarketsandMarkets](https://www.marketsandmarkets.com/Market-Reports/geography/building-automation-control-systems-market/Mexico); [Data Bridge](https://www.databridgemarketresearch.com/nucleus/mexico-building-automation-system-market); consulta 14-oct-2026) `[V débil, no coinciden]`.
- Hoteles: ≈ 909,719 cuartos y 27,948 hoteles a fin de 2025 (estimación Horwath HTL con datos de SECTUR/Datatur); 58 % de los cuartos en diez estados ([Horwath HTL](https://horwathhtl.com/wp-content/uploads/2026/08/Mexico-Hotel-Industry-Report-2025-English.pdf)) `[V débil]`.
- Condominios: «más de la mitad de la población vive en condominios» sin fuente citada ([Yucatán](https://www.yucatan.com.mx/imagen/2022/09/22/que-es-un-condominio-como-funciona-349044.html)) `[CG]`. Número de condominios y administradoras: **no encontrado**.

**Dolores concretos.** Bombas de agua y cisternas del edificio, alumbrado de áreas comunes con horarios, control de acceso y facturación de consumo. El mercado condominal se digitaliza sobre todo en cobranza y administración (Neivor, material promocional) ([Neivor](https://cdn.uc.assets.prezly.com/1039991c-7ead-4d0c-a4f0-80a57dc58530/-/inline/no/Neivor_Plataformas_Gesti%C3%B3n_Condominios_V1.pdf)). Dolor de energía/agua medido: no encontrado `[H]`.

**Quién compra y canal.** Administradores y comités de condominio (decisión lenta, presupuesto por asamblea) `[CG]`; ingenierías de mantenimiento de hoteles y oficinas; integradores de BMS. Canal: integrador o instalador eléctrico.

**Competencia.** BMS de gran marca (Schneider, Honeywell, Siemens) [CG]; Honeywell ofrece submedición Modbus ([Syscom](https://www.syscom.mx/productosinfo/218420)) `[V débil]`. Precios de BMS/gestión de cuarto de hotel: **no encontrado**.

**Regulación.** NOM-007-ENER-2014 (eficiencia del alumbrado en edificios no residenciales ≥ 3 kW de carga de alumbrado) afecta el diseño, no el producto ([IEA](https://www.iea.org/policies/7830); consulta 14-oct-2026) `[V débil]`. Inmuebles de concentración pública requieren verificación UVIE de la instalación (ver regla 4). Control de acceso o alarmas contra incendio: son otra familia de normas y **AP no debe tocar funciones de seguridad de vida**.

**¿Sin certificación de red? DEPENDE.** Sí para leer medidores Modbus de submedición, cisternas y bombas con contactor de terceros y alarmas por relé de 24 V; no si el valor es conmutar la iluminación o cuartos con la propia placa. Ciclo de venta largo y comprador difuso: apuesta de segundo orden.

---

## 3. Energía (CFE, tarifas, factor de potencia, demanda, solar, inyección cero)

**Tamaño y tendencia.**
- Generación distribuida (GD) solar: 5,164.98 MW en 600,368 solicitudes al cierre de 2025 (CNE, vía pv magazine); total GD < 0,7 MW: 5,189.71 MW, solar > 99,5 % ([pv magazine, 3-jun-2026](https://www.pv-magazine.com/2026/06/03/mexico-supera-en-2025-los-5-gw-solares-en-generacion-distribuida/), consulta 14-oct-2026) `[V débil]`. Desaceleración: 4,444 MW en ene-2025 a 4,751 MW en jul-2025 ([Expansión, 12-dic-2025](https://expansion.mx/empresas/2025/12/12/negocio-de-paneles-solares-se-enfria-desaparicion-cre)). **Nota:** 2025 usa umbral de 0,7 MW; cifras previas usaban 0,5 MW (en 1S-2024: 3,891.22 MW y 460,896 contratos, [Factor Energético](https://factorenergetico.mx/generacion-distribuida-suma-inversiones-de-5200-mdd-y-una-capacidad-instalada-de-3891-mw-al-primer-semestre-de-2024)); no son comparables.
- Marco legal: Ley del Sector Eléctrico (marzo de 2025), Reglamento (3-oct-2025); la CNE publicó acuerdo de permisos de autoconsumo interconectado de 0,7 a 20 MW vigente desde el 4-oct-2025 y disposiciones en dic-2025. El autoconsumo **aislado** no puede interconectarse y debe consumir todo en sitio; el interconectado puede operar **sin vender excedentes** ([Creel](https://www.projectfinance.law/publications/2025/march/se-emiten-nuevas-leyes-para-el-sector-el%C3%A9ctrico-en-m%C3%A9xico/); [Garrigues](https://www.garrigues.com/es_ES/noticia/mexico-publican-nuevas-reglas-generar-electricidad-modalidad-autoconsumo-interconectado.md); consulta 14-oct-2026) `[V débil]`. «Inyección cero» como término regulatorio: **no encontrado**; se entiende como control técnico del inversor.
- Clientes CFE: 49.79 millones a dic-2025 ([CFE vía BMV](https://www.bmv.com.mx/docs-pub/infinan/infinan_1536939_2025-04_1.pdf)) `[V débil]`. Usuarios en GDMTH/GDMTO: **no encontrado**.
- Tarifa GDMTH: demanda ≥ 100 kW, 1 a 35 kV, tres periodos (base, intermedio, punta); cargo por capacidad ligado a la demanda máxima en punta ([CONUEE](https://www.gob.mx/cms/uploads/attachment/file/831924/DOCUMENTO-VF1.pdf); [Industronic](https://grupoindustronic.com/en/?p=11694)) `[V débil]`. Ejemplo 2025 de cargo de demanda, GDMT: $64.12/kW (Valle de México Centro) y $102.05/kW (Bajío), MXN, **sin aclarar si incluye IVA** ([Luz Noticias, feb-2025](https://www.luznoticias.mx/2025-02-21/mexico/cfe-publica-nuevas-tarifas-de-energia-para-este-2025-asi-quedaron-por-region-y-tipo-de-usuario/235565)). Alzas de 8-12 % en 2025 las cita el estudio industrial.
- **Factor de potencia:** Circutor dice mínimo 0.95 desde 1-ene-2024 para contratos ≥ 1 MW y 0.90 para menores ([Circutor](https://circutor.com/mx/wp-json/wp/v2/posts/54071)); Industronic dice 0.95 para industriales; Tractian dice 0.90 ([Tractian](https://tractian.com/es/calculadora-cfe)). **Las fuentes no coinciden**; fórmula de penalización y bonificación: no encontrado. Ya listado como pendiente en el estudio industrial.
- Hogar, DAC: límites de consumo por tarifa según prensa (1: 250 kWh; 1A: 300; 1B: 400; 1C: 850; 1D: 1,000; 1E: 2,000; 1F: 2,500 kWh/mes); DAC con cargo fijo ≈ $142.41 y energía de $6 a más de $7/kWh según región; promedio móvil de 12 meses ([Yucatán.com.mx, 7-may-2026](https://www.yucatan.com.mx/mexico/2026/05/07/recibo-luz-cfe-2026-tarifa-dac-como-evitar-perder-subsidio.html); [Ámbito](https://www.ambito.com/mexico/economia/adios-al-subsidio-cfe-advierte-que-quintuplicara-el-recibo-deluz-miles-mexicanos-previo-aviso-n6274147)) `[V débil, prensa, no oficial]`. Usuarios DAC: 210,352 de 46.2 millones (0.4 %), **sin año** ([Factor Energético](https://factorenergetico.mx/?p=5739)); otra cifra, 61,550 clientes a fin de 2024, es ambigua. Tomar el orden «cientos de miles» como `[H]`. Es un nicho pequeño.

**Dolores concretos.** Industrial/comercial: demanda en punta, factor de potencia, saber qué máquina o proceso eleva el cargo. Solar: limitar exportación cuando la red o el contrato no lo permiten, y no perder generación. Los dolores específicos de usuarios mexicanos: `[H]`, sin medición propia.

**Quién compra y canal.** Jefes de mantenimiento/energía de naves y comercios en GDMTH, instaladores solares, ingenierías de eficiencia energética, distribuidores eléctricos como Syscom.

**Competencia y precios.**
- Medidores Modbus RS-485 de terceros en Syscom: Total Ground TOV452 (RS-485 Modbus) ([Syscom 152059](https://www.syscom.mx/productosinfo/152059)), Honeywell SPM03EDN ([Syscom 218420](https://www.syscom.mx/productosinfo/218420)), Shelly Pro 3EM con Wi-Fi/Ethernet ([Syscom 217257](https://www.syscom.mx/productosinfo/217257)); Circutor CEM-C21-485 con MID. **Precios en MXN: no encontrado** en lo que devolvió la búsqueda; el Pro 3EM figura a USD 30.00 en una tienda no mexicana, dato dudoso. Hay que cotizar con Syscom.
- Inversores con limitación de exportación nativa: Solis documenta control dinámico con medidor ([Solis](https://www.solisinverters.com/mx/documentation/Solis_Residential_PV_Project_Export_Power_Manage_Solution_mx.html)); el mercado de limitadores de terceros se reduce porque los marcas lo incluyen. Precios: no encontrado.
- Software de energía industrial: ver `ESTUDIO_MERCADO_INDUSTRIAL.md`.

**Regulación.** La instalación del medidor y su certificación metrológica no son de AP: se compra el medidor ya aprobado. La interconexión (permisos CNE, contrato con CFE, UVIE) la gestiona el instalador/dueño. Modificar la protección o el relé de desconexión de la planta sí exigiría pruebas de red `[CG]` y queda fuera.

**¿Sin certificación de red? SÍ, solo en modo lectura y relé de 24 V.** AP lee el medidor por RS-485 (Modbus) y entrega alarmas, tableros locales y, si se quiere, una orden por contacto seco de 24 V a un contactor o al inversor; **no** pasa corriente de red por la placa y **no** es protección. Se vuelve «no» si el producto exige actuar sobre el interruptor de interconexión o ser la protección de anti-isla `[CG]`. Es el segmento con mejor ajuste técnico y menor fricción regulatoria; el riesgo es de mercado (el cliente ya recibe alertas de su inversor o del medidor).

---

## 4. Agua y bombeo (cisternas, riego, organismos operadores)

**Tamaño y tendencia.** 2,922 organismos operadores; 5.5 de cada 10 litros suministrados se facturan; solo 53.3 % de las tomas domésticas tiene medidor ([BBVA Research, 3-ago-2026](https://www.bbvaresearch.com/wp-content/uploads/2026/08/2026-08-03-Nota-situacion-del-agua-2026.pdf), consulta 14-oct-2026) `[V débil]`. El peso de la electricidad en el costo de organismos operadores: 36.5 a 60 % según BDAN, datos de 2021 ([BDAN](https://www.nadb.org/uploads/content/files/UMI%20Seminars/Eficiencia_energtica_sesion_1_23_sept_2021.pdf)). Riego federal: meta de tecnificar más de 200 mil ha con inversión estimada de $51,800 millones entre 2025 y 2030 (otra nota habla de $105 mil millones 2024-2030, no coinciden); 86 distritos de riego; solo ~40 % de la superficie bajo riego con sistema controlado (cifra de 2023) ([Vanguardia](https://vanguardia.com.mx/noticias/mexico/conagua-apuestan-a-tecnificar-200-mil-hectareas-de-riego-AE15441357); [ADN40](https://www.adn40.mx/mexico/2025-01-07/firman-conagua-aguascalientes-convenio-primer-distrito-riego-tecnificado-mexico/)) `[V débil]`. Eficiencia física de organismos (agua producida vs. perdida): solo datos viejos de 2014 y 2002-2008; **no encontrado reciente**.

**Dolores concretos.** Cisternas y tinacos que se desbordan o se secan, bombas que giran en vacío, falta de alternancia de bombas, cobro de energía en horario punta, y en el campo falta de automatización de los pozos. En hogar: un usuario de foro relata que un electronivel Ceisa costó ≈ $500 y el cableado de electrodos otros ≈ $500 (undated, `[CG]`) ([Promodescuentos](https://www.promodescuentos.com/discusiones/contacto-wifi-y-bomba-con-alexa-453787)).

**Quién compra y canal.** Condominios y hoteles (jefe de mantenimiento), instaladores hidroneumáticos, distribuidores de bombas, ingenierías de pozos agrícolas, organismos operadores (licitación pública, ciclo largo) y CONAGUA para riego tecnificado.

**Competencia y precios.** Electroniveles y controles de tinaco/cisterna (Ceisa, kits solares inalámbricos y tableros duplex con alternador) en [Mercado Libre](https://www.mercadolibre.com.mx/shorts/clips/bKvAXP/electronivel-solar-wireless-kit-automatico-tinaco-cisterna); tableros de control de proveedores en [Cosmos](https://www.cosmos.com.mx/producto/tableros-de-control-para-sistemas-de-tinacos-y-cisternas-c18q/). **Precios vigentes en MXN: no encontrado.** Programadores de riego Rain Bird/Hunter: precios solo de España (Rain Bird TM2 6 zonas ≈ 92 a 105 € con IVA, [Obramat](https://www.obramat.es/productos/programador-tm2-rain-bird-6-zonas-interior-25048554.html)) y Chile (Rain Bird ARC6I $117,990 CLP, [Sodimac Chile](https://www.sodimac.cl/sodimac-cl/marca/RAIN%20BIRD)); en México: no encontrado.

**Regulación.** Contactores y arrancadores de motor son productos de terceros certificados; AP no los fabrica. Para pozos y bombas de organismos operadores aplica NOM-001-SEDE en la instalación y las bases de licitación del organismo [CG]. Calidad del agua y medición son otros regímenes (NOM de agua potable) fuera del alcance de una placa de control `[CG]`.

**¿Sin certificación de red? DEPENDE (mayormente sí).** Los sensores de nivel de baja tensión, las entradas y los relés de 24 V que excitan un contactor o una electroválvula de 24 V son manejables con la placa de 24 V. No lo es: vender un «tablero listo» que integre el arranque del motor con tensión de red, que es un tablero eléctrico que debe cumplir la NOM del instalador. Condición: el tablero de potencia lo arma y asume un instalador/tablerista; AP aporta el cerebro de 24 V.

---

## 5. Agro e invernaderos

**Tamaño y tendencia.** Las cifras de agricultura protegida **son inconsistentes**: 27,951 ha (SADER, sin año claro), 51,853 ha (artículo), ~58 mil ha (especialista, 2026), más de 77,000 ha (GreenTech Americas, mar-2026), ~78,000 ha proyectadas por un análisis de mercado; el SIAP reporta 13,413.84 ha solo en Jalisco en 2024 ([Imagen Agropecuaria](https://imagenagropecuaria.com/etiqueta/agricultura-protegida/); [MIDE Jalisco](https://mide.jalisco.gob.mx/mide/reporte/ficha_indicador/1279); [El Financiero, 10-mar-2026](https://www.elfinanciero.com.mx/economia/2026/03/10/horticultura-protegida-y-tecnologia-los-ejes-en-la-greentech-americas-2026/); consulta 14-oct-2026) `[V débil]`. Un artículo académico dice que la política federal de impulso se abandonó desde 2020. Usar un rango **28 mil a 78 mil ha** hasta contrastar con SIAP.

**Dolores concretos.** Ventilación y riego manuales, control de fertirriego, pérdida de cosecha por calor, escasez de agua. Para pequeño productor, controladores de clima de marca (Ridder HortiMaX-Go!, Priva) existen, sin precio en México (no encontrado); ventilación natural con poca o ninguna energía para enfriar es lo que mejor se adapta, lo que reduce la necesidad de un controlador caro ([Colegio de Postgraduados, SciELO](https://www.scielo.org.mx/pdf/rcsh/v18n1/v18n1a9.pdf)) `[V débil]`. Una universidad mexicana (UAZ) afirma un controlador de microclima a ≈ 10 % del precio de uno importado (afirmación de investigadores) ([Portal Frutícola](https://www.portalfruticola.com/noticias/2014/04/23/investigadores-mexicanos-innovan-con-tecnologia-para-invernaderos/)).

**Quién compra y canal.** Productor mediano, empresas de invernaderos llave en mano, distribuidores de insumos y riego, agrónomos. Programas de gobierno: no encontrado para 2026.

**Competencia y precios.** Ridder HortiMaX-Go! ([Ridder](https://ridder.com/ridder-hortimax-go)) sin precio público; controladores de riego Rain Bird/Hunter con precios fuera de México (arriba).

**Regulación.** Para venta de controladores de baja tensión no hay norma específica encontrada; los motores de ventilación y bombas son de terceros. Radio y red como en la sección 0.

**¿Sin certificación de red? DEPENDE (probablemente sí).** Electroválvulas de 24 V, sensores 0-10 V / 4-20 mA, motorreductores de cortina vía contactor/relé externo y lectura Modbus de sensores de clima son compatibles con la placa de 24 V. Riesgos de mercado: conectividad rural, precio muy bajo de la competencia asiática y ciclos agrícolas estacionales; el estudio industrial ya puntuó esto bajo (riego e invernadero: 3/2/5/1).

---

## 6. Cuarto frío y cadena de frío

**Tamaño y tendencia.** Mercado de logística de cadena de frío: USD 7,04 mil millones en 2025, TCAC 4,9 % hasta 2031 (Mordor); IMARC: cadena de frío USD 5,7 mil millones en 2025 con TCAC 17,78 % hasta 2034 y almacenamiento en frío USD 3,4 mil millones ([Mordor](https://www.mordorintelligence.ar/industry-reports/mexico-cold-chain-logistics-market); [IMARC](https://www.imarcgroup.com/report/es/mexico-cold-chain-market); [IMARC almacenamiento](https://www.imarcgroup.com/report/es/mexico-cold-chain-warehousing-market); consulta 14-oct-2026) `[V débil, las dos consultoras discrepan en crecimiento: 4,9 % vs 17,78 %]`. Capacidad: 15 millones de m³ (GCCA, reporte de 2018, dato antiguo); 110 empresas y 176 almacenes refrigerados en DENUE (fecha no confirmada) ([The Logistics World](https://thelogisticsworld.com/historico/gran-potencial-en-cadena-de-frio-del-mercado-mexicano/)). Hay convenio ANETIF-GCCA en 2025 ([BM Editores](https://bmeditores.mx/entorno-pecuario/firman-acuerdo-anetif-y-gcca-para-fortalecer-la-cadena-de-frio-en-mexico/)). Número de cuartos fríos pequeños (carnicerías, florerías, restaurantes, farmacias): **no encontrado**.

**Dolores concretos.** Pérdida de producto por falla de compresor o puerta abierta, evidencia de temperatura ante auditorías, alarma remota, desescarche y arranque escalonado de compresores. Para fármacos, las normas exigen evidencia de que no se rompió la cadena y registros de data loggers y calibración (fuente comercial, no el DOF) ([Logistics World, ago-2026](https://thelogisticsworld.com/logistica-y-distribucion/estandares-logisticos-certificaciones-distribucion-medicamentos-mexico/)) `[V débil]`.

**Quién compra y canal.** Técnicos de refrigeración (instaladores), restauranteros, supermercados, bodegas de alimentos/fármacos, empacadoras. Canal: distribuidores de refrigeración y técnicos; para farmacia/cuarto validado, empresas de monitoreo.

**Competencia y precios (MXN, publicaciones de minorista, IVA incluido [CG]).** Danfoss UT72 ≈ $1,035 ([Mercado Libre](https://listado.mercadolibre.com.mx/danfoss-controlador-temperatura)); Carel PZGXS0J111 ≈ $1,799 (Icehaus) ([Mercado Libre Carel](https://listado.mercadolibre.com.mx/control-de-temperatura-carel)); Dixell ≈ $1,049.27 y genéricos de $750 a $920 ([eBay México](https://mx.ebay.com/b/Refrigerator-Temperature-Control-In-Plc-Temperature-Modules/181723/bn_7022193618)). Inkbird ITC-308 (Wi-Fi opcional): CAD 35.99 / AUD 37.11 / USD 35 a 49, sin dato en MXN ([Inkbird](https://ca.inkbird.com/products/temperature-controller-itc-308)). **Un controlador de cuarto frío cuesta $750 a $1,800 MXN**: una placa de AP no compite como termostato; solo con lo que ellos no dan (registro, alarma, lógica de varios compresores, desescarche, Modbus).

**Regulación.** Para alimentos aplica NOM-251-SSA1 (higiene), para medicamentos NOM-059-SSA1 y COFEPRIS; ambos regulan **al usuario y el proceso**, no obligan a un producto a tener sello. Para vacunas y medicamentos puede pedirse calibración trazable del sensor `[CG]`; la placa necesitaría sondas con certificado de calibración de terceros. Las fuentes encontradas son secundarias; verificar texto en el DOF.

**¿Sin certificación de red? DEPENDE.** Sí si AP lee sondas (NTC/PT100 por módulo externo o 4-20 mA), registra, alarma y comanda el compresor por **contactor externo** con contacto seco; no si la placa conmuta el compresor. La seguridad de alimentos y la de fármacos no son seguridad funcional, pero una alarma que no avisa es un riesgo de responsabilidad (no se promete garantía de conservación). Buen candidato.

---

## 7. Retail y comercio (letreros, iluminación, climatización)

**Tamaño y tendencia.** ANTAD: 27,313 tiendas (3,906 autoservicio, 1,576 departamentales, 21,831 especializadas) y 20.1 millones de m² de piso de ventas; **la fuente es un artículo con fecha dudosa**, verificar con ANTAD ([The Logistics World](https://thelogisticsworld.com/historico/reporta-antad-un-aumento-del-4-2-en-las-ventas-de-afiliados)) `[V débil]`. Ventas ANTAD de 2024: $1 billón 614.7 mil millones, +7.1 % ([El CEO](https://elceo.com/negocios/supermercados-y-departamentales-invertiran-3000-mdd-en-2025-antad/)); inversión anunciada USD 3,000 millones en 2025. Censos Económicos 2024 del INEGI: 749,365 unidades económicas en el universo de la ficha citada; 95.4 % microempresas ([INEGI](https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2025/ce/CE_2024_Def_EdMx.pdf); [México ¿cómo vamos?](https://mexicocomovamos.mx/?p=36045)) `[V débil]`. El número de comercios al por menor (SCIAN 46) y de abarrotes: **no encontrado** (hay que sacarlo de las tablas del INEGI).

**Dolores concretos.** Letreros e iluminación prendidos fuera de horario, aire acondicionado sin control central, tiendas de cadena sin visibilidad del consumo por sucursal, refrigeración de exhibidores (ver cuarto frío) `[H]`. Sin medición propia.

**Quién compra y canal.** Gerencias de mantenimiento/operaciones de cadenas (compra central, exige proveedor homologado y soporte nacional), franquicias, dueños de comercios pequeños (compra por distribuidor eléctrico o Mercado Libre).

**Competencia.** Apagadores programables/temporizadores y fotoceldas (muy baratos); BMS para cadenas; precios: **no encontrado**.

**Regulación.** NOM-007-ENER-2014 fija densidad de potencia del alumbrado interior y exterior de edificios nuevos o ampliados con ≥ 3 kW instalados; no aplica a un control como producto [V débil, IEA]. No encontré fuente que diga si los letreros luminosos entran; NOM-031-ENER-2012 corresponde a luminarias LED de vialidad. Conmutar cargas de red de un local (letrero, aire) con contactores es instalación NOM-001-SEDE.

**¿Sin certificación de red? DEPENDE (más bien NO para el producto central).** Sí para medir/registrar y comandar contactores de un tablero hecho por el instalador; no para vender «control de letrero» con relé de red en la placa. Compite con temporizadores muy baratos y exige soporte en múltiples sucursales: poco atractivo al inicio.

---

## 8. Educación técnica (CONALEP, universidades tecnológicas)

**Tamaño y tendencia.**
- CONALEP: 313 planteles y 321,236 alumnos en el ciclo 2025-2026 (313,525 escolarizados y 7,711 en Sistema Dual); 324,335 en 2024; 64 carreras, 45 de ellas del área industrial (documento de Quintana Roo) ([CONALEP, informe 2025-2026](https://www.conalep.edu.mx/sites/default/files/micrositios/dpp/L5X%20CONALEP_Informe%20avance%20y%20resultados%202025-2026%20vf.1%20def.pdf); [Cuenta Pública 2024](https://www.cuentapublica.hacienda.gob.mx/work/models/CP/2024/tomo/VII/MAT_Print.11L5X.01.INTRO.pdf); [CONALEP Q. Roo](https://conalep.qroo.gob.mx/wp-content/uploads/2024/11/Guia-para-la-Proyeccion-de-los-Espacios-Educativos-en-el-CONALEP-Quintana-Roo.pdf); consulta 14-oct-2026) `[V débil]`.
- Universidades Tecnológicas y Politécnicas (UTyP): 191 instituciones en 31 estados (SEP, 2025) y ~240,164 alumnos de TSU y licenciatura en tecnológicas más 105,357 en politécnicas (ciclo 2024-2025 preliminar, SEP 911) ([Excélsior](https://www.excelsior.com.mx/nacional/sep-impulsa-plan-estrategico-fortalecer-sistema-tecnologico-politecnico/1744058); [ANUIES CUPIA, mayo 2025](https://organoscolegiados.anuies.mx/cupia/wp-content/uploads/sites/6/2025/05/11.-CUPIA-23.05.2025-final.pdf)) `[V débil, cifras de alumnado inconsistentes entre fuentes]`.
- Tecnológico Nacional de México (institutos tecnológicos) y bachilleratos tecnológicos (CBTis/CETis): no investigados; hay que sumar si el canal escolar es prioritario.

**Dolores concretos.** Entrenadores didácticos de Festo/Siemens son caros y de marca única; kits de PLC con Arduino son una alternativa barata documentada en la literatura (hasta > 50 % más baratos en un trabajo de Malasia de 2015) ([UTHM/UiTM](https://oarr.uitm.edu.my/search/Record/uthm-1379/Details)). Precio de entrenadores en México: **no encontrado**. Necesidad real de los planteles y presupuesto de equipamiento: no encontrado `[H]`.

**Quién compra y canal.** Dirección de plantel, coordinación de carrera, jefes de laboratorio; compras gubernamentales por licitación o adjudicación directa con proveedores registrados; convenios con empresas (modelo dual). Ciclos ligados al presupuesto anual `[CG]`.

**Competencia.** Festo Didactic ([catálogo](https://www.festo.com/pdf_flip/didactic/Factory_Automation/en/252-253/)) y Siemens LOGO! en paneles didácticos; Controllino con kit de entrenamiento comercial. Precios: no encontrado.

**Regulación.** Un kit en 24 V CC con fuente certificada de terceros tiene el mejor perfil de seguridad: baja tensión, sin red en la placa. La compra pública exige facturar con RFC, registros de proveedor y, en ciertos casos, certificados de producto `[CG]`: pregunta para legal. La entrega a menores aconseja la etiqueta de baja tensión y manual de seguridad.

**¿Sin certificación de red? SÍ.** Es el segmento donde la restricción de 24 V es una ventaja. Es de bajo volumen económico por unidad pero sirve para validar firmware/app, generar casos y formar a futuros técnicos (ya listado como AP Lab en el estudio industrial).

---

## 9. Cuadro comparativo de los ocho segmentos

| # | Segmento | Tamaño con cifra (fiabilidad) | Comprador y canal | Ancla de precio | Papeles que bloquean | ¿Sin certificar red? |
|---|---|---|---|---|---|---|
| 1 | Hogar inteligente | USD 1,8 mil M (2025, IMARC, pago) | Consumidor, marketplaces | $369-489 MXN apagador Steren | NOM-003, NOM-001-SCFI, radio | **No** |
| 2 | Edificios y propiedades | USD 2,7-4,8 mil M (rango); 909 mil cuartos de hotel | Administrador, integrador | no encontrado | UVIE en lugares de concentración | **Depende** |
| 3 | Energía | 5.16 GW GD solar; GDMTH ≥ 100 kW | Mantenimiento, instalador solar | medidor Modbus: sin MXN | Interconexión CNE/CFE del cliente | **Sí (lectura y 24 V)** |
| 4 | Agua y bombeo | 2,922 organismos; 200 mil ha a tecnificar | Condominio, instalador, organismo | electronivel ≈ $500 (dato viejo) | Tablero de potencia del instalador | **Depende** |
| 5 | Agro e invernaderos | 28 a 78 mil ha (no coincide) | Productor, llave en mano | sin MXN | Radio si hay WiFi | **Depende** |
| 6 | Cuarto frío | USD 5,7-7,0 mil M (consultoras discrepan) | Técnico de refrigeración | $750-1,800 MXN controlador | COFEPRIS en fármacos (proceso) | **Depende** |
| 7 | Retail y comercio | 27,313 tiendas ANTAD (fecha dudosa) | Mantenimiento de cadenas | no encontrado | NOM-007-ENER (diseño), NOM-001-SEDE | **Depende (más no)** |
| 8 | Educación técnica | 313 planteles CONALEP; 191 UTyP | Dirección, licitación | no encontrado | Compras públicas | **Sí** |

---

## 10. Ranking con criterios explícitos

**Criterios (1 a 5; 5 es lo mejor).** A: dolor evidenciado y pagado; B: libertad de certificación de red (5 = nada de red); C: encaje con el hardware y software ya diseñado (24 V, Modbus, tablero local); D: acceso a clientes en ≤ 3 meses sin intermediarios largos; E: espacio frente a la competencia (a un precio de 55-88 USD de clones no se compite solo con relés); F: calidad del dato de mercado (menor incertidumbre). Pesos `[H]`: A 25 %, B 25 %, C 20 %, D 15 %, E 10 %, F 5 %. **Son puntuaciones del analista basadas en lo que pude ver; no hay entrevistas.**

| Segmento | A | B | C | D | E | F | Total ponderado |
|---|---|---|---|---|---|---|---|
| 3 Energía (lectura Modbus, alarma, 24 V) | 4 | 5 | 5 | 3 | 3 | 3 | **4.15** |
| 8 Educación técnica | 3 | 5 | 5 | 3 | 3 | 4 | **3.95** |
| 6 Cuarto frío (monitoreo, registro, alarma) | 4 | 4 | 4 | 4 | 3 | 2 | **3.8** |
| 4 Agua y bombeo | 4 | 3 | 4 | 3 | 3 | 3 | **3.45** |
| 5 Agro e invernaderos | 3 | 3 | 4 | 3 | 3 | 1 | **3.1** |
| 2 Edificios y propiedades | 3 | 3 | 3 | 2 | 3 | 2 | **2.8** |
| 7 Retail y comercio | 2 | 2 | 3 | 2 | 2 | 2 | **2.2** |
| 1 Hogar inteligente | 2 | 1 | 2 | 2 | 1 | 3 | **1.7** |

Cálculo `[C]`: p. ej. Energía = 4×0.25 + 5×0.25 + 5×0.20 + 3×0.15 + 3×0.10 + 3×0.05 = 4.15. Educación 3.95, Cuarto frío 3.80, Agua 3.45. El orden entre 3, 8 y 6 es sensible a los pesos; solo las entrevistas lo desempatan.

## 11. Cinco apuestas para validar primero con entrevistas

1. **Monitor de demanda y factor de potencia en GDMTH (lectura de medidor Modbus de terceros + alarma de pico).** Entrevistar jefes de mantenimiento/energía de 8 a 10 naves y comercios con demanda ≥ 100 kW y a 3 gestores energéticos. Validar: ¿ya existe el medidor?, ¿se sabe qué línea causa el pico?, ¿pagarían un tablero local sin nube? Ya es la idea n.º 2 del estudio industrial.
2. **Monitoreo y alarma de cuarto frío con contacto seco al contactor** (carnicerías, restaurantes, empacadoras, farmacias privadas). Entrevistar 10 técnicos de refrigeración y 5 dueños. Validar el dolor de pérdida de producto, si pagan sobre un controlador de $1,000-1,800, y si necesitan registro con sonda calibrada.
3. **Bombeo de cisterna/hidroneumático para condominios y hoteles pequeños (alternancia de bombas, nivel, protección de marcha en seco por entrada de 24 V).** Entrevistar administradores, jefes de mantenimiento e instaladores de bombas. Validar quién arma el tablero y si aceptan que AP solo provea la parte de 24 V.
4. **Solar con inyección cero o limitación de exportación para naves/comercios** (leyendo medidor e inversor por Modbus). Entrevistar 5 instaladores solares y 3 usuarios. Validar si los inversores ya lo resuelven (Solis lo documenta) y si queda hueco en plantas con varios inversores o marcas.
5. **Kit de enseñanza en 24 V para CONALEP/UTyP.** Entrevistar 5 coordinadores de carrera y 3 jefes de laboratorio. Validar presupuesto, proceso de compra pública, y qué kit usan hoy (marca y precio, hoy no encontrado). Sirve de banco de pruebas barato para las otras cuatro.

Descartadas por ahora: hogar (requiere red, precio ancla muy bajo), retail (compite con temporizadores) y edificios como segmento propio (ciclo largo, se alcanza vía las apuestas 1 y 3).

## 12. Preguntas abiertas

1. ¿Qué laboratorio decide si una placa solo alimentada con una fuente certificada de 24 V CC entra en NOM-001-SCFI-2018 y NOM-003-SCFI-2014? Pedir criterio por escrito a NYCE y ANCE (con costo y plazo). Tampoco sé qué autoridad homologa hoy el radio.
2. ¿Cuál es el umbral y la fórmula vigentes de factor de potencia en GDMTH y GDMTO (0.90 contra 0.95) y cuántos usuarios hay en esas tarifas? Abrir el tarifario oficial y el Código de Red.
3. ¿Cuánto cuestan en MXN con IVA los medidores Modbus (Total Ground, Honeywell, Shelly Pro 3EM, Eastron) en Syscom? Cotizar.
4. ¿Cuántos cuartos fríos pequeños hay y qué paga hoy quien monitorea (data logger, servicio)? Sin dato público.
5. ¿Cuál es la superficie real de agricultura protegida (SIAP 2025) y quién compra controladores en pequeña escala?
6. ¿El mercado de bombeo condominal paga por alternancia y protección de marcha en seco, o lo resuelve un electronivel de $500?
7. ¿Qué exigen las compras públicas educativas (registro de proveedor, certificados de producto, garantía) y con qué presupuesto?
8. ¿Se puede vender solo la parte de 24 V sin que el cliente culpe a AP de fallas del tablero de potencia? Contrato, aviso y alcance de responsabilidad: legal.
9. Las cifras de consultoras (IMARC, Mordor, MarketsandMarkets) son de pago y discrepan; ¿vale la pena comprar un informe o basta con entrevistas?
10. Abrir cada URL citada completa (la herramienta de lectura falló en esta sesión) y confirmar que el dato se encuentra en el documento.

---

## Hallazgos (por orden de importancia)
1. **El mejor ajuste con menos riesgo regulatorio es leer y alertar, no conmutar red:** energía (medidor Modbus de terceros), cuarto frío (sondas + contacto seco), bombeo (nivel + contactor externo) y educación. Hogar y retail exigen conmutar 127 V.
2. **Cifras de mercado débiles y contradictorias:** agricultura protegida (28 a 78 mil ha), cadena de frío (TCAC 4,9 % contra 17,78 %), edificios (USD 2,7 a 4,8 mil M), factor de potencia (0.90 contra 0.95). No usar ninguna sin abrir la fuente.
3. **Precios en México casi no se encontraron** para medidores Modbus, cuarto frío (solo controladores sueltos), riego y entrenadores; no hay ancla para fijar precio.
4. **El hogar tiene ancla de precio muy baja** ($369 a $489 MXN un apagador Wi-Fi) y exige certificación: confirmar la pausa de AP Home.
5. **La pregunta regulatoria central (placa de 24 V alimentada por fuente de terceros) sigue sin respuesta oficial.**

## Qué falta saber
Ver sección 12.

## Siguiente paso recomendado
Preparar guiones de entrevista para las cinco apuestas (sección 11) y pasarlos a `ap-ventas-clientes`; en paralelo, pedir a `ap-calidad-normas` el criterio de NYCE/ANCE y cotizar medidores Modbus con `ap-compras-proveedores`. No abrir preventa (puerta B o C) por ninguno de estos segmentos antes de las entrevistas.

## Fuentes
Todas consultadas el 14-oct-2026 mediante WebSearch (sin lectura de página completa): las URL están citadas en línea en cada sección. Fuentes de partida del repositorio: `hardware/ap-electric/ESTUDIO_MERCADO_INDUSTRIAL.md`, `hardware/ap-electric/ANALISIS_ECOSISTEMA.md`, `empresa/CONTEXTO_COMPARTIDO.md`, `empresa/ORGANIZACION.md`.
