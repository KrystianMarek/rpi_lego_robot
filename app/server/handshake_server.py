"""
HandshakeServer - Handles client connection handshake.

Manages the initial connection from clients and triggers startup of
BrickPi and Kinect components on first client connection.

Formerly named HelloServer.
"""
import logging
import time
from threading import Thread

import zmq

from app.networking import HeartbeatResponse, HeartbeatRequest, get_available_interfaces
from app.common.serialization import compress, decompress
from app.server.BrickPiWrapper import BrickPiWrapper
from app.server.KinectProcess import KinectProcess


class HandshakeServer(Thread):
    """
    REQ/REP server for client handshake.

    Starts BrickPi and Kinect on first client connection.
    No longer needs to track client IP (commands now flow client → robot).
    """

    def __init__(
            self,
            port: int,
            brick_pi_wrapper: BrickPiWrapper,
            kinect_process: KinectProcess,
            sleep_time: float = 1):

        Thread.__init__(self)
        self.daemon = True

        self._port = port
        self._sleep_time = sleep_time
        self._logger = logging.getLogger(__name__)
        self._running = True

        self._brick_pi_wrapper = brick_pi_wrapper
        self._kinect_process = kinect_process
        self._components_started = False

    def run(self):
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        address = "tcp://*:{}".format(self._port)
        socket.bind(address)
        self._logger.info("HandshakeServer starting -> address: {}".format(address))

        while self._running:
            try:
                request = decompress(socket.recv())

                if isinstance(request, HeartbeatRequest):
                    # Start hardware components on first client connection
                    if not self._components_started:
                        self._start_components()
                        self._components_started = True

                    # Send response with server info
                    sequence = request.sequence + 1
                    response = HeartbeatResponse(
                        sequence,
                        running=True,
                        network=get_available_interfaces(),
                        sleep=self._sleep_time
                    )
                    socket.send(compress(response))

                time.sleep(self._sleep_time)

            except KeyboardInterrupt:
                self._logger.debug("Shutting down...")
                self._running = False
            except Exception as e:
                self._logger.exception(e)
                break

        socket.close()
        context.term()

    def _start_components(self):
        """Start BrickPi and Kinect components."""
        self._logger.info("First client connected, starting hardware components...")

        if not self._brick_pi_wrapper.is_alive():
            self._brick_pi_wrapper.start()
            self._logger.info("BrickPiWrapper started")

        if not self._kinect_process.is_alive():
            self._kinect_process.start()
            self._logger.info("KinectProcess started")


# Backward compatibility alias
HelloServer = HandshakeServer

