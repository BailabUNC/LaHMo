#include <Arduino.h>
#include "LaHMo2.h"
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

    if (lsm6dsox.begin() != LSM6DSOX_OK)
    {
        ESP_LOGE(TAG, "Cannot initialize IMU!");
        while (1)
            ;
    }

    if (lsm6dsox.Enable_G() == LSM6DSOX_OK &&
        lsm6dsox.Enable_X() == LSM6DSOX_OK)
    {
        ESP_LOGI(TAG, "Success enabling accelero and gyro");
    }
    else
    {
        ESP_LOGE(TAG, "Error enabling accelero and gyro");
        while (1)
            ;
    }

    uint8_t id;
    lsm6dsox.ReadID(&id);
    if (id != LSM6DSOX_ID)
    {
        ESP_LOGE(TAG, "Wrong id for LSM6DSOX sensor. Check that device is plugged.");
        while (1)
            ;
    }
    else
    {
        ESP_LOGI(TAG, "Success checking id for LSM6DSOX sensor.");
    }

    lsm6dsox.Set_X_FS(2);
    lsm6dsox.Set_G_FS(250);
    lsm6dsox.Set_X_ODR(SR);
    lsm6dsox.Set_G_ODR(SR);
    lsm6dsox.Set_FIFO_Mode(LSM6DSOX_BYPASS_MODE);
    lsm6dsox.Set_FIFO_Mode(LSM6DSOX_STREAM_MODE);

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
                if (lsm6dsox.Get_X_DRDY_Status(&stateAcc) == LSM6DSOX_OK &&
                    lsm6dsox.Get_G_DRDY_Status(&stateGyr) == LSM6DSOX_OK)
                {
                    lsm6dsox.Get_X_Axes(acc);
                    lsm6dsox.Get_G_Axes(gyr);

                    acc_x = acc[0] * 9.8 / 1000;
                    acc_y = acc[1] * 9.8 / 1000;
                    acc_z = acc[2] * 9.8 / 1000;
                    gyr_x = gyr[0] / 1000;
                    gyr_y = gyr[1] / 1000;
                    gyr_z = gyr[2] / 1000;

                    filter.updateIMU(gyr_x, gyr_y, gyr_z, acc_x, acc_y, acc_z);
                    roll = filter.getRoll();
                    pitch = filter.getPitch();
                    yaw = filter.getYaw();
                }

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
