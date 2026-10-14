// AP Control: núcleo común de AP Home (Plug / Switch) y AP Electric Industrial 7R Tour.
// Sin dependencias del hardware: se prueba en la PC (pruebas/prueba_control.cpp). Todo es no bloqueante: paso() se
// llama cada pocos milisegundos con lo leído del hardware y devuelve qué escribir.
//
// Reglas de seguridad funcional (NO es un sistema de seguridad; paro de emergencia y enclavamientos van aparte):
//  - Al arrancar todo queda apagado y después se aplica la política de cada canal:
//    APAGADO (fábrica), ÚLTIMO o ENCENDIDO. Un canal de PROCESO (motor, bomba, máquina) solo admite APAGADO:
//    nunca se reenciende solo tras un corte de energía o de comunicación.
//  - Pérdida de comunicación Modbus (vigilancia > 0 s): los canales que mandaba el maestro pasan a su acción
//    configurada (APAGAR por omisión). Al volver la comunicación no se reenciende nada por sí solo.
//  - El mando manual por hardware (DIP del 7R Tour) no pasa por aquí: el programa solo lo ve como "bobina energizada
//    sin pedido" (forzado) y lo informa.
#pragma once
#include <stdint.h>
#include <string.h>
#include <stddef.h>

namespace apc {

const int MAX_CANALES = 7, MAX_ENTRADAS = 8;
const uint32_t FIRMA = 0x41504331;              // "APC1"
const uint16_t VERSION_CFG = 1;

enum Arranque : uint8_t { ARR_APAGADO = 0, ARR_ULTIMO = 1, ARR_ENCENDIDO = 2 };
enum Carga : uint8_t { CARGA_ALUMBRADO = 0, CARGA_PROCESO = 1 };
enum ModoEntrada : uint8_t { ENT_PULSADOR = 0, ENT_INTERRUPTOR = 1, ENT_CONMUTADOR = 2, ENT_DESACOPLADA = 3 };
enum AccionCom : uint8_t { COM_APAGAR = 0, COM_MANTENER = 1 };
enum Origen : uint8_t { OR_NINGUNO = 0, OR_BOTON, OR_ENTRADA, OR_MODBUS, OR_RED, OR_PLC, OR_TEMPORIZADOR, OR_ARRANQUE,
                        OR_COMUNICACION };
enum Falla : uint16_t { F_CONFIG = 1, F_BOBINA = 2, F_COMUNICACION = 4, F_SIN_24V = 8, F_MANTENIMIENTO = 16,
                        F_VIGILANTE = 32, F_EXPANSOR = 64 };
enum Rechazo : uint8_t { OK = 0, R_CANAL, R_VALOR, R_PLC, R_PROCESO };

struct ConfigCanal { uint8_t arranque, carga, accionCom, libre; uint16_t pulsoS; uint16_t libre2; };
struct ConfigEntrada { uint8_t modo, canal, libre; uint8_t libre2; uint16_t antirreboteMs; uint16_t libre3; };
struct Config {
  uint32_t firma;
  uint16_t version;
  uint8_t nCanales, nEntradas;
  ConfigCanal canal[MAX_CANALES];
  ConfigEntrada entrada[MAX_ENTRADAS];
  uint8_t mbDireccion, mbParidad;
  uint16_t mbVigilanciaS;                      // 0 = sin vigilancia
  uint32_t mbBaudios;
  uint32_t vidaManiobras;                      // aviso de mantenimiento al 80 % (de la hoja del relé)
  uint32_t crc;
};

inline uint32_t crc32(const uint8_t* d, size_t n) {
  uint32_t c = 0xFFFFFFFFu;
  for (size_t i = 0; i < n; i++) {
    c ^= d[i];
    for (int k = 0; k < 8; k++) c = (c >> 1) ^ (0xEDB88320u & (0u - (c & 1)));
  }
  return ~c;
}
inline uint32_t crcDe(const Config& c) { return crc32((const uint8_t*)&c, offsetof(Config, crc)); }

// Valores de fábrica: todo apagado al arrancar. Placa de 1 canal (AP Home): la entrada es pulsador del canal 1.
// Placa de varios canales (7R Tour): entradas DESACOPLADAS; se acoplan a un canal solo a propósito (las entradas cuentan piezas
// o dan andon; que cada pieza haga conmutar un relé gastaría su vida y movería cargas).
inline Config fabrica(uint8_t nCanales, uint8_t nEntradas) {
  Config c;
  memset(&c, 0, sizeof(c));
  c.firma = FIRMA; c.version = VERSION_CFG; c.nCanales = nCanales; c.nEntradas = nEntradas;
  for (int k = 0; k < MAX_CANALES; k++) c.canal[k] = ConfigCanal{ARR_APAGADO, CARGA_ALUMBRADO, COM_APAGAR, 0, 0, 0};
  for (int k = 0; k < MAX_ENTRADAS; k++)
    c.entrada[k] = nCanales > 1 ? ConfigEntrada{ENT_DESACOPLADA, 0, 0, 0, 30, 0}
                                : ConfigEntrada{ENT_PULSADOR, (uint8_t)(k < nCanales ? k + 1 : 0), 0, 0, 30, 0};
  c.mbDireccion = 1; c.mbParidad = 0; c.mbVigilanciaS = 0; c.mbBaudios = 9600;
  c.vidaManiobras = 30000;                     // G2RL-1A-E: 30 000 maniobras a 16 A 250 VCA resistivo (hoja Omron)
  c.crc = crcDe(c);
  return c;
}

// Revisa rangos. Devuelve false si algo estaba mal (lo corrige). Un canal de proceso queda en ARRANQUE APAGADO.
inline bool validar(Config& c) {
  bool ok = c.firma == FIRMA && c.version == VERSION_CFG && c.crc == crcDe(c);
  if (c.nCanales < 1 || c.nCanales > MAX_CANALES) return false;
  if (c.nEntradas > MAX_ENTRADAS) { c.nEntradas = MAX_ENTRADAS; ok = false; }
  for (int k = 0; k < MAX_CANALES; k++) {
    ConfigCanal& x = c.canal[k];
    if (x.carga > CARGA_PROCESO) { x.carga = CARGA_PROCESO; ok = false; }
    if (x.arranque > ARR_ENCENDIDO) { x.arranque = ARR_APAGADO; ok = false; }
    if (x.carga == CARGA_PROCESO && x.arranque != ARR_APAGADO) { x.arranque = ARR_APAGADO; ok = false; }
    if (x.accionCom > COM_MANTENER) { x.accionCom = COM_APAGAR; ok = false; }
    if (x.carga == CARGA_PROCESO && x.accionCom != COM_APAGAR) { x.accionCom = COM_APAGAR; ok = false; }
    if (x.pulsoS > 36000) { x.pulsoS = 0; ok = false; }
  }
  for (int k = 0; k < MAX_ENTRADAS; k++) {
    ConfigEntrada& e = c.entrada[k];
    if (e.modo > ENT_DESACOPLADA) { e.modo = ENT_DESACOPLADA; ok = false; }
    if (e.canal > c.nCanales) { e.canal = 0; ok = false; }
    if (e.antirreboteMs < 5 || e.antirreboteMs > 2000) { e.antirreboteMs = 30; ok = false; }
  }
  if (c.mbDireccion < 1 || c.mbDireccion > 247) { c.mbDireccion = 1; ok = false; }
  if (c.mbParidad > 2) { c.mbParidad = 0; ok = false; }
  if (!(c.mbBaudios == 9600 || c.mbBaudios == 19200 || c.mbBaudios == 38400 || c.mbBaudios == 57600 || c.mbBaudios == 115200)) {
    c.mbBaudios = 9600; ok = false;
  }
  if (c.mbVigilanciaS > 3600) { c.mbVigilanciaS = 0; ok = false; }
  if (c.vidaManiobras == 0) { c.vidaManiobras = 30000; ok = false; }
  c.firma = FIRMA; c.version = VERSION_CFG; c.crc = crcDe(c);
  return ok;
}

struct Evento { uint32_t t; uint8_t tipo, canal, valor, origen; };
enum TipoEvento : uint8_t { EV_ARRANQUE = 1, EV_CANAL, EV_FALLA, EV_FALLA_FIN, EV_COM_PERDIDA, EV_COM_OK, EV_RECHAZO };

class Controlador {
 public:
  Config cfg;
  uint8_t salida = 0;            // lo que se manda a las bobinas
  uint8_t entradas = 0;          // entradas estables (bit = activa)
  uint8_t botones = 0;           // botones estables
  uint8_t bobinas = 0;           // retroalimentación: bobina energizada
  uint8_t forzado = 0;           // bobina energizada sin pedido (DIP manual o falla del excitador)
  uint8_t plcMascara = 0;        // canales que manda el programa PLC (si está en RUN)
  uint8_t deModbus = 0;          // canales cuyo último mando fue del maestro Modbus
  uint8_t origen[MAX_CANALES] = {};
  uint16_t fallas = 0;
  uint32_t maniobras[MAX_CANALES] = {};
  bool comPerdida = false, hayRetro = true, sin24V = false;
  bool guardarEstado = false;    // el último estado cambió y conviene guardarlo (con límite de escrituras)
  bool guardarManiobras = false;

  Evento ev[32];
  uint8_t nEv = 0, sigEv = 0;

  void iniciar(const Config& c, uint8_t ultimo, const uint32_t* maniobrasGuardadas, uint32_t ahora, bool vigilanteDisparo) {
    cfg = c;
    if (!validar(cfg)) fallas |= F_CONFIG;
    if (maniobrasGuardadas) memcpy(maniobras, maniobrasGuardadas, sizeof(maniobras));
    if (vigilanteDisparo) fallas |= F_VIGILANTE;
    salida = 0;
    for (int k = 0; k < cfg.nCanales; k++) {
      bool on = false;
      if (cfg.canal[k].carga == CARGA_ALUMBRADO) {
        if (cfg.canal[k].arranque == ARR_ENCENDIDO) on = true;
        if (cfg.canal[k].arranque == ARR_ULTIMO) on = ultimo & (1 << k);
      }
      if (on) { salida |= 1 << k; origen[k] = OR_ARRANQUE; tFin[k] = cfg.canal[k].pulsoS ? ahora + cfg.canal[k].pulsoS * 1000u : 0; }
    }
    anterior = salida;
    for (int k = 0; k < MAX_ENTRADAS; k++) { crudoAnt[k] = false; tCambio[k] = ahora; }
    for (int k = 0; k < MAX_CANALES; k++) { btnAnt[k] = false; tBtn[k] = ahora; tRetro[k] = ahora; }
    tModbus = 0; tEstado = ahora;
    evento(ahora, EV_ARRANQUE, 0, salida, OR_ARRANQUE);
  }

  // Orden de una fuente (botón, entrada, Modbus, red). valor: 0 apagar, 1 encender, 2 alternar.
  Rechazo ordenar(int canal, int valor, Origen o, uint32_t ahora) {
    if (canal < 1 || canal > cfg.nCanales) return R_CANAL;
    if (valor < 0 || valor > 2) return R_VALOR;
    int k = canal - 1;
    if ((plcMascara & (1 << k)) && o != OR_PLC) { evento(ahora, EV_RECHAZO, canal, valor, o); return R_PLC; }
    bool on = valor == 2 ? !(salida & (1 << k)) : valor == 1;
    poner(k, on, o, ahora);
    return OK;
  }

  // «Maestro presente»: se llama con CUALQUIER trama Modbus válida dirigida a este equipo (lecturas incluidas), no solo con escrituras.
  void modbusEscribio(uint32_t ahora) {
    tModbus = ahora ? ahora : 1;
    if (comPerdida) { comPerdida = false; fallas &= ~F_COMUNICACION; evento(ahora, EV_COM_OK, 0, 0, OR_MODBUS); }
  }

  // Lo que manda el programa PLC (solo los bits de plcMascara)
  void plc(uint8_t q, uint32_t ahora) {
    for (int k = 0; k < cfg.nCanales; k++)
      if (plcMascara & (1 << k)) poner(k, q & (1 << k), OR_PLC, ahora);
  }

  // Un paso: entradas y botones crudos (bit = activo), bobinas leídas (bit = energizada), hayRetro = la placa la tiene.
  void paso(uint32_t ahora, uint8_t entCrudas, uint8_t btnCrudos, uint8_t bobinasLeidas) {
    // entradas con antirrebote
    for (int k = 0; k < cfg.nEntradas; k++) {
      bool v = entCrudas & (1 << k);
      if (v != crudoAnt[k]) { crudoAnt[k] = v; tCambio[k] = ahora; }
      bool estable = entradas & (1 << k);
      if (v != estable && ahora - tCambio[k] >= cfg.entrada[k].antirreboteMs) {
        if (v) entradas |= 1 << k; else entradas &= ~(1 << k);
        aplicarEntrada(k, v, ahora);
      }
    }
    // botones de canal: 30 ms, al presionar alternan su canal
    for (int k = 0; k < cfg.nCanales; k++) {
      bool v = btnCrudos & (1 << k);
      if (v != btnAnt[k]) { btnAnt[k] = v; tBtn[k] = ahora; }
      bool est = botones & (1 << k);
      if (v != est && ahora - tBtn[k] >= 30) {
        if (v) { botones |= 1 << k; ordenar(k + 1, 2, OR_BOTON, ahora); } else botones &= ~(1 << k);
      }
    }
    // temporizador de apagado (escalera, pulso)
    for (int k = 0; k < cfg.nCanales; k++)
      if (tFin[k] && (int32_t)(ahora - tFin[k]) >= 0 && (salida & (1 << k))) poner(k, false, OR_TEMPORIZADOR, ahora);
    // vigilancia de la comunicación Modbus
    if (cfg.mbVigilanciaS && tModbus && !comPerdida && ahora - tModbus > cfg.mbVigilanciaS * 1000u) {
      comPerdida = true; fallas |= F_COMUNICACION;
      evento(ahora, EV_COM_PERDIDA, 0, deModbus, OR_COMUNICACION);
      for (int k = 0; k < cfg.nCanales; k++)
        if ((deModbus & (1 << k)) && cfg.canal[k].accionCom == COM_APAGAR) poner(k, false, OR_COMUNICACION, ahora);
    }
    // retroalimentación de las bobinas (si la placa la tiene)
    bobinas = bobinasLeidas;
    if (hayRetro) {
      uint8_t f = 0, nuevoForzado = 0;
      for (int k = 0; k < cfg.nCanales; k++) {
        bool pedido = salida & (1 << k), real = bobinas & (1 << k);
        if (pedido == real) { tRetro[k] = ahora; continue; }
        if (ahora - tRetro[k] < 300) continue;                   // el relé tarda unos ms; se espera 300 ms
        if (pedido && !real) f |= 1 << k;
        if (!pedido && real) nuevoForzado |= 1 << k;
      }
      forzado = nuevoForzado;
      bool todos = f && (f == (salida & ((1 << cfg.nCanales) - 1)));   // ninguna bobina pedida tiene tensión
      sin24V = todos && !bobinas;
      marcar(F_BOBINA, f && !sin24V, ahora);
      marcar(F_SIN_24V, sin24V, ahora);
      fallaBobina = f;
    }
    // mantenimiento
    bool mant = false;
    for (int k = 0; k < cfg.nCanales; k++) if (maniobras[k] >= cfg.vidaManiobras / 5 * 4) mant = true;
    marcar(F_MANTENIMIENTO, mant, ahora);
  }

  uint8_t fallaBobina = 0;
  uint32_t eventos() const { return nEv; }

 private:
  uint8_t anterior = 0;
  bool crudoAnt[MAX_ENTRADAS] = {}, btnAnt[MAX_CANALES] = {};
  uint32_t tCambio[MAX_ENTRADAS] = {}, tBtn[MAX_CANALES] = {}, tRetro[MAX_CANALES] = {}, tFin[MAX_CANALES] = {};
  uint32_t tModbus = 0, tEstado = 0;

  void evento(uint32_t t, uint8_t tipo, uint8_t canal, uint8_t valor, uint8_t o) {
    ev[sigEv] = Evento{t, tipo, canal, valor, o};
    sigEv = (sigEv + 1) % 32; if (nEv < 32) nEv++;
  }
  void marcar(uint16_t f, bool activa, uint32_t t) {
    bool era = fallas & f;
    if (activa && !era) { fallas |= f; evento(t, EV_FALLA, 0, (uint8_t)f, 0); }
    if (!activa && era) { fallas &= ~f; evento(t, EV_FALLA_FIN, 0, (uint8_t)f, 0); }
  }
  void poner(int k, bool on, Origen o, uint32_t ahora) {
    uint8_t b = 1 << k;
    bool era = salida & b;
    if (o == OR_MODBUS) deModbus |= b; else if (o != OR_COMUNICACION && o != OR_TEMPORIZADOR) deModbus &= ~b;
    origen[k] = o;
    if (on == era) { if (on && cfg.canal[k].pulsoS) tFin[k] = ahora + cfg.canal[k].pulsoS * 1000u; return; }  // re-disparo
    if (on) {
      salida |= b; maniobras[k]++; guardarManiobras = true;
      tFin[k] = cfg.canal[k].pulsoS ? ahora + cfg.canal[k].pulsoS * 1000u : 0;
    } else { salida &= ~b; tFin[k] = 0; }
    tRetro[k] = ahora;
    guardarEstado = true;
    evento(ahora, EV_CANAL, k + 1, on, o);
  }
  void aplicarEntrada(int k, bool activa, uint32_t ahora) {
    const ConfigEntrada& e = cfg.entrada[k];
    if (!e.canal) return;
    switch (e.modo) {
      case ENT_PULSADOR: if (activa) ordenar(e.canal, 2, OR_ENTRADA, ahora); break;
      case ENT_INTERRUPTOR: ordenar(e.canal, activa ? 1 : 0, OR_ENTRADA, ahora); break;
      case ENT_CONMUTADOR: ordenar(e.canal, 2, OR_ENTRADA, ahora); break;   // apagadores de escalera: cada cambio alterna
      default: break;
    }
  }
};

// Límite de escrituras a la memoria: el último estado se guarda 10 s después del último cambio y como máximo una vez
// por minuto; las maniobras, una vez por hora. Si la energía falla dentro de esa ventana, se pierde el último cambio.
struct LimiteEscritura {
  uint32_t tPedido = 0, tPrimero = 0, tUltima = 0; bool pendiente = false; uint32_t escrituras = 0;
  // Escribe 10 s después del último cambio, o al minuto de cambios seguidos; nunca más de una vez por minuto.
  bool debeEscribir(bool cambio, uint32_t ahora, uint32_t quieto = 10000, uint32_t minimo = 60000) {
    if (cambio) { if (!pendiente) tPrimero = ahora; pendiente = true; tPedido = ahora; }
    if (!pendiente) return false;
    bool listo = ahora - tPedido >= quieto || ahora - tPrimero >= minimo;
    if (listo && (escrituras == 0 || ahora - tUltima >= minimo)) {
      pendiente = false; tUltima = ahora; escrituras++; return true;
    }
    return false;
  }
};

}  // namespace apc
