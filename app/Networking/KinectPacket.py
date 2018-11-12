from app.Networking import Packet


class KinectPacket(Packet):
    def __init__(self, sequence, video_frame, depth, tilt_state, tilt_degs):
        Packet.__init__(self, sequence)
        self._video_frame = video_frame
        self._depth = depth
        self._tilt_state = tilt_state
        self._tilt_degs = tilt_degs

    def get_video_frame(self):
        return self._video_frame

    def get_depth(self):
        return self._depth

    def get_tilt_state(self):
        return self._tilt_state

    def get_tilt_degs(self):
        return self._tilt_degs
