#ifndef LAHMO_CALLBACKS_H
#define LAHMO_CALLBACKS_H

#include <lahmo.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <BLEClient.h>

class MyClientCallback: public BLEClientCallbacks
{
    void onConnect(BLEClient *pClient);
    void onDisconnect(BLEClient *pClient);
};

class MyAdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks
{
    void onResult(BLEAdvertisedDevice advertisedDevice);
};

#endif