"""
CommandClient - Sends commands to the robot.

Connects to the robot's CommandReceiver via ZMQ PUSH socket.
"""
import logging

import zmq
from PyQt5 import QtCore

from app.common.config import Config
from app.common.serialization import compress
from app.networking import CommandPacket


class CommandClient(QtCore.QThread):
    """
    Sends commands to the robot via ZMQ PUSH socket.

    Connects to the robot's CommandReceiver (PULL socket).
    This is the inverse of the old design where the robot connected to the client.
    """

    def __init__(self, robot_ip: str, port: int = None, parent=None):
        if port is None:
            port = Config.COMMAND_PORT
        QtCore.QThread.__init__(self, parent)
        self._logger = logging.getLogger(__name__)
        self._running = True
        self._robot_ip = robot_ip
        self._port = port
        self._context = zmq.Context()
        self._sender = self._context.socket(zmq.PUSH)

        # Connect to robot's command receiver
        address = "tcp://{}:{}".format(robot_ip, port)
        self._sender.connect(address)
        self._logger.info("CommandClient connected to {}".format(address))

    def on_command_packet(self, packet: CommandPacket):
        """Send a command packet to the robot."""
        try:
            self._sender.send(compress(packet))
        except Exception as e:
            self._logger.exception(e)

    def run(self):
        """Keep thread alive while running."""
        while self._running:
            QtCore.QThread.msleep(100)

        self._sender.close()
        self._context.term()

    def stop(self):
        """Stop the command client."""
        self._running = False

