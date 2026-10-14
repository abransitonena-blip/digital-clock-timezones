# 5. Etiquetado, información comercial y declaraciones prohibidas

> **ADVERTENCIA:** lista de verificación para revisión de un abogado mexicano y de un organismo de evaluación de la conformidad. **No es asesoría legal ni de certificación.** Textos oficiales no abiertos en esta ronda (bloqueo de red, 14-oct-2026).

## 1. Normas y regímenes que podrían aplicar

| Norma / régimen | Qué es | Estado verificado | Aplicabilidad a AP | Marca |
|---|---|---|---|---|
| **NOM-024-SCFI-2013** «Información comercial para empaques, instructivos y garantías de los productos electrónicos, eléctricos y electrodomésticos» | Información comercial mínima en producto/empaque, instructivo y garantía | **Vigente** en el catálogo de la Secretaría de Economía; publicada en el DOF 12-ago-2013; fecha de entrada en vigor: 11-oct-2013 (otra fuente da otra, por 60 días de publicación) | Probable para productos eléctricos/electrónicos que se comercialicen en México; si el 7R Tour industrial queda en su campo: **por confirmar con abogado** (leer el apartado «campo de aplicación») | `[V*]` https://platiica.economia.gob.mx/normalizacion/nom-024-scfi-2013/ · texto DOF https://dof.gob.mx/normasOficiales/5178/SEECO/SEECO.html · PDF https://platiica.economia.gob.mx/normalizacion/wp-content/uploads/sites/2/PDF_Normas_Publicas/024scfi2013.pdf |
| **NOM-001-SCFI-2018** «Aparatos electrónicos-Requisitos de seguridad y métodos de prueba» | Seguridad de aparatos electrónicos; certificación de producto | Vigente en el catálogo (DOF 17-sep-2019; entrada en vigor 14-may-2020 según una fuente, 14-ago-2020 según otra) | No se confirmó si cubre equipo industrial de riel DIN: **leer «Objetivo y campo de aplicación»**. Hoy el piloto **no está certificado** y debe decirlo | `[V*]` https://platiica.economia.gob.mx/normalizacion/nom-001-scfi-2018/ · https://dof.gob.mx/normasOficiales/7880/seeco11_C/seeco11_C.html |
| **Homologación de equipos de telecomunicaciones** (el ESP32-C3 trae Wi-Fi/BLE) | Obligatoria para equipo que use espectro o se conecte a redes (Ley en Materia de Telecomunicaciones y Radiodifusión, art. 271-272; publicada 16-jul-2025). La autoridad de homologación aparece como la **Comisión Reguladora de Telecomunicaciones (CRT)**, ya no el IFT | Art. 271: homologar según la Ley de Infraestructura de la Calidad; art. 272: la Comisión mantiene los procedimientos | Probable para el módulo inalámbrico: **un módulo ya homologado no garantiza el equipo final**; por confirmar con abogado/organismo. Mientras no esté: no declarar homologación ni «IFT» | `[V*]` https://mley.mx/LMTR/articulo/271/ · https://mley.mx/LMTR/articulo/272/ |
| **Ley de Infraestructura de la Calidad** (sustituyó a la Ley Federal sobre Metrología y Normalización) | Marco de normas, evaluación de la conformidad y acreditación | Citada por el art. 271 de la LMTR | Marco | `[V*]` (mención) |
| Etiquetado general de productos preenvasados (NOM-050-SCFI-2004 u otra vigente) | Información comercial general (denominación, país de origen, importador) | No verificada | Por confirmar con abogado si aplica a productos no preenvasados | `[CG]` por confirmar con abogado |
| **LFPC** (información veraz, idioma español, precios) | Obligaciones de información al consumidor | Ver `04_terminos_preventa.md` | Si hay consumidores | `[V*]` |
| Eficiencia energética (p. ej. NOM para lámparas LED) y seguridad de luminarias | Solo para línea de alumbrado (AP Electric Luz / Home) | No verificadas | **En pausa**; no aplica al piloto industrial 24 V | `[CG]` por confirmar |
| Instalaciones eléctricas (NOM-001-SEDE) | Norma de **instalación**, no de producto | No verificada | Responsabilidad de quien instala; mencionar en el instructivo | `[CG]` por confirmar |
| Importación: pedimento, regulaciones no arancelarias, verificación de etiquetado en aduana | Aduanas | No verificado | Agente aduanal | `[CG]` por confirmar con agente aduanal |

## 2. Qué debe contener la etiqueta (borrador de verificación, no definitivo)

Contenido típico de información comercial según la práctica de la NOM-024 `[CG]`; **confirmar cada punto contra el texto oficial**:
- [ ] Denominación/nombre del producto y modelo.
- [ ] Marca.
- [ ] País de origen (o «Hecho en [país]» con base en dónde se fabrica; no escribir «Hecho en México» salvo que proceda: por confirmar con abogado).
- [ ] Nombre o razón social y domicilio del **fabricante o importador**, y su RFC. (Hoy no existen: sin sociedad no hay quien aparezca.)
- [ ] Características eléctricas nominales **solo si fueron determinadas**: tensión de entrada, corriente, potencia, frecuencia si aplica. Para el 7R Tour 24DC: la entrada es 24 V CC `[R]`; **corrientes y capacidad de contactos «por determinar por ensayo»** `[R]`: no imprimirlas.
- [ ] Contenido neto/unidades.
- [ ] Instructivo en español con advertencias (montaje, conexión, uso previsto, **no es seguridad**).
- [ ] Póliza o información de garantía (ver `04_...`).
- [ ] Leyendas de precaución visibles y en español.
- [ ] Marcado NOM **solo** si hay certificado que lo autorice (hoy no).
- [ ] Marcas de terceros en la etiqueta solo si se tiene derecho a ello.

Etiquetas del repositorio: `identidad/etiqueta_7r_tour_24dc.*` y variantes. **No se revisaron aquí contra la norma**; el abogado y el responsable de calidad (`ap-calidad-normas`) deben revisarlas antes de imprimir. La etiqueta `7r_tour_ca` y las de Home corresponden a líneas en pausa (red de 127/220 V): **no usarlas**.

## 3. Declaraciones prohibidas mientras no haya certificación

Aplica a la página web, fichas, etiquetas, presentaciones, correos y voz de ventas. Base: reglas 2 y 5 de `CONTEXTO_COMPARTIDO.md`, y publicidad veraz de la LFPC `[V*]`/`[CG]`.

| Prohibido | Por qué | Redacción permitida |
|---|---|---|
| «Certificado», «aprobado», «cumple con [norma]», «conforme a NOM/UL/CE/IEC…» | No hay certificación ni ensayo | «Prototipo sin certificación» |
| Sellos o logotipos **CE, UL, cULus, NOM, IFT/CRT, FCC, RoHS, IP**, «homologado» | Son declaraciones legales; usarlos sin derecho es infracción y publicidad engañosa | Omitirlos |
| «Seguro», «a prueba de fallas», «protege al operador», «apto para seguridad», «SIL/PL», «IEC 61508 / ISO 13849» | Ningún producto de AP es función de seguridad (`CONTEXTO_COMPARTIDO.md` regla 5) | «No es un dispositivo de seguridad» |
| «Listo para vender», «en producción», «disponible», «en existencia», «entrega inmediata» | Nada se ha fabricado | «Prototipo de ingeniería en validación; sin fecha comprometida» |
| Cifras medidas: vida de relés, temperatura, EMC, corriente, tiempo de respuesta, precisión del reloj | Hoy no hay mediciones `[M]` | Solo «diseño, sin medir» con marca `[C]` o `[H]` |
| «Precio», «oferta», «descuento» o promesa de fecha | Sin precio ni fecha comprometidos | «Sin precio ni fecha comprometidos» |
| «OEE garantizado», «aumenta tu productividad X %», «ahorra $» | Sin evidencia | «Calcula OEE a partir de lo que mide» |
| «Compatible con Wi-Fi/Modbus/PackML certificado» o «Wi-Fi Certified» | Marcas y certificaciones de terceros; la conformidad PackML/Modbus no está certificada. Usar el logotipo Wi-Fi requiere certificación de la Wi-Fi Alliance `[CG]` | «Habla Modbus RTU» / «implementa estados PackML» (descriptivo, `[CG]` por confirmar uso nominativo con abogado) |
| «Reemplaza a un PLC» | Es una caja con lógica tipo PLC, no un PLC certificado | «Lógica tipo PLC» |
| «Hecho en México», «mexicano» | Se fabrica fuera (JLCPCB en la ruta actual); declaración de origen regulada | Describir diseño en México solo si es cierto: por confirmar con abogado |
| «Garantía de por vida», «sin riesgo», «100 % confiable» | Promesa no sustentable | Garantía definida por escrito |
| Reseñas, logos o nombres de clientes no autorizados | Uso indebido de marcas / engaño | Solo con autorización por escrito |
| «Sin nube» **si** la plataforma de la página guarda datos | Debe distinguirse equipo de página | «El equipo no necesita nube; esta página guarda tus solicitudes en [plataforma]» |

## 4. Revisión rápida de lo que ya se publica (solo lectura)
- `web/index.html` muestra «PROTOTIPO» en la tabla de producto (`estado proto`) y dice que una solicitud no es compra ni compromete precio o fecha `[R]`: coherente.
- `PREVENTA_AP_MONITOR.md` menciona una referencia de $5,000 a $7,000 MXN «se prueba»: **no publicarla como precio** (el propio documento dice que no hay precio publicado).
- La página lista productos de red de 127 V (AP Home) con el rótulo «127 V CA»: por la regla 6, están en pausa; no mostrar como disponibles.

## Hallazgos
1. No se ha revisado ninguna etiqueta contra NOM-024 (gravedad media). Sin razón social no puede completarse el dato de fabricante/importador (alta para puerta B/C).
2. El módulo Wi-Fi/BLE exige homologación ante la autoridad de telecomunicaciones vigente (CRT); mientras no exista, no puede decirse «homologado» y debe evaluarse si el piloto debe operar con Wi-Fi apagado (DIP 8) `[H]`.
3. Los textos «Wi-Fi», «Modbus», «PackML» son marcas o nombres de terceros: usarlos descriptivamente.

## Qué falta saber
Campo de aplicación exacto de NOM-024 y NOM-001-SCFI para equipo de riel DIN industrial, estatus actual de los lineamientos de homologación de la CRT, quién será el importador de registro.

## Siguiente paso recomendado
Un organismo de evaluación de la conformidad (o `ap-calidad-normas`) lee el campo de aplicación de ambas NOM y dice si el 7R Tour está dentro; el abogado revisa la etiqueta de `identidad/` con esa respuesta.

## Fuentes (consultadas 14-oct-2026)
- https://platiica.economia.gob.mx/normalizacion/nom-024-scfi-2013/
- https://dof.gob.mx/normasOficiales/5178/SEECO/SEECO.html
- https://platiica.economia.gob.mx/normalizacion/wp-content/uploads/sites/2/PDF_Normas_Publicas/024scfi2013.pdf
- https://www2.aladi.org/nsfaladi/normasTecnicas.nsf/ccc11adff39a6a9403257cf600683dc4/eac7338c1d6cc5ae032585b900597ef9/$FILE/Not%20A%2024-2.pdf
- https://platiica.economia.gob.mx/normalizacion/nom-001-scfi-2018/
- https://dof.gob.mx/normasOficiales/7880/seeco11_C/seeco11_C.html
- https://mley.mx/LMTR/articulo/271/ · https://mley.mx/LMTR/articulo/272/
- https://www.gob.mx/profeco (publicidad veraz, a leer en la LFPC)
