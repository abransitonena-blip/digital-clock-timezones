// Pruebas en la PC del reloj PCF8563 (conversión BCD <-> epoch) y del Modbus RTU del AP PLC C24 rev B.
#include <cstdio>
#include "sim_link.h"
#include "../APRack/ap_rack.h"
#include "../APRack/modbus_tcp.h"
#include "../APRack/rtc_pcf8563.h"

static int fallas = 0, pruebas = 0;
#define CHECK(c, ...) do { pruebas++; if (!(c)) { fallas++; printf("FALLA (línea %d): ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

int main() {
  {   // reloj: 1760000000 = 2025-10-09 08:53:20 UTC, jueves
    uint8_t r[7]; CHECK(rtc::aRegistros(1760000000u, r), "convierte");
    CHECK(r[0] == 0x20 && r[1] == 0x53 && r[2] == 0x08 && r[3] == 0x09 && r[4] == 4 && r[5] == 0x10 && r[6] == 0x25, "BCD: %02X %02X %02X %02X %02X %02X %02X", r[0], r[1], r[2], r[3], r[4], r[5], r[6]);
    uint32_t e = 0; CHECK(rtc::deRegistros(r, &e) && e == 1760000000u, "ida y vuelta (%u)", e);
    r[0] |= 0x80; CHECK(!rtc::deRegistros(r, &e), "VL = 1 no es de fiar");
    // 29 de febrero de 2028 y fin de siglo
    uint32_t casos[] = {951782400u /* 2000-02-29 */, 1835395200u /* 2028-02-29 */, 4102444799u /* 2099-12-31 23:59:59 */, 946684800u /* 2000-01-01 */};
    for (uint32_t c : casos) { uint8_t b[7]; uint32_t v = 0; CHECK(rtc::aRegistros(c, b) && rtc::deRegistros(b, &v) && v == c, "caso %u -> %u", c, v); }
    uint8_t b[7]; CHECK(!rtc::aRegistros(4102444800u, b), "2100 no cabe");
    CHECK(!rtc::aRegistros(900000000u, b), "1998 no cabe");
    uint8_t mal[7] = {0x61, 0x00, 0x00, 0x01, 0, 0x01, 0x25}; CHECK(!rtc::deRegistros(mal, &e), "segundos 61");
  }
  {   // Modbus RTU
    Sim s(1); Caps plc{7, 12, 12, VERSION, 0}; s.energia(0, true, true, plc);
    uint32_t t = 0; while (t < 20000 && !(s.cabeza() && s.cabeza()->total() == 1)) { s.paso(); t++; }
    s.correr(400);
    aprack::PlcRack pl; pl.e = s.cabeza(); uint16_t seg = 0; bool cb = false; uint8_t r[300];
    auto rtu = [&](std::initializer_list<uint8_t> pdu, uint8_t dir, uint8_t* out, uint32_t epoch = 0) {
      uint8_t q[300]; size_t m = 0; q[m++] = dir; for (uint8_t b : pdu) q[m++] = b;
      uint16_t c = aprack::crc16Modbus(q, m); q[m++] = (uint8_t)c; q[m++] = (uint8_t)(c >> 8);
      return aprack::modbusRtu(*s.cabeza(), pl, &seg, 7, 1, q, m, out, &cb, epoch);
    };
    size_t n = rtu({0x04, 0x00, 0x00, 0x00, 0x04}, 1, r);
    CHECK(n == 1 + 1 + 1 + 8 + 2 && r[0] == 1 && r[1] == 4 && r[2] == 8 && (r[3] << 8 | r[4]) == 1 && (r[7] << 8 | r[8]) == 12 && aprack::crc16Modbus(r, n) == 0, "FC4 por RTU (n=%zu)", n);
    n = rtu({0x05, 0x00, 0x02, 0xFF, 0x00}, 1, r);
    CHECK(n == 8, "FC5 eco"); for (int i = 0; i < 300; i++) { s.paso(); pl.paso(s.ahora); }
    CHECK(s.n[0]->e->salidas() == 0x0004, "la salida 3 se enciende (0x%04X)", s.n[0]->e->salidas());
    CHECK(rtu({0x04, 0x00, 0x00, 0x00, 0x01}, 2, r) == 0, "otra dirección: no contesta");
    n = rtu({0x05, 0x00, 0x00, 0xFF, 0x00}, 0, r); for (int i = 0; i < 300; i++) { s.paso(); pl.paso(s.ahora); }
    CHECK(n == 0 && (s.n[0]->e->salidas() & 1), "difusión: ejecuta y no contesta");
    uint8_t mal[] = {1, 4, 0, 0, 0, 1, 0x00, 0x00};
    CHECK(aprack::modbusRtu(*s.cabeza(), pl, &seg, 0, 1, mal, sizeof mal, r, &cb) == 0, "CRC malo: sin respuesta");
    n = rtu({0x04, 0x00, 0x09, 0x00, 0x03}, 1, r, 1760000000u);
    CHECK(n == 11 && ((uint32_t)(r[5] << 8 | r[6]) << 16 | (r[3] << 8 | r[4])) == 1760000000u && (r[7] << 8 | r[8]) == 1, "hora por RTU");
    n = rtu({0x04, 0x00, 0x0C, 0x00, 0x01}, 1, r);
    CHECK(n == 7 && r[1] == 4, "el registro 12 (tensión) existe");
  }
  if (fallas) { printf("RTC y Modbus RTU: %d de %d comprobaciones fallaron\n", fallas, pruebas); return 1; }
  printf("RTC y Modbus RTU: todo bien (%d comprobaciones)\n", pruebas);
  return 0;
}
