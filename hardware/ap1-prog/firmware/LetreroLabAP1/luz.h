// AP LIGHT: cálculos del PCA9685 (PWM4 y AO4) y del horario solar (ocaso y amanecer), sin dependencias del hardware.
// Se prueban en la PC con tools/probar_apbus.sh (prueba_luz.cpp).
#pragma once
#include <stdint.h>
#include <math.h>

// ---- PCA9685: 16 salidas PWM de 12 bits, reloj interno de 25 MHz ----
const uint8_t PCA_MODE1 = 0x00, PCA_MODE2 = 0x01, PCA_LED0 = 0x06, PCA_PRESCALE = 0xFE;
inline uint8_t pcaPreescala(float hz) {                     // frecuencia = 25 MHz / (4096 x (preescala + 1))
  int p = (int)(25000000.0f / (4096.0f * hz) + 0.5f) - 1;
  return p < 3 ? 3 : (p > 255 ? 255 : (uint8_t)p);         // 3 = 1526 Hz (máximo), 255 = 24 Hz
}
inline float pcaFrecuencia(uint8_t pre) { return 25000000.0f / (4096.0f * (pre + 1)); }
// Registros ON_L, ON_H, OFF_L, OFF_H de un canal para un ciclo de 0 a 4096 (4096 = siempre encendido)
inline void pcaCanal(uint16_t v, uint8_t* r) {
  if (v >= 4096) { r[0] = 0; r[1] = 0x10; r[2] = 0; r[3] = 0; }           // bit "todo encendido"
  else if (v == 0) { r[0] = 0; r[1] = 0; r[2] = 0; r[3] = 0x10; }         // bit "todo apagado"
  else { r[0] = 0; r[1] = 0; r[2] = v & 0xFF; r[3] = v >> 8; }
}
// Rampa: acerca "actual" a "objetivo" (0-100 %) a razón de 100 % cada "segundos"
inline float luzRampa(float actual, float objetivo, float dt, float segundos) {
  if (segundos <= 0) return objetivo;
  float paso = 100.0f * dt / segundos;
  if (actual < objetivo) return actual + paso >= objetivo ? objetivo : actual + paso;
  return actual - paso <= objetivo ? objetivo : actual - paso;
}

// ---- horario solar (algoritmo del Almanaque Náutico / NOAA simplificado, error de 1-2 min) ----
inline int diaDelAnio(int anio, int mes, int dia) {
  static const int AC[12] = {0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334};
  bool bis = (anio % 4 == 0 && anio % 100 != 0) || anio % 400 == 0;
  return AC[mes - 1] + dia + (bis && mes > 2 ? 1 : 0);
}
// Minutos UTC (0-1440) de la salida (salida = true) o la puesta del Sol en esa fecha; NAN si no sale o no se pone.
// Cenit 90.833: borde superior del disco con la refracción normal (lo que se llama "amanecer" y "ocaso").
inline float solMinutosUTC(int anio, int mes, int dia, float lat, float lon, bool salida) {
  const float R = 3.14159265f / 180.0f;
  int n = diaDelAnio(anio, mes, dia);
  float lh = lon / 15.0f;
  float t = n + ((salida ? 6.0f : 18.0f) - lh) / 24.0f;
  float m = 0.9856f * t - 3.289f;
  float l = m + 1.916f * sinf(m * R) + 0.020f * sinf(2 * m * R) + 282.634f;
  l = fmodf(l + 720.0f, 360.0f);
  float ra = atanf(0.91764f * tanf(l * R)) / R;
  ra = fmodf(ra + 720.0f, 360.0f);
  ra += floorf(l / 90.0f) * 90.0f - floorf(ra / 90.0f) * 90.0f;          // mismo cuadrante que la longitud solar
  ra /= 15.0f;
  float sd = 0.39782f * sinf(l * R), cd = cosf(asinf(sd));
  float ch = (cosf(90.833f * R) - sd * sinf(lat * R)) / (cd * cosf(lat * R));
  if (ch > 1 || ch < -1) return NAN;                        // día o noche polar
  float h = (salida ? 360.0f - acosf(ch) / R : acosf(ch) / R) / 15.0f;
  float tl = h + ra - 0.06571f * t - 6.622f;
  float ut = fmodf(tl - lh + 48.0f, 24.0f);
  return ut * 60.0f;
}
// Minuto local (0-1439) de un evento dado en minutos UTC y la diferencia local - UTC en minutos
inline int16_t solLocal(float minutosUtc, int16_t difMin) {
  int v = (int)(minutosUtc + 0.5f) + difMin;
  return (int16_t)(((v % 1440) + 1440) % 1440);
}
