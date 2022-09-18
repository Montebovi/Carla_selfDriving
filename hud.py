import pygame
import os
import math
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


class HUD():
    def __init__(self, pilotMode, navigator, drivemonitor=None, width=100, height=300):
        self.dim = (width, height)
        font = pygame.font.Font(pygame.font.get_default_font(), 20)
        self._textFont = font
        font_name = 'courier' if os.name == 'nt' else 'mono'
        fonts = [x for x in pygame.font.get_fonts() if font_name in x]
        default_font = 'ubuntumono'
        mono = default_font if default_font in fonts else fonts[0]
        mono = pygame.font.match_font(mono)
        self._font_mono = pygame.font.Font(mono, 12 if os.name == 'nt' else 14)
        self.notifications = FadingText(font, (width, 40), (0, height - 40))
        self._show_info = True
        self._info_text = []
        self._server_clock = pygame.time.Clock()
        self._server_time = pygame.time
        self.pilotMode = pilotMode
        self._navigator = navigator
        self._drivemonitor = drivemonitor

        self._leftImg = self._loadDecal('images/left.png',alfa=128,forceWidth=80)
        self._rightImg = self._loadDecal('images/right.png',alfa=128,forceWidth=80)
        self._forwardImg = self._loadDecal('images/forward.png',alfa=128,forceWidth=80)
        self._distToJoin = "--"
        self._currentDir = None


    def _loadDecal(self,filename, alfa=128, forceWidth = None):
        img = pygame.image.load(filename)
        if forceWidth is not None:
            width, height = img.get_width(), img.get_height()
            newHeight = int((forceWidth * height) / width)
            img = pygame.transform.scale(img, (forceWidth, newHeight))
        img.set_alpha(alfa)
        return img


    def update(self,display,world,clock,vehicleActor):
        self.__tick(world,clock,vehicleActor)
        self.__render(display)

    def __tick(self,world,clock,vehicleActor):
        self.notifications.tick(world, clock)
        if not self._show_info:
            return
        #t = vehicleActor.get_transform()
        v = vehicleActor.get_velocity()
        c = vehicleActor.get_control()
        #vehicles = world.get_actors().filter('vehicle.*')
        self._info_text = [
            'Speed:   % 15.0f km/h' % (3.6 * math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2)),
            '']
        if isinstance(c, carla.VehicleControl):
            dist = self._navigator.getTargetDistanceFromVehicle()
            dist = f"{dist:.1f}"
            nextDirection = self._navigator.nextDirection()
            self._currentDir = nextDirection
            if (nextDirection["dir"][0] == 1):
                direction = "<-"
            elif (nextDirection["dir"][1] == 1):
                direction = "^"
            elif (nextDirection["dir"][2] == 1):
                direction = "->"
            else:
                direction = "-"
            angle = nextDirection["angle"]
            angle =  f"{angle:.1f}"
            distToJoin = nextDirection["dist"]
            if distToJoin is None:
                distToJoin = "--"
            else:
                distToJoin = f"{distToJoin:.1f}"

            self._distToJoin = distToJoin

            self._info_text += [
                ('Time: ' + str(self._server_time.get_ticks()/1000.0)),
                #('Auto pilot: ' + str(self.pilotMode.IsAutoPilot())),
                ('Pilot mode: ' + str(self.pilotMode.GetModeAsString())),
                ('Recording: ' + str(self.pilotMode.IsRecording())),
                ('Throttle:', c.throttle, 0.0, 1.0),
                ('Steer:', c.steer, -1.0, 1.0),
                ('Brake:', c.brake, 0.0, 1.0),
                ('Reverse:', c.reverse),
                ('Hand brake:', c.hand_brake),
                ('Manual gear:', c.manual_gear_shift),
                'Gear:        %s' % {-1: 'R', 0: 'N'}.get(c.gear, c.gear),
                f"Navigation: [{direction}] - [{distToJoin} m.]",
                f"Target dist.: {dist} m.",
                f"Target angle: {angle}° ",

            ]
            if self._drivemonitor is not None:
                data_driver_monitor = self._drivemonitor.get_info()
                totalJoinPoints = data_driver_monitor["totalJoinPoints"]
                self._info_text += ["------------------------------",
                                    f"Dist. traveled: {(data_driver_monitor['meters_traveled']/1000):.2f} km",
                                    f"max speed: {data_driver_monitor['max_speed']:.2f} m/s",
                                    f"targets: {data_driver_monitor['reached_targets']}",
                                    f"collisions: {data_driver_monitor['total_collisions']}",
                                    f"obstacles: {data_driver_monitor['total_obstacles']}",
                                    f"lane invasions: {data_driver_monitor['total_lane_invasions']}",
                                    f"wrong dir. count: {data_driver_monitor['wrong_direction_count']} out of {totalJoinPoints}",
                                    f"repos count: {data_driver_monitor['repos_count']}"
                                    ]

    def __render(self, display):
        if self._show_info:
            wWin, hWin = display.get_size()

            if self._currentDir is None:
                pass
            elif self._currentDir["dir"][0] == 1:
                display.blit(self._leftImg, ((wWin - 80) / 2, hWin - self._leftImg.get_height() - 10))
            elif self._currentDir["dir"][1] == 1:
                display.blit(self._forwardImg, ((wWin - 80) / 2, hWin - self._forwardImg.get_height() - 10))
            elif self._currentDir["dir"][2] == 1:
                display.blit(self._rightImg, ((wWin - 80) / 2, hWin - self._rightImg.get_height() - 10))


            disttext = self._textFont.render(self._distToJoin+" mt.",True,(0,0,0))
            xx = (wWin - 80) / 2 + 100
            yy = hWin -50
            disttext.set_alpha(128)
            display.blit(disttext,(xx,yy))


            info_surface = pygame.Surface((220, self.dim[1]))
            info_surface.set_alpha(100)
            display.blit(info_surface, (0, 0))
            v_offset = 4
            bar_h_offset = 100
            bar_width = 106
            for item in self._info_text:
                if v_offset + 18 > self.dim[1]:
                    break
                if isinstance(item, list):
                    if len(item) > 1:
                        points = [(x + 8, v_offset + 8 + (1.0 - y) * 30) for x, y in enumerate(item)]
                        pygame.draw.lines(display, (255, 136, 0), False, points, 2)
                    item = None
                    v_offset += 18
                elif isinstance(item, tuple):
                    if isinstance(item[1], bool):
                        rect = pygame.Rect((bar_h_offset, v_offset + 8), (6, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect, 0 if item[1] else 1)
                    else:
                        rect_border = pygame.Rect((bar_h_offset, v_offset + 8), (bar_width, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect_border, 1)
                        f = (item[1] - item[2]) / (item[3] - item[2])
                        if item[2] < 0.0:
                            rect = pygame.Rect((bar_h_offset + f * (bar_width - 6), v_offset + 8), (6, 6))
                        else:
                            rect = pygame.Rect((bar_h_offset, v_offset + 8), (f * bar_width, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect)
                    item = item[0]
                if item:  # At this point has to be a str.
                    surface = self._font_mono.render(item, True, (255, 255, 255))
                    display.blit(surface, (8, v_offset))
                v_offset += 18
        self.notifications.render(display)



class FadingText(object):
    def __init__(self, font, dim, pos):
        self.font = font
        self.dim = dim
        self.pos = pos
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)

    def set_text(self, text, color=(255, 255, 255), seconds=2.0):
        text_texture = self.font.render(text, True, color)
        self.surface = pygame.Surface(self.dim)
        self.seconds_left = seconds
        self.surface.fill((0, 0, 0, 0))
        self.surface.blit(text_texture, (10, 11))

    def tick(self, _, clock):
        delta_seconds = 1e-3 * clock.get_time()
        self.seconds_left = max(0.0, self.seconds_left - delta_seconds)
        self.surface.set_alpha(500.0 * self.seconds_left)

    def render(self, display):
        display.blit(self.surface, self.pos)






