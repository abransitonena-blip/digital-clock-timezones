#include "nucleo.h"
#include <math.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>

namespace ap {

// Rt = 29.4k en la placa; R_B en la tarjeta. Vref = 0.8 V.  Vmax = 0.8*(1+29.4k/R_B)
const Perfil PERFILES[] = {
  {"5V 3A",   10000,  4.98f, 3.0f, 5620.f},
  {"12V 1A",  15000, 12.00f, 1.0f, 2100.f},
  {"12V 2A",  22000, 12.00f, 2.0f, 2100.f},
  {"12V 5A",  33000, 12.00f, 5.0f, 2100.f},
  {"15V 1A",  47000, 15.05f, 1.0f, 1650.f},
  {"15V 3A",  68000, 15.05f, 3.0f, 1650.f},
  {"24V 2A", 100000, 24.32f, 2.0f, 1000.f},
  {"24V 3A", 150000, 24.32f, 3.0f, 1000.f},
  {"PERSONAL", 220000, 0.f, 0.f, 0.f},    // R_B a la medida; límites desde la app
};
const size_t N_PERFILES = sizeof(PERFILES) / sizeof(PERFILES[0]);

int decodificarTarjeta(float mv, float vcc, float rpu) {
  if (mv < 80.f || mv > vcc - 120.f) return -1;          // corto o sin tarjeta
  float r = rpu * mv / (vcc - mv);
  for (size_t i = 0; i < N_PERFILES; ++i) {
    float ri = PERFILES[i].r_id;
    if (fabsf(r - ri) <= 0.15f * ri) return (int)i;      // ventana ±15 % (vecinos ≥ ×1.4)
  }
  return -1;
}

// Inyección con diodo en serie: el DAC solo puede METER corriente al nodo FB,
// así que solo baja el voltaje. Con el DAC en 0 V o colgado => Vout = Vmax de la tarjeta.
static float vmaxRed(const RedFB& r) { return r.vref * (1.f + r.rt / r.rb); }
float vmaxDeRed(const RedFB& r) { return vmaxRed(r); }
float vminDeRed(const RedFB& r) {
  float vinj = r.vdac_max - 0.30f - r.vref;  // 0.30 V: diodo Schottky BAT54 a ~50 µA
  if (vinj < 0) vinj = 0;
  return vmaxRed(r) - vinj * r.rt / r.rinj;
}
float dacParaVoltaje(const RedFB& r, float vset) {
  float vmax = vmaxRed(r);
  if (vset >= vmax) return 0.f;                // sin inyección
  float vmin = vminDeRed(r);
  if (vset < vmin) vset = vmin;
  float vdac = r.vref + 0.30f + (vmax - vset) * r.rinj / r.rt;
  return vdac > r.vdac_max ? r.vdac_max : vdac;
}

float ntcCelsius(float mv, float vcc, float rs, float r25, float beta) {
  if (mv <= 1.f) return 150.f;                  // NTC en corto: tratar como caliente
  if (mv >= vcc - 1.f) return -40.f;            // NTC abierto
  // NTC abajo, resistencia serie arriba
  float rn = rs * mv / (vcc - mv);
  float inv = 1.f / 298.15f + logf(rn / r25) / beta;
  return 1.f / inv - 273.15f;
}

float factorTermico(float c) {
  if (c <= 70.f) return 1.f;
  if (c >= 90.f) return 0.f;
  if (c <= 85.f) return 1.f - 0.7f * (c - 70.f) / 15.f;  // 100 % -> 30 %
  return 0.3f * (90.f - c) / 5.f;                      // 30 % -> 0
}

uint16_t gamma12(uint8_t v) {
  return (uint16_t)lroundf(powf(v / 255.f, 2.2f) * 4095.f);
}

RGBW rueda(uint8_t p) {
  if (p < 85)  return {(uint8_t)(255 - p * 3), (uint8_t)(p * 3), 0, 0};
  if (p < 170) { p -= 85;  return {0, (uint8_t)(255 - p * 3), (uint8_t)(p * 3), 0}; }
  p -= 170;    return {(uint8_t)(p * 3), 0, (uint8_t)(255 - p * 3), 0};
}

const char* nombreFalla(Falla f) {
  switch (f) {
    case Falla::NINGUNA: return "ninguna";
    case Falla::SIN_TARJETA: return "sin_tarjeta";
    case Falla::TARJETA_INCONSISTENTE: return "tarjeta_inconsistente";
    case Falla::SOBRECORRIENTE: return "sobrecorriente";
    case Falla::SOBRETEMPERATURA: return "sobretemperatura";
    case Falla::SUBVOLTAJE_ENTRADA: return "subvoltaje_entrada";
    case Falla::CORTO: return "corto";
  }
  return "?";
}

static float respiro(uint32_t t);

// ---------------- Controlador ----------------
static const uint32_t T_RAMPA = 600, T_REINTENTO = 5000, T_DISPARO_OC = 50;
static const uint8_t MAX_REINTENTOS = 3;

void Controlador::configurar(int perfil, const RedFB& red) {
  perfil_ = perfil; red_ = red;
  falla_ = perfil < 0 ? Falla::SIN_TARJETA : Falla::NINGUNA;
  vset_ = vmaxPerfil();
  if (perfil >= 0 && vset_ > vmaxRed(red_)) vset_ = vmaxRed(red_);
}

float Controlador::limiteCorriente() const {
  if (perfil_ < 0) return 0.f;
  return perfil_ == PERFIL_PERSONAL ? imax_personal_ : PERFILES[perfil_].imax;
}
float Controlador::vmaxPerfil() const {
  if (perfil_ < 0) return 0.f;
  return perfil_ == PERFIL_PERSONAL ? vmax_personal_ : PERFILES[perfil_].vmax;
}
bool Controlador::fijarLimitesPersonal(float vmax, float imax) {
  if (perfil_ != PERFIL_PERSONAL || !(vmax >= 3.f && vmax <= 24.4f) || !(imax >= 0.2f && imax <= 5.f)) return false;
  vmax_personal_ = vmax; imax_personal_ = imax;
  red_.rb = red_.rt / (vmax / red_.vref - 1.f);      // R_B que el usuario puso en la tarjeta (calculada por la web)
  if (vset_ <= 0.f || vset_ > vmax) vset_ = vmax;
  return true;
}

bool Controlador::encender(bool on) {
  if (on && (perfil_ < 0 || limiteCorriente() <= 0.f)) return false;
  if (on && !on_) { rampa_ = 0.f; recorte_i_ = 1.f; }
  if (!on && falla_ != Falla::SIN_TARJETA) { falla_ = Falla::NINGUNA; reintentos_ = 0; }
  on_ = on;
  return true;
}
bool Controlador::fijarColor(RGBW c) { color_ = c; return true; }
bool Controlador::fijarBrillo(float b) {
  if (!(b >= 0.f && b <= 1.f)) return false;
  brillo_ = b; return true;
}
bool Controlador::fijarVoltaje(float v) {
  if (perfil_ < 0 || !(v > 0.f)) return false;
  float vmax = vmaxPerfil(), vmin = vminDeRed(red_);
  if (vmax <= 0.f) return false;
  if (v > vmax) v = vmax;          // nunca por encima de la tarjeta
  if (v < vmin) v = vmin;
  vset_ = v; return true;
}
bool Controlador::fijarModo(Modo m) { modo_ = m; return true; }
void Controlador::reconocerFalla() {
  if (falla_ != Falla::SIN_TARJETA) { falla_ = Falla::NINGUNA; reintentos_ = 0; rampa_ = 0.f; }
}

void Controlador::disparar(Falla f, uint32_t ahora) {
  falla_ = f; t_falla_ = ahora; rampa_ = 0.f; sobre_activo_ = false;
  if (reintentos_ < 255) ++reintentos_;
}

Salida Controlador::paso(const Medicion& m, uint32_t ahora) {
  uint32_t dt = t_ultimo_ ? ahora - t_ultimo_ : 0;
  t_ultimo_ = ahora;
  if (prog_on_ && hora_ok_) {                      // horario diario: actúa al cruzar el minuto programado
    int mm = minutoDelDia(ahora);
    if (mm != ultimo_min_) {
      if (ultimo_min_ >= 0) {
        if (mm == min_on_) encender(true);
        else if (mm == min_off_) encender(false);
      }
      ultimo_min_ = mm;
    }
  }
  Salida s{};
  s.vdac = dacParaVoltaje(red_, vset_);

  // --- Gestión de fallas con reintento ---
  if (falla_ != Falla::NINGUNA) {
    bool electrica = falla_ == Falla::SOBRECORRIENTE || falla_ == Falla::CORTO ||
                     falla_ == Falla::SUBVOLTAJE_ENTRADA;
    bool reintenta = electrica ? (reintentos_ <= MAX_REINTENTOS && ahora - t_falla_ >= T_REINTENTO)
                               : (falla_ == Falla::SOBRETEMPERATURA && m.temp_c < 70.f);
    if (on_ && reintenta) {
      falla_ = Falla::NINGUNA; rampa_ = 0.f; recorte_i_ = 1.f;
    } else {
      return s;  // todo apagado
    }
  }
  if (!on_) { rampa_ = 0.f; return s; }

  s.habilitar_reductor = true;
  float lim = limiteCorriente();
  bool arrancado = rampa_ >= 1.f;

  // --- Protecciones (respaldo; el INA226 ALERT corta el EN por hardware en ~1 ms) ---
  if (m.temp_c >= 90.f) { disparar(Falla::SOBRETEMPERATURA, ahora); return Salida{false, {0,0,0,0}, s.vdac, 0.f}; }
  if (m.iout > 1.5f * lim) {
    if (!sobre_activo_) { sobre_activo_ = true; t_sobre_ = ahora; }
    if (ahora - t_sobre_ >= T_DISPARO_OC) {
      disparar(m.vout < 0.5f * vset_ ? Falla::CORTO : Falla::SOBRECORRIENTE, ahora);
      return Salida{false, {0,0,0,0}, s.vdac, 0.f};
    }
  } else sobre_activo_ = false;
  if (arrancado && m.vin > 1.f && m.vin < vset_ + 1.2f) {
    disparar(Falla::SUBVOLTAJE_ENTRADA, ahora); return Salida{false, {0,0,0,0}, s.vdac, 0.f};
  }
  if (arrancado && m.iout < 0.05f * lim && m.vout > 1.10f * vset_ + 0.2f) {
    // Sin carga y el voltaje medido supera lo pedido: R_FB no corresponde al perfil.
    disparar(Falla::TARJETA_INCONSISTENTE, ahora); reintentos_ = 255;
    return Salida{false, {0,0,0,0}, s.vdac, 0.f};
  }
  if (arrancado && reintentos_ && falla_ == Falla::NINGUNA && ahora - t_falla_ > 60000) reintentos_ = 0;

  // --- Limitación suave de corriente (baja brillo antes de disparar) ---
  if (m.iout > lim) recorte_i_ *= 0.97f;
  else if (m.iout < 0.95f * lim && recorte_i_ < 1.f) recorte_i_ = fminf(1.f, recorte_i_ + 0.004f);
  if (recorte_i_ < 0.05f) recorte_i_ = 0.05f;

  // --- Arranque suave ---
  if (rampa_ < 1.f) rampa_ = fminf(1.f, rampa_ + (float)dt / T_RAMPA);

  // --- Efectos (tiras analógicas: toda la tira igual) ---
  float b = brillo_;
  t_efecto_ = ahora;
  bool dmx = dmxActivo(ahora);
  RGBW c;
  uint8_t quinto = 0;
  if (dmx) {                                       // DMX manda: atenuador + 4 canales
    const uint8_t* d = dmx_ + (dmx_dir_ - 1);
    int disp = dmx_n_ - (dmx_dir_ - 1);
    auto canal = [&](int k) -> uint8_t { return k < disp ? d[k] : 0; };
    b = direccionable(tira_) ? 1.f : canal(0) / 255.f;
    c = {canal(1), canal(2), canal(3), canal(4)};
    quinto = canal(5);
  } else {
    if (modo_ == Modo::RESPIRA || modo_ == Modo::COMETA) b *= respiro(ahora);
    c = colorPixel(0, 1, ahora);
  }

  float k = b * rampa_ * factorTermico(m.temp_c) * recorte_i_;
  s.brillo_efectivo = k;
  if (!direccionable(tira_)) {
    uint8_t ch[5] = {c.r, c.g, c.b, c.w, 0};
    if (tira_ == Tira::RGB) ch[3] = 0;
    else if (tira_ == Tira::RGBCCT) {              // W = nivel de blanco, repartido entre cálido y frío
      if (dmx) ch[4] = quinto;
      else { RGBW w = mezclaCCT(cct_); ch[3] = (uint8_t)(c.w * w.r / 255); ch[4] = (uint8_t)(c.w * w.g / 255); }
    }
    else if (tira_ == Tira::CCT) { RGBW w = dmx ? RGBW{c.r, c.g, 0, 0} : mezclaCCT(cct_); ch[0] = w.r; ch[1] = w.g; ch[2] = 0; ch[3] = 0; }
    else if (tira_ == Tira::MONO) { ch[3] = dmx ? c.r : 255; ch[0] = ch[1] = ch[2] = 0; }
    for (int i = 0; i < 5; ++i) s.pwm[i] = (uint16_t)lroundf(gamma12(ch[i]) * k);
  }
  return s;
}

// ---------------- Tiras ----------------
const char* nombreTira(Tira t) {
  static const char* n[] = {"RGBW", "RGB", "CCT", "MONO", "WS2812B", "SK6812", "WS2811", "WS2815", "RGBCCT"};
  return n[(int)t];
}
bool igual(const char* a, const char* b);
bool tiraDeTexto(const char* s, Tira& t) {
  for (int i = 0; i <= (int)Tira::RGBCCT; ++i) if (igual(s, nombreTira((Tira)i))) { t = (Tira)i; return true; }
  if (igual(s, "WS2812")) { t = Tira::WS2812B; return true; }
  return false;
}
bool direccionable(Tira t) { return t >= Tira::WS2812B && t <= Tira::WS2815; }
uint8_t bytesPorLed(Tira t) { return t == Tira::SK6812 ? 4 : 3; }
float tensionTira(Tira t) {
  switch (t) { case Tira::WS2812B: case Tira::SK6812: return 5.f; case Tira::WS2811: case Tira::WS2815: return 12.f; default: return 0.f; }
}
RGBW mezclaCCT(uint16_t k) {
  float m = (k - 2700.f) / (6500.f - 2700.f);
  if (m < 0) m = 0;
  if (m > 1) m = 1;
  float ww = 1.f - m, cw = m, mx = ww > cw ? ww : cw;      // a 4600 K ambos al 100 %
  return {(uint8_t)lroundf(255 * ww / mx), (uint8_t)lroundf(255 * cw / mx), 0, 0};
}
uint8_t ordenarBytes(Tira t, RGBW c, uint8_t* o) {
  switch (t) {
    case Tira::WS2811: o[0] = c.r; o[1] = c.g; o[2] = c.b; return 3;
    case Tira::SK6812: o[0] = c.g; o[1] = c.r; o[2] = c.b; o[3] = c.w; return 4;
    default:           o[0] = c.g; o[1] = c.r; o[2] = c.b; return 3;   // WS2812B, WS2815
  }
}
const char* nombreModo(Modo m) {
  static const char* n[] = {"fijo", "respira", "arcoiris", "fuego", "cometa"};
  return n[(int)m];
}
static float respiro(uint32_t t) { return 0.15f + 0.85f * (0.5f - 0.5f * cosf(2.f * 3.14159265f * (t % 4000) / 4000.f)); }
static uint32_t mezclar(uint32_t x) { x ^= x >> 16; x *= 0x7feb352dU; x ^= x >> 15; x *= 0x846ca68bU; x ^= x >> 16; return x; }

RGBW Controlador::colorPixel(uint16_t i, uint16_t n, uint32_t t) const {
  if (n == 0) n = 1;
  if (direccionable(tira_) && dmxActivo(t)) {      // un LED por cada 3 (o 4) canales
    uint8_t bpp = bytesPorLed(tira_);
    uint32_t k = (uint32_t)(dmx_dir_ - 1) + (uint32_t)i * bpp;
    if (k + bpp > dmx_n_) return {0, 0, 0, 0};
    return {dmx_[k], dmx_[k + 1], dmx_[k + 2], bpp == 4 ? dmx_[k + 3] : (uint8_t)0};
  }
  switch (modo_) {
    case Modo::ARCOIRIS: return rueda((uint8_t)((i * 256u / n + t / 40) & 0xFF));
    case Modo::FUEGO: {
      uint32_t h = mezclar(i * 7919u + (t / 70) * 104729u);
      float f = 0.45f + 0.55f * (h & 0xFF) / 255.f;           // parpadeo cálido
      return {(uint8_t)(255 * f), (uint8_t)((70 + (h >> 8 & 0x3F)) * f), 0, (uint8_t)(color_.w * f)};
    }
    case Modo::COMETA: {
      if (n == 1) return color_;
      uint16_t cabeza = (uint16_t)((t / 25) % n);
      uint16_t d = (uint16_t)((cabeza + n - i) % n);
      float f = d > 12 ? 0.f : 1.f - d / 12.f;
      return {(uint8_t)(color_.r * f), (uint8_t)(color_.g * f), (uint8_t)(color_.b * f), (uint8_t)(color_.w * f)};
    }
    case Modo::RESPIRA: case Modo::FIJO: default: return color_;
  }
}

bool Controlador::fijarTira(Tira t) {
  float vt = tensionTira(t);
  if (t == Tira::RGBCCT && !cinco_canales_) return false;
  if (vt > 0.f) {                                   // direccionable: la tarjeta debe dar su voltaje (±10 %)
    float vm = vmaxPerfil();
    if (vm <= 0.f || vm < vt * 0.9f || vm > vt * 1.1f) return false;
  }
  tira_ = t; return true;
}
bool Controlador::fijarCCT(uint16_t k) {
  if (k < 2700 || k > 6500) return false;
  cct_ = k; return true;
}
void Controlador::fijarHora(uint32_t epoch, uint32_t ahora) { epoch_ref_ = epoch; ms_ref_ = ahora; hora_ok_ = true; ultimo_min_ = -1; }
int Controlador::minutoDelDia(uint32_t ahora) const {
  if (!hora_ok_) return -1;
  uint32_t s = epoch_ref_ + (ahora - ms_ref_) / 1000;
  return (int)((s / 60) % 1440);
}
bool Controlador::programar(bool activo, uint16_t a, uint16_t b) {
  if (activo && (a >= 1440 || b >= 1440 || a == b)) return false;
  prog_on_ = activo; min_on_ = a; min_off_ = b; ultimo_min_ = -1; return true;
}

static const char* tras(const char* json, const char* clave) {   // apunta al valor de "clave":
  char k[16]; snprintf(k, sizeof k, "\"%s\"", clave);
  const char* p = strstr(json, k);
  if (!p) return nullptr;
  p += strlen(k);
  while (*p == ' ') ++p;
  if (*p != ':') return nullptr;
  ++p; while (*p == ' ') ++p;
  return p;
}
bool Controlador::aplicarWled(const char* js) {
  bool hubo = false;
  if (const char* p = tras(js, "on")) {
    if (!strncmp(p, "true", 4)) { encender(true); hubo = true; }
    else if (!strncmp(p, "false", 5)) { encender(false); hubo = true; }
    else if (!strncmp(p, "\"t\"", 3)) { encender(!on_); hubo = true; }
  }
  if (const char* p = tras(js, "bri")) {
    char* e; long v = strtol(p, &e, 10);
    if (e != p && v >= 0 && v <= 255) { if (v == 0) encender(false); else brillo_ = v / 255.f; hubo = true; }
  }
  if (const char* p = tras(js, "col")) {
    while (*p == '[' || *p == ' ') ++p;
    long v[4] = {0, 0, 0, color_.w}; int k = 0;
    while (k < 4) {
      char* e; long x = strtol(p, &e, 10);
      if (e == p || x < 0 || x > 255) break;
      v[k++] = x; p = e; while (*p == ' ' || *p == ',') ++p;
      if (*p == ']') break;
    }
    if (k >= 3) { color_ = {(uint8_t)v[0], (uint8_t)v[1], (uint8_t)v[2], (uint8_t)v[3]}; hubo = true; }
  }
  return hubo;
}
size_t Controlador::estadoWled(char* buf, size_t n) const {
  int w = snprintf(buf, n, "{\"on\":%s,\"bri\":%d,\"seg\":[{\"id\":0,\"col\":[[%u,%u,%u,%u]],\"fx\":%d}]}",
                   on_ ? "true" : "false", (int)lroundf(brillo_ * 255), color_.r, color_.g, color_.b, color_.w, (int)modo_);
  return w < 0 ? 0 : ((size_t)w < n ? (size_t)w : n - 1);
}

// ---------------- DMX por red ----------------
static uint16_t be16(const uint8_t* p) { return (uint16_t)(p[0] << 8 | p[1]); }
bool leerArtNet(const uint8_t* p, size_t len, uint16_t& u, const uint8_t*& d, uint16_t& n) {
  if (len < 18 || memcmp(p, "Art-Net\0", 8) != 0) return false;
  if ((p[8] | p[9] << 8) != 0x5000 || p[11] < 14) return false;      // OpDmx, versión ≥ 14
  u = (uint16_t)((p[15] & 0x7F) << 8 | p[14]);
  n = be16(p + 16);
  if (n < 2 || n > 512 || 18u + n > len) return false;
  d = p + 18; return true;
}
bool leerE131(const uint8_t* p, size_t len, uint16_t& u, const uint8_t*& d, uint16_t& n) {
  static const uint8_t ID[12] = {'A', 'S', 'C', '-', 'E', '1', '.', '1', '7', 0, 0, 0};
  if (len < 126 || be16(p) != 0x0010 || memcmp(p + 4, ID, 12) != 0) return false;
  if (p[18] || p[19] || p[20] || p[21] != 0x04) return false;          // raíz: datos
  if (p[40] || p[41] || p[42] || p[43] != 0x02) return false;          // trama: DMP
  if (p[112] & 0x40) return false;                                      // stream_terminated
  if (p[117] != 0x02 || p[118] != 0xA1 || p[125] != 0x00) return false; // DMP, código de inicio 0
  u = be16(p + 113);
  uint16_t cuenta = be16(p + 123);
  if (cuenta < 1 || cuenta > 513 || 125u + cuenta > len) return false;
  n = cuenta - 1; d = p + 126; return true;
}
bool Controlador::configurarDmx(ProtoDmx p, uint16_t u, uint16_t dir) {
  if (p == ProtoDmx::CABLE) u = 0;
  if (dir < 1 || dir > 512 || (p == ProtoDmx::SACN && (u < 1 || u > 63999)) || (p == ProtoDmx::ARTNET && u > 32767)) return false;
  dmx_proto_ = p; dmx_univ_ = u; dmx_dir_ = dir; t_dmx_ = 0; return true;
}
bool Controlador::paqueteRed(const uint8_t* p, size_t len, uint32_t ahora) {
  uint16_t u, n; const uint8_t* d;
  bool ok = dmx_proto_ == ProtoDmx::ARTNET ? leerArtNet(p, len, u, d, n) :
            dmx_proto_ == ProtoDmx::SACN ? leerE131(p, len, u, d, n) : false;
  if (!ok || u != dmx_univ_) return false;
  return entradaDmx(d, n, ahora);
}
bool Controlador::entradaDmx(const uint8_t* d, uint16_t n, uint32_t ahora) {
  if (dmx_proto_ == ProtoDmx::OFF || n > 512) return false;
  memcpy(dmx_, d, n); dmx_n_ = n; t_dmx_ = ahora ? ahora : 1;
  if (!on_) encender(true);
  return true;
}
void ReceptorDmx::ruptura() {
  if (n_ >= 2 && trabajo_[0] == 0x00 && !hay_) {   // código de inicio 0 = niveles
    n_lista_ = n_ - 1; memcpy(lista_, trabajo_ + 1, n_lista_); hay_ = true; ++tramas_;
  }
  n_ = 0;
}
bool ReceptorDmx::tomar(uint8_t* destino, uint16_t& n) {
  if (!hay_) return false;
  n = n_lista_; memcpy(destino, lista_, n); hay_ = false; return true;
}
bool Controlador::dmxActivo(uint32_t ahora) const {
  return dmx_proto_ != ProtoDmx::OFF && t_dmx_ && ahora - t_dmx_ < 2500;
}

// ---------------- Escenas ----------------
bool Controlador::guardarEscena(int i) {
  if (i < 1 || i > N_ESCENAS) return false;
  escenas_[i - 1] = {true, color_, (uint8_t)lroundf(brillo_ * 100), modo_, cct_}; return true;
}
bool Controlador::aplicarEscena(int i) {
  if (i < 1 || i > N_ESCENAS || !escenas_[i - 1].ok) return false;
  const Escena& e = escenas_[i - 1];
  color_ = e.color; brillo_ = e.brillo / 100.f; modo_ = e.modo; cct_ = e.cct; return true;
}

unsigned Controlador::mascaraEscenas() const {
  unsigned m = 0; for (int i = 0; i < N_ESCENAS; ++i) if (escenas_[i].ok) m |= 1u << i; return m;
}
size_t Controlador::estadoJson(char* buf, size_t n, const Medicion& m) const {
  float vmax = vmaxPerfil();
  int w = snprintf(buf, n,
    "{\"on\":%d,\"perfil\":\"%s\",\"vmax\":%.2f,\"vmin\":%.2f,\"imax\":%.2f,\"vset\":%.2f,"
    "\"v\":%.2f,\"i\":%.3f,\"w\":%.1f,\"vin\":%.1f,\"t\":%.1f,\"brillo\":%d,"
    "\"rgbw\":[%u,%u,%u,%u],\"modo\":\"%s\",\"falla\":\"%s\",\"tira\":\"%s\",\"cct\":%u,"
    "\"prog\":%s,\"on_min\":%u,\"off_min\":%u,\"hora\":%d,\"dmx\":\"%s\",\"univ\":%u,\"dir\":%u,"
    "\"dmx_vivo\":%s,\"escenas\":%u}",
    on_ ? 1 : 0, perfil_ < 0 ? "-" : PERFILES[perfil_].nombre, vmax,
    perfil_ < 0 ? 0.f : vminDeRed(red_), limiteCorriente(), vset_,
    m.vout, m.iout, m.vout * m.iout, m.vin, m.temp_c, (int)lroundf(brillo_ * 100),
    color_.r, color_.g, color_.b, color_.w, nombreModo(modo_), nombreFalla(falla_), nombreTira(tira_), cct_,
    prog_on_ ? "true" : "false", min_on_, min_off_, minutoDelDia(t_ultimo_),
    dmx_proto_ == ProtoDmx::ARTNET ? "artnet" : dmx_proto_ == ProtoDmx::SACN ? "sacn" : dmx_proto_ == ProtoDmx::CABLE ? "cable" : "off", dmx_univ_, dmx_dir_,
    dmxActivo(t_ultimo_) ? "true" : "false", mascaraEscenas());
  return w < 0 ? 0 : ((size_t)w < n ? (size_t)w : n - 1);
}

// ---------------- Protocolo ----------------
bool igual(const char* a, const char* b);
bool igual(const char* a, const char* b) {
  while (*a && *b) { if (toupper((unsigned char)*a) != toupper((unsigned char)*b)) return false; ++a; ++b; }
  return *a == 0 && *b == 0;
}
static size_t resp(char* r, size_t n, const char* t) { snprintf(r, n, "%s", t); return strlen(r); }

size_t procesarComando(Controlador& c, const char* linea, const Medicion& m, char* r, size_t n) {
  char buf[64];
  size_t L = strnlen(linea, sizeof(buf) - 1);
  memcpy(buf, linea, L); buf[L] = 0;
  while (L && (buf[L-1] == '\n' || buf[L-1] == '\r' || buf[L-1] == ' ')) buf[--L] = 0;
  char* arg[6] = {}; int na = 0;
  for (char* t = strtok(buf, " "); t && na < 6; t = strtok(nullptr, " ")) arg[na++] = t;
  if (!na) return resp(r, n, "ERR vacio");
  auto num = [](const char* s, float& out) { char* e; out = strtof(s, &e); return e != s && *e == 0; };

  if (igual(arg[0], "ON"))  return resp(r, n, c.encender(true) ? "OK" : "ERR sin_tarjeta");
  if (igual(arg[0], "OFF")) { c.encender(false); return resp(r, n, "OK"); }
  if (igual(arg[0], "ESTADO")) return c.estadoJson(r, n, m);
  if (igual(arg[0], "RESET")) { c.reconocerFalla(); return resp(r, n, "OK"); }
  if (igual(arg[0], "BRILLO") && na == 2) {
    float b; if (!num(arg[1], b) || b < 0 || b > 100) return resp(r, n, "ERR rango 0-100");
    c.fijarBrillo(b / 100.f); return resp(r, n, "OK");
  }
  if (igual(arg[0], "V") && na == 2) {
    float v; if (!num(arg[1], v) || !c.fijarVoltaje(v)) return resp(r, n, "ERR voltaje");
    snprintf(r, n, "OK %.2f", c.vset()); return strlen(r);
  }
  if (igual(arg[0], "RGBW") && na == 5) {
    float v[4];
    for (int i = 0; i < 4; ++i) if (!num(arg[i+1], v[i]) || v[i] < 0 || v[i] > 255) return resp(r, n, "ERR rango 0-255");
    c.fijarColor({(uint8_t)v[0], (uint8_t)v[1], (uint8_t)v[2], (uint8_t)v[3]}); return resp(r, n, "OK");
  }
  if (igual(arg[0], "MODO") && na == 2) {
    for (int i = 0; i <= (int)Modo::COMETA; ++i)
      if (igual(arg[1], nombreModo((Modo)i))) { c.fijarModo((Modo)i); return resp(r, n, "OK"); }
    return resp(r, n, "ERR modo");
  }
  if (igual(arg[0], "TIRA") && na == 2) {
    Tira t; if (!tiraDeTexto(arg[1], t)) return resp(r, n, "ERR tira");
    if (!c.fijarTira(t)) { snprintf(r, n, "ERR %s necesita tarjeta de %.0f V", nombreTira(t), tensionTira(t)); return strlen(r); }
    return resp(r, n, "OK");
  }
  if (igual(arg[0], "CCT") && na == 2) {
    float k; if (!num(arg[1], k) || !c.fijarCCT((uint16_t)k)) return resp(r, n, "ERR rango 2700-6500");
    return resp(r, n, "OK");
  }
  if (igual(arg[0], "HORA") && na == 2) {
    char* e; unsigned long v = strtoul(arg[1], &e, 10);
    if (e == arg[1] || *e) return resp(r, n, "ERR hora");
    c.fijarHora((uint32_t)v, c.ahora()); return resp(r, n, "OK");
  }
  if (igual(arg[0], "PROG")) {
    if (na == 2 && igual(arg[1], "OFF")) { c.programar(false, 0, 0); return resp(r, n, "OK"); }
    unsigned h1, m1, h2, m2;
    if (na == 3 && sscanf(arg[1], "%u:%u", &h1, &m1) == 2 && sscanf(arg[2], "%u:%u", &h2, &m2) == 2 &&
        h1 < 24 && m1 < 60 && h2 < 24 && m2 < 60 && c.programar(true, h1 * 60 + m1, h2 * 60 + m2)) return resp(r, n, "OK");
    return resp(r, n, "ERR usa PROG hh:mm hh:mm o PROG OFF");
  }
  if (igual(arg[0], "ESCENA")) {
    if (na == 3 && igual(arg[1], "GUARDAR")) { int i = atoi(arg[2]); return resp(r, n, c.guardarEscena(i) ? "OK" : "ERR escena 1-8"); }
    if (na == 2) { int i = atoi(arg[1]); return resp(r, n, c.aplicarEscena(i) ? "OK" : "ERR escena vacía o fuera de 1-8"); }
    return resp(r, n, "ERR usa ESCENA n o ESCENA GUARDAR n");
  }
  if (igual(arg[0], "DMX")) {
    if (na == 2 && igual(arg[1], "OFF")) { c.configurarDmx(ProtoDmx::OFF, 0, 1); return resp(r, n, "OK"); }
    if (na == 3 && igual(arg[1], "CABLE")) {
      if (c.configurarDmx(ProtoDmx::CABLE, 0, (uint16_t)atoi(arg[2]))) return resp(r, n, "OK");
    }
    if (na == 4 && (igual(arg[1], "ARTNET") || igual(arg[1], "SACN"))) {
      ProtoDmx p = igual(arg[1], "ARTNET") ? ProtoDmx::ARTNET : ProtoDmx::SACN;
      if (c.configurarDmx(p, (uint16_t)atoi(arg[2]), (uint16_t)atoi(arg[3]))) return resp(r, n, "OK");
    }
    return resp(r, n, "ERR usa DMX ARTNET|SACN universo direccion, DMX CABLE direccion o DMX OFF");
  }
  if (igual(arg[0], "LIMITES") && na == 3) {
    float v, i; if (!num(arg[1], v) || !num(arg[2], i) || !c.fijarLimitesPersonal(v, i)) return resp(r, n, "ERR solo tarjeta PERSONAL, 3-24.4 V y 0.2-5 A");
    return resp(r, n, "OK");
  }
  return resp(r, n, "ERR comando");
}

} // namespace ap
