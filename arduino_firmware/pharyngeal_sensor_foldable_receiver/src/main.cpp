#include <Arduino.h>
#include "pharyngeal_sensor_foldable_receiver.h"
#include "esp_gap_ble_api.h"
#include "esp_log.h"

static const char* TAG = "PHARYNGEAL_SENSOR";

static BLEUUID lhm_serviceUUID(LHM_SERVICE_UUID);
static BLEUUID lhm_charUUID(LHM_CHAR_UUID);

BLEClient *pClient  = nullptr;
BLEScan *pBLEScan = nullptr;
BLERemoteService *pRemoteService = nullptr;

esp_ble_conn_update_params_t    conn_params;

static bool isFoundService = false;
static bool isConnected = false;
static bool isStartNewScan = false;

static BLERemoteCharacteristic *pLHMChar;
static BLEAdvertisedDevice     *myDevice;

void notifyCallback(BLERemoteCharacteristic* pBLERemoteCharacteristic, uint8_t* pData, size_t length, bool isNotify)
{
	// Convert the received data to a string
	std::string data(reinterpret_cast<char*>(pData), length);

	// Parse the values
	std::vector<std::string> values;
	std::stringstream ss(data);
	std::string value;
	while (std::getline(ss, value, ','))
	{
		values.push_back(value);
	}

	if (values.size() >= 8)
	{
		uint32_t timestamp = std::stoul(values[0]);
        float photovoltage0 = std::stof(values[2]);
        float photovoltage1 = std::stof(values[1]);
        float photovoltage2 = std::stof(values[3]);
        float photovoltage3 = std::stof(values[4]);
        float roll = std::stof(values[5]);
        float pitch = std::stof(values[6]);
        float yaw = std::stof(values[7]);

		ESP_LOGI(TAG, "%lu\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f", timestamp, photovoltage0, photovoltage1, photovoltage2, photovoltage3, roll, pitch, yaw);
	}
	else
	{
		ESP_LOGW(TAG, "Received data is incomplete.");
	}
}

class MyClientCallback: public BLEClientCallbacks
{
	void onConnect(BLEClient *pClient)
	{
		isConnected = true;
		ESP_LOGI(TAG, "Connected to the device.");
	}
	void onDisconnect(BLEClient *pClient)
	{
		isConnected = false;
		ESP_LOGI(TAG, "Device disconnected.");
	}
};

bool connect_to_server()
{
	ESP_LOGI(TAG, "Forming a connection to: %s", myDevice->getAddress().toString().c_str());

	pClient = BLEDevice::createClient();
	ESP_LOGI(TAG, " - Created client");
	pClient->setClientCallbacks(new MyClientCallback());

	// Connect to the remote BLE server
	pClient->connect(myDevice);
	ESP_LOGI(TAG, " - Connected to server");
 
	// Connection params
	pClient->setMTU(517); // maximum transmission unit

	// Obtain a reference to the service we are after in the remote BLE server
	pRemoteService = pClient->getService(lhm_serviceUUID);
	if (pRemoteService == nullptr)
	{
		ESP_LOGE(TAG, "Failed to find our service UUID: %s", lhm_serviceUUID.toString().c_str());
		pClient->disconnect();
		return false;
	}
	ESP_LOGI(TAG, " - Found our service");
 
	// Obtain a reference to the characteristic in the service of the remote BLE server
	pLHMChar = pRemoteService->getCharacteristic(lhm_charUUID);
	if (pLHMChar == nullptr)
	{
		ESP_LOGE(TAG, "Failed to find our characteristic UUID");
		pClient->disconnect();
		return false;
	}

	// Enable notifications
	if (pLHMChar->canNotify())
	{
		pLHMChar->registerForNotify(notifyCallback);
		ESP_LOGI(TAG, "Registered for notification.");
	}

	isConnected = true;
	return true;
}


/**
 * Scan for BLE servers and find the first one that advertises the service we are looking for.
 */
class MyAdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks
{
	/**
    * Called for each advertising BLE server.
    */
   void onResult(BLEAdvertisedDevice advertisedDevice)
   {
		ESP_LOGI(TAG, "BLE advertised device found: %s", advertisedDevice.toString().c_str());

		// Check if the device contains the service
		if (advertisedDevice.haveServiceUUID() &&
		    advertisedDevice.isAdvertisingService(lhm_serviceUUID))
		{
			BLEDevice::getScan()->stop();
			myDevice = new BLEAdvertisedDevice(advertisedDevice);
			isFoundService = true;
		}
		else
		{
			isStartNewScan = true;
		}
   }
};

void setup()
{
	ESP_LOGI(TAG, "Starting pharyngeal sensor receiver...");
	BLEDevice::init("");

	// Retrieve a Scanner and set the callback we want to use to be informed when we
    // have detected a new device. Specify that we want active scanning and start the
    // scan to run for 5 seconds.
    pBLEScan = BLEDevice::getScan();
    pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
    pBLEScan->setInterval(1349);
    pBLEScan->setWindow(449);
    pBLEScan->setActiveScan(true);
    pBLEScan->start(5, false);
}

void loop()
{
	// If the flag "isFoundService" is true, then we have scanned for and found the desired
    // BLE Server with which we wish to connect. Now we connect to it. Once we are
    // connected we set the connected flag to be true
	if (isFoundService)
	{
		if (connect_to_server())
		{
			ESP_LOGI(TAG, "Connect to the BLE server.");
		}
		else
		{
			ESP_LOGE(TAG, "Failed connection. Given service or characteristic not exist.");
		}
		isFoundService = false;
	}
	else if (isStartNewScan && !isConnected)
	{
		BLEDevice::getScan()->start(0);
		delay(1000);
	}
}