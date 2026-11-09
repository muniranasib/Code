
import tkinter as tk
from tkinter import messagebox

import time 

from robot_connection import RobotConnection
from sudoku_app import SudokuApp

from project_paths import IMAGE_DIR
from sudoku_solver import format_board
from sudoku_vision import process_image, recognize_and_solve


import cv2
import time

from config import MODE
from robot_connection import RobotConnection
from camera_connection import IDSCamera
from project_paths import IMAGE_DIR

# --------------------------------------------------
# BOARD SETTINGS
# --------------------------------------------------

BOARD_SIZE = "mini"

BOARD_SIZE_OPTIONS = {
    "mini": (120.0, 120.0),
    "small": (150.0, 150.0),
}

#Hoved
"""def main():
    root = tk.Tk()
    robot = RobotConnection()

    try:
        robot.start_server()

        SudokuApp(root, robot)

        root.mainloop()

    except Exception as exc:
        messagebox.showerror("Startup error", str(exc))
        raise

    finally:
        robot.close()


if __name__ == "__main__":
    main()
"""



import cv2

from project_paths import IMAGE_DIR
from camera_connection import IDSCamera
from aruco_calibration import (
    make_detector,
    detect_markers,
    REQUIRED_IDS
)
from sudoku_vision import (
    process_image,
    get_board_cell_positions
)
from coordinate_transform import board_geometry_from_corners
from robot_connection import RobotConnection


# --------------------------------------------------
# TEST DATA
# --------------------------------------------------

SUDOKU_1 = "2222222222222222"
SUDOKU_2 = "2202222022220222"

# Start with one cell per board for safety.
# Change to False when the first tests succeed.
TEST_ONLY_ONE_CELL = True


# --------------------------------------------------
# CAMERA AND BOARD DETECTION
# --------------------------------------------------

def detect_sudoku_board(camera):

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    image_path = IMAGE_DIR / "sudoku_photo.jpg"

    dictionary, parameters, detector = make_detector()

    print("\nIDS camera started.")
    print("Show the complete Sudoku board.")
    print("Press C to capture when all markers are visible.")
    print("Press Q to quit.")

    while True:

        ok, frame = camera.read()

        if not ok:
            raise RuntimeError("Could not read IDS camera.")

        found, corners, ids = detect_markers(
            frame, dictionary, parameters, detector
        )

        display = frame.copy()

        if ids is not None:
            cv2.aruco.drawDetectedMarkers(display, corners, ids)

        missing = sorted(set(REQUIRED_IDS) - set(found))

        if not missing:
            status = "All 4 markers found - press C"
            color = (0, 255, 0)
        else:
            status = f"Missing markers: {missing}"
            color = (0, 0, 255)

        cv2.putText(
            display,
            status,
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2
        )

        cv2.imshow("IDS Camera - Live", display)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            return None

        if key == ord("c"):

            if missing:
                print("Cannot capture: markers are missing.")
                continue

            if not cv2.imwrite(str(image_path), frame):
                raise OSError("Could not save camera image.")

            print(f"Image saved: {image_path}")
            break
        result = process_image(image_path, board_size="large")

        print("\nDetected board corners:")
        print(result["corners"])

        # Calculate board geometry in robot coordinates
        geometry = board_geometry_from_corners(
            result["corners"]
        )

        print("\nDetected board geometry:")
        print(f"Origin X: {geometry['origin_x']:.2f} mm")
        print(f"Origin Y: {geometry['origin_y']:.2f} mm")
        print(f"Cell width: {geometry['cell_width']:.2f} mm")
        print(f"Cell height: {geometry['cell_height']:.2f} mm")

        return geometry

    print("\nSudoku board detected!")
    print("Board corners:")
    print(result["corners"])

    # Calculate the center of each cell in image pixels.
    cell_positions = get_board_cell_positions(
        result["corners"]
    )

    # Convert pixel positions to robot coordinates.
    robot_positions = image_points_to_robot(
        [
            (cell["x"], cell["y"])
            for cell in cell_positions
        ]
    )

    print("\nDetected cell positions:")

    for cell, (x, y) in zip(cell_positions, robot_positions):

        cell["robot_x"] = x
        cell["robot_y"] = y

        print(
            f"Row {cell['row']}, Col {cell['col']}: "
            f"X={x:.1f} mm, Y={y:.1f} mm"
        )

    # Show corrected board and grid.
    cv2.imshow(
        "Rectified Sudoku Board",
        result["board_image"]
    )

    cv2.imshow(
        "Sudoku Grid Preview",
        cv2.imread(str(result["preview_path"]))
    )

    print("\nPress any key to continue.")

    cv2.waitKey(0)

    return cell_positions


# --------------------------------------------------
# SEND SUDOKU TO ABB ROBOT
# --------------------------------------------------

def send_sudoku(robot, board, sudoku):

    if len(sudoku) != 16:
        raise ValueError("Sudoku must contain 16 digits.")

    if any(digit not in "01234" for digit in sudoku):
        raise ValueError("Invalid Sudoku digit.")

    sent = 0

    for index, digit in enumerate(sudoku):

        # Empty cell
        if digit == "0":
            continue

        row, col = divmod(index, 4)

        command = (
            f"WRITE {board} {row + 1} {col + 1} {digit}"
        )

        print(f"Sending: {command}")

        reply = robot.send_line(command)

        if reply != "OK":
            raise RuntimeError(
                f"Robot response: {reply}"
            )

        sent += 1

        if TEST_ONLY_ONE_CELL:
            break

    print(f"Board {board}: {sent} digits sent.")


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    camera = None
    robot = RobotConnection()

    try:

        print("Starting robot TCP server...")

        robot.start_server()

        print("Waiting for ABB robot...")

        if not robot.connected_event.wait(timeout=30):
            raise TimeoutError("ABB robot did not connect.")

        print("ABB robot connected!")

        # Start IDS camera
        camera = IDSCamera(camera_id=2)

        # Find board and calculate all cell positions
        positions = detect_sudoku_board(camera)

        if positions is None:
            print("Camera test cancelled.")
            return

        print("\nAll 16 cell positions calculated.")

        # Close camera before robot movement
        camera.release()
        camera = None
        cv2.destroyAllWindows()

        input(
            "\nCheck robot work area and board position. "
            "Press ENTER to start writing..."
        )

        # Large Sudoku
        print("\n========== LARGE SUDOKU ==========")

        send_sudoku(robot, 1, SUDOKU_1)

        if TEST_ONLY_ONE_CELL:
            print("\nSingle-cell test completed.")
        else:

            input("\nPress ENTER for small Sudoku...")

            # Small Sudoku
            print("\n========== SMALL SUDOKU ==========")

            send_sudoku(robot, 2, SUDOKU_2)

        reply = robot.send_line("PARK")

        if reply != "OK":
            raise RuntimeError("Could not park robot.")

        print("\nTest completed!")

    except Exception as exc:

        print(f"\nERROR: {exc}")

    finally:

        if camera is not None:
            camera.release()

        cv2.destroyAllWindows()
        robot.close()


if __name__ == "__main__":
    main()




"""Test"""

import cv2




"""def main():
 

  IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    # This is the image file that will be overwritten.
    image_path = IMAGE_DIR / "sudoku_photo.jpg"

    dictionary, parameters, detector = make_detector()

    camera = IDSCamera(camera_id=2)

    try:
        print("Live camera started.")
        print("Press C to capture an image.")
        print("Press Q to quit.")

        while True:

            ok, frame = camera.read()

            if not ok:
                raise RuntimeError("Could not read image from IDS camera.")

            # Detect ArUco markers in the live image.
            found, corners, ids = detect_markers(
                frame, dictionary, parameters, detector
            )

            display_frame = frame.copy()

            if ids is not None:
                cv2.aruco.drawDetectedMarkers(
                    display_frame, corners, ids
                )

            missing = sorted(set(REQUIRED_IDS) - set(found))

            if not missing:
                status = "All 4 markers found - press C to capture"
                color = (0, 255, 0)
            else:
                status = f"Missing markers: {missing}"
                color = (0, 0, 255)

            cv2.putText(
                display_frame,
                status,
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )

            cv2.imshow("IDS Camera - Live", display_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                print("Capture cancelled.")
                break

            if key == ord("c"):

                if missing:
                    print("Cannot capture: ArUco markers are missing.")
                    continue

                # Save the original, unannotated camera image.
                # cv2.imwrite overwrites the existing file.
                if not cv2.imwrite(str(image_path), frame):
                    raise OSError("Could not save camera image.")

                print(f"New camera image saved: {image_path}")
                print("The previous sudoku_photo.jpg has been overwritten.")

                break

        else:
            return

        # Process the newly captured image.
        result = process_image(image_path, board_size="large")
        sudoku_string, solution = recognize_and_solve(result["cells"])

        print("\nSudoku board detected successfully!")
        print("Detected corners:")
        print(result["corners"])

        print("Rectified board:")
        print(result["warped_path"])

        print("Cell preview:")
        print(result["preview_path"])

        cv2.imshow("Rectified Sudoku Board", result["board_image"])
        cv2.imshow("Sudoku Grid Preview", cv2.imread(str(result["preview_path"])))

        print("\nPress any key to close the image windows.")
        cv2.waitKey(0)

        print("\nOriginal Sudoku:")
        print(format_board(sudoku_string))

        print("\nSolved Sudoku:")
        print(format_board(solution))

    finally:
        camera.release()
        cv2.destroyAllWindows()"""


if __name__ == "__main__":
    main()
