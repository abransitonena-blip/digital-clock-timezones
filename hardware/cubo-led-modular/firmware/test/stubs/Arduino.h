// Cabeceras simuladas SOLO para revisar sintaxis en PC (no reemplazan al core real).
#pragma once
#include <stdint.h>
#include <string.h>
#include <strings.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string>
#define OUTPUT 1
#define INPUT_PULLUP 2
#define LOW 0
#define HIGH 1
template <class T, class L, class H> T constrain(T x, L a, H b) { return x < a ? a : (x > b ? b : x); }
void pinMode(int, int); void digitalWrite(int, int); int digitalRead(int);
uint32_t analogReadMilliVolts(int); void analogReadResolution(int);
bool ledcAttach(int, uint32_t, int); bool ledcWrite(int, uint32_t);
uint32_t millis();
size_t strlcpy(char*, const char*, size_t);
struct HardwareSerial { void begin(long); int available(); int read(); size_t println(const char*); int printf(const char*, ...); };
extern HardwareSerial Serial;
struct EspClass { uint64_t getEfuseMac(); }; extern EspClass ESP;
