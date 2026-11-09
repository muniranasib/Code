"""
Live IDS-camera test for the 4x4 Sudoku digit recognition pipeline.

Run from the project root:
    python test_camera_recognition.py

Controls:
    C = capture the current frame and run recognition
    Q = quit

The camera is the overhead IDS uEye camera (camera_id=2), matching main.py.
All four ArUco markers (IDs 0, 1, 2, 3) must be visible before capture.
"""

from pathlib import Path
import cv2

from project_paths import IMAGE_DIR, GENERATED_IMAGE_DIR
from camera_connection import IDSCamera
from aruco_calibration import (
    make_detector,
    detect_markers,
    REQUIRED_IDS,
)
from sudoku_vision import (
    process_image,
    is_empty_cell,
    recognize_digit,
    normalize_digit,
)
from digit_classifier import train_classifier


CAMERA_ID = 2
BOARD_SIZE = "large"  # Change to "small" if your physical board is 150 x 150 mm.


def main():
    # Give a useful message for common OpenCV installation problems.
    if not hasattr(cv2, "aruco"):
        raise RuntimeError(
            "cv2.aruco is missing. Install opencv-contrib-python."
        )

    if not hasattr(cv2, "HOGDescriptor"):
        raise RuntimeError(
            "cv2.HOGDescriptor is missing. Your OpenCV installation is "
            "incomplete or conflicting. Reinstall opencv-contrib-python "
            "in the same Python environment."
        )

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    output_dir = GENERATED_IMAGE_DIR / "camera_recognition_test"
    output_dir.mkdir(parents=True, exist_ok=True)

    captured_image_path = IMAGE_DIR / "sudoku_camera_test.jpg"

    dictionary, parameters, detector = make_detector()
    camera = None

    try:
        print(f"Opening overhead IDS camera (camera_id={CAMERA_ID})...")
        camera = IDSCamera(camera_id=CAMERA_ID)

        print("\nLive camera started.")
        print("Place the Sudoku board under the camera.")
        print("Make sure ArUco markers 0, 1, 2 and 3 are visible.")
        print("Press C to capture and recognize, or Q to quit.\n")

        while True:
            ok, frame = camera.read()

            if not ok or frame is None:
                raise RuntimeError("Could not read image from IDS camera.")

            found, marker_corners, marker_ids = detect_markers(
                frame, dictionary, parameters, detector
            )

            display = frame.copy()

            if marker_ids is not None:
                cv2.aruco.drawDetectedMarkers(
                    display, marker_corners, marker_ids
                )

            missing = sorted(set(REQUIRED_IDS) - set(found))

            if not missing:
                status = "All markers found - press C to capture"
                color = (0, 255, 0)
            else:
                status = f"Missing ArUco IDs: {missing}"
                color = (0, 0, 255)

            cv2.putText(
                display,
                status,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                color,
                2,
            )

            # Resize only the preview, not the image saved for processing.
            preview = cv2.resize(
                display, None, fx=0.5, fy=0.5,
                interpolation=cv2.INTER_AREA
            )
            cv2.imshow("Overhead IDS camera - Sudoku recognition test", preview)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                print("Test cancelled.")
                return

            if key == ord("c"):
                if missing:
                    print(
                        "Capture blocked: all four ArUco markers must be "
                        f"visible. Missing: {missing}"
                    )
                    continue

                if not cv2.imwrite(str(captured_image_path), frame):
                    raise OSError(
                        f"Could not save camera image: {captured_image_path}"
                    )

                print(f"\nCaptured image: {captured_image_path}")
                break

        cv2.destroyAllWindows()

        # Train the HOG + KNN classifier once for this test run.
        print("\nTraining digit classifier from digit templates...")
        knn = train_classifier()
        print("Classifier ready.")

        # Run the same Sudoku vision pipeline used by the application.
        print("\nDetecting and rectifying Sudoku board...")
        result = process_image(
            captured_image_path,
            output_dir=output_dir,
            board_size=BOARD_SIZE,
        )

        print("[OK] Sudoku board detected and split into cells.")

        # Recognize every cell separately. An error in one cell should not
        # prevent us from seeing the results for the other 15 cells.
        print("\nRecognizing digits...")
        recognized = []

        for row in range(4):
            recognized_row = []

            for col in range(4):
                cell = result["cells"][row][col]
                cell_name = f"row {row + 1}, column {col + 1}"

                try:
                    if is_empty_cell(cell):
                        digit = "0"
                    else:
                        digit = recognize_digit(cell, knn)

                    print(f"[OK] {cell_name}: {digit}")

                except Exception as error:
                    digit = "?"
                    print(
                        f"[ERROR] {cell_name}: "
                        f"{type(error).__name__}: {error}"
                    )

                recognized_row.append(digit)

                # Save the normalized cell for visual debugging.
                try:
                    normalized = (
                        normalize_digit(cell)
                        if digit != "0" and digit != "?"
                        else cv2.resize(
                            cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY),
                            (64, 64)
                        ) if digit == "?"
                        else cv2.cvtColor(
                            cell, cv2.COLOR_BGR2GRAY
                        )
                    )
                    cv2.imwrite(
                        str(output_dir / f"cell_r{row + 1}_c{col + 1}.png"),
                        normalized,
                    )
                except Exception:
                    pass

            recognized.append(recognized_row)

        sudoku_string = "".join(
            digit for row in recognized for digit in row
        )

        print("\nRecognized Sudoku (0 = empty, ? = error):")
        for row in recognized:
            print(" ".join(row))

        print(f"\nSudoku string: {sudoku_string}")
        print(f"Rectified board saved to: {result['warped_path']}")
        print(f"Grid preview saved to: {result['preview_path']}")
        print(f"Recognition debug images: {output_dir}")

        # Show the processed board for visual inspection.
        cv2.imshow("Rectified Sudoku board", result["board_image"])
        cv2.waitKey(0)

    finally:
        if camera is not None:
            camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
