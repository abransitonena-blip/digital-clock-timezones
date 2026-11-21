// Cubo AP · grupos de cubos en la misma red (p. ej. 20 letreros de un cliente).
// Una orden enviada a un cubo puede reenviarse por UDP broadcast a todos los del grupo.
// Cada mensaje va firmado con HMAC-SHA256 y la clave del grupo, y lleva un contador que
// solo puede crecer (y, si hay hora, debe estar a ±120 s del reloj): nadie en la red puede
// inventar ni repetir órdenes. Solo se aceptan órdenes de luz (nunca Wi-Fi, límites ni DMX).
#pragma once
#include <stdint.h>
#include <stddef.h>

namespace ap {

void sha256(const uint8_t* datos, size_t n, uint8_t salida[32]);
void hmacSha256(const uint8_t* clave, size_t nclave, const uint8_t* msg, size_t n, uint8_t salida[32]);

static const uint16_t PUERTO_GRUPO = 21330;

// Órdenes que un grupo puede mandar: ON, OFF, BRILLO, RGBW, MODO, ESCENA n, CCT.
bool comandoDeGrupoPermitido(const char* cmd);

// Arma "APG1 <grupo> <contador> <cmd> <firma16>". Devuelve longitud o 0 si no cabe / no es válido.
size_t firmarGrupo(const char* grupo, const char* clave, uint64_t contador, const char* cmd, char* out, size_t n);

enum class Rechazo : uint8_t { NINGUNO, FORMATO, OTRO_GRUPO, FIRMA, REPETIDO, FUERA_DE_HORA, NO_PERMITIDO };
// Verifica un mensaje recibido. ultimo: mayor contador aceptado (se actualiza).
// ahora_ms_epoch: hora local en ms (0 si no se conoce). cmd recibe la orden si es válida.
Rechazo verificarGrupo(const char* msg, const char* grupo, const char* clave, uint64_t& ultimo,
                       uint64_t ahora_ms_epoch, char* cmd, size_t ncmd);

} // namespace ap
