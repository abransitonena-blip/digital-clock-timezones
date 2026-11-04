#pragma once
#include "Arduino.h"
struct WiFiUDP { uint8_t begin(uint16_t); uint8_t beginMulticast(IPAddress, uint16_t); void stop(); int parsePacket(); int read(uint8_t*, size_t); };
