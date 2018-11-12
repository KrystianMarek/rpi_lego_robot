import pickle
import zlib

import zmq
import random
import sys
import time

port = "5556"
context = zmq.Context()
socket = context.socket(zmq.PAIR)
socket.connect("tcp://localhost:%s" % port)


def simple():
    while True:
        msg = socket.recv()
        print(msg)


def deserialize():
    while True:
        msg = socket.recv()
        p = zlib.decompress(msg)
        obj = pickle.loads(p)

        print(obj.name)


if __name__ == '__main__':
    simple()
