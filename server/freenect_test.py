#!/usr/bin/env python
import freenect
import cv2


def get_depth():
    #return frame_convert.pretty_depth_cv(freenect.sync_get_depth()[0])
    narray, _ = freenect.sync_get_depth()
    narray = cv2.cvtColor(narray, cv2.COLOR_RGB2BGR)
    return narray


def get_video():
    #return frame_convert.video_cv(freenect.sync_get_video()[0])
    array,_ = freenect.sync_get_video()
    return cv2.cvtColor(array,cv2.COLOR_RGB2BGR)


for i in range(5):
    #cv.SaveImage('depth_{:>05}.jpg'.format(i), get_depth())
    cv2.imwrite("/home/pi/Pictures/video_{:>05}.jpg".format(i), get_video())

