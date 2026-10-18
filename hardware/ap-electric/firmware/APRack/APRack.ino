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
#include <ETH.h>
#include <SPI.h>
#include "esp_task_wdt.h"
#include "bootloader_random.h"
#include "ap_rack.h"
#include "modbus_tcp.h"

#define VERSION "AP Rack 1.1"
// Pines (ver rack16/gen/make.py)
const uint8_t P_VSENSE = 0, P_ETH_CS = 0, P_ETH_SCK = 7, P_ETH_MISO = 20, P_ETH_MOSI = 21, P_TX = 1, P_SDA = 2, P_RX = 3, P_INT = 4, P_SENSE_I = 5, P_SENSE_O = 6, P_SCL = 8, P_MODO = 9, P_DE = 10;
const uint8_t TCA_S1 = 0x20, TCA_S2 = 0x21, TCA_ENT = 0x22, TCA_LED = 0x23;      // AP Rack 16
const uint8_t TCA_E1 = 0x24, TCA_E2 = 0x25;                                      // AP Rack IN16 (entradas 1-8 y 9-16)
const uint8_t TCA_ENT2 = 0x24;                                                   // AP PLC C24: entradas 9-12 (P0-P3) y botón RUN/STOP (P4); el IN16 usa 0x24 y 0x25 pero NO tiene 0x20
const uint8_t ADS_A = 0x48, ADS_B = 0x49;                                        // AP Rack AI8 (canales 1-4 y 5-8)
const uint8_t PCA_LED = 0x40;                                                    // AP Rack LED8: PCA9685 (salidas 1-8 con brillo; entradas 1-8 en el TCA 0x22)
const uint8_t PCA_AO = 0x41;                                                     // AP Rack AO4: PCA9685 con A0 a 3.3 V (salidas 0-10 V); el LED8 usa 0x40
uint8_t pcaDir = PCA_LED, pcaPre = 5;                                           // dirección y prescaler del PCA9685 (5 = 1 kHz, 3 = 1.5 kHz)
enum Tipo : uint8_t { T_RACK16 = 1, T_IN16 = 2, T_AI8 = 3, T_LED8 = 4, T_RL4 = 5, T_AO4 = 6, T_PLC24 = 7 };   // T_RL4: 4 relés de 24 V (solo el expansor 0x20)
uint8_t tipoMod = T_RACK16;
uint16_t anaVal[8] = {}; uint8_t anaMascara = 0;      // anaMascara: bit i = el canal i tiene el puente de 4-20 mA (se informa mA)
uint8_t adsCanal = 0; uint32_t tAds = 0; bool adsEsperando = false;
const uint32_t BAUDIOS_LINK = 250000;
uint16_t VIN_MIN_MV = 10500, VIN_MAX_MV = 31500;           // aviso (no apaga nada): fuera de 12-30 V con margen (el RL4 usa 24 V ± 10 % con margen: ver setup)
const uint16_t F_I2C = 1, F_SUBTENSION = 2, F_SOBRETENSION = 4;

Preferences pref;
WebServer web(80);
String claveCache;
uint16_t seguraLocal = 0;
uint32_t segundos = 0, tSeg = 0, tCom = 0, tLed = 0, tEnt = 0, tSerial = 0, tWifi = 0;
bool ethArriba = false, botonPrevio = true; uint32_t tBoton = 0;   // Ethernet (W5500) y el botón RUN/STOP del AP PLC C24
WiFiServer modbus(502); WiFiClient clienteMb; uint8_t mbBuf[300]; size_t mbN = 0; uint32_t tMb = 0;
bool wifiActivo = false;
uint8_t dutyEscrito[8] = {}; bool pwmValido = false;
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
aprack::PlcRack plc;

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
  aprack::json(buf, sizeof buf, *enlace, VERSION, mac6().c_str(), segundos, &plc);
  return String(buf);
}
void hacerFabrica() { String ck = claveAP(); pref.clear(); pref.putString("ckey", ck); delay(100); ESP.restart(); }
bool ejecutar(String s, bool local) {
  s.trim(); if (!s.length()) return false;
  if (s.startsWith("GUARDAR")) { pref.putUShort("seg", seguraLocal); pref.putUChar("am", anaMascara); return true; }
  if (s.startsWith("AM ")) { if (tipoMod != T_AI8) return false; long m = s.substring(3).toInt(); if (m < 0 || m > 255) return false; anaMascara = (uint8_t)m; return true; }       // AM máscara: canales con puente de 4-20 mA
  if (s.startsWith("CLAVE")) { if (!local) return false; Serial.printf("Clave del equipo: %s\n", (s.indexOf("NUEVA") > 0 ? claveNueva() : claveAP()).c_str()); return true; }
  if (s.startsWith("FABRICA")) { if (!local) return false; hacerFabrica(); }
  bool ok = aprack::orden(*enlace, s.c_str(), &seguraLocal, &plc);
  if (ok && s.startsWith("PLC")) {                                       // el programa y su modo se recuerdan al reiniciar
    String a = s.substring(4); a.trim(); a.toUpperCase();
    if (a == "RUN" || a == "STOP") pref.putBool("plcrun", plc.run);
    else if (a == "BORRAR") { pref.remove("plc"); pref.putBool("plcrun", false); }
    else if (a.startsWith("TXT")) pref.putString("plc", plc.texto);
  }
  return ok;
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
  web.on("/plc", []() {
    if (web.method() == HTTP_POST) {
      if (!claveCorrecta(web.arg("k"))) { web.send(401, "application/json", "{\"ok\":0,\"err\":\"clave\"}"); return; }
      String t = web.arg("plain");
      bool ok = enlace->rol() == aplink::Rol::CABEZA && plc.cargar(t.c_str());
      if (ok) pref.putString("plc", plc.texto);
      web.send(200, "application/json", String("{\"ok\":") + ok + ",\"err\":\"" + plc.prog.error + "\"}"); return;
    }
    web.send(200, "text/plain; charset=utf-8", plc.texto);
  });
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
bool existe(uint8_t dir) { Wire.beginTransmission(dir); return Wire.endTransmission() == 0; }
// ADS1115: una conversión de un solo disparo por canal, sin bloquear (el siguiente canal se pide al leer el anterior)
void adsPaso(uint32_t t) {
  uint8_t chip = adsCanal >> 2 ? ADS_B : ADS_A, mux = adsCanal & 3;
  if (!adsEsperando) {
    uint16_t cfg = 0x8000 | ((4 + mux) << 12) | 0x0200 | 0x0100 | 0x0080 | 0x0003;     // ±4.096 V, un disparo, 128 SPS
    Wire.beginTransmission(chip); Wire.write(1); Wire.write(cfg >> 8); Wire.write(cfg & 0xFF);
    if (Wire.endTransmission() != 0) { fallasHw |= F_I2C; adsCanal = (adsCanal + 4) & 7; return; }
    adsEsperando = true; tAds = t; return;
  }
  if (t - tAds < 10) return;
  Wire.beginTransmission(chip); Wire.write(0);
  if (Wire.endTransmission(false) != 0 || Wire.requestFrom((int)chip, 2) != 2) { fallasHw |= F_I2C; adsEsperando = false; adsCanal = (adsCanal + 1) & 7; return; }
  int16_t raw = (int16_t)((Wire.read() << 8) | Wire.read());
  anaVal[adsCanal] = aprack::analogica(raw, (anaMascara >> adsCanal) & 1);
  adsEsperando = false; adsCanal = (adsCanal + 1) & 7;
}
void aplicarSalidas(uint16_t s) {
  bool a = tcaEscribir(TCA_S1, 1, s & 0xFF), b = tipoMod == T_RL4 ? true : tcaEscribir(TCA_S2, 1, tipoMod == T_PLC24 ? (s >> 8) & 0x0F : s >> 8);
  if (a && b) { salidasEscritas = s; fallasHw &= ~F_I2C; enlace->aplicadas(s); } else fallasHw |= F_I2C;
}
// PCA9685 a 1 kHz (prescaler 5 con el reloj de 25 MHz). Cada canal: apagado = «todo apagado» (bit 4 de OFF_H), pleno = «todo encendido» (bit 4 de ON_H),
// si no, 12 bits: duty x 16 cuentas.
bool pcaIniciar() {
  bool ok = tcaEscribir(pcaDir, 0x00, 0x10) && tcaEscribir(pcaDir, 0xFE, pcaPre) && tcaEscribir(pcaDir, 0x01, 0x04) && tcaEscribir(pcaDir, 0x00, 0x20);
  delay(1);
  return ok && tcaEscribir(pcaDir, 0x00, 0xA0);
}
void aplicarPwm(uint16_t s, const uint8_t* d) {
  Wire.beginTransmission(pcaDir); Wire.write(0x06);
  for (uint8_t i = 0; i < 8; i++) {
    uint16_t on = 0, off = 0;
    if (!((s >> i) & 1) || d[i] == 0) off = 0x1000;
    else if (d[i] == 255) on = 0x1000;
    else off = (uint16_t)d[i] * 16;
    Wire.write(on & 0xFF); Wire.write(on >> 8); Wire.write(off & 0xFF); Wire.write(off >> 8);
  }
  if (Wire.endTransmission() == 0) {
    salidasEscritas = s; memcpy(dutyEscrito, d, 8); pwmValido = true; fallasHw &= ~F_I2C; if (enlace) enlace->aplicadas(s);
  } else fallasHw |= F_I2C;
}
void ponerLeds(uint32_t t) {
  uint8_t pos = enlace->pos();
  if (tipoMod == T_PLC24) {                                  // P0 RUN, P1 FALLA, P2 COM, P3 NET, P4-P7 = M1-M4 del programa del PLC
    uint8_t w = 0;
    if (plc.run) w |= 0x01; else if ((t / 500) & 1) w |= 0x01;   // RUN fijo si el programa corre; parpadea en STOP
    if (fallasHw || (plc.run && plc.hayFallaModulos())) w |= 0x02;
    if (t - tCom < 120) w |= 0x04;
    if (ethArriba && t - tMb < 250) w |= 0x08;
    for (int i = 0; i < 4; i++) if (plc.prog.m[1 + i]) w |= (uint8_t)(0x10 << i);
    if (w != ledsEscritos && tcaEscribir(TCA_LED, 1, w)) ledsEscritos = w;
    return;
  }
  uint8_t v = pos & 0x0F;                                   // posición en binario: P0 = 1, P1 = 2, P2 = 4, P3 = 8
  if ((t / 500) & 1) v |= 0x10;                              // RUN: parpadea 1 Hz
  if (fallasHw || (enlace->rol() == aplink::Rol::ESCLAVO && enlace->enSeguro()) || enlace->rol() == aplink::Rol::ESPERA) v |= 0x20;   // FALLA
  if (t - tCom < 120) v |= 0x40;                             // COM: hubo tramas
  if (enlace->rol() == aplink::Rol::CABEZA) v |= 0x80;       // CABEZA
  if (v != ledsEscritos && tcaEscribir(TCA_LED, 1, v)) ledsEscritos = v;
}
// Botón RUN/STOP del AP PLC C24 (TCA 0x24, P4, activo en 0): cada pulsación alterna RUN y STOP; el modo se recuerda al reiniciar
void botonRunStop(int b, uint32_t t) {
  bool suelto = (b >> 4) & 1;
  if (suelto == botonPrevio || t - tBoton < 40) return;                // antirrebote
  tBoton = t; botonPrevio = suelto;
  if (!suelto && enlace->rol() == aplink::Rol::CABEZA) { plc.modo(!plc.run); pref.putBool("plcrun", plc.run); }
}
void ethIniciar() {
  SPI.begin(P_ETH_SCK, P_ETH_MISO, P_ETH_MOSI, P_ETH_CS);
  // W5500 por SPI sin pin de interrupción (el programa consulta) y con el reset por RC de la placa
  ethArriba = ETH.begin(ETH_PHY_W5500, 1, P_ETH_CS, -1, -1, SPI2_HOST, P_ETH_SCK, P_ETH_MISO, P_ETH_MOSI);
  if (ethArriba) { modbus.begin(); configTime(0, 0, "pool.ntp.org", "time.google.com"); }     // hora por NTP (UTC) en cuanto haya red
  Serial.printf("Ethernet: %s\n", ethArriba ? "W5500 iniciado (DHCP)" : "W5500 no contesta");
}
// Modbus TCP (puerto 502): un cliente a la vez; la trama completa va a aprack::modbusTcp. Sin respuesta = trama mala = se cierra.
void modbusPaso(uint32_t t) {
  if (!ethArriba) return;
  if (!clienteMb || !clienteMb.connected()) { clienteMb = modbus.accept(); mbN = 0; if (!clienteMb) return; }
  while (clienteMb.available() && mbN < sizeof mbBuf) mbBuf[mbN++] = (uint8_t)clienteMb.read();
  if (mbN >= 7) {
    size_t largo = 6 + (size_t)(mbBuf[4] << 8 | mbBuf[5]);
    if (largo > sizeof mbBuf) { clienteMb.stop(); mbN = 0; return; }
    if (mbN >= largo) {
      uint8_t r[300]; bool cambio = false;
      time_t ahora = time(nullptr); uint32_t epoch = ahora > 1735689600 ? (uint32_t)ahora : 0;      // antes de 2025 = sin ajustar
      size_t k = aprack::modbusTcp(*enlace, plc, &seguraLocal, segundos, mbBuf, largo, r, &cambio, epoch);
      if (!k) { clienteMb.stop(); mbN = 0; return; }
      clienteMb.write(r, k); tMb = t;
      if (cambio) pref.putBool("plcrun", plc.run);
      mbN -= largo; if (mbN) memmove(mbBuf, mbBuf + largo, mbN);
    }
  }
}
void leerEntradas() {
  int raw;
  if (tipoMod == T_IN16) { int a = tcaLeer(TCA_E1), b = tcaLeer(TCA_E2); raw = (a < 0 || b < 0) ? -1 : (a | (b << 8)); }
  else if (tipoMod == T_AI8) raw = 0;
  else if (tipoMod == T_PLC24) { int a = tcaLeer(TCA_ENT), b = tcaLeer(TCA_ENT2); raw = (a < 0 || b < 0) ? -1 : (a | ((b & 0x0F) << 8)); botonRunStop(b < 0 ? 0x10 : b, millis()); }
  else raw = tcaLeer(TCA_ENT);
  uint16_t vin = tipoMod == T_PLC24 ? 0 : (uint16_t)(analogReadMilliVolts(P_VSENSE) * 11UL);   // divisor 100 k / 10 k; el AP PLC C24 no lo mide (IO0 es el CS del W5500)
  if (raw < 0) fallasHw |= F_I2C; else if (!(fallasHw & F_I2C)) fallasHw &= ~F_I2C;
  fallasHw &= ~(F_SUBTENSION | F_SOBRETENSION);
  if (tipoMod != T_PLC24) { if (vin < VIN_MIN_MV) fallasHw |= F_SUBTENSION; else if (vin > VIN_MAX_MV) fallasHw |= F_SOBRETENSION; }
  uint16_t mascaraEnt = tipoMod == T_IN16 ? 0xFFFF : tipoMod == T_AI8 ? 0 : tipoMod == T_PLC24 ? 0x0FFF : 0x00FF;
  enlace->ponerLocales(raw < 0 ? 0 : (uint16_t)(~raw & mascaraEnt), fallasHw, vin);
  if (tipoMod == T_AI8) enlace->ponerAnalogicas(anaVal, 8, anaMascara);
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
  // el tipo de módulo se reconoce por los chips que contestan: ADS1115 = AI8, expansor 0x24 = IN16, si no AP Rack 16
  tipoMod = existe(ADS_A) ? T_AI8 : (existe(TCA_E1) && existe(TCA_S1)) ? T_PLC24 : existe(TCA_E1) ? T_IN16 : existe(PCA_AO) ? T_AO4 : existe(PCA_LED) ? T_LED8 : !existe(TCA_S2) ? T_RL4 : T_RACK16;   // RL4: tiene el 0x20 pero no el 0x21
  if (tipoMod == T_RL4) { VIN_MIN_MV = 20000; VIN_MAX_MV = 27500; }       // bobinas de 24 V: 21.6 a 26.4 V
  if (tipoMod == T_RACK16 || tipoMod == T_RL4 || tipoMod == T_PLC24) {
    tcaEscribir(TCA_S1, 1, 0); tcaEscribir(TCA_S1, 3, 0x00); if (tipoMod != T_RL4) { tcaEscribir(TCA_S2, 1, 0); tcaEscribir(TCA_S2, 3, tipoMod == T_PLC24 ? 0xF0 : 0x00); }
    tcaEscribir(TCA_ENT, 3, 0xFF);
  } else if (tipoMod == T_LED8 || tipoMod == T_AO4) { if (tipoMod == T_AO4) { pcaDir = PCA_AO; pcaPre = 3; } pcaIniciar(); aplicarPwm(0, dutyEscrito); tcaEscribir(TCA_ENT, 3, 0xFF);
  } else if (tipoMod == T_IN16) { tcaEscribir(TCA_E1, 3, 0xFF); tcaEscribir(TCA_E2, 3, 0xFF); }
  if (tipoMod == T_PLC24) tcaEscribir(TCA_ENT2, 3, 0xFF);
  anaMascara = pref.getUChar("am", 0);
  tcaEscribir(TCA_LED, 1, 0); tcaEscribir(TCA_LED, 3, 0x00);
  Serial1.begin(BAUDIOS_LINK, SERIAL_8N1, P_RX, P_TX);
  aplink::Caps c; c.tipo = tipoMod; c.nSal = tipoMod == T_RACK16 ? 16 : tipoMod == T_PLC24 ? 12 : tipoMod == T_LED8 ? 8 : (tipoMod == T_RL4 || tipoMod == T_AO4) ? 4 : 0; c.nEnt = tipoMod == T_PLC24 ? 12 : (tipoMod == T_RACK16 || tipoMod == T_LED8 || tipoMod == T_RL4 || tipoMod == T_AO4) ? 8 : tipoMod == T_IN16 ? 16 : 0; c.nAna = tipoMod == T_AI8 ? 8 : 0; c.nPwm = tipoMod == T_LED8 ? 8 : tipoMod == T_AO4 ? 4 : 0;
  enlace = new aplink::Enlace(hal, uidModulo(), c, true);
  enlace->maskSegura(seguraLocal);
  plc.e = enlace;
  if (tipoMod == T_PLC24) ethIniciar();
  { String prg = pref.getString("plc", ""); if (prg.length() && plc.cargar(prg.c_str()) && pref.getBool("plcrun", false)) plc.modo(true); }
  esp_task_wdt_config_t w = {8000, 0, true};
  if (esp_task_wdt_reconfigure(&w) != ESP_OK) esp_task_wdt_init(&w);
  esp_task_wdt_add(nullptr);
  Serial.printf("%s · %s · id %s · escuchando la cadena…\n", VERSION, tipoMod == T_PLC24 ? "AP PLC C24" : tipoMod == T_AO4 ? "AP Rack AO4" : tipoMod == T_RL4 ? "AP Rack RL4" : tipoMod == T_LED8 ? "AP Rack LED8" : tipoMod == T_AI8 ? "AP Rack AI8" : tipoMod == T_IN16 ? "AP Rack IN16" : "AP Rack 16", mac6().c_str());
}

void loop() {
  uint32_t t = millis();
  while (Serial1.available()) enlace->recibir((uint8_t)Serial1.read());
  enlace->tick();
  if (tipoMod == T_AI8) adsPaso(t);
  if (t - tEnt >= 5) { tEnt = t; leerEntradas(); }
  plc.paso(t);
  if (tipoMod == T_PLC24) modbusPaso(t);
  uint16_t s = enlace->salidas();
  if ((tipoMod == T_RACK16 || tipoMod == T_RL4 || tipoMod == T_PLC24) && (s != salidasEscritas || (fallasHw & F_I2C))) aplicarSalidas(s);
  if ((tipoMod == T_LED8 || tipoMod == T_AO4) && (!pwmValido || (s & 0xFF) != salidasEscritas || memcmp(dutyEscrito, enlace->dutyLocal(), 8) || (fallasHw & F_I2C))) aplicarPwm(s & 0xFF, enlace->dutyLocal());
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
