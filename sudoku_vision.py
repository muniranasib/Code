



import argparse
from pathlib import Path

import cv2
import numpy as np


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