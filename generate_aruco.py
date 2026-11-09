"Generate a printable A4 sheet with four ArUco reference markers (IDs 0-3)."

from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw

from project_paths import GENERATED_IMAGE_DIR

OUT = GENERATED_IMAGE_DIR / "aruco_calibration_sheet_4tags.png"

DICT_NAME = "DICT_4X4_50"
MARKER_IDS = [0, 1, 2, 3]
MARKER_SIZE_MM = 40
DPI = 300
PAGE_W_MM, PAGE_H_MM = 297, 210  # A4 landscape
MARGIN_MM = 18

def mm_to_px(mm):
    return round(mm * DPI / 25.4)

def main():
    if not hasattr(cv2, "aruco"):
        raise RuntimeError("cv2.aruco mangler. Installer opencv-contrib-python.")

    aruco = cv2.aruco
    dictionary = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
    page = Image.new("RGB", (mm_to_px(PAGE_W_MM), mm_to_px(PAGE_H_MM)), "white")
    draw = ImageDraw.Draw(page)
    marker_px = mm_to_px(MARKER_SIZE_MM)

    # Four markers near the four corners of the A4 sheet.
    # For calibration, place/attach each marker so its CENTRE coincides with
    # the corresponding known reference point, or measure its centre position.
    positions = [
        (MARGIN_MM, MARGIN_MM),
        (PAGE_W_MM - MARGIN_MM - MARKER_SIZE_MM, MARGIN_MM),
        (PAGE_W_MM - MARGIN_MM - MARKER_SIZE_MM, PAGE_H_MM - MARGIN_MM - MARKER_SIZE_MM),
        (MARGIN_MM, PAGE_H_MM - MARGIN_MM - MARKER_SIZE_MM),
    ]

    for marker_id, (x_mm, y_mm) in zip(MARKER_IDS, positions):
        if hasattr(aruco, "generateImageMarker"):
            marker = aruco.generateImageMarker(dictionary, marker_id, marker_px)
        else:
            marker = np.zeros((marker_px, marker_px), dtype=np.uint8)
            aruco.drawMarker(dictionary, marker_id, marker_px, marker, 1)
        page.paste(Image.fromarray(marker).convert("RGB"), (mm_to_px(x_mm), mm_to_px(y_mm)))
        draw.text((mm_to_px(x_mm), mm_to_px(y_mm + MARKER_SIZE_MM + 2)), f"ID {marker_id}", fill="black")

    draw.text((mm_to_px(18), mm_to_px(105)),
              "ArUco DICT_4X4_50 | IDs 0-3 | marker side 40 mm | print at 100%",
              fill="black")
    page.save(OUT, dpi=(DPI, DPI))
    print(f"Saved: {OUT}")
if __name__ == "__main__":
    main()
