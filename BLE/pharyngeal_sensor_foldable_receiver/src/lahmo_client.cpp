#include "lahmo.h"
#include "lahmo_client.h"
#include "lahmo_callbacks.h"
#include "lahmo_sensor_data.h"

LaHMoClient *LaHMoClient::pLaHMoClient = nullptr;
BLEScan *LaHMoClient::pLaHMoScan = nullptr;
BLERemoteService *LaHMoClient::pLaHMoRemoteService = nullptr;
BLERemoteCharacteristic *LaHMoClient::pLaHMoChar = nullptr;
BLEAdvertisedDevice *LaHMoClient::myDevice = nullptr;

bool LaHMoClient::isServiceFound = false;
bool LaHMoClient::isClientConnected = false;
bool LaHMoClient::isStartingNewScan = false;

uint32_t LaHMoClient::previous_millis = 0;
uint32_t LaHMoClient::current_millis = 0;
const uint32_t LaHMoClient::read_interval_millis = 1000;

void LaHMoClient::initScan()
{
    pLaHMoScan = BLEDevice::getScan();
    pLaHMoScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
    pLaHMoScan->setInterval(1349);
    pLaHMoScan->setWindow(449);
    pLaHMoScan->setActiveScan(true);
    pLaHMoScan->start(5, false);
}

void LaHMoClient::handleScanResults()
{
    if (isServiceFound)
    {
        if (connectToServer())
        {
            Serial.println("Connected to the LaHMo server.");
        }
        else
        {
            Serial.println("Failed connection. Given service or characteristic not exist.");
        }
        isServiceFound = false;
        previous_millis = millis();
    }
    else if (isStartingNewScan)
    {
        BLEDevice::getScan()->start(0);
        delay(1000);
    }
}

void LaHMoClient::handleConnection()
{
    if (isClientConnected)
    {
        current_millis = micros();
        if (current_millis - previous_millis >= read_interval_millis)
        {
            std::string data = pLaHMoChar->readValue();
            SensorData::parseSensorData(data);
            previous_millis = current_millis;
        }
    }
}

bool LaHMoClient::connectToServer()
{
    Serial.print("Forming a connection to: ");
    Serial.println(myDevice->getAddress().toString().c_str());

    pLaHMoClient = new LaHMoClient();
    Serial.println(" - Created LaHMo client");
    pLaHMoClient->setClientCallbacks(new MyClientCallback());

    // Connect to the remote LaHMo server
    pLaHMoClient->connect(myDevice);
    Serial.println(" - Connected to LaHMo server");

    // Connection params
    pLaHMoClient->setMTU(517); // maximum transmission unit

    // Obtain a reference to the service we are after in the remote LaHMo server
    pLaHMoRemoteService = pLaHMoClient->getService(LHM_SERVICE_UUID);
    if (pLaHMoRemoteService == nullptr)
    {
        Serial.print("Failed to find our service UUID: ");
        Serial.println(lhm_service_uuid.toString().c_str());
        pLaHMoClient->disconnect();
        return false;
    }
    Serial.println(" - Found our service");

    // Obtain a reference to the characteristic in the service of the remote LaHMo server
    pLaHMoChar = pLaHMoRemoteService->getCharacteristic(LHM_CHAR_UUID);
    if (pLaHMoChar == nullptr)
    {
        Serial.println("Failed to find our characteristic UUID");
        pLaHMoClient->disconnect();
        return false;
    }

    BLEServer* pServer = BLEDevice::createServer();
    if (pServer != nullptr)
    {
        BLEAddress clientAddress = BLEDevice::getAddress();
        uint16_t minInterval = 0x10; // 20ms
        uint16_t maxInterval = 0x20; // 40ms
        uint16_t latency = 0x00;
        uint16_t timeout = 0xA0; // 4000ms
        pServer->updateConnParams((uint8_t*)clientAddress.getNative(), minInterval, maxInterval, latency, timeout);
        Serial.println("Updated connection parameters");

        delete pServer;
    }
    else
    {
        Serial.println("Failed to create BLEServer");
    }

    isClientConnected = true;
    return true;
}