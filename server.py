#!/usr/bin/env python3
import logging
from queue import Queue

import zmq

from app.common.LoggingWrapper import setup_logging
from app.server.BrickPiWrapper import BrickPiWrapper
from app.server.CommandSubscriber import CommandSubscriber
from app.server.HelloServer import HelloServer
from app.server.KinectProcess import KinectProcess


def server(localhost, brick_pi_port, kinect_port, publisher_port):
    context = zmq.Context()
    logger = logging.getLogger(__name__)
    brick_pi_receiver = context.socket(zmq.PULL)
    brick_pi_receiver.connect("tcp://{}:{}".format(localhost, brick_pi_port))

    kinect_receiver = context.socket(zmq.PULL)
    kinect_receiver.connect("tcp://{}:{}".format(localhost, kinect_port))

    poller = zmq.Poller()
    poller.register(brick_pi_receiver, zmq.POLLIN)
    poller.register(kinect_receiver, zmq.POLLIN)

    publisher = context.socket(zmq.PUB)
    publisher.bind('tcp://*:{}'.format(publisher_port))

    while True:
        try:
            socks = dict(poller.poll())
        except KeyboardInterrupt:
            break

        if brick_pi_receiver in socks:
            # logger.debug("Publishing data from BrickPi")
            publisher.send(brick_pi_receiver.recv())

        if kinect_receiver in socks:
            # logger.debug("Publishing data from Kinect")
            publisher.send(kinect_receiver.recv())

    publisher.close()
    brick_pi_receiver.close()
    kinect_receiver.close()
    context.term()


def main():
    logger = logging.getLogger(__name__)
    localhost = "127.0.0.1"
    hello_server_port = 5556
    brick_pi_port = 5557
    kinect_port = 5558
    publisher_port = 5559

    command_subscriber_port = 5560
    command_queue = Queue(maxsize=100)

    brick_pi_wrapper = BrickPiWrapper(localhost, brick_pi_port, command_queue, 0.1)
    kinect_process = KinectProcess(localhost, kinect_port)
    command_subscriber = CommandSubscriber(command_queue, command_subscriber_port)

    hello_server = HelloServer(
        hello_server_port, brick_pi_wrapper, kinect_process=kinect_process, command_subscriber=command_subscriber)

    hello_server.start()

    server(localhost, brick_pi_port, kinect_port, publisher_port)


if __name__ == '__main__':
    setup_logging()
    main()
