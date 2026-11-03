// Pruebas del núcleo en PC:  g++ -std=c++17 -Wall -Wextra -I../src test_nucleo.cpp ../src/nucleo.cpp -o t && ./t
#include "nucleo.h"
#include <cstdio>
#include <cmath>
#include <cstring>
#include <initializer_list>
using namespace ap;
static int fallos = 0, total = 0;
#define CHECK(c) do { ++total; if (!(c)) { ++fallos; printf("FALLO %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)
static bool cerca(float a, float b, float tol) { return fabsf(a - b) <= tol; }

static float mvDe(float r) { return 3300.f * r / (r + 47000.f); }
static RedFB redPara(int p) { return {0.8f, 29400.f, PERFILES[p].r_b, 47000.f, 3.3f}; }

int main() {
  // --- Tarjeta: cada perfil se reconoce con resistencias al ±5 % y error ADC ±25 mV ---
  for (size_t i = 0; i < N_PERFILES; ++i)
    for (float tol : {-0.05f, 0.f, 0.05f})
      for (float e : {-25.f, 0.f, 25.f})
        CHECK(decodificarTarjeta(mvDe(PERFILES[i].r_id * (1 + tol)) + e) == (int)i);
  CHECK(decodificarTarjeta(3300.f) == -1);   // sin tarjeta
  CHECK(decodificarTarjeta(10.f) == -1);     // corto
  CHECK(decodificarTarjeta(mvDe(4700)) == -1); // valor no válido entre perfiles
  for (size_t i = 0; i < N_PERFILES; ++i)        // tarjeta al revés: ID ve R_B -> inválida
    CHECK(decodificarTarjeta(mvDe(PERFILES[i].r_b)) == -1);
  for (size_t i = 0; i < N_PERFILES; ++i) {       // ... y FB ve R_ID -> voltaje bajo (seguro)
    RedFB rev{0.8f, 29400.f, (float)PERFILES[i].r_id, 47000.f, 3.3f};
    CHECK(vmaxDeRed(rev) < 3.3f);
  }

  // --- Red de realimentación: R_FB da el voltaje del perfil ---
  for (size_t i = 0; i < N_PERFILES; ++i) CHECK(cerca(vmaxDeRed(redPara(i)), PERFILES[i].vmax, 0.06f));
  RedFB r12 = redPara(3);
  CHECK(dacParaVoltaje(r12, 12.5f) == 0.f);      // pedir más que el máximo: sin inyección
  CHECK(vminDeRed(r12) > 10.f && vminDeRed(r12) < 11.f);
  float vd = dacParaVoltaje(r12, 11.5f);          // 11.5 V para tiras más frías
  float vout = vmaxDeRed(r12) - (vd - 0.30f - 0.8f) * r12.rt / r12.rinj;
  CHECK(cerca(vout, 11.5f, 0.01f));
  CHECK(dacParaVoltaje(r12, 1.f) <= 3.3f);

  // --- NTC ---
  CHECK(cerca(ntcCelsius(1650.f), 25.f, 0.1f));
  CHECK(ntcCelsius(0.f) > 100.f);   // NTC en corto => se trata como caliente (seguro)
  CHECK(factorTermico(60) == 1.f && cerca(factorTermico(85), 0.3f, 1e-4f) && factorTermico(95) == 0.f);

  // --- Gamma ---
  CHECK(gamma12(0) == 0 && gamma12(255) == 4095 && gamma12(128) < 1000);

  // --- Controlador: arranque suave ---
  Controlador c; c.configurar(3, r12);               // 12 V 5 A
  Medicion ok{12.f, 2.f, 24.f, 40.f};
  CHECK(c.encender(true));
  c.fijarColor({255, 0, 0, 0}); c.fijarBrillo(1.f);
  Salida s = c.paso(ok, 1000);
  CHECK(s.habilitar_reductor && s.pwm[0] == 0);      // primer ciclo rampa en 0
  s = c.paso(ok, 1300); CHECK(s.pwm[0] > 1900 && s.pwm[0] < 2200);   // ~mitad
  s = c.paso(ok, 1700); CHECK(s.pwm[0] == 4095 && s.pwm[1] == 0);

  // --- Limitación suave: sobre el límite baja brillo sin disparar ---
  Medicion alto{12.f, 5.4f, 24.f, 40.f};
  uint32_t t = 1710;
  for (int k = 0; k < 4; ++k, t += 10) s = c.paso(alto, t);
  CHECK(c.falla() == Falla::NINGUNA && s.pwm[0] < 4095);

  // --- Sobrecorriente dura (>1.5×) por 50 ms => falla, reintento a los 5 s ---
  Medicion oc{11.f, 8.f, 24.f, 40.f};
  for (int k = 0; k < 7; ++k, t += 10) s = c.paso(oc, t);
  CHECK(c.falla() == Falla::SOBRECORRIENTE && !s.habilitar_reductor);
  s = c.paso(ok, t + 1000); CHECK(!s.habilitar_reductor);
  s = c.paso(ok, t + 5100); CHECK(s.habilitar_reductor && c.falla() == Falla::NINGUNA);

  // --- Corto: tras 3 reintentos queda bloqueado hasta RESET ---
  Controlador d; d.configurar(1, redPara(1)); d.encender(true);
  Medicion corto{0.3f, 3.f, 24.f, 30.f};
  uint32_t u = 100;
  for (int ciclo = 0; ciclo < 5; ++ciclo) { for (int k = 0; k < 8; ++k, u += 10) d.paso(corto, u); u += 5200; }
  CHECK(d.falla() == Falla::CORTO);
  s = d.paso(Medicion{12, 0.5f, 24, 30}, u + 20000); CHECK(!s.habilitar_reductor);
  d.reconocerFalla(); s = d.paso(Medicion{12, 0.5f, 24, 30}, u + 20010); CHECK(s.habilitar_reductor);

  // --- Temperatura ---
  Controlador e; e.configurar(1, redPara(1)); e.encender(true); e.fijarBrillo(1.f);
  e.paso(ok, 10); e.paso(Medicion{12, 0.5f, 24, 40}, 700);
  s = e.paso(Medicion{12, 0.5f, 24, 80}, 710); CHECK(s.brillo_efectivo < 0.6f && s.brillo_efectivo > 0.4f);
  s = e.paso(Medicion{12, 0.5f, 24, 92}, 720); CHECK(e.falla() == Falla::SOBRETEMPERATURA);
  s = e.paso(Medicion{12, 0.f, 24, 75}, 9000); CHECK(!s.habilitar_reductor);
  s = e.paso(Medicion{12, 0.f, 24, 65}, 9010); CHECK(s.habilitar_reductor);

  // --- Tarjeta inconsistente (R_FB de 24 V con ID de 12 V) ---
  Controlador g; g.configurar(1, redPara(1)); g.encender(true);
  g.paso(Medicion{24, 0, 30, 30}, 10); g.paso(Medicion{24, 0, 30, 30}, 700);
  s = g.paso(Medicion{24, 0, 30, 30}, 710);
  CHECK(g.falla() == Falla::TARJETA_INCONSISTENTE && !s.habilitar_reductor);
  s = g.paso(Medicion{24, 0, 30, 30}, 99999); CHECK(!s.habilitar_reductor);  // no reintenta

  // --- Subvoltaje de entrada (cartucho de 12 V con perfil de 12 V) ---
  Controlador h; h.configurar(1, redPara(1)); h.encender(true);
  Medicion ok1{12.f, 0.8f, 24.f, 30.f};
  h.paso(ok1, 10); h.paso(ok1, 700); CHECK(h.falla() == Falla::NINGUNA);
  h.paso(Medicion{11.5f, 0.8f, 12.2f, 30}, 710); CHECK(h.falla() == Falla::SUBVOLTAJE_ENTRADA);

  // --- Corte por ALERT de hardware ---
  Controlador k; k.configurar(1, redPara(1)); k.encender(true);
  k.paso(ok1, 10); k.fallaExterna(Falla::SOBRECORRIENTE, 20);
  s = k.paso(ok1, 30); CHECK(!s.habilitar_reductor && k.falla() == Falla::SOBRECORRIENTE);
  s = k.paso(ok1, 5100); CHECK(s.habilitar_reductor);

  // --- Sin tarjeta no enciende ---
  Controlador z; z.configurar(-1, r12); CHECK(!z.encender(true) && z.falla() == Falla::SIN_TARJETA);

  // --- Protocolo ---
  Controlador p; p.configurar(1, redPara(1));
  char r[300];
  procesarComando(p, "on\r\n", ok, r, sizeof r);          CHECK(!strcmp(r, "OK") && p.encendido());
  procesarComando(p, "V 18", ok, r, sizeof r);            CHECK(!strcmp(r, "OK 12.00"));   // recortado al máximo
  procesarComando(p, "V 11.5", ok, r, sizeof r);          CHECK(!strcmp(r, "OK 11.50"));
  procesarComando(p, "V abc", ok, r, sizeof r);           CHECK(!strncmp(r, "ERR", 3));
  procesarComando(p, "RGBW 255 0 128 10", ok, r, sizeof r); CHECK(!strcmp(r, "OK") && p.color().b == 128);
  procesarComando(p, "RGBW 300 0 0 0", ok, r, sizeof r);  CHECK(!strncmp(r, "ERR", 3));
  procesarComando(p, "BRILLO 40", ok, r, sizeof r);       CHECK(cerca(p.brillo(), 0.4f, 1e-6f));
  procesarComando(p, "MODO respira", ok, r, sizeof r);    CHECK(p.modo() == Modo::RESPIRA);
  procesarComando(p, "BORRAR", ok, r, sizeof r);          CHECK(!strcmp(r, "ERR comando"));
  size_t L = procesarComando(p, "ESTADO", ok, r, sizeof r);
  CHECK(L > 50 && strstr(r, "\"perfil\":\"12V 1A\"") && strstr(r, "\"vset\":11.50"));
  printf("%s\n", r);
  char largo[200]; memset(largo, 'A', sizeof largo); largo[199] = 0;
  procesarComando(p, largo, ok, r, sizeof r);             CHECK(!strncmp(r, "ERR", 3));   // no desborda

  printf("%d/%d pruebas OK\n", total - fallos, total);
  return fallos ? 1 : 0;
}
