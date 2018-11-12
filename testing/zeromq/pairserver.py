import pickle
import zlib

import zmq
import random
import sys
import time

from MyClass import MyClass

port = "5556"
context = zmq.Context()
socket = context.socket(zmq.PAIR)
socket.bind("tcp://*:%s" % port)


def simple():
    while True:
        socket.send_string("Server message to client3")
        msg = socket.recv()
        print(msg)
        time.sleep(1)


def serialize():
    for index in range(10):
        obj = MyClass("instance_{}".format(index))
        p = pickle.dumps(obj)
        z = zlib.compress(p)
        socket.send(z)
        time.sleep(1)


if __name__ == '__main__':
    serialize()
