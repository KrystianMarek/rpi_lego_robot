import time


class Packet:
    def __init__(self, sequence):
        self._sequence = sequence
        self._time = time.time()

    @property
    def sequence(self):
        return self._sequence

    # @sequence.setter
    # def sequence(self, sequence):
    #     self._sequence = sequence

    @property
    def time(self):
        return self._time
