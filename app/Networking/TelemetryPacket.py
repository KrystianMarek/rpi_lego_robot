from app.Networking import Packet


class SystemStats:
    """System statistics from the robot (CPU, RAM, Network)."""

    def __init__(self):
        self._cpu_percent = 0.0
        self._ram_percent = 0.0
        self._ram_used_mb = 0.0
        self._ram_total_mb = 0.0
        self._net_bytes_sent = 0
        self._net_bytes_recv = 0
        self._net_bandwidth_mbps = 0.0  # Calculated bandwidth

    @property
    def cpu_percent(self) -> float:
        return self._cpu_percent

    @cpu_percent.setter
    def cpu_percent(self, value: float):
        self._cpu_percent = value

    @property
    def ram_percent(self) -> float:
        return self._ram_percent

    @ram_percent.setter
    def ram_percent(self, value: float):
        self._ram_percent = value

    @property
    def ram_used_mb(self) -> float:
        return self._ram_used_mb

    @ram_used_mb.setter
    def ram_used_mb(self, value: float):
        self._ram_used_mb = value

    @property
    def ram_total_mb(self) -> float:
        return self._ram_total_mb

    @ram_total_mb.setter
    def ram_total_mb(self, value: float):
        self._ram_total_mb = value

    @property
    def net_bytes_sent(self) -> int:
        return self._net_bytes_sent

    @net_bytes_sent.setter
    def net_bytes_sent(self, value: int):
        self._net_bytes_sent = value

    @property
    def net_bytes_recv(self) -> int:
        return self._net_bytes_recv

    @net_bytes_recv.setter
    def net_bytes_recv(self, value: int):
        self._net_bytes_recv = value

    @property
    def net_bandwidth_mbps(self) -> float:
        return self._net_bandwidth_mbps

    @net_bandwidth_mbps.setter
    def net_bandwidth_mbps(self, value: float):
        self._net_bandwidth_mbps = value


class LegoMotor:
    def __init__(self, port=None, speed=0, desired_speed=0, angle=0):
        self._port = port
        self._speed = speed
        self._desired_speed = desired_speed
        self._angle = angle

    @property
    def port(self):
        return self._port

    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, speed):
        self._speed = speed

    @property
    def desired_speed(self):
        return self._desired_speed

    @desired_speed.setter
    def desired_speed(self, desired_speed):
        self._desired_speed = desired_speed

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, angle):
        self._angle = angle

    def stop(self):
        self._speed = 0


class LegoSensor:
    def __init__(self, port=None):
        self._port = port
        self._raw = 0

    @property
    def port(self):
        return self._port

    @property
    def raw(self):
        return self._raw

    @raw.setter
    def raw(self, raw):
        self._raw = raw


class TelemetryPacket(Packet):
    def __init__(self, sequence, left_motor=LegoMotor(), right_motor=LegoMotor(),
                 turret_motor=LegoMotor(), ultrasound_sensor=LegoSensor(), color_sensor=LegoSensor()):
        Packet.__init__(self, sequence)
        self._left_motor = left_motor
        self._right_motor = right_motor
        self._turret_motor = turret_motor

        self._ultrasound_sensor = ultrasound_sensor
        self._color_sensor = color_sensor

        self._voltage = 0
        self._temperature = 0
        self._system_stats = SystemStats()

    @property
    def voltage(self):
        return self._voltage

    @voltage.setter
    def voltage(self, voltage):
        self._voltage = voltage

    @property
    def temperature(self):
        return self._temperature

    @temperature.setter
    def temperature(self, temperature):
        self._temperature = temperature

    @property
    def left_motor(self) -> LegoMotor:
        return self._left_motor

    @left_motor.setter
    def left_motor(self, motor: LegoMotor):
        self._left_motor = motor

    @property
    def right_motor(self) -> LegoMotor:
        return self._right_motor

    @right_motor.setter
    def right_motor(self, motor: LegoMotor):
        self._right_motor = motor

    @property
    def turret_motor(self) -> LegoMotor:
        return self._turret_motor

    @turret_motor.setter
    def turret_motor(self, motor: LegoMotor):
        self._turret_motor = motor

    @property
    def ultrasound_sensor(self) -> LegoSensor:
        return self._ultrasound_sensor

    @ultrasound_sensor.setter
    def ultrasound_sensor(self, sensor: LegoSensor):
        self._ultrasound_sensor = sensor

    @property
    def color_sensor(self) -> LegoSensor:
        return self._color_sensor

    @color_sensor.setter
    def color_sensor(self, sensor: LegoSensor):
        self._color_sensor = sensor

    @property
    def system_stats(self) -> SystemStats:
        return self._system_stats

    @system_stats.setter
    def system_stats(self, stats: SystemStats):
        self._system_stats = stats