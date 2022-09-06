import glob
import os
import sys
import math

from carlacfg import CARLA_LIB_PATH

try:
    sys.path.append(glob.glob(CARLA_LIB_PATH + '/carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass
import carla


class ForwardAgent:
    def __init__(self, vehicleActor, pilotMode,  maxSpeedKmh = 30.0):
        self._maxSpeedKmh = maxSpeedKmh
        self._pilotMode = pilotMode
        self._vehicleActor = vehicleActor
        self._control = carla.VehicleControl()

    def run_step(self, measurements, sensors_data):
        if not (self._pilotMode.IsAgentMode()):
            return None

        self._control.throttle = 0.8
        self._control.brake = 0.0
        self._control.steer = 0.0

        velocity = self._vehicleActor.get_velocity()
        velocity = (math.sqrt(velocity.x ** 2 + velocity.y ** 2 + velocity.z ** 2)) * 3.6  # m/s
        if velocity > self._maxSpeedKmh:
            self._control.throttle = (10 - min((velocity - self._maxSpeedKmh), 10)) / 10.0

        self._vehicleActor.apply_control(self._control)

        return self._control
