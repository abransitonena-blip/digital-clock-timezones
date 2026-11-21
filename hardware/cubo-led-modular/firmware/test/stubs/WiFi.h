#pragma once
#include "Arduino.h"
#define WIFI_STA 1
#define WL_CONNECTED 3
struct WiFiClass { bool mode(int); bool setHostname(const char*); int begin(const char*, const char*); int status();
  bool disconnect(bool = false); IPAddress localIP(); IPAddress broadcastIP(); uint8_t* macAddress(uint8_t*); };
extern WiFiClass WiFi;
