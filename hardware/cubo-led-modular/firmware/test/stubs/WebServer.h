#pragma once
#include "Arduino.h"
#include <functional>
enum HTTPMethod { HTTP_GET, HTTP_POST };
struct WebServer { WebServer(int); typedef std::function<void(void)> H;
  void on(const char*, HTTPMethod, H); void onNotFound(H); void begin(); void handleClient();
  void send(int, const char*, const char*); void send_P(int, PGM_P, PGM_P); void sendHeader(const char*, const char*);
  String arg(const char*); String arg(int); String uri(); String header(const char*); void collectHeaders(const char**, size_t); };
