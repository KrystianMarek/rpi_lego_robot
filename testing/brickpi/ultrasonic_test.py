import time

from BrickPi import BrickPiSetup, PORT_4, TYPE_SENSOR_ULTRASONIC_CONT, \
    BrickPiUpdateValues, BrickPi, BrickPiSetupSensors

BrickPiSetup()  # setup the serial port for communication

port_number = PORT_4	# Define the port number here.

BrickPi.SensorType[port_number] = TYPE_SENSOR_ULTRASONIC_CONT   #Set the type of sensor at PORT_1

BrickPiSetupSensors()   #Send the properties of sensors to BrickPi

while True:
    result = BrickPiUpdateValues()  # Ask BrickPi to update values for sensors/motors
    if not result:
        print(BrickPi.Sensor[port_number])     #BrickPi.Sensor[PORT] stores the value obtained from sensor
    time.sleep(1)     # sleep for 10 ms
