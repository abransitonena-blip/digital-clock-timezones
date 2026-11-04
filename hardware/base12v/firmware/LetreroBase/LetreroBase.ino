/*
  LetreroLab - Placa base 12 V (3 canales) - programa para Arduino Nano
  ----------------------------------------------------------------------
  Canales (MOSFET IRLZ44N, PWM):  CH1 = D9   CH2 = D10   CH3 = D11
  Boton MODO: A0 a GND (pads "MODO" de la placa, pull-up interno)
     - toque corto  : siguiente modo
     - mantener 1 s : cambia la velocidad (5 niveles)
  Bluetooth HC-05/HC-06 (opcional, 9600 baudios), enchufado en J3:  TXD -> A5,  RXD <- 1k <- A2
     (SoftwareSerial: D0/D1 quedan libres, se puede programar por USB con el HC-05 puesto)
     Comandos (una letra, desde cualquier app "Bluetooth Terminal" del celular):
       0..6  modo          +  /  -  velocidad        a..j  brillo 10 % .. 100 %
       ?     muestra el estado
  El modo, la velocidad y el brillo se guardan en la EEPROM (se recuerdan al desconectar).

  Modos:
    0  FIJO        los 3 canales encendidos
    1  SECUENCIA   1 -> 2 -> 3 -> 1 ... (flechas: 100, 010, 001)
    2  PARPADEO    los 3 juntos
    3  RESPIRAR    los 3 suben y bajan suave
    4  SEC. SUAVE  secuencia 1-2-3 con desvanecido
    5  ALTERNADO   1+3 / 2 (para flores o centros)
    6  COLOR RGB   ciclo de colores para una tira RGB de anodo comun (CH1=R, CH2=G, CH3=B)
*/
#include <SoftwareSerial.h>
#include <EEPROM.h>

const uint8_t CH[3] = {9, 10, 11};
const uint8_t PIN_BOTON = A0;
SoftwareSerial bt(A5, A2);  // RX (desde TXD del HC-05), TX (hacia RXD del HC-05)

const uint8_t N_MODOS = 7;
const uint16_t PASO_MS[5] = {1200, 900, 650, 450, 300};  // tiempo por paso segun la velocidad

uint8_t modo = 1;        // arranca en SECUENCIA (flechas)
uint8_t velocidad = 2;   // 0 = lento ... 4 = rapido
uint8_t brillo = 100;    // %

uint32_t t0 = 0;
uint8_t paso = 0;

void guardar() {
  EEPROM.update(0, 0xA5);
  EEPROM.update(1, modo);
  EEPROM.update(2, velocidad);
  EEPROM.update(3, brillo);
}

void cargar() {
  if (EEPROM.read(0) == 0xA5) {
    modo = EEPROM.read(1) % N_MODOS;
    velocidad = EEPROM.read(2) % 5;
    brillo = constrain(EEPROM.read(3), 10, 100);
  }
}

void salida(uint8_t c, uint8_t nivel) {            // nivel 0..255, se escala con el brillo
  analogWrite(CH[c], (uint16_t)nivel * brillo / 100);
}

void todos(uint8_t nivel) {
  for (uint8_t c = 0; c < 3; c++) salida(c, nivel);
}

uint8_t triangulo(uint32_t t, uint32_t periodo) {  // 0..255..0 en un periodo
  uint32_t f = t % periodo;
  uint32_t mitad = periodo / 2;
  return (f < mitad) ? (f * 255 / mitad) : ((periodo - f) * 255 / mitad);
}

void estado() {
  bt.print(F("modo=")); bt.print(modo);
  bt.print(F(" velocidad=")); bt.print(velocidad);
  bt.print(F(" brillo=")); bt.println(brillo);
}

void comando(char c) {
  if (c >= '0' && c < '0' + N_MODOS) { modo = c - '0'; paso = 0; t0 = millis(); }
  else if (c == '+' && velocidad < 4) velocidad++;
  else if (c == '-' && velocidad > 0) velocidad--;
  else if (c >= 'a' && c <= 'j') brillo = (c - 'a' + 1) * 10;
  else if (c == '?') { estado(); return; }
  else return;
  guardar();
  estado();
}

void leerBoton() {
  static bool antes = HIGH;
  static uint32_t tPresion = 0;
  static bool largo = false;
  bool ahora = digitalRead(PIN_BOTON);
  uint32_t t = millis();
  if (antes == HIGH && ahora == LOW) { tPresion = t; largo = false; }
  if (ahora == LOW && !largo && t - tPresion > 1000) {      // mantener 1 s: velocidad
    largo = true;
    velocidad = (velocidad + 1) % 5;
    guardar();
  }
  if (antes == LOW && ahora == HIGH && !largo && t - tPresion > 30) {  // toque corto: modo
    modo = (modo + 1) % N_MODOS;
    paso = 0; t0 = t;
    guardar();
  }
  antes = ahora;
}

void setup() {
  for (uint8_t c = 0; c < 3; c++) { pinMode(CH[c], OUTPUT); analogWrite(CH[c], 0); }
  pinMode(PIN_BOTON, INPUT_PULLUP);
  bt.begin(9600);
  cargar();
  t0 = millis();
}

void loop() {
  leerBoton();
  while (bt.available()) comando(bt.read());

  uint32_t t = millis();
  uint16_t T = PASO_MS[velocidad];

  switch (modo) {
    case 0:  // FIJO
      todos(255);
      break;

    case 1:  // SECUENCIA 100 / 010 / 001
      if (t - t0 >= T) { t0 = t; paso = (paso + 1) % 3; }
      for (uint8_t c = 0; c < 3; c++) salida(c, c == paso ? 255 : 0);
      break;

    case 2:  // PARPADEO
      if (t - t0 >= T) { t0 = t; paso ^= 1; }
      todos(paso ? 255 : 0);
      break;

    case 3:  // RESPIRAR
      todos(triangulo(t, 4UL * T));
      break;

    case 4: {  // SECUENCIA SUAVE: cada canal sube y baja desfasado
      uint32_t periodo = 3UL * T;
      for (uint8_t c = 0; c < 3; c++) {
        uint32_t fase = (t + periodo - (uint32_t)c * T) % periodo;
        uint8_t v = (fase < 2UL * T) ? triangulo(fase, 2UL * T) : 0;
        salida(c, v);
      }
      break;
    }

    case 5:  // ALTERNADO 1+3 / 2
      if (t - t0 >= T) { t0 = t; paso ^= 1; }
      salida(0, paso ? 255 : 0);
      salida(2, paso ? 255 : 0);
      salida(1, paso ? 0 : 255);
      break;

    case 6: {  // COLOR RGB: rueda de colores
      uint16_t h = (t / (T / 64 + 1)) % 768;   // 0..767
      uint8_t r, g, b;
      if (h < 256)      { r = 255 - h; g = h;         b = 0; }
      else if (h < 512) { r = 0;       g = 511 - h;   b = h - 256; }
      else              { r = h - 512; g = 0;         b = 767 - h; }
      salida(0, r); salida(1, g); salida(2, b);
      break;
    }
  }
}
