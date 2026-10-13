// Prueba en la PC de la respuesta JSON del equipo (estadoJSON de APControl.ino, API 2).
// El fragmento se EXTRAE del programa real (probar_apbus.sh lo copia a /tmp/estado_json.inc), así que prueba el código que corre en la placa.
// Genera /tmp/json_*.txt; probar_json.py comprueba que es JSON válido y que tiene la forma que espera la consola.
#include "../APControl/ap_control.h"
#include "../APControl/modbus_esclavo.h"
#include "../APControl/unidad_packml.h"
#include "../APControl/logica.h"
#include <cstdio>
#include <string>
#define VERSION "AP Control 1.0"
// Imita String de Arduino: un número sin signo de 8 bits se agrega como número y un char como carácter.
struct String {
  std::string v;
  String() {}
  String(const char* c) : v(c) {}
  String& operator+=(const char* c) { v += c; return *this; }
  String& operator+=(char c) { v += c; return *this; }
  String& operator+=(const String& o) { v += o.v; return *this; }
  template <class T, class = typename std::enable_if<std::is_arithmetic<T>::value || std::is_enum<T>::value>::type>
  String& operator+=(T n) { v += std::to_string((long long)n); return *this; }
  String operator+(const char* c) const { String r = *this; r += c; return r; }
};
enum Placa : uint8_t { PLACA_HOME = 2, PLACA_7R = 1 };
static uint8_t placa = PLACA_7R;
static uint32_t segundos = 123;
static apc::Controlador ctl;
static apc::UnidadPackML pk;
static apc::Esclavo mb(ctl, 1, PLACA_HOME, &segundos);
static logica::Programa plc;
static bool plcRun = false;
static uint32_t millis() { return 5000; }
static String mac6() { return String("AB12CD"); }
#include "/tmp/estado_json.inc"

static void guardar(const char* nombre) { FILE* f = fopen(nombre, "w"); fputs(estadoJSON().v.c_str(), f); fclose(f); }

int main() {
  placa = PLACA_7R; ctl.iniciar(apc::fabrica(7, 8), 0, nullptr, 0, false); pk.iniciar(0);
  guardar("/tmp/json_7r.txt");                                   // 7R en reposo
  ctl.salida = 0x05; ctl.entradas = 0x03; ctl.bobinas = 0x05; ctl.fallas = apc::F_BOBINA | apc::F_COMUNICACION;
  uint32_t t = 1000;
  pk.comando(1, apc::OR_BOTON, t); pk.paso(t += 100); pk.comando(2, apc::OR_BOTON, t);       // Reset y Start
  guardar("/tmp/json_7r_falla.txt");
  placa = PLACA_HOME; apc::Config h = apc::fabrica(1, 1); h.crc = apc::crcDe(h); ctl.iniciar(h, 0, nullptr, 0, false);
  guardar("/tmp/json_home.txt");
  printf("JSON generados\n");
  return 0;
}
