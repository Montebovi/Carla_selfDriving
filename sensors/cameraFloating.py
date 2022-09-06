import sys
import os
import glob
import pygame
import numpy as np

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


class RenderObject(object):
    def __init__(self, width, height):
        init_image = np.random.randint(0,255,(height,width,3),dtype='uint8')
        self.surface = pygame.surfarray.make_surface(init_image.swapaxes(0,1))


# Camera sensor callback, reshapes raw data from camera into 2D RGB and applies to PyGame surface
def pygame_callback(data, obj):
    img = np.reshape(np.copy(data.raw_data), (data.height, data.width, 4))
    img = img[:,:,:3]
    img = img[:, :, ::-1]
    obj.surface = pygame.surfarray.make_surface(img.swapaxes(0,1))


class CameraFloating(object):
    def __init__(self, parent_actor):
        self._parent = parent_actor
        camera_init_trans = carla.Transform(carla.Location(x=-5, z=3), carla.Rotation(pitch=-20))
        world = self._parent.get_world()
        camera_bp = world.get_blueprint_library().find('sensor.camera.rgb')
        self.camera = world.spawn_actor(camera_bp, camera_init_trans, attach_to=self._parent)

        # Get camera dimensions
        self.image_w = camera_bp.get_attribute("image_size_x").as_int()
        self.image_h = camera_bp.get_attribute("image_size_y").as_int()

        # Instantiate objects for rendering and vehicle control
        CameraFloating.renderObject = RenderObject(self.image_w, self.image_h)

        # Start camera with PyGame callback
        self.camera.listen(lambda image: pygame_callback(image, CameraFloating.renderObject))

    def dispose(self):
        self.camera.stop()
        self.camera.destroy()
        self.camera = None
        self._parent = None
        print('cameraFloating.dispose')

