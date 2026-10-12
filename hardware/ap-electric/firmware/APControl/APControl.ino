/*
  AP Control 1.0 - programa común de AP Home (Plug / Switch) y AP Electric Industrial 7R Tour (ESP32-C3-WROOM-02).
  Estado: CONCEPTO (compila y pasa las pruebas en la PC; no se ha probado en una placa fabricada).

  Funciona local desde el primer encendido: sin cuenta, sin nube y sin Wi-Fi. Wi-Fi apagado de fábrica.
  - Botones del equipo: mandan su canal. MODO 3 s = abre la red de configuración (15 min); MODO 10 s = valores de fábrica.
  - Consola por USB (115200): las mismas órdenes que la página local y /api?c=...
  - 7R Tour: Modbus RTU esclavo por el RS-485 aislado (mapa en modbus_esclavo.h); DIP 8 = Wi-Fi apagado.
  - Programa tipo PLC (AP LÓGICA, logica.h): I = entradas, Q = canales, M, T, C, S; los canales que usa le pertenecen.
  - Vínculos sin nube: una entrada de un equipo manda el canal de otro en la misma red (UDP 4210).

  Órdenes (una por renglón):
    C k 0|1|2         canal k apagar / encender / alternar             ?            estado JSON
    A k 0|1|2         arranque del canal (apagado / último / encendido) T k 0|1      carga (alumbrado / proceso)
    P k s             apagado automático a los s segundos (0 = no)      X k 0|1      al perder Modbus: apagar / mantener
    E k modo canal ms entrada k: modo 0 pulsador, 1 interruptor, 2 conmutador (escalera), 3 desacoplada
    MB dir baud par vig   Modbus: dirección, baudios, paridad 0 N / 1 E / 2 O, vigilancia en s (0 = sin)
    GUARDAR           guarda la configuración en la memoria             FABRICA      valores de fábrica (y reinicia)
    WIFI AP | WIFI STA red,clave | WIFI OFF                             PLC RUN | PLC STOP | PLC BORRAR
    VINC i mac6 entrada canal modo   vínculo i (0-7): la entrada del equipo mac6 manda el canal local   VINC i -
*/
#include <WiFi.h>
#include <WebServer.h>
#include <WiFiUdp.h>
#include <Preferences.h>
#include <Wire.h>
#include "esp_task_wdt.h"
#include "ap_control.h"
#include "modbus_esclavo.h"
#include "unidad_packml.h"
#include "logica.h"

void abrirAP();
void conectarSTA();
void iniciarModbus();

#define VERSION "AP Control 1.0"
const uint16_t VERSION_NUM = 100;

// ---------------- placas ----------------
enum Placa : uint8_t { PLACA_HOME = 2, PLACA_7R = 1 };
Placa placa = PLACA_HOME;
// 7R Tour
const uint8_t P7_SDA = 2, P7_SCL = 8, P7_INT = 4, P7_LRUN = 5, P7_LFAL = 6, P7_LCOM = 7, P7_TX = 1, P7_RX = 3, P7_DE = 10;
const uint8_t TCA_SAL = 0x20, TCA_ENT = 0x21, TCA_RETRO = 0x22, TCA_BTN = 0x23;
// AP Home
const uint8_t PH_RELE = 4, PH_LVERDE = 5, PH_LROJO = 6, PH_SW = 7;
const uint8_t P_MODO = 9;

apc::Controlador ctl;
apc::UnidadPackML pk;
uint32_t segundos = 0;
apc::Esclavo mb(ctl, VERSION_NUM, PLACA_HOME, &segundos);
Preferences pref;
WebServer web(80);
WiFiUDP udp;
logica::Programa plc;
bool plcRun = false;
String plcTexto;
bool wifiApagadoDip = false, wifiActivo = false;
uint32_t tWifi = 0;
String red, clave;
apc::LimiteEscritura limEstado, limManiobras, limPk;
uint8_t escrito = 0xFF;
bool fallaI2C = false;

struct Vinculo { char mac[7]; uint8_t entrada, canal, modo; };
Vinculo vinc[8];

// ---------------- hardware ----------------
bool tcaEscribir(uint8_t dir, uint8_t reg, uint8_t v) {
  Wire.beginTransmission(dir); Wire.write(reg); Wire.write(v); return Wire.endTransmission() == 0;
}
int tcaLeer(uint8_t dir) {
  Wire.beginTransmission(dir); Wire.write(0);
  if (Wire.endTransmission(false) != 0) return -1;
  if (Wire.requestFrom((int)dir, 1) != 1) return -1;
  return Wire.read();
}
bool detectar7R() {
  Wire.begin(P7_SDA, P7_SCL, 400000);
  // salidas en 0 ANTES de ponerlas como salidas: ningún relé se mueve al arrancar
  if (!tcaEscribir(TCA_SAL, 1, 0x00)) return false;
  tcaEscribir(TCA_SAL, 3, 0x80);             // P0-P6 salidas, P7 entrada (identificación)
  int id = tcaLeer(TCA_SAL);
  return id >= 0 && !(id & 0x80) && tcaLeer(TCA_ENT) >= 0;
}
void escribirSalidas(uint8_t m) {
  if (placa == PLACA_7R) {
    if (m != escrito || millis() % 1000 < 6) {
      bool ok = tcaEscribir(TCA_SAL, 1, m & 0x7F) && tcaEscribir(TCA_SAL, 3, 0x80);
      fallaI2C = !ok; if (ok) escrito = m;
    }
  } else digitalWrite(PH_RELE, m & 1);
}
uint32_t tSwActivo = 0;
void leerHardware(uint8_t& ent, uint8_t& btn, uint8_t& bob) {
  if (placa == PLACA_7R) {
    int e = tcaLeer(TCA_ENT), b = tcaLeer(TCA_BTN), r = tcaLeer(TCA_RETRO);
    if (e < 0 || b < 0 || r < 0) { fallaI2C = true; ent = ctl.entradas; btn = 0; bob = ctl.bobinas; return; }
    ent = ~e & 0xFF;                         // optoacoplador encendido = 0
    btn = ~b & 0x7F;
    bob = ~r & 0x7F;                         // divisor de la bobina en 0 = bobina energizada
    wifiApagadoDip = !(r & 0x80);
  } else {
    // el optoacoplador de la entrada de red deja pasar casi todo el ciclo: activa si se vio en 0 en los últimos 25 ms
    if (!digitalRead(PH_SW)) tSwActivo = millis();
    ent = (tSwActivo && millis() - tSwActivo < 25) ? 1 : 0;
    btn = 0; bob = 0;
  }
}

// ---------------- memoria ----------------
void guardarConfig() {
  ctl.cfg.crc = apc::crcDe(ctl.cfg);
  pref.putBytes("cfg", &ctl.cfg, sizeof(ctl.cfg));
  pref.putBytes("pkm", &pk.paraGuardar(), sizeof(apc::ConfigMonitor));      // función de cada entrada, ciclo nominal y modo
  pref.putBytes("vinc", vinc, sizeof(vinc));
}
void cargarVinculos() {
  if (pref.getBytes("vinc", vinc, sizeof(vinc)) != sizeof(vinc)) memset(vinc, 0, sizeof(vinc));
}

// ---------------- PLC ----------------
struct EntornoAPC : logica::Entorno {
  uint8_t q = 0;
  bool leerBit(char a, int i) override {
    if (a == 'I') return i >= 1 && i <= 8 && (ctl.entradas & (1 << (i - 1)));
    if (a == 'Q') return i >= 1 && i <= 7 && (ctl.salida & (1 << (i - 1)));
    if (a == 'S') return i == 2 ? (millis() / 500) & 1 : i == 3 ? true : i == 5 ? ctl.fallas != 0
                     : (i >= 10 && i < 10 + apc::PK_N) ? pk.estado == i - 10 : false;   // S11-S27: estado PackML (S10 + estado)
    return false;
  }
  float valor(char, int) override { return NAN; }
  void escribir(char a, int i, bool v) override {
    if (a == 'Q' && i >= 1 && i <= 7) { if (v) q |= 1 << (i - 1); else q &= ~(1 << (i - 1)); }
  }
} entorno;
uint8_t mascaraPLC() {
  uint8_t m = 0;
  for (int i = 0; i < plc.n; i++) {
    const logica::Ins& in = plc.ins[i];
    if ((in.op == logica::OUT || in.op == logica::SET || in.op == logica::RST) && in.area == 'Q' && in.idx >= 1 && in.idx <= ctl.cfg.nCanales)
      m |= 1 << (in.idx - 1);
  }
  return m;
}
void plcModo(bool run) {
  if (run && !plc.n) return;
  if (!run && plcRun) { for (int k = 0; k < 7; k++) if (ctl.plcMascara & (1 << k)) ctl.ordenar(k + 1, 0, apc::OR_PLC, millis()); }
  plcRun = run; ctl.plcMascara = run ? mascaraPLC() : 0;
  if (run) { entorno.q = ctl.salida; plc.primerCiclo = true; }
  pref.putBool("plcrun", run);
}

// ---------------- órdenes ----------------
long num(const char*& p) { while (*p == ' ' || *p == ',') p++; long v = strtol(p, (char**)&p, 0); return v; }
String estadoJSON();
// `local` = la orden viene de la consola USB (alguien junto al equipo). Por la web o la red (local = false) la unidad PackML
// solo acepta parar, retener y abortar, igual que por Modbus, y no se puede dar permiso para reanudar.
bool ejecutar(String s, bool local = false) {
  s.trim(); if (!s.length()) return false;
  const char* p = s.c_str() + 1;
  char c = toupper(s[0]);
  uint32_t t = millis();
  apc::Config cfg = ctl.cfg;
  auto aplicar = [&](void) { cfg.crc = apc::crcDe(cfg); if (!apc::validar(cfg)) return false; ctl.cfg = cfg; return true; };
  if (s.startsWith("GUARDAR")) { guardarConfig(); return true; }
  if (s.startsWith("FABRICA")) { pref.remove("cfg"); pref.remove("vinc"); pref.remove("est"); pref.remove("pkm"); pref.remove("pkn"); delay(100); ESP.restart(); }
  if (s.startsWith("PLC ")) {
    String a = s.substring(4);
    if (a == "RUN") plcModo(true); else if (a == "STOP") plcModo(false);
    else if (a == "BORRAR") { plcModo(false); plc.n = 0; plcTexto = ""; pref.remove("plc"); }
    return true;
  }
  if (s.startsWith("PK ")) {                          // unidad PackML: órdenes locales (las únicas que pueden dar permiso remoto)
    String a = s.substring(3); a.trim(); a.toUpperCase();
    static const char* cmds[] = {"", "RESET", "START", "STOP", "HOLD", "UNHOLD", "SUSPEND", "UNSUSPEND", "ABORT", "CLEAR"};
    for (int i = 1; i < 10; i++) if (a == cmds[i]) return pk.comando(i, local ? apc::OR_BOTON : apc::OR_RED, t);
    if (a == "SC") return pk.completar(t);
    if (a == "BUENA") return pk.contar(true, t);
    if (a == "MALA") return pk.contar(false, t);
    if (a.startsWith("MODO ")) return pk.cambiarModo(a.substring(5).toInt(), t);
    if (a.startsWith("MOTIVO ")) { pk.motivoParo(a.substring(7).toInt()); return true; }
    if (a.startsWith("CICLO ")) { long v = a.substring(6).toInt(); if (v < 0 || v > 65535) return false; pk.cfg.cicloNominalMs = v; return true; }
    if (a.startsWith("ENT ")) {                       // PK ENT ciclo mala andon reanuda (0 = ninguna)
      const char* q = a.c_str() + 4; apc::ConfigMonitor n = pk.mon;
      n.entCiclo = num(q); n.entMala = num(q); n.entAndon = num(q); n.entReanuda = num(q);
      return pk.configurarMonitor(n, ctl.cfg.nEntradas);
    }
    if (a.startsWith("REMOTO ") && local) { pk.cfg.remotoReanuda = a.substring(7).toInt() != 0; return true; }
    return false;
  }
  if (s.startsWith("WIFI")) {
    String a = s.substring(5);
    if (a.startsWith("OFF")) { WiFi.mode(WIFI_OFF); wifiActivo = false; pref.putUChar("wifi", 0); }
    else if (a.startsWith("AP")) abrirAP();
    else if (a.startsWith("STA ")) { int i = a.indexOf(','); red = a.substring(4, i); clave = i > 0 ? a.substring(i + 1) : "";
      pref.putString("red", red); pref.putString("clave", clave); pref.putUChar("wifi", 2); conectarSTA(); }
    return true;
  }
  if (s.startsWith("MB ")) {
    p = s.c_str() + 3;
    long d = num(p), b = num(p), pa = num(p), v = num(p);
    cfg.mbDireccion = d; cfg.mbBaudios = b; cfg.mbParidad = pa; cfg.mbVigilanciaS = v;
    if (!aplicar()) return false;
    iniciarModbus(); return true;
  }
  if (s.startsWith("VINC ")) {
    p = s.c_str() + 5; int i = num(p);
    if (i < 0 || i > 7) return false;
    while (*p == ' ') p++;
    if (*p == '-') { memset(&vinc[i], 0, sizeof(Vinculo)); return true; }
    char m[7] = {0}; for (int k = 0; k < 6 && isxdigit(*p); k++) m[k] = toupper(*p++);
    int e = num(p), ca = num(p), mo = num(p);
    if (strlen(m) != 6 || e < 1 || e > 8 || ca < 1 || ca > ctl.cfg.nCanales || mo < 0 || mo > 2) return false;
    memcpy(vinc[i].mac, m, 7); vinc[i].entrada = e; vinc[i].canal = ca; vinc[i].modo = mo; return true;
  }
  int k = num(p);
  switch (c) {
    case '?': return true;
    case 'C': { int v = num(p); return ctl.ordenar(k, v, apc::OR_RED, t) == apc::OK; }
    case 'A': if (k < 1 || k > cfg.nCanales) return false; cfg.canal[k - 1].arranque = num(p); return aplicar();
    case 'T': if (k < 1 || k > cfg.nCanales) return false; cfg.canal[k - 1].carga = num(p);
              if (cfg.canal[k - 1].carga) { cfg.canal[k - 1].arranque = 0; cfg.canal[k - 1].accionCom = 0; } return aplicar();
    case 'P': if (k < 1 || k > cfg.nCanales) return false; cfg.canal[k - 1].pulsoS = num(p); return aplicar();
    case 'X': if (k < 1 || k > cfg.nCanales) return false; cfg.canal[k - 1].accionCom = num(p); return aplicar();
    case 'E': if (k < 1 || k > cfg.nEntradas) return false;
              cfg.entrada[k - 1].modo = num(p); cfg.entrada[k - 1].canal = num(p); cfg.entrada[k - 1].antirreboteMs = num(p);
              return aplicar();
  }
  return false;
}

// ---------------- Modbus RTU (7R Tour) ----------------
HardwareSerial& rs = Serial1;
uint8_t rxb[260]; size_t rxn = 0; uint32_t tRx = 0, t35 = 2;
void iniciarModbus() {
  if (placa != PLACA_7R) return;
  uint32_t cfgSer = ctl.cfg.mbParidad == 1 ? SERIAL_8E1 : ctl.cfg.mbParidad == 2 ? SERIAL_8O1 : SERIAL_8N2;
  rs.end(); rs.begin(ctl.cfg.mbBaudios, cfgSer, P7_RX, P7_TX);
  t35 = ctl.cfg.mbBaudios > 19200 ? 2 : (uint32_t)(38500UL / ctl.cfg.mbBaudios) + 1;   // 3.5 caracteres de 11 bits
}
void atenderModbus(uint32_t t) {
  if (placa != PLACA_7R) return;
  while (rs.available()) { int b = rs.read(); if (rxn < sizeof(rxb)) rxb[rxn++] = b; tRx = t; }
  if (rxn && t - tRx > t35) {
    uint8_t r[260];
    size_t n = mb.procesar(rxb, rxn, r, t);
    rxn = 0;
    if (n) {
      digitalWrite(P7_DE, HIGH); rs.write(r, n); rs.flush(); digitalWrite(P7_DE, LOW);
      digitalWrite(P7_LCOM, HIGH);
    }
    if (mb.pedirGuardar) { mb.pedirGuardar = false; guardarConfig(); }
    if (mb.pedirFabrica) { ejecutar("FABRICA"); }
    if (mb.cambioComunicacion) { mb.cambioComunicacion = false; iniciarModbus(); }
  }
}

// ---------------- Wi-Fi (opcional) ----------------
String claveAP() {                            // clave propia de cada equipo (va en la etiqueta y en la consola)
  uint64_t m = ESP.getEfuseMac(); uint32_t h = apc::crc32((const uint8_t*)&m, 6);
  char b[9]; snprintf(b, 9, "%08lu", (unsigned long)(h % 100000000UL)); return b;
}
String mac6() { uint64_t m = ESP.getEfuseMac(); char b[7]; snprintf(b, 7, "%02X%02X%02X", (uint8_t)(m >> 24), (uint8_t)(m >> 32), (uint8_t)(m >> 40)); return b; }
void abrirAP() {
  if (wifiApagadoDip) { Serial.println("Wi-Fi apagado por el DIP 8"); return; }
  WiFi.mode(WIFI_AP); WiFi.softAP(("APElectric-" + mac6()).c_str(), claveAP().c_str());
  wifiActivo = true; tWifi = millis();
  Serial.printf("Red de configuración APElectric-%s, clave %s, http://%s\n", mac6().c_str(), claveAP().c_str(), WiFi.softAPIP().toString().c_str());
}
void conectarSTA() {
  if (wifiApagadoDip || !red.length()) return;
  WiFi.mode(WIFI_STA); WiFi.begin(red.c_str(), clave.c_str()); wifiActivo = true; udp.begin(4210);
}
void enviarEvento(int entrada, bool v) {
  if (!wifiActivo || WiFi.getMode() != WIFI_STA || !WiFi.isConnected()) return;
  char b[40]; snprintf(b, sizeof(b), "APV1 EV %s %d %d", mac6().c_str(), entrada, v);
  udp.beginPacket(IPAddress(255, 255, 255, 255), 4210); udp.write((const uint8_t*)b, strlen(b)); udp.endPacket();
}
void recibirEventos(uint32_t t) {
  if (!wifiActivo || WiFi.getMode() != WIFI_STA) return;
  int n = udp.parsePacket(); if (n <= 0 || n > 63) return;
  char b[64]; n = udp.read(b, 63); b[n] = 0;
  char m[7]; int e, v;
  if (sscanf(b, "APV1 EV %6s %d %d", m, &e, &v) != 3) return;
  static bool ant[8][9];
  for (auto& x : vinc) {
    if (!x.canal || strcmp(x.mac, m) || x.entrada != e) continue;
    int i = &x - vinc;
    bool cambio = ant[i][e] != (bool)v; ant[i][e] = v;
    if (x.modo == 0 && v) ctl.ordenar(x.canal, 2, apc::OR_RED, t);
    else if (x.modo == 1) ctl.ordenar(x.canal, v, apc::OR_RED, t);
    else if (x.modo == 2 && cambio) ctl.ordenar(x.canal, 2, apc::OR_RED, t);
  }
}
const char PAGINA[] PROGMEM = R"HTML(<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AP Control</title><style>body{font:16px system-ui;margin:16px;background:#f2f2f7;color:#1c1c1e}.c{background:#fff;border-radius:14px;padding:14px;margin:10px 0}
button{font:inherit;border:0;border-radius:10px;padding:10px 14px;margin:4px;background:#e5e5ea}.on{background:#30d158;color:#fff}.f{color:#c0281f}</style>
<h2 id=t>AP Control</h2><div class=c id=s></div><div class=c id=e></div><div class=c id=k></div><div class=c id=f></div>
<p>Más ajustes: órdenes por /api?c=… o por la consola USB (ver el manual).</p>
<script>
async function a(c){const r=await fetch('/api'+(c?'?c='+encodeURIComponent(c):''));const j=await r.json();p(j)}
function p(j){t.textContent=j.placa+' · '+j.v;let h='';for(let k=1;k<=j.n;k++){const o=j.s>>(k-1)&1;h+=`<button class="${o?'on':''}" onclick="a('C ${k} 2')">Canal ${k}${j.fz>>(k-1)&1?' (manual)':''}</button>`}
s.innerHTML=h;let g='Entradas: ';for(let k=1;k<=j.ne;k++)g+=(j.e>>(k-1)&1?'●':'○')+' ';e.textContent=g;
f.innerHTML=j.f?'<b class=f>Falla: '+j.fn.join(', ')+'</b>':'Sin fallas';
const E=['','Limpiando','Detenida','Arrancando','Lista','Suspendida','En marcha','Deteniendo','Abortando','Abortada','Reteniendo','Retenida','Reanudando','Suspendiendo','Reanudando susp.','Reiniciando','Terminando','Terminada'];
const q=j.pk,P=v=>v==65535?'—':(v/10).toFixed(1)+' %';
k.innerHTML='<b>'+E[q.e]+'</b> · piezas '+q.n+' ('+q.d+' malas)<br>Disponibilidad '+P(q.disp)+' · Desempeño '+P(q.des)+' · Calidad '+P(q.cal)+' · <b>OEE '+P(q.oee)+'</b>'+(q.mp?' <span class=f>microparo</span>':'')+
'<br><button onclick="a(\'PK HOLD\')">Retener</button><button onclick="a(\'PK STOP\')">Parar</button><button onclick="a(\'PK ABORT\')">Abortar</button>'+(q.rem?'':' <small>Arrancar y reanudar: en la máquina</small>');}
a();setInterval(a,1500)</script></html>)HTML";
const char* NOMBRE_FALLA[] = {"configuración inválida", "bobina sin tensión", "comunicación perdida", "sin 24 V",
                              "mantenimiento de relés", "reinicio por vigilante", "expansor I2C"};
String estadoJSON() {
  String s = "{\"v\":\"" VERSION "\",\"placa\":\""; s += placa == PLACA_7R ? "7R Tour" : "AP Home";
  s += "\",\"n\":"; s += ctl.cfg.nCanales; s += ",\"ne\":"; s += ctl.cfg.nEntradas;
  s += ",\"s\":"; s += ctl.salida; s += ",\"e\":"; s += ctl.entradas; s += ",\"b\":"; s += ctl.bobinas;
  s += ",\"fz\":"; s += ctl.forzado; s += ",\"f\":"; s += ctl.fallas; s += ",\"fn\":[";
  bool pr = true; for (int i = 0; i < 7; i++) if (ctl.fallas & (1 << i)) { if (!pr) s += ','; pr = false; s += '"'; s += NOMBRE_FALLA[i]; s += '"'; }
  s += "],\"man\":["; for (int k = 0; k < ctl.cfg.nCanales; k++) { if (k) s += ','; s += ctl.maniobras[k]; }
  s += "],\"arr\":["; for (int k = 0; k < ctl.cfg.nCanales; k++) { if (k) s += ','; s += ctl.cfg.canal[k].arranque; }
  s += "],\"carga\":["; for (int k = 0; k < ctl.cfg.nCanales; k++) { if (k) s += ','; s += ctl.cfg.canal[k].carga; }
  s += "],\"mb\":{\"dir\":"; s += ctl.cfg.mbDireccion; s += ",\"bps\":"; s += ctl.cfg.mbBaudios; s += ",\"vig\":"; s += ctl.cfg.mbVigilanciaS;
  s += ",\"ok\":"; s += mb.tramasBien; s += ",\"mal\":"; s += mb.tramasMal; s += "},\"pk\":{\"e\":"; s += pk.estado; s += ",\"m\":"; s += pk.modo; s += ",\"r\":"; s += pk.motivo; s += ",\"n\":"; s += pk.procesadas;
  s += ",\"d\":"; s += pk.defectuosas; s += ",\"disp\":"; s += pk.disponibilidad(); s += ",\"des\":"; s += pk.desempeno();
  s += ",\"cal\":"; s += pk.calidad(); s += ",\"oee\":"; s += pk.oee(); s += ",\"mp\":"; s += pk.microparo; s += ",\"rem\":"; s += pk.cfg.remotoReanuda;
  s += "},\"plc\":{\"run\":"; s += plcRun;
  s += ",\"n\":"; s += plc.n; s += ",\"err\":\""; s += plc.error; s += "\"},\"id\":\""; s += mac6(); s += "\",\"t\":"; s += segundos; s += '}';
  return s;
}
void rutas() {
  web.on("/", []() { web.send_P(200, "text/html; charset=utf-8", PAGINA); });
  web.on("/api", []() { if (web.hasArg("c")) ejecutar(web.arg("c")); web.send(200, "application/json", estadoJSON()); });
  web.on("/plc", []() {
    if (web.method() == HTTP_POST) {
      String t = web.arg("plain");
      logica::Programa* q = new logica::Programa(); bool ok = t.length() < 3800 && q->compilar(t.c_str());
      if (ok) { bool r = plcRun; plcModo(false); plc = *q; plcTexto = t; pref.putString("plc", t); if (r) plcModo(true); }
      String e = ok ? "" : q->error; delete q;
      web.send(200, "application/json", String("{\"ok\":") + ok + ",\"err\":\"" + e + "\"}"); return;
    }
    web.send(200, "text/plain; charset=utf-8", plcTexto);
  });
}

// ---------------- arranque y ciclo ----------------
void setup() {
  Serial.begin(115200);
  pref.begin("apcontrol", false);
  placa = detectar7R() ? PLACA_7R : PLACA_HOME;
  if (placa == PLACA_7R) {
    pinMode(P7_LRUN, OUTPUT); pinMode(P7_LFAL, OUTPUT); pinMode(P7_LCOM, OUTPUT); pinMode(P7_DE, OUTPUT); digitalWrite(P7_DE, LOW);
    tcaEscribir(TCA_ENT, 3, 0xFF); tcaEscribir(TCA_RETRO, 3, 0xFF); tcaEscribir(TCA_BTN, 3, 0xFF);
  } else {
    pinMode(PH_RELE, OUTPUT); digitalWrite(PH_RELE, LOW);
    pinMode(PH_LVERDE, OUTPUT); pinMode(PH_LROJO, OUTPUT); pinMode(PH_SW, INPUT_PULLUP);
  }
  pinMode(P_MODO, INPUT_PULLUP);
  mb.placa = placa;
  mb.um = &pk;
  pk.iniciar(millis());
  { apc::ConfigMonitor m; uint32_t n[2] = {0, 0};
    if (pref.getBytes("pkm", &m, sizeof(m)) == sizeof(m)) pk.cargarMonitor(m, placa == PLACA_7R ? 8 : 1);
    if (pref.getBytes("pkn", n, sizeof(n)) == sizeof(n)) pk.restaurarContadores(n[0], n[1]); }
  apc::Config c;
  uint8_t nC = placa == PLACA_7R ? 7 : 1, nE = placa == PLACA_7R ? 8 : 1;
  if (pref.getBytes("cfg", &c, sizeof(c)) != sizeof(c) || c.nCanales != nC) c = apc::fabrica(nC, nE);
  uint32_t man[7] = {0}; pref.getBytes("man", man, sizeof(man));
  uint8_t ultimo = pref.getUChar("est", 0);
  bool porVigilante = esp_reset_reason() == ESP_RST_TASK_WDT || esp_reset_reason() == ESP_RST_INT_WDT;
  ctl.hayRetro = placa == PLACA_7R;
  ctl.iniciar(c, ultimo, man, millis(), porVigilante);
  escribirSalidas(ctl.salida);
  cargarVinculos();
  plcTexto = pref.getString("plc", "");
  if (plcTexto.length() && plc.compilar(plcTexto.c_str()) && pref.getBool("plcrun", false)) plcModo(true);
  iniciarModbus();
  red = pref.getString("red", ""); clave = pref.getString("clave", "");
  uint8_t ar, ae, ab; leerHardware(ar, ae, ab);       // lee el DIP 8 antes de decidir el Wi-Fi
  if (pref.getUChar("wifi", 0) == 2) conectarSTA();
  rutas(); web.begin();
  esp_task_wdt_config_t w = {8000, 0, true};
  if (esp_task_wdt_reconfigure(&w) != ESP_OK) esp_task_wdt_init(&w);
  esp_task_wdt_add(nullptr);
  Serial.printf("%s · %s · %d canales · id %s\n", VERSION, placa == PLACA_7R ? "7R Tour" : "AP Home", nC, mac6().c_str());
}

void loop() {
  uint32_t t = millis();
  static uint32_t tPaso = 0, tPlc = 0, tSeg = 0, tBtn = 0;
  static bool btnAnt = false;
  if (t - tPaso >= 5) {
    tPaso = t;
    uint8_t ent, btn, bob; leerHardware(ent, btn, bob);
    uint8_t antes = ctl.entradas;
    // AP Home: el botón MODO corto también es el botón del canal
    bool m = !digitalRead(P_MODO);
    if (m && !btnAnt) tBtn = t;
    if (!m && btnAnt) {
      uint32_t d = t - tBtn;
      if (d >= 10000) ejecutar("FABRICA");
      else if (d >= 3000) abrirAP();
      else if (d > 40 && placa == PLACA_HOME) ctl.ordenar(1, 2, apc::OR_BOTON, t);
    }
    btnAnt = m;
    ctl.paso(t, ent, btn, bob);
    if (fallaI2C) ctl.fallas |= apc::F_EXPANSOR; else ctl.fallas &= ~apc::F_EXPANSOR;
    pk.entradas(ctl.entradas, t); pk.paso(t); pk.alFalla(ctl.fallas, t);        // unidad PackML: tiempos por estado y paro o retención ante fallas
    uint8_t dif = antes ^ ctl.entradas;
    for (int k = 0; k < 8; k++) if (dif & (1 << k)) enviarEvento(k + 1, ctl.entradas & (1 << k));
    escribirSalidas(ctl.salida);
    mb.wifiApagado = wifiApagadoDip;
    if (wifiApagadoDip && wifiActivo) { WiFi.mode(WIFI_OFF); wifiActivo = false; }
  }
  if (plcRun && t - tPlc >= 10) {
    uint32_t dt = min<uint32_t>(t - tPlc, 100); tPlc = t;
    entorno.q = ctl.salida;
    plc.ciclo(entorno, dt);
    ctl.plc(entorno.q, t);
  }
  atenderModbus(t);
  if (wifiActivo) { web.handleClient(); recibirEventos(t); }
  if (wifiActivo && WiFi.getMode() == WIFI_AP && WiFi.softAPgetStationNum() == 0 && t - tWifi > 900000UL) {
    WiFi.mode(WIFI_OFF); wifiActivo = false;          // la red de configuración se cierra sola a los 15 min
  }
  if (WiFi.getMode() == WIFI_AP && WiFi.softAPgetStationNum()) tWifi = t;
  if (Serial.available()) { String l = Serial.readStringUntil('\n'); bool ok = ejecutar(l, true); Serial.println(ok ? estadoJSON() : "?"); }
  // memoria con escrituras limitadas
  if (limEstado.debeEscribir(ctl.guardarEstado, t)) pref.putUChar("est", ctl.salida);
  ctl.guardarEstado = false;
  if (limManiobras.debeEscribir(ctl.guardarManiobras, t, 60000, 3600000UL)) pref.putBytes("man", ctl.maniobras, sizeof(ctl.maniobras));
  ctl.guardarManiobras = false;
  if (limPk.debeEscribir(pk.contadoresCambiaron, t, 60000, 600000UL)) { uint32_t n[2] = {pk.procesadas, pk.defectuosas}; pref.putBytes("pkn", n, sizeof(n)); }
  pk.contadoresCambiaron = false;
  // indicadores
  if (t - tSeg >= 1000) { tSeg = t; segundos++; }
  bool run = (t / 500) & 1, fal = ctl.fallas && ((t / 150) % 4 == 0);
  if (placa == PLACA_7R) {
    digitalWrite(P7_LRUN, plcRun ? HIGH : run); digitalWrite(P7_LFAL, ctl.fallas ? fal || (ctl.fallas & apc::F_SIN_24V) : LOW);
    static uint32_t tCom = 0; if (digitalRead(P7_LCOM)) { if (!tCom) tCom = t; if (t - tCom > 30) { digitalWrite(P7_LCOM, LOW); tCom = 0; } }
  } else {
    digitalWrite(PH_LVERDE, ctl.salida & 1); digitalWrite(PH_LROJO, ctl.fallas ? fal : LOW);
  }
  esp_task_wdt_reset();
}
