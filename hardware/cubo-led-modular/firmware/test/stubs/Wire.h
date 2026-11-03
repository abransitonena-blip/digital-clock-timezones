#pragma once
#include <stdint.h>
struct TwoWire { bool begin(int, int, uint32_t); void beginTransmission(uint8_t); size_t write(uint8_t);
  uint8_t endTransmission(bool = true); uint8_t requestFrom(uint8_t, uint8_t); int read(); };
extern TwoWire Wire;
