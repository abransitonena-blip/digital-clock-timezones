"""AP CONNECT: los conectores con cable de AP ELECTRIC (en lugar de borneras de tornillo).

Regla "Control ≠ Potencia": cada uso tiene su familia, de tamaño y forma distintos, para que no se puedan cruzar.
  BUS      Qwiic / JST SH 1.0 mm, 4 patas           I2C y 3.3 V entre CORE y módulos
  CONTROL  JST XH 2.5 mm (2, 3 o 4 patas), 3 A       entradas, salidas de 24 V a bobinas, 0-10 V, DMX, sensores
  POTENCIA JST VH 3.96 mm (2 o 3 patas), 10 A/pata   canales de LED, ramas, salidas de pixeles, alimentación de módulos
  ENTRADA  AMASS XT60 (macho en la placa), 30 A      fuente de las placas de mucha corriente (BASE, PIX, DIST 4)
Todos tienen seguro o forma con polaridad: no entran al revés. Los cables se compran armados (o se ponchan con las
terminales de cada familia).
Códigos LCSC en tools/jlcpcb.py (POR_HUELLA).
"""
XT60 = "Connector_AMASS:AMASS_XT60PW-M_1x02_P7.20mm_Horizontal"
VH2 = "Connector_JST:JST_VH_B2P-VH_1x02_P3.96mm_Vertical"
VH3 = "Connector_JST:JST_VH_B3P-VH_1x03_P3.96mm_Vertical"
VH4 = "Connector_JST:JST_VH_B4P-VH_1x04_P3.96mm_Vertical"     # entrada de 20 A: patas 1-2 = +, 3-4 = -
XH2 = "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical"
XH3 = "Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical"
XH4 = "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical"
SYM = {2: "Connector_Generic:Conn_01x02", 3: "Connector_Generic:Conn_01x03", 4: "Connector_Generic:Conn_01x04"}
SYM_XT60 = "Connector_Generic:Conn_01x02"
