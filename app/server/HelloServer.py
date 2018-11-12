import logging
import time
from threading import Thread

import zmq

from app.Networking import HelloServerPacket, get_available_interfaces, HelloClientPacket
from app.common.Misc import compress, decompress, print_recv, print_send
from app.server.BrickPiWrapper import BrickPiWrapper
from app.server.CommandSubscriber import CommandSubscriber
from app.server.KinectProcess import KinectProcess


class HelloServer(Thread):
    def __init__(
            self, port,
            brick_pi_wrapper: BrickPiWrapper, command_subscriber: CommandSubscriber, kinect_process: KinectProcess,
            sleep_time=1):

        Thread.__init__(self)
        Thread.daemon = True

        self._port = port
        self._sleep_time = sleep_time
        self._logger = logging.getLogger(__name__)
        self._running = True

        self._brick_pi_wrapper = brick_pi_wrapper
        self._command_subscriber = command_subscriber
        self._kinect_process = kinect_process

    @staticmethod
    def get_client_packet(packet: object) -> HelloClientPacket:
        return packet

    def run(self):
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        address = "tcp://*:{}".format(self._port)
        socket.bind(address)
        self._logger.info("Starting -> address: {}".format(address))

        while self._running:
            try:
                response = decompress(socket.recv())
                # self._logger.info(print_recv(response))
                if type(response) is HelloClientPacket and response.sequence == 1:
                    client_hello = self.get_client_packet(response)

                    client_network_data = client_hello.get_network()
                    client_default_iface = client_network_data['default']
                    client_ip = client_network_data[client_default_iface]['addr']

                    if not self._brick_pi_wrapper.isAlive():
                        self._brick_pi_wrapper.start()
                        self._kinect_process.start()
                        self._command_subscriber.set_client_ip(client_ip)
                        self._command_subscriber.start()

                sequence = response.sequence + 1
                request = HelloServerPacket(
                    sequence, running=True, network=get_available_interfaces(), sleep=self._sleep_time)
                socket.send(compress(request))
                # self._logger.info(print_send(request))
                time.sleep(self._sleep_time)
            except KeyboardInterrupt:
                self._logger.debug("exiting...")
                self._running = False
            except Exception as e:
                self._logger.exception(e)
                break

        socket.close()
        context.term()
