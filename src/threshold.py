from pathlib import Path

from PIL import Image


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RESULTS_FOLDER = PROJECT_ROOT / "results"


# =========================================================
# TEST IMAGES
# =========================================================

TEST_IMAGES = [
    (
        RESULTS_FOLDER / "nic_genuine_01_grayscale.jpg",
        RESULTS_FOLDER / "nic_genuine_01_binary.png",
    ),
    (
        RESULTS_FOLDER / "nic_altered_01_grayscale.jpg",
        RESULTS_FOLDER / "nic_altered_01_binary.png",
    ),
]


# =========================================================
# BUILD PIXEL HISTOGRAM
# =========================================================

def build_histogram(image):
    """
    Count how many pixels exist for every grayscale
    brightness value from 0 to 255.
    """

    histogram = [0] * 256

    width, height = image.size

    pixels = image.load()

    for y in range(height):

        for x in range(width):

            value = pixels[x, y]

            histogram[value] += 1

    return histogram


# =========================================================
# CALCULATE AUTOMATIC THRESHOLD
# =========================================================

def calculate_automatic_threshold(histogram, total_pixels):
    """
    Calculate an automatic threshold using between-class
    variance.

    Dark pixels and light pixels are separated into two
    groups. The threshold producing the strongest separation
    is selected.
    """

    total_intensity = 0

    for intensity in range(256):

        total_intensity += (
            intensity * histogram[intensity]
        )


    background_weight = 0

    background_sum = 0

    highest_variance = -1

    best_threshold = 0


    for threshold in range(256):

        # ---------------------------------------------
        # BACKGROUND / DARK GROUP
        # ---------------------------------------------

        background_weight += histogram[threshold]

        if background_weight == 0:
            continue


        # ---------------------------------------------
        # FOREGROUND / LIGHT GROUP
        # ---------------------------------------------

        foreground_weight = (
            total_pixels - background_weight
        )

        if foreground_weight == 0:
            break


        # ---------------------------------------------
        # MEAN INTENSITY OF DARK GROUP
        # ---------------------------------------------

        background_sum += (
            threshold * histogram[threshold]
        )

        background_mean = (
            background_sum
            / background_weight
        )


        # ---------------------------------------------
        # MEAN INTENSITY OF LIGHT GROUP
        # ---------------------------------------------

        foreground_sum = (
            total_intensity - background_sum
        )

        foreground_mean = (
            foreground_sum
            / foreground_weight
        )


        # ---------------------------------------------
        # BETWEEN-CLASS VARIANCE
        # ---------------------------------------------

        mean_difference = (
            background_mean
            - foreground_mean
        )

        variance = (
            background_weight
            * foreground_weight
            * mean_difference
            * mean_difference
        )


        # ---------------------------------------------
        # KEEP BEST THRESHOLD
        # ---------------------------------------------

        if variance > highest_variance:

            highest_variance = variance

            best_threshold = threshold


    return best_threshold


# =========================================================
# CREATE BINARY IMAGE
# =========================================================

def create_binary_image(
    grayscale_image,
    threshold,
):
    """
    Convert grayscale pixels into black or white pixels.

    Pixel <= threshold:
        Black

    Pixel > threshold:
        White
    """

    width, height = grayscale_image.size

    grayscale_pixels = grayscale_image.load()


    binary_image = Image.new(
        "L",
        (width, height),
        255,
    )

    binary_pixels = binary_image.load()


    black_pixels = 0

    white_pixels = 0


    for y in range(height):

        for x in range(width):

            grayscale_value = (
                grayscale_pixels[x, y]
            )


            if grayscale_value <= threshold:

                binary_pixels[x, y] = 0

                black_pixels += 1


            else:

                binary_pixels[x, y] = 255

                white_pixels += 1


    return (
        binary_image,
        black_pixels,
        white_pixels,
    )


# =========================================================
# PROCESS ONE IMAGE
# =========================================================

def process_image(
    input_path,
    output_path,
):

    # -----------------------------------------------------
    # CHECK INPUT FILE
    # -----------------------------------------------------

    if not input_path.exists():

        print()
        print("ERROR: Input image not found.")
        print(f"Expected location: {input_path}")

        return False


    # -----------------------------------------------------
    # OPEN GRAYSCALE IMAGE
    # -----------------------------------------------------

    with Image.open(input_path) as source_image:

        grayscale_image = source_image.convert("L")

        width, height = grayscale_image.size

        total_pixels = width * height


        if total_pixels <= 0:

            print("ERROR: Invalid image.")

            return False


        # -------------------------------------------------
        # BUILD HISTOGRAM
        # -------------------------------------------------

        histogram = build_histogram(
            grayscale_image
        )


        # -------------------------------------------------
        # FIND AUTOMATIC THRESHOLD
        # -------------------------------------------------

        threshold = (
            calculate_automatic_threshold(
                histogram,
                total_pixels,
            )
        )


        # -------------------------------------------------
        # CREATE BINARY IMAGE
        # -------------------------------------------------

        (
            binary_image,
            black_pixels,
            white_pixels,

        ) = create_binary_image(
            grayscale_image,
            threshold,
        )


        # -------------------------------------------------
        # SAVE RESULT
        # -------------------------------------------------

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        binary_image.save(
            output_path
        )


        # -------------------------------------------------
        # CALCULATE PIXEL RATIOS
        # -------------------------------------------------

        black_ratio = (
            black_pixels
            / total_pixels
        ) * 100

        white_ratio = (
            white_pixels
            / total_pixels
        ) * 100


        # -------------------------------------------------
        # DISPLAY RESULT
        # -------------------------------------------------

        print()
        print("========================================")
        print("BINARY CONVERSION COMPLETE")
        print("========================================")

        print(
            f"Input file:     {input_path.name}"
        )

        print(
            f"Output file:    {output_path.name}"
        )

        print(
            f"Image size:     {width} x {height}"
        )

        print(
            f"Threshold:      {threshold}"
        )

        print(
            f"Black pixels:   {black_pixels}"
        )

        print(
            f"White pixels:   {white_pixels}"
        )

        print(
            f"Black ratio:    {black_ratio:.2f}%"
        )

        print(
            f"White ratio:    {white_ratio:.2f}%"
        )

        print("========================================")


    return True


# =========================================================
# MAIN PROGRAM
# =========================================================

def main():

    print()
    print(
        "Document Alteration Detection Module"
    )

    print(
        "Step 4 - Automatic Thresholding"
    )


    successful = 0


    for input_path, output_path in TEST_IMAGES:

        result = process_image(
            input_path,
            output_path,
        )

        if result:
            successful += 1


    print()

    print(
        f"Successfully processed "
        f"{successful}/{len(TEST_IMAGES)} images."
    )


if __name__ == "__main__":
    main()