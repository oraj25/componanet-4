from pathlib import Path

from PIL import Image


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FOLDER = PROJECT_ROOT / "data"
RESULTS_FOLDER = PROJECT_ROOT / "results"


# =========================================================
# TEST IMAGES
# =========================================================

TEST_IMAGES = [
    (
        DATA_FOLDER / "genuine" / "nic_genuine_01.jpg",
        RESULTS_FOLDER / "nic_genuine_01_grayscale.jpg",
    ),
    (
        DATA_FOLDER / "altered" / "nic_altered_01.jpg",
        RESULTS_FOLDER / "nic_altered_01_grayscale.jpg",
    ),
]


# =========================================================
# MANUAL RGB TO GRAYSCALE CALCULATION
# =========================================================

def calculate_grayscale_value(red, green, blue):
    """
    Convert one RGB pixel into one grayscale brightness value.

    The calculation gives different importance to each colour
    because the human eye does not perceive red, green, and blue
    with equal brightness.

    Output range:
        0   = black
        255 = white
    """

    grayscale_value = (
        (0.299 * red)
        + (0.587 * green)
        + (0.114 * blue)
    )

    grayscale_value = round(grayscale_value)

    # Ensure the result remains inside the valid 0-255 range.
    if grayscale_value < 0:
        grayscale_value = 0

    if grayscale_value > 255:
        grayscale_value = 255

    return grayscale_value


# =========================================================
# MANUAL IMAGE GRAYSCALE CONVERSION
# =========================================================

def convert_image_to_grayscale(input_path, output_path):
    """
    Load an image, manually calculate the grayscale value of
    every pixel, and save the resulting grayscale image.

    Pillow is used only for:
        - opening the image
        - accessing pixels
        - creating the output image
        - saving the image

    The grayscale calculation itself is implemented by us.
    """

    # -----------------------------------------------------
    # CHECK INPUT FILE
    # -----------------------------------------------------

    if not input_path.exists():
        print()
        print("ERROR: Input image was not found.")
        print(f"Expected location: {input_path}")
        return False


    # -----------------------------------------------------
    # OPEN IMAGE
    # -----------------------------------------------------

    with Image.open(input_path) as source_image:

        # JPEG images should normally be RGB.
        # This ensures that each pixel contains R, G and B values.
        rgb_image = source_image.convert("RGB")

        width, height = rgb_image.size


        # -------------------------------------------------
        # VALIDATE IMAGE SIZE
        # -------------------------------------------------

        if width <= 0 or height <= 0:
            print()
            print("ERROR: Invalid image dimensions.")
            return False


        # -------------------------------------------------
        # CREATE EMPTY GRAYSCALE IMAGE
        # -------------------------------------------------

        grayscale_image = Image.new(
            "L",
            (width, height),
        )


        # -------------------------------------------------
        # ACCESS PIXEL DATA
        # -------------------------------------------------

        source_pixels = rgb_image.load()
        grayscale_pixels = grayscale_image.load()


        # -------------------------------------------------
        # PROCESS EVERY PIXEL
        # -------------------------------------------------

        for y in range(height):

            for x in range(width):

                red, green, blue = source_pixels[x, y]

                grayscale_value = calculate_grayscale_value(
                    red,
                    green,
                    blue,
                )

                grayscale_pixels[x, y] = grayscale_value


        # -------------------------------------------------
        # CREATE RESULTS FOLDER IF REQUIRED
        # -------------------------------------------------

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )


        # -------------------------------------------------
        # SAVE RESULT
        # -------------------------------------------------

        grayscale_image.save(output_path)


        # -------------------------------------------------
        # DISPLAY INFORMATION
        # -------------------------------------------------

        centre_x = width // 2
        centre_y = height // 2

        original_centre_pixel = source_pixels[
            centre_x,
            centre_y,
        ]

        grayscale_centre_pixel = grayscale_pixels[
            centre_x,
            centre_y,
        ]


        print()
        print("========================================")
        print("GRAYSCALE CONVERSION COMPLETE")
        print("========================================")
        print(f"Input file:  {input_path.name}")
        print(f"Output file: {output_path.name}")
        print(f"Width:       {width}")
        print(f"Height:      {height}")
        print(f"Pixels:      {width * height}")
        print()
        print(
            "Original centre RGB pixel:",
            original_centre_pixel,
        )
        print(
            "Grayscale centre value:",
            grayscale_centre_pixel,
        )
        print("========================================")

    return True


# =========================================================
# MAIN PROGRAM
# =========================================================

def main():

    print()
    print("Document Alteration Detection Module")
    print("Step 3 - Manual Grayscale Conversion")

    success_count = 0

    for input_path, output_path in TEST_IMAGES:

        success = convert_image_to_grayscale(
            input_path,
            output_path,
        )

        if success:
            success_count += 1


    print()
    print(
        f"Successfully processed "
        f"{success_count}/{len(TEST_IMAGES)} images."
    )


if __name__ == "__main__":
    main()