#pragma once
#include <stdint.h>
#include <stddef.h>
#define UPDATE_SIZE_UNKNOWN 0xFFFFFFFF
struct UpdateClass { bool begin(size_t); size_t write(uint8_t*, size_t); bool end(bool = false); bool hasError(); };
extern UpdateClass Update;
