// Pruebas en la PC de la unidad PackML (unidad_packml.h) y de sus registros Modbus (PackTags v1).
#include "../APControl/ap_control.h"
#include "../APControl/unidad_packml.h"
#include "../APControl/modbus_esclavo.h"
#include "../APControl/logica.h"
#include <cstdio>
#include <cmath>
#include <vector>
using namespace apc;
static int fallas = 0;
#define REVISA(c) do { if (!(c)) { printf("  falla en la línea %d: %s\n", __LINE__, #c); fallas++; } } while (0)

struct Banco {
  UnidadPackML u; uint32_t t = 1000;
  Banco() { u.iniciar(t); }
  void correr(uint32_t ms) { for (uint32_t i = 0; i < ms; i += 10) { t += 10; u.paso(t); } }
  bool cmd(uint8_t c, uint8_t o = OR_BOTON) { return u.comando(c, o, t); }
  // lleva la unidad a EXECUTE por el camino normal
  void aExecute() { REVISA(cmd(CK_RESET)); correr(30); REVISA(u.estado == PK_IDLE); REVISA(cmd(CK_START)); correr(30); REVISA(u.estado == PK_EXECUTE); }
};
static std::vector<uint8_t> trama(std::vector<uint8_t> q) { uint16_t k = crc16(q.data(), q.size()); q.push_back(k & 0xFF); q.push_back(k >> 8); return q; }
static std::vector<uint8_t> pedir(Esclavo& e, std::vector<uint8_t> q, uint32_t t) {
  auto f = trama(q); uint8_t r[260]; size_t n = e.procesar(f.data(), f.size(), r, t); return std::vector<uint8_t>(r, r + n);
}
static uint16_t leer(Esclavo& e, uint8_t fn, uint16_t a, uint32_t t) {
  auto r = pedir(e, {1, fn, (uint8_t)(a >> 8), (uint8_t)a, 0, 1}, t);
  return r.size() >= 5 && r[1] == fn ? (r[3] << 8 | r[4]) : 0xDEAD;
}
static int bit(Esclavo& e, uint16_t a, uint32_t t) {                      // entrada discreta; -1 = excepción
  auto r = pedir(e, {1, 2, (uint8_t)(a >> 8), (uint8_t)a, 0, 1}, t);
  return r.size() >= 4 && r[1] == 2 ? (r[3] & 1) : -1;
}
static uint8_t escribir(Esclavo& e, uint16_t a, uint16_t v, uint32_t t) {   // 0 = bien; si no, la excepción
  auto r = pedir(e, {1, 6, (uint8_t)(a >> 8), (uint8_t)a, (uint8_t)(v >> 8), (uint8_t)v}, t);
  return r.size() >= 3 && (r[1] & 0x80) ? r[2] : 0;
}

int main() {
  // 1) arranca en STOPPED y recorre el ciclo normal: Reset > Idle > Start > Execute > Complete > Reset
  {
    Banco b;
    REVISA(b.u.estado == PK_STOPPED && b.u.modo == MK_PRODUCCION);
    REVISA(!b.u.procesoHabilitado());
    REVISA(!b.cmd(CK_START));                         // desde STOPPED no se puede arrancar
    REVISA(b.cmd(CK_RESET)); REVISA(b.u.estado == PK_RESETTING);
    b.correr(30); REVISA(b.u.estado == PK_IDLE);
    REVISA(b.cmd(CK_START)); REVISA(b.u.estado == PK_STARTING);
    b.correr(30); REVISA(b.u.estado == PK_EXECUTE && b.u.procesoHabilitado());
    REVISA(b.u.completar(b.t)); REVISA(b.u.estado == PK_COMPLETING);
    b.correr(30); REVISA(b.u.estado == PK_COMPLETE);
    REVISA(b.cmd(CK_RESET)); b.correr(30); REVISA(b.u.estado == PK_IDLE);
  }
  // 2) hold, suspend y stop; comandos inválidos
  {
    Banco b; b.aExecute();
    REVISA(!b.cmd(CK_UNHOLD));                        // no está en HELD
    REVISA(b.cmd(CK_HOLD)); b.correr(30); REVISA(b.u.estado == PK_HELD && !b.u.procesoHabilitado());
    REVISA(b.cmd(CK_UNHOLD)); b.correr(30); REVISA(b.u.estado == PK_EXECUTE);
    REVISA(b.cmd(CK_SUSPEND)); b.correr(30); REVISA(b.u.estado == PK_SUSPENDED);
    REVISA(!b.cmd(CK_HOLD));                          // HOLD solo desde EXECUTE
    REVISA(b.cmd(CK_UNSUSPEND)); b.correr(30); REVISA(b.u.estado == PK_EXECUTE);
    REVISA(b.cmd(CK_STOP)); REVISA(b.u.estado == PK_STOPPING); b.correr(30); REVISA(b.u.estado == PK_STOPPED);
    REVISA(!b.cmd(CK_NADA)); REVISA(!b.cmd(200));
  }
  // 3) abort: desde casi todo, CLEAR solo desde ABORTED
  {
    Banco b; b.aExecute();
    REVISA(!b.cmd(CK_CLEAR));
    REVISA(b.cmd(CK_ABORT)); REVISA(b.u.estado == PK_ABORTING);
    REVISA(!b.cmd(CK_ABORT));                         // ya abortando
    b.correr(30); REVISA(b.u.estado == PK_ABORTED);
    REVISA(!b.cmd(CK_RESET) && !b.cmd(CK_START));
    REVISA(b.cmd(CK_CLEAR)); REVISA(b.u.estado == PK_CLEARING); b.correr(30); REVISA(b.u.estado == PK_STOPPED);
  }
  // 4) el estado "actuando" puede esperar a la aplicación (por ejemplo el motor a velocidad)
  {
    Banco b; b.u.esperarAplicacion(PK_STARTING);
    REVISA(b.cmd(CK_RESET)); b.correr(30); REVISA(b.cmd(CK_START)); b.correr(500); REVISA(b.u.estado == PK_STARTING);
    REVISA(b.u.completar(b.t)); REVISA(b.u.estado == PK_EXECUTE);
  }
  // 5) modo: solo en STOPPED o ABORTED; mantenimiento y manual no usan suspender ni ciclo completo
  {
    Banco b;
    REVISA(b.u.cambiarModo(MK_MANTENIMIENTO, b.t) && b.u.modo == MK_MANTENIMIENTO);
    REVISA(!b.u.cambiarModo(9, b.t) && !b.u.cambiarModo(0, b.t));
    b.aExecute();
    REVISA(!b.u.cambiarModo(MK_PRODUCCION, b.t));     // en EXECUTE no se cambia el modo
    REVISA(!b.cmd(CK_SUSPEND)); REVISA(!b.u.completar(b.t));
    REVISA(b.cmd(CK_HOLD));                           // la retención sí está
    b.cmd(CK_ABORT); b.correr(30); REVISA(b.u.estado == PK_ABORTED); REVISA(b.u.cambiarModo(MK_PRODUCCION, b.t));
  }
  // 6) origen remoto: parar, retener y abortar siempre; lo que reanuda, no (salvo permiso local)
  {
    Banco b; b.aExecute();
    REVISA(b.cmd(CK_HOLD, OR_MODBUS)); b.correr(30); REVISA(b.u.estado == PK_HELD);
    REVISA(!b.cmd(CK_UNHOLD, OR_MODBUS) && b.u.estado == PK_HELD);
    REVISA(!b.cmd(CK_UNHOLD, OR_RED));
    REVISA(b.cmd(CK_UNHOLD, OR_PLC)); b.correr(30); REVISA(b.u.estado == PK_EXECUTE);   // local sí
    REVISA(b.cmd(CK_STOP, OR_RED)); b.correr(30); REVISA(b.u.estado == PK_STOPPED);
    REVISA(!b.cmd(CK_RESET, OR_MODBUS));
    b.u.cfg.remotoReanuda = true;
    REVISA(b.cmd(CK_RESET, OR_MODBUS)); b.correr(30); REVISA(b.cmd(CK_START, OR_MODBUS));
  }
  // 7) fallas: grave = ABORT; leve = HOLD solo en EXECUTE; CLEAR bloqueado mientras la falla siga
  {
    Banco b; b.aExecute();
    b.u.alFalla(F_BOBINA, b.t); b.correr(30);
    REVISA(b.u.estado == PK_HELD && b.u.motivo / 100 == CP_AVERIA);
    b.u.alFalla(F_BOBINA | F_SIN_24V, b.t); b.correr(30);
    REVISA(b.u.estado == PK_ABORTED); REVISA(b.u.motivo == CP_AVERIA * 100 + 4);      // bit 3 de las fallas = causa 4
    REVISA(!b.cmd(CK_CLEAR));                         // la falla sigue
    b.u.alFalla(F_BOBINA, b.t);                       // se fue SIN_24V
    REVISA(b.cmd(CK_CLEAR)); b.correr(30); REVISA(b.u.estado == PK_STOPPED);
    REVISA(b.cmd(CK_RESET)); b.correr(30); REVISA(b.u.estado == PK_IDLE);
    // comunicación perdida en EXECUTE = HOLD por causa externa
    Banco c; c.aExecute(); c.u.alFalla(F_COMUNICACION, c.t); c.correr(30);
    REVISA(c.u.estado == PK_HELD && c.u.motivo / 100 == CP_EXTERNA);
    // la misma falla en IDLE no pide nada
    Banco d; d.cmd(CK_RESET); d.correr(30); d.u.alFalla(F_COMUNICACION, d.t); d.correr(30); REVISA(d.u.estado == PK_IDLE);
    // reinicio por vigilante: ABORT al arrancar, pero el CLEAR sí se acepta
    Banco e; e.u.alFalla(F_VIGILANTE, e.t); e.correr(30);
    REVISA(e.u.estado == PK_ABORTED); REVISA(e.cmd(CK_CLEAR));
  }
  // 8) tiempos por estado y OEE
  {
    Banco b; b.u.cfg.cicloNominalMs = 1000;
    b.aExecute();
    REVISA(b.u.disponibilidad() == 1000);
    b.correr(60000);                                  // 60 s en EXECUTE
    for (int i = 0; i < 50; i++) { b.correr(1000); REVISA(b.u.contar(i % 10 != 0, b.t)); }  // 50 piezas, 5 malas, en 50 s
    REVISA(b.u.procesadas == 50 && b.u.defectuosas == 5);
    b.cmd(CK_HOLD); b.correr(30); b.correr(40000);    // 40 s detenido
    REVISA(b.u.estado == PK_HELD);
    uint32_t exe = b.u.segundosEn(PK_EXECUTE), held = b.u.segundosEn(PK_HELD);
    REVISA(exe >= 109 && exe <= 111); REVISA(held >= 39 && held <= 41);
    REVISA(b.u.disponibilidad() > 700 && b.u.disponibilidad() < 760);     // ~110/(110+40) = 733
    REVISA(b.u.calidad() == 900);
    REVISA(b.u.desempeno() > 400 && b.u.desempeno() < 500);                // 50 piezas x 1 s en 110 s
    uint32_t oee = (uint32_t)b.u.disponibilidad() * b.u.desempeno() / 1000 * b.u.calidad() / 1000;
    REVISA(b.u.oee() == oee);
    Banco c; REVISA(c.u.disponibilidad() == 0xFFFF && c.u.desempeno() == 0xFFFF && c.u.calidad() == 0xFFFF && c.u.oee() == 0xFFFF);
  }
  // 9) piezas solo en EXECUTE; microparo = sin piezas más de 3 ciclos (mínimo 2 s)
  {
    Banco b; b.u.cfg.cicloNominalMs = 1000;
    REVISA(!b.u.contar(true, b.t));                   // STOPPED
    b.aExecute();
    REVISA(b.u.contar(true, b.t));
    b.correr(1500); REVISA(!b.u.microparo);
    b.correr(2000); REVISA(b.u.microparo && b.u.microMs > 0);
    REVISA(b.u.contar(true, b.t) && !b.u.microparo);
    Banco c; c.aExecute(); c.correr(60000); REVISA(!c.u.microparo);        // sin ciclo nominal no hay microparos
  }
  // 10) bitácora: anota transiciones y rechazos
  {
    Banco b; b.cmd(CK_START); b.cmd(CK_RESET);
    REVISA(b.u.nEv == 2);
    REVISA(b.u.ev[0].de == PK_STOPPED && b.u.ev[0].a == PK_STOPPED && b.u.ev[0].cmd == CK_START);   // rechazo
    REVISA(b.u.ev[1].a == PK_RESETTING);
    for (int i = 0; i < 40; i++) { b.cmd(CK_STOP); }
    REVISA(b.u.nEv == 16);
  }
  // 11) Modbus: PackTags v1
  {
    Config c = fabrica(7, 8); c.mbDireccion = 1; c.crc = crcDe(c);
    Controlador ctl; ctl.iniciar(c, 0, nullptr, 0, false);
    uint32_t seg = 0; Esclavo mb(ctl, 100, 1, &seg);
    UnidadPackML u; u.iniciar(1000); u.cfg.cicloNominalMs = 500;
    // sin unidad: los registros no existen
    REVISA(leer(mb, 4, 101, 0) == 0xDEAD && escribir(mb, 300, 2, 0) == 2);
    mb.um = &u;
    uint32_t t = 1000;
    auto correr = [&](uint32_t ms) { for (uint32_t i = 0; i < ms; i += 10) { t += 10; u.paso(t); } };
    REVISA(leer(mb, 4, 100, t) == 1 && leer(mb, 4, 101, t) == PK_STOPPED && leer(mb, 4, 102, t) == MK_PRODUCCION);
    REVISA(bit(mb, 49, t) == 0 && bit(mb, 48, t) == 0 && bit(mb, 50, t) == 0 && bit(mb, 51, t) == -1);
    // el maestro no puede reanudar: RESET por Modbus se rechaza con la excepción 04
    REVISA(escribir(mb, 300, CK_RESET, t) == 4 && u.estado == PK_STOPPED);
    REVISA(escribir(mb, 300, 99, t) == 3);
    REVISA(escribir(mb, 305, 1, t) == 2);             // no puede darse permiso a sí mismo
    REVISA(leer(mb, 3, 305, t) == 0);
    // con permiso local sí
    u.cfg.remotoReanuda = true; REVISA(leer(mb, 3, 305, t) == 1);
    REVISA(escribir(mb, 300, CK_RESET, t) == 0); correr(30); REVISA(leer(mb, 4, 101, t) == PK_IDLE);
    REVISA(escribir(mb, 300, CK_START, t) == 0); correr(30); REVISA(leer(mb, 4, 101, t) == PK_EXECUTE);
    REVISA(leer(mb, 3, 300, t) == CK_START);
    REVISA(escribir(mb, 303, 1, t) == 0 && escribir(mb, 303, 2, t) == 0 && escribir(mb, 303, 3, t) == 3);
    REVISA(leer(mb, 4, 105, t) == 2 && leer(mb, 4, 107, t) == 1);
    REVISA(escribir(mb, 302, 301, t) == 0 && leer(mb, 4, 103, t) == 301 && escribir(mb, 302, 1000, t) == 3);
    REVISA(escribir(mb, 304, 750, t) == 0 && u.cfg.cicloNominalMs == 750);
    correr(5000);
    REVISA(leer(mb, 4, 110 + 2 * (PK_EXECUTE - 1), t) >= 4);          // segundos en EXECUTE
    REVISA(leer(mb, 4, 153, t) != 0xDEAD && leer(mb, 4, 152, t) == 500);
    REVISA(escribir(mb, 300, CK_HOLD, t) == 0); correr(30);
    REVISA(leer(mb, 4, 101, t) == PK_HELD);
    REVISA(bit(mb, 49, t) == 0);
    REVISA(escribir(mb, 300, CK_UNHOLD, t) == 0);     // remotoReanuda activo
    u.cfg.remotoReanuda = false; correr(30);
    REVISA(escribir(mb, 300, CK_HOLD, t) == 0);       // retener siempre se acepta
    correr(30); REVISA(escribir(mb, 300, CK_UNHOLD, t) == 4);
    REVISA(escribir(mb, 301, MK_MANUAL, t) == 4);     // en HELD no se cambia el modo
    REVISA(escribir(mb, 300, CK_ABORT, t) == 0); correr(30); REVISA(leer(mb, 4, 101, t) == PK_ABORTED);
    REVISA(escribir(mb, 301, MK_MANTENIMIENTO, t) == 0 && leer(mb, 3, 301, t) == MK_MANTENIMIENTO);
    REVISA(leer(mb, 4, 157, t) == 0xDEAD);            // fuera del mapa
  }
  // 13) entradas de la máquina: ciclo, mala, andon y reanudar; una entrada, una función
  {
    Banco b;
    ConfigMonitor m = b.u.mon; m.entCiclo = 1; m.entMala = 2; m.entAndon = 3; m.entReanuda = 4; m.cicloNominalMs = 800; m.modo = MK_PRODUCCION;
    REVISA(b.u.configurarMonitor(m, 8) && b.u.cfg.cicloNominalMs == 800);
    b.u.entradas(0x01, b.t);                          // la entrada 1 ya estaba activa al arrancar: no cuenta
    b.correr(30); b.u.entradas(0x01, b.t); REVISA(b.u.procesadas == 0);
    b.u.entradas(0, b.t);
    b.aExecute();
    auto pulso = [&](uint8_t bit) { b.u.entradas(bit, b.t); b.correr(30); b.u.entradas(0, b.t); b.correr(30); };
    pulso(0x01); pulso(0x01); pulso(0x02);
    REVISA(b.u.procesadas == 3 && b.u.defectuosas == 1);
    pulso(0x08);                                      // reanudar sin estar en HOLD: se ignora
    REVISA(b.u.estado == PK_EXECUTE);
    pulso(0x04);                                      // andon
    REVISA(b.u.estado == PK_HELD && b.u.motivo == MOTIVO_ANDON);
    pulso(0x01); REVISA(b.u.procesadas == 3);         // en HELD no se cuentan piezas
    pulso(0x08);                                      // el botón junto a la máquina reanuda (origen local)
    REVISA(b.u.estado == PK_EXECUTE);
    bool desdeEntrada = false;                        // la bitácora anotó el UNHOLD con origen de entrada
    for (int i = 0; i < b.u.nEv; i++) if (b.u.ev[i].cmd == CK_UNHOLD && b.u.ev[i].origen == OR_ENTRADA) desdeEntrada = true;
    REVISA(desdeEntrada);
    // una entrada con dos funciones, o fuera de rango, no se acepta y deja todo como estaba
    ConfigMonitor malo = b.u.mon; malo.entMala = 1;
    REVISA(!b.u.configurarMonitor(malo, 8) && b.u.mon.entMala == 2);
    malo = b.u.mon; malo.entCiclo = 9; REVISA(!b.u.configurarMonitor(malo, 8));
    malo = b.u.mon; malo.entCiclo = 5; REVISA(!b.u.configurarMonitor(malo, 4));      // AP Home solo tiene 1 entrada
    malo = b.u.mon; malo.modo = 7; REVISA(!b.u.configurarMonitor(malo, 8));
  }
  // 14) memoria: se carga solo con firma y CRC buenos; contadores con tope lógico
  {
    Banco b; b.u.cfg.cicloNominalMs = 1200; b.u.cambiarModo(MK_MANTENIMIENTO, b.t);
    ConfigMonitor m = b.u.mon; m.entCiclo = 2; REVISA(b.u.configurarMonitor(m, 8));
    b.u.cfg.cicloNominalMs = 1200;
    ConfigMonitor g = b.u.paraGuardar();
    REVISA(g.cicloNominalMs == 1200 && g.modo == MK_MANTENIMIENTO && g.entCiclo == 2);
    Banco c;
    REVISA(c.u.cargarMonitor(g, 8) && c.u.mon.entCiclo == 2 && c.u.cfg.cicloNominalMs == 1200 && c.u.modo == MK_MANTENIMIENTO);
    ConfigMonitor roto = g; roto.entMala = 7;           // cambia sin recalcular el CRC
    Banco d; REVISA(!d.u.cargarMonitor(roto, 8) && d.u.mon.entCiclo == 0);
    ConfigMonitor sinFirma = g; sinFirma.firma = 0; REVISA(!d.u.cargarMonitor(sinFirma, 8));
    Banco e; e.u.restaurarContadores(100, 7); REVISA(e.u.procesadas == 100 && e.u.defectuosas == 7);
    e.u.restaurarContadores(5, 9); REVISA(e.u.procesadas == 100);                  // más malas que buenas: se ignora
    // el modo de la memoria solo se aplica si la unidad está detenida
    Banco f; f.aExecute(); REVISA(f.u.cargarMonitor(g, 8) && f.u.modo == MK_PRODUCCION);
    Banco h; h.aExecute(); h.u.contadoresCambiaron = false; h.u.contar(true, h.t); REVISA(h.u.contadoresCambiaron);
  }
  // 15) Modbus: función de cada entrada
  {
    Config c = fabrica(7, 8); c.mbDireccion = 1; c.crc = crcDe(c);
    Controlador ctl; ctl.iniciar(c, 0, nullptr, 0, false);
    uint32_t seg = 0; Esclavo mb(ctl, 100, 1, &seg);
    UnidadPackML u; u.iniciar(0); mb.um = &u;
    REVISA(escribir(mb, 306, 1, 0) == 0 && escribir(mb, 307, 2, 0) == 0 && escribir(mb, 308, 3, 0) == 0 && escribir(mb, 309, 4, 0) == 0);
    REVISA(leer(mb, 3, 306, 0) == 1 && leer(mb, 3, 309, 0) == 4 && u.mon.entAndon == 3);
    REVISA(escribir(mb, 307, 1, 0) == 3 && leer(mb, 3, 307, 0) == 2);              // repetida
    REVISA(escribir(mb, 308, 9, 0) == 3 && escribir(mb, 308, 300, 0) == 3);        // fuera de rango
    REVISA(escribir(mb, 308, 0, 0) == 0 && leer(mb, 3, 308, 0) == 0);              // quitar la función
  }
  // 12) PLC: los estados PackML se leen como bits del área S (S10 + estado)
  {
    struct Ent : logica::Entorno {
      UnidadPackML* u;
      bool leerBit(char a, int i) override { return a == 'S' && i >= 10 && i < 10 + PK_N && u->estado == i - 10; }
      float valor(char, int) override { return NAN; }
      void escribir(char, int, bool) override {}
    } e;
    UnidadPackML u; u.iniciar(0); e.u = &u;
    logica::Programa p;
    char src[64]; snprintf(src, sizeof(src), "LD S%d\nOUT M1\nLD S%d\nOUT M2", 10 + PK_STOPPED, 10 + PK_EXECUTE);
    REVISA(p.compilar(src));
    p.ciclo(e, 10); REVISA(p.m[1] && !p.m[2]);
  }
  printf(fallas ? "%d FALLAS\n" : "AP Control PackML: todo bien\n", fallas);
  return fallas != 0;
}
