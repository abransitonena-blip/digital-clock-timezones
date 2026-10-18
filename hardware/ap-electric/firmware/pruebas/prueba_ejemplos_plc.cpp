// Los programas de ejemplo de PLC_C24_EJEMPLOS.md, corridos sobre un AP PLC C24 simulado (12 entradas, 12 salidas) con un Rack 16 detrás.
// g++ -std=c++17 prueba_ejemplos_plc.cpp -o /tmp/pej && /tmp/pej
#include <cstdio>
#include <string>
#include "sim_link.h"
#include "../APRack/ap_rack.h"

static int fallas = 0, pruebas = 0;
#define CHECK(c, ...) do { pruebas++; if (!(c)) { fallas++; printf("FALLA (línea %d): ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

struct Equipo {
  Sim s; aprack::PlcRack plc; uint16_t segura = 0; uint32_t t = 0;
  Equipo(std::vector<Caps> tipos) : s((int)tipos.size()) {
    for (size_t i = 0; i < tipos.size(); i++) s.energia((int)i, true, i == 0, tipos[i]);
    while (t < 20000 && !(s.cabeza() && s.cabeza()->total() == tipos.size())) { s.paso(); t++; }
    s.correr(400); plc.e = s.cabeza();
  }
  void correr(uint32_t ms) { for (uint32_t i = 0; i < ms; i++) { s.paso(); plc.paso(s.ahora); } }
  bool prog(const char* txt) { return aprack::orden(*s.cabeza(), (std::string("PLC TXT ") + txt).c_str(), &segura, &plc) && aprack::orden(*s.cabeza(), "PLC RUN", &segura, &plc); }
  void ent(int bit, bool v) { if (v) s.n[0]->ent |= (uint16_t)(1u << bit); else s.n[0]->ent &= (uint16_t)~(1u << bit); }
  bool q(int n) { return (s.n[0]->e->salidas() >> (n - 1)) & 1; }
};

int main() {
  Caps plc{7, 12, 12, VERSION, 0}, rack{1, 16, 8, VERSION, 0};
  {   // 1. Arranque y paro con sello: I1 arranca, I2 para
    Equipo e({plc});
    CHECK(e.prog("LD I1|OR Q1|ANDN I2|OUT Q1"), "compila: %s", e.plc.prog.error);
    e.correr(200); CHECK(!e.q(1), "apagado al inicio");
    e.ent(0, 1); e.correr(100); e.ent(0, 0); e.correr(100); CHECK(e.q(1), "arranca y se sella al soltar el botón");
    e.ent(1, 1); e.correr(100); e.ent(1, 0); e.correr(100); CHECK(!e.q(1), "el paro lo apaga y se queda apagado");
  }
  {   // 2. Intermitente de 1 s con el pulso del sistema S2
    Equipo e({plc});
    CHECK(e.prog("LD S2|OUT Q2"), "compila");
    int cambios = 0; bool previo = e.q(2);
    for (int i = 0; i < 4000; i++) { e.correr(1); if (e.q(2) != previo) { cambios++; previo = e.q(2); } }
    CHECK(cambios >= 6 && cambios <= 10, "parpadea (%d cambios en 4 s)", cambios);
  }
  {   // 3. Retardo a la conexión: el motor (Q3) arranca 3 s después de pulsar I3 y se apaga al soltarlo
    Equipo e({plc});
    CHECK(e.prog("LD I3|TON T1 3000|LD T1|OUT Q3"), "compila");
    e.ent(2, 1); e.correr(2500); CHECK(!e.q(3), "a los 2.5 s todavía no");
    e.correr(900); CHECK(e.q(3), "a los 3.4 s ya arrancó");
    e.ent(2, 0); e.correr(100); CHECK(!e.q(3), "al soltar se apaga");
  }
  {   // 4. Contador de piezas: I4 cuenta, a la 5.ª enciende Q4, I5 reinicia
    Equipo e({plc});
    CHECK(e.prog("LD I4|CTU C1 5|LD C1|OUT Q4|LD I5|RST C1"), "compila");
    for (int i = 0; i < 4; i++) { e.ent(3, 1); e.correr(60); e.ent(3, 0); e.correr(60); }
    CHECK(!e.q(4), "con 4 piezas no");
    e.ent(3, 1); e.correr(60); e.ent(3, 0); e.correr(60); CHECK(e.q(4), "con 5 piezas sí");
    e.ent(4, 1); e.correr(60); e.ent(4, 0); e.correr(60); CHECK(!e.q(4), "I5 reinicia");
  }
  {   // 5. Aviso de módulo perdido con S6 (el Rack 16 de atrás se queda sin energía)
    Equipo e({plc, rack});
    CHECK(e.prog("LD S6|OUT Q5"), "compila");
    e.correr(300); CHECK(!e.q(5), "con los dos módulos no hay aviso");
    e.s.energia(1, false); e.correr(3000); CHECK(e.q(5), "al perder el módulo 2 se enciende Q5");
  }
  {   // 6. Una entrada del Rack 16 manda una salida del PLC y al revés (numeración seguida: I13 = entrada 1 del Rack, Q13 = salida 1 del Rack)
    Equipo e({plc, rack});
    CHECK(e.prog("LD I13|OUT Q1|LD I1|OUT Q13"), "compila");
    e.s.n[1]->ent = 0x0001; e.correr(300); CHECK(e.q(1), "I13 enciende Q1");
    e.ent(0, 1); e.correr(300); CHECK(((e.s.n[1]->e->salidas()) & 1) == 1, "I1 enciende la salida 1 del Rack 16 (Q13)");
  }
  if (fallas) { printf("Ejemplos del PLC: %d de %d comprobaciones fallaron\n", fallas, pruebas); return 1; }
  printf("Ejemplos del PLC: todo bien (%d comprobaciones)\n", pruebas);
  return 0;
}
