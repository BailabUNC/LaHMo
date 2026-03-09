#ifndef LAHMO2_H
#define LAHMO2_H

#include <Arduino.h>
#include "BLEDevice.h"
#include "BLEUtils.h"
#include "BLEServer.h"

#define MY_ADS1115_ADDRESS   0x48

#define ELAPSED_MICROS       current_micros - previous_micros

#define NUM_CHANNEL          4

#define LED0                 10
#define LED1                 5
#define LED2                 3
#define LED3                 4

#define SDA                  19
#define SCL                  18
#define SR                   6667.0F

#define ALARM_US             50000

// See the following for generating UUIDs:
// https://www.uuidgenerator.net/
#define DEVICE_NAME           "LaHMo2"
#define LHM_SERVICE_UUID      "0000FF01-0000-1000-8000-00805F9B34FB"
#define LHM_CHAR_UUID         "0000ABEF-0000-1000-8000-00805F9B34FB"
#define LHM_DESC_UUID         (BLEUUID(uint16_t(0x2901)))

void IRAM_ATTR onTimer();
void ioInit(void);
void peripheralInit(void);
void sensorInit(void);
void serviceInit(void);
void advertisingInit(void);

#endif // LAHMO2_H