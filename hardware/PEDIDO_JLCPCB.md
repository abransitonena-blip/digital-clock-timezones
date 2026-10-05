# Cómo pedir las placas a JLCPCB con todo y componentes

Todo está en la carpeta **`PEDIDO_JLCPCB/`** (y comprimido en `PEDIDO_JLCPCB.zip`). Hay una subcarpeta por placa:

| Carpeta | Placa | Para qué |
|---|---|---|
| `1_BASE` | AP-1 base universal (4 capas) | Potencia: letreros, tiras y focos de corriente constante |
| `2_PROGRAMADOR` | AP-1 programador | El cerebro con Wi-Fi: va encima de la base o del módulo industrial |
| `3_MODULO_INDUSTRIAL` | AP-1 IND | 0-10 V aislado y contactores (naves, luces de red) |
| `4_MODULO_PIXELES` | AP-1 PIX | Pixeles direccionables WS2812/SK6812/WS2815 (letras en secuencia, efectos de color) |
| `5_AP02_placa_unica` | AP-0.2 rev D | Todo en una sola placa (alternativa sencilla al AP-1) |
| `6_PLANTILLA_modulos_nuevos` | AP-1 PLANTILLA | Base para probar y diseñar módulos nuevos: entrada protegida, 12 V, memoria, conector LL repetido en J8 y área de prototipos ([guía](ap1-plantilla/LEEME.md)) |

**Sistema mínimo:** 1 base + 1 programador. Para naves industriales: 1 IND + 1 programador. Para letreros de pixeles: 1 PIX + 1 programador. Para probar ideas: 1 PLANTILLA + 1 programador.

Cada carpeta trae:
- `1_..._GERBER.zip`: la placa (se sube tal cual, sin descomprimir).
- `ensamble_completo/`: BOM (`2_...`) y CPL (`3_...`) con **todas** las piezas.
- `ensamble_economico_solo_SMD/`: BOM y CPL **sin las piezas de patas** (clemas, zócalos, portafusible). Esas se sueldan a mano y no pagan cargo de montaje. **Recomendado.**
- `RESUMEN_costo_montaje.txt`: cuántos tipos de pieza Extended lleva cada opción y el cargo aproximado.
- `vista_superior.png`: para comparar con la vista previa de JLCPCB.

## Paso a paso en jlcpcb.com

1. **Order now → Add gerber file**: sube `1_..._GERBER.zip`. Las medidas y las capas se leen solas.
2. Opciones de la placa (lo que no está en la tabla se deja como venga):

| Opción | BASE | PROGRAMADOR | IND | PIX | AP-0.2 | PLANTILLA |
|---|---|---|---|---|---|---|
| Layers | **4** | 2 | 2 | 2 | 2 || 2 |
| PCB Thickness | 1.6 mm | 1.6 mm | 1.6 mm | 1.6 mm | 1.6 mm | 1.6 mm |
| Outer Copper Weight | **2 oz** | 1 oz | 1 oz | **2 oz** | **2 oz** | 1 oz |
| Inner Copper Weight | 1 oz | — | — | — | — | — |
| Layer stackup | JLC04161H-7628 | — | — | — | — | — |
| Surface finish | HASL sin plomo (o ENIG) | HASL sin plomo | HASL sin plomo | HASL sin plomo | HASL sin plomo | HASL sin plomo |
| Mark on PCB (número de pedido) | Remove (o "specify position") | igual | igual | igual | igual | igual |

3. Activa **PCB Assembly**:
   - **Assembly side: Top Side.** Todas las piezas SMD van arriba.
   - **PCBA Type: Standard.** La base es de 4 capas y lleva piezas Extended.
   - **Tooling holes: Added by JLCPCB.**
   - **Confirm parts placement: Yes.** Un técnico revisa giros y posiciones antes de armar.
4. **Next → sube la BOM y el CPL** de la carpeta que elegiste (económico o completo). Si pregunta por columnas:
   - Comment → Comment;
   - Designator → Designator;
   - Footprint → Footprint;
   - LCSC Part # → JLCPCB Part #.
5. **Revisión de la BOM:**
   - Todas las piezas SMD ya traen su código LCSC.
   - Revisa que digan "In stock". Si alguna se agotó, el buscador de JLCPCB ofrece una equivalente: mismo valor, encapsulado y voltaje igual o mayor.
   - Las filas sin código son piezas de patas para soldar a mano: marca **"Do not place"**.
6. **Vista previa de colocación (lo más importante):** revisa el **giro** de las piezas con polaridad y gíralas en la página si hace falta:
   - circuitos integrados: el punto de la pata 1;
   - MOSFET;
   - diodos: la raya del cátodo;
   - LED;
   - capacitor electrolítico (C1): la franja negativa;
   - conector USB-C;
   - módulo ESP32.

   Compara con `vista_superior.png`. KiCad y JLCPCB no siempre usan el mismo ángulo de origen, así que esta revisión siempre hace falta.
7. Paga. Si dejaste "Confirm parts placement: Yes", te piden aprobar las fotos antes de soldar.

## Piezas que se sueldan a mano (pedido económico)

| Placa | Piezas | Dónde se compran |
|---|---|---|
| BASE | J1, J3 (clema 2 polos 5.08 mm), J4 (4 polos 5.08 mm), J5 (4 polos 3.5 mm), J6 (2 polos 3.5 mm), F1 (portafusible mini Keystone 3568), J7 (zócalo hembra 2×8, 8.5 mm de alto) | Phoenix MKDS 3 y PT 1,5 o equivalentes (KEFA KF128-5.08-2P es C474952); portafusible C3206956; zócalo C30734 |
| PROGRAMADOR | J1 (macho 2×8, **por abajo**), J4 (macho 1×4), U4 (receptor IR TSOP38238) | C68234, C5116483, C141632 |
| IND | J1 (2 polos 5.08 mm), J2 (4 polos 3.5 mm), J3 (8 polos 3.5 mm), J7 (zócalo 2×8), U2 (convertidor B1212S-1WR3, C49260979) | Igual que la base |
| AP-0.2 | Clemas, portafusible ATO, relevador (C30431) | Igual |
| PLANTILLA | J1 (2 polos 5.08 mm), J7 (zócalo 2×8), J8 (macho 2×8) | C474952, C30734, C68234 |

Si prefieres que JLCPCB suelde también estas piezas, usa la carpeta `ensamble_completo`. Las que no tengan código, búscalas en la página de la BOM ("Search") o déjalas en "Do not place".

## Costo aproximado del montaje (por pedido, no por placa)

| Placa | Completo | Económico (solo SMD) |
|---|---|---|
| BASE | ~54 USD | ~36 USD |
| PROGRAMADOR | ~27 USD | ~18 USD |
| IND | ~24 USD | ~9 USD |
| PIX | ~36 USD | ~24 USD |
| AP-0.2 | ~57 USD | ~39 USD |

Cada tipo de pieza Extended cuesta unos 3 USD por pedido. Las Basic y Preferred no pagan ese cargo. A eso se suman la placa, las piezas y el montaje por unidad.

**Primera tanda sugerida:** 5 de cada placa, que es el mínimo de JLCPCB. Así se prueban antes de pedir más.

## Revisión hecha antes de generar los archivos

- ERC 0 y DRC 0 (incluidas advertencias), 0 sin conectar, 0 diferencias entre esquema y placa, en las 6 placas.
- **Reglas de fabricación de JLCPCB** revisadas con KiCad en las 6 placas:
  - pista y separación mínimas de 0.127 mm;
  - agujeros de 0.3 mm o más;
  - anillos de vía de 0.1 mm o más;
  - 0.5 mm entre agujeros de redes distintas;
  - 0.3 mm al borde;
  - textos de 0.8 mm o más.
- Se corrigieron dos cosas para JLCPCB:
  - el módulo ESP32 traía 12 vías de 0.2 mm (fuera del proceso estándar), que quedaron como 4 vías de 0.3 mm;
  - el shunt de 4 terminales (WSK2512) estaba agotado en LCSC; se cambió por un HoJLR2512 de 1 mΩ y 2 W en existencia, con una huella que mantiene la medición Kelvin.
