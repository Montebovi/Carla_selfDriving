import sys
import os
import glob

import math
import pygame
import random
import time

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


class Navigator:
    def __init__(self, world, vehicleActor, lazyMode = True):
        self._lazyMode = lazyMode  # quando True l'indicazione viene impostata solo se ravvicinata
        self._actor = vehicleActor
        self._world = world
        self._map = world.get_map()
        self._spawn_points = self._map.get_spawn_points()
        self._destPoint = None
        self._coneObj = None
        self._sampling_resolution = 8
        self._dao = GlobalRoutePlannerDAO(self._map, self._sampling_resolution)
        self._grp = GlobalRoutePlanner(self._dao)
        self._grp.setup()
        self._lastDirection = None   # ultima direzione stabilita
        self._lastAngle = 0      # ultimo angolo calcolato tra il veicolo e il target (relativo alla rotazione del veicolo)
        self._lastRoute = None

        self._currentPoint = None
        self._currentYaw = None
        self._nextJoinPoint = None  # prossima giunzione sulla strada del route

    def setRandomPosition(self):
        vhiclePosition = self._actor.get_transform()
        dists = [{"d": self.__distPoints(vhiclePosition, p), "point": p} for p in self._spawn_points]
        dists = sorted(dists, key=lambda d: d['d'], reverse=True)
        n = int(len(dists) / 4)
        n = random.randint(0,n)
        self.setDestination(dists[n]["point"])
        self._putCone()

    def setDestination(self, destPoint):
        self._destPoint = carla.Transform(destPoint.location, destPoint.rotation)
        self._destPoint.location.z = 2.5
        self._destPoint.rotation.yaw = self._destPoint.rotation.yaw + 90

    def _putCone(self):
        self.removeCone()
        bp = self._world.get_blueprint_library().find("static.prop.streetsign")
        self._coneObj = self._world.spawn_actor(bp, self._destPoint)

    def removeCone(self):
        if self._coneObj is not None:
            self._coneObj.destroy()
            self._coneObj = None

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

    def run_step(self):
        t = self._actor.get_transform()

        self._currentPoint = t.location
        self._currentYaw = t.rotation.yaw

        w1 = self._grp.trace_route(self._currentPoint, self._destPoint.location)
        self._lastRoute = w1

        self._lastAngle = self._calcRelativeAngle(self._currentPoint, self._destPoint.location, self._currentYaw)

        # ######################################################################
        # direzione utilizzando la prossima giunzione della strada
        idxGiunzioni = [i for i in range(len(w1)) if w1[i][0].is_junction]
        primaGiunzione = None
        anteGiunzione = None
        postGiunzione = None
        if len(idxGiunzioni) > 0:
            primaGiunzione = w1[idxGiunzioni[0]][0]
            if idxGiunzioni[0] > 1:
                anteGiunzione = w1[idxGiunzioni[0] - 2][0]
            elif idxGiunzioni[0] > 0:
                anteGiunzione = w1[idxGiunzioni[0] - 1][0]

            if (idxGiunzioni[0] < len(w1) - 3):
                postGiunzione = w1[idxGiunzioni[0] + 3][0]
            else:
                postGiunzione = None

        # self._wrongVersus  = False
        # if (len(w1) > 1):
        #     nextPoint = w1[1][0]
        #     aa = self._calcRelativeAngle(self._currentPoint, nextPoint.transform.location, self._currentYaw)
        #     if (abs(aa) > 100):
        #         self._wrongVersus = True
        #         # print("INVERSO: ",aa)
        # else:
        #     nextPoint = None

        if primaGiunzione is None:
            self._nextJoinPoint = None
        else:
            self._nextJoinPoint = primaGiunzione.transform

        d = self._calcoloDirezione(anteGiunzione, primaGiunzione, postGiunzione)


        if (d is None):
            angoloPerDir = self._lastAngle
            angolo_diritto = 20
            if (angoloPerDir < -angolo_diritto):
                d = [0, 0, 1]
            elif (angoloPerDir > angolo_diritto):
                d = [1, 0, 0]
            else:
                d = [0, 1, 0]

        if self._lazyMode:
            distanza = self.__distPoints(carla.Transform(self._currentPoint), self._nextJoinPoint)
            if (distanza is not None) and (distanza < 35):
                self._lastDirection = d
            else:
                self._lastDirection = [0, 1, 0]
        else:
            self._lastDirection = d

        dist = self.getTargetDistanceFromVehicle()
        return dist < 5.0


    def nextDirection(self):
        if (self._lastDirection is None):
            return {"dir": [0, 1, 0], "angle": self._lastAngle, "dist":0}
        d = self.__distPoints(carla.Transform(self._currentPoint),self._nextJoinPoint)
        return {"dir": self._lastDirection, "angle": self._lastAngle, "dist":d}

    def _calcoloDirezione(self, anteGiunzione, primaGiunzione, postGiunzione):
        if primaGiunzione is None:
            return [0, 1, 0]

        if anteGiunzione is None:
            return self._lastDirection

        if postGiunzione is None:
            return self._lastDirection

        v1 = (primaGiunzione.transform.location.x - anteGiunzione.transform.location.x,
              primaGiunzione.transform.location.y - anteGiunzione.transform.location.y)
        v2 = (postGiunzione.transform.location.x - primaGiunzione.transform.location.x,
              postGiunzione.transform.location.y - primaGiunzione.transform.location.y)
        angle = pygame.math.Vector2(v1).angle_to(v2)

        while angle > 180:
            angle -= 360

        while angle < -180:
            angle += 360

        #print("angolo dir: ", angle, f"   v1={v1}   v2={v2}")

        if abs(angle) > 110:
            print("INDIETRO")
        elif (angle > 3 ):
            return [0, 0, 1]
        elif (angle < -3 ):
            return [1, 0, 0]
        else:
            return [0, 1, 0]

    def getTargetDistanceFromVehicle(self):
        if self._currentPoint is None:
            return 0
        dist = math.sqrt(
            (self._destPoint.location.x - self._currentPoint.x) ** 2 + (self._destPoint.location.y - self._currentPoint.y) ** 2)
        return dist

    def __distPoints(self, p1, p2):
        if (p1 is None) or (p2 is None):
            return None
        dist = math.sqrt((p1.location.x - p2.location.x) ** 2 + (p1.location.y - p2.location.y) ** 2)
        return dist
