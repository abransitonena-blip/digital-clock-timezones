// AP Control: autoprueba de puesta en marcha del 7R Tour. Aquí solo está la evaluación (pura, se prueba en la PC);
// las lecturas y el accionamiento de los relés los hace el programa del equipo (APControl.ino, orden TEST).
//
//  TEST        no acciona nada: mira el I2C, la identificación de la placa, el DIP, los botones, el conteo rápido y el reloj.
//  TEST RELES  además enciende cada relé 150 ms y comprueba que SOLO su bobina se energiza. Hay que desconectar las
//              cargas antes: los contactos hacen clic. Solo se permite con la unidad en STOPPED y el PLC detenido.
#pragma once
#include <stdint.h>
#include <stdio.h>

namespace apc {

struct LecturaBasica {
  bool i2cSalidas, i2cEntradas, i2cRetro, i2cBotones;     // 0x20, 0x21, 0x22, 0x23 contestan
  bool rtcResponde, rtcHoraBuena;                          // 0x51 contesta / la hora que leyó es creíble
  bool idCorrecto;                                         // P7 de 0x20 = 0 (7R Tour)
  uint8_t bobinas, forzado;                                // retroalimentación con todas las salidas apagadas
  uint8_t botones, entradas;                               // botones y entradas estables (bit = activa)
  bool nivelIo0, nivelIo20;                                // nivel de IO0 (entrada 1) e IO20 (entrada 2): 1 = reposo
};

enum FallaPrueba : uint16_t {
  PT_I2C_SALIDAS = 1, PT_I2C_ENTRADAS = 2, PT_I2C_RETRO = 4, PT_I2C_BOTONES = 8, PT_ID = 16, PT_FORZADO = 32,
  PT_BOTON_PRESIONADO = 64, PT_CONTEO_E1 = 128, PT_CONTEO_E2 = 256,
  PT_AVISO_RTC_AUSENTE = 512, PT_AVISO_RTC_HORA = 1024        // avisos: el resto del equipo funciona sin reloj
};
const uint16_t PT_AVISOS = PT_AVISO_RTC_AUSENTE | PT_AVISO_RTC_HORA;

inline uint16_t evaluarBasica(const LecturaBasica& l) {
  uint16_t f = 0;
  if (!l.i2cSalidas) f |= PT_I2C_SALIDAS;
  if (!l.i2cEntradas) f |= PT_I2C_ENTRADAS;
  if (!l.i2cRetro) f |= PT_I2C_RETRO;
  if (!l.i2cBotones) f |= PT_I2C_BOTONES;
  if (l.i2cSalidas && !l.idCorrecto) f |= PT_ID;
  if (l.i2cRetro && (l.bobinas || l.forzado)) f |= PT_FORZADO;
  if (l.i2cBotones && l.botones) f |= PT_BOTON_PRESIONADO;
  if (l.i2cEntradas) {                                     // IO0 e IO20 deben ver lo mismo que el expansor (nivel 0 = activa)
    if ((l.nivelIo0 == 0) != ((l.entradas & 1) != 0)) f |= PT_CONTEO_E1;
    if ((l.nivelIo20 == 0) != ((l.entradas & 2) != 0)) f |= PT_CONTEO_E2;
  }
  if (!l.rtcResponde) f |= PT_AVISO_RTC_AUSENTE;
  else if (!l.rtcHoraBuena) f |= PT_AVISO_RTC_HORA;
  return f;
}

inline const char* describirFalla(uint16_t bit) {
  switch (bit) {
    case PT_I2C_SALIDAS: return "no contesta el expansor de salidas (0x20)";
    case PT_I2C_ENTRADAS: return "no contesta el expansor de entradas (0x21)";
    case PT_I2C_RETRO: return "no contesta el expansor de retroalimentación (0x22)";
    case PT_I2C_BOTONES: return "no contesta el expansor de botones (0x23)";
    case PT_ID: return "la identificación de la placa no es 7R Tour (P7 de 0x20 debe estar en 0)";
    case PT_FORZADO: return "hay una bobina con tensión con todas las salidas apagadas (DIP en ON, 24 V o ULN2003 en corto)";
    case PT_BOTON_PRESIONADO: return "hay un botón de canal presionado o en corto";
    case PT_CONTEO_E1: return "IO0 no coincide con la entrada 1 (revisar la unión del optoacoplador 1 con IO0)";
    case PT_CONTEO_E2: return "IO20 no coincide con la entrada 2 (revisar la unión del optoacoplador 2 con IO20)";
    case PT_AVISO_RTC_AUSENTE: return "aviso: no contesta el reloj de tiempo real (0x51)";
    case PT_AVISO_RTC_HORA: return "aviso: el reloj perdió la hora (falta la batería) o no está ajustado";
  }
  return "";
}

// Un relé: bobinas vistas con ese relé encendido y con todo apagado.
const uint8_t PR_NO_ENERGIZA = 1, PR_OTRA_BOBINA = 2, PR_NO_SUELTA = 4, PR_SIN_RETRO = 8;
inline uint8_t evaluarRele(uint8_t k, uint8_t bobinasEncendido, uint8_t bobinasApagado, bool hayRetro) {
  if (!hayRetro) return PR_SIN_RETRO;                      // sin retroalimentación no se puede comprobar
  uint8_t f = 0, bit = (uint8_t)(1u << (k - 1));
  if (!(bobinasEncendido & bit)) f |= PR_NO_ENERGIZA;
  if (bobinasEncendido & ~bit) f |= PR_OTRA_BOBINA;
  if (bobinasApagado) f |= PR_NO_SUELTA;
  return f;
}
inline int describirRele(uint8_t k, uint8_t f, char* s, size_t n) {
  if (f & PR_SIN_RETRO) return snprintf(s, n, "canal %d: sin retroalimentación, no se puede comprobar", k);
  return snprintf(s, n, "canal %d:%s%s%s", k, (f & PR_NO_ENERGIZA) ? " no se energizó (¿24 V, ULN2003, divisor?)" : "",
                  (f & PR_OTRA_BOBINA) ? " se energizó otra bobina" : "", (f & PR_NO_SUELTA) ? " no soltó" : "");
}

}  // namespace apc
