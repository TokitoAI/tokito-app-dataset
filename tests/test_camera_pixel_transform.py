from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from camera_pixel_transform import map_intrinsics


class CameraCoordinates(unittest.TestCase):
    def test_centered_16_by_9_crop_preserves_principal_point(self):
        result=map_intrinsics([2780,2780,2048,1536,0],[4096,3072],[0,384,4096,2688],[1280,720],0)
        self.assertEqual(result['projection_in_original_camera_axes'],[[868.75,0,640],[0,868.75,360],[0,0,1]])

    def test_portrait_rotation_preserves_original_camera_axes(self):
        result=map_intrinsics([2780,2780,2048,1536,0],[4096,3072],[0,0,4096,3072],[4096,3072],90)
        self.assertEqual(result['output_dimensions'],[3072,4096])
        self.assertEqual(result['projection_in_original_camera_axes'],[[0,-2780,1535],[2780,0,2048],[0,0,1]])
        self.assertFalse(result['camera_axes_rotated'])

    def test_crop_outside_sensor_rejected(self):
        with self.assertRaises(ValueError):
            map_intrinsics([2780,2780,2048,1536,0],[4096,3072],[-1,0,4096,3072],[640,480],0)

    def test_unknown_rotation_rejected(self):
        with self.assertRaises(ValueError):
            map_intrinsics([2780,2780,2048,1536,0],[4096,3072],[0,0,4096,3072],[640,480],45)
