# Ficha: AP Monitor (AP Monitor 24)

> **Estado propuesto: Prototipo** (diseño cerrado por software; **ninguna unidad fabricada**). Responsable: ap-producto · 14-oct-2026. Marcas: [R] repositorio · [V] fuente · [H] hipótesis · PD por determinar. Plataforma: [`../PLATAFORMA_Y_HOJA_DE_RUTA.md`](../PLATAFORMA_Y_HOJA_DE_RUTA.md).

**Qué es.** Perfil sobre la placa base (7R Tour 24DC rev B + firmware PackML/OEE + tablero local) que agrega a una máquina sin datos: estado, conteo de piezas buenas/malas, causa de paro, microparos, andon, OEE y hora de cada evento [R: `PREVENTA_AP_MONITOR.md`].

**Para quién [H].** Talleres y plantas Tier 2/3 con máquinas viejas sin datos (inyectoras, maquinados, líneas de ensamble) que no sacan datos a internet [R: estudio §6].

**Problema que resuelve.** Hueco de «andon + OEE en una caja» sin nube, en español, con soporte local; las alternativas son suscripción por máquina (Evocon 189-319 USD/máquina/mes [V, estudio §5.2]) o clones de relés sin aplicación [R: ANALISIS §2.2].

**Hardware / firmware / web.** Placa base sin cambios; `cap`: `packml`, `entradas`, `conteo_rapido`, `rtc`; pestaña Producción de AP Studio. Sensor **PNP** de 24 V; **NPN no funciona** directo; sin Ethernet [R].

**Evidencia.** Escritorio: estudio §9 oportunidad 1 (I=5, E=2, R=5, Rg=1). Campo: **ninguna** (sin entrevistas ni medición).

**Lo que NO es.** No es función de seguridad, no está certificado, sin capacidad de contactos medida.

**Riesgos.** NPN (V1); bitácora y tiempos por estado que se reinician al apagar (V3); OEE por validar con un cliente [R: PACKML]; competencia de precio de clones de 55-88 USD [V].

**Siguiente puerta.** Etapas A-D en 2 placas → 72 h en máquina propia → puerta B. **Criterio de parar:** menos de 3 de 10 entrevistas pagan el rango de la hipótesis (no hay precio publicado) [R: ANALISIS §9].

**Qué falta.** Cotización real, entrevistas, mediciones M1-M14, caja DIN y etiqueta.
