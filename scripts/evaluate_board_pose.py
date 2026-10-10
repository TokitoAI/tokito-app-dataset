"""Evaluate physical board pose with withheld 3D/image landmarks.

Fitting landmarks are never included in the reported projection accuracy.
Input coordinates must share the source model's metric frame. Image points
must already match the supplied camera matrix and distortion coefficients.
"""
import json
import math
import numpy as np


def evaluate(record):
    fit = record['fit_landmarks']
    held = record['withheld_landmarks']
    if len(fit) < 4 or len(held) < 3:
        raise ValueError('Require four fit and three independently withheld landmarks')
    ids = [p['id'] for p in fit + held]
    if len(set(ids)) != len(ids):
        raise ValueError('Fit/withheld landmark identities must be disjoint')
    k = np.asarray(record['camera_matrix'], dtype=np.float64)
    distortion = np.asarray(record['distortion_coefficients'], dtype=np.float64)
    xyz = lambda points: np.asarray([p['model_xyz_metres'] for p in points], dtype=np.float64)
    uv = lambda points: np.asarray([p['image_xy_pixels'] for p in points], dtype=np.float64)
    for arr in [k, distortion, xyz(fit), uv(fit), xyz(held), uv(held)]:
        if not np.isfinite(arr).all():
            raise ValueError('Nonfinite geometry or camera values')
    if (k.shape != (3, 3) or k[0, 0] <= 0 or k[1, 1] <= 0
            or not np.allclose(k[2], [0.0, 0.0, 1.0], atol=1e-9)
            or not np.isclose(k[1, 0], 0.0, atol=1e-9)):
        raise ValueError('Supply a camera-axis-consistent conventional camera matrix')
    fit_xyz = xyz(fit)
    centered = fit_xyz - fit_xyz.mean(axis=0)
    rank = np.linalg.matrix_rank(centered, tol=1e-10)
    if rank < 2 or (rank == 3 and len(fit) < 6):
        raise ValueError('Fit landmarks are collinear or too few for nonplanar pose')
    import cv2
    ok, rvec, tvec = cv2.solvePnP(xyz(fit), uv(fit), k, distortion, flags=cv2.SOLVEPNP_ITERATIVE)
    if not ok:
        raise ValueError('Pose fit failed')
    predicted, _ = cv2.projectPoints(xyz(held), rvec, tvec, k, distortion)
    errors = np.linalg.norm(predicted.reshape(-1, 2) - uv(held), axis=1)
    rotation, _ = cv2.Rodrigues(rvec)
    depths = (xyz(fit + held) @ rotation.T + tvec.reshape(1, 3))[:, 2]
    return {
        'fit_landmark_count': len(fit), 'withheld_landmark_count': len(held),
        'withheld_errors_pixels': errors.tolist(),
        'withheld_rmse_pixels': float(math.sqrt(np.mean(errors ** 2))),
        'withheld_max_error_pixels': float(errors.max()),
        'all_landmarks_in_front_of_camera': bool((depths > 0).all()),
        'rotation_model_to_camera': rotation.tolist(),
        'translation_model_to_camera_metres': tvec.reshape(3).tolist(),
        'physical_validation_eligible': bool((depths > 0).all()
                                             and record.get('capture_camera_transform_verified')
                                             and record.get('independent_landmark_review_verified')
                                             and record.get('source_to_specimen_geometry_verified')),
        'continuous_flip_tracking_verified': False,
        'production_eligible': False,
    }


if __name__ == '__main__':
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record', type=Path)
    args = parser.parse_args()
    print(json.dumps(evaluate(json.loads(args.record.read_text())), indent=2))
