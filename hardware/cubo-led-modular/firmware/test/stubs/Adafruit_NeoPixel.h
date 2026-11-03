#pragma once
#include <stdint.h>
#define NEO_GRB 0x52
#define NEO_KHZ800 0x0000
struct Adafruit_NeoPixel { Adafruit_NeoPixel(uint16_t, int16_t, uint16_t); void begin(); void show();
  void updateLength(uint16_t); uint16_t numPixels() const; void setPixelColor(uint16_t, uint32_t);
  static uint32_t Color(uint8_t, uint8_t, uint8_t); };
