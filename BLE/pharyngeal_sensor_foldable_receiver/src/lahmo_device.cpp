#include "lahmo_device.h"

void LaHMoDevice::init(std::string deviceName)
{
    BLEDevice::init(deviceName);
}

BLEAdvertising* LaHMoDevice::getAdvertising()
{
    return BLEDevice::getAdvertising();
}

void LaHMoDevice::startAdvertising()
{
    BLEAdvertising* advertising = getAdvertising();
    advertising->start();
}

BLEServer* LaHMoDevice::createServer()
{
    return BLEDevice::createServer();
}