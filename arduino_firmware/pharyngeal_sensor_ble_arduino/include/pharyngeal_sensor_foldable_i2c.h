#ifndef PHARYGEAL_SENSOR_FOLDABLE_H
#define PHARYGEAL_SENSOR_FOLDABLE_H

#include <Arduino.h>
#include <ArduinoBLE.h>

#define MY_ADS1115_ADDRESS   0x48

#define ELAPSED_MICROS       current_micros - previous_micros

#define NUM_CHANNEL          4

#define LED0                 10
#define LED1                 11
#define LED2                 3
#define LED3                 8

#define SDA                  19
#define SCL                  18
#define SR                   6667.0F

#define ALARM_US             50000

// See the following for generating UUIDs:
// https://www.uuidgenerator.net/
#define DEVICE_NAME           "LaHMo2"
#define LHM_SERVICE_UUID      "12fb95d1-4954-450f-a82b-802f71541562"
#define LHM_CHAR_UUID         "67136980-20d0-4711-8b37-3acd0fec8e7f"

void IRAM_ATTR onTimer();
void ioInit(void);
void peripheralInit(void);
void sensorInit(void);
void serviceInit(void);
void advertisingInit(void);

#endif