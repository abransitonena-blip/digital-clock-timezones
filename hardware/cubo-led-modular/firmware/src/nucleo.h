// Cubo AP · núcleo portable del firmware (sin dependencias de Arduino).
// Todo lo que decide seguridad y comportamiento vive aquí para poder probarlo en PC.
#pragma once
#include <stdint.h>
#include <stddef.h>

namespace ap {

// ---------- Tarjeta de configuración ----------
// La tarjeta (conector de 3 pines: 1 FB, 2 GND, 3 ID) lleva 2 resistencias:
//   R_B   (pin 1-2) -> resistencia INFERIOR del divisor de realimentación; la superior (29.4k)
//            está en la placa. Fija por HARDWARE el voltaje máximo. Sin tarjeta, FB = Vout
//            y la salida se cae a ~0.8 V (falla segura).
//   R_ID  (pin 3-2) -> 10k…150k, con pull-up de 47k a 3.3 V: el ADC lee qué perfil es.
//   Tarjeta al revés: FB ve R_ID (≥10k => Vout ≤ 3.2 V) e ID ve R_B (<6k => inválido). Seguro.
struct Perfil {
  const char* nombre;
  uint32_t r_id;      // ohm, valor E12 en la tarjeta
  float vmax;         // V  (debe coincidir con R_FB)
  float imax;         // A  límite continuo
  float r_b;          // ohm, resistencia inferior de realimentación (en la tarjeta)
};
extern const Perfil PERFILES[];
extern const size_t N_PERFILES;
const int PERFIL_PERSONAL = 8;   // R_ID 220k: límites desde la app
// Devuelve índice del perfil o -1 si no hay tarjeta / valor fuera de ventana.
int decodificarTarjeta(float adc_mv, float vcc_mv = 3300.f, float r_pullup = 47000.f);

// ---------- Ajuste de voltaje por DAC (solo puede BAJAR del máximo) ----------
// Red: Vout -- Rt(29.4k) -- FB -- Rb(tarjeta) -- GND ;  DAC -- BAT54 -- Rinj(47k) -- FB.  Vref TPS54560 = 0.8 V
struct RedFB { float vref, rt, rb, rinj, vdac_max; };
float vmaxDeRed(const RedFB& r);                 // voltaje con DAC = Vref (sin inyección)
float vminDeRed(const RedFB& r);                 // voltaje con DAC al máximo
float dacParaVoltaje(const RedFB& r, float vset); // V en la salida del DAC, ya recortada

// ---------- Temperatura ----------
float ntcCelsius(float adc_mv, float vcc_mv = 3300.f, float r_serie = 10000.f,
                 float r25 = 10000.f, float beta = 3950.f);
// Factor 0..1 de potencia permitido por temperatura interna del cubo.
float factorTermico(float c);

// ---------- Color ----------
uint16_t gamma12(uint8_t v); // 8 bit -> 12 bit con curva de percepción (2.2)
struct RGBW { uint8_t r, g, b, w; };
RGBW rueda(uint8_t pos);      // arcoíris

// ---------- Tipos de tira compatibles ----------
// Analógicas (ánodo común, salidas R G B W):
//   RGBW, RGB, CCT (blanco cálido en R, frío en G), MONO (un color, salida W).
// Direccionables (una línea de datos, salida DAT): WS2812B (5 V, GRB), SK6812 (5 V, GRBW),
//   WS2811 (12 V, RGB), WS2815 (12 V, GRB). Con relojes (APA102/SK9822) no: requieren 2 líneas.
enum class Tira : uint8_t { RGBW, RGB, CCT, MONO, WS2812B, SK6812, WS2811, WS2815 };
const char* nombreTira(Tira t);
bool tiraDeTexto(const char* s, Tira& t);
bool direccionable(Tira t);
uint8_t bytesPorLed(Tira t);              // 3 (RGB) o 4 (RGBW)
float tensionTira(Tira t);                // V nominal de las direccionables; 0 = la decide la tarjeta
RGBW mezclaCCT(uint16_t kelvin);          // r = cálido (2700 K), g = frío (6500 K), normalizado a 255
// Escribe el color en el orden de bytes que espera el chip (GRB, GRBW, RGB). Devuelve nº de bytes.
uint8_t ordenarBytes(Tira t, RGBW c, uint8_t* out);

// ---------- Estado del módulo ----------
enum class Modo : uint8_t { FIJO, RESPIRA, ARCOIRIS, FUEGO, COMETA };
const char* nombreModo(Modo m);
enum class Falla : uint8_t { NINGUNA, SIN_TARJETA, TARJETA_INCONSISTENTE, SOBRECORRIENTE,
                             SOBRETEMPERATURA, SUBVOLTAJE_ENTRADA, CORTO };
const char* nombreFalla(Falla f);

struct Medicion {        // lo que llega de sensores en cada ciclo
  float vout, iout;      // INA226
  float vin;             // divisor de entrada
  float temp_c;          // NTC
};

struct Salida {          // lo que el firmware aplica al hardware en cada ciclo
  bool habilitar_reductor;
  uint16_t pwm[4];       // 12 bit R,G,B,W
  float vdac;            // V para el DAC de ajuste
  float brillo_efectivo; // 0..1 tras limitaciones
};

class Controlador {
public:
  void configurar(int perfil, const RedFB& red);
  // Comandos (devuelven false si se rechazan)
  bool encender(bool on);
  bool fijarColor(RGBW c);
  bool fijarBrillo(float b);          // 0..1
  bool fijarVoltaje(float v);         // se recorta a [vmin, vmax del perfil]
  bool fijarModo(Modo m);
  bool fijarTira(Tira t);             // rechaza direccionables si la tarjeta no da su voltaje
  bool fijarCCT(uint16_t kelvin);     // 2700–6500 K
  // Reloj y horario diario (la app o NTP mandan la hora local en segundos desde 1970)
  void fijarHora(uint32_t epoch_local, uint32_t ahora_ms);
  bool programar(bool activo, uint16_t min_encender, uint16_t min_apagar);
  int minutoDelDia(uint32_t ahora_ms) const;   // -1 si no hay hora
  // Tarjeta PERSONAL (R_ID 220k): límites programados desde la app y guardados en memoria
  bool fijarLimitesPersonal(float vmax, float imax);
  void reconocerFalla();
  // Corte por hardware (ALERT del INA226) detectado por el firmware: se registra y reintenta igual.
  void fallaExterna(Falla f, uint32_t ahora) { if (on_ && falla_ == Falla::NINGUNA) disparar(f, ahora); }
  // Ciclo de control, llamar cada dt_ms (recomendado 10 ms)
  Salida paso(const Medicion& m, uint32_t ahora_ms);

  // Lectura
  bool encendido() const { return on_; }
  Falla falla() const { return falla_; }
  uint32_t ahora() const { return t_ultimo_; }
  int perfil() const { return perfil_; }
  float vset() const { return vset_; }
  float brillo() const { return brillo_; }
  RGBW color() const { return color_; }
  Modo modo() const { return modo_; }
  float limiteCorriente() const;
  float vmaxPerfil() const;
  Tira tira() const { return tira_; }
  uint16_t cct() const { return cct_; }
  bool horarioActivo() const { return prog_on_; }
  uint16_t minEncender() const { return min_on_; }
  uint16_t minApagar() const { return min_off_; }
  // Color de cada LED en tiras direccionables (sin brillo; se multiplica por brillo_efectivo)
  RGBW colorPixel(uint16_t i, uint16_t n, uint32_t ahora_ms) const;
  // API JSON compatible con WLED (subconjunto: on, bri, col). bri 0–255.
  size_t estadoWled(char* buf, size_t n) const;
  bool aplicarWled(const char* json);
  // Respuesta de estado en JSON compacto para la app
  size_t estadoJson(char* buf, size_t n, const Medicion& m) const;

private:
  void disparar(Falla f, uint32_t ahora);
  int perfil_ = -1;
  RedFB red_{};
  bool on_ = false;
  RGBW color_{255, 255, 255, 0};
  float brillo_ = 0.6f, vset_ = 0.f, rampa_ = 0.f, recorte_i_ = 1.f;
  Modo modo_ = Modo::FIJO;
  Falla falla_ = Falla::NINGUNA;
  uint32_t t_ultimo_ = 0, t_sobre_ = 0, t_falla_ = 0, t_efecto_ = 0;
  uint8_t reintentos_ = 0;
  bool sobre_activo_ = false;
  Tira tira_ = Tira::RGBW;
  uint16_t cct_ = 4000;
  uint32_t epoch_ref_ = 0, ms_ref_ = 0;
  bool hora_ok_ = false, prog_on_ = false;
  uint16_t min_on_ = 0, min_off_ = 0;
  int ultimo_min_ = -1;
  float vmax_personal_ = 0.f, imax_personal_ = 0.f;
};

// ---------- Protocolo de texto (BLE UART / USB serie) ----------
// ON | OFF | RGBW r g b w | BRILLO 0-100 | V 11.5 | MODO FIJO|RESPIRA|ARCOIRIS|FUEGO|COMETA | ESTADO | RESET
// TIRA RGBW|RGB|CCT|MONO|WS2812B|SK6812|WS2811|WS2815 | CCT 2700-6500 | HORA epoch | PROG 18:30 01:00 | PROG OFF
// LIMITES vmax imax (solo tarjeta PERSONAL)
// Respuesta: "OK", "ERR <motivo>" o JSON de estado.
size_t procesarComando(Controlador& c, const char* linea, const Medicion& m, char* resp, size_t n);

} // namespace ap
