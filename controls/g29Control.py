import math

import pygame
from pygame.locals import K_m
from pygame.locals import K_r
import glob
import os
import sys
from configparser import ConfigParser
from hud import HUD

from carlacfg import CARLA_LIB_PATH

try:
    sys.path.append(glob.glob(CARLA_LIB_PATH + '/carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass
import carla


def processManualControl(button):
    return (button % 11)


class g29Control(object):
    def __init__(self, veh, pilotMode):
        self._pilotMode = pilotMode
        self._control = carla.VehicleControl()
        self._steer_cache = 0.0
        self._parent = veh
        pygame.joystick.init()
        self._last_button = None
        joystick_count = pygame.joystick.get_count()
        if joystick_count > 1:
            raise ValueError("Please Connect Just One Joystick")

        self._joystick = pygame.joystick.Joystick(0)
        self._joystick.init()

        self._parser = ConfigParser()
        self._parser.read('wheel_config.ini')
        self._steer_idx = int(
            self._parser.get('G29 Racing Wheel', 'steering_wheel'))
        self._throttle_idx = int(
            self._parser.get('G29 Racing Wheel', 'throttle'))
        self._brake_idx = int(self._parser.get('G29 Racing Wheel', 'brake'))
        self._reverse_idx = int(self._parser.get('G29 Racing Wheel', 'reverse'))
        self._handbrake_idx = int(
            self._parser.get('G29 Racing Wheel', 'handbrake'))

    def parse_control(self, event, clock):
        world = self._parent.get_world()
        if event.type == pygame.QUIT:
            return True
        elif event.type == pygame.JOYBUTTONDOWN:
            self._last_button = event.button
            # print('lastbutton = ', self._last_button)
            if event.button == 0:
                world.restart()
            elif event.button == 1:
                HUD.toggle_info()
            elif event.button == 2:
                world.camera_manager.toggle_camera()
            elif event.button == 3:
                world.next_weather()
            elif self._control.manual_gear_shift and event.button == 5:
                self._control.gear = max(-1, self._control.gear - 1)
            elif self._control.manual_gear_shift and event.button == 4:
                self._control.gear = self._control.gear + 1
            elif self._control.manual_gear_shift and (11 < event.button < 18):
                self._control.reverse = False
                LASTBUTTON = event.button
                self._control.gear = processManualControl(event.button)
            elif self._control.manual_gear_shift and event.button == 18:
                self._control.gear = -1
            elif event.button == 23:
                world.camera_manager.next_sensor()

        elif event.type == pygame.JOYBUTTONUP:
            if 11 < self._last_button < 19:
                self._control.gear = 0
                print('button up', self._last_button)

        elif event.type == pygame.KEYUP:
            if event.key == K_m:
                self._control.manual_gear_shift = not self._control.manual_gear_shift
                self._control.gear = self._parent.get_control().gear
                print('%s Transmission' %
                      ('Manual' if self._control.manual_gear_shift else 'Automatic'))
                # HUD.notification('%s Transmission' %
                #                  ('Manual' if self._control.manual_gear_shift else 'Automatic'))

        if self._pilotMode.get_mode() != self._pilotMode.MANUAL_WHEEL_PILOT:
            return None
        # self._parse_vehicle_keys(pygame.key.get_pressed(), clock.get_time())
        self._parse_vehicle_wheel()
        self._control.reverse = self._control.gear < 0
        self._parent.apply_control(self._control)

        return self._control

    def _parse_vehicle_wheel(self):
        numAxes = self._joystick.get_numaxes()
        jsInputs = [float(self._joystick.get_axis(i)) for i in range(numAxes)]
        # print (jsInputs)
        # jsButtons = [float(self._joystick.get_button(i)) for i in
        #              range(self._joystick.get_numbuttons())]

        # Custom function to map range of inputs [1, -1] to outputs [0, 1] i.e 1 from inputs means nothing is pressed
        # For the steering, it seems fine as it is
        K1 = 1.0  # 0.55
        steerCmd = K1 * math.tan(1.1 * jsInputs[self._steer_idx])

        K2 = 1.6  # 1.6
        throttleCmd = K2 + (2.05 * math.log10(
            -0.7 * jsInputs[self._throttle_idx] + 1.4) - 1.2) / 0.92
        if throttleCmd <= 0:
            throttleCmd = 0
        elif throttleCmd > 1:
            throttleCmd = 1

        brakeCmd = 1.6 + (2.05 * math.log10(
            -0.7 * jsInputs[self._brake_idx] + 1.4) - 1.2) / 0.92
        if brakeCmd <= 0:
            brakeCmd = 0
        elif brakeCmd > 1:
            brakeCmd = 1

        self._control.steer = steerCmd
        self._control.brake = brakeCmd
        self._control.throttle = throttleCmd
