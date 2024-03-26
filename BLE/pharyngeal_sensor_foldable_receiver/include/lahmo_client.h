#ifndef LAHMO_CLIENT_H
#define LAHMO_CLIENT_H

#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <BLEClient.h>

#include "lahmo.h"

BLEUUID lhm_service_uuid(LHM_SERVICE_UUID);
BLEUUID lhm_char_uuid(LHM_CHAR_UUID);

class LaHMoClient : public BLEClient
{
public:
    static void initScan();
    static void handleScanResults();
    static void handleConnection();

    static bool isServiceFound;
    static bool isClientConnected;
    static bool isStartingNewScan;

    static BLEAdvertisedDevice *myDevice;

private:
    static LaHMoClient *pLaHMoClient;
    static BLEScan *pLaHMoScan;
    static BLERemoteService *pLaHMoRemoteService;
    static BLERemoteCharacteristic *pLaHMoChar;

    static uint32_t previous_millis;
    static uint32_t current_millis;
    static const uint32_t read_interval_millis;

    static bool connectToServer();
};

#endif // LAHMO_CLIENT_H