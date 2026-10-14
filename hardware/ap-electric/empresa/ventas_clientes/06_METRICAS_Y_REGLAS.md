# 6. Métricas de aprendizaje y reglas de parar o continuar

> Fecha: 14-oct-2026. **Hoy hay cero entrevistas registradas; no hay cifras de disposición a pagar ni de mercado.** Los umbrales son **hipótesis `[H]` de decisión** que debe aprobar Dirección antes de la primera ronda, para que las respuestas no se interpreten a conveniencia después. Con 10 conversaciones la muestra es pequeña: detecta señales fuertes, no estima proporciones del mercado. Complementa `ANALISIS_ECOSISTEMA.md` §9.

## 1. Definición operativa de «dispuesto a pagar»
Un prospecto cuenta como **dispuesto a pagar (`si`)** solo si, en conversación hecha (llamada o visita), cumple **las cuatro**:
1. Describe un problema concreto reciente (pregunta 11) con costo o consecuencia.
2. Nombra un **rubro o quién autoriza** el gasto (preguntas 8, 17, 18).
3. Da un **rango propio** de precio por máquina (pregunta 6), aunque sea inferior a nuestra hipótesis.
4. Acepta un **siguiente paso con fecha** (visita o piloto; pregunta 24).
`condicionado` = cumple 1 y 3, pero falta decisor o fecha. Cortesía, «me interesa» y «mándeme información» **no cuentan**.

## 2. Métricas (semanales; las calcula `resumen_embudo.py` donde se indica)
| Grupo | Métrica | Por qué importa |
|---|---|---|
| Alcance | Contactos intentados · respuestas · conversaciones hechas (script) | Mide si el canal funciona |
| Calidad | Semáforo verde/amarillo/rojo (script) | Evidencia de ajuste |
| Dinero | Dispuestos `si` de las conversaciones hechas (script) · rangos mencionados (media y mediana, **solo si hay al menos 5 rangos**) | Valida precio y negocio |
| Técnica | % con NPN o 127/220 V (script) · tipo de máquina · torre de luz | Qué falta de producto |
| Barreras | Bloqueadores principales (script): certificación, TI, soporte, garantía, nube | Qué objeciones frenan |
| Presión externa | % cuyo cliente (Tier 1/OEM) pide indicadores | Motor de compra `[H]` |
| Canal | % de integradores que instalarían en 2 o más clientes | Multiplicador de ventas |
| Piloto | Días con registro continuo; reinicios; exactitud de conteo; decisiones tomadas; horas de soporte | Funciona y sirve |
| Aprendizaje | Hipótesis confirmadas, refutadas y nuevas por semana (anotar en una lista) | Evita acumular datos sin conclusiones |

## 3. Reglas de parar, ajustar o continuar
Se evalúan **tras 10 conversaciones hechas** (no antes) salvo las reglas de seguridad.

| # | Condición | Decisión | Acción |
|---|---|---|---|
| R1 | Menos de **3 de 10** dispuestos a pagar (`si`) | **PARAR gasto en hardware** y revisar | No fabricar más placas; revisar segmento, propuesta y precio con las citas; decidir si se hace otra ronda de 10 con un perfil distinto o se descarta el producto |
| R2 | 3 o 4 de 10 | **CONTINUAR con límite** | Una segunda ronda de 10 en el segmento con más verdes; solo puerta B mínima (2-3 pilotos); sin ampliar compras |
| R3 | 5 o más de 10, con al menos 2 pilotos dispuestos | **AVANZAR** a preparar la puerta B | Completar `PUESTA_EN_MARCHA.md` y las condiciones de §7 de `ANALISIS_ECOSISTEMA.md` |
| R4 | 5 o más de 10 con sensores NPN | Priorizar **rev C (entradas NPN/PNP)** antes de pilotos | Solicitar a `ap-producto` y `ap-hardware` |
| R5 | 3 o más exigen certificación antes de cualquier prueba | **PAUSAR pilotos** | Consultar ruta con ANCE/NYCE y abogado (costos `PD`); reevaluar segmento (talleres chicos suelen exigir menos `[H]`) |
| R6 | 3 o más quieren usarlo como función de seguridad | **Reposicionar el mensaje** | Rediseñar la comunicación; si insisten, no es el mercado |
| R7 | Menos de 5 respuestas de 30 contactos fríos | Problema de **canal** | Cambiar a recomendaciones, clústeres o integradores antes de juzgar el producto |
| R8 | Ningún prospecto reconoce un problema concreto (verde en pregunta 11) en 6 de 10 | **Problema poco doloroso** | Detener; pivotar al segmento o al problema |
| R9 | El precio dicho por los dispuestos queda por debajo del costo real cuando exista cotización | No avanzar a puerta C | Revisar con `ap-finanzas` |
| R10 | **Incidente de seguridad** o sospecha de que el equipo afecte un circuito de seguridad | **PARO TOTAL** de pilotos | Retirar equipos, revisión independiente, informar al cliente |
| R11 | Primeros 3 pilotos: ninguno toma una decisión con el dato (O5) | Parar y rediseñar el uso | El dato no genera valor aunque funcione |
| R12 | Reinicios o fallas no explicadas en 2 de los primeros 3 pilotos | Volver a ingeniería | `PLAN_VERIFICACION.md` y corrección antes de continuar |

Estas reglas dan una decisión de **ventas y aprendizaje**; la decisión final es de Dirección. Un solo cliente entusiasta no cambia una regla.

## 4. Ritual semanal (30 minutos)
1. Correr `python3 resumen_embudo.py <csv>`.
2. Escribir 3 hechos nuevos con cita textual.
3. Marcar hipótesis confirmadas/refutadas.
4. Ver qué reglas R1-R12 se acercan.
5. Acordar los 5 contactos de la próxima semana.

## Fuentes
- `ANALISIS_ECOSISTEMA.md` §7, §9, §10; `PREVENTA_AP_MONITOR.md`.
- Método de entrevista: https://www.koji.so/docs/mom-test-user-interviews (14-oct-2026). Los umbrales son criterio del equipo `[H]`, no de una fuente.
