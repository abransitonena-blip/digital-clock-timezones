// PLC (AP LÓGICA) del cabeza de una cadena AP Rack: el mismo motor logica.h que AP Control, con las entradas y salidas de TODOS los módulos.
//   I1..  entradas digitales de todos los módulos en orden de cadena (módulo 1 primero)
//   Q1..  salidas digitales (igual)
//   A1..  entradas analógicas de los módulos AI8 en orden, en V o mA (solo para comparar: LD A3 > 4.5)
//   R1..R16 consignas que el panel escribe (PLC R n valor); no se recuerdan al apagar. M1..M64 las puede escribir el panel con PLC M n 0|1
//   S2 pulso de 1 s · S3 siempre 1 · S5 hay falla · S6 falta algún módulo (hay menos que cuando arrancó el programa o uno no contesta) · S7 hay más de un módulo · S11-S26: el módulo n (1-16) está presente
// El programa es dueño de las salidas Q que nombra con OUT, SET o RST mientras está en RUN: la consola no las puede cambiar.
// Al pasar a STOP esas salidas se apagan. Si el cabeza deja de serlo, el programa no corre.
#pragma once
#include <math.h>
#include "ap_link.h"
#include "logica.h"

namespace aprack {

struct PlcRack : logica::Entorno {
  aplink::Enlace* e = nullptr;
  logica::Programa prog;
  bool run = false;
  char texto[2048] = "";
  uint16_t dueno[aplink::MAX_MODULOS] = {};     // bits de cada módulo que maneja el programa
  uint16_t q[aplink::MAX_MODULOS] = {};         // copia de trabajo de las salidas pedidas
  uint32_t tUlt = 0, ahora = 0;
  float r[16] = {};                              // R1-R16: valores que escribe el panel (consignas); el programa solo los compara
  uint8_t maxVisto = 0;                         // módulos que había al arrancar el programa; si luego hay menos, S6 = 1

  explicit PlcRack(aplink::Enlace* en = nullptr) : e(en) {}

  // Compila un texto nuevo. Si no compila, el programa anterior queda como estaba.
  bool cargar(const char* txt) {
    if (strlen(txt) >= sizeof(texto)) { snprintf(prog.error, sizeof(prog.error), "programa demasiado largo"); return false; }
    logica::Programa* nuevo = new logica::Programa();
    bool ok = nuevo->compilar(txt);
    if (ok) {
      bool estabaRun = run;
      modo(false);
      prog = *nuevo;
      strcpy(texto, txt);
      if (estabaRun) modo(true);
    } else strncpy(prog.error, nuevo->error, sizeof(prog.error));
    delete nuevo;
    return ok;
  }
  void borrar() { modo(false); prog.n = 0; texto[0] = 0; prog.error[0] = 0; }

  void modo(bool r) {
    if (r == run) return;
    if (r && !prog.n) return;
    if (!r) {
      calcularDueno();
      for (uint8_t p = 1; p <= aplink::MAX_MODULOS; p++)                       // al parar, lo que era del programa se apaga
        if (const aplink::InfoMod* m = e->modulo(p)) if (dueno[p - 1]) e->mandar(p, m->deseadas & ~dueno[p - 1]);
      memset(dueno, 0, sizeof dueno);
    } else { prog.primerCiclo = true; maxVisto = e->total(); }
    run = r;
  }

  bool ponerM(int n, bool v) { if (n < 1 || n >= logica::M_RETENTIVA) return false; prog.m[n] = v; return true; }
  bool ponerR(int n, float v) { if (n < 1 || n > 16 || v != v) return false; r[n - 1] = v; return true; }

  bool poseeCanal(uint16_t g) const {
    if (!run) return false;
    uint8_t p, l;
    return e->canalGlobal(g, &p, &l) && (dueno[p - 1] >> (l - 1) & 1);
  }
  // salidas de un módulo que maneja el programa (0 si no corre)
  uint16_t duenoDe(uint8_t pos) const { return (run && pos >= 1 && pos <= aplink::MAX_MODULOS) ? dueno[pos - 1] : 0; }

  void paso(uint32_t t) {
    ahora = t;
    if (e->total() > maxVisto) maxVisto = e->total();
    if (!run || e->rol() != aplink::Rol::CABEZA) return;
    if (t - tUlt < 10) return;
    uint32_t dt = t - tUlt; if (dt > 100) dt = 100;
    tUlt = t;
    calcularDueno();
    for (uint8_t p = 1; p <= aplink::MAX_MODULOS; p++) { const aplink::InfoMod* m = e->modulo(p); q[p - 1] = m ? m->deseadas : 0; }
    prog.ciclo(*this, dt);
    for (uint8_t p = 1; p <= aplink::MAX_MODULOS; p++) {
      const aplink::InfoMod* m = e->modulo(p);
      if (!m) continue;
      uint16_t nuevo = (uint16_t)((m->deseadas & ~dueno[p - 1]) | (q[p - 1] & dueno[p - 1]));
      if (nuevo != m->deseadas) e->mandar(p, nuevo);
    }
  }

  // ---- el entorno del programa ----
  bool leerBit(char a, int i) override {
    uint8_t p, l;
    if (a == 'I') { if (!e->entradaGlobal(i, &p, &l)) return false; const aplink::InfoMod* m = e->modulo(p); return m && !m->perdido && (m->ent >> (l - 1) & 1); }
    if (a == 'Q') { if (!e->canalGlobal(i, &p, &l)) return false; return q[p - 1] >> (l - 1) & 1; }
    if (a == 'S') {
      if (i == 2) return (ahora / 500) & 1;
      if (i == 3) return true;
      if (i == 5) return hayFalla();
      if (i == 6) return algunoPerdido();
      if (i == 7) return e->total() > 1;
      if (i >= 11 && i <= 26) { const aplink::InfoMod* m = e->modulo(i - 10); return m && !m->perdido; }
    }
    return false;
  }
  float valor(char a, int i) override {
    uint8_t p, l;
    if (a == 'R') return (i >= 1 && i <= 16) ? r[i - 1] : NAN;
    if (a != 'A' || !e->analogicaGlobal(i, &p, &l)) return NAN;
    const aplink::InfoMod* m = e->modulo(p);
    if (!m || m->perdido) return NAN;
    return m->ana[l - 1] / 1000.0f;                                              // mV -> V, µA -> mA
  }
  void escribir(char a, int i, bool v) override {
    uint8_t p, l;
    if (a != 'Q' || !e->canalGlobal(i, &p, &l)) return;
    if (v) q[p - 1] |= (uint16_t)(1u << (l - 1)); else q[p - 1] &= (uint16_t)~(1u << (l - 1));
  }

 bool hayFallaModulos() const { return hayFalla(); }

 private:
  bool algunoPerdido() const { if (e->total() < maxVisto) return true; for (uint8_t p = 1; p <= aplink::MAX_MODULOS; p++) if (const aplink::InfoMod* m = e->modulo(p)) if (m->perdido) return true; return false; }
  bool hayFalla() const { for (uint8_t p = 1; p <= aplink::MAX_MODULOS; p++) if (const aplink::InfoMod* m = e->modulo(p)) if (m->perdido || m->fallas) return true; return false; }
  void calcularDueno() {
    memset(dueno, 0, sizeof dueno);
    for (int k = 0; k < prog.n; k++) {
      const logica::Ins& in = prog.ins[k];
      if ((in.op == logica::OUT || in.op == logica::SET || in.op == logica::RST) && in.area == 'Q') {
        uint8_t p, l;
        if (e->canalGlobal(in.idx, &p, &l)) dueno[p - 1] |= (uint16_t)(1u << (l - 1));
      }
    }
  }
};

}  // namespace aprack
