"""Detect four ArUco reference markers and calculate pixel -> wobjA3 XY mapping.

ROBOT_POINTS_MM contains the measured XY coordinates (mm) of the
outermost corner of each marker, in the wobjA3 coordinate frame.

The same marker corners are extracted from the camera image.
Run: python aruco_calibration.py; press C to save calibration, Q to quit.
"""

from pathlib import Path
import cv2
import numpy as np
from coordinate_transform import create_calibration, save_calibration
from camera_connection import IDSCamera


REQUIRED_IDS = (0, 1, 2, 3)

# Measured robot XY coordinates of the selected outer corner of each marker.
ROBOT_POINTS_MM = {
    0: (-235.9, 225.7),  # (X_mm, Y_mm)
    1: (532.5, 238.1),
    2: (529.4, -56.3),
    3: (-231.4, -70.3),
}

def make_detector():
    aruco = cv2.aruco
    dictionary = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
    parameters = aruco.DetectorParameters() if hasattr(aruco, "DetectorParameters") else aruco.DetectorParameters_create()
    detector = aruco.ArucoDetector(dictionary, parameters) if hasattr(aruco, "ArucoDetector") else None
    return dictionary, parameters, detector


def detect_markers(frame, dictionary, parameters, detector):

    if detector is not None:
        corners, ids, _ = detector.detectMarkers(frame)
    else:
        corners, ids, _ = cv2.aruco.detectMarkers(
            frame, dictionary, parameters=parameters
        )

    found = {}

    # Select the outermost corner of each marker.
    outer_corner_indices = {
        0: 0,  # Bottom-right marker
        1: 1,  # Bottom-left marker
        2: 2,  # Top-left marker
        3: 3,  # Top-right marker
    }

    if ids is not None:
        for marker_corners, marker_id in zip(corners, ids.flatten()):

            marker_id = int(marker_id)
            if marker_id not in REQUIRED_IDS:
                continue

            points = np.asarray(
                marker_corners, dtype=np.float32
            ).reshape(4, 2)

            corner_index = outer_corner_indices[marker_id]
            selected_corner = points[corner_index]

            found[marker_id] = (
                float(selected_corner[0]),
                float(selected_corner[1])
            )

    return found, corners, ids


def main():
    if not hasattr(cv2, "aruco"):
        raise RuntimeError("cv2.aruco mangler. Installer opencv-contrib-python.")
    
    missing_coords = [marker_id for marker_id in REQUIRED_IDS if ROBOT_POINTS_MM[marker_id] is None]
    
    if missing_coords:
        print("Fyll inn ROBOT_POINTS_MM før kalibrering. Mangler koordinater for ID:", missing_coords)
        print("Koordinatene må være ytterhjørnene målt i wobjA3, ikke base/world.")
        print("Kameraet kan likevel brukes til å kontrollere at ID 0-3 blir oppdaget.")

    dictionary, parameters, detector = make_detector()

    camera = IDSCamera(camera_id=2)
    

    print("Vis alle fire markørene. Trykk C for kalibrering, Q for å avslutte.")
    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                print("Kunne ikke lese kamerabilde")
                break


            found, corners, ids = detect_markers(frame, dictionary, parameters, detector)
            

            if ids is not None:
                cv2.aruco.drawDetectedMarkers(frame, corners, ids)
            for marker_id, (px, py) in found.items():
                cv2.circle(frame, (round(px), round(py)), 5, (0, 255, 0), -1)
                cv2.putText(frame, f"ID {marker_id}", (round(px) + 8, round(py) - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            missing = sorted(set(REQUIRED_IDS) - set(found))
            status = f"Found all 4 - press C | IDs {sorted(found)}" if not missing else f"Missing IDs: {missing}"
            cv2.putText(frame, status, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                        (0, 200, 0) if not missing else (0, 0, 255), 2)
            
            # Display the full camera image at 50% size.
            display_frame = cv2.resize(
                frame,
                None,
                fx=0.5,
                fy=0.5,
                interpolation=cv2.INTER_AREA
            )

            cv2.imshow("Four ArUco calibration markers", display_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("c"):
                if missing:
                    print("Kalibrering avbrutt. Markører mangler:", missing)
                    continue
                if missing_coords:
                    print("Kalibrering kan ikke lagres før ROBOT_POINTS_MM er fylt inn.")
                    continue
                pixel_points = [found[i] for i in REQUIRED_IDS]
                robot_points = [ROBOT_POINTS_MM[i] for i in REQUIRED_IDS]
                matrix = create_calibration(pixel_points, robot_points)
                save_calibration(matrix)
                print("Kalibrering lagret. Homography (pixel -> wobjA3 XY):")
                print(matrix)
    finally:
        camera.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
