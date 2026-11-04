
from pathlib import Path
import cv2


from sudoku_vision import process_image, normalize_digit

""" createing the code to create digit templates from the images of sudoku boards.
The templates will be used for digit recognition in the Sudoku solver application. 
Each digit will have its own folder containing the corresponding templates."""


# Folder for saving the digit templates and data images
BASE_DIR = Path(__file__).resolve().parent

TRAING_DATA_DIR = BASE_DIR / "training_data"
IMAGE_DIR = TRAING_DATA_DIR / "images"
TEMPLATE_DIR = TRAING_DATA_DIR / "digit_templates"


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




def create_templates():    
    # Create folders for each digit
    for digit in "1234":
        digit_folder = TEMPLATE_DIR / digit
        digit_folder.mkdir(parents=True, exist_ok=True)

    for image_name, samples in SAMPLES.items():

        print(f"\nProcessing {image_name}")

        # Detect and rectify the Sudoku board
        image_path = IMAGE_DIR / image_name
        if not image_path.exists():
            raise FileNotFoundError(f"Training image not found: {image_path}")

        result = process_image(str(image_path), None)
        cells = result["cells"]

        for (row, col), digit in samples.items():

            # Get the corresponding cell
            cell = cells[row][col]

            # Normalize the handwritten digit
            template = normalize_digit(cell)

            # Create folder for this digit
            digit_folder = TEMPLATE_DIR / digit
            digit_folder.mkdir(parents=True, exist_ok=True)

            # Save template
            filename = (
                f"{Path(image_name).stem}"
                f"_r{row}_c{col}.png"
            )

            save_path = digit_folder / filename

            # Skip saving for existing templates
            if save_path.exists():
                print(f"Template already exists: {save_path}")
                continue

            # Save the template image
            if not cv2.imwrite(str(save_path), template):
                raise OSError(f"Could not save template: {save_path}")

            print(f"Saved digit {digit}: {save_path}")

    print("\nTemplates overview:")

    for digit in "1234":
        digit_folder = TEMPLATE_DIR / digit
        templates = list(digit_folder.glob("*.png"))

        print(f"Digit {digit}: {len(templates)} template(s) saved.")


if __name__ == "__main__":
    create_templates()
