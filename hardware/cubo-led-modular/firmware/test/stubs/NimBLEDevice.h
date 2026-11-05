#pragma once
#include <stdint.h>
#include <string>
#define BLE_HS_IO_DISPLAY_ONLY 0
namespace NIMBLE_PROPERTY { enum : uint32_t { READ = 1, READ_ENC = 2, WRITE = 8, WRITE_ENC = 16, WRITE_AUTHEN = 32, NOTIFY = 64 }; }
struct NimBLEConnInfo {};
struct NimBLEAttValue { operator std::string() const; };
class NimBLEServer;
class NimBLEServerCallbacks { public: virtual ~NimBLEServerCallbacks() {}
  virtual void onConnect(NimBLEServer*, NimBLEConnInfo&) {} virtual void onDisconnect(NimBLEServer*, NimBLEConnInfo&, int) {} };
class NimBLECharacteristic;
class NimBLECharacteristicCallbacks { public: virtual ~NimBLECharacteristicCallbacks() {}
  virtual void onWrite(NimBLECharacteristic*, NimBLEConnInfo&) {} };
class NimBLECharacteristic { public: NimBLEAttValue getValue(); void setValue(const uint8_t*, size_t);
  bool notify(bool = true); void setCallbacks(NimBLECharacteristicCallbacks*); };
class NimBLEService { public: NimBLECharacteristic* createCharacteristic(const char*, uint32_t); bool start(); };
class NimBLEServer { public: void setCallbacks(NimBLEServerCallbacks*, bool = true); NimBLEService* createService(const char*); };
class NimBLEAdvertising { public: bool addServiceUUID(const char*); bool setName(const std::string&); bool start(uint32_t = 0); };
struct NimBLEDevice { static bool init(const std::string&); static void setSecurityAuth(bool, bool, bool);
  static void setSecurityPasskey(uint32_t); static void setSecurityIOCap(uint8_t); static NimBLEServer* createServer();
  static NimBLEAdvertising* getAdvertising(); static bool startAdvertising(uint32_t = 0); static bool deleteAllBonds(); };
