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
    / "photo_features"
)

COMPARISON_FOLDER = (
    PROJECT_ROOT
    / "results"
    / "photo_comparisons"
)

PREVIEW_FOLDER = (
    PROJECT_ROOT
    / "results"
    / "photo_analysis_previews"
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
# FEATURE WEIGHTS
# =========================================================

FEATURE_WEIGHTS = {

    "border_edge_ratio": 0.35,

    "border_mean_strength": 0.25,

    "left_edge_ratio": 0.10,

    "right_edge_ratio": 0.10,

    "top_edge_ratio": 0.10,

    "bottom_edge_ratio": 0.10,
}


FEATURE_FLOORS = {

    "border_edge_ratio": 1.0,

    "border_mean_strength": 20.0,

    "left_edge_ratio": 1.0,

    "right_edge_ratio": 1.0,

    "top_edge_ratio": 1.0,

    "bottom_edge_ratio": 1.0,
}


# =========================================================
# BASIC FUNCTIONS
# =========================================================

def calculate_mean(values):

    if not values:
        return 0.0

    total = 0.0

    for value in values:
        total += value

    return total / len(values)


def calculate_stddev(values, mean):

    if not values:
        return 0.0

    total = 0.0

    for value in values:

        difference = value - mean

        total += (
            difference
            * difference
        )

    variance = (
        total
        / len(values)
    )

    return sqrt(variance)


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

    rgb_image = image.convert("RGB")

    width, height = rgb_image.size

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
# SOBEL GRADIENT
# =========================================================

def calculate_gradient_map(matrix):

    height = len(matrix)

    if height == 0:
        return [], []


    width = len(
        matrix[0]
    )


    gradient_map = [

        [0.0 for _ in range(width)]

        for _ in range(height)
    ]


    values = []


    for y in range(
        1,
        height - 1,
    ):

        for x in range(
            1,
            width - 1,
        ):

            gx = 0.0
            gy = 0.0


            for ky in range(3):

                for kx in range(3):

                    pixel = matrix[
                        y + ky - 1
                    ][
                        x + kx - 1
                    ]


                    gx += (
                        pixel
                        * SOBEL_X[ky][kx]
                    )


                    gy += (
                        pixel
                        * SOBEL_Y[ky][kx]
                    )


            magnitude = sqrt(
                gx * gx
                +
                gy * gy
            )


            gradient_map[y][x] = (
                magnitude
            )


            values.append(
                magnitude
            )


    return (
        gradient_map,
        values,
    )


# =========================================================
# AUTOMATIC EDGE THRESHOLD
# =========================================================

def calculate_edge_threshold(values):

    if not values:
        return 0.0


    mean = calculate_mean(
        values
    )


    stddev = calculate_stddev(
        values,
        mean,
    )


    threshold = (
        mean
        + stddev
    )


    if threshold < 40:
        threshold = 40


    if threshold > 600:
        threshold = 600


    return threshold


# =========================================================
# PHOTO BORDER FEATURES
# =========================================================

def analyse_photo_border(
    gradient_map,
    threshold,
):

    height = len(
        gradient_map
    )


    if height == 0:
        return {}


    width = len(
        gradient_map[0]
    )


    # -----------------------------------------------------
    # BORDER BAND
    # -----------------------------------------------------

    border_size = round(
        min(
            width,
            height,
        )
        * 0.12
    )


    if border_size < 2:
        border_size = 2


    maximum = (
        min(
            width,
            height,
        )
        // 3
    )


    border_size = min(
        border_size,
        maximum,
    )


    # -----------------------------------------------------
    # COUNTERS
    # -----------------------------------------------------

    border_pixels = 0
    border_edges = 0

    border_strength_values = []


    left_pixels = 0
    left_edges = 0

    right_pixels = 0
    right_edges = 0

    top_pixels = 0
    top_edges = 0

    bottom_pixels = 0
    bottom_edges = 0


    # =====================================================
    # ANALYSE BORDER
    # =====================================================

    for y in range(
        1,
        height - 1,
    ):

        for x in range(
            1,
            width - 1,
        ):

            strength = (
                gradient_map[y][x]
            )


            is_edge = (
                strength
                >= threshold
            )


            # ---------------------------------------------
            # LEFT
            # ---------------------------------------------

            if x < border_size:

                left_pixels += 1

                if is_edge:
                    left_edges += 1


            # ---------------------------------------------
            # RIGHT
            # ---------------------------------------------

            if x >= (
                width
                - border_size
            ):

                right_pixels += 1

                if is_edge:
                    right_edges += 1


            # ---------------------------------------------
            # TOP
            # ---------------------------------------------

            if y < border_size:

                top_pixels += 1

                if is_edge:
                    top_edges += 1


            # ---------------------------------------------
            # BOTTOM
            # ---------------------------------------------

            if y >= (
                height
                - border_size
            ):

                bottom_pixels += 1

                if is_edge:
                    bottom_edges += 1


            # ---------------------------------------------
            # GENERAL BORDER
            # ---------------------------------------------

            is_border = (

                x < border_size

                or

                x >= (
                    width
                    - border_size
                )

                or

                y < border_size

                or

                y >= (
                    height
                    - border_size
                )
            )


            if is_border:

                border_pixels += 1

                border_strength_values.append(
                    strength
                )


                if is_edge:

                    border_edges += 1


    # =====================================================
    # SAFE RATIO
    # =====================================================

    def ratio(
        edges,
        pixels,
    ):

        if pixels == 0:
            return 0.0

        return (
            edges
            / pixels
        ) * 100


    border_edge_ratio = ratio(
        border_edges,
        border_pixels,
    )


    left_edge_ratio = ratio(
        left_edges,
        left_pixels,
    )


    right_edge_ratio = ratio(
        right_edges,
        right_pixels,
    )


    top_edge_ratio = ratio(
        top_edges,
        top_pixels,
    )


    bottom_edge_ratio = ratio(
        bottom_edges,
        bottom_pixels,
    )


    border_mean_strength = (
        calculate_mean(
            border_strength_values
        )
    )


    # -----------------------------------------------------
    # SIDE ASYMMETRY
    # -----------------------------------------------------

    side_values = [

        left_edge_ratio,

        right_edge_ratio,

        top_edge_ratio,

        bottom_edge_ratio,
    ]


    side_mean = (
        calculate_mean(
            side_values
        )
    )


    side_stddev = (
        calculate_stddev(
            side_values,
            side_mean,
        )
    )


    return {

        "width":
            width,

        "height":
            height,

        "border_size":
            border_size,

        "border_edge_ratio":
            round(
                border_edge_ratio,
                4,
            ),

        "border_mean_strength":
            round(
                border_mean_strength,
                4,
            ),

        "left_edge_ratio":
            round(
                left_edge_ratio,
                4,
            ),

        "right_edge_ratio":
            round(
                right_edge_ratio,
                4,
            ),

        "top_edge_ratio":
            round(
                top_edge_ratio,
                4,
            ),

        "bottom_edge_ratio":
            round(
                bottom_edge_ratio,
                4,
            ),

        "border_side_stddev":
            round(
                side_stddev,
                4,
            ),

        "edge_threshold":
            round(
                threshold,
                4,
            ),
    }


# =========================================================
# CREATE PREVIEW
# =========================================================

def create_photo_preview(
    region_path,
    border_size,
    output_path,
):

    with Image.open(
        region_path
    ) as image:

        preview = image.convert(
            "RGB"
        )


    width, height = (
        preview.size
    )


    draw = ImageDraw.Draw(
        preview
    )


    # Outer photo border.
    draw.rectangle(
        [
            1,
            1,
            width - 2,
            height - 2,
        ],
        outline="red",
        width=2,
    )


    # Inner border-analysis boundary.
    draw.rectangle(
        [
            border_size,
            border_size,
            width - border_size,
            height - border_size,
        ],
        outline="yellow",
        width=2,
    )


    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


    preview.save(
        output_path
    )


# =========================================================
# ANALYSE PHOTO REGION
# =========================================================

def analyse_photo_region(
    region_path,
):

    with Image.open(
        region_path
    ) as image:

        matrix = (
            build_grayscale_matrix(
                image
            )
        )


    (
        gradient_map,
        gradient_values,

    ) = calculate_gradient_map(
        matrix
    )


    threshold = (
        calculate_edge_threshold(
            gradient_values
        )
    )


    features = (
        analyse_photo_border(
            gradient_map,
            threshold,
        )
    )


    return features


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

        print(metadata_path)

        return None


    with open(
        metadata_path,
        "r",
        encoding="utf-8",
    ) as file:

        metadata = json.load(file)


    photo_information = (
        metadata[
            "regions"
        ].get(
            "photo"
        )
    )


    if photo_information is None:

        print(
            f"No photo region for "
            f"{document_name}"
        )

        return None


    region_path = (

        input_folder
        / photo_information[
            "file"
        ]
    )


    if not region_path.exists():

        print(
            f"Photo image missing: "
            f"{region_path}"
        )

        return None


    features = (
        analyse_photo_region(
            region_path
        )
    )


    # =====================================================
    # PREVIEW
    # =====================================================

    preview_path = (

        PREVIEW_FOLDER
        / document_type.lower()
        / document_name
        / "photo_border_analysis.png"
    )


    create_photo_preview(

        region_path,

        features[
            "border_size"
        ],

        preview_path,
    )


    result = {

        "document_type":
            document_type,

        "document":
            document_name,

        "source_image":
            metadata[
                "source_image"
            ],

        "photo_region":
            {

                "features":
                    features,

                "preview":
                    preview_path.name,
            },
    }


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
            + "_photo_features.json"
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
    print("========================================")
    print(f"PHOTO ANALYSIS: {document_name}")
    print("========================================")

    print(
        f"Border edge ratio: "
        f"{features['border_edge_ratio']:.2f}%"
    )

    print(
        f"Left border: "
        f"{features['left_edge_ratio']:.2f}%"
    )

    print(
        f"Right border: "
        f"{features['right_edge_ratio']:.2f}%"
    )

    print(
        f"Top border: "
        f"{features['top_edge_ratio']:.2f}%"
    )

    print(
        f"Bottom border: "
        f"{features['bottom_edge_ratio']:.2f}%"
    )

    print(
        f"Border strength: "
        f"{features['border_mean_strength']:.2f}"
    )

    print("========================================")


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
# COMPARE PHOTO TO TEMPLATE
# =========================================================

def compare_photo(
    document_type,
    template_result,
    document_result,
):

    template_features = (

        template_result[
            "photo_region"
        ][
            "features"
        ]
    )


    document_features = (

        document_result[
            "photo_region"
        ][
            "features"
        ]
    )


    comparisons = {}

    weighted_total = 0.0

    total_weight = 0.0


    for feature_name, weight in (
        FEATURE_WEIGHTS.items()
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

        "photo_border_difference_score":
            round(
                score,
                4,
            ),

        "feature_comparisons":
            comparisons,
    }


# =========================================================
# SAVE COMPARISON
# =========================================================

def save_comparison(
    document_type,
    comparison,
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
            comparison["document"]
            + "_photo_comparison.json"
        )
    )


    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            comparison,
            file,
            indent=4,
        )


    return output_path


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print(
        "Document Alteration Detection Module"
    )

    print(
        "Step 13 - Photo Replacement Analysis"
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
                compare_photo(
                    document_type,
                    template_result,
                    document_result,
                )
            )


            output_path = (
                save_comparison(
                    document_type,
                    comparison,
                )
            )


            print()
            print("----------------------------------------")

            print(
                f"Photo comparison: "
                f"{document_name}"
            )

            print(
                "Photo border difference score: "
                f"{comparison['photo_border_difference_score']:.2f}"
            )

            print(
                f"Saved: "
                f"{output_path.name}"
            )

            print("----------------------------------------")


    print()
    print("========================================")
    print("STEP 13 COMPLETE")
    print("========================================")


if __name__ == "__main__":
    main()