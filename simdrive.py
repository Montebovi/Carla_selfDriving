# ######################################################################################################################
# Carla API documentation
# https://carla.readthedocs.io/en/0.9.10/python_api/

import carlacfg
import argparse

# parameters of drive simulation environment
parser = argparse.ArgumentParser(description='Drive Simulation Environment (powered by CARLA)')
parser.add_argument('--carla_lib_path', help='Carla library path (example C:/CARLA_0.9.10.1/WindowsNoEditor/PythonAPI)',
                    required=True)
parser.add_argument('--data_path', help='folder where data is collected', required=True)
parser.add_argument('--fps', help='fps for simulation', type=int, default=20)
parser.add_argument('--num_of_vehicles', help='number of traffic vehicles (use zero if no traffic) ', type=int, default=0)
parser.add_argument('--model_path', help='neural network model (file h5)')
parser.add_argument('--no_gpu', help='exclude GPU use', action='store_const', const=True)
parser.add_argument('--start_in_autopilot', help='when start the vehicle is in autopilot mode', action='store_const',
                    const=True)
parser.add_argument('--start_recording', help='when start active recording automatically', action='store_const',
                    const=True)
parser.add_argument('--enable_driver_monitor', help='activate drive quality metric', action='store_const',
                    const=True)
parser.add_argument('--add_lateral_cameras', help='adds semantic cameras to the sides of the vehicle',
                    action='store_const', const=True)
parser.add_argument('--add_rgb_camera', help='adds central RGB camera to the vehicle',
                    action='store_const', const=True)
parser.add_argument('--add_driver_videocam', help='adds video camera in front of the driver (webcam)',
                    action='store_const', const=True)
parser.add_argument('--carla_svr_path', help='if defined then carla server is started automatically')

args = parser.parse_args()
carlacfg.CARLA_LIB_PATH = args.carla_lib_path

print(f"Simluation FPS: {args.fps}")
print(f"Folder where data is collected [data_path]: {args.data_path}")
if args.model_path is not None:
    print(f"Neural network model (file h5) [model_path]: {args.model_path}")

# ######################################################################################################################
# EXTRARNAL LIBS
import glob
import psutil
import subprocess
import sys
import pygame
import datetime
# endregion

# ######################################################################################################################
# region INTERNAL LIBS
import utils.townChooser as tc
import utils.folderUtils as folderUtils
from actors.vehicle import Vehicle
from controls.dlAgent import DLModelAgent
from controls.dlAgent2 import DLModelAgent2
from controls.forwardAgent import ForwardAgent
from controls.g29Control import g29Control
from controls.joystickControl import JoystickControl
from controls.kbdControl import KbdControl
from pilotMode import PilotMode
from recorderData import RecorderData
from sensors.videoCam import VideoCam
from sensors.cameraFloating import CameraFloating
from sensors.cameraRGB import CameraRGB
from sensors.cameraSemantic import CameraSemantic
from sensors.navigationMonitor import NavigationMonitor
from sensors.navigator import Navigator
from sensors.obstacleSensor import ObstacleSensor
from sensors.vehicleData import VehicleData
from sensors.vehicleState import VehicleState
from simWorld import SimWorld
from hud import HUD
from driveMonitor import DriveMonitor

# endregion


# ####################################################################
# Constants initialization
FPS = args.fps  # fps del sistema
START_WITH_RECORDING = args.start_recording
ADD_SEMANTIC_CAMERAS_ON_SIDES = args.add_lateral_cameras
ADD_RGB_CAMERA_CENTRAL = args.add_rgb_camera
ADD_VIDEO_CAMERA = args.add_driver_videocam
ENABLE_AGENT = args.model_path is not None
ENABLE_DRIVER_MONITOR = args.enable_driver_monitor

# exclusion GPU usage ############################################
import os

if args.no_gpu:
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# ######################################################################################################################
# IMPORT CARLA
import carlacfg
from trafficGenerator import TrafficGenerator

try:
    sys.path.append(glob.glob(carlacfg.CARLA_LIB_PATH + '/carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass
import carla

# ######################################################################################################################
# start Carla server if not running
if args.carla_svr_path is not None:
    if not ("CARLAUE4.EXE" in (p.name().upper() for p in psutil.process_iter())):
        print('Start CARLA server execution')
        os.startfile(args.carla_svr_path)

# ######################################################################################################################
# MAP SELECTION
townChooser = tc.TownChooser()
choosenMap = townChooser.selectTown()
if (choosenMap is None):
    print('Map is not valid')
    exit(-1)

print(f'The chosen map is: {choosenMap}')

# directory preparation for saving recorded data
folderForRecord = folderUtils.createFolderForMap(choosenMap, args.data_path)

try:
    # initialize pygame
    pygame.init()
    pygame.font.init()

    # detect Gamepad or Wheel ##############################################
    ENABLE_WHEEL = False
    ENABLE_GAMEPAD = False
    if (pygame.joystick.get_count() > 0):
        joystick = pygame.joystick.Joystick(0)
        name = joystick.get_name()
        if "g29" in name.lower():
            # 'Logitech G HUB G29 Driving Force Racing Wheel USB'
            print("wheel detected: ", name)
            ENABLE_WHEEL = True
        elif "xbox 360 controller" in name.lower():
            # 'Xbox 360 Controller'
            print("gamepad detected: ", name)
            ENABLE_GAMEPAD = True
        joystick.quit()


    recorder = RecorderData(folderForRecord, numFrameToSkip=FPS, enabled=START_WITH_RECORDING)

    client = carla.Client("localhost", 2000)
    client.set_timeout(50.0)

    sim_world = SimWorld(client.load_world(choosenMap), client.get_trafficmanager(), FPS)

    # vehicle creation
    theVehicle = Vehicle(sim_world.world, sim_world.traffic_manager, sim_world.blueprint_library, numPoint=0)

    # set pilot mode
    pilotMode = PilotMode(theVehicle.actor, gamePadEnabled=ENABLE_GAMEPAD, wheelEnabled=ENABLE_WHEEL,
                          agentEnabled=ENABLE_AGENT, isRecording=START_WITH_RECORDING)
    if args.start_in_autopilot:
        pilotMode.set_mode(pilotMode.AUTO_PILOT)
    else:
        pilotMode.set_mode(pilotMode.MANUAL_KBD_PILOT)

    # put vehicle into world
    sim_world.addObject(theVehicle)

    # instance traffic if required
    if args.num_of_vehicles > 0:
        trafficGenerator = TrafficGenerator(sim_world.world, sim_world.traffic_manager)
        trafficGenerator.generateVehicles(args.num_of_vehicles, theVehicle.initialSpawnPoint)
    else:
        trafficGenerator = None

    # create navigator
    navigator = Navigator(sim_world.world, theVehicle.actor)
    navigator.setRandomPosition()

    # creating floating camera useful for driving
    cameraFloating = CameraFloating(theVehicle.actor)
    sim_world.addObject(cameraFloating)

    # region MOUNT CONTROLS ################################################
    kbdControl = KbdControl(theVehicle.actor, pilotMode, maxVelocity=70.0, maxThrottle=1.0)
    if ENABLE_GAMEPAD:
        gamepadControl = JoystickControl(theVehicle.actor, pilotMode)
    else:
        gamepadControl = None

    if ENABLE_WHEEL:
        wheelControl = g29Control(theVehicle.actor, pilotMode)
    else:
        wheelControl = None

    if ENABLE_AGENT:
        # driverAgent = ForwardAgent(theVehicle.actor, pilotMode)
        driverAgent = DLModelAgent(theVehicle.actor,
                                   args.model_path,
                                   pilotMode)
    else:
        driverAgent = None
    # endregion

    # region MOUNT SENSORS ##############################################################################################
    navigatorMonitor = NavigationMonitor(navigator)
    recorder.subscribeRecordableObject(navigatorMonitor)

    cameraSemanticCentral = CameraSemantic("cameraCentral", theVehicle.actor, position='center',
                                           imgWidth=192, imgHeight=144, showWin=True)
    sim_world.addObject(cameraSemanticCentral)
    recorder.subscribeRecordableObject(cameraSemanticCentral)

    if ADD_SEMANTIC_CAMERAS_ON_SIDES:
        cameraSemanticLeft = CameraSemantic("cameraLeft", theVehicle.actor, position='left',
                                            imgWidth=192, imgHeight=144, showWin=True)
        sim_world.addObject(cameraSemanticLeft)
        recorder.subscribeRecordableObject(cameraSemanticLeft)

        cameraSemanticRight = CameraSemantic("cameraRight", theVehicle.actor, position='right',
                                             imgWidth=192, imgHeight=144, showWin=True)
        sim_world.addObject(cameraSemanticRight)
        recorder.subscribeRecordableObject(cameraSemanticRight)

    if ADD_RGB_CAMERA_CENTRAL:
        cameraRgbCentral = CameraRGB("cameraRgbCentral", theVehicle.actor, position='center',
                                     imgWidth=192, imgHeight=144, showWin=True)
        sim_world.addObject(cameraRgbCentral)
        recorder.subscribeRecordableObject(cameraRgbCentral)

    if ADD_VIDEO_CAMERA:
        cameraVideo = VideoCam("driverVideoCam", width=320, height=240)
        recorder.subscribeRecordableObject(cameraVideo)

    vehicleData = VehicleData(theVehicle)
    recorder.subscribeRecordableObject(vehicleData)

    vehicleState = VehicleState(theVehicle)
    recorder.subscribeRecordableObject(vehicleState)

    obstacleSensor = ObstacleSensor("obstacleSensor", theVehicle.actor)
    recorder.subscribeRecordableObject(obstacleSensor)
    # endregion

    if ENABLE_DRIVER_MONITOR:
        driveMonitor = DriveMonitor("driveMonitor", theVehicle, folderForRecord)
        driveMonitor.open()
    else:
        driveMonitor = None

    # ################################################
    # create object to display HUD in main window
    hudHeight = 300
    if ENABLE_DRIVER_MONITOR:
        hudHeight = 440
    hud = HUD(pilotMode, navigator,driveMonitor,height=hudHeight)

    # Initialise the display
    gameDisplay = pygame.display.set_mode((cameraFloating.image_w, cameraFloating.image_h),
                                          pygame.HWSURFACE | pygame.DOUBLEBUF)
    # Draw black to the display
    gameDisplay.fill((0, 0, 0))
    gameDisplay.blit(CameraFloating.renderObject.surface, (0, 0))

    pygame.display.flip()

    clock = pygame.time.Clock()
    start_time = datetime.datetime.now()

    measurements = dict()
    lastVehicleControlCmds = None
    ended = False

    while not ended:
        clock.tick(FPS)
        sim_world.world.tick()

        sim_world.setTrafficLights()

        gameDisplay.blit(CameraFloating.renderObject.surface, (0, 0))

        hud.update(gameDisplay, sim_world.world, clock, theVehicle.actor)

        pygame.display.flip()

        theVehicle.forceTrafficLightToGreen()

        targetReached = navigator.run_step()
        if targetReached:
            if driveMonitor is not  None:
                driveMonitor.signalTargetReached()
            hud.notifications.set_text("arrivato")
            navigator.setRandomPosition()
        elif driveMonitor is not  None:
            driveMonitor.notifyRoute(navigator._lastRoute)

        cameraSemanticCentral.drawImage()
        if ADD_SEMANTIC_CAMERAS_ON_SIDES:
            cameraSemanticLeft.drawImage()
            cameraSemanticRight.drawImage()

        if ADD_RGB_CAMERA_CENTRAL:
            cameraRgbCentral.drawImage()

        timestamp = sim_world.world.get_snapshot().timestamp
        elapsed_millisec = (int)(round(timestamp.elapsed_seconds * 1000, 0))

        for event in pygame.event.get():
            kbdControl.parse_control(event)

            # If the window is closed, break the while loop
            if event.type == pygame.QUIT or kbdControl.escPressed:
                print('pygame.QUIT')
                ended = True

        lastVehicleControlCmd = None

        measurements["velocity"] = vehicleState.getSpeed_ms()
        measurements["obstacle"] = obstacleSensor.getDistance()

        dataNav = navigator.nextDirection()
        measurements['dir'] = dataNav['dir']
        measurements['dirDist'] = dataNav['dist']

        centralCam = cameraSemanticCentral.last_image
        if ADD_SEMANTIC_CAMERAS_ON_SIDES:
            leftCam = cameraSemanticLeft.last_image
            rightCam = cameraSemanticRight.last_image
        else:
            leftCam = None
            rightCam = None

        if ADD_RGB_CAMERA_CENTRAL:
            cameraRgbCentralScaledImage = cameraRgbCentral.last_image
        else:
            cameraRgbCentralScaledImage = None

        cmd = kbdControl.process_control()
        if cmd is not None:
            lastVehicleControlCmd = cmd

        if gamepadControl is not None:
            cmd = gamepadControl.parse_control(event, clock)
            if cmd is not None:
                lastVehicleControlCmd = cmd

        if wheelControl is not None:
            cmd = wheelControl.parse_control(event, clock)
            if cmd is not None:
                lastVehicleControlCmd = cmd

        if driverAgent is not None:
            cmd = driverAgent.run_step(measurements, [centralCam, leftCam, rightCam, cameraRgbCentralScaledImage])
            if cmd is not None:
                lastVehicleControlCmd = cmd

        vehicleData.SetLastCmds(lastVehicleControlCmd)

        recorder.EnableRecording(pilotMode.IsRecording())
        recorder.recordFrame(elapsed_millisec)

        if driveMonitor is not None:
            driveMonitor.run_step(elapsed_millisec)

finally:
    if driveMonitor is not None:
        driveMonitor.close()
        driveMonitor.dispose()
    recorder.dispose()

    sim_world.destroy()

    if trafficGenerator is not None:
        trafficGenerator.dispose()

    pygame.quit()
    print('pygame.quit()')

    # for proc in psutil.process_iter():
    #     # check whether the process name matches
    #     if proc.name().upper() == "CARLAUE4.EXE":
    #         proc.kill()

    subprocess.call("TASKKILL /F /IM CarlaUE4-Win64-Shipping.exe", shell=True)
    print('*** END ***')
