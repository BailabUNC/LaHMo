#ifndef PHARYNGEAL_SENSOR_FOLDABLE_RECEIVER_H
#define PHARYNGEAL_SENSOR_FOLDABLE_RECEIVER_H

#include <Arduino.h>
#include <sstream>
#include <string>
#include <vector>

#include "BLEDevice.h"
#include "BLEUtils.h"
#include "BLEServer.h"

#define DEVICE_NAME          "SpectraDerma"
#define LHM_SERVICE_UUID     "0000ACEF-0000-1000-8000-00805F9B34FB"
#define LHM_CHAR_UUID        "0000FF01-0000-1000-8000-00805F9B34FB"
#define LHM_DESC_UUID        (BLEUUID(uint16_t(0x2901)))

#endif