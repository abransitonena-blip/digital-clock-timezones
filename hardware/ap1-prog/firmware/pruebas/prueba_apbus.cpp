// Prueba en la PC del protocolo AP BUS (apbus.h):  bash tools/probar_apbus.sh
#include <cstdio>
#include <cstring>
#include "../LetreroLabAP1/apbus.h"

static int fallas = 0;
#define REVISA(c) do { if (!(c)) { printf("FALLA linea %d: %s\n", __LINE__, #c); fallas++; } } while (0)

int main() {
  // identificadores
  REVISA(busIdEstado(1) == 0x101 && busIdOrden(3) == 0x203);
  REVISA(busNodoDe(0x101, BUS_ID_ESTADO) == 1 && busNodoDe(0x103, BUS_ID_ESTADO) == 3);
  REVISA(busNodoDe(0x100, BUS_ID_ESTADO) == 0 && busNodoDe(0x104, BUS_ID_ESTADO) == 0);   // fuera de 1..3
  REVISA(busNodoDe(0x201, BUS_ID_ESTADO) == 0 && busNodoDe(0x201, BUS_ID_ORDEN) == 1);
  // estado: ida y vuelta
  BusEstado e{0x05, 0x03, {0xA5, 0x0F, 0x77, 0x99}, 1}, r{};
  uint8_t d[8];
  uint8_t n = busCodificarEstado(e, d);
  REVISA(n == 7 && d[0] == 0x35 && d[6] == BUS_VERSION);
  REVISA(busDecodificarEstado(d, n, &r));
  REVISA(r.salidas == 0x05 && r.entradas == 0x03 && r.banderas == 1);
  REVISA(r.ent[0] == 0xA5 && r.ent[1] == 0x0F);
  REVISA(r.ent[2] == 0 && r.ent[3] == 0);              // módulos ausentes: entradas en 0 aunque lleguen bits
  REVISA(!busDecodificarEstado(d, 6, &r));             // trama corta
  d[6] = BUS_VERSION + 1;
  REVISA(!busDecodificarEstado(d, 7, &r));             // otra versión del protocolo
  // orden: ida y vuelta
  BusOrden o{{0xFF, 0x01, 0x80, 0x00}}, p{};
  n = busCodificarOrden(o, d);
  REVISA(n == 6 && d[5] == BUS_VERSION && d[4] == 0);
  REVISA(busDecodificarOrden(d, n, &p) && !memcmp(o.sal, p.sal, 4));
  REVISA(!busDecodificarOrden(d, 5, &p));
  // tiempo: 0 = nunca, vuelta de millis()
  REVISA(busVencido(5000, 0, BUS_VENCE));
  REVISA(!busVencido(5000, 4500, BUS_VENCE) && busVencido(5000, 3000, BUS_VENCE));
  REVISA(!busVencido(200, 0xFFFFFF00u, BUS_VENCE));   // millis() dio la vuelta: 456 ms
  // carga del bus: 3 nodos x 2 tramas cada 100 ms, ~120 bits por trama a 250 kbit/s
  double carga = 3 * 2 * 10 * 120.0 / 250000 * 100;
  printf("carga del bus: %.1f %%\n", carga);
  REVISA(carga < 5);
  printf(fallas ? "%d FALLAS\n" : "AP BUS: todo bien\n", fallas);
  return fallas != 0;
}
