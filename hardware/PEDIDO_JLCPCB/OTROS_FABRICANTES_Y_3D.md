# Dónde fabricar AP ELECTRIC: placas armadas, impresión 3D y tornillería

> Precios y tiempos cambian. Confirma siempre en la cotización de cada sitio. Fuentes al final.

## Placas armadas (PCB + componentes)

| Fabricante | Ventajas | Desventajas | Archivos |
|---|---|---|---|
| **JLCPCB** (China) — **recomendado para empezar** | Precio y tiempo en línea al momento. Catálogo LCSC integrado: **todas las piezas de AP ELECTRIC traen su código LCSC**. Mínimo 5 placas (2 armadas). Muy barato en prototipos | Cada pieza "Extended" cobra ~3 USD por pedido. Piezas fuera de LCSC hay que pedirlas como "consigned" | **`PEDIDO_JLCPCB.zip`**: Gerber + BOM + CPL ya en su formato |
| **PCBWay** (China) | Acepta cualquier pieza (compra por número de fabricante, MPN), placas más complejas, revisión humana | Cotización de ensamble en 1-2 días hábiles; más caro en tiradas chicas | El mismo Gerber. La BOM pide columnas *MPN, Manufacturer, Qty, Designator, Package*: usa la de JLCPCB y agrega el MPN (va en la descripción de cada pieza del esquema). El CPL de JLCPCB sirve |
| **Seeed Fusion** (China) | Placa y ensamble en un solo servicio; consigue piezas difíciles | Menos piezas en existencia inmediata que LCSC | Gerber + BOM con MPN + CPL |
| **NextPCB / HQ** (China) | Precios competitivos; acepta códigos LCSC en la BOM | Catálogo propio menos usado | Gerber + BOM + CPL |
| **Fabricantes en México** (p. ej. PCBRAPIDO, PCB Central en Irapuato, Circuitec, Nortech en Monterrey) | Sin aduana, factura nacional, visita a planta, soporte en español | Normalmente más caros por pieza; revisar si arman SMD fino (0603, TSSOP) | Gerber (estándar RS-274X) + BOM + CPL; enviar también el PDF del esquema |

**Recomendación:**
1. **Prototipos (5-20 piezas por placa):** JLCPCB con `PEDIDO_JLCPCB.zip`, opción **"ensamble económico solo SMD"**. Los conectores (XT60, VH, XH, Qwiic) se sueldan a mano o se piden en "ensamble completo".
2. **Producción (100+):** cotiza el mismo paquete en JLCPCB **y** PCBWay; pide a un fabricante mexicano para comparar entrega y factura.
3. **Antes de producción:** pide muestras, prueba con las guías de cada placa (sección "Pruebas") y cambia lo que haga falta en el generador (`gen/make.py`).

## Conectores AP CONNECT (ya en el pedido)

Todos van en la BOM con código LCSC: JLCPCB los suelda en "ensamble completo", o se sueldan a mano.

| Familia | Uso | Código LCSC del lado de la placa | Del lado del cable |
|---|---|---|---|
| XT60PW-M (horizontal) | Entrada de la DIST 4 (hasta 30 A) | C98732 | Hembra XT60 con cable de 12-14 AWG (se vende armada) |
| JST VH 3.96 mm, 2/3/4 patas | Potencia: canales, pixeles, ramas, entradas de 20 A | C160315 / C160316 / C160317 | Carcasa VHR-2N/3N/4N + terminales SVH-21T-P1.1 (18-22 AWG); hay cables armados |
| JST XH 2.5 mm, 2/3/4 patas | Control: entradas, salidas de 24 V, 0-10 V, DMX, sensores | C158012 / C144394 / C144395 | Carcasa XHP-2/3/4 + terminales SXH-001T-P0.6 (22-28 AWG); hay cables armados |
| Qwiic (JST SH 1.0 mm, 4 patas) | Bus I2C entre CORE y módulos | C160404 | Cable Qwiic/STEMMA QT armado (5-50 cm) |

> Pide **cables ya armados** (los venden por color y largo). Solo si haces muchos, compra la **ponchadora** de cada familia (XH/VH y SH usan terminales distintas).

## Impresión 3D (gabinetes, soportes DIN, tapas de color)

| Servicio | Materiales | Notas |
|---|---|---|
| **JLC3DP** (de JLCPCB) | Resina, nylon, PETG/ASA (FDM), metal | Se puede pedir junto con las placas y llega en la misma caja |
| **PCBWay 3D** | PETG, ASA, nylon, resina, CNC | Coloca insertos si envías un plano con su ubicación |
| **Craftcloud** | Compara más de 150 talleres; PETG, ASA, nylon | Ve precios con envío a México |
| **Talleres locales** (Mercado Libre, makerspaces) | PETG/ASA | Más rápido para piezas sueltas; pide **ASA o PETG**, no PLA (el PLA se deforma al sol y en tableros calientes) |

Archivos a imprimir:
- `ap1-gabinete/gabinete/caja_base.stl` y `caja_tapa.stl`;
- `ap1-gabinete/din/soporte_din_88x56.stl` (BASE, IND, PIX, DMX, PLANTILLA, DIST 4, DO8, AP NODE, AP GATE, PWM4, AO4);
- `ap1-gabinete/din/soporte_din_72x56.stl` (AP INPUT, AI4).

Parámetros: **4 paredes, 40 % de relleno, ASA o PETG**. Para exteriores usa **ASA** (resiste UV).

## Tornillería e insertos

| Pieza | Para qué | Dónde |
|---|---|---|
| Inserto de latón M3 para calor (D 4.2 × 5.7 mm) | Postes del gabinete y del soporte DIN | JLCPCB/LCSC (marca XHHD, "heat-set insert"), Amazon, Mercado Libre |
| Tornillo M3 × 6 mm, cabeza plana o Allen | Placa al soporte | Ferretería, Mercado Libre |
| Tornillo de **nylon** M3 × 20 + separador de 11 mm | Programador sobre la base, junto a la antena (sin metal) | Mercado Libre, LCSC |
| Riel DIN TS35 (35 × 7.5 mm) | Montaje en tablero | Proveedores eléctricos |
| Fusibles mini de auto (ATM) 3-20 A | BASE, PIX, DIST 4 | Refaccionarias de autos |

> Los insertos y tornillos del catálogo de JLCPCB solo se pueden usar dentro de un pedido de ensamble; **no se envían sueltos**. Para piezas sueltas, usa LCSC o proveedores locales.

## Fuentes

- [Comparación JLCPCB vs PCBWay vs NextPCB 2026 (NextPCB)](https://www.nextpcb.com/blog/jlcpcb-vs-pcbway-vs-nextpcb-comparison-2026)
- [Capacidades de PCBA comparadas (NextPCB)](https://www.nextpcb.com/blog/pcba-capability-comparison)
- [JLCPCB vs PCBWay vs otros (Zbotic)](https://zbotic.in/jlcpcb-vs-pcbway-vs-lioncircuits-vs-zbotic-pcb-service-comparison-2026/)
- [Formato de BOM/CPL para PCBWay](https://skills.sh/aklofas/kicad-happy/pcbway)
- [Fabricantes de PCB en México (ensun)](https://ensun.io/search/printed-circuit-board-pcb/mexico)
- [Nortech: ensamble en Monterrey](https://www.businesswire.com/news/home/20150930006829/en/)
- [Servicio de impresión 3D de PCBWay (Fabbaloo)](https://www.fabbaloo.com/news/a-closer-look-at-pcbways-online-3d-printing-workflow)
- [Prueba del servicio 3D de JLC (Hackaday)](https://hackaday.io/page/395320-trying-out-jlcs-3d-printing-service)
- [Alternativas de impresión 3D: Craftcloud y otras (All3DP)](https://all3dp.com/2/best-shapeways-alternatives/)
- [Insertos de latón en JLCPCB (XHHD)](https://jlcpcb.com/partdetail/XHHD-SZTB1218/C51939033)
- Códigos de conectores: [XH 2P C158012](https://www.lcsc.com/product-image/C158012.html), [XH 3P C144394](https://www.lcsc.com/product-image/C144394.html), [XH 4P C144395](https://www.lcsc.com/product-image/C144395.html), [VH 2P C160315](https://jlcpcb.com/partdetail/JST-B2P_VH_LF_SN/C160315), [VH 3P C160316](https://www.lcsc.com/product-detail/C160316.html), [VH 4P C160317](https://www.lcsc.com/product-image/C160317.html), [XT60PW-M C98732](https://jlcpcb.com/partdetail/XT60PW-M/C98732), [TCA9554PWR C477924](https://www.lcsc.com/product-image/C477924.html), [ADS1115IDGSR C37593](https://www.lcsc.com/product-detail/C37593.html)
