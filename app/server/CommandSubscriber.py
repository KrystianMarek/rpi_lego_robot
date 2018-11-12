import logging
from queue import Queue
from threading import Thread

import zmq

from app.common.Misc import decompress
from app.Networking.CommandPacket import CommandPacket, GoForward, GoBackward, GoLeft, GoRight, TurnLeft, TurnRight, \
    TurretLeft, TurretRight
from app.Networking.TelemetryPacket import TelemetryPacket, LegoMotor


class CommandSubscriber(Thread):
    def __init__(self, queue: Queue, client_port):
        Thread.__init__(self)
        Thread.daemon = False
        self._logger = logging.getLogger(__name__)
        self._running = True

        self._client_ip = None
        self._client_port = client_port

        self._queue = queue

    def set_client_ip(self, ip):
        self._client_ip = ip

    def run(self):
        context = zmq.Context()
        address = "tcp://{}:{}".format(self._client_ip, self._client_port)
        subscriber = context.socket(zmq.SUB)
        subscriber.connect(address)
        subscriber.setsockopt(zmq.SUBSCRIBE, b'')
        self._logger.info("Starting -> address: {}".format(address))

        while self._running:
            try:
                data = decompress(subscriber.recv())
                self.handle_command_packet(data)

            except Exception as e:
                self._logger.exception(e)
                break

        subscriber.close()
        context.term()

    def handle_command_packet(self, packet: CommandPacket):
        try:
            if type(packet) is GoForward:
                self._queue.put_nowait(TelemetryPacket(
                    sequence=0,
                    left_motor=LegoMotor(speed=-packet.value),
                    right_motor=LegoMotor(speed=packet.value)))
            if type(packet) is GoBackward:
                self._queue.put_nowait(TelemetryPacket(
                    0,
                    left_motor=LegoMotor(speed=packet.value),
                    right_motor=LegoMotor(speed=-packet.value)
                ))
            if type(packet) is GoLeft:
                self._queue.put_nowait(TelemetryPacket(
                    0,
                    left_motor=LegoMotor(speed=-int(packet.value/2)),
                    right_motor=LegoMotor(speed=packet.value)
                ))
            if type(packet) is GoRight:
                self._queue.put_nowait(TelemetryPacket(
                    0,
                    left_motor=LegoMotor(speed=-packet.value),
                    right_motor=LegoMotor(speed=int(packet.value/2))
                ))
            if type(packet) is TurnLeft:
                self._queue.put_nowait(TelemetryPacket(
                    0,
                    left_motor=LegoMotor(speed=-packet.value),
                    right_motor=LegoMotor(speed=-packet.value)
                ))
            if type(packet) is TurnRight:
                self._queue.put_nowait(TelemetryPacket(
                    0,
                    left_motor=LegoMotor(speed=packet.value),
                    right_motor=LegoMotor(speed=packet.value)
                ))
            if type(packet) is TurretLeft:
                self._queue.put_nowait(TelemetryPacket(
                    0,
                    turret_motor=LegoMotor(speed=packet.value)
                ))
            if type(packet) is TurretRight:
                self._queue.put_nowait(TelemetryPacket(
                    0,
                    turret_motor=LegoMotor(speed=-packet.value)
                ))

        except Exception as error:
            self._logger.exception(error)
