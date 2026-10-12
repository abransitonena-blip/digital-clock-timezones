# AP Electric · Home Plug: hoja de datos preliminar

> **Estado: CONCEPTO.** Placa AP Home rev A (ERC y DRC sin errores); programa AP Control 1.0 (compila; pruebas en la PC). No fabricado, medido ni certificado.
>
> Origen de cada valor: [R] requisito · [C] cálculo · [E] componente · [M] medido (ninguno) · [A] aprobado (ninguno) · **PD** = por determinar.

| | |
|---|---|
| Función | Enchufar y usar: enciende y apaga una lámpara de 127 V CA conectada a su receptáculo. Sin regulación de brillo |
| Instalación | Se enchufa en un contacto con tierra. El usuario **no accede a bornes ni conductores de red**: la clavija y el receptáculo van encerrados en la caja |
| Limitación esencial | Si el apagador propio de la lámpara está abierto, este equipo no puede encenderla |

## Cargas

| Carga | Estado |
|---|---|
| Lámparas incandescentes y focos LED de 127 V no regulables (de mesa, de pie) | Previstas; carga máxima **PD** (meta 6 A resistivos [R]) |
| Lámparas regulables con atenuador, motores, calefactores, herramientas | **No** |

## Eléctrico

| | Valor | Origen |
|---|---|---|
| Alimentación | 127 V CA 60 Hz | [R] |
| Rango del producto | PD | |
| Fuente | Mean Well IRM-03-5: 85-305 V CA, 5 V 600 mA, certificada por su fabricante | [E] |
| Consumo en espera | PD; estimado < 1 W con Wi-Fi apagado | [C] |
| Relé | Omron G2RL-1A-E-HA DC5, monoestable; 16 A 250 V CA resistivo | [E] |
| Corriente al receptáculo (producto) | **PD**; la limita también el receptáculo y la clavija elegidos | |
| Irrupción de focos LED admisible | **PD** | |
| Protección interna | Fusible de retardo T2A y varistor 10D471K del lado de la electrónica | [E] |
| Protección de la carga | El interruptor de la instalación (contacto de 15 A típico) | |
| Tierra | Pasa directo de la clavija al receptáculo; no toca la placa | |
| Aislamiento red-baja tensión en la placa | ≥ 6.4 mm en el aire y por la superficie (DRC) | [C] |
| Aislamiento de la fuente | El de la IRM-03-5 | [E] |
| Clase de aislamiento del producto | PD | |

## Uso y comportamiento

| | |
|---|---|
| Botón | Corto = encender o apagar · 3 s = abre la red de configuración (15 min) · 10 s = valores de fábrica |
| LED | Verde = encendido · rojo = falla |
| Primer uso | Funciona local desde el primer encendido: sin cuenta, sin teléfono, sin nube, sin Wi-Fi |
| Arranque | Apagado (fábrica); opcional «último estado» o «encendido» (solo alumbrado) |
| Falla del programa | Vigilante de 8 s; el relé es monoestable y su salida del ESP32 tiene resistencia a 0 V: al reiniciar abre |

## Mecánica y ambiente

| | |
|---|---|
| Caja (concepto) | ≈ 62 × 87 × 38 mm, con clavija NEMA 5-15P y receptáculo NEMA 5-15R comprados y certificados (proveedor **PD**) |
| Uso | Interiores secos |
| Temperatura, humedad | PD |
| IP / IK | No declarados |

## Certificación

Ninguna. Por estudiar:
- NOM-003-SCFI-2014 y la NMX aplicable;
- IEC 60669-2-1 como referencia de diseño;
- homologación de radio (NOM-208 / IFT-008 → CRT).
