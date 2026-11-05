#pragma once
#include <stdint.h>
struct Preferences { bool begin(const char*, bool); void end();
  uint8_t getUChar(const char*, uint8_t); float getFloat(const char*, float); uint16_t getUShort(const char*, uint16_t);
  bool getBool(const char*, bool); size_t putUChar(const char*, uint8_t); size_t putFloat(const char*, float);
  size_t putUShort(const char*, uint16_t); size_t putBool(const char*, bool);
  size_t getString(const char*, char*, size_t); size_t putString(const char*, const char*); int8_t getChar(const char*, int8_t); size_t putChar(const char*, int8_t);
  size_t getBytes(const char*, void*, size_t); size_t putBytes(const char*, const void*, size_t); };
