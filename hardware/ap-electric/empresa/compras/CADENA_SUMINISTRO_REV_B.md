# Cadena de suministro: placa 7R Tour rev B 24DC

Fecha de consulta: 14-oct-2026. Agente: ap-compras-proveedores. Estado: análisis documental; nada se ha pedido, cotizado ni medido.

Marcas: `[V]` dato con fuente y fecha · `[R]` dato del repositorio · `[C]` cálculo · `[CG]` conocimiento general sin verificar · `[H]` hipótesis · `PD` por determinar.

## 0. Límites de esta investigación (leer primero)
- `WebFetch` no pudo abrir ningún sitio externo (el proxy de la sesión rechazó jlcpcb.com, omron.com, espressif.com). Todo lo `[V]` sale de **resultados de WebSearch** (fragmentos y listados de distribuidores), consultados el 14-oct-2026. No leí las hojas de datos oficiales completas. Cada dato de un distribuidor debe confirmarse en el PDF del fabricante antes de pedir.
- Las clases Basic/Preferred/Extended de la tabla vienen de `AP_7R_TOUR_24DC_BOM_JLCPCB.csv`, `hardware/tools/jlcpcb.py` y `jlcpcb_catalogo.csv` `[R]`. **No las reverifiqué en vivo** en jlcpcb.com; la clase y las existencias cambian.
- Los precios del catálogo del repositorio son una instantánea de fecha desconocida `[R]`.

## 0.1 Inconsistencia del repositorio que afecta la compra
- `RESUMEN_JLCPCB.txt` lista 59 tipos y 21 Extended, e incluye **PS1 IRM-20-24 (C194964), RV1 10D471K (C317795), F2 T2A 250VCA (C2838939), J8, C3, D3**. El BOM `AP_7R_TOUR_24DC_BOM_JLCPCB.csv` **no los tiene** (tiene 20 filas Extended distintas: sin PS1, RV1, F2). Hay que saber cuál es la rev B vigente: el resumen parece de otra variante (con fuente de red).
- Si PS1/RV1/F2 (fuente de 127/220 V, varistor y fusible de 250 VCA) fueran parte del piloto, chocarían con la regla 6 del contexto compartido (nada de red en el piloto). Se lo señalo a ap-hardware y a la dirección; no lo corrijo.
- Consecuencia: los conteos de «21 tipos Extended ~63 USD» están sujetos a esta aclaración (ver §2).

## 1. Piezas críticas

Columnas de riesgo: **mono** = una sola fuente de fabricante; **ciclo** = estado de vida; **plazo** = existencias/plazo visto.

### 1.1 Relé Omron G2RL-1A-E DC24 (K1 a K7, LCSC C231362, Extended `[R]`)
- **Función:** salida de potencia a contacto seco, 7 canales, bobina 24 V.
- **Riesgo:** mono (Omron) `[CG]`. Los listados de distribuidores coinciden en bobina 1.44 kΩ, 16.7 mA, 15 ms de operación, SPST-NO, 29 x 12.7 x 15.7 mm `[V]` https://pcxco.com/electronic-components/G2RL-1A-E-DC24 (14-oct-2026). **Hay conflicto de fuentes sobre la capacidad en 24 VCD**: una hoja de Omron para G2RL-1A-E-CF DC9 da 16 A a 250 VCA y 24 VCD `[V]` https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/1062/G2RL-1A-E-CF-DC9_Spec.pdf (hoja de 2011, otra bobina); un listado de distribuidor da 12 A / 24 VCD para el G2RL-1A sin «-E» (misma búsqueda). No usar ninguna capacidad en la documentación hasta leer la hoja Omron del código exacto.
- **Alternativa casi pin a pin:** Hongfa HF115F/024-1HS3A, 16 A / 250 VCA, bobina 24 V 1.44 kΩ, caja 29 x 12.7 x 15.7 mm, 6 pines `[V]` https://www.lcsc.com/product-detail/C2976789.html (14-oct-2026). La coincidencia de huella **no está confirmada**; comparar el dibujo de pines de ambas hojas antes de cualquier cambio. La variante sin «A» (C24645) aparece sin existencias.
- **Clase JLCPCB:** Extended `[R]`.

### 1.2 ESP32-C3-WROOM-02 (U9, C2934560, Extended `[R]`)
- **Función:** MCU, Wi-Fi y BLE.
- **Riesgo:** mono (Espressif). No encontré aviso NRND para el ESP32-C3-WROOM-02 `[V]`; sí aparece NRND en módulos vecinos: ESP32-C3-MINI-1-N4 según Mouser `[V]` https://www.mouser.in/ProductDetail/356-ESP32-C3-MINI1N4 y ESP-WROOM-02D/02U (datasheet v2.3, 2025.11) `[V]` https://documentation.espressif.com/esp-wroom-02d_esp-wroom-02u_datasheet_cn.html. Espressif afirma que NRND no afecta su compromiso de longevidad `[V]` https://www.espressif.com/products/longevity-commitment. Confirmar el estado del C3-WROOM-02 en esa página y en la hoja https://documentation.espressif.com/0c-esp-wroom-02_datasheet_en.html (cuyo nombre de archivo parece de la familia ESP-WROOM-02; verificar que sea la hoja correcta).
- **Alternativas:** ninguna respaldada con hoja. El ESP8684-WROOM-02C se menciona como sucesor del ESP-WROOM-02D `[V]`, pero no se afirma compatibilidad de pines con el C3-WROOM-02: PD, pedir a ap-firmware/ap-hardware que la comparen.
- **Clase:** Extended `[R]`.

### 1.3 CA-IS3092W (U6, C2890051, Extended `[R]`)
- **Función:** transceptor RS-485 aislado con DC-DC integrado, SOIC-16 ancho, hasta 5 kVrms; la serie CA-IS3092 llega a 0.5 Mbps `[V]` https://www.compel.ru/infosheet/CHIPANLG/CA-IS3092W (hoja Chipanalog v1.09 de 2023/05/23; v1.13 listada).
- **Riesgo:** mono (Chipanalog), proveedor menos conocido en México `[CG]`; plazo PD. Las variantes VW agregan una alimentación lógica separada: no son sustituto directo.
- **Alternativa pin a pin:** no encontrada con respaldo. Hay que comparar las hojas de otros RS-485 aislados de 16 pines (TI, ADI, Silicon Labs) contra la del CA-IS3092W; sin comparación, `PD`.
- **Clase:** Extended `[R]`.

### 1.4 TCA9554PWR (U2 a U5, C477924, Extended `[R]`)
- **Función:** expansor I2C de 8 bits (4 piezas).
- **Riesgo:** TI lo marca activo y recomendado para diseños nuevos `[V]` https://www.radiolocman.com/datasheet/data.html?di=222921; hoja https://www.ti.com/document-viewer/TCA9554/datasheet. Las 4 piezas comparten un solo código, así que cuentan como un solo tipo Extended (un solo cargo).
- **Alternativa:** PCA9554PWR aparece como «no para diseños nuevos» `[V]` https://www.cytechsystems.com/de/product/pca9554pwr; **no la recomiendo**. Sin otra alternativa respaldada.
- **Clase:** Extended `[R]`.

### 1.5 ULN2003A (U1, ULN2003ADR C7512, Basic `[R]`)
- **Función:** excitador Darlington de 7 canales para las bobinas.
- **Riesgo:** bajo; TI activo, recomendado para diseños nuevos, y hay segunda fuente `[V]` https://www.radiolocman.com/datasheet/data.html?di=95446. Catálogo del repositorio: 414,440 en existencia a 0.159 USD `[R]` (fecha desconocida).
- **Alternativas casi pin a pin (verificar hoja):** onsemi ULN2003ADR2G y MC1413BDR2G (como sustituto en la lista de DigiKey) y ST ULQ2003 `[V]` https://punchouttest.digikey.de/en/products/detail/texas-instruments/ULN2003AIDRE4/1912622 y https://www.oemstrade.com/search/ULN2003A. La compatibilidad de pines es práctica común `[CG]`; no la he leído en hojas de onsemi ni ST.
- **Clase:** Basic `[R]`.

### 1.6 LMR16006XDDC (U7, C87080, Extended `[R]`)
- **Función:** reductor de 60 V / 0.6 A para el bus de 24 V. La X es la versión de 0.7 MHz (la Y, 2.1 MHz) `[V]` https://www.ti.com/product/LMR16006 (activo, 4 a 60 V, SOT-23-THN de 6 pines).
- **Riesgo:** mono (TI); plazo PD. La variante Y no es sustituto (cambia la frecuencia y los pasivos).
- **Alternativa:** ninguna respaldada con hoja.
- **Clase:** Extended `[R]`.

### 1.7 AP63203WU (U8, C780769, Extended `[R]`)
- **Función:** reductor síncrono de 2 A, entrada 3.8 a 32 V, 1.1 MHz, TSOT26; la salida de 3.3 V solo la dan listados de terceros `[V]` https://www.diodes.com/part/AP63203 y https://www.radiolocman.com/datasheet/data.html?di=580805. Confirmar en la hoja de Diodes Inc.
- **Riesgo:** mono (Diodes Inc.). Entrada máxima de 32 V frente a un bus de 24 V con transitorios: el SMBJ33A limita a unos 53 V `[V]` (ver §1.11), por encima de los 32 V del reductor. **Hallazgo para ap-hardware:** revisar si el AP63203 se alimenta antes o después de LMR16006X (si está detrás, sin problema; si cuelga del bus de 24 V, el margen es corto).
- **Alternativas:** AP63200/AP63201/AP63205 son otras salidas/frecuencias de la misma familia, no sustitutos. Ninguna respaldada.
- **Clase:** Extended `[R]`.

### 1.8 LTV-217 (OK1 a OK8, C115450, Basic `[R]`)
- **Función:** optoacopladores de las 8 entradas.
- **Riesgo:** bajo; catálogo del repositorio: Lite-On LTV-217-B-G, 23,767 en existencia, 0.064 USD `[R]`. Los listados difieren en tensión/aislamiento (70 V/3 kV vs 80 V/3.75 kV según variante) `[V]` https://fat.lcsc.com/product-detail/Optocouplers-Phototransistor-Output_Lite-On-LTV-217-B-G_C115450.html.
- **Alternativas misma huella (otra banda de CTR):** LTV-217-A-G (C123195) y LTV-217-C-G (C123196) `[V]` https://datasheet.lcsc.com/lcsc/2304140030_Lite-On-LTV-217-A-G_C123195.pdf y https://datasheet.lcsc.com/lcsc/2304140030_Lite-On-LTV-217-C-G_C123196.pdf. Cambia la ganancia (CTR): hay que recalcular las resistencias de entrada (ap-hardware).
- **Clase:** Basic `[R]`.

### 1.9 PCF8563T/5,518 (U11, C7440, Extended `[R]`)
- **Función:** reloj de tiempo real I2C.
- **Riesgo (el más delicado del grupo):** LCSC trae una nota de «no recomendado para diseños nuevos»; otros distribuidores lo dan por activo; DigiKey lo mostraba sin existencias con plazo de 16 semanas `[V]` https://fat.lcsc.com/product-detail/Real-time-Clocks-RTC_NXP-Semicon-PCF8563T-5-518_C7440.html y https://punchouttest.digikey.ca/en/products/detail/nxp-usa-inc/PCF8563T-5-518/2606091. No encontré el estado oficial de NXP.
- **Alternativas:** DigiKey sugiere Renesas, Abracon, Rohm y ADI/Maxim, **sin números de parte ni compatibilidad confirmada** `[V]`; no listo códigos. Acción: pedir a ap-firmware si el RTC es indispensable o si basta el del ESP32.
- **Clase:** Extended `[R]`.

### 1.10 Bornes KF128-5.08-2P / -3P (J1 a J7, J9; J11 a J14; C474952 / C474953, Extended `[R]`)
- **Función:** conexión de campo, paso 5.08 mm.
- **Riesgo:** Kefa (KEFA), marca genérica; el listado dice 24 A y -40 a +105 °C para el KF128-5.08-2P-AA `[V]` https://www.flux.ai/lcsc/kf128-5p08-2p-aa~0pbi.md. Otro listado da 250 V y 22-12 AWG para el KF128-5.08-2P `[V]` https://www.hqonline.com/product-detail/terminal-blocks-kefa-kf128-5-08-2p-2500313692. **No hay una calificación de seguridad (UL/VDE) confirmada para el borne**; no afirmarla.
- **Alternativa:** RS PRO CTB0509, 2 contactos, 5.08 mm, LCSC C53900280 `[V]` https://www.lcsc.com/product-detail/C53900280.html. Altura y huella sin comprobar: «casi», verificar.
- **Clase:** Extended `[R]`. Son piezas de patas: soldadura a mano en el pedido económico `[R]`.

### 1.11 USB-C (J15, HRO TYPE-C-31-M-12, C165948, Extended `[R]`)
- **Función:** programación/consola.
- **Riesgo:** mono (Hroparts); existencias 71,000 a 156,000 según la captura; los listados difieren en contactos y corriente (16 contactos, 5 A vs 3 A) `[V]` https://lcsc.com/product-detail/C165948.html y https://hqonline.com/product-detail/usb-connectors-hro-type-c-31-m-12-2500242159. La hoja oficial no apareció.
- **Alternativa:** hay un hilo de alternativas en el foro de DigiKey https://forum.digikey.com/t/alternative-for-type-c-31-m-12-from-korean-hroparts-elec/30155 (no leído). Otros TYPE-C-31-M-31 (C2760486) y -26A (C2848621) `[V]` son otras huellas: no son sustituto directo.
- **Clase:** Extended `[R]`.

### 1.12 Fusible 3 A 1206 (F1, JK 12 100.3, C355685, Extended `[R]`)
- **Función:** protección del bus de entrada.
- **Riesgo alto de suministro:** LCSC lo mostraba **sin existencias**, mínimo de 10 `[V]` https://www.lcsc.com/de/product/C355685.html (captura 14-oct-2026). Rápido, 1206, 3 A, 72/63/32/24 VCD, 50 A a 72 VCD, AEC-Q200.
- **Alternativas 3 A 1206 encontradas (verificar voltaje, curva y huella):** Reomax R12.100.3 (C2874926) `[V]` https://www.lcsc.com/product-detail/C2874926.html; AEM F1206HI3000V032TM (C85063, 32 V) `[V]` https://www.lcsc.com/product-detail/C85063.html; BHFUSE BSMD1206C-1300T (C41367225, 72 V) `[V]` https://www.lcsc.com/product-detail/C41367225.html. Con bus de 24 V, 32 V deja poco margen; preferir la de 72 V si la hoja lo confirma. Decisión final: ap-hardware y calidad.
- **Clase:** Extended `[R]`.

### 1.13 Supresor SMBJ33A (D2, C19077586, Preferred `[R]`)
- **Función:** TVS unidireccional del bus. Datos de distribuidor: 33 V de reposo, ruptura mínima 36.7 V, sujeción máxima 53.3 V, 600 W, DO-214AA `[V]` https://www.digikey.com/en/products/detail/littelfuse-inc/SMBJ33A/286006 (consulta equivalente en digikey.it).
- **Riesgo:** bajo; múltiples fabricantes. Alternativa mismo código de industria: SMBJ33A-13-F de Diodes Inc. `[V]` https://ciiva.com/part/smbj33a-13-f-282874. Verificar la hoja (tensión de sujeción). Ver la nota de margen en §1.7.
- **Clase:** Preferred `[R]`.

### 1.14 Cristal 32.768 kHz 12.5 pF (Y1, Epson Q13FC13500004, C32346, Extended `[R]`)
- **Función:** base de tiempo del RTC. Datos: ±20 ppm, 70 kΩ ESR máx., 3215, -40 a +85 °C `[V]` https://www.lcsc.com/product-detail/C32346.html.
- **Riesgo:** mono (Epson) para ese código; cristales de 32.768 kHz son comunes, pero la carga de 12.5 pF debe corresponder a los capacitores del PCF8563. Alternativa respaldada: ninguna.
- **Clase:** Extended `[R]`.

### 1.15 DIP de 8 posiciones (SW1, DSWB08LHGET, C99413, Extended `[R]`)
- **Función:** dirección/configuración. Pieza de patas (soldadura a mano en el pedido económico) `[R]`.
- **Riesgo:** mono; no encontré hoja ni listado en esta ronda (la búsqueda cubrió solo el fusible). Alternativa y datos: `PD`.
- **Clase:** Extended `[R]`.

### 1.16 Resumen de riesgo (para la dirección)
1. Fusible JK 12 100.3 sin existencias (verificado en captura): cambiar o confirmar antes de pedir.
2. PCF8563T: señales mixtas de ciclo de vida y plazo largo.
3. Relé Omron: mono y con capacidad en 24 VCD contradictoria entre fuentes.
4. CA-IS3092W: mono, sin alternativa respaldada.
5. Inconsistencia BOM vs RESUMEN (§0.1).

## 2. Estructura de costo de la primera tanda (5 placas)

| Rubro | Qué es | Estado | Cómo obtenerlo |
|---|---|---|---|
| PCB 2 capas, 2 oz | Fabricación de 5 placas | **PD** | En el cotizador de JLCPCB: dimensiones, 2 capas, espesor, **cobre exterior 2 oz**, acabado, color de máscara. JLCPCB declara 1 o 2 oz exterior `[V]` https://jlcpcb.com/help/article/jlcpcb-copper-weight; el sobrecosto de 2 oz no lo encontré en fuente oficial. Con 2 oz, el mínimo ancho/espacio es 8 mil frente a 5 mil con 1 oz `[V]` (misma fuente): ap-hardware debe revisar DRC. |
| Ensamble: cargo de montaje/arranque | Cargo fijo por pedido | **PD** | Cotizador de ensamble: lado(s), tipo económico/estándar, cantidad 5; pedir el desglose de «setup/stencil/ingeniería». |
| Cargo por tipo Extended | ~3 USD por tipo Extended por pedido `[R]` (resumen) y `[V]` secundario: https://www.elektroda.com/qa,jlcpcb-component-library-parts.html y otros; sin fuente oficial leída. JLCPCB a veces exonera piezas frecuentes `[V]` | **`[C]`** 20 o 21 tipos Extended x 3 = ~60 a 63 USD (el BOM del CSV tiene 20 filas Extended; el resumen dice 21); pedido económico 14 tipos = ~42 USD `[R]` | Confirmar la cifra y los tipos en el carrito. Depende de la aclaración de §0.1. |
| Piezas Basic/Preferred | Costo de componentes | **`[R]`** ~1.02 USD por placa (catálogo) = **~5.1 USD en 5 placas** `[C]` | Reconfirmar con el carrito; fecha del catálogo desconocida. |
| Piezas Extended (precio de la pieza) | Relés, ESP32, bornes, etc., por 5 placas | **PD** | Cargar el BOM/CPL en el cotizador y exportar el desglose «parts cost»; anotar cantidad mínima de compra por línea (el fusible pide 10 `[V]`). |
| Piezas a mano | 24 piezas de patas en el pedido económico `[R]` | **PD** | Costo de mano de obra propia o taller (ver §3). |
| Envío internacional | DHL u otro | **PD** | Cotizador al seleccionar México; pedir peso y modalidad (ver §5). |
| Aranceles y IVA | Importación a México | **PD** (referencias abajo) | Ver §5. IVA 16 % `[V]` https://flavorcloud.com/knowledge-base/mexico-country-guide-import-and-landed-cost-reference ; DTA 0.8 % (fuente secundaria) ; tasa de paquetería 33.5 % «desde 15-ago-2025» `[V]` https://thelogisticsworld.com/actualidad-logistica/mexico-lleva-al-33-5-el-impuesto-a-importaciones-por-paqueteria/ (la nota llega fechada de forma contradictoria; no confirmé vigencia hoy). Arancel por fracción: 5 % a 50 % desde 1-ene-2026 para países sin tratado `[V]` https://www.chilat.com/blog/2094242762900004866. |
| Rechazos/merma | Reposición de piezas | **`[H]`** | Pedir 10 a 20 % más en pasivos baratos; no cuantifico sin cotización. |
| Pruebas y retrabajo | Mano de obra interna | **PD** | Estimar con ap-calidad. |

Totales: **no entrego un total** porque faltan el PCB, el ensamble, las piezas Extended y el envío. Suma conocida solo de los rubros `[R]`/`[C]` por los dos cargos de arriba: ~5 USD (piezas básicas) + ~60 a 63 USD (cargos Extended), a confirmar.

Campos para la cotización (copiar tal cual): cantidad 5; material FR-4; capas 2; espesor PD; cobre exterior 2 oz; acabado PD; ensamble de una o dos caras PD; económico/estándar; BOM, CPL y Gerber (carpeta `fabricacion/jlcpcb/`); método de envío; Incoterm DDP o CPT (con DDP, JLCPCB paga el impuesto por adelantado según su política `[V]` https://jlcpcb.com/help/article/Customs,-Duties-and-Taxes).

## 3. Ensamble en México (EMS)

Todo lo siguiente sale de directorios y blogs; no verifiqué ninguna empresa directamente.

| Empresa | Ciudad | Qué dice la fuente | Umbral mínimo |
|---|---|---|---|
| Asteelflash | Tijuana | Planta de ~5,300 m², líneas SMT, AOI, ola, ICT, conformal; ISO 9001, ISO 13485, AS/EN 9100 `[V]` https://www.asteelflash.com/facility/asteelflash-mexico/ | **No encontrado.** Por perfil es EMS de volumen `[H]` |
| NEOTech | Tijuana | Ensamble PCBA `[V]` https://www.electronicspecifier.com/news/awards/neotech-wins-2023-mexico-technology-award/ | No encontrado |
| Plexus | Guadalajara | Planta en el Guadalajara Technology Park (nota de 2013) `[V]` https://electronics360.globalspec.com/article/2169/ems-provider-plexus-expands-its-footprint-in-mexico | No encontrado; volumen `[H]` |
| Micron Corp | Monterrey | Prototipos SMT/patas, 5 días hábiles estándar (blog) `[V]` https://www.bestpcbs.com/blog/tag/mexico-pcb-prototyping/ | No encontrado |
| NWC Circuits | Tijuana | SMT automatizado y prototipos rápidos (blog) `[V]` https://www.bestpcbs.com/blog/tag/pcb-prototyping-in-mexico/ | No encontrado |
| Fine Pitch de México, SMT UNION (Guadalajara), PCB Central (Irapuato), Intesing (Edo. de México) | varias | Aparecen en directorios `[V]` https://ensun.io/search/printed-circuit-board-pcb/mexico y https://dirind.com/dae/maquilas-electronica1.html | No encontrado |

**Umbral mínimo de volumen: no encontrado en ninguna fuente.** Para 5 placas lo probable es un taller de prototipos, no un EMS grande `[H]`. Cómo obtenerlo: enviar a 3 a 5 empresas el BOM, CPL y Gerber y preguntar: lote mínimo, cargo de arranque/NRE, costo por placa a 5/25/100 piezas, si compran las piezas (turnkey) o se consignan, plazo de piezas con LCSC o distribuidor, AOI/prueba funcional, tiempo de entrega y si sueldan las 24 piezas de patas.

## 4. Gabinete, fuente de 24 V y accesorios

**Gabinete para riel DIN** (todo IP20, sin certificación de producto para AP):
- CamdenBoss CNMB/6 (6 módulos, policarbonato UL94-V0, ~106 x 90 x 58 mm; admite 2 o 3 PCB) `[V]` https://www.rapidonline.com/camdenboss-cnmb-6-kit-din-rail-mounting-boxes-cnmb-6-30-1068 y https://uk.rs-online.com/web/p/din-rail-terminal-accessories/2819519. Precios de referencia en libras (CNMB/6V/2 £6.30 en 1 pieza; kit £18.56) en Rapid; son de distribuidor del Reino Unido.
- Hammond 1597DIN6GY (6 módulos, UL94-V0) `[V]` https://rapidonline.com/Hammond-1597DIN6GY-6-Module-DIN-Rail-Mounted-Enclosure-30-4285 (£9.38 en 1 pieza); familia 1597DIN https://www.elektormagazine.com/news/hammond-din-rail-enclosures.
- Por hacer: comprobar que la placa cabe (dimensiones del PCB frente a la ranura); distribuidor en México: `PD` (Mouser México y DigiKey tienen sitio mexicano `[CG]`).

**Fuente de 24 V certificada:**
- Mean Well HDR-60-24: 24 V, 2.5 A, 60 W, 85 a 264 VCA, IP20, 52.5 x 90 x 54.5 mm `[V]` https://www.distrelec.ch/en/din-rail-power-supply-90-24v-5a-60w-adjustable-mean-well-hdr-60-24/p/30134166 (los listados no concuerdan en la corriente; el cuerpo de los listados da 2.5 A: confirmar).
- Mean Well MDR-40-24 (40 W) en México: https://www.cyberpuerta.mx/Energia/Fuentes-Industriales/Fuentes-Industriales-CD/Mean-Well-Fuente-de-Poder-de-Montaje-en-Riel-24V-40W.html y https://www.syscom.mx/products/73656 (garantía de 3 años según Syscom).
- Catálogo de Mouser México con certificados UL/cUL/TÜV/CB/CE declarados por Mean Well `[V]` https://www.mouser.mx/meanwell-din-rail-power-supply.
- Dimensionar: 7 bobinas de 24 V a 16.7 mA c/u (~117 mA) más la placa; la carga total de campo la define el cliente `[C]`. Margen y modelo: ap-hardware. La fuente la compra el cliente o AP; **la fuente conecta a la red, no AP**: cualquier función de red queda fuera del piloto (regla 6).

**Cable USB-C y accesorios:** no encontré fuente específica en esta ronda. `PD`: cable USB-C a USB-A de datos (no solo carga) y bornes de repuesto; cotizar en Mouser México o DigiKey México y anotar URL y fecha.

## 5. Lista de verificación de importación (para un agente aduanal, no es asesoría)
1. Definir quién importa: persona física o moral con RFC. ¿Se necesita padrón de importadores? **Confirmar con el agente** `[CG]`.
2. Incoterm/modalidad: DDP (JLCPCB paga impuestos) o CPT (los paga AP); JLCPCB no reembolsa por problemas de despacho causados por el destinatario `[V]` https://jlcpcb.com/help/article/Customs,-Duties-and-Taxes.
3. Vía: mensajería (DHL) frente a importación formal con agente. La regla de paquetería de 33.5 % `[V]` tiene tope en dólares que **no confirmé**; confirmar en las RGCE vigentes y con DHL.
4. Fracción arancelaria **a confirmar** (no la asigno): una tarjeta ensamblada se clasifica por su función `[CG]`; el agente debe emitir criterio. Las partidas que suelen discutirse son 8537, 8543 y 8517 `[CG]`; ninguna está confirmada en las fuentes. Desde 2026 hay 1,463 fracciones con tasas de 5 a 50 % para países sin tratado `[V]` https://www.chilat.com/blog/2094242762900004866: verificar si la fracción de la tarjeta está afectada.
5. Valor en aduana: placa + piezas + envío + seguro. IVA 16 % sobre valor en aduana más arancel, y DTA 0.8 % `[V]` https://flavorcloud.com/knowledge-base/mexico-country-guide-import-and-landed-cost-reference. La acreditación del IVA depende del régimen de AP: consultar contador.
6. NOM y etiquetado: determinar si la fracción tiene regulación no arancelaria (NOM, cumplimiento de la importación); ap-legal-marca y ap-calidad.
7. Documentos: factura comercial con descripción técnica, país de origen, lista de empaque, guía aérea; pedir a JLCPCB la factura detallada.
8. Origen de las piezas (si vienen de varios países) y trato de T-MEC: `PD`.
9. Guardar la cotización, la factura y el pedimento como evidencia para ap-finanzas.

## 6. Plan B si JLCPCB no ofrece 2 oz con ensamble
- **Estado:** JLCPCB ofrece 2 oz exterior como opción de fabricación `[V]` https://jlcpcb.com/help/article/jlcpcb-copper-weight. **No encontré una fuente que confirme o niegue 2 oz con ensamble** (un usuario de foro reporta haber pedido 10 placas ensambladas con 2 oz, anecdótico `[V]` https://www.diyaudio.com/community/threads/active-rectifier.409514/latest). Primer paso: poner 2 oz y ensamble en el cotizador, o preguntar a soporte por escrito.
- **B1, fabricar y ensamblar por separado:** pedir solo el PCB de 2 oz a JLCPCB, y enviar a ensamblar a un taller mexicano (§3) con piezas compradas por AP (Mouser México/DigiKey México). Más trabajo logístico y mayor costo `[H]`.
- **B2, otro fabricante de PCB:** PCBWay tiene cobre pesado (≥3 oz, con tabla desde 4 oz) `[V]` https://www.PCBWay.ru/pcb_prototype/Thick_Copper_PCBs.html; **2 oz y ensamble llave en mano no confirmados**. Pedir cotización.
- **B3, rediseño a 1 oz:** ensanchar pistas de potencia, usar vertidos de cobre y refuerzo con estaño; decisión de ap-hardware con el cálculo de corriente por canal. Es el único plan B que mantiene el ensamble completo en JLCPCB si la corriente lo permite `[H]`.
- **B4, soldadura a mano** de los 24 componentes de patas ya está en el pedido económico `[R]`.
- No publicar fechas ni precios hasta tener respuesta de soporte.

## Hallazgos (por gravedad)
1. BOM y RESUMEN no coinciden (PS1/RV1/F2/J8/C3/D3); si la fuente de red entra al piloto, choca con la regla 6.
2. Fusible F1 sin existencias en la captura; alternativas listadas, sin decidir.
3. PCF8563T con señales de ciclo de vida y plazo largo.
4. Capacidad del relé en 24 VCD contradictoria entre fuentes.
5. 2 oz con ensamble en JLCPCB: sin confirmar.
6. Margen del AP63203 (32 V) frente al SMBJ33A (sujeción ~53 V): revisar topología.

## Qué falta saber
Estado de cada pieza en jlcpcb.com hoy; precio de 2 oz y de ensamble; cualquier umbral de EMS en México; fracción arancelaria; hoja oficial del DIP, del USB-C y del relé; alternativa respaldada del CA-IS3092W y de la ESP32.

## Siguiente paso recomendado
1) Dirección y ap-hardware: aclarar BOM vigente (§0.1). 2) Con la cuenta de JLCPCB: cotizar 5 placas con 2 oz y ensamble económico y estándar, exportar el desglose. 3) Pedir cotizaciones a 3 EMS mexicanos. 4) Consultar a un agente aduanal con el BOM y la ficha del producto.

## Fuentes (consultadas el 14-oct-2026, vía WebSearch; hojas completas no leídas)
JLCPCB cobre https://jlcpcb.com/help/article/jlcpcb-copper-weight · aduanas JLCPCB https://jlcpcb.com/help/article/Customs,-Duties-and-Taxes · Omron G2RL https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/1062/G2RL-1A-E-CF-DC9_Spec.pdf · Hongfa https://www.lcsc.com/product-detail/C2976789.html · Espressif https://www.espressif.com/products/longevity-commitment · CA-IS3092W https://www.compel.ru/infosheet/CHIPANLG/CA-IS3092W · TI TCA9554 https://www.ti.com/document-viewer/TCA9554/datasheet · TI LMR16006 https://www.ti.com/product/LMR16006 · Diodes AP63203 https://www.diodes.com/part/AP63203 · LTV-217 https://fat.lcsc.com/product-detail/C115450.html · PCF8563 https://fat.lcsc.com/product-detail/Real-time-Clocks-RTC_NXP-Semicon-PCF8563T-5-518_C7440.html · KF128 https://www.flux.ai/lcsc/kf128-5p08-2p-aa~0pbi.md · USB-C https://lcsc.com/product-detail/C165948.html · fusible https://www.lcsc.com/de/product/C355685.html · cristal https://www.lcsc.com/product-detail/C32346.html · gabinetes y fuentes: URLs en §4 · importación: URLs en §2 y §5 · repositorio: BOM CSV, RESUMEN_JLCPCB.txt, hardware/tools/jlcpcb.py, jlcpcb_catalogo.csv.
