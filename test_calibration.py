
"""Test the saved camera-to-robot calibration using ArUco markers.

The program detects four reference markers, loads the saved homography
and allows the user to click points in the camera image.

Mouse clicks are transformed into wobjA3 coordinates in millimeters.

This program does not move the robot.
"""

import json
from pathlib import Path

import cv2
import numpy as np

from camera_connection import IDSCamera


# Reference marker IDs
REQUIRED_IDS = (0, 1, 2, 3)

# Measured robot coordinates in wobjA3 (mm)
ROBOT_POINTS_MM = {
    0: (-235.9, 225.7),
    1: (532.5, 238.1),
    2: (529.4, -56.3),
    3: (-231.4, -70.3),
}

# Selected outer corner for each marker
OUTER_CORNER_INDICES = {
    0: 0,  # ID 0: top-left marker
    1: 1,  # ID 1: bottom-left marker
    2: 2,  # ID 2: bottom-right marker
    3: 3,  # ID 3: top-right marker
}

PROJECT_DIR = Path(__file__).resolve().parent

CALIBRATION_FILE = (
    PROJECT_DIR
    / "data"
    / "generated_data"
    / "camera_calibration.json"
)

if not CALIBRATION_FILE.is_file():
    CALIBRATION_FILE = PROJECT_DIR / "camera_calibration.json"

IMAGE_DIR = PROJECT_DIR / "images" / "generated_images"

WINDOW_NAME = "Test camera calibration"

# Selected point from mouse click
selected_pixel = None


def load_homography():
    """Load and validate the saved pixel-to-robot homography."""

    if not CALIBRATION_FILE.is_file():
        raise FileNotFoundError(
            f"Fant ikke kalibreringsfilen: {CALIBRATION_FILE}"
        )

    with CALIBRATION_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("coordinate_frame") != "wobjA3":
        raise ValueError("Kalibreringen må bruke wobjA3.")

    if data.get("units") != "mm":
        raise ValueError("Kalibreringen må bruke millimeter.")

    matrix = np.asarray(
        data.get("homography"),
        dtype=np.float64
    )

    if matrix.shape != (3, 3):
        raise ValueError("Homography må være en 3x3-matrise.")

    if not np.all(np.isfinite(matrix)):
        raise ValueError("Homography inneholder ugyldige tall.")

    if abs(np.linalg.det(matrix)) < 1e-12:
        raise ValueError("Homography-matrisen kan ikke inverteres.")

    return matrix


def make_detector():
    """Create an ArUco detector compatible with different OpenCV versions."""

    aruco = cv2.aruco

    dictionary = aruco.getPredefinedDictionary(
        aruco.DICT_4X4_50
    )

    parameters = (
        aruco.DetectorParameters()
        if hasattr(aruco, "DetectorParameters")
        else aruco.DetectorParameters_create()
    )

    detector = (
        aruco.ArucoDetector(dictionary, parameters)
        if hasattr(aruco, "ArucoDetector")
        else None
    )

    return dictionary, parameters, detector


def detect_reference_points(frame, dictionary, parameters, detector):
    """Detect the selected outer corner of each reference marker."""

    if detector is not None:
        corners, ids, _ = detector.detectMarkers(frame)

    else:
        corners, ids, _ = cv2.aruco.detectMarkers(
            frame,
            dictionary,
            parameters=parameters
        )

    found = {}

    if ids is not None:

        for marker_corners, marker_id in zip(corners, ids.flatten()):

            marker_id = int(marker_id)

            if marker_id not in REQUIRED_IDS:
                continue

            marker_points = np.asarray(
                marker_corners,
                dtype=np.float32
            ).reshape(4, 2)

            corner_index = OUTER_CORNER_INDICES[marker_id]

            px, py = marker_points[corner_index]

            found[marker_id] = (float(px), float(py))

    return found, corners, ids


def pixel_to_robot(pixel_point, homography):
    """Transform a pixel point into wobjA3 X/Y coordinates in mm."""

    point = np.asarray(
        [[pixel_point]],
        dtype=np.float64
    )

    transformed = cv2.perspectiveTransform(
        point,
        homography.astype(np.float64)
    )

    return tuple(
        float(value) for value in transformed[0, 0]
    )


def mouse_callback(event, x, y, flags, param):
    """Select a point using the mouse in the displayed image."""

    global selected_pixel

    if event == cv2.EVENT_LBUTTONDOWN:

        # Display image is scaled to 50%.
        # Convert display coordinates to original image coordinates.
        selected_pixel = (x * 2, y * 2)


def main():

    global selected_pixel

    if not hasattr(cv2, "aruco"):
        raise RuntimeError(
            "cv2.aruco mangler. Installer opencv-contrib-python."
        )

    homography = load_homography()

    dictionary, parameters, detector = make_detector()

    print(f"Kalibrering lastet fra: {CALIBRATION_FILE}")
    print("Koordinatsystem: wobjA3 | Enhet: mm")
    print()
    print("Klikk på et punkt i Sudoku-brettet for å beregne X/Y.")
    print("Trykk S for å lagre bildet.")
    print("Trykk Q for å avslutte.")
    print()

    camera = IDSCamera(camera_id=2)

    reported = False
    last_reported_pixel = None

    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, mouse_callback)

    try:

        while True:

            ok, frame = camera.read()

            if not ok:
                print("Kunne ikke lese kamerabilde.")
                break

            # Detect ArUco markers
            found, corners, ids = detect_reference_points(
                frame,
                dictionary,
                parameters,
                detector
            )

            if ids is not None:
                cv2.aruco.drawDetectedMarkers(
                    frame,
                    corners,
                    ids
                )

            missing = sorted(
                set(REQUIRED_IDS) - set(found)
            )

            # Draw reference marker coordinates
            for marker_id, pixel_point in found.items():

                px, py = pixel_point

                robot_x, robot_y = pixel_to_robot(
                    pixel_point,
                    homography
                )

                cv2.circle(
                    frame,
                    (round(px), round(py)),
                    6,
                    (0, 255, 0),
                    -1
                )

                label = (
                    f"ID {marker_id}: "
                    f"X={robot_x:.1f}, Y={robot_y:.1f} mm"
                )

                cv2.putText(
                    frame,
                    label,
                    (round(px) + 8, round(py) - 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (0, 255, 0),
                    2
                )

            # Print reference results only once
            if len(found) == len(REQUIRED_IDS) and not reported:

                print("Resultat for referansemarkørene:")

                for marker_id in REQUIRED_IDS:

                    robot_x, robot_y = pixel_to_robot(
                        found[marker_id],
                        homography
                    )

                    expected_x, expected_y = ROBOT_POINTS_MM[marker_id]

                    error = np.hypot(
                        robot_x - expected_x,
                        robot_y - expected_y
                    )

                    print(
                        f"ID {marker_id}: "
                        f"beregnet=({robot_x:.2f}, {robot_y:.2f}) mm | "
                        f"referanse=({expected_x:.2f}, {expected_y:.2f}) mm | "
                        f"avvik={error:.3f} mm"
                    )

                print()
                reported = True

            # Marker detection status
            status = (
                "All 4 markers detected"
                if not missing
                else f"Missing IDs: {missing}"
            )

            cv2.putText(
                frame,
                status,
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 200, 0) if not missing else (0, 0, 255),
                2
            )

            # Calculate coordinates of selected mouse point
            if selected_pixel is not None:

                px, py = selected_pixel

                robot_x, robot_y = pixel_to_robot(
                    selected_pixel,
                    homography
                )

                cv2.circle(
                    frame,
                    (px, py),
                    8,
                    (255, 0, 0),
                    -1
                )

                cv2.putText(
                    frame,
                    f"X={robot_x:.1f}, Y={robot_y:.1f} mm",
                    (px + 10, py - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 0, 0),
                    2
                )

                # Print only when a new point is selected
                if selected_pixel != last_reported_pixel:

                    print(
                        f"Valgt punkt: pixel=({px}, {py}) | "
                        f"Robot X={robot_x:.2f} mm, "
                        f"Y={robot_y:.2f} mm"
                    )

                    last_reported_pixel = selected_pixel

            # Resize only the displayed image
            display_frame = cv2.resize(
                frame,
                None,
                fx=0.5,
                fy=0.5,
                interpolation=cv2.INTER_AREA
            )

            cv2.imshow(WINDOW_NAME, display_frame)

            # Keyboard controls
            key = cv2.waitKey(1) & 0xFF

            if key == ord("s"):

                IMAGE_DIR.mkdir(
                    parents=True,
                    exist_ok=True
                )

                image_path = IMAGE_DIR / "sudoku_calibration_test.png"

                cv2.imwrite(
                    str(image_path),
                    frame
                )

                print(f"Bildet er lagret: {image_path}")

            if key == ord("q"):
                break

    finally:

        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
