"""Camera pixel <-> ABB robot workobject XY coordinate transformation."""
import json
import cv2
import numpy as np

from project_paths import GENERATED_DATA_DIR

CALIBRATION_FILE = (GENERATED_DATA_DIR / "camera_calibration.json")
MIN_CALIBRATION_POINTS = 4


def create_calibration(pixel_points, robot_points):
    pixels = np.asarray(pixel_points, dtype=np.float32)
    robot = np.asarray(robot_points, dtype=np.float32)

    if pixels.shape != robot.shape or pixels.ndim != 2 or pixels.shape[1] != 2:
        raise ValueError("Begge punktlister må ha samme form (N, 2).")

    if len(pixels) < MIN_CALIBRATION_POINTS:
        raise ValueError("Minst fire samsvarende kalibreringspunkter kreves.")

    if not np.all(np.isfinite(pixels)) or not np.all(np.isfinite(robot)):
        raise ValueError("Kalibreringspunktene må være gyldige tall.")

    if len(np.unique(pixels, axis=0)) != len(pixels):
        raise ValueError("Pikselpunktene må være unike.")

    if len(np.unique(robot, axis=0)) != len(robot):
        raise ValueError("Robotpunktene må være unike.")

    matrix, _ = cv2.findHomography(pixels, robot, method=0)

    if matrix is None or not np.all(np.isfinite(matrix)):
        raise RuntimeError("Kunne ikke beregne en gyldig homography.")

    return matrix


def save_calibration(matrix):
    data = {"homography": np.asarray(matrix, dtype=float).tolist(),
            "coordinate_frame": "wobjA3", "units": "mm"}

    matrix = np.asarray(matrix, dtype=np.float64)

    if matrix.shape != (3, 3) or not np.all(np.isfinite(matrix)):
        raise ValueError("Ugyldig kalibreringsmatrise.")
    
    CALIBRATION_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(CALIBRATION_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
    print(f"Kalibrering lagret: {CALIBRATION_FILE}")


def load_calibration():
    if not CALIBRATION_FILE.exists():
        raise FileNotFoundError("camera_calibration.json finnes ikke. Kjør aruco_calibration.py først.")
    
    with open(CALIBRATION_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("coordinate_frame") != "wobjA3" or data.get("units") != "mm":
        raise ValueError("Kalibreringsfilen har feil koordinatsystem eller enhet.")
    
    matrix = np.asarray(data["homography"], dtype=np.float64)

    if matrix.shape != (3, 3):
        raise ValueError("Ugyldig kalibreringsmatrise.")
    return matrix


def image_to_robot(pixel_x, pixel_y, matrix=None):
    matrix = load_calibration() if matrix is None else matrix
    point = np.array([[[pixel_x, pixel_y]]], dtype=np.float32)
    x, y = cv2.perspectiveTransform(point, matrix)[0][0]
    return float(x), float(y)


def image_points_to_robot(pixel_points, matrix=None):
    matrix = load_calibration() if matrix is None else matrix
    points = np.asarray(pixel_points, dtype=np.float32).reshape(-1, 1, 2)
    transformed = cv2.perspectiveTransform(points, matrix)
    return [(float(p[0][0]), float(p[0][1])) for p in transformed]


def board_geometry_from_corners(board_corners_px, matrix=None):
    """Return top-left board origin and cell width/height in WObj mm.

    board_corners_px must be ordered [top-left, top-right, bottom-right, bottom-left].
    Assumes board edges are parallel to the X/Y axes of wobjA3 for RAPID drawing.
    """
    if len(board_corners_px) != 4:
        raise ValueError("Brettet må ha nøyaktig fire hjørner.")
    robot_corners = image_points_to_robot(board_corners_px, matrix)
    tl, tr, br, bl = robot_corners
    width = (np.linalg.norm(np.asarray(tr) - np.asarray(tl)) +
             np.linalg.norm(np.asarray(br) - np.asarray(bl))) / 2.0
    height = (np.linalg.norm(np.asarray(bl) - np.asarray(tl)) +
              np.linalg.norm(np.asarray(br) - np.asarray(tr))) / 2.0
    if abs(width - height) > max(width, height) * 0.15:
        print("Advarsel: Brettet ser ikke kvadratisk ut i robotkoordinater.")
    return {"origin_x": tl[0], "origin_y": tl[1],
            "cell_width": width / 4.0, "cell_height": height / 4.0,
            "corners_robot": robot_corners}
