# AP Electric: arquitectura de la familia residencial e industrial

> **Estado de todo este documento: CONCEPTO.** Nada de lo descrito se ha fabricado, medido ni certificado.
>
> Cada cifra lleva su origen:
>
> | Marca | Origen |
> |---|---|
> | **[R]** | Requisito propuesto |
> | **[C]** | Cálculo |
> | **[E]** | Especificación del componente (hoja del fabricante o del distribuidor) |
> | **[M]** | Medido |
> | **[A]** | Límite aprobado del producto |
>
> Hoy no existe ningún valor [M] ni [A]. «Por determinar» significa que falta evidencia.

## 1. Corrección del alcance

- Las cargas residenciales son **focos y luminarias convencionales de 127 V CA**. Llevan su propio driver o balastro y se conectan como indica su fabricante, normalmente en paralelo a la red.
- Las placas anteriores de corriente constante para cadenas de LED **no alimentan estos focos** y no se reutilizan aquí. Son AP FOCO, AP FOCO 127, PWM4 y la línea de letreros.
  - Quedan como familia separada, **AP LED**.
  - No aparecen en las fichas ni en las matrices de carga de esta familia.

## 2. Menos módulos, más funciones: la familia mínima

Después de comparar (sección 4), la familia queda en **2 placas** para **4 SKU iniciales**:

| Placa | SKU | Instalación | Qué hace |
|---|---|---|---|
| **AP Home** (red, 1 canal) | **Home Plug** | Se enchufa (clavija y receptáculo encerrados). El usuario no toca bornes de red | Enciende y apaga una lámpara de 127 V |
| | **Home Switch** | Fija, con fase, neutro y entrada para apagador. La instala una persona competente con el circuito desenergizado | Lo mismo, conservando el apagador de pared (simple o de escalera) |
| **AP 7R Tour** (lógica de 24 V CC, 7 relés) | **7R Tour 24DC** | Tablero, riel DIN. Fuente de 24 V CC certificada externa | 7 salidas, 8 entradas de 24 V, Modbus RTU aislado, programa tipo PLC |
| | **7R Tour CA** | Igual, con la fuente encapsulada certificada de 85-264 V CA en la placa | Lo mismo, sin fuente externa |

**Por qué así:**

- **Misma placa, distinto SKU:**
  - Home Plug y Home Switch solo cambian la caja, los bornes y si la entrada de apagador está habilitada.
  - 7R Tour 24DC y CA solo cambian si se monta la fuente de red.
  - Cada cambio de aislamiento, conector, protección o certificación es un SKU distinto, como pide el alcance. No hace falta otra placa.
- **Un solo cerebro y un solo programa** en las dos placas (ESP32-C3-WROOM-02 + firmware **AP Control**):
  - mismas funciones de horario, escenas, vínculos y lógica tipo PLC;
  - misma app;
  - mismas reglas de seguridad de arranque.
- **Se conectan entre sí sin nube:**
  - **Wi-Fi local:** cualquier entrada de un equipo puede mandar sobre la salida de otro, con «vínculos» por UDP en la red de la casa.
  - **AP LINK (Modbus RTU sobre RS-485 aislado)** en el 7R Tour, para PLC, pantallas o un sistema de edificio.
  - Un Home Switch puede ser una entrada remota del 7R Tour y viceversa.
- **Lo que no se integra:**
  - **Regulación de brillo:** solo en un SKU futuro específico (sección 6).
  - **Funciones de seguridad:** van en equipos de seguridad evaluados, no en estos productos.

## 3. Nombre del modelo 7R Tour

**Supuesto pendiente de confirmar:** «7R» se interpreta como **siete canales de relé**.

- El diseño tiene 7 canales porque el excitador ULN2003A tiene exactamente 7.
- El nombre no promete amperaje.
- Si «7R» significa otra cosa, se cambia el nombre y no las salidas.
- Antes de comercializar hay que revisar si las marcas **AP Electric** y **7R Tour** están disponibles ante el IMPI (pendiente).

## 4. Comparación de arquitectura (industrial)

| Opción | A favor | En contra | Decisión |
|---|---|---|---|
| **Placa propia ESP32-C3 + firmware AP Control** | Costo bajo; relés elegidos para alumbrado; Wi-Fi y RS-485 en la misma placa; un solo programa para toda la familia; lógica tipo PLC propia (AP LÓGICA), sin licencias de terceros | Toda la evaluación de seguridad y EMC corre por nuestra cuenta | **Base del 7R Tour y de AP Home** |
| **Arduino Opta** (AFX00001/2) | PLC compacto con IEC 61131-3 (PLC IDE).<br>4 relés NO de 10 A [E], 12-24 V CC [E], 8 entradas 0-24 V / 0-10 V [E], RS-485 Modbus RTU en AFX00001/2 [E] | Solo 4 relés: 7 canales piden 2 equipos o expansión.<br>«Short-circuit protection: No, external fuse required» [E].<br>Rango de temperatura contradictorio entre fuentes | Alternativa para clientes que piden un PLC de catálogo. No se mezcla con la placa propia «por apariencia» |
| **PLC comercial** (gama compacta) | Herramientas, soporte y certificaciones del fabricante; mejor cuando el cliente ya tiene ese ecosistema o el entorno lo exige | Costo; poco sentido para encender alumbrado | Recomendado cuando la integración o el mantenimiento lo justifiquen. El 7R Tour se conecta a él por Modbus |
| **OpenPLC** | Editor IEC 61131-3 libre | Runtime v3 **GPL-3.0** y ya en fin de vida (lo reemplaza el Runtime v4).<br>En microcontroladores solo es esclavo Modbus | No se incorpora al firmware (evita obligaciones GPL en el producto). Un OpenPLC v4 en una PC o Raspberry Pi puede manejar al 7R Tour como esclavo Modbus |

Ningún Arduino, Opta ni PLC autoriza por sí mismo a conmutar cualquier carga ni es un sistema de seguridad certificado. Lo mismo vale para el 7R Tour.

## 5. Matriz de modelos y cargas (preliminar)

**Sí**:
- con relé y dentro de límites que todavía están **por determinar por ensayo**;
- la capacidad con lámparas LED, CFL o balastros **no se declara** hasta medir la irrupción real (sección 7).

**No**: excluida. **Externo**: solo como contacto de mando a la bobina de un contactor elegido por categoría de utilización.

| Carga | Home Plug | Home Switch | 7R Tour (por canal) |
|---|---|---|---|
| Foco incandescente / halógeno 127 V | Sí | Sí | Sí |
| Foco LED 127 V (driver integrado), no regulable | Sí | Sí | Sí |
| Luminaria LED con driver, fluorescente con balastro electrónico | Por determinar | Por determinar | Por determinar; si la irrupción excede, contactor externo |
| Lámpara regulable con atenuador | **No** (solo encendido/apagado) | **No** | **No** |
| Motores, bombas, compresores | **No** | **No** | **Externo** (contactor AC-3) |
| Solenoides, válvulas CA | **No** | **No** | Externo, o directo por debajo de un límite por determinar con supresor |
| Resistencias de calefacción | **No** | **No** | Externo (AC-1) por encima de un límite por determinar |
| Cargas en CC (> 30 V) | **No** | **No** | **No** (el contacto de CA no queda autorizado para CC) |
| 208/400/480 V, trifásico | **No** | **No** | **No** con este SKU. Requiere otro SKU y otro aislamiento, o contactor externo con su propia bobina |
| Cargas de seguridad (paro de emergencia, enclavamientos) | **No** | **No** | **No** |

## 6. Decisiones de diseño comunes

**Conmutación**
- Encendido y apagado con **relé electromecánico monoestable**: sin energía en la bobina, el contacto abre.
- No hay atenuación por PWM en la red ni relés a frecuencia de atenuación.
- **Relé del 7R Tour: Omron G2RL-1A-E DC24** (LCSC C231362):
  - bobina de 24 V, 16.7 mA, 1.44 kΩ, 400 mW [E];
  - 16 A 250 V CA resistivo [E];
  - 8 mm de distancia en aire y por superficie entre bobina y contacto [E];
  - huella oficial de KiCad.
- **Lo que no tiene el relé:**
  - No tiene valor publicado para lámparas LED ni de irrupción.
  - Por eso su capacidad con lámparas queda **por determinar por ensayo**.
  - Para cargas de irrupción alta está la alternativa **Omron G5RL-1A-E-HR** («inrush peak currents up to 100 A» [E]).
  - El G5RL no se usa todavía porque no tengo su dibujo de montaje verificado.
- **Relés biestables:** se descartaron los Omron G5RL-U/-K (resistentes a irrupción). Mantienen el contacto sin energía y contradicen el arranque seguro.

**Arranque y pérdida de energía**
- Al energizar, todas las salidas quedan **apagadas**.
- Cada canal se configura así:
  - **Apagado** (predeterminado y obligatorio para cargas de proceso);
  - **Último estado**;
  - **Encendido**: solo alumbrado, con confirmación explícita en la configuración.
- Tras un corte, una máquina **no se reenciende sola**.

**Mando manual**
- **Por software:** botones del frente. Dependen del microcontrolador.
- **Por hardware (7R Tour):**
  - un interruptor DIP por canal cierra la bobina directo a 0 V y enciende el relé aunque el microcontrolador esté detenido o sin programa;
  - una posición extra bloquea todas las bobinas.
  - Esto **no** es un bypass del contacto: si el relé está soldado o la bobina abierta, no ayuda.
  - Necesita los 24 V de la placa.
- **Bypass físico del contacto:** no se ofrece.

**Indicación de estado**
- Los LED de salida están en paralelo con cada bobina: muestran si la bobina recibe tensión, venga la orden del programa o del DIP.
- Los LED de entrada van en serie con el optoacoplador.
- **No** se promete detectar un contacto soldado. Haría falta medir la carga y tener un segundo medio de desconexión, y no se tienen.

**Comunicaciones**
- **RS-485 aislado** (Chipanalog CA-IS3092W, 5 kVrms, fuente aislada integrada [E]).
- Si el maestro Modbus deja de escribir, cada canal pasa a un estado configurable; el predeterminado es **apagado**.

**Fuentes de red**
- Solo módulos encapsulados certificados por su fabricante: Mean Well IRM-20-24 en el 7R Tour CA e IRM-03-5 en AP Home.
- No se usan fuentes capacitivas.

## 7. Irrupción de lámparas LED: por qué no hay cifra todavía

- Los drivers de LED tienen una irrupción que puede pasar de 10 veces la corriente nominal; hay casos documentados mucho mayores.
- La irrupción de varios drivers en un mismo circuito se suma.
- La norma NEMA 410 define cómo medirla.
- Plan:
  - medir con lámparas reales de 127 V del mercado mexicano (sección 9 del plan de verificación);
  - declarar el número de lámparas o los watts LED admisibles por canal;
  - si no alcanza, limitar irrupción o pasar a contactor.

## 8. Normas y evaluación (a confirmar con un organismo de certificación)

| Tema | Referencia | Aplica a |
|---|---|---|
| Seguridad de producto eléctrico (México) | NOM-003-SCFI-2014 (vigente desde 27/5/2016); evaluación vía NMX-J-508-ANCE según la SE | Home Plug, Home Switch, 7R Tour CA (a confirmar el alcance exacto) |
| Interruptores electrónicos para instalaciones fijas | IEC 60669-2-1 (2021): CA ≤ 250 V, ≤ 16 A. **No** proporcionan «full off-state» sin interruptor mecánico | Home Switch (y probablemente Home Plug) |
| Controles automáticos incorporados a aparatos | IEC 60730-1 (excluida de 60669-2-1) | Solo si se vende integrado a un aparato |
| Equipo de control y PLC | IEC 61010-2-201 (ed. 2024; incluye la seguridad de PLC y la referencia cruzada con IEC 61131-2). IEC 61131-2 define entradas tipo 1/2/3 | 7R Tour |
| Instalación | NOM-001-SEDE-2012 (vigente; sigue el anteproyecto de reemplazo) | Instrucciones de instalación |
| Radio (Wi-Fi 2.4 GHz) | NOM-208-SCFI-2016 / IFT-008-2015. La autoridad pasó a la CRT; IFT-017-2023 rige 5-6 GHz. No encontré homologación mexicana pública del ESP32-C3-WROOM-02 | Todos (Wi-Fi) |
| Coordinación de aislamiento | IEC 60664-1 (distancias según tensión, sobretensión, contaminación, material y altitud) | Todos |

- **Sellos:** no se imprime ninguno (NOM, CE, UL ni otro) hasta tener el certificado.
- **IP e IK:** solo por ensayo.

## 9. Pendientes concretos

1. Confirmar el significado de «7R» y la disponibilidad de las marcas.
2. **Hoja original de cada pieza crítica.** Desde este entorno no pude descargar los PDF, porque los dominios de los fabricantes están bloqueados. Las cifras [E] salen de páginas de fabricante y distribuidores vistas por búsqueda. Las piezas son:
   - G2RL-1A-E;
   - CA-IS3092W (orden de patas);
   - IRM-03-5 e IRM-20-24;
   - LTV-814S;
   - DIP.
3. Medir la irrupción de lámparas LED de 127 V y fijar los límites por canal.
4. Revisar la homologación del módulo Wi-Fi o planear la del producto.
5. Elegir el organismo de certificación y las normas exactas por SKU (NOM-003 con NMX, IEC 60669-2-1, IEC 61010-2-201).
6. Componentes mecánicos de la clavija y el receptáculo del Home Plug (NEMA 5-15, con tierra pasante) y su proveedor certificado.

## Fuentes consultadas

**Relés**
- [Omron G5RL-U/-K](https://components.omron.com/us-en/datasheet_pdf/K265-E1.pdf) · [Omron G5RL (HR, TV8, LN)](https://components.omron.com/us-en/datasheet_pdf/K132-E1.pdf) · [Omron G5RL-U/K-EL-HA (irrupción)](https://components.omron.com/us-en/fresh-on-the-board/202201-products)
- [Omron G2RL](https://media.digikey.com/pdf/Data%20Sheets/Omron%20PDFs/G2RL.pdf) · [G2RL-1A-E DC24 en LCSC (C231362)](https://www.lcsc.com/product-detail/Relays_Omron-Electronics-G2RL-1A-E-DC24_C231362.html) · [G2RL-1A-E DC24 en DigiKey](https://www.digikey.com/en/products/detail/omron-electronics-inc-emc-div/G2RL-1A-E-DC24/368854)
- [G5RL-1A-E-TV8 DC24 en LCSC (C2896748)](https://www.lcsc.com/product-detail/Power-Relays_Omron-Electronics_C2896748.html) · [Hongfa HF152F-T/012-1HST (C2976802)](https://www.lcsc.com/product-detail/C2976802.html)

**Interfaz y fuentes**
- [Chipanalog CA-IS3092W (hoja)](https://e.chipanalog.com/Public/Uploads/uploadfile/files/20240611/CAIS30923098datasheetVersion1.11en.pdf) · [CA-IS3092W en LCSC (C2890051)](https://www.lcsc.com/product-detail/Isolated-RS-485-422-Transceivers-with-power_Chipanalog-CA-IS3092W_C2890051.html)
- [Mean Well IRM-03-5 en LCSC (C6969425)](https://www.lcsc.com/product-detail/AC-DC-Power-Modules_MW-MEAN-WELL-Enterprises-IRM-03-5_C6969425.html) · [LTV-814S-TA1-A (C108051)](https://www.lcsc.com/product-detail/Optocouplers_Lite-On-LTV-814S-TA1-A_C108051.html) · [DIP DSWB08LHGET (C99413)](https://www.lcsc.com/product-detail/DIP-Switches_Dongguan-Guangzhu-Industrial-Dongguan-Guangzhu-Industrial-DIP-switch-Dip-Switch-DSWB08LHGET_C99413.html)

**Plataformas**
- [Arduino Opta RS485 (RS)](https://se.rs-online.com/web/p/plcs-programmable-logic-controllers/2600884) · [Arduino docs (Opta)](https://github.com/arduino/docs-content/pull/1669/files)
- [OpenPLC v3 (GPL-3.0, fin de vida)](https://github.com/thiagoralves/OpenPLC_v3) · [OpenPLC en ESP32 (foro)](https://openplc.discussion.community/post/how-to-add-ethernet-module-to-esp32-12695213)

**Normas y regulación**
- [IEC 60669-2-1](https://standards.globalspec.com/std/14362806/iec-60669-2-1) · [UNE-EN IEC 60669-2-1:2023](https://www.en-standard.eu/une-en-iec-60669-2-1-2023-switches-for-household-and-similar-fixed-electrical-installations-part-2-1-particular-requirements-electronic-control-devices/)
- [IEC 61010-2-201](https://scc-ccn.ca/standardsdb/standards/2021291) · [UL sobre IEC 61010-2-201](https://code-authorities.ul.com/wp-content/uploads/sites/40/2015/09/IEC-61010-2-201_2005_V1.pdf)
- [Entradas IEC 61131-2 (Analog Devices)](https://www.analog.com/en/design-notes/industrial-digital-inputs-with-the-max22191.html) · [Beckhoff DK9222](https://download.beckhoff.com/download/document/application_notes/DK9222-0909-0008.pdf)
- [NOM-003-SCFI-2014 (SE)](https://platiica.economia.gob.mx/normalizacion/?p=46776) · [Agrupación de familias NOM-003 (Intertek)](https://www.intertek.com.mx/contentassets/785f7ef4a151408a8bbb0636d52a19f0/wp_ew_nom_41-agrupacion---nom-003-scfi-2014.pdf) · [NOM-001-SEDE-2012 (SE)](https://platiica.economia.gob.mx/normalizacion/NOM-001-SEDE-2012/)
- [IFT-017-2023 (UL)](https://latam.ul.com/en/resources/ift-017-2023-requirements-equipment-using-radio-spectrum) · [Homologación México (TÜV)](https://tuv.com/market-access-services/en/certification-filter/mexico-radio-telecom-approval-(ifetel).html)

**Irrupción de LED**
- [NEMA 410 y eldoLED (Acuity)](https://insights.acuitybrands.com/eldoled/nema-410-inrush-requirements-for-eldoled-drivers) · [IOTA: irrupción](https://www.iotaengineering.com/-/media/abl/iota/files/technical-library/controls/iota-tech-brief_emergency-lighting-and-inrush.pdf)

**Diseño de referencia de entrada de apagador**
- [Shelly 1 Gen3](https://www.shelly.com/blogs/documentation/shelly-1-gen3) · [Shelly 1 Gen3, interfaz web (modos de entrada)](https://www.shelly.com/blogs/documentation/shelly-1-gen3-web-interface-guide)
