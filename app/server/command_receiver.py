"""
CommandReceiver - Receives movement commands from clients.

Uses ZMQ PULL socket that BINDS to a port, allowing multiple clients
to connect and send commands. This is the inverse of the old
CommandSubscriber which required knowing the client's IP address.
"""
import logging
from queue import Queue
from threading import Thread

import zmq

from app.common.config import Config
from app.common.serialization import decompress
from app.networking import (
    CommandPacket, GoForward, GoBackward, GoLeft, GoRight,
    TurnLeft, TurnRight, TurretLeft, TurretRight, TurretReset,
    TelemetryPacket, LegoMotor
)


class CommandReceiver(Thread):
    """
    Receives commands from clients via ZMQ PULL socket.

    The robot BINDS to a port and clients CONNECT to it.
    This allows multiple clients and eliminates the need for client IP discovery.
    """

    def __init__(self, queue: Queue, port: int = None):
        if port is None:
            port = Config.COMMAND_PORT
        Thread.__init__(self)
        self.daemon = True
        self._logger = logging.getLogger(__name__)
        self._running = True
        self._port = port
        self._queue = queue

    @property
    def running(self):
        return self._running

    @running.setter
    def running(self, value: bool):
        self._running = value

    def run(self):
        context = zmq.Context()
        receiver = context.socket(zmq.PULL)
        address = "tcp://*:{}".format(self._port)
        receiver.bind(address)
        self._logger.info("Starting -> address: {}".format(address))

        while self._running:
            try:
                data = decompress(receiver.recv())
                self.handle_command_packet(data)
            except zmq.ZMQError as e:
                if self._running:
                    self._logger.exception(e)
                break
            except Exception as e:
                self._logger.exception(e)
                break

        receiver.close()
        context.term()

    def handle_command_packet(self, packet: CommandPacket):
        """Translate high-level commands to motor control packets."""
        try:
            if type(packet) is GoForward:
                self._queue.put_nowait(TelemetryPacket(
                    sequence=0,
                    left_motor=LegoMotor(speed=-packet.value),
                    right_motor=LegoMotor(speed=packet.value)
                ))
            elif type(packet) is GoBackward:
                self._queue.put_nowait(TelemetryPacket(
                    sequence=0,
                    left_motor=LegoMotor(speed=packet.value),
                    right_motor=LegoMotor(speed=-packet.value)
                ))
            elif type(packet) is GoLeft:
                self._queue.put_nowait(TelemetryPacket(
                    sequence=0,
                    left_motor=LegoMotor(speed=-int(packet.value / 2)),
                    right_motor=LegoMotor(speed=packet.value)
                ))
            elif type(packet) is GoRight:
                self._queue.put_nowait(TelemetryPacket(
                    sequence=0,
                    left_motor=LegoMotor(speed=-packet.value),
                    right_motor=LegoMotor(speed=int(packet.value / 2))
                ))
            elif type(packet) is TurnLeft:
                self._queue.put_nowait(TelemetryPacket(
                    sequence=0,
                    left_motor=LegoMotor(speed=-packet.value),
                    right_motor=LegoMotor(speed=-packet.value)
                ))
            elif type(packet) is TurnRight:
                self._queue.put_nowait(TelemetryPacket(
                    sequence=0,
                    left_motor=LegoMotor(speed=packet.value),
                    right_motor=LegoMotor(speed=packet.value)
                ))
            elif type(packet) is TurretLeft:
                self._queue.put_nowait(TelemetryPacket(
                    sequence=0,
                    turret_motor=LegoMotor(speed=packet.value)
                ))
            elif type(packet) is TurretRight:
                self._queue.put_nowait(TelemetryPacket(
                    sequence=0,
                    turret_motor=LegoMotor(speed=-packet.value)
                ))
            elif type(packet) is TurretReset:
                self._queue.put_nowait(TelemetryPacket(
                    sequence=0,
                    turret_motor=LegoMotor(speed=0)
                ))
        except Exception as error:
            self._logger.exception(error)

