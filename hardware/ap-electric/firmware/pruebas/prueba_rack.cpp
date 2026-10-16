// Pruebas en la PC de AP Rack 16 (ap_rack.h) sobre el simulador de la cadena AP LINK (sim_link.h):
// órdenes con canales globales, módulos que aparecen en el JSON, esclavos que rechazan órdenes y estado seguro.
// Deja JSON de ejemplo en /tmp/json_rack_*.txt para probar_rack.py y la prueba de contrato de la consola.
#include <cstdio>
#include <cstdlib>
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
  if (fallas) { printf("AP Rack: %d de %d comprobaciones fallaron\n", fallas, pruebas); return 1; }
  printf("AP Rack: todo bien (%d comprobaciones)\n", pruebas);
  return 0;
}
