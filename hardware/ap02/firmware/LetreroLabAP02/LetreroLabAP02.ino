/*
  LetreroLab AP-0.2  -  programa del ESP32-C3-WROOM-02 (Arduino-ESP32 3.x, placa "ESP32C3 Dev Module",
                        "USB CDC On Boot: Enabled")
  -------------------------------------------------------------------------------------------------
  Salidas:  4 canales de potencia (IO4..IO7, PWM de 12 bits a 19.5 kHz, sin zumbido)
            relevador para focos de 127/240 V (IO1)
  Control:  - App web incluida en el módulo (Wi-Fi): http://<nombre>.local o la IP
            - Puerto USB-C (mismo protocolo de texto que el AP-0.1, 115200)
            - Botón MODO (IO9): toque = modo, 1 s = velocidad, 3 s = encender/apagar, 10 s = borrar Wi-Fi
            - Control remoto IR de tiras (NEC), sensor de luz (LDR), reloj DS3231 opcional (I2C)
  Casa:     - Hora de internet (NTP) con zona horaria; si hay DS3231 la conserva sin internet
            - 8 horarios por día de la semana ("apagar todo a las 21:00")
            - Grupos por la red local: "@* P0" apaga todos los letreros/luces de la casa
            - MQTT opcional (servidor en la nube) para controlar fuera de casa
            - Actualización por Wi-Fi (página "Ajustes" o ArduinoOTA), protegida con clave

  Protocolo (una línea por orden; también por /api?c=... y MQTT):
     M n  modo 0..9         V n  velocidad 0..9      B n  brillo 0..100     C r g b w  color 0..255
     N n  canales 1..4      P 0|1 todo apagado/encendido                   X 0|1 relevador (focos)
     E 0|1 ahorro (máx 60%) L 0|1 [umbral] solo de noche con LDR           S n / R n  guardar/cargar escena 0..3
     H hh:mm hh:mm  ventana diaria encendido   H -  sin ventana
     A i dias hh:mm acc val  horario i=0..7, dias=suma(1=dom,2=lun,4=mar..64=sab; 127=todos),
                             acc 0=apagar 1=encender 2=focos(val 0/1) 3=escena val 4=brillo val     A i -  borrar
     T aaaa-mm-dd hh:mm:ss  poner hora     Z tz  zona horaria POSIX (p. ej. CST6 = centro de México)
     D nombre   nombre del equipo (y nombre.local)        G grupo   grupo (p. ej. planta-alta)
     W red,clave  conectar a Wi-Fi     W -  olvidar Wi-Fi  Q uri[,usuario,clave]  MQTT   Q -  sin MQTT
     K clave  clave de la app/OTA (vacío = sin clave)      @ grupo orden  enviar a un grupo (* = todos)
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
#include "pagina.h"

#define VERSION "AP-0.2 fw 1.0"

// ---------------- pines de la placa AP-0.2 ----------------
const uint8_t PWM_PIN[4] = {4, 5, 6, 7};   // CH1..CH4 (drivers UCC27524 -> MOSFET)
const uint8_t PIN_RELE = 1;                // AO3400 -> bobina del relevador
const uint8_t PIN_MODO = 9;                // botón BOOT/MODO (a GND)
const uint8_t PIN_IR = 3;                  // receptor IR (J6-5)
const uint8_t PIN_LED = 10;                // LED de estado (a GND con 1k)
const uint8_t PIN_LDR = 0;                 // LDR a GND con pull-up de 10k (J6-6)
const uint8_t PIN_SDA = 2, PIN_SCL = 8;    // I2C (J6-3/4): DS3231 opcional
const uint32_t PWM_HZ = 19531;             // 80 MHz / 4096
const uint8_t PWM_BITS = 12;
const uint16_t UDP_PUERTO = 4210;

const uint8_t N_MODOS = 10;
const char* const NOMBRE[N_MODOS] = {"FIJO", "SECUENCIA", "PARPADEO", "RESPIRAR", "SEC. SUAVE", "ALTERNADO",
                                     "COLOR", "ARCOIRIS", "FLASH", "VELA"};

struct Prog { uint8_t activo, dias, h, m, acc, val; };
struct Config {
  uint8_t firma, modo, vel, brillo, canales, encendido, aux, eco, ldr;
  uint8_t color[4];
  int16_t horaOn, horaOff, umbral;
  Prog prog[8];
};
Config cfg;
const Config DEF = {0xB2, 1, 4, 100, 3, 1, 0, 0, 0, {255, 120, 0, 0}, -1, -1, 600, {}};

Preferences pref;
String nombre, grupo, tz, wifiRed, wifiClave, mqUri, mqUsr, mqClave, clave;
WebServer web(80);
DNSServer dns;
NetworkUDP udp;
esp_mqtt_client_handle_t mq = nullptr;
QueueHandle_t colaMq;
bool modoAP = false, hayRTC = false, sucio = false, mqConectado = false;
uint32_t tSucio = 0, t0 = 0, tInicioWifi = 0;
uint8_t paso = 0;
bool porHorario = true, porLuz = true;
uint16_t GAMMA12[256];

struct Vecino { String nombre, grupo; IPAddress ip; uint32_t visto; };
Vecino vecinos[16];

// ---------------- memoria (con retardo para no gastar la flash) ----------------
void marcar() { sucio = true; tSucio = millis(); }
void guardarAhora() { pref.putBytes("cfg", &cfg, sizeof(cfg)); sucio = false; }
void cargar() {
  if (pref.getBytes("cfg", &cfg, sizeof(cfg)) != sizeof(cfg) || cfg.firma != DEF.firma || cfg.modo >= N_MODOS) cfg = DEF;
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
void salida(uint8_t c, uint8_t nivel) {
  uint8_t maxb = cfg.eco ? min<uint8_t>(cfg.brillo, 60) : cfg.brillo;
  ledcWrite(PWM_PIN[c], GAMMA12[(uint16_t)nivel * maxb / 100]);
}
void todos(uint8_t v) { for (uint8_t c = 0; c < cfg.canales; c++) salida(c, v); }
void apagarTodo() { for (uint8_t c = 0; c < 4; c++) ledcWrite(PWM_PIN[c], 0); }

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
  s += ",\"lv\":"; s += analogRead(PIN_LDR) >> 2; s += ",\"u\":"; s += cfg.umbral;
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
  }
  marcar();
}

bool pedirReinicio = false;

// devuelve true si cambió algo (se publica el estado)
bool ejecutar(const char* s, bool remoto) {
  const char* p = s + 1;
  char c = s[0];
  switch (c) {
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
      if (h > 23 || m > 59 || acc > 4) return false;
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
      if (!orden.length() || orden[0] == '@' || strchr("WQKDZ!", orden[0])) return false;   // solo luces
      enviarGrupo(g, orden.c_str());
      if (g == "*" || g == grupo) ejecutar(orden.c_str(), true);
    } return true;
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
        if (linea[0] == 'I') Serial.println(VERSION " - LetreroLab, ESP32-C3, 4 canales + relevador");
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
  if (antes == LOW && ahora == HIGH && largo == 0 && t - tP > 30) { cfg.modo = (cfg.modo + 1) % N_MODOS; paso = 0; marcar(); }
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
    if ((strcmp(gr, "*") == 0 || grupo == gr) && orden[0] && orden[0] != '@' && !strchr("WQKDZ!", orden[0])) {
      if (ejecutar(orden, true)) mqPublicar();
    }
  }
}

void setup() {
  for (uint8_t c = 0; c < 4; c++) { ledcAttach(PWM_PIN[c], PWM_HZ, PWM_BITS); ledcWrite(PWM_PIN[c], 0); }
  pinMode(PIN_RELE, OUTPUT); digitalWrite(PIN_RELE, LOW);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_MODO, INPUT_PULLUP);
  pinMode(PIN_IR, INPUT_PULLUP);
  analogReadResolution(12);
  for (uint16_t i = 0; i < 256; i++) GAMMA12[i] = (uint16_t)(powf(i / 255.0f, 2.2f) * 4095.0f + 0.5f);
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
  ArduinoOTA.onStart([]() { apagarTodo(); });
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
  if (irListo) { irListo = false; teclaIR(irCodigo); }
  char buf[128];
  while (xQueueReceive(colaMq, buf, 0) == pdTRUE) if (ejecutar(buf, true)) mqPublicar();

  static uint32_t tRevisa = 0, tAnuncio = 0, tRtc = 0;
  if (t - tRevisa > 1000) {
    tRevisa = t;
    revisarHorarios();
    if (cfg.ldr) {                                     // más alto = más oscuro, con histéresis
      int l = analogRead(PIN_LDR) >> 2;
      if (l > cfg.umbral + 40) porLuz = true;
      else if (l < cfg.umbral - 40) porLuz = false;
    } else porLuz = true;
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
  digitalWrite(PIN_RELE, (activo && cfg.aux) ? HIGH : LOW);
  uint16_t per = modoAP ? 150 : (conectado ? (activo ? 1000 : 250) : 500);
  digitalWrite(PIN_LED, (t / per) & 1);
  if (activo) efectos(t); else apagarTodo();
}
