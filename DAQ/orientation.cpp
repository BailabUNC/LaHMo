#include <MadgwickAHRS.h>
#include <Arduino_LSM6DSOX.h>

uint32_t current_time;
uint32_t previous_time;
uint32_t read_interval;

int16_t delta_time;

Madgwick filter;
float roll, pitch, yaw;
float Ax, Ay, Az;
float Gx, Gy, Gz;

void log_data()
{
    Serial.println("Accelerometer data: ");
    Serial.print(Ax);
    Serial.print('\t');
    Serial.print(Ay);
    Serial.print('\t');
    Serial.println(Az);
    Serial.println();

    Serial.println("Gyroscope data: ");
    Serial.print(Gx);
    Serial.print('\t');
    Serial.print(Gy);
    Serial.print('\t');
    Serial.println(Gz);
    Serial.println();
}

void setup()
{
    uint32_t sample_rate;

    Serial.begin(9600);

    while(!Serial);

    if (!IMU.begin()) {
        Serial.println("Failed to initialize IMU!");
        while (1);
    }

    // Serial.print("Accelerometer sample rate = ");
    // Serial.print(IMU.accelerationSampleRate());
    // Serial.println("Hz");
    // Serial.println();

    // Serial.print("Gyroscope sample rate = ");  
    // Serial.print(IMU.gyroscopeSampleRate());
    // Serial.println("Hz");
    // Serial.println();

    delay(100);

    if (IMU.accelerationSampleRate() == IMU.gyroscopeSampleRate())
    {
        sample_rate = IMU.accelerationSampleRate();
        filter.begin(sample_rate);
    }
    else
    {
        Serial.println("Wrong sample rate");
        while (1);
    }

    // Time initialization
    // read_interval = 1000000 / sample_rate;
    read_interval = 10000;
    previous_time = micros();
    // Serial.println("Orientation detection start");
}

void loop()
{
    current_time = micros();
    if (current_time - previous_time >= read_interval)
    {
        if (IMU.accelerationAvailable())
        {
            IMU.readAcceleration(Ax, Ay, Az);
        }

        if (IMU.gyroscopeAvailable())
        {
            IMU.readGyroscope(Gx, Gy, Gz);
        }

        // log_data();

        filter.updateIMU(Gx, Gy, Gz, Ax, Ay, Az);
        roll = filter.getRoll();
        pitch = filter.getPitch();
        yaw = filter.getYaw();

        // Serial.print("Orientation: ");
        Serial.print(yaw);
        Serial.print("\t");
        Serial.print(pitch);
        Serial.print("\t");
        Serial.println(roll);

        previous_time += read_interval;
    }
}