// Pruebas en la PC de AP LÓGICA (logica.h): compilación, contactos, bloques, flancos, temporizadores y contadores.
#include "../LetreroLabAP1/logica.h"
#include <cstdio>
#include <cmath>
static int fallas = 0;
#define REVISA(c) do { if (!(c)) { printf("  falla en la línea %d: %s\n", __LINE__, #c); fallas++; } } while (0)

struct Simulado : logica::Entorno {
  bool I[17] = {}, Q[17] = {}, L[37] = {}, P = false, noche = false;
  float A[9] = {};
  bool leerBit(char a, int i) override {
    if (a == 'I') return I[i];
    if (a == 'Q') return Q[i];
    if (a == 'L') return L[i];
    if (a == 'P') return P;
    if (a == 'S') return i == 3 ? true : i == 4 ? noche : false;
    return false;
  }
  float valor(char a, int i) override { return a == 'A' ? A[i] : NAN; }
  void escribir(char a, int i, bool v) override { if (a == 'Q') Q[i] = v; else if (a == 'L') L[i] = v; else if (a == 'P') P = v; }
};

static void correr(logica::Programa& p, Simulado& e, int ms) { for (int t = 0; t < ms; t += 10) p.ciclo(e, 10); }

int main() {
  // 1) arranque y paro con autorretención: (I1 OR Q1) AND NOT I2 -> Q1
  {
    logica::Programa p; Simulado e;
    REVISA(p.compilar("// motor\nLD I1\nOR Q1\nANDN I2\nOUT Q1\n"));
    correr(p, e, 20); REVISA(!e.Q[1]);
    e.I[1] = true; correr(p, e, 20); REVISA(e.Q[1]);
    e.I[1] = false; correr(p, e, 20); REVISA(e.Q[1]);          // se queda
    e.I[2] = true; correr(p, e, 20); REVISA(!e.Q[1]);          // paro
    e.I[2] = false; correr(p, e, 20); REVISA(!e.Q[1]);
  }
  // 2) TON 500 ms, TOF 300 ms, TP 200 ms
  {
    logica::Programa p; Simulado e;
    REVISA(p.compilar("LD I1\nTON T1 500\nLD T1\nOUT Q1\nLD I2\nTOF T2 300\nLD T2\nOUT Q2\nLDP I3\nTP T3 200\nLD T3\nOUT Q3"));
    e.I[1] = true; correr(p, e, 490); REVISA(!e.Q[1]); correr(p, e, 30); REVISA(e.Q[1]);
    e.I[1] = false; correr(p, e, 10); REVISA(!e.Q[1]);
    e.I[2] = true; correr(p, e, 20); REVISA(e.Q[2]);
    e.I[2] = false; correr(p, e, 280); REVISA(e.Q[2]); correr(p, e, 40); REVISA(!e.Q[2]);
    e.I[3] = true; correr(p, e, 100); REVISA(e.Q[3]); correr(p, e, 200); REVISA(!e.Q[3]);   // pulso aunque siga en 1
    REVISA(p.et(1) == 0);
  }
  // 2b) tiempos y presets de 4 o más cifras (antes se cortaban a 3: TON T1 3000 valía 300 ms)
  {
    logica::Programa p; Simulado e;
    REVISA(p.compilar("LD I1\nTON T1 3000\nLD T1\nOUT Q1\nLD I2\nTON T2 12000\nLD T2\nOUT Q2\nLD I3\nCTU C1 1000\nLD C1\nOUT Q3"));
    REVISA(p.ins[1].val == 3000.0f && p.ins[5].val == 12000.0f && p.ins[9].val == 1000.0f);
    e.I[1] = true; correr(p, e, 2900); REVISA(!e.Q[1]); correr(p, e, 200); REVISA(e.Q[1]);
    e.I[2] = true; correr(p, e, 11900); REVISA(!e.Q[2]); correr(p, e, 200); REVISA(e.Q[2]);
    REVISA(!p.compilar("LD I1\nTON T1 -5"));
  }
  // 3) contador de piezas con flanco: 3 pulsos -> Q1; RST con I2
  {
    logica::Programa p; Simulado e;
    REVISA(p.compilar("LD I1\nCTU C1 3\nLD C1\nOUT Q1\nLD I2\nRST C1"));
    for (int k = 0; k < 3; k++) { e.I[1] = true; correr(p, e, 20); e.I[1] = false; correr(p, e, 20); }
    REVISA(p.cv(1) == 3 && e.Q[1]);
    e.I[2] = true; correr(p, e, 20); e.I[2] = false; correr(p, e, 20);
    REVISA(p.cv(1) == 0 && !e.Q[1]);
    REVISA(p.retentivaCambio);
    REVISA((p.flujo[0] & 0x3F) == 0);                           // monitoreo: nada cerrado
    e.I[2] = true; correr(p, e, 10); REVISA((p.flujo[0] & 0x30) == 0x30);   // LD I2 y RST C1 con corriente
  }
  // 4) bloques: (I1 AND I2) OR (I3 AND I4) -> Q1 ; SET / RST con flancos
  {
    logica::Programa p; Simulado e;
    REVISA(p.compilar("LD I1\nAND I2\nLD I3\nAND I4\nORB\nOUT Q1\nLDP I5\nSET M70\nLDF I5\nRST M2\nLD M70\nOUT L33"));
    e.I[3] = e.I[4] = true; correr(p, e, 10); REVISA(e.Q[1]);
    e.I[4] = false; correr(p, e, 10); REVISA(!e.Q[1]);
    e.I[1] = e.I[2] = true; correr(p, e, 10); REVISA(e.Q[1]);
    e.I[5] = true; correr(p, e, 10); REVISA(p.m[70] && e.L[33] && p.retentivaCambio);
  }
  // 5) comparación analógica con histéresis por SET/RST: A1 > 3.5 enciende, A1 < 2 apaga
  {
    logica::Programa p; Simulado e;
    REVISA(p.compilar("LD A1 > 3.5\nSET Q4\nLD A1 < 2\nRST Q4\nLD S4\nAND P\nOUT L1\nLD C2 >= 0\nOUT M1"));
    e.A[1] = 3.0f; correr(p, e, 10); REVISA(!e.Q[4]);
    e.A[1] = 4.0f; correr(p, e, 10); REVISA(e.Q[4]);
    e.A[1] = 3.0f; correr(p, e, 10); REVISA(e.Q[4]);
    e.A[1] = 1.0f; correr(p, e, 10); REVISA(!e.Q[4]);
    e.noche = true; e.P = true; correr(p, e, 10); REVISA(e.L[1]);
    REVISA(p.m[1]);
  }
  // 6) CTD empieza en su preset; S1 solo en el primer ciclo
  {
    logica::Programa p; Simulado e;
    REVISA(p.compilar("LD I1\nCTD C1 2\nLD C1\nOUT Q1\nLD S1\nSET M3"));
    correr(p, e, 10); REVISA(p.cv(1) == 2 && !e.Q[1] && p.m[3]);
    p.m[3] = false; correr(p, e, 10); REVISA(!p.m[3]);
    for (int k = 0; k < 2; k++) { e.I[1] = true; correr(p, e, 10); e.I[1] = false; correr(p, e, 10); }
    REVISA(p.cv(1) == 0 && e.Q[1]);
  }
  // 7) errores con su renglón
  {
    logica::Programa p;
    REVISA(!p.compilar("LD I1\nOUT X3")); REVISA(strstr(p.error, "renglon 2"));
    REVISA(!p.compilar("AND I1\nOUT Q1")); REVISA(strstr(p.error, "renglon 1"));
    REVISA(!p.compilar("LD I1\nLD I2\nOUT Q1")); REVISA(strstr(p.error, "bloque sin cerrar"));
    REVISA(!p.compilar("LD A1\nOUT Q1"));
    REVISA(!p.compilar("LD I1\nTON C1 100"));
    REVISA(!p.compilar("LD I1\nOUT Q1\nAND I2\nOUT Q2"));
    REVISA(!p.compilar("LD M200\nOUT Q1"));
    REVISA(p.compilar("ld i1 ; comentario\nout q1"));
    REVISA(p.n == 2);
  }
  printf(fallas ? "%d FALLAS\n" : "AP LÓGICA: todo bien\n", fallas);
  return fallas != 0;
}
