import sys
import unittest
from pathlib import Path
import numpy as np
import cv2
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from evaluate_board_pose import evaluate


class PoseEvaluationTests(unittest.TestCase):
    def fixture(self, flipped=False):
        xyz = np.array([[-.05,-.03,0],[.05,-.03,0],[.05,.03,0],[-.05,.03,0],
                        [-.02,-.01,.004],[.015,.015,.008],[.03,-.02,.003]], dtype=float)
        k = np.array([[1000.,0,640],[0,1000.,360],[0,0,1]])
        r = np.array([np.pi if flipped else .2, .1, .08])
        points, _ = cv2.projectPoints(xyz, r, np.array([0.,0.,.4]), k, np.zeros(5))
        items = [{'id': str(i), 'model_xyz_metres': p.tolist(), 'image_xy_pixels': q.tolist()}
                 for i,(p,q) in enumerate(zip(xyz,points.reshape(-1,2)))]
        return {'fit_landmarks': items[:4], 'withheld_landmarks': items[4:],
                'camera_matrix': k.tolist(), 'distortion_coefficients': [0]*5}

    def test_withheld_projection_on_top_and_flipped_board(self):
        for flipped in [False, True]:
            result = evaluate(self.fixture(flipped))
            self.assertLess(result['withheld_max_error_pixels'], .01)
            self.assertTrue(result['all_landmarks_in_front_of_camera'])
            self.assertFalse(result['physical_validation_eligible'])
            self.assertFalse(result['continuous_flip_tracking_verified'])

    def test_holdout_error_is_not_hidden_by_exact_fit(self):
        record = self.fixture()
        record['withheld_landmarks'][0]['image_xy_pixels'][0] += 25
        self.assertGreater(evaluate(record)['withheld_max_error_pixels'], 24)

    def test_fit_point_cannot_be_reused_as_holdout(self):
        record = self.fixture()
        record['withheld_landmarks'][0]['id'] = '0'
        with self.assertRaises(ValueError):
            evaluate(record)

    def test_rotated_noncanonical_matrix_rejected(self):
        record = self.fixture()
        record['camera_matrix'] = [[0, -1000, 719], [1000, 0, 0], [0, 0, 1]]
        with self.assertRaises(ValueError):
            evaluate(record)

    def test_collinear_fit_landmarks_rejected(self):
        record = self.fixture()
        for index, point in enumerate(record['fit_landmarks']):
            point['model_xyz_metres'] = [index * .01, 0, 0]
        with self.assertRaises(ValueError):
            evaluate(record)
