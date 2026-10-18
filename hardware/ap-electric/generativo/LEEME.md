# Diseño generativo híbrido

Dos piezas donde un algoritmo decide la forma y una parte paramétrica fija lo que no se puede mover (el gancho del riel DIN, los tornillos, las zonas prohibidas). Se genera con `python3 generativo/generar.py` (desde `hardware/ap-electric`).

| Pieza | Parte paramétrica (naranja) | Parte generativa (grafito) | Archivos |
|---|---|---|---|
| **Soporte de riel generativo** (`soporte_riel_generativo`) | Gancho de riel DIN TS35 con su plataforma y dos bosses de tornillo M3 de 11 mm | Ménsula en A de 8 mm de espesor, de optimización topológica 2D (SIMP, filtro de densidad) con 38 % del volumen | `salida/soporte_riel_generativo.stl` y `.glb` (dos materiales), `soporte_densidad.png` |
| **Tapa ventilada generativa** (`tapa_ventilada_generativa`) | La tapa de la caja AP Rack con sus 4 tornillos y la ventana de LED | 38 ventanas de un diagrama de Voronoi relajado, más densas y grandes donde están las piezas que calientan (reguladores, bobinas, MOSFET de salida) | `salida/tapa_ventilada_generativa.stl` y `.glb`, `tapa_mapa_calor.png` |

`salida/informe.json` trae los números de la última corrida.

## Cómo se genera

- **Soporte.** `topologia.py` resuelve elasticidad plana lineal (E = 1500 MPa supuesto para PETG impreso, ν = 0.35) en una cuadrícula de 120 × 60 elementos de 0.5 mm. El apoyo es el gancho (40 mm centrales de la base); la carga son 30 N repartidos en los dos tornillos (un módulo de 0.3 kg con factor 10 de vibración). Se mantienen sólidos los anillos de tornillo. Del campo de densidad sale un contorno, se limpia (sin filos de menos de 0.7 mm), se extruye y se une al gancho paramétrico.
- **Tapa.** Un mapa de calor (suma de gaussianas centradas en las piezas que calientan, tomadas de `rack16/gen/make.py`) fija la probabilidad de las semillas; cuatro pasos de relajación de Lloyd regularizan las celdas; solo se abren ventanas donde el calor pasa de un umbral, con nervios de 1.8 mm, y nunca sobre los tornillos ni la ventana de LED.

## Resultados del modelo (no medidos)

- Soporte: con la misma masa, la forma optimizada es unas **1.5 veces más rígida** que una placa de densidad uniforme en el modelo 2D (1.7 veces la flexibilidad de la placa llena con 38 % de la masa).
- Tapa: unos **44 cm²** de ventana repartidos en 38 aberturas.

## Límites (léelos antes de imprimir)

- Las cargas, el material y el mapa de calor son **supuestos de diseño**. No hay análisis por elementos finitos 3D, ni simulación térmica ni ensayo de carga de una pieza impresa; la impresión FDM es anisótropa (las capas son el punto débil) y el modelo plano no lo ve.
- Las ventanas **abren la caja al polvo y a los dedos**: la tapa ventilada no es IP-algo ni protege contra contactos. No usar donde haya que cumplir un grado de protección.
- Que la ventilación baje la temperatura de la placa **no está medido**.
- Nada está impreso. Son piezas de diseño.
