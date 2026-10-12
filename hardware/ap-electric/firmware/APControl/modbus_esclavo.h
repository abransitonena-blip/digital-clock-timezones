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
// Los cambios de configuración se validan y valen al momento, pero solo se guardan con la orden 0xA55A
// (así un maestro que escribe seguido no desgasta la memoria). Una escritura inválida responde la excepción 03.
#pragma once
#include "ap_control.h"

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
  bool pedirGuardar = false, pedirFabrica = false, cambioComunicacion = false;
  uint32_t tramasBien = 0, tramasMal = 0;
  Esclavo(Controlador& c, uint16_t v, uint16_t p, uint32_t* s) : ctl(c), version(v), placa(p), segundos(s) {}

  // 0 = sin respuesta (otra dirección, difusión o trama mala)
  size_t procesar(const uint8_t* q, size_t n, uint8_t* r, uint32_t ahora) {
    if (n < 4 || crc16(q, n - 2) != (uint16_t)(q[n - 2] | q[n - 1] << 8)) { tramasMal++; return 0; }
    uint8_t dir = q[0];
    if (dir != 0 && dir != ctl.cfg.mbDireccion) return 0;
    tramasBien++;
    uint8_t fn = q[1];
    uint16_t a = n >= 6 ? (q[2] << 8 | q[3]) : 0, c = n >= 6 ? (q[4] << 8 | q[5]) : 0;
    size_t m = 0;
    r[m++] = ctl.cfg.mbDireccion; r[m++] = fn;
    uint8_t ex = 0;
    switch (fn) {
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
    return -1;
  }
  uint8_t escribirBobina(uint16_t a, bool v, uint32_t ahora) {
    if (a >= ctl.cfg.nCanales) return 2;
    ctl.modbusEscribio(ahora);
    return ctl.ordenar(a + 1, v, OR_MODBUS, ahora) == OK ? 0 : 4;    // 4 = el canal lo maneja el programa PLC
  }
  uint8_t escribirHolding(uint16_t a, uint16_t v, uint32_t ahora) {
    Config c = ctl.cfg;
    int n = c.nCanales, ne = c.nEntradas;
    ctl.modbusEscribio(ahora);
    if (a == 1) {
      if (v >> n) return 3;
      for (int k = 0; k < n; k++) if (ctl.ordenar(k + 1, (v >> k) & 1, OR_MODBUS, ahora) != OK) return 4;
      return 0;
    }
    if (a == 200) {
      if (v == 0xA55A) { pedirGuardar = true; return 0; }
      if (v == 0x5AA5) { pedirFabrica = true; return 0; }
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
