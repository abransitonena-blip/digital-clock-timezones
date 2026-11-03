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

// ---------------- Controlador ----------------
static const uint32_t T_RAMPA = 600, T_REINTENTO = 5000, T_DISPARO_OC = 50;
static const uint8_t MAX_REINTENTOS = 3;

void Controlador::configurar(int perfil, const RedFB& red) {
  perfil_ = perfil; red_ = red;
  falla_ = perfil < 0 ? Falla::SIN_TARJETA : Falla::NINGUNA;
  vset_ = perfil < 0 ? 0.f : PERFILES[perfil].vmax;
  if (perfil >= 0 && vset_ > vmaxRed(red_)) vset_ = vmaxRed(red_);
}

float Controlador::limiteCorriente() const { return perfil_ < 0 ? 0.f : PERFILES[perfil_].imax; }

bool Controlador::encender(bool on) {
  if (on && perfil_ < 0) return false;
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
  float vmax = PERFILES[perfil_].vmax, vmin = vminDeRed(red_);
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

  // --- Efectos ---
  float b = brillo_;
  RGBW c = color_;
  t_efecto_ = ahora;
  if (modo_ == Modo::RESPIRA) {
    float f = 0.5f - 0.5f * cosf(2.f * 3.14159265f * (ahora % 4000) / 4000.f);
    b *= 0.15f + 0.85f * f;
  } else if (modo_ == Modo::ARCOIRIS) {
    c = rueda((uint8_t)((ahora / 40) & 0xFF));
  }

  float k = b * rampa_ * factorTermico(m.temp_c) * recorte_i_;
  s.brillo_efectivo = k;
  if (modo_ != Modo::DIRECCIONABLE) {
    const uint8_t ch[4] = {c.r, c.g, c.b, c.w};
    for (int i = 0; i < 4; ++i) s.pwm[i] = (uint16_t)lroundf(gamma12(ch[i]) * k);
  }
  return s;
}

size_t Controlador::estadoJson(char* buf, size_t n, const Medicion& m) const {
  const char* modos[] = {"fijo", "respira", "arcoiris", "direc"};
  float vmax = perfil_ < 0 ? 0.f : PERFILES[perfil_].vmax;
  int w = snprintf(buf, n,
    "{\"on\":%d,\"perfil\":\"%s\",\"vmax\":%.2f,\"vmin\":%.2f,\"imax\":%.2f,\"vset\":%.2f,"
    "\"v\":%.2f,\"i\":%.3f,\"w\":%.1f,\"vin\":%.1f,\"t\":%.1f,\"brillo\":%d,"
    "\"rgbw\":[%u,%u,%u,%u],\"modo\":\"%s\",\"falla\":\"%s\"}",
    on_ ? 1 : 0, perfil_ < 0 ? "-" : PERFILES[perfil_].nombre, vmax,
    perfil_ < 0 ? 0.f : vminDeRed(red_), limiteCorriente(), vset_,
    m.vout, m.iout, m.vout * m.iout, m.vin, m.temp_c, (int)lroundf(brillo_ * 100),
    color_.r, color_.g, color_.b, color_.w, modos[(int)modo_], nombreFalla(falla_));
  return w < 0 ? 0 : ((size_t)w < n ? (size_t)w : n - 1);
}

// ---------------- Protocolo ----------------
static bool igual(const char* a, const char* b) {
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
    if (igual(arg[1], "FIJO")) c.fijarModo(Modo::FIJO);
    else if (igual(arg[1], "RESPIRA")) c.fijarModo(Modo::RESPIRA);
    else if (igual(arg[1], "ARCOIRIS")) c.fijarModo(Modo::ARCOIRIS);
    else if (igual(arg[1], "DIREC")) c.fijarModo(Modo::DIRECCIONABLE);
    else return resp(r, n, "ERR modo");
    return resp(r, n, "OK");
  }
  return resp(r, n, "ERR comando");
}

} // namespace ap
