// Pruebas en la PC de AP Rack 16 (ap_rack.h) sobre el simulador de la cadena AP LINK (sim_link.h):
// órdenes con canales globales, módulos que aparecen en el JSON, esclavos que rechazan órdenes y estado seguro.
// Deja JSON de ejemplo en /tmp/json_rack_*.txt para probar_rack.py y la prueba de contrato de la consola.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include "sim_link.h"
#include "../APRack/ap_rack.h"

static int fallas = 0, pruebas = 0;
#define CHECK(c, ...) do { pruebas++; if (!(c)) { fallas++; printf("FALLA (línea %d): ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

static void guardar(const char* ruta, const Enlace& e, uint32_t t) {
  static char b[4096];
  aprack::json(b, sizeof b, e, "1.0", "AB12CD", t);
  FILE* f = fopen(ruta, "w"); fputs(b, f); fputc('\n', f); fclose(f);
}

int main() {
  Sim s(3);
  s.energia(0, true); s.energia(1, true);
  uint32_t t = 0; while (t < 8000 && !(s.cabeza() && s.cabeza()->total() == 2)) { s.paso(); t++; }
  s.correr(300);
  Enlace* h = s.cabeza();
  CHECK(h && h->total() == 2, "dos módulos");
  uint16_t segura = 0;
  CHECK(aprack::orden(*h, "C 1 1", &segura), "C 1 1");
  CHECK(aprack::orden(*h, "C 17 1", &segura), "C 17 1 (módulo 2, salida 1)");
  CHECK(aprack::orden(*h, "C 32 1", &segura), "C 32 1 (módulo 2, salida 16)");
  CHECK(!aprack::orden(*h, "C 33 1", &segura), "el canal 33 no existe con 2 módulos");
  CHECK(!aprack::orden(*h, "C 0 1", &segura) && !aprack::orden(*h, "C 5 7", &segura) && !aprack::orden(*h, "C x", &segura) && !aprack::orden(*h, "Z", &segura), "órdenes inválidas");
  s.correr(300);
  CHECK(s.n[0]->e->salidas() == 0x0001 && s.n[1]->e->salidas() == 0x8001, "salidas 0x%04X y 0x%04X", s.n[0]->e->salidas(), s.n[1]->e->salidas());
  CHECK(aprack::orden(*h, "C 17 2", &segura), "alternar");
  s.correr(200);
  CHECK(s.n[1]->e->salidas() == 0x8000, "alternar apagó la salida 17 (0x%04X)", s.n[1]->e->salidas());
  CHECK(aprack::orden(*h, "M 2 0x00F0", &segura) && aprack::orden(*h, "A 0", &segura), "M y A");
  s.correr(200);
  CHECK(s.n[0]->e->salidas() == 0 && s.n[1]->e->salidas() == 0, "A 0 apaga todo");
  CHECK(aprack::orden(*h, "A 1", &segura), "A 1");
  s.correr(200);
  CHECK(s.n[0]->e->salidas() == 0xFFFF && s.n[1]->e->salidas() == 0xFFFF, "A 1 enciende los 32 canales");
  aprack::orden(*h, "M 2 0x00F0", &segura); aprack::orden(*h, "M 1 5", &segura);
  s.n[1]->ent = 0x0042; s.correr(300);
  guardar("/tmp/json_rack_2mod.txt", *h, 77);
  guardar("/tmp/json_rack_esclavo.txt", *s.n[1]->e, 77);
  // el esclavo no manda; sí acepta su máscara segura
  Enlace* es = s.n[1]->e.get();
  CHECK(!aprack::orden(*es, "C 1 1", &segura) && !aprack::orden(*es, "A 1", &segura), "el esclavo rechaza C y A");
  CHECK(aprack::orden(*es, "S 0x0003", &segura) && segura == 3, "máscara segura local");
  // el cabeza se queda sin energía: el esclavo va a su máscara segura
  s.energia(0, false); s.correr(1300);
  CHECK(es->enSeguro() && es->salidas() == 0x0003, "esclavo en seguro con su máscara (0x%04X)", es->salidas());
  // se conecta un tercer módulo: el JSON del cabeza lo lista
  s.energia(0, true);
  t = 0; while (t < 20000 && !(s.cabeza() && s.cabeza()->total() == 2)) { s.paso(); t++; }
  s.energia(2, true);
  t = 0; while (t < 12000 && s.cabeza()->total() != 3) { s.paso(); t++; }
  s.correr(400);
  CHECK(s.cabeza()->total() == 3 && s.cabeza()->totalSalidas() == 48, "tres módulos y 48 salidas");
  CHECK(aprack::orden(*s.cabeza(), "C 48 1", &segura), "C 48 1");
  s.correr(200);
  CHECK(s.n[2]->e->salidas() == 0x8000, "salida 16 del módulo 3");
  guardar("/tmp/json_rack_3mod.txt", *s.cabeza(), 99);
  // texto completo con 16 módulos cabe en el búfer
  Sim g(16);
  for (int i = 0; i < 16; i++) g.energia(i, true);
  g.correr(60000);
  static char b[4096];
  size_t k = aprack::json(b, sizeof b, *g.cabeza(), "1.0", "AB12CD", 1);
  CHECK(g.cabeza()->total() == 16 && k > 1000 && k < sizeof b - 1, "JSON de 16 módulos: %zu bytes", k);
  // conversión del ADS1115: 5 V y 10 V en modo tensión; 4, 12 y 20 mA en modo corriente; negativo y fuera de escala
  CHECK(aprack::analogica(12500, false) == 5000 && aprack::analogica(25000, false) == 10000, "5 V y 10 V");
  {
    auto cuenta_mA = [](double mA) { double nodo_mV = mA * 149.3; return (int16_t)(nodo_mV / 3.2 / 0.125 + 0.5); };
    CHECK(std::abs((int)aprack::analogica(cuenta_mA(4.0), true) - 4000) < 25, "4 mA -> %u µA", aprack::analogica(cuenta_mA(4.0), true));
    CHECK(std::abs((int)aprack::analogica(cuenta_mA(12.0), true) - 12000) < 25, "12 mA");
    CHECK(std::abs((int)aprack::analogica(cuenta_mA(20.0), true) - 20000) < 25, "20 mA -> %u µA", aprack::analogica(cuenta_mA(20.0), true));
  }
  CHECK(aprack::analogica(-5, false) == 0 && aprack::analogica(32767, true) == 65535, "negativo = 0 y saturación");
  // módulos de tres tipos en la misma cadena: el JSON del cabeza lleva los analógicos del AI8
  {
    Sim m(3);
    Caps rack{1, 16, 8, VERSION, 0}, in16{2, 0, 16, VERSION, 0}, ai8{3, 0, 0, VERSION, 8};
    m.energia(0, true, true, rack); m.energia(1, true, true, in16); m.energia(2, true, true, ai8);
    uint32_t t2 = 0; while (t2 < 20000 && !(m.cabeza() && m.cabeza()->total() == 3)) { m.paso(); t2++; }
    m.n[2]->ana[0] = 6200; m.n[2]->ana[7] = 20000; m.n[2]->anaModo = 0x80; m.n[1]->ent = 0x8001; m.correr(500);
    static char jb[4096]; aprack::json(jb, sizeof jb, *m.cabeza(), "1.0", "AB12CD", 1);
    FILE* f = fopen("/tmp/json_rack_3tipos.txt", "w"); fputs(jb, f); fputc('\n', f); fclose(f);
    CHECK(m.cabeza()->totalEntradas() == 24 && m.cabeza()->totalAnalogicas() == 8 && m.cabeza()->totalSalidas() == 16, "totales con 3 tipos");
    CHECK(strstr(jb, "\"tp\":3") && strstr(jb, "\"a\":[6200,") && strstr(jb, ",20000]") && strstr(jb, "\"am\":128"), "el JSON trae las analógicas del AI8: %s", jb);
  }
  // AP Rack LED8 en la cadena: la orden D fija el brillo y el JSON lo lleva
  {
    Sim m(2);
    Caps rack{1, 16, 8, VERSION, 0}, led8{4, 8, 8, VERSION, 0, 8};
    m.energia(0, true, true, rack); m.energia(1, true, true, led8);
    uint32_t t3 = 0; while (t3 < 20000 && !(m.cabeza() && m.cabeza()->total() == 2)) { m.paso(); t3++; }
    m.correr(300);
    Enlace* hh = m.cabeza(); uint16_t sg = 0;
    CHECK(aprack::orden(*hh, "D 17 100", &sg) && aprack::orden(*hh, "D 24 7", &sg), "D en las salidas 17 y 24 (módulo 2, salidas 1 y 8)");
    CHECK(!aprack::orden(*hh, "D 1 100", &sg) && !aprack::orden(*hh, "D 25 100", &sg) && !aprack::orden(*hh, "D 17 256", &sg) && !aprack::orden(*hh, "D 17", &sg) && !aprack::orden(*hh, "D 17 -1", &sg), "D rechaza salidas sin PWM, canales que no existen y brillos fuera de 0-255");
    CHECK(aprack::orden(*hh, "C 17 1", &sg), "y C la enciende");
    m.correr(300);
    CHECK(m.n[1]->e->dutyLocal()[0] == 100 && m.n[1]->e->dutyLocal()[7] == 7 && m.n[1]->e->salidas() == 1, "el LED8 recibe brillo 100 y 7");
    static char jl[4096]; aprack::json(jl, sizeof jl, *hh, "1.0", "AB12CD", 1);
    FILE* f = fopen("/tmp/json_rack_led8.txt", "w"); fputs(jl, f); fputc('\n', f); fclose(f);
    CHECK(strstr(jl, "\"tp\":4") && strstr(jl, "\"np\":8") && strstr(jl, "\"d\":[100,255,255,255,255,255,255,7]"), "el JSON trae el brillo: %s", jl);
    guardar("/tmp/json_led8_esclavo.txt", *m.n[1]->e, 5);
  }
  // AP Rack RL4 (4 relés) detrás de un Rack 16: la numeración sigue (Q17-Q20) y A 1 no enciende salidas que no existen
  {
    Sim m(2);
    Caps rack{1, 16, 8, VERSION, 0}, rl4{5, 4, 8, VERSION, 0, 0};
    m.energia(0, true, true, rack); m.energia(1, true, true, rl4);
    uint32_t t4 = 0; while (t4 < 20000 && !(m.cabeza() && m.cabeza()->total() == 2)) { m.paso(); t4++; }
    m.correr(300);
    Enlace* hh = m.cabeza(); uint16_t sg = 0;
    CHECK(hh->totalSalidas() == 20 && hh->totalEntradas() == 16, "Rack 16 + RL4: 20 salidas y 16 entradas");
    CHECK(aprack::orden(*hh, "C 20 1", &sg) && !aprack::orden(*hh, "C 21 1", &sg), "la salida 20 (relé 4) existe y la 21 no");
    CHECK(aprack::orden(*hh, "A 1", &sg), "A 1");
    m.correr(300);
    CHECK(m.n[1]->e->salidas() == 0x000F && m.n[0]->e->salidas() == 0xFFFF, "A 1 enciende 4 relés y 16 salidas (0x%04X)", m.n[1]->e->salidas());
    static char jr[4096]; aprack::json(jr, sizeof jr, *hh, "1.0", "AB12CD", 1);
    CHECK(strstr(jr, "\"tp\":5") && strstr(jr, "\"ns\":4"), "el JSON trae el módulo RL4: %s", jr);
    guardar("/tmp/json_rl4_esclavo.txt", *m.n[1]->e, 5);
    static char b2[4096]; aprack::json(b2, sizeof b2, *m.n[1]->e, "1.0", "AB12CD", 1);
    CHECK(strstr(b2, "AP Rack RL4"), "el nombre de placa del RL4");
  }
  // AP Rack AO4 (salidas 0-10 V): el nivel se manda con D y la salida con C; el JSON trae el nombre y los niveles
  {
    Sim m(2);
    Caps rack{1, 16, 8, VERSION, 0}, ao4{6, 4, 8, VERSION, 0, 4};
    m.energia(0, true, true, rack); m.energia(1, true, true, ao4);
    uint32_t t5 = 0; while (t5 < 20000 && !(m.cabeza() && m.cabeza()->total() == 2)) { m.paso(); t5++; }
    m.correr(300);
    Enlace* hh = m.cabeza(); uint16_t sg = 0;
    CHECK(aprack::orden(*hh, "D 18 128", &sg) && aprack::orden(*hh, "C 18 1", &sg), "AO4: nivel 128 y salida 2 habilitada (canal 18)");
    CHECK(!aprack::orden(*hh, "D 21 10", &sg), "AO4: solo tiene 4 salidas");
    m.correr(300);
    CHECK(m.n[1]->e->dutyLocal()[1] == 128 && m.n[1]->e->salidas() == 0x0002, "el AO4 recibe nivel 128 y la máscara 0x0002");
    static char ja[4096]; aprack::json(ja, sizeof ja, *hh, "1.0", "AB12CD", 1);
    CHECK(strstr(ja, "\"tp\":6") && strstr(ja, "\"np\":4") && strstr(ja, "\"d\":[255,128,255,255]"), "el JSON del AO4: %s", ja);
    static char jb2[4096]; aprack::json(jb2, sizeof jb2, *m.n[1]->e, "1.0", "AB12CD", 1);
    CHECK(strstr(jb2, "AP Rack AO4"), "nombre de placa del AO4");
  }
  if (fallas) { printf("AP Rack: %d de %d comprobaciones fallaron\n", fallas, pruebas); return 1; }
  printf("AP Rack: todo bien (%d comprobaciones)\n", pruebas);
  return 0;
}
