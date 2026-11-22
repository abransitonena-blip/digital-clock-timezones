"""Datos PÚBLICOS de los productos AP: entradas, salidas, límites, ambiente y uso.
Única fuente para las hojas de datos, el manual, la garantía (PDF) y la página Soporte del sitio (src/datos/fichas.json).
Aquí NO va cómo está hecho por dentro (chips, circuito, firmware): solo lo que el usuario conecta, ve y puede esperar.
Valores de diseño: preliminares hasta medir prototipos y certificar."""

FECHA = "2026-11-22"
VERSION = "0.9 (preliminar)"
EMPRESA = {   # completar antes de publicar: la LFPC exige nombre, domicilio y teléfono del responsable
    "razon": "[Razón social del fabricante o importador]", "domicilio": "[Domicilio completo]", "rfc": "[RFC]",
    "telefono": "[Teléfono de soporte]", "correo": "[Correo de soporte]", "web": "[Sitio web]",
}

CUBO = {
    "codigo": "HD-CUBO-AP", "nombre": "Cubo AP", "subtitulo": "Controlador LED inteligente impermeable para letreros y arquitectura",
    "resumen": ("Controlador de tiras LED en un cubo sellado de 80 mm con fuente integrada. Maneja tiras analógicas de 1 a 5 canales "
                "y tiras direccionables, se controla por Bluetooth, Wi-Fi, DMX512, Art-Net/sACN y Matter, y protege la tira con un "
                "voltaje máximo fijado por una tarjeta de configuración."),
    "versiones": [
        ["Cuerpo ASA (plástico)", "Interiores y exteriores bajo techo, hasta ≈ 15 W de salida continua a 30 °C"],
        ["Cuerpo de aluminio con aletas", "Exteriores e instalaciones de potencia: hasta 60–75 W de salida (ver curva de carga)"],
    ],
    "secciones": [
        ["Entrada de alimentación", [
            ["Con cartucho de corriente alterna", "100–240 V~, 50/60 Hz (rango 90–264 V~)"],
            ["Cartucho S / L", "25 W / 75 W de salida máxima"],
            ["Sin cartucho (corriente directa)", "12–36 V⎓; debe ser al menos 1.2 V mayor que el voltaje de salida"],
            ["Consumo en espera (luz apagada, Wi-Fi conectado)", "≈ 1 W (estimado)"],
            ["Protecciones de entrada", "Fusible, polaridad invertida (CD), supresión de transitorios, bajo voltaje"],
        ]],
        ["Salida LED analógica (ánodo común)", [
            ["Canales", "Hasta 5: R, G, B, W y blanco frío (según el tipo de tira)"],
            ["Voltaje de salida", "Fijado por la tarjeta: 5, 12, 15 o 24 V⎓; ajustable hacia abajo desde la app"],
            ["Corriente máxima total", "Fijada por la tarjeta: 1 a 5 A (ver tabla de perfiles)"],
            ["Corriente máxima por canal", "5 A"],
            ["Atenuación", "PWM de 19 kHz, 4096 pasos, sin parpadeo visible en cámara"],
            ["Tipos de tira", "RGBW, RGB, CCT (blanco dual), monocolor y RGB+CCT"],
        ]],
        ["Salida LED direccionable", [
            ["Señal", "Datos de 5 V, un hilo"],
            ["Compatibles", "WS2812B y SK6812 (5 V), WS2811 y WS2815 (12 V)"],
            ["Número de LEDs", "Hasta 600"],
        ]],
        ["Control y comunicación", [
            ["Bluetooth", "Bluetooth LE 5, vinculación con PIN de 6 dígitos (en la etiqueta)"],
            ["Wi-Fi", "2.4 GHz 802.11 b/g/n, antena externa"],
            ["Iluminación profesional", "Art-Net y sACN (E1.31) por Wi-Fi; DMX512 por cable, entrada o salida"],
            ["Hogar", "Matter (Apple Home, Google Home, Amazon Alexa, Home Assistant) en la versión con Matter; WLED y Alexa en la versión estándar"],
            ["Grupos", "Varios cubos sincronizados con clave de grupo"],
            ["Funciones", "Brillo, color, temperatura de blanco, 5 efectos, 8 escenas, horario diario, actualización por Wi-Fi"],
        ]],
        ["Protección de la carga", [
            ["Voltaje máximo", "Lo fija la tarjeta: ninguna orden de la app puede rebasarlo"],
            ["Sobrecorriente", "Reduce el brillo al acercarse al límite; corta a 1.5 × el máximo y reintenta (3 veces, cada 5 s)"],
            ["Corto en la salida", "Corte inmediato y reintento"],
            ["Temperatura", "Reduce el brillo de forma gradual por encima de 70 °C internos; apaga a 90 °C y vuelve al enfriarse"],
        ]],
        ["Ambiente", [
            ["Temperatura de operación", "−20 a +50 °C (con la curva de carga de abajo)"],
            ["Temperatura de almacenamiento", "−30 a +70 °C"],
            ["Humedad", "10–95 %; membrana de ventilación contra la condensación"],
            ["Protección", "IP67 de diseño (sumergible 30 min a 1 m); certificación pendiente"],
            ["Sol directo", "Preferir acabado claro; el sol suma calor y reduce la carga máxima"],
        ]],
        ["Mecánica", [
            ["Medidas", "80 × 80 × 80 mm (104 mm de largo con las orejas de montaje)"],
            ["Masa aproximada", "ASA ≈ 300 g · aluminio ≈ 550 g (con cartucho S)"],
            ["Entradas de cable", "2 prensaestopas M16 IP68 para cable de 4–8 mm de diámetro (alimentación y LED)"],
            ["Conexiones internas", "Borneras enchufables: entrada 2 polos, salida LED 8 polos (V+ R G B WW CW DAT GND), DMX 3 polos"],
            ["Montaje", "2 orejas con ranura para tornillo M4 (pared, poste o riel)"],
        ]],
    ],
    "perfiles": [["5 V 3 A", "5.0 V", "3 A", "15 W", "Direccionables de 5 V"],
                 ["12 V 1 A · 2 A · 5 A", "12.0 V", "1 / 2 / 5 A", "12 / 24 / 60 W", "Tiras de 12 V; 12 V 5 A requiere cuerpo de aluminio"],
                 ["15 V 1 A · 3 A", "15.0 V", "1 / 3 A", "15 / 45 W", "Módulos de 15 V"],
                 ["24 V 2 A · 3 A", "24.3 V", "2 / 3 A", "48 / 72 W", "Tiras de 24 V; cuerpo de aluminio y cartucho L"]],
    "notas": ["Valores de diseño, preliminares: se confirmarán con mediciones en prototipos y con las certificaciones.",
              "Certificaciones pendientes: seguridad eléctrica (NOM), homologación de radio (IFT) e IP67 en laboratorio.",
              "La instalación del lado de 100–240 V~ debe hacerla personal calificado."],
}

NODO = {
    "codigo": "HD-NODO-AP", "nombre": "Nodo AP", "subtitulo": "Decodificador DMX512 de 4 canales para tiras LED",
    "resumen": ("Recibe DMX512 por cable y maneja una tira de 12–24 V de 4 canales (RGBW, ánodo común). "
                "Se encadena: muchos nodos en una sola línea DMX, alimentada por un Cubo AP, una consola o una interfaz Art-Net."),
    "versiones": [["Caja de plástico", "Interiores; carga completa hasta 40 °C"],
                  ["Caja de perfil de aluminio", "Carga completa hasta 50 °C; recomendada para 5 A continuos"]],
    "secciones": [
        ["Entrada de alimentación", [
            ["Voltaje", "12–24 V⎓ (rango 10.8–26.4 V)"],
            ["Consumo propio", "< 0.5 W"],
            ["Protecciones", "Fusible de 8 A, protección de la lógica contra polaridad invertida"],
        ]],
        ["Salidas", [
            ["Canales", "4 (R, G, B, W), ánodo común: V+ y un negativo por canal"],
            ["Corriente", "Hasta 3 A por canal y 5 A en total"],
            ["Atenuación", "PWM de 3.9 kHz, 1024 pasos, curva gamma 2.2 (o lineal)"],
            ["Al arrancar", "Salidas apagadas hasta recibir DMX"],
        ]],
        ["DMX512", [
            ["Estándar", "DMX512-A (ANSI E1.11), 250 kbit/s"],
            ["Conexión", "Bornera de entrada y bornera de salida en paralelo (encadenar), 3 polos: GND · D− · D+ (XLR 1 · 2 · 3)"],
            ["Terminación", "120 Ω con puente, solo en el último equipo de la línea"],
            ["Canales que usa", "4 consecutivos a partir de su dirección (1–509)"],
            ["Dirección", "Con el botón APRENDER (ver manual); se guarda aunque se apague"],
            ["Sin señal", "Mantiene el último valor; el LED lo indica"],
            ["Protección", "Contra descargas electrostáticas en la línea DMX"],
        ]],
        ["Indicador", [["LED verde", "Fijo: recibe DMX · un destello por segundo: sin señal · rápido: aprendiendo dirección"]]],
        ["Ambiente y mecánica", [
            ["Temperatura de operación", "−20 a +40 °C (caja de plástico) · −20 a +50 °C (aluminio)"],
            ["Humedad", "10–90 % sin condensación"],
            ["Protección", "IP20 (uso interior). Para exterior, dentro de una caja IP65"],
            ["Medidas", "Plástico 58 × 46 × 23 mm · aluminio 70 × 50 × 25 mm"],
            ["Bornas", "Potencia: 5.08 mm, cable de 0.5–2.5 mm² · DMX: 3.5 mm, cable de 0.2–1.5 mm²"],
        ]],
    ],
    "notas": ["Valores de diseño, preliminares hasta medir prototipos.",
              "Usar cable de par trenzado de 120 Ω para DMX (o cable de red categoría 5); hasta 32 nodos por línea sin repetidor."],
}

CURVA_CUBO = {   # del informe térmico (analisis/termico.py): % de carga continua contra temperatura ambiente
    "temperaturas": [25, 30, 35, 40, 45, 50, 55],
    "aluminio": {"12 V 5 A (60 W)": "12V 5A · aluminio", "24 V 3 A (72 W)": "24V 3A · aluminio"},
    "plastico_w": True,
}
