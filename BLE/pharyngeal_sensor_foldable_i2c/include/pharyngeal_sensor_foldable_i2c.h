#ifndef PHARYGEAL_SENSOR_FOLDABLE_H
#define PHARYGEAL_SENSOR_FOLDABLE_H

#include <Arduino.h>
#include "BLEDevice.h"
#include "BLEUtils.h"
#include "BLEServer.h"

#define MY_ADS1115_ADDRESS   0x48

#define ELAPSED_MICROS       current_micros - previous_micros

#define NUM_CHANNEL          4

#define LED0                 11
#define LED1                 12
#define LED2                 13
#define LED3                 14

#define SDA                  10
#define SCL                  9
#define SR                   1667.0F

#define INTERVAL_US          100000
#define DURATION_US          20000
#define ALARM_US             10000

// #define INTERVAL_US          100000
// #define DURATION_US          20000
// #define ALARM_US             1000

// See the following for generating UUIDs:
// https://www.uuidgenerator.net/
#define DEVICE_NAME           "LHM_Yihan"
#define LHM_SERVICE_UUID      "12fb95d1-4954-450f-a82b-802f71541562"
#define LHM_CHAR_UUID         "67136980-20d0-4711-8b37-3acd0fec8e7f"
#define LHM_DESC_UUID         (BLEUUID(uint16_t(0x2901)))

void IRAM_ATTR onTimer();
void ioInit(void);
void peripheralInit(void);
void sensorInit(void);
void serviceInit(void);
void advertisingInit(void);

#endif