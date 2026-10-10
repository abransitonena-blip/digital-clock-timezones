// AP BUS: protocolo CAN entre el nodo maestro y los nodos remotos AP NODE (250 kbit/s, identificadores de 11 bits).
// Sin dependencias del hardware: se prueba en la PC con tools/probar_apbus.sh.
//
//   0x100 + id  nodo -> maestro, cada 100 ms y al cambiar una entrada (DLC 7)
//               [0] módulos presentes: bits 0-3 = DO8 en 0x20-0x23, bits 4-7 = AP INPUT en 0x24-0x27
//               [1..4] entradas de los AP INPUT 0x24-0x27 (1 = activa)
//               [5] banderas: bit 0 = salidas apagadas por pérdida del bus
//               [6] versión del protocolo
//   0x200 + id  maestro -> nodo, cada 100 ms y al cambiar una salida (DLC 6)
//               [0..3] salidas de los DO8 0x20-0x23 (1 = encendida)
//               [4] reservado (0)
//               [5] versión del protocolo
// id = 1..BUS_NODOS. Si un nodo pasa BUS_VENCE ms sin órdenes, apaga todas sus salidas (falla segura).
#pragma once
#include <stdint.h>

const uint8_t BUS_VERSION = 1, BUS_NODOS = 3;
const uint16_t BUS_ID_ESTADO = 0x100, BUS_ID_ORDEN = 0x200;
const uint32_t BUS_PERIODO = 100, BUS_VENCE = 1000;

struct BusEstado { uint8_t salidas, entradas, ent[4], banderas; };   // salidas/entradas: módulos presentes (4 bits)
struct BusOrden { uint8_t sal[4]; };

inline uint16_t busIdEstado(uint8_t nodo) { return BUS_ID_ESTADO + nodo; }
inline uint16_t busIdOrden(uint8_t nodo) { return BUS_ID_ORDEN + nodo; }
// nodo 1..BUS_NODOS si el identificador es de ese tipo; 0 si no
inline uint8_t busNodoDe(uint32_t ident, uint16_t base) {
  return (ident > base && ident <= (uint32_t)base + BUS_NODOS) ? (uint8_t)(ident - base) : 0;
}

inline uint8_t busCodificarEstado(const BusEstado& e, uint8_t* d) {
  d[0] = (e.salidas & 0x0F) | (uint8_t)((e.entradas & 0x0F) << 4);
  for (uint8_t i = 0; i < 4; i++) d[1 + i] = e.ent[i];
  d[5] = e.banderas;
  d[6] = BUS_VERSION;
  return 7;
}
inline bool busDecodificarEstado(const uint8_t* d, uint8_t dlc, BusEstado* e) {
  if (dlc < 7 || d[6] != BUS_VERSION) return false;
  e->salidas = d[0] & 0x0F;
  e->entradas = d[0] >> 4;
  for (uint8_t i = 0; i < 4; i++) e->ent[i] = (e->entradas & (1 << i)) ? d[1 + i] : 0;
  e->banderas = d[5];
  return true;
}
inline uint8_t busCodificarOrden(const BusOrden& o, uint8_t* d) {
  for (uint8_t i = 0; i < 4; i++) d[i] = o.sal[i];
  d[4] = 0;
  d[5] = BUS_VERSION;
  return 6;
}
inline bool busDecodificarOrden(const uint8_t* d, uint8_t dlc, BusOrden* o) {
  if (dlc < 6 || d[5] != BUS_VERSION) return false;
  for (uint8_t i = 0; i < 4; i++) o->sal[i] = d[i];
  return true;
}
// millis() da la vuelta cada 49 días: la resta sin signo lo resuelve
inline bool busVencido(uint32_t ahora, uint32_t ultimo, uint32_t limite) { return ultimo == 0 || ahora - ultimo > limite; }
