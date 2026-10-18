// AP LINK v1: enlace entre módulos AP Electric (estilo DMX: cadena de cable, un módulo detrás de otro).
//
// Capa física: RS-485 a 250 kbit/s, 8N1; conector de 4 patas (1 GND, 2 B, 3 A, 4 SENSE). Cada módulo tiene dos conectores iguales,
// ENTRA y SIGUE, con A, B y GND unidos en la placa (como el THRU de DMX). SENSE no se une: la pata 4 de ENTRA es SENSE_IN y la de SIGUE
// es SENSE_OUT (la maneja el microcontrolador). Con SENSE los módulos saben quién está detrás de quién sin interruptores ni direcciones a mano.
//
//   · SENSE_OUT tiene 4.7 kΩ a 0 V en cada módulo: sin programa (o sin energía) vale 0.
//   · SENSE_IN tiene 100 kΩ a 3.3 V: sin cable vale 1.
//   · Un módulo sube SENSE_OUT solo cuando ya tiene dirección; el siguiente de la cadena queda "habilitado" para responder a la enumeración.
//
// Roles: CABEZA (módulo 1, el maestro), ESCLAVO (con dirección 2..16) y ESPERA (sin dirección).
// Al arrancar un módulo escucha 1.5 s: si oye una baliza, es ESPERA; si no oye nada y SENSE_IN vale 1 (nadie lo habilita desde atrás), es CABEZA.
// La cadena se parte donde se desconecta un cable: cada tramo elige su cabeza y sigue funcionando; al reconectar, la baliza de más
// prioridad gana y el otro cabeza se vuelve ESPERA (y avisa a sus esclavos con RESET).
//
// Salidas: el cabeza manda a cada módulo su máscara de salidas cada POLL_MS y recibe las entradas. Si un esclavo no oye al cabeza en
// WDOG_MS, apaga sus salidas (o las pone en su máscara segura); a los DROP_MS vuelve a ESPERA.
//
// Este archivo no depende del hardware: el programa del equipo da un HAL (enviar bytes, leer/poner SENSE, reloj) y llama recibir() y tick().
#pragma once
#include <stdint.h>
#include <stddef.h>
#include <string.h>

namespace aplink {

constexpr uint8_t SYNC = 0xA5;
constexpr uint8_t VERSION = 1;
constexpr uint8_t MAX_MODULOS = 16;
constexpr uint8_t MAX_DATOS = 32;
constexpr uint8_t MAX_PWM = 8;                // salidas con brillo (PWM) por módulo
constexpr uint8_t MAX_ANA = 8;                // entradas analógicas por módulo
constexpr uint8_t TODOS = 0xFF;

constexpr uint32_t ESCUCHA_MS = 1500;     // al arrancar, antes de decidir si es cabeza
constexpr uint32_t BALIZA_MS = 500;
constexpr uint32_t POLL_MS = 50;          // periodo de cada módulo
constexpr uint32_t ENUM_RAPIDA_MS = 30;   // mientras se forma la cadena
constexpr uint32_t ENUM_LENTA_MS = 1000;  // después, para detectar módulos nuevos
constexpr uint32_t RESPUESTA_MS = 8;      // espera de la respuesta a un POLL
constexpr uint8_t PERDIDO_TRAS = 3;       // sin respuesta: el módulo se marca perdido
constexpr uint8_t QUITAR_TRAS = 20;       // sin respuesta: se quita de la lista (≈ 1 s)
constexpr uint32_t WDOG_MS = 1000;        // el esclavo pasa a salidas seguras
constexpr uint32_t DROP_MS = 12000;       // el esclavo vuelve a ESPERA (mayor que el último PROMOVER_MS)
constexpr uint32_t PROMOVER_MS = 3000;    // un esclavo huérfano (SENSE_IN en 1) se hace cabeza tras esto + 500 ms por posición

enum Tipo : uint8_t { T_BALIZA = 1, T_ENUM = 2, T_HOLA = 3, T_ASIGNA = 4, T_ACK = 5, T_POLL = 6, T_ESTADO = 7, T_RESET = 8 };

struct Trama {
  uint8_t dst = 0, src = 0, tipo = 0, n = 0;
  uint8_t d[MAX_DATOS] = {0};
};

inline uint16_t crc16(const uint8_t* p, size_t n) {
  uint16_t c = 0xFFFF;
  for (size_t i = 0; i < n; i++) {
    c ^= p[i];
    for (int k = 0; k < 8; k++) c = (c & 1) ? (c >> 1) ^ 0xA001 : c >> 1;
  }
  return c;
}

// SYNC dst src tipo n datos... crcBajo crcAlto  (el CRC cubre desde dst hasta el último dato)
inline size_t codificar(const Trama& t, uint8_t* out) {
  size_t i = 0;
  out[i++] = SYNC; out[i++] = t.dst; out[i++] = t.src; out[i++] = t.tipo; out[i++] = t.n;
  for (uint8_t k = 0; k < t.n; k++) out[i++] = t.d[k];
  uint16_t c = crc16(out + 1, i - 1);
  out[i++] = c & 0xFF; out[i++] = c >> 8;
  return i;
}

// Receptor de tramas con resincronización: si el CRC falla, vuelve a buscar SYNC desde el byte siguiente.
struct Receptor {
  uint8_t b[MAX_DATOS + 8];
  size_t n = 0;
  uint32_t malas = 0;
  bool listo = false;
  Trama t;

  bool poner(uint8_t x) {
    if (n == 0 && x != SYNC) return false;
    b[n++] = x;
    for (;;) {
      if (n >= 5 && b[4] > MAX_DATOS) { descartar(); if (n == 0) return false; continue; }
      if (n >= 5 && n == (size_t)b[4] + 7) {
        uint16_t c = crc16(b + 1, n - 3);
        if (c == (uint16_t)(b[n - 2] | (b[n - 1] << 8))) {
          t.dst = b[1]; t.src = b[2]; t.tipo = b[3]; t.n = b[4];
          memcpy(t.d, b + 5, t.n);
          n = 0;
          return true;
        }
        malas++; descartar();
        if (n == 0) return false;
        continue;
      }
      return false;
    }
  }
  // quita el SYNC inicial y conserva desde el siguiente SYNC
  void descartar() {
    size_t i = 1;
    while (i < n && b[i] != SYNC) i++;
    size_t resto = n - i;
    memmove(b, b + i, resto);
    n = resto;
  }
};

struct Caps {
  uint8_t tipo = 0;     // 1 = AP Rack 16, 2 = AP Rack IN16, 3 = AP Rack AI8, 4 = AP Rack LED8, 5 = RL4, 6 = AO4, 7 = AP PLC C24 (ver AP_LINK.md)
  uint8_t nSal = 0, nEnt = 0;
  uint8_t ver = VERSION;
  uint8_t nAna = 0;     // entradas analógicas (hasta MAX_ANA)
  uint8_t nPwm = 0;     // salidas con brillo: las primeras nPwm salidas aceptan un duty 0-255 (hasta MAX_PWM)
};

struct InfoMod {
  bool presente = false, perdido = false;
  uint32_t uid = 0;
  Caps caps;
  uint16_t ent = 0, sal = 0, fallas = 0, vin_mV = 0;
  uint8_t flags = 0;                 // bit 0: salidas en estado seguro por pérdida del enlace
  uint32_t visto = 0;
  uint8_t fallos = 0;
  uint16_t deseadas = 0;             // lo que el cabeza pide
  uint16_t ana[MAX_ANA] = {};        // analógicas en milésimas (mV o µA, según anaModo)
  uint8_t anaModo = 0;               // bit i = el canal i mide corriente (µA); 0 = tensión (mV)
  uint8_t duty[MAX_PWM] = {255, 255, 255, 255, 255, 255, 255, 255};   // brillo que pide el cabeza (255 = pleno)
};

struct HAL {
  virtual void enviar(const uint8_t* p, size_t n) = 0;     // pone el transceptor en transmisión, manda y vuelve a recibir
  virtual bool senseEntra() = 0;
  virtual void senseSale(bool alto) = 0;
  virtual uint32_t ms() = 0;
  virtual ~HAL() {}
};

enum class Rol : uint8_t { ARRANCANDO, ESPERA, ESCLAVO, CABEZA };

class Enlace {
 public:
  Enlace(HAL& h, uint32_t uid, Caps c, bool puedeCabeza = true, uint8_t prioridad = 1)
      : h_(h), uid_(uid), caps_(c), puedeCabeza_(puedeCabeza), prio_(prioridad) {
    t0_ = h.ms();
    h_.senseSale(false);
  }

  // ---- lo que usa el programa del equipo ----
  void recibir(uint8_t byte) { if (rx_.poner(byte)) atender(rx_.t); }
  void tick();
  Rol rol() const { return rol_; }
  uint8_t pos() const { return pos_; }                       // 0 = sin dirección
  uint8_t total() const { return total_; }                   // módulos en la cadena (el cabeza lo cuenta; los demás lo leen de la baliza)
  uint32_t uid() const { return uid_; }
  uint32_t malas() const { return rx_.malas; }
  uint32_t uidCabeza() const { return huid_; }
  const Caps& caps() const { return caps_; }
  uint16_t entLocal() const { return ent_; }
  uint16_t salAplicadas() const { return aplicadas_; }
  uint16_t vinLocal() const { return vin_; }
  uint16_t fallasLocales() const { return fallas_; }
  const uint16_t* anaLocal() const { return ana_; }
  uint8_t anaModoLocal() const { return anaModo_; }
  // brillo (0-255) de cada salida con PWM de ESTE módulo; vale lo que pidió el cabeza (la máscara de salidas decide si está encendida)
  const uint8_t* dutyLocal() const { return duty_; }

  // entradas y mediciones locales: las pone el programa del equipo
  void ponerLocales(uint16_t ent, uint16_t fallas = 0, uint16_t vin_mV = 0) { ent_ = ent; fallas_ = fallas; vin_ = vin_mV; }
  void ponerAnalogicas(const uint16_t* v, uint8_t n, uint8_t modo) {
    for (uint8_t i = 0; i < MAX_ANA; i++) ana_[i] = i < n ? v[i] : 0;
    anaModo_ = modo;
  }
  // salidas que el programa debe aplicar en ESTE módulo (ya con estado seguro si se perdió el enlace)
  uint16_t salidas() const { return seguro_ ? maskSegura_ : sal_; }
  bool enSeguro() const { return seguro_; }
  void maskSegura(uint16_t m) { maskSegura_ = m; }
  void aplicadas(uint16_t s) { aplicadas_ = s; }            // lectura de vuelta de las salidas (si se puede)

  // ---- solo cabeza ----
  bool mandar(uint8_t pos, uint16_t mask) {
    if (rol_ != Rol::CABEZA || pos < 1 || pos > MAX_MODULOS || !tabla_[pos - 1].presente) return false;
    tabla_[pos - 1].deseadas = mask;
    if (pos == 1) sal_ = mask;
    return true;
  }
  // brillo de la salida local 1..nPwm del módulo en pos (0-255)
  bool mandarDuty(uint8_t pos, uint8_t local, uint8_t v) {
    if (rol_ != Rol::CABEZA || pos < 1 || pos > MAX_MODULOS || !tabla_[pos - 1].presente) return false;
    if (local < 1 || local > tabla_[pos - 1].caps.nPwm || local > MAX_PWM) return false;
    tabla_[pos - 1].duty[local - 1] = v;
    if (pos == 1) duty_[local - 1] = v;
    return true;
  }
  bool mandarDutyCanal(uint16_t g, uint8_t v) { uint8_t p, l; return canalGlobal(g, &p, &l) && mandarDuty(p, l, v); }
  const InfoMod* modulo(uint8_t pos) const { return (pos >= 1 && pos <= MAX_MODULOS && tabla_[pos - 1].presente) ? &tabla_[pos - 1] : nullptr; }
  // canales globales 1..N sumando las salidas de cada módulo en orden de cadena
  bool mandarCanal(uint16_t g, bool on);
  bool canalGlobal(uint16_t g, uint8_t* pos, uint8_t* local) const;
  uint16_t totalSalidas() const { uint16_t s = 0; for (auto& m : tabla_) if (m.presente) s += m.caps.nSal; return s; }
  uint16_t totalEntradas() const { uint16_t s = 0; for (auto& m : tabla_) if (m.presente) s += m.caps.nEnt; return s; }
  uint16_t totalAnalogicas() const { uint16_t s = 0; for (auto& m : tabla_) if (m.presente) s += m.caps.nAna; return s; }
  // entrada digital global g (1..): módulo y bit local (1..); analógica global igual
  bool entradaGlobal(uint16_t g, uint8_t* pos, uint8_t* local) const { return ubicar(g, false, pos, local); }
  bool analogicaGlobal(uint16_t g, uint8_t* pos, uint8_t* local) const { return ubicar(g, true, pos, local); }

 private:
  HAL& h_;
  uint32_t uid_;
  Caps caps_;
  bool puedeCabeza_;
  uint8_t prio_;
  Receptor rx_;
  Rol rol_ = Rol::ARRANCANDO;
  uint8_t pos_ = 0, total_ = 0;
  uint32_t t0_ = 0;
  // esclavo
  uint32_t huid_ = 0;                 // cabeza que lo enumeró (o el último que oyó)
  uint8_t hprio_ = 0;
  uint32_t ultimoCabeza_ = 0;         // última vez que el cabeza le habló
  uint32_t ultimaBaliza_ = 0;
  bool oyoCabeza_ = false;
  bool seguro_ = true;
  bool hubo_ = false;                 // el enlace se perdió desde el último STATE enviado (se informa una vez)
  uint16_t sal_ = 0, maskSegura_ = 0, ent_ = 0, fallas_ = 0, vin_ = 0, aplicadas_ = 0;
  uint16_t ana_[MAX_ANA] = {};
  uint8_t anaModo_ = 0;
  uint8_t duty_[MAX_PWM] = {255, 255, 255, 255, 255, 255, 255, 255};
  // cabeza
  InfoMod tabla_[MAX_MODULOS];
  uint32_t tBaliza_ = 0, tEnum_ = 0, tPoll_ = 0, tResp_ = 0, tInicio_ = 0;
  uint8_t cursor_ = 0;
  bool esperando_ = false;
  uint8_t esperaPos_ = 0;
  uint8_t rondasVacias_ = 0;
  bool enumEnCurso_ = false;

  void enviar(uint8_t dst, uint8_t tipo, const uint8_t* d = nullptr, uint8_t n = 0) {
    Trama t; t.dst = dst; t.src = pos_ ? pos_ : 0; t.tipo = tipo; t.n = n;
    if (n) memcpy(t.d, d, n);
    uint8_t buf[MAX_DATOS + 8];
    size_t k = codificar(t, buf);
    h_.enviar(buf, k);
  }
  static void p32(uint8_t* d, uint32_t v) { d[0] = v; d[1] = v >> 8; d[2] = v >> 16; d[3] = v >> 24; }
  static uint32_t g32(const uint8_t* d) { return d[0] | (d[1] << 8) | (d[2] << 16) | ((uint32_t)d[3] << 24); }

  void volverEspera() {
    rol_ = Rol::ESPERA; pos_ = 0; total_ = 0; seguro_ = true; huid_ = 0; esperando_ = false;
    for (auto& d : duty_) d = 255;
    for (auto& m : tabla_) m = InfoMod();
    h_.senseSale(false);
  }
  void hacerseCabeza(uint8_t prio) {
    rol_ = Rol::CABEZA; pos_ = 1; prio_ = prio; seguro_ = false;
    for (auto& m : tabla_) m = InfoMod();
    InfoMod& yo = tabla_[0];
    yo.presente = true; yo.uid = uid_; yo.caps = caps_; yo.visto = h_.ms();
    total_ = 1; huid_ = uid_;
    tInicio_ = h_.ms(); tBaliza_ = tEnum_ = tPoll_ = tInicio_;
    rondasVacias_ = 0; enumEnCurso_ = true; esperando_ = false; cursor_ = 0;
    uint8_t d[4]; p32(d, uid_);
    enviar(TODOS, T_RESET, d, 4);      // el tramo anterior (si lo había) vuelve a ESPERA
    h_.senseSale(true);
    baliza(h_.ms());
  }
  bool ubicar(uint16_t g, bool ana, uint8_t* pos, uint8_t* local) const {
    if (g < 1) return false;
    uint16_t base = 0;
    for (uint8_t i = 0; i < MAX_MODULOS; i++) {
      if (!tabla_[i].presente) continue;
      uint8_t n = ana ? tabla_[i].caps.nAna : tabla_[i].caps.nEnt;
      if (g <= base + n) { *pos = i + 1; *local = g - base; return true; }
      base += n;
    }
    return false;
  }
  void baliza(uint32_t ahora) {
    tBaliza_ = ahora;
    uint8_t d[7]; p32(d, uid_); d[4] = total_; d[5] = prio_; d[6] = VERSION;
    enviar(TODOS, T_BALIZA, d, 7);
  }
  void atender(const Trama& t);
  void tickCabeza(uint32_t ahora);
  void tickEsclavo(uint32_t ahora);
};

inline bool Enlace::canalGlobal(uint16_t g, uint8_t* pos, uint8_t* local) const {
  if (g < 1) return false;
  uint16_t base = 0;
  for (uint8_t i = 0; i < MAX_MODULOS; i++) {
    if (!tabla_[i].presente) continue;
    if (g <= base + tabla_[i].caps.nSal) { *pos = i + 1; *local = g - base; return true; }
    base += tabla_[i].caps.nSal;
  }
  return false;
}

inline bool Enlace::mandarCanal(uint16_t g, bool on) {
  uint8_t p, l;
  if (!canalGlobal(g, &p, &l)) return false;
  uint16_t m = tabla_[p - 1].deseadas;
  if (on) m |= (1u << (l - 1)); else m &= ~(1u << (l - 1));
  return mandar(p, m);
}

inline void Enlace::tick() {
  uint32_t ahora = h_.ms();
  if (rol_ == Rol::ARRANCANDO) {
    if (ahora - t0_ >= ESCUCHA_MS) {
      if (oyoCabeza_ || !h_.senseEntra() || !puedeCabeza_) { rol_ = Rol::ESPERA; ultimoCabeza_ = ahora; }
      else hacerseCabeza(prio_);
    }
    return;
  }
  if (rol_ == Rol::CABEZA) tickCabeza(ahora);
  else tickEsclavo(ahora);
}

inline void Enlace::tickEsclavo(uint32_t ahora) {
  if (rol_ == Rol::ESCLAVO) {
    if (!seguro_ && ahora - ultimoCabeza_ >= WDOG_MS) { seguro_ = true; hubo_ = true; }
    if (ahora - ultimoCabeza_ >= DROP_MS) { volverEspera(); ultimoCabeza_ = ahora; return; }
    // huérfano: si SENSE_IN vale 1 y nadie habla, el más cercano a donde estaba el cabeza toma el mando
    if (puedeCabeza_ && h_.senseEntra() && ahora - ultimoCabeza_ >= PROMOVER_MS + 500u * (pos_ - 1)) {
      hacerseCabeza(0);
    }
  } else if (rol_ == Rol::ESPERA) {
    if (puedeCabeza_ && h_.senseEntra() && ahora - ultimoCabeza_ >= PROMOVER_MS) hacerseCabeza(0);
  }
}

inline void Enlace::tickCabeza(uint32_t ahora) {
  // el cabeza es el módulo 1: su propia fila se actualiza sin tramas
  InfoMod& yo = tabla_[0];
  yo.ent = ent_; yo.sal = aplicadas_; yo.fallas = fallas_; yo.vin_mV = vin_; yo.visto = ahora; yo.flags = 0;
  for (uint8_t i = 0; i < MAX_ANA; i++) yo.ana[i] = ana_[i];
  yo.anaModo = anaModo_;
  // baliza
  if (ahora - tBaliza_ >= BALIZA_MS) baliza(ahora);
  // respuesta pendiente
  if (esperando_) {
    if (ahora - tResp_ < RESPUESTA_MS) return;
    esperando_ = false;
    if (esperaPos_ == 0) {                              // nadie contestó a la pregunta "quién sigue"
      if (rondasVacias_ < 255) rondasVacias_++;
      if (rondasVacias_ >= 2) enumEnCurso_ = false;
      return;
    }
    InfoMod& m = tabla_[esperaPos_ - 1];
    if (m.presente) {
      if (m.fallos < 255) m.fallos++;
      if (m.fallos >= PERDIDO_TRAS) m.perdido = true;
      if (m.fallos >= QUITAR_TRAS) {                    // se quita el módulo y los de atrás; sin POLL vuelven solos a ESPERA
        for (uint8_t i = esperaPos_ - 1; i < MAX_MODULOS; i++) tabla_[i] = InfoMod();
        total_ = esperaPos_ - 1;
        rondasVacias_ = 0; enumEnCurso_ = true;
      }
    }
    return;
  }
  // enumeración: "¿quién sigue?"
  uint32_t periodo = enumEnCurso_ ? ENUM_RAPIDA_MS : ENUM_LENTA_MS;
  if (total_ < MAX_MODULOS && ahora - tEnum_ >= periodo) {
    tEnum_ = ahora;
    uint8_t d[1] = {total_};
    enviar(TODOS, T_ENUM, d, 1);
    esperando_ = true; esperaPos_ = 0; tResp_ = ahora;
    return;
  }
  // POLL de los módulos remotos, uno por turno, repartidos en POLL_MS
  uint8_t remotos = total_ > 1 ? total_ - 1 : 0;
  if (!remotos) return;
  uint32_t intervalo = POLL_MS / remotos;
  if (intervalo < 5) intervalo = 5;
  if (ahora - tPoll_ < intervalo) return;
  for (uint8_t k = 0; k < MAX_MODULOS; k++) {
    cursor_ = (cursor_ + 1) % MAX_MODULOS;
    if (cursor_ == 0) continue;                         // índice 0 = el cabeza
    InfoMod& m = tabla_[cursor_];
    if (!m.presente) continue;
    tPoll_ = ahora;
    uint8_t d[3 + MAX_PWM] = {(uint8_t)(m.deseadas & 0xFF), (uint8_t)(m.deseadas >> 8), 0};
    uint8_t np = m.caps.nPwm <= MAX_PWM ? m.caps.nPwm : MAX_PWM;
    for (uint8_t i = 0; i < np; i++) d[3 + i] = m.duty[i];
    enviar(cursor_ + 1, T_POLL, d, 3 + np);
    esperando_ = true; esperaPos_ = cursor_ + 1; tResp_ = ahora;
    return;
  }
}

inline void Enlace::atender(const Trama& t) {
  uint32_t ahora = h_.ms();
  switch (t.tipo) {
    case T_BALIZA: {
      if (t.n < 7) return;
      uint32_t huid = g32(t.d);
      if (huid == uid_) return;
      uint8_t tot = t.d[4], prio = t.d[5];
      if (rol_ == Rol::ARRANCANDO) { oyoCabeza_ = true; huid_ = huid; hprio_ = prio; return; }
      if (rol_ == Rol::CABEZA) {
        // dos cabezas en el mismo bus: gana la prioridad mayor y, a igual prioridad, el uid menor
        bool pierdo = (prio > prio_) || (prio == prio_ && huid < uid_);
        if (pierdo) {
          uint8_t d[4]; p32(d, uid_);
          enviar(TODOS, T_RESET, d, 4);            // sus esclavos vuelven a ESPERA
          volverEspera(); ultimoCabeza_ = ahora; huid_ = huid; hprio_ = prio;
        }
        return;
      }
      if (rol_ == Rol::ESPERA) { huid_ = huid; hprio_ = prio; total_ = tot; ultimoCabeza_ = ahora; return; }
      if (huid == huid_) { total_ = tot; ultimoCabeza_ = ahora; }      // esclavo: solo sigue a su cabeza
      return;
    }
    case T_ENUM:
      if (rol_ == Rol::ESPERA && h_.senseEntra()) {
        // responde "hola" con su uid y capacidades
        uint8_t d[10]; p32(d, uid_); d[4] = caps_.tipo; d[5] = caps_.nSal; d[6] = caps_.nEnt; d[7] = caps_.ver; d[8] = caps_.nAna; d[9] = caps_.nPwm;
        enviar(TODOS, T_HOLA, d, 10);
        ultimoCabeza_ = ahora;
      }
      return;
    case T_HOLA:
      if (rol_ != Rol::CABEZA || t.n < 8 || !esperando_ || esperaPos_ != 0) return;
      {
        esperando_ = false;
        uint32_t uid = g32(t.d);
        for (auto& m : tabla_) if (m.presente && m.uid == uid) return;       // ya está (uid repetido): se ignora
        if (total_ >= MAX_MODULOS) return;
        InfoMod& m = tabla_[total_];
        m = InfoMod();
        m.presente = true; m.uid = uid; m.caps.tipo = t.d[4]; m.caps.nSal = t.d[5]; m.caps.nEnt = t.d[6]; m.caps.ver = t.d[7];
        m.caps.nAna = (t.n >= 9 && t.d[8] <= MAX_ANA) ? t.d[8] : 0;
        m.caps.nPwm = (t.n >= 10 && t.d[9] <= MAX_PWM) ? t.d[9] : 0;
        m.visto = ahora;
        total_++;
        rondasVacias_ = 0;
        uint8_t d[10]; p32(d, uid); d[4] = total_; p32(d + 5, uid_); d[9] = prio_;
        // uid del módulo, su dirección y quién es su cabeza; el módulo contesta con T_ACK
        enviar(TODOS, T_ASIGNA, d, 10);
        esperando_ = true; esperaPos_ = total_; tResp_ = ahora;
      }
      return;
    case T_ASIGNA:
      if (rol_ == Rol::ESPERA && t.n >= 10 && g32(t.d) == uid_) {
        pos_ = t.d[4]; huid_ = g32(t.d + 5); hprio_ = t.d[9]; rol_ = Rol::ESCLAVO; seguro_ = true; ultimoCabeza_ = ahora; sal_ = 0;
        enviar(1, T_ACK);
        h_.senseSale(true);                    // habilita al siguiente de la cadena
      }
      return;
    case T_ACK:
      if (rol_ == Rol::CABEZA && esperando_ && t.src == esperaPos_ && esperaPos_ > 1) {
        // confirmó su dirección; si ya hay un POLL en la lista, esto cierra la espera
        esperando_ = false;
        InfoMod& m = tabla_[esperaPos_ - 1];
        m.visto = ahora; m.fallos = 0;
        tEnum_ = ahora - ENUM_RAPIDA_MS;       // pregunta de inmediato quién sigue
      }
      return;
    case T_POLL:
      if (rol_ == Rol::ESCLAVO && t.dst == pos_ && t.n >= 3) {
        sal_ = t.d[0] | (t.d[1] << 8);
        for (uint8_t i = 0; i < caps_.nPwm && i < MAX_PWM && t.n >= 4 + i; i++) duty_[i] = t.d[3 + i];
        seguro_ = false;
        ultimoCabeza_ = ahora;
        uint8_t d[MAX_DATOS];
        d[0] = ent_; d[1] = ent_ >> 8; d[2] = aplicadas_; d[3] = aplicadas_ >> 8;
        d[4] = fallas_; d[5] = fallas_ >> 8; d[6] = vin_; d[7] = vin_ >> 8; d[8] = hubo_ ? 1 : 0; hubo_ = false;
        uint8_t n = 9;
        if (caps_.nAna) { d[n++] = anaModo_; for (uint8_t i = 0; i < caps_.nAna && i < MAX_ANA; i++) { d[n++] = ana_[i]; d[n++] = ana_[i] >> 8; } }
        enviar(1, T_ESTADO, d, n);
      }
      return;
    case T_ESTADO:
      if (rol_ == Rol::CABEZA && t.n >= 9 && t.src >= 2 && t.src <= MAX_MODULOS && tabla_[t.src - 1].presente) {
        InfoMod& m = tabla_[t.src - 1];
        m.ent = t.d[0] | (t.d[1] << 8); m.sal = t.d[2] | (t.d[3] << 8);
        m.fallas = t.d[4] | (t.d[5] << 8); m.vin_mV = t.d[6] | (t.d[7] << 8); m.flags = t.d[8];
        if (m.caps.nAna && t.n >= 10 + 2 * m.caps.nAna) {
          m.anaModo = t.d[9];
          for (uint8_t i = 0; i < m.caps.nAna && i < MAX_ANA; i++) m.ana[i] = t.d[10 + 2 * i] | (t.d[11 + 2 * i] << 8);
        }
        m.visto = ahora; m.fallos = 0; m.perdido = false;
        if (esperando_ && esperaPos_ == t.src) esperando_ = false;
      }
      return;
    case T_RESET:
      if (t.n >= 4 && (rol_ == Rol::ESCLAVO || rol_ == Rol::ESPERA) && g32(t.d) == huid_) {
        volverEspera(); ultimoCabeza_ = ahora;
      }
      return;
    default: return;
  }
}

}  // namespace aplink
