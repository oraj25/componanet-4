from pathlib import Path
from math import sqrt
from collections import deque
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
    / "symbol_features"
)

COMPARISON_FOLDER = (
    PROJECT_ROOT
    / "results"
    / "symbol_comparisons"
)

PREVIEW_FOLDER = (
    PROJECT_ROOT
    / "results"
    / "symbol_previews"
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
# REGION TYPES
# =========================================================

ANALYSED_TYPES = {
    "signature",
    "logo",
    "security_feature",
}


# =========================================================
# FEATURE WEIGHTS
# =========================================================

FEATURE_WEIGHTS = {

    "signature": {
        "foreground_ratio": 0.25,
        "component_count": 0.10,
        "mean_component_area": 0.15,
        "bounding_box_ratio": 0.20,
        "centre_x_ratio": 0.15,
        "centre_y_ratio": 0.15,
    },

    "logo": {
        "foreground_ratio": 0.20,
        "component_count": 0.10,
        "mean_component_area": 0.15,
        "bounding_box_ratio": 0.20,
        "centre_x_ratio": 0.15,
        "centre_y_ratio": 0.20,
    },

    "security_feature": {
        "foreground_ratio": 0.20,
        "component_count": 0.15,
        "mean_component_area": 0.15,
        "bounding_box_ratio": 0.20,
        "centre_x_ratio": 0.15,
        "centre_y_ratio": 0.15,
    },
}


FEATURE_FLOORS = {

    "foreground_ratio": 2.0,

    "component_count": 2.0,

    "mean_component_area": 5.0,

    "bounding_box_ratio": 5.0,

    "centre_x_ratio": 5.0,

    "centre_y_ratio": 5.0,
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


# =========================================================
# RGB TO GRAYSCALE
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

            gray = calculate_grayscale(
                red,
                green,
                blue,
            )

            row.append(gray)

        matrix.append(row)


    return matrix


# =========================================================
# HISTOGRAM
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
# BINARY MATRIX
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
# CONNECTED COMPONENTS
# =========================================================

def find_components(binary):

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


    components = []


    for y in range(height):

        for x in range(width):

            if binary[y][x] == 0:
                continue

            if visited[y][x]:
                continue


            queue = deque(
                [(x, y)]
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

                    nx = (
                        current_x + dx
                    )

                    ny = (
                        current_y + dy
                    )


                    if not (
                        0 <= nx < width
                    ):
                        continue


                    if not (
                        0 <= ny < height
                    ):
                        continue


                    if visited[ny][nx]:
                        continue


                    if binary[ny][nx] == 0:
                        continue


                    visited[ny][nx] = True

                    queue.append(
                        (nx, ny)
                    )


            component_width = (
                max_x
                - min_x
                + 1
            )


            component_height = (
                max_y
                - min_y
                + 1
            )


            components.append(
                {
                    "x1": min_x,
                    "y1": min_y,

                    "x2": max_x + 1,
                    "y2": max_y + 1,

                    "width":
                        component_width,

                    "height":
                        component_height,

                    "pixel_count":
                        pixel_count,

                    "area":
                        component_width
                        * component_height,
                }
            )


    return components


# =========================================================
# FILTER COMPONENTS
# =========================================================

def filter_components(
    components,
    width,
    height,
):

    filtered = []

    total_area = (
        width * height
    )


    for component in components:

        if component["pixel_count"] < 3:
            continue


        if component["area"] > (
            total_area * 0.70
        ):
            continue


        filtered.append(
            component
        )


    return filtered


# =========================================================
# CALCULATE FEATURES
# =========================================================

def calculate_symbol_features(
    components,
    foreground_ratio,
    width,
    height,
):

    if not components:

        return {

            "foreground_ratio":
                round(
                    foreground_ratio,
                    4,
                ),

            "component_count":
                0,

            "mean_component_area":
                0.0,

            "bounding_box_ratio":
                0.0,

            "centre_x_ratio":
                0.0,

            "centre_y_ratio":
                0.0,
        }


    areas = [
        component["area"]
        for component in components
    ]


    mean_component_area = (
        calculate_mean(
            areas
        )
    )


    # =====================================================
    # COMBINED FOREGROUND BOUNDING BOX
    # =====================================================

    min_x = min(
        component["x1"]
        for component in components
    )

    min_y = min(
        component["y1"]
        for component in components
    )

    max_x = max(
        component["x2"]
        for component in components
    )

    max_y = max(
        component["y2"]
        for component in components
    )


    bounding_width = (
        max_x - min_x
    )

    bounding_height = (
        max_y - min_y
    )


    bounding_area = (
        bounding_width
        * bounding_height
    )


    image_area = (
        width * height
    )


    if image_area == 0:

        bounding_box_ratio = 0.0

    else:

        bounding_box_ratio = (
            bounding_area
            / image_area
        ) * 100


    # =====================================================
    # SYMBOL CENTRE POSITION
    # =====================================================

    centre_x = (
        min_x + max_x
    ) / 2


    centre_y = (
        min_y + max_y
    ) / 2


    if width == 0:

        centre_x_ratio = 0.0

    else:

        centre_x_ratio = (
            centre_x
            / width
        ) * 100


    if height == 0:

        centre_y_ratio = 0.0

    else:

        centre_y_ratio = (
            centre_y
            / height
        ) * 100


    return {

        "foreground_ratio":
            round(
                foreground_ratio,
                4,
            ),

        "component_count":
            len(components),

        "mean_component_area":
            round(
                mean_component_area,
                4,
            ),

        "bounding_box_ratio":
            round(
                bounding_box_ratio,
                4,
            ),

        "centre_x_ratio":
            round(
                centre_x_ratio,
                4,
            ),

        "centre_y_ratio":
            round(
                centre_y_ratio,
                4,
            ),
    }


# =========================================================
# ANALYSE REGION
# =========================================================

def analyse_region(
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
        binary,
        foreground_ratio,

    ) = create_binary_matrix(
        grayscale_matrix,
        threshold,
    )


    components = (
        find_components(
            binary
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
        calculate_symbol_features(
            components,
            foreground_ratio,
            width,
            height,
        )
    )


    features["threshold"] = (
        threshold
    )


    return (
        features,
        components,
    )


# =========================================================
# COMPONENT PREVIEW
# =========================================================

def create_preview(
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
            "ERROR: Missing regions.json"
        )

        print(
            metadata_path
        )

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
    print(f"SYMBOL ANALYSIS: {document_name}")
    print("========================================")


    for region_name, region_info in (
        metadata[
            "regions"
        ].items()
    ):

        region_type = (
            region_info[
                "type"
            ]
        )


        if region_type not in ANALYSED_TYPES:
            continue


        region_path = (

            input_folder
            / region_info[
                "file"
            ]
        )


        if not region_path.exists():
            continue


        (
            features,
            components,

        ) = analyse_region(
            region_path
        )


        preview_path = (

            PREVIEW_FOLDER
            / document_type.lower()
            / document_name
            / (
                region_name
                + "_analysis.png"
            )
        )


        create_preview(
            region_path,
            components,
            preview_path,
        )


        result["regions"][
            region_name
        ] = {

            "type":
                region_type,

            "features":
                features,

            "preview":
                preview_path.name,
        }


        print()

        print(
            f"Region: {region_name}"
        )

        print(
            f"  Type: {region_type}"
        )

        print(
            f"  Foreground ratio: "
            f"{features['foreground_ratio']:.2f}%"
        )

        print(
            f"  Components: "
            f"{features['component_count']}"
        )

        print(
            f"  Bounding box: "
            f"{features['bounding_box_ratio']:.2f}%"
        )


    # =====================================================
    # SAVE FEATURES
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
            + "_symbol_features.json"
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


    return result


# =========================================================
# FEATURE DIFFERENCE
# =========================================================

def calculate_difference(
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
# COMPARE REGION
# =========================================================

def compare_region(
    region_type,
    template_features,
    document_features,
):

    weights = (
        FEATURE_WEIGHTS[
            region_type
        ]
    )


    comparisons = {}

    weighted_total = 0.0

    total_weight = 0.0


    for feature_name, weight in (
        weights.items()
    ):

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
            calculate_difference(
                template_value,
                document_value,
                FEATURE_FLOORS[
                    feature_name
                ],
            )
        )


        comparisons[
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


        total_weight += weight


    if total_weight == 0:

        score = 0.0

    else:

        score = (
            weighted_total
            / total_weight
        )


    return {

        "symbol_difference_score":
            round(
                score,
                4,
            ),

        "feature_comparisons":
            comparisons,
    }


# =========================================================
# COMPARE DOCUMENT
# =========================================================

def compare_document(
    document_type,
    template_result,
    document_result,
):

    comparison = {

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


        region_type = (
            document_region[
                "type"
            ]
        )


        result = (
            compare_region(
                region_type,
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
                "symbol_difference_score"
            ]
        )


        comparison[
            "regions"
        ][
            region_name
        ] = {

            "type":
                region_type,

            "symbol_difference_score":
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

                "type":
                    region_type,

                "symbol_difference_score":
                    score,
            }
        )


    ranking.sort(

        key=lambda item:
            item[
                "symbol_difference_score"
            ],

        reverse=True,
    )


    comparison[
        "ranked_candidate_regions"
    ] = ranking


    if ranking:

        average = (
            sum(
                item[
                    "symbol_difference_score"
                ]
                for item in ranking
            )
            /
            len(ranking)
        )

    else:

        average = 0.0


    comparison[
        "average_symbol_difference_score"
    ] = round(
        average,
        4,
    )


    return comparison


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
            result[
                "document"
            ]
            + "_symbol_comparison.json"
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
# PRINT RESULTS
# =========================================================

def print_comparison(
    comparison,
):

    print()
    print("========================================")
    print("SYMBOL TEMPLATE COMPARISON")
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
            f"{item['type']:<18} "
            f"{item['symbol_difference_score']:.2f}"
        )


    print()

    print(
        "Average symbol difference: "
        f"{comparison['average_symbol_difference_score']:.2f}"
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
        "Step 14 - Signature, Logo and "
        "Security Feature Analysis"
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
                f"Saved: "
                f"{output_path.name}"
            )


    print()
    print("========================================")
    print("STEP 14 COMPLETE")
    print("========================================")


if __name__ == "__main__":
    main()