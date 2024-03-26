#ifndef LAHMO_DEVICE_H
#define LAHMO_DEVICE_H

#include <BLEDevice.h>

class LaHMoDevice
{
public:
    static void init(std::string deviceName);
    static BLEAdvertising* getAdvertising();
    static void startAdvertising();

private:
    static BLEServer* createServer();
};

#endif // LAHMO_DEVICE_H