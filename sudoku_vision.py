
import argparse
from pathlib import Path

import cv2
import numpy as np

from project_paths import TEMPLATE_DIR, IMAGE_DIR, GENERATED_IMAGE_DIR
from sudoku_solver import format_board, solve_sudoku, is_valid_solution
from coordinate_transform import load_calibration, image_points_to_robot
from digit_classifier import train_classifier, predict_digit

BOARD_SIZES_MM = {
    "mini": (120.0, 120.0),
    "small": (150.0, 150.0),

}

# Maximum allowed relative difference between measured and expected board size.
BOARD_SIZE_TOLERANCE = 0.10

BOARD_PIXELS = 800
MACTH_THRESHOLD = 0.35  # Threshold for template matching

def order_corners(points):
    # Order of the corners: top-left, top, right, bottom right, bottom-left
    points = np.asarray(points, dtype=np.float32).reshape(4, 2)

    sums = points.sum(axis=1)
    diffs = np.diff(points, axis=1).reshape(-1)

    top_left = points[np.argmin(sums)]
    bottom_right = points[np.argmax(sums)]
    top_right = points[np.argmin(diffs)]
    bottom_left = points[np.argmax(diffs)]

    return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)

def get_board_cell_positions(corners):
    """Calculate the pixel coordinates of the center of each Sudoku cell."""

    positions = []

    for row in range(4):
        for col in range(4):

            # Calculate relative position inside the board
            u = (col + 0.5) / 4
            v = (row + 0.5) / 4

            # Interpolate between the four detected corners
            top = corners[0] * (1 - u) + corners[1] * u
            bottom = corners[3] * (1 - u) + corners[2] * u

            center = top * (1 - v) + bottom * v

            positions.append({
                "row": row + 1,
                "col": col + 1,
                "x": float(center[0]),
                "y": float(center[1])
            })

    return positions

def find_board_corners(image, board_size="auto", size_tolerance=BOARD_SIZE_TOLERANCE, calibration_matrix=None):

    if image is None or image.size == 0:
        raise ValueError("Could not read the image.")
    
    if size_tolerance < 0:
        raise ValueError("size_tolerance cannot be negative.")

    # Load camera calibration
    if calibration_matrix is None:
        calibration_matrix = load_calibration()

    calibration_matrix = np.asarray(calibration_matrix, dtype=np.float64)

    if calibration_matrix.shape != (3, 3):
        raise ValueError("Calibration matrix must have shape (3, 3).")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5),0) 

    edges = cv2.Canny(blurred, 40, 140)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    image_area = image.shape[0] * image.shape[1]
    candidates = []

    if board_size == "auto":
        expected_sizes = BOARD_SIZES_MM
    else: expected_sizes = {board_size: BOARD_SIZES_MM[board_size]}

     # Select expected board dimensions
    if board_size == "auto":
        expected_sizes = BOARD_SIZES_MM
    else:
        expected_sizes = {
            board_size: BOARD_SIZES_MM[board_size]
        }


    for contour in contours:
        area = cv2.contourArea(contour)

        if area < image_area * 0.01:
            continue

        perimiter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimiter, True)

        if len(approx) != 4 or not cv2.isContourConvex(approx):
            continue

        corners_px = order_corners(approx.reshape(4,2)) 
        
       # Convert pixel coordinates to robot coordinates in mm.
        try:
            corners_mm = np.asarray(
                image_points_to_robot(
                    corners_px,
                    calibration_matrix
                ),
                dtype=np.float64
            )
        except (ValueError, cv2.error):
            continue

        tl, tr, br, bl = corners_mm

        # Calculate physical width and height.
        width_mm = (
            np.linalg.norm(tr - tl) +
            np.linalg.norm(br - bl)
        ) / 2.0

        height_mm = (
            np.linalg.norm(bl - tl) +
            np.linalg.norm(br - tr)
        ) / 2.0

        if width_mm <= 0 or height_mm <= 0:
            continue

        # The Sudoku board should be approximately square.
        squareness_error = (
            abs(width_mm - height_mm) /
            max(width_mm, height_mm)
        )

        if squareness_error > 0.15:
            continue

        # Compare the measured dimensions with the expected dimensions.
        for size_name, (expected_width, expected_height) in expected_sizes.items():

            width_error = abs(width_mm - expected_width) / expected_width
            height_error = abs(height_mm - expected_height) / expected_height

            if ( width_error <= size_tolerance and height_error <= size_tolerance):

                size_error = (width_error + height_error) / 2.0

                score = size_error + squareness_error * 0.25

                candidates.append((
                    score,
                    area,
                    corners_px,
                    size_name,
                    width_mm,
                    height_mm
                ))

    if not candidates:
        expected_text = ", ".join(
            f"{name}: {width:g} x {height:g} mm"
            for name, (width, height) in expected_sizes.items()
            )

        raise RuntimeError(
                "Could not find a Sudoku board matching the configured physical size. "
                f"Expected {expected_text} "
                f"(tolerance {size_tolerance * 100:.0f}%). "
                "Check that the calibration file is correct and all four outer "
                "board corners are visible."
            )

    # Select the candidate closest to the expected physical dimensions.
    best = min(
        candidates,
        key=lambda item: (item[0], -item[1])
    )

    _, _, best_corners, detected_size, width_mm, height_mm = best

    print(
        f"Detected {detected_size} Sudoku board: "
        f"{width_mm:.1f} x {height_mm:.1f} mm"
    )

    return {
    "corners": best_corners,
    "board_size": detected_size,
    "width_mm": width_mm,
    "height_mm": height_mm
}



def rectify_board(image, corners, output_size=BOARD_PIXELS):
    destination = np.array([
        [0, 0],
        [output_size - 1, 0],
        [output_size - 1, output_size -1],
        [0, output_size - 1],
    ], dtype=np.float32)

    transform = cv2.getPerspectiveTransform(corners, destination)

    return cv2.warpPerspective(image, transform, (output_size, output_size))



def split_cells(board_image):
    heigth, width = board_image.shape[:2]


    """ ER DETTE NØDVENDIG????"""
    if heigth != width:
        raise ValueError("Rectified board must be square.")


    if heigth % 4 != 0:
            raise ValueError("Board image dimensions must be divisible by four.")

    cell_size = heigth // 4
    cells = []

    for row in range(4):
        cell_row = []

        for col in range(4):
            cell = board_image[
                row * cell_size:(row + 1) * cell_size,
                col * cell_size:(col + 1) * cell_size,
            ]
            cell_row.append(cell.copy())
        cells.append(cell_row)
    return cells


def make_grid_preview(board_image):
    # Visual inspection
    preview = board_image.copy()
    height, width = preview.shape[:2]

    for i in range(1, 4):
        x = round(i * width / 4)
        y = round(i * height / 4)

        thickness = 4 if i == 2 else 2

        # Vertical grid line
        cv2.line(preview, (x, 0), (x, height -1), (0, 0, 255), thickness)
        # Horizontal grid line
        cv2.line(preview, (0, y), (width -1, y), (0, 0, 255), thickness)
    return preview



def get_cell_centers(board_image):
    height, width = board_image.shape[:2]

    cell_width = width / 4
    cell_heigth = height / 4

    centers = []

    for row in range(4):
        for col in range(4):
            x = (col + 0.5) * cell_width
            y = (row + 0.5) * cell_heigth

            centers.append({
                "row": row + 1,
                "col": col + 1,
                "x": x,
                "y": y,

            })
    return centers



def normalize_digit(cell):
    """Extract and normalize a handwritten digit."""

    # Remove the cell borders
    height, width = cell.shape[:2]

    margin_x = int(width * 0.12)
    margin_y = int(height * 0.12)

    cell = cell[
        margin_y:height - margin_y,
        margin_x:width - margin_x
    ]

    # Convert to grayscale
    gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)

    # Threshold: black background, white handwriting
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    _, binary = cv2.threshold(
        blurred, 
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    # Find the area containing the handwriting
    points = cv2.findNonZero(binary)

    if points is None:
        raise ValueError("No digit found in cell.")

    x, y, w, h = cv2.boundingRect(points)

    digit = binary[y:y + h, x:x + w]

    # Resize while preserving the aspect ratio
    canvas_size = 64
    padding = 8

    scale = min(
        (canvas_size - 2 * padding) / w,
        (canvas_size - 2 * padding) / h
    )

    new_width = max(1, round(w * scale))
    new_height = max(1, round(h * scale))

    resized = cv2.resize(
        digit,
        (new_width, new_height),
        interpolation=cv2.INTER_AREA
    )

    # Place the digit in the center of a black canvas
    canvas = np.zeros((canvas_size, canvas_size), dtype=np.uint8)

    x_offset = (canvas_size - new_width) // 2
    y_offset = (canvas_size - new_height) // 2

    canvas[
        y_offset:y_offset + new_height,
        x_offset:x_offset + new_width
    ] = resized

    return canvas




def process_image(image_path, output_dir=None, board_size="auto"):
    image_path = Path(image_path).expanduser().resolve()
    image = cv2.imread(str(image_path))

    if image is None:
        raise FileNotFoundError(f'Could not load image: {image_path}')

    detection = find_board_corners(
    image,
    board_size=board_size
)

    corners = detection["corners"]
    detected_size = detection["board_size"]

    #Rotate the board 180 degrees to correct digit orientation
    rectified = rectify_board(image, corners, output_size=BOARD_PIXELS)
    cells = split_cells(rectified)

    # Save original and processed cells.
    cells_dir = GENERATED_IMAGE_DIR / "cells"
    processed_dir = GENERATED_IMAGE_DIR / "processed_cells"

    cells_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    for row in range(4):
        for col in range(4):

            cell = cells[row][col]

            # Save original cell.
            cell_path = cells_dir / f"cell_{row}_{col}.png"

            if not cv2.imwrite(str(cell_path), cell):
                raise OSError(f"Could not save cell: {cell_path}")

            # Save normalized cell.
            processed_path = (
                processed_dir / f"cell_{row}_{col}.png"
            )

            if is_empty_cell(cell):
                processed_cell = np.zeros((64, 64), dtype=np.uint8)
            else:
                processed_cell = normalize_digit(cell)

            if not cv2.imwrite(str(processed_path), processed_cell):
                raise OSError(
                    f"Could not save processed cell: {processed_path}"
                )


    destination_dir = Path(output_dir).expanduser().resolve() if output_dir else GENERATED_IMAGE_DIR
    destination_dir.mkdir(parents=True, exist_ok=True)
    warped_path = destination_dir / f'{image_path.stem}_board_warped.png'
    preview_path = destination_dir / f"{image_path.stem}_grid_preview.png"

    if not cv2.imwrite(str(warped_path), rectified):
        raise OSError(f'Could not save output image: {warped_path}')

    preview = make_grid_preview(rectified)

    if not cv2.imwrite(str(preview_path), preview):
        raise OSError(f"Could not save output image: {preview_path}")

    return {
        "board_image": rectified,
        "cells": cells,
        "corners": corners,
        "warped_path": warped_path,
        "preview_path": preview_path,
        "board_size": detected_size,
        "width_mm": detection["width_mm"],
        "height_mm": detection["height_mm"],
    }




"""
Number recognition
"""

def preprocess_cell(cell):
    "Prepare a sudoku cell for further analysis."

    # Convert cell to grayscale
    gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to reduce noise and improve thresholding
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # Convert to binary image (black or white - no gray tones)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    normalized = cv2.resize(binary, (64, 64), interpolation=cv2.INTER_AREA)

    # Remove gray vaøues introduced by resizing
    _, normalized_binary = cv2.threshold(normalized, 127, 255, cv2.THRESH_BINARY)
    return normalized_binary




### TESTING ###
def test_preprocess_cell(cell):
    """Display the original and preprocessed cell for comparison."""

    normalized = preprocess_cell(cell)

    cv2.imshow("Original cell", cell)
    cv2.imshow("Preprocessed cell", normalized)

    cv2.imwrite(str(GENERATED_IMAGE_DIR / "test_original.png"), cell)
    cv2.imwrite(str(GENERATED_IMAGE_DIR / "test_preprocessed.png"), normalized)

    print("Image size:", normalized.shape)
    print("Pixel values:", set(normalized.flatten()))

    cv2.waitKey(0)
    cv2.destroyAllWindows()



def is_empty_cell(cell):
    " Checks if a cell is empty."

    # Removed the cell boarders
    height, width = cell.shape[:2]

    margin_x = int(width * 0.12)
    margin_y = int(height * 0.12)

    cell = cell[margin_y:height - margin_y, margin_x:width - margin_x]

    binary = preprocess_cell(cell)  # Preprocess the cell to get a binary image

    # Count the number of white pixels in the binary image
    white_pixels = cv2.countNonZero(binary) 
    total_pixels = binary.size

    pixel_ratio = white_pixels / total_pixels # Calculate the ratio of white pixels to total pixels

    print(f"White pixel ratio: {pixel_ratio:.4f}")  # Debugging output

    return pixel_ratio < 0.05  # Adjust threshold as needed


def load_digit_templates():
    " Loading all digit templetes from the training data folder"

    templates = {}

    for digit in "1234":
        digit_folder = TEMPLATE_DIR / digit
        digit_templates = []

        for image_path in digit_folder.glob("*.png"):
            template = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)

            if template is None:
                raise OSError(f"Could not load template image: {image_path}")

            digit_templates.append(template)

        if not digit_templates:
            raise FileNotFoundError(f"No templates found for digit '{digit}' in {digit_folder}")

        templates[digit] = digit_templates
    return templates


def recognize_digit(cell, knn):

    digit_image = normalize_digit(cell)

    prediction, distances = predict_digit(
        digit_image,
        knn
    )

    return prediction




def recognize_board(cells, knn):

    sudoku_string = ""

    for row in range(4):
        for col in range(4):

            cell = cells[row][col]

            if is_empty_cell(cell):
                sudoku_string += "0"

            else:
                try:
                    digit = recognize_digit(cell, knn)
                    sudoku_string += digit

                except ValueError as error:
                    raise ValueError(
                        f"Recognition failed at "
                        f"row {row + 1}, column {col + 1}: {error}"
                    ) from error

    return sudoku_string


def recognize_and_solve(cells):
    """Recognize the Sudoku board and calculate its solution."""

    templates = load_digit_templates()

    # Recognize the numbers from the image.
    sudoku_string = recognize_board(cells, templates)

    print("\nRecognized Sudoku:")
    print(format_board(sudoku_string))

    # Calculate the solution.
    solution = solve_sudoku(sudoku_string)

    # Validate the solution.
    if not is_valid_solution(sudoku_string, solution):
        raise RuntimeError("The Sudoku solver returned an invalid solution.")

    print("\nSudoku solution:")
    print(format_board(solution))

    return sudoku_string, solution
    


def main():
    parser = argparse.ArgumentParser(
        description="Find and rectify a printed 4x4 Sudoku board."
    )

    parser.add_argument(
        "image",
        nargs="?",
        default=str(IMAGE_DIR / "sudoku_photo.jpg"),
        help="Path to the Sudoku photo",
    )

    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output folder (defaults to the photo folder)",
    )

    args = parser.parse_args()

    result = process_image(args.image, args.output_dir)

    templates = load_digit_templates()
    sudoku_string = recognize_board(result["cells"], templates)
 

    print("Recognized Sudoku: ")
    print(format_board(sudoku_string))



    #Center of each cell
    centers = get_cell_centers(result["board_image"])

    for cell in centers:
        print(cell)


    print(
        f"Board detected. Saved rectified board: "
        f"{result['warped_path']}"
    )
    print(f"Saved cell-grid preview: {result['preview_path']}")
    print(f"Split into {len(result['cells']) * len(result['cells'][0])} cells.")
    print("Digit recognition is not implemented yet.")

    
 

if __name__ == "__main__":
    main()