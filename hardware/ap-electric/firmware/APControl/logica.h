// AP LÓGICA: el programa de tipo PLC del equipo (escalera / lista de instrucciones, al estilo IEC 61131-3).
// Sin dependencias del hardware: se prueba en la PC con tools/probar_apbus.sh (prueba_logica.cpp).
//
// Cada ciclo (10 ms) se lee la imagen de entradas, se ejecuta el programa de arriba abajo y se escriben las salidas.
// Texto, una instrucción por renglón ("//" o ";" = comentario):
//   Contactos  LD x | LDN x | AND x | ANDN x | OR x | ORN x       x = I3, Q1, M10, T2, C1, L33, P, S2 ...
//              LDP / LDF / ANDP / ANDF / ORP / ORF x             flanco de subida (P) o de bajada (F)
//              LD A1 > 3.5 | AND R2 <= 100 | OR C1 >= 10         comparación (A analógica, R Modbus, C/T valor)
//   Bloques    ANB | ORB | NOT                                   (LD a mitad de un renglón abre un bloque)
//   Bobinas    OUT x | SET x | RST x                             x = Q, M, L, P; RST también para T y C
//   Funciones  TON Tn ms | TOF Tn ms | TP Tn ms | CTU Cn pv | CTD Cn pv
// Áreas: I entradas, Q salidas, M marcas (M1-M64 normales, M65-M128 retentivas), T temporizadores (16),
//        C contadores (16, retentivos), L luminarias, P luz principal, A entradas analógicas, R puntos Modbus,
//        S sistema: S1 primer ciclo, S2 pulso de 1 s, S3 siempre 1, S4 es de noche (horario solar), S5 hay falla.
#pragma once
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <ctype.h>

namespace logica {

const int MAX_INS = 256, N_M = 128, N_T = 16, N_C = 16, M_RETENTIVA = 65;

enum Op : uint8_t { LD, AND, OR, ANB, ORB, NOT, OUT, SET, RST, TON, TOF, TP, CTU, CTD };
enum Cmp : uint8_t { BIT, GT, LT, GE, LE, EQ, NE };
enum Flanco : uint8_t { NADA, SUBE, BAJA };

struct Ins {
  uint8_t op, area, cmp, flanco;   // area = 'I', 'Q', ...
  uint8_t neg, pad;
  uint16_t idx;                    // 1.. (0 para P)
  float val;                       // comparación, tiempo (ms) o preset
};

// Lo que el equipo le da al programa
struct Entorno {
  virtual bool leerBit(char area, int idx) = 0;               // I, Q, L, P, S
  virtual float valor(char area, int idx) = 0;            // A, R
  virtual void escribir(char area, int idx, bool v) = 0;  // Q, L, P
  virtual ~Entorno() {}
};

struct Temporizador { uint32_t et; bool q, in; uint8_t tipo; uint32_t pt; };
struct Contador { int32_t cv, pv; bool q, in; uint8_t tipo; };

struct Programa {
  Ins ins[MAX_INS];
  int n = 0;
  char error[64] = "";
  bool m[N_M + 1] = {};
  Temporizador t[N_T + 1] = {};
  Contador c[N_C + 1] = {};
  bool previo[MAX_INS] = {};       // estado anterior de cada contacto de flanco
  bool primerCiclo = true;
  uint32_t ciclos = 0;
  bool retentivaCambio = false;
  uint8_t flujo[MAX_INS / 8] = {};  // monitoreo en línea: bit i = contacto i cerrado / bobina i con corriente

  static bool areaValida(char a) { return strchr("IQMTCLPARS", a) != nullptr; }

  // Compila el texto; regresa false y llena "error" ("renglón 3: ...") si algo está mal
  bool compilar(const char* txt) {
    n = 0; error[0] = 0;
    int renglon = 0;
    int pila = 0;                   // profundidad de bloques para validar ANB/ORB
    bool enRenglon = false;         // ya hubo un contacto en el renglón actual
    bool trasBobina = false;        // la instrucción anterior fue una bobina o función
    while (*txt) {
      char lin[96]; int k = 0;
      while (*txt && *txt != '\n' && k < 95) lin[k++] = *txt++;
      lin[k] = 0;
      while (*txt && *txt != '\n') txt++;
      if (*txt == '\n') txt++;
      renglon++;
      char* c = strstr(lin, "//"); if (c) *c = 0;
      c = strchr(lin, ';'); if (c) *c = 0;
      char op[8] = "", opnd[16] = "", cmp[4] = "", num[24] = "";
      int campos = sscanf(lin, " %7s %15s %3s %23s", op, opnd, cmp, num);
      if (campos <= 0 || !op[0]) continue;
      for (char* p = op; *p; p++) *p = toupper(*p);
      for (char* p = opnd; *p; p++) *p = toupper(*p);
      if (n >= MAX_INS) return falla(renglon, "programa demasiado largo");
      Ins in{}; in.area = 0;
      // contactos con flanco y negados
      int L = strlen(op);
      if (L >= 3 && (op[L - 1] == 'P' || op[L - 1] == 'F') && (!strncmp(op, "LD", 2) || !strncmp(op, "AND", 3) || !strncmp(op, "OR", 2))
          && strcmp(op, "ORB") && strcmp(op, "ANB")) {
        in.flanco = op[L - 1] == 'P' ? SUBE : BAJA; op[L - 1] = 0;
      }
      L = strlen(op);
      if (!strcmp(op, "LDN") || !strcmp(op, "ANDN") || !strcmp(op, "ORN")) { in.neg = 1; op[L - 1] = 0; }
      if (!strcmp(op, "LD") || !strcmp(op, "AND") || !strcmp(op, "OR")) {
        in.op = !strcmp(op, "LD") ? LD : !strcmp(op, "AND") ? AND : OR;
        if (!operando(opnd, in)) return falla(renglon, "operando no válido");
        if (cmp[0]) {
          in.cmp = !strcmp(cmp, ">") ? GT : !strcmp(cmp, "<") ? LT : !strcmp(cmp, ">=") ? GE : !strcmp(cmp, "<=") ? LE
                 : !strcmp(cmp, "=") || !strcmp(cmp, "==") ? EQ : !strcmp(cmp, "<>") || !strcmp(cmp, "!=") ? NE : 255;
          if (in.cmp == 255 || !num[0]) return falla(renglon, "comparación no válida");
          if (!strchr("ARCT", in.area)) return falla(renglon, "solo A, R, C y T se comparan");
          in.val = (float)atof(num);
        } else if (strchr("AR", in.area)) return falla(renglon, "A y R necesitan una comparación");
        if (in.op == LD) {
          if (trasBobina || !enRenglon) { pila = 0; trasBobina = false; } else pila++;   // renglón nuevo o bloque
          enRenglon = true;
        } else if (!enRenglon || trasBobina) return falla(renglon, "falta LD al inicio del renglón");
      } else if (!strcmp(op, "ANB") || !strcmp(op, "ORB")) {
        in.op = op[0] == 'A' ? ANB : ORB;
        if (pila <= 0 || trasBobina) return falla(renglon, "ANB/ORB sin bloque abierto");
        pila--;
      } else if (!strcmp(op, "NOT")) {
        in.op = NOT; if (!enRenglon || trasBobina) return falla(renglon, "falta LD al inicio del renglón");
      } else if (!strcmp(op, "OUT") || !strcmp(op, "SET") || !strcmp(op, "RST") || !strcmp(op, "ST") || !strcmp(op, "S") || !strcmp(op, "R")) {
        in.op = (!strcmp(op, "OUT") || !strcmp(op, "ST")) ? OUT : (op[0] == 'S') ? SET : RST;
        if (!enRenglon) return falla(renglon, "bobina sin contactos");
        if (pila) return falla(renglon, "bloque sin cerrar (falta ANB u ORB)");
        if (!operando(opnd, in)) return falla(renglon, "operando no válido");
        if (in.op == RST ? !strchr("QMLPTC", in.area) : !strchr("QMLP", in.area)) return falla(renglon, "no se puede escribir ahí");
      } else if (!strcmp(op, "TON") || !strcmp(op, "TOF") || !strcmp(op, "TP") || !strcmp(op, "CTU") || !strcmp(op, "CTD")) {
        in.op = !strcmp(op, "TON") ? TON : !strcmp(op, "TOF") ? TOF : !strcmp(op, "TP") ? TP : !strcmp(op, "CTU") ? CTU : CTD;
        if (!enRenglon) return falla(renglon, "función sin contactos");
        if (pila) return falla(renglon, "bloque sin cerrar (falta ANB u ORB)");
        if (!operando(opnd, in) || in.area != (in.op <= TP ? 'T' : 'C')) return falla(renglon, in.op <= TP ? "usa un T" : "usa un C");
        if (!cmp[0]) return falla(renglon, in.op <= TP ? "falta el tiempo en ms" : "falta el preset");
        in.val = (float)atof(cmp);
        if (in.val < 0) return falla(renglon, "valor negativo");
      } else return falla(renglon, "instrucción desconocida");
      ins[n++] = in;
      if (in.op >= OUT) trasBobina = true;   // varias bobinas seguidas comparten el resultado; un LD abre otro renglón
    }
    if (pila) return falla(renglon, "bloque sin cerrar al final");
    return true;
  }

  // Un ciclo de programa; dt en ms
  void ciclo(Entorno& e, uint32_t dt) {
    bool pila[32]; int sp = 0;
    bool acc = false, despuesDeBobina = true;
    for (int i = 0; i < n; i++) {
      const Ins& in = ins[i];
      switch (in.op) {
        case LD: case AND: case OR: {
          bool v = leer(e, in);
          if (in.flanco) { bool p = previo[i]; previo[i] = v; v = in.flanco == SUBE ? (v && !p) : (!v && p); }
          if (in.neg) v = !v;
          marca(i, v);
          if (in.op == LD) {
            if (despuesDeBobina) { sp = 0; despuesDeBobina = false; }
            else if (sp < 32) pila[sp++] = acc;
            acc = v;
          } else if (in.op == AND) acc = acc && v;
          else acc = acc || v;
        } break;
        case ANB: if (sp) acc = pila[--sp] && acc; marca(i, acc); break;
        case ORB: if (sp) acc = pila[--sp] || acc; marca(i, acc); break;
        case NOT: acc = !acc; marca(i, acc); break;
        case OUT: marca(i, acc); escribir(e, in.area, in.idx, acc); despuesDeBobina = true; break;
        case SET: marca(i, acc); if (acc) escribir(e, in.area, in.idx, true); despuesDeBobina = true; break;
        case RST:
          marca(i, acc);
          if (acc) {
            if (in.area == 'T' && in.idx <= N_T) t[in.idx] = Temporizador{};
            else if (in.area == 'C' && in.idx <= N_C) {           // CTU vuelve a 0; CTD vuelve a su preset
              Contador& x = c[in.idx]; x.cv = x.tipo == CTD ? x.pv : 0; x.q = false; retentivaCambio = true;
            }
            else escribir(e, in.area, in.idx, false);
          }
          despuesDeBobina = true; break;
        case TON: case TOF: case TP: marca(i, acc); temporizar(in, acc, dt); despuesDeBobina = true; break;
        case CTU: case CTD: marca(i, acc); contar(in, acc); despuesDeBobina = true; break;
      }
    }
    primerCiclo = false;
    ciclos++;
  }

  // valor de un temporizador / contador (para la app)
  uint32_t et(int k) const { return (k >= 1 && k <= N_T) ? t[k].et : 0; }
  int32_t cv(int k) const { return (k >= 1 && k <= N_C) ? c[k].cv : 0; }

 private:
  void marca(int i, bool v) { if (v) flujo[i >> 3] |= 1 << (i & 7); else flujo[i >> 3] &= ~(1 << (i & 7)); }
  bool falla(int r, const char* m) { snprintf(error, sizeof(error), "renglon %d: %s", r, m); n = 0; return false; }
  static bool operando(const char* s, Ins& in) {
    if (!s[0] || !areaValida(s[0])) return false;
    in.area = s[0];
    if (in.area == 'P') { in.idx = 0; return s[1] == 0; }
    if (!isdigit((unsigned char)s[1])) return false;
    long v = strtol(s + 1, nullptr, 10);
    if (v < 1 || v > 999) return false;
    if (in.area == 'M' && v > N_M) return false;
    if (in.area == 'T' && v > N_T) return false;
    if (in.area == 'C' && v > N_C) return false;
    in.idx = (uint16_t)v;
    return true;
  }
  bool leer(Entorno& e, const Ins& in) {
    if (in.cmp != BIT) {
      float v = in.area == 'C' ? (float)c[in.idx].cv : in.area == 'T' ? (float)t[in.idx].et : e.valor(in.area, in.idx);
      if (v != v) return false;                         // sin lectura (NaN): falso
      switch (in.cmp) {
        case GT: return v > in.val; case LT: return v < in.val; case GE: return v >= in.val;
        case LE: return v <= in.val; case EQ: return v == in.val; default: return v != in.val;
      }
    }
    switch (in.area) {
      case 'M': return m[in.idx];
      case 'T': return t[in.idx].q;
      case 'C': return c[in.idx].q;
      case 'S': if (in.idx == 1) return primerCiclo; return e.leerBit('S', in.idx);
      default: return e.leerBit(in.area, in.idx);
    }
  }
  void escribir(Entorno& e, char area, int idx, bool v) {
    if (area == 'M') { if (m[idx] != v && idx >= M_RETENTIVA) retentivaCambio = true; m[idx] = v; }
    else e.escribir(area, idx, v);
  }
  void temporizar(const Ins& in, bool en, uint32_t dt) {
    Temporizador& x = t[in.idx];
    uint32_t pt = (uint32_t)in.val;
    x.pt = pt; x.tipo = in.op;
    if (in.op == TON) {
      if (en) { if (x.et < pt) x.et = (x.et + dt > pt) ? pt : x.et + dt; } else x.et = 0;
      x.q = en && x.et >= pt;
    } else if (in.op == TOF) {
      if (en) { x.et = 0; x.q = true; }
      else if (x.q) { x.et = (x.et + dt > pt) ? pt : x.et + dt; if (x.et >= pt) x.q = false; }
    } else {                                           // TP: pulso de pt al subir la entrada
      if (en && !x.in && !x.q) { x.q = true; x.et = 0; }
      if (x.q) { x.et = (x.et + dt > pt) ? pt : x.et + dt; if (x.et >= pt) x.q = false; }
      if (!x.q && !en) x.et = 0;
    }
    x.in = en;
  }
  void contar(const Ins& in, bool en) {
    Contador& x = c[in.idx];
    x.pv = (int32_t)in.val;
    if (x.tipo != in.op) { x.tipo = in.op; if (in.op == CTD && x.cv == 0) x.cv = x.pv; }   // CTD empieza en su preset
    if (en && !x.in) { x.cv += in.op == CTU ? 1 : -1; retentivaCambio = true; }
    x.in = en;
    x.q = in.op == CTU ? x.cv >= x.pv : x.cv <= 0;
  }
};

}  // namespace logica
