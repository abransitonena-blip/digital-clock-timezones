// Modbus RTU (maestro) para la placa AP GATE: tramas, CRC y lectura de valores.
// Sin dependencias del hardware: se prueba en la PC con tools/probar_apbus.sh (prueba_modbus.cpp).
//
//   Lectura:   esclavo, función 3 (holding) o 4 (input), registro inicial, cantidad  ->  esclavo, función, bytes, datos
//   Escritura: función 6 (un registro) o 5 (una bobina: 0xFF00 = encendida)          ->  eco de la petición
//   Error:     esclavo, función | 0x80, código de excepción
// Los registros se numeran desde 0 en la trama (el "40001" de los manuales es el registro 0 de la función 3).
#pragma once
#include <stdint.h>
#include <string.h>

// Cómo se arma el valor de un punto con 1 o 2 registros
enum MbTipo : uint8_t { MB_U16 = 0, MB_S16, MB_U32, MB_S32, MB_F32, MB_F32_INV, MB_TIPOS };   // INV = palabras invertidas (CDAB)

inline uint16_t mbCrc(const uint8_t* d, uint16_t n) {
  uint16_t c = 0xFFFF;
  for (uint16_t i = 0; i < n; i++) {
    c ^= d[i];
    for (uint8_t b = 0; b < 8; b++) c = (c & 1) ? (c >> 1) ^ 0xA001 : c >> 1;
  }
  return c;                                    // en la trama va primero el byte bajo
}
inline uint8_t mbRegistros(uint8_t tipo) { return tipo >= MB_U32 ? 2 : 1; }

inline uint8_t mbArmar(uint8_t* t, uint8_t esclavo, uint8_t funcion, uint16_t reg, uint16_t valor) {
  t[0] = esclavo; t[1] = funcion;
  t[2] = reg >> 8; t[3] = reg & 0xFF;
  t[4] = valor >> 8; t[5] = valor & 0xFF;      // cantidad (3/4), valor (6) o 0xFF00/0x0000 (5)
  uint16_t c = mbCrc(t, 6);
  t[6] = c & 0xFF; t[7] = c >> 8;
  return 8;
}
inline uint8_t mbLeer(uint8_t* t, uint8_t esclavo, uint8_t funcion, uint16_t reg, uint8_t tipo) {
  return mbArmar(t, esclavo, funcion, reg, mbRegistros(tipo));
}

// Largo esperado de la respuesta (para saber cuándo terminó de llegar). 0 = aún no se sabe.
inline uint8_t mbLargoRespuesta(const uint8_t* r, uint8_t n) {
  if (n < 2) return 0;
  if (r[1] & 0x80) return 5;
  if (r[1] == 5 || r[1] == 6) return 8;
  if (n < 3) return 0;
  return 5 + r[2];
}

// Resultado de revisar una respuesta
enum MbResultado : int8_t { MB_OK = 0, MB_CORTA = -1, MB_CRC = -2, MB_OTRO = -3, MB_EXCEPCION = -4 };

inline int8_t mbRevisar(const uint8_t* r, uint8_t n, const uint8_t* pedido, uint8_t* excepcion) {
  uint8_t largo = mbLargoRespuesta(r, n);
  if (!largo || n < largo) return MB_CORTA;
  uint16_t c = mbCrc(r, largo - 2);
  if (r[largo - 2] != (c & 0xFF) || r[largo - 1] != (c >> 8)) return MB_CRC;
  if (r[0] != pedido[0] || (r[1] & 0x7F) != pedido[1]) return MB_OTRO;
  if (r[1] & 0x80) { if (excepcion) *excepcion = r[2]; return MB_EXCEPCION; }
  if (pedido[1] == 3 || pedido[1] == 4) {
    uint16_t cant = (pedido[4] << 8) | pedido[5];
    if (r[2] != cant * 2) return MB_OTRO;
  } else if (memcmp(r, pedido, 6)) return MB_OTRO;           // escritura: el esclavo regresa el eco
  return MB_OK;
}

// Valor de una respuesta de lectura ya revisada, por el tipo del punto (sin escala)
inline float mbValor(const uint8_t* r, uint8_t tipo) {
  const uint8_t* d = r + 3;
  uint16_t a = (d[0] << 8) | d[1];
  if (tipo == MB_U16) return a;
  if (tipo == MB_S16) return (int16_t)a;
  uint16_t b = (d[2] << 8) | d[3];
  uint32_t v = tipo == MB_F32_INV ? ((uint32_t)b << 16) | a : ((uint32_t)a << 16) | b;
  if (tipo == MB_U32) return (float)v;
  if (tipo == MB_S32) return (float)(int32_t)v;
  float f;
  memcpy(&f, &v, 4);
  return f;
}

// Silencio entre tramas: 3.5 caracteres (11 bits cada uno); la norma fija 1.75 ms por encima de 19200 baudios
inline uint32_t mbSilencioUs(uint32_t baudios) { return baudios > 19200 ? 1750 : 38500000UL / baudios; }
