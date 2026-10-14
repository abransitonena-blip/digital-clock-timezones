# Documentos técnicos de un expediente de producto: AP Monitor 24

Fecha: 2026-10-14 · Dueño: ap-calidad-normas · Es la lista de lo que debe existir para poder defender el producto ante un cliente, un organismo o una autoridad. **Lista de verificación, no asesoría.** Estado: «Existe» significa que hay un archivo en el repositorio; no significa que esté completo ni revisado.

| ID | Documento | Contenido mínimo | Estado hoy | Dueño |
|---|---|---|---|---|
| D-01 | Especificación de producto y alcance | Qué es, qué no es, cargas permitidas, exclusiones, límites aprobados [A] | Parcial: `HOJA_DATOS_7R_TOUR.md` (concepto) | ap-producto |
| D-02 | Matriz de requisitos → evidencia | Esta carpeta, `MATRIZ_REQUISITOS_EVIDENCIA.csv` | Existe (borrador) | ap-calidad-normas |
| D-03 | Diseño de hardware | Esquemas, placa, generador, BOM, CPL, Gerber, notas de revisión; versión congelada con sello de integridad (hash) | Existe en `7r-tour/` | ap-hardware |
| D-04 | Control de configuración | Versión del firmware por número de placa, registro de cambios, hash del binario | Falta | ap-firmware |
| D-05 | Hojas de datos originales de piezas críticas | PDF del fabricante de G2RL-1A-E, CA-IS3092W, ULN2003A, TCA9554, PCF8563, LTV-217, regulador/buck, fusible, SMBJ33A, SS34, bornes KF128 | Falta (solo datos de páginas de distribuidor) | ap-compras-proveedores |
| D-06 | Análisis de riesgos y FMEA | `FMEA_AP_MONITOR_24.csv`, `REGISTRO_RIESGOS.csv` | Existe (estimaciones [H]) | ap-calidad-normas |
| D-07 | Información al usuario | Manual de instalación y uso, advertencias (no es equipo de seguridad; contacto soldado no se detecta; PNP; fuente SELV; protección externa; sin sello), etiqueta (modelo, tensión, corriente, bornes, polaridad, fabricante), hoja de arranque seguro | Falta | ap-calidad-normas + ap-producto |
| D-08 | Límites de producto por canal | Valores [A] respaldados por ensayo, y la decisión sobre el límite de tensión de contactos | Falta | ap-producto |
| D-09 | Plan y reportes de ensayos | `PLAN_PRUEBAS_BANCO.md` + hojas capturadas; `PLAN_ENSAYOS_LABORATORIO.md`; informes de laboratorio | Plan existe; reportes no | ap-calidad-normas |
| D-10 | Pruebas de software | Salida de `verificar_todo.sh` con fecha y versión, `probar_apbus.sh` | Existe (script); falta archivar la corrida por versión | ap-firmware |
| D-11 | Expediente normativo | Lista de normas aplicables y justificación de las que no, respuestas de organismos (L-00), certificados, alcances de laboratorios | Falta | ap-calidad-normas |
| D-12 | Trazabilidad de fabricación | Lote de placa, fecha, lista de piezas ensambladas, inspección de entrada, resultado de pruebas de aceptación por placa | Falta | ap-compras-proveedores |
| D-13 | Control de cambios | Procedimiento de cambio de BOM, placa o firmware, con matriz de qué ensayos se repiten | Falta | ap-calidad-normas |
| D-14 | Inspección de entrada y aceptación | Criterios de aceptación por placa (B-A, B-B, B-C, B-S1) y de componentes | Parcial: PUESTA_EN_MARCHA | ap-calidad-normas |
| D-15 | Mecánica | Plano de carcasa, material y ficha de inflamabilidad del plástico, bornes (sección y par) | Falta (concepto) | ap-hardware |
| D-16 | Radio | Decisión (homologar / módulo con número mexicano / variante sin radio), certificados, etiqueta con número | Falta | ap-calidad-normas + ap-legal-marca |
| D-17 | Garantía, devolución y términos | Revisados por abogado (ANALISIS_ECOSISTEMA §7) | Falta | ap-legal-marca |
| D-18 | Registro de marca y propiedad intelectual | IMPI «AP Electric», «7R Tour»; licencias de bibliotecas del firmware y avisos | Falta | ap-legal-marca |
| D-19 | Seguridad de la información | Gestión de clave Wi-Fi por equipo, actualización de firmware, qué datos guarda | Falta | ap-firmware |
| D-20 | Soporte y vigilancia posventa | Registro de quejas y fallas, acciones correctivas, recall hipotético | Falta | ap-ventas-clientes |
| D-21 | Registro de instrumentos de medición | Equipos usados en banco, calibración | Falta | ap-calidad-normas |
| D-22 | Declaración de uso previsto y uso indebido previsible | Qué hará mal el usuario (DIP olvidado, CC > 30 V, NPN, equipo de seguridad) y cómo se mitiga | Falta | ap-calidad-normas |

Regla del expediente: nada se imprime como «certificado», «cumple» ni con sellos (NOM, CE, UL, IFT) hasta que el documento correspondiente (D-11, D-16) exista y esté revisado por Dirección y por un profesional.
