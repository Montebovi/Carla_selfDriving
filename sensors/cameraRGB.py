import sys
import os
import glob
import weakref
import cv2
import numpy as np

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


class CameraRGB(RecordableObject):
    def __init__(self, name, parent_actor, position, recorder=None, showWin=False,
                 imgWidth=640, imgHeight=480, fov=110):
        super().__init__(name, createProperDir=True)
        self._parent = parent_actor
        self.showWin = showWin
        self.imgWidth = imgWidth
        self.imgHeight = imgHeight

        self.last_image = None

        world = self._parent.get_world()

        cam_bp = world.get_blueprint_library().find('sensor.camera.rgb')
        # cam_bp = carla.sensor.Camera('MyCamera', PostProcessing='SemanticSegmentation')
        cam_bp.set_attribute("image_size_x", f"{imgWidth}")
        cam_bp.set_attribute("image_size_y", f"{imgHeight}")
        cam_bp.set_attribute("fov", str(fov))

        if position == 'left':
            loc = carla.Location(x=2.5, y=-2, z=1)
            rot = carla.Rotation(pitch=-15.0, yaw=25)
        elif position == 'right':
            loc = carla.Location(x=2.5, y=2, z=1)
            rot = carla.Rotation(pitch=-15.0, yaw=-25)
        else:
            loc = carla.Location(x=2, y=0, z=2)
            rot = carla.Rotation(pitch=-25.0)

        spawn_point = carla.Transform(loc, rot)
        self.sensor = world.spawn_actor(cam_bp, spawn_point, attach_to=parent_actor)
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda image: CameraRGB.process_image(weak_self, image))

        self.imagetoShow = None
        self.existsImage = False

    @staticmethod
    def process_image(weak_self, image):
        self = weak_self()
        if not self:
            return

        i = np.array(image.raw_data)
        i2 = i.reshape((self.imgHeight, self.imgWidth, 4))
        i3 = i2[:, :, :3]
        #i3 = i3[:, :, ::-1]
        if self.showWin:
            self.imagetoShow = i3
            self.existsImage = True

        scaled_image = i3 / 255.0
        # if (self.recorder):
        #     self.recorder.write(self.NAME, scaled_image, image.timestamp)

        self.last_image = scaled_image

    def drawImage(self):
        if self.existsImage:
            cv2.imshow(self._NAME, self.imagetoShow)
            cv2.waitKey(1)

    def saveDataFrame(self,timestamp):
        fullFileName = os.path.join(self._properDir, str(timestamp).zfill(10) + ".jpg")
        if self.existsImage:
            cv2.imwrite(fullFileName, self.imagetoShow)
        pass

    def dispose(self):
        self.sensor.stop()
        self.sensor.destroy()
        if (self.showWin):
            cv2.destroyWindow(self._NAME)
