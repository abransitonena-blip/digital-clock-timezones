/*
  LetreroLab AP-1  -  programa del PROGRAMADOR (ESP32-C3-WROOM-02; Arduino-ESP32 3.x, placa "ESP32C3 Dev Module",
                      "USB CDC On Boot: Enabled", particiones "Minimal SPIFFS")
  -------------------------------------------------------------------------------------------------
  El programador se enclava sobre la BASE universal AP-1 y la maneja por el conector 2x8:
     4 canales de 8 A (IO4..IO7, PWM 12 bits a 19.5 kHz, desfasados), 2 canales de corriente constante para focos
     (AL8860, IO10 e IO0, PWM a 1 kHz), salida AUX 12 V (IO1), y el bus I2C de la base:
     INA238 0x40 (V, A, W), TMP1075 0x48 (temperatura), EEPROM 0x50 (modelo, calibración, serie, horas; M24C02 o AT24CS02).
  Conector Qwiic (opcional): pantalla OLED SSD1306 0x3C, sensor de luz BH1750 0x23, reloj DS3231 0x68.

  Diagnóstico de salidas: "DIAG" prueba cada salida por turno con el medidor de precisión de la base (primero al 5 %
  para descubrir un corto sin riesgo, luego al 100 %) y la califica: OK, sin carga, corto, baja (tramo fundido) o alta.
  "APRENDER" guarda en la base el consumo normal de cada salida; desde entonces la comparación es contra ese valor y,
  en modo fijo o color, el equipo avisa si el consumo total se aleja más de 25 % de lo esperado.

  Protocolo (una línea por orden; también por /api?c=... y MQTT):
     M n  modo 0..9         V n  velocidad 0..9      B n  brillo 0..100     C r g b w  color 0..255
     N n  canales 1..4      P 0|1 todo apagado/encendido                   X 0|1 salida AUX (relevador/contactor)
     O a b  focos de corriente constante 1 y 2: 0..100 %                   Y 0|1 AUX manual / ventilador por temperatura
     E 0|1 ahorro (máx 60%) L 0|1 [lux] solo de noche (sensor de luz Qwiic) S n / R n  guardar/cargar escena 0..3
     H hh:mm hh:mm  ventana diaria encendido   H -  sin ventana
     A i dias hh:mm acc val  horario i=0..7, dias=suma(1=dom,2=lun,4=mar..64=sab; 127=todos),
                             acc 0=apagar 1=encender 2=AUX(val 0/1) 3=escena val 4=brillo val     A i -  borrar
     T aaaa-mm-dd hh:mm:ss  poner hora     Z tz  zona horaria POSIX (p. ej. CST6 = centro de México)
     D nombre   nombre del equipo (y nombre.local)        G grupo   grupo (p. ej. planta-alta)
     W red,clave  conectar a Wi-Fi     W -  olvidar Wi-Fi  Q uri[,usuario,clave]  MQTT   Q -  sin MQTT
     K clave  clave de la app/OTA (vacío = sin clave)      @ grupo orden  enviar a un grupo (* = todos)
     J n  límite de corriente total 1..25 A (protección)   F 0  borrar una falla     U 0  reiniciar el contador de kWh
     DIAG  probar salidas     APRENDER  probar y guardar el consumo normal     MODELO texto  modelo de la base
     Módulo IND (0-10 V): canales 1-4 = salidas 0-10 V, contactor 1 sigue al encendido, O 100 / O 0 = contactor 2
     Módulo PIX: PX a b c d  LED por salida (0-600)   PS n  segmentos o letras (0 = una por salida)
                 PO n  orden de color 0 GRB, 1 RGB, 2 BRG; C r g b = color de los efectos; J = límite de corriente
     Módulo DMX: PD dir canales  dirección del primer equipo y canales (1, 3 o 4)   PX n  equipos
     VIVO 0|1  control en vivo por Art-Net / sACN (xLights, QLC+, Jinx!)   UNI n  universo inicial
     AP OUTPUT / AP INPUT (Qwiic): SA n 0|1|2  salida n (1-28) apagar/encender/alternar
                 EA n acc val [modo]  regla de la entrada n (1-32): acc como en los horarios; modo 1 = al soltar, lo contrario
                 EA n -  sin regla.  Acciones: 0 apagar 1 encender 2 AUX 3 escena 4 brillo 5/6/7 salida val on/off/alternar 8 alternar luz
     HA 0|1  aparecer en Home Assistant por MQTT (descubrimiento automático; 1 por omisión)
     ?  estado JSON     I  información     !  reiniciar
*/
#include <WiFi.h>
#include <WebServer.h>
#include <DNSServer.h>
#include <ESPmDNS.h>
#include <NetworkUdp.h>
#include <ArduinoOTA.h>
#include <Update.h>
#include <Preferences.h>
#include <Wire.h>
#include <time.h>
#include <sys/time.h>
#include "mqtt_client.h"
#include "esp_crt_bundle.h"
#include "driver/ledc.h"
#include "pagina.h"

#define VERSION "AP-1 fw 1.5"

// ---------------- pines del programador AP-1 ----------------
const uint8_t PWM_PIN[4] = {4, 5, 6, 7};   // CH1..CH4 de la base (drivers UCC27524 -> MOSFET); pull-down de 10k
const uint8_t CC_PIN[2] = {10, 0};         // CTRL de los AL8860 (corriente constante); pull-down de 2.2k en la base
const uint8_t PIN_AUX = 1;                 // AO3400 de la base: relevador, contactor o ventilador externo
const uint8_t PIN_MODO = 9;                // botón BOOT/MODO (a GND) y J4-4
const uint8_t PIN_IR = 3;                  // receptor IR TSOP382 y J4-3
const uint8_t PIN_LED = 21;                // LED verde (IO21: su registro de arranque solo lo hace parpadear)
const uint8_t PIN_SDA = 2, PIN_SCL = 8;    // I2C de la base y del conector Qwiic
const uint8_t PIN_ALERTA = 20;             // ALERT del INA238 y del TMP1075 (colector abierto, activa en bajo)
const float R_SHUNT = 0.001f;              // RS1 = 1 mOhm
const uint32_t PWM_HZ = 19531;             // 80 MHz / 4096
const uint8_t PWM_BITS = 12;
const uint16_t UDP_PUERTO = 4210;
const uint32_t PWM_MAX = 1UL << PWM_BITS;  // 4096 = 100 %
const uint32_t CC_HZ = 1000;               // PWM del CTRL de los AL8860
const uint32_t IND_HZ = 2000;              // módulo industrial: los optoacopladores de las salidas 0-10 V

const uint8_t N_MODOS = 10;
const char* const NOMBRE[N_MODOS] = {"FIJO", "SECUENCIA", "PARPADEO", "RESPIRAR", "SEC. SUAVE", "ALTERNADO",
                                     "COLOR", "ARCOIRIS", "FLASH", "VELA"};

struct Prog { uint8_t activo, dias, h, m, acc, val; };
struct Config {
  uint8_t firma, modo, vel, brillo, canales, encendido, aux, eco, ldr;
  uint8_t color[4];
  int16_t horaOn, horaOff, umbral;
  Prog prog[8];
  uint8_t limiteA;                         // corriente máxima total (A)
  uint8_t cc[2];                           // focos de corriente constante 0..100 %
  uint8_t auxModo;                         // 0 = manual (X), 1 = ventilador automático por temperatura
};
Config cfg;
const Config DEF = {0xC1, 1, 4, 100, 3, 1, 0, 0, 0, {255, 120, 0, 0}, -1, -1, 20, {}, 20, {100, 100}, 0};

Preferences pref;
String nombre, grupo, tz, wifiRed, wifiClave, mqUri, mqUsr, mqClave, clave;
WebServer web(80);
DNSServer dns;
NetworkUDP udp;
esp_mqtt_client_handle_t mq = nullptr;
QueueHandle_t colaMq;
bool modoAP = false, hayRTC = false, sucio = false, mqConectado = false, haActivo = true;
uint32_t tSucio = 0, t0 = 0, tInicioWifi = 0;
uint8_t paso = 0;
bool porHorario = true, porLuz = true;
uint16_t GAMMA12[256];
uint16_t factor = 0;                       // 0..1000: arranque suave x reducción por temperatura
uint32_t dutyActual[4] = {9999, 9999, 9999, 9999};

// mediciones y protección
bool hayINA = false, hayTMP = false;
float vin = 0, amp = 0, watts = 0, tTarjeta = NAN, tIna = NAN;
double whTotal = 0, whHoy = 0, whGuardado = 0;
enum { SIN_FALLA = 0, F_CORRIENTE, F_TEMPERATURA, F_VOLTAJE };
const char* const FALLA[] = {"", "sobrecorriente", "temperatura alta", "sobrevoltaje"};
uint8_t falla = SIN_FALLA, disparos = 0;
uint32_t tFalla = 0, tPrimerDisparo = 0;
volatile bool alerta = false;

// base (memoria AT24CS02), Qwiic y diagnóstico
bool hayBase = false, hayOLED = false, hayLux = false, auxVent = false;
bool modoInd = false;                       // módulo AP-1 IND (0-10 V + contactores) en lugar de la base
bool modoPix = false;                       // módulo AP-1 PIX (pixeles direccionables) en lugar de la base
bool modoDmx = false;                       // módulo AP-1 DMX (DMX512): cada equipo DMX es un "pixel" (modoPix también)
char baseModelo[17] = "", baseSerie[33] = "";
uint32_t baseHoras = 0;
uint16_t baseNormal[6] = {0};              // consumo normal aprendido por salida (mA, a 100 %)
uint16_t baseReposo = 0;                   // consumo con todo apagado (mA)
float lux = NAN;
enum { D_SIN = 0, D_OK, D_ABIERTO, D_CORTO, D_BAJO, D_ALTO };
const char* const DIAG_TXT[] = {"-", "OK", "sin carga", "corto", "baja", "alta"};
struct Prueba { uint8_t est; uint16_t mA; };
Prueba prueba[6];
int8_t diagSalida = -1;                    // -1 = sin diagnóstico en curso; 0..5 = salida que se prueba
uint8_t diagFase = 0;
bool diagAprender = false;
uint32_t tDiag = 0;
float diagI0 = 0, diagI5 = 0;
String aviso;

struct Vecino { String nombre, grupo; IPAddress ip; uint32_t visto; };
Vecino vecinos[16];

// ---------------- control en vivo: Art-Net y sACN (E1.31) ----------------
// Programas como xLights, QLC+, Jinx! o Resolume mandan los niveles cuadro por cuadro por la red.
// Mientras lleguen datos (y la luz esté encendida) mandan ellos; 2.5 s sin datos vuelven los efectos.
// Pixeles: 170 LED RGB por universo (510 canales). DMX: el universo pasa tal cual (512 canales).
// Base e IND: canales 1-4 = salidas 1-4; 5-6 = focos de corriente constante (base).
const uint16_t ART_PUERTO = 6454, SACN_PUERTO = 5568, VIVO_UNIS = 16;
NetworkUDP udpArt, udpSacn;
bool vivoActivo = true;
uint16_t vivoUni = 1;                       // universo inicial (el mismo número en Art-Net y en sACN)
uint8_t vivoDatos[VIVO_UNIS * 512];
uint32_t tVivo = 0, vivoPaquetes = 0;
bool vivo() { return vivoActivo && tVivo && millis() - tVivo < 2500; }
void vivoIniciar();                         // (más abajo, junto a la red)

// ---------------- AP OUTPUT / AP INPUT: módulos de salidas y entradas por I2C (Qwiic) ----------------
// TCA9554 en 0x20-0x23 = AP OUTPUT (P0-P6 salidas de 24 V, P7 LED RUN); 0x24-0x27 = AP INPUT (8 entradas aisladas).
// Salidas S1..S28 (0x20 = S1-S7, 0x21 = S8-S14...), entradas E1..E32 (0x24 = E1-E8...). Al arrancar todo apagado.
const uint8_t IO_N = 4, ACC_NADA = 255;
uint8_t ioOut = 0, ioIn = 0;                // módulos presentes (un bit por dirección)
uint8_t salEstado[IO_N] = {0}, entEstado[IO_N] = {0}, entCrudo[IO_N] = {0};
struct Regla { uint8_t acc, val, modo; };   // qué hace cada entrada al activarse (modo 1: al soltar, lo contrario)
Regla reglas[IO_N * 8];
bool ioCambio = false;

// ---------------- memoria (con retardo para no gastar la flash) ----------------
void marcar() { sucio = true; tSucio = millis(); }
void guardarAhora() { pref.putBytes("cfg", &cfg, sizeof(cfg)); sucio = false; }
void cargar() {
  if (pref.getBytes("cfg", &cfg, sizeof(cfg)) != sizeof(cfg) || cfg.firma != DEF.firma || cfg.modo >= N_MODOS) cfg = DEF;
  if (cfg.limiteA < 1 || cfg.limiteA > 25) cfg.limiteA = 20;
  whTotal = whGuardado = pref.getDouble("wh", 0);
  vivoActivo = pref.getBool("vivo", true);
  if (pref.getBytes("reglas", reglas, sizeof(reglas)) != sizeof(reglas))
    for (auto& r : reglas) r = Regla{ACC_NADA, 0, 0};
  vivoUni = pref.getUShort("uni", 1);
  char def[16];
  snprintf(def, sizeof(def), "letrero-%04x", (uint16_t)(ESP.getEfuseMac() >> 32));
  nombre = pref.getString("nombre", def);
  grupo = pref.getString("grupo", "casa");
  tz = pref.getString("tz", "CST6");
  wifiRed = pref.getString("red", "");
  wifiClave = pref.getString("wclave", "");
  mqUri = pref.getString("mquri", "");
  mqUsr = pref.getString("mqusr", "");
  mqClave = pref.getString("mqclave", "");
  haActivo = pref.getBool("ha", true);
  clave = pref.getString("clave", "");
}
void guardarEscena(uint8_t n) { if (n < 4) { char k[8]; snprintf(k, 8, "esc%u", n); pref.putBytes(k, &cfg, sizeof(cfg)); } }
void cargarEscena(uint8_t n) {
  if (n >= 4) return;
  char k[8];
  snprintf(k, 8, "esc%u", n);
  Config e;
  if (pref.getBytes(k, &e, sizeof(e)) == sizeof(e) && e.firma == DEF.firma && e.modo < N_MODOS) {
    memcpy(e.prog, cfg.prog, sizeof(cfg.prog));     // la escena no borra los horarios
    cfg = e;
    paso = 0;
  }
}

// ---------------- salidas ----------------
// Cada canal arranca su pulso en otro cuarto del periodo (hpoint): con varios canales a medio brillo la corriente
// de la fuente se reparte en el tiempo en vez de llegar en un solo pico (menos rizo y menos calor en C1/C2).
// Módulo IND: el filtro del optoacoplador (RE 4.7k, RF 10k, RD 47k) no es lineal con el ciclo de trabajo;
// se invierte su curva para que el voltaje 0-10 V salga proporcional a lo pedido.
uint32_t linealInd(uint32_t duty) {
  const float a = 1 / 10e3f, b = 1 / 10e3f - 1 / 14.7e3f, c = 1 / 14.7e3f + 1 / 47e3f, f1 = a / (b + c);
  float x = min(1.0f, duty / (float)PWM_MAX);
  return (uint32_t)constrain(x * f1 * c / (a - x * f1 * b) * PWM_MAX + 0.5f, 0.0f, (float)PWM_MAX);
}
void pwm(uint8_t c, uint32_t duty) {
  if (modoPix) return;                                      // en el módulo PIX los pines son datos de pixeles
  if (duty == dutyActual[c]) return;
  dutyActual[c] = duty;
  if (modoInd) duty = linealInd(duty);
  uint32_t hp = c * (PWM_MAX / 4);
  if (hp + duty > PWM_MAX) hp = PWM_MAX - duty;          // el pulso nunca pasa del fin del periodo
  ledc_set_duty_with_hpoint(LEDC_LOW_SPEED_MODE, (ledc_channel_t)c, duty, hp);
  ledc_update_duty(LEDC_LOW_SPEED_MODE, (ledc_channel_t)c);
}
void salida(uint8_t c, uint8_t nivel) {
  uint8_t maxb = cfg.eco ? min<uint8_t>(cfg.brillo, 60) : cfg.brillo;
  pwm(c, (uint32_t)GAMMA12[(uint16_t)nivel * maxb / 100] * factor / 1000);
}
void todos(uint8_t v) { for (uint8_t c = 0; c < cfg.canales; c++) salida(c, v); }
uint32_t ccActual[2] = {9999, 9999};
void focoCC(uint8_t k, uint32_t duty) {   // 0..4096
  if (duty == ccActual[k]) return;
  ccActual[k] = duty;
  ledcWrite(CC_PIN[k], duty);
}
void apagarTodo() {                      // en el módulo IND el contactor 2 es manual y no lo apaga el efecto
  for (uint8_t c = 0; c < 4; c++) pwm(c, 0);
  if (!modoInd) { focoCC(0, 0); focoCC(1, 0); }
}

uint8_t triangulo(uint32_t t, uint32_t per) {
  uint32_t f = t % per, m = per / 2;
  return f < m ? f * 255 / m : (per - f) * 255 / m;
}
void rueda(uint16_t h, uint8_t* r, uint8_t* g, uint8_t* b) {   // h 0..767
  if (h < 256) { *r = 255 - h; *g = h; *b = 0; }
  else if (h < 512) { h -= 256; *r = 0; *g = 255 - h; *b = h; }
  else { h -= 512; *r = h; *g = 0; *b = 255 - h; }
}

void efectos(uint32_t t) {
  uint16_t T = 1500 - cfg.vel * 140;          // ms por paso (1500 .. 240)
  uint8_t n = cfg.canales;
  switch (cfg.modo) {
    case 0: todos(255); break;                                                 // FIJO
    case 1: if (t - t0 >= T) { t0 = t; paso = (paso + 1) % n; }                // SECUENCIA
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
    case 6: for (uint8_t c = 0; c < n; c++) salida(c, cfg.color[c]); break;     // COLOR (RGBW)
    case 7: { uint8_t r, g, b; rueda((t / (T / 64 + 1)) % 768, &r, &g, &b);     // ARCOIRIS
              salida(0, r); if (n > 1) salida(1, g); if (n > 2) salida(2, b); if (n > 3) salida(3, 0); } break;
    case 8: { uint32_t f = t % (2UL * T); todos(f < 60 || (f > 180 && f < 240) ? 255 : 0); } break;   // FLASH
    case 9: { static uint8_t v = 200; if (t - t0 > 60) { t0 = t; v = 150 + random(0, 106); }          // VELA
              for (uint8_t c = 0; c < n; c++) salida(c, (uint16_t)v * cfg.color[c] / 255); } break;
  }
}

// ---------------- hora: NTP + DS3231 opcional ----------------
uint8_t bcd2(uint8_t v) { return (v >> 4) * 10 + (v & 15); }
uint8_t aBcd(uint8_t v) { return ((v / 10) << 4) | (v % 10); }
bool horaValida() { return time(nullptr) > 1704067200; }      // posterior a 2024
void rtcEscribir(const struct tm& t) {
  if (!hayRTC) return;
  Wire.beginTransmission(0x68); Wire.write(0);
  Wire.write(aBcd(t.tm_sec)); Wire.write(aBcd(t.tm_min)); Wire.write(aBcd(t.tm_hour)); Wire.write(t.tm_wday + 1);
  Wire.write(aBcd(t.tm_mday)); Wire.write(aBcd(t.tm_mon + 1)); Wire.write(aBcd(t.tm_year % 100));
  Wire.endTransmission();
}
void rtcLeer() {                                   // el DS3231 guarda la hora local
  Wire.beginTransmission(0x68); Wire.write(0);
  if (Wire.endTransmission() != 0 || Wire.requestFrom(0x68, 7) < 7) return;
  struct tm t = {};
  t.tm_sec = bcd2(Wire.read() & 0x7F); t.tm_min = bcd2(Wire.read()); t.tm_hour = bcd2(Wire.read() & 0x3F);
  Wire.read();
  t.tm_mday = bcd2(Wire.read()); t.tm_mon = bcd2(Wire.read() & 0x1F) - 1; t.tm_year = bcd2(Wire.read()) + 100;
  t.tm_isdst = -1;
  struct timeval tv = {mktime(&t), 0};
  if (tv.tv_sec > 1704067200) settimeofday(&tv, nullptr);
}
void ponerHora(int an, int me, int di, int h, int mi, int s) {
  struct tm t = {};
  t.tm_year = an - 1900; t.tm_mon = me - 1; t.tm_mday = di; t.tm_hour = h; t.tm_min = mi; t.tm_sec = s; t.tm_isdst = -1;
  struct timeval tv = {mktime(&t), 0};
  settimeofday(&tv, nullptr);
  localtime_r(&tv.tv_sec, &t);
  rtcEscribir(t);
}
int16_t minutosAhora(uint8_t* wday) {
  if (!horaValida()) return -1;
  time_t ahora = time(nullptr);
  struct tm t;
  localtime_r(&ahora, &t);
  if (wday) *wday = t.tm_wday;
  return t.tm_hour * 60 + t.tm_min;
}
bool dentroVentana(int16_t m) {
  if (cfg.horaOn < 0 || m < 0) return true;
  if (cfg.horaOn <= cfg.horaOff) return m >= cfg.horaOn && m < cfg.horaOff;
  return m >= cfg.horaOn || m < cfg.horaOff;          // cruza la medianoche
}

// ---------------- medidor INA238 y temperatura TMP1075 ----------------
const uint8_t INA = 0x40, TMP = 0x48;
bool escribir16(uint8_t dir, uint8_t reg, uint16_t v) {
  Wire.beginTransmission(dir); Wire.write(reg); Wire.write(v >> 8); Wire.write(v & 0xFF);
  return Wire.endTransmission() == 0;
}
int32_t leer16(uint8_t dir, uint8_t reg) {           // -1 si no responde
  Wire.beginTransmission(dir); Wire.write(reg);
  if (Wire.endTransmission(false) != 0 || Wire.requestFrom(dir, (uint8_t)2) != 2) return -1;
  uint16_t v = Wire.read() << 8;
  return v | Wire.read();
}
void inaLimite() {                                  // alerta por hardware: corriente (SOVL) en pasos de 1.25 uV
  if (hayINA) escribir16(INA, 0x0C, (uint16_t)min(32767.0f, cfg.limiteA * R_SHUNT / 1.25e-6f));
}
void iniciarSensores() {
  hayINA = leer16(INA, 0x3E) == 0x5449;             // "TI"
  if (hayINA) {
    escribir16(INA, 0x00, 0x0010);                  // ADCRANGE = 1: +-40.96 mV (hasta 40 A con 1 mOhm)
    // continuo: bus 150 us, shunt 540 us, temperatura 150 us; promedio de 16 para las lecturas.
    // La alerta compara cada conversión sin promediar (SLOWALERT = 0): responde en menos de 1 ms y en la base
    // ALERT apaga los drivers de los MOSFET por hardware (D8/D9 a los EN del UCC27524).
    escribir16(INA, 0x01, 0xF512);
    escribir16(INA, 0x0B, 0x8000);                  // alerta retenida hasta leer DIAG_ALRT
    escribir16(INA, 0x0E, (uint16_t)(28.0f / 0.003125f));     // sobrevoltaje: 28 V (el supresor SMBJ26A empieza a 28.9 V)
    escribir16(INA, 0x10, (uint16_t)((int)(100 / 0.125f) << 4)); // temperatura del INA: 100 C
    inaLimite();
  }
  hayTMP = leer16(TMP, 0x00) >= 0;
  if (hayTMP) {                                      // TMP1075 / LM75: alerta a 85 C, se libera a 75 C
    escribir16(TMP, 0x03, (uint16_t)((int)(85 / 0.0625f) << 4));
    escribir16(TMP, 0x02, (uint16_t)((int)(75 / 0.0625f) << 4));
  }
}
void leerSensores() {
  if (hayINA) {
    int32_t sh = leer16(INA, 0x04), bus = leer16(INA, 0x05), dt = leer16(INA, 0x06);
    if (sh >= 0) amp = (int16_t)sh * 1.25e-6f / R_SHUNT;
    if (bus >= 0) vin = (int16_t)bus * 0.003125f;
    if (dt >= 0) tIna = ((int16_t)dt >> 4) * 0.125f;
    watts = vin * amp;
  }
  if (hayTMP) { int32_t t = leer16(TMP, 0x00); if (t >= 0) tTarjeta = ((int16_t)t >> 4) * 0.0625f; }
}
void IRAM_ATTR alertaISR() { alerta = true; }

// ---- memoria de la base (M24C02 o AT24CS02): 0 "LL" v1 | 3 modelo[16] | 20 normal[6] mA | 32 horas | 36 reposo mA
//      | 40 serie[16] (si la memoria no trae serie de fábrica en 0x58, se crea una al azar la primera vez) ----
const uint8_t EEP = 0x50, EEP_SERIE = 0x58;
bool eepLeer(uint8_t dir, void* buf, uint8_t n) {
  uint8_t* b = (uint8_t*)buf;
  for (uint8_t i = 0; i < n; i += 16) {
    uint8_t k = min<uint8_t>(16, n - i);
    Wire.beginTransmission(EEP); Wire.write(dir + i);
    if (Wire.endTransmission(false) != 0 || Wire.requestFrom(EEP, k) != k) return false;
    for (uint8_t j = 0; j < k; j++) b[i + j] = Wire.read();
  }
  return true;
}
void eepEscribir(uint8_t dir, const void* buf, uint8_t n) {   // páginas de 8 bytes; 5 ms por página
  const uint8_t* b = (const uint8_t*)buf;
  while (n) {
    uint8_t k = min<uint8_t>(n, 8 - (dir % 8));
    Wire.beginTransmission(EEP); Wire.write(dir); Wire.write(b, k); Wire.endTransmission();
    delay(6);
    dir += k; b += k; n -= k;
  }
}
bool dmxDetectar();                          // módulo DMX (más abajo)
void leerBase() {
  uint8_t cab[3];
  hayBase = eepLeer(0, cab, 3);
  if (!hayBase) return;
  if (cab[0] != 'L' || cab[1] != 'L' || cab[2] != 1) {            // base nueva: se le da formato
    uint8_t vacio[37] = {'L', 'L', 1};
    // BASE: medidor + temperatura; PIX: solo medidor; IND: ninguno de los dos
    // sin medidor: DMX si el transceptor regresa el eco, si no IND
    strcpy((char*)vacio + 3, hayINA ? (hayTMP ? "AP-1 universal" : "LL-PIX") : (dmxDetectar() ? "LL-DMX" : "LL-IND"));
    eepEscribir(0, vacio, sizeof(vacio));
  }
  eepLeer(3, baseModelo, 16); baseModelo[16] = 0;
  modoInd = !strncmp(baseModelo, "LL-IND", 6);
  modoDmx = !strncmp(baseModelo, "LL-DMX", 6);
  modoPix = modoDmx || !strncmp(baseModelo, "LL-PIX", 6);
  eepLeer(20, baseNormal, 12);
  eepLeer(32, &baseHoras, 4);
  eepLeer(36, &baseReposo, 2);
  for (auto& v : baseNormal) if (v == 0xFFFF) v = 0;
  if (baseReposo == 0xFFFF) baseReposo = 0;
  uint8_t sn[16];                                                   // número de serie de fábrica (128 bits)
  Wire.beginTransmission(EEP_SERIE); Wire.write(0x80);
  if (Wire.endTransmission(false) == 0 && Wire.requestFrom(EEP_SERIE, (uint8_t)16) == 16) {
    for (uint8_t i = 0; i < 16; i++) sn[i] = Wire.read();          // AT24CS02: serie de fábrica
  } else if (eepLeer(40, sn, 16)) {                                 // M24C02 (más barata): serie propia
    bool vacia = true;
    for (uint8_t v : sn) if (v != 0xFF) vacia = false;
    if (vacia) {
      for (uint8_t i = 0; i < 16; i += 4) { uint32_t a = esp_random() ^ micros(); memcpy(sn + i, &a, 4); }
      uint64_t mac = ESP.getEfuseMac();                            // con la MAC del programador: no se repite
      for (uint8_t i = 0; i < 6; i++) sn[i] ^= (uint8_t)(mac >> (8 * i));
      eepEscribir(40, sn, 16);
    }
  } else return;
  for (uint8_t i = 0; i < 16; i++) sprintf(baseSerie + 2 * i, "%02X", sn[i]);
}
void guardarNormal() { eepEscribir(20, baseNormal, 12); eepEscribir(36, &baseReposo, 2); }

// ---- módulo PIX: pixeles WS2812/SK6812/WS2815 en PWM 1-4 ----
// El ESP32-C3 tiene 2 canales RMT de salida: las 4 salidas se mandan una tras otra, abriendo el canal para cada una.
// La cantidad de LED, los segmentos ("letras") y el orden de color viven en la memoria del módulo (bytes 64-73):
// el letrero lleva su propia configuración.
const uint16_t PIX_MAX = 600;              // LED por salida
const uint8_t EEP_PIX = 64;
uint16_t pixN[4] = {0, 0, 0, 0};
uint8_t pixSeg = 0, pixOrden = 0;           // segmentos (0 = uno por salida); orden 0 GRB, 1 RGB, 2 BRG
uint16_t ablFactor = 1000;                  // limitación de brillo por corriente medida (0..1000)
// ---- módulo DMX: DMX512 por RS-485 (SP3485). DI = PWM1 (TX de UART1), RO = PWM2, DE = PWM3; /RE fijo en bajo,
// así el receptor regresa el eco de lo que se manda: con eso se reconoce el módulo. Dirección y canales: bytes 74-76.
const uint8_t EEP_DMX = 74;
uint16_t dmxDir = 1;                        // canal DMX del primer equipo (1-512)
uint8_t dmxCh = 3;                          // canales por equipo: 1 atenuador, 3 RGB, 4 RGBW
uint8_t dmxBuf[513];                        // [0] = código de inicio (0); [1..512] = canales
uint32_t dmxCuadros = 0;
void dmxAjustar() {                         // que todos los equipos quepan en el universo
  if (dmxDir + (uint32_t)pixN[0] * dmxCh > 513) pixN[0] = (513 - dmxDir) / dmxCh;
}
bool dmxDetectar() {
  for (uint8_t c = 0; c < 3; c++) ledcDetach(PWM_PIN[c]);
  pinMode(PWM_PIN[0], OUTPUT); pinMode(PWM_PIN[2], OUTPUT); pinMode(PWM_PIN[1], INPUT);
  digitalWrite(PWM_PIN[2], HIGH);                            // DE: transmitir
  bool ok = true;
  for (uint8_t i = 0; i < 8 && ok; i++) {
    digitalWrite(PWM_PIN[0], i & 1);
    delayMicroseconds(20);
    ok = digitalRead(PWM_PIN[1]) == (i & 1);
  }
  digitalWrite(PWM_PIN[0], LOW); digitalWrite(PWM_PIN[2], LOW);
  for (uint8_t c = 0; c < 3; c++) { ledcAttachChannel(PWM_PIN[c], PWM_HZ, PWM_BITS, c); dutyActual[c] = 9999; }
  Serial.printf("Eco DMX: %s\n", ok ? "si" : "no");
  return ok;
}
rmt_data_t* pixBuf = nullptr;
uint32_t tPix = 0;
void pixLeer() {
  uint8_t b[10];
  if (!eepLeer(EEP_PIX, b, 10)) return;
  for (uint8_t k = 0; k < 4; k++) {
    uint16_t v = b[2 * k] | (b[2 * k + 1] << 8);
    pixN[k] = v == 0xFFFF ? (k == 0 ? 60 : 0) : min<uint16_t>(v, PIX_MAX);   // módulo nuevo: 60 LED en la salida 1
  }
  pixSeg = b[8] == 0xFF ? 0 : b[8];
  pixOrden = b[9] > 2 ? (modoDmx ? 1 : 0) : b[9];               // DMX: RGB por omisión; tiras: GRB
  if (modoDmx) {
    uint8_t d[3];
    if (!eepLeer(EEP_DMX, d, 3)) return;
    uint16_t dir = d[0] | (d[1] << 8);
    dmxDir = (dir < 1 || dir > 512) ? 1 : dir;
    dmxCh = (d[2] == 1 || d[2] == 3 || d[2] == 4) ? d[2] : 3;
    pixN[1] = pixN[2] = pixN[3] = 0;                          // una sola línea DMX
    if (pixN[0] == 60 && b[0] == 0xFF) pixN[0] = 8;           // módulo nuevo: 8 equipos RGB
    dmxAjustar();
  }
}
void pixGuardar() {
  uint8_t b[10];
  for (uint8_t k = 0; k < 4; k++) { b[2 * k] = pixN[k] & 0xFF; b[2 * k + 1] = pixN[k] >> 8; }
  b[8] = pixSeg; b[9] = pixOrden;
  eepEscribir(EEP_PIX, b, 10);
  if (modoDmx) { uint8_t d[3] = {(uint8_t)(dmxDir & 0xFF), (uint8_t)(dmxDir >> 8), dmxCh}; eepEscribir(EEP_DMX, d, 3); }
}
uint16_t pixTotal() { return pixN[0] + pixN[1] + pixN[2] + pixN[3]; }
void pixIniciar() {
  if (modoDmx) {
    for (uint8_t c = 0; c < 4; c++) { ledcDetach(PWM_PIN[c]); pinMode(PWM_PIN[c], OUTPUT); digitalWrite(PWM_PIN[c], LOW); }
    digitalWrite(PWM_PIN[2], HIGH);                           // DE: el módulo solo transmite
    Serial1.setTxBufferSize(1024);                            // el cuadro se manda sin detener el programa
    Serial1.begin(250000, SERIAL_8N2, PWM_PIN[1], PWM_PIN[0]);
    return;
  }
  for (uint8_t c = 0; c < 4; c++) { ledcDetach(PWM_PIN[c]); pinMode(PWM_PIN[c], OUTPUT); digitalWrite(PWM_PIN[c], LOW); }
  pixBuf = (rmt_data_t*)malloc(PIX_MAX * 24 * sizeof(rmt_data_t));
}
// color del pixel g (las 4 salidas cuentan como una sola cadena) según el modo; los mismos 10 modos que la base
void pixColor(uint16_t g, uint16_t tot, uint8_t nseg, uint32_t t, uint16_t T, uint8_t* r, uint8_t* v, uint8_t* a) {
  uint8_t cr = cfg.color[0], cg = cfg.color[1], cb = cfg.color[2];
  if (!cr && !cg && !cb) cr = cg = cb = 255;                     // sin color elegido: blanco
  uint8_t s = (uint32_t)g * nseg / max<uint16_t>(tot, 1), k = 255;
  switch (cfg.modo) {
    case 1: k = s == paso % nseg ? 255 : 0; break;                                     // SECUENCIA por letras
    case 2: k = (paso & 1) ? 255 : 0; break;                                           // PARPADEO
    case 3: k = triangulo(t, 4UL * T); break;                                          // RESPIRAR
    case 4: { uint32_t per = (uint32_t)nseg * T, f = (t + per - (uint32_t)s * T) % per;   // SECUENCIA SUAVE
              k = f < 2UL * T ? triangulo(f, 2UL * T) : 0; } break;
    case 5: k = ((s & 1) ^ (paso & 1)) ? 255 : 0; break;                               // ALTERNADO
    case 7: rueda(((uint32_t)g * 768 / max<uint16_t>(tot, 1) + t / (T / 64 + 1)) % 768, &cr, &cg, &cb); break;  // ARCOIRIS
    case 8: { uint32_t f = t % (2UL * T); k = (f < 60 || (f > 180 && f < 240)) ? 255 : 0; } break;  // FLASH
    case 9: k = 150 + (esp_random() % 106); break;                                     // VELA (cada LED distinto)
  }
  *r = (uint16_t)cr * k / 255; *v = (uint16_t)cg * k / 255; *a = (uint16_t)cb * k / 255;
}
uint8_t pixNivel(uint8_t x, uint32_t esc) { return min<uint32_t>(255, ((uint32_t)GAMMA12[x] * esc / 1000) >> 4); }   // curva 2.2 y brillo
void dmxEnviar(uint32_t t) {
  uint16_t T = 1500 - cfg.vel * 140, tot = pixN[0];
  uint8_t nseg = pixSeg ? pixSeg : min<uint16_t>(max<uint16_t>(tot, 1), 255);   // 0: cada equipo es una "letra"
  if ((cfg.modo == 1 || cfg.modo == 2 || cfg.modo == 5) && t - t0 >= T) { t0 = t; paso++; }
  uint8_t maxb = cfg.eco ? min<uint8_t>(cfg.brillo, 60) : cfg.brillo;
  uint32_t esc = (uint32_t)maxb * factor / 100;                                        // 0..1000
  memset(dmxBuf, 0, sizeof(dmxBuf));
  uint16_t p = dmxDir;
  if (vivo()) {                                          // el universo del programa externo pasa tal cual (con el brillo)
    for (uint16_t i = 0; i < 512; i++) dmxBuf[1 + i] = (uint32_t)vivoDatos[i] * esc / 1000;
    tot = 0;
  }
  for (uint16_t g = 0; g < tot && p + dmxCh <= 513; g++, p += dmxCh) {
    uint8_t r, v, a;
    pixColor(g, tot, nseg, t, T, &r, &v, &a);
    r = pixNivel(r, esc); v = pixNivel(v, esc); a = pixNivel(a, esc);
    if (dmxCh == 1) { dmxBuf[p] = max(r, max(v, a)); continue; }                       // atenuador
    uint8_t w = 0;
    if (dmxCh == 4) { w = min(r, min(v, a)); r -= w; v -= w; a -= w; }                 // RGBW: el blanco común al LED W
    uint8_t* c = dmxBuf + p;
    if (pixOrden == 1) { c[0] = r; c[1] = v; c[2] = a; }
    else if (pixOrden == 2) { c[0] = a; c[1] = r; c[2] = v; }
    else { c[0] = v; c[1] = r; c[2] = a; }
    if (dmxCh == 4) c[3] = w;
  }
  Serial1.flush();                                      // termina el cuadro anterior (22.6 ms a 250 kbit/s)
  Serial1.updateBaudRate(83333);                        // BREAK: un 0 a 83.3 kbit/s = 108 us en bajo, 24 us de MAB
  Serial1.write((uint8_t)0);
  Serial1.flush();
  Serial1.updateBaudRate(250000);
  Serial1.write(dmxBuf, sizeof(dmxBuf));                // código de inicio 0 y 512 canales
  dmxCuadros++;
}
void pixEnviar(uint32_t t) {
  if (modoDmx) { dmxEnviar(t); return; }
  if (!pixBuf) return;
  uint16_t T = 1500 - cfg.vel * 140, tot = pixTotal(), g = 0;
  uint8_t usadas = (pixN[0] > 0) + (pixN[1] > 0) + (pixN[2] > 0) + (pixN[3] > 0);
  uint8_t nseg = pixSeg ? pixSeg : max<uint8_t>(usadas, 1);
  if ((cfg.modo == 1 || cfg.modo == 2 || cfg.modo == 5) && t - t0 >= T) { t0 = t; paso++; }
  uint8_t maxb = cfg.eco ? min<uint8_t>(cfg.brillo, 60) : cfg.brillo;
  uint32_t esc = (uint32_t)maxb * factor / 100 * ablFactor / 1000;                       // 0..1000
  bool enVivo = vivo();
  for (uint8_t o = 0; o < 4; o++) {
    uint16_t n = pixN[o];
    if (!n) continue;
    rmt_data_t* p = pixBuf;
    for (uint16_t i = 0; i < n; i++, g++) {
      uint8_t c[3], r, v, a;
      if (enVivo) {                                                                        // RGB del programa externo
        const uint8_t* q = vivoDatos + (uint32_t)g * 3;
        r = (uint32_t)q[0] * esc / 1000; v = (uint32_t)q[1] * esc / 1000; a = (uint32_t)q[2] * esc / 1000;
      } else {
        pixColor(g, tot, nseg, t, T, &r, &v, &a);
        r = pixNivel(r, esc); v = pixNivel(v, esc); a = pixNivel(a, esc);
      }
      if (pixOrden == 1) { c[0] = r; c[1] = v; c[2] = a; }
      else if (pixOrden == 2) { c[0] = a; c[1] = r; c[2] = v; }
      else { c[0] = v; c[1] = r; c[2] = a; }                                             // GRB (WS2812B)
      for (uint8_t j = 0; j < 3; j++)
        for (int8_t bit = 7; bit >= 0; bit--, p++) {                                     // 0.1 us por tick
          bool uno = (c[j] >> bit) & 1;
          p->level0 = 1; p->duration0 = uno ? 7 : 4; p->level1 = 0; p->duration1 = uno ? 6 : 8;
        }
    }
    if (rmtInit(PWM_PIN[o], RMT_TX_MODE, RMT_MEM_NUM_BLOCKS_2, 10000000)) {
      rmtWrite(PWM_PIN[o], pixBuf, (size_t)n * 24, 50);
      rmtDeinit(PWM_PIN[o]);
    }
    pinMode(PWM_PIN[o], OUTPUT); digitalWrite(PWM_PIN[o], LOW);                           // reinicio de la tira
  }
  if (hayINA) {                                     // limitación automática: 90 % del límite de corriente configurado
    if (amp > cfg.limiteA * 0.9f) ablFactor = max<int>(100, ablFactor - 60);
    else if (amp < cfg.limiteA * 0.8f && ablFactor < 1000) ablFactor = min<int>(1000, ablFactor + 10);
  }
}


// ---- sensor de luz BH1750 (Qwiic, opcional) ----
void leerLuz() {
  if (!hayLux) return;
  if (Wire.requestFrom((uint8_t)0x23, (uint8_t)2) == 2) { uint16_t r = Wire.read() << 8; r |= Wire.read(); lux = r / 1.2f; }
}

// ---- pantalla OLED SSD1306 128x64 (Qwiic, opcional): texto de 21 x 8 ----
const uint8_t OLED = 0x3C;
const uint8_t FUENTE[96][5] PROGMEM = {
  {0,0,0,0,0},{0,0,0x5F,0,0},{0,7,0,7,0},{0x14,0x7F,0x14,0x7F,0x14},{0x24,0x2A,0x7F,0x2A,0x12},{0x23,0x13,8,0x64,0x62},
  {0x36,0x49,0x56,0x20,0x50},{0,8,7,3,0},{0,0x1C,0x22,0x41,0},{0,0x41,0x22,0x1C,0},{0x2A,0x1C,0x7F,0x1C,0x2A},
  {8,8,0x3E,8,8},{0,0x80,0x70,0x30,0},{8,8,8,8,8},{0,0,0x60,0x60,0},{0x20,0x10,8,4,2},
  {0x3E,0x51,0x49,0x45,0x3E},{0,0x42,0x7F,0x40,0},{0x72,0x49,0x49,0x49,0x46},{0x21,0x41,0x49,0x4D,0x33},
  {0x18,0x14,0x12,0x7F,0x10},{0x27,0x45,0x45,0x45,0x39},{0x3C,0x4A,0x49,0x49,0x31},{0x41,0x21,0x11,9,7},
  {0x36,0x49,0x49,0x49,0x36},{0x46,0x49,0x49,0x29,0x1E},{0,0,0x14,0,0},{0,0x40,0x34,0,0},{0,8,0x14,0x22,0x41},
  {0x14,0x14,0x14,0x14,0x14},{0,0x41,0x22,0x14,8},{2,1,0x59,9,6},{0x3E,0x41,0x5D,0x59,0x4E},
  {0x7C,0x12,0x11,0x12,0x7C},{0x7F,0x49,0x49,0x49,0x36},{0x3E,0x41,0x41,0x41,0x22},{0x7F,0x41,0x41,0x41,0x3E},
  {0x7F,0x49,0x49,0x49,0x41},{0x7F,9,9,9,1},{0x3E,0x41,0x41,0x51,0x73},{0x7F,8,8,8,0x7F},{0,0x41,0x7F,0x41,0},
  {0x20,0x40,0x41,0x3F,1},{0x7F,8,0x14,0x22,0x41},{0x7F,0x40,0x40,0x40,0x40},{0x7F,2,0x1C,2,0x7F},
  {0x7F,4,8,0x10,0x7F},{0x3E,0x41,0x41,0x41,0x3E},{0x7F,9,9,9,6},{0x3E,0x41,0x51,0x21,0x5E},{0x7F,9,0x19,0x29,0x46},
  {0x26,0x49,0x49,0x49,0x32},{3,1,0x7F,1,3},{0x3F,0x40,0x40,0x40,0x3F},{0x1F,0x20,0x40,0x20,0x1F},
  {0x3F,0x40,0x38,0x40,0x3F},{0x63,0x14,8,0x14,0x63},{3,4,0x78,4,3},{0x61,0x59,0x49,0x4D,0x43},{0,0x7F,0x41,0x41,0x41},
  {2,4,8,0x10,0x20},{0,0x41,0x41,0x41,0x7F},{4,2,1,2,4},{0x40,0x40,0x40,0x40,0x40},{0,3,7,8,0},
  {0x20,0x54,0x54,0x78,0x40},{0x7F,0x28,0x44,0x44,0x38},{0x38,0x44,0x44,0x44,0x28},{0x38,0x44,0x44,0x28,0x7F},
  {0x38,0x54,0x54,0x54,0x18},{0,8,0x7E,9,2},{0x18,0xA4,0xA4,0x9C,0x78},{0x7F,8,4,4,0x78},{0,0x44,0x7D,0x40,0},
  {0x20,0x40,0x40,0x3D,0},{0x7F,0x10,0x28,0x44,0},{0,0x41,0x7F,0x40,0},{0x7C,4,0x78,4,0x78},{0x7C,8,4,4,0x78},
  {0x38,0x44,0x44,0x44,0x38},{0xFC,0x18,0x24,0x24,0x18},{0x18,0x24,0x24,0x18,0xFC},{0x7C,8,4,4,8},
  {0x48,0x54,0x54,0x54,0x24},{4,4,0x3F,0x44,0x24},{0x3C,0x40,0x40,0x20,0x7C},{0x1C,0x20,0x40,0x20,0x1C},
  {0x3C,0x40,0x30,0x40,0x3C},{0x44,0x28,0x10,0x28,0x44},{0x4C,0x90,0x90,0x90,0x7C},{0x44,0x64,0x54,0x4C,0x44},
  {0,8,0x36,0x41,0},{0,0,0x77,0,0},{0,0x41,0x36,8,0},{2,1,2,4,2},{0,0,0,0,0}};
uint8_t pantalla[1024];
void oledCmd(std::initializer_list<uint8_t> c) {
  Wire.beginTransmission(OLED); Wire.write(0x00);
  for (uint8_t b : c) Wire.write(b);
  Wire.endTransmission();
}
void oledIniciar() {
  oledCmd({0xAE, 0xD5, 0x80, 0xA8, 0x3F, 0xD3, 0x00, 0x40, 0x8D, 0x14, 0x20, 0x00, 0xA1, 0xC8});
  oledCmd({0xDA, 0x12, 0x81, 0xCF, 0xD9, 0xF1, 0xDB, 0x40, 0xA4, 0xA6, 0xAF});
}
void oledTexto(uint8_t fila, const char* t) {          // fila 0..7, hasta 21 caracteres (sin acentos)
  uint8_t* p = pantalla + fila * 128;
  memset(p, 0, 128);
  for (uint8_t i = 0; t[i] && i < 21; i++) {
    uint8_t c = (uint8_t)t[i];
    if (c < 32 || c > 127) c = '?';
    for (uint8_t k = 0; k < 5; k++) p[i * 6 + k] = pgm_read_byte(&FUENTE[c - 32][k]);
  }
}
void oledMostrar() {
  oledCmd({0x21, 0, 127, 0x22, 0, 7});
  for (uint16_t i = 0; i < 1024; i += 16) {
    Wire.beginTransmission(OLED); Wire.write(0x40); Wire.write(pantalla + i, 16); Wire.endTransmission();
  }
}
bool i2cPresente(uint8_t dir) { Wire.beginTransmission(dir); return Wire.endTransmission() == 0; }
void dispararFalla(uint8_t f) {
  apagarTodo();
  factor = 0;
  if (falla == SIN_FALLA) {
    if (f == F_CORRIENTE) {                         // 3 disparos en 5 min: se queda apagado hasta "F 0" o el botón
      if (millis() - tPrimerDisparo > 300000UL) { tPrimerDisparo = millis(); disparos = 0; }
      disparos++;
    }
    Serial.printf("FALLA: %s (%.1f V, %.1f A, %.1f C)\n", FALLA[f], vin, amp, tTarjeta);
  }
  falla = f;
  tFalla = millis();
}
void revisarProteccion() {
  if (alerta || digitalRead(PIN_ALERTA) == LOW) {   // primero se apaga; luego se averigua la causa
    alerta = false;
    apagarTodo();
    int32_t d = hayINA ? leer16(INA, 0x0B) : 0;     // leer DIAG_ALRT libera la alerta retenida
    leerSensores();
    if (d > 0 && (d & (1 << 6))) dispararFalla(F_CORRIENTE);
    else if (d > 0 && (d & (1 << 4))) dispararFalla(F_VOLTAJE);
    else if ((d > 0 && (d & (1 << 7))) || tTarjeta >= 84.5f) dispararFalla(F_TEMPERATURA);
    else if (digitalRead(PIN_ALERTA) == LOW && hayTMP) dispararFalla(F_TEMPERATURA);
  }
  if (hayINA && amp > cfg.limiteA * 1.05f) dispararFalla(F_CORRIENTE);     // respaldo por programa
  if (falla == F_CORRIENTE && disparos < 3 && millis() - tFalla > 10000) falla = SIN_FALLA;          // reintento
  if (falla == F_TEMPERATURA && (isnan(tTarjeta) || tTarjeta < 70) && digitalRead(PIN_ALERTA) == HIGH) falla = SIN_FALLA;
  if (falla == F_VOLTAJE && vin < 27 && digitalRead(PIN_ALERTA) == HIGH) falla = SIN_FALLA;
}
uint16_t factorTemperatura() {                      // 100 % hasta 70 C, baja a 30 % a 84 C
  if (isnan(tTarjeta) || tTarjeta <= 70) return 1000;
  return (uint16_t)max(300.0f, 1000 - (tTarjeta - 70) * 50);
}
void sumarEnergia(float dtSeg) {
  double wh = max(0.0f, watts) * dtSeg / 3600.0;
  whTotal += wh; whHoy += wh;
  if (whTotal - whGuardado > 20) { whGuardado = whTotal; pref.putDouble("wh", whTotal); }   // cada 20 Wh (cuida la flash)
}

// ---------------- control remoto IR (NEC) ----------------
volatile uint32_t irCodigo = 0, irBits = 0, irUlt = 0;
volatile uint8_t irN = 0;
volatile bool irListo = false;
void IRAM_ATTR irISR() {                             // tiempo entre flancos de bajada
  uint32_t t = micros(), d = t - irUlt;
  irUlt = t;
  if (d > 12000) { irN = 0; return; }
  if (d > 10000) { irN = 1; irBits = 0; return; }     // 13.5 ms = encabezado
  if (d > 8000 && irN == 0) { irCodigo = 0xFFFFFFFF; irListo = true; return; }   // repetir
  if (irN == 0) return;
  irBits = (irBits << 1) | (d > 1700 ? 1 : 0);
  if (++irN > 32) { irCodigo = irBits; irListo = true; irN = 0; }
}

// ---------------- estado ----------------
String estadoJSON() {
  uint8_t wd = 0;
  int16_t m = minutosAhora(&wd);
  String s;
  s.reserve(700);
  s += "{\"v\":\"" VERSION "\",\"nom\":\""; s += nombre; s += "\",\"g\":\""; s += grupo;
  s += "\",\"p\":"; s += cfg.encendido; s += ",\"m\":"; s += cfg.modo;
  s += ",\"n\":\""; s += NOMBRE[cfg.modo]; s += "\",\"s\":"; s += cfg.vel; s += ",\"b\":"; s += cfg.brillo;
  s += ",\"ch\":"; s += cfg.canales; s += ",\"c\":[";
  for (uint8_t i = 0; i < 4; i++) { s += cfg.color[i]; if (i < 3) s += ','; }
  s += "],\"x\":"; s += cfg.aux; s += ",\"e\":"; s += cfg.eco; s += ",\"l\":"; s += cfg.ldr;
  s += ",\"u\":"; s += cfg.umbral;
  s += ",\"on\":"; s += cfg.horaOn; s += ",\"off\":"; s += cfg.horaOff; s += ",\"t\":"; s += m; s += ",\"wd\":"; s += wd;
  s += ",\"tz\":\""; s += tz; s += "\",\"rtc\":"; s += hayRTC;
  s += ",\"a\":[";
  for (uint8_t i = 0; i < 8; i++) {
    const Prog& p = cfg.prog[i];
    if (i) s += ',';
    s += '['; s += p.activo; s += ','; s += p.dias; s += ','; s += p.h; s += ','; s += p.m; s += ','; s += p.acc;
    s += ','; s += p.val; s += ']';
  }
  s += "],\"ap\":"; s += modoAP; s += ",\"red\":\""; s += wifiRed; s += "\",\"ip\":\"";
  s += WiFi.isConnected() ? WiFi.localIP().toString() : WiFi.softAPIP().toString();
  s += "\",\"rssi\":"; s += WiFi.isConnected() ? WiFi.RSSI() : 0;
  s += ",\"mq\":"; s += mqUri.length() ? (mqConectado ? 2 : 1) : 0;
  s += ",\"k\":"; s += clave.length() ? 1 : 0;
  s += ",\"med\":"; s += hayINA; s += ",\"vin\":"; s += String(vin, 2); s += ",\"i\":"; s += String(amp, 2);
  s += ",\"w\":"; s += String(watts, 1); s += ",\"kwh\":"; s += String(whTotal / 1000, 3);
  s += ",\"hoy\":"; s += String(whHoy / 1000, 3); s += ",\"tc\":"; s += isnan(tTarjeta) ? "null" : String(tTarjeta, 1);
  s += ",\"ti\":"; s += isnan(tIna) ? "null" : String(tIna, 1);
  s += ",\"f\":"; s += falla; s += ",\"fn\":\""; s += FALLA[falla]; s += "\",\"lim\":"; s += cfg.limiteA;
  s += ",\"fp\":"; s += factor / 10;
  s += ",\"cc\":["; s += cfg.cc[0]; s += ','; s += cfg.cc[1]; s += "],\"ym\":"; s += cfg.auxModo;
  s += ",\"av\":"; s += auxVent;
  s += ",\"lux\":"; s += isnan(lux) ? "null" : String(lux, 0);
  s += ",\"ind\":"; s += modoInd; s += ",\"px\":"; s += modoPix; s += ",\"dmx\":"; s += modoDmx;
  s += ",\"vivo\":{\"on\":"; s += vivoActivo; s += ",\"u\":"; s += vivoUni; s += ",\"rx\":"; s += vivo();
  s += ",\"p\":"; s += vivoPaquetes; s += '}';
  s += ",\"io\":{\"o\":"; s += ioOut; s += ",\"i\":"; s += ioIn; s += ",\"s\":[";
  for (uint8_t m = 0; m < IO_N; m++) { if (m) s += ','; s += salEstado[m]; }
  s += "],\"e\":[";
  for (uint8_t m = 0; m < IO_N; m++) { if (m) s += ','; s += entEstado[m]; }
  s += "],\"r\":[";                                          // reglas solo de los módulos de entradas presentes
  bool primera = true;
  for (uint8_t n = 0; n < IO_N * 8; n++) {
    if (!(ioIn & (1 << (n / 8)))) continue;
    if (!primera) s += ',';
    primera = false;
    s += '['; s += n + 1; s += ','; s += reglas[n].acc; s += ','; s += reglas[n].val; s += ','; s += reglas[n].modo; s += ']';
  }
  s += "]}";
  if (modoPix) {
    s += ",\"pix\":{\"n\":["; for (uint8_t k = 0; k < 4; k++) { if (k) s += ','; s += pixN[k]; }
    s += "],\"s\":"; s += pixSeg; s += ",\"o\":"; s += pixOrden; s += ",\"abl\":"; s += ablFactor / 10;
    if (modoDmx) { s += ",\"d\":"; s += dmxDir; s += ",\"ch\":"; s += dmxCh; s += ",\"fr\":"; s += dmxCuadros; }
    s += '}';
  }
  s += ",\"base\":{\"ok\":"; s += hayBase; s += ",\"mod\":\""; s += baseModelo; s += "\",\"sn\":\""; s += baseSerie;
  s += "\",\"h\":"; s += baseHoras; s += ",\"n\":[";
  for (uint8_t i = 0; i < 6; i++) { if (i) s += ','; s += baseNormal[i]; }
  s += "]},\"dg\":"; s += diagSalida; s += ",\"pr\":[";
  for (uint8_t i = 0; i < 6; i++) { if (i) s += ','; s += '['; s += prueba[i].est; s += ','; s += prueba[i].mA; s += ']'; }
  s += "],\"aviso\":\""; s += aviso; s += "\",\"oled\":"; s += hayOLED;
  s += '}';
  return s;
}

// ---------------- MQTT (servidor en la nube: control fuera de casa) ----------------
String temaBase() { return "letrerolab/" + nombre; }
void mqPublicar() {
  if (mq && mqConectado) {
    String t = temaBase() + "/estado", e = estadoJSON();
    esp_mqtt_client_publish(mq, t.c_str(), e.c_str(), e.length(), 1, 1);
  }
}
// Home Assistant (descubrimiento MQTT, como Shelly, Tasmota o WLED): el equipo aparece solo con su luz, AUX, focos CC,
// botón de diagnóstico y sensores de V, A, W, kWh, temperatura y falla. "HA 0" lo retira de Home Assistant.
void haUno(const String& uid, const char* tipo, const char* obj, const String& cfgJson) {
  String t = String("homeassistant/") + tipo + "/" + uid + "/" + obj + "/config";
  String e;
  if (haActivo) {
    e = "{\"~\":\"" + temaBase() + "\",\"unique_id\":\"" + uid + "_" + obj + "\",\"object_id\":\"" + nombre + "_" + obj +
        "\",\"availability_topic\":\"~/conectado\",\"payload_available\":\"1\",\"payload_not_available\":\"0\"," + cfgJson +
        ",\"device\":{\"identifiers\":[\"" + uid + "\"],\"name\":\"" + nombre + "\",\"manufacturer\":\"LetreroLab\",\"model\":\"AP-1 " +
        String(hayBase ? baseModelo : "sin base") + "\",\"sw_version\":\"" VERSION "\",\"configuration_url\":\"http://" +
        WiFi.localIP().toString() + "\"}}";
  }
  esp_mqtt_client_publish(mq, t.c_str(), e.c_str(), e.length(), 1, 1);   // vacío y retenido = borrar
}
void haPublicar() {
  if (!mq || !mqConectado) return;
  String uid = "letrerolab_" + WiFi.macAddress();
  uid.replace(":", "");
  uid.toLowerCase();
  String fx = "[";
  for (uint8_t i = 0; i < N_MODOS; i++) { if (i) fx += ','; fx += '\''; fx += NOMBRE[i]; fx += '\''; }
  fx += ']';
  String lista = fx; lista.replace('\'', '"');
  haUno(uid, "light", "luz", "\"name\":\"Letrero\",\"schema\":\"template\",\"command_topic\":\"~/cmd\",\"state_topic\":\"~/estado\","
        "\"command_on_template\":\"P 1{% if brightness is defined %}\\nB {{ (brightness / 2.55) | round | int }}{% endif %}"
        "{% if effect is defined %}\\nM {{ " + fx + ".index(effect) }}{% endif %}" +
        String(modoPix ? "{% if red is defined %}\\nC {{ red }} {{ green }} {{ blue }} 0{% endif %}" : "") +
        "\",\"command_off_template\":\"P 0\","
        "\"state_template\":\"{{ 'on' if value_json.p == 1 else 'off' }}\","
        "\"brightness_template\":\"{{ (value_json.b * 2.55) | round | int }}\"," +
        String(modoPix ? "\"red_template\":\"{{ value_json.c[0] }}\",\"green_template\":\"{{ value_json.c[1] }}\","
                         "\"blue_template\":\"{{ value_json.c[2] }}\"," : "") +
        "\"effect_list\":" + lista + ",\"effect_template\":\"{{ value_json.n }}\"");
  if (modoPix) {                                               // módulo de pixeles: sin AUX, focos CC ni diagnóstico
    const char* QUITAR[][2] = {{"switch", "aux"}, {"number", "cc1"}, {"number", "cc2"}, {"button", "diag"}, {"sensor", "tc"}};
    for (auto& q : QUITAR) {
      String t = String("homeassistant/") + q[0] + "/" + uid + "/" + q[1] + "/config";
      esp_mqtt_client_publish(mq, t.c_str(), "", 0, 1, 1);
    }
  }
  for (uint8_t m = 0; m < IO_N; m++) {                         // AP OUTPUT y AP INPUT presentes
    for (uint8_t b = 0; b < 7; b++) {
      uint8_t n = m * 7 + b + 1;
      String obj = String("s") + n;
      if (ioOut & (1 << m))
        haUno(uid, "switch", obj.c_str(), String("\"name\":\"Salida ") + n + "\",\"command_topic\":\"~/cmd\","
              "\"payload_on\":\"SA " + n + " 1\",\"payload_off\":\"SA " + n + " 0\",\"state_topic\":\"~/estado\","
              "\"value_template\":\"{{ (value_json.io.s[" + m + "] // " + (1 << b) + ") % 2 }}\",\"state_on\":\"1\",\"state_off\":\"0\"");
      else { String t = String("homeassistant/switch/") + uid + "/" + obj + "/config"; esp_mqtt_client_publish(mq, t.c_str(), "", 0, 1, 1); }
    }
    for (uint8_t b = 0; b < 8; b++) {
      uint8_t n = m * 8 + b + 1;
      String obj = String("e") + n;
      if (ioIn & (1 << m))
        haUno(uid, "binary_sensor", obj.c_str(), String("\"name\":\"Entrada ") + n + "\",\"state_topic\":\"~/estado\","
              "\"value_template\":\"{{ (value_json.io.e[" + m + "] // " + (1 << b) + ") % 2 }}\",\"payload_on\":\"1\",\"payload_off\":\"0\"");
      else { String t = String("homeassistant/binary_sensor/") + uid + "/" + obj + "/config"; esp_mqtt_client_publish(mq, t.c_str(), "", 0, 1, 1); }
    }
  }
  if (modoInd) {                                               // módulo industrial: contactor 2 manual
    haUno(uid, "switch", "k2", "\"name\":\"Contactor 2\",\"command_topic\":\"~/cmd\",\"payload_on\":\"O 100\","
          "\"payload_off\":\"O 0\",\"state_topic\":\"~/estado\",\"value_template\":\"{{ 1 if value_json.cc[0] > 0 else 0 }}\","
          "\"state_on\":\"1\",\"state_off\":\"0\"");
    const char* QUITAR[][2] = {{"switch", "aux"}, {"number", "cc1"}, {"number", "cc2"}, {"button", "diag"}, {"sensor", "vin"},
                               {"sensor", "i"}, {"sensor", "w"}, {"sensor", "kwh"}, {"sensor", "tc"}};
    for (auto& q : QUITAR) {                                   // sin medidor ni focos CC: se retiran si existían
      String t = String("homeassistant/") + q[0] + "/" + uid + "/" + q[1] + "/config";
      esp_mqtt_client_publish(mq, t.c_str(), "", 0, 1, 1);
    }
    haUno(uid, "sensor", "rssi", "\"name\":\"Señal Wi-Fi\",\"state_topic\":\"~/estado\",\"value_template\":\"{{ value_json.rssi }}\","
          "\"unit_of_measurement\":\"dBm\",\"device_class\":\"signal_strength\",\"entity_category\":\"diagnostic\"");
    return;
  }
  if (!modoPix) haUno(uid, "switch", "aux", "\"name\":\"AUX\",\"command_topic\":\"~/cmd\",\"payload_on\":\"X 1\",\"payload_off\":\"X 0\","
        "\"state_topic\":\"~/estado\",\"value_template\":\"{{ value_json.x }}\",\"state_on\":\"1\",\"state_off\":\"0\"");
  for (uint8_t k = 0; k < 2 && !modoPix; k++)
    haUno(uid, "number", k ? "cc2" : "cc1", String("\"name\":\"Foco CC ") + (k + 1) + "\",\"command_topic\":\"~/cmd\","
          "\"command_template\":\"O " + (k ? "- " : "") + "{{ value | int }}\",\"state_topic\":\"~/estado\","
          "\"value_template\":\"{{ value_json.cc[" + k + "] }}\",\"min\":0,\"max\":100,\"unit_of_measurement\":\"%\"");
  if (!modoPix) haUno(uid, "button", "diag", "\"name\":\"Probar salidas\",\"command_topic\":\"~/cmd\",\"payload_press\":\"DIAG\","
        "\"entity_category\":\"diagnostic\"");
  struct Sen { const char *obj, *nom, *campo, *unidad, *clase, *estado; bool diag; };
  static const Sen SEN[] = {
    {"vin", "Voltaje", "vin", "V", "voltage", "measurement", false},
    {"i", "Corriente", "i", "A", "current", "measurement", false},
    {"w", "Potencia", "w", "W", "power", "measurement", false},
    {"kwh", "Energía", "kwh", "kWh", "energy", "total_increasing", false},
    {"tc", "Temperatura", "tc", "°C", "temperature", "measurement", false},
    {"rssi", "Señal Wi-Fi", "rssi", "dBm", "signal_strength", "measurement", true},
  };
  for (const Sen& x : SEN)
    if (!(modoPix && !strcmp(x.obj, "tc")))                    // el módulo PIX no tiene sensor de temperatura
    haUno(uid, "sensor", x.obj, String("\"name\":\"") + x.nom + "\",\"state_topic\":\"~/estado\",\"value_template\":\"{{ value_json." +
          x.campo + " }}\",\"unit_of_measurement\":\"" + x.unidad + "\",\"device_class\":\"" + x.clase +
          "\",\"state_class\":\"" + x.estado + "\"" + (x.diag ? ",\"entity_category\":\"diagnostic\"" : ""));
  haUno(uid, "sensor", "falla", "\"name\":\"Falla\",\"state_topic\":\"~/estado\",\"value_template\":\"{{ value_json.fn }}\","
        "\"entity_category\":\"diagnostic\"");
}
void mqEvento(void*, esp_event_base_t, int32_t id, void* datos) {   // corre en la tarea de MQTT
  esp_mqtt_event_handle_t ev = (esp_mqtt_event_handle_t)datos;
  if (id == MQTT_EVENT_CONNECTED) {
    mqConectado = true;
    String t = temaBase() + "/cmd";
    esp_mqtt_client_subscribe(ev->client, t.c_str(), 1);
    esp_mqtt_client_subscribe(ev->client, "letrerolab/todos/cmd", 1);
    t = "letrerolab/grupo/" + grupo + "/cmd";
    esp_mqtt_client_subscribe(ev->client, t.c_str(), 1);
    t = temaBase() + "/conectado";
    esp_mqtt_client_publish(ev->client, t.c_str(), "1", 1, 1, 1);
    haPublicar();
  } else if (id == MQTT_EVENT_DISCONNECTED) {
    mqConectado = false;
  } else if (id == MQTT_EVENT_DATA && ev->data_len > 0 && ev->data_len < 120) {
    char buf[128];
    memcpy(buf, ev->data, ev->data_len);
    buf[ev->data_len] = 0;
    xQueueSend(colaMq, buf, 0);
  }
}
void mqIniciar() {
  if (mq) { esp_mqtt_client_stop(mq); esp_mqtt_client_destroy(mq); mq = nullptr; mqConectado = false; }
  if (!mqUri.length() || modoAP) return;
  esp_mqtt_client_config_t c = {};
  c.broker.address.uri = mqUri.c_str();
  if (mqUri.startsWith("mqtts")) c.broker.verification.crt_bundle_attach = esp_crt_bundle_attach;
  if (mqUsr.length()) c.credentials.username = mqUsr.c_str();
  if (mqClave.length()) c.credentials.authentication.password = mqClave.c_str();
  c.credentials.client_id = nombre.c_str();
  static String lwt;
  lwt = temaBase() + "/conectado";
  c.session.last_will.topic = lwt.c_str();
  c.session.last_will.msg = "0";
  c.session.last_will.retain = 1;
  mq = esp_mqtt_client_init(&c);
  if (!mq) return;
  esp_mqtt_client_register_event(mq, MQTT_EVENT_ANY, mqEvento, nullptr);
  esp_mqtt_client_start(mq);
}

// ---------------- grupos por la red local (UDP) ----------------
void anunciar() {
  if (!WiFi.isConnected()) return;
  udp.beginPacket(IPAddress(255, 255, 255, 255), UDP_PUERTO);
  udp.printf("LL1 A %s %s %d", nombre.c_str(), grupo.c_str(), cfg.encendido);
  udp.endPacket();
}
void enviarGrupo(const String& g, const char* orden) {
  if (!WiFi.isConnected()) return;
  udp.beginPacket(IPAddress(255, 255, 255, 255), UDP_PUERTO);
  udp.printf("LL1 C %s %s", g.c_str(), orden);
  udp.endPacket();
}

// ---------------- órdenes ----------------
int numero(const char*& p) {
  while (*p == ' ') p++;
  int v = 0;
  bool neg = false;
  if (*p == '-') { neg = true; p++; }
  while (*p >= '0' && *p <= '9') v = v * 10 + (*p++ - '0');
  if (*p == ':' || *p == '-' || *p == ',') p++;
  return neg ? -v : v;
}
String resto(const char* p) { while (*p == ' ') p++; String s(p); s.trim(); return s; }
String campo(String& s) {                      // separa "a,b,c" por comas
  int i = s.indexOf(',');
  String r = i < 0 ? s : s.substring(0, i);
  s = i < 0 ? "" : s.substring(i + 1);
  return r;
}
bool nombreValido(const String& s) {
  if (!s.length() || s.length() > 24) return false;
  for (char ch : s) if (!isalnum((unsigned char)ch) && ch != '-') return false;
  return true;
}

void aplicarAccion(uint8_t acc, uint8_t val) {
  switch (acc) {
    case 0: cfg.encendido = 0; break;
    case 1: cfg.encendido = 1; break;
    case 2: cfg.aux = val ? 1 : 0; break;
    case 3: cargarEscena(val); break;
    case 4: cfg.brillo = constrain(val, 0, 100); break;
    case 5: case 6: case 7:                                   // salida val (1-28) encender / apagar / alternar
      if (val >= 1 && val <= IO_N * 7) {
        uint8_t m = (val - 1) / 7, b = (val - 1) % 7;
        if (acc == 5) salEstado[m] |= 1 << b; else if (acc == 6) salEstado[m] &= ~(1 << b); else salEstado[m] ^= 1 << b;
        ioCambio = true;
      }
      return;
    case 8: cfg.encendido = !cfg.encendido; break;            // alternar la luz (pulsador)
    default: return;
  }
  marcar();
}
bool tcaEscribir(uint8_t dir, uint8_t reg, uint8_t v) {
  Wire.beginTransmission(dir); Wire.write(reg); Wire.write(v);
  return Wire.endTransmission() == 0;
}
int tcaLeer(uint8_t dir, uint8_t reg) {
  Wire.beginTransmission(dir); Wire.write(reg);
  if (Wire.endTransmission(false) != 0 || Wire.requestFrom(dir, (uint8_t)1) != 1) return -1;
  return Wire.read();
}
void ioBuscar() {                                             // al arrancar y cada 5 s (se pueden conectar en marcha)
  uint8_t o = 0, i = 0;
  for (uint8_t m = 0; m < IO_N; m++) {
    if (i2cPresente(0x20 + m)) o |= 1 << m;
    if (i2cPresente(0x24 + m)) i |= 1 << m;
  }
  for (uint8_t m = 0; m < IO_N; m++) {
    if ((i & (1 << m)) && !(ioIn & (1 << m))) {             // entrada nueva: polaridad invertida (1 = activa)
      tcaEscribir(0x24 + m, 2, 0xFF); tcaEscribir(0x24 + m, 3, 0xFF);
      int v = tcaLeer(0x24 + m, 0);
      entEstado[m] = entCrudo[m] = v < 0 ? 0 : v;             // el estado inicial no dispara reglas
    }
    if ((o & (1 << m)) && !(ioOut & (1 << m))) salEstado[m] = 0;   // salida nueva: empieza apagada
  }
  if (o != ioOut || i != ioIn) {
    ioOut = o; ioIn = i; ioCambio = true;
    Serial.printf("AP OUTPUT: %02X  AP INPUT: %02X\n", ioOut, ioIn);
    haPublicar();
  }
}
void ioEntrada(uint8_t n, bool activa) {                      // n = 0..31
  const Regla& r = reglas[n];
  if (r.acc == ACC_NADA) return;
  if (activa) aplicarAccion(r.acc, r.val);
  else if (r.modo == 1) {                                     // "mientras": al soltar, lo contrario
    if (r.acc == 0 || r.acc == 1) aplicarAccion(1 - r.acc, 0);
    else if (r.acc == 2) aplicarAccion(2, !r.val);
    else if (r.acc == 5 || r.acc == 6) aplicarAccion(11 - r.acc, r.val);
  }
}
void ioActualizar(uint32_t t) {
  static uint32_t tLee = 0, tBusca = 0, tEscribe = 0;
  if (t - tBusca > 5000) { tBusca = t; ioBuscar(); }
  if (!ioOut && !ioIn) return;
  if (t - tLee >= 20) {                                       // entradas cada 20 ms; dos lecturas iguales = estable
    tLee = t;
    for (uint8_t m = 0; m < IO_N; m++) {
      if (!(ioIn & (1 << m))) continue;
      int v = tcaLeer(0x24 + m, 0);
      if (v < 0) continue;
      if (v == entCrudo[m] && v != entEstado[m]) {
        uint8_t dif = v ^ entEstado[m];
        entEstado[m] = v;
        for (uint8_t b = 0; b < 8; b++) if (dif & (1 << b)) ioEntrada(m * 8 + b, v & (1 << b));
        ioCambio = true;
      }
      entCrudo[m] = v;
    }
  }
  bool run = (t / 500) & 1;                                   // LED RUN parpadeando: el programa está al mando
  static bool runAntes = false;
  if (ioCambio || run != runAntes || t - tEscribe > 1000) {   // cada segundo se reescribe todo (por si se reconectó)
    for (uint8_t m = 0; m < IO_N; m++) {
      if (!(ioOut & (1 << m))) continue;
      tcaEscribir(0x20 + m, 1, (salEstado[m] & 0x7F) | (run ? 0 : 0x80));
      tcaEscribir(0x20 + m, 3, 0x00);                         // todas salidas
    }
    if (ioCambio) mqPublicar();
    ioCambio = false; runAntes = run;
    if (t - tEscribe > 1000) tEscribe = t;
  }
}
void ioApagar() {
  for (uint8_t m = 0; m < IO_N; m++) { salEstado[m] = 0; if (ioOut & (1 << m)) tcaEscribir(0x20 + m, 1, 0x80); }
}

bool pedirReinicio = false;

// ---------------- diagnóstico de salidas con el medidor de la base ----------------
void salidaPrueba(int8_t k, uint32_t duty) {            // solo la salida k encendida (0-3 canales, 4-5 focos CC)
  for (uint8_t c = 0; c < 4; c++) pwm(c, k == c ? duty : 0);
  focoCC(0, k == 4 ? duty : 0);
  focoCC(1, k == 5 ? duty : 0);
}
float medirA() { delay(30); leerSensores(); return amp; }   // 30 ms: una conversión promediada nueva del INA238
void iniciarDiag(bool aprender) {
  if (falla != SIN_FALLA || !hayINA || modoInd || modoPix) return;   // el diagnóstico es para los MOSFET de la base
  diagAprender = aprender; diagSalida = 0; diagFase = 0; tDiag = millis(); aviso = "";
  for (auto& r : prueba) r = Prueba{D_SIN, 0};
  apagarTodo();
}
void calificar(uint8_t k, float dA) {
  uint16_t mA = (uint16_t)constrain(dA * 1000, 0, 60000);
  uint8_t est = D_OK;
  if (mA < 20) est = D_ABIERTO;
  else if (baseNormal[k] > 20 && !diagAprender) {
    float r = (float)mA / baseNormal[k];
    est = r < 0.8f ? D_BAJO : (r > 1.25f ? D_ALTO : D_OK);
  }
  prueba[k] = Prueba{est, mA};
}
void diagSiguiente() {
  salidaPrueba(-1, 0);
  diagFase = 0; tDiag = millis();
  if (++diagSalida < 6) return;
  diagSalida = -1;
  if (diagAprender) {                                    // lo medido pasa a ser el consumo normal de esta instalación
    for (uint8_t k = 0; k < 6; k++) baseNormal[k] = prueba[k].est == D_CORTO ? 0 : prueba[k].mA;
    baseReposo = (uint16_t)constrain(diagI0 * 1000, 0, 60000);
    if (hayBase) guardarNormal();
  }
  Serial.print("Diagnostico:");
  for (uint8_t k = 0; k < 6; k++) Serial.printf(" %s%u=%s(%umA)", k < 4 ? "CH" : "CC", k < 4 ? k + 1 : k - 3,
                                                DIAG_TXT[prueba[k].est], prueba[k].mA);
  Serial.println();
}
void diagnostico(uint32_t t) {
  if (falla != SIN_FALLA) {                              // la propia prueba disparó la protección
    if (falla == F_CORRIENTE) { prueba[diagSalida] = Prueba{D_CORTO, (uint16_t)(cfg.limiteA * 1000)}; falla = SIN_FALLA; disparos = 0; diagSiguiente(); }
    else diagSalida = -1;                                // temperatura o voltaje: se aborta
    return;
  }
  switch (diagFase) {
    case 0:                                              // todo apagado: consumo en reposo
      salidaPrueba(-1, 0);
      if (t - tDiag > 500) { diagI0 = medirA(); salidaPrueba(diagSalida, PWM_MAX / 20); diagFase = 1; tDiag = millis(); }
      break;
    case 1:                                              // 5 %: si a 100 % pasaría del límite, es un corto
      if (t - tDiag > 300) {
        diagI5 = medirA() - diagI0;
        if (diagSalida < 4 && diagI5 * 20 > cfg.limiteA * 1.1f) {
          prueba[diagSalida] = Prueba{D_CORTO, (uint16_t)constrain(diagI5 * 20000, 0, 60000)};
          diagSiguiente();
        } else { salidaPrueba(diagSalida, PWM_MAX); diagFase = 2; tDiag = millis(); }
      }
      break;
    case 2:                                              // 100 %: consumo de esta salida
      if (t - tDiag > 700) { float d = medirA() - diagI0; calificar(diagSalida, d); diagSiguiente(); }
      break;
  }
}
// En modo fijo o color compara el consumo con lo aprendido: un tramo fundido o un corto parcial se nota sin apagar nada
void vigilarConsumo() {
  static uint8_t malos = 0, buenos = 0;
  if (diagSalida >= 0 || !hayINA || (cfg.modo != 0 && cfg.modo != 6) || factor < 1000) { malos = buenos = 0; return; }
  float esperado = baseReposo;
  bool hay = false;
  for (uint8_t c = 0; c < 4; c++) if (baseNormal[c]) { esperado += baseNormal[c] * (float)dutyActual[c] / PWM_MAX; hay = true; }
  for (uint8_t k = 0; k < 2; k++) if (baseNormal[4 + k]) { esperado += baseNormal[4 + k] * (float)ccActual[k] / PWM_MAX; hay = true; }
  if (!hay || esperado < 100) return;
  float dif = (amp * 1000 - esperado) / esperado;
  if (fabsf(dif) > 0.25f) { buenos = 0; if (++malos >= 5) aviso = String("consumo ") + (dif > 0 ? "+" : "") + String((int)(dif * 100)) + "% vs lo normal: haga DIAG"; }
  else if (++buenos >= 5) { malos = 0; aviso = ""; }
}
bool ordenDeGrupo(const char* o) {                       // por grupo solo viajan órdenes de luces
  return o[0] && o[0] != '@' && !strchr("WQKDZ!JFUY", o[0]) && strncmp(o, "MODELO", 6) && strncmp(o, "APRENDER", 8);
}

// devuelve true si cambió algo (se publica el estado)
bool ejecutar(const char* s, bool remoto) {
  if (!strncmp(s, "DIAG", 4)) { iniciarDiag(false); return true; }
  if (!strncmp(s, "PX", 2) || !strncmp(s, "PS", 2) || !strncmp(s, "PO", 2) || !strncmp(s, "PD", 2)) {   // pixeles y DMX
    if (!modoPix) return false;
    const char* q = s + 2;
    if (s[1] == 'X') for (uint8_t k = 0; k < 4; k++) { while (*q == ' ') q++; if (*q) pixN[k] = constrain(numero(q), 0, PIX_MAX); }
    else if (s[1] == 'S') pixSeg = constrain(numero(q), 0, modoDmx ? 255 : 64);
    else if (s[1] == 'O') pixOrden = constrain(numero(q), 0, 2);
    else if (modoDmx) {                                       // PD dirección canales  (p. ej. PD 1 3)
      dmxDir = constrain(numero(q), 1, 512);
      while (*q == ' ') q++;
      if (*q) { int c = numero(q); dmxCh = (c == 1 || c == 4) ? c : 3; }
    } else return false;
    if (modoDmx) { pixN[1] = pixN[2] = pixN[3] = 0; dmxAjustar(); }
    pixGuardar();
    return true;
  }
  if (!strncmp(s, "SA ", 3)) {                                 // SA n 0|1|2: salida de AP OUTPUT
    const char* q = s + 3;
    int n = numero(q), v = numero(q);
    if (n < 1 || n > IO_N * 7 || v < 0 || v > 2) return false;
    aplicarAccion(v == 2 ? 7 : (v ? 5 : 6), n);
    return true;
  }
  if (!strncmp(s, "EA ", 3)) {                                 // EA n acc val [modo] / EA n -: regla de una entrada
    const char* q = s + 3;
    int n = numero(q);
    if (n < 1 || n > IO_N * 8) return false;
    while (*q == ' ') q++;
    Regla r{ACC_NADA, 0, 0};
    if (*q != '-') {
      int acc = numero(q), val = numero(q);
      while (*q == ' ') q++;
      int modo = *q ? numero(q) : 0;
      if (acc < 0 || acc > 8 || val < 0 || val > 255) return false;
      r = Regla{(uint8_t)acc, (uint8_t)val, (uint8_t)(modo ? 1 : 0)};
    }
    reglas[n - 1] = r;
    pref.putBytes("reglas", reglas, sizeof(reglas));
    return true;
  }
  if (!strncmp(s, "VIVO", 4)) {                               // VIVO 0|1: control en vivo por Art-Net / sACN
    vivoActivo = atoi(s + 4) != 0 || !s[4];
    pref.putBool("vivo", vivoActivo);
    tVivo = 0;
    if (WiFi.isConnected()) vivoIniciar();
    return true;
  }
  if (!strncmp(s, "UNI", 3)) {                                // UNI n: universo inicial
    vivoUni = constrain(atoi(s + 3), 0, 32767);
    pref.putUShort("uni", vivoUni);
    tVivo = 0;
    if (WiFi.isConnected()) vivoIniciar();
    return true;
  }
  if (!strncmp(s, "HA", 2) && (s[2] == ' ' || !s[2])) {        // HA 0|1: aparecer o no en Home Assistant
    haActivo = atoi(s + 2) != 0 || !s[2];
    pref.putBool("ha", haActivo);
    haPublicar();
    return true;
  }
  if (!strncmp(s, "APRENDER", 8)) { iniciarDiag(true); return true; }
  if (!strncmp(s, "MODELO", 6)) {
    String m = resto(s + 6);
    if (!hayBase || !m.length()) return false;
    char b[16] = {0};
    strncpy(b, m.c_str(), 16);
    eepEscribir(3, b, 16);
    memcpy(baseModelo, b, 16); baseModelo[16] = 0;
    modoInd = !strncmp(baseModelo, "LL-IND", 6);
    modoDmx = !strncmp(baseModelo, "LL-DMX", 6);
    modoPix = modoDmx || !strncmp(baseModelo, "LL-PIX", 6);
    pedirReinicio = true;                                   // frecuencias y Home Assistant según el módulo
    return true;
  }
  const char* p = s + 1;
  char c = s[0];
  switch (c) {
    case 'O':                                     // "O a b", "O a" (solo el 1) u "O - b" (solo el 2)
      while (*p == ' ') p++;
      if (*p == '-') p++; else cfg.cc[0] = constrain(numero(p), 0, 100);
      while (*p == ' ') p++;
      if (*p) cfg.cc[1] = constrain(numero(p), 0, 100);
      break;
    case 'Y': cfg.auxModo = numero(p) ? 1 : 0; break;
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
      if (*p == '-') cfg.horaOn = cfg.horaOff = -1;
      else { int a = numero(p), b = numero(p), c2 = numero(p), d = numero(p); cfg.horaOn = a * 60 + b; cfg.horaOff = c2 * 60 + d; }
      break;
    case 'A': {
      int i = numero(p);
      if (i < 0 || i > 7) return false;
      while (*p == ' ') p++;
      Prog& g = cfg.prog[i];
      if (*p == '-') { g = Prog{}; break; }
      int dias = numero(p), h = numero(p), m = numero(p), acc = numero(p), val = numero(p);
      if (h > 23 || m > 59 || acc > 8) return false;
      g = Prog{1, (uint8_t)(dias & 127), (uint8_t)h, (uint8_t)m, (uint8_t)acc, (uint8_t)val};
    } break;
    case 'T': { int an = numero(p), me = numero(p), di = numero(p), h = numero(p), mi = numero(p), se = numero(p);
                if (an > 2000) ponerHora(an, me, di, h, mi, se); } return true;
    case 'Z': { String z = resto(p); if (!z.length() || z.length() > 40) return false;
                tz = z; pref.putString("tz", tz); configTzTime(tz.c_str(), "pool.ntp.org", "time.google.com"); } return true;
    case 'D': { String n = resto(p); if (!nombreValido(n)) return false;
                nombre = n; pref.putString("nombre", nombre); pedirReinicio = true; } return true;
    case 'G': { String g = resto(p); if (!nombreValido(g)) return false;
                grupo = g; pref.putString("grupo", grupo); mqIniciar(); } return true;
    case 'W': { String r = resto(p);
                if (r == "-") { wifiRed = wifiClave = ""; }
                else { wifiRed = campo(r); wifiClave = r; }
                pref.putString("red", wifiRed); pref.putString("wclave", wifiClave); pedirReinicio = true; } return true;
    case 'Q': { String r = resto(p);
                if (r == "-" || !r.length()) { mqUri = mqUsr = mqClave = ""; }
                else { mqUri = campo(r); mqUsr = campo(r); mqClave = r; }
                pref.putString("mquri", mqUri); pref.putString("mqusr", mqUsr); pref.putString("mqclave", mqClave);
                mqIniciar(); } return true;
    case 'K': clave = resto(p); pref.putString("clave", clave); return true;   // por red solo llega ya autorizado
    case 'S': guardarEscena(numero(p)); return false;
    case 'R': cargarEscena(numero(p)); break;
    case '@': {                                   // "@grupo orden"
      String r = resto(p);
      int i = r.indexOf(' ');
      if (i < 1) return false;
      String g = r.substring(0, i), orden = r.substring(i + 1);
      orden.trim();
      if (!ordenDeGrupo(orden.c_str())) return false;   // solo luces
      enviarGrupo(g, orden.c_str());
      if (g == "*" || g == grupo) ejecutar(orden.c_str(), true);
    } return true;
    case 'J': cfg.limiteA = constrain(numero(p), 1, 25); inaLimite(); break;
    case 'F': if (falla != SIN_FALLA) Serial.println("Falla borrada"); falla = SIN_FALLA; disparos = 0; return true;
    case 'U': whTotal = whHoy = whGuardado = 0; pref.putDouble("wh", 0); return true;
    case '!': pedirReinicio = true; return false;
    default: return false;
  }
  marcar();
  return true;
}

// ---------------- puerto USB ----------------
char linea[128];
uint8_t nl = 0;
void leerSerie() {
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n' || ch == '\r') {
      if (nl) {
        linea[nl] = 0;
        nl = 0;
        if (linea[0] == 'I') Serial.println(VERSION " - LetreroLab AP-1: 4 canales + 2 focos CC + AUX");
        else { if (ejecutar(linea, false)) mqPublicar(); Serial.println(estadoJSON()); }
      }
    } else if (nl < sizeof(linea) - 1) {
      linea[nl++] = ch;
    }
  }
}

// ---------------- servidor web ----------------
bool autorizado() {
  if (!clave.length()) return true;
  if (web.authenticate("letrerolab", clave.c_str())) return true;
  web.requestAuthentication(BASIC_AUTH, "LetreroLab");
  return false;
}
void rutaInicio() {
  if (!autorizado()) return;
  web.sendHeader("Cache-Control", "no-cache");
  web.send_P(200, "text/html; charset=utf-8", PAGINA);
}
void rutaApi() {
  if (!autorizado()) return;
  web.sendHeader("Access-Control-Allow-Origin", "*");
  if (web.hasArg("c")) {
    String c = web.arg("c");
    c.trim();
    if (c.length() && c.length() < 120 && ejecutar(c.c_str(), true)) mqPublicar();
  }
  web.send(200, "application/json", estadoJSON());
}
void rutaVecinos() {
  if (!autorizado()) return;
  String s = "[";
  bool primero = true;
  for (auto& v : vecinos) {
    if (!v.visto || millis() - v.visto > 60000) continue;
    if (!primero) s += ',';
    primero = false;
    s += "{\"nom\":\"" + v.nombre + "\",\"g\":\"" + v.grupo + "\",\"ip\":\"" + v.ip.toString() + "\"}";
  }
  s += ']';
  web.sendHeader("Access-Control-Allow-Origin", "*");
  web.send(200, "application/json", s);
}
void rutaRedes() {
  if (!autorizado()) return;
  int n = WiFi.scanNetworks();
  String s = "[";
  for (int i = 0; i < n && i < 20; i++) {
    if (i) s += ',';
    String r = WiFi.SSID(i);
    r.replace("\"", "'");
    s += "{\"r\":\"" + r + "\",\"s\":" + String(WiFi.RSSI(i)) + "}";
  }
  s += ']';
  WiFi.scanDelete();
  web.send(200, "application/json", s);
}
void rutaOtaFin() {
  if (!autorizado()) return;
  bool ok = !Update.hasError();
  web.send(200, "text/plain", ok ? "OK, reiniciando" : "ERROR en la actualizacion");
  if (ok) pedirReinicio = true;
}
void rutaOtaDatos() {
  if (clave.length() && !web.authenticate("letrerolab", clave.c_str())) return;
  HTTPUpload& u = web.upload();
  if (u.status == UPLOAD_FILE_START) { apagarTodo(); Update.begin(UPDATE_SIZE_UNKNOWN); }
  else if (u.status == UPLOAD_FILE_WRITE) Update.write(u.buf, u.currentSize);
  else if (u.status == UPLOAD_FILE_END) Update.end(true);
}
void rutaOtra() {                         // portal cautivo: cualquier dirección abre la app
  web.sendHeader("Location", String("http://") + WiFi.softAPIP().toString() + "/");
  web.send(302, "text/plain", "");
}

// ---------------- Wi-Fi ----------------
void iniciarAP() {
  modoAP = true;
  WiFi.mode(wifiRed.length() ? WIFI_AP_STA : WIFI_AP);
  String ssid = "LetreroLab-" + nombre.substring(nombre.length() - 4);
  WiFi.softAP(ssid.c_str(), "letrerolab");
  dns.start(53, "*", WiFi.softAPIP());
  Serial.printf("Modo configuracion: red %s clave letrerolab -> http://%s\n", ssid.c_str(),
                WiFi.softAPIP().toString().c_str());
}
void iniciarWifi() {
  WiFi.setHostname(nombre.c_str());
  if (!wifiRed.length()) { iniciarAP(); return; }
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(wifiRed.c_str(), wifiClave.c_str());
  tInicioWifi = millis();
}

// ---------------- botón ----------------
void leerBoton() {
  static bool antes = HIGH;
  static uint32_t tP = 0;
  static uint8_t largo = 0;
  bool ahora = digitalRead(PIN_MODO);
  uint32_t t = millis();
  if (antes == HIGH && ahora == LOW) { tP = t; largo = 0; }
  if (ahora == LOW && largo == 0 && t - tP > 1000) { largo = 1; cfg.vel = (cfg.vel + 2) % 10; marcar(); }
  if (ahora == LOW && largo == 1 && t - tP > 3000) { largo = 2; cfg.encendido ^= 1; marcar(); }
  if (ahora == LOW && largo == 2 && t - tP > 10000) {          // 10 s: olvidar Wi-Fi y abrir la configuración
    largo = 3; ejecutar("W -", false);
  }
  if (antes == LOW && ahora == HIGH && largo == 0 && t - tP > 30) {
    if (falla != SIN_FALLA) { falla = SIN_FALLA; disparos = 0; }   // con falla, el primer toque solo la borra
    else { cfg.modo = (cfg.modo + 1) % N_MODOS; paso = 0; marcar(); }
  }
  antes = ahora;
}

void teclaIR(uint32_t k) {
  static uint32_t ultima = 0;
  if (k == 0xFFFFFFFF) k = ultima; else ultima = k;
  uint8_t* col = cfg.color;
  switch (k) {
    case 0xF7C03F: cfg.encendido = 1; break;
    case 0xF740BF: cfg.encendido = 0; break;
    case 0xF700FF: cfg.brillo = min(100, cfg.brillo + 10); break;
    case 0xF7807F: cfg.brillo = max(10, cfg.brillo - 10); break;
    case 0xF720DF: cfg.modo = 6; col[0] = 255; col[1] = 0; col[2] = 0; col[3] = 0; break;
    case 0xF7A05F: cfg.modo = 6; col[0] = 0; col[1] = 255; col[2] = 0; col[3] = 0; break;
    case 0xF7609F: cfg.modo = 6; col[0] = 0; col[1] = 0; col[2] = 255; col[3] = 0; break;
    case 0xF7E01F: cfg.modo = 6; col[0] = 255; col[1] = 255; col[2] = 255; col[3] = 255; break;
    case 0xF7D02F: cfg.modo = 8; break;
    case 0xF7F00F: cfg.modo = 2; break;
    case 0xF7C837: cfg.modo = 4; break;
    case 0xF7E817: cfg.modo = 7; break;
    default: Serial.printf("IR desconocido: %08lX\n", (unsigned long)k); return;
  }
  marcar();
  mqPublicar();
}

// ---------------- tareas periódicas ----------------
void revisarHorarios() {
  static int16_t ultimoMin = -1;
  uint8_t wd = 0;
  int16_t m = minutosAhora(&wd);
  porHorario = dentroVentana(m);
  if (m < 0 || m == ultimoMin) return;
  ultimoMin = m;
  bool cambio = false;
  for (auto& p : cfg.prog)
    if (p.activo && (p.dias & (1 << wd)) && p.h * 60 + p.m == m) { aplicarAccion(p.acc, p.val); cambio = true; }
  if (cambio) mqPublicar();
}
void vivoGuardar(uint16_t uni, const uint8_t* d, int n) {
  if (uni < vivoUni || uni - vivoUni >= VIVO_UNIS || n <= 0) return;
  uint16_t paso = modoDmx ? 512 : 510;                       // pixeles: 170 LED RGB completos por universo
  memcpy(vivoDatos + (uint32_t)(uni - vivoUni) * paso, d, min<int>(n, paso));
  tVivo = millis();
  if (!tVivo) tVivo = 1;                                    // 0 = sin datos
  vivoPaquetes++;
}
void vivoAplicar() {                                         // base e IND
  for (uint8_t c = 0; c < 4; c++) salida(c, vivoDatos[c]);
  if (!modoInd) {
    uint8_t maxb = cfg.eco ? min<uint8_t>(cfg.brillo, 60) : cfg.brillo;
    for (uint8_t k = 0; k < 2; k++) focoCC(k, (uint32_t)GAMMA12[(uint16_t)vivoDatos[4 + k] * maxb / 100] * factor / 1000);
  }
}
void artResponder(IPAddress a) {                             // ArtPollReply: así los programas encuentran el equipo
  uint8_t r[239] = {0};
  memcpy(r, "Art-Net", 8);
  r[9] = 0x21;                                               // OpPollReply
  IPAddress ip = WiFi.localIP();
  for (uint8_t i = 0; i < 4; i++) r[10 + i] = ip[i];
  r[14] = 0x36; r[15] = 0x19;                                // puerto 6454
  r[17] = 14;                                                // versión
  r[18] = (vivoUni >> 8) & 0x7F; r[19] = (vivoUni >> 4) & 0x0F;
  r[23] = 0xD0;                                              // indicadores normales, dirección por el equipo
  strncpy((char*)r + 26, nombre.c_str(), 17);
  snprintf((char*)r + 44, 64, "LetreroLab %s %s", VERSION, baseModelo);
  snprintf((char*)r + 108, 64, "#0001 [%04lu] OK", (unsigned long)(vivoPaquetes % 10000));
  r[173] = 1;                                                // un puerto
  r[174] = 0x80;                                             // salida DMX512
  r[182] = 0x80;                                             // transmitiendo
  r[190] = vivoUni & 0x0F;
  uint8_t mac[6]; WiFi.macAddress(mac); memcpy(r + 201, mac, 6);
  for (uint8_t i = 0; i < 4; i++) r[207 + i] = ip[i];
  r[211] = 1; r[212] = 0x08;                                 // dirección de 15 bits
  udpArt.beginPacket(a, ART_PUERTO); udpArt.write(r, sizeof(r)); udpArt.endPacket();
}
void vivoIniciar() {                                         // al conectarse a la red
  udpArt.stop(); udpSacn.stop();
  if (!vivoActivo) return;
  udpArt.begin(ART_PUERTO);
  udpSacn.beginMulticast(IPAddress(239, 255, vivoUni >> 8, vivoUni & 0xFF), SACN_PUERTO);   // y unicast
}
void revisarVivo() {
  if (!vivoActivo) return;
  static uint8_t b[640];
  for (uint8_t k = 0; k < 16; k++) {                         // varios universos por vuelta
    int n = udpArt.parsePacket();
    if (n <= 0) break;
    n = udpArt.read(b, sizeof(b));
    if (n < 12 || memcmp(b, "Art-Net", 8)) continue;
    uint16_t op = b[8] | (b[9] << 8);
    if (op == 0x5000 && n > 18) vivoGuardar(((b[15] & 0x7F) << 8) | b[14], b + 18, min<int>((b[16] << 8) | b[17], n - 18));
    else if (op == 0x2000) artResponder(udpArt.remoteIP());
  }
  for (uint8_t k = 0; k < 16; k++) {
    int n = udpSacn.parsePacket();
    if (n <= 0) break;
    n = udpSacn.read(b, sizeof(b));
    if (n < 126 || memcmp(b + 4, "ASC-E1.17", 9) || b[21] != 0x04 || b[43] != 0x02 || b[117] != 0x02) continue;
    if (b[112] & 0x40) { tVivo = 0; continue; }               // el programa terminó: vuelven los efectos
    if (b[125] != 0) continue;                               // solo niveles (código de inicio 0)
    vivoGuardar((b[113] << 8) | b[114], b + 126, min<int>(((b[123] << 8) | b[124]) - 1, n - 126));
  }
}
void revisarUDP() {
  int n = udp.parsePacket();
  if (n <= 0 || n > 150) { if (n > 0) udp.clear(); return; }
  char b[160];
  n = udp.read(b, sizeof(b) - 1);
  b[n] = 0;
  if (strncmp(b, "LL1 A ", 6) == 0) {                     // anuncio de otro equipo
    char nom[32] = "", gr[32] = "";
    if (sscanf(b + 6, "%31s %31s", nom, gr) < 2 || nombre == nom) return;
    Vecino* libre = nullptr;
    for (auto& v : vecinos) {
      if (v.nombre == nom) { libre = &v; break; }
      if (!libre && (!v.visto || millis() - v.visto > 120000)) libre = &v;
    }
    if (libre) { libre->nombre = nom; libre->grupo = gr; libre->ip = udp.remoteIP(); libre->visto = millis(); }
  } else if (strncmp(b, "LL1 C ", 6) == 0) {              // orden de grupo
    char gr[32] = "";
    int usado = 0;
    if (sscanf(b + 6, "%31s %n", gr, &usado) < 1 || !usado) return;
    const char* orden = b + 6 + usado;
    if ((strcmp(gr, "*") == 0 || grupo == gr) && ordenDeGrupo(orden)) {
      if (ejecutar(orden, true)) mqPublicar();
    }
  }
}

void setup() {
  for (uint8_t c = 0; c < 4; c++) { ledcAttachChannel(PWM_PIN[c], PWM_HZ, PWM_BITS, c); pwm(c, 0); }
  for (uint8_t k = 0; k < 2; k++) { ledcAttachChannel(CC_PIN[k], CC_HZ, PWM_BITS, 4 + k); focoCC(k, 0); }
  pinMode(PIN_AUX, OUTPUT); digitalWrite(PIN_AUX, LOW);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_MODO, INPUT_PULLUP);
  pinMode(PIN_IR, INPUT_PULLUP);
  for (uint16_t i = 0; i < 256; i++) GAMMA12[i] = (uint16_t)(powf(i / 255.0f, 2.2f) * PWM_MAX + 0.5f);   // 255 = 100 %
  pinMode(PIN_ALERTA, INPUT_PULLUP);
  Serial.begin(115200);
  colaMq = xQueueCreate(6, 128);
  pref.begin("letrerolab", false);
  cargar();
  randomSeed(esp_random());

  setenv("TZ", tz.c_str(), 1);
  tzset();
  Wire.begin(PIN_SDA, PIN_SCL, 100000);
  Wire.beginTransmission(0x68);
  hayRTC = (Wire.endTransmission() == 0);
  if (hayRTC) rtcLeer();
  iniciarSensores();
  ioBuscar();
  leerBase();
  if (modoInd) for (uint8_t c = 0; c < 4; c++) { ledcChangeFrequency(PWM_PIN[c], IND_HZ, PWM_BITS); dutyActual[c] = 9999; pwm(c, 0); }
  if (modoPix) { pixLeer(); pixIniciar(); }
  hayOLED = i2cPresente(OLED);
  if (hayOLED) oledIniciar();
  hayLux = i2cPresente(0x23);
  if (hayLux) { Wire.beginTransmission(0x23); Wire.write(0x10); Wire.endTransmission(); }   // BH1750 continuo
  Serial.printf("Base: %s  modelo \"%s\"  serie %s  %lu h\n", hayBase ? "si" : "NO", baseModelo, baseSerie,
                (unsigned long)baseHoras);
  attachInterrupt(PIN_ALERTA, alertaISR, FALLING);
  Serial.printf("Medidor INA238: %s  Temperatura TMP1075: %s\n", hayINA ? "si" : "no", hayTMP ? "si" : "no");

  attachInterrupt(PIN_IR, irISR, FALLING);
  iniciarWifi();
  configTzTime(tz.c_str(), "pool.ntp.org", "time.google.com");

  web.on("/", rutaInicio);
  web.on("/api", rutaApi);
  web.on("/vecinos", rutaVecinos);
  web.on("/redes", rutaRedes);
  web.on("/ota", HTTP_POST, rutaOtaFin, rutaOtaDatos);
  web.onNotFound([]() { if (modoAP) rutaOtra(); else web.send(404, "text/plain", "no existe"); });
  web.begin();
  udp.begin(UDP_PUERTO);

  ArduinoOTA.setHostname(nombre.c_str());
  if (clave.length()) ArduinoOTA.setPassword(clave.c_str());
  ArduinoOTA.onStart([]() { apagarTodo(); ioApagar(); });
  Serial.println(VERSION);
}

void loop() {
  uint32_t t = millis();
  static bool conectadoAntes = false;
  bool conectado = WiFi.isConnected();
  if (conectado && !conectadoAntes) {                      // recién conectado
    MDNS.begin(nombre.c_str());
    MDNS.addService("http", "tcp", 80);
    ArduinoOTA.begin();
    if (modoAP) {                                          // ya hay red: se apaga la red de configuración
      dns.stop(); WiFi.softAPdisconnect(true); WiFi.mode(WIFI_STA); modoAP = false;
    }
    mqIniciar();
    vivoIniciar();
    Serial.printf("Wi-Fi %s  IP %s  http://%s.local\n", wifiRed.c_str(), WiFi.localIP().toString().c_str(), nombre.c_str());
  }
  conectadoAntes = conectado;
  if (conectado) tInicioWifi = t;
  else if (!modoAP && t - tInicioWifi > 30000) iniciarAP();   // 30 s sin red: abrir la red de configuración

  if (modoAP) dns.processNextRequest();
  web.handleClient();
  if (conectado) ArduinoOTA.handle();
  leerSerie();
  leerBoton();
  revisarUDP();
  revisarVivo();
  ioActualizar(t);
  if (irListo) { irListo = false; teclaIR(irCodigo); }
  char buf[128];
  while (xQueueReceive(colaMq, buf, 0) == pdTRUE) {     // varias órdenes por mensaje, una por renglón
    bool cambio = false;
    for (char* l = strtok(buf, "\n"); l; l = strtok(nullptr, "\n")) cambio |= ejecutar(l, true);
    if (cambio) mqPublicar();
  }

  revisarProteccion();
  static uint32_t tRevisa = 0, tAnuncio = 0, tRtc = 0, tMed = 0, tPub = 0;
  if (t - tMed >= 250) {                                   // mediciones 4 veces por segundo
    float dt = (t - tMed) / 1000.0f;
    tMed = t;
    leerSensores();
    if (dt < 5) sumarEnergia(dt);
  }
  if (mqConectado && t - tPub > 30000) { tPub = t; mqPublicar(); }     // telemetría cada 30 s
  if (t - tRevisa > 1000) {
    tRevisa = t;
    static int8_t diaAnterior = -1;                         // kWh de hoy: se reinicia a medianoche
    uint8_t wd;
    if (minutosAhora(&wd) >= 0) { if (diaAnterior >= 0 && wd != diaAnterior) whHoy = 0; diaAnterior = wd; }
    revisarHorarios();
    leerLuz();
    if (cfg.ldr && hayLux && !isnan(lux)) {             // solo de noche, con histéresis
      if (lux < cfg.umbral) porLuz = true;
      else if (lux > cfg.umbral * 1.5f + 2) porLuz = false;
    } else porLuz = true;
    if (!isnan(tTarjeta)) { if (tTarjeta > 45) auxVent = true; else if (tTarjeta < 38) auxVent = false; }
    vigilarConsumo();
    static uint32_t segundos = 0;                       // horas de uso de la base (garantía)
    if (hayBase && ++segundos >= 3600) { segundos = 0; baseHoras++; eepEscribir(32, &baseHoras, 4); }
    if (hayOLED) {
      char l[22];
      oledTexto(0, nombre.c_str());
      oledTexto(1, WiFi.isConnected() ? WiFi.localIP().toString().c_str() : (modoAP ? "Configurar: Wi-Fi" : "Sin red"));
      snprintf(l, 22, "%.1fV %.2fA %.0fW", vin, amp, watts); oledTexto(2, l);
      snprintf(l, 22, "%.0fC  hoy %.2fkWh", isnan(tTarjeta) ? 0.0f : tTarjeta, whHoy / 1000); oledTexto(3, l);
      snprintf(l, 22, "%s %s", cfg.encendido ? "ON " : "OFF", NOMBRE[cfg.modo]); oledTexto(4, l);
      if (falla) snprintf(l, 22, "FALLA: %s", FALLA[falla]);
      else if (diagSalida >= 0) snprintf(l, 22, "Probando salida %d..", diagSalida + 1);
      else if (aviso.length()) snprintf(l, 22, "%s", aviso.c_str());
      else snprintf(l, 22, "CC1 %u%%  CC2 %u%%", cfg.cc[0], cfg.cc[1]);
      oledTexto(5, l);
      const char* letra = "-OACBH";                     // sin probar, OK, abierta, corto, baja, alta
      snprintf(l, 22, "Sal %c%c%c%c  Focos %c%c", letra[prueba[0].est], letra[prueba[1].est], letra[prueba[2].est],
               letra[prueba[3].est], letra[prueba[4].est], letra[prueba[5].est]);
      oledTexto(6, l);
      snprintf(l, 22, "Base %.6s %luh", baseSerie[0] ? baseSerie + 26 : "------", (unsigned long)baseHoras); oledTexto(7, l);
      oledMostrar();
    }
  }
  if (t - tAnuncio > 10000) { tAnuncio = t; anunciar(); }
  if (hayRTC && conectado && horaValida() && (tRtc == 0 || t - tRtc > 6UL * 3600000UL)) {   // copia la hora de internet al DS3231
    tRtc = t;
    time_t a = time(nullptr);
    struct tm tm;
    localtime_r(&a, &tm);
    rtcEscribir(tm);
  }
  if (sucio && t - tSucio > 3000) guardarAhora();
  if (pedirReinicio) { if (sucio) guardarAhora(); delay(300); ESP.restart(); }

  bool activo = cfg.encendido && porHorario && porLuz;
  if (modoInd) digitalWrite(PIN_AUX, activo ? HIGH : LOW);     // contactor 1: sigue al encendido de la luz
  else if (modoDmx) digitalWrite(PIN_AUX, (dmxCuadros >> 3) & 1);  // LED DMX: parpadea mientras se transmite
  else digitalWrite(PIN_AUX, cfg.auxModo ? auxVent : ((activo && cfg.aux) ? HIGH : LOW));
  uint16_t per = falla ? 80 : (modoAP ? 150 : (conectado ? (activo ? 1000 : 250) : 500));
  digitalWrite(PIN_LED, falla ? ((t / per) % 6 < 2) : ((t / per) & 1));    // falla: doble destello
  static uint32_t tRampa = 0;
  if (diagSalida >= 0) {
    diagnostico(t);
    tRampa = t;
  } else if (activo && falla == SIN_FALLA) {
    uint32_t r = min<uint32_t>(1000, (t - tRampa) * 1000 / 600);          // arranque suave de 0.6 s
    factor = (uint16_t)(r * factorTemperatura() / 1000);
    bool enVivo = vivo();
    if (enVivo && !modoPix) vivoAplicar();
    else if (!modoPix) efectos(t);
    if (!modoInd && !modoPix && !enVivo) for (uint8_t k = 0; k < 2; k++) focoCC(k, (uint32_t)GAMMA12[cfg.cc[k] * 255 / 100] * factor / 1000);
  } else {
    tRampa = t;
    factor = 0;
    apagarTodo();
  }
  if (modoInd) { focoCC(0, cfg.cc[0] ? PWM_MAX : 0); focoCC(1, 0); }   // contactor 2: manual (O), no atenúa
  if (modoPix && t - tPix >= (factor ? 33u : 500u)) { tPix = t; pixEnviar(t); }   // 30 cuadros/s; apagado: negro cada 0.5 s
}
