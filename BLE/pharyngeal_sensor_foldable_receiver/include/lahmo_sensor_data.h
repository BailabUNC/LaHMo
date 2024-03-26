#ifndef LAHMO_SENSOR_DATA_H
#define LAHMO_SENSOR_DATA_H

#include <string>

class SensorData
{
public:
    static void parseSensorData(const std::string& data);

private:
    static void printSensorData(uint32_t timestamp, float photovoltage0, float photovoltage1,
                                float photovoltage2, float photovoltage3, float roll, float pitch, float yaw);
};

#endif