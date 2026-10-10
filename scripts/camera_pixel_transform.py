"""Explicit sensor crop/resize/rotation mapping for board calibration data."""
import math


def multiply(a,b):
    return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def map_intrinsics(intrinsics, sensor_size, crop, unrotated_output_size, clockwise_rotation):
    fx,fy,cx,cy,skew=intrinsics
    width,height=sensor_size
    left,top,right,bottom=crop
    out_width,out_height=unrotated_output_size
    if not all(math.isfinite(value) for value in [*intrinsics,*sensor_size,*crop,*unrotated_output_size]):
        raise ValueError('Non-finite camera parameters')
    if not (0<=left<right<=width and 0<=top<bottom<=height and out_width>0 and out_height>0 and fx>0 and fy>0):
        raise ValueError('Invalid explicit crop or dimensions')
    sx,sy=out_width/(right-left),out_height/(bottom-top)
    sensor_to_buffer=[[sx,0,-left*sx],[0,sy,-top*sy],[0,0,1]]
    rotations={0:[[1,0,0],[0,1,0],[0,0,1]],
               90:[[0,-1,out_height-1],[1,0,0],[0,0,1]],
               180:[[-1,0,out_width-1],[0,-1,out_height-1],[0,0,1]],
               270:[[0,1,0],[-1,0,out_width-1],[0,0,1]]}
    if clockwise_rotation not in rotations:
        raise ValueError('Rotation must be 0, 90, 180 or 270 degrees')
    intrinsic=[[fx,skew,cx],[0,fy,cy],[0,0,1]]
    transform=multiply(rotations[clockwise_rotation],sensor_to_buffer)
    return {'sensor_to_image_pixels':transform,
            'projection_in_original_camera_axes':multiply(transform,intrinsic),
            'output_dimensions':[out_height,out_width] if clockwise_rotation in [90,270] else [out_width,out_height],
            'coordinate_convention':'integer pixel centers, origin at upper-left',
            'camera_axes_rotated':False,
            'distortion_and_document_warp_applied':False}
