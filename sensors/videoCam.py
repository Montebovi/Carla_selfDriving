import sys
import os
import glob
import weakref
import cv2
import numpy as np

########################################################################################################################
# carla
from carlacfg import CARLA_LIB_PATH
from sensors.recordableObject import RecordableObject

try:
    sys.path.append(glob.glob(CARLA_LIB_PATH + '/carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass
import carla

class VideoCam(RecordableObject):
    def __init__(self,name,width=320, height=240):
        super().__init__(name, createProperDir=True)
        self._name = name
        self._width = width
        self._height = height
        self._camera = None

    def initRecording(self, baseDir):
        super(VideoCam, self).initRecording(baseDir)
        self._closeCamera()
        self._camera = cv2.VideoCapture(0)
        self._camera.set(3, self._width)
        self._camera.set(4, self._height)

    def saveDataFrame(self, timestamp):
        return_value, image = self._camera.read()
        fullFileName = os.path.join(self._properDir, str(timestamp).zfill(10) + ".jpg")
        cv2.imwrite(fullFileName, image)
        pass

    def endRecording(self):
        self._closeCamera()
        # cv2.destroyAllWindows()
        super(VideoCam, self).endRecording()

    def _closeCamera(self):
        if (self._camera):
            self._camera.release()
            self._camera = None
