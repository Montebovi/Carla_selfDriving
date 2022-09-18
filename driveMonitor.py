import sys
import os
import glob
import weakref
import time
import math
import pygame
import numpy as np
import random

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


class DriveMonitor:
    def __init__(self, name, vehicle, pathForData):
        self._name = name
        self._vehicle = vehicle
        self._pathForData = pathForData
        self._reposIdleTimeout = 15

        # collection data ###############
        self._maxSpeed = 0
        self._meanSpeed = 0
        self._duration = 0
        self._meters_traveled = 0
        self._reachedTargets = 0
        self._repositioningCounter = 0
        self._wrongDirectionCounter = 0
        self._totalJoinPoints = 0
        self._collisionHistory = []
        self._obstacleHistory = []
        self._laneInvasionHistory = []
        # ###############################

        self._precRoute = None
        self._lastNotIdleTime = 0
        self._lastCollisionActorName = None
        self._lastCollisionActorId = None
        self._lastCollisionIntensity = None
        self._lastCollisionLoc = None
        self._last_obstacle_dist = None
        self._last_obstacle_actor = None
        self._lastLocation = None
        self._lastInvasion = None
        self._filterWrongDirTime = 0
        self._lastJoinPoint = None

        weak_self = weakref.ref(self)

        world = self._vehicle.actor.get_world()

        bp = world.get_blueprint_library().find('sensor.other.collision')
        self.collisionSensor = world.spawn_actor(bp, carla.Transform(), attach_to=self._vehicle.actor)
        self.collisionSensor.listen(lambda event: DriveMonitor._on_collision(weak_self, event))

        bp2 = world.get_blueprint_library().find('sensor.other.obstacle')
        bp2.set_attribute('distance', '10')
        bp2.set_attribute('hit_radius', '1')
        obstacle_sensor_transform = carla.Transform(carla.Location(x=1.6, z=1.3), carla.Rotation(yaw=0))
        self._obstacleSensor = world.spawn_actor(bp2, obstacle_sensor_transform, attach_to=self._vehicle.actor)
        self._obstacleSensor.listen(lambda event: DriveMonitor._on_obstacle(weak_self, event))

        bp3 = world.get_blueprint_library().find('sensor.other.lane_invasion')
        self._lane_invasion_sensor = world.spawn_actor(bp3, carla.Transform(), attach_to=self._vehicle.actor)
        self._lane_invasion_sensor.listen(lambda event: DriveMonitor._on_invasion(weak_self, event))

    def open(self):
        self._starttime = time.time()
        self._lastNotIdleTime = self._starttime
        self._lastLocation = None
        filename = os.path.join(self._pathForData, self._name + ".npy")
        self._its_file = open(filename, "ba+")

    def dispose(self):
        self.collisionSensor.stop()
        self.collisionSensor.destroy()
        self._obstacleSensor.stop()
        self._obstacleSensor.destroy()
        self._lane_invasion_sensor.stop()
        self._lane_invasion_sensor.destroy()

    def close(self):
        data = dict()
        data["duration"] = self._duration
        data["max_speed"] = self._maxSpeed
        data["mean_speed"] = self._meanSpeed
        data["meters_traveled"] = self._meters_traveled
        data["collisions"] = [(el[0], el[1], el[2], el[4]) for el in self._collisionHistory]
        data["obstacles"] = self._obstacleHistory
        data["lane_invasions"] = self._laneInvasionHistory
        data["reached_targets"] = self._reachedTargets
        data["wrong_direction_count"] = self._wrongDirectionCounter
        data["totalJoinPoints"] = self._totalJoinPoints
        data["repos_count"] = self._repositioningCounter
        np.save(self._its_file, data)
        self._its_file.close()

    def get_info(self):
        data = dict()
        data["max_speed"] = self._maxSpeed
        data["meters_traveled"] = self._meters_traveled
        data["total_collisions"] = len(self._collisionHistory)
        data["total_obstacles"] = len(self._obstacleHistory)
        data["total_lane_invasions"] = len(self._laneInvasionHistory)
        data["reached_targets"] = self._reachedTargets
        data["wrong_direction_count"] = self._wrongDirectionCounter
        data["totalJoinPoints"] = self._totalJoinPoints
        data["repos_count"] = self._repositioningCounter
        return data

    @staticmethod
    def _on_invasion(weak_self, event):
        """On invasion method"""
        self = weak_self()
        if not self:
            return
        lane_types = set(x.type for x in event.crossed_lane_markings)
        self._lastInvasion = [(str(type(a)), a.name) for a in lane_types]
        # print(self._lastInvasion)
        self._filterWrongDirTime = time.time() + 1
        # text = ['%r' % str(x).split()[-1] for x in lane_types]
        # print('Crossed line %s' % ' and '.join(text))
        # print(lane_types)

    @staticmethod
    def _on_obstacle(weak_self, event):
        self = weak_self()
        if not self:
            return
        self._last_obstacle_dist = event.distance
        self._last_obstacle_actor = event.other_actor

    @staticmethod
    def _on_collision(weak_self, event):
        self = weak_self()
        if not self:
            return
        impulse = event.normal_impulse
        self._lastCollisionActorName = DriveMonitor.get_actor_display_name(event.other_actor)
        self._lastCollisionActorId = event.other_actor.type_id
        self._lastCollisionIntensity = math.sqrt(impulse.x ** 2 + impulse.y ** 2 + impulse.z ** 2)
        self._lastCollisionLoc = self._vehicle.actor.get_location()

    @staticmethod
    def get_actor_display_name(actor, truncate=250):
        """Method to get actor display name"""
        name = ' '.join(actor.type_id.replace('_', '.').title().split('.')[1:])
        return (name[:truncate - 1] + u'\u2026') if len(name) > truncate else name

    def run_step(self, timestamp):
        vehicleSpeed = self._vehicle.getVelocity()
        if vehicleSpeed > self._maxSpeed:
            self._maxSpeed = vehicleSpeed

        actualTime = time.time()
        self._duration = actualTime - self._starttime

        vehicleLoc = self._vehicle.actor.get_location()
        if self._lastLocation is not None:
            dist = self.__distPoints(self._lastLocation, vehicleLoc)
            self._meters_traveled = self._meters_traveled + dist
        self._lastLocation = vehicleLoc

        if (self._duration > 0):
            self._meanSpeed = self._meters_traveled / self._duration
        else:
            self._meanSpeed = 0

        if self._lastCollisionLoc is None:
            if len(self._collisionHistory) > 0:
                lastCollision = self._collisionHistory[-1]
                if not lastCollision[5]:
                    d = self.__distPoints(lastCollision[3], vehicleLoc)
                    collisionClosed = d > 2
                    if collisionClosed:
                        # print("exited from the point of collision")
                        self._collisionHistory[-1] = (lastCollision[0], lastCollision[1],
                                                      lastCollision[2], lastCollision[3], lastCollision[4], True)
        else:
            toAppendCollision = False
            if len(self._collisionHistory) == 0:
                toAppendCollision = True
            else:
                lastCollision = self._collisionHistory[-1]
                if lastCollision[1] != self._lastCollisionActorName:  # collisione con altro oggetto
                    toAppendCollision = True
                elif lastCollision[5]:  # la collisione è chiusa
                    toAppendCollision = True
            if toAppendCollision:
                self._collisionHistory.append(
                    (timestamp, self._lastCollisionActorName, self._lastCollisionIntensity, self._lastCollisionLoc,
                     self._lastCollisionActorId, False))
                # print(
                #     f"duration: {self._duration} - max speed: {self._maxSpeed} - mean speed: {self._meanSpeed} - mt: {self._meters_traveled}")
                # print(f"Collision with: {self._lastCollisionActorName}")

        self._lastCollisionIntensity = None
        self._lastCollisionActorName = None
        self._lastCollisionActorId = None
        self._lastCollisionLoc = None

        if self._last_obstacle_dist is not None:
            toAppend = False
            if len(self._obstacleHistory) == 0:
                toAppend = True
            else:
                lastObstacle = self._obstacleHistory[-1]
                if lastObstacle[3] != self._last_obstacle_actor.id:
                    toAppend = True
                if lastObstacle[2] != self._last_obstacle_actor.type_id:
                    toAppend = True

            if toAppend:
                self._obstacleHistory.append((timestamp, self._last_obstacle_dist,
                                              self._last_obstacle_actor.type_id, self._last_obstacle_actor.id))
                # print(f"Obstacle: {self._last_obstacle_actor.type_id} - at {self._last_obstacle_dist} mt")

        self._last_obstacle_dist = None
        self._last_obstacle_actor_typeid = None

        if (self._lastInvasion is not None):
            self._laneInvasionHistory.append((timestamp, actualTime, self._lastInvasion))
            self._lastInvasion = None

        # self.history.append((event.frame, intensity))
        # if len(self.history) > 4000:
        #     self.history.pop(0)

        if vehicleSpeed > 0.5:
            self._lastNotIdleTime = time.time()
        else:
            idleTime = time.time() - self._lastNotIdleTime
            if (idleTime > self._reposIdleTimeout):
                self._vehicleRepos()
                self._lastNotIdleTime = time.time()

    def __distPoints(self, p1, p2):
        if (p1 is None) or (p2 is None):
            return None
        dist = math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)
        return dist

    def _vehicleRepos(self):
        print("vehicle repositioning")
        self._repositioningCounter = self._repositioningCounter + 1
        world = self._vehicle.actor.get_world()
        pts = world.get_map().get_spawn_points()
        spawn_point = random.choice(world.get_map().get_spawn_points())
        self._vehicle.actor.set_transform(spawn_point)
        self._filterWrongDirTime = time.time() + 1

    def signalTargetReached(self):
        self._reachedTargets = self._reachedTargets + 1
        self._precRoute = None
        self._filterWrongDirTime = time.time() + 4

    def notifyRoute(self, lastRoute):
        actual = [w[0] for w in lastRoute]

        # firstJoin = next((x for x in actual if x.is_junction), None)
        if len(actual) > 0:
            if actual[0].is_junction:
                i = 0
                # while actual[i].is_junction and i < len(actual):
                #     i = i+1
                if actual[i] != self._lastJoinPoint:
                    d = 1000
                    if self._lastJoinPoint is not None:
                        d = self.__distPoints(self._lastJoinPoint.transform.location, actual[i].transform.location)
                    if d > 15:
                        self._totalJoinPoints = self._totalJoinPoints + 1
                        # print("join points: " + str(self._totalJoinPoints))
                    self._lastJoinPoint = actual[i]

        t = self._vehicle.actor.get_transform()
        currentPoint = t.location
        currentYaw = t.rotation.yaw
        # wrongVersus = False
        if (len(actual) > 1):
            nextPoint = actual[1]
            angleversus = self._calcRelativeAngle(currentPoint, nextPoint.transform.location, currentYaw)
            if (abs(angleversus) > 100):
                # self._filterWrongDirTime = time.time() + 1
                # wrongVersus = True
                return

        toIncrement = False
        actual.reverse()
        if self._precRoute is not None:
            delta = abs(len(actual) - len(self._precRoute))
            if (delta > 4):
                toIncrement = True
            else:
                min_len = min(len(self._precRoute), len(actual))
                for i in range(0, min_len):
                    if (self._precRoute[i].transform.location != actual[i].transform.location):
                        delta = delta + 1
                        if (delta > 4):
                            toIncrement = True
                            break

        if toIncrement:
            if (self._filterWrongDirTime is None) or (self._filterWrongDirTime < time.time()):
                self._wrongDirectionCounter = self._wrongDirectionCounter + 1
                print(str(self._wrongDirectionCounter) + ") direzione sbagliata")
            self._filterWrongDirTime = time.time() + 2

        self._precRoute = actual

    # calcola angolo tra il vettore s(ource) e d(estination)
    def _calcRelativeAngle(self, s, d, yaw):
        dx = s.x - d.x
        dy = s.y - d.y
        if (dx == 0) and (dy == 0):
            return None

        angle = pygame.math.Vector2((1, 0)).angle_to((-dx, -dy))
        angle -= yaw
        angle = -angle

        while (angle <= -180):
            angle = angle + 360
        while angle > 180:
            angle = angle - 360
        return angle
