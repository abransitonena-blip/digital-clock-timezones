// Simulador de una cadena de módulos AP LINK (RS-485 compartido por tramo de cable, SENSE entre módulos, energía por módulo,
// tramas perdidas y dañadas). Cada paso es 1 ms. Lo usan prueba_link.cpp y prueba_rack.cpp.
#pragma once
#include <vector>
#include <deque>
#include <memory>
#include "../APRack/ap_link.h"
using namespace aplink;

struct Sim;
struct Nodo : HAL {
  Sim* s; int idx;
  std::unique_ptr<Enlace> e;
  bool altoSale = false;
  uint16_t ent = 0;
  Nodo(Sim* s_, int i) : s(s_), idx(i) {}
  void enviar(const uint8_t* p, size_t n) override;
  bool senseEntra() override;
  void senseSale(bool a) override { altoSale = a; }
  uint32_t ms() override;
};

struct Trafico { uint32_t t; int de; std::vector<uint8_t> b; };

struct Sim {
  uint32_t ahora = 0;
  std::vector<std::unique_ptr<Nodo>> n;
  std::vector<bool> cable;                  // cable[i]: unido el módulo i con el i+1
  std::deque<Trafico> cola;
  double pPerder = 0, pDanar = 0;
  uint32_t semilla = 12345;
  uint32_t tramas = 0;
  bool hayEnergia(int i) { return (bool)n[i]->e; }

  uint32_t rnd() { semilla = semilla * 1664525u + 1013904223u; return semilla >> 8; }
  double u() { return (rnd() & 0xFFFF) / 65536.0; }

  explicit Sim(int cuantos) {
    for (int i = 0; i < cuantos; i++) n.emplace_back(new Nodo(this, i));
    cable.assign(cuantos > 0 ? cuantos - 1 : 0, true);
  }
  void energia(int i, bool on, bool puedeCabeza = true) {
    if (on && !n[i]->e) {
      n[i]->altoSale = false;
      Caps c; c.tipo = 1; c.nSal = 16; c.nEnt = 8;
      n[i]->e.reset(new Enlace(*n[i], 0x1000u + 7919u * i, c, puedeCabeza));
    } else if (!on) { n[i]->e.reset(); n[i]->altoSale = false; }
  }
  bool mismoTramo(int a, int b) {
    if (a > b) { int t = a; a = b; b = t; }
    for (int i = a; i < b; i++) if (!cable[i]) return false;
    return true;
  }
  void poner(int de, const uint8_t* p, size_t k) {
    tramas++;
    if (u() < pPerder) return;
    Trafico t; t.t = ahora + 1; t.de = de; t.b.assign(p, p + k);
    if (u() < pDanar) t.b[rnd() % t.b.size()] ^= (uint8_t)(1u << (rnd() % 8));
    cola.push_back(t);
  }
  void paso() {
    ahora++;
    size_t m = cola.size();                    // solo lo que ya estaba en la cola (latencia mínima de 1 ms)
    for (size_t k = 0; k < m; k++) {
      Trafico t = cola.front(); cola.pop_front();
      for (size_t j = 0; j < n.size(); j++)
        if ((int)j != t.de && n[j]->e && mismoTramo(t.de, (int)j))
          for (uint8_t b : t.b) n[j]->e->recibir(b);
    }
    for (auto& nd : n) if (nd->e) { nd->e->ponerLocales(nd->ent, 0, 24000); nd->e->aplicadas(nd->e->salidas()); nd->e->tick(); }
  }
  void correr(uint32_t ms) { for (uint32_t i = 0; i < ms; i++) paso(); }
  Enlace* cabeza() {
    Enlace* c = nullptr;
    for (auto& nd : n) if (nd->e && nd->e->rol() == Rol::CABEZA) { if (c) return nullptr; c = nd->e.get(); }
    return c;
  }
  int cuantosCabezas() { int c = 0; for (auto& nd : n) if (nd->e && nd->e->rol() == Rol::CABEZA) c++; return c; }
};

void Nodo::enviar(const uint8_t* p, size_t k) { s->poner(idx, p, k); }
bool Nodo::senseEntra() {
  if (idx == 0 || !s->cable[idx - 1]) return true;          // sin cable: la resistencia a 3.3 V
  Nodo& a = *s->n[idx - 1];
  return a.e ? a.altoSale : false;                          // módulo anterior sin energía: su resistencia a 0 V
}
uint32_t Nodo::ms() { return s->ahora; }

