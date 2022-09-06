import os
import sys
import glob

from carlacfg import CARLA_LIB_PATH

try:
    sys.path.append(glob.glob(CARLA_LIB_PATH +'/carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass
import carla


class SimWorld(object):
    def __init__(self, carla_world, traffic_manager, fps):
        self.world = carla_world
        settings = self.world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = 1.0 / fps
        self.world.apply_settings(settings)

        self.traffic_manager = traffic_manager
        self.traffic_manager.set_synchronous_mode(True)

        self.blueprint_library = self.world.get_blueprint_library()
        self.objects = []

        semafori =self.world.get_actors().filter('traffic.traffic_light*')
        for s in semafori:
            s.set_red_time(12)

    def setTrafficLights(self):

        semafori =self.world.get_actors().filter('traffic.traffic_light*')

        for s in semafori:
            stato = s.get_state()
            if stato == carla.TrafficLightState.Red:
                tempo = s.get_elapsed_time()
                if tempo > 10:
                    s.set_state(carla.TrafficLightState.Green)

    def addObject(self, actor):
        self.objects.append(actor)

    def destroy(self):
        if self.world is not None:
            settings = self.world.get_settings()
            settings.synchronous_mode = False
            settings.fixed_delta_seconds = None
            self.world.apply_settings(settings)
            self.traffic_manager.set_synchronous_mode(True)

        for obj in self.objects:
            obj.dispose()
