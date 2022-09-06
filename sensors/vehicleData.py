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



class VehicleData(RecordableObject):
    def __init__(self,vehicle):
        super().__init__("vehicleData",createProperDir=False)
        self.vehicle = vehicle
        self._itsFile = None
        self._lastVehicleControlCmd = None

    def initRecording(self, baseDir):
        super(VehicleData, self).initRecording(baseDir)
        filename = os.path.join(self._properDir, self._NAME + ".npy")
        self._itsFile = open(filename, "ba+")

    def endRecording(self):
        self._itsFile.close()
        super(VehicleData, self).endRecording()


    def saveDataFrame(self, timestamp):
        if self._lastVehicleControlCmd is not None:
            data = [self._lastVehicleControlCmd.steer, self._lastVehicleControlCmd.throttle, self._lastVehicleControlCmd.brake]
        else:
            data = self.vehicle.getDataOfControls()
        np.save(self._itsFile, {"timestamp": timestamp, "data": data, "currentDateTime": datetime.now()})

    def SetLastCmds(self, lastVehicleControlCmd):
        self._lastVehicleControlCmd = lastVehicleControlCmd



