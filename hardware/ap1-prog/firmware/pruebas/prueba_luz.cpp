// Prueba en la PC de AP LIGHT (luz.h): registros del PCA9685, rampa y horario solar.  bash tools/probar_apbus.sh
#include <cstdio>
#include <cmath>
#include "../LetreroLabAP1/luz.h"

static int fallas = 0;
#define REVISA(c) do { if (!(c)) { printf("FALLA linea %d: %s\n", __LINE__, #c); fallas++; } } while (0)

static float dif(float a, float b) { float d = fabsf(a - b); return d > 720 ? 1440 - d : d; }   // minutos, circular

int main() {
  // PCA9685: preescala y frecuencia
  REVISA(pcaPreescala(500) == 11 && fabsf(pcaFrecuencia(11) - 508.6f) < 1);   // PWM4: 508 Hz
  REVISA(pcaPreescala(1526) == 3 && pcaPreescala(5000) == 3);                  // AO4: 1526 Hz (máximo)
  REVISA(pcaPreescala(200) == 30 && pcaPreescala(10) == 255);
  uint8_t r[4];
  pcaCanal(0, r);    REVISA(r[1] == 0 && r[3] == 0x10);                        // todo apagado
  pcaCanal(4096, r); REVISA(r[1] == 0x10 && r[3] == 0);                        // todo encendido
  pcaCanal(2048, r); REVISA(r[0] == 0 && r[1] == 0 && r[2] == 0 && r[3] == 8);
  pcaCanal(1, r);    REVISA(r[2] == 1 && r[3] == 0);
  // rampa de 1 s: 10 pasos de 0.1 s llegan exactos a 100 sin pasarse
  float v = 0;
  for (int i = 0; i < 10; i++) v = luzRampa(v, 100, 0.1f, 1.0f);
  REVISA(fabsf(v - 100) < 1e-3);
  REVISA(luzRampa(80, 20, 0.1f, 1.0f) == 70 && luzRampa(25, 20, 0.1f, 1.0f) == 20 && luzRampa(5, 50, 0.1f, 0) == 50);
  // horario solar contra la "ecuación de salida del sol" (cálculo independiente en Python), en minutos UTC
  struct { int a, m, d; float lat, lon, sal, pue; } C[] = {
    {2026, 3, 20, 19.43f, -99.13f, 760.6f, 47.4f},     // Ciudad de México, equinoccio
    {2026, 6, 21, 19.43f, -99.13f, 719.2f, 77.4f},     // solsticio de verano
    {2026, 12, 21, 19.43f, -99.13f, 785.9f, 3.3f},     // solsticio de invierno
    {2026, 6, 21, 25.67f, -100.31f, 710.8f, 95.2f},    // Monterrey
    {2026, 12, 21, 32.53f, -117.04f, 886.0f, 46.5f},   // Tijuana
    {2026, 1, 15, 20.97f, -89.62f, 757.9f, 1417.5f},   // Mérida
  };
  for (auto& c : C) {
    float s = solMinutosUTC(c.a, c.m, c.d, c.lat, c.lon, true), p = solMinutosUTC(c.a, c.m, c.d, c.lat, c.lon, false);
    if (dif(s, c.sal) > 3 || dif(p, c.pue) > 3) printf("  %d-%02d-%02d %.2f %.2f: %.1f/%.1f contra %.1f/%.1f\n",
                                                      c.a, c.m, c.d, c.lat, c.lon, s, p, c.sal, c.pue);
    REVISA(dif(s, c.sal) <= 3 && dif(p, c.pue) <= 3);
  }
  REVISA(isnan(solMinutosUTC(2026, 6, 21, 80.0f, 0.0f, true)));           // sol de medianoche
  // a hora local de la Ciudad de México (UTC-6): ocaso del equinoccio a las 18:47
  REVISA(solLocal(47.4f, -360) == 18 * 60 + 47);
  REVISA(solLocal(760.6f, -360) == 6 * 60 + 41);
  REVISA(diaDelAnio(2024, 3, 1) == 61 && diaDelAnio(2026, 3, 1) == 60);
  printf(fallas ? "%d FALLAS\n" : "AP LIGHT: todo bien\n", fallas);
  return fallas != 0;
}
