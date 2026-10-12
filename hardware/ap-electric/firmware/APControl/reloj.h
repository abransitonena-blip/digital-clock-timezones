// AP Control: hora de calendario (sin zona horaria: UTC o la hora local que cargue quien ajusta el reloj), conversión a
// segundos desde 1970 y los registros del reloj de tiempo real PCF8563 del 7R Tour rev B (I2C 0x51). Sin hardware: se prueba en la PC.
#pragma once
#include <stdint.h>

namespace apc {

struct HoraCal { uint16_t anio; uint8_t mes, dia, hora, min, seg; };

// Segundos desde 1970-01-01 00:00:00 (algoritmo de días civiles, años 1970-2099).
inline uint32_t aEpoch(const HoraCal& h) {
  int32_t y = h.anio, m = h.mes;
  y -= m <= 2;
  int32_t era = y / 400, yoe = y - era * 400;
  int32_t doy = (153 * (m + (m > 2 ? -3 : 9)) + 2) / 5 + h.dia - 1;
  int32_t doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
  int32_t dias = era * 146097 + doe - 719468;
  return (uint32_t)dias * 86400u + h.hora * 3600u + h.min * 60u + h.seg;
}
inline HoraCal deEpoch(uint32_t t) {
  uint32_t dias = t / 86400u, r = t % 86400u;
  HoraCal h{};
  h.hora = r / 3600; h.min = (r % 3600) / 60; h.seg = r % 60;
  int32_t z = (int32_t)dias + 719468;
  int32_t era = z / 146097, doe = z - era * 146097;
  int32_t yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
  int32_t y = yoe + era * 400;
  int32_t doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
  int32_t mp = (5 * doy + 2) / 153;
  h.dia = doy - (153 * mp + 2) / 5 + 1;
  h.mes = mp < 10 ? mp + 3 : mp - 9;
  h.anio = y + (h.mes <= 2);
  return h;
}
inline bool horaValida(const HoraCal& h) {
  if (h.anio < 2024 || h.anio > 2099 || h.mes < 1 || h.mes > 12 || h.dia < 1 || h.hora > 23 || h.min > 59 || h.seg > 59) return false;
  static const uint8_t dm[] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
  uint8_t d = dm[h.mes - 1] + (h.mes == 2 && h.anio % 4 == 0 ? 1 : 0);        // 2024-2099: todo año múltiplo de 4 es bisiesto
  return h.dia <= d;
}
// Antes de esta fecha (2024-01-01) una hora se considera «sin ajustar».
const uint32_t EPOCH_MINIMO = 1704067200u;
inline bool epochCreible(uint32_t t) { return t >= EPOCH_MINIMO && t < 4102444800u; }      // hasta 2100-01-01

// ---- PCF8563: registros 0x02-0x08 (segundos, minutos, horas, día, día de la semana, mes + siglo, año), en BCD ----
inline uint8_t aBcd(uint8_t v) { return (uint8_t)((v / 10) << 4 | (v % 10)); }
inline uint8_t deBcd(uint8_t b) { return (uint8_t)((b >> 4) * 10 + (b & 0x0F)); }
inline bool bcdValido(uint8_t b) { return (b >> 4) <= 9 && (b & 0x0F) <= 9; }

// Lee los 7 registros 0x02-0x08. `perdida` = el bit VL de los segundos: el reloj perdió la tensión y la hora no vale.
inline bool leerPCF8563(const uint8_t r[7], HoraCal& h, bool& perdida) {
  perdida = r[0] & 0x80;
  uint8_t s = r[0] & 0x7F, mi = r[1] & 0x7F, ho = r[2] & 0x3F, di = r[3] & 0x3F, me = r[5] & 0x1F, an = r[6];
  if (!bcdValido(s) || !bcdValido(mi) || !bcdValido(ho) || !bcdValido(di) || !bcdValido(me) || !bcdValido(an)) return false;
  h.seg = deBcd(s); h.min = deBcd(mi); h.hora = deBcd(ho); h.dia = deBcd(di); h.mes = deBcd(me); h.anio = 2000 + deBcd(an);
  return horaValida(h) && !perdida;
}
// Los 7 registros a escribir (el bit VL queda en 0). Día de la semana: 0 = domingo.
inline void escribirPCF8563(const HoraCal& h, uint8_t r[7]) {
  uint32_t dias = aEpoch(h) / 86400u;
  uint8_t sem = (uint8_t)((dias + 4) % 7);                    // 1970-01-01 fue jueves (4)
  r[0] = aBcd(h.seg); r[1] = aBcd(h.min); r[2] = aBcd(h.hora); r[3] = aBcd(h.dia); r[4] = sem;
  r[5] = aBcd(h.mes); r[6] = aBcd(h.anio - 2000);
}

}  // namespace apc
