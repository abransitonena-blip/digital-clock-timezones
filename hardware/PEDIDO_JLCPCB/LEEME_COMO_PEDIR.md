# Cómo pedir las placas AP ELECTRIC armadas

Todo está en **`PEDIDO_JLCPCB.zip`** (carpeta `PEDIDO_JLCPCB/`). Hay una subcarpeta por placa. **Ya no hay borneras de tornillo:** todo se conecta con cables armados (AP CONNECT: XT60, JST VH, JST XH y Qwiic), y **todas las piezas traen código LCSC**.

| Carpeta | Placa | Para qué |
|---|---|---|
| `1_BASE` | AP BASE (4 capas) | Potencia: 4 canales de 8 A, 2 focos de corriente constante, AUX; entrada de 20 A |
| `2_PROGRAMADOR` | AP CORE | El cerebro con Wi-Fi: va encima de la base o de un módulo |
| `3_MODULO_INDUSTRIAL` | AP-1 IND | 0-10 V aislado y 2 contactores (naves, luces de red por contactor) |
| `4_MODULO_PIXELES` | AP-1 PIX | Pixeles WS2812/SK6812/WS2815 |
| `6_PLANTILLA_modulos_nuevos` | PLANTILLA | Base para probar y diseñar módulos nuevos |
| `7_MODULO_DMX` | AP-1 DMX | Controlador DMX512 con Wi-Fi |
| `8_AP_INPUT` | AP INPUT | 8 entradas de 12-24 V aisladas |
| `9_AP_OUTPUT` | AP OUTPUT | 7 salidas de 24 V DC (bobinas, válvulas) |
| `10_AP_SIGN_DIST4` | AP SIGN DIST 4 | Distribución DC de 4 ramas con fusible y diagnóstico |
| `11_AP_PRO_AI4` | AP PRO AI4 | 4 entradas analógicas 0-10 V / 4-20 mA |

La AP-0.2 (placa única con borneras) ya no está en el pedido: la reemplaza el sistema modular.

**Combinaciones:**

| Para | Pide |
|---|---|
| Sistema mínimo | 1 BASE + 1 PROGRAMADOR |
| Prototipo AP ELECTRIC (luces, sensores, válvula) | 1 BASE + 1 PROGRAMADOR + 1 AP INPUT + 1 AP OUTPUT |
| Bombeo y nivel | + 1 AI4 |
| Letreros | PIX o DMX + 1 PROGRAMADOR (+ DIST 4) |
| Naves | IND + 1 PROGRAMADOR |

Cada carpeta trae:
- `1_..._GERBER.zip`: la placa (se sube tal cual, sin descomprimir).
- `ensamble_completo/`: BOM (`2_...`) y CPL (`3_...`) con **todas** las piezas, incluidos conectores y portafusibles.
- `ensamble_economico_solo_SMD/`: BOM y CPL **sin las piezas de patas** (conectores, zócalos, portafusibles). Esas se sueldan a mano y no pagan cargo de montaje.
- `RESUMEN_costo_montaje.txt`: cuántos tipos de pieza Extended lleva cada opción y el cargo aproximado.
- `vista_superior.png`: para comparar con la vista previa de JLCPCB.

**¿Completo o económico?**
- **Completo** si quieres recibir las placas listas para conectar. Recomendado ahora que todo son conectores con cable.
- **Económico** si tienes cautín: los conectores de patas se sueldan en minutos.

## Paso a paso en jlcpcb.com

1. **Order now → Add gerber file**: sube `1_..._GERBER.zip`. Las medidas y las capas se leen solas.
2. Opciones de la placa (lo que no está en la tabla se deja como venga):

| Opción | BASE | PIX, DIST 4 | Todas las demás |
|---|---|---|---|
| Layers | **4** | 2 | 2 |
| PCB Thickness | 1.6 mm | 1.6 mm | 1.6 mm |
| Outer Copper Weight | **2 oz** | **2 oz** | 1 oz |
| Inner Copper Weight | 1 oz | — | — |
| Layer stackup | JLC04161H-7628 | — | — |
| Surface finish | HASL sin plomo (o ENIG) | HASL sin plomo | HASL sin plomo |
| Mark on PCB (número de pedido) | Remove (o "specify position") | igual | igual |

3. Activa **PCB Assembly**:
   - **Assembly side: Top Side.** Todas las piezas van arriba.
   - **PCBA Type: Standard** (la BASE es de 4 capas y hay piezas de patas).
   - **Tooling holes: Added by JLCPCB.**
   - **Confirm parts placement: Yes.** Un técnico revisa giros y posiciones antes de armar.
4. **Next → sube la BOM y el CPL** de la carpeta que elegiste. Si pregunta por columnas:
   - Comment → Comment;
   - Designator → Designator;
   - Footprint → Footprint;
   - LCSC Part # → JLCPCB Part #.
5. **Revisión de la BOM:**
   - Todas las piezas traen su código LCSC.
   - Revisa que digan "In stock". Si alguna se agotó, el buscador de JLCPCB ofrece una equivalente: mismo valor, encapsulado y voltaje igual o mayor.
   - Los puentes de soldadura (JP) y los puntos de prueba (TP) no son piezas y no aparecen.
6. **Vista previa de colocación (lo más importante):** revisa el **giro** de las piezas con polaridad y gíralas en la página si hace falta:
   - circuitos integrados: el punto de la pata 1;
   - diodos: la raya del cátodo;
   - LED;
   - capacitores electrolíticos;
   - conectores: el seguro del lado correcto;
   - módulo ESP32.

   Compara con `vista_superior.png`.
7. Paga. Si dejaste "Confirm parts placement: Yes", te piden aprobar las fotos antes de soldar.

## Piezas de patas (se sueldan a mano en el pedido económico)

| Placa | Piezas | Códigos LCSC |
|---|---|---|
| BASE | J1 (VH 4), J3 (VH 2), J4 (VH 4), J5 y J8 (XH 2), J6 (XH 2), F1 (portafusible mini), J7 (zócalo 2×8) | C160317, C160315, C158012, C3206956, C30734 |
| PROGRAMADOR | J1 (macho 2×8, **por abajo**), J4 (macho 1×4), U4 (receptor IR) | C68234, C5116483, C141632 |
| IND | J1 (VH 2), J2/J4 (XH 2), J5/J6/J8/J9 (XH 2), J7 (zócalo 2×8), U2 (convertidor SIP) | C160315, C158012, C30734, C49260979 |
| PIX | J1 (VH 4), J2-J5 (VH 3), F1 (portafusible mini), J7 (zócalo) | C160317, C160316, C3206956, C30734 |
| PLANTILLA | J1 (VH 2), J7 (zócalo), J8 (macho 2×8) | C160315, C30734, C68234 |
| DMX | J1 (VH 2), J2 (XH 3), J7 (zócalo) | C160315, C144394, C30734 |
| AP INPUT | J4-J11 (XH 2), J3 (macho 1×4) | C158012, C5116483 |
| AP OUTPUT | J4 (VH 2), J5-J11 (XH 2), J3 (macho 1×4) | C160315, C158012, C5116483 |
| DIST 4 | J1 (XT60), J2-J5 (VH 2), F1-F4 (portafusibles mini) | C98732, C160315, C3206956 |
| AI4 | J7 (VH 2), J3/J4/J8/J9 (XH 3) | C160315, C144394 |

## Costo aproximado del cargo de montaje (por pedido, no por placa)

| Placa | Completo | Económico (solo SMD) |
|---|---|---|
| BASE | ~51 USD | ~36 USD |
| PROGRAMADOR | ~27 USD | ~18 USD |
| IND | ~21 USD | ~9 USD |
| PIX | ~36 USD | ~24 USD |
| PLANTILLA | ~18 USD | ~9 USD |
| DMX | ~18 USD | ~9 USD |
| AP INPUT | ~12 USD | ~6 USD |
| AP OUTPUT | ~18 USD | ~9 USD |
| DIST 4 | ~15 USD | ~6 USD |
| AI4 | ~15 USD | ~9 USD |

- Cada tipo de pieza Extended cuesta unos 3 USD por pedido. Las Basic y Preferred no pagan ese cargo.
- A eso se suman la placa, las piezas y el montaje por unidad.

**Primera tanda sugerida:** 5 de cada placa, que es el mínimo de JLCPCB. Así se prueban antes de pedir más (pruebas en la guía `LEEME.md` de cada placa).

**Otros fabricantes** (PCBWay, Seeed, NextPCB, fabricantes en México), **impresión 3D** de gabinetes y soportes DIN, y **tornillería:** ver `OTROS_FABRICANTES_Y_3D.md`.

## Revisión hecha antes de generar los archivos

- **ERC 0 y DRC 0** (incluidas advertencias), 0 sin conectar y 0 diferencias entre esquema y placa, en las 10 placas.
- **Reglas de fabricación de JLCPCB** revisadas con KiCad en las 10 placas:
  - pista y separación mínimas de 0.127 mm;
  - agujeros de 0.3 mm o más;
  - anillos de vía de 0.1 mm o más;
  - 0.5 mm entre agujeros de redes distintas;
  - 0.3 mm al borde;
  - textos de 0.8 mm o más.
- **Códigos LCSC verificados** en lcsc.com / jlcpcb.com para los conectores AP CONNECT, el TCA9554PWR (C477924) y el ADS1115 (C37593).
