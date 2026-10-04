from pathlib import Path
from math import sqrt
import json

from PIL import Image


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXTRACTED_FOLDER = (
    PROJECT_ROOT
    / "results"
    / "extracted_regions"
)

ANALYSIS_FOLDER = (
    PROJECT_ROOT
    / "results"
    / "background_analysis"
)


# =========================================================
# DOCUMENT FOLDERS
# =========================================================

DOCUMENTS = {

    "NIC": [
        "nic_template_v1_normalized",
        "nic_genuine_01_normalized",
        "nic_altered_01_normalized",
    ],

    "DRIVING_LICENCE": [
        "driving_licence_template_v1_normalized",
        "driving_licence_genuine_01_normalized",
        "driving_licence_altered_01_normalized",
    ],
}


# =========================================================
# RGB TO GRAYSCALE
# =========================================================

def calculate_grayscale(
    red,
    green,
    blue,
):
    """
    Convert RGB into grayscale using our own
    weighted luminance calculation.
    """

    value = (
        (0.299 * red)
        +
        (0.587 * green)
        +
        (0.114 * blue)
    )

    value = round(value)


    if value < 0:
        value = 0

    if value > 255:
        value = 255


    return value


# =========================================================
# BUILD GRAYSCALE MATRIX
# =========================================================

def build_grayscale_matrix(image):
    """
    Convert an RGB image into a two-dimensional matrix
    of grayscale intensity values.
    """

    rgb_image = image.convert(
        "RGB"
    )

    width, height = (
        rgb_image.size
    )

    pixels = rgb_image.load()


    matrix = []


    for y in range(height):

        row = []


        for x in range(width):

            red, green, blue = (
                pixels[x, y]
            )


            gray = calculate_grayscale(
                red,
                green,
                blue,
            )


            row.append(
                gray
            )


        matrix.append(
            row
        )


    return matrix


# =========================================================
# CALCULATE MEAN
# =========================================================

def calculate_mean(values):

    if not values:
        return 0.0


    total = 0.0


    for value in values:

        total += value


    return (
        total
        / len(values)
    )


# =========================================================
# CALCULATE STANDARD DEVIATION
# =========================================================

def calculate_standard_deviation(
    values,
    mean,
):

    if not values:
        return 0.0


    squared_difference_total = 0.0


    for value in values:

        difference = (
            value - mean
        )


        squared_difference_total += (
            difference
            * difference
        )


    variance = (
        squared_difference_total
        / len(values)
    )


    return sqrt(
        variance
    )


# =========================================================
# CALCULATE DARK AND BRIGHT PIXEL RATIOS
# =========================================================

def calculate_pixel_ratios(values):

    if not values:

        return (
            0.0,
            0.0,
        )


    dark_pixels = 0
    bright_pixels = 0


    for value in values:

        if value <= 90:

            dark_pixels += 1


        if value >= 200:

            bright_pixels += 1


    total_pixels = len(values)


    dark_ratio = (
        dark_pixels
        / total_pixels
    ) * 100


    bright_ratio = (
        bright_pixels
        / total_pixels
    ) * 100


    return (
        dark_ratio,
        bright_ratio,
    )


# =========================================================
# CALCULATE NEIGHBOUR DIFFERENCE
# =========================================================

def calculate_neighbour_difference(
    matrix,
):
    """
    Measure how strongly adjacent pixels differ.

    Smooth background:
        lower value

    Rough / inconsistent background:
        higher value
    """

    height = len(matrix)


    if height == 0:
        return 0.0


    width = len(
        matrix[0]
    )


    difference_total = 0.0

    comparisons = 0


    for y in range(height):

        for x in range(width):

            current = (
                matrix[y][x]
            )


            # ---------------------------------------------
            # HORIZONTAL NEIGHBOUR
            # ---------------------------------------------

            if x + 1 < width:

                right = (
                    matrix[y][x + 1]
                )


                difference_total += abs(
                    current - right
                )


                comparisons += 1


            # ---------------------------------------------
            # VERTICAL NEIGHBOUR
            # ---------------------------------------------

            if y + 1 < height:

                below = (
                    matrix[y + 1][x]
                )


                difference_total += abs(
                    current - below
                )


                comparisons += 1


    if comparisons == 0:
        return 0.0


    return (
        difference_total
        / comparisons
    )


# =========================================================
# CALCULATE LOCAL BLOCK VARIATION
# =========================================================

def calculate_block_variation(
    matrix,
    block_size=16,
):
    """
    Divide the region into blocks and calculate the
    brightness mean of each block.

    Large differences between block means may indicate
    inconsistent document background.
    """

    height = len(matrix)


    if height == 0:

        return {
            "block_count": 0,
            "block_mean_average": 0.0,
            "block_mean_stddev": 0.0,
            "min_block_mean": 0.0,
            "max_block_mean": 0.0,
        }


    width = len(
        matrix[0]
    )


    block_means = []


    # -----------------------------------------------------
    # PROCESS BLOCKS
    # -----------------------------------------------------

    for start_y in range(
        0,
        height,
        block_size,
    ):

        for start_x in range(
            0,
            width,
            block_size,
        ):

            values = []


            end_y = min(
                start_y + block_size,
                height,
            )

            end_x = min(
                start_x + block_size,
                width,
            )


            for y in range(
                start_y,
                end_y,
            ):

                for x in range(
                    start_x,
                    end_x,
                ):

                    values.append(
                        matrix[y][x]
                    )


            if values:

                block_mean = (
                    calculate_mean(
                        values
                    )
                )


                block_means.append(
                    block_mean
                )


    if not block_means:

        return {
            "block_count": 0,
            "block_mean_average": 0.0,
            "block_mean_stddev": 0.0,
            "min_block_mean": 0.0,
            "max_block_mean": 0.0,
        }


    mean = calculate_mean(
        block_means
    )


    standard_deviation = (
        calculate_standard_deviation(
            block_means,
            mean,
        )
    )


    return {

        "block_count":
            len(block_means),

        "block_mean_average":
            mean,

        "block_mean_stddev":
            standard_deviation,

        "min_block_mean":
            min(block_means),

        "max_block_mean":
            max(block_means),
    }


# =========================================================
# CALCULATE REGION FEATURES
# =========================================================

def analyse_region(
    region_path,
):
    """
    Calculate statistical and texture features
    for one extracted document region.
    """

    with Image.open(
        region_path
    ) as image:

        width, height = (
            image.size
        )


        matrix = (
            build_grayscale_matrix(
                image
            )
        )


    # -----------------------------------------------------
    # CREATE FLAT PIXEL LIST
    # -----------------------------------------------------

    values = []


    for row in matrix:

        for value in row:

            values.append(
                value
            )


    # -----------------------------------------------------
    # BASIC STATISTICS
    # -----------------------------------------------------

    mean = calculate_mean(
        values
    )


    standard_deviation = (
        calculate_standard_deviation(
            values,
            mean,
        )
    )


    dark_ratio, bright_ratio = (
        calculate_pixel_ratios(
            values
        )
    )


    # -----------------------------------------------------
    # TEXTURE MEASUREMENT
    # -----------------------------------------------------

    neighbour_difference = (
        calculate_neighbour_difference(
            matrix
        )
    )


    # -----------------------------------------------------
    # LOCAL BLOCK VARIATION
    # -----------------------------------------------------

    block_results = (
        calculate_block_variation(
            matrix,
            block_size=16,
        )
    )


    # -----------------------------------------------------
    # RETURN FEATURES
    # -----------------------------------------------------

    return {

        "width":
            width,

        "height":
            height,

        "total_pixels":
            width * height,

        "mean_brightness":
            round(
                mean,
                4,
            ),

        "brightness_stddev":
            round(
                standard_deviation,
                4,
            ),

        "dark_pixel_ratio":
            round(
                dark_ratio,
                4,
            ),

        "bright_pixel_ratio":
            round(
                bright_ratio,
                4,
            ),

        "neighbour_difference":
            round(
                neighbour_difference,
                4,
            ),

        "block_count":
            block_results[
                "block_count"
            ],

        "block_mean_average":
            round(
                block_results[
                    "block_mean_average"
                ],
                4,
            ),

        "block_mean_stddev":
            round(
                block_results[
                    "block_mean_stddev"
                ],
                4,
            ),

        "min_block_mean":
            round(
                block_results[
                    "min_block_mean"
                ],
                4,
            ),

        "max_block_mean":
            round(
                block_results[
                    "max_block_mean"
                ],
                4,
            ),
    }


# =========================================================
# ANALYSE ONE DOCUMENT
# =========================================================

def analyse_document(
    document_type,
    document_folder_name,
):

    input_folder = (

        EXTRACTED_FOLDER
        / document_type.lower()
        / document_folder_name
    )


    metadata_path = (
        input_folder
        / "regions.json"
    )


    if not metadata_path.exists():

        print()
        print(
            f"WARNING: regions.json not found:"
        )

        print(
            metadata_path
        )

        return False


    # -----------------------------------------------------
    # LOAD REGION METADATA
    # -----------------------------------------------------

    with open(
        metadata_path,
        "r",
        encoding="utf-8",
    ) as file:

        metadata = json.load(
            file
        )


    result = {

        "document_type":
            document_type,

        "source_image":
            metadata[
                "source_image"
            ],

        "regions": {},
    }


    print()
    print("========================================")

    print(
        f"DOCUMENT: "
        f"{document_folder_name}"
    )

    print("========================================")


    # -----------------------------------------------------
    # PROCESS EACH REGION
    # -----------------------------------------------------

    for region_name, region_info in (
        metadata["regions"].items()
    ):

        region_file = (
            input_folder
            / region_info["file"]
        )


        if not region_file.exists():

            print(
                f"WARNING: Missing region: "
                f"{region_file.name}"
            )

            continue


        features = (
            analyse_region(
                region_file
            )
        )


        result["regions"][
            region_name
        ] = {

            "type":
                region_info["type"],

            "features":
                features,
        }


        print()

        print(
            f"Region: "
            f"{region_name}"
        )

        print(
            f"  Type: "
            f"{region_info['type']}"
        )

        print(
            f"  Mean brightness: "
            f"{features['mean_brightness']}"
        )

        print(
            f"  Brightness stddev: "
            f"{features['brightness_stddev']}"
        )

        print(
            f"  Neighbour difference: "
            f"{features['neighbour_difference']}"
        )

        print(
            f"  Block variation: "
            f"{features['block_mean_stddev']}"
        )


    # -----------------------------------------------------
    # CREATE OUTPUT FOLDER
    # -----------------------------------------------------

    output_folder = (

        ANALYSIS_FOLDER
        / document_type.lower()
    )


    output_folder.mkdir(
        parents=True,
        exist_ok=True,
    )


    # -----------------------------------------------------
    # SAVE JSON RESULT
    # -----------------------------------------------------

    output_path = (

        output_folder
        / (
            document_folder_name
            + "_background_features.json"
        )
    )


    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            result,
            file,
            indent=4,
        )


    print()

    print(
        f"Saved: "
        f"{output_path.name}"
    )


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
        "Step 9 - Background and Texture Analysis"
    )


    successful = 0


    for document_type, documents in (
        DOCUMENTS.items()
    ):

        for document in documents:

            result = analyse_document(
                document_type,
                document,
            )


            if result:

                successful += 1


    print()
    print("========================================")

    print(
        f"Documents analysed: "
        f"{successful}"
    )

    print("========================================")


if __name__ == "__main__":
    main()