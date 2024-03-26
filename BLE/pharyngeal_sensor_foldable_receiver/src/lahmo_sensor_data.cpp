
#include <sstream>
#include <vector>
#include "lahmo.h"
#include "lahmo_sensor_data.h"

void SensorData::parseSensorData(const std::string& data)
{
    std::vector<std::string> values;
    std::stringstream ss(data);
    std::string value;
    while (std::getline(ss, value, ','))
    {
        values.push_back(value);
    }

    if (values.size() == 8)
    {
        uint32_t timestamp = std::stoul(values[0]);
        float photovoltage0 = std::stof(values[1]);
        float photovoltage1 = std::stof(values[2]);
        float photovoltage2 = std::stof(values[3]);
        float photovoltage3 = std::stof(values[4]);
        float roll = std::stof(values[5]);
        float pitch = std::stof(values[6]);
        float yaw = std::stof(values[7]);

        printSensorData(timestamp, photovoltage0, photovoltage1,
                        photovoltage2, photovoltage3, roll, pitch, yaw);
    }
    else
    {
        Serial.println("Received data format is incorrect.");
    }
}

void SensorData::printSensorData(uint32_t timestamp, float photovoltage0, float photovoltage1,
                                 float photovoltage2, float photovoltage3, float roll, float pitch, float yaw)
{
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
}