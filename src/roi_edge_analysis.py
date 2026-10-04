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

EDGE_FEATURE_FOLDER = (
    PROJECT_ROOT
    / "results"
    / "roi_edge_features"
)

EDGE_MAP_FOLDER = (
    PROJECT_ROOT
    / "results"
    / "roi_edge_maps"
)

EDGE_COMPARISON_FOLDER = (
    PROJECT_ROOT
    / "results"
    / "edge_comparisons"
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
# EDGE FEATURE WEIGHTS BY REGION TYPE
# =========================================================

EDGE_WEIGHTS = {

    "text": {
        "edge_ratio": 0.35,
        "border_edge_ratio": 0.15,
        "centre_edge_ratio": 0.30,
        "mean_edge_strength": 0.20,
    },

    "photo": {
        "edge_ratio": 0.15,
        "border_edge_ratio": 0.50,
        "centre_edge_ratio": 0.15,
        "mean_edge_strength": 0.20,
    },

    "signature": {
        "edge_ratio": 0.20,
        "border_edge_ratio": 0.35,
        "centre_edge_ratio": 0.25,
        "mean_edge_strength": 0.20,
    },

    "logo": {
        "edge_ratio": 0.30,
        "border_edge_ratio": 0.25,
        "centre_edge_ratio": 0.25,
        "mean_edge_strength": 0.20,
    },

    "security_feature": {
        "edge_ratio": 0.25,
        "border_edge_ratio": 0.30,
        "centre_edge_ratio": 0.25,
        "mean_edge_strength": 0.20,
    },
}


# =========================================================
# FEATURE FLOORS
# =========================================================

FEATURE_FLOORS = {

    "edge_ratio": 1.0,

    "border_edge_ratio": 1.0,

    "centre_edge_ratio": 1.0,

    "mean_edge_strength": 50.0,
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
# MEAN
# =========================================================

def calculate_mean(values):

    if not values:
        return 0.0

    total = 0.0

    for value in values:
        total += value

    return total / len(values)


# =========================================================
# STANDARD DEVIATION
# =========================================================

def calculate_standard_deviation(
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

    value = round(
        value
    )

    if value < 0:
        value = 0

    if value > 255:
        value = 255

    return value


# =========================================================
# BUILD GRAYSCALE MATRIX
# =========================================================

def build_grayscale_matrix(image):

    rgb_image = image.convert(
        "RGB"
    )

    width, height = (
        rgb_image.size
    )

    pixels = (
        rgb_image.load()
    )

    matrix = []


    for y in range(height):

        row = []

        for x in range(width):

            red, green, blue = (
                pixels[x, y]
            )

            gray = (
                calculate_grayscale(
                    red,
                    green,
                    blue,
                )
            )

            row.append(
                gray
            )

        matrix.append(
            row
        )


    return matrix


# =========================================================
# CALCULATE SOBEL GRADIENT MAP
# =========================================================

def calculate_gradient_map(
    matrix,
):

    height = len(
        matrix
    )

    if height == 0:
        return [], [], [], []


    width = len(
        matrix[0]
    )


    gradient_map = [
        [0.0 for _ in range(width)]
        for _ in range(height)
    ]


    gradient_x_map = [
        [0.0 for _ in range(width)]
        for _ in range(height)
    ]


    gradient_y_map = [
        [0.0 for _ in range(width)]
        for _ in range(height)
    ]


    gradient_values = []


    # -----------------------------------------------------
    # SOBEL CALCULATION
    # -----------------------------------------------------

    for y in range(
        1,
        height - 1,
    ):

        for x in range(
            1,
            width - 1,
        ):

            gradient_x = 0.0
            gradient_y = 0.0


            for kernel_y in range(3):

                for kernel_x in range(3):

                    image_x = (
                        x
                        + kernel_x
                        - 1
                    )

                    image_y = (
                        y
                        + kernel_y
                        - 1
                    )


                    pixel_value = (
                        matrix[
                            image_y
                        ][
                            image_x
                        ]
                    )


                    gradient_x += (
                        pixel_value
                        *
                        SOBEL_X[
                            kernel_y
                        ][
                            kernel_x
                        ]
                    )


                    gradient_y += (
                        pixel_value
                        *
                        SOBEL_Y[
                            kernel_y
                        ][
                            kernel_x
                        ]
                    )


            magnitude = sqrt(
                (
                    gradient_x
                    * gradient_x
                )
                +
                (
                    gradient_y
                    * gradient_y
                )
            )


            gradient_x_map[y][x] = (
                gradient_x
            )

            gradient_y_map[y][x] = (
                gradient_y
            )

            gradient_map[y][x] = (
                magnitude
            )

            gradient_values.append(
                magnitude
            )


    return (
        gradient_map,
        gradient_x_map,
        gradient_y_map,
        gradient_values,
    )


# =========================================================
# AUTOMATIC EDGE THRESHOLD
# =========================================================

def calculate_edge_threshold(
    gradient_values,
):

    if not gradient_values:
        return 0.0


    mean = calculate_mean(
        gradient_values
    )


    standard_deviation = (
        calculate_standard_deviation(
            gradient_values,
            mean,
        )
    )


    threshold = (
        mean
        + standard_deviation
    )


    if threshold < 40:
        threshold = 40


    if threshold > 600:
        threshold = 600


    return threshold


# =========================================================
# BUILD EDGE MAP
# =========================================================

def build_edge_map(
    gradient_map,
    threshold,
):

    height = len(
        gradient_map
    )

    if height == 0:
        return []


    width = len(
        gradient_map[0]
    )


    edge_map = [
        [False for _ in range(width)]
        for _ in range(height)
    ]


    for y in range(
        1,
        height - 1,
    ):

        for x in range(
            1,
            width - 1,
        ):

            if (
                gradient_map[y][x]
                >= threshold
            ):

                edge_map[y][x] = True


    return edge_map


# =========================================================
# CREATE EDGE IMAGE
# =========================================================

def create_edge_image(
    edge_map,
):

    height = len(
        edge_map
    )

    width = len(
        edge_map[0]
    )


    image = Image.new(
        "L",
        (
            width,
            height,
        ),
        0,
    )


    pixels = (
        image.load()
    )


    for y in range(height):

        for x in range(width):

            if edge_map[y][x]:

                pixels[
                    x,
                    y,
                ] = 255


    return image


# =========================================================
# CALCULATE EDGE FEATURES
# =========================================================

def calculate_edge_features(
    gradient_map,
    edge_map,
):

    height = len(
        edge_map
    )


    if height == 0:
        return {}


    width = len(
        edge_map[0]
    )


    analysed_pixels = (
        max(
            1,
            (width - 2)
            *
            (height - 2),
        )
    )


    # -----------------------------------------------------
    # BORDER THICKNESS
    # -----------------------------------------------------

    border_thickness = round(
        min(
            width,
            height,
        )
        * 0.08
    )


    if border_thickness < 2:
        border_thickness = 2


    maximum_border = (
        min(
            width,
            height,
        )
        // 3
    )


    border_thickness = min(
        border_thickness,
        maximum_border,
    )


    edge_count = 0

    edge_strength_values = []


    border_pixels = 0
    border_edges = 0


    centre_pixels = 0
    centre_edges = 0


    # -----------------------------------------------------
    # SIDE BORDER STATISTICS
    # -----------------------------------------------------

    left_pixels = 0
    left_edges = 0

    right_pixels = 0
    right_edges = 0

    top_pixels = 0
    top_edges = 0

    bottom_pixels = 0
    bottom_edges = 0


    for y in range(
        1,
        height - 1,
    ):

        for x in range(
            1,
            width - 1,
        ):

            is_edge = (
                edge_map[y][x]
            )


            if is_edge:

                edge_count += 1

                edge_strength_values.append(
                    gradient_map[y][x]
                )


            # ---------------------------------------------
            # LEFT
            # ---------------------------------------------

            if x < border_thickness:

                left_pixels += 1

                if is_edge:
                    left_edges += 1


            # ---------------------------------------------
            # RIGHT
            # ---------------------------------------------

            if x >= (
                width
                - border_thickness
            ):

                right_pixels += 1

                if is_edge:
                    right_edges += 1


            # ---------------------------------------------
            # TOP
            # ---------------------------------------------

            if y < border_thickness:

                top_pixels += 1

                if is_edge:
                    top_edges += 1


            # ---------------------------------------------
            # BOTTOM
            # ---------------------------------------------

            if y >= (
                height
                - border_thickness
            ):

                bottom_pixels += 1

                if is_edge:
                    bottom_edges += 1


            # ---------------------------------------------
            # GENERAL BORDER / CENTRE
            # ---------------------------------------------

            is_border = (

                x < border_thickness

                or

                x >= (
                    width
                    - border_thickness
                )

                or

                y < border_thickness

                or

                y >= (
                    height
                    - border_thickness
                )
            )


            if is_border:

                border_pixels += 1

                if is_edge:
                    border_edges += 1


            else:

                centre_pixels += 1

                if is_edge:
                    centre_edges += 1


    # =====================================================
    # RATIOS
    # =====================================================

    edge_ratio = (
        edge_count
        / analysed_pixels
    ) * 100


    if border_pixels > 0:

        border_edge_ratio = (
            border_edges
            / border_pixels
        ) * 100

    else:

        border_edge_ratio = 0.0


    if centre_pixels > 0:

        centre_edge_ratio = (
            centre_edges
            / centre_pixels
        ) * 100

    else:

        centre_edge_ratio = 0.0


    def safe_ratio(
        edge_total,
        pixel_total,
    ):

        if pixel_total == 0:
            return 0.0

        return (
            edge_total
            / pixel_total
        ) * 100


    left_edge_ratio = safe_ratio(
        left_edges,
        left_pixels,
    )

    right_edge_ratio = safe_ratio(
        right_edges,
        right_pixels,
    )

    top_edge_ratio = safe_ratio(
        top_edges,
        top_pixels,
    )

    bottom_edge_ratio = safe_ratio(
        bottom_edges,
        bottom_pixels,
    )


    # =====================================================
    # EDGE STRENGTH
    # =====================================================

    mean_edge_strength = (
        calculate_mean(
            edge_strength_values
        )
    )


    # =====================================================
    # RETURN FEATURES
    # =====================================================

    return {

        "width":
            width,

        "height":
            height,

        "border_thickness":
            border_thickness,

        "edge_count":
            edge_count,

        "edge_ratio":
            round(
                edge_ratio,
                4,
            ),

        "border_edge_ratio":
            round(
                border_edge_ratio,
                4,
            ),

        "centre_edge_ratio":
            round(
                centre_edge_ratio,
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

        "mean_edge_strength":
            round(
                mean_edge_strength,
                4,
            ),
    }


# =========================================================
# ANALYSE ONE REGION
# =========================================================

def analyse_region(
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
        gradient_x_map,
        gradient_y_map,
        gradient_values,

    ) = calculate_gradient_map(
        matrix
    )


    threshold = (
        calculate_edge_threshold(
            gradient_values
        )
    )


    edge_map = build_edge_map(
        gradient_map,
        threshold,
    )


    features = (
        calculate_edge_features(
            gradient_map,
            edge_map,
        )
    )


    features[
        "edge_threshold"
    ] = round(
        threshold,
        4,
    )


    edge_image = (
        create_edge_image(
            edge_map
        )
    )


    return (
        features,
        edge_image,
    )


# =========================================================
# ANALYSE ONE DOCUMENT
# =========================================================

def analyse_document(
    document_type,
    document_name,
):

    document_folder = (

        EXTRACTED_FOLDER
        / document_type.lower()
        / document_name
    )


    metadata_path = (
        document_folder
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

        metadata = json.load(
            file
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

        "regions": {},
    }


    edge_map_output = (

        EDGE_MAP_FOLDER
        / document_type.lower()
        / document_name
    )


    edge_map_output.mkdir(
        parents=True,
        exist_ok=True,
    )


    print()
    print("========================================")

    print(
        f"EDGE ANALYSIS: {document_name}"
    )

    print("========================================")


    for region_name, region_information in (
        metadata[
            "regions"
        ].items()
    ):

        region_path = (

            document_folder
            / region_information[
                "file"
            ]
        )


        if not region_path.exists():

            print(
                f"Missing: "
                f"{region_path.name}"
            )

            continue


        (
            features,
            edge_image,

        ) = analyse_region(
            region_path
        )


        edge_output_path = (

            edge_map_output
            / (
                region_name
                + "_edges.png"
            )
        )


        edge_image.save(
            edge_output_path
        )


        result[
            "regions"
        ][
            region_name
        ] = {

            "type":
                region_information[
                    "type"
                ],

            "features":
                features,

            "edge_map":
                edge_output_path.name,
        }


        print()

        print(
            f"Region: "
            f"{region_name}"
        )

        print(
            f"  Edge ratio: "
            f"{features['edge_ratio']:.2f}%"
        )

        print(
            f"  Border edges: "
            f"{features['border_edge_ratio']:.2f}%"
        )

        print(
            f"  Centre edges: "
            f"{features['centre_edge_ratio']:.2f}%"
        )

        print(
            f"  Edge strength: "
            f"{features['mean_edge_strength']:.2f}"
        )


    # =====================================================
    # SAVE FEATURE JSON
    # =====================================================

    output_folder = (

        EDGE_FEATURE_FOLDER
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
            + "_edge_features.json"
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
# NORMALIZED FEATURE DIFFERENCE
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
        abs(
            template_value
        ),
        minimum_reference,
    )


    score = (
        difference
        / denominator
    ) * 100


    if score > 100:
        score = 100


    return score


# =========================================================
# COMPARE ONE REGION
# =========================================================

def compare_region(
    region_type,
    template_features,
    document_features,
):

    weights = (
        EDGE_WEIGHTS.get(
            region_type,
            EDGE_WEIGHTS[
                "text"
            ],
        )
    )


    feature_comparisons = {}

    weighted_score = 0.0

    total_weight = 0.0


    for feature_name, weight in (
        weights.items()
    ):

        if (
            feature_name
            not in template_features
        ):

            continue


        if (
            feature_name
            not in document_features
        ):

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


        feature_comparisons[
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


        weighted_score += (
            difference
            * weight
        )


        total_weight += (
            weight
        )


    if total_weight == 0:

        final_score = 0.0

    else:

        final_score = (
            weighted_score
            / total_weight
        )


    return {

        "edge_difference_score":
            round(
                final_score,
                4,
            ),

        "feature_comparisons":
            feature_comparisons,
    }


# =========================================================
# COMPARE DOCUMENT TO TEMPLATE
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

        if (
            region_name
            not in template_result[
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


        result = compare_region(

            region_type,

            template_region[
                "features"
            ],

            document_region[
                "features"
            ],
        )


        score = (
            result[
                "edge_difference_score"
            ]
        )


        comparison[
            "regions"
        ][
            region_name
        ] = {

            "type":
                region_type,

            "edge_difference_score":
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

                "edge_difference_score":
                    score,
            }
        )


    ranking.sort(

        key=lambda item:
            item[
                "edge_difference_score"
            ],

        reverse=True,
    )


    comparison[
        "ranked_candidate_regions"
    ] = ranking


    # =====================================================
    # AVERAGE EDGE DIFFERENCE
    # =====================================================

    if ranking:

        total = 0.0


        for item in ranking:

            total += (
                item[
                    "edge_difference_score"
                ]
            )


        average = (
            total
            / len(ranking)
        )

    else:

        average = 0.0


    comparison[
        "average_edge_difference_score"
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
    comparison,
):

    output_folder = (

        EDGE_COMPARISON_FOLDER
        / document_type.lower()
    )


    output_folder.mkdir(
        parents=True,
        exist_ok=True,
    )


    output_path = (

        output_folder
        / (
            comparison[
                "document"
            ]
            + "_edge_comparison.json"
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
# PRINT COMPARISON
# =========================================================

def print_comparison(
    comparison,
):

    print()
    print("========================================")
    print("EDGE TEMPLATE COMPARISON")
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
            f"{item['edge_difference_score']:.2f}"
        )


    print()

    print(
        "Average edge difference: "
        f"{comparison['average_edge_difference_score']:.2f}"
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
        "Step 11 - ROI Edge Analysis"
    )


    for document_type, configuration in (
        DOCUMENTS.items()
    ):

        # =================================================
        # ANALYSE TEMPLATE
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
        # ANALYSE SUBMITTED DOCUMENTS
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


            # =============================================
            # COMPARE WITH TEMPLATE
            # =============================================

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
    print("STEP 11 COMPLETE")
    print("========================================")


if __name__ == "__main__":
    main()