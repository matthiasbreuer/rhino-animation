import math
import random

import rhinoscript as rs
import scriptcontext as sc

import PiTweener
import Rhino as r


class Camera(object):
    def __init__(self):
        self.tweener = PiTweener.Tweener()

        self.view = sc.doc.Views.ActiveView

        self.camera_lens = self.view.ActiveViewport.Camera35mmLensLength
        self.camera_location = self.view.ActiveViewport.CameraLocation
        self.camera_target = self.view.ActiveViewport.CameraTarget
        self.camera_vector = None

        self.default_duration = 4.0

        self.progress = 0
        self.update_callback = None

    def update_camera(self):
        self.view.ActiveViewport.SetCameraLocations(self.camera_target, self.camera_location)

    def __reset(self):
        self.progress = 0
        self.complete_fired = False
        self.update_callback = None
        self.on_complete = None

    def update_tween(self, td=None):
        self.tweener.update(td)
        if self.tweener.has_tweens():
            self.update_callback()
            self.update_camera()
        else:
            if (self.on_complete and not self.complete_fired):
                self.complete_fired = True
                self.on_complete()

    def look_at(self, obj, distance=None):
        self.calculate_positions(obj, distance)
        self.camera_location = self.new_camera_location
        self.camera_target = self.new_camera_target
        self.update_camera()

    def pan_to(self, obj, distance=None, hop=0, duration=None, tween_type=None, on_complete=None):
        self.calculate_positions(obj, distance)

        self.__reset()

        self.update_callback = self.update_pan_locations
        self.on_complete = on_complete

        self.target_path = r.Geometry.Line(self.camera_target, self.new_camera_target)

        camera_location_center = r.Geometry.Line(self.camera_location, self.new_camera_location).PointAt(0.5)
        camera_location_center.Z += hop
        self.camera_path = r.Geometry.Curve.CreateControlPointCurve(
            [self.camera_location, camera_location_center, self.new_camera_location])

        if tween_type is None:
            tween_type = self.tweener.OUT_CUBIC
        if duration is None:
            duration = self.default_duration

        self.tweener.add_tween(self, progress=1.0, tween_time=duration, tween_type=tween_type)

    def update_pan_locations(self):
        self.camera_target = self.target_path.PointAt(self.progress)
        self.camera_location = self.camera_path.PointAtNormalizedLength(self.progress)

    def circle_position(self, cycles=1, duration=None, tween_type=None, on_complete=None):
        self.__reset()

        self.update_callback = self.update_circle_position
        self.on_complete = on_complete

        self.camera_vector = r.Geometry.Point3d.Subtract(self.camera_location, self.camera_target)

        if tween_type is None:
            tween_type = self.tweener.IN_OUT_CUBIC
        if duration is None:
            duration = self.default_duration

        self.tweener.add_tween(self, progress=1.0 * cycles, tween_time=duration * cycles,
                               tween_type=tween_type)

    def update_circle_position(self):
        vector_duplicate = r.Geometry.Vector3d(self.camera_vector)
        vector_duplicate.Rotate((self.progress % 1.0) * math.pi * -2, r.Geometry.Vector3d.ZAxis)
        self.camera_location = r.Geometry.Point3d.Add(self.camera_target, vector_duplicate)

    def calculate_positions(self, obj, distance=None):
        if type(obj) is r.Geometry.Point3d:
            self.new_camera_target = obj
            if distance is None:
                distance = 30
        else:
            geometry = rs.utility.coercegeometry(obj)
            bbox = geometry.GetBoundingBox(False)
            self.new_camera_target = bbox.Center
            if distance is None:
                distance = bbox.Max.Z - bbox.Min.Z

        vec = r.Geometry.Vector3d(8 * distance, 0, 0)
        vec.Rotate(-math.pi / 6, r.Geometry.Vector3d.YAxis)

        sign = -1 if random.random() > 0.5 else 1
        vec.Rotate(sign * math.pi / 4, r.Geometry.Vector3d.ZAxis)
        self.new_camera_location = r.Geometry.Point3d.Add(self.new_camera_target, vec)

    def set_lens(self, length):
        self.view.ActiveViewport.Camera35mmLensLength = length

    def set_target(self, target):
        self.camera_target = rs.utility.coerce3dpoint(target)
        self.update_camera()

    def set_camera(self, location):
        self.camera_location = rs.utility.coerce3dpoint(location)
        self.update_camera()

    def set_camera(self, target, location):
        self.camera_target = rs.utility.coerce3dpoint(target)
        self.camera_location = rs.utility.coerce3dpoint(location)
        self.update_camera()