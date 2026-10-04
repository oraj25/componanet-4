from pathlib import Path
from math import floor

from PIL import Image


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FOLDER = PROJECT_ROOT / "data"
RESULTS_FOLDER = PROJECT_ROOT / "results"
NORMALIZED_FOLDER = RESULTS_FOLDER / "normalized"


# =========================================================
# DOCUMENT CONFIGURATION
# =========================================================

DOCUMENTS = {
    "NIC": {
        "template": (
            DATA_FOLDER
            / "templates"
            / "nic_template_v1.jpg"
        ),

        "images": [
            (
                DATA_FOLDER
                / "genuine"
                / "nic_genuine_01.jpg",

                NORMALIZED_FOLDER
                / "nic_genuine_01_normalized.png",
            ),
            (
                DATA_FOLDER
                / "altered"
                / "nic_altered_01.jpg",

                NORMALIZED_FOLDER
                / "nic_altered_01_normalized.png",
            ),
        ],
    },

    "DRIVING_LICENCE": {
        "template": (
            DATA_FOLDER
            / "templates"
            / "driving_licence_template_v1.jpg"
        ),

        "images": [
            (
                DATA_FOLDER
                / "genuine"
                / "driving_licence_genuine_01.jpg",

                NORMALIZED_FOLDER
                / "driving_licence_genuine_01_normalized.png",
            ),
            (
                DATA_FOLDER
                / "altered"
                / "driving_licence_altered_01.jpg",

                NORMALIZED_FOLDER
                / "driving_licence_altered_01_normalized.png",
            ),
        ],
    },
}


# =========================================================
# LIMIT RGB VALUE
# =========================================================

def clamp(value):
    """
    Ensure RGB value remains between 0 and 255.
    """

    value = round(value)

    if value < 0:
        return 0

    if value > 255:
        return 255

    return value


# =========================================================
# BILINEAR PIXEL CALCULATION
# =========================================================

def calculate_bilinear_pixel(
    pixels,
    source_width,
    source_height,
    source_x,
    source_y,
):
    """
    Calculate a new RGB pixel using the four nearest
    pixels from the source image.
    """

    x0 = floor(source_x)
    y0 = floor(source_y)

    x1 = min(
        x0 + 1,
        source_width - 1,
    )

    y1 = min(
        y0 + 1,
        source_height - 1,
    )


    x_difference = (
        source_x - x0
    )

    y_difference = (
        source_y - y0
    )


    top_left = pixels[x0, y0]
    top_right = pixels[x1, y0]

    bottom_left = pixels[x0, y1]
    bottom_right = pixels[x1, y1]


    new_pixel = []


    for channel in range(3):

        # ---------------------------------------------
        # INTERPOLATE TOP TWO PIXELS
        # ---------------------------------------------

        top_value = (
            top_left[channel]
            * (1 - x_difference)
            +
            top_right[channel]
            * x_difference
        )


        # ---------------------------------------------
        # INTERPOLATE BOTTOM TWO PIXELS
        # ---------------------------------------------

        bottom_value = (
            bottom_left[channel]
            * (1 - x_difference)
            +
            bottom_right[channel]
            * x_difference
        )


        # ---------------------------------------------
        # INTERPOLATE VERTICALLY
        # ---------------------------------------------

        final_value = (
            top_value
            * (1 - y_difference)
            +
            bottom_value
            * y_difference
        )


        new_pixel.append(
            clamp(final_value)
        )


    return tuple(new_pixel)


# =========================================================
# MANUAL IMAGE NORMALIZATION
# =========================================================

def resize_image_manually(
    source_image,
    target_width,
    target_height,
):
    """
    Resize an RGB image using our own bilinear
    interpolation algorithm.
    """

    source_width, source_height = (
        source_image.size
    )

    source_pixels = (
        source_image.load()
    )


    normalized_image = Image.new(
        "RGB",
        (
            target_width,
            target_height,
        ),
    )

    normalized_pixels = (
        normalized_image.load()
    )


    # -----------------------------------------------------
    # SCALE RATIOS
    # -----------------------------------------------------

    if target_width > 1:

        x_scale = (
            (source_width - 1)
            /
            (target_width - 1)
        )

    else:

        x_scale = 0


    if target_height > 1:

        y_scale = (
            (source_height - 1)
            /
            (target_height - 1)
        )

    else:

        y_scale = 0


    # -----------------------------------------------------
    # CREATE EVERY TARGET PIXEL
    # -----------------------------------------------------

    for target_y in range(target_height):

        source_y = (
            target_y * y_scale
        )


        for target_x in range(target_width):

            source_x = (
                target_x * x_scale
            )


            new_pixel = (
                calculate_bilinear_pixel(
                    source_pixels,
                    source_width,
                    source_height,
                    source_x,
                    source_y,
                )
            )


            normalized_pixels[
                target_x,
                target_y,
            ] = new_pixel


    return normalized_image


# =========================================================
# NORMALIZE ONE DOCUMENT
# =========================================================

def normalize_document(
    input_path,
    output_path,
    target_width,
    target_height,
):

    if not input_path.exists():

        print()
        print(
            f"ERROR: Image not found: "
            f"{input_path}"
        )

        return False


    with Image.open(input_path) as image:

        rgb_image = image.convert(
            "RGB"
        )

        original_width, original_height = (
            rgb_image.size
        )


        normalized_image = (
            resize_image_manually(
                rgb_image,
                target_width,
                target_height,
            )
        )


        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )


        normalized_image.save(
            output_path
        )


        print()
        print("----------------------------------------")

        print(
            f"Input:  {input_path.name}"
        )

        print(
            f"Original size: "
            f"{original_width} x "
            f"{original_height}"
        )

        print(
            f"Normalized size: "
            f"{target_width} x "
            f"{target_height}"
        )

        print(
            f"Saved: {output_path.name}"
        )

        print("----------------------------------------")


    return True


# =========================================================
# PROCESS DOCUMENT TYPE
# =========================================================

def process_document_type(
    document_type,
    configuration,
):

    template_path = (
        configuration["template"]
    )


    if not template_path.exists():

        print()
        print(
            f"ERROR: Template not found "
            f"for {document_type}"
        )

        print(
            f"Expected: {template_path}"
        )

        return 0


    # -----------------------------------------------------
    # READ TEMPLATE DIMENSIONS
    # -----------------------------------------------------

    with Image.open(template_path) as template:

        template_width, template_height = (
            template.size
        )


    print()
    print("========================================")
    print(f"DOCUMENT TYPE: {document_type}")
    print("========================================")

    print(
        f"Template: "
        f"{template_path.name}"
    )

    print(
        f"Target size: "
        f"{template_width} x "
        f"{template_height}"
    )


    # -----------------------------------------------------
    # SAVE NORMALIZED TEMPLATE COPY
    # -----------------------------------------------------

    template_output = (

        NORMALIZED_FOLDER
        /
        (
            template_path.stem
            + "_normalized.png"
        )
    )


    normalize_document(
        template_path,
        template_output,
        template_width,
        template_height,
    )


    successful = 0


    # -----------------------------------------------------
    # NORMALIZE TEST IMAGES
    # -----------------------------------------------------

    for input_path, output_path in configuration["images"]:

        result = normalize_document(
            input_path,
            output_path,
            template_width,
            template_height,
        )


        if result:
            successful += 1


    return successful


# =========================================================
# MAIN PROGRAM
# =========================================================

def main():

    print()
    print(
        "Document Alteration Detection Module"
    )

    print(
        "Step 6 - Document Size Normalization"
    )


    total_processed = 0


    for document_type, configuration in DOCUMENTS.items():

        processed = (
            process_document_type(
                document_type,
                configuration,
            )
        )

        total_processed += processed


    print()
    print("========================================")

    print(
        f"Test documents normalized: "
        f"{total_processed}"
    )

    print("========================================")


if __name__ == "__main__":
    main()