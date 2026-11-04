// Catálogo del sitio AP: tiras del mercado, líneas de producto, compatibilidad y proyectos.
// Consumos y medidas: valores típicos del mercado. Verifica siempre la ficha del fabricante de tu rollo.

export const TIRAS = [
  { id: '2835-60-12', nombre: 'SMD2835 · 60 LED/m · 12 V', tipo: 'MONO', v: 12, wm: 4.8, tramoMax: 5, uso: 'Letreros, cajas de luz, cocinas' },
  { id: '2835-120-12', nombre: 'SMD2835 · 120 LED/m · 12 V', tipo: 'MONO', v: 12, wm: 9.6, tramoMax: 5, uso: 'Iluminación lineal continua' },
  { id: '2835-120-24', nombre: 'SMD2835 · 120 LED/m · 24 V', tipo: 'MONO', v: 24, wm: 9.6, tramoMax: 10, uso: 'Tramos largos, fachadas' },
  { id: 'cob-320-24', nombre: 'COB · 320 LED/m · 24 V', tipo: 'MONO', v: 24, wm: 10, tramoMax: 10, uso: 'Luz sin puntos en perfil de aluminio' },
  { id: 'cob-12', nombre: 'COB · 12 V', tipo: 'MONO', v: 12, wm: 8, tramoMax: 5, uso: 'Repisas, vitrinas' },
  { id: 'neon-12', nombre: 'Neón flex · 12 V', tipo: 'MONO', v: 12, wm: 10, tramoMax: 5, uso: 'Letreros tipo neón' },
  { id: 'cct-24', nombre: 'Blanco dual CCT · 24 V', tipo: 'CCT', v: 24, wm: 12, tramoMax: 10, uso: 'Hogar, oficinas, alimentos' },
  { id: '5050-rgb-30-12', nombre: 'SMD5050 RGB · 30 LED/m · 12 V', tipo: 'RGB', v: 12, wm: 7.2, tramoMax: 5, uso: 'Decoración, ambientación' },
  { id: '5050-rgb-60-12', nombre: 'SMD5050 RGB · 60 LED/m · 12 V', tipo: 'RGB', v: 12, wm: 14.4, tramoMax: 5, uso: 'Decoración intensa' },
  { id: 'rgbcct-60-24', nombre: 'SMD5050 RGB + CCT · 60 LED/m · 24 V', tipo: 'RGBCCT', v: 24, wm: 19.2, tramoMax: 8, uso: 'Color + blanco cálido y frío (placa v2)' },
  { id: '5050-rgbw-60-24', nombre: 'SMD5050 RGBW · 60 LED/m · 24 V', tipo: 'RGBW', v: 24, wm: 18, tramoMax: 8, uso: 'Color + blanco real' },
  { id: 'ws2812b-30', nombre: 'WS2812B · 30 LED/m · 5 V', tipo: 'WS2812B', v: 5, wm: 9, tramoMax: 2, uso: 'Efectos, letreros animados' },
  { id: 'ws2812b-60', nombre: 'WS2812B · 60 LED/m · 5 V', tipo: 'WS2812B', v: 5, wm: 18, tramoMax: 1.5, uso: 'Efectos de alta resolución' },
  { id: 'sk6812-60', nombre: 'SK6812 RGBW · 60 LED/m · 5 V', tipo: 'SK6812', v: 5, wm: 20, tramoMax: 1.5, uso: 'Efectos con blanco puro' },
  { id: 'ws2811-12', nombre: 'WS2811 · 60 LED/m · 12 V', tipo: 'WS2811', v: 12, wm: 14.4, tramoMax: 5, uso: 'Fachadas animadas (3 LED por pixel)' },
  { id: 'ws2815-60', nombre: 'WS2815 · 60 LED/m · 12 V', tipo: 'WS2815', v: 12, wm: 14.4, tramoMax: 5, uso: 'Direccionable a 12 V con línea de respaldo' },
]

export const LINEAS = [
  {
    id: 'letreros', nombre: 'Letreros y anuncios', icono: '🪧',
    resumen: 'Cajas de luz, letras 3D y neón flex para comercios. Un cubo por letrero, encendido por horario.',
    tiras: ['SMD2835 12 V', 'Neón flex 12 V', 'WS2812B para animación'],
    config: 'Cartucho S o M · tarjeta 12V 1A–5A · horario 18:30–01:00',
    funciones: ['Horario diario sin internet', 'Bajar a 11.5 V para alargar la vida de la tira', 'Vuelve encendido tras un apagón'],
    ejemplo: { v: 12, a: 1, cantidad: 20, nombre: 'Letrero 60 × 40 cm' },
  },
  {
    id: 'arquitectura', nombre: 'Arquitectónico y fachadas', icono: '🏛️',
    resumen: 'Bañadores, cornisas y perfiles exteriores. Tramos largos a 24 V con caja IP67.',
    tiras: ['COB 24 V', 'SMD2835 24 V', 'WS2811 / WS2815 para animación'],
    config: 'Cartucho M o L · tarjeta 24V 2A–3A · cable 16–18 AWG',
    funciones: ['Escenas por horario', 'Medición de consumo por cubo', 'Varios cubos por fachada'],
    ejemplo: { v: 24, a: 2, cantidad: 6, nombre: 'Cornisa 10 m' },
  },
  {
    id: 'hogar', nombre: 'Hogar inteligente', icono: '🏠',
    resumen: 'Cocinas, plafones y cabeceras con blanco cálido a frío y control por voz.',
    tiras: ['Blanco dual CCT 24 V', 'RGBW 24 V', 'COB 12 V'],
    config: 'Cartucho S o M · tarjeta 24V 2A · Wi-Fi + integraciones',
    funciones: ['Alexa local', 'Home Assistant (vía WLED)', 'Temperatura de blanco 2700–6500 K'],
    ejemplo: { v: 24, a: 1.5, cantidad: 3, nombre: 'Cocina' },
  },
  {
    id: 'comercio', nombre: 'Comercio y exhibidores', icono: '🛍️',
    resumen: 'Vitrinas, repisas y refrigeradores. Blanco correcto para cada producto.',
    tiras: ['COB 12 V', 'Blanco dual CCT', 'SMD2835 120 LED/m'],
    config: 'Cartucho S · tarjeta 12V 1A–2A',
    funciones: ['CCT cálido para pan y carne, frío para joyería', 'Horario de tienda', 'Bajo consumo medido'],
    ejemplo: { v: 12, a: 2, cantidad: 8, nombre: 'Vitrina' },
  },
  {
    id: 'eventos', nombre: 'Eventos y escenarios', icono: '🎉',
    resumen: 'Barras, cabinas de DJ y backdrops con efectos direccionables listos para usar.',
    tiras: ['WS2812B 5 V', 'SK6812 RGBW', 'WS2815 12 V'],
    config: 'Tarjeta 5V 3A o 12V 5A · varios cubos sincronizados por Wi-Fi (WLED)',
    funciones: ['Art-Net y sACN para consolas y xLights', 'Efectos arcoíris, fuego y cometa', '8 escenas guardadas'],
    ejemplo: { v: 5, a: 3, cantidad: 4, nombre: 'Barra 2 m' },
  },
  {
    id: 'solar', nombre: 'Solar y fuera de red', icono: '☀️',
    resumen: 'Ranchos, bodegas y anuncios en carretera con batería de 12 o 24 V. Sin cartucho: la placa acepta 12–36 V.',
    tiras: ['SMD2835 12 V (con batería de 24 V)', 'WS2812B 5 V', 'COB 12 V'],
    config: 'Entrada directa de batería LiFePO4 24 V · tarjeta 12V · horario',
    funciones: ['Protección contra polaridad invertida', 'Lectura del voltaje de batería', 'Horario para cuidar la carga'],
    ejemplo: { v: 12, a: 2, cantidad: 2, nombre: 'Anuncio solar' },
  },
  {
    id: 'vehiculos', nombre: 'Vehículos y náutico', icono: '🚚',
    resumen: 'Camiones y lanchas con sistema de 24 V. En autos de 12 V solo sirve para tiras de 5 V (el reductor necesita Vin ≥ Vout + 1.2 V).',
    tiras: ['WS2812B 5 V', 'SMD2835 12 V (solo con 24 V)'],
    config: 'Entrada 24 V del vehículo · tarjeta 12V o 5V · fusible en la línea',
    funciones: ['Arranque suave', 'Recorte térmico', 'Control por Bluetooth sin internet'],
    ejemplo: { v: 12, a: 3, cantidad: 1, nombre: 'Caja de tráiler' },
  },
]

// Compatibilidad: estado 'si' | 'parcial' | 'plan' | 'no'
export const COMPAT = [
  { grupo: 'Tiras analógicas', items: [
    ['Un color (12/24 V)', 'si', 'Salida W, hasta 5 A'],
    ['RGB 5050', 'si', 'Salidas R, G, B'],
    ['RGBW / RGBWW 4 en 1', 'si', 'Salidas R, G, B, W'],
    ['Blanco dual CCT', 'si', 'Cálido en R, frío en G; 2700–6500 K'],
    ['RGB + CCT (5 canales)', 'si', 'Placa v2: blanco cálido en W y frío en el 5.º canal'],
  ] },
  { grupo: 'Tiras direccionables', items: [
    ['WS2812B / WS2813 (5 V, GRB)', 'si', 'Hasta 600 LED; tarjeta de 5 V'],
    ['SK6812 RGBW (5 V)', 'si', 'Orden GRBW'],
    ['WS2811 (12 V)', 'si', 'Orden RGB; tarjeta de 12 V'],
    ['WS2815 (12 V)', 'si', 'Orden GRB; tarjeta de 12 V'],
    ['APA102 / SK9822 (datos + reloj)', 'no', 'Necesitan 2 líneas; la v1 tiene 1'],
  ] },
  { grupo: 'Control e integraciones', items: [
    ['App web por Bluetooth (Android, Windows, macOS, ChromeOS)', 'si', 'Chrome o Edge; PIN de 6 dígitos'],
    ['iPhone / iPad', 'parcial', 'Safari no tiene Bluetooth web: usa Wi-Fi (página del cubo) o la app Bluefy'],
    ['Página de control por Wi-Fi (cuboap-xxxx.local)', 'si', 'La sirve el propio cubo; pide el PIN'],
    ['App WLED y API JSON /json/state', 'parcial', 'Encendido, brillo y color; sin segmentos ni paletas'],
    ['Home Assistant', 'parcial', 'Con la integración WLED (descubrimiento mDNS)'],
    ['Amazon Alexa', 'parcial', 'Local, sin skill (emulación Hue): encender, apagar y brillo'],
    ['Google Home / Apple Home', 'parcial', 'A través de Home Assistant (Nabu Casa o HomeKit Bridge)'],
    ['Matter (Wi-Fi)', 'plan', 'El ESP32-C3 lo permite; requiere migrar el firmware a ESP-IDF'],
    ['Actualización por Wi-Fi (OTA)', 'si', 'Desde la página del cubo, con PIN'],
    ['DMX por red: Art-Net y sACN / E1.31', 'parcial', 'Consolas, xLights, QLC+, Resolume, MadMapper; probado con paquetes de prueba, falta con consola real'],
    ['DMX512 por cable', 'parcial', 'Placa v2: RS-485 con protección y terminación; bornera GND·D−·D+. Falta probar con consola'],
    ['Tuya / Smart Life', 'no', 'Ecosistema cerrado en la nube'],
  ] },
  { grupo: 'Energía', items: [
    ['Cartucho AC 127 V → 24 V (S 25 W, M 40 W, L 75 W)', 'si', 'Usa módulos certificados de fabricante'],
    ['Batería 12/24 V (plomo, LiFePO4)', 'si', 'Entrada 12–36 V con protección de polaridad'],
    ['Fuente de laptop 19–20 V', 'si', 'Para salidas de hasta ~18 V'],
    ['USB-C PD 20 V con módulo disparador', 'parcial', 'Hasta 60–100 W según el cargador; probar antes'],
    ['Sistema de auto 12 V', 'parcial', 'Solo salidas de 5 V'],
  ] },
]

export const PROYECTOS = [
  {
    id: 'cubo', nombre: 'Cubo AP · módulo LED inteligente', estado: 'Diseño completo, sin fabricar',
    img: 'img/cubo_render_explotado.jpg',
    texto: 'Caja IP67 de 80 mm con cartucho de potencia, tarjeta de configuración, ESP32-C3, Bluetooth, Wi-Fi y 4 canales de 5 A.',
    docs: [['Sistema (PDF)', 'docs/cubo_ap_sistema.pdf']],
  },
  {
    id: 'placa', nombre: 'Placa de control 68 × 64 mm', estado: 'Gerber listos, sin fabricar',
    img: 'img/placa_control_arriba.jpg',
    texto: 'TPS54560 5 A, INA226, DAC, 2 × UCC27524 + 4 MOSFET, 74AHCT1G125. 2 capas, DRC sin errores.',
    docs: [['Esquema (PDF)', 'docs/esquema_placa_control.pdf'], ['Gerber (ZIP)', 'docs/cubo_ap_control_gerbers.zip'], ['BOM (CSV)', 'docs/bom.csv']],
  },
  {
    id: 'placa2', nombre: 'Placa de control v2 · DMX + 5 canales', estado: 'Gerber listos, sin fabricar',
    img: 'img/placa_control_v2_arriba.jpg',
    texto: 'Todo lo de la v1 más DMX512 por cable (RS-485 con TVS y terminación) y 5.º canal para tiras RGB+CCT. DRC sin errores.',
    docs: [['Esquema v2 (PDF)', 'docs/esquema_placa_control_v2.pdf'], ['BOM v2 (CSV)', 'docs/bom_v2.csv']],
  },
  {
    id: 'fuente127', nombre: 'Fuente universal 127 V (flyback)', estado: 'Diseño para planchar, sin probar',
    img: 'img/fuente127_vista_montaje.jpg',
    texto: 'Flyback UC3844 tipo cargador + LM2596-ADJ: de 127 V a 1.2–20 V 2 A en una sola placa.',
    docs: [['Manual (PDF)', 'docs/manual_fuente_universal_127v.pdf']],
  },
  {
    id: 'modulo', nombre: 'Módulo universal ajustable', estado: 'Diseño para planchar',
    img: 'img/manual_modulo_universal.jpg',
    texto: 'LM2596S-ADJ con trimpot multivuelta: 1.2–24 V a 2 A, entrada 8–35 V DC o 6–22 V~ sin polaridad.',
    docs: [['Manual (PDF)', 'docs/manual_modulo_universal.pdf']],
  },
  {
    id: 'regulador', nombre: 'Regulador 12 V 2 A SMD', estado: 'Diseño para planchar',
    img: 'img/manual_regulador_12v_2a.jpg',
    texto: 'LM2596S-12 en 50 × 44 mm: tiras de 12 V desde 16–35 V DC, con protección de polaridad.',
    docs: [['Manual (PDF)', 'docs/manual_regulador_12v_2a.pdf']],
  },
  {
    id: 'fuente17', nombre: 'Fuente 12 V 1.7 A desde 127 V', estado: 'Diseño para planchar',
    img: 'img/manual_fuente_12v_1.7a.jpg',
    texto: 'Transformador 127 V → 18 V, puente y filtro en placa, LM2596S-12: 12 V 1.7 A en 72 × 50 mm.',
    docs: [['Manual (PDF)', 'docs/manual_fuente_12v_1.7a.pdf']],
  },
  {
    id: '5x5', nombre: 'Fuente capacitiva 2 canales 5 × 5 cm', estado: 'Construida: 1 canal funciona',
    img: 'img/manual_montaje_5x5_v9.jpg',
    texto: 'Fuente capacitiva para LEDs a 127 V en placa de una cara; versión v9 con serigrafía fiel a los componentes.',
    docs: [['Montaje v9 (PDF)', 'docs/manual_montaje_5x5_v9.pdf'], ['Diagnóstico (PDF)', 'docs/diagnostico_canal_5x5_v9.pdf']],
  },
]

export const DOCS_REFERENCIA = [
  ['Base de datos de capacitores para LEDs', 'docs/base_datos_capacitores_led.pdf'],
  ['Fichas de componentes', 'docs/fichas_componentes.pdf'],
]
