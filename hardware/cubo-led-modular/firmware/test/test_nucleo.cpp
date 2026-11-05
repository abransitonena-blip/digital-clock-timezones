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


static size_t artnet(uint8_t* b, uint16_t univ, const uint8_t* d, uint16_t n) {
  memcpy(b, "Art-Net\0", 8); b[8] = 0x00; b[9] = 0x50; b[10] = 0; b[11] = 14; b[12] = 1; b[13] = 0;
  b[14] = univ & 0xFF; b[15] = (univ >> 8) & 0x7F; b[16] = n >> 8; b[17] = n & 0xFF; memcpy(b + 18, d, n); return 18 + n;
}
static size_t sacn(uint8_t* b, uint16_t univ, const uint8_t* d, uint16_t n) {
  memset(b, 0, 126 + n);
  b[1] = 0x10; memcpy(b + 4, "ASC-E1.17\0\0\0", 12); b[21] = 0x04; b[43] = 0x02; b[108] = 100;
  b[113] = univ >> 8; b[114] = univ & 0xFF; b[117] = 0x02; b[118] = 0xA1; b[122] = 1;
  b[123] = (n + 1) >> 8; b[124] = (n + 1) & 0xFF; b[125] = 0; memcpy(b + 126, d, n); return 126 + n;
}

int main() {
  // --- Tarjeta: cada perfil se reconoce con resistencias al ±5 % y error ADC ±25 mV ---
  for (size_t i = 0; i < N_PERFILES; ++i)
    for (float tol : {-0.05f, 0.f, 0.05f})
      for (float e : {-25.f, 0.f, 25.f})
        CHECK(decodificarTarjeta(mvDe(PERFILES[i].r_id * (1 + tol)) + e) == (int)i);
  CHECK(decodificarTarjeta(3300.f) == -1);   // sin tarjeta
  CHECK(decodificarTarjeta(10.f) == -1);     // corto
  CHECK(decodificarTarjeta(mvDe(4700)) == -1); // valor no válido entre perfiles
  for (size_t i = 0; i < (size_t)PERFIL_PERSONAL; ++i)        // tarjeta al revés: ID ve R_B -> inválida
    CHECK(decodificarTarjeta(mvDe(PERFILES[i].r_b)) == -1);
  for (size_t i = 0; i < N_PERFILES; ++i) {       // ... y FB ve R_ID -> voltaje bajo (seguro)
    RedFB rev{0.8f, 29400.f, (float)PERFILES[i].r_id, 47000.f, 3.3f};
    CHECK(vmaxDeRed(rev) < 3.3f);
  }

  // --- Red de realimentación: R_FB da el voltaje del perfil ---
  for (size_t i = 0; i < (size_t)PERFIL_PERSONAL; ++i) CHECK(cerca(vmaxDeRed(redPara(i)), PERFILES[i].vmax, 0.06f));
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

  // ================= Nuevas funciones =================
  // --- Tipos de tira ---
  Tira tt;
  CHECK(tiraDeTexto("ws2812", tt) && tt == Tira::WS2812B && direccionable(tt) && bytesPorLed(tt) == 3);
  CHECK(tiraDeTexto("SK6812", tt) && bytesPorLed(tt) == 4 && tensionTira(tt) == 5.f);
  CHECK(tiraDeTexto("cct", tt) && !direccionable(tt) && tensionTira(tt) == 0.f);
  CHECK(!tiraDeTexto("APA102", tt));
  uint8_t ob[4];
  CHECK(ordenarBytes(Tira::WS2812B, {10, 20, 30, 40}, ob) == 3 && ob[0] == 20 && ob[1] == 10 && ob[2] == 30);
  CHECK(ordenarBytes(Tira::SK6812, {10, 20, 30, 40}, ob) == 4 && ob[0] == 20 && ob[3] == 40);
  CHECK(ordenarBytes(Tira::WS2811, {10, 20, 30, 40}, ob) == 3 && ob[0] == 10);
  RGBW k27 = mezclaCCT(2700), k65 = mezclaCCT(6500), k46 = mezclaCCT(4600);
  CHECK(k27.r == 255 && k27.g == 0 && k65.r == 0 && k65.g == 255 && k46.r == 255 && k46.g == 255);

  // --- Direccionable de 5 V rechazada con tarjeta de 12 V; aceptada con la de 5 V ---
  Controlador t12; t12.configurar(3, redPara(3));
  CHECK(!t12.fijarTira(Tira::WS2812B) && t12.fijarTira(Tira::WS2815) && t12.fijarTira(Tira::CCT));
  Controlador t5; t5.configurar(0, redPara(0));
  CHECK(t5.fijarTira(Tira::WS2812B) && !t5.fijarTira(Tira::WS2811));
  char rr[300];
  procesarComando(t12, "TIRA WS2812B", ok, rr, sizeof rr); CHECK(strstr(rr, "necesita tarjeta de 5 V") != nullptr);

  // --- Mapeo de canales en tiras analógicas ---
  Medicion ok12{12.f, 1.f, 24.f, 30.f};
  Controlador a; a.configurar(3, redPara(3)); a.encender(true); a.fijarBrillo(1.f); a.fijarColor({255, 128, 0, 200});
  a.fijarTira(Tira::RGB); a.paso(ok12, 10); s = a.paso(ok12, 700);
  CHECK(s.pwm[0] == 4095 && s.pwm[2] == 0 && s.pwm[3] == 0);
  a.fijarTira(Tira::CCT); a.fijarCCT(2700); s = a.paso(ok12, 710);
  CHECK(s.pwm[0] == 4095 && s.pwm[1] == 0 && s.pwm[2] == 0 && s.pwm[3] == 0);
  a.fijarTira(Tira::MONO); s = a.paso(ok12, 720);
  CHECK(s.pwm[3] == 4095 && s.pwm[0] == 0);
  a.fijarTira(Tira::WS2815); s = a.paso(ok12, 730);
  CHECK(s.pwm[0] == 0 && s.pwm[3] == 0 && s.brillo_efectivo > 0.9f && s.habilitar_reductor);

  // --- Efectos por pixel ---
  a.fijarColor({200, 100, 50, 0}); a.fijarModo(Modo::FIJO);
  CHECK(a.colorPixel(5, 60, 1234).r == 200);
  a.fijarModo(Modo::ARCOIRIS);
  CHECK(a.colorPixel(0, 60, 0).r != a.colorPixel(30, 60, 0).r);
  a.fijarModo(Modo::COMETA);
  RGBW cab = a.colorPixel(4, 60, 100), lejos = a.colorPixel(40, 60, 100);   // cabeza en 100/25 = 4
  CHECK(cab.r == 200 && lejos.r == 0);
  a.fijarModo(Modo::FUEGO);
  RGBW f1 = a.colorPixel(3, 60, 0), f2 = a.colorPixel(3, 60, 700);
  CHECK(f1.b == 0 && f1.r > f1.g && (f1.r != f2.r || f1.g != f2.g));

  // --- Horario diario 18:30 a 01:00 ---
  Controlador hz; hz.configurar(1, redPara(1)); hz.encender(false);
  CHECK(!hz.programar(true, 600, 600) && hz.programar(true, 18 * 60 + 30, 60));
  uint32_t base = 1767225600u + 18 * 3600 + 29 * 60 + 50;      // 18:29:50
  hz.fijarHora(base, 0);
  Medicion ok1b{12.f, 0.5f, 24.f, 30.f};
  hz.paso(ok1b, 1000); CHECK(!hz.encendido() && hz.minutoDelDia(1000) == 18 * 60 + 29);
  hz.paso(ok1b, 11000); CHECK(hz.encendido());                    // 18:30:00
  hz.paso(ok1b, 11000 + 6 * 3600 * 1000u); CHECK(hz.encendido());    // 00:30: sigue encendido
  // (pasa por 01:00 en algún ciclo intermedio)
  Controlador hz2; hz2.configurar(1, redPara(1)); hz2.programar(true, 18 * 60 + 30, 60);
  hz2.fijarHora(1767225600u + 59 * 60 + 30, 0); hz2.encender(true);        // 00:59:30 encendido
  hz2.paso(ok1b, 100); hz2.paso(ok1b, 31000); CHECK(!hz2.encendido());      // 01:00 -> apaga
  procesarComando(hz2, "PROG 25:00 01:00", ok, rr, sizeof rr); CHECK(!strncmp(rr, "ERR", 3));
  procesarComando(hz2, "PROG 07:15 23:45", ok, rr, sizeof rr); CHECK(!strcmp(rr, "OK") && hz2.minEncender() == 435 && hz2.minApagar() == 1425);
  procesarComando(hz2, "PROG OFF", ok, rr, sizeof rr); CHECK(!hz2.horarioActivo());

  // --- API JSON tipo WLED ---
  Controlador wl; wl.configurar(1, redPara(1));
  CHECK(wl.aplicarWled("{\"on\":true,\"bri\":128,\"seg\":[{\"col\":[[255,0,10]]}]}"));
  CHECK(wl.encendido() && cerca(wl.brillo(), 128 / 255.f, 1e-3f) && wl.color().r == 255 && wl.color().b == 10);
  CHECK(wl.aplicarWled("{\"on\":\"t\"}") && !wl.encendido());
  CHECK(wl.aplicarWled("{\"col\":[[1,2,3,4]]}") && wl.color().w == 4);
  CHECK(!wl.aplicarWled("{\"bri\":999}") && !wl.aplicarWled("hola"));
  wl.estadoWled(rr, sizeof rr); CHECK(strstr(rr, "\"on\":false") && strstr(rr, "[[1,2,3,4]]"));

  // --- Tarjeta PERSONAL (220k) ---
  CHECK(decodificarTarjeta(mvDe(220000)) == PERFIL_PERSONAL);
  RedFB rp{0.8f, 29400.f, 1910.f, 47000.f, 3.3f};          // R_B 1.91k -> ~13.1 V
  Controlador pe; pe.configurar(PERFIL_PERSONAL, rp);
  CHECK(!pe.encender(true));                                 // sin límites programados no enciende
  procesarComando(pe, "LIMITES 13 2.5", ok, rr, sizeof rr); CHECK(!strcmp(rr, "OK"));
  CHECK(pe.encender(true) && cerca(pe.limiteCorriente(), 2.5f, 1e-6f) && cerca(pe.vset(), 13.f, 1e-6f));
  pe.fijarVoltaje(12.f); s = pe.paso(Medicion{12.f, 0.5f, 24.f, 30.f}, 50);     // la red se ajustó a Vmax = 13 V
  CHECK(cerca(s.vdac, dacParaVoltaje(RedFB{0.8f, 29400.f, 29400.f / (13.f / 0.8f - 1.f), 47000.f, 3.3f}, 12.f), 1e-4f) && s.vdac > 1.1f);
  procesarComando(pe, "LIMITES 30 2", ok, rr, sizeof rr); CHECK(!strncmp(rr, "ERR", 3));
  procesarComando(p, "LIMITES 12 1", ok, rr, sizeof rr); CHECK(!strncmp(rr, "ERR", 3));   // tarjeta normal: no
  procesarComando(p, "MODO fuego", ok, rr, sizeof rr); CHECK(p.modo() == Modo::FUEGO);
  procesarComando(p, "CCT 9000", ok, rr, sizeof rr); CHECK(!strncmp(rr, "ERR", 3));

  // ================= DMX por red y escenas =================
  uint8_t pk[700], dm[512] = {};
  uint16_t uu, nn; const uint8_t* dd;
  dm[0] = 200; dm[1] = 10; dm[2] = 20; dm[3] = 30; dm[4] = 40;
  size_t L1 = artnet(pk, 3, dm, 512);
  CHECK(leerArtNet(pk, L1, uu, dd, nn) && uu == 3 && nn == 512 && dd[0] == 200);
  CHECK(!leerArtNet(pk, 17, uu, dd, nn) && !leerArtNet(pk, L1 - 1, uu, dd, nn));      // truncado
  pk[0] = 'X'; CHECK(!leerArtNet(pk, L1, uu, dd, nn));
  size_t L2 = sacn(pk, 7, dm, 512);
  CHECK(leerE131(pk, L2, uu, dd, nn) && uu == 7 && nn == 512 && dd[4] == 40);
  CHECK(!leerE131(pk, 125, uu, dd, nn) && !leerE131(pk, L2 - 10, uu, dd, nn));
  pk[112] = 0x40; CHECK(!leerE131(pk, L2, uu, dd, nn));                               // fin de stream
  for (size_t k = 0; k < 2000; ++k) { uint8_t basura[64]; for (auto& x : basura) x = (uint8_t)(k * 31 + (&x - basura) * 7); leerArtNet(basura, sizeof basura, uu, dd, nn); leerE131(basura, sizeof basura, uu, dd, nn); }

  Controlador dx; dx.configurar(3, redPara(3)); dx.fijarTira(Tira::RGBW);
  CHECK(!dx.configurarDmx(ProtoDmx::SACN, 0, 1) && !dx.configurarDmx(ProtoDmx::ARTNET, 1, 600));
  CHECK(dx.configurarDmx(ProtoDmx::ARTNET, 3, 1));
  CHECK(!dx.paqueteRed(pk, artnet(pk, 4, dm, 512), 10));                 // otro universo: se ignora
  CHECK(dx.paqueteRed(pk, artnet(pk, 3, dm, 512), 10) && dx.encendido() && dx.dmxActivo(10));
  dx.paso(ok12, 10); s = dx.paso(ok12, 700);
  CHECK(cerca(s.brillo_efectivo, 200 / 255.f, 0.01f) && s.pwm[0] == (uint16_t)lroundf(gamma12(10) * s.brillo_efectivo) && s.pwm[3] == (uint16_t)lroundf(gamma12(40) * s.brillo_efectivo));
  CHECK(!dx.dmxActivo(3600));                                            // sin paquetes 2.5 s: vuelve a normal
  dx.fijarBrillo(1.f); s = dx.paso(ok12, 3600); CHECK(s.brillo_efectivo > 0.99f);
  // direccionable WS2815: 3 canales por LED desde la dirección 10
  for (int k = 0; k < 512; ++k) dm[k] = (uint8_t)k;
  dx.fijarTira(Tira::WS2815); dx.configurarDmx(ProtoDmx::SACN, 1, 10); dx.paqueteRed(pk, sacn(pk, 1, dm, 510), 4000);
  RGBW px0 = dx.colorPixel(0, 200, 4000), px2 = dx.colorPixel(2, 200, 4000), pxf = dx.colorPixel(199, 200, 4000);
  CHECK(px0.r == 9 && px0.g == 10 && px0.b == 11 && px2.r == 15 && pxf.r == 0 && pxf.g == 0);   // fuera del universo: negro
  procesarComando(dx, "ESTADO", ok, rr, sizeof rr);
  char grande[700]; dx.estadoJson(grande, sizeof grande, ok); CHECK(strstr(grande, "\"dmx\":\"sacn\"") && strstr(grande, "\"dir\":10"));
  procesarComando(dx, "DMX ARTNET 0 1", ok, rr, sizeof rr); CHECK(!strcmp(rr, "OK") && dx.protoDmx() == ProtoDmx::ARTNET);
  procesarComando(dx, "DMX SACN 0 1", ok, rr, sizeof rr); CHECK(!strncmp(rr, "ERR", 3));
  procesarComando(dx, "DMX OFF", ok, rr, sizeof rr); CHECK(dx.protoDmx() == ProtoDmx::OFF && !dx.paqueteRed(pk, artnet(pk, 0, dm, 512), 5000));

  // escenas
  Controlador es; es.configurar(1, redPara(1));
  es.fijarColor({1, 2, 3, 4}); es.fijarBrillo(0.3f); es.fijarModo(Modo::FUEGO);
  procesarComando(es, "ESCENA GUARDAR 2", ok, rr, sizeof rr); CHECK(!strcmp(rr, "OK") && es.mascaraEscenas() == 2u);
  es.fijarColor({9, 9, 9, 9}); es.fijarBrillo(1.f); es.fijarModo(Modo::FIJO);
  procesarComando(es, "ESCENA 2", ok, rr, sizeof rr); CHECK(es.color().r == 1 && cerca(es.brillo(), 0.3f, 1e-6f) && es.modo() == Modo::FUEGO);
  procesarComando(es, "ESCENA 5", ok, rr, sizeof rr); CHECK(!strncmp(rr, "ERR", 3));
  procesarComando(es, "ESCENA GUARDAR 9", ok, rr, sizeof rr); CHECK(!strncmp(rr, "ERR", 3));
  Controlador es2; es2.cargarEscenas(es.escenas()); CHECK(es2.aplicarEscena(2) && es2.color().b == 3);

  // ================= Placa v2: RGB+CCT (5 canales) y DMX por cable =================
  Controlador v2; v2.configurar(6, redPara(6));                        // 24 V 2 A
  CHECK(!v2.fijarTira(Tira::RGBCCT));                                   // placa v1: no hay 5.º canal
  v2.placaCincoCanales(true); CHECK(v2.fijarTira(Tira::RGBCCT) && !direccionable(Tira::RGBCCT));
  CHECK(tiraDeTexto("rgbcct", tt) && tt == Tira::RGBCCT);
  Medicion ok24{24.f, 1.f, 30.f, 30.f};
  v2.encender(true); v2.fijarBrillo(1.f); v2.fijarColor({255, 0, 0, 255}); v2.fijarCCT(6500);
  v2.paso(ok24, 10); s = v2.paso(ok24, 700);
  CHECK(s.pwm[0] == 4095 && s.pwm[3] == 0 && s.pwm[4] == 4095);         // 6500 K: todo el blanco al frío
  v2.fijarCCT(2700); s = v2.paso(ok24, 710); CHECK(s.pwm[3] == 4095 && s.pwm[4] == 0);
  v2.fijarTira(Tira::RGBW); s = v2.paso(ok24, 720); CHECK(s.pwm[4] == 0);   // otras tiras: 5.º canal apagado

  // receptor DMX512: bytes de la UART + rupturas
  ReceptorDmx rx; uint8_t got[512]; uint16_t gn = 0;
  CHECK(!rx.tomar(got, gn));
  rx.ruptura();                                                          // primera ruptura: no hay trama previa
  rx.byte(0x00); for (int k = 1; k <= 512; ++k) rx.byte((uint8_t)k);    // código 0 + 512 canales
  rx.byte(0x77);                                                         // byte de más: se ignora
  rx.ruptura(); CHECK(rx.tomar(got, gn) && gn == 512 && got[0] == 1 && got[511] == 0 && rx.tramas() == 1);
  CHECK(!rx.tomar(got, gn));                                             // ya se tomó
  rx.byte(0xCC); rx.byte(5); rx.ruptura(); CHECK(!rx.tomar(got, gn));    // código 0xCC (RDM): no es de niveles
  rx.byte(0x00); rx.ruptura(); CHECK(!rx.tomar(got, gn));                // trama vacía
  rx.byte(0x00); rx.byte(200); rx.byte(1); rx.byte(2); rx.byte(3); rx.byte(4); rx.byte(5); rx.ruptura();
  CHECK(rx.tomar(got, gn) && gn == 6);
  // RGB+CCT por DMX: atenuador, R, G, B, cálido, frío
  v2.fijarTira(Tira::RGBCCT); CHECK(v2.configurarDmx(ProtoDmx::CABLE, 99, 1) && v2.universoDmx() == 0);
  CHECK(v2.entradaDmx(got, gn, 800)); s = v2.paso(ok24, 810);
  CHECK(cerca(s.brillo_efectivo, 200 / 255.f, 0.01f) && s.pwm[4] == (uint16_t)lroundf(gamma12(5) * s.brillo_efectivo) && s.pwm[3] == (uint16_t)lroundf(gamma12(4) * s.brillo_efectivo));
  procesarComando(v2, "DMX CABLE 600", ok, rr, sizeof rr); CHECK(!strncmp(rr, "ERR", 3));
  procesarComando(v2, "DMX CABLE 17", ok, rr, sizeof rr); CHECK(!strcmp(rr, "OK") && v2.protoDmx() == ProtoDmx::CABLE && v2.direccionDmx() == 17);
  v2.estadoJson(grande, sizeof grande, ok); CHECK(strstr(grande, "\"dmx\":\"cable\"") && strstr(grande, "\"tira\":\"RGBCCT\""));
  procesarComando(v2, "DMX OFF", ok, rr, sizeof rr); CHECK(!v2.entradaDmx(got, gn, 900));

  printf("%d/%d pruebas OK\n", total - fallos, total);
  return fallos ? 1 : 0;
}
