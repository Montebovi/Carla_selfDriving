import sys
import os
import glob
from datetime import datetime
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



class VehicleState(RecordableObject):
    def __init__(self,vehicle):
        super().__init__("vehicleState", createProperDir=False)
        self.vehicle = vehicle
        self._itsFile = None

    def initRecording(self, baseDir):
        super(VehicleState, self).initRecording(baseDir)
        filename = os.path.join(self._properDir, self._NAME + ".npy")
        self._itsFile = open(filename, "ba+")

    def endRecording(self):
        self._itsFile.close()
        super(VehicleState, self).endRecording()

    def saveDataFrame(self, timestamp):
        speed = self.vehicle.getVelocity()
        np.save(self._itsFile, {"timestamp": timestamp, "speed_ms": speed, "currentDateTime": datetime.now()})

    def getSpeed_ms(self):
        return self.vehicle.getVelocity()


