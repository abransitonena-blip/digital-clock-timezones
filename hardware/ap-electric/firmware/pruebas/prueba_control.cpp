// Pruebas en la PC del núcleo AP Control (ap_control.h) y del esclavo Modbus (modbus_esclavo.h).
#include "../APControl/ap_control.h"
#include "../APControl/modbus_esclavo.h"
#include <cstdio>
#include <vector>
using namespace apc;
static int fallas = 0;
#define REVISA(c) do { if (!(c)) { printf("  falla en la línea %d: %s\n", __LINE__, #c); fallas++; } } while (0)

struct Banco {                                 // simula el hardware del 7R Tour: la bobina sigue a la salida
  Controlador c; uint32_t t = 0; uint8_t ent = 0, btn = 0, forzar = 0; bool hay24 = true;
  void correr(uint32_t ms) { for (uint32_t i = 0; i < ms; i += 5) { t += 5; c.paso(t, ent, btn, hay24 ? (c.salida | forzar) : forzar); } }
};
static std::vector<uint8_t> trama(std::vector<uint8_t> q) { uint16_t k = crc16(q.data(), q.size()); q.push_back(k & 0xFF); q.push_back(k >> 8); return q; }

int main() {
  // 1) arranque: fábrica = todo apagado; último y encendido solo en alumbrado; proceso siempre apagado
  {
    Config c = fabrica(7, 8);
    c.canal[0].arranque = ARR_ULTIMO; c.canal[1].arranque = ARR_ENCENDIDO;
    c.canal[2].arranque = ARR_ENCENDIDO; c.canal[2].carga = CARGA_PROCESO;      // inválido: se corrige
    c.crc = crcDe(c);
    Banco b; b.c.iniciar(c, 0x7F, nullptr, 0, false);
    REVISA(b.c.salida == 0x03);                     // canal 1 (último = 1) y 2 (encendido); el 3 de proceso no
    REVISA(b.c.fallas & F_CONFIG);                  // se avisó que la configuración tenía algo inválido
    REVISA(b.c.cfg.canal[2].arranque == ARR_APAGADO);
    Banco f; f.c.iniciar(fabrica(7, 8), 0x7F, nullptr, 0, false);
    REVISA(f.c.salida == 0 && f.c.fallas == 0);
  }
  // 2) entradas: pulsador alterna, interruptor sigue, conmutador (escalera) alterna en cada cambio, antirrebote
  {
    Config c = fabrica(7, 8);
    for (int k = 0; k < 3; k++) c.entrada[k].canal = k + 1;               // de fábrica las entradas no están acopladas a ningún canal
    c.entrada[0].modo = ENT_PULSADOR; c.entrada[1].modo = ENT_INTERRUPTOR; c.entrada[2].modo = ENT_CONMUTADOR; c.entrada[3].modo = ENT_DESACOPLADA;
    c.crc = crcDe(c);
    Banco b; b.c.iniciar(c, 0, nullptr, 0, false);
    b.ent = 1; b.correr(20); REVISA(!(b.c.salida & 1));      // 20 ms: todavía no pasa el antirrebote de 30 ms
    b.correr(20); REVISA(b.c.salida & 1);
    b.ent = 0; b.correr(50); REVISA(b.c.salida & 1);          // soltar el pulsador no lo apaga
    b.ent = 1; b.correr(50); b.ent = 0; b.correr(50); REVISA(!(b.c.salida & 1));
    for (int i = 0; i < 5; i++) { b.ent ^= 1; b.correr(3); }  // rebote de 15 ms: no cambia nada
    b.ent = 0; b.correr(50); REVISA(!(b.c.salida & 1));
    b.ent = 2; b.correr(50); REVISA(b.c.salida & 2); b.ent = 0; b.correr(50); REVISA(!(b.c.salida & 2));
    b.ent = 4; b.correr(50); REVISA(b.c.salida & 4); b.ent = 0; b.correr(50); REVISA(!(b.c.salida & 4));
    b.ent = 4; b.correr(50); REVISA(b.c.salida & 4);          // el otro apagador de la escalera también alterna
    b.ent = 8; b.correr(50); REVISA(!(b.c.salida & 8));       // desacoplada: no manda
    REVISA(b.c.entradas == 0x08);
  }
  // 3) botones y temporizador de escalera (pulso de 2 s, se vuelve a disparar)
  {
    Config c = fabrica(7, 8); c.canal[4].pulsoS = 2; c.crc = crcDe(c);
    Banco b; b.c.iniciar(c, 0, nullptr, 0, false);
    b.btn = 1 << 4; b.correr(40); b.btn = 0; b.correr(40); REVISA(b.c.salida & 16);
    b.correr(1500); REVISA(b.c.salida & 16);
    b.c.ordenar(5, 1, OR_RED, b.t); b.correr(1500); REVISA(b.c.salida & 16);   // re-disparo
    b.correr(600); REVISA(!(b.c.salida & 16));
    REVISA(b.c.maniobras[4] == 1);
  }
  // 4) Modbus: lectura, escritura, excepciones, difusión, vigilancia de comunicación
  {
    Config c = fabrica(7, 8); c.mbDireccion = 3; c.mbVigilanciaS = 2; c.canal[1].accionCom = COM_MANTENER; c.crc = crcDe(c);
    Banco b; b.c.iniciar(c, 0, nullptr, 0, false);
    uint32_t seg = 77; Esclavo m(b.c, 100, 1, &seg); uint8_t r[260];
    auto q = trama({3, 5, 0, 0, 0xFF, 0}); size_t n = m.procesar(q.data(), q.size(), r, b.t);
    REVISA(n == 8 && r[1] == 5 && (b.c.salida & 1));
    q = trama({3, 15, 0, 1, 0, 2, 1, 3}); n = m.procesar(q.data(), q.size(), r, b.t);   // canales 2 y 3
    REVISA(n == 8 && (b.c.salida & 6) == 6);
    q = trama({3, 1, 0, 0, 0, 7}); n = m.procesar(q.data(), q.size(), r, b.t);
    REVISA(n == 6 && r[2] == 1 && r[3] == 7);
    q = trama({3, 4, 0, 0, 0, 2}); n = m.procesar(q.data(), q.size(), r, b.t);
    REVISA(n == 9 && r[3] == 0 && r[4] == 100 && r[6] == 1);
    q = trama({3, 3, 0, 9, 0, 1}); n = m.procesar(q.data(), q.size(), r, b.t);         // registro que no existe
    REVISA(n == 5 && r[1] == 0x83 && r[2] == 2);
    q = trama({3, 6, 0, 20, 0, 1}); n = m.procesar(q.data(), q.size(), r, b.t);        // canal 1 = proceso
    REVISA(n == 8 && b.c.cfg.canal[0].carga == CARGA_PROCESO);
    q = trama({3, 6, 0, 10, 0, 2}); n = m.procesar(q.data(), q.size(), r, b.t);        // proceso + encendido: no
    REVISA(n == 5 && r[1] == 0x86 && r[2] == 3);
    q = trama({4, 5, 0, 3, 0xFF, 0}); REVISA(m.procesar(q.data(), q.size(), r, b.t) == 0 && !(b.c.salida & 8));  // otro esclavo
    q = trama({0, 5, 0, 3, 0xFF, 0}); REVISA(m.procesar(q.data(), q.size(), r, b.t) == 0 && (b.c.salida & 8));   // difusión
    q = trama({3, 5, 0, 0, 0xFF, 0}); q[3] ^= 1; REVISA(m.procesar(q.data(), q.size(), r, b.t) == 0 && m.tramasMal == 1);
    b.correr(1900); REVISA(!b.c.comPerdida);
    b.correr(200); REVISA(b.c.comPerdida && (b.c.fallas & F_COMUNICACION));
    REVISA((b.c.salida & 0x0F) == 0x02);            // 1, 3, 4 se apagan; el 2 (mantener) sigue
    q = trama({3, 3, 0, 0, 0, 1}); m.procesar(q.data(), q.size(), r, b.t);          // una lectura SÍ cuenta: el maestro está presente
    REVISA(!b.c.comPerdida && (b.c.salida & 0x0D) == 0);                            // vuelve sin reencender nada
    q = trama({3, 6, 0, 0, 0, 2}); m.procesar(q.data(), q.size(), r, b.t);
    REVISA(!b.c.comPerdida && (b.c.salida & 0x0D) == 0);
    q = trama({3, 6, 0, 200, 0xA5, 0x5A}); m.procesar(q.data(), q.size(), r, b.t); REVISA(m.pedirGuardar);
    q = trama({3, 6, 0, 200, 0x5A, 0xA5}); n = m.procesar(q.data(), q.size(), r, b.t);
    REVISA(n == 5 && r[1] == 0x86 && r[2] == 4 && !m.pedirFabrica);               // fábrica por Modbus exige el permiso local
    q = trama({3, 3, 0xFF, 0xFF, 0, 2}); n = m.procesar(q.data(), q.size(), r, b.t);
    REVISA(n == 5 && r[1] == 0x83 && r[2] == 2);                                   // dirección + cantidad pasan de 65535
  }
  // 4 bis) un maestro que solo LEE no dispara la pérdida de comunicación
  {
    Config c = fabrica(7, 8); c.mbVigilanciaS = 2; c.crc = crcDe(c);
    Banco b; b.c.iniciar(c, 0, nullptr, 0, false);
    Esclavo m(b.c, 1, 1, nullptr); m.ultimoAhora = 0; std::vector<uint8_t> q; uint8_t r[260];
    q = trama({1, 5, 0, 0, 0xFF, 0}); m.procesar(q.data(), q.size(), r, b.t); REVISA(b.c.salida & 1);
    for (int i = 0; i < 20; i++) { b.correr(1000); q = trama({1, 3, 0, 0, 0, 1}); m.procesar(q.data(), q.size(), r, b.t); }
    REVISA(!b.c.comPerdida && (b.c.salida & 1));                                   // 20 s solo leyendo: sigue encendido
    b.correr(2500); REVISA(b.c.comPerdida && !(b.c.salida & 1));                   // sin ninguna trama: ahí sí
  }
  // 4 ter) valores de fábrica: placa de varios canales con entradas desacopladas; AP Home con pulsador
  {
    Banco b; b.c.iniciar(fabrica(7, 8), 0, nullptr, 0, false);
    for (int i = 0; i < 10; i++) { b.ent = 3; b.correr(60); b.ent = 0; b.correr(60); }
    REVISA(b.c.salida == 0);                                                       // contar piezas no mueve relés
    Config h = fabrica(1, 1); REVISA(h.entrada[0].modo == ENT_PULSADOR && h.entrada[0].canal == 1);
  }
  // 5) PLC: los canales del programa no aceptan otras órdenes
  {
    Banco b; b.c.iniciar(fabrica(7, 8), 0, nullptr, 0, false);
    b.c.plcMascara = 1; b.c.plc(1, b.t); REVISA(b.c.salida & 1);
    REVISA(b.c.ordenar(1, 0, OR_BOTON, b.t) == R_PLC && (b.c.salida & 1));
    REVISA(b.c.ordenar(2, 1, OR_BOTON, b.t) == OK);
  }
  // 6) retroalimentación: sin 24 V, bobina abierta y forzado manual (DIP)
  {
    Banco b; b.c.iniciar(fabrica(7, 8), 0, nullptr, 0, false);
    b.c.ordenar(1, 1, OR_RED, b.t); b.c.ordenar(2, 1, OR_RED, b.t);
    b.hay24 = false; b.correr(400); REVISA((b.c.fallas & F_SIN_24V) && !(b.c.fallas & F_BOBINA));
    b.hay24 = true; b.correr(400); REVISA(!(b.c.fallas & (F_SIN_24V | F_BOBINA)));
    b.forzar = 1 << 6; b.correr(400); REVISA(b.c.forzado == 1 << 6 && !(b.c.fallas & F_BOBINA));
    b.forzar = 0; b.correr(50);
    struct Abierta : Banco {} a; a.c.iniciar(fabrica(7, 8), 0, nullptr, 0, false);
    a.c.ordenar(1, 1, OR_RED, 0); a.c.ordenar(2, 1, OR_RED, 0);
    for (int i = 0; i < 100; i++) { a.t += 5; a.c.paso(a.t, 0, 0, a.c.salida & ~1); }   // la bobina 1 no responde
    REVISA((a.c.fallas & F_BOBINA) && a.c.fallaBobina == 1);
  }
  // 7) mantenimiento y límite de escrituras
  {
    Config c = fabrica(7, 8); c.vidaManiobras = 10; c.crc = crcDe(c);
    Banco b; b.c.iniciar(c, 0, nullptr, 0, false);
    for (int i = 0; i < 8; i++) { b.c.ordenar(1, 1, OR_RED, b.t); b.correr(10); b.c.ordenar(1, 0, OR_RED, b.t); b.correr(10); }
    REVISA(b.c.fallas & F_MANTENIMIENTO);
    LimiteEscritura L; int w = 0;
    for (uint32_t t = 0; t < 300000; t += 100) if (L.debeEscribir(t % 1000 == 0, t)) w++;   // cambia cada segundo
    REVISA(w >= 4 && w <= 6);                       // ~1 por minuto en 5 minutos, no 300
  }
  printf(fallas ? "%d FALLAS\n" : "AP Control: todo bien\n", fallas);
  return fallas != 0;
}
