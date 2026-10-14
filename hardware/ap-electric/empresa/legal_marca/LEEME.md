# Legal y marca de AP Electric: índice

> **ADVERTENCIA:** todo lo de esta carpeta son **listas de verificación y borradores para revisión de un abogado mexicano** (y, según el tema, de un contador, notario, corredor de seguros o agente aduanal). **No es asesoría legal.** Nada aquí está revisado por un profesional. Fecha de elaboración: 14-oct-2026. AP Electric no es una empresa constituida (ver `../ORGANIZACION.md`).

## Archivos

| # | Archivo | Qué contiene | Puerta que habilita |
|---|---|---|---|
| 1 | [01_marca_impi.md](01_marca_impi.md) | Procedimiento MARCia, clases de Niza, riesgo por nombre, alternativas | Todas (antes de imprimir etiquetas) |
| 2 | [02_aviso_privacidad.md](02_aviso_privacidad.md) | Marco vigente (LFPDPPP 2025) y borrador de aviso para la página | A (hoy ya se recogen datos) |
| 3 | [03_contrato_piloto_b2b.md](03_contrato_piloto_b2b.md) | Borrador de contrato corto de piloto | B |
| 4 | [04_terminos_preventa.md](04_terminos_preventa.md) | Regulación de consumo y comercio electrónico, borrador de términos con pago | C |
| 5 | [05_etiquetado_y_declaraciones.md](05_etiquetado_y_declaraciones.md) | NOM-024-SCFI y otras, tabla de declaraciones prohibidas | B y C |
| 6 | [06_responsabilidad_seguros.md](06_responsabilidad_seguros.md) | Preguntas para un corredor | B y C |
| 7 | [07_constitucion_empresa.md](07_constitucion_empresa.md) | Preguntas para contador y notario, sin recomendar | B y C |
| 8 | [08_licencias_software.md](08_licencias_software.md) | Dependencias y licencias del repositorio | B y C |

## Cómo se marcó la evidencia

`[V]`, `[CG]`, `[H]` según `../CONTEXTO_COMPARTIDO.md`, más:
- **`[V*]`** (añadida aquí): lo dijo un resultado de búsqueda con URL, **pero no se pudo abrir el texto oficial** (ver abajo). Es mejor que `[CG]` y peor que `[V]`.
- **«por confirmar con abogado»**: no se verificó o hay fuentes que se contradicen.

## Limitación importante de esta ronda

Desde este entorno el proxy **bloqueó el acceso directo** a `dof.gob.mx`, `diputados.gob.mx`, `mley.mx` y los portales del IMPI (WebFetch/curl: «CONNECT tunnel failed, 403»; fecha de intento 14-oct-2026). Solo funcionó el buscador, que devuelve resúmenes de terceros. Por eso **ningún artículo se pudo leer en el texto oficial**: ningún dato legal de estos documentos tiene `[V]` pleno. Antes de usar cualquier cita, el abogado debe leerla en el DOF o en la Cámara de Diputados. Tampoco se pudo consultar MARCia: **no se hizo ninguna búsqueda real de marcas**; no se afirma que algún nombre esté libre u ocupado.

## Hallazgos principales (por gravedad)

1. **Los cinco nombres tienen un elemento genérico o descriptivo** (Electric, Monitor, Control, Studio, 7R=7 relés) y solo «AP» y «Tour» distinguen; «AP» (dos letras) es probable que choque con terceros. Riesgo alto de objeción o de registro débil [H].
2. **La página ya recoge nombre, organización y contacto** (formulario de solicitudes) sin aviso de privacidad visible en el código revisado (`web/index.html`). Hay que publicarlo antes de difundir el enlace. La ley cambió: es la de 2025 y la autoridad ya no es el INAI.
3. **El repositorio no tiene archivo de licencia** y los encabezados del firmware no declaran titular ni licencia; los binarios incluyen el núcleo ESP32 de Arduino (licencia por confirmar, probablemente LGPL-2.1) con obligaciones al distribuirlos.
4. **La preventa con pago** exige términos conformes a la Ley Federal de Protección al Consumidor (si el comprador es consumidor) y al Código de Comercio; las cifras (garantía mínima, plazo de desistimiento) tienen fuentes contradictorias y quedan «por confirmar con abogado».
5. Declaraciones como «certificado», «seguro», sellos NOM/CE/UL/IFT, «compatible» con marcas ajenas (Wi-Fi, Modbus) y cualquier insinuación de función de seguridad están prohibidas hoy (ver archivo 5).

## Qué falta saber

Titular de la marca (¿persona física o futura sociedad?), quién firmará contratos, si los clientes del piloto serán empresas (B2B) o personas físicas consumidoras, si habrá importación de producto terminado, y si la página seguirá dentro de la plataforma actual (que guarda datos con la cuenta del visitante).

## Siguiente paso recomendado

1. Pagar una **búsqueda profesional de antecedentes** (agente de propiedad industrial) para los nombres elegidos, antes de gastar en etiquetas o dominio.
2. Pedir a un abogado de datos personales que revise el borrador 2 y lo publique en la página.
3. Abrir puerta B solo con contrato revisado (borrador 3), etiqueta (archivo 5) y póliza evaluada (archivo 6).

## Fuentes generales
- Búsquedas del 14-oct-2026 citadas en cada archivo. Fuentes oficiales a consultar: https://www.dof.gob.mx · https://www.diputados.gob.mx/LeyesBiblio/ · https://www.gob.mx/impi · https://www.gob.mx/profeco · https://platiica.economia.gob.mx/normalizacion/
