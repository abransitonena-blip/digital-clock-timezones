// g++ -std=c++17 -I../src test_grupo.cpp ../src/grupo.cpp -o tg && ./tg
#include "grupo.h"
#include <cstdio>
#include <cstring>
#include <string>
using namespace ap;
static int fallos = 0, total = 0;
#define CHECK(c) do { ++total; if (!(c)) { ++fallos; printf("FALLO %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)
static std::string hex(const uint8_t* d, size_t n) { std::string s; char b[3]; for (size_t i = 0; i < n; ++i) { snprintf(b, 3, "%02x", d[i]); s += b; } return s; }

int main() {
  uint8_t h[32];
  // Vectores oficiales FIPS 180-2
  sha256((const uint8_t*)"abc", 3, h); CHECK(hex(h, 32) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
  sha256((const uint8_t*)"", 0, h); CHECK(hex(h, 32) == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
  const char* m2 = "abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq";
  sha256((const uint8_t*)m2, strlen(m2), h); CHECK(hex(h, 32) == "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1");
  std::string mil(1000000, 'a'); sha256((const uint8_t*)mil.data(), mil.size(), h);
  CHECK(hex(h, 32) == "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0");
  for (size_t n : {55u, 56u, 63u, 64u, 65u}) { std::string s(n, 'x'); sha256((const uint8_t*)s.data(), n, h); CHECK(h[0] || h[1]); }   // bordes del relleno
  // RFC 4231, casos 2 y 1
  hmacSha256((const uint8_t*)"Jefe", 4, (const uint8_t*)"what do ya want for nothing?", 28, h);
  CHECK(hex(h, 32) == "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843");
  uint8_t k1[20]; memset(k1, 0x0b, 20); hmacSha256(k1, 20, (const uint8_t*)"Hi There", 8, h);
  CHECK(hex(h, 32) == "b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7");
  uint8_t k6[131]; memset(k6, 0xaa, 131);        // caso 6: clave más larga que el bloque
  const char* m6 = "Test Using Larger Than Block-Size Key - Hash Key First";
  hmacSha256(k6, 131, (const uint8_t*)m6, strlen(m6), h);
  CHECK(hex(h, 32) == "60e431591ee0b67f0d8a26aacbf5b77f8e0bc6213728c5140546040f0ee37f54");

  // Mensajes de grupo
  char msg[160], cmd[64]; uint64_t ult = 0;
  const char* G = "tienda-centro"; const char* C = "clave-secreta-1";
  CHECK(firmarGrupo(G, C, 1000, "BRILLO 40", msg, sizeof msg) > 0);
  CHECK(verificarGrupo(msg, G, C, ult, 0, cmd, sizeof cmd) == Rechazo::NINGUNO && !strcmp(cmd, "BRILLO 40") && ult == 1000);
  CHECK(verificarGrupo(msg, G, C, ult, 0, cmd, sizeof cmd) == Rechazo::REPETIDO);              // repetición
  CHECK(verificarGrupo(msg, "otro", C, ult, 0, cmd, sizeof cmd) == Rechazo::OTRO_GRUPO);
  uint64_t u2 = 0; CHECK(verificarGrupo(msg, G, "otra-clave-xx", u2, 0, cmd, sizeof cmd) == Rechazo::FIRMA);
  std::string alt(msg); alt.replace(alt.find("40"), 2, "99");                                    // alterado en el camino
  u2 = 0; CHECK(verificarGrupo(alt.c_str(), G, C, u2, 0, cmd, sizeof cmd) == Rechazo::FIRMA);
  CHECK(firmarGrupo(G, C, 5, "WIFI red clave", msg, sizeof msg) == 0);                          // no se firman órdenes peligrosas
  CHECK(firmarGrupo(G, C, 5, "LIMITES 24 5", msg, sizeof msg) == 0 && firmarGrupo(G, C, 5, "ESCENA GUARDAR 1", msg, sizeof msg) == 0);
  CHECK(firmarGrupo(G, "corta", 5, "ON", msg, sizeof msg) == 0 && firmarGrupo("con espacio", C, 5, "ON", msg, sizeof msg) == 0);
  // aunque alguien con la clave firme "a mano" una orden prohibida, el receptor la rechaza
  { char cuerpo[100]; int k = snprintf(cuerpo, sizeof cuerpo, "APG1 %s 2000 DMX OFF", G);
    uint8_t m[32]; hmacSha256((const uint8_t*)C, strlen(C), (const uint8_t*)cuerpo, k, m);
    std::string falso = std::string(cuerpo) + " " + hex(m, 8);
    CHECK(verificarGrupo(falso.c_str(), G, C, ult, 0, cmd, sizeof cmd) == Rechazo::NO_PERMITIDO); }
  // con hora: el contador es la hora en ms y debe estar a ±120 s
  uint64_t ahora = 1767225600000ull; ult = 0;
  firmarGrupo(G, C, ahora + 5000, "ON", msg, sizeof msg);
  CHECK(verificarGrupo(msg, G, C, ult, ahora, cmd, sizeof cmd) == Rechazo::NINGUNO);
  firmarGrupo(G, C, ahora - 600000, "OFF", msg, sizeof msg); ult = 0;
  CHECK(verificarGrupo(msg, G, C, ult, ahora, cmd, sizeof cmd) == Rechazo::FUERA_DE_HORA);
  // basura no rompe nada
  const char* malos[] = {"", "APG1", "APG1 x 1 ON 0123456789abcdef", "APG1 tienda-centro abc ON 0123456789abcdef", "hola mundo cualquier cosa larga 0123456789abcdef"};
  for (const char* m : malos) { uint64_t u = 0; CHECK(verificarGrupo(m, G, C, u, 0, cmd, sizeof cmd) != Rechazo::NINGUNO); }
  for (int k = 0; k < 3000; ++k) { char b[160]; for (int i = 0; i < 159; ++i) b[i] = (char)(32 + (k * 131 + i * 17) % 95); b[159] = 0; memcpy(b, "APG1 ", 5); uint64_t u = 0; verificarGrupo(b, G, C, u, 0, cmd, sizeof cmd); }
  printf("%d/%d pruebas de grupo OK\n", total - fallos, total);
  return fallos ? 1 : 0;
}
