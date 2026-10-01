/*
  LetreroLab AP-0.1  -  programa del CABEZAL (ATmega328P a 16 MHz, compatible con "Arduino Nano/Uno")
  ------------------------------------------------------------------------------------------------
  Controla la placa de POTENCIA por el conector de 8 hilos:
     PWM1..PWM4 -> 4 canales MOSFET (letrero por secciones, o tira RGB / RGBW de anodo comun)
     AUX        -> relevador (contacto seco) para focos normales de 127/240 V
  Control:
     - App LetreroLab (Bluetooth BLE HM-10/AT-09/JDY-23) o adaptador USB-serie: puerto serie D0/D1 a 9600
     - Boton MODO (toque = modo siguiente, 1 s = velocidad, 3 s = encender/apagar)
     - Control remoto infrarrojo de tiras RGB (NEC, el de 24 teclas)
     - Reloj DS3231 opcional (I2C): horario de encendido/apagado, aunque se vaya la luz
     - Sensor de luz (LDR) opcional: encender solo de noche
  Todo se guarda en la EEPROM.

  Protocolo (una linea por orden, termina en \n; tambien acepta las letras sueltas del programa anterior):
     M n          modo 0..9                         V n      velocidad 0..9
     B n          brillo 0..100 %                   C r g b w  color 0..255 (modos de color)
     N n          canales usados 1..4 (3 = flechas, 4 = RGBW)
     P 0|1        apagar / encender todo            X 0|1    relevador (focos) apagado / encendido
     H hh:mm hh:mm  horario encender / apagar       H -      sin horario
     T aaaa-mm-dd hh:mm:ss   poner el reloj         L 0|1 [umbral 0..1023]  solo de noche con LDR
     E 0|1        modo ahorro (brillo maximo 60 %)  S n / R n  guardar / cargar escena 0..3
     ?            estado en JSON                    I        informacion del equipo
*/
#include <EEPROM.h>
#include <Wire.h>

// ---------------- pines del cabezal AP-0.1 ----------------
const uint8_t PWM_PIN[4] = {11, 10, 9, 6};   // PWM1..PWM4 (D11, D10, D9, D6)
const uint8_t PIN_AUX = 12;                  // relevador
const uint8_t PIN_MODO = A1;                 // boton a GND (J4)
const uint8_t PIN_IR = A2;                   // receptor IR (J7), interrupcion por cambio de pin
const uint8_t PIN_LED = A3;                  // LED de estado
const uint8_t PIN_LDR = A0;                  // LDR a GND (J8, pull-up interno)
// Bluetooth BLE en el puerto serie del chip (D0 <- TXD del modulo, D1 -> divisor -> RXD del modulo), 9600 baudios.
// Para programar: quitar el modulo y conectar el adaptador USB-serie (GND, TX, RX en los pines del modulo; DTR en J2).

#define VERSION "AP-0.1 fw 1.0"
const uint8_t N_MODOS = 10;
const char* const NOMBRE[N_MODOS] = {"FIJO", "SECUENCIA", "PARPADEO", "RESPIRAR", "SEC. SUAVE", "ALTERNADO",
                                     "COLOR", "ARCOIRIS", "FLASH", "VELA"};

struct Config {
  uint8_t firma, modo, vel, brillo, canales, encendido, aux, eco, ldr;
  uint8_t color[4];
  int16_t horaOn, horaOff;     // minutos del dia; -1 = sin horario
  int16_t umbral;           // 0..1023 (LDR: mas alto = mas oscuro)
};
Config cfg;
const Config DEF = {0xA7, 1, 4, 100, 3, 1, 0, 0, 0, {255, 120, 0, 0}, -1, -1, 600};

uint32_t t0 = 0;
uint8_t paso = 0;
bool hayRTC = false;
bool porHorario = true, porLuz = true;   // permisos calculados

// ---------------- memoria ----------------
void guardar() { EEPROM.put(0, cfg); }
void cargar() {
  EEPROM.get(0, cfg);
  if (cfg.firma != 0xA7 || cfg.modo >= N_MODOS) cfg = DEF;
}
void guardarEscena(uint8_t n) { if (n < 4) EEPROM.put(64 + n * sizeof(Config), cfg); }
void cargarEscena(uint8_t n) {
  if (n >= 4) return;
  Config e;
  EEPROM.get(64 + n * sizeof(Config), e);
  if (e.firma == 0xA7 && e.modo < N_MODOS) { cfg = e; guardar(); }
}

// ---------------- salidas ----------------
const uint8_t GAMMA[17] = {0, 1, 2, 4, 7, 11, 17, 25, 35, 47, 62, 80, 101, 126, 155, 187, 255};
uint8_t gamma8(uint8_t v) {               // correccion de brillo para que el desvanecido se vea parejo
  uint8_t i = v >> 4, f = v & 15;
  return GAMMA[i] + (uint16_t)(GAMMA[i + 1] - GAMMA[i]) * f / 16;
}
void salida(uint8_t c, uint8_t nivel) {
  uint8_t maxb = cfg.eco ? (cfg.brillo < 60 ? cfg.brillo : 60) : cfg.brillo;
  analogWrite(PWM_PIN[c], gamma8((uint16_t)nivel * maxb / 100));
}
void todos(uint8_t v) { for (uint8_t c = 0; c < cfg.canales; c++) salida(c, v); }
void apagarTodo() { for (uint8_t c = 0; c < 4; c++) analogWrite(PWM_PIN[c], 0); }

uint8_t triangulo(uint32_t t, uint32_t per) {
  uint32_t f = t % per, m = per / 2;
  return f < m ? f * 255 / m : (per - f) * 255 / m;
}
void rueda(uint16_t h, uint8_t* r, uint8_t* g, uint8_t* b) {   // h 0..767
  if (h < 256) { *r = 255 - h; *g = h; *b = 0; }
  else if (h < 512) { h -= 256; *r = 0; *g = 255 - h; *b = h; }
  else { h -= 512; *r = h; *g = 0; *b = 255 - h; }
}

// ---------------- reloj DS3231 ----------------
uint8_t bcd2(uint8_t v) { return (v >> 4) * 10 + (v & 15); }
uint8_t aBcd(uint8_t v) { return ((v / 10) << 4) | (v % 10); }
int16_t minutosRTC() {                    // -1 si no hay reloj
  if (!hayRTC) return -1;
  Wire.beginTransmission(0x68); Wire.write(1);
  if (Wire.endTransmission() != 0) return -1;
  Wire.requestFrom(0x68, 2);
  if (Wire.available() < 2) return -1;
  uint8_t mi = bcd2(Wire.read()), h = bcd2(Wire.read() & 0x3F);
  return h * 60 + mi;
}
void ponerRTC(int an, int me, int di, int h, int mi, int s) {
  Wire.beginTransmission(0x68); Wire.write(0);
  Wire.write(aBcd(s)); Wire.write(aBcd(mi)); Wire.write(aBcd(h)); Wire.write(1);
  Wire.write(aBcd(di)); Wire.write(aBcd(me)); Wire.write(aBcd(an % 100));
  Wire.endTransmission();
}

// ---------------- control remoto IR (NEC) ----------------
volatile uint32_t irCodigo = 0, irBits = 0;
volatile uint32_t irUlt = 0;
volatile uint8_t irN = 0;
volatile bool irListo = false;
void irISR();
ISR(PCINT1_vect) {                        // A2 = PC2: solo flancos de bajada
  if (!(PINC & _BV(2))) irISR();
}
void irISR() {                            // mide el tiempo entre flancos de bajada
  uint32_t t = micros(), d = t - irUlt;
  irUlt = t;
  if (d > 12000) { irN = 0; return; }                 // silencio: inicio
  if (d > 10000) { irN = 1; irBits = 0; return; }     // 13.5 ms = encabezado
  if (d > 8000 && irN == 0) { irListo = true; irCodigo = 0xFFFFFFFF; return; }   // 11.25 ms = repetir
  if (irN == 0) return;
  irBits = (irBits << 1) | (d > 1700 ? 1 : 0);        // 2.25 ms = 1, 1.12 ms = 0
  if (++irN > 32) { irCodigo = irBits; irListo = true; irN = 0; }
}

// ---------------- comandos ----------------
Stream* resp = &Serial;
char linea[40];
uint8_t nl = 0;

void estado() {
  int16_t m = minutosRTC();
  resp->print(F("{\"v\":\"" VERSION "\",\"p\":")); resp->print(cfg.encendido);
  resp->print(F(",\"m\":")); resp->print(cfg.modo);
  resp->print(F(",\"n\":\"")); resp->print(NOMBRE[cfg.modo]);
  resp->print(F("\",\"s\":")); resp->print(cfg.vel);
  resp->print(F(",\"b\":")); resp->print(cfg.brillo);
  resp->print(F(",\"ch\":")); resp->print(cfg.canales);
  resp->print(F(",\"c\":[")); for (uint8_t i = 0; i < 4; i++) { resp->print(cfg.color[i]); if (i < 3) resp->print(','); }
  resp->print(F("],\"x\":")); resp->print(cfg.aux);
  resp->print(F(",\"e\":")); resp->print(cfg.eco);
  resp->print(F(",\"l\":")); resp->print(cfg.ldr);
  resp->print(F(",\"lv\":")); resp->print(analogRead(PIN_LDR));
  resp->print(F(",\"u\":")); resp->print(cfg.umbral);
  resp->print(F(",\"on\":")); resp->print(cfg.horaOn);
  resp->print(F(",\"off\":")); resp->print(cfg.horaOff);
  resp->print(F(",\"t\":")); resp->print(m);
  resp->println('}');
}

int numero(const char*& p) {
  while (*p == ' ') p++;
  int v = 0; bool neg = false;
  if (*p == '-') { neg = true; p++; }
  while (*p >= '0' && *p <= '9') v = v * 10 + (*p++ - '0');
  if (*p == ':' || *p == '-' || *p == ',') p++;
  return neg ? -v : v;
}

void ejecutar(const char* s) {
  const char* p = s + 1;
  char c = s[0];
  if (c >= 'a' && c <= 'z' && s[1] == 0 && c != 'i') { if (c <= 'j') cfg.brillo = (c - 'a' + 1) * 10; }   // letras sueltas
  else if (c >= '0' && c <= '9' && s[1] == 0) { cfg.modo = c - '0'; paso = 0; }
  else if (c == '+' && s[1] == 0) { if (cfg.vel < 9) cfg.vel++; }
  else if (c == '-' && s[1] == 0) { if (cfg.vel > 0) cfg.vel--; }
  else switch (c) {
    case 'M': { int v = numero(p); if (v >= 0 && v < N_MODOS) { cfg.modo = v; paso = 0; } } break;
    case 'V': cfg.vel = constrain(numero(p), 0, 9); break;
    case 'B': cfg.brillo = constrain(numero(p), 0, 100); break;
    case 'C': for (uint8_t i = 0; i < 4; i++) cfg.color[i] = constrain(numero(p), 0, 255); break;
    case 'N': cfg.canales = constrain(numero(p), 1, 4); apagarTodo(); break;
    case 'P': cfg.encendido = numero(p) ? 1 : 0; break;
    case 'X': cfg.aux = numero(p) ? 1 : 0; break;
    case 'E': cfg.eco = numero(p) ? 1 : 0; break;
    case 'L': cfg.ldr = numero(p) ? 1 : 0; { int u = numero(p); if (u > 0) cfg.umbral = u; } break;
    case 'H':
      while (*p == ' ') p++;
      if (*p == '-') { cfg.horaOn = cfg.horaOff = -1; }
      else { int a = numero(p), b = numero(p), c2 = numero(p), d = numero(p); cfg.horaOn = a * 60 + b; cfg.horaOff = c2 * 60 + d; }
      break;
    case 'T': { int an = numero(p), me = numero(p), di = numero(p), h = numero(p), mi = numero(p), se = numero(p);
                ponerRTC(an, me, di, h, mi, se); hayRTC = true; } break;
    case 'S': guardarEscena(numero(p)); break;
    case 'R': cargarEscena(numero(p)); break;
    case 'I': resp->println(F(VERSION " - LetreroLab, 4 canales PWM + relevador")); return;
    case '?': estado(); return;
    default: return;
  }
  guardar();
  estado();
}

void leer(Stream& s) {
  while (s.available()) {
    char ch = s.read();
    resp = &s;
    if (ch == '\n' || ch == '\r') {
      if (nl) { linea[nl] = 0; ejecutar(linea); nl = 0; }
    } else if (nl < sizeof(linea) - 1) {
      linea[nl++] = ch;
    }
  }
}

// ---------------- boton ----------------
void leerBoton() {
  static bool antes = HIGH;
  static uint32_t tP = 0;
  static uint8_t largo = 0;
  bool ahora = digitalRead(PIN_MODO);
  uint32_t t = millis();
  if (antes == HIGH && ahora == LOW) { tP = t; largo = 0; }
  if (ahora == LOW && largo == 0 && t - tP > 1000) { largo = 1; cfg.vel = (cfg.vel + 2) % 10; guardar(); }
  if (ahora == LOW && largo == 1 && t - tP > 3000) { largo = 2; cfg.encendido ^= 1; guardar(); }
  if (antes == LOW && ahora == HIGH && largo == 0 && t - tP > 30) { cfg.modo = (cfg.modo + 1) % N_MODOS; paso = 0; guardar(); }
  antes = ahora;
}

// ---------------- control remoto: teclas del control de 24 botones ----------------
void teclaIR(uint32_t k) {
  static uint32_t ultima = 0;
  if (k == 0xFFFFFFFF) k = ultima; else ultima = k;    // tecla sostenida
  uint8_t* col = cfg.color;
  switch (k) {
    case 0xF7C03F: cfg.encendido = 1; break;                      // ON
    case 0xF740BF: cfg.encendido = 0; break;                      // OFF
    case 0xF700FF: cfg.brillo = min(100, cfg.brillo + 10); break; // brillo +
    case 0xF7807F: cfg.brillo = max(10, cfg.brillo - 10); break;  // brillo -
    case 0xF720DF: cfg.modo = 6; col[0] = 255; col[1] = 0; col[2] = 0; col[3] = 0; break;     // R
    case 0xF7A05F: cfg.modo = 6; col[0] = 0; col[1] = 255; col[2] = 0; col[3] = 0; break;     // G
    case 0xF7609F: cfg.modo = 6; col[0] = 0; col[1] = 0; col[2] = 255; col[3] = 0; break;     // B
    case 0xF7E01F: cfg.modo = 6; col[0] = 255; col[1] = 255; col[2] = 255; col[3] = 255; break; // W
    case 0xF7D02F: cfg.modo = 8; break;                           // FLASH
    case 0xF7F00F: cfg.modo = 2; break;                           // STROBE -> parpadeo
    case 0xF7C837: cfg.modo = 4; break;                           // FADE
    case 0xF7E817: cfg.modo = 7; break;                           // SMOOTH -> arcoiris
    default: Serial.print(F("IR desconocido: ")); Serial.println(k, HEX); return;
  }
  guardar();
}

// ---------------- efectos ----------------
void efectos(uint32_t t) {
  uint16_t T = 1500 - cfg.vel * 140;          // ms por paso (1500 .. 240)
  uint8_t n = cfg.canales;
  switch (cfg.modo) {
    case 0: todos(255); break;                                                 // FIJO
    case 1: if (t - t0 >= T) { t0 = t; paso = (paso + 1) % n; }                // SECUENCIA 100/010/001
            for (uint8_t c = 0; c < n; c++) salida(c, c == paso ? 255 : 0); break;
    case 2: if (t - t0 >= T) { t0 = t; paso ^= 1; } todos(paso ? 255 : 0); break;   // PARPADEO
    case 3: todos(triangulo(t, 4UL * T)); break;                               // RESPIRAR
    case 4: { uint32_t per = (uint32_t)n * T;                                  // SECUENCIA SUAVE
              for (uint8_t c = 0; c < n; c++) {
                uint32_t f = (t + per - (uint32_t)c * T) % per;
                salida(c, f < 2UL * T ? triangulo(f, 2UL * T) : 0);
              } } break;
    case 5: if (t - t0 >= T) { t0 = t; paso ^= 1; }                            // ALTERNADO
            for (uint8_t c = 0; c < n; c++) salida(c, ((c & 1) ^ paso) ? 255 : 0); break;
    case 6: for (uint8_t c = 0; c < n; c++) salida(c, cfg.color[c]); break;     // COLOR fijo (RGBW)
    case 7: { uint8_t r, g, b; rueda((t / (T / 64 + 1)) % 768, &r, &g, &b);     // ARCOIRIS
              salida(0, r); if (n > 1) salida(1, g); if (n > 2) salida(2, b); if (n > 3) salida(3, 0); } break;
    case 8: { uint32_t f = t % (2UL * T); todos(f < 60 || (f > 180 && f < 240) ? 255 : 0); } break;   // FLASH doble
    case 9: { static uint8_t v = 200; if (t - t0 > 60) { t0 = t; v = 150 + (random(0, 106)); }       // VELA
              for (uint8_t c = 0; c < n; c++) salida(c, (uint16_t)v * cfg.color[c] / 255); } break;
  }
}

bool dentroHorario(int16_t m) {
  if (cfg.horaOn < 0 || m < 0) return true;
  if (cfg.horaOn <= cfg.horaOff) return m >= cfg.horaOn && m < cfg.horaOff;
  return m >= cfg.horaOn || m < cfg.horaOff;          // cruza la medianoche (p. ej. 19:00 a 02:00)
}

void setup() {
  for (uint8_t c = 0; c < 4; c++) { pinMode(PWM_PIN[c], OUTPUT); analogWrite(PWM_PIN[c], 0); }
  pinMode(PIN_AUX, OUTPUT); digitalWrite(PIN_AUX, LOW);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_MODO, INPUT_PULLUP);
  pinMode(PIN_IR, INPUT_PULLUP);
  pinMode(PIN_LDR, INPUT_PULLUP);
  Serial.begin(9600);
  Wire.begin();
  Wire.beginTransmission(0x68);
  hayRTC = (Wire.endTransmission() == 0);
  cargar();
  randomSeed(analogRead(A6));
  PCICR |= _BV(PCIE1);                       // interrupcion por cambio en A2 (PCINT10)
  PCMSK1 |= _BV(PCINT10);
  Serial.println(F(VERSION));
}

void loop() {
  uint32_t t = millis();
  leer(Serial);
  leerBoton();
  if (irListo) { irListo = false; teclaIR(irCodigo); }

  static uint32_t tRevisa = 0;                 // horario y luz: cada 2 s
  if (t - tRevisa > 2000) {
    tRevisa = t;
    porHorario = dentroHorario(minutosRTC());
    if (cfg.ldr) {                             // con histeresis para que no parpadee al amanecer
      int l = analogRead(PIN_LDR);             // mas alto = mas oscuro (LDR a GND con pull-up)
      if (l > cfg.umbral + 40) porLuz = true;
      else if (l < cfg.umbral - 40) porLuz = false;
    } else porLuz = true;
  }
  bool activo = cfg.encendido && porHorario && porLuz;
  digitalWrite(PIN_AUX, (activo && cfg.aux) ? HIGH : LOW);
  digitalWrite(PIN_LED, (t / (activo ? 1000 : 250)) & 1);    // late lento = encendido, rapido = en pausa
  if (activo) efectos(t); else apagarTodo();
}
