#ifndef PHARYNGEAL_SENSOR_FOLDABLE_RECEIVER_H
#define PHARYNGEAL_SENSOR_FOLDABLE_RECEIVER_H

#include <Arduino.h>
#include <sstream>
#include <string>
#include <vector>

#include "BLEDevice.h"
#include "BLEUtils.h"
#include "BLEServer.h"

#define DEVICE_NAME          "LHM_Yihan"
#define LHM_SERVICE_UUID     "12fb95d1-4954-450f-a82b-802f71541562"
#define LHM_CHAR_UUID        "67136980-20d0-4711-8b37-3acd0fec8e7f"
#define LHM_DESC_UUID        (BLEUUID(uint16_t(0x2901)))

#endif