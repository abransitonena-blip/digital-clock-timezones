/* AP Rack 16 · programa del módulo (ESP32-C3, Arduino-ESP32 3.1.1). CONCEPTO: nada probado en una placa real.

   16 salidas protegidas (2 x TCA9554 0x20/0x21 -> 74HCT125 -> NCV8406A), 8 entradas de 12-30 V (TCA9554 0x22, activas en 0),
   LED de panel (TCA9554 0x23) y el enlace AP LINK (ap_link.h) por el SP3485 en UART1 a 250 kbit/s.

   Cadena: el módulo que no recibe SENSE de otro (primero del cable) es el CABEZA; los demás se numeran solos 2, 3... según el cable.
   Solo el cabeza abre el Wi-Fi y manda salidas; cada módulo muestra su posición en binario en los LED 1-2-4-8 (el 1 = cabeza).
   Si un módulo pierde al cabeza, sus salidas pasan a la máscara segura (de fábrica, todo apagado) en 1 s.

   Órdenes por USB (115200) o por red (/api?c=...&k=CLAVE): ver ap_rack.h. Además: CLAVE, CLAVE NUEVA, GUARDAR, FABRICA (solo por USB).
   Esto NO es una función de seguridad: no sustituye paro de emergencia, guardas ni relés de seguridad. */
#include <WiFi.h>
#include <WebServer.h>
#include <Preferences.h>
#include <Wire.h>
#include "esp_task_wdt.h"
#include "bootloader_random.h"
#include "ap_rack.h"

#define VERSION "AP Rack 1.0"
// Pines (ver rack16/gen/make.py)
const uint8_t P_VSENSE = 0, P_TX = 1, P_SDA = 2, P_RX = 3, P_INT = 4, P_SENSE_I = 5, P_SENSE_O = 6, P_SCL = 8, P_MODO = 9, P_DE = 10;
const uint8_t TCA_S1 = 0x20, TCA_S2 = 0x21, TCA_ENT = 0x22, TCA_LED = 0x23;
const uint32_t BAUDIOS_LINK = 250000;
const uint16_t VIN_MIN_MV = 10500, VIN_MAX_MV = 31500;     // aviso (no apaga nada): fuera de 12-30 V con margen
const uint16_t F_I2C = 1, F_SUBTENSION = 2, F_SOBRETENSION = 4;

Preferences pref;
WebServer web(80);
String claveCache;
uint16_t seguraLocal = 0;
uint32_t segundos = 0, tSeg = 0, tCom = 0, tLed = 0, tEnt = 0, tSerial = 0, tWifi = 0;
bool wifiActivo = false;
uint16_t salidasEscritas = 0xFFFF, ledsEscritos = 0xFFFF, fallasHw = 0;
String linea;

bool tcaEscribir(uint8_t dir, uint8_t reg, uint8_t v) { Wire.beginTransmission(dir); Wire.write(reg); Wire.write(v); return Wire.endTransmission() == 0; }
int tcaLeer(uint8_t dir) {
  Wire.beginTransmission(dir); Wire.write(0);
  if (Wire.endTransmission(false) != 0) return -1;
  if (Wire.requestFrom((int)dir, 1) != 1) return -1;
  return Wire.read();
}

struct HalEsp : aplink::HAL {
  void enviar(const uint8_t* p, size_t n) override {
    digitalWrite(P_DE, HIGH); delayMicroseconds(8);       // DE y /RE van juntos: al transmitir no se recibe
    Serial1.write(p, n); Serial1.flush();
    delayMicroseconds(12); digitalWrite(P_DE, LOW);
    tCom = millis();
  }
  bool senseEntra() override { return digitalRead(P_SENSE_I); }
  void senseSale(bool alto) override { digitalWrite(P_SENSE_O, alto ? HIGH : LOW); }
  uint32_t ms() override { return millis(); }
} hal;
aplink::Enlace* enlace = nullptr;

// ---------------- clave del equipo (igual que AP Control) ----------------
String claveNueva() {
  uint32_t r[2]; bootloader_random_enable(); esp_fill_random(r, sizeof(r)); bootloader_random_disable();
  uint64_t v = ((uint64_t)r[0] << 32 | r[1]) ^ ((uint64_t)esp_random() << 16) ^ ESP.getEfuseMac();
  char b[9]; snprintf(b, 9, "%08lu", (unsigned long)(v % 100000000ULL));
  claveCache = b; pref.putString("ckey", claveCache); return claveCache;
}
String claveAP() {
  if (claveCache.length() == 8) return claveCache;
  claveCache = pref.getString("ckey", "");
  return claveCache.length() == 8 ? claveCache : claveNueva();
}
bool claveCorrecta(const String& k) {
  String c = claveAP(); if (k.length() != c.length()) return false;
  uint8_t d = 0; for (size_t i = 0; i < c.length(); i++) d |= (uint8_t)(c[i] ^ k[i]);
  return d == 0;
}
String mac6() { uint64_t m = ESP.getEfuseMac(); char b[7]; snprintf(b, 7, "%02X%02X%02X", (uint8_t)(m >> 24), (uint8_t)(m >> 32), (uint8_t)(m >> 40)); return b; }
uint32_t uidModulo() { return (uint32_t)(ESP.getEfuseMac() & 0xFFFFFFFFULL); }

// ---------------- JSON, órdenes ----------------
String estadoJSON() {
  static char buf[4096];
  aprack::json(buf, sizeof buf, *enlace, VERSION, mac6().c_str(), segundos);
  return String(buf);
}
void hacerFabrica() { String ck = claveAP(); pref.clear(); pref.putString("ckey", ck); delay(100); ESP.restart(); }
bool ejecutar(String s, bool local) {
  s.trim(); if (!s.length()) return false;
  if (s.startsWith("GUARDAR")) { pref.putUShort("seg", seguraLocal); return true; }
  if (s.startsWith("CLAVE")) { if (!local) return false; Serial.printf("Clave del equipo: %s\n", (s.indexOf("NUEVA") > 0 ? claveNueva() : claveAP()).c_str()); return true; }
  if (s.startsWith("FABRICA")) { if (!local) return false; hacerFabrica(); }
  return aprack::orden(*enlace, s.c_str(), &seguraLocal);
}

// ---------------- Wi-Fi: solo en el cabeza ----------------
const char PAGINA[] PROGMEM =
  "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>AP Rack</title>"
  "<body style='font:16px system-ui;margin:16px'><h2>AP Rack 16</h2><div id=m>cargando…</div>"
  "<p style='color:#666'>Para controlar y configurar usa la Consola AP Base y conéctala por red a esta dirección con la clave de la etiqueta.</p>"
  "<script>async function f(){try{const j=await (await fetch('/api')).json();let h='<p><b>'+j.rol+'</b> · '+j.total+' módulo(s) · '+j.n+' salidas · '+j.ne+' entradas</p><table border=1 cellpadding=6 style=\"border-collapse:collapse\"><tr><th>Módulo</th><th>Salidas</th><th>Entradas</th><th>V</th><th>Enlace</th></tr>';"
  "for(const m of j.mods)h+='<tr><td>'+m.p+' ('+m.id+')</td><td>'+m.s.toString(2).padStart(m.ns,'0')+'</td><td>'+m.e.toString(2).padStart(m.ne,'0')+'</td><td>'+(m.v/1000).toFixed(1)+'</td><td>'+(m.ok?'ok':'sin respuesta')+'</td></tr>';"
  "document.getElementById('m').innerHTML=h+'</table>'}catch(e){document.getElementById('m').textContent='sin datos'}}f();setInterval(f,1500)</script>";
void rutas() {
  web.on("/", []() { web.send_P(200, "text/html; charset=utf-8", PAGINA); });
  web.on("/api", []() {
    web.sendHeader("Access-Control-Allow-Origin", "*");
    if (web.hasArg("c")) {
      if (!claveCorrecta(web.arg("k"))) { web.send(401, "application/json", "{\"err\":\"clave\"}"); return; }
      ejecutar(web.arg("c"), false);
    }
    web.send(200, "application/json", estadoJSON());
  });
}
void wifiSegunRol() {
  bool debe = enlace->rol() == aplink::Rol::CABEZA;
  if (debe && !wifiActivo) {
    WiFi.mode(WIFI_AP); WiFi.softAP(("APElectric-" + mac6()).c_str(), claveAP().c_str());
    web.begin(); wifiActivo = true;
    Serial.printf("Cabeza: red APElectric-%s, http://%s\n", mac6().c_str(), WiFi.softAPIP().toString().c_str());
  } else if (!debe && wifiActivo) {
    web.stop(); WiFi.mode(WIFI_OFF); wifiActivo = false;
  }
}

// ---------------- hardware ----------------
void aplicarSalidas(uint16_t s) {
  bool a = tcaEscribir(TCA_S1, 1, s & 0xFF), b = tcaEscribir(TCA_S2, 1, s >> 8);
  if (a && b) { salidasEscritas = s; fallasHw &= ~F_I2C; enlace->aplicadas(s); } else fallasHw |= F_I2C;
}
void ponerLeds(uint32_t t) {
  uint8_t pos = enlace->pos();
  uint8_t v = pos & 0x0F;                                   // posición en binario: P0 = 1, P1 = 2, P2 = 4, P3 = 8
  if ((t / 500) & 1) v |= 0x10;                              // RUN: parpadea 1 Hz
  if (fallasHw || (enlace->rol() == aplink::Rol::ESCLAVO && enlace->enSeguro()) || enlace->rol() == aplink::Rol::ESPERA) v |= 0x20;   // FALLA
  if (t - tCom < 120) v |= 0x40;                             // COM: hubo tramas
  if (enlace->rol() == aplink::Rol::CABEZA) v |= 0x80;       // CABEZA
  if (v != ledsEscritos && tcaEscribir(TCA_LED, 1, v)) ledsEscritos = v;
}
void leerEntradas() {
  int raw = tcaLeer(TCA_ENT);
  uint16_t vin = (uint16_t)(analogReadMilliVolts(P_VSENSE) * 11UL);   // divisor 100 k / 10 k
  if (raw < 0) fallasHw |= F_I2C; else if (!(fallasHw & F_I2C)) fallasHw &= ~F_I2C;
  fallasHw &= ~(F_SUBTENSION | F_SOBRETENSION);
  if (vin < VIN_MIN_MV) fallasHw |= F_SUBTENSION; else if (vin > VIN_MAX_MV) fallasHw |= F_SOBRETENSION;
  enlace->ponerLocales(raw < 0 ? 0 : (uint16_t)(~raw & 0xFF), fallasHw, vin);
}

void setup() {
  Serial.begin(115200); Serial.setTimeout(20);
  pref.begin("aprack", false);
  seguraLocal = pref.getUShort("seg", 0);
  pinMode(P_DE, OUTPUT); digitalWrite(P_DE, LOW);
  pinMode(P_SENSE_I, INPUT); pinMode(P_SENSE_O, OUTPUT); digitalWrite(P_SENSE_O, LOW);
  pinMode(P_INT, INPUT_PULLUP);
  analogReadResolution(12);
  Wire.begin(P_SDA, P_SCL, 400000);
  // las salidas arrancan apagadas: primero el valor, después la dirección (los pull-down de 10 k ya las mantienen apagadas)
  tcaEscribir(TCA_S1, 1, 0); tcaEscribir(TCA_S2, 1, 0); tcaEscribir(TCA_S1, 3, 0x00); tcaEscribir(TCA_S2, 3, 0x00);
  tcaEscribir(TCA_ENT, 3, 0xFF);
  tcaEscribir(TCA_LED, 1, 0); tcaEscribir(TCA_LED, 3, 0x00);
  Serial1.begin(BAUDIOS_LINK, SERIAL_8N1, P_RX, P_TX);
  aplink::Caps c; c.tipo = 1; c.nSal = 16; c.nEnt = 8;
  enlace = new aplink::Enlace(hal, uidModulo(), c, true);
  enlace->maskSegura(seguraLocal);
  esp_task_wdt_config_t w = {8000, 0, true};
  if (esp_task_wdt_reconfigure(&w) != ESP_OK) esp_task_wdt_init(&w);
  esp_task_wdt_add(nullptr);
  Serial.printf("%s · id %s · escuchando la cadena…\n", VERSION, mac6().c_str());
}

void loop() {
  uint32_t t = millis();
  while (Serial1.available()) enlace->recibir((uint8_t)Serial1.read());
  enlace->tick();
  if (t - tEnt >= 5) { tEnt = t; leerEntradas(); }
  uint16_t s = enlace->salidas();
  if (s != salidasEscritas || (fallasHw & F_I2C)) aplicarSalidas(s);
  if (t - tLed >= 50) { tLed = t; ponerLeds(t); }
  if (t - tSeg >= 1000) { tSeg += 1000; segundos++; wifiSegunRol(); }
  if (wifiActivo) web.handleClient();
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n' || ch == '\r') { if (linea.length()) { bool ok = ejecutar(linea, true); Serial.println(ok ? estadoJSON() : "?"); linea = ""; } }
    else if (linea.length() < 80) linea += ch;
  }
  esp_task_wdt_reset();
}
