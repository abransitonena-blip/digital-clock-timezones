# Secuenciador de 3 flechas (3 × 9 LED verdes), 127 VCA

Placa de **50 × 60 mm**, una cara, con componentes de patas (THT) y **2 puentes de alambre**. Está hecha para transferencia de tóner.

Es **no aislada**, con el mismo principio que la placa Radox:

- NE555 como reloj.
- CD4017 que cuenta 1 → 2 → 3.
- 3 SCR MCR100-6 (o PCR606J), uno por flecha.

> **PELIGRO:** con la placa enchufada, todo el circuito (LED, 555, 4017, cables) queda a voltaje de red.
> Desenchufa y espera 10 s antes de tocar. Monta la placa dentro de la caja, sin partes metálicas accesibles.

## Cómo funciona

| Bloque | Qué hace |
|---|---|
| C1 474J + R1 + BR1 (2W10) + DZ1 12 V + C3 220 µF | Fuente de 12 V para el 555 y el 4017 (unos 19 mA; el zener absorbe lo que sobra) |
| C2 224J + R2 + BR2 (2W10) | Corriente de las flechas: **≈ 8 mA** (240 × 0.22 µF × (180 − 27 V)). Sin filtro, para que el SCR se apague en cada cruce por cero |
| NE555 + R6 47k + C5 10 µF | Reloj: T ≈ 1.4 × R6 × C5 ≈ **0.66 s por flecha** |
| CD4017 | Q0 → flecha 1, Q1 → flecha 2, Q2 → flecha 3; Q3 lo reinicia (solo 3 pasos). INH va al reset |
| R8–R10 4.7k + SCR1–SCR3 | Enciende la flecha que toca. Siempre hay una encendida |
| R3 1M | Descarga los capacitores al desenchufar |

Para cambiar la velocidad, cambia R6:

| R6 | Tiempo por flecha |
|---|---|
| 33k | 0.46 s |
| 47k | 0.66 s |
| 68k | 0.95 s |
| 100k | 1.4 s |

## Conexiones

- **J1 (clema):** 127 VCA, N y L (se pueden intercambiar). Toma los cables del mismo cordón que la placa Radox, en paralelo.
- **J2 (pads para cable), de arriba abajo:**
  - **+**: ánodo común de las 3 flechas.
  - **F3**: cátodo de la flecha 3.
  - **F1**: cátodo de la flecha 1.
  - **F2**: cátodo de la flecha 2.
  - El orden físico de los pads es F3, F1, F2, pero la secuencia sigue siendo 1 → 2 → 3.
- **SCR (TO-92):** patas **K G A** como marca la serigrafía. Verifícalo con la hoja de datos de tu SCR.
- **Puente 2W10:** el **+** del cuerpo va al pad cuadrado.
- **W1 y W2:** puentes de alambre en el lado de componentes, con **cable forrado** (W2 pasa sobre R6). Suéldalos primero.

## Materiales

| Cant | Pieza |
|---|---|
| 1 | Capacitor 474J 400 V (paso 10 o 15 mm) |
| 1 | Capacitor 224J 400 V (paso 10 o 15 mm) |
| 2 | Puente rectificador 2W10 |
| 2 | Resistencia 220 Ω 1 W fusible |
| 1 | Resistencia 1 MΩ ½ W |
| 1 | Zener 1N4742A (12 V 1 W) |
| 1 | Electrolítico 220 µF 25 V |
| 1 | Electrolítico 10 µF 25 V |
| 1 | NE555P + base DIP-8 |
| 1 | CD4017BE + base DIP-16 |
| 1 | Resistencia 47k |
| 3 | Resistencia 4.7k |
| 3 | SCR MCR100-6 o PCR606J |
| 1 | Clema de 2 polos |
| — | Cable forrado para W1/W2 y para J2 |

## Archivos (`fabricacion/`)

- `pcb/1_cobre_para_planchado_1a1.pdf`: imprímelo al 100 %.
- `pcb/3_lado_componentes_1a1.pdf`, `pcb/4_plantilla_perforaciones_1a1.pdf`, `pcb/5_ensamble_componentes_con_valores.pdf`
- `esquema/Flechas127_esquema.pdf`, `bom/BOM_KiCad.csv`, `gerber/`, `3d/`
- `reportes/`: ERC y DRC sin errores, y el esquema coincide con la placa.

## Prueba

1. Sin los CI (U1 y U2 fuera de su base), pon las puntas del multímetro con caimanes en las patas de DZ1 **antes de enchufar**. Enchufa sin tocar nada y lee **≈ 12 V**. Desenchufa.
2. Pon los CI (desenchufado) y conecta las flechas. Al enchufar deben correr 1 → 2 → 3.
