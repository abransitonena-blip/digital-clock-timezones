# 3. Hoja de seguimiento de solicitudes y prospectos

> Fecha: 14-oct-2026. Archivos: `seguimiento_plantilla.csv` (vacía, solo encabezados), `seguimiento_ejemplo_FICTICIO.csv` (**datos inventados a propósito**: empresas «FICTICIA», correos `@ejemplo.invalid`; no son evidencia) y `resumen_embudo.py`.
> Contiene **datos personales** de contactos reales cuando se use: guardarla solo en un lugar con acceso limitado, registrar el consentimiento, no subirla al repositorio con datos reales. Aviso de privacidad y tratamiento: lista para un abogado en `empresa/legal_marca/`.

## Uso
```
python3 resumen_embudo.py seguimiento_plantilla.csv          # el tuyo
python3 resumen_embudo.py seguimiento_ejemplo_FICTICIO.csv --hoy 2026-10-14
python3 resumen_embudo.py archivo.csv --dias-vencido 10
```
Solo biblioteca estándar de Python 3 (probado con `python3 -I`). El script **no modifica** el CSV: imprime embudo por estado, origen, perfil, etapa de descubrimiento, semáforo, disposición a pagar con la regla de 3 de 10, bloqueadores, sensores, seguimientos vencidos y registros sin consentimiento.

## Columnas
| Columna | Valores / formato | Para qué |
|---|---|---|
| `id` | texto único (por ejemplo `AP-001`) | Identificador interno |
| `fecha_alta` | AAAA-MM-DD | Entrada al seguimiento |
| `origen` | `web`, `recomendacion`, `directorio`, `evento`, `prospecto`, otro | De dónde vino |
| `tipo_registro` | `solicitud` (llegó por la página) o `prospecto` (lo buscamos nosotros) | Separar demanda real de prospección |
| `folio` | folio que genera la página | Enlace con la solicitud web |
| `empresa`, `contacto`, `cargo`, `correo_o_telefono` | texto | Datos de contacto (personales) |
| `perfil` | `A` taller/planta, `B` integrador, `C` OEM | Ver `01_PLAYBOOK_DESCUBRIMIENTO.md` §1 |
| `ciudad_estado` | texto | Ubicación |
| `tipo_solicitud` | cotizacion, piloto, muestra, diseno_a_medida, soporte, interes, proveedor | Tipos de la página |
| `estado` | **Recibida · En revisión · Respondida · Piloto o muestra confirmados · En lista de espera · Cerrada · No viable** | Los mismos estados de la página (`WEB_Y_PLACA.md`). Escribirlos exactamente así |
| `etapa_descubrimiento` | identificado, contactado, sin_respuesta, llamada_hecha, visita_hecha | Avance de la prospección; el script cuenta las conversaciones hechas |
| `semaforo` | verde, amarillo, rojo, sin_dato | Regla del §6 del playbook |
| `maquinas_sin_datos` | número | Respuesta a la pregunta 1 |
| `sensores` | PNP, NPN, contacto_seco, torre_luz, mixto | Pregunta 3 |
| `bloqueador_principal` | npn, ti, certificacion, soporte, garantia, precio, nube, otro, ninguno | Objeción principal registrada |
| `disposicion_pago` | `si`, `condicionado`, `no`, `sin_dato` | Ver definición en `06_METRICAS_Y_REGLAS.md` |
| `rango_pago_mencionado_mxn` | texto, por ejemplo `5000-7000` | Número dicho por el cliente, no el nuestro |
| `fecha_ultimo_contacto`, `proximo_paso`, `fecha_proximo_paso` | AAAA-MM-DD y texto | Seguimiento |
| `responsable` | texto | Quién da seguimiento |
| `consentimiento_datos` | `si` / `no` | Si no es `si`, no se usa el contacto |
| `notas` | texto | Citas textuales, hechos; sin opiniones sobre la persona |

## Reglas
1. Un estado cambia solo con evidencia (mensaje, llamada). **Una solicitud web no es una compra**: no se cobra ni se promete precio ni fecha.
2. `Piloto o muestra confirmados` significa que el **cliente aceptó participar**, no que exista unidad: la entrega depende de la puerta B (`ANALISIS_ECOSISTEMA.md` §7).
3. `En lista de espera` = quiere participar, pero no hay unidad probada o no es el momento.
4. `No viable` se usa con motivo en `bloqueador_principal` (por ejemplo, exige certificación, quiere seguridad funcional, sensores NPN sin alternativa).
5. Los folios y estados de la web viven en la base de la página; este CSV es el espejo de trabajo del equipo. Al cambiar un estado en el panel, actualizarlo aquí el mismo día.
6. Revisión semanal: correr el script y atender los seguimientos vencidos antes de buscar prospectos nuevos.
