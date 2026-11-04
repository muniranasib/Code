
import argparse
from pathlib import Path

import cv2
import numpy as np
from sudoku_solver import format_board

BOARD_PIXELS = 800

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


def find_board_corners(image):

    if image is None or image.size == 0:
        raise ValueError("Could not read the image.")


    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5),0) 
    edges = cv2.Canny(blurred, 40, 140)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    image_area = image.shape[0] * image.shape[1]
    candidates = []

    for contour in contours:
        area = cv2.contourArea(contour)

        if area < image_area * 0.15:
            continue

        perimiter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimiter, True)

        if len(approx) == 4 and cv2.isContourConvex(approx):
            candidates.append((area, approx.reshape(4, 2)))

    if not candidates:
        raise RuntimeError("Could not find the Sudoku board. Take a clearer photo with all four outside corners visible and with good contrast")

    best_corners = max(candidates, key=lambda item: item[0])[1]
    
    return order_corners(best_corners)



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





def process_image(image_path, output_dir):
    image_path = Path(image_path).expanduser().resolve()
    image = cv2.imread(str(image_path))

    if image is None:
        raise FileNotFoundError(f'Could not load image: {image_path}')

    corners = find_board_corners(image)
    rectified = rectify_board(image, corners, output_size=BOARD_PIXELS)
    cells = split_cells(rectified)

    destination_dir = Path(output_dir).expanduser().resolve() if output_dir else image_path.parent
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

    cv2.imwrite("test_original.png", cell)
    cv2.imwrite("test_preprocessed.png", normalized)

    print("Image size:", normalized.shape)
    print("Pixel values:", set(normalized.flatten()))

    cv2.waitKey(0)
    cv2.destroyAllWindows()



def is_empty_cell(cell):
    " Checks if a cell is empty."
    "Returns True if the cell is empty, False otherwise."

    binary = preprocess_cell(cell)

    white_pixels = cv2.countNonZero(binary) # Count white cells
    total_pixels = binary.size

    pixel_ratio = white_pixels / total_pixels # Calculate the ratio of white pixels to total pixels

    print(f"White pixel ratio: {pixel_ratio:.4f}")  # Debugging output

    return pixel_ratio < 0.05  # Adjust threshold as needed


def recognize_digit(cell):
    "Identifies digit (1, 2, 3 or 4)"
    "Template Matching - algorithm"

    binary = preprocess_cell(cell)

    # This is a placeholder for the actual digit recognition logic.

    # Compare the preprocessed cell with templates for digits 1-4
    
    # Find the best maching template and return the corresponding digit.

    return "0"

def recognize_board(cells):
    "Recognizes all cells cells and builds a string representation of the board."

    sudoku_string = ""

    for row in range(4):
        for col in range(4):
            cell = cells[row][col]

            if is_empty_cell(cell):
                sudoku_string += "0"
            else:
                digit = recognize_digit(cell)
                sudoku_string += str(digit)

    return sudoku_string


    



def main():
    parser = argparse.ArgumentParser(
        description="Find and rectify a printed 4x4 Sudoku board."
    )

    parser.add_argument(
        "image",
        nargs="?",
        default="sudoku_photo.jpg",
        help="Path to the Sudoku photo",
    )

    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output folder (defaults to the photo folder)",
    )

    args = parser.parse_args()

    result = process_image(args.image, args.output_dir)

    ######TESTING######
    test_preprocess_cell(result["cells"][1][0])

    # Tester at alle cellene er tomme eller ikke
    for row in range(4):
        for col in range(4):
            empty = is_empty_cell(result["cells"][row][col])
            print(f"Row {row + 1}, Col {col + 1}: Empty = {empty}")

    #Tilbake til vanlig main-funksjon
    #ish
    sudoku_string = recognize_board(result["cells"])

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