# Modelo financiero de AP Monitor 24

Fecha: 14-oct-2026. Agente: ap-finanzas. Producto: AP Monitor 24 = 7R Tour 24DC rev B + firmware PackML/OEE + consola.

**Estado:** nada se ha cotizado, fabricado ni medido. Este documento es un modelo con celdas de entrada, no una predicción. Todo costo de piezas Extended, PCB, ensamble, fuente, caja, flete y aduana es **PD** hasta tener cotización. Los números del script en `--ejemplo` son **ilustrativos** (redondos, inventados a propósito para probar el código) y no deben citarse.

Marcas: `[V]` con fuente y fecha · `[R]` repositorio · `[C]` cálculo · `[H]` hipótesis · `PD` por determinar · `[CG]` conocimiento general sin verificar.

Archivos de esta carpeta:
- `modelo_ap_monitor.py`: script (solo biblioteca estándar). `--ejemplo`, `--json archivo`, `--plantilla`, o sin banderas (solo la tabla de costo directo máximo).
- `SALIDA_EJEMPLO_ILUSTRATIVO.txt`: salida de `python3 -I modelo_ap_monitor.py --ejemplo`, ejecutada el 14-oct-2026 sin errores.

## 1. Cómo usar el modelo
1. `python3 modelo_ap_monitor.py --plantilla > entradas.json`
2. Llenar cada `null` con la cotización indicada abajo (USD donde dice USD, MXN el resto, sin IVA).
3. `python3 modelo_ap_monitor.py --json entradas.json`

Si falta una entrada, el script dice cuál y no calcula ese lote; no rellena huecos.

## 2. Entradas: qué es, de dónde sale el rango y qué cotización la reemplaza

| Entrada | Qué es | Origen del rango | Se reemplaza con |
|---|---|---|---|
| `tipo_cambio_mxn_usd` | MXN por USD para todo lo importado | `[H]` 17-20. Referencias: estudio de mercado usa ~18 `[V]` (12-oct-2026); notas de prensa citan ~18.1-18.4 para el 5-9 oct-2026 y Banxico muestra ~17.4 en julio, **sin que haya podido confirmar el FIX exacto de hoy** (ver §8) | FIX de Banxico el día del pago, o el tipo de cambio de la tarjeta/banco con que se pague |
| `n_piezas_extended_unicas` | Piezas Extended distintas del BOM (cada una paga cargo de carga en JLCPCB) | `[R]` contado: BOM 24DC tiene 18 Extended únicas, 4 Preferred, 25 Basic (56 líneas, 184 piezas) | Se actualiza si cambia el BOM |
| `pcb_usd` (por lote) | Fabricación del PCB desnudo | `PD`. Sin dato en el repositorio | Cotización en línea de JLCPCB con los Gerbers de `7r-tour/fabricacion/` para 5, 50 y 200 piezas |
| `piezas_usd` (por lote) | Total de piezas del lote | `PD`. El catálogo `hardware/tools/jlcpcb_catalogo.csv` `[R]` trae precio de 39 de las 56 líneas, pero **ninguna de las relevantes** (relés, ESP32-C3, CA-IS3092W, TCA9554, reguladores, bornes, USB-C, fusible) y los precios de catálogo son de una fecha anterior; no se usan | Cotización de ensamble de JLCPCB con el BOM/CPL de `24DC`, que lista cada pieza y su precio por volumen |
| `cargo_extended_usd` (por lote) | Cargo por pieza Extended × `n_piezas_extended_unicas` | `PD`. No se asume la tarifa por pieza | Línea del mismo presupuesto de JLCPCB (hoy se muestra al cotizar) |
| `ensamble_usd` (por lote) | Ensamble SMT, plantilla (stencil), ingeniería | `PD` | Mismo presupuesto de JLCPCB |
| `envio_usd` (por lote) | Flete internacional | `PD` | Opciones de envío del pedido de JLCPCB y/o cotización de un forwarder |
| `mano_obra_final_mxn` (por lote) | Prueba, ensamble en caja, etiquetado, encajado | `PD`. Si se hace en casa: horas × costo hora | Tiempo cronometrado en los primeros 5 kits; o cotización de un taller local de ensamble |
| `fuente_24v_mxn` | Fuente de 24 V certificada de terceros, para riel DIN | `PD` | Cotización a 2-3 distribuidores (nacionales) de fuentes conmutadas de 24 V; elegir amperaje según la corriente máxima del diseño (`DISENO_FINAL.md`, `PLAN_VERIFICACION.md`) |
| `caja_din_mxn` | Carcasa/caja DIN con corte de ventana y serigrafía | `PD` | Cotización de 2-3 fabricantes de caja DIN (estándar de catálogo vs a medida), con 5, 50 y 200 piezas |
| `etiqueta_mxn` | Etiqueta de datos y advertencias («no es función de seguridad», «prototipo») | `PD` | Imprenta de etiquetas (vinil/poliéster) con cotización por millar |
| `empaque_mxn` | Caja, espuma, instructivo impreso | `PD` | Cotización de cajas de cartón y espuma |
| `flete_nacional_mxn_unidad` | Paquetería al cliente | `PD` | Tarifario de la paquetería con peso y medidas reales del kit empacado |
| `arancel_pct` | Arancel de importación (%) | `PD`. Referencia pública no oficial para la partida 8537.10.01: 10 % `[V parcial]` (ver §8). Otra fracción puede aplicar al PCBA | Opinión escrita de un agente aduanal con la fracción arancelaria, descripción y valor |
| `iva_importacion_pct` | IVA de importación | `[V]` 16 % tasa general (ver §8). Es acreditable; en el modelo solo pesa en el flujo de caja | Confirmar con contador/agente aduanal |
| `dta_y_agente_mxn_lote` | Honorarios del agente aduanal y derechos por pedimento | `PD` | Cotización del agente aduanal, o del servicio de paquetería con despacho. Preguntar si el envío pequeño entra por mensajería y bajo qué régimen |
| `merma_placas_pct` | % de placas inservibles o con retrabajo | `[H]` 0-20. Es rev B sin medición ni primer arranque; el piloto exactamente sirve para medirlo | Resultado real de la primera tanda de 5 |
| `garantia_pct_costo` | Reserva para reemplazos | `[H]` 3-10 % del costo directo | Tasa de falla medida; revisar con el seguro y el contrato de piloto |
| `soporte_horas_unidad` | Horas de puesta en marcha y soporte por kit | `[H]` | Bitácora del piloto (cronometrar cada visita y llamada) |
| `costo_hora_soporte_mxn` | Costo de la hora | `[H]` | Sueldo real/hora del ingeniero propio o tarifa de un tercero |
| `comision_canal_pct` | Margen que se queda el integrador/distribuidor | `[H]` 0 venta directa; 10-25 % si hay canal. El estudio §5.5 dice que el integrador suele decidir la especificación, sin cifra de comisión | Entrevistas con 3 integradores; condiciones comerciales del distribuidor |
| `precio_lista_mxn` | Precio sin IVA a probar | `[H]` $5,000-7,000 MXN, pago único, tablero local sin costo (estudio §6; ANALISIS §6) | Se decide solo con cotización real y 3 conversaciones con clientes (regla de la organización) |
| `gastos_fijos_totales_mxn` | NRE y gastos fijos que el margen debe recuperar | `PD`. Ver §5 | Cotizaciones de §5 |

Las columnas de lote se llenan por separado (5, 50, 200) porque el precio unitario de PCB, ensamble y piezas cambia con el volumen y porque la plantilla (stencil) y el cargo Extended se reparten entre menos unidades en el lote 5.

### Cómo calcula el script
- Valor de aduana = (PCB + piezas + cargo Extended + ensamble + envío) × tipo de cambio.
- Arancel = valor de aduana × `arancel_pct`; IVA importación = (valor + arancel + agente) × 16 %.
- Placa unitaria = (valor + arancel + agente + mano de obra final) / N / (1 − merma).
- Costo directo = placa + fuente + caja + etiqueta + empaque + flete nacional.
- Costo cargado = directo + reserva de garantía + horas de soporte × costo hora.
- Margen = (precio × (1 − comisión) − costo cargado) / precio.
- Precio mínimo = costo cargado / (1 − margen objetivo − comisión).
- Equilibrio = gastos fijos / (precio × (1 − comisión) − costo cargado).
- Capital del lote = salida de efectivo antes de cobrar, con y sin IVA de importación y con gastos fijos.

Límites declarados: no modela intereses, no descuenta en el tiempo, no incluye ISR, no modela inventario de piezas sobrantes ni retrasos en cobro. El IVA de importación es recuperable pero inmoviliza caja.

## 3. Precio ancla de competidores frente a la hipótesis de $5,000-7,000 MXN

Anclas del estudio (§5, consultadas 12-oct-2026, ~18 MXN/USD, **sin IVA, arancel ni flete** para las de distribuidor extranjero; conversión `[C]`):

| Producto | Precio | En MXN `[C]` a 18 |
|---|---|---|
| Siemens LOGO! 8 | $3,750-4,560 MXN `[V]` | 3,750-4,560 |
| Kincony KC868-A8 | 55 USD `[V]` | ~990 |
| Norvi IIOT-AE01-R | 88 USD `[V]` | ~1,584 |
| Arduino Opta Lite/WiFi | 146-184 USD `[V]` | ~2,628-3,312 |
| Schneider Zelio SR2 | 276-383 USD `[V]` | ~4,968-6,894 |
| WEG CLIC02 | 246 USD `[V]` | ~4,428 |
| Industrial Shields ESP32 PLC 21 | €239 `[V]` | no convertido (falta EUR/MXN verificado) |
| Allen-Bradley Micro820 | 514-1,224 USD `[V]` | ~9,252-22,032 |
| Evocon (OEE en la nube) | 189-319 USD **por máquina al mes** `[V]` | ~3,402-5,742 **al mes**; 12 meses ~40,800-68,900 |

Lectura:
- $5,000-7,000 queda **por encima** de LOGO!, Opta y clones asiáticos (que no son OEE/andon listos) y **en el rango** de Zelio, pero sin pantalla propia ni respaldo de marca. Eso es una desventaja de precio que hay que compensar con función (OEE+andon sin nube) y soporte local.
- Frente a Evocon, un pago único de $5,000-7,000 equivale a **menos de 2 meses** de suscripción en el rango alto y a ~1-2 meses en el bajo `[C]`. Es el argumento fuerte, pero compara hardware con servicio: no equivale a un reemplazo sin matices (Evocon incluye nube y análisis).
- Riesgo: el criterio de parar del ANALISIS §9 dice que si un competidor local baja claramente el precio, el diferenciador debe pesar. La entrevista debe medirlo, no suponerlo.

### Costo directo máximo que permitiría cada margen
Fórmula `[C]`: directo_max = (precio × (1 − margen − comisión) − soporte) / (1 + garantía). Aquí garantía 5 % `[H]`, soporte 0 (se resta después), precio sin IVA. Salida del script:

Comisión 0 %:

| Precio | margen 30 % | margen 50 % | margen 66.7 % (regla 3×) |
|---|---|---|---|
| 3,750 | 2,500 | 1,786 | 1,190 |
| 4,560 | 3,040 | 2,171 | 1,448 |
| 5,000 | 3,333 | 2,381 | 1,587 |
| 6,000 | 4,000 | 2,857 | 1,905 |
| 7,000 | 4,667 | 3,333 | 2,222 |

Comisión de canal 15 % `[H]`:

| Precio | margen 30 % | margen 50 % | margen 66.7 % |
|---|---|---|---|
| 3,750 | 1,964 | 1,250 | 655 |
| 4,560 | 2,389 | 1,520 | 796 |
| 5,000 | 2,619 | 1,667 | 873 |
| 6,000 | 3,143 | 2,000 | 1,048 |
| 7,000 | 3,667 | 2,333 | 1,222 |

Cómo leerlo: para cumplir la regla de partida «precio ≥ 3 × costo directo» a $6,000, el costo directo (todo: placa importada con arancel, fuente, caja, etiqueta, empaque, flete) no debe pasar de ~$1,900 MXN, y de ~$1,050 si hay 15 % de canal y se resta además soporte. Restar las horas de soporte (`soporte_horas × costo_hora`) del valor de la tabla antes de comparar con la cotización. Si la suma de cotizaciones excede la celda correspondiente, las palancas son: quitar funciones (menos relés, que son las piezas Extended más repetidas: 7 × G2RL), subir el precio, o vender solo la placa sin fuente ni caja.

## 4. Escenarios de ingreso del piloto

No se usa ninguna cifra de demanda. Se lee como «**si N clientes pagan P**». Ingreso = N × P sin IVA (el IVA de venta, 16 %, se cobra aparte y se entera; no es ingreso).

| Si N clientes pagan… | $5,000 | $6,000 | $7,000 |
|---|---|---|---|
| 3 | 15,000 | 18,000 | 21,000 |
| 5 | 25,000 | 30,000 | 35,000 |
| 10 | 50,000 | 60,000 | 70,000 |

Cómo usarlos:
- Compare cada celda con el **capital del lote** (salida del script) y con `gastos_fijos_totales_mxn`. Un piloto de 5-10 kits cubre, en el mejor caso del rango, una parte de los costos de lote; no cubre gastos fijos de certificación. Esto no es un fracaso: la puerta B del ANALISIS (kits piloto a costo) dice que el piloto es para aprender.
- **Puerta B, kits a costo:** P = costo cargado del lote (PD). Ingreso = N × costo cargado; margen 0 por diseño.
- **Puerta C, preventa con pago:** P ∈ rango [H]; solo con cotización real, entrevistas y los textos revisados por abogado.
- Con comisión de canal c, el ingreso neto es N × P × (1 − c).
- Cobro: documentar anticipo/saldo; los días de cobro no están en el script y afectan el capital.

## 5. Gastos no técnicos de una empresa de hardware en México

Lista de verificación para consultar a un profesional; **no es asesoría** (regla 10). Ninguna cifra se asume: todos son `PD`.

| Gasto | Qué cubre / pregunta clave | Cómo cotizar |
|---|---|---|
| Constitución y régimen fiscal | Persona moral o física con actividad empresarial; razón social, RFC, e.firma | Cotizar con 2-3 notarías/despachos; pedir qué incluye y si está el acta, el alta SAT y la cuenta |
| Contador | Contabilidad, facturación electrónica (CFDI), declaraciones, IVA e ISR, importaciones | 2-3 despachos; minuta de servicio mensual con alcance y qué no incluye |
| Abogado | Contrato de piloto, términos de venta, garantía, aviso de privacidad, marca (IMPI), propiedad del firmware y licencia de código abierto | Pedir cotización por entregable a 2-3 despachos con experiencia en propiedad intelectual y contratos tecnológicos; enlazar a `empresa/legal_marca/` |
| Marca y registro | Registro de marca ante el IMPI; búsqueda previa | Cotización del despacho o tasas oficiales vigentes del IMPI (consultar sitio oficial; no se asumen) |
| Certificación del producto: NOM / seguridad eléctrica | Qué norma oficial mexicana o evaluación aplica a un equipo de control de 24 V CC; si aplica etiquetado o evaluación de la conformidad. **No se asume cuál**. | Consultar a un organismo de certificación/laboratorio acreditado (entidad mexicana de acreditación, ema) para una evaluación de alcance; cotizar ensayos por norma |
| EMC | Emisiones/inmunidad del producto con Wi-Fi y relés (no hay medición alguna hoy) | Laboratorio acreditado: pedir cotización de pre-cumplimiento (más barato) y de ensayo completo, por separado |
| Radio / telecomunicaciones | El módulo ESP32-C3-WROOM-02 trae su propia documentación de radio, pero la homologación del equipo final en México debe verificarse con el regulador `[CG]` (el regulador cambió de nombre en 2025, confirmar vigente) | Consulta al regulador y a un gestor/lab acreditado; pedir si el certificado del módulo se puede aprovechar y bajo qué condiciones |
| Seguro | Responsabilidad civil de producto y de operaciones; daños a terceros por producto instalado en una planta | 2-3 corredores; describir producto, aclarar que **no es función de seguridad**, y pedir exclusiones por escrito |
| Garantía (reserva) | Reemplazos y retornos | Es el `garantia_pct_costo` del modelo; fijar con tasa de falla del piloto y términos del contrato |
| Stock de piezas y producto | Capital en inventario de piezas largas de entrega (relés, ESP32) y sobrantes; obsolescencia | Cotizar con proveedores el mínimo de compra y plazos; el script cuenta capital del lote, no stock de seguridad |
| Aduana y agente aduanal | Fracción, valor, pedimento, IVA, régimen para mensajería | Opinión por escrito del agente con la fracción; cotizar 2 agentes |
| Cuenta bancaria y pasarela de pago | Apertura, comisiones | Comparar 2-3 bancos/fintech: comisión por transferencia y por tarjeta |
| Local/taller y herramienta | Mesa de prueba, instrumentos (osciloscopio, fuente, carga), software | Cotización de equipo o renta de laboratorio; guardarlo como NRE |
| Cumplimiento de datos | Aviso de privacidad por captura de correos en web/consola | Entregable del abogado |
| Soporte posventa | Teléfono/correo, horas de ingeniería | Se modela con `soporte_horas_unidad` |
| Documentación y capacitación | Manual, hoja de datos revisada, videos | Horas internas o freelancer: cotizar por entregable |
| Contingencia | Rediseño rev C, placas fallidas, retraso de entrega | `[H]` porcentaje sobre el NRE total; decidir cuánto se tolera perder |

Suma de todo esto = `gastos_fijos_totales_mxn` en el modelo.

## 6. Valor para el cliente (ahorro por mejorar OEE): plantilla

OEE = Disponibilidad × Rendimiento × Calidad (definición estándar). Se sustenta el precio demostrando que el cliente recupera el precio en pocos meses. Todas las celdas son `[H]` y se llenan **con los datos de la planta del cliente**, no con promedios de la industria; no hay línea base medida de ningún cliente hoy.

| Celda | Símbolo | Cómo se obtiene | Valor |
|---|---|---|---|
| Horas planeadas de producción por año | H | Turnos × horas × días del cliente | `[H]` |
| Piezas ideales por hora | Ri | Ciclo ideal de la máquina (placa de datos o ingeniería del cliente) | `[H]` |
| Contribución por pieza buena (precio − costo variable) | Cp | Finanzas del cliente | `[H]` |
| OEE actual | O0 | Hoy suele estimarse a mano; el piloto mide la línea base | `[H]` |
| Mejora de OEE alcanzable (puntos porcentuales) | ΔO | Objetivo acordado con el cliente. No se asume cifra: se mide en el piloto | `[H]` |
| Costo de paro por hora si la máquina es cuello de botella | Cph | Cp × Ri × O0 aprox., o dato del cliente | `[H]` |
| Costo de calidad (retrabajo/rechazo) evitado | Cq | Tasa de rechazo × costo | `[H]` |

Fórmulas `[C]`:
- Piezas buenas adicionales/año = H × Ri × ΔO.
- **Ahorro o ingreso adicional anual = H × Ri × ΔO × Cp + Cq.**
- Valor de 1 punto de OEE = H × Ri × 0.01 × Cp.
- **Recuperación (meses) = precio por máquina / (ahorro anual / 12).**
- **ΔO de equilibrio = precio / (H × Ri × Cp)**, es decir, cuántos puntos de OEE debe ganar el cliente para pagar el equipo en un año.
- Si la máquina no es cuello de botella, el valor de las piezas adicionales es 0; el valor viene entonces de menor tiempo de supervisión, de calidad o de la reducción de paros costosos. Hay que preguntarlo, no asumirlo.

Ejemplo **ilustrativo** (números redondos para mostrar el uso, no son datos): H = 4,000 h, Ri = 100 pzas/h, Cp = $10, ΔO = 2 puntos. Ahorro anual = 4,000 × 100 × 0.02 × 10 = $80,000. A precio $6,000, recuperación = 6,000 / (80,000/12) = 0.9 meses. Con una máquina de menor ritmo o contribución, el resultado cambia por órdenes de magnitud; por eso se llena con datos del cliente. **Prohibido** usar este ejemplo como promesa de ahorro: el producto no ha sido medido y no existe resultado de OEE real.

Uso en la entrevista: pedir H, Ri, Cp y el costo de una hora de paro; calcular el ΔO de equilibrio y preguntar «¿cree que un monitor puede ayudarle a ganar esos puntos?». Eso respalda el precio mejor que compararse con la competencia.

## 7. Criterios financieros para parar o cambiar de rumbo
Umbrales `[H]`: son propuesta para la Dirección, se fijan antes de gastar, no después.

1. **Costo contra precio:** con cotizaciones reales, si el costo directo del lote 50 excede la celda de la tabla de §3 para margen 50 % al precio máximo creíble (≈ $7,000), rediseñar la oferta (menos relés, solo conteo/andon, venta sin fuente) antes de comprar más placas.
2. **Precio mínimo fuera de mercado:** si el precio mínimo para margen 30 % del lote 50 supera lo que el cliente dice que pagaría en entrevistas, parar.
3. **Entrevistas:** menos de 3 de 10 dispuestas a pagar el rango de §6 del ANALISIS (criterio ya vigente).
4. **Capital:** capital del lote + gastos fijos del primer año mayor que el capital que la Dirección acepta perder por completo. Fijar ese monto por escrito antes de pedir los 5.
5. **Valor para el cliente:** si ΔO de equilibrio (§6) supera lo que el cliente cree alcanzable, el precio no se sostiene; bajar precio o función.
6. **Piloto técnico:** fallos de aislamiento o alimentación (criterio ya vigente) o merma real de la primera tanda por encima de la hipótesis, que mueve el costo por encima de las celdas anteriores.
7. **Cotización de certificación:** si NOM/EMC/radio, sumado, supera el ingreso plausible del primer año de ventas, no vender más allá de piloto con carta; replantear mercado o alcance.
8. **Competidor:** un competidor local publica un precio claramente menor y el diferenciador (sin nube, soporte) no pesa en las entrevistas.
9. **Garantía/soporte:** las horas de soporte reales por kit superan el margen del precio; se detiene la venta hasta simplificar la instalación.
10. **Plazo:** sin avance de cotizaciones a la fecha que fije la Dirección (propuesta: 30 días), se pausa el gasto.

## 8. Fuentes externas (consultadas 14-oct-2026)
- IVA de importación 16 % (interior del país; 8 % franja norte) y 10 % para la fracción 8537.10.01 según catálogos TIGIE **no oficiales**: [Tariff Catalog 8502.13.01](https://tariffs.joffroy.com/en/fraccion/8502.13.01.html) y [camtomx 8537.10.01](https://www.camtomx.com/fraccion/8537-10-01). No se localizó el texto oficial de la TIGIE/LIGIE ni confirmación de que el capítulo 85 no esté exento; el [Anexo 27 de las RGCE 2025 (SAT)](https://www.sat.gob.mx/minisitio/NormatividadRMFyRGCE/documentos2025/rgce/anexos/Anexo27delasRGCEpara2025.pdf) lista exenciones y la búsqueda solo recuperó los capítulos 01-03. **Estado: `[V parcial]`; confirmar con agente aduanal.** El estudio cita además ~27.7 % de tasa efectiva de un agregador ([Wove](https://tariffs.wove.com/us/tariff/8537.10.91.60/delta-dvp-es2-plc)) para otro producto; por eso el arancel es entrada y no dato.
- Tipo de cambio: la fuente oficial es [Banxico, tipo de cambio](https://www.banxico.org.mx/tipcamb/tipCamMIAction.do?idioma=es) (FIX). La búsqueda no pudo extraer el FIX exacto de hoy y las notas de prensa difieren: [El Congresista, 5-oct-2026](https://elcongresista.mx/dolar-mexico-5-octubre-2026) reporta FIX ≈ 18.13; otra nota cita cierre de 18.4111 el 9-oct. Se deja la entrada como `[H]` 17-20 y se toma el valor del día de pago.
- Precios de competidores: `ESTUDIO_MERCADO_INDUSTRIAL.md` §5 (fuentes enlazadas ahí).

## Hallazgos
1. El costo real no puede calcularse: faltan todas las cotizaciones; el BOM 24DC tiene 18 piezas Extended únicas (incluyendo 7 relés, ESP32-C3, CA-IS3092W y 4 TCA9554) que concentran probablemente el costo `[H]`, y ninguna está en el catálogo local.
2. La regla «precio ≥ 3 × costo directo» a $5,000-7,000 exige costo directo ≲ $1,600-2,200 sin canal y ≲ $870-1,220 con 15 % de canal `[C]`.
3. El pago único de $5,000-7,000 frente a Evocon equivale a ~1-2 meses de suscripción, pero no son productos idénticos.
4. El lote de 5 es un gasto de aprendizaje: en el ejemplo ilustrativo, la plantilla y los cargos fijos hacen que el costo unitario de 5 piezas sea muy superior al de 50 y 200; no usar el lote de 5 para fijar precio.
5. Arancel y tipo de cambio mueven el costo más de lo que parece; ver sensibilidad.

## Qué falta saber
Cotización de JLCPCB (PCB+ensamble+piezas Extended), cotización de fuente, caja, etiqueta, empaque, flete, opinión aduanal (fracción, arancel, IVA, régimen), costos de NOM/EMC/radio, seguro, abogado, contador, cinco entrevistas con H, Ri, Cp y costo de paro, y capital máximo aceptable a perder.

## Siguiente paso recomendado
Pedir las cotizaciones de §2 en este orden: JLCPCB (5/50/200), agente aduanal, fuente/caja; correr el script con el JSON real; comparar el costo directo contra las tablas de §3; solo entonces definir precio.
