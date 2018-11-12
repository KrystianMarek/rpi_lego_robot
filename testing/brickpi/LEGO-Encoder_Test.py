#!/usr/bin/env python
from BrickPi import *   #import BrickPi.py file to use BrickPi operations

BrickPiSetup()  # setup the serial port for communication

BrickPi.MotorEnable[PORT_A] = 1     #Enable the Motor A
BrickPi.MotorSpeed[PORT_A] = 100    #Set the speed of MotorA (-255 to 255)

BrickPiSetupSensors()       #Send the properties of sensors to BrickPi

while True:
    result = BrickPiUpdateValues()  # Ask BrickPi to update values for sensors/motors
    if not result:                 # if updating values succeeded
        print(( BrickPi.Encoder[PORT_A] %720 ) /2)   # print the encoder degrees
    time.sleep(.1)		#sleep for 100 ms

# Note: One encoder value counts for 0.5 degrees. So 360 degrees = 720 enc. Hence, to get degress = (enc%720)/2
