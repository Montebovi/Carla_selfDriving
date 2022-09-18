import glob
import os
import sys
import numpy as np
import tensorflow as tf
import keras

from carlacfg import CARLA_LIB_PATH

try:
    sys.path.append(glob.glob(CARLA_LIB_PATH + '/carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass
import carla

import keras.backend as K
import math


MAX_SPEED = 100

class DLModelAgent:
    def __init__(self, vehicleActor, model_path, pilotMode):
        self._vehicleActor = vehicleActor
        self._pilotMode = pilotMode
        self.model = keras.models.load_model(model_path, compile=False)
        print("model loaded")

    def run_step(self, measurements, sensors_data):
        if not (self._pilotMode.IsAgentMode()):
            return None

        current_speed = measurements['velocity']
        obstacle_dist = measurements["obstacle"]
        directions = measurements['dir']
        joinDist = measurements['dirDist']
        if joinDist is None:
            joinDist = 0

        # current_data = [measurements['velocity'], measurements['steer']]
        current_data = [current_speed/MAX_SPEED]
        directionData = directions + [joinDist/(1+joinDist)]
        if math.isnan(obstacle_dist[1]):
            obstacle_dist[1]=0
        obstacle_distdata = [obstacle_dist[0]/(1+obstacle_dist[0]), obstacle_dist[1]/(1+abs(obstacle_dist[1]))]

        input = sensors_data
        control = carla.VehicleControl()
        if (input[0] is None) or (input[1] is None) or (input[2] is None):
            control.throttle = 1
            control.steer = 0
            control.brake = 0
        # [[steer, throttle]] = self.model.predict(np.array([input][0:2]))
        else:
            # a = np.array([input[0]])
            # print("a.shape=", a.shape)
            [[steer, throttle, brake]] = self.model.predict([np.array([input[0]]),
                                                             np.array([input[1]]),
                                                             np.array([input[2]]),
                                                             np.array([input[3]]),
                                                             np.array([current_data]),
                                                             np.array([directionData]),
                                                             np.array([obstacle_distdata])])
            # [steer] = self.model.predict([np.array([input[0]]),     ])

            # print("predicted=", "%r %r %r" % (steer,throttle,brake))
            # IPython.display.display(f"Steer: {steer}\t Throttle: {throttle}\t Brake:{brake}")

            # Xview.img_show2('img-from-sensor', sensor_data.camera['depth'], sensor_data.camera['semantic'], 100)
            control.throttle = throttle.item()
            control.steer = steer.item()
            control.brake = brake.item()
        # control.brake = 0

        if control.brake < 0.1:
             control.brake = 0.0
        if control.throttle > 0.2:
            control.brake = 0.0
        #
        # # if control.brake > control.throttle:
        # #     control.throttle = 0.0
        #
        # # We limit speed to 35 km/h to avoid
        if current_speed > 13.0 and brake < 0.2 and control.throttle > 0.65:
            control.throttle = 0.65

        control.hand_brake = 0
        control.reverse = 0

        self._vehicleActor.apply_control(control)

        return control
