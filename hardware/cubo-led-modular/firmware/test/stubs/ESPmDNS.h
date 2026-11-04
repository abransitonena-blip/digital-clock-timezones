#pragma once
struct MDNSResponder { bool begin(const char*); void addService(const char*, const char*, unsigned short); };
extern MDNSResponder MDNS;
