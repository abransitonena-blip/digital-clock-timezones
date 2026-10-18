// Pruebas en la PC del Modbus TCP del cabeza (AP PLC C24): lectura y escritura de bobinas, entradas y registros de TODA la cadena,
// el programa del PLC como dueño de sus salidas, excepciones y tramas mal formadas. g++ -std=c++17 prueba_modbus_tcp.cpp -o /tmp/pmt && /tmp/pmt
#include <cstdio>
#include "sim_link.h"
#include "../APRack/ap_rack.h"
#include "../APRack/modbus_tcp.h"

static int fallas = 0, pruebas = 0;
#define CHECK(c, ...) do { pruebas++; if (!(c)) { fallas++; printf("FALLA (línea %d): ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

struct Cadena {
  Sim s; aprack::PlcRack plc; uint16_t segura = 0; uint32_t t = 0; bool cambio = false; uint16_t tid = 1;
  Cadena(int n, std::vector<Caps> tipos) : s(n) {
    for (int i = 0; i < n; i++) s.energia(i, true, i == 0, tipos[i]);
    while (t < 20000 && !(s.cabeza() && s.cabeza()->total() == n)) { s.paso(); t++; }
    s.correr(400);
    plc.e = s.cabeza();
  }
  void correr(uint32_t ms) { for (uint32_t i = 0; i < ms; i++) { s.paso(); plc.paso(s.ahora); } }
  // arma la trama TCP (MBAP + PDU) y devuelve la respuesta
  size_t tcp(std::initializer_list<uint8_t> pdu, uint8_t* r) {
    uint8_t q[300]; size_t m = 0;
    q[m++] = tid >> 8; q[m++] = (uint8_t)tid; q[m++] = 0; q[m++] = 0; q[m++] = (uint8_t)((pdu.size() + 1) >> 8); q[m++] = (uint8_t)(pdu.size() + 1); q[m++] = 1;
    for (uint8_t b : pdu) q[m++] = b;
    tid++;
    return aprack::modbusTcp(*s.cabeza(), plc, &segura, s.ahora / 1000, q, m, r, &cambio);
  }
};

int main() {
  Caps plc12{1, 12, 12, VERSION, 0}, rack{1, 16, 8, VERSION, 0}, ai8{3, 0, 0, VERSION, 8};
  uint8_t r[300];
  {
    // el PLC (12 E / 12 S) como cabeza + un Rack 16 + un AI8: bobinas 0-27, entradas 0-19, analógicas 0-7
    Cadena c(3, {plc12, rack, ai8});
    size_t n = c.tcp({0x04, 0x00, 0x00, 0x00, 0x09}, r);
    CHECK(n == 7 + 2 + 18 && r[7] == 4 && r[8] == 18, "FC4 9 registros: largo %zu", n);
    CHECK((r[9] << 8 | r[10]) == 1 && (r[11] << 8 | r[12]) == 3 && (r[13] << 8 | r[14]) == 28 && (r[15] << 8 | r[16]) == 20 && (r[25] << 8 | r[26]) == 8,
          "versión 1, 3 módulos, 28 salidas, 20 entradas, 8 analógicas");
    CHECK(r[0] == 0 && r[1] == 1 && r[2] == 0 && r[3] == 0 && (size_t)(r[4] << 8 | r[5]) == n - 6 && r[6] == 1, "el MBAP de la respuesta repite el identificador y el largo");
    // escribir la bobina 0 (salida 1 del PLC) y la 12 (salida 1 del Rack 16, módulo 2)
    n = c.tcp({0x05, 0x00, 0x00, 0xFF, 0x00}, r);
    CHECK(n == 12 && r[7] == 5 && r[10] == 0xFF, "FC5 eco");
    n = c.tcp({0x05, 0x00, 0x0C, 0xFF, 0x00}, r);
    CHECK(n == 12, "FC5 sobre el módulo 2");
    c.correr(300);
    CHECK(c.s.n[0]->e->salidas() == 0x0001 && c.s.n[1]->e->salidas() == 0x0001, "las salidas llegan a cada módulo (0x%04X 0x%04X)", c.s.n[0]->e->salidas(), c.s.n[1]->e->salidas());
    n = c.tcp({0x01, 0x00, 0x00, 0x00, 0x1C}, r);
    CHECK(n == 7 + 2 + 4 && r[8] == 4 && r[9] == 0x01 && r[10] == 0x10 && (r[11] & 0xFF) == 0x00, "FC1 lee las 28 bobinas: %02X %02X %02X %02X", r[9], r[10], r[11], r[12]);
    // FC15: 3 bobinas a partir de la 1
    n = c.tcp({0x0F, 0x00, 0x01, 0x00, 0x03, 0x01, 0x05}, r);
    CHECK(n == 12 && r[7] == 15, "FC15 eco");
    c.correr(300);
    CHECK((c.s.n[0]->e->salidas() & 0x0F) == 0x0B, "FC15: bobinas 1 y 3 (0x%04X)", c.s.n[0]->e->salidas());
    // entradas: I1 del PLC y I13 (la 5ª del Rack 16 que empieza en la 13)
    c.s.n[0]->ent = 0x0001; c.s.n[1]->ent = 0x0010; c.correr(300);
    n = c.tcp({0x02, 0x00, 0x00, 0x00, 0x14}, r);
    CHECK(n == 7 + 2 + 3 && r[9] == 0x01 && r[10] == 0x00 && r[11] == 0x01, "FC2 20 entradas: %02X %02X %02X", r[9], r[10], r[11]);
    // analógica 1 del AI8
    c.s.n[2]->ana[0] = 6200; c.correr(300);
    n = c.tcp({0x04, 0x00, 0x09, 0x00, 0x03}, r);
    CHECK(n == 7 + 2 + 6 && (r[9] << 8 | r[10]) == 0 && (r[13] << 8 | r[14]) == 0, "sin NTP: hora 0 y no ajustada");
    { uint8_t q[] = {0, 7, 0, 0, 0, 6, 1, 4, 0, 9, 0, 3}; bool cb = false; uint16_t sg = 0; size_t m = aprack::modbusTcp(*c.s.cabeza(), c.plc, &sg, 0, q, sizeof q, r, &cb, 1760000000u);
      CHECK(m == 15 && ((uint32_t)(r[11] << 8 | r[12]) << 16 | (r[9] << 8 | r[10])) == 1760000000u && (r[13] << 8 | r[14]) == 1, "con NTP: la hora llega partida en dos registros"); }
    n = c.tcp({0x04, 0x00, 0x64, 0x00, 0x01}, r);
    CHECK(n == 11 && (r[9] << 8 | r[10]) == 6200, "FC4 analógica 1 = 6200 mV (%d)", r[9] << 8 | r[10]);
  }
  {
    Cadena c(1, {Caps{1, 12, 12, VERSION, 0}});
    // el programa del PLC es dueño de Q1: Modbus no la puede cambiar (excepción 04) y sí la Q2
    CHECK(c.plc.cargar("LD I1\nOUT Q1\nLD R1 > 5\nOUT Q3"), "programa (%s)", c.plc.prog.error);
    size_t n = c.tcp({0x06, 0x00, 0x00, 0x00, 0x01}, r);
    CHECK(n == 12 && r[10] == 0 && r[11] == 1 && c.plc.run && c.cambio, "FC6 reg 0 = 1 pone el PLC en RUN y avisa el cambio");
    c.cambio = false; c.correr(200);
    n = c.tcp({0x05, 0x00, 0x00, 0xFF, 0x00}, r);
    CHECK(n == 9 && r[7] == 0x85 && r[8] == 4, "Q1 es del programa: excepción 04 (%02X %02X)", r[7], r[8]);
    n = c.tcp({0x05, 0x00, 0x01, 0xFF, 0x00}, r);
    CHECK(n == 12, "Q2 no es del programa: se acepta");
    n = c.tcp({0x06, 0x00, 0x01, 0x00, 0x07}, r);                                    // R1 = 7
    c.correr(200);
    CHECK(n == 12 && (c.s.n[0]->e->salidas() & 0x0006) == 0x0006, "R1 = 7 > 5 enciende Q3 (0x%04X)", c.s.n[0]->e->salidas());
    n = c.tcp({0x03, 0x00, 0x00, 0x00, 0x02}, r);
    CHECK(n == 7 + 2 + 4 && (r[9] << 8 | r[10]) == 1 && (r[11] << 8 | r[12]) == 7, "FC3 lee el modo (RUN) y R1 = 7");
    n = c.tcp({0x06, 0x00, 0x01, 0xFF, 0xFE}, r);                                    // R1 = -2
    n = c.tcp({0x03, 0x00, 0x01, 0x00, 0x01}, r);
    CHECK((int16_t)(r[9] << 8 | r[10]) == -2, "R1 admite negativos");
    n = c.tcp({0x06, 0x00, 0x00, 0x00, 0x00}, r);
    CHECK(n == 12 && !c.plc.run && c.cambio, "reg 0 = 0 pone STOP");
    c.cambio = false;
    // excepciones
    n = c.tcp({0x01, 0x00, 0x00, 0x00, 0x0D}, r);
    CHECK(n == 9 && r[7] == 0x81 && r[8] == 2, "más bobinas que las que hay: excepción 02");
    n = c.tcp({0x03, 0x00, 0x00, 0x00, 0x00}, r);
    CHECK(n == 9 && r[7] == 0x83 && r[8] == 3, "cantidad 0: excepción 03");
    n = c.tcp({0x03, 0x00, 0x00, 0x00, 0x20}, r);
    CHECK(n == 9 && r[7] == 0x83 && r[8] == 2, "registro que no existe: excepción 02");
    n = c.tcp({0x2B, 0x0E, 0x01, 0x00}, r);
    CHECK(n == 9 && r[7] == 0xAB && r[8] == 1, "función no soportada: excepción 01");
    n = c.tcp({0x06, 0x00, 0x00, 0x00, 0x05}, r);
    CHECK(n == 9 && r[8] == 3, "modo con valor 5: excepción 03");
    c.plc.borrar();
    n = c.tcp({0x06, 0x00, 0x00, 0x00, 0x01}, r);
    CHECK(n == 9 && r[8] == 4 && !c.plc.run, "RUN sin programa: excepción 04");
    // tramas mal formadas: no se contesta (conviene cerrar la conexión)
    uint8_t mala[] = {0, 1, 0, 1, 0, 2, 1, 3};                                      // protocolo 1
    CHECK(aprack::modbusTcp(*c.s.cabeza(), c.plc, &c.segura, 0, mala, sizeof mala, r, &c.cambio) == 0, "protocolo distinto de 0");
    uint8_t larga[] = {0, 1, 0, 0, 0, 9, 1, 3, 0, 0, 0, 1};                         // el largo declarado no coincide
    CHECK(aprack::modbusTcp(*c.s.cabeza(), c.plc, &c.segura, 0, larga, sizeof larga, r, &c.cambio) == 0, "largo que no coincide");
    CHECK(aprack::modbusTcp(*c.s.cabeza(), c.plc, &c.segura, 0, larga, 5, r, &c.cambio) == 0, "trama corta");
  }
  {
    // un módulo esclavo no manda: las escrituras dan excepción 04
    Cadena c(2, {Caps{1, 12, 12, VERSION, 0}, Caps{1, 16, 8, VERSION, 0}});
    Enlace* esc = c.s.n[1]->e.get();
    uint8_t q[] = {0, 9, 0, 0, 0, 6, 1, 5, 0, 0, 0xFF, 0};
    bool cb = false; uint16_t seg = 0; aprack::PlcRack p2(esc);
    size_t n = aprack::modbusTcp(*esc, p2, &seg, 0, q, sizeof q, r, &cb);
    CHECK(n == 9 && r[7] == 0x85 && r[8] == 4, "esclavo: excepción 04");
  }
  if (fallas) { printf("Modbus TCP: %d de %d comprobaciones fallaron\n", fallas, pruebas); return 1; }
  printf("Modbus TCP: todo bien (%d comprobaciones)\n", pruebas);
  return 0;
}
