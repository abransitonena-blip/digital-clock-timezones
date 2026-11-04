#pragma once
#include "WebServer.h"
typedef void (*BrightnessCallbackFunction)(uint8_t);
struct Espalexa { bool begin(WebServer* = nullptr); void loop(); int addDevice(String, BrightnessCallbackFunction, uint8_t = 0);
  bool handleAlexaApiCall(String, String); };
