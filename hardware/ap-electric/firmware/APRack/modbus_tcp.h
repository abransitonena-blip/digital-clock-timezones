// Modbus TCP del cabeza (AP PLC C24 y cualquier cabeza con Ethernet o Wi-Fi). Portable: sin Arduino, sin memoria dinámica.
// Atiende las funciones 01, 02, 03, 04, 05, 06, 15 y 16 sobre TODAS las entradas y salidas de la cadena (las del cabeza y las de los módulos).
// Mapa (direcciones del protocolo, base 0; entre paréntesis la notación 1-based de los PLC):
//   Bobinas (0x)            0..  salida global 1.. (la del cabeza primero; ver «C g v» en ap_rack.h)       (00001..)
//                           leer = lo que se pidió; escribir = mandar. Si el programa del PLC maneja esa salida: excepción 04
//   Entradas discretas      0..  entrada global 1..                                                          (10001..)
//   Registros de entrada    0 versión del mapa (1) · 1 módulos · 2 salidas · 3 entradas · 4 PLC en RUN (0/1) · 5 hay falla (0/1)   (30001..)
//                           6-7 segundos encendido (bajo, alto) · 8 analógicas · 9-10 hora en segundos desde 1970 (bajo, alto; 0 = sin ajustar, por NTP) · 11 hora ajustada (0/1) · 100.. analógica global 1.. (mV o µA, sin signo)
//   Registros (4x)          0 modo del PLC: leer 0 = STOP, 1 = RUN; escribir 1 = RUN, 0 = STOP (excepción 04 si no hay programa) (40001)
//                           1..16 R1..R16: consignas que lee el programa del PLC (enteros de 16 bits con signo)             (40002..40017)
// El cabeza informa cambios de modo en *modoCambio para que el programa de la placa los guarde. Solo el cabeza contesta; un módulo esclavo, excepción 04.
// Esto NO es una función de seguridad: Modbus TCP no tiene autenticación ni cifrado; usar en una red de planta aislada o detrás de un cortafuegos.
#pragma once
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include "ap_rack.h"

namespace aprack {

inline uint16_t mbVersion() { return 1; }

// q = trama TCP completa (MBAP de 7 bytes + función + datos); r = respuesta. Devuelve su largo, o 0 si la trama no es Modbus TCP (conviene cerrar la conexión).
inline size_t modbusTcp(aplink::Enlace& e, PlcRack& plc, uint16_t* segura, uint32_t segundos, const uint8_t* q, size_t n, uint8_t* r, bool* modoCambio, uint32_t epoch = 0) {
  if (n < 8 || q[2] || q[3]) return 0;                                    // el identificador de protocolo es 0
  size_t largo = (size_t)(q[4] << 8 | q[5]);
  if (largo != n - 6 || largo < 2) return 0;
  const uint8_t* p = q + 7; size_t pn = n - 7;                          // PDU: función + datos
  uint8_t fn = p[0];
  uint8_t* d = r + 7; size_t m = 0;
  r[0] = q[0]; r[1] = q[1]; r[2] = 0; r[3] = 0; r[6] = q[6];
  d[m++] = fn;
  uint16_t a = pn >= 5 ? (uint16_t)(p[1] << 8 | p[2]) : 0, c = pn >= 5 ? (uint16_t)(p[3] << 8 | p[4]) : 0;
  uint8_t ex = 0;
  bool cabeza = e.rol() == aplink::Rol::CABEZA;
  uint16_t nSal = e.totalSalidas(), nEnt = e.totalEntradas(), nAna = e.totalAnalogicas();

  auto bobina = [&](uint16_t g, bool* v) -> bool {                       // g base 1
    uint8_t pos, l; if (!e.canalGlobal(g, &pos, &l)) return false;
    const aplink::InfoMod* mo = e.modulo(pos); if (!mo) return false;
    *v = (mo->deseadas >> (l - 1)) & 1; return true;
  };
  auto entrada = [&](uint16_t g, bool* v) -> bool {
    uint8_t pos, l; if (!e.entradaGlobal(g, &pos, &l)) return false;
    const aplink::InfoMod* mo = e.modulo(pos); *v = mo && !mo->perdido && ((mo->ent >> (l - 1)) & 1); return true;
  };
  auto analogica = [&](uint16_t g) -> uint16_t {
    uint8_t pos, l; if (!e.analogicaGlobal(g, &pos, &l)) return 0;
    const aplink::InfoMod* mo = e.modulo(pos); return mo && !mo->perdido ? mo->ana[l - 1] : 0;
  };
  auto hayFalla = [&]() -> uint16_t {
    for (uint8_t i = 1; i <= aplink::MAX_MODULOS; i++) if (const aplink::InfoMod* mo = e.modulo(i)) if (mo->perdido || mo->fallas) return 1;
    return 0;
  };
  auto registro = [&](bool entrada4x, uint16_t reg) -> int32_t {          // -1 = no existe
    if (entrada4x) {
      switch (reg) {
        case 0: return mbVersion(); case 1: return e.total(); case 2: return nSal; case 3: return nEnt; case 4: return plc.run ? 1 : 0;
        case 5: return hayFalla(); case 6: return (int32_t)(segundos & 0xFFFF); case 7: return (int32_t)(segundos >> 16); case 8: return nAna; case 9: return (int32_t)(epoch & 0xFFFF); case 10: return (int32_t)(epoch >> 16); case 11: return epoch ? 1 : 0;
      }
      if (reg >= 100 && reg < 100u + nAna) return analogica(reg - 99);
      return -1;
    }
    if (reg == 0) return plc.run ? 1 : 0;
    if (reg >= 1 && reg <= 16) { float v = plc.r[reg - 1]; return (int32_t)(uint16_t)(int16_t)(v > 32767 ? 32767 : v < -32768 ? -32768 : v); }
    return -1;
  };
  auto ponerBobina = [&](uint16_t g, bool v) -> uint8_t {                  // devuelve excepción o 0
    if (!cabeza) return 4;
    if (g >= nSal) return 2;
    char ord[24]; snprintf(ord, sizeof ord, "C %u %d", (unsigned)(g + 1), v ? 1 : 0);
    return orden(e, ord, segura, &plc) ? 0 : 4;                           // «C» rechaza lo que maneja el programa del PLC
  };
  auto ponerRegistro = [&](uint16_t reg, uint16_t v) -> uint8_t {
    if (!cabeza) return 4;
    if (reg == 0) { if (v > 1) return 3; bool antes = plc.run; plc.modo(v == 1); if (v == 1 && !plc.run) return 4; if (antes != plc.run && modoCambio) *modoCambio = true; return 0; }
    if (reg >= 1 && reg <= 16) return plc.ponerR(reg, (float)(int16_t)v) ? 0 : 3;
    return 2;
  };

  if (!cabeza && (fn == 5 || fn == 6 || fn == 15 || fn == 16)) ex = 4;
  else switch (fn) {
    case 1: case 2: {
      if (pn != 5 || c < 1 || c > 2000) { ex = 3; break; }
      uint16_t lim = fn == 1 ? nSal : nEnt;
      if ((uint32_t)a + c > lim) { ex = 2; break; }
      d[m++] = (uint8_t)((c + 7) / 8);
      for (uint16_t i = 0; i < (c + 7) / 8; i++) d[m + i] = 0;
      for (uint16_t i = 0; i < c; i++) { bool v = false; if (fn == 1) bobina(a + i + 1, &v); else entrada(a + i + 1, &v); if (v) d[m + i / 8] |= (uint8_t)(1u << (i % 8)); }
      m += (c + 7) / 8; break;
    }
    case 3: case 4: {
      if (pn != 5 || c < 1 || c > 125) { ex = 3; break; }
      d[m++] = (uint8_t)(2 * c);
      for (uint16_t i = 0; i < c; i++) {
        int32_t v = registro(fn == 4, (uint16_t)(a + i));
        if (v < 0) { ex = 2; break; }
        d[m++] = (uint8_t)(v >> 8); d[m++] = (uint8_t)v;
      }
      break;
    }
    case 5: {
      if (pn != 5) { ex = 3; break; }
      if (c != 0x0000 && c != 0xFF00) { ex = 3; break; }
      ex = ponerBobina(a, c == 0xFF00);
      if (!ex) { d[m++] = p[1]; d[m++] = p[2]; d[m++] = p[3]; d[m++] = p[4]; }
      break;
    }
    case 6: {
      if (pn != 5) { ex = 3; break; }
      ex = ponerRegistro(a, c);
      if (!ex) { d[m++] = p[1]; d[m++] = p[2]; d[m++] = p[3]; d[m++] = p[4]; }
      break;
    }
    case 15: {
      if (pn < 7 || c < 1 || c > 1968 || p[5] != (c + 7) / 8 || pn != (size_t)(6 + p[5])) { ex = 3; break; }
      if ((uint32_t)a + c > nSal) { ex = 2; break; }
      for (uint16_t i = 0; i < c && !ex; i++) ex = ponerBobina(a + i, (p[6 + i / 8] >> (i % 8)) & 1);
      if (!ex) { d[m++] = p[1]; d[m++] = p[2]; d[m++] = p[3]; d[m++] = p[4]; }
      break;
    }
    case 16: {
      if (pn < 8 || c < 1 || c > 123 || p[5] != 2 * c || pn != (size_t)(6 + p[5])) { ex = 3; break; }
      if (registro(false, a) < 0 || registro(false, (uint16_t)(a + c - 1)) < 0) { ex = 2; break; }
      for (uint16_t i = 0; i < c && !ex; i++) ex = ponerRegistro(a + i, (uint16_t)(p[6 + 2 * i] << 8 | p[7 + 2 * i]));
      if (!ex) { d[m++] = p[1]; d[m++] = p[2]; d[m++] = p[3]; d[m++] = p[4]; }
      break;
    }
    default: ex = 1;
  }
  if (ex) { m = 0; d[m++] = fn | 0x80; d[m++] = ex; }
  r[4] = (uint8_t)((m + 1) >> 8); r[5] = (uint8_t)(m + 1);
  return 7 + m;
}

}  // namespace aprack
