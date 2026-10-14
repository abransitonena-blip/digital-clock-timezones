// AP Control: esclavo Modbus RTU (funciones 01, 02, 03, 04, 05, 06, 15, 16) y el mapa de registros del equipo.
// procesar() recibe una trama completa (el bosquejo la separa por el silencio de 3.5 caracteres) y escribe la respuesta.
// Mapa (direcciones del protocolo, base 0; entre paréntesis la notación 1-based de los PLC):
//   Bobinas (0x)          0-6     canal 1-7: leer = salida; escribir = mandar el canal           (00001-00007)
//   Entradas discretas    0-7     entrada 1-8 (estable)                                          (10001-10008)
//                         16-22   bobina 1-7 energizada (retroalimentación)                      (10017-10023)
//                         32      DIP 8 "Wi-Fi apagado" · 33 comunicación perdida · 34 hay falla (10033-10035)
//   Registros de entrada  0 versión (100 x mayor + menor) · 1 placa (1 = 7R Tour, 2 = AP Home)   (30001-30002)
//                         2 fallas (bits) · 3 salidas · 4 entradas · 5 bobinas · 6 forzado     (30003-30007)
//                         7-8 segundos encendido (bajo, alto) · 20-33 maniobras de los canales 1-7 (32 bits)
//   Registros (4x)        0 vigilancia en s (0 = sin) · 1 salidas (máscara)                     (40001-40002)
//                         10-16 arranque (0 apagado, 1 último, 2 encendido) · 20-26 carga (0 alumbrado, 1 proceso)
//                         30-36 al perder la comunicación (0 apagar, 1 mantener) · 40-46 pulso en s (0 = sin)
//                         50-57 modo de entrada (0 pulsador, 1 interruptor, 2 conmutador, 3 desacoplada)
//                         60-67 canal de la entrada (0 = ninguno) · 70-77 antirrebote en ms
//                         100 dirección · 101 baudios / 100 · 102 paridad (0 N, 1 E, 2 O)
//                         200 orden: 0xA55A = guardar la configuración en la memoria, 0x5AA5 = valores de fábrica
//   PackTags v1 (solo si el equipo tiene unidad PackML; si no, excepción 02). Estados y comandos: unidad_packml.h
//     Entradas discretas  48 microparo · 49 proceso habilitado (estado EXECUTE) · 50 comandos remotos que reanudan permitidos
//     Registros de entrada 100 versión del mapa (1) · 101 StateCurrent · 102 UnitModeCurrent · 103 StopReason
//                          104 último comando aceptado · 105-106 ProdProcessedCount · 107-108 ProdDefectiveCount
//                          110-143 segundos acumulados en cada estado 1-17 (32 bits: bajo, alto; estado n en 110 + 2 (n-1))
//                          150 disponibilidad · 151 desempeño · 152 calidad · 153 OEE (milésimas; 65535 = no calculable)
//                          154 microparo (0/1) · 155-156 segundos en microparo (bajo, alto)
//                          160-161 hora en segundos desde 1970 (bajo, alto; 0 = sin ajustar) · 162 hora ajustada (0/1)
//     Registros (4x)       300 CntrlCmd (escribir 1 Reset · 2 Start · 3 Stop · 4 Hold · 5 Unhold · 6 Suspend · 7 Unsuspend ·
//                          8 Abort · 9 Clear; excepción 04 si el estado, el modo o el origen no lo permiten)
//                          301 UnitMode (1 producción · 2 mantenimiento · 3 manual; solo en STOPPED o ABORTED)
//                          302 StopReason (categoría x 100 + causa) · 303 contar pieza (1 buena · 2 defectuosa)
//                          304 ciclo nominal en ms (0 = sin ciclo)
//                          305 comandos remotos que reanudan (0 no · 1 sí): SOLO LECTURA por Modbus, se cambia en el equipo
//                          320-321 ajustar la hora (segundos desde 1970): primero la palabra baja y al escribir la alta se ajusta; excepción 03 si
//                          es anterior a 2024 o posterior a 2099. Entrada discreta 51 = hora ajustada
//                          306 entrada de pieza buena · 307 de pieza mala · 308 de andon (pide HOLD) · 309 de reanudar (0-8; 0 = ninguna;
//                          una entrada no puede tener dos funciones; excepción 03). Se guardan con la orden 200 = 0xA55A
// Los cambios de configuración se validan y valen al momento, pero solo se guardan con la orden 0xA55A
// (así un maestro que escribe seguido no desgasta la memoria). Una escritura inválida responde la excepción 03.
#pragma once
#include "ap_control.h"
#include "unidad_packml.h"

namespace apc {

inline uint16_t crc16(const uint8_t* d, size_t n) {
  uint16_t c = 0xFFFF;
  for (size_t i = 0; i < n; i++) {
    c ^= d[i];
    for (int k = 0; k < 8; k++) c = (c & 1) ? (c >> 1) ^ 0xA001 : c >> 1;
  }
  return c;
}

struct Esclavo {
  Controlador& ctl;
  uint16_t version, placa;
  uint32_t* segundos;
  UnidadPackML* um = nullptr;                    // opcional: sin ella los registros PackTags no existen
  bool horaNueva = false;                        // un maestro ajustó la hora: hay que escribirla en el reloj de tiempo real
  uint16_t horaBaja = 0;
  uint32_t ultimoAhora = 0;                      // reloj de la última trama (para la hora que se informa)
  bool pedirGuardar = false, pedirFabrica = false, cambioComunicacion = false;
  uint32_t tramasBien = 0, tramasMal = 0;
  Esclavo(Controlador& c, uint16_t v, uint16_t p, uint32_t* s) : ctl(c), version(v), placa(p), segundos(s) {}

  // 0 = sin respuesta (otra dirección, difusión o trama mala)
  size_t procesar(const uint8_t* q, size_t n, uint8_t* r, uint32_t ahora) {
    if (n < 4 || crc16(q, n - 2) != (uint16_t)(q[n - 2] | q[n - 1] << 8)) { tramasMal++; return 0; }
    uint8_t dir = q[0];
    if (dir != 0 && dir != ctl.cfg.mbDireccion) return 0;
    tramasBien++; ultimoAhora = ahora;
    ctl.modbusEscribio(ahora);                    // un maestro que solo lee también está presente (vigilancia de comunicación)
    uint8_t fn = q[1];
    uint16_t a = n >= 6 ? (q[2] << 8 | q[3]) : 0, c = n >= 6 ? (q[4] << 8 | q[5]) : 0;
    size_t m = 0;
    r[m++] = ctl.cfg.mbDireccion; r[m++] = fn;
    uint8_t ex = ((fn == 1 || fn == 2 || fn == 3 || fn == 4 || fn == 15 || fn == 16) && (uint32_t)a + c > 65536u) ? 2 : 0;
    if (!ex) switch (fn) {
      case 1: case 2: {
        if (n != 8 || c < 1 || c > 2000) { ex = 3; break; }
        uint8_t nb = (c + 7) / 8; r[m++] = nb;
        for (int i = 0; i < nb; i++) r[m + i] = 0;
        for (int i = 0; i < c && !ex; i++) {
          int v = fn == 1 ? bobina(a + i) : discreta(a + i);
          if (v < 0) ex = 2; else if (v) r[m + i / 8] |= 1 << (i % 8);
        }
        m += nb; break;
      }
      case 3: case 4: {
        if (n != 8 || c < 1 || c > 125) { ex = 3; break; }
        r[m++] = c * 2;
        for (int i = 0; i < c && !ex; i++) {
          int32_t v = fn == 3 ? holding(a + i) : input(a + i);
          if (v < 0) ex = 2; else { r[m++] = v >> 8; r[m++] = v & 0xFF; }
        }
        break;
      }
      case 5: {
        if (n != 8 || !(c == 0xFF00 || c == 0)) { ex = 3; break; }
        ex = escribirBobina(a, c == 0xFF00, ahora);
        if (!ex) { memcpy(r + 2, q + 2, 4); m = 6; }
        break;
      }
      case 6: {
        if (n != 8) { ex = 3; break; }
        ex = escribirHolding(a, c, ahora);
        if (!ex) { memcpy(r + 2, q + 2, 4); m = 6; }
        break;
      }
      case 15: {
        if (n < 10 || c < 1 || c > 1968 || q[6] != (c + 7) / 8 || n != 9u + q[6]) { ex = 3; break; }
        for (int i = 0; i < c && !ex; i++) ex = escribirBobina(a + i, q[7 + i / 8] & (1 << (i % 8)), ahora);
        if (!ex) { memcpy(r + 2, q + 2, 4); m = 6; }
        break;
      }
      case 16: {
        if (n < 11 || c < 1 || c > 123 || q[6] != c * 2 || n != 9u + q[6]) { ex = 3; break; }
        for (int i = 0; i < c && !ex; i++) ex = escribirHolding(a + i, q[7 + 2 * i] << 8 | q[8 + 2 * i], ahora);
        if (!ex) { memcpy(r + 2, q + 2, 4); m = 6; }
        break;
      }
      default: ex = 1;
    }
    if (ex) { r[1] = fn | 0x80; r[2] = ex; m = 3; }
    if (dir == 0) return 0;                       // difusión: se ejecuta sin responder
    uint16_t k = crc16(r, m); r[m++] = k & 0xFF; r[m++] = k >> 8;
    return m;
  }

 private:
  int bobina(uint16_t a) { return a < ctl.cfg.nCanales ? (ctl.salida >> a) & 1 : -1; }
  int discreta(uint16_t a) {
    if (a < ctl.cfg.nEntradas) return (ctl.entradas >> a) & 1;
    if (a >= 16 && a < 16 + ctl.cfg.nCanales) return (ctl.bobinas >> (a - 16)) & 1;
    if (a == 32) return wifiApagado;
    if (a == 33) return ctl.comPerdida;
    if (a == 34) return ctl.fallas != 0;
    if (um && a == 48) return um->microparo;
    if (um && a == 49) return um->procesoHabilitado();
    if (um && a == 51) return um->horaFijada;
    if (um && a == 50) return um->cfg.remotoReanuda;
    return -1;
  }
  int32_t input(uint16_t a) {
    switch (a) {
      case 0: return version; case 1: return placa; case 2: return ctl.fallas; case 3: return ctl.salida;
      case 4: return ctl.entradas; case 5: return ctl.bobinas; case 6: return ctl.forzado;
      case 7: return segundos ? (*segundos & 0xFFFF) : 0; case 8: return segundos ? (*segundos >> 16) : 0;
    }
    if (a >= 20 && a < 20 + 2 * ctl.cfg.nCanales) {
      uint32_t v = ctl.maniobras[(a - 20) / 2];
      return (a - 20) % 2 ? v >> 16 : v & 0xFFFF;
    }
    return um ? inputPK(a) : -1;
  }
  int32_t inputPK(uint16_t a) {
    const UnidadPackML& u = *um;
    switch (a) {
      case 100: return 1; case 101: return u.estado; case 102: return u.modo; case 103: return u.motivo;
      case 104: return u.ultimoCmd; case 105: return u.procesadas & 0xFFFF; case 106: return u.procesadas >> 16;
      case 107: return u.defectuosas & 0xFFFF; case 108: return u.defectuosas >> 16;
      case 150: return u.disponibilidad(); case 151: return u.desempeno(); case 152: return u.calidad(); case 153: return u.oee();
      case 160: return u.epochAhora(ultimoAhora) & 0xFFFF; case 161: return u.epochAhora(ultimoAhora) >> 16; case 162: return u.horaFijada;
      case 154: return u.microparo; case 155: return (uint32_t)(u.microMs / 1000) & 0xFFFF; case 156: return (uint32_t)(u.microMs / 1000) >> 16;
    }
    if (a >= 110 && a < 110 + 2 * (PK_COMPLETE)) {
      uint32_t v = u.segundosEn(1 + (a - 110) / 2);
      return (a - 110) % 2 ? v >> 16 : v & 0xFFFF;
    }
    return -1;
  }
  int32_t holding(uint16_t a) {
    const Config& c = ctl.cfg;
    int n = c.nCanales, ne = c.nEntradas;
    if (a == 0) return c.mbVigilanciaS;
    if (a == 1) return ctl.salida;
    if (a >= 10 && a < 10 + n) return c.canal[a - 10].arranque;
    if (a >= 20 && a < 20 + n) return c.canal[a - 20].carga;
    if (a >= 30 && a < 30 + n) return c.canal[a - 30].accionCom;
    if (a >= 40 && a < 40 + n) return c.canal[a - 40].pulsoS;
    if (a >= 50 && a < 50 + ne) return c.entrada[a - 50].modo;
    if (a >= 60 && a < 60 + ne) return c.entrada[a - 60].canal;
    if (a >= 70 && a < 70 + ne) return c.entrada[a - 70].antirreboteMs;
    if (a == 100) return c.mbDireccion;
    if (a == 101) return c.mbBaudios / 100;
    if (a == 102) return c.mbParidad;
    if (a == 200) return 0;
    if (um && a == 300) return um->ultimoCmd;
    if (um && a == 301) return um->modo;
    if (um && a == 302) return um->motivo;
    if (um && a == 303) return 0;
    if (um && a == 304) return um->cfg.cicloNominalMs;
    if (um && a == 305) return um->cfg.remotoReanuda;
    if (um && a == 306) return um->mon.entCiclo;
    if (um && a == 307) return um->mon.entMala;
    if (um && a == 308) return um->mon.entAndon;
    if (um && a == 309) return um->mon.entReanuda;
    if (um && (a == 320 || a == 321)) return 0;
    return -1;
  }
  uint8_t escribirBobina(uint16_t a, bool v, uint32_t ahora) {
    if (a >= ctl.cfg.nCanales) return 2;
    ctl.modbusEscribio(ahora);
    return ctl.ordenar(a + 1, v, OR_MODBUS, ahora) == OK ? 0 : 4;    // 4 = el canal lo maneja el programa PLC
  }
  // 3 = valor ilegal; 4 = el estado, el modo o el origen no lo permiten (nunca se reanuda por sí solo)
  uint8_t escribirPK(uint16_t a, uint16_t v, uint32_t ahora) {
    switch (a) {
      case 300: if (v == CK_NADA) return 0; if (v >= CK_N) return 3; return um->comando(v, OR_MODBUS, ahora) ? 0 : 4;
      case 301: if (v < MK_PRODUCCION || v > MK_MANUAL) return 3; return um->cambiarModo(v, ahora) ? 0 : 4;
      case 302: if (v > 999) return 3; um->motivoParo(v); return 0;
      case 303: if (v != 1 && v != 2) return 3; return um->contar(v == 1, ahora) ? 0 : 4;
      case 304: um->cfg.cicloNominalMs = v; return 0;
      case 305: return 2;                       // solo lectura: un maestro no puede darse permiso para reanudar
      case 320: horaBaja = v; return 0;           // hora: primero la palabra baja (320) y al escribir la alta (321) se ajusta
      case 321: {
        uint32_t t = (uint32_t)v << 16 | horaBaja;
        if (!um->fijarHora(t, ahora)) return 3;
        horaNueva = true; return 0;
      }
      case 306: case 307: case 308: case 309: {    // función de cada entrada (0 = ninguna); no puede repetirse
        ConfigMonitor n = um->mon;
        (a == 306 ? n.entCiclo : a == 307 ? n.entMala : a == 308 ? n.entAndon : n.entReanuda) = v > 255 ? 255 : v;
        return um->configurarMonitor(n, ctl.cfg.nEntradas) ? 0 : 3;
      }
    }
    return 2;
  }
  uint8_t escribirHolding(uint16_t a, uint16_t v, uint32_t ahora) {
    Config c = ctl.cfg;
    int n = c.nCanales, ne = c.nEntradas;
    ctl.modbusEscribio(ahora);
    if (um && a >= 300 && a <= 321) return escribirPK(a, v, ahora);
    if (a == 1) {
      if (v >> n) return 3;
      for (int k = 0; k < n; k++) if (ctl.ordenar(k + 1, (v >> k) & 1, OR_MODBUS, ahora) != OK) return 4;
      return 0;
    }
    if (a == 200) {
      if (v == 0xA55A) { pedirGuardar = true; return 0; }
      if (v == 0x5AA5) { if (!(um && um->cfg.remotoReanuda)) return 4; pedirFabrica = true; return 0; }   // exige el permiso local
      return 3;
    }
    if (a == 0) { if (v > 3600) return 3; c.mbVigilanciaS = v; }
    else if (a >= 10 && a < 10 + n) { if (v > ARR_ENCENDIDO || (v && c.canal[a - 10].carga == CARGA_PROCESO)) return 3; c.canal[a - 10].arranque = v; }
    else if (a >= 20 && a < 20 + n) {
      if (v > CARGA_PROCESO) return 3;
      c.canal[a - 20].carga = v;
      if (v == CARGA_PROCESO) { c.canal[a - 20].arranque = ARR_APAGADO; c.canal[a - 20].accionCom = COM_APAGAR; }
    }
    else if (a >= 30 && a < 30 + n) { if (v > COM_MANTENER || (v && c.canal[a - 30].carga == CARGA_PROCESO)) return 3; c.canal[a - 30].accionCom = v; }
    else if (a >= 40 && a < 40 + n) { if (v > 36000) return 3; c.canal[a - 40].pulsoS = v; }
    else if (a >= 50 && a < 50 + ne) { if (v > ENT_DESACOPLADA) return 3; c.entrada[a - 50].modo = v; }
    else if (a >= 60 && a < 60 + ne) { if (v > n) return 3; c.entrada[a - 60].canal = v; }
    else if (a >= 70 && a < 70 + ne) { if (v < 5 || v > 2000) return 3; c.entrada[a - 70].antirreboteMs = v; }
    else if (a == 100) { if (v < 1 || v > 247) return 3; c.mbDireccion = v; cambioComunicacion = true; }
    else if (a == 101) { uint32_t b = v * 100u; if (!(b == 9600 || b == 19200 || b == 38400 || b == 57600 || b == 115200)) return 3; c.mbBaudios = b; cambioComunicacion = true; }
    else if (a == 102) { if (v > 2) return 3; c.mbParidad = v; cambioComunicacion = true; }
    else return 2;
    c.crc = crcDe(c);
    if (!validar(c)) return 3;
    ctl.cfg = c;
    return 0;
  }
 public:
  bool wifiApagado = false;
};

}  // namespace apc
