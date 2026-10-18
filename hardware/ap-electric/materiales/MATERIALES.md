# Materiales de cables, conectores y contactos

Qué material conviene en cada parte de lo que ofrecemos: cobre o una aleación mejor según lo que hace la pieza, y el plástico adecuado. Los modelos 3D (`web/modelos3d/AP_CABLE_*.glb`, `AP_BORNE_KF128.glb`, `AP_CONTACTO_RELE.glb`, `AP_CONEXION_24V.glb`) separan cada parte con su material: hilos de cobre, aislante, puntera, cuerpo plástico y contacto metálico. Se generan con `python3 materiales/modelos_cables.py`.

> Todo lo de esta tabla es **conocimiento general de ingeniería [CG]** y recomendación de diseño: no es la lista de materiales de ninguna pieza comprada ni se ha validado con ensayos. Confirma siempre con la hoja del fabricante de cada conector, borne y relé.

| Parte | Material recomendado | Alternativas | Por qué |
|---|---|---|---|
| Hilos del cable AP LINK y de 24 V | Cobre electrolítico ETP C11000 estañado, trenzado fino (clase 5) | Cobre desnudo; **no** CCA (aluminio recubierto de cobre) | Mejor conductividad (100 % IACS); el estañado evita la corrosión en bornas y facilita la soldadura; el trenzado fino aguanta flexión y vibración |
| Aislante del cable | PVC 70-80 °C (tableros) o XLPE 90-125 °C (cerca de calor) | Silicona o TPE (temperatura alta o cables que se mueven) | PVC barato y autoextinguible; XLPE más temperatura; confirmar la clase de ignifugación |
| Punta del cable de 24 V (puntera) | Tubo de cobre electrolítico estañado con collar de PA o PP | Latón estañado (más barato, peor conductividad) | Baja resistencia de contacto, no se oxida; evita que los hilos se abran bajo el tornillo |
| Contactos a presión del conector XH | Bronce fosforado CuSn5 (C51000) estañado | Latón CuZn30; CuBe C17200 (resorte premium, trato especial por el berilio) | Elasticidad: conserva la fuerza de contacto con los ciclos de conexión (15-20 % IACS, suficiente para los pocos mA del AP LINK) |
| Cuerpo del conector XH y del borne | PA66 con fibra de vidrio (V-0, 105-125 °C) | PBT-GF; PA46 si se suelda con reflujo sin plomo | Aguanta la soldadura y es autoextinguible (UL 94 V-0); el PA absorbe humedad y cambia medidas |
| Abrazadera del borne de tornillo | Latón CuZn39Pb3 (C38500) estañado o niquelado | Cobre estañado; **CuCrZr (C18150)** para bornes de 30 A o más | El latón se mecaniza y aguanta el apriete; CuCrZr conserva resistencia mecánica con conductividad de cerca de 80 % IACS, para corrientes altas |
| Tornillo del borne | Acero zincado pasivado (o inoxidable A2) | Latón niquelado | La corriente va por la abrazadera, no por el tornillo |
| Contactos del relé | **AgSnO2** sobre lámina de bronce o CuSn6 | AgNi 90/10 en cargas resistivas pequeñas; el AgCdO ya no se usa | Resiste el desgaste y la soldadura del arco con motores o lámparas |
| Pistas y planos de la placa | Cobre 2 oz (70 µm), HASL sin plomo o ENIG | Cobre 3-4 oz para 10 A o más (placa especial) | Hoy: pistas de +V de 0.8 mm con fusible de 3 A, sin medir el calentamiento |
| Caja y tapa (prototipo) | PETG (interior) o ASA (exterior) | PA12 (MJF) en series cortas; PC/ABS inyectado en producción | PETG fácil y tenaz; ASA no amarillea; la inyección pide molde |
| Soporte generativo | PETG o PA12-CF impreso | Aluminio mecanizado o fundido si la carga lo exige | La rigidez real depende de la orientación de las capas: probarla |

## Qué cambiaría en producción respecto al prototipo

- Cables: de hilos sueltos con carcasa XH a un arnés con funda y malla si el AP LINK se tiende junto a motores o variadores (el diseño actual no lleva blindaje).
- Bornes y contactos: elegir por **corriente** y **temperatura**, no solo por precio: arriba de unos 16 A, abrazaderas de cobre o CuCrZr y tornillo de acero inoxidable.
- Plásticos de contacto con el cobre: PA66-GF V-0 o PBT-GF; el PETG impreso solo en cajas de prototipo, nunca como cuerpo de un conector que lleve corriente.

## Qué se modeló y qué no

Modelado: cable AP LINK (par trenzado A/B, SENSE y GND, conectores XH, hilos de cobre visibles), cable de 24 V con punteras, borne KF128 de 3 polos (cuerpo, tornillos, abrazaderas, patas), contacto de relé (terminal de cobre, lámina de bronce, botones AgSnO2) y la conexión de un borne con dos cables. Las medidas son de dibujo [H]; no son los modelos del fabricante.
