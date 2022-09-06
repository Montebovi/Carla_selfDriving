# #######################################
# https://carla.readthedocs.io/en/0.9.10/python_api/
#
# https://github.com/carla-simulator/carla/issues/3890
# https://github.com/carla-simulator/carla/issues/5424
# https://carla.org/2018/11/16/release-0.9.1/

# #######################################
# EXTRARNAL LIBS
import glob
import psutil
import subprocess
import os
import sys
import random
import time
import pygame
import numpy as np
import traceback
import datetime
# from folderUtils import *
import cv2

# #######################################
# INTERNAL LIBS
import utils.townChooser as tc
import utils.folderUtils as folderUtils
from actors.vehicle import Vehicle
from controls.dlAgent import DLModelAgent
from controls.forwardAgent import ForwardAgent
from controls.joystickControl import JoystickControl
from controls.kbdControl import KbdControl
from pilotMode import PilotMode
from recorderData import RecorderData
from sensors.cameraFloating import CameraFloating
from sensors.cameraSemantic import CameraSemantic
from sensors.vehicleData import VehicleData
from sensors.vehicleState import VehicleState
from simWorld import SimWorld
from hud import HUD


# ######################################################################################################################
# IMPORT CARLA
from carlacfg import CARLA_LIB_PATH

try:
    sys.path.append(glob.glob(CARLA_LIB_PATH + '/carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass
import carla

from agents.navigation.global_route_planner import GlobalRoutePlanner
from agents.navigation.global_route_planner_dao import GlobalRoutePlannerDAO

# ####################################################################
# Alcune costanti di configurazione
FPS = 20  # fps del sistema


# start Carla server if not runningr
if not ("CARLAUE4.EXE" in (p.name().upper() for p in psutil.process_iter())):
    os.startfile("H:/CARLA_0.9.10.1/WindowsNoEditor/CarlaUE4.exe")

# ####################################################################
# Selezione mappa
townChooser = tc.TownChooser()
choosenMap = townChooser.selectTown()
if (choosenMap is None):
    print('Mappa non valida')
    exit(-1)

print(f'La mappa scelta è: {choosenMap}')


try:
    client = carla.Client("localhost", 2000)
    client.set_timeout(20.0)

    sim_world = SimWorld(client.load_world(choosenMap), client.get_trafficmanager(), FPS)

    # ################################################
    # Initialise the display
    pygame.init()
    pygame.font.init()

    clock = pygame.time.Clock()
    start_time = datetime.datetime.now()

    # #################################################################
    world = sim_world.world
    amap = world.get_map()
    sampling_resolution = 2
    dao = GlobalRoutePlannerDAO(amap, sampling_resolution)
    grp = GlobalRoutePlanner(dao)
    grp.setup()

    spawn_points = world.get_map().get_spawn_points()
    a = carla.Location(spawn_points[50].location)
    b = carla.Location(spawn_points[100].location)
    w1 = grp.trace_route(a, b)  # there are other funcations can be used to generate a route in GlobalRoutePlanner.
    i = 0
    for w in w1:
        if i % 10 == 0:
            world.debug.draw_string(w[0].transform.location, 'O', draw_shadow=False,
                                    color=carla.Color(r=255, g=0, b=0), life_time=120.0,
                                    persistent_lines=True)
        else:
            world.debug.draw_string(w[0].transform.location, 'O', draw_shadow=False,
                                    color=carla.Color(r=0, g=0, b=255), life_time=1000.0,
                                    persistent_lines=True)
        i += 1

    # #################################################################


    ended = False
    while not ended:
        clock.tick(FPS)
        sim_world.world.tick()

finally:
    sim_world.destroy()

    pygame.quit()
    print('pygame.quit()')


    subprocess.call("TASKKILL /F /IM CarlaUE4-Win64-Shipping.exe", shell=True)
    print('*** END ***')


