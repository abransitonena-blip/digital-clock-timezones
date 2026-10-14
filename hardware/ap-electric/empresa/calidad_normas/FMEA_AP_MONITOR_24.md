# Análisis de modos de falla (FMEA) del AP Monitor 24

Fecha: 2026-10-14 · Dueño: ap-calidad-normas con ap-hardware y ap-firmware · **S, O y D son estimaciones [H]**, no medidas; se revisan con los resultados del banco.

Escalas (1 a 10):
- **S (severidad):** 1 sin efecto · 3 molestia o dato erróneo · 5 parada de máquina · 7 daño al equipo o a la carga · 9 riesgo de fuego o de lesión probable · 10 lesión grave posible.
- **O (ocurrencia):** 1 improbable · 3 poco probable · 5 ocasional · 7 frecuente · 9 casi seguro.
- **D (detección antes de que llegue al cliente con los controles actuales):** 1 casi seguro se detecta · 5 puede detectarse · 9 casi nunca se detecta · 10 no se detecta.
- **RPN = S x O x D.** Regla de trabajo [H]: toda falla con **S ≥ 9** recibe acción aunque el RPN sea bajo; RPN ≥ 100 se atiende antes de la puerta B.

El CSV equivalente: `FMEA_AP_MONITOR_24.csv`. Orden: por RPN descendente.

| ID | Función | Modo de falla | Efecto | S | O | D | RPN | Controles actuales | Acción | Dueño |
|---|---|---|---|---|---|---|---|---|---|---|
| FM-09 | Salida (relé) | Vida de contacto menor a la esperada con LED | Contacto soldado o abierto | 8 | 5 | 8 | 320 | Límites por canal en PD; contactor externo recomendado | B-H1/B-H2 antes de declarar lámparas; no vender para LED sin límite | ap-hardware / ap-producto |
| FM-11 | Salida (relé) | Mala tensión de contacto aplicada por el usuario (CC > 30 V, trifásico) | Arco, daño, riesgo | 9 | 3 | 8 | 216 | Exclusiones en documentos | Etiqueta en equipo, manual, y revisión de textos comerciales | ap-calidad-normas |
| FM-10 | Salida (relé) | Sobrecalentamiento con 7 canales cargados | Deformación, fuego | 9 | 3 | 7 | 189 | Ninguno. «Sobretemperatura no se detecta» | B-F3, L-01; reducción por temperatura; evaluar NTC en rev C | ap-hardware |
| FM-07 | Alimentación | Sobretensión > 33 V (picos en red de 24 V de la máquina) | Daño del buck o reinicios | 6 | 5 | 6 | 180 | SMBJ33A | L-06 (sobretensión) y L-05 (ráfagas); instruir fuente dedicada | ap-hardware |
| FM-31 | Carcasa/Bornes | Borne flojo o conductor mal apretado | Calentamiento, arco | 7 | 4 | 6 | 168 | Ninguno | Hoja del borne, par en manual, B-F3 | ap-hardware |
| FM-04 | Corte de 24 V | Relé no abre al perder 24 V | Carga queda energizada | 9 | 2 | 9 | 162 | Ninguna: contacto soldado no se detecta (HOJA_DATOS) | Límites de carga por ensayo; declarar la limitación; medidas externas (contactor/termomagnético); considerar retroalimentación del lado de carga en rev C [H] | ap-hardware |
| FM-18 | Entradas | Ruido o ESD en cables largos produce conteos falsos | OEE erróneo | 5 | 5 | 6 | 150 | Antirrebote; optoaislamiento | L-04, L-05, L-06 | ap-hardware |
| FM-05 | Corte de 24 V | Re-cierre o rebote de relé durante caída lenta de 24 V | Pulsos en carga durante apagado | 6 | 4 | 6 | 144 | Ninguno | B-S2b; evaluar supervisor de tensión (rev C) si se observa | ap-hardware |
| FM-08 | Alimentación | Reinicios espurios por caídas breves de 24 V | Pérdida de estado de máquina; salidas abren | 5 | 5 | 5 | 125 | Monoestable abre; política de arranque | L-09 (caídas/interrupciones CC); documentar la fuente requerida | ap-firmware / ap-hardware |
| FM-02 | Arranque seguro | Relé se excita con USB conectado y 24 V que llega después | Pulso de carga | 8 | 3 | 5 | 120 | revisar_pines.py | B-S4a; documentar secuencia segura | ap-hardware |
| FM-06 | Polaridad | Polaridad invertida daña la placa | Placa inutilizada; riesgo térmico | 6 | 4 | 5 | 120 | Diodo serie SS34; fusible F1 3 A | B-S3a con limitación de corriente; marcar polaridad en serigrafía y borne | ap-hardware |
| FM-14 | Mando manual (DIP) | DIP usado como si fuera paro de emergencia o bypass | Falsa sensación de seguridad | 10 | 2 | 6 | 120 | Documentado: no es bypass ni seguridad | Texto explícito en el manual y la etiqueta | ap-calidad-normas |
| FM-01 | Arranque seguro | Un relé se excita brevemente al energizar | Pulso de carga; en proceso: arranque no deseado de equipo | 9 | 3 | 4 | 108 | RD1-RD7 10 kΩ (rev B); programa escribe 0 antes de configurar; prueba de arranque en PC | B-S1 obligatorio en cada placa de la primera tanda; prueba de aceptación en cada lote | ap-hardware |
| FM-26 | Vigilante | Programa trabado hasta 8 s con salidas retenidas | Carga energizada 8 s tras fallo de firmware | 7 | 3 | 5 | 105 | Vigilante de 8 s | B-S5; declarar; evaluar vigilante externo o parámetro más corto [H] | ap-firmware / ap-hardware |
| FM-15 | Entradas | No cuenta piezas (pérdida de pulsos) | OEE erróneo; decisiones equivocadas | 4 | 5 | 5 | 100 | Antirrebote; interrupción dedicada IO0/IO20 | B-D2a/b/c | ap-firmware |
| FM-21 | Modbus RS-485 | Tramas con error por ruido de conmutación | Pérdida de datos o comandos | 5 | 5 | 4 | 100 | CRC; aislamiento; SM712 | B-E3c/d, L-05, L-08 | ap-hardware |
| FM-32 | Documentación | Cliente toma el 7R Tour como equipo de seguridad o certificado | Daño a personas; responsabilidad | 10 | 2 | 5 | 100 | Reglas 2 y 5 del grupo | Revisión de textos; aviso de prototipo; revisión del revisor adversarial | ap-calidad-normas |
| FM-30 | Firmware | Versión equivocada cargada en una placa | Comportamiento no verificado | 6 | 4 | 4 | 96 | Línea de arranque con versión | Registro de firmware por número de placa (D-04) | ap-firmware |
| FM-23 | Modbus RS-485 | Pérdida de maestro no apaga canales | Carga queda en último estado | 7 | 3 | 4 | 84 | Vigilancia 0-3600 s; por omisión apaga | B-S7; advertencia de que 0 desactiva; configurar por defecto distinto de 0 [H] | ap-firmware |
| FM-24 | Wi-Fi / configuración | Red de configuración accesible por tercero | Cambio de configuración | 7 | 3 | 4 | 84 | Apagado de fábrica; clave propia por equipo | B-E4; confirmar generación de clave y tiempo de apertura | ap-firmware / ap-web-software |
| FM-25 | Wi-Fi / radio | Emisión sin homologación en México | Incumplimiento regulatorio; decomiso | 6 | 7 | 2 | 84 | Wi-Fi apagado de fábrica (no es una excusa legal) | L-12 antes de puerta C; sin vender hasta tenerlo | ap-calidad-normas / ap-legal-marca |
| FM-16 | Entradas | Umbral fuera de lo esperado (sensor a 24 V no reconocido) | Máquina no ve señal | 5 | 4 | 4 | 80 | Cálculo [C] | B-D1 | ap-hardware |
| FM-27 | Persistencia de configuración | Configuración corrupta tras corte durante escritura | Política de arranque errónea | 8 | 2 | 5 | 80 | Límite de escrituras (SW-LOGICA); configuración inválida reportada | Prueba de corte durante guardado (100 ciclos) en banco | ap-firmware |
| FM-29 | PackML/OEE | Datos de OEE erróneos por paro mal clasificado | Decisiones comerciales erróneas | 3 | 5 | 5 | 75 | Pruebas de PackML (PC) | Piloto en máquina real, comparación manual 1 turno | ap-firmware / ap-ventas-clientes |
| FM-13 | Mando manual (DIP) | DIP se deja encendido por olvido | Canal energizado aunque el programa diga apagado | 6 | 4 | 3 | 72 | LED de bobina; retroalimentación avisa «forzado» | Etiquetar la tapa; el aviso «forzado» visible en consola | ap-firmware |
| FM-19 | Reloj | Deriva de minutos por mes | Registros con hora errónea; trazabilidad | 4 | 6 | 3 | 72 | Ajuste por Modbus/consola | B-D5; cambio de cristal en rev C si > criterio | ap-hardware |
| FM-28 | Consola USB | Orden de «Probar relés» con carga conectada | Carga conmutada inesperadamente | 8 | 3 | 3 | 72 | Confirmación obligatoria | Prueba de la consola con placa real | ap-web-software |
| FM-03 | Arranque seguro | El canal de proceso arranca con política ÚLTIMO/ENCENDIDO por configuración errónea | Máquina arranca sola tras corte | 10 | 2 | 3 | 60 | Canal de proceso solo admite APAGADO (firmware) | B-S2c; revisión de que la consola no ofrezca la opción; advertencia | ap-firmware |
| FM-20 | Reloj | Pila recibe corriente (recarga) | Fuga o incendio de pila | 6 | 2 | 5 | 60 | BAT54C OR | B-D6 | ap-hardware |
| FM-22 | Modbus RS-485 | Escritura remota no autorizada reanuda máquina | Arranque inesperado | 10 | 2 | 3 | 60 | Permiso local; reanudar remoto bloqueado (PACKML) | B-E1b; prueba negativa en cada versión | ap-firmware |
| FM-17 | Entradas | Sensor NPN conectado | No funciona o corriente anómala | 3 | 6 | 3 | 54 | Documentado | Advertencia en etiqueta; rev C bipolar | ap-producto |
| FM-12 | Salida (bobina) | Pico inductivo de bobinas perjudica ULN2003A o EMC | Falla de driver; emisiones | 4 | 3 | 4 | 48 | Diodos del ULN2003A | B-S1 (forma de onda), L-03 | ap-hardware |
