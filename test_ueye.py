
import cv2
import numpy as np
from pyueye import ueye


CAMERA_ID = 2


def main():
    camera = ueye.HIDS(CAMERA_ID)

    image_memory = ueye.c_mem_p()
    memory_id = ueye.int()

    camera_initialized = False
    memory_allocated = False
    video_started = False

    try:
        # Initialize IDS camera.
        result = ueye.is_InitCamera(camera, None)

        if result != ueye.IS_SUCCESS:
            print("Could not open IDS camera:", result)
            return

        camera_initialized = True

        print("IDS camera opened successfully!")
        print(f"Camera ID: {CAMERA_ID}")

        # Get sensor information.
        sensor_info = ueye.SENSORINFO()

        result = ueye.is_GetSensorInfo(camera, sensor_info)

        if result != ueye.IS_SUCCESS:
            print("Could not get sensor information.")
            return

        width = int(sensor_info.nMaxWidth)
        height = int(sensor_info.nMaxHeight)

        print(f"Sensor resolution: {width} x {height}")

        # Set color mode.
        result = ueye.is_SetColorMode(
            camera,
            ueye.IS_CM_BGR8_PACKED
        )

        if result != ueye.IS_SUCCESS:
            print("Could not set color mode:", result)
            return

        # Allocate image memory.
        bits_per_pixel = ueye.INT(24)

        width_param = ueye.INT(width)
        height_param = ueye.INT(height)
        pitch = ueye.INT()

        result = ueye.is_AllocImageMem(
            camera,
            width,
            height,
            bits_per_pixel,
            image_memory,
            memory_id
        )

        if result != ueye.IS_SUCCESS:
            print("Could not allocate image memory:", result)
            return

        memory_allocated = True

        # Activate allocated image memory.
        result = ueye.is_SetImageMem(
            camera,
            image_memory,
            memory_id
        )

        if result != ueye.IS_SUCCESS:
            print("Could not set image memory:", result)
            return

        # Get actual image memory pitch.
        result = ueye.is_InquireImageMem(
            camera,
            image_memory,
            memory_id,
            width_param,
            height_param,
            bits_per_pixel,
            pitch
        )

        if result != ueye.IS_SUCCESS:
            print("Could not inquire image memory:", result)
            return

        print("Image memory allocated successfully.")

        # Start live acquisition.
        result = ueye.is_CaptureVideo(
            camera,
            ueye.IS_DONT_WAIT
        )

        if result != ueye.IS_SUCCESS:
            print("Could not start video:", result)
            return

        video_started = True

        print("Camera is running. Press Q to quit.")

        while True:

            # Read image data from allocated camera memory.
            image_data = ueye.get_data(
                image_memory,
                width_param,
                height_param,
                bits_per_pixel,
                pitch,
                copy=True
            )

            frame = np.asarray(image_data).reshape(
                height,
                int(pitch.value) // 3
            )[:, :width * 3].reshape(height, width, 3)

            # Display image.
            cv2.imshow("IDS uEye camera test", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

    except Exception as error:
        print("Camera error:", error)

    finally:
        # Release resources in the correct order.
        if video_started:
            ueye.is_StopLiveVideo(camera, ueye.IS_WAIT)

        if memory_allocated:
            ueye.is_FreeImageMem(
                camera,
                image_memory,
                memory_id
            )

        if camera_initialized:
            ueye.is_ExitCamera(camera)

        cv2.destroyAllWindows()

        print("Camera closed.")


if __name__ == "__main__":
    main()
