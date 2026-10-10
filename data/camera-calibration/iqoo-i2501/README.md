# iQOO camera coordinates

`profile.json` records selected factory Camera2 characteristics for rear camera
IDs 0 and 2, retrieved from the connected I2501. The SHA-256 binds the filtered
static metadata file; camera-service events and unrelated client information
are excluded. Factory coefficients are a starting point, not measured optical
calibration or proof of correct board projection.

The reported default sensor frame is 4096 x 3072. Intrinsic calibration uses
pre-correction sensor coordinates. Maximum-resolution sensor modes need their
own characteristics. Sensor orientation alone does not determine the rotation
of an encoded photograph or the application's preview.

`scripts/camera_pixel_transform.py` requires an explicit sensor crop, buffer
size, and clockwise image rotation. It returns the image transform and its
product with the sensor intrinsic matrix, retaining the original camera axes.
After a 90-degree image rotation this product is not a conventional triangular
camera matrix: do not pass it to a solver that assumes that form. Its crop/scale
convention uses integer pixel centers without an additional half-pixel offset;
the actual image resampler must use the same convention.

Before projecting metric component geometry, record the actual camera ID,
sensor pixel mode, CaptureResult crop and intrinsics, output dimensions,
rotation/mirroring, and any stabilization or document-mode warp. Apply the
appropriate distortion mapping separately. Reported zero distortion does not
prove zero physical distortion. Validate projection against independent
landmarks across tilted views, both board faces, and a continuous flip before
enabling production use. This profile and helper do not yet activate mobile AR.

Android's coordinate definitions:
https://developer.android.com/reference/android/hardware/camera2/CameraCharacteristics#LENS_INTRINSIC_CALIBRATION
