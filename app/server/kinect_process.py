import freenect
import logging
import numpy as np
from multiprocessing import Process

import zmq

from app.networking import KinectPacket
from app.common.serialization import compress


class KinectProcess(Process):
    def __init__(self, host, port, running=True):
        Process.__init__(self)
        Process.daemon = True
        self._host = host
        self._port = port
        self._running = running
        self._logger = logging.getLogger(__name__)
        self._freenect = freenect
        self._kinect_device = 0

    @property
    def running(self):
        return self._running

    @running.setter
    def running(self, running):
        self._running = running

    def run(self):
        # self._freenect.open_device(self._kinect_device)
        context = zmq.Context()
        sender = context.socket(zmq.PUSH)
        address = "tcp://{}:{}".format(self._host, self._port)
        sender.bind(address)
        self._logger.info("Starting -> address: {}".format(address))

        sequence = 0
        while self._running:
            try:
                kinect_packet = KinectPacket(
                    sequence,
                    self.get_video(),
                    self.get_depth(),
                    self.get_tilt_state(),
                    self.get_tilt_degs())
                # self._logger.debug("Kinect sending {}".format(kinect_packet))
                sender.send(compress(kinect_packet))
            except KeyboardInterrupt:
                self._logger.debug("exiting...")
                self._running = False
            except Exception as e:
                self._logger.exception(e)
                break

            sequence += 1

        self._freenect.sync_stop()
        self._freenect.close_device(self._kinect_device)
        sender.close()
        context.term()

    def get_video(self):
        array, _ = self._freenect.sync_get_video(self._kinect_device)
        # return cv2.cvtColor(array, cv2.COLOR_RGB2BGR)
        return array

    def get_depth(self):
        array, _ = self._freenect.sync_get_depth(self._kinect_device)
        # array = cv2.cvtColor(array, cv2.COLOR_RGB2BGR)
        return array

    @staticmethod
    def pretty_depth(depth):
        """Converts depth into a 'nicer' format for display

        This is abstracted to allow for experimentation with normalization

        Args:
            depth: A numpy array with 2 bytes per pixel

        Returns:
            A numpy array that has been processed with unspecified datatype
        """
        np.clip(depth, 0, 2**10 - 1, depth)
        depth >>= 2
        return depth.astype(np.uint8)

    def get_tilt_state(self):
        # tilt_state, _ = self._freenect.get_tilt_state()
        return 0

    def get_tilt_degs(self):
        #tilt_degs, _ = self._freenect.get_tilt_degs()
        return 0

