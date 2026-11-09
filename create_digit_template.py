
import cv2
from pathlib import Path

from sudoku_vision import process_image, normalize_digit

from project_paths import (
    TRAINING_IMAGE_DIR,
    TRAINING_GENERATED_IMAGE_DIR,
    TEMPLATE_DIR,
)


"""
Create digit templates from training images.

Input:
    training_data/images/

Generated images:
    training_data/images/generated_images/

Digit templates:
    training_data/digit_templates/
"""


# Positions and corresponding digits in the two images.
# Row and column start at 0.

SAMPLES = {
    "image_for_digit_template_1.jpeg": {
        (0, 1): "4",
        (0, 3): "1",
        (1, 0): "2",
        (2, 2): "4",
        (3, 0): "4",
        (3, 1): "2",
        (3, 2): "4",
        (3, 3): "3",
    },

    "image_for_digit_template_2.jpeg": {
        (0, 2): "1",
        (0, 3): "3",
        (1, 1): "1",
        (1, 2): "2",
        (2, 0): "4",
        (2, 3): "1",
        (3, 0): "1",
        (3, 1): "3",
    },
}


def create_templates(overwrite=False):
    """Create digit templates from Sudoku training images."""

    # Create folders for each digit
    for digit in "1234":
        digit_folder = TEMPLATE_DIR / digit
        digit_folder.mkdir(parents=True, exist_ok=True)

    saved = {digit: 0 for digit in "1234"}

    for image_name, samples in SAMPLES.items():

        print(f"\nProcessing {image_name}")

        # Load original training image
        image_path = TRAINING_IMAGE_DIR / image_name

        if not image_path.exists():
            raise FileNotFoundError(
                f"Training image not found: {image_path}"
            )

        # Detect and rectify the Sudoku board
        result = process_image(
            image_path,
            output_dir=TRAINING_GENERATED_IMAGE_DIR
        )

        cells = result["cells"]

        for (row, col), digit in samples.items():

            # Validate digit label
            if digit not in "1234":
                raise ValueError(
                    f"Invalid label {digit!r}; expected 1, 2, 3 or 4."
                )

            # Validate cell coordinates
            if not (0 <= row < 4 and 0 <= col < 4):
                raise ValueError(
                    f"Invalid cell coordinate: {(row, col)}"
                )

            # Get corresponding cell
            cell = cells[row][col]

            # Normalize handwritten digit
            template = normalize_digit(cell)

            # Create digit folder
            digit_folder = TEMPLATE_DIR / digit
            digit_folder.mkdir(parents=True, exist_ok=True)

            # Create template filename
            filename = (
                f"{Path(image_name).stem}"
                f"_r{row}_c{col}.png"
            )

            save_path = digit_folder / filename

            # Skip existing templates unless overwrite=True
            if save_path.exists() and not overwrite:
                print(f"Template already exists: {save_path}")
                continue

            # Save template
            if not cv2.imwrite(str(save_path), template):
                raise OSError(
                    f"Could not save template: {save_path}"
                )

            saved[digit] += 1

            print(f"Saved digit {digit}: {save_path}")

    # Display template overview
    print("\nTemplates overview:")

    for digit in "1234":
        digit_folder = TEMPLATE_DIR / digit
        templates = list(digit_folder.glob("*.png"))

        print(
            f"Digit {digit}: {len(templates)} template(s) "
            f"(new this run: {saved[digit]})"
        )


def create_templates_robot(overwrite=False):
    """Create digit templates from robot-written digits on paper."""

    # Create folders for each digit
    for digit in "1234":
        (TEMPLATE_DIR / digit).mkdir(
            parents=True,
            exist_ok=True
        )

    # Original robot-written training image
    sheet_names = ["robot_writing_copy.jpg"]

    # Two columns for each digit
    digit_columns = {
        "1": [0, 1],
        "2": [2, 3],
        "3": [4, 5],
        "4": [6, 7],
    }

    saved = {digit: 0 for digit in "1234"}

    for image_name in sheet_names:

        print(f"\nProcessing {image_name}")

        # Load original image
        image_path = TRAINING_IMAGE_DIR / image_name

        if not image_path.exists():
            raise FileNotFoundError(
                f"Training image not found: {image_path}"
            )

        image = cv2.imread(str(image_path))

        if image is None:
            raise ValueError(
                f"Could not read image: {image_path}"
            )

        sheet = image.copy()

        height, width = sheet.shape[:2]

        # Preview of the 5 x 8 grid
        preview = sheet.copy()

        for row in range(5):
            for col in range(8):

                x1 = round(col * width / 8)
                x2 = round((col + 1) * width / 8)

                y1 = round(row * height / 5)
                y2 = round((row + 1) * height / 5)

                cv2.rectangle(
                    preview,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

        # Save grid preview
        preview_path = (
            TRAINING_GENERATED_IMAGE_DIR
            / f"{Path(image_name).stem}_grid_preview.png"
        )

        if not cv2.imwrite(str(preview_path), preview):
            raise OSError(
                f"Could not save preview: {preview_path}"
            )

        print(f"Saved grid preview: {preview_path}")

        # Extract all 40 cells
        for row in range(5):

            for digit, columns in digit_columns.items():

                for col in columns:

                    # Calculate cell coordinates
                    x1 = round(col * width / 8)
                    x2 = round((col + 1) * width / 8)

                    y1 = round(row * height / 5)
                    y2 = round((row + 1) * height / 5)

                    cell = sheet[y1:y2, x1:x2]

                    if cell.size == 0:
                        raise ValueError(
                            f"Empty cell at row {row}, column {col}"
                        )

                    # Normalize digit
                    template = normalize_digit(cell)

                    # Create filename
                    filename = (
                        f"{Path(image_name).stem}"
                        f"_r{row}_c{col}.png"
                    )

                    digit_folder = TEMPLATE_DIR / digit
                    save_path = digit_folder / filename

                    # Skip existing templates unless overwrite=True
                    if save_path.exists() and not overwrite:
                        print(f"Template already exists: {save_path}")
                        continue

                    # Save template
                    if not cv2.imwrite(str(save_path), template):
                        raise OSError(
                            f"Could not save template: {save_path}"
                        )

                    saved[digit] += 1

                    print(f"Saved digit {digit}: {filename}")

    # Display template overview
    print("\nRobot templates overview:")

    for digit in "1234":

        digit_folder = TEMPLATE_DIR / digit
        templates = list(digit_folder.glob("*.png"))

        print(
            f"Digit {digit}: {len(templates)} templates "
            f"(new this run: {saved[digit]})"
        )

    print("\nRobot template creation completed.")


if __name__ == "__main__":

    create_templates(overwrite=True)

    create_templates_robot(overwrite=True)
