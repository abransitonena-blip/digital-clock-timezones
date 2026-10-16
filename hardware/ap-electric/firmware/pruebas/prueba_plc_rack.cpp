// Pruebas en la PC del PLC (AP LÓGICA) sobre una cadena AP Rack: entradas y salidas de varios módulos, analógicas, dueño de las salidas,
// falla de módulo, STOP y estado del PLC en el JSON. Deja /tmp/json_rack_plc.txt para la prueba de contrato del navegador.
#include <cstdio>
#include "sim_link.h"
#include "../APRack/ap_rack.h"

static int fallas = 0, pruebas = 0;
#define CHECK(c, ...) do { pruebas++; if (!(c)) { fallas++; printf("FALLA (línea %d): ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

struct Cadena {
  Sim s; aprack::PlcRack plc; uint16_t segura = 0; uint32_t t = 0;
  Cadena(int n, std::vector<Caps> tipos) : s(n) {
    for (int i = 0; i < n; i++) s.energia(i, true, i == 0, tipos[i]);
    while (t < 20000 && !(s.cabeza() && s.cabeza()->total() == n)) { s.paso(); t++; }
    s.correr(400);
    plc.e = s.cabeza();
  }
  void correr(uint32_t ms) { for (uint32_t i = 0; i < ms; i++) { s.paso(); plc.paso(s.ahora); } }
  bool ord(const char* c) { return aprack::orden(*s.cabeza(), c, &segura, &plc); }
};

int main() {
  Caps rack{1, 16, 8, VERSION, 0}, in16{2, 0, 16, VERSION, 0}, ai8{3, 0, 0, VERSION, 8};
  {
    // Rack 16 + IN16 + AI8: I1-I8 son del rack, I9-I24 del módulo de entradas; A1-A8 del módulo analógico
    Cadena c(3, {rack, in16, ai8});
    CHECK(c.s.cabeza()->totalEntradas() == 24 && c.s.cabeza()->totalSalidas() == 16 && c.s.cabeza()->totalAnalogicas() == 8, "totales");
    CHECK(c.ord("PLC TXT LD I9|OUT Q1|LD I24|OUT Q16|LD A1 > 5.0|OUT Q3|LDN I9|ANDN I24|OUT Q4"), "el programa compila (%s)", c.plc.prog.error);
    CHECK(c.ord("PLC RUN") && c.plc.run, "RUN");
    c.correr(300);
    CHECK(c.s.n[0]->e->salidas() == 0x0008, "sin entradas solo Q4 (0x%04X)", c.s.n[0]->e->salidas());
    c.s.n[1]->ent = 0x0001; c.correr(300);                       // I9 = bit 0 del módulo 2
    CHECK(c.s.n[0]->e->salidas() == 0x0001, "I9 enciende Q1 y apaga Q4 (0x%04X)", c.s.n[0]->e->salidas());
    c.s.n[1]->ent = 0x8001; c.correr(300);                       // I24 = bit 15 del módulo 2
    CHECK(c.s.n[0]->e->salidas() == 0x8001, "I24 enciende Q16 (0x%04X)", c.s.n[0]->e->salidas());
    c.s.n[2]->ana[0] = 6200; c.correr(300);                      // 6.2 V
    CHECK(c.s.n[0]->e->salidas() == 0x8005, "A1 = 6.2 V enciende Q3 (0x%04X)", c.s.n[0]->e->salidas());
    c.s.n[2]->ana[0] = 4800; c.correr(300);
    CHECK(c.s.n[0]->e->salidas() == 0x8001, "A1 = 4.8 V la apaga");
    // la consola no puede cambiar lo que maneja el programa, sí lo demás
    CHECK(!c.ord("C 1 0") && !c.ord("C 3 1") && c.ord("C 2 1"), "C sobre canal del PLC se rechaza; sobre otro se acepta");
    c.correr(300);
    CHECK((c.s.n[0]->e->salidas() & 0x0002) && (c.s.n[0]->e->salidas() & 0x8001) == 0x8001, "Q2 manual convive con el programa (0x%04X)", c.s.n[0]->e->salidas());
    CHECK(c.ord("A 0"), "A 0");
    c.correr(300);
    CHECK((c.s.n[0]->e->salidas() & 0x0002) == 0 && (c.s.n[0]->e->salidas() & 0x8001) == 0x8001, "A 0 apaga lo manual y respeta lo del programa (0x%04X)", c.s.n[0]->e->salidas());
    // módulo de entradas sin energía: sus entradas valen 0 y S6 avisa
    char b[4096]; aprack::json(b, sizeof b, *c.s.cabeza(), "1.0", "AB12CD", 5, &c.plc);
    FILE* f = fopen("/tmp/json_rack_plc.txt", "w"); fputs(b, f); fputc('\n', f); fclose(f);
    c.ord("PLC STOP"); c.correr(200);
    CHECK(!c.plc.run && c.s.n[0]->e->salidas() == 0, "STOP apaga lo que era del programa (0x%04X)", c.s.n[0]->e->salidas());
    CHECK(!c.ord("PLC TXT LD I1|OUT"), "programa con error se rechaza");
    CHECK(strlen(c.plc.prog.error) > 0, "queda el mensaje de error");
    CHECK(c.plc.prog.n > 0, "el programa anterior sigue ahí");
    c.ord("PLC BORRAR"); CHECK(c.plc.prog.n == 0 && !c.ord("PLC RUN"), "BORRAR");
  }
  {
    // el panel escribe marcas y consignas: M n y R n
    Cadena c(1, {rack});
    CHECK(c.ord("PLC TXT LD M5|OUT Q1|LD R2 > 12.5|OUT Q2|LD I1|OUT M6|LD M6|OUT Q3"), "programa con M y R (%s)", c.plc.prog.error);
    c.ord("PLC RUN"); c.correr(200);
    CHECK(c.s.n[0]->e->salidas() == 0, "todo apagado al principio");
    CHECK(c.ord("PLC M 5 1") && c.ord("PLC R 2 20.5"), "el panel escribe M5 y R2");
    c.correr(200);
    CHECK(c.s.n[0]->e->salidas() == 0x0003, "M5 enciende Q1 y R2 = 20.5 > 12.5 enciende Q2 (0x%04X)", c.s.n[0]->e->salidas());
    CHECK(c.ord("PLC R 2 10") && !c.ord("PLC R 17 1") && !c.ord("PLC M 70 1") && !c.ord("PLC M 5 2") && !c.ord("PLC R 1 abc"), "valores fuera de rango o mal escritos se rechazan");
    c.correr(200);
    CHECK(c.s.n[0]->e->salidas() == 0x0001, "R2 = 10 apaga Q2 (0x%04X)", c.s.n[0]->e->salidas());
    char b[4096]; aprack::json(b, sizeof b, *c.s.cabeza(), "1.0", "AB12CD", 5, &c.plc);
    CHECK(strstr(b, "\"r\":[0,10,") != nullptr && strstr(b, "\"m\":[5") != nullptr, "el JSON trae R y M: %s", strstr(b, "\"plc\"") ? strstr(b, "\"plc\"") : "sin plc");
  }
  {
    // falla de un módulo: S6 y comparaciones con NaN
    Cadena c(3, {rack, in16, ai8});
    CHECK(c.ord("PLC TXT LD S6|OUT Q5|LD A1 < 100|OUT Q6|LD S13|OUT Q7"), "programa de fallas");
    c.ord("PLC RUN"); c.correr(300);
    CHECK((c.s.n[0]->e->salidas() & 0x70) == 0x60, "módulos completos: S6 = 0, A1 < 100 verdadero, S13 (módulo 3 presente) = 1 (0x%04X)", c.s.n[0]->e->salidas());
    c.s.energia(2, false);                                       // se cae el módulo analógico
    c.correr(3000);
    CHECK((c.s.n[0]->e->salidas() & 0x70) == 0x10, "módulo 3 perdido: S6 = 1, A1 sin lectura es falso, S13 = 0 (0x%04X)", c.s.n[0]->e->salidas());
  }
  {
    // el programa no corre si este módulo deja de ser el cabeza
    Cadena c(2, {rack, rack});
    c.ord("PLC TXT LD S3|OUT Q17"); c.ord("PLC RUN"); c.correr(300);
    CHECK(c.s.n[1]->e->salidas() == 0x0001, "Q17 = salida 1 del módulo 2");
    c.s.energia(0, false); c.correr(1500);
    CHECK(c.s.n[1]->e->enSeguro() && c.s.n[1]->e->salidas() == 0, "sin cabeza el módulo 2 va a seguro aunque el PLC haya mandado encender");
  }
  if (fallas) { printf("PLC de AP Rack: %d de %d comprobaciones fallaron\n", fallas, pruebas); return 1; }
  printf("PLC de AP Rack: todo bien (%d comprobaciones)\n", pruebas);
  return 0;
}
