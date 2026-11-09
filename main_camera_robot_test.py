
"""
Camera-to-ABB test for the 4x4 Sudoku robot.

Test sequence:
1. Start Python TCP server and wait for ABB connection.
2. Start IDS camera.
3. Detect all four ArUco markers.
4. Capture one image containing both Sudoku boards.
5. Detect the MINI board (120 x 120 mm).
6. Detect the SMALL board (150 x 150 mm).
7. Calculate robot geometry for both boards.
8. Send SETBOARD for both boards.
9. Send all Sudoku digits to both boards.
10. Send PARK.

The Sudoku strings below are predefined test data.
Camera-based digit recognition and Sudoku solving are not performed here.
"""

import cv2

from project_paths import IMAGE_DIR
from camera_connection import IDSCamera

from aruco_calibration import (
    make_detector,
    detect_markers,
    REQUIRED_IDS,
)

from sudoku_vision import process_image
from coordinate_transform import board_geometry_from_corners
from robot_connection import RobotConnection


# --------------------------------------------------
# TEST SETTINGS
# --------------------------------------------------

SUDOKU_1 = "1341341341341341"
SUDOKU_2 = "1234123412341234"

CAMERA_ID = 2
ROBOT_CONNECT_TIMEOUT = 30

AXIS_ALIGNMENT_TOLERANCE_MM = 10.0

# Mapping between detected board size and RAPID board number.
# IMPORTANT: Confirm that this mapping matches your RAPID module.
BOARD_CONFIG = {
    "mini": {
        "robot_board": 1,
        "sudoku": SUDOKU_1,
    },
    "small": {
        "robot_board": 2,
        "sudoku": SUDOKU_2,
    },
}


# --------------------------------------------------
# GEOMETRY VALIDATION
# --------------------------------------------------

def validate_geometry_for_rapid(geometry):
    """
    Validate board orientation for RAPID.

    X decreases from left to right.
    Y increases from top to bottom.
    """

    corners = geometry["corners_robot"]

    if len(corners) != 4:
        raise ValueError("Expected four board corners.")

    tl, tr, br, bl = corners

    top_dx = tr[0] - tl[0]
    bottom_dx = br[0] - bl[0]

    left_dy = bl[1] - tl[1]
    right_dy = br[1] - tr[1]

    if top_dx >= 0 or bottom_dx >= 0:
        raise ValueError(
            "Board X direction does not match RAPID: "
            "X must decrease from left to right."
        )

    if left_dy <= 0 or right_dy <= 0:
        raise ValueError(
            "Board Y direction does not match RAPID: "
            "Y must increase from top to bottom."
        )

    if (
        abs(tl[1] - tr[1]) > AXIS_ALIGNMENT_TOLERANCE_MM
        or abs(bl[1] - br[1]) > AXIS_ALIGNMENT_TOLERANCE_MM
        or abs(tl[0] - bl[0]) > AXIS_ALIGNMENT_TOLERANCE_MM
        or abs(tr[0] - br[0]) > AXIS_ALIGNMENT_TOLERANCE_MM
    ):
        raise ValueError(
            "Board is rotated relative to wobjA3."
        )

    print("Board orientation validated successfully.")


# --------------------------------------------------
# CAMERA / BOARD DETECTION
# --------------------------------------------------

def detect_sudoku_boards(camera):
    """
    Capture one image and detect both Sudoku boards.

    Returns a dictionary containing the detection result
    and robot geometry for each board.
    """

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    image_path = IMAGE_DIR / "sudoku_photo.jpg"

    dictionary, parameters, detector = make_detector()

    print("\nIDS camera started.")
    print("Show BOTH Sudoku boards and all four ArUco markers.")
    print("Press C to capture when all markers are visible.")
    print("Press Q to cancel.")

    try:
        while True:

            ok, frame = camera.read()

            if not ok:
                raise RuntimeError(
                    "Could not read IDS camera."
                )

            found, marker_corners, ids = detect_markers(
                frame,
                dictionary,
                parameters,
                detector
            )

            display = frame.copy()

            if ids is not None:
                cv2.aruco.drawDetectedMarkers(
                    display,
                    marker_corners,
                    ids
                )

            missing = sorted(
                set(REQUIRED_IDS) - set(found)
            )

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
                print("Camera capture cancelled.")
                return None

            if key == ord("c"):

                if missing:
                    print(
                        "Cannot capture: ArUco markers are missing."
                    )
                    continue

                if not cv2.imwrite(str(image_path), frame):
                    raise OSError(
                        "Could not save camera image."
                    )

                print(f"Image saved: {image_path}")
                break

        # --------------------------------------------------
        # DETECT BOTH BOARD SIZES FROM THE SAME IMAGE
        # --------------------------------------------------

        results = {}

        for board_size in ("mini", "small"):

            print(
                f"\n========== DETECTING {board_size.upper()} =========="
            )

            result = process_image(
                image_path,
                board_size=board_size
            )

            print(
                f"Detected {board_size}: "
                f"{result['width_mm']:.1f} x "
                f"{result['height_mm']:.1f} mm"
            )

            print(f"{board_size} corners (pixels):")
            print(result["corners"])

            # Convert detected corners into robot coordinates.
            geometry = board_geometry_from_corners(
                result["corners"]
            )

            # Validate orientation before sending anything to RAPID.
            validate_geometry_for_rapid(geometry)

            print(
                f"\n{board_size.upper()} geometry in wobjA3:"
            )

            tl, tr, br, bl = geometry["corners_robot"]

            print(
                f"Top-left:     X={tl[0]:.2f}, Y={tl[1]:.2f}"
            )
            print(
                f"Top-right:    X={tr[0]:.2f}, Y={tr[1]:.2f}"
            )
            print(
                f"Bottom-right: X={br[0]:.2f}, Y={br[1]:.2f}"
            )
            print(
                f"Bottom-left:  X={bl[0]:.2f}, Y={bl[1]:.2f}"
            )

            print(
                f"Origin X: {geometry['origin_x']:.2f} mm"
            )
            print(
                f"Origin Y: {geometry['origin_y']:.2f} mm"
            )
            print(
                f"Cell width: {geometry['cell_width']:.2f} mm"
            )
            print(
                f"Cell height: {geometry['cell_height']:.2f} mm"
            )

            results[board_size] = {
                "result": result,
                "geometry": geometry,
            }

            # Display each detected and rectified board.
            cv2.imshow(
                f"{board_size.upper()} - Rectified Board",
                result["board_image"]
            )

            cv2.waitKey(500)

        print("\nBoth Sudoku boards detected successfully.")

        print(
            "\nInspect both rectified boards and their geometry."
        )
        print("Press any key in an image window to continue.")

        cv2.waitKey(0)

        return results

    finally:
        cv2.destroyAllWindows()


# --------------------------------------------------
# TCP COMMANDS
# --------------------------------------------------

def send_board_geometry(robot, board, geometry):
    """
    Send SETBOARD and require RAPID to acknowledge the update.
    """

    command = (
        f"SETBOARD {board} "
        f"{geometry['origin_x']:.2f} "
        f"{geometry['origin_y']:.2f} "
        f"{geometry['cell_width']:.2f} "
        f"{geometry['cell_height']:.2f}"
    )

    print(f"\nSending board geometry: {command}")

    reply = robot.send_line(command)

    if reply != "OK":
        raise RuntimeError(
            f"RAPID did not accept board geometry. "
            f"Command: {command!r}, response: {reply!r}"
        )

    print(
        f"RAPID confirmed geometry for board {board}."
    )


def send_sudoku(robot, board, sudoku):
    """
    Send WRITE commands for all non-empty cells.
    """

    if len(sudoku) != 16:
        raise ValueError(
            "Sudoku must contain exactly 16 digits."
        )

    if any(digit not in "01234" for digit in sudoku):
        raise ValueError(
            "Invalid Sudoku digit. Allowed digits are 0, 1, 2, 3, 4."
        )

    sent = 0

    for index, digit in enumerate(sudoku):

        if digit == "0":
            continue

        row, col = divmod(index, 4)

        command = (
            f"WRITE {board} "
            f"{row + 1} {col + 1} {digit}"
        )

        print(f"Sending: {command}")

        reply = robot.send_line(command)

        if reply != "OK":
            raise RuntimeError(
                f"Robot response to {command!r}: {reply!r}"
            )

        sent += 1

    print(
        f"Board {board}: {sent} digit(s) sent."
    )


def park_robot(robot):
    """
    Ask RAPID to move to its configured parking position.
    """

    print("\nSending PARK...")

    reply = robot.send_line("PARK")

    if reply != "OK":
        raise RuntimeError(
            f"Could not park robot. RAPID response: {reply!r}"
        )

    print("RAPID confirmed parking command.")


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    camera = None
    robot = RobotConnection()

    try:

        # --------------------------------------------------
        # CONNECT TO ABB
        # --------------------------------------------------

        print("Starting robot TCP server...")

        robot.start_server()

        print("Waiting for ABB robot connection...")

        if not robot.connected_event.wait(
            timeout=ROBOT_CONNECT_TIMEOUT
        ):
            raise TimeoutError(
                "ABB robot did not connect within "
                f"{ROBOT_CONNECT_TIMEOUT} seconds."
            )

        print("ABB robot connected.")

        # --------------------------------------------------
        # START CAMERA
        # --------------------------------------------------

        camera = IDSCamera(camera_id=CAMERA_ID)

        results = detect_sudoku_boards(camera)

        if results is None:
            print(
                "Camera capture cancelled. "
                "No WRITE commands sent."
            )
            return

        camera.release()
        camera = None

        cv2.destroyAllWindows()

        print("\nBoth board geometries detected successfully.")

        # --------------------------------------------------
        # SAFETY CHECK
        # --------------------------------------------------

        input(
            "\nSAFETY CHECK:\n"
            "- Confirm the robot area is clear.\n"
            "- Confirm both boards are fixed.\n"
            "- Confirm the pen and tool height are correct.\n"
            "- Confirm the emergency stop is accessible.\n"
            "- Confirm the board mapping in RAPID.\n\n"
            "Press ENTER to send both geometries and all digits..."
        )

        # --------------------------------------------------
        # SEND BOTH BOARD GEOMETRIES FIRST
        # --------------------------------------------------

        print("\n========== SENDING BOARD GEOMETRIES ==========")

        for board_size, config in BOARD_CONFIG.items():

            geometry = results[board_size]["geometry"]

            robot_board = config["robot_board"]

            print(
                f"\nUpdating {board_size} "
                f"(RAPID board {robot_board})"
            )

            send_board_geometry(
                robot,
                board=robot_board,
                geometry=geometry
            )

        # --------------------------------------------------
        # SEND ALL SUDOKU DIGITS
        # --------------------------------------------------

        print("\n========== WRITING BOTH BOARDS ==========")

        for board_size, config in BOARD_CONFIG.items():

            robot_board = config["robot_board"]
            sudoku = config["sudoku"]

            print(
                f"\n========== {board_size.upper()} BOARD =========="
            )

            send_sudoku(
                robot,
                board=robot_board,
                sudoku=sudoku
            )

        # --------------------------------------------------
        # PARK ROBOT
        # --------------------------------------------------

        park_robot(robot)

        print("\nBoth board tests completed successfully.")

    except Exception as exc:

        print(f"\nERROR: {exc}")
        raise

    finally:

        if camera is not None:
            camera.release()

        cv2.destroyAllWindows()
        robot.close()


if __name__ == "__main__":
    main()
