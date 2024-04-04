#include <Arduino.h>
#include "pharyngeal_sensor_foldable_i2c.h"
#include "LSM6DSOXSensor.h"
#include "MadgwickAHRS.h"
#include "ADS1X15.h"

#include "esp_log.h"
static const char *TAG = "MY_APP";

// ADC
ADS1115 ads(MY_ADS1115_ADDRESS);
volatile bool canOutput = false;

// IMU
LSM6DSOXSensor lsm6dsox(&Wire, LSM6DSOX_I2C_ADD_L);
Madgwick filter;

// Timer
hw_timer_t               *timer;

// LED
volatile bool isLED     = true;
uint8_t stateAcc;
uint8_t stateGyr;
int32_t acc[3];
int32_t gyr[3];
int32_t acc_x, acc_y, acc_z;
int32_t gyr_x, gyr_y, gyr_z;
float roll, pitch, yaw;

// BLE connection
bool isConnectedToClient = false;
bool isConnectedToLastClient = false;

BLEServer         *p_server         = nullptr;
BLECharacteristic *p_lhm_char       = nullptr;
BLEDescriptor      lhm_desc(LHM_DESC_UUID);

void led_on()
{
    digitalWrite(LED0, HIGH);
    digitalWrite(LED1, HIGH);
    digitalWrite(LED2, HIGH);
    digitalWrite(LED3, HIGH);
}

void led_off()
{
    digitalWrite(LED0, LOW);
    digitalWrite(LED1, LOW);
    digitalWrite(LED2, LOW);
    digitalWrite(LED3, LOW);
}

// Connection callbacks
class MyServerCallbacks: public BLEServerCallbacks
{
    void onConnect(BLEServer *p_server)
    {
        isConnectedToClient = true;
    }
    void onDisconnect(BLEServer *p_server)
    {
        isConnectedToClient = false;
    }
};

void IRAM_ATTR onTimer()
{
    static uint32_t previous_micros = micros();
    uint32_t current_micros = micros();

    if (ELAPSED_MICROS >= INTERVAL_US)
    {
        previous_micros = current_micros;
        canOutput = true;
    }
}

void ioInit()
{
    pinMode(LED0, OUTPUT);
    pinMode(LED1, OUTPUT);
    pinMode(LED2, OUTPUT);
    pinMode(LED3, OUTPUT);

    led_on();
}

void peripheralInit()
{
    timer = timerBegin(0, 80, true);
    timerAttachInterrupt(timer, &onTimer, true);
    timerAlarmWrite(timer, ALARM_US, true);
    timerAlarmEnable(timer);
}

void sensorInit()
{
    delay(1000);
    Wire.begin(SDA, SCL);
    Wire.setClock(400000);

	if (!ads.isConnected())
	{
		ESP_LOGE(TAG, "Failed to initialize ADS1115.");
		while (1);
	}
	ESP_LOGV(TAG, "ADS1115 initialized.");
    ads.setMode(0);
	ads.setGain(1);
	ads.setDataRate(7);

	// Initialize IMU
	if (lsm6dsox.begin() != LSM6DSOX_OK)
    {
        ESP_LOGE(TAG, "Cannot initialize IMU!");
        while (1);
    }


	if (lsm6dsox.Enable_G() == LSM6DSOX_OK &&
		lsm6dsox.Enable_X() == LSM6DSOX_OK)
	{
		ESP_LOGV(TAG, "Success enabling accelero and gyro");
	}
	else
	{
		ESP_LOGE(TAG, "Error enabling accelero and gyro");
		while (1);
	}

	uint8_t id;
	lsm6dsox.ReadID(&id);
	if (id != LSM6DSOX_ID)
	{
		ESP_LOGE(TAG, "Wrong id for LSM6DSOX sensor. Check that device is plugged.");
        std::string info = std::to_string(id);
        // ESP_LOGE(TAG, info);
        log_printf(info.c_str());
		while (1);
	}
	else
	{
		ESP_LOGV(TAG, "Success checking id for LSM6DSOX sensor.");
	}

	// IMU setup
	lsm6dsox.Set_X_FS(2);
	lsm6dsox.Set_G_FS(250);
	lsm6dsox.Set_X_ODR(SR);
	lsm6dsox.Set_G_ODR(SR);

    // filter init
    filter.begin(1000000.0f/INTERVAL_US);

    ESP_LOGV(TAG, "Sensor initialized.");
}

void serviceInit()
{
    BLEDevice::init(DEVICE_NAME);
    p_server = BLEDevice::createServer();
    p_server->setCallbacks(new MyServerCallbacks());
    static BLEService *p_lhm_service = p_server->createService(LHM_SERVICE_UUID);

    lhm_desc.setValue("LHM");

    p_lhm_char = p_lhm_service->createCharacteristic(LHM_CHAR_UUID, BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);
    p_lhm_char->addDescriptor(&lhm_desc);

    p_lhm_service->start();
}

void advertisingInit()
{
    static BLEAdvertising *p_advertising = BLEDevice::getAdvertising();
    p_advertising->addServiceUUID(LHM_SERVICE_UUID);
    
    p_advertising->setScanResponse(true);
    p_advertising->setMinPreferred(0x06);
    p_advertising->setMinPreferred(0x12);
    BLEDevice::startAdvertising();
    ESP_LOGV(TAG, "Start advertising.");
}

void setup()
{
    sensorInit();
    ioInit();
    peripheralInit();
    serviceInit();
    advertisingInit();

    // Serial.begin(115200);
    ESP_LOGV(TAG, "Device started.");

    // led_on();
}

void loop()
{   
    if (isConnectedToClient)
    {
        if (canOutput)
        {
            if (lsm6dsox.Get_X_DRDY_Status(&stateAcc) == LSM6DSOX_OK &&
                lsm6dsox.Get_G_DRDY_Status(&stateGyr) == LSM6DSOX_OK)
            {
                lsm6dsox.Get_X_Axes(acc);
                lsm6dsox.Get_G_Axes(gyr);

                acc_x = acc[0]*9.8/1000;
                acc_y = acc[1]*9.8/1000;
                acc_z = acc[2]*9.8/1000;
                gyr_x = gyr[0]/1000;
                gyr_y = gyr[1]/1000;
                gyr_z = gyr[2]/1000;

                filter.updateIMU(gyr_x, gyr_y, gyr_z, acc_x, acc_y, acc_z);
                roll = filter.getRoll();
                pitch = filter.getPitch();
                yaw = filter.getYaw();
            }

            // Read ADC values
            uint32_t timestamp = millis();
            float photovoltage0 = ads.toVoltage(ads.readADC(0));
            float photovoltage1 = ads.toVoltage(ads.readADC(1));
            float photovoltage2 = ads.toVoltage(ads.readADC(2));
            float photovoltage3 = ads.toVoltage(ads.readADC(3));

            // Convert each value to a string
            std::string timestamp_str = std::to_string(static_cast<int32_t>(timestamp));
            std::string photovoltage0_str = std::to_string(photovoltage0);
            std::string photovoltage1_str = std::to_string(photovoltage1);
            std::string photovoltage2_str = std::to_string(photovoltage2);
            std::string photovoltage3_str = std::to_string(photovoltage3);
            std::string roll_str = std::to_string(roll);
            std::string pitch_str = std::to_string(pitch);
            std::string yaw_str = std::to_string(yaw);

            // Combine all the values into a single string, separated by commas
            std::string data = timestamp_str + "," +
                               photovoltage0_str + "," +
                               photovoltage1_str + "," +
                               photovoltage2_str + "," +
                               photovoltage3_str + "," +
                               roll_str + "," +
                               pitch_str + "," +
                               yaw_str;
            p_lhm_char->setValue(data.c_str());
            p_lhm_char->notify();

            canOutput = false;            
        }
    }

    if (!isConnectedToClient && isConnectedToLastClient)
    {
        delay(500);
        p_server->startAdvertising();
        isConnectedToLastClient = isConnectedToClient;
    }

    if (isConnectedToClient && !isConnectedToLastClient)
    {
        isConnectedToLastClient = isConnectedToClient;
    }
}