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
#include "ap_link.h"

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
inline bool orden(aplink::Enlace& e, const char* s, uint16_t* seguraLocal) {
  while (*s == ' ') s++;
  if (!*s) return false;
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
    bool on = b == 2 ? !((e.modulo(pos)->deseadas >> (loc - 1)) & 1) : b == 1;
    return e.mandarCanal((uint16_t)a, on);
  }
  if (c == 'A') {
    if (!numero(p, &a) || a < 0 || a > 1) return false;
    for (uint8_t q = 1; q <= aplink::MAX_MODULOS; q++)
      if (const aplink::InfoMod* m = e.modulo(q)) e.mandar(q, a ? (uint16_t)((m->caps.nSal >= 16) ? 0xFFFF : ((1u << m->caps.nSal) - 1)) : 0);
    return true;
  }
  if (c == 'M') {
    if (!numero(p, &a) || !numero(p, &b) || a < 1 || a > aplink::MAX_MODULOS || b < 0 || b > 0xFFFF) return false;
    return e.mandar((uint8_t)a, (uint16_t)b);
  }
  return false;
}

struct Esc {
  char* b; size_t n, i = 0;
  Esc(char* buf, size_t cap) : b(buf), n(cap) { if (n) b[0] = 0; }
  void s(const char* t) { while (*t && i + 1 < n) b[i++] = *t++; if (n) b[i] = 0; }
  void u(unsigned long v) { char t[16]; snprintf(t, sizeof t, "%lu", v); s(t); }
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
inline void modJson(Esc& o, uint8_t p, uint32_t uid, const aplink::Caps& c, uint16_t s, uint16_t en, uint16_t v, uint16_t f, bool ok, bool seg) {
  o.s("{\"p\":"); o.u(p); o.s(",\"id\":\""); o.h(uid); o.s("\",\"tp\":"); o.u(c.tipo); o.s(",\"ns\":"); o.u(c.nSal); o.s(",\"ne\":"); o.u(c.nEnt);
  o.s(",\"s\":"); o.u(s); o.s(",\"e\":"); o.u(en); o.s(",\"v\":"); o.u(v); o.s(",\"f\":"); o.u(f);
  o.s(",\"ok\":"); o.s(ok ? "1" : "0"); o.s(",\"seg\":"); o.s(seg ? "1" : "0"); o.s("}");
}

inline size_t json(char* buf, size_t cap, const aplink::Enlace& e, const char* version, const char* id, uint32_t segundos) {
  Esc o(buf, cap);
  bool cab = e.rol() == aplink::Rol::CABEZA;
  uint16_t ns = cab ? e.totalSalidas() : e.caps().nSal, ne = cab ? e.totalEntradas() : e.caps().nEnt;
  o.s("{\"v\":\""); o.s(version); o.s("\",\"placa\":\"AP Rack 16\",\"api\":2,\"cap\":[\"salidas\",\"entradas\",\"aplink\",\"modulos\"],");
  o.s("\"rol\":\""); o.s(nombreRol(e.rol())); o.s("\",\"pos\":"); o.u(e.pos()); o.s(",\"total\":"); o.u(cab ? e.total() : (e.total() ? e.total() : (e.pos() ? e.pos() : 1)));
  o.s(",\"n\":"); o.u(ns); o.s(",\"ne\":"); o.u(ne); o.s(",\"enl\":{\"mal\":"); o.u(e.malas()); o.s("},\"mods\":[");
  if (cab) {
    bool primero = true;
    for (uint8_t p = 1; p <= aplink::MAX_MODULOS; p++) {
      const aplink::InfoMod* m = e.modulo(p);
      if (!m) continue;
      if (!primero) o.s(",");
      primero = false;
      modJson(o, p, m->uid, m->caps, m->sal, m->ent, m->vin_mV, m->fallas, !m->perdido, (m->flags & 1) != 0);
    }
  } else {
    modJson(o, e.pos(), e.uid(), e.caps(), e.salAplicadas(), e.entLocal(), e.vinLocal(), e.fallasLocales(), true, e.enSeguro());
  }
  o.s("],\"id\":\""); o.s(id); o.s("\",\"t\":"); o.u(segundos); o.s("}");
  return o.i;
}

}  // namespace aprack
