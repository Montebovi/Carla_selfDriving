import sys
import os
import glob
import weakref
import cv2
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


class ObstacleSensor(RecordableObject):
    def __init__(self, name, parent_actor, only_dynamics=True):
        super().__init__(name, createProperDir=False)
        self._parent = parent_actor
        world = self._parent.get_world()
        bp = world.get_blueprint_library().find('sensor.other.obstacle')
        bp.set_attribute('distance', '10')
        bp.set_attribute('hit_radius', '1')
        # bp.set_attribute('debug_linetrace', 'true')
        if only_dynamics:
            bp.set_attribute('only_dynamics', 'true')

        sensor_transform = carla.Transform(carla.Location(x=1.6, z=1.3), carla.Rotation(yaw=0))
        # sensor_transform = carla.Transform()

        self.sensor = world.spawn_actor(bp, sensor_transform, attach_to=self._parent)

        weak_self = weakref.ref(self)

        self._distance = None
        self._other_actor = None

        self.sensor.listen(lambda event: ObstacleSensor._on_obstacle(weak_self, event))

    @staticmethod
    def _on_obstacle(weak_self, event):
        self = weak_self()
        if not self:
            return
        self._distance = event.distance
        self._other_actor = event.other_actor
        # print("ObstacleSensor: ", event.distance)

    def initRecording(self, baseDir):
        super(ObstacleSensor, self).initRecording(baseDir)
        filename = os.path.join(self._properDir, self._NAME + ".npy")
        self._itsFile = open(filename, "ba+")

    def endRecording(self):
        self._itsFile.close()
        super(ObstacleSensor, self).endRecording()

    def getLastData(self):
        if self._distance is None:
            return None
        return [self._distance,self._other_actor.type_id]

    def saveDataFrame(self, timestamp):
        if self._distance is not None:
            data = [self._distance]
        else:
            data = [1000]
        # print("ObstacleSensor: ",data)
        np.save(self._itsFile, {"timestamp": timestamp, "data": data, "currentDateTime": datetime.now()})
        self._distance = None

    def dispose(self):
        self.sensor.stop()
        self.sensor.destroy()

    def getDistance(self):
        if self._distance is not None:
            data = self._distance
        else:
            data = 1000
        return data
