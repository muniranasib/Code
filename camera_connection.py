
"""Connection to the IDS uEye camera using the pyueye SDK."""

import cv2
import numpy as np
from pyueye import ueye


class IDSCamera:
    """Handles initialization, image capture and cleanup of an IDS camera."""

    def __init__(self, camera_id=2):
        self.camera = ueye.HIDS(camera_id)
        self.image_memory = ueye.c_mem_p()
        self.memory_id = ueye.int()

        self.initialized = False
        self.memory_allocated = False
        self.capturing = False

        self.width = 0
        self.height = 0
        self.bits_per_pixel = ueye.INT(24)
        self.pitch = ueye.INT()

        self._open_camera()

    def _check(self, result, operation):
        if result != ueye.IS_SUCCESS:
            raise RuntimeError(
                f"IDS camera error during {operation}: {result}"
            )

    def _open_camera(self):
        """Initialize the camera and start image acquisition."""

        self._check(
            ueye.is_InitCamera(self.camera, None),
            "camera initialization"
        )
        self.initialized = True

        sensor_info = ueye.SENSORINFO()
        self._check(
            ueye.is_GetSensorInfo(self.camera, sensor_info),
            "getting sensor information"
        )

        self.width = int(sensor_info.nMaxWidth)
        self.height = int(sensor_info.nMaxHeight)

        print(f"IDS camera resolution: {self.width} x {self.height}")

        self._check(
            ueye.is_SetColorMode(self.camera, ueye.IS_CM_BGR8_PACKED),
            "setting BGR color mode"
        )

        width_param = ueye.INT(self.width)
        height_param = ueye.INT(self.height)

        self._check(
            ueye.is_AllocImageMem(
                self.camera,
                width_param,
                height_param,
                self.bits_per_pixel,
                self.image_memory,
                self.memory_id
            ),
            "allocating image memory"
        )
        self.memory_allocated = True

        self._check(
            ueye.is_SetImageMem(
                self.camera,
                self.image_memory,
                self.memory_id
            ),
            "setting image memory"
        )

        self._check(
        ueye.is_InquireImageMem(
            self.camera,
            self.image_memory,
            self.memory_id,
            width_param,
            height_param,
            self.bits_per_pixel,
            self.pitch
        ),
        "inquiring image memory"
    )

        self._check(
            ueye.is_CaptureVideo(self.camera, ueye.IS_DONT_WAIT),
            "starting video capture"
        )
        self.capturing = True

    def read(self):
        """Return the latest camera image as an OpenCV BGR frame."""

        if not self.capturing:
            return False, None

        image_data = ueye.get_data(
            self.image_memory,
            ueye.INT(self.width),
            ueye.INT(self.height),
            self.bits_per_pixel,
            self.pitch,
            copy=True
        )

        frame_data = np.asarray(image_data, dtype=np.uint8).reshape(-1)

        expected_size = self.width * self.height * 3

        if frame_data.size == expected_size:
            frame = frame_data.reshape(
                self.height, self.width, 3
            )

        elif frame_data.size == self.pitch.value * self.height:
            frame = frame_data.reshape(
                self.height, self.pitch.value
            )
            frame = frame[:, :self.width * 3]
            frame = frame.reshape(
                self.height, self.width, 3
            )

        else:
            raise RuntimeError(
                "Unexpected IDS image buffer size: "
                f"{frame_data.size}. Expected {expected_size} "
                f"or {self.pitch.value * self.height}."
            )

        return True, frame.copy()

    def release(self):
        """Stop acquisition and release camera resources."""

        if self.capturing:
            ueye.is_StopLiveVideo(
                self.camera, ueye.IS_FORCE_VIDEO_STOP
            )
            self.capturing = False

        if self.memory_allocated:
            ueye.is_FreeImageMem(
                self.camera,
                self.image_memory,
                self.memory_id
            )
            self.memory_allocated = False

        if self.initialized:
            ueye.is_ExitCamera(self.camera)
            self.initialized = False

        print("IDS camera closed.")
