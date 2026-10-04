from pathlib import Path
from math import sqrt

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
        RESULTS_FOLDER / "nic_genuine_01_edges.png",
    ),
    (
        RESULTS_FOLDER / "nic_altered_01_grayscale.jpg",
        RESULTS_FOLDER / "nic_altered_01_edges.png",
    ),
]


# =========================================================
# SOBEL KERNELS
# =========================================================

SOBEL_X = [
    [-1, 0, 1],
    [-2, 0, 2],
    [-1, 0, 1],
]

SOBEL_Y = [
    [-1, -2, -1],
    [0, 0, 0],
    [1, 2, 1],
]


# =========================================================
# CALCULATE GRADIENT AT ONE PIXEL
# =========================================================

def calculate_gradient(pixels, x, y):
    """
    Calculate horizontal and vertical intensity changes
    around one pixel using manually implemented Sobel
    calculations.
    """

    gradient_x = 0
    gradient_y = 0

    for kernel_y in range(3):

        for kernel_x in range(3):

            image_x = x + kernel_x - 1
            image_y = y + kernel_y - 1

            pixel_value = pixels[
                image_x,
                image_y,
            ]

            gradient_x += (
                pixel_value
                * SOBEL_X[kernel_y][kernel_x]
            )

            gradient_y += (
                pixel_value
                * SOBEL_Y[kernel_y][kernel_x]
            )

    magnitude = sqrt(
        (gradient_x * gradient_x)
        +
        (gradient_y * gradient_y)
    )

    return magnitude


# =========================================================
# CALCULATE AUTOMATIC EDGE THRESHOLD
# =========================================================

def calculate_edge_threshold(
    gradient_values,
):
    """
    Calculate an adaptive edge threshold using the
    mean and standard deviation of gradient magnitudes.
    """

    if not gradient_values:
        return 0


    # -----------------------------------------------------
    # MEAN
    # -----------------------------------------------------

    total = 0

    for value in gradient_values:
        total += value

    mean = total / len(gradient_values)


    # -----------------------------------------------------
    # VARIANCE
    # -----------------------------------------------------

    variance_total = 0

    for value in gradient_values:

        difference = value - mean

        variance_total += (
            difference * difference
        )

    variance = (
        variance_total
        / len(gradient_values)
    )


    # -----------------------------------------------------
    # STANDARD DEVIATION
    # -----------------------------------------------------

    standard_deviation = sqrt(
        variance
    )


    # -----------------------------------------------------
    # THRESHOLD
    # -----------------------------------------------------

    threshold = (
        mean + standard_deviation
    )


    # Keep threshold within a useful range.
    if threshold < 30:
        threshold = 30

    if threshold > 200:
        threshold = 200


    return threshold


# =========================================================
# EDGE DETECTION
# =========================================================

def detect_edges(
    grayscale_image,
):
    """
    Detect strong image boundaries using our own
    Sobel gradient calculations.
    """

    width, height = grayscale_image.size

    source_pixels = grayscale_image.load()


    # -----------------------------------------------------
    # STORE GRADIENT VALUES
    # -----------------------------------------------------

    gradient_map = [
        [0.0 for _ in range(width)]
        for _ in range(height)
    ]

    gradient_values = []


    # -----------------------------------------------------
    # CALCULATE GRADIENT FOR EACH NON-BORDER PIXEL
    # -----------------------------------------------------

    for y in range(1, height - 1):

        for x in range(1, width - 1):

            magnitude = calculate_gradient(
                source_pixels,
                x,
                y,
            )

            gradient_map[y][x] = magnitude

            gradient_values.append(
                magnitude
            )


    # -----------------------------------------------------
    # CALCULATE AUTOMATIC THRESHOLD
    # -----------------------------------------------------

    threshold = calculate_edge_threshold(
        gradient_values
    )


    # -----------------------------------------------------
    # CREATE EDGE IMAGE
    # -----------------------------------------------------

    edge_image = Image.new(
        "L",
        (width, height),
        0,
    )

    edge_pixels = edge_image.load()


    edge_count = 0


    for y in range(1, height - 1):

        for x in range(1, width - 1):

            magnitude = gradient_map[y][x]


            if magnitude >= threshold:

                edge_pixels[x, y] = 255

                edge_count += 1


            else:

                edge_pixels[x, y] = 0


    return (
        edge_image,
        threshold,
        edge_count,
    )


# =========================================================
# PROCESS ONE IMAGE
# =========================================================

def process_image(
    input_path,
    output_path,
):

    # -----------------------------------------------------
    # CHECK FILE
    # -----------------------------------------------------

    if not input_path.exists():

        print()
        print("ERROR: Grayscale image not found.")
        print(f"Expected location: {input_path}")

        return False


    # -----------------------------------------------------
    # OPEN IMAGE
    # -----------------------------------------------------

    with Image.open(input_path) as source_image:

        grayscale_image = source_image.convert(
            "L"
        )

        width, height = grayscale_image.size


        if width < 3 or height < 3:

            print(
                "ERROR: Image is too small "
                "for edge detection."
            )

            return False


        # -------------------------------------------------
        # DETECT EDGES
        # -------------------------------------------------

        (
            edge_image,
            threshold,
            edge_count,

        ) = detect_edges(
            grayscale_image
        )


        # -------------------------------------------------
        # SAVE RESULT
        # -------------------------------------------------

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        edge_image.save(
            output_path
        )


        # -------------------------------------------------
        # STATISTICS
        # -------------------------------------------------

        analysed_pixels = (
            (width - 2)
            *
            (height - 2)
        )


        edge_ratio = (
            edge_count
            / analysed_pixels
        ) * 100


        # -------------------------------------------------
        # DISPLAY RESULT
        # -------------------------------------------------

        print()
        print("========================================")
        print("EDGE DETECTION COMPLETE")
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
            f"Edge threshold: {threshold:.2f}"
        )

        print(
            f"Edge pixels:    {edge_count}"
        )

        print(
            f"Edge ratio:     {edge_ratio:.2f}%"
        )

        print("========================================")


    return True


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print(
        "Document Alteration Detection Module"
    )

    print(
        "Step 5 - Manual Sobel Edge Detection"
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