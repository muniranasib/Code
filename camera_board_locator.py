"""Live camera demo: detect a 4x4 Sudoku board and express its geometry in wobjA3 XY.
Run only after aruco_calibration.py has saved camera_calibration.json.
"""
import cv2
import json
from pathlib import Path
from coordinate_transform import board_geometry_from_corners
from sudoku_vision import find_board_corners
from project_paths import GENERATED_DATA_DIR

OUTPUT_FILE = (GENERATED_DATA_DIR / "detected_board_position.json")

CAMERA_INDEX = 0


def main():
    camera = cv2.VideoCapture(CAMERA_INDEX)
    if not camera.isOpened():
        raise RuntimeError(f"Kunne ikke åpne kamera {CAMERA_INDEX}")

    print("Vis hele Sudoku-brettet. Trykk s for å lagre posisjon, q for å avslutte.")
    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                break
            display = frame.copy()
            geometry = None
            try:
                detection = find_board_corners(frame)

                corners = detection["corners"]

                geometry = board_geometry_from_corners(corners)

                cv2.polylines(display, [corners.astype('int32')], True, (0, 255, 0), 3)

                for i, (x, y) in enumerate(corners.astype('int32')):
                    cv2.circle(display, (int(x), int(y)), 6, (0, 0, 255), -1)
                    cv2.putText(display, str(i), (int(x) + 8, int(y) - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                text = (f"WObj origin: ({geometry['origin_x']:.1f}, {geometry['origin_y']:.1f}) mm  "f"cell: {geometry['cell_width']:.1f} mm")

                cv2.putText(display, text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            except (RuntimeError, ValueError, FileNotFoundError) as exc:
                cv2.putText(display, "Board/calibration not ready", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.imshow("Sudoku board position", display)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            if key == ord('s') and geometry is not None:
                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    json.dump(geometry, f, indent=4)
                print(f"Saved board geometry: {OUTPUT_FILE}")
                print(geometry)
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
