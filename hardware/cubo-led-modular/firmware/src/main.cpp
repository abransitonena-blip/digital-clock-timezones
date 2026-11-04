// Cubo AP · firmware ESP32-C3 (Arduino-ESP32 3.x + NimBLE-Arduino 2.x + Adafruit NeoPixel + Espalexa)
// La lógica (límites, protecciones, tiras, efectos, horario, protocolo, JSON WLED) está en nucleo.cpp y se prueba en PC.
// Conectividad:
//   · Bluetooth LE (Nordic UART) con PIN de 6 dígitos  -> app web / celular
//   · Wi-Fi: página de control en http://<nombre>.local, API /api/cmd (pide PIN en cabecera X-PIN)
//   · DMX por red: Art-Net (UDP 6454) y sACN/E1.31 (UDP 5568, multicast) para consolas, xLights, QLC+, Resolume
//   · DMX512 por cable (placa v2): transceptor RS-485 en GPIO2, 250 kbit/s
//   · Actualización OTA en /update (pide PIN; apaga la salida mientras escribe)
//   · Integraciones (se activan con "INTEGRACIONES ON" por Bluetooth): API JSON tipo WLED (/json/state),
//     anuncio mDNS _wled._tcp y Alexa local (emulación Hue con Espalexa). Home Assistant las usa vía WLED/Hue.
#include <Arduino.h>
#include <Wire.h>
#include <Preferences.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <WiFiUdp.h>
#include <Update.h>
#include <NimBLEDevice.h>
#include <Adafruit_NeoPixel.h>
#include <Espalexa.h>
#include <time.h>
#include "nucleo.h"
#include "pagina.h"     // generada desde ../app/index.html con gen_pagina.py

// ---------------- Pines (ver README: tabla de pines) ----------------
static const int P_TARJETA = 0;   // ADC: R_ID de la tarjeta (pull-up 47k)
static const int P_VIN     = 1;   // ADC: Vin / 11 (100k / 10k)
#ifndef CUBO_PLACA
#define CUBO_PLACA 2               // 1: placa v1 (botón en GPIO2) · 2: placa v2 (DMX por cable + 5.º canal)
#endif
static const int P_BOTON   = 2;   // v1: botón a GND (pull-up 10k) · v2: RO del transceptor RS-485 (DMX512)
static const int P_CANAL5  = 10;  // v2: 5.º canal (blanco frío) en el mismo GPIO que DAT; nunca se usan juntos
static const int P_NTC     = 3;   // ADC: NTC 10k B3950 a GND, 10k a 3.3 V
static const int P_EN      = 4;   // EN del reductor (4.7k serie, 10k a GND; ALERT del INA226 lo tira a GND)
static const int P_PWM[4]  = {21, 5, 6, 7}; // R G B W -> drivers UCC27524 -> MOSFET
static const int P_SDA = 8, P_SCL = 9;      // I2C con pull-up 4.7k
static const int P_DATOS   = 10;  // WS2812/SK6812/WS2811/WS2815 vía 74AHCT1G125
static const int P_LED     = 20;  // LED de estado (tubo de luz de la tapa)

static const uint8_t INA = 0x40, DAC = 0x60;
static const float R_SHUNT = 0.005f, I_LSB = 0.0002f;   // 5 mΩ, 0.2 mA/bit
static const ap::RedFB RED_BASE = {0.8f, 29400.f, 0.f, 47000.f, 3.3f};  // rb viene de la tarjeta

static const char* UUID_SVC = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E";  // Nordic UART
static const char* UUID_RX  = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E";
static const char* UUID_TX  = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E";

static ap::Controlador ctl;
static ap::Medicion med{};
static Preferences nvs;
static Adafruit_NeoPixel tira(60, P_DATOS, NEO_GRB + NEO_KHZ800);
static NimBLECharacteristic* tx = nullptr;
static WebServer web(80);
static Espalexa alexa;
static WiFiUDP udp_art, udp_sacn;
static ap::ReceptorDmx rx_dmx;
static bool uart_dmx = false;
static bool reiniciar_udp = true, ota_negada = false, ota_activa = false;
static volatile bool conectado = false;
static bool en_previo = false, guardar_pendiente = false, integraciones = false, wifi_ok = false;
static uint32_t t_cambio = 0, t_notif = 0, t_ntp = 0;
static char linea_pendiente[96]; static volatile bool hay_linea = false;
static char nombre[24] = "CuboAP";
static int zona_h = -6;            // UTC-6 (centro de México); "ZONA n" la cambia

// ---------------- I2C ----------------
static void ina_w(uint8_t reg, uint16_t v) {
  Wire.beginTransmission(INA); Wire.write(reg); Wire.write(v >> 8); Wire.write(v & 0xFF); Wire.endTransmission();
}
static uint16_t ina_r(uint8_t reg) {
  Wire.beginTransmission(INA); Wire.write(reg); Wire.endTransmission(false);
  if (Wire.requestFrom(INA, (uint8_t)2) != 2) return 0;
  uint16_t hi = Wire.read(); return (hi << 8) | Wire.read();
}
static void dac_w(float volts) {
  uint16_t d = (uint16_t)constrain(lroundf(volts / 3.3f * 4095.f), 0, 4095);
  Wire.beginTransmission(DAC); Wire.write((d >> 8) & 0x0F); Wire.write(d & 0xFF); Wire.endTransmission();
}
static void ina_configurar(float imax) {
  ina_w(0x00, 0x4207);                                   // prom. 4, 140 µs, continuo
  ina_w(0x05, (uint16_t)(0.00512f / (I_LSB * R_SHUNT))); // calibración
  ina_w(0x07, (uint16_t)(1.6f * imax * R_SHUNT / 2.5e-6f)); // límite de shunt = 1.6 × Imax
  ina_w(0x06, 0x8001);                                   // ALERT por sobre-shunt, enclavado
}

// ---------------- Sensores ----------------
static float adc_mv(int pin, int n = 8) {
  uint32_t s = 0; for (int i = 0; i < n; ++i) s += analogReadMilliVolts(pin); return (float)s / n;
}
static void medir() {
  med.vout = ina_r(0x02) * 0.00125f;
  med.iout = (int16_t)ina_r(0x04) * I_LSB;
  if (med.iout < 0) med.iout = 0;
  med.vin = adc_mv(P_VIN, 4) * 11.f / 1000.f;
  med.temp_c = ap::ntcCelsius(adc_mv(P_NTC, 4));
}

// ---------------- Tira direccionable ----------------
static void tipo_neopixel() {
  static bool pwm10 = false;
  bool quiero_pwm = CUBO_PLACA >= 2 && ctl.tira() == ap::Tira::RGBCCT;
  if (quiero_pwm && !pwm10) { ledcAttach(P_CANAL5, 19000, 12); ledcWrite(P_CANAL5, 0); pwm10 = true; }
  if (!quiero_pwm && pwm10) { ledcDetach(P_CANAL5); pwm10 = false; tira.begin(); }
  switch (ctl.tira()) {
    case ap::Tira::SK6812: tira.updateType(NEO_GRBW + NEO_KHZ800); break;
    case ap::Tira::WS2811: tira.updateType(NEO_RGB + NEO_KHZ800); break;
    default:               tira.updateType(NEO_GRB + NEO_KHZ800); break;
  }
}

// ---------------- Persistencia ----------------
static void cargar() {
  nvs.begin("cubo", true);
  ctl.fijarColor({nvs.getUChar("r", 255), nvs.getUChar("g", 255), nvs.getUChar("b", 255), nvs.getUChar("w", 0)});
  ctl.fijarBrillo(nvs.getFloat("brillo", 0.6f));
  if (ctl.perfil() == ap::PERFIL_PERSONAL) ctl.fijarLimitesPersonal(nvs.getFloat("vp", 0), nvs.getFloat("ip", 0));
  float v = nvs.getFloat("vset", 0); if (v > 0) ctl.fijarVoltaje(v);
  ctl.fijarModo((ap::Modo)nvs.getUChar("modo", 0));
  ctl.fijarTira((ap::Tira)nvs.getUChar("tira", 0));       // si no corresponde a la tarjeta, se queda en RGBW
  ctl.fijarCCT(nvs.getUShort("cct", 4000));
  ctl.configurarDmx((ap::ProtoDmx)nvs.getUChar("dmxp", 0), nvs.getUShort("dmxu", 1), nvs.getUShort("dmxd", 1));
  { ap::Escena e[ap::N_ESCENAS] = {}; if (nvs.getBytes("esc", e, sizeof e) == sizeof e) ctl.cargarEscenas(e); }
  if (nvs.getBool("prog", false)) ctl.programar(true, nvs.getUShort("pon", 0), nvs.getUShort("poff", 0));
  tira.updateLength(nvs.getUShort("leds", 60));
  zona_h = nvs.getChar("zona", -6);
  integraciones = nvs.getBool("integ", false);
  nvs.getString("nombre", nombre, sizeof nombre);
  bool on = nvs.getBool("on", true);   // letreros: vuelve encendido tras un corte de luz
  nvs.end();
  tipo_neopixel();
  ctl.encender(on);
}
static void guardar() {
  nvs.begin("cubo", false);
  ap::RGBW c = ctl.color();
  nvs.putUChar("r", c.r); nvs.putUChar("g", c.g); nvs.putUChar("b", c.b); nvs.putUChar("w", c.w);
  nvs.putFloat("brillo", ctl.brillo()); nvs.putFloat("vset", ctl.vset());
  nvs.putUChar("modo", (uint8_t)ctl.modo()); nvs.putBool("on", ctl.encendido());
  nvs.putUChar("tira", (uint8_t)ctl.tira()); nvs.putUShort("cct", ctl.cct());
  nvs.putBool("prog", ctl.horarioActivo()); nvs.putUShort("pon", ctl.minEncender()); nvs.putUShort("poff", ctl.minApagar());
  nvs.putUShort("leds", tira.numPixels());
  nvs.putUChar("dmxp", (uint8_t)ctl.protoDmx()); nvs.putUShort("dmxu", ctl.universoDmx()); nvs.putUShort("dmxd", ctl.direccionDmx());
  nvs.putBytes("esc", ctl.escenas(), sizeof(ap::Escena) * ap::N_ESCENAS);
  if (ctl.perfil() == ap::PERFIL_PERSONAL) { nvs.putFloat("vp", ctl.vmaxPerfil()); nvs.putFloat("ip", ctl.limiteCorriente()); }
  nvs.end();
}
static void marcar() { guardar_pendiente = true; t_cambio = millis(); }

// ---------------- Comandos (mismo protocolo por BLE, USB y Wi-Fi) ----------------
static uint32_t passkey() {   // 6 dígitos únicos por equipo; se imprime en la etiqueta
  uint64_t mac = ESP.getEfuseMac(); return 100000 + (uint32_t)(mac % 900000ULL);
}
static void wifi_iniciar();
static void ejecutar(const char* l, char* r, size_t n) {
  if (!strncasecmp(l, "LEDS ", 5)) {
    int k = atoi(l + 5);
    if (k < 1 || k > 600) { snprintf(r, n, "ERR rango 1-600"); return; }
    tira.updateLength(k); marcar(); snprintf(r, n, "OK"); return;
  }
  if (!strncasecmp(l, "WIFI ", 5)) {                     // WIFI ssid clave   |   WIFI OFF
    char ssid[33] = "", clave[65] = "";
    if (!strcasecmp(l + 5, "OFF")) { nvs.begin("cubo", false); nvs.putString("ssid", ""); nvs.end(); WiFi.disconnect(true); wifi_ok = false; snprintf(r, n, "OK"); return; }
    if (sscanf(l + 5, "%32s %64s", ssid, clave) < 1) { snprintf(r, n, "ERR usa WIFI ssid clave"); return; }
    nvs.begin("cubo", false); nvs.putString("ssid", ssid); nvs.putString("clave", clave); nvs.end();
    wifi_iniciar(); snprintf(r, n, "OK conectando a %s", ssid); return;
  }
  if (!strncasecmp(l, "ZONA ", 5)) {
    int z = atoi(l + 5); if (z < -12 || z > 14) { snprintf(r, n, "ERR -12..14"); return; }
    zona_h = z; nvs.begin("cubo", false); nvs.putChar("zona", (int8_t)z); nvs.end(); t_ntp = 0; snprintf(r, n, "OK"); return;
  }
  if (!strncasecmp(l, "NOMBRE ", 7)) {                    // nombre para Alexa y la red (cuboap-xxxx.local)
    strlcpy(nombre, l + 7, sizeof nombre); nvs.begin("cubo", false); nvs.putString("nombre", nombre); nvs.end();
    snprintf(r, n, "OK reinicia para aplicar"); return;
  }
  if (!strncasecmp(l, "INTEGRACIONES ", 14)) {            // WLED/Alexa en la red local (sin contraseña)
    integraciones = !strcasecmp(l + 14, "ON");
    nvs.begin("cubo", false); nvs.putBool("integ", integraciones); nvs.end();
    snprintf(r, n, "OK reinicia para aplicar"); return;
  }
  if (!strcasecmp(l, "RED")) {
    snprintf(r, n, "{\"wifi\":%s,\"ip\":\"%s\",\"nombre\":\"%s\",\"integraciones\":%s,\"zona\":%d}", wifi_ok ? "true" : "false",
             wifi_ok ? WiFi.localIP().toString().c_str() : "", nombre, integraciones ? "true" : "false", zona_h);
    return;
  }
  ap::Tira antes = ctl.tira();
  ap::ProtoDmx p0 = ctl.protoDmx(); uint16_t u0 = ctl.universoDmx();
  ap::procesarComando(ctl, l, med, r, n);
  if (ctl.tira() != antes) tipo_neopixel();
  if (ctl.protoDmx() != p0 || ctl.universoDmx() != u0) reiniciar_udp = true;
  if (strncasecmp(l, "ESTADO", 6)) marcar();
}

// ---------------- Bluetooth ----------------
static void notificar(const char* s) {        // en trozos de 180 bytes; la app une hasta el salto de línea
  if (!tx || !conectado) return;
  size_t L = strlen(s);
  for (size_t i = 0; i < L; i += 180) { size_t k = L - i < 180 ? L - i : 180; tx->setValue((const uint8_t*)s + i, k); tx->notify(); }
  tx->setValue((const uint8_t*)"\n", 1); tx->notify();
}
class SrvCB : public NimBLEServerCallbacks {
  void onConnect(NimBLEServer*, NimBLEConnInfo&) override { conectado = true; }
  void onDisconnect(NimBLEServer*, NimBLEConnInfo&, int) override { conectado = false; NimBLEDevice::startAdvertising(); }
};
class RxCB : public NimBLECharacteristicCallbacks {
  void onWrite(NimBLECharacteristic* c, NimBLEConnInfo&) override {
    std::string v = c->getValue();
    if (hay_linea || v.empty()) return;           // se procesa en loop(), no en la tarea BLE
    strlcpy(linea_pendiente, v.c_str(), sizeof linea_pendiente);
    hay_linea = true;
  }
};
static void ble_iniciar() {
  NimBLEDevice::init(nombre);
  NimBLEDevice::setSecurityAuth(true, true, true);        // bonding + MITM + conexión segura
  NimBLEDevice::setSecurityPasskey(passkey());
  NimBLEDevice::setSecurityIOCap(BLE_HS_IO_DISPLAY_ONLY);
  NimBLEServer* srv = NimBLEDevice::createServer();
  srv->setCallbacks(new SrvCB());
  NimBLEService* svc = srv->createService(UUID_SVC);
  NimBLECharacteristic* rx = svc->createCharacteristic(UUID_RX,
      NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::WRITE_ENC | NIMBLE_PROPERTY::WRITE_AUTHEN);
  rx->setCallbacks(new RxCB());
  tx = svc->createCharacteristic(UUID_TX, NIMBLE_PROPERTY::NOTIFY | NIMBLE_PROPERTY::READ_ENC);
  // NimBLE 2.x arranca los servicios junto con el servidor
  NimBLEAdvertising* adv = NimBLEDevice::getAdvertising();
  adv->addServiceUUID(UUID_SVC);
  adv->setName(nombre);
  adv->start();
  Serial.printf("BLE %s  PIN %06lu\n", nombre, (unsigned long)passkey());
}

// ---------------- Wi-Fi, página y APIs ----------------
static bool pin_ok() {
  char pin[8]; snprintf(pin, sizeof pin, "%06lu", (unsigned long)passkey());
  return web.header("X-PIN") == pin;
}
static void cuerpo_json(const char* s) { web.sendHeader("Cache-Control", "no-store"); web.send(200, "application/json", s); }
static void wled_info() {
  char b[300]; uint8_t m[6]; WiFi.macAddress(m);
  snprintf(b, sizeof b, "{\"ver\":\"0.14.0-cuboap\",\"vid\":2611040,\"name\":\"%s\",\"brand\":\"AP\",\"product\":\"Cubo AP\","
           "\"leds\":{\"count\":%u,\"rgbw\":%s,\"wv\":%d},\"mac\":\"%02x%02x%02x%02x%02x%02x\",\"arch\":\"esp32c3\"}",
           nombre, tira.numPixels(), ap::bytesPorLed(ctl.tira()) == 4 || !ap::direccionable(ctl.tira()) ? "true" : "false",
           ap::bytesPorLed(ctl.tira()) == 4 ? 1 : 0, m[0], m[1], m[2], m[3], m[4], m[5]);
  cuerpo_json(b);
}
static void cb_alexa(uint8_t bri) {                       // "Alexa, enciende/apaga/pon al 50 % el letrero"
  if (bri == 0) ctl.encender(false); else { ctl.encender(true); ctl.fijarBrillo(bri / 255.f); }
  marcar();
}
static void web_iniciar() {
  const char* cabeceras[] = {"X-PIN"};
  web.collectHeaders(cabeceras, 1);
  web.on("/", HTTP_GET, [] { web.send_P(200, "text/html", PAGINA_HTML); });
  web.on("/api/estado", HTTP_GET, [] { char b[640]; ctl.estadoJson(b, sizeof b, med); cuerpo_json(b); });
  web.on("/update", HTTP_POST, [] {                       // OTA: el archivo .bin de "pio run"
    if (ota_negada) { web.send(401, "text/plain", "ERR PIN"); return; }
    bool ok = !Update.hasError();
    web.send(ok ? 200 : 500, "text/plain", ok ? "OK reiniciando" : "ERR actualizacion");
    if (ok) { delay(300); ESP.restart(); }
    ota_activa = false;
  }, [] {
    HTTPUpload& u = web.upload();
    if (u.status == UPLOAD_FILE_START) {
      ota_negada = !pin_ok(); if (ota_negada) return;
      ota_activa = true; ctl.encender(false); digitalWrite(P_EN, LOW);   // sin salida mientras se escribe la flash
      Update.begin(UPDATE_SIZE_UNKNOWN);
    } else if (u.status == UPLOAD_FILE_WRITE && !ota_negada) Update.write(u.buf, u.currentSize);
    else if (u.status == UPLOAD_FILE_END && !ota_negada) Update.end(true);
  });
  web.on("/api/cmd", HTTP_POST, [] {
    if (!pin_ok()) { web.send(401, "text/plain", "ERR PIN"); return; }
    char r[640]; String c = web.arg("plain"); c.trim();
    ejecutar(c.c_str(), r, sizeof r); web.send(200, r[0] == '{' ? "application/json" : "text/plain", r);
  });
  if (integraciones) {
    web.on("/json/state", HTTP_GET, [] { char b[200]; ctl.estadoWled(b, sizeof b); cuerpo_json(b); });
    web.on("/json/state", HTTP_POST, [] { ctl.aplicarWled(web.arg("plain").c_str()); marcar(); char b[200]; ctl.estadoWled(b, sizeof b); cuerpo_json(b); });
    web.on("/json/info", HTTP_GET, wled_info);
    web.on("/json", HTTP_GET, [] {
      char s[200]; ctl.estadoWled(s, sizeof s);
      String b = String("{\"state\":") + s + ",\"info\":{\"ver\":\"0.14.0-cuboap\",\"name\":\"" + nombre + "\"}}";
      cuerpo_json(b.c_str());
    });
    web.onNotFound([] {
      if (!alexa.handleAlexaApiCall(web.uri(), web.arg(0))) web.send(404, "text/plain", "no encontrado");
    });
    alexa.addDevice(nombre, cb_alexa);
    alexa.begin(&web);                                    // también arranca el servidor web
  } else {
    web.onNotFound([] { web.send(404, "text/plain", "no encontrado"); });
    web.begin();
  }
}
static void wifi_iniciar() {
  char ssid[33] = "", clave[65] = "";
  nvs.begin("cubo", true); nvs.getString("ssid", ssid, sizeof ssid); nvs.getString("clave", clave, sizeof clave); nvs.end();
  if (!ssid[0]) return;
  WiFi.mode(WIFI_STA); WiFi.setHostname(nombre); WiFi.begin(ssid, clave);
}
static void wifi_atender(uint32_t t) {
  bool ahora = WiFi.status() == WL_CONNECTED;
  if (ahora && !wifi_ok) {                                // recién conectado
    wifi_ok = true;
    char host[32]; uint64_t mac = ESP.getEfuseMac();
    snprintf(host, sizeof host, "cuboap-%04x", (unsigned)((mac >> 32) & 0xFFFF));
    MDNS.begin(host); MDNS.addService("http", "tcp", 80);
    if (integraciones) MDNS.addService("wled", "tcp", 80);
    configTime(0, 0, "pool.ntp.org", "time.google.com");
    static bool web_listo = false;
    if (!web_listo) { web_iniciar(); web_listo = true; }
    Serial.printf("Wi-Fi %s  http://%s.local\n", WiFi.localIP().toString().c_str(), host);
  }
  if (!ahora && wifi_ok) reiniciar_udp = true;
  if (!ahora) wifi_ok = false;
  if (wifi_ok && (t_ntp == 0 || t - t_ntp > 3600000UL)) {   // hora local para el horario, cada hora
    time_t u = time(nullptr);
    if (u > 1700000000) { ctl.fijarHora((uint32_t)(u + zona_h * 3600L), t); t_ntp = t; }
  }
  if (wifi_ok) { web.handleClient(); if (integraciones) alexa.loop(); }
  if (wifi_ok && reiniciar_udp) {                          // DMX por red
    udp_art.stop(); udp_sacn.stop();
    if (ctl.protoDmx() == ap::ProtoDmx::ARTNET) udp_art.begin(6454);
    if (ctl.protoDmx() == ap::ProtoDmx::SACN) {
      uint16_t u = ctl.universoDmx();
      udp_sacn.beginMulticast(IPAddress(239, 255, u >> 8, u & 0xFF), 5568);   // también recibe unicast
    }
    reiniciar_udp = false;
  }
  if (wifi_ok && ctl.protoDmx() != ap::ProtoDmx::OFF) {
    static uint8_t pq[640];
    WiFiUDP& udp = ctl.protoDmx() == ap::ProtoDmx::ARTNET ? udp_art : udp_sacn;
    for (int k = 0; k < 4; ++k) {                          // hasta 4 paquetes por vuelta
      int len = udp.parsePacket(); if (len <= 0) break;
      int leidos = udp.read(pq, sizeof pq);
      if (leidos > 0) ctl.paqueteRed(pq, (size_t)leidos, t);
    }
  }
}

// ---------------- LED de estado y botón ----------------
static void led_estado(uint32_t t) {
  bool v;
  if (ctl.falla() != ap::Falla::NINGUNA) {             // N destellos = código de falla
    uint32_t n = (uint32_t)ctl.falla(), f = t % 3000;
    v = f < n * 300 && (f % 300) < 150;
  } else if (ctl.encendido()) v = !conectado || (t % 2000) < 1900;
  else v = (t % 2000) < 60;                            // latido en espera
  digitalWrite(P_LED, v);
}
static void uart_dmx_atender() {                 // DMX512 por cable: 250 kbit/s 8N2, la ruptura separa tramas
#if CUBO_PLACA >= 2
  bool quiero = ctl.protoDmx() == ap::ProtoDmx::CABLE;
  if (quiero && !uart_dmx) {
    Serial1.setRxBufferSize(1024);
    Serial1.onReceive([] { while (Serial1.available()) rx_dmx.byte((uint8_t)Serial1.read()); });
    Serial1.onReceiveError([](hardwareSerial_error_t e) {
      if (e == UART_BREAK_ERROR) { while (Serial1.available()) rx_dmx.byte((uint8_t)Serial1.read()); rx_dmx.ruptura(); }
    });
    Serial1.begin(250000, SERIAL_8N2, P_BOTON, -1);
    uart_dmx = true;
  } else if (!quiero && uart_dmx) { Serial1.end(); uart_dmx = false; }
  static uint8_t trama[512]; uint16_t n;
  if (uart_dmx && rx_dmx.tomar(trama, n)) ctl.entradaDmx(trama, n, millis());
#endif
}
static void boton(uint32_t t) {
#if CUBO_PLACA >= 2
  (void)t; return;                                   // v2 no tiene botón: ese GPIO es la entrada DMX
#endif
  static uint32_t t0 = 0; static bool prev = true;
  bool b = digitalRead(P_BOTON);
  if (!b && prev) t0 = t;
  if (b && !prev) {
    uint32_t d = t - t0;
    if (d > 6000) { NimBLEDevice::deleteAllBonds(); Serial.println("Vinculos borrados"); }
    else if (d > 40) {
      if (ctl.falla() != ap::Falla::NINGUNA) ctl.reconocerFalla();
      else ctl.encender(!ctl.encendido());
      marcar();
    }
  }
  prev = b;
}

// ---------------- Arranque ----------------
void setup() {
  pinMode(P_EN, OUTPUT); digitalWrite(P_EN, LOW);      // reductor apagado hasta decidir
  pinMode(P_LED, OUTPUT); pinMode(P_BOTON, INPUT_PULLUP);
  ctl.placaCincoCanales(CUBO_PLACA >= 2);
  for (int i = 0; i < 4; ++i) { ledcAttach(P_PWM[i], 19000, 12); ledcWrite(P_PWM[i], 0); }
  Serial.begin(115200);
  analogReadResolution(12);
  Wire.begin(P_SDA, P_SCL, 400000);
  dac_w(0);                                            // sin inyección: Vout = máximo de tarjeta

  int perfil = ap::decodificarTarjeta(adc_mv(P_TARJETA, 32));
  ap::RedFB red = RED_BASE;
  if (perfil >= 0) red.rb = ap::PERFILES[perfil].r_b > 0 ? ap::PERFILES[perfil].r_b : 1910.f;  // PERSONAL: aprox.
  ctl.configurar(perfil, red);
  Serial.printf("Tarjeta: %s\n", perfil >= 0 ? ap::PERFILES[perfil].nombre : "NO DETECTADA");

  uint64_t mac = ESP.getEfuseMac();
  snprintf(nombre, sizeof nombre, "CuboAP-%04X", (unsigned)((mac >> 32) & 0xFFFF));
  tira.begin(); tira.show();
  cargar();
  if (perfil >= 0) ina_configurar(ctl.limiteCorriente() > 0 ? ctl.limiteCorriente() : 1.f);
  ble_iniciar();
  wifi_iniciar();
}

void loop() {
  static uint32_t t_paso = 0, t_tira = 0;
  uint32_t t = millis();
  char r[640];
  if (hay_linea) { ejecutar(linea_pendiente, r, sizeof r); notificar(r); Serial.println(r); hay_linea = false; }
  while (Serial.available()) {                          // mismo protocolo por USB
    static char b[96]; static size_t n = 0;
    char ch = Serial.read();
    if (ch == '\n' || n == sizeof b - 1) {
      b[n] = 0;
      if (!strcasecmp(b, "OLVIDAR")) { NimBLEDevice::deleteAllBonds(); Serial.println("OK vinculos borrados"); }  // solo por USB
      else if (n) { ejecutar(b, r, sizeof r); Serial.println(r); }
      n = 0;
    }
    else if (ch != '\r') b[n++] = ch;
  }
  boton(t);
  uart_dmx_atender();
  led_estado(t);
  wifi_atender(t);

  if (ota_activa) return;                              // actualizando: salida apagada
  if (t - t_paso >= 10) {                               // ciclo de control 100 Hz
    t_paso = t;
    medir();
    if (en_previo && (ina_r(0x06) & 0x0010)) ctl.fallaExterna(ap::Falla::SOBRECORRIENTE, t); // AFF: ALERT disparó
    ap::Salida s = ctl.paso(med, t);
    if (s.habilitar_reductor && !en_previo) ina_r(0x06);  // leer Mask/Enable libera el ALERT
    en_previo = s.habilitar_reductor;
    dac_w(s.vdac);
    digitalWrite(P_EN, s.habilitar_reductor);
    for (int i = 0; i < 4; ++i) ledcWrite(P_PWM[i], s.pwm[i]);
    if (CUBO_PLACA >= 2 && ctl.tira() == ap::Tira::RGBCCT) ledcWrite(P_CANAL5, s.pwm[4]);
    if (ap::direccionable(ctl.tira()) && t - t_tira >= 20) {   // 50 cuadros por segundo
      t_tira = t; float k = s.brillo_efectivo;
      for (uint16_t i = 0; i < tira.numPixels(); ++i) {
        ap::RGBW c = ctl.colorPixel(i, tira.numPixels(), t);
        tira.setPixelColor(i, (uint8_t)(c.r * k), (uint8_t)(c.g * k), (uint8_t)(c.b * k), (uint8_t)(c.w * k));
      }
      tira.show();
    }
  }
  if (conectado && t - t_notif >= 1000) {               // telemetría cada segundo
    t_notif = t; ctl.estadoJson(r, sizeof r, med); notificar(r);
  }
  if (guardar_pendiente && t - t_cambio > 2000) { guardar(); guardar_pendiente = false; }
}
