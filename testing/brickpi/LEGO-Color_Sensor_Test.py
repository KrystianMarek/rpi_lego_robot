#!/usr/bin/env python
from BrickPi import *

BrickPiSetup()

Color_Sensor_Port = PORT_1
BrickPi.SensorType[Color_Sensor_Port] = TYPE_SENSOR_LIGHT_ON   #Set the type of sensor

BrickPiSetupSensors()

while True:
    result = BrickPiUpdateValues()
    if not result:
        print(BrickPi.Sensor[Color_Sensor_Port])
    time.sleep(1)     # sleep for 100 ms
