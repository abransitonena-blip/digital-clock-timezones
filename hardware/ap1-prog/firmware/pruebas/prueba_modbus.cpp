// Prueba en la PC del maestro Modbus RTU (modbus.h):  bash tools/probar_apbus.sh
#include <cstdio>
#include <cmath>
#include "../LetreroLabAP1/modbus.h"

static int fallas = 0;
#define REVISA(c) do { if (!(c)) { printf("FALLA linea %d: %s\n", __LINE__, #c); fallas++; } } while (0)

static uint8_t conCrc(uint8_t* t, uint8_t n) { uint16_t c = mbCrc(t, n); t[n] = c & 0xFF; t[n + 1] = c >> 8; return n + 2; }

int main() {
  uint8_t t[8];
  // ejemplos clásicos de la guía Modbus: 01 03 00 00 00 0A -> C5 CD ; 01 06 00 01 00 03 -> 98 0B
  mbArmar(t, 1, 3, 0, 10);
  REVISA(t[6] == 0xC5 && t[7] == 0xCD);
  mbArmar(t, 1, 6, 1, 3);
  REVISA(t[6] == 0x98 && t[7] == 0x0B);
  // lectura de un float (medidor de energía: voltaje 230.0 V = 0x43660000) con 2 registros
  uint8_t p[8];
  mbLeer(p, 2, 4, 0, MB_F32);
  REVISA(p[4] == 0 && p[5] == 2);
  uint8_t r[16] = {2, 4, 4, 0x43, 0x66, 0x00, 0x00};
  uint8_t n = conCrc(r, 7);
  REVISA(mbLargoRespuesta(r, 3) == 9 && n == 9);
  REVISA(mbRevisar(r, n, p, nullptr) == MB_OK);
  REVISA(fabsf(mbValor(r, MB_F32) - 230.0f) < 1e-4);
  // palabras invertidas (CDAB)
  uint8_t r2[16] = {2, 4, 4, 0x00, 0x00, 0x43, 0x66};
  REVISA(fabsf(mbValor(r2, MB_F32_INV) - 230.0f) < 1e-4);
  // enteros
  uint8_t r3[16] = {1, 3, 4, 0xFF, 0xFE, 0x00, 0x01};
  REVISA(mbValor(r3, MB_S16) == -2 && mbValor(r3, MB_U16) == 65534);
  REVISA(mbValor(r3, MB_S32) == (float)(int32_t)0xFFFE0001);
  // errores
  r[4] ^= 1;
  REVISA(mbRevisar(r, n, p, nullptr) == MB_CRC);
  r[4] ^= 1;
  REVISA(mbRevisar(r, n - 1, p, nullptr) == MB_CORTA);
  uint8_t p3[8]; mbLeer(p3, 3, 4, 0, MB_F32);
  REVISA(mbRevisar(r, n, p3, nullptr) == MB_OTRO);              // respondió otro esclavo
  uint8_t ex[8] = {2, 0x84, 0x02}; uint8_t ne = conCrc(ex, 3), cod = 0;
  REVISA(mbRevisar(ex, ne, p, &cod) == MB_EXCEPCION && cod == 2);   // dirección no válida
  // escritura: eco
  uint8_t w[8]; mbArmar(w, 5, 5, 0, 0xFF00);
  REVISA(mbRevisar(w, 8, w, nullptr) == MB_OK && mbLargoRespuesta(w, 2) == 8);
  // silencio entre tramas
  REVISA(mbSilencioUs(9600) == 4010 && mbSilencioUs(115200) == 1750);
  printf(fallas ? "%d FALLAS\n" : "Modbus: todo bien\n", fallas);
  return fallas != 0;
}
