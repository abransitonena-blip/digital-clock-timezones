// AP Rack 16: órdenes y JSON del equipo (API 2 con módulos). Portable: sin Arduino, sin memoria dinámica.
//
// Órdenes (las que acepta el cabeza; un esclavo responde «?»):
//   C g v      canal global g (1 = salida 1 del módulo 1; el módulo 2 sigue donde acaba el 1); v = 0 apaga, 1 enciende, 2 alterna
//   A v        todas las salidas de todos los módulos (0 o 1)
//   M p máscara   las 16 salidas del módulo p de una vez (decimal o 0x...)
//   S máscara  máscara segura de ESTE módulo (qué salidas quedan encendidas si pierde el enlace; de fábrica 0 = todo apagado)
//   ?          solo lee
// El JSON que devuelve va en una línea (la consola USB lo lee igual que el de AP Control).
#pragma once
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>
#include <strings.h>
#include "ap_link.h"
#include "plc_rack.h"

namespace aprack {

inline bool numero(const char*& p, long* v) {
  while (*p == ' ') p++;
  if (!*p) return false;
  char* fin = nullptr;
  long x = strtol(p, &fin, 0);
  if (fin == p) return false;
  p = fin; *v = x; return true;
}

// Devuelve true si la orden es válida y se aceptó. `seguraLocal` es la máscara segura de este módulo (el programa la guarda en memoria).
inline bool orden(aplink::Enlace& e, const char* s, uint16_t* seguraLocal, PlcRack* plc = nullptr) {
  while (*s == ' ') s++;
  if (!*s) return false;
  if (!strncasecmp(s, "PLC ", 4)) {                                    // PLC RUN | STOP | BORRAR | TXT renglón | renglón | ...
    if (!plc || e.rol() != aplink::Rol::CABEZA) return false;
    const char* a = s + 4; while (*a == ' ') a++;
    if (!strcasecmp(a, "RUN")) { plc->modo(true); return plc->run; }
    if (!strcasecmp(a, "STOP")) { plc->modo(false); return true; }
    if (!strcasecmp(a, "BORRAR")) { plc->borrar(); return true; }
    if ((a[0] == 'M' || a[0] == 'm' || a[0] == 'R' || a[0] == 'r') && a[1] == ' ') {           // PLC M n 0|1 · PLC R n valor (del panel)
      const char* q = a + 2; long n = 0;
      if (!numero(q, &n)) return false;
      while (*q == ' ') q++;
      if (!*q) return false;
      if (a[0] == 'M' || a[0] == 'm') { char* fin; long v = strtol(q, &fin, 10); return fin != q && (v == 0 || v == 1) && plc->ponerM((int)n, v == 1); }
      char* fin; double v = strtod(q, &fin); return fin != q && plc->ponerR((int)n, (float)v);
    }
    if (!strncasecmp(a, "TXT ", 4)) {
      char buf[sizeof(plc->texto)]; size_t n = strlen(a + 4);
      if (n >= sizeof buf) return false;
      for (size_t i = 0; i <= n; i++) buf[i] = a[4 + i] == '|' ? '\n' : a[4 + i];
      return plc->cargar(buf);
    }
    return false;
  }
  char c = toupper((unsigned char)s[0]);
  const char* p = s + 1;
  if (c == '?') return true;
  long a = 0, b = 0;
  if (c == 'S') {
    if (!numero(p, &a) || a < 0 || a > 0xFFFF) return false;
    *seguraLocal = (uint16_t)a; e.maskSegura((uint16_t)a); return true;
  }
  if (e.rol() != aplink::Rol::CABEZA) return false;                 // solo el cabeza manda salidas
  if (c == 'C') {
    if (!numero(p, &a) || !numero(p, &b) || b < 0 || b > 2 || a < 1) return false;
    uint8_t pos, loc;
    if (!e.canalGlobal((uint16_t)a, &pos, &loc)) return false;
    if (plc && plc->poseeCanal((uint16_t)a)) return false;              // lo maneja el programa PLC
    bool on = b == 2 ? !((e.modulo(pos)->deseadas >> (loc - 1)) & 1) : b == 1;
    return e.mandarCanal((uint16_t)a, on);
  }
  if (c == 'A') {
    if (!numero(p, &a) || a < 0 || a > 1) return false;
    for (uint8_t q = 1; q <= aplink::MAX_MODULOS; q++)
      if (const aplink::InfoMod* m = e.modulo(q)) {
        uint16_t todos = (uint16_t)((m->caps.nSal >= 16) ? 0xFFFF : ((1u << m->caps.nSal) - 1)), d = plc ? plc->duenoDe(q) : 0;
        e.mandar(q, (uint16_t)((a ? todos : 0) & ~d) | (m->deseadas & d));
      }
    return true;
  }
  if (c == 'M') {
    if (!numero(p, &a) || !numero(p, &b) || a < 1 || a > aplink::MAX_MODULOS || b < 0 || b > 0xFFFF) return false;
    uint16_t d = plc ? plc->duenoDe((uint8_t)a) : 0;
    const aplink::InfoMod* m = e.modulo((uint8_t)a);
    return m && e.mandar((uint8_t)a, (uint16_t)(((uint16_t)b & ~d) | (m->deseadas & d)));
  }
  return false;
}

// ADS1115 (±4.096 V, 0.125 mV por cuenta) -> milésimas: mV de la entrada (divisor 22 k / 10 k: x 3.2) o µA con el shunt de 150 Ω
// (en paralelo con el divisor: 149.3 Ω). Negativos = 0.
inline uint16_t analogica(int16_t raw, bool corriente) {
  float pin = raw > 0 ? raw * 0.125f : 0.0f, nodo = pin * 3.2f, v = corriente ? nodo * 6.698f : nodo;
  return v > 65535.0f ? 65535 : (uint16_t)v;
}

struct Esc {
  char* b; size_t n, i = 0;
  Esc(char* buf, size_t cap) : b(buf), n(cap) { if (n) b[0] = 0; }
  void s(const char* t) { while (*t && i + 1 < n) b[i++] = *t++; if (n) b[i] = 0; }
  void u(unsigned long v) { char t[16]; snprintf(t, sizeof t, "%lu", v); s(t); }
  void n_(long v) { char t[16]; snprintf(t, sizeof t, "%ld", v); s(t); }
  void h(uint32_t v) { char t[12]; snprintf(t, sizeof t, "%08lX", (unsigned long)v); s(t); }
};

inline const char* nombreRol(aplink::Rol r) {
  switch (r) {
    case aplink::Rol::CABEZA: return "cabeza";
    case aplink::Rol::ESCLAVO: return "esclavo";
    case aplink::Rol::ESPERA: return "espera";
    default: return "arrancando";
  }
}

// Un módulo del JSON: p posición, id uid en hexadecimal, tp tipo, ns/ne salidas y entradas, s salidas aplicadas, e entradas,
// v tensión de entrada en mV, f fallas, ok = 1 responde, seg = 1 salidas en estado seguro por pérdida del enlace.
inline void modJson(Esc& o, uint8_t p, uint32_t uid, const aplink::Caps& c, uint16_t s, uint16_t en, uint16_t v, uint16_t f, bool ok, bool seg,
                    const uint16_t* ana = nullptr, uint8_t anaModo = 0) {
  o.s("{\"p\":"); o.u(p); o.s(",\"id\":\""); o.h(uid); o.s("\",\"tp\":"); o.u(c.tipo); o.s(",\"ns\":"); o.u(c.nSal); o.s(",\"ne\":"); o.u(c.nEnt);
  o.s(",\"s\":"); o.u(s); o.s(",\"e\":"); o.u(en); o.s(",\"v\":"); o.u(v); o.s(",\"f\":"); o.u(f);
  o.s(",\"ok\":"); o.s(ok ? "1" : "0"); o.s(",\"seg\":"); o.s(seg ? "1" : "0");
  if (c.nAna) {
    o.s(",\"na\":"); o.u(c.nAna); o.s(",\"am\":"); o.u(anaModo); o.s(",\"a\":[");
    for (uint8_t i = 0; i < c.nAna && i < aplink::MAX_ANA; i++) { if (i) o.s(","); o.u(ana ? ana[i] : 0); }
    o.s("]");
  }
  o.s("}");
}

inline size_t json(char* buf, size_t cap, const aplink::Enlace& e, const char* version, const char* id, uint32_t segundos, const PlcRack* plc = nullptr) {
  Esc o(buf, cap);
  bool cab = e.rol() == aplink::Rol::CABEZA;
  uint16_t ns = cab ? e.totalSalidas() : e.caps().nSal, ne = cab ? e.totalEntradas() : e.caps().nEnt;
  o.s("{\"v\":\""); o.s(version); o.s("\",\"placa\":\""); o.s(e.caps().tipo == 3 ? "AP Rack AI8" : e.caps().tipo == 2 ? "AP Rack IN16" : "AP Rack 16"); o.s("\",\"api\":2,\"cap\":[\"salidas\",\"entradas\",\"aplink\",\"modulos\"" ); if (plc) o.s(",\"plc\""); o.s("],");
  o.s("\"rol\":\""); o.s(nombreRol(e.rol())); o.s("\",\"pos\":"); o.u(e.pos()); o.s(",\"total\":"); o.u(cab ? e.total() : (e.total() ? e.total() : (e.pos() ? e.pos() : 1)));
  o.s(",\"n\":"); o.u(ns); o.s(",\"ne\":"); o.u(ne); o.s(",\"enl\":{\"mal\":"); o.u(e.malas()); o.s("},\"mods\":[");
  if (cab) {
    bool primero = true;
    for (uint8_t p = 1; p <= aplink::MAX_MODULOS; p++) {
      const aplink::InfoMod* m = e.modulo(p);
      if (!m) continue;
      if (!primero) o.s(",");
      primero = false;
      modJson(o, p, m->uid, m->caps, m->sal, m->ent, m->vin_mV, m->fallas, !m->perdido, (m->flags & 1) != 0, m->ana, m->anaModo);
    }
  } else {
    modJson(o, e.pos(), e.uid(), e.caps(), e.salAplicadas(), e.entLocal(), e.vinLocal(), e.fallasLocales(), true, e.enSeguro(), e.anaLocal(), e.anaModoLocal());
  }
  o.s("]");
  if (plc) {                                                              // estado del PLC para el panel
    o.s(",\"plc\":{\"run\":"); o.s(plc->run ? "1" : "0"); o.s(",\"n\":"); o.u(plc->prog.n); o.s(",\"err\":\""); o.s(plc->prog.error); o.s("\",\"ciclos\":"); o.u(plc->prog.ciclos);
    o.s(",\"m\":["); bool pr = true;
    for (int k = 1; k <= logica::N_M; k++) if (plc->prog.m[k]) { if (!pr) o.s(","); pr = false; o.u(k); }
    o.s("],\"r\":["); for (int k = 0; k < 16; k++) { if (k) o.s(","); char tb[24]; snprintf(tb, sizeof tb, "%g", (double)plc->r[k]); o.s(tb); }
    o.s("],\"t\":["); for (int k = 1; k <= logica::N_T; k++) { if (k > 1) o.s(","); o.u(plc->prog.et(k)); }
    o.s("],\"c\":["); for (int k = 1; k <= logica::N_C; k++) { if (k > 1) o.s(","); o.n_((long)plc->prog.cv(k)); }
    o.s("]}");
  }
  o.s(",\"id\":\""); o.s(id); o.s("\",\"t\":"); o.u(segundos); o.s("}");
  return o.i;
}

}  // namespace aprack
