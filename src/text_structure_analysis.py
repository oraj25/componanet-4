from collections import deque
from pathlib import Path
from math import sqrt
import json

from PIL import Image, ImageDraw


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXTRACTED_FOLDER = (
    PROJECT_ROOT
    / "results"
    / "extracted_regions"
)

FEATURE_FOLDER = (
    PROJECT_ROOT
    / "results"
    / "text_structure_features"
)

COMPONENT_MAP_FOLDER = (
    PROJECT_ROOT
    / "results"
    / "text_component_maps"
)

COMPARISON_FOLDER = (
    PROJECT_ROOT
    / "results"
    / "text_comparisons"
)


# =========================================================
# DOCUMENT CONFIGURATION
# =========================================================

DOCUMENTS = {

    "NIC": {
        "template":
            "nic_template_v1_normalized",

        "documents": [
            "nic_genuine_01_normalized",
            "nic_altered_01_normalized",
        ],
    },

    "DRIVING_LICENCE": {
        "template":
            "driving_licence_template_v1_normalized",

        "documents": [
            "driving_licence_genuine_01_normalized",
            "driving_licence_altered_01_normalized",
        ],
    },
}


# =========================================================
# COMPARISON WEIGHTS
# =========================================================

FEATURE_WEIGHTS = {

    "mean_component_height": 0.20,

    "component_height_stddev": 0.15,

    "mean_component_width": 0.10,

    "mean_horizontal_gap": 0.20,

    "horizontal_gap_stddev": 0.10,

    "baseline_stddev": 0.15,

    "foreground_ratio": 0.10,
}


FEATURE_FLOORS = {

    "mean_component_height": 2.0,

    "component_height_stddev": 1.0,

    "mean_component_width": 2.0,

    "mean_horizontal_gap": 2.0,

    "horizontal_gap_stddev": 1.0,

    "baseline_stddev": 1.0,

    "foreground_ratio": 2.0,
}


# =========================================================
# BASIC STATISTICS
# =========================================================

def calculate_mean(values):

    if not values:
        return 0.0

    total = 0.0

    for value in values:
        total += value

    return total / len(values)


def calculate_stddev(
    values,
    mean,
):

    if not values:
        return 0.0

    total = 0.0

    for value in values:

        difference = (
            value - mean
        )

        total += (
            difference
            * difference
        )

    variance = (
        total
        / len(values)
    )

    return sqrt(
        variance
    )


# =========================================================
# MANUAL RGB TO GRAYSCALE
# =========================================================

def calculate_grayscale(
    red,
    green,
    blue,
):

    value = (
        (0.299 * red)
        +
        (0.587 * green)
        +
        (0.114 * blue)
    )

    value = round(value)

    return max(
        0,
        min(
            255,
            value,
        ),
    )


def build_grayscale_matrix(image):

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

            row.append(
                calculate_grayscale(
                    red,
                    green,
                    blue,
                )
            )

        matrix.append(row)


    return matrix


# =========================================================
# BUILD HISTOGRAM
# =========================================================

def build_histogram(matrix):

    histogram = [0] * 256

    total_pixels = 0


    for row in matrix:

        for value in row:

            histogram[value] += 1

            total_pixels += 1


    return (
        histogram,
        total_pixels,
    )


# =========================================================
# AUTOMATIC THRESHOLD
# =========================================================

def calculate_threshold(
    histogram,
    total_pixels,
):

    total_intensity = 0


    for intensity in range(256):

        total_intensity += (
            intensity
            * histogram[intensity]
        )


    dark_weight = 0
    dark_sum = 0

    best_threshold = 0
    highest_variance = -1


    for threshold in range(256):

        dark_weight += (
            histogram[threshold]
        )


        if dark_weight == 0:
            continue


        light_weight = (
            total_pixels
            - dark_weight
        )


        if light_weight == 0:
            break


        dark_sum += (
            threshold
            * histogram[threshold]
        )


        dark_mean = (
            dark_sum
            / dark_weight
        )


        light_sum = (
            total_intensity
            - dark_sum
        )


        light_mean = (
            light_sum
            / light_weight
        )


        difference = (
            dark_mean
            - light_mean
        )


        variance = (
            dark_weight
            * light_weight
            * difference
            * difference
        )


        if variance > highest_variance:

            highest_variance = variance

            best_threshold = threshold


    return best_threshold


# =========================================================
# CREATE BINARY MATRIX
# =========================================================

def create_binary_matrix(
    grayscale_matrix,
    threshold,
):

    binary = []

    foreground_pixels = 0
    total_pixels = 0


    for row in grayscale_matrix:

        binary_row = []

        for value in row:

            if value <= threshold:

                binary_row.append(1)

                foreground_pixels += 1

            else:

                binary_row.append(0)


            total_pixels += 1


        binary.append(
            binary_row
        )


    if total_pixels == 0:

        foreground_ratio = 0.0

    else:

        foreground_ratio = (
            foreground_pixels
            / total_pixels
        ) * 100


    return (
        binary,
        foreground_ratio,
    )


# =========================================================
# CONNECTED COMPONENT DETECTION
# =========================================================

def find_connected_components(
    binary,
):

    height = len(binary)

    if height == 0:
        return []


    width = len(
        binary[0]
    )


    visited = [
        [False for _ in range(width)]
        for _ in range(height)
    ]


    components = []


    neighbours = [
        (-1, -1),
        (0, -1),
        (1, -1),

        (-1, 0),
        (1, 0),

        (-1, 1),
        (0, 1),
        (1, 1),
    ]


    for y in range(height):

        for x in range(width):

            if binary[y][x] == 0:
                continue

            if visited[y][x]:
                continue


            queue = deque()

            queue.append(
                (x, y)
            )

            visited[y][x] = True


            min_x = x
            max_x = x

            min_y = y
            max_y = y

            pixel_count = 0


            while queue:

                current_x, current_y = (
                    queue.popleft()
                )


                pixel_count += 1


                min_x = min(
                    min_x,
                    current_x,
                )

                max_x = max(
                    max_x,
                    current_x,
                )

                min_y = min(
                    min_y,
                    current_y,
                )

                max_y = max(
                    max_y,
                    current_y,
                )


                for dx, dy in neighbours:

                    neighbour_x = (
                        current_x + dx
                    )

                    neighbour_y = (
                        current_y + dy
                    )


                    if not (
                        0
                        <= neighbour_x
                        < width
                    ):
                        continue


                    if not (
                        0
                        <= neighbour_y
                        < height
                    ):
                        continue


                    if visited[
                        neighbour_y
                    ][
                        neighbour_x
                    ]:
                        continue


                    if binary[
                        neighbour_y
                    ][
                        neighbour_x
                    ] == 0:
                        continue


                    visited[
                        neighbour_y
                    ][
                        neighbour_x
                    ] = True


                    queue.append(
                        (
                            neighbour_x,
                            neighbour_y,
                        )
                    )


            components.append(
                {
                    "x1":
                        min_x,

                    "y1":
                        min_y,

                    "x2":
                        max_x + 1,

                    "y2":
                        max_y + 1,

                    "width":
                        max_x
                        - min_x
                        + 1,

                    "height":
                        max_y
                        - min_y
                        + 1,

                    "pixel_count":
                        pixel_count,

                    "center_x":
                        (
                            min_x
                            + max_x
                        )
                        / 2,

                    "center_y":
                        (
                            min_y
                            + max_y
                        )
                        / 2,
                }
            )


    return components


# =========================================================
# REMOVE NOISE / LARGE BACKGROUND COMPONENTS
# =========================================================

def filter_components(
    components,
    image_width,
    image_height,
):

    filtered = []


    image_area = (
        image_width
        * image_height
    )


    for component in components:

        width = (
            component["width"]
        )

        height = (
            component["height"]
        )

        pixel_count = (
            component[
                "pixel_count"
            ]
        )


        # Small isolated noise.
        if pixel_count < 3:
            continue


        if width < 2:
            continue


        if height < 2:
            continue


        component_area = (
            width * height
        )


        # Ignore huge connected background / border areas.
        if component_area > (
            image_area * 0.35
        ):
            continue


        # Ignore extremely tall decorative/background areas.
        if height > (
            image_height * 0.85
        ):
            continue


        filtered.append(
            component
        )


    return filtered


# =========================================================
# GROUP COMPONENTS INTO TEXT LINES
# =========================================================

def group_into_lines(
    components,
):

    if not components:
        return []


    sorted_components = sorted(

        components,

        key=lambda item:
            item["center_y"],
    )


    heights = [
        component["height"]
        for component in components
    ]


    average_height = (
        calculate_mean(
            heights
        )
    )


    vertical_tolerance = max(
        4.0,
        average_height * 0.65,
    )


    lines = []


    for component in sorted_components:

        assigned = False


        for line in lines:

            line_center = (
                calculate_mean(
                    [
                        item["center_y"]
                        for item in line
                    ]
                )
            )


            if abs(
                component["center_y"]
                - line_center
            ) <= vertical_tolerance:

                line.append(
                    component
                )

                assigned = True

                break


        if not assigned:

            lines.append(
                [component]
            )


    # Sort components in each line horizontally.
    for line in lines:

        line.sort(
            key=lambda item:
                item["x1"]
        )


    return lines


# =========================================================
# TEXT STRUCTURE FEATURES
# =========================================================

def calculate_text_features(
    components,
    foreground_ratio,
):

    if not components:

        return {

            "component_count": 0,

            "line_count": 0,

            "mean_component_width": 0.0,

            "component_width_stddev": 0.0,

            "mean_component_height": 0.0,

            "component_height_stddev": 0.0,

            "mean_horizontal_gap": 0.0,

            "horizontal_gap_stddev": 0.0,

            "baseline_stddev": 0.0,

            "foreground_ratio":
                round(
                    foreground_ratio,
                    4,
                ),
        }


    widths = [
        component["width"]
        for component in components
    ]


    heights = [
        component["height"]
        for component in components
    ]


    mean_width = (
        calculate_mean(
            widths
        )
    )


    width_stddev = (
        calculate_stddev(
            widths,
            mean_width,
        )
    )


    mean_height = (
        calculate_mean(
            heights
        )
    )


    height_stddev = (
        calculate_stddev(
            heights,
            mean_height,
        )
    )


    # -----------------------------------------------------
    # LINE GROUPING
    # -----------------------------------------------------

    lines = group_into_lines(
        components
    )


    horizontal_gaps = []

    baseline_deviations = []


    for line in lines:

        if not line:
            continue


        # ---------------------------------------------
        # HORIZONTAL SPACING
        # ---------------------------------------------

        for index in range(
            len(line) - 1
        ):

            current = (
                line[index]
            )

            following = (
                line[index + 1]
            )


            gap = (
                following["x1"]
                - current["x2"]
            )


            if gap >= 0:

                horizontal_gaps.append(
                    gap
                )


        # ---------------------------------------------
        # BASELINE / ALIGNMENT
        # ---------------------------------------------

        bottoms = [
            component["y2"]
            for component in line
        ]


        line_bottom_mean = (
            calculate_mean(
                bottoms
            )
        )


        line_stddev = (
            calculate_stddev(
                bottoms,
                line_bottom_mean,
            )
        )


        baseline_deviations.append(
            line_stddev
        )


    # -----------------------------------------------------
    # SPACING STATISTICS
    # -----------------------------------------------------

    mean_gap = (
        calculate_mean(
            horizontal_gaps
        )
    )


    gap_stddev = (
        calculate_stddev(
            horizontal_gaps,
            mean_gap,
        )
    )


    # -----------------------------------------------------
    # ALIGNMENT STATISTIC
    # -----------------------------------------------------

    baseline_stddev = (
        calculate_mean(
            baseline_deviations
        )
    )


    return {

        "component_count":
            len(components),

        "line_count":
            len(lines),

        "mean_component_width":
            round(
                mean_width,
                4,
            ),

        "component_width_stddev":
            round(
                width_stddev,
                4,
            ),

        "mean_component_height":
            round(
                mean_height,
                4,
            ),

        "component_height_stddev":
            round(
                height_stddev,
                4,
            ),

        "mean_horizontal_gap":
            round(
                mean_gap,
                4,
            ),

        "horizontal_gap_stddev":
            round(
                gap_stddev,
                4,
            ),

        "baseline_stddev":
            round(
                baseline_stddev,
                4,
            ),

        "foreground_ratio":
            round(
                foreground_ratio,
                4,
            ),
    }


# =========================================================
# CREATE COMPONENT PREVIEW
# =========================================================

def create_component_preview(
    region_path,
    components,
    output_path,
):

    with Image.open(
        region_path
    ) as image:

        preview = image.convert(
            "RGB"
        )


    draw = ImageDraw.Draw(
        preview
    )


    for component in components:

        draw.rectangle(
            [
                component["x1"],
                component["y1"],
                component["x2"],
                component["y2"],
            ],
            outline="red",
            width=1,
        )


    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


    preview.save(
        output_path
    )


# =========================================================
# ANALYSE ONE TEXT REGION
# =========================================================

def analyse_text_region(
    region_path,
):

    with Image.open(
        region_path
    ) as image:

        width, height = (
            image.size
        )


        grayscale_matrix = (
            build_grayscale_matrix(
                image
            )
        )


    histogram, total_pixels = (
        build_histogram(
            grayscale_matrix
        )
    )


    threshold = (
        calculate_threshold(
            histogram,
            total_pixels,
        )
    )


    (
        binary_matrix,
        foreground_ratio,

    ) = create_binary_matrix(
        grayscale_matrix,
        threshold,
    )


    components = (
        find_connected_components(
            binary_matrix
        )
    )


    components = (
        filter_components(
            components,
            width,
            height,
        )
    )


    features = (
        calculate_text_features(
            components,
            foreground_ratio,
        )
    )


    features[
        "threshold"
    ] = threshold


    return (
        features,
        components,
    )


# =========================================================
# ANALYSE DOCUMENT
# =========================================================

def analyse_document(
    document_type,
    document_name,
):

    input_folder = (

        EXTRACTED_FOLDER
        / document_type.lower()
        / document_name
    )


    metadata_path = (
        input_folder
        / "regions.json"
    )


    if not metadata_path.exists():

        print()
        print(
            f"ERROR: Missing regions.json:"
        )

        print(metadata_path)

        return None


    with open(
        metadata_path,
        "r",
        encoding="utf-8",
    ) as file:

        metadata = json.load(file)


    result = {

        "document_type":
            document_type,

        "document":
            document_name,

        "source_image":
            metadata[
                "source_image"
            ],

        "regions": {},
    }


    print()
    print("========================================")
    print(f"TEXT ANALYSIS: {document_name}")
    print("========================================")


    for region_name, region_information in (
        metadata["regions"].items()
    ):

        # Only analyse configured text ROIs.
        if (
            region_information[
                "type"
            ]
            != "text"
        ):
            continue


        region_path = (

            input_folder
            / region_information[
                "file"
            ]
        )


        if not region_path.exists():
            continue


        (
            features,
            components,

        ) = analyse_text_region(
            region_path
        )


        # -------------------------------------------------
        # SAVE COMPONENT PREVIEW
        # -------------------------------------------------

        preview_path = (

            COMPONENT_MAP_FOLDER
            / document_type.lower()
            / document_name
            / (
                region_name
                + "_components.png"
            )
        )


        create_component_preview(
            region_path,
            components,
            preview_path,
        )


        result["regions"][
            region_name
        ] = {

            "type": "text",

            "features":
                features,

            "component_preview":
                preview_path.name,
        }


        print()

        print(
            f"Region: {region_name}"
        )

        print(
            f"  Components: "
            f"{features['component_count']}"
        )

        print(
            f"  Lines: "
            f"{features['line_count']}"
        )

        print(
            f"  Mean height: "
            f"{features['mean_component_height']:.2f}"
        )

        print(
            f"  Mean gap: "
            f"{features['mean_horizontal_gap']:.2f}"
        )

        print(
            f"  Baseline deviation: "
            f"{features['baseline_stddev']:.2f}"
        )


    # =====================================================
    # SAVE FEATURE FILE
    # =====================================================

    output_folder = (

        FEATURE_FOLDER
        / document_type.lower()
    )


    output_folder.mkdir(
        parents=True,
        exist_ok=True,
    )


    output_path = (

        output_folder
        / (
            document_name
            + "_text_features.json"
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
        f"Saved: {output_path.name}"
    )


    return result


# =========================================================
# NORMALIZED DIFFERENCE
# =========================================================

def calculate_feature_difference(
    template_value,
    document_value,
    minimum_reference,
):

    difference = abs(
        document_value
        - template_value
    )


    denominator = max(
        abs(template_value),
        minimum_reference,
    )


    score = (
        difference
        / denominator
    ) * 100


    return min(
        100.0,
        score,
    )


# =========================================================
# COMPARE TEXT REGION
# =========================================================

def compare_text_region(
    template_features,
    document_features,
):

    comparison = {}

    weighted_total = 0.0

    total_weight = 0.0


    for feature_name, weight in (
        FEATURE_WEIGHTS.items()
    ):

        if feature_name not in template_features:
            continue

        if feature_name not in document_features:
            continue


        template_value = float(
            template_features[
                feature_name
            ]
        )


        document_value = float(
            document_features[
                feature_name
            ]
        )


        difference = (
            calculate_feature_difference(
                template_value,
                document_value,
                FEATURE_FLOORS[
                    feature_name
                ],
            )
        )


        comparison[
            feature_name
        ] = {

            "template_value":
                round(
                    template_value,
                    4,
                ),

            "document_value":
                round(
                    document_value,
                    4,
                ),

            "difference_percent":
                round(
                    difference,
                    4,
                ),

            "weight":
                weight,
        }


        weighted_total += (
            difference
            * weight
        )


        total_weight += (
            weight
        )


    if total_weight == 0:

        score = 0.0

    else:

        score = (
            weighted_total
            / total_weight
        )


    return {

        "text_structure_difference_score":
            round(
                score,
                4,
            ),

        "feature_comparisons":
            comparison,
    }


# =========================================================
# COMPARE DOCUMENT WITH TEMPLATE
# =========================================================

def compare_document(
    document_type,
    template_result,
    document_result,
):

    output = {

        "document_type":
            document_type,

        "template":
            template_result[
                "document"
            ],

        "document":
            document_result[
                "document"
            ],

        "regions": {},

        "ranked_candidate_regions": [],
    }


    ranking = []


    for region_name, document_region in (
        document_result[
            "regions"
        ].items()
    ):

        if region_name not in (
            template_result[
                "regions"
            ]
        ):
            continue


        template_region = (

            template_result[
                "regions"
            ][
                region_name
            ]
        )


        result = (
            compare_text_region(

                template_region[
                    "features"
                ],

                document_region[
                    "features"
                ],
            )
        )


        score = (
            result[
                "text_structure_difference_score"
            ]
        )


        output[
            "regions"
        ][
            region_name
        ] = {

            "text_structure_difference_score":
                score,

            "feature_comparisons":
                result[
                    "feature_comparisons"
                ],
        }


        ranking.append(
            {

                "region":
                    region_name,

                "text_structure_difference_score":
                    score,
            }
        )


    ranking.sort(

        key=lambda item:
            item[
                "text_structure_difference_score"
            ],

        reverse=True,
    )


    output[
        "ranked_candidate_regions"
    ] = ranking


    if ranking:

        average = (
            sum(
                item[
                    "text_structure_difference_score"
                ]
                for item in ranking
            )
            /
            len(ranking)
        )

    else:

        average = 0.0


    output[
        "average_text_structure_difference_score"
    ] = round(
        average,
        4,
    )


    return output


# =========================================================
# SAVE COMPARISON
# =========================================================

def save_comparison(
    document_type,
    result,
):

    output_folder = (

        COMPARISON_FOLDER
        / document_type.lower()
    )


    output_folder.mkdir(
        parents=True,
        exist_ok=True,
    )


    output_path = (

        output_folder
        / (
            result["document"]
            + "_text_comparison.json"
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


    return output_path


# =========================================================
# PRINT COMPARISON
# =========================================================

def print_comparison(
    comparison,
):

    print()
    print("========================================")
    print("TEXT STRUCTURE COMPARISON")
    print("========================================")

    print(
        f"Document: "
        f"{comparison['document']}"
    )

    print()


    for position, item in enumerate(
        comparison[
            "ranked_candidate_regions"
        ],
        start=1,
    ):

        print(
            f"{position}. "
            f"{item['region']:<22} "
            f"{item['text_structure_difference_score']:.2f}"
        )


    print()

    print(
        "Average text difference: "
        f"{comparison['average_text_structure_difference_score']:.2f}"
    )

    print("========================================")


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print(
        "Document Alteration Detection Module"
    )

    print(
        "Step 12 - Text Structure Analysis"
    )


    for document_type, configuration in (
        DOCUMENTS.items()
    ):

        # =================================================
        # TEMPLATE
        # =================================================

        template_result = (
            analyse_document(
                document_type,
                configuration[
                    "template"
                ],
            )
        )


        if template_result is None:
            continue


        # =================================================
        # TEST DOCUMENTS
        # =================================================

        for document_name in (
            configuration[
                "documents"
            ]
        ):

            document_result = (
                analyse_document(
                    document_type,
                    document_name,
                )
            )


            if document_result is None:
                continue


            comparison = (
                compare_document(
                    document_type,
                    template_result,
                    document_result,
                )
            )


            print_comparison(
                comparison
            )


            output_path = (
                save_comparison(
                    document_type,
                    comparison,
                )
            )


            print(
                f"Saved comparison: "
                f"{output_path.name}"
            )


    print()
    print("========================================")
    print("STEP 12 COMPLETE")
    print("========================================")


if __name__ == "__main__":
    main()