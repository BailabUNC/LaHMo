#include <Arduino.h>
#include "LaHMo2.h"
#include <Adafruit_LSM6DSOX.h>
#include "MadgwickAHRS.h"
#include "ADS1X15.h"
#include "esp_log.h"

static const char *TAG = "MY_APP";

// ADC
ADS1115 ads(MY_ADS1115_ADDRESS);
volatile bool canOutput = false;

// IMU
Adafruit_LSM6DSOX lsm6dsox;
Madgwick filter;

// Timer
hw_timer_t *timer;

// LED
volatile bool isLED = true;
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
BLEService lhmService(LHM_SERVICE_UUID);
BLEStringCharacteristic lhmChar(LHM_CHAR_UUID, BLERead | BLENotify, 100);
BLEDescriptor lhmDesc(LHM_DESC_UUID, "LHM");

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

void IRAM_ATTR onTimer()
{
    canOutput = true;
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
    Wire.setClock(100000);

    if (!ads.isConnected())
    {
        ESP_LOGE(TAG, "Failed to initialize ADS1115.");
        while (1)
            ;
    }
    ESP_LOGI(TAG, "ADS1115 initialized.");
    ads.setMode(0);
    ads.setGain(1);
    ads.setDataRate(7);

    if (!lsm6dsox.begin_I2C()) {
        ESP_LOGE(TAG, "Cannot initialize IMU!");
        while (1) { delay(10); }
    }

    // Configure ranges and data rates
    lsm6dsox.setAccelRange(LSM6DS_ACCEL_RANGE_2_G);
    lsm6dsox.setGyroRange(LSM6DS_GYRO_RANGE_250_DPS);
    // Map SR (Hz) to sensor settings. Using SR defined (e.g., 6667 Hz) is above sensor capability; choose closest valid (e.g., 6.66 kHz not supported). We'll select 1.66 kHz for both.
    lsm6dsox.setAccelDataRate(LSM6DS_RATE_1660_HZ);
    lsm6dsox.setGyroDataRate(LSM6DS_RATE_1660_HZ);
    ESP_LOGI(TAG, "LSM6DSOX initialized with 1660 Hz ODR.");

    filter.begin(1000000.0f / ALARM_US);

    ESP_LOGI(TAG, "Sensor initialized.");
}

void serviceInit()
{
    if (!BLE.begin())
    {
        ESP_LOGE(TAG, "starting BLE failed!");
        while (1)
            ;
    }

    BLE.setLocalName(DEVICE_NAME);
    BLE.setAdvertisedService(lhmService);

    lhmService.addCharacteristic(lhmChar);
    lhmChar.addDescriptor(lhmDesc);
    BLE.addService(lhmService);
}

void advertisingInit()
{
    BLE.advertise();
    ESP_LOGV(TAG, "Start advertising.");
}

void setup()
{
    sensorInit();
    ioInit();
    peripheralInit();
    serviceInit();
    advertisingInit();

    ESP_LOGI(TAG, "Device started.");
}

void loop()
{
    BLEDevice central = BLE.central();

    if (central)
    {
        isConnectedToClient = true;
        while (central.connected())
        {
            if (canOutput)
            {
                sensors_event_t accel;  
                sensors_event_t gyro;   
                sensors_event_t temp;   
                lsm6dsox.getEvent(&accel, &gyro, &temp);

                acc_x = accel.acceleration.x; // m/s^2
                acc_y = accel.acceleration.y;
                acc_z = accel.acceleration.z;
                // Arduino Madgwick library expects gyroscope data in degrees/second.
                gyr_x = gyro.gyro.x * 57.295779513; // rad/s -> deg/s
                gyr_y = gyro.gyro.y * 57.295779513;
                gyr_z = gyro.gyro.z * 57.295779513;

                filter.updateIMU(gyr_x, gyr_y, gyr_z, acc_x, acc_y, acc_z);
                roll = filter.getRoll();
                pitch = filter.getPitch();
                yaw = filter.getYaw();

                uint32_t timestamp = millis();
                float photovoltage0 = ads.toVoltage(ads.readADC(0));
                float photovoltage1 = ads.toVoltage(ads.readADC(1));
                float photovoltage2 = ads.toVoltage(ads.readADC(2));
                float photovoltage3 = ads.toVoltage(ads.readADC(3));

                std::string timestamp_str = std::to_string(static_cast<int32_t>(timestamp));
                std::string photovoltage0_str = std::to_string(photovoltage0);
                std::string photovoltage1_str = std::to_string(photovoltage1);
                std::string photovoltage2_str = std::to_string(photovoltage2);
                std::string photovoltage3_str = std::to_string(photovoltage3);
                std::string roll_str = std::to_string(roll);
                std::string pitch_str = std::to_string(pitch);
                std::string yaw_str = std::to_string(yaw);

                std::string data = timestamp_str + "," +
                                   photovoltage0_str + "," +
                                   photovoltage1_str + "," +
                                   photovoltage2_str + "," +
                                   photovoltage3_str + "," +
                                   roll_str + "," +
                                   pitch_str + "," +
                                   yaw_str;

                lhmChar.writeValue(data.c_str());

                canOutput = false;
            }

            BLE.poll();
        }
        isConnectedToClient = false;
    }

    if (!isConnectedToClient && isConnectedToLastClient)
    {
        delay(500);
        BLE.advertise();
        isConnectedToLastClient = isConnectedToClient;
    }

    if (isConnectedToClient && !isConnectedToLastClient)
    {
        isConnectedToLastClient = isConnectedToClient;
    }
}
