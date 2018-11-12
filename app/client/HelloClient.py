import logging
import time
from threading import Thread

import zmq
from PyQt5.QtCore import QThread

from app.Networking import HelloClientPacket, get_available_interfaces
from app.common.Misc import compress, decompress, print_send, print_recv


class HelloClient(QThread):
    def __init__(self, server_ip, port, sleep_time=1):
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
        self._logger.info("Starting -> address: {}".format(address))

        sequence = 0
        while self._running:
            try:
                request = HelloClientPacket(
                    sequence, running=True, network=get_available_interfaces(), sleep=self._sleep_time)
                # self._logger.debug(print_send(request))
                socket.send(compress(request))

                response = decompress(socket.recv())
                # self._logger.debug(print_recv(response))
                sequence = response.sequence
                time.sleep(self._sleep_time)
            except Exception as e:
                self._logger.exception(e)
                break

        socket.close()
        context.term()
