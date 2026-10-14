# AP Electric Group: organización y forma de trabajo

> **Estado:** estructura de trabajo propuesta, hoy operada por un coordinador (dirección) y 12 agentes especializados definidos en `.claude/agents/`. **No es una empresa constituida**: no hay razón social, cuentas, contratos ni empleados. Esto organiza el trabajo para que, cuando exista la empresa, cada área tenga dueño, reglas y evidencia.

## Estructura

```
Dirección (coordinador)
├── Mercado e inteligencia
│   ├── ap-mercado-industrial          industria y automotriz de México
│   └── ap-mercado-hogar-energia       hogar, edificios, energía, agua, agro, comercio
├── Producto
│   └── ap-producto                    catálogo, hoja de ruta, puertas de preventa, precios como hipótesis
├── Ingeniería
│   ├── ap-hardware                    placas, ruteo, BOM/CPL, pines
│   ├── ap-firmware                    AP Control, PackML, Modbus, pruebas
│   └── ap-web-software                web, consola, AP Studio, solicitudes
├── Calidad y cumplimiento
│   ├── ap-calidad-normas              plan de verificación, normas, evidencia
│   └── ap-revisor-adversarial         revisión independiente (no corrige, reporta)
├── Operaciones
│   └── ap-compras-proveedores         piezas, alternativas, manufactura, aranceles
├── Comercial
│   └── ap-ventas-clientes             entrevistas, pilotos, folios, aprendizaje
└── Legal y finanzas
    ├── ap-legal-marca                 marca, privacidad, contratos (listas para un abogado)
    └── ap-finanzas                    costo, margen, equilibrio, capital
```

## Qué decide quién

| Decisión | Responsable (R) | Debe opinar (C) | Aprueba (A) |
|---|---|---|---|
| Qué producto entra al piloto | ap-producto | mercado, ingeniería, calidad | Dirección |
| Cambio de una placa | ap-hardware | firmware, calidad, revisor | Dirección, tras `verificar_todo.sh` y revisión |
| Cambio del firmware | ap-firmware | hardware, calidad, revisor | Dirección, tras pruebas |
| Qué se afirma al cliente | ap-ventas-clientes | calidad, legal | Dirección |
| Precio de lista | ap-finanzas | producto, compras, ventas | Dirección, solo con cotización real y entrevistas |
| Pedir placas a JLCPCB | ap-compras-proveedores | hardware, calidad | Dirección (la persona con la cuenta) |
| Abrir una puerta de preventa | ap-producto | legal, calidad, finanzas, ventas | Dirección |

## Reglas de la empresa
1. **Evidencia primero:** un agente que afirma algo lo respalda con fuente, medición o prueba; si no, lo marca `[H]` o `PD`.
2. **Dueño de área:** solo el dueño cambia sus archivos (hardware, firmware, web). Los demás proponen por escrito.
3. **Revisión independiente:** `ap-revisor-adversarial` revisa antes de pedir placas o abrir un piloto; sus hallazgos se atienden o se justifican por escrito.
4. **Puertas de preventa** (ver `ANALISIS_ECOSISTEMA.md` §7): A lista de interés sin cobro → B kits piloto a costo → C preventa con pago. Ninguna se abre sin sus condiciones.
5. **Verificación única:** `bash hardware/tools/verificar_todo.sh` es la compuerta técnica por software. No sustituye ensayos físicos.
6. **Un coordinador:** los agentes no hacen commit ni push; la dirección integra, resuelve choques y publica.
7. **Registro:** cada informe va en `hardware/ap-electric/empresa/<área>/` con fecha, fuentes y marcas de origen.

## Ritmo de trabajo
1. **Ola de investigación** (mercado, compras, legal, finanzas, ventas, calidad, producto): informes con fuentes.
2. **Ola de revisión** (revisor adversarial sobre hardware, firmware, web y documentos).
3. **Ola de ingeniería** (hardware, firmware, web atienden hallazgos y propuestas de producto).
4. **Cierre:** `verificar_todo.sh`, actualización de documentos, commit y publicación.
5. **Medición real** (cuando existan placas): bitácora en `PLAN_VERIFICACION.md` y nueva ola.

## Cómo invocar a un agente
Desde Claude Code, con el nombre del agente (por ejemplo `ap-revisor-adversarial`) y un encargo concreto: qué revisar, dónde escribir y qué evidencia entregar. Los agentes leen `CONTEXTO_COMPARTIDO.md` antes de empezar.

## Qué falta para ser una empresa de verdad
Razón social y régimen fiscal, cuenta bancaria, aviso de privacidad, contrato de piloto revisado, seguro de responsabilidad, proveedor de ensamble con cotización, certificaciones del producto, y personas que ocupen cada rol. Las listas de verificación están en `empresa/legal_marca/` y `empresa/finanzas/`.
