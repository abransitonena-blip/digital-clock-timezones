# Fuente capacitiva de 5 canales, versión 3 (placa de una cara)

Cinco canales independientes. Cada salida tiene su propia corriente, fijada por su capacitor X2. Mejoras respecto a la versión de 5 canales:

- Varistor 10D241K en la entrada.
- Capacitor X2 en bornera de 3 polos (se corta la pata de en medio): se cambia sin soldar.
- Zener de 5 W (1N53xxB) y resistencia de 100 Ω por canal: suavizan el golpe al conectar LED y limitan el voltaje sin carga.
- LED testigo por canal.
- Portafusible de chasis e interruptor iluminado en la caja.
- 4 agujeros de montaje M3.

Placa: 124 × 109 mm, sin puentes de alambre.

> ⚠ **No está aislada de la red.** Caja de plástico cerrada. Conecta los LED con la fuente apagada. Primera prueba con foco de 60 W en serie.

| Archivo | Qué es |
|---|---|
| `fuente_5canales_v3.pdf` | Pistas 1:1 para planchar (sin invertir), acomodo de piezas, lista de material, tabla capacitor/zener, cableado de la caja |
| `generar.py` | Genera los SVG y revisa separaciones (≥ 1.5 mm) y que cada conexión quede completa |
| `tabla.py` | Calcula el capacitor y el zener según los LED de cada salida |
| `hacer_pdf.cjs` | Arma el PDF |

Para regenerar: `python3 generar.py && python3 -c "import json,tabla;json.dump([[str(n),*[tabla.fila(n,3.1,3.4)[i] for i in (0,2)],*[tabla.fila(n,2.0,2.3)[i] for i in (0,2)]] for n in [1,3,5,8,10,15,20,25,30]],open('tabla.json','w'),ensure_ascii=False)" && node hacer_pdf.cjs`
