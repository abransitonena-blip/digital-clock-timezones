// Reloj de tiempo real PCF8563 (I2C 0x51) del AP PLC C24 rev B: conversión entre segundos desde 1970 (UTC) y los 7 registros BCD 0x02-0x08.
// Portable: sin Arduino. Registro 0x02 = segundos (bit 7 = VL, «la hora no es de fiar»), 03 minutos, 04 horas, 05 día del mes, 06 día de la semana,
// 07 mes (bit 7 = siglo), 08 año 00-99. Aquí el año 00-99 es 2000-2099 y el bit de siglo queda en 0.
#pragma once
#include <stdint.h>

namespace rtc {

inline int64_t diasDesdeCivil(int y, unsigned m, unsigned d) {              // algoritmo de Howard Hinnant
  y -= m <= 2;
  const int64_t era = (y >= 0 ? y : y - 399) / 400;
  const unsigned yoe = (unsigned)(y - era * 400), doy = (153 * (m + (m > 2 ? -3 : 9)) + 2) / 5 + d - 1, doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
  return era * 146097 + (int64_t)doe - 719468;
}
inline void civilDesdeDias(int64_t z, int* y, unsigned* m, unsigned* d) {
  z += 719468;
  const int64_t era = (z >= 0 ? z : z - 146096) / 146097;
  const unsigned doe = (unsigned)(z - era * 146097), yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
  const int64_t yy = (int64_t)yoe + era * 400;
  const unsigned doy = doe - (365 * yoe + yoe / 4 - yoe / 100), mp = (5 * doy + 2) / 153;
  *d = doy - (153 * mp + 2) / 5 + 1; *m = mp < 10 ? mp + 3 : mp - 9; *y = (int)(yy + (*m <= 2));
}
inline uint8_t aBcdByte(unsigned v) { return (uint8_t)(((v / 10) << 4) | (v % 10)); }
inline unsigned deBcdByte(uint8_t b) { return (b >> 4) * 10 + (b & 0x0F); }

// epoch -> 7 bytes (registros 0x02..0x08). Devuelve false si no cabe en 2000-2099.
inline bool aRegistros(uint32_t epoch, uint8_t out[7]) {
  int64_t dias = epoch / 86400; uint32_t s = epoch % 86400;
  int y; unsigned m, d; civilDesdeDias(dias, &y, &m, &d);
  if (y < 2000 || y > 2099) return false;
  out[0] = aBcdByte(s % 60); out[1] = aBcdByte((s / 60) % 60); out[2] = aBcdByte(s / 3600);
  out[3] = aBcdByte(d); out[4] = (uint8_t)((dias + 4) % 7);                      // 1970-01-01 fue jueves = 4 (domingo = 0)
  out[5] = aBcdByte(m); out[6] = aBcdByte((unsigned)(y - 2000));
  return true;
}
// 7 bytes -> epoch. Devuelve false si el bit VL está en 1 o los campos no tienen sentido (batería agotada o reloj sin ajustar).
inline bool deRegistros(const uint8_t in[7], uint32_t* epoch) {
  if (in[0] & 0x80) return false;
  unsigned s = deBcdByte(in[0] & 0x7F), mi = deBcdByte(in[1] & 0x7F), h = deBcdByte(in[2] & 0x3F), d = deBcdByte(in[3] & 0x3F), mo = deBcdByte(in[5] & 0x1F), y = 2000 + deBcdByte(in[6]);
  if (s > 59 || mi > 59 || h > 23 || d < 1 || d > 31 || mo < 1 || mo > 12) return false;
  *epoch = (uint32_t)(diasDesdeCivil((int)y, mo, d) * 86400 + h * 3600 + mi * 60 + s);
  return true;
}

}  // namespace rtc
