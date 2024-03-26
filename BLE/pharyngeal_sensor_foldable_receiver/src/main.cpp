#include <Arduino.h>
#include "lahmo.h"
#include "lahmo_device.h"
#include "lahmo_client.h"

void setup()
{
    Serial.begin(115200);
    while (!Serial);

    Serial.println("Starting pharyngeal sensor receiver...");
    LaHMoDevice::init("");

    LaHMoClient::initScan();
}

void loop()
{
    LaHMoClient::handleScanResults();
    LaHMoClient::handleConnection();
}