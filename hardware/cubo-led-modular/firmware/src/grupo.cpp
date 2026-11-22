#include "grupo.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>

namespace ap {

// ---------------- SHA-256 (FIPS 180-4) ----------------
static const uint32_t K[64] = {
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01,
  0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
  0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
  0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
  0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116, 0x1e376c08,
  0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
  0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2};
static inline uint32_t rotr(uint32_t x, int n) { return (x >> n) | (x << (32 - n)); }
static void bloque(uint32_t h[8], const uint8_t* p) {
  uint32_t w[64];
  for (int i = 0; i < 16; ++i) w[i] = (uint32_t)p[4 * i] << 24 | (uint32_t)p[4 * i + 1] << 16 | (uint32_t)p[4 * i + 2] << 8 | p[4 * i + 3];
  for (int i = 16; i < 64; ++i) {
    uint32_t s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >> 3);
    uint32_t s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >> 10);
    w[i] = w[i - 16] + s0 + w[i - 7] + s1;
  }
  uint32_t a = h[0], b = h[1], c = h[2], d = h[3], e = h[4], f = h[5], g = h[6], hh = h[7];
  for (int i = 0; i < 64; ++i) {
    uint32_t t1 = hh + (rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)) + ((e & f) ^ (~e & g)) + K[i] + w[i];
    uint32_t t2 = (rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)) + ((a & b) ^ (a & c) ^ (b & c));
    hh = g; g = f; f = e; e = d + t1; d = c; c = b; b = a; a = t1 + t2;
  }
  h[0] += a; h[1] += b; h[2] += c; h[3] += d; h[4] += e; h[5] += f; h[6] += g; h[7] += hh;
}
void sha256(const uint8_t* d, size_t n, uint8_t out[32]) {
  uint32_t h[8] = {0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19};
  size_t i = 0;
  for (; i + 64 <= n; i += 64) bloque(h, d + i);
  uint8_t fin[128] = {}; size_t r = n - i;
  memcpy(fin, d + i, r); fin[r] = 0x80;
  size_t total = r + 1 + 8 <= 64 ? 64 : 128;
  uint64_t bits = (uint64_t)n * 8;
  for (int k = 0; k < 8; ++k) fin[total - 1 - k] = (uint8_t)(bits >> (8 * k));
  bloque(h, fin); if (total == 128) bloque(h, fin + 64);
  for (int k = 0; k < 8; ++k) { out[4 * k] = h[k] >> 24; out[4 * k + 1] = h[k] >> 16; out[4 * k + 2] = h[k] >> 8; out[4 * k + 3] = h[k]; }
}
void hmacSha256(const uint8_t* key, size_t nk, const uint8_t* msg, size_t n, uint8_t out[32]) {
  uint8_t k0[64] = {}, buf[64 + 256], ih[32];
  if (nk > 64) sha256(key, nk, k0); else memcpy(k0, key, nk);
  if (n > 256) n = 256;                                  // los mensajes de grupo son cortos
  for (int i = 0; i < 64; ++i) buf[i] = k0[i] ^ 0x36;
  memcpy(buf + 64, msg, n); sha256(buf, 64 + n, ih);
  uint8_t ob[96];
  for (int i = 0; i < 64; ++i) ob[i] = k0[i] ^ 0x5c;
  memcpy(ob + 64, ih, 32); sha256(ob, 96, out);
}

// ---------------- Mensajes de grupo ----------------
static bool igualCI(const char* a, const char* b) {
  while (*a && *b) { if (toupper((unsigned char)*a) != toupper((unsigned char)*b)) return false; ++a; ++b; }
  return !*a && !*b;
}
bool comandoDeGrupoPermitido(const char* cmd) {
  char p[12]; size_t i = 0;
  while (cmd[i] && cmd[i] != ' ' && i < sizeof p - 1) { p[i] = cmd[i]; ++i; }
  p[i] = 0;
  static const char* ok[] = {"ON", "OFF", "BRILLO", "RGBW", "MODO", "ESCENA", "CCT"};
  for (const char* o : ok) if (igualCI(p, o)) return !(igualCI(p, "ESCENA") && strstr(cmd, "GUARDAR"));
  return false;
}
static bool nombreValido(const char* g) {
  size_t n = strlen(g);
  if (n < 1 || n > 24) return false;
  for (size_t i = 0; i < n; ++i) if (!isalnum((unsigned char)g[i]) && g[i] != '-' && g[i] != '_') return false;
  return true;
}
static void firma16(const char* clave, const char* cuerpo, size_t n, char out[17]) {
  uint8_t m[32]; hmacSha256((const uint8_t*)clave, strlen(clave), (const uint8_t*)cuerpo, n, m);
  for (int i = 0; i < 8; ++i) snprintf(out + 2 * i, 3, "%02x", m[i]);
}
size_t firmarGrupo(const char* grupo, const char* clave, uint64_t contador, const char* cmd, char* out, size_t n) {
  if (!nombreValido(grupo) || strlen(clave) < 8 || !comandoDeGrupoPermitido(cmd) || strlen(cmd) > 60) return 0;
  int k = snprintf(out, n, "APG1 %s %llu %s", grupo, (unsigned long long)contador, cmd);
  if (k < 0 || (size_t)k + 18 > n) return 0;
  char f[17]; firma16(clave, out, (size_t)k, f);
  out[k] = ' '; memcpy(out + k + 1, f, 17);
  return (size_t)k + 17;
}
Rechazo verificarGrupo(const char* msg, const char* grupo, const char* clave, uint64_t& ultimo,
                       uint64_t ahora, char* cmd, size_t ncmd) {
  size_t L = strnlen(msg, 160);
  if (L < 30 || L >= 160 || strncmp(msg, "APG1 ", 5)) return Rechazo::FORMATO;
  const char* sp = strrchr(msg, ' ');
  if (!sp || strlen(sp + 1) != 16) return Rechazo::FORMATO;
  size_t cuerpo = (size_t)(sp - msg);
  const char* g = msg + 5; const char* g_fin = strchr(g, ' ');
  if (!g_fin || g_fin > sp) return Rechazo::FORMATO;
  if ((size_t)(g_fin - g) != strlen(grupo) || strncmp(g, grupo, g_fin - g)) return Rechazo::OTRO_GRUPO;
  char* e; unsigned long long cont = strtoull(g_fin + 1, &e, 10);
  if (e == g_fin + 1 || *e != ' ' || e >= sp) return Rechazo::FORMATO;
  char f[17]; firma16(clave, msg, cuerpo, f);
  uint8_t dif = 0; for (int i = 0; i < 16; ++i) dif |= (uint8_t)(f[i] ^ sp[1 + i]);   // tiempo constante
  if (dif) return Rechazo::FIRMA;
  if (cont <= ultimo) return Rechazo::REPETIDO;
  if (ahora) { long long d = (long long)cont - (long long)ahora; if (d > 120000 || d < -120000) return Rechazo::FUERA_DE_HORA; }
  size_t nc = (size_t)(sp - (e + 1));
  if (nc == 0 || nc >= ncmd) return Rechazo::FORMATO;
  memcpy(cmd, e + 1, nc); cmd[nc] = 0;
  if (!comandoDeGrupoPermitido(cmd)) return Rechazo::NO_PERMITIDO;
  ultimo = cont;
  return Rechazo::NINGUNO;
}

} // namespace ap
