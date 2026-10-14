# Ficha: AP Poka-Yoke

> **Estado propuesto: Concepto.** Responsable: ap-producto · 14-oct-2026. Marcas: [R] · [V] · [CG] · [H] · PD.

**Qué es [H].** Supervisor de estación: secuencia, presencia, torque OK y bitácora para trazabilidad, con salida de liberación que solo se activa si lectura válida, presencia y paso previo están bien [R: estudio §7.3, §9 oportunidad 5].

**Para quién [H].** Ensamble automotriz Tier 2/3 que debe documentar error-proofing y trazabilidad (IATF 16949: 8.5.2.1 y 10.2.4 [V: AIAG, vía estudio]; textos oficiales de pago, no leídos).

**Problema.** Soluciones comerciales de torque/poka-yoke cuestan miles de USD por estación (4,835-7,615 USD [V, estudio §5]).

**Hardware / firmware / web.** Base + AP INPUT + memoria no volátil (V3); bitácora con *hash* encadenado, receta, `plc`. Consola con tarjeta de secuencia y exportación.

**Evidencia.** Escritorio: I=4, E=3, R=4, Rg=3. Campo: ninguna.

**Lo que NO es.** **No es un dispositivo de seguridad.** No sustituye paro de emergencia ni guardas; no valida por sí mismo un proceso certificado.

**Riesgos.** Responsabilidad si el cliente lo confunde con seguridad; cada armadora tiene requisitos propios [V]; bitácora sin memoria no volátil no sirve.

**Siguiente puerta.** V3 en la Rev C y un cliente automotriz dispuesto a piloto. **Criterio de parar:** el cliente exige certificación que AP no pueda dar.

**Qué falta.** Definir qué registra exactamente, revisión de riesgos con un especialista, entrevistas.
