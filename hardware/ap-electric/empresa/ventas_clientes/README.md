# Manual comercial de AP Monitor 24 (ventas y clientes)

> Fecha: 14-oct-2026. Validar antes de gastar. **Sin entrevistas no hay cifras:** nada aquí es evidencia de mercado. Prototipo sin placas medidas, sin certificación, no es función de seguridad, sin precio ni fecha comprometidos.

| Archivo | Contenido |
|---|---|
| `01_PLAYBOOK_DESCUBRIMIENTO.md` | 3 perfiles, cómo encontrar 10 prospectos, guion de 20 min y de 60 min, 25 preguntas, semáforo |
| `02_PLANTILLA_PILOTO_30_DIAS.md` | Objetivos, línea base manual de OEE y paros, instalación acompañada, checklist de seguridad, criterios, reporte |
| `03_SEGUIMIENTO.md`, `seguimiento_plantilla.csv`, `seguimiento_ejemplo_FICTICIO.csv`, `resumen_embudo.py` | Hoja de seguimiento y script del embudo |
| `04_MENSAJES_TIPO.md` | Correo y WhatsApp: contacto, seguimiento, cierre |
| `05_OBJECIONES.md` | Marca, certificación, NPN, nube, soporte, garantía, precio, seguridad |
| `06_METRICAS_Y_REGLAS.md` | Métricas y reglas R1-R12 de parar/continuar |
| `07_CAPACITACION_INTEGRADOR.md` | Módulos y examen práctico |

## Hallazgos (por gravedad)
1. **El riesgo mayor es confundir interés con demanda.** Se definió «dispuesto a pagar» con 4 condiciones medibles y reglas de decisión fijadas antes de entrevistar (06).
2. **Las entradas solo PNP bloquean a clientes con máquinas viejas (NPN).** Se mide desde la primera llamada (pregunta 3) y la regla R4 decide si la rev C va antes de los pilotos.
3. **El piloto no puede abrirse hoy:** la puerta B exige etapas A-D probadas en 2 placas, 72 h y contrato revisado; la plantilla se usa en papel hasta entonces.
4. **Seguridad:** el piloto propone no usar salidas de relé en serie con paros ni la «habilitación de proceso» para detener la máquina `[H]`; debe revisarla `ap-calidad-normas` y un responsable de seguridad.
5. Las fuentes para buscar prospectos (DENUE, SIEM, clústeres, Meximold, Directorio Automotriz) dan **listas y criterios, no nombres**. No se encontró un padrón público de socios de INA ni el directorio de ANIPAC.
6. El script se probó con el CSV ficticio y con el CSV vacío.

## Qué falta saber
Tasa de respuesta del canal, disposición a pagar real, proporción de NPN, qué exigen las plantas como certificación, si el OEE de AP coincide con ISO 22400-2, tolerancia de conteo aceptable, términos legales del piloto (abogado), portal vigente de consulta del DENUE y del SIEM.

## Siguiente paso recomendado
Que Dirección apruebe los umbrales R1-R12 y haga la primera ronda de 10 conversaciones (sin hardware) usando el playbook; registrar en el CSV y correr el script cada viernes.

## Fuentes (consultadas 14-oct-2026; solo resultados de búsqueda, no lectura completa)
Ver las secciones de fuentes de `01`, `02`, `06`. Principales: INEGI DENUE (guía y boletín), SIEM (gob.mx), clusterindustrial.com.mx, S&P Global sobre INA, Meximold (liderempresarial.com), Vorne OEE, NOM-004-STPS-1999 y NOM-029-STPS-2011, resúmenes de The Mom Test y SPIN. Documentos internos: `PREVENTA_AP_MONITOR.md`, `ANALISIS_ECOSISTEMA.md`, `WEB_Y_PLACA.md`, `PUESTA_EN_MARCHA.md`, `PACKML.md`.

Nota: la definición del agente indica la carpeta `ventas-clientes/` (con guion); por encargo explícito se escribió en `ventas_clientes/`.
