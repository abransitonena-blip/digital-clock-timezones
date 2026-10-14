# Plan de ensayos de laboratorio para la puerta C (AP Monitor 24)

Fecha: 2026-10-14 · Dueño: ap-calidad-normas · Estado: **plan de consulta, no asesoría ni declaración de cumplimiento** (CONTEXTO regla 10). Ningún ensayo se ha hecho. Sin cotizaciones: el costo se da como orden relativo (Bajo < Medio < Alto < Muy alto) [H].

Condición de la puerta C (ANALISIS_ECOSISTEMA §7): «pre-escaneo de EMC y pruebas de seguridad eléctrica hechos». Este plan separa lo que se puede hacer antes (pre-cumplimiento) de lo que se contrata a un laboratorio.

## 1. Qué aplica al equipo y por qué (resumen)

| Tema | Aplica | Fuente | Nota |
|---|---|---|---|
| Seguridad del equipo de control (serie IEC 61010) | **Sí, por ensayar [H]**; ver §2 | [IEC 61010-2-201 (SCC)](https://scc-ccn.ca/standardsdb/standards/2027704), [ed. 2 2017 (genorma)](https://genorma.com/en/standards/iec-61010-2-201-2017-ed2/amp) | El alcance de 61010-2-201 es «cualquier producto que realice la función de equipo de control» para mando de máquinas y procesos industriales. Nuestro producto encaja por su función |
| IEC 61131-2 (PLC: requisitos funcionales y EMC) | **Sí como referencia funcional y de EMC** | [IEC 61131-2:2017 (iTeh)](https://iteh.es/catalog/standards/iec/7ee48e64-4d9a-4008-8d44-a60d102ff444/iec-61131-2-2017), [PLCopen](https://plcopen.org/node/210) | La edición 4 (2017) quitó los requisitos de seguridad en favor de 61010-2-201; queda funcionalidad y EMC (cláusula 7 de EMC según PLCopen). La seguridad no se demuestra con 61131-2 |
| EMC industrial | **Sí, requisito de mercado** (no se encontró NOM obligatoria de EMC para este producto) | [IEC 61000-6-2:2016 (IEC)](https://webstore.iec.ch/publication/25630) | 6-2 es inmunidad en ambiente industrial; 6-4 es emisión industrial (no se obtuvo la ficha oficial; verificar) |
| Radio Wi-Fi 2.4 GHz | **Sí** (el hardware tiene radio aunque venga apagado) | [TÜV](https://tuv.com/market-access-services/en/certification-filter/mexico-radio-telecom-approval-(ifetel).html), [Applus](https://appluslaboratories-test.applus.solutions/dam/PDFServices/Laboratories/GLOBAL/mexico-radio-type-approval-(ift--nom)_es.pdf) | Ver L-12 |
| NOM de seguridad de producto eléctrico | **Por confirmar con organismo** | ver §3 | NOM-001-SCFI-2018, NOM-019-SCFI-1998, NOM-003-SCFI-2014 |

### Por qué un controlador alimentado a 24 V de una fuente externa sí necesita revisión de seguridad
1. La alimentación es SELV, pero las **salidas son contactos que conmutan lo que el usuario conecte** (meta 250 V CA, HOJA_DATOS). Con tensión peligrosa en los bornes de salida, el equipo tiene partes peligrosas accesibles aunque la alimentación sea de 24 V. El criterio de «parte peligrosa con tensión» se asocia a valores de ≈ 30 V eficaces, 42.4 V pico o 60 V CC [CG; ver nota de fuente: aparece en IEC 61010-031:2015 según [InCompliance](https://incompliancemag.com/on-limited-current-circuits/) y [EVS](https://evs.ee/en/evs-en-61010-031-2015); verificar en IEC 61010-1]. Por eso **limitar las salidas a ≤ 30 V reduce drásticamente la evaluación** pero no la elimina (calentamiento, inflamabilidad, ensayo de bornes y de fallas siguen).
2. La norma de control (61010-2-201) es una norma particular que se aplica **junto con** IEC 61010-1; no existe un umbral de «solo 24 V, no aplica» en lo que pude verificar. Lo confirma el organismo.
3. IEC 61131-2 por sí sola ya no cubre la seguridad (edición 2017). Quien pida «cumple 61131-2» pide funcionalidad y EMC.

No se verificó la redacción exacta del alcance de 61010-1 (la búsqueda no devolvió el texto del campo de aplicación con límite de tensión de alimentación). Pendiente: comprar o consultar el texto de la norma y confirmar con el organismo.

## 2. Plan de ensayos por prioridad y costo relativo

Orden recomendado: de lo barato y que más informa a lo caro y formal. Cada fila lleva «quién la hace en México»: la capacidad de cada organismo/laboratorio **no se verificó**; se da el tipo de entidad y los criterios para elegir (§4).

| Orden | ID | Ensayo | Norma de referencia | Costo relativo [H] | Puntos que cubre | Quién (México) | Cuándo |
|---|---|---|---|---|---|---|---|
| 1 | L-00 | Consultas escritas a organismos (alcance NOM-001/019/003 para 7R Tour 24DC, radio, ruta más barata) | — | Bajo | Elimina incertidumbre normativa | ap-calidad-normas con ANCE y NYCE (dos respuestas por escrito) | ya |
| 2 | L-P1 | Banco: arranque, polaridad, caída, RS-485 (B-S1..S9, B-E3) | PLAN_PRUEBAS_BANCO | Bajo | Antes de gastar en laboratorio, cerrar fallas de diseño | ap-hardware | primera tanda |
| 3 | L-P2 | **Pre-cumplimiento EMC** propio o de laboratorio: ESD con pistola, ráfagas, emisión con sonda de campo cercano | ver L-03..L-08 | Bajo a Medio | Reduce el riesgo de fallar en el laboratorio acreditado (RG-12) | ap-hardware; laboratorio universitario o comercial con servicio de pre-cumplimiento (la UNAM Juriquilla tiene una cámara EMC orientada a automotriz y pre-cumplimiento: [póster](https://www.ingenieria.unam.mx/uat/images/galeria/LabEMC/PosterLaboratorioEMC2021.pdf); no confirmé que acepte esto) | tras primera tanda |
| 4 | L-01 | **Seguridad** del equipo de control: aislamiento, rigidez dieléctrica, resistencia de aislamiento, distancias, calentamiento, falla única, inflamabilidad de carcasa, dedo de prueba, marcado | IEC 61010-2-201 (ed. 2024 según ARQUITECTURA §8) con IEC 61010-1 | **Alto** | RQ-05, 06, 17, 18, 21, 27, 49, 50 | Organismo de certificación o laboratorio acreditado; **no se afirma que ANCE o NYCE tengan alcance en 61010-2-201** (no verificado): preguntar | tras tener carcasa y límites por canal |
| 5 | L-03 | Emisiones EMC industriales (conducida y radiada) | IEC 61000-6-4 | Medio | RQ-22, 29 | Laboratorio EMC acreditado | tras L-P2 |
| 6 | L-04 | Inmunidad a descarga electrostática | IEC 61000-4-2 | Bajo a Medio | RQ-18, FM-18; USB-C y bornes | ídem | ídem |
| 7 | L-05 | Inmunidad a transitorios rápidos en ráfaga | IEC 61000-4-4 | Bajo a Medio | RQ-29, FM-21 | ídem | ídem |
| 8 | L-06 | Inmunidad a sobretensión (surge) | IEC 61000-4-5 | Medio | RQ-03, FM-07 | ídem | ídem |
| 9 | L-07 | Inmunidad a campos radiados | IEC 61000-4-3 | Medio | FM-18, 21 | ídem (cámara semianecoica) | ídem |
| 10 | L-08 | Inmunidad a perturbaciones conducidas por RF | IEC 61000-4-6 | Medio | FM-21 | ídem | ídem |
| 11 | L-09 | Caídas, interrupciones y variaciones de CC | IEC 61000-4-29 (NMX-J-610/4-29-ANCE-2009 es su equivalente según [PLATIICA](https://platiica.economia.gob.mx/normalizacion/NMX-J-610-4-29-ANCE-2009); estado por confirmar) | Bajo a Medio | RQ-04, FM-08 | ídem | ídem |
| 12 | L-02 | Funcional de PLC: entradas tipo 1/3 (curvas), temperatura si se declara | IEC 61131-2:2017 | Medio | RQ-07..11 | Laboratorio con alcance; el ensayo de entradas puede hacerse en casa y documentarse (B-D1) si el cliente no exige informe de tercero | opcional |
| 13 | L-12 | Radio (Wi-Fi 2.4 GHz): homologación o variante sin radio | NOM-208-SCFI-2016 / IFT-008-2015 (autoridad actual: CRT) | Medio a Alto | RQ-33, FM-25 | Laboratorio reconocido para la CRT; representante o importador en México | antes de vender con Wi-Fi |
| 14 | L-16 | Revisión de etiquetas, instructivo y garantía | NOM-024-SCFI-2013 (por confirmar si aplica) | Bajo | RQ-57 | unidad de verificación u organismo | antes de lote comercial |
| 15 | L-11 | Ambientales si se declaran: frío, calor, calor húmedo, vibración, choque | serie IEC 60068-2 [CG, números de parte por confirmar] | Medio a Alto | RQ-47, 48 | Laboratorio ambiental | **no declarar y no ensayar** hasta que un cliente lo exija |
| 16 | L-13/14/15 | Evaluación NOM de seguridad (certificado) | ver §3 | según organismo | RQ-57 | ANCE, NYCE u otro organismo acreditado | tras L-00 |

Notas:
- IEC 61000-6-2 describe inmunidad en ambiente industrial de 0 Hz a 400 GHz cuando no existe norma de producto. Una fuente secundaria ([IB-Lenhardt](https://ib-lenhardt.com/kb/glossary/en-61000-6-2)) lista como orden de magnitud ESD ±4 kV contacto y ±8 kV aire, campo radiado 10 V/m (80 MHz-1 GHz), ráfaga ±2 kV en alimentación y ±1 kV en E/S, sobretensión ±2 kV línea-tierra y ±1 kV línea-línea, y RF conducida 10 V (150 kHz-80 MHz). **No son valores verificados contra la norma**; el laboratorio fija niveles, puertos y criterios de aceptación por puerto con la norma en la mano (y qué puertos de CC aplican).
- Cada ensayo EMC tiene un **criterio de funcionamiento** (A, B o C). Para este producto el criterio debe incluir «no cambia el estado de ningún relé y no reinicia» durante la perturbación; esa es la parte que hay que definir con el laboratorio, porque un reinicio de 8 s (B-S5) afectaría salidas.
- Vibración y temperatura: no se declara ningún valor hoy. La HOJA_DATOS dice «PD». Hacer ensayo solo si se declara o lo pide el cliente.

## 3. Normas mexicanas: aplica sí / no / por confirmar

| Norma | Qué es | Aplica al 7R Tour 24DC | Fuente | Quién y cómo |
|---|---|---|---|---|
| NOM-001-SCFI-2018 | Aparatos electrónicos: requisitos de seguridad y métodos de prueba; cancela a NOM-001-SCFI-1993 | **Por confirmar con organismo.** Según una reseña ([Mondaq](https://www.mondaq.com/Article/851702)) cubre equipos y accesorios de CA monofásica hasta 277 V y de otras fuentes (baterías) hasta 500 V CC. Excluye equipos que deban cumplir otra NOM específica (p. ej. NOM-019-SCFI-1998), según [texto en boxlity](https://boxlity.com.mx/wp-content/uploads/2025/05/NOM-001-SCFI-2018-Aparatos-electronicos.pdf). No encontré si un controlador industrial queda dentro o fuera | [PLATIICA ficha](https://platiica.economia.gob.mx/normalizacion/nom-001-scfi-2018/), [ANCE](https://www.ance.org.mx/Ance/nom-001-scfi-2018/) | Organismos de certificación acreditados (ANCE, NYCE, otros del listado de la Secretaría de Economía; p. ej. [lista OCPR 2023-004](https://platiica.economia.gob.mx/wp-content/uploads/sites/5/Tarifas/ocpr-2023-004.pdf)) |
| NOM-019-SCFI-1998 | Seguridad de equipo de procesamiento de datos; vigente según ficha; hay un proyecto PROY-NOM-019-SE-2020 de reemplazo (no se encontró si se publicó) | **Probablemente no** (no es equipo de TI) pero **por confirmar**: un dictamen de un organismo remitió a NOM-019 un controlador de pantalla táctil de 48 V CC, según el resultado de búsqueda (documento no abierto) | [PLATIICA ficha](https://platiica.economia.gob.mx/normalizacion/nom-019-scfi-1998/) | Pregunta en L-00 |
| NOM-003-SCFI-2014 | Productos eléctricos: especificaciones de seguridad; vigente desde 27/5/2016 | **Por confirmar.** Núcleo: productos de uso doméstico y similar. Una fuente comercial ([HQTS](https://www.hqts.com/es/nom-003-scfi-2014-que-verificar-antes-de-exportar-productos-electricos-a-mexico/)) afirma alcance hasta 1000 V CA y 1500 V CC: **no verificado en el texto** del DOF. Sí aplicaría a Home Plug/Home Switch/7R Tour CA (ARQUITECTURA §8) | [PLATIICA PDF](https://platiica.economia.gob.mx/wp-content/uploads/sites/2/PDF_Normas_Publicas/003scfi2015.pdf), [Intertek: agrupación de familias](https://www.intertek.com.mx/contentassets/785f7ef4a151408a8bbb0636d52a19f0/wp_ew_nom_41-agrupacion---nom-003-scfi-2014.pdf) | Organismo acreditado, por SKU |
| NOM-208-SCFI-2016 / IFT-008-2015 | Equipos de radiocomunicación de corto alcance (902-928, 2400-2483.5, 5725-5850 MHz) | **Sí** si el producto sale con radio | [TÜV Rheinland](https://tuv.com/market-access-services/en/certification-filter/mexico-radio-telecom-approval-(ifetel).html) | Ver L-12 |
| NOM-024-SCFI-2013 | Información comercial en empaques, instructivos y garantías de productos electrónicos, eléctricos y electrodomésticos; vigente según ficha | **Por confirmar (probable)** | [PLATIICA ficha](https://platiica.economia.gob.mx/normalizacion/nom-024-scfi-2013/) | Unidades de verificación / organismos |
| NOM-001-SEDE-2012 | Instalaciones eléctricas (utilización) | **No es norma de producto.** Se cita en instrucciones de instalación | [PLATIICA](https://platiica.economia.gob.mx/normalizacion/NOM-001-SEDE-2012/) | Instalador |
| EMC | No encontré una NOM de EMC obligatoria para este producto | **No encontrada**; ensayar por requisito de cliente | — | Laboratorio EMC |

Hallazgo de fecha: las fuentes divergen en la entrada en vigor de NOM-001-SCFI-2018 (14 de agosto de 2020 según mexicanlaws.com; 14 de mayo de 2020 según totalnom.com). No afecta este plan; verificar en el DOF si se cita.

### L-12: radio con ESP32-C3-WROOM-02
- **Reportes encontrados** del módulo (consulta 14-oct-2026): ANATEL Brasil ([ESP32-C3-WROOM-02 ANATEL](https://www.espressif.com/sites/default/files/ESP32-C3-WROOM-02%20ANATEL%20Certification.pdf), con vigencia declarada hasta 15/08/2026, es decir, vencida; hay un certificado ANATEL más reciente para la variante 02U), CE (variante 02U), KCC Corea, SRRC China, IC Canadá (variante 02U) y una entrada de FCC en el listado de [certificados de Espressif](https://www.espressif.com/en/support/documents/certificates?keys=fcc). **No encontré ningún certificado mexicano (IFT/NOM-208).**
- **Lo que parece aprovechable:** reportes de laboratorio de otras jurisdicciones (FCC, CE) pueden servir al laboratorio como antecedente para reducir pruebas, pero **no lo afirmo**: debe confirmarlo el laboratorio y la CRT. El acuerdo de reconocimiento mutuo con EE. UU. modificado el 28-oct-2025 obliga a aceptar reportes de laboratorios de EE. UU. para ciertas normas, entre ellas IFT-016-2024; **IFT-008-2015 no aparece en esa lista** según [resumen CAICT](https://gma.caict.ac.cn/en/update/69/1075) (fuente secundaria).
- **Transferibilidad:** según [Foley](https://www.foley.com/?p=48169), desde el 25-feb-2021 los certificados de conformidad de telecom no son transferibles y los de componentes no se extienden al producto final. Applus señala que los equipos anfitrión con módulo aprobado llevan leyenda «Este producto contiene un módulo aprobado, modelo X, IFT No. Y»: eso exige que **el módulo tenga número en México**, que no encontré para el -02.
- **Autoridad:** el IFT dejó de operar el 17-oct-2025 y sus funciones pasaron a la Comisión Reguladora en Telecomunicaciones (CRT); los certificados IFT previos siguen válidos hasta su vencimiento ([Eleos](https://eleoscompliance.com/en/article/mexico-mexico%E2%80%99s-ift-ceases-operations)). IFT-017-2023 (WLAN 5-6 GHz) reemplazó en parte a IFT-008-2015 y está en vigor desde el 7-nov-2025 según [UL](https://latam.ul.com/en/resources/ift-017-2023-requirements-equipment-using-radio-spectrum). **No pude confirmar con fuente oficial de la CRT el estado vigente de IFT-008-2015 para 2.4 GHz.**
- **Opciones a comparar (decisión de ap-producto):** (a) homologar el producto con un laboratorio reconocido y un representante en México; (b) usar un módulo que **ya tenga** número mexicano (verificar en la base pública de la CRT); (c) vender una variante sin radio (se cambia el módulo; implica rev nueva). Para (b) y (c) hay costo de rediseño; el firmware ya trata Wi-Fi como opcional.

## 4. Criterios para elegir organismo o laboratorio
1. **Alcance de acreditación vigente por escrito** para la norma y la edición exactas (por ejemplo IEC 61010-2-201 ed. 2024, o IEC 61000-4-x), y la entidad que acredita (en México, la Entidad Mexicana de Acreditación; para laboratorios extranjeros, el organismo equivalente). No asumir: pedir el certificado de acreditación y el listado de pruebas.
2. **Aceptación de sus informes** por quien los va a exigir: la Secretaría de Economía para NOM, la CRT para radio, y el cliente armador para EMC. Preguntar antes de contratar.
3. **Experiencia con equipos de control en riel DIN** y con relés; pedir un ejemplo anonimizado de informe.
4. **Disponibilidad de pre-cumplimiento** (hora de ensayo previa a la formal) y política de repetición tras una falla.
5. **Entregables**: informe con fotografías, configuraciones, criterios de aceptación y lista de modificaciones; propiedad del informe.
6. **Representación local y razón social:** los trámites piden persona moral o física con actividad (RG-21).
7. **Claridad del precio**: cotización por escrito con lo que incluye y no (muestras, repeticiones, traslados). Comparar al menos tres.
8. **Confidencialidad** de archivos de diseño y plazo realista de entrega.
9. **Muestras**: cuántas, qué estado (con carcasa, con firmware final, sin radio activo, con modo de prueba) y cuánto tardan en regresarse.
10. Para ensayos EMC, laboratorios con **cámara semianecoica** y capacidad de ensayar **alimentación CC** (muchos ensayan CA; confirmarlo).

## 5. Muestras y condiciones que se necesitan antes de entrar a laboratorio
- Carcasa y etiqueta definitivas, bornes y tapa, firmware congelado y versión identificada.
- Límites por canal definidos (RQ-17, 18, 21) o decisión de ≤ 30 V.
- Modo de ensayo del firmware: relés alternando, comunicación activa, entradas simuladas, para que el laboratorio observe el criterio de funcionamiento.
- Lista de cables y largos máximos declarados (el laboratorio los usa para decidir puertos).
- 3 a 5 muestras por tipo de ensayo (cantidad PD; la fija el laboratorio).

## 6. Qué falta saber (resumen)
1. Texto vigente de alcance de NOM-001-SCFI-2018 y NOM-019 aplicado a controladores industriales (consultar a ANCE/NYCE).
2. Si IFT-008-2015 sigue vigente en 2026 tras el cambio a la CRT y qué trámite aplica para 2.4 GHz.
3. Si ANCE o NYCE tienen alcance en IEC 61010-2-201 y en IEC 61000-4-x.
4. Texto de IEC 61010-1/-2-201 (alcance y umbral de tensión): verificar con la norma comprada.

## Fuentes
- IEC 61010-2-201 (SCC): https://scc-ccn.ca/standardsdb/standards/2027704 · genorma: https://genorma.com/en/standards/iec-61010-2-201-2017-ed2/amp
- IEC 61131-2:2017: https://iteh.es/catalog/standards/iec/7ee48e64-4d9a-4008-8d44-a60d102ff444/iec-61131-2-2017 · https://plcopen.org/node/210
- IEC 61000-6-2:2016: https://webstore.iec.ch/publication/25630 · https://ib-lenhardt.com/kb/glossary/en-61000-6-2
- NOM-001-SCFI-2018: https://platiica.economia.gob.mx/normalizacion/nom-001-scfi-2018/ · https://www.mondaq.com/Article/851702 · https://boxlity.com.mx/wp-content/uploads/2025/05/NOM-001-SCFI-2018-Aparatos-electronicos.pdf
- NOM-019-SCFI-1998: https://platiica.economia.gob.mx/normalizacion/nom-019-scfi-1998/
- NOM-003-SCFI-2014: https://platiica.economia.gob.mx/wp-content/uploads/sites/2/PDF_Normas_Publicas/003scfi2015.pdf · https://www.hqts.com/es/nom-003-scfi-2014-que-verificar-antes-de-exportar-productos-electricos-a-mexico/
- NOM-024-SCFI-2013: https://platiica.economia.gob.mx/normalizacion/nom-024-scfi-2013/
- Radio: https://tuv.com/market-access-services/en/certification-filter/mexico-radio-telecom-approval-(ifetel).html · https://eleoscompliance.com/en/article/mexico-mexico%E2%80%99s-ift-ceases-operations · https://latam.ul.com/en/resources/ift-017-2023-requirements-equipment-using-radio-spectrum · https://www.foley.com/?p=48169 · https://appluslaboratories-test.applus.solutions/dam/PDFServices/Laboratories/GLOBAL/mexico-radio-type-approval-(ift--nom)_es.pdf · https://gma.caict.ac.cn/en/update/69/1075
- Certificados del módulo: https://www.espressif.com/en/support/documents/certificates?keys=fcc · https://www.espressif.com/sites/default/files/documentation/esp32-c3-wroom-02_datasheet_en.pdf
- Umbral de tensión peligrosa (secundaria): https://incompliancemag.com/on-limited-current-circuits/ · https://evs.ee/en/evs-en-61010-031-2015
- NMX-J-610/4-29: https://platiica.economia.gob.mx/normalizacion/NMX-J-610-4-29-ANCE-2009
- Laboratorio EMC universitario: https://www.ingenieria.unam.mx/uat/images/galeria/LabEMC/PosterLaboratorioEMC2021.pdf
Consultadas el 2026-10-14. El acceso directo a las páginas se bloqueó desde este entorno (solo resultados de búsqueda); por eso varias cifras quedan como «verificar en la norma».
