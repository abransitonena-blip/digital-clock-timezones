// AP Control: unidad con modelo de estados tipo PackML (OMAC / ANSI/ISA-TR88.00.02) para OEE, andon y poka-yoke.
// Sin dependencias del hardware: se prueba en la PC (pruebas/prueba_packml.cpp).
//
// QUÉ ES Y QUÉ NO ES
//  - Es una tabla propia de transiciones (estado x comando) con tiempos por estado, causas de paro, contadores y OEE.
//  - Los números de estado y de comando, y qué estados quedan habilitados por modo, son una IMPLEMENTACIÓN PROPUESTA
//    tomada de conocimiento general: falta confirmarlos con el texto oficial de ISA-TR88.00.02-2022 u OMAC.
//  - NO es una función de seguridad. Paro de emergencia y guardas van a un relé de seguridad. Esta unidad solo informa el
//    estado y puede pedir paro o retención ante fallas; no rearma nada que haya parado por falla.
//  - Reglas que se cuidan aquí:
//      * Arranca en STOPPED (nada se reanuda solo tras un corte de energía).
//      * Desde Modbus o la red, PARAR, RETENER y ABORTAR siempre se aceptan; los comandos que reanudan (RESET, START,
//        UNHOLD, UNSUSPEND, CLEAR) se rechazan salvo que se habilite `remotoReanuda` (apagado de fábrica).
//      * Con una falla que causó ABORT todavía activa no se acepta CLEAR, RESET ni START. La del vigilante (reinicio
//        por watchdog) no bloquea: pide ABORT al arrancar y hace falta un CLEAR explícito.
//      * El modo solo cambia en STOPPED o ABORTED.
#pragma once
#include "ap_control.h"
#include "reloj.h"

namespace apc {

// Numeración propuesta [conocimiento general]. 0 = ninguno.
enum EstadoPK : uint8_t {
  PK_NINGUNO = 0, PK_CLEARING = 1, PK_STOPPED = 2, PK_STARTING = 3, PK_IDLE = 4, PK_SUSPENDED = 5, PK_EXECUTE = 6,
  PK_STOPPING = 7, PK_ABORTING = 8, PK_ABORTED = 9, PK_HOLDING = 10, PK_HELD = 11, PK_UNHOLDING = 12, PK_SUSPENDING = 13,
  PK_UNSUSPENDING = 14, PK_RESETTING = 15, PK_COMPLETING = 16, PK_COMPLETE = 17, PK_N = 18
};
enum ComandoPK : uint8_t {
  CK_NADA = 0, CK_RESET = 1, CK_START = 2, CK_STOP = 3, CK_HOLD = 4, CK_UNHOLD = 5, CK_SUSPEND = 6, CK_UNSUSPEND = 7,
  CK_ABORT = 8, CK_CLEAR = 9, CK_N = 10
};
enum ModoPK : uint8_t { MK_PRODUCCION = 1, MK_MANTENIMIENTO = 2, MK_MANUAL = 3 };

// Causa de paro = categoria * 100 + causa (0-99). Las categorías siguen las 6 grandes pérdidas [conocimiento general].
enum CategoriaParo : uint8_t {
  CP_NINGUNA = 0, CP_AVERIA = 1, CP_CAMBIO = 2, CP_MICROPARO = 3, CP_VELOCIDAD = 4, CP_DEFECTOS = 5, CP_ARRANQUE = 6,
  CP_PLANEADO = 7, CP_EXTERNA = 8
};

inline bool esActuando(uint8_t e) {
  return e == PK_CLEARING || e == PK_STARTING || e == PK_STOPPING || e == PK_ABORTING || e == PK_HOLDING ||
         e == PK_UNHOLDING || e == PK_SUSPENDING || e == PK_UNSUSPENDING || e == PK_RESETTING || e == PK_COMPLETING;
}

// Qué hace cada entrada de la máquina (1-8; 0 = no se usa). Se guarda en memoria con la orden de guardar.
//   ciclo: cada flanco de subida cuenta una pieza buena · mala: cuenta una pieza defectuosa · andon: pide HOLD con la causa
//   «llamado de andon» · reanuda: botón junto a la máquina que sale de HOLD (origen local).
const uint16_t MOTIVO_ANDON = CP_AVERIA * 100 + 90;      // causa 190 = llamado de andon
struct ConfigMonitor {
  uint32_t firma;
  uint8_t entCiclo, entMala, entAndon, entReanuda;
  uint16_t cicloNominalMs; uint8_t modo, libre;
  uint32_t crc;
};
const uint32_t FIRMA_MONITOR = 0x41504D31;      // "APM1"

struct ConfigPK {
  uint16_t cicloNominalMs = 0;      // 0 = sin ciclo nominal: no se calcula el desempeño ni los microparos
  uint16_t abortarCon = F_SIN_24V | F_VIGILANTE | F_EXPANSOR;   // fallas nuevas que piden ABORT
  uint16_t retenerCon = F_BOBINA | F_COMUNICACION;              // fallas nuevas que piden HOLD (solo en EXECUTE)
  bool remotoReanuda = false;       // permite RESET/START/UNHOLD/UNSUSPEND/CLEAR por Modbus o red
  uint32_t scAuto = 0;              // bit n = el estado "actuando" n termina solo; se llena en iniciar()
};

struct EventoPK { uint32_t t; uint8_t de, a, cmd, origen; uint16_t motivo; uint32_t epoch; };   // epoch 0 = hora sin ajustar

class UnidadPackML {
 public:
  ConfigPK cfg;
  ConfigMonitor mon{FIRMA_MONITOR, 0, 0, 0, 0, 0, MK_PRODUCCION, 0, 0};
  bool contadoresCambiaron = false;
  uint8_t rapidas = 0;                    // bit n-1 = la entrada n se cuenta con pulsos por interrupción (no por lectura)
  bool horaFijada = false;       // para guardarlos con límite de escrituras
  uint8_t estado = PK_STOPPED, modo = MK_PRODUCCION, ultimoCmd = CK_NADA;
  uint16_t motivo = 0;                          // última causa de paro (categoria * 100 + causa)
  uint64_t ms[PK_N] = {};                       // tiempo acumulado en cada estado
  uint32_t procesadas = 0, defectuosas = 0;
  bool microparo = false;
  uint64_t microMs = 0;                         // tiempo acumulado en microparo (dentro de EXECUTE)
  uint16_t fallasPrev = 0;
  EventoPK ev[16];
  uint8_t nEv = 0, sigEv = 0;

  void iniciar(uint32_t ahora) {
    estado = PK_STOPPED; modo = MK_PRODUCCION; ultimoCmd = CK_NADA; motivo = 0;
    memset(ms, 0, sizeof(ms)); procesadas = defectuosas = 0; microparo = false; microMs = 0; fallasPrev = 0;
    nEv = sigEv = 0;
    tUlt = tEntrada = tUltCuenta = ahora; entPrev = 0; primeraLectura = true;
    cfg.scAuto = 0;
    for (uint8_t e = 1; e < PK_N; e++) if (esActuando(e)) cfg.scAuto |= 1u << e;   // todo "actuando" termina solo
  }

  // El estado "actuando" `e` espera a la aplicación (por ejemplo, el motor a velocidad): quita el automático.
  void esperarAplicacion(uint8_t e) { cfg.scAuto &= ~(1u << e); }
  void automatico(uint8_t e) { if (esActuando(e)) cfg.scAuto |= 1u << e; }

  // Qué estados están habilitados en cada modo (propuesta: mantenimiento y manual no usan retención externa ni ciclo completo).
  static bool habilitado(uint8_t m, uint8_t e) {
    if (m == MK_PRODUCCION) return e >= 1 && e < PK_N;
    return e >= 1 && e < PK_N && e != PK_SUSPENDING && e != PK_SUSPENDED && e != PK_UNSUSPENDING && e != PK_COMPLETING &&
           e != PK_COMPLETE;
  }

  // Tabla de transiciones por comando. 0 = el comando no vale en ese estado.
  static uint8_t destino(uint8_t e, uint8_t c) {
    switch (c) {
      case CK_RESET: return (e == PK_STOPPED || e == PK_COMPLETE) ? PK_RESETTING : 0;
      case CK_START: return e == PK_IDLE ? PK_STARTING : 0;
      case CK_STOP:
        switch (e) {
          case PK_IDLE: case PK_STARTING: case PK_EXECUTE: case PK_COMPLETING: case PK_COMPLETE: case PK_HOLDING:
          case PK_HELD: case PK_UNHOLDING: case PK_SUSPENDING: case PK_SUSPENDED: case PK_UNSUSPENDING: case PK_RESETTING:
            return PK_STOPPING;
        }
        return 0;
      case CK_HOLD: return e == PK_EXECUTE ? PK_HOLDING : 0;
      case CK_UNHOLD: return e == PK_HELD ? PK_UNHOLDING : 0;
      case CK_SUSPEND: return e == PK_EXECUTE ? PK_SUSPENDING : 0;
      case CK_UNSUSPEND: return e == PK_SUSPENDED ? PK_UNSUSPENDING : 0;
      case CK_ABORT: return (e == PK_ABORTING || e == PK_ABORTED) ? 0 : PK_ABORTING;
      case CK_CLEAR: return e == PK_ABORTED ? PK_CLEARING : 0;
    }
    return 0;
  }
  static bool reanuda(uint8_t c) { return c == CK_RESET || c == CK_START || c == CK_UNHOLD || c == CK_UNSUSPEND || c == CK_CLEAR; }
  static bool esRemoto(uint8_t o) { return o == OR_MODBUS || o == OR_RED; }

  // true = se aceptó y se hizo la transición.
  bool comando(uint8_t c, uint8_t origen, uint32_t ahora) {
    if (c == CK_NADA || c >= CK_N) return false;
    if (esRemoto(origen) && reanuda(c) && !cfg.remotoReanuda) { rechazar(c, origen, ahora); return false; }
    if ((c == CK_CLEAR || c == CK_RESET || c == CK_START) && (fallasPrev & cfg.abortarCon & ~F_VIGILANTE)) { rechazar(c, origen, ahora); return false; }
    uint8_t d = destino(estado, c);
    if (!d || !habilitado(modo, d)) { rechazar(c, origen, ahora); return false; }
    ultimoCmd = c;
    pasarA(d, c, origen, ahora);
    return true;
  }

  // Fin del estado actual ("State Complete"): lo manda la aplicación cuando el estado no es automático.
  bool completar(uint32_t ahora) {
    uint8_t d = 0;
    switch (estado) {
      case PK_STARTING: case PK_UNHOLDING: case PK_UNSUSPENDING: d = PK_EXECUTE; break;
      case PK_RESETTING: d = PK_IDLE; break;
      case PK_EXECUTE: d = PK_COMPLETING; break;
      case PK_COMPLETING: d = PK_COMPLETE; break;
      case PK_HOLDING: d = PK_HELD; break;
      case PK_SUSPENDING: d = PK_SUSPENDED; break;
      case PK_STOPPING: case PK_CLEARING: d = PK_STOPPED; break;
      case PK_ABORTING: d = PK_ABORTED; break;
    }
    if (!d || !habilitado(modo, d)) return false;
    pasarA(d, CK_NADA, OR_NINGUNO, ahora);
    return true;
  }

  // Solo en STOPPED o ABORTED.
  bool cambiarModo(uint8_t m, uint32_t ahora) {
    (void)ahora;
    if (m < MK_PRODUCCION || m > MK_MANUAL || (estado != PK_STOPPED && estado != PK_ABORTED)) return false;
    modo = m; return true;
  }

  void motivoParo(uint16_t codigo) { motivo = codigo > 999 ? 0 : codigo; }

  // Pieza terminada: solo se cuenta en EXECUTE o COMPLETING.
  bool contar(bool buena, uint32_t ahora) {
    if (estado != PK_EXECUTE && estado != PK_COMPLETING) return false;
    procesadas++; if (!buena) defectuosas++;
    contadoresCambiaron = true;
    tUltCuenta = ahora; microparo = false;
    return true;
  }

  // Se llama cada pocos ms con el reloj.
  void paso(uint32_t ahora) {
    uint32_t dt = ahora - tUlt; tUlt = ahora;
    if (horaFijada && ahora - msBase > 86400000UL) { uint32_t s = (ahora - msBase) / 1000; epochBase += s; msBase += s * 1000; }   // evita perder la cuenta al dar la vuelta millis()
    ms[estado] += dt;
    if (estado == PK_EXECUTE && cfg.cicloNominalMs) {
      // microparo = EXECUTE sin piezas durante más de 3 ciclos nominales (mínimo 2 s)
      uint32_t umbral = 3u * cfg.cicloNominalMs; if (umbral < 2000) umbral = 2000;
      if (ahora - tUltCuenta > umbral) { microparo = true; microMs += dt; }
    } else microparo = false;
    if (esActuando(estado) && (cfg.scAuto & (1u << estado)) && ahora != tEntrada) completar(ahora);
  }


  // ---- Entradas de la máquina (monitor): se llama cada paso con las entradas estables (bit = activa) ----
  // La primera lectura solo toma el estado inicial: nada se cuenta ni se pide por una entrada que ya estaba activa.
  void entradas(uint8_t ent, uint32_t ahora) {
    uint8_t subio = primeraLectura ? 0 : (uint8_t)(ent & ~entPrev);
    entPrev = ent; primeraLectura = false;
    if (!subio) return;
    auto sube = [&](uint8_t n) { return n >= 1 && n <= 8 && (subio & (1 << (n - 1))); };
    if (sube(mon.entCiclo) && !(rapidas & (1 << (mon.entCiclo - 1)))) contar(true, ahora);
    if (sube(mon.entMala) && !(rapidas & (1 << (mon.entMala - 1)))) contar(false, ahora);
    if (sube(mon.entAndon) && estado == PK_EXECUTE) { motivo = MOTIVO_ANDON; comando(CK_HOLD, OR_ENTRADA, ahora); }
    if (sube(mon.entReanuda)) comando(CK_UNHOLD, OR_ENTRADA, ahora);
  }
  // Una entrada no puede tener dos funciones. false = no válido (queda sin cambios).
  bool configurarMonitor(const ConfigMonitor& n, uint8_t nEntradas) {
    uint8_t v[4] = {n.entCiclo, n.entMala, n.entAndon, n.entReanuda};
    for (int i = 0; i < 4; i++) {
      if (v[i] > nEntradas) return false;
      for (int j = i + 1; j < 4; j++) if (v[i] && v[i] == v[j]) return false;
    }
    if (n.modo < MK_PRODUCCION || n.modo > MK_MANUAL) return false;
    mon = n; mon.firma = FIRMA_MONITOR; mon.crc = crc32((const uint8_t*)&mon, offsetof(ConfigMonitor, crc));
    cfg.cicloNominalMs = mon.cicloNominalMs;
    return true;
  }
  // La memoria es de confianza solo con firma y CRC correctos.
  bool cargarMonitor(const ConfigMonitor& n, uint8_t nEntradas) {
    if (n.firma != FIRMA_MONITOR || n.crc != crc32((const uint8_t*)&n, offsetof(ConfigMonitor, crc))) return false;
    if (!configurarMonitor(n, nEntradas)) return false;
    if (estado == PK_STOPPED) modo = mon.modo;
    return true;
  }
  // Antes de guardar: copia el ciclo nominal y el modo vigentes.
  const ConfigMonitor& paraGuardar() {
    mon.firma = FIRMA_MONITOR; mon.cicloNominalMs = cfg.cicloNominalMs; mon.modo = modo;
    mon.crc = crc32((const uint8_t*)&mon, offsetof(ConfigMonitor, crc));
    return mon;
  }
  void restaurarContadores(uint32_t buenas, uint32_t malas) {
    if (malas > buenas) return;
    procesadas = buenas; defectuosas = malas;
  }

  // ---- Hora: segundos desde 1970 (la fija el reloj de tiempo real, la red o un maestro Modbus) ----
  bool fijarHora(uint32_t epoch, uint32_t ahora) {
    if (!epochCreible(epoch)) return false;
    epochBase = epoch; msBase = ahora; horaFijada = true; return true;
  }
  uint32_t epochAhora(uint32_t ahora) const { return horaFijada ? epochBase + (ahora - msBase) / 1000 : 0; }

  // ---- Pulsos contados por interrupción en una entrada de conteo rápido (1 o 2): `total` es el acumulado del hardware ----
  // Cada pulso nuevo cuenta como pieza buena o mala según la función de la entrada. Más de 1000 en un paso se ignora.
  void pulsos(uint8_t n, uint32_t total, uint32_t ahora) {
    if (n < 1 || n > 2) return;
    uint32_t d = total - pulsosPrev[n - 1];
    pulsosPrev[n - 1] = total;
    if (!pulsosListos[n - 1]) { pulsosListos[n - 1] = true; return; }    // la primera lectura solo toma el acumulado
    if (d > 1000) return;                                              // salto imposible en un paso: se ignora, no se inventan piezas
    for (uint32_t i = 0; i < d; i++) {
      if (mon.entCiclo == n) contar(true, ahora);
      if (mon.entMala == n) contar(false, ahora);
    }
  }

  // Fallas nuevas del controlador: piden ABORT o HOLD. Una falla que sigue activa bloquea CLEAR, RESET y START.
  void alFalla(uint16_t fallas, uint32_t ahora) {
    uint16_t nuevas = fallas & ~fallasPrev;
    fallasPrev = fallas;
    if (!nuevas) return;
    if (nuevas & cfg.abortarCon) {
      motivo = CP_AVERIA * 100 + bitBajo(nuevas & cfg.abortarCon);
      comando(CK_ABORT, OR_NINGUNO, ahora);
    } else if ((nuevas & cfg.retenerCon) && estado == PK_EXECUTE) {
      uint16_t b = nuevas & cfg.retenerCon;
      motivo = ((b & F_COMUNICACION) ? CP_EXTERNA : CP_AVERIA) * 100 + bitBajo(b);
      comando(CK_HOLD, OR_NINGUNO, ahora);
    }
  }

  // Solo para mirar o apagar la salida de proceso: no es una función de seguridad.
  bool procesoHabilitado() const { return estado == PK_EXECUTE; }

  // ---- OEE en milésimas (0-1000). 0xFFFF = no calculable (falta el ciclo nominal o piezas) ----
  // Definición AP (propuesta; falta confirmar con ISO 22400-2): disponibilidad = EXECUTE / (EXECUTE + paros no planeados),
  // con paros no planeados = HOLDING, HELD, UNHOLDING, SUSPENDING, SUSPENDED, UNSUSPENDING, ABORTING, ABORTED, CLEARING.
  uint64_t paroNoPlaneadoMs() const {
    return ms[PK_HOLDING] + ms[PK_HELD] + ms[PK_UNHOLDING] + ms[PK_SUSPENDING] + ms[PK_SUSPENDED] + ms[PK_UNSUSPENDING] +
           ms[PK_ABORTING] + ms[PK_ABORTED] + ms[PK_CLEARING];
  }
  uint16_t disponibilidad() const {
    uint64_t t = ms[PK_EXECUTE] + paroNoPlaneadoMs();
    return t ? (uint16_t)(ms[PK_EXECUTE] * 1000 / t) : 0xFFFF;
  }
  uint16_t desempeno() const {
    if (!cfg.cicloNominalMs || !ms[PK_EXECUTE] || !procesadas) return 0xFFFF;
    uint64_t v = (uint64_t)procesadas * cfg.cicloNominalMs * 1000 / ms[PK_EXECUTE];
    return v > 1000 ? 1000 : (uint16_t)v;
  }
  uint16_t calidad() const { return procesadas ? (uint16_t)((uint64_t)(procesadas - defectuosas) * 1000 / procesadas) : 0xFFFF; }
  uint16_t oee() const {
    uint16_t a = disponibilidad(), p = desempeno(), q = calidad();
    if (a == 0xFFFF || p == 0xFFFF || q == 0xFFFF) return 0xFFFF;
    return (uint16_t)((uint32_t)a * p / 1000 * q / 1000);
  }
  uint32_t segundosEn(uint8_t e) const { return e < PK_N ? (uint32_t)(ms[e] / 1000) : 0; }

 private:
  uint32_t tUlt = 0, tEntrada = 0, tUltCuenta = 0;
  uint8_t entPrev = 0; bool primeraLectura = true;
  uint32_t epochBase = 0, msBase = 0, pulsosPrev[2] = {0, 0}; bool pulsosListos[2] = {false, false};

  static uint8_t bitBajo(uint16_t v) { uint8_t i = 0; while (v && !(v & 1)) { v >>= 1; i++; } return i + 1; }
  void pasarA(uint8_t d, uint8_t c, uint8_t origen, uint32_t ahora) {
    registrar(estado, d, c, origen, ahora);
    estado = d; tEntrada = ahora;
    if (d == PK_EXECUTE) { tUltCuenta = ahora; microparo = false; }
  }
  void rechazar(uint8_t c, uint8_t origen, uint32_t ahora) { registrar(estado, estado, c, origen, ahora); }
  void registrar(uint8_t de, uint8_t a, uint8_t c, uint8_t origen, uint32_t ahora) {
    ev[sigEv] = EventoPK{ahora, de, a, c, origen, motivo, epochAhora(ahora)};
    sigEv = (sigEv + 1) % 16; if (nEv < 16) nEv++;
  }
};

}  // namespace apc
