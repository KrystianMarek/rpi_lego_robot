"""
HeartbeatClient - Sends periodic heartbeat to robot server.

Maintains connection by sending heartbeat requests and receiving responses.
This was formerly named HelloClient.
"""
import logging
import time

import zmq
from PyQt5.QtCore import QThread

from app.networking import HeartbeatRequest, get_available_interfaces
from app.common.serialization import compress, decompress


class HeartbeatClient(QThread):
    """
    Sends periodic heartbeat requests to the robot server.

    Used to maintain connection and trigger server-side component startup.
    """

    def __init__(self, server_ip: str, port: int, sleep_time: float = 1):
        QThread.__init__(self, parent=None)
        self._running = True
        self._logger = logging.getLogger(__name__)
        self._host = server_ip
        self._port = port
        self._sleep_time = sleep_time

    def run(self):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        address = "tcp://{}:{}".format(self._host, self._port)
        socket.connect(address)
        self._logger.info("HeartbeatClient starting -> address: {}".format(address))

        sequence = 0
        while self._running:
            try:
                request = HeartbeatRequest(
                    sequence,
                    running=True,
                    network=get_available_interfaces(),
                    sleep=self._sleep_time
                )
                socket.send(compress(request))

                response = decompress(socket.recv())
                sequence = response.sequence
                time.sleep(self._sleep_time)
            except Exception as e:
                self._logger.exception(e)
                break

        socket.close()
        context.term()

    def stop(self):
        """Stop the heartbeat client."""
        self._running = False


# Backward compatibility alias
HelloClient = HeartbeatClient

