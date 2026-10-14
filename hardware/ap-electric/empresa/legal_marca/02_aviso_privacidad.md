# 2. Aviso de privacidad: marco vigente y borrador para la página

> **ADVERTENCIA:** lista de verificación y borrador para revisión de un abogado mexicano. **No es asesoría legal.** No usar el borrador sin revisión. No se pudo abrir el texto oficial de la ley (acceso bloqueado, 14-oct-2026); los artículos citados son de resúmenes de terceros.

## 1. ¿Qué ley y qué autoridad rigen hoy (14-oct-2026)?

| Hecho | Marca | Fuente |
|---|---|---|
| La ley de 2010 fue **abrogada**. Rige una **nueva Ley Federal de Protección de Datos Personales en Posesión de los Particulares (LFPDPPP)**, publicada en el DOF el **20-mar-2025**, en vigor el **21-mar-2025** | `[V*]` | EY https://www.ey.com/content/dam/ey-unified-site/ey-com/es-mx/technical/tax/documents/ey-law-flash-nueva-lfpdppp.pdf · Cámara de Diputados (por título del resultado) https://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf (no abierto) |
| El **INAI se extinguió** (reforma constitucional de dic-2024). La autoridad para particulares es la **Secretaría Anticorrupción y Buen Gobierno** | `[V*]` | EY (arriba); GT Law https://www.gtlaw.com/es/insights/2025/3/nueva-ley-general-proteccion-de-datos |
| Una versión consolidada indica **última reforma del 14-nov-2025**; puede haber cambios posteriores hasta hoy | `[V*]` por confirmar con abogado | SCJN https://www.internet2.scjn.gob.mx/red/delitos/Word/27.%20LFPDPPP.docx |
| Mantiene los principios de 2010 (licitud, consentimiento, información, calidad, finalidad, lealtad, proporcionalidad, responsabilidad) | `[V*]` | AMDA https://www.amda.mx/wp-content/uploads/2025/04/anexo%201%20de%20circular%2023%20de%202025.pdf |
| El aviso se presenta en modalidades **integral, simplificado y corto** y debe distinguir **finalidades necesarias de voluntarias** | `[V*]` | Legiscope https://www.legiscope.com/blog/aviso-privacidad-mexico-lfpdppp.html |
| Derechos ARCO (acceso, rectificación, cancelación, oposición) y revocación del consentimiento; ejercicio gratuito | `[V*]` | Legiscope https://www.legiscope.com/blog/lfpdppp-mexico-guia-cumplimiento.html |
| Plazos para responder y hacer efectivo el derecho (art. 31 según un resumen) | **por confirmar con abogado** | KYC Systems https://kyc-systems.com/blog/lfpdppp (no detalla). Con la ley de 2010 eran 20 días hábiles para responder y 15 para ejecutar `[CG]`, no asumir que siguen igual |
| Si el **reglamento de 2011** y los **lineamientos del aviso** siguen aplicándose, o qué los sustituye | **por confirmar con abogado** | Sin fuente |
| Nombre y contenido exacto del «derecho de portabilidad» u otros derechos nuevos | **por confirmar con abogado** | Sin fuente |
| Si los **datos de contacto de personas que actúan por una empresa** están exceptuados o no | **por confirmar con abogado** | Sin fuente. Tratar como datos personales mientras tanto |

## 2. Qué datos recoge hoy la página (`web/index.html`)

| Dato | Dónde | Observación |
|---|---|---|
| Tipo de solicitud, productos, segmento | Formulario `formSol` | No personal por sí solo |
| **Organización** (opcional) | `sOrg` | Puede identificar a una persona física |
| **Contacto (correo o teléfono)** | `sCon` | Dato personal |
| **Caso** (texto libre, 600 caracteres) | `sMsg` | Riesgo de que la persona escriba datos de terceros o sensibles |
| **Nombre** | Lista de interés: «El equipo ve tu nombre»; la página usa la cuenta de Claude del visitante (`window.claude.use("user")`) | La identidad la aporta la plataforma; el aviso debe decir qué ve AP y qué trata la plataforma |
| Nota (200 caracteres) | `iNota` | Texto libre |
| `localStorage` «apSolicitudes» | Navegador del visitante | Se queda en su equipo; mencionarlo |
| Google Fonts | `fonts.googleapis.com` | El navegador del visitante contacta a Google (IP); mencionarlo |

Los datos se guardan con la base de datos de la plataforma donde está publicada la página. Quién es el **encargado** (tercero que trata por cuenta del responsable), dónde están los servidores y si hay transferencia internacional: **por confirmar con abogado** y con los términos de la plataforma.

No se recogen: datos sensibles, de menores, financieros ni de salud (`[R]` del formulario revisado). Pedir a los visitantes que no los escriban en el texto libre.

## 3. Lista de verificación previa a publicar

- [ ] Definir el **responsable** (persona física hoy; razón social cuando exista) y su **domicilio**.
- [ ] Definir un **correo de contacto** del área o persona de datos para ARCO.
- [ ] Leer en el DOF la ley vigente (y cualquier reforma posterior al 14-nov-2025) y ajustar el borrador a sus artículos.
- [ ] Definir si el aviso es integral en una página propia y si el formulario muestra el simplificado/corto con enlace.
- [ ] Añadir casilla o texto de consentimiento para finalidades **voluntarias** (p. ej., avisos de novedades), separada de las necesarias.
- [ ] Definir quién recibe los datos (equipo, contador, mensajería, plataforma) y si hay transferencias.
- [ ] Definir un procedimiento interno de ARCO: quién recibe, cómo se acredita la identidad, plazos, bitácora.
- [ ] Definir medidas de seguridad mínimas (acceso solo de la dirección, sin copias en correo personal).
- [ ] Definir plazo de conservación y borrado (propuesta abajo, `[H]`).
- [ ] Cambio de plataforma: si la página sale de donde está hoy, revisar de nuevo.
- [ ] Revisar si se requieren cookies/localStorage con aviso (hoy solo `localStorage` propio del visitante).
- [ ] La página no debe pedir correo o teléfono hasta que el aviso esté visible.

## 4. Borrador del aviso (para la página)

> Texto con **[CORCHETES]** por llenar. Redacción en lenguaje simple. Pendiente de revisión legal.

---

### Aviso de privacidad de AP Electric

**Última actualización:** [FECHA]

**1. Quién es el responsable.** [NOMBRE COMPLETO O RAZÓN SOCIAL] («AP Electric»), con domicilio en [DOMICILIO], es responsable del tratamiento de tus datos personales. Contacto para temas de datos: [CORREO ARCO].

**2. Qué datos pedimos.**
- Nombre (cuando la plataforma nos lo muestra al registrar tu interés).
- Nombre de tu organización (opcional).
- Correo electrónico o teléfono, tal como tú lo escribas.
- Lo que cuentes en los cuadros de texto sobre tu máquina, instalación o caso.
- Datos técnicos de tu solicitud: productos elegidos, segmento, alimentación y tipo de sensores o cargas.

**No pedimos datos sensibles** (salud, origen, religión, ideología, finanzas, etc.), ni datos de menores. Te pedimos no escribirlos en los cuadros de texto.

**3. Para qué los usamos.**
*Finalidades necesarias:*
- Registrar y dar seguimiento a tu solicitud (folio, estado).
- Contactarte para responder tu solicitud, cotizar, o coordinar un piloto.
- Avisarte cuando haya prototipos disponibles, **si marcaste interés** en un producto.
- Llevar un registro interno de solicitudes para decidir qué producto desarrollar.

*Finalidades voluntarias (requieren tu consentimiento; puedes decir que no y tu solicitud sigue igual):*
- [ ] Enviarte novedades de AP Electric.
- [ ] Invitarte a entrevistas o encuestas de producto.

**4. Con quién compartimos tus datos.** No vendemos tus datos. Los ve el equipo de AP Electric [Y SUS ASESORES CONTABLE/LEGAL, SI APLICA]. La página funciona en una plataforma de terceros que almacena la información por nuestra cuenta: [NOMBRE DE LA PLATAFORMA Y PAÍS]. Además, el navegador pide tipografías a Google Fonts, por lo que Google puede recibir tu dirección IP. [AJUSTAR TRAS REVISIÓN: TRANSFERENCIAS Y ENCARGADOS].

**5. Tus derechos (ARCO) y revocación.** Puedes **acceder** a tus datos, **rectificarlos**, pedir su **cancelación** u **oponerte** a su uso, así como **revocar** tu consentimiento para las finalidades voluntarias. [AÑADIR LOS DERECHOS QUE EL ABOGADO CONFIRME EN LA LEY VIGENTE.] El ejercicio es gratuito. Escribe a [CORREO ARCO] con: tu nombre, un medio para responderte, una descripción clara de lo que pides, y una copia de una identificación (o los datos que nos permitan reconocerte, por ejemplo el folio de tu solicitud). Te responderemos en un plazo de [PLAZO CONFIRMADO POR EL ABOGADO] y, si procede, lo haremos efectivo en [PLAZO]. Si no estás de acuerdo con la respuesta, puedes acudir a la autoridad de protección de datos: [AUTORIDAD VIGENTE CONFIRMADA: SECRETARÍA ANTICORRUPCIÓN Y BUEN GOBIERNO].

**6. Cuánto tiempo los conservamos.** [PROPUESTA `[H]`: solicitudes sin respuesta o sin avance, 12 meses desde la última comunicación; clientes del piloto, mientras dure el piloto y 24 meses después para atender garantías y dudas, salvo que la ley fiscal o contractual exija más; después se borran o se disocian.] Si pides cancelación, los bloqueamos y borramos cuando termine el plazo que la ley exija.

**7. Seguridad.** Limitamos el acceso a quienes lo necesitan y usamos las medidas de la plataforma. [DETALLAR TRAS REVISIÓN.] Ningún sistema es infalible; si ocurre una vulneración que afecte tus derechos, te lo informaremos como la ley exige.

**8. Lo que se guarda en tu navegador.** La página guarda en tu navegador una lista de tus solicitudes (para que las veas de nuevo). Esa copia vive en tu equipo; puedes borrarla desde la configuración del navegador.

**9. Cambios a este aviso.** Publicaremos cualquier cambio en esta página con su fecha.

**Consentimiento.** Al enviar tu solicitud o registrar tu interés, declaras haber leído este aviso. [MARCAR COMO CASILLA SEPARADA SI EL ABOGADO LO PIDE.]

---

## 5. Mini-formato de solicitud ARCO (para tener listo)
Campos: nombre del titular · medio de respuesta · derecho que ejerce (A/R/C/O/revocación) · descripción · documentos de identidad o folio · fecha · responsable que recibe · plazo calculado · fecha de respuesta · resultado. `[H]` Formato libre; el abogado confirma si la ley exige requisitos adicionales.

## Hallazgos
1. La página ya recoge contacto y no se encontró aviso en el código revisado (gravedad alta).
2. Hay un tercero (plataforma) que almacena los datos y otro (Google Fonts) que recibe la IP: deben mencionarse.
3. Autoridad y plazos cambiaron respecto de lo que muchos formatos de internet aún dicen (INAI, 20 días): usar solo lo confirmado.

## Qué falta saber
Texto oficial vigente (con reformas posteriores a nov-2025), responsable y domicilio, términos de la plataforma sobre almacenamiento y país, y si se usarán los datos para mercadotecnia.

## Siguiente paso recomendado
Con el abogado: confirmar ley vigente, plazos y modalidades; llenar los corchetes; publicar el aviso en la página con enlace desde ambos formularios.

## Fuentes (consultadas 14-oct-2026)
- https://www.ey.com/content/dam/ey-unified-site/ey-com/es-mx/technical/tax/documents/ey-law-flash-nueva-lfpdppp.pdf
- https://www.gtlaw.com/es/insights/2025/3/nueva-ley-general-proteccion-de-datos
- https://www.amda.mx/wp-content/uploads/2025/04/anexo%201%20de%20circular%2023%20de%202025.pdf
- https://www.legiscope.com/blog/aviso-privacidad-mexico-lfpdppp.html
- https://www.legiscope.com/blog/lfpdppp-mexico-guia-cumplimiento.html
- https://idconline.mx/corporativo/2025/04/01/nueva-ley-de-proteccion-de-datos-cambios-en-derechos-y-obligaciones
- https://www.internet2.scjn.gob.mx/red/delitos/Word/27.%20LFPDPPP.docx
- Oficial a leer: https://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf · https://www.dof.gob.mx
