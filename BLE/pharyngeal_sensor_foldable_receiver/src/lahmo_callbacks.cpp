#include "lahmo_client.h"
#include "lahmo_callbacks.h"

void MyClientCallback::onConnect(BLEClient *pClient)
{
    LaHMoClient::isClientConnected = true;
    Serial.println("Connected to LaHMo server.");
}

void MyClientCallback::onDisconnect(BLEClient *pClient)
{
    LaHMoClient::isClientConnected = false;
    Serial.println("Disconnected from LaHMo server.");
}

void MyAdvertisedDeviceCallbacks::onResult(BLEAdvertisedDevice advertisedDevice)
{
    Serial.print("LaHMo advertised device found: ");
    Serial.println(advertisedDevice.toString().c_str());

    if (advertisedDevice.haveServiceUUID() &&
        advertisedDevice.isAdvertisingService(lhm_service_uuid))
    {
        BLEDevice::getScan()->stop();
        LaHMoClient::myDevice = new BLEAdvertisedDevice(advertisedDevice);
        LaHMoClient::isServiceFound = true;
    }
    else
    {
        LaHMoClient::isStartingNewScan = true;
    }
}