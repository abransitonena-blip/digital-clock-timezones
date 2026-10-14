# 6. Responsabilidad por producto y seguros: preguntas para un corredor

> **ADVERTENCIA:** lista de preguntas para un corredor de seguros y un abogado mexicanos. **No es asesoría legal ni de seguros.** No se verificó ninguna póliza, prima ni cobertura; no se cita ninguna aseguradora.

## 1. Contexto de riesgo `[R]` / `[H]`
- Producto: AP Monitor 24 = 7R Tour 24DC rev B + firmware + consola; prototipo, sin certificación; **no es función de seguridad**; 24 V CC de una fuente de terceros; 7 relés de contacto seco para torre de luz, andon y habilitación de proceso.
- Riesgos que el corredor debe conocer `[H]`: (a) un relé que energice una «habilitación de proceso» y arranque una máquina inesperadamente; (b) un cliente que lo use como seguridad pese a la advertencia; (c) calentamiento o incendio de la placa o de la caja; (d) falla que detenga o descomponga una línea (pérdida de producción); (e) pérdida de datos de producción; (f) daños a terceros durante la instalación; (g) retiro de unidades.
- Entidad: hoy no hay sociedad (ver `07_constitucion_empresa.md`): ¿a nombre de quién se contrata?

## 2. Preguntas para el corredor

### A. Tipo de póliza
1. ¿Qué cobertura se llama «responsabilidad civil de productos» frente a «responsabilidad civil general/comercial» en México? ¿Se contratan juntas?
2. ¿Existe una póliza para **prototipos / etapa piloto**, o la aseguradora exige producto terminado y certificado?
3. ¿Cubre daños **a terceros en sus instalaciones** (la planta del cliente) por unidades instaladas ahí?
4. ¿Cubre **errores de diseño y software** (responsabilidad profesional / tecnología), o hay que añadirla?
5. ¿Qué cubre una póliza de **retiro de producto** (recall)? ¿Aplica a este volumen?
6. ¿Hay cobertura para **daños al producto del cliente** (la máquina) o a la producción detenida (pérdida consecuencial)?
7. ¿Cobertura **cibernética** (el equipo tiene Wi-Fi, Modbus y datos de producción)? ¿Aplica a un producto, no a una oficina?

### B. Exclusiones y condiciones
8. ¿Las aseguradoras excluyen **equipos sin certificación** (NOM, UL, CE) o productos «en desarrollo»?
9. ¿Excluyen **uso en funciones de seguridad**? ¿Cómo debe quedar redactado el aviso para que no sea excusa de la aseguradora para negar?
10. ¿Excluyen componentes **importados** o fabricados por terceros fuera de México?
11. ¿Qué hace falta de documentación: planos, lista de materiales, reportes de prueba, manual?
12. ¿Exigen que el contrato con el cliente contenga **limitación de responsabilidad** o **renuncia a subrogación**? ¿Qué cláusulas del borrador (`03_contrato_piloto_b2b.md`) las aseguradoras rechazan?

### C. Monto y precio
13. ¿Cómo se determina la **suma asegurada** y el deducible para un negocio con 5 a 10 unidades? (No se asume ninguna cifra.)
14. ¿La prima depende de las ventas, del número de unidades instaladas o de la actividad? ¿Cuándo se ajusta?
15. ¿Hay **cobertura retroactiva** (reclamación presentada después de que termine la póliza) y cómo se compra?
16. ¿Cuál es la vigencia de la cobertura sobre unidades **ya vendidas** si se cancela la póliza?

### D. Quién es asegurado
17. ¿Persona física con actividad empresarial o sociedad? ¿Qué cambia en la póliza si se constituye después?
18. ¿Los **fabricantes por contrato** (ensamble) y el **proveedor de la fuente de 24 V** deben aparecer como coasegurados o pedirse su póliza?
19. ¿Se puede pedir al **cliente piloto** que muestre su póliza de planta y que cubra el uso del equipo?
20. ¿Qué cobertura necesitan los **empleados/contratistas** que instalen (riesgo de trabajo, IMSS)?

### E. Siniestros
21. ¿Cuál es el procedimiento y los plazos para avisar un incidente?
22. ¿Debo mantener bitácora de lotes y trazabilidad (número de serie, versión de firmware) para ser asegurable?
23. ¿Hay asistencia legal incluida?

## 3. Preguntas para el abogado sobre responsabilidad `[H]`
- ¿Qué régimen de responsabilidad por productos aplica a un fabricante/importador en México (civil, consumo, mercantil)?
- ¿Cómo responde el **importador** frente al fabricante extranjero?
- ¿La limitación de responsabilidad del contrato B2B (borrador cl. 9) es válida y hasta dónde? (dolo no renunciable; ver `03_...`.)
- ¿La advertencia «no es seguridad» en etiqueta y contrato protege, y cómo se documenta la entrega y aceptación?
- ¿Qué responsabilidad hay como persona física si no existe sociedad?

## 4. Mitigaciones técnicas que el corredor valorará (de `CONTEXTO_COMPARTIDO.md`) `[R]`
Arranque con todo apagado · canales de proceso solo con política APAGADO · pérdida de comunicación apaga canales · Wi-Fi apagado de fábrica · sin red de 127/220 V en el piloto · fuente certificada de terceros. **Nada de esto está medido ni certificado**; no presentarlo a la aseguradora como seguridad probada.

## Hallazgos
1. Sin sociedad, no hay asegurado claro (alta).
2. La aseguradora puede excluir el uso sin certificación y el uso como seguridad: las cláusulas de contrato deben coordinarse con la póliza.
3. El mayor escenario de daño es la «habilitación de proceso» de la máquina; hay que describirlo con precisión al corredor y limitar el piloto.

## Qué falta saber
Cuántas unidades, en qué máquinas, qué tipo de empresa cliente y qué valor tienen sus máquinas; presupuesto disponible.

## Siguiente paso recomendado
Pedir cotización de responsabilidad civil de producto a dos corredores con este documento y el borrador de contrato, antes de abrir la puerta B.

## Fuentes
- `CONTEXTO_COMPARTIDO.md`, `PREVENTA_AP_MONITOR.md`, `ANALISIS_ECOSISTEMA.md` §7 `[R]`. Sin fuentes externas: todo lo demás son preguntas.
