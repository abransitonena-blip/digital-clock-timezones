// Cubo AP · firmware ESP32-C3 (Arduino-ESP32 3.x + NimBLE-Arduino 2.x + Adafruit NeoPixel)
// La lógica (límites, protecciones, efectos, protocolo) está en nucleo.cpp y se prueba en PC.
#include <Arduino.h>
#include <Wire.h>
#include <Preferences.h>
#include <NimBLEDevice.h>
#include <Adafruit_NeoPixel.h>
#include "nucleo.h"

// ---------------- Pines (ver README: tabla de pines) ----------------
static const int P_TARJETA = 0;   // ADC: R_ID de la tarjeta (pull-up 47k)
static const int P_VIN     = 1;   // ADC: Vin / 11 (100k / 10k)
static const int P_BOTON   = 2;   // botón a GND (pull-up 10k; strap: libre al arrancar)
static const int P_NTC     = 3;   // ADC: NTC 10k B3950 a GND, 10k a 3.3 V
static const int P_PWM[4]  = {21, 5, 6, 7}; // R G B W -> drivers UCC27524 -> MOSFET
static const int P_SDA = 8, P_SCL = 9;      // I2C con pull-up 4.7k (mantienen altos los straps)
static const int P_DATOS   = 10;  // WS2812 vía 74AHCT1G125 (5 V)
static const int P_LED     = 20;  // LED de estado (luz por el tubo de la tapa)
static const int P_EN      = 4;   // EN del reductor (4.7k serie, 10k a GND; ALERT del INA226 lo tira a GND)

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
static volatile bool conectado = false;
static bool en_previo = false, guardar_pendiente = false;
static uint32_t t_cambio = 0, t_notif = 0;
static char linea_pendiente[64]; static volatile bool hay_linea = false;

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

// ---------------- Persistencia ----------------
static void cargar() {
  nvs.begin("cubo", true);
  ctl.fijarColor({nvs.getUChar("r", 255), nvs.getUChar("g", 255), nvs.getUChar("b", 255), nvs.getUChar("w", 0)});
  ctl.fijarBrillo(nvs.getFloat("brillo", 0.6f));
  float v = nvs.getFloat("vset", 0); if (v > 0) ctl.fijarVoltaje(v);
  ctl.fijarModo((ap::Modo)nvs.getUChar("modo", 0));
  uint16_t n = nvs.getUShort("leds", 60); tira.updateLength(n);
  bool on = nvs.getBool("on", true);   // letreros: vuelve encendido tras un corte de luz
  nvs.end();
  ctl.encender(on);
}
static void guardar() {
  nvs.begin("cubo", false);
  ap::RGBW c = ctl.color();
  nvs.putUChar("r", c.r); nvs.putUChar("g", c.g); nvs.putUChar("b", c.b); nvs.putUChar("w", c.w);
  nvs.putFloat("brillo", ctl.brillo()); nvs.putFloat("vset", ctl.vset());
  nvs.putUChar("modo", (uint8_t)ctl.modo()); nvs.putBool("on", ctl.encendido());
  nvs.putUShort("leds", tira.numPixels());
  nvs.end();
}

// ---------------- Bluetooth ----------------
static void enviar(const char* s) {
  if (tx && conectado) { tx->setValue((const uint8_t*)s, strlen(s)); tx->notify(); }
  Serial.println(s);
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
static uint32_t passkey() {   // 6 dígitos únicos por equipo; se imprime en la etiqueta
  uint64_t mac = ESP.getEfuseMac(); return 100000 + (uint32_t)(mac % 900000ULL);
}
static void ble_iniciar() {
  char nombre[16]; uint64_t mac = ESP.getEfuseMac();
  snprintf(nombre, sizeof nombre, "CuboAP-%04X", (unsigned)((mac >> 32) & 0xFFFF));
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
  svc->start();
  NimBLEAdvertising* adv = NimBLEDevice::getAdvertising();
  adv->addServiceUUID(UUID_SVC);
  adv->setName(nombre);
  adv->start();
  Serial.printf("BLE %s  PIN %06lu\n", nombre, (unsigned long)passkey());
}

static void atender(const char* l) {
  char r[320];
  if (!strncasecmp(l, "LEDS ", 5)) {                  // nº de LEDs de la tira direccionable
    int n = atoi(l + 5);
    if (n < 1 || n > 600) { enviar("ERR rango 1-600"); return; }
    tira.updateLength(n); guardar_pendiente = true; t_cambio = millis(); enviar("OK"); return;
  }
  ap::procesarComando(ctl, l, med, r, sizeof r);
  if (strncasecmp(l, "ESTADO", 6)) { guardar_pendiente = true; t_cambio = millis(); }
  enviar(r);
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
static void boton(uint32_t t) {
  static uint32_t t0 = 0; static bool prev = true;
  bool b = digitalRead(P_BOTON);
  if (!b && prev) t0 = t;
  if (b && !prev) {
    uint32_t d = t - t0;
    if (d > 6000) { NimBLEDevice::deleteAllBonds(); enviar("Vinculos borrados"); }
    else if (d > 40) {
      if (ctl.falla() != ap::Falla::NINGUNA) ctl.reconocerFalla();
      else ctl.encender(!ctl.encendido());
      guardar_pendiente = true; t_cambio = t;
    }
  }
  prev = b;
}

// ---------------- Arranque ----------------
void setup() {
  pinMode(P_EN, OUTPUT); digitalWrite(P_EN, LOW);      // reductor apagado hasta decidir
  pinMode(P_LED, OUTPUT); pinMode(P_BOTON, INPUT_PULLUP);
  for (int i = 0; i < 4; ++i) { ledcAttach(P_PWM[i], 19000, 12); ledcWrite(P_PWM[i], 0); }
  Serial.begin(115200);
  analogReadResolution(12);
  Wire.begin(P_SDA, P_SCL, 400000);
  dac_w(0);                                            // sin inyección: Vout = máximo de tarjeta

  int perfil = ap::decodificarTarjeta(adc_mv(P_TARJETA, 32));
  ap::RedFB red = RED_BASE;
  if (perfil >= 0) red.rb = ap::PERFILES[perfil].r_b;
  ctl.configurar(perfil, red);
  if (perfil >= 0) ina_configurar(ap::PERFILES[perfil].imax);
  Serial.printf("Tarjeta: %s\n", perfil >= 0 ? ap::PERFILES[perfil].nombre : "NO DETECTADA");

  tira.begin(); tira.show();
  cargar();
  ble_iniciar();
}

void loop() {
  static uint32_t t_paso = 0;
  uint32_t t = millis();
  if (hay_linea) { atender(linea_pendiente); hay_linea = false; }
  while (Serial.available()) {                          // mismo protocolo por USB
    static char b[64]; static size_t n = 0;
    char ch = Serial.read();
    if (ch == '\n' || n == sizeof b - 1) { b[n] = 0; if (n) atender(b); n = 0; }
    else if (ch != '\r') b[n++] = ch;
  }
  boton(t);
  led_estado(t);

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
    if (ctl.modo() == ap::Modo::DIRECCIONABLE) {
      ap::RGBW c = ctl.color(); float k = s.brillo_efectivo;
      for (uint16_t i = 0; i < tira.numPixels(); ++i)
        tira.setPixelColor(i, tira.Color((uint8_t)(c.r * k), (uint8_t)(c.g * k), (uint8_t)(c.b * k)));
      tira.show();
    }
  }
  if (conectado && t - t_notif >= 1000) {               // telemetría cada segundo
    t_notif = t; char r[320]; ctl.estadoJson(r, sizeof r, med);
    tx->setValue((const uint8_t*)r, strlen(r)); tx->notify();
  }
  if (guardar_pendiente && t - t_cambio > 2000) { guardar(); guardar_pendiente = false; }
}
