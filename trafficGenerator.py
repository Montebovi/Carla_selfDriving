import random
import sys
import os
import glob
import traceback

########################################################################################################################
# carla
from carlacfg import CARLA_LIB_PATH

try:
    sys.path.append(glob.glob(CARLA_LIB_PATH + '/carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass
import carla


class TrafficGenerator():
    def __init__(self, world, traffic_manager):
        self.trafficManager = traffic_manager
        # traffic_manager.global_distance_to_leading_vehicle(self, 2.5)
        traffic_manager.set_hybrid_physics_mode(False)
        # traffic_manager.set_hybrid_mode_radius(70)
        self.bps = world.get_blueprint_library().filter('vehicle.*')

        self.world = world
        self._vehiclesList = []

    def generateVehicles(self, numOfVehicles, pointToExclude):
        self._destroyVehicles()
        spawn_points = self.world.get_map().get_spawn_points()
        spawn_points = [p for p in spawn_points if (self._distance(p, pointToExclude) > 20)]
        number_of_spawn_points = len(spawn_points)
        if numOfVehicles > number_of_spawn_points:
            raise Exception("number of vehicles exceeding available points")

        for n, p in enumerate(spawn_points):
            if (n >= numOfVehicles):
                break
            blueprint = random.choice(self.bps)
            if blueprint.has_attribute('color'):
                color = random.choice(blueprint.get_attribute('color').recommended_values)
                blueprint.set_attribute('color', color)
                vehicle = self.world.spawn_actor(blueprint, p)
                vehicle.set_autopilot(True)
                self.trafficManager.vehicle_percentage_speed_difference(vehicle, -30.0)
                self._vehiclesList.append(vehicle)

    def _distance(self, p, pointToExclude):
        return p.location.distance(pointToExclude.location)

    def _destroyVehicles(self):
        for v in self._vehiclesList:
            v.destroy()
        self._vehiclesList = []

    def dispose(self):
        self._destroyVehicles()
