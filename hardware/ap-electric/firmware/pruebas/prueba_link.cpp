// Pruebas en la PC de AP LINK (ap_link.h): simulador de una cadena de módulos con RS-485 compartido, cables que se quitan y se ponen,
// energía por módulo, SENSE entre módulos, tramas perdidas y dañadas. Cada "ms" del simulador es un milisegundo del equipo.
//   g++ -std=c++17 -Wall -Wextra -Werror prueba_link.cpp && ./a.out
#include <cstdio>
#include <cstdlib>
#include "sim_link.h"

static int fallas = 0, pruebas = 0;
#define CHECK(c, ...) do { pruebas++; if (!(c)) { fallas++; printf("FALLA (línea %d): ", __LINE__); printf(__VA_ARGS__); printf("\n"); } } while (0)

// ---------------------------------------------------------------------------------------------
static void prueba_trama() {
  Trama t; t.dst = 3; t.src = 1; t.tipo = T_POLL; t.n = 3; t.d[0] = 0x34; t.d[1] = 0x12; t.d[2] = 0;
  uint8_t b[40]; size_t k = codificar(t, b);
  Receptor r; bool ok = false;
  for (size_t i = 0; i < k; i++) ok = r.poner(b[i]);
  CHECK(ok && r.t.dst == 3 && r.t.tipo == T_POLL && r.t.d[0] == 0x34, "trama simple");
  // basura antes, trama dañada en medio, trama buena al final: debe recuperarse
  Receptor q; int buenas = 0;
  uint8_t mala[40]; memcpy(mala, b, k); mala[6] ^= 0x40;
  std::vector<uint8_t> flujo = {0x00, 0xFF, 0xA5, 0x01};            // basura con un SYNC falso
  flujo.insert(flujo.end(), mala, mala + k);
  flujo.insert(flujo.end(), b, b + k);
  for (uint8_t x : flujo) if (q.poner(x)) buenas++;
  CHECK(buenas == 1 && q.malas >= 1, "resincroniza tras CRC malo: buenas=%d malas=%u", buenas, q.malas);
  // largo imposible
  Receptor w; uint8_t c[] = {SYNC, 1, 2, 3, 200, 0, 0};
  bool algo = false; for (uint8_t x : c) algo |= w.poner(x);
  CHECK(!algo, "largo mayor al máximo se descarta");
  // dos tramas pegadas
  Receptor v; int dos = 0;
  for (int rep = 0; rep < 2; rep++) for (size_t i = 0; i < k; i++) if (v.poner(b[i])) dos++;
  CHECK(dos == 2, "dos tramas seguidas");
}

static void prueba_dos_modulos() {
  Sim s(2);
  s.energia(0, true); s.energia(1, true);
  uint32_t t = 0; while (t < 6000 && !(s.cabeza() && s.cabeza()->total() == 2)) { s.paso(); t++; }
  CHECK(s.cabeza() != nullptr, "hay exactamente un cabeza");
  CHECK(s.cabeza() && s.cabeza()->total() == 2, "dos módulos reconocidos (t=%u ms)", t);
  s.correr(100);
  CHECK(t < 4000, "se forma en menos de 4 s (t=%u)", t);
  CHECK(s.n[0]->e->rol() == Rol::CABEZA && s.n[0]->e->pos() == 1, "el primero es el cabeza, posición 1");
  CHECK(s.n[1]->e->rol() == Rol::ESCLAVO && s.n[1]->e->pos() == 2, "el segundo es esclavo en la posición 2");
  s.correr(500);
  Enlace* c = s.cabeza();
  CHECK(c->totalSalidas() == 32 && c->totalEntradas() == 16, "canales sumados: %u salidas, %u entradas", c->totalSalidas(), c->totalEntradas());
  CHECK(s.n[1]->e->total() == 2, "el esclavo también sabe que son 2");
  // canal global 17 = salida 1 del módulo 2
  uint8_t p, l;
  CHECK(c->canalGlobal(17, &p, &l) && p == 2 && l == 1, "canal 17 -> módulo 2, salida 1");
  CHECK(c->canalGlobal(16, &p, &l) && p == 1 && l == 16, "canal 16 -> módulo 1, salida 16");
  CHECK(!c->canalGlobal(33, &p, &l), "el canal 33 no existe");
  CHECK(c->mandarCanal(17, true) && c->mandarCanal(32, true) && c->mandarCanal(3, true), "mandar canales");
  s.correr(200);
  CHECK(s.n[1]->e->salidas() == (0x0001 | 0x8000), "salidas del módulo 2 = 0x%04X", s.n[1]->e->salidas());
  CHECK(s.n[0]->e->salidas() == 0x0004, "salidas del módulo 1 = 0x%04X", s.n[0]->e->salidas());
  // entradas del módulo 2 llegan al cabeza
  s.n[1]->ent = 0x00A5; s.correr(200);
  CHECK(c->modulo(2) && c->modulo(2)->ent == 0x00A5, "entradas del módulo 2 en el cabeza");
  CHECK(c->modulo(2) && c->modulo(2)->vin_mV == 24000, "tensión de entrada del módulo 2 informada");
  CHECK(c->modulo(2) && c->modulo(2)->sal == (0x0001 | 0x8000), "el módulo 2 confirma las salidas aplicadas");
}

static void prueba_orden_de_energia() {
  // 5 módulos; el orden de encendido no cambia el orden de la cadena (lo fija el cable, vía SENSE)
  const int orden[][5] = {{0, 1, 2, 3, 4}, {4, 3, 2, 1, 0}, {2, 4, 0, 3, 1}};
  for (auto& o : orden) {
    Sim s(5);
    for (int k = 0; k < 5; k++) { s.energia(o[k], true); s.correr(137); }
    uint32_t t = 0; while (t < 20000 && !(s.cabeza() && s.cabeza()->total() == 5)) { s.paso(); t++; }
    s.correr(200);
    bool bien = s.cabeza() && s.cabeza()->total() == 5;
    CHECK(bien, "orden %d%d%d%d%d: 5 módulos (t=%u)", o[0], o[1], o[2], o[3], o[4], t);
    for (int i = 0; i < 5 && bien; i++) {
      CHECK(s.n[i]->e->pos() == i + 1, "orden de energía %d%d%d%d%d: el módulo físico %d quedó en la posición %d", o[0], o[1], o[2], o[3], o[4], i, s.n[i]->e->pos());
    }
    CHECK(s.cuantosCabezas() == 1, "un solo cabeza (%d)", s.cuantosCabezas());
  }
}

static void prueba_modulo_nuevo() {
  Sim s(4);
  for (int i = 0; i < 3; i++) s.energia(i, true);
  s.correr(8000);
  CHECK(s.cabeza() && s.cabeza()->total() == 3, "arranca con 3 (%d)", s.cabeza() ? s.cabeza()->total() : -1);
  s.cabeza()->mandar(2, 0x1234);
  s.energia(3, true);                          // se conecta uno nuevo al final con la cadena en marcha
  uint32_t t = 0; while (t < 8000 && s.cabeza()->total() != 4) { s.paso(); t++; }
  CHECK(s.cabeza()->total() == 4, "el módulo nuevo entra (t=%u ms)", t);
  s.correr(200);
  CHECK(s.n[3]->e->pos() == 4, "posición 4");
  CHECK(s.n[1]->e->pos() == 2 && s.n[2]->e->pos() == 3, "los demás no cambian de posición");
  s.correr(300);
  CHECK(s.n[1]->e->salidas() == 0x1234, "la cadena siguió mandando durante el alta (0x%04X)", s.n[1]->e->salidas());
}

static void prueba_estado_seguro() {
  Sim s(3);
  for (int i = 0; i < 3; i++) s.energia(i, true);
  s.correr(6000);
  Enlace* c = s.cabeza(); c->mandar(2, 0xFFFF); c->mandar(3, 0x00FF);
  s.correr(300);
  CHECK(s.n[1]->e->salidas() == 0xFFFF && s.n[2]->e->salidas() == 0x00FF, "salidas aplicadas");
  s.n[2]->e->maskSegura(0x0001);               // configuración: este módulo deja la salida 1 encendida si pierde el enlace
  s.energia(0, false);                         // el cabeza se apaga de golpe
  uint32_t t = 0; while (t < 3000 && !s.n[1]->e->enSeguro()) { s.paso(); t++; }
  CHECK(t <= (uint32_t)WDOG_MS + 100, "salidas seguras en %u ms tras perder al cabeza (máx %u)", t, (unsigned)WDOG_MS);
  s.correr(150);
  CHECK(s.n[1]->e->salidas() == 0x0000, "módulo 2 apaga todo");
  CHECK(s.n[2]->e->enSeguro() && s.n[2]->e->salidas() == 0x0001, "módulo 3 va a su máscara segura (0x%04X)", s.n[2]->e->salidas());
}

static void prueba_cabeza_reinicia() {
  Sim s(3);
  for (int i = 0; i < 3; i++) s.energia(i, true);
  s.correr(6000);
  s.cabeza()->mandar(2, 0xAAAA);
  s.correr(200);
  s.energia(0, false); s.correr(800);          // el cabeza se reinicia (menos de PROMOVER_MS)
  s.energia(0, true);
  uint32_t t = 0; while (t < 12000 && !(s.cabeza() && s.cabeza()->total() == 3 && s.n[2]->e->rol() == Rol::ESCLAVO && s.n[1]->e->rol() == Rol::ESCLAVO)) { s.paso(); t++; }
  CHECK(s.cabeza() && s.cabeza()->total() == 3, "la cadena se rearma (t=%u ms)", t);
  CHECK(s.n[0]->e->rol() == Rol::CABEZA && s.n[1]->e->pos() == 2 && s.n[2]->e->pos() == 3, "mismas posiciones tras el reinicio");
  CHECK(s.cuantosCabezas() == 1, "un solo cabeza");
}

static void prueba_cable_cortado() {
  Sim s(4);
  for (int i = 0; i < 4; i++) s.energia(i, true);
  s.correr(8000);
  CHECK(s.cabeza() && s.cabeza()->total() == 4, "4 módulos");
  s.cabeza()->mandar(3, 0xFFFF);
  s.correr(200);
  s.cable[1] = false;                          // se desconecta el cable entre el módulo 2 y el 3
  uint32_t t = 0; while (t < 4000 && s.cabeza()->total() != 2) { s.paso(); t++; }
  CHECK(s.cabeza()->total() == 2, "el cabeza ve 2 módulos tras el corte (t=%u)", t);
  s.correr(300);
  CHECK(s.n[2]->e->enSeguro() && s.n[3]->e->enSeguro(), "los módulos sin cabeza van a salidas seguras");
  CHECK(s.n[2]->e->salidas() == 0, "módulo 3 apagado");
  // el tramo aislado elige su cabeza
  t = 0; while (t < 15000 && s.cuantosCabezas() != 2) { s.paso(); t++; }
  CHECK(s.cuantosCabezas() == 2, "cada tramo con su cabeza (t=%u)", t);
  t = 0; while (t < 15000 && !(s.n[2]->e->rol() == Rol::CABEZA && s.n[2]->e->total() == 2)) { s.paso(); t++; }
  s.correr(200);
  CHECK(s.n[2]->e->rol() == Rol::CABEZA && s.n[2]->e->total() == 2 && s.n[3]->e->pos() == 2, "el tramo aislado se rearma como 2 módulos");
  CHECK(s.n[0]->e->rol() == Rol::CABEZA && s.n[0]->e->total() == 2, "el tramo principal sigue con su cabeza");
  // se reconecta: gana el cabeza original y vuelven los 4 en orden
  s.cable[1] = true;
  t = 0; while (t < 40000 && !(s.cuantosCabezas() == 1 && s.cabeza() && s.cabeza()->total() == 4 && s.n[2]->e->pos() == 3 && s.n[3]->e->pos() == 4)) { s.paso(); t++; }
  CHECK(s.cuantosCabezas() == 1 && s.cabeza() == s.n[0]->e.get(), "gana el cabeza original (cabezas=%d)", s.cuantosCabezas());
  CHECK(s.cabeza() && s.cabeza()->total() == 4 && s.n[2]->e->pos() == 3 && s.n[3]->e->pos() == 4, "vuelven los 4 módulos en orden (t=%u)", t);
  s.cabeza()->mandar(4, 0x0F0F);
  s.correr(300);
  CHECK(s.n[3]->e->salidas() == 0x0F0F, "y vuelve a mandar salidas");
}

static void prueba_modulo_sin_energia() {
  Sim s(4);
  s.energia(0, true); s.energia(1, true); s.energia(3, true);       // el módulo 3 (índice 2) está apagado
  s.correr(10000);
  CHECK(s.cabeza() && s.cabeza()->total() == 2, "con un módulo apagado en medio, el cabeza ve 2 (%d)", s.cabeza() ? s.cabeza()->total() : -1);
  CHECK(s.n[3]->e->rol() != Rol::ESCLAVO, "el que está detrás del apagado no se une (SENSE queda en 0)");
  s.energia(2, true);
  uint32_t t = 0; while (t < 15000 && !(s.cabeza() && s.cabeza()->total() == 4)) { s.paso(); t++; }
  CHECK(s.cabeza() && s.cabeza()->total() == 4, "al encenderlo, entran el 3 y el 4 en orden (t=%u)", t);
  s.correr(300);
  CHECK(s.n[2]->e->pos() == 3 && s.n[3]->e->pos() == 4, "posiciones 3 y 4");
  // se le va la energía a uno en marcha
  s.energia(2, false);
  t = 0; while (t < 4000 && s.cabeza()->total() != 2) { s.paso(); t++; }
  CHECK(s.cabeza()->total() == 2, "el cabeza nota la baja (t=%u)", t);
}

static void prueba_ruido() {
  Sim s(5);
  s.pPerder = 0.04; s.pDanar = 0.04;
  for (int i = 0; i < 5; i++) s.energia(i, true);
  uint32_t t = 0; while (t < 30000 && !(s.cabeza() && s.cabeza()->total() == 5)) { s.paso(); t++; }
  CHECK(s.cabeza() && s.cabeza()->total() == 5, "con 4%% de tramas perdidas y 4%% dañadas se forma la cadena (t=%u)", t);
  s.cabeza()->mandar(5, 0x5A5A);
  s.correr(15000);
  CHECK(s.cabeza() && s.cabeza()->total() == 5, "y se mantiene 15 s sin perder módulos");
  CHECK(s.n[4]->e->salidas() == 0x5A5A, "salidas del último módulo correctas (0x%04X)", s.n[4]->e->salidas());
  uint32_t malas = 0; for (auto& nd : s.n) malas += nd->e->malas();
  CHECK(malas > 0, "hubo tramas dañadas detectadas por CRC (%u)", malas);
  for (int i = 1; i < 5; i++) CHECK(s.n[i]->e->pos() == i + 1, "posición %d", i + 1);
}

static void prueba_lleno() {
  Sim s(18);
  for (int i = 0; i < 18; i++) s.energia(i, true);
  s.correr(60000);
  CHECK(s.cabeza() && s.cabeza()->total() == MAX_MODULOS, "máximo %d módulos (hay %d)", MAX_MODULOS, s.cabeza() ? s.cabeza()->total() : -1);
  CHECK(s.cabeza() && s.cabeza()->totalSalidas() == 16 * MAX_MODULOS, "%u salidas en total", s.cabeza() ? s.cabeza()->totalSalidas() : 0);
  CHECK(s.n[16]->e->rol() == Rol::ESPERA && s.n[17]->e->rol() == Rol::ESPERA, "los módulos 17 y 18 esperan sin dirección");
  // con 16 módulos el POLL de cada uno sigue sin pasar de 100 ms
  s.cabeza()->mandar(16, 0xBEEF);
  s.correr(200);
  CHECK(s.n[15]->e->salidas() == 0xBEEF, "el módulo 16 recibe su orden en menos de 200 ms");
}

static void prueba_sin_candidato_a_cabeza() {
  Sim s(3);
  for (int i = 0; i < 3; i++) s.energia(i, true, i == 1 ? false : (i == 2 ? false : true));
  s.correr(8000);
  CHECK(s.cabeza() && s.cabeza()->total() == 3, "módulos que no pueden ser cabeza se unen a uno que sí");
  Sim q(2);
  q.energia(0, true, false); q.energia(1, true, false);
  q.correr(20000);
  CHECK(q.cuantosCabezas() == 0, "si nadie puede ser cabeza, nadie manda ni suelta salidas");
  CHECK(q.n[0]->e->enSeguro() && q.n[1]->e->enSeguro(), "y sus salidas quedan seguras");
}

static void prueba_brillo_pwm() {
  Sim s(3);
  s.energia(0, true); s.energia(1, true, true, Caps{4, 8, 8, VERSION, 0, 8}); s.energia(2, true, true, Caps{4, 8, 0, VERSION, 0, 4});
  uint32_t t = 0; while (t < 8000 && !(s.cabeza() && s.cabeza()->total() == 3)) { s.paso(); t++; }
  Enlace* c = s.cabeza();
  CHECK(c && c->total() == 3, "con módulos LED8 la cadena sigue formándose");
  s.correr(300);
  const InfoMod* m2 = c->modulo(2); const InfoMod* m3 = c->modulo(3);
  CHECK(m2 && m2->caps.tipo == 4 && m2->caps.nPwm == 8 && m3->caps.nPwm == 4, "el cabeza conoce cuántas salidas con brillo tiene cada módulo");
  CHECK(s.n[1]->e->dutyLocal()[0] == 255, "el brillo por defecto es pleno");
  CHECK(c->mandarDuty(2, 3, 64) && c->mandarDuty(3, 4, 200), "mandar brillo a las salidas con PWM");
  CHECK(!c->mandarDuty(3, 5, 10), "una salida sin PWM rechaza el brillo");
  CHECK(!c->mandarDuty(1, 1, 10), "un módulo sin PWM rechaza el brillo");
  CHECK(c->mandarDutyCanal(17, 128), "brillo por canal global: 17 = módulo 2, salida 1");
  CHECK(c->mandarCanal(17, true) && c->mandarCanal(19, true), "y encender esas salidas");
  s.correr(300);
  CHECK(s.n[1]->e->dutyLocal()[2] == 64 && s.n[1]->e->dutyLocal()[0] == 128, "el módulo 2 recibe los brillos 64 y 128");
  CHECK(s.n[2]->e->dutyLocal()[3] == 200, "el módulo 3 recibe el brillo 200");
  CHECK(s.n[1]->e->salidas() == 0x0005, "las salidas encendidas llegan junto con el brillo (0x%04X)", s.n[1]->e->salidas());
  s.n[1]->e.reset();                                  // se apaga el módulo 2 y vuelve con energía: arranca otra vez en brillo pleno
  s.correr(3000);
  s.energia(1, true, true, Caps{4, 8, 8, VERSION, 0, 8});
  s.correr(8000);
  CHECK(s.n[1]->e && s.n[1]->e->dutyLocal()[2] == 255, "un módulo que vuelve a la cadena arranca en brillo pleno (el cabeza ya no recuerda el brillo)");
}

int main() {
  prueba_trama();
  prueba_dos_modulos();
  prueba_orden_de_energia();
  prueba_modulo_nuevo();
  prueba_estado_seguro();
  prueba_cabeza_reinicia();
  prueba_cable_cortado();
  prueba_modulo_sin_energia();
  prueba_ruido();
  prueba_lleno();
  prueba_sin_candidato_a_cabeza();
  prueba_brillo_pwm();
  if (fallas) { printf("AP LINK: %d de %d comprobaciones fallaron\n", fallas, pruebas); return 1; }
  printf("AP LINK: todo bien (%d comprobaciones)\n", pruebas);
  return 0;
}
