import random
import sys
import os
import glob
import traceback

########################################################################################################################
# carla
from carlacfg import CARLA_LIB_PATH

try:
    sys.path.append(glob.glob(CARLA_LIB_PATH +'/carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass
import carla

import math

class Vehicle(object):
    def __init__(self,world,traffic_manager,blueprint_library, randomPosition=False, numPoint=0):
        bp = blueprint_library.filter("model3")[0]
        bp.set_attribute('role_name', 'hero')
        if randomPosition:
            spawn_point = random.choice(world.get_map().get_spawn_points())
        else:
            spawn_point = world.get_map().get_spawn_points()[numPoint]
        self.initialSpawnPoint = spawn_point
        vehicle = world.spawn_actor(bp, spawn_point)
        #print("role name: ",vehicle.attributes["role_name"])

        #-------------------------------
        # bp1 = world.get_blueprint_library().find('static.prop.box01')
        # box01 = world.spawn_actor(bp1, spawn_point)
        # box01.size = "0.001"
        #--------------------------------

        # if (isAutoPilot):
        #     vehicle.set_autopilot(True)
        # else:
        vehicle.apply_control(carla.VehicleControl(throttle=0.0, steer=0.0))

        traffic_manager.vehicle_percentage_speed_difference(vehicle,-40.0)
        self.actor = vehicle

    def getVelocity(self):
        velocity = self.actor.get_velocity()
        currentVelocity = (math.sqrt(velocity.x ** 2 + velocity.y ** 2 + velocity.z ** 2))  # m/s
        return currentVelocity

    def getDataOfControls(self):
        control = self.actor.get_control()
        data = [control.steer, control.throttle, control.brake]
        return data

    def dispose(self):
        self.actor.destroy()
        self.actor = None
        print("Vehicle destroyed")

    def forceTrafficLightToGreen(self):
        if self.actor.is_at_traffic_light():
            try:
                #print("semaforo rilevato")
                traffic_light = self.actor.get_traffic_light()
                if not (traffic_light is None):
                    traffic_light.set_state(carla.TrafficLightState.Green)
                    traffic_light.set_green_time(60.0)
            except Exception as e:
                traceback.print_exc()
                raise e



