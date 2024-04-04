#include <Arduino.h>
#include "pharyngeal_sensor_foldable_receiver.h"
#include "esp_gap_ble_api.h"

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

static uint32_t                 previous_micros;
static uint32_t                 current_micros;
static const uint32_t           READ_INTERVAL_US = 1;

class MyClientCallback: public BLEClientCallbacks
{
	void onConnect(BLEClient *pClient)
	{
		esp_err_t err;
		isConnected = true;
		
		// Prepare the connection paramters update request
		conn_params.latency = 0;
		conn_params.max_int = 0x20; // max_int = 0x20*1.25ms = 40ms
		conn_params.min_int = 0x10; // min_int = 0x10*1.25ms = 20ms
		conn_params.timeout = 400;  // timeout = 400*10ms = 4000ms
		err = ::esp_ble_gap_update_conn_params(&conn_params);

		if (err != ESP_OK)
		{
			Serial.printf("esp_ble_gap_update_conn_params: rc=%d %s\n", err, esp_err_to_name(err));
		}
		else
		{
			Serial.println("Connection params updated.");
		}

		BLEAddress peerAddress = myDevice->getAddress();
		esp_bd_addr_t *remote_bd_addr = peerAddress.getNative();

		err = esp_ble_gap_set_prefered_phy(*remote_bd_addr,
								     	   ESP_BLE_GAP_NO_PREFER_RECEIVE_PHY | ESP_BLE_GAP_NO_PREFER_TRANSMIT_PHY, // Set 'no preference' for certain PHYs
								     	   ESP_BLE_GAP_PHY_2M_PREF_MASK, // Prefer 2M PHY for TX
								     	   ESP_BLE_GAP_PHY_2M_PREF_MASK, // Prefer 2M PHY for RX
								     	   ESP_BLE_GAP_PHY_OPTIONS_NO_PREF  // No specific PHY options
    							     	  );
		if (err != ESP_OK)
		{
			Serial.println("Error setting preferred PHY");
		}
		else
		{
			Serial.println("Set to 2M PHY");
		}
	}
	void onDisconnect(BLEClient *pClient)
	{
		isConnected = false;
		Serial.println("Device desconnected.");
	}
};

bool connect_to_server()
{
	Serial.print("Forming a connection to: ");
	Serial.println(myDevice->getAddress().toString().c_str());

	pClient = BLEDevice::createClient();
	Serial.println(" - Created client");
	pClient->setClientCallbacks(new MyClientCallback());

	// Connect to the remote BLE server
	pClient->connect(myDevice);
	Serial.println(" - Connected to server");
 
	// Connection params
	pClient->setMTU(517); // maximum transmission unit

	// Obtain a reference to the service we are after in the remote BLE server
	pRemoteService = pClient->getService(lhm_serviceUUID);
	if (pRemoteService == nullptr)
	{
		Serial.print("Failed to find our service UUID: ");
		Serial.println(lhm_serviceUUID.toString().c_str());
		pClient->disconnect();
		return false;
	}
	Serial.println(" - Found our service");
 
	// Obtain a reference to the characteristic in the service of the remote BLE server
	pLHMChar = pRemoteService->getCharacteristic(lhm_charUUID);
	if (pLHMChar == nullptr)
	{
		Serial.println("Failed to find our characteristic UUID"); // TODO
		pClient->disconnect();
		return false;
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
		Serial.print("BLE advertised device found: ");
		Serial.println(advertisedDevice.toString().c_str());

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
	Serial.begin(115200);
	while (!Serial);

	Serial.println("Starting pharyngeal sensor receiver...");
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
			Serial.println("Connected to the BLE server.");
		}
		else
		{
			Serial.println("Failed connection. Given service or characteristic not exist.");
		}
		isFoundService = false;
		previous_micros = micros();
	}
	// If we are connected
	if (isConnected)
	{
		// Serial.println(micros());
		current_micros = micros();
		if (current_micros - previous_micros >= READ_INTERVAL_US)
		{
			std::string data = pLHMChar->readValue();

			std::vector<std::string> values;
			std::stringstream ss(data);
			std::string value;
			while (std::getline(ss, value, ','))
			{
				values.push_back(value);
			}
			uint32_t timestamp = std::stoul(values[0]);
			float photovoltage0 = std::stof(values[1]);
			float photovoltage1 = std::stof(values[2]);
			float photovoltage2 = std::stof(values[3]);
			float photovoltage3 = std::stof(values[4]);
			float roll = std::stof(values[5]);
			float pitch = std::stof(values[6]);
			float yaw = std::stof(values[7]);

			Serial.print(timestamp);
            Serial.print("\t");
            Serial.print(photovoltage0, 4);
            Serial.print("\t");
            Serial.print(photovoltage1, 4);
            Serial.print("\t");
			Serial.print(photovoltage2, 4);
            Serial.print("\t");
			Serial.print(photovoltage3, 4);
            Serial.print("\t");

            Serial.print(roll, 4);
            Serial.print("\t");
            Serial.print(pitch, 4);
            Serial.print("\t");
            Serial.print(yaw, 4);
            Serial.print("\t");

            Serial.print("\n");

			previous_micros = current_micros;
			current_micros = micros();
		}
		// Serial.println(micros());
	}
	else if (isStartNewScan)
	{
		BLEDevice::getScan()->start(0);
		delay(1000);
	}
}