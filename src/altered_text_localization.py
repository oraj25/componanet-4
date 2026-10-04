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

NORMALIZED_FOLDER = (
    PROJECT_ROOT
    / "results"
    / "normalized"
)

OUTPUT_FOLDER = (
    PROJECT_ROOT
    / "results"
    / "altered_text_localization"
)

HIGHLIGHT_FOLDER = (
    PROJECT_ROOT
    / "results"
    / "suspicious_highlights"
)


# =========================================================
# DOCUMENT CONFIGURATION
# =========================================================

DOCUMENTS = {

    "NIC": {
        "template":
            "nic_template_v1_normalized",

        "template_image":
            "nic_template_v1_normalized.png",

        "documents": [
            "nic_genuine_01_normalized",
            "nic_altered_01_normalized",
        ],

        "document_images": {
            "nic_genuine_01_normalized":
                "nic_genuine_01_normalized.png",

            "nic_altered_01_normalized":
                "nic_altered_01_normalized.png",
        },
    },

    "DRIVING_LICENCE": {
        "template":
            "driving_licence_template_v1_normalized",

        "template_image":
            "driving_licence_template_v1_normalized.png",

        "documents": [
            "driving_licence_genuine_01_normalized",
            "driving_licence_altered_01_normalized",
        ],

        "document_images": {
            "driving_licence_genuine_01_normalized":
                "driving_licence_genuine_01_normalized.png",

            "driving_licence_altered_01_normalized":
                "driving_licence_altered_01_normalized.png",
        },
    },
}


# =========================================================
# SETTINGS
# =========================================================

BLOCK_SIZE = 16

MINIMUM_SUSPICIOUS_SCORE = 30.0


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
# GET ONE BLOCK FROM MATRIX
# =========================================================

def get_block_values(
    matrix,
    start_x,
    start_y,
    end_x,
    end_y,
):

    values = []


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


    return values


# =========================================================
# NEIGHBOUR DIFFERENCE
# =========================================================

def calculate_neighbour_difference(
    matrix,
    start_x,
    start_y,
    end_x,
    end_y,
):

    total = 0.0

    comparisons = 0


    for y in range(
        start_y,
        end_y,
    ):

        for x in range(
            start_x,
            end_x,
        ):

            current = (
                matrix[y][x]
            )


            if x + 1 < end_x:

                right = (
                    matrix[y][x + 1]
                )

                total += abs(
                    current - right
                )

                comparisons += 1


            if y + 1 < end_y:

                below = (
                    matrix[y + 1][x]
                )

                total += abs(
                    current - below
                )

                comparisons += 1


    if comparisons == 0:
        return 0.0


    return (
        total
        / comparisons
    )


# =========================================================
# SIMPLE LOCAL EDGE RATIO
# =========================================================

def calculate_edge_ratio(
    matrix,
    start_x,
    start_y,
    end_x,
    end_y,
):

    edge_pixels = 0

    analysed_pixels = 0


    for y in range(
        max(
            start_y + 1,
            1,
        ),
        min(
            end_y - 1,
            len(matrix) - 1,
        ),
    ):

        for x in range(
            max(
                start_x + 1,
                1,
            ),
            min(
                end_x - 1,
                len(matrix[0]) - 1,
            ),
        ):

            left = (
                matrix[y][x - 1]
            )

            right = (
                matrix[y][x + 1]
            )

            top = (
                matrix[y - 1][x]
            )

            bottom = (
                matrix[y + 1][x]
            )


            horizontal_change = abs(
                right - left
            )

            vertical_change = abs(
                bottom - top
            )


            strength = sqrt(
                (
                    horizontal_change
                    * horizontal_change
                )
                +
                (
                    vertical_change
                    * vertical_change
                )
            )


            if strength >= 60:

                edge_pixels += 1


            analysed_pixels += 1


    if analysed_pixels == 0:

        return 0.0


    return (
        edge_pixels
        / analysed_pixels
    ) * 100


# =========================================================
# BLOCK FEATURES
# =========================================================

def calculate_block_features(
    matrix,
    start_x,
    start_y,
    end_x,
    end_y,
):

    values = (
        get_block_values(
            matrix,
            start_x,
            start_y,
            end_x,
            end_y,
        )
    )


    mean = calculate_mean(
        values
    )


    stddev = (
        calculate_stddev(
            values,
            mean,
        )
    )


    neighbour_difference = (
        calculate_neighbour_difference(
            matrix,
            start_x,
            start_y,
            end_x,
            end_y,
        )
    )


    edge_ratio = (
        calculate_edge_ratio(
            matrix,
            start_x,
            start_y,
            end_x,
            end_y,
        )
    )


    return {

        "mean_brightness":
            mean,

        "brightness_stddev":
            stddev,

        "neighbour_difference":
            neighbour_difference,

        "edge_ratio":
            edge_ratio,
    }


# =========================================================
# NORMALIZED DIFFERENCE
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
        score,
        100.0,
    )


# =========================================================
# COMPARE ONE BLOCK
# =========================================================

def compare_block(
    template_features,
    document_features,
):

    brightness_difference = (
        calculate_difference(
            template_features[
                "mean_brightness"
            ],
            document_features[
                "mean_brightness"
            ],
            20.0,
        )
    )


    variation_difference = (
        calculate_difference(
            template_features[
                "brightness_stddev"
            ],
            document_features[
                "brightness_stddev"
            ],
            5.0,
        )
    )


    texture_difference = (
        calculate_difference(
            template_features[
                "neighbour_difference"
            ],
            document_features[
                "neighbour_difference"
            ],
            2.0,
        )
    )


    edge_difference = (
        calculate_difference(
            template_features[
                "edge_ratio"
            ],
            document_features[
                "edge_ratio"
            ],
            2.0,
        )
    )


    # =====================================================
    # WEIGHTED LOCAL ALTERATION SCORE
    # =====================================================

    score = (

        brightness_difference
        * 0.20

        +

        variation_difference
        * 0.25

        +

        texture_difference
        * 0.30

        +

        edge_difference
        * 0.25
    )


    return {

        "score":
            round(
                score,
                4,
            ),

        "brightness_difference":
            round(
                brightness_difference,
                4,
            ),

        "variation_difference":
            round(
                variation_difference,
                4,
            ),

        "texture_difference":
            round(
                texture_difference,
                4,
            ),

        "edge_difference":
            round(
                edge_difference,
                4,
            ),
    }


# =========================================================
# COMPARE ONE TEXT ROI
# =========================================================

def compare_text_region(
    template_path,
    document_path,
):

    with Image.open(
        template_path
    ) as template_image:

        template_matrix = (
            build_grayscale_matrix(
                template_image
            )
        )

        template_width, template_height = (
            template_image.size
        )


    with Image.open(
        document_path
    ) as document_image:

        document_matrix = (
            build_grayscale_matrix(
                document_image
            )
        )

        document_width, document_height = (
            document_image.size
        )


    # =====================================================
    # BOTH ROI IMAGES MUST HAVE SAME SIZE
    # =====================================================

    if (
        template_width
        != document_width
        or
        template_height
        != document_height
    ):

        print(
            f"WARNING: Region size mismatch: "
            f"{document_path.name}"
        )

        return []


    blocks = []


    for start_y in range(
        0,
        document_height,
        BLOCK_SIZE,
    ):

        for start_x in range(
            0,
            document_width,
            BLOCK_SIZE,
        ):

            end_x = min(
                start_x
                + BLOCK_SIZE,
                document_width,
            )


            end_y = min(
                start_y
                + BLOCK_SIZE,
                document_height,
            )


            # Ignore extremely small remainder blocks.
            if (
                end_x - start_x
                < 5
            ):
                continue


            if (
                end_y - start_y
                < 5
            ):
                continue


            template_features = (
                calculate_block_features(
                    template_matrix,
                    start_x,
                    start_y,
                    end_x,
                    end_y,
                )
            )


            document_features = (
                calculate_block_features(
                    document_matrix,
                    start_x,
                    start_y,
                    end_x,
                    end_y,
                )
            )


            comparison = (
                compare_block(
                    template_features,
                    document_features,
                )
            )


            blocks.append(
                {

                    "x1":
                        start_x,

                    "y1":
                        start_y,

                    "x2":
                        end_x,

                    "y2":
                        end_y,

                    **comparison,
                }
            )


    return blocks


# =========================================================
# CALCULATE AUTOMATIC CANDIDATE THRESHOLD
# =========================================================

def calculate_candidate_threshold(
    blocks,
):

    if not blocks:

        return 100.0


    scores = [
        block["score"]
        for block in blocks
    ]


    mean = calculate_mean(
        scores
    )


    stddev = (
        calculate_stddev(
            scores,
            mean,
        )
    )


    threshold = (
        mean
        + stddev
    )


    # Never flag very small differences.
    threshold = max(
        threshold,
        MINIMUM_SUSPICIOUS_SCORE,
    )


    # Keep inside score range.
    threshold = min(
        threshold,
        100.0,
    )


    return threshold


# =========================================================
# MERGE TOUCHING SUSPICIOUS BLOCKS
# =========================================================

def boxes_touch(
    first,
    second,
):

    return not (

        first["x2"] < second["x1"] - 2

        or

        second["x2"] < first["x1"] - 2

        or

        first["y2"] < second["y1"] - 2

        or

        second["y2"] < first["y1"] - 2
    )


def merge_boxes(
    boxes,
):

    boxes = [
        dict(box)
        for box in boxes
    ]


    changed = True


    while changed:

        changed = False

        merged = []

        used = [
            False
            for _ in boxes
        ]


        for i in range(
            len(boxes)
        ):

            if used[i]:
                continue


            current = dict(
                boxes[i]
            )


            score_values = [
                current["score"]
            ]


            used[i] = True


            for j in range(
                i + 1,
                len(boxes),
            ):

                if used[j]:
                    continue


                if boxes_touch(
                    current,
                    boxes[j],
                ):

                    current["x1"] = min(
                        current["x1"],
                        boxes[j]["x1"],
                    )

                    current["y1"] = min(
                        current["y1"],
                        boxes[j]["y1"],
                    )

                    current["x2"] = max(
                        current["x2"],
                        boxes[j]["x2"],
                    )

                    current["y2"] = max(
                        current["y2"],
                        boxes[j]["y2"],
                    )


                    score_values.append(
                        boxes[j]["score"]
                    )


                    current["score"] = (
                        calculate_mean(
                            score_values
                        )
                    )


                    used[j] = True

                    changed = True


            merged.append(
                current
            )


        boxes = merged


    return boxes


# =========================================================
# LOAD REGION METADATA
# =========================================================

def load_region_metadata(
    folder,
):

    path = (
        folder
        / "regions.json"
    )


    if not path.exists():

        return None


    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


# =========================================================
# ANALYSE ONE DOCUMENT
# =========================================================

def analyse_document(
    document_type,
    template_name,
    document_name,
):

    template_folder = (

        EXTRACTED_FOLDER
        / document_type.lower()
        / template_name
    )


    document_folder = (

        EXTRACTED_FOLDER
        / document_type.lower()
        / document_name
    )


    template_metadata = (
        load_region_metadata(
            template_folder
        )
    )


    document_metadata = (
        load_region_metadata(
            document_folder
        )
    )


    if template_metadata is None:

        print(
            f"ERROR: Template metadata missing "
            f"for {document_type}"
        )

        return None


    if document_metadata is None:

        print(
            f"ERROR: Document metadata missing "
            f"for {document_name}"
        )

        return None


    all_candidate_blocks = []

    region_results = {}


    # =====================================================
    # FIRST PASS - CALCULATE ALL TEXT BLOCK SCORES
    # =====================================================

    for region_name, region_info in (
        document_metadata[
            "regions"
        ].items()
    ):

        if region_info[
            "type"
        ] != "text":

            continue


        if region_name not in (
            template_metadata[
                "regions"
            ]
        ):

            continue


        template_file = (

            template_folder
            / template_metadata[
                "regions"
            ][
                region_name
            ][
                "file"
            ]
        )


        document_file = (

            document_folder
            / region_info[
                "file"
            ]
        )


        if not template_file.exists():
            continue


        if not document_file.exists():
            continue


        blocks = (
            compare_text_region(
                template_file,
                document_file,
            )
        )


        region_results[
            region_name
        ] = {

            "blocks":
                blocks,

            "region_info":
                region_info,
        }


        for block in blocks:

            all_candidate_blocks.append(
                block
            )


    # =====================================================
    # AUTOMATIC DOCUMENT THRESHOLD
    # =====================================================

    threshold = (
        calculate_candidate_threshold(
            all_candidate_blocks
        )
    )


    final_regions = {}

    suspicious_full_coordinates = []


    # =====================================================
    # SECOND PASS - SELECT SUSPICIOUS BLOCKS
    # =====================================================

    for region_name, data in (
        region_results.items()
    ):

        blocks = (
            data["blocks"]
        )


        region_info = (
            data["region_info"]
        )


        suspicious_blocks = []


        for block in blocks:

            if block[
                "score"
            ] >= threshold:

                suspicious_blocks.append(
                    block
                )


        # -------------------------------------------------
        # MERGE ADJACENT BLOCKS
        # -------------------------------------------------

        merged_blocks = (
            merge_boxes(
                suspicious_blocks
            )
        )


        output_blocks = []


        for block in merged_blocks:

            # =============================================
            # CONVERT ROI COORDINATES TO FULL DOCUMENT
            # =============================================

            full_x1 = (
                region_info["x1"]
                + block["x1"]
            )

            full_y1 = (
                region_info["y1"]
                + block["y1"]
            )

            full_x2 = (
                region_info["x1"]
                + block["x2"]
            )

            full_y2 = (
                region_info["y1"]
                + block["y2"]
            )


            suspicious_area = {

                "region":
                    region_name,

                "reason":
                    "Local text/background/edge inconsistency",

                "score":
                    round(
                        block["score"],
                        4,
                    ),

                "x1":
                    full_x1,

                "y1":
                    full_y1,

                "x2":
                    full_x2,

                "y2":
                    full_y2,
            }


            output_blocks.append(
                suspicious_area
            )


            suspicious_full_coordinates.append(
                suspicious_area
            )


        final_regions[
            region_name
        ] = {

            "total_blocks":
                len(blocks),

            "suspicious_blocks":
                len(output_blocks),

            "locations":
                output_blocks,
        }


    # =====================================================
    # SORT MOST SUSPICIOUS FIRST
    # =====================================================

    suspicious_full_coordinates.sort(

        key=lambda item:
            item["score"],

        reverse=True,
    )


    return {

        "document_type":
            document_type,

        "template":
            template_name,

        "document":
            document_name,

        "candidate_threshold":
            round(
                threshold,
                4,
            ),

        "regions":
            final_regions,

        "suspicious_areas":
            suspicious_full_coordinates,

        "total_suspicious_areas":
            len(
                suspicious_full_coordinates
            ),
    }


# =========================================================
# CREATE HIGHLIGHTED FULL DOCUMENT
# =========================================================

def create_highlighted_document(
    document_type,
    document_name,
    document_image_name,
    result,
):

    image_path = (

        NORMALIZED_FOLDER
        / document_image_name
    )


    if not image_path.exists():

        print(
            f"ERROR: Normalized image missing:"
        )

        print(
            image_path
        )

        return None


    with Image.open(
        image_path
    ) as source_image:

        output_image = (
            source_image.convert(
                "RGB"
            )
        )


    draw = ImageDraw.Draw(
        output_image
    )


    # =====================================================
    # DRAW EACH SUSPICIOUS LOCATION
    # =====================================================

    for position, suspicious in enumerate(
        result[
            "suspicious_areas"
        ],
        start=1,
    ):

        x1 = suspicious["x1"]
        y1 = suspicious["y1"]

        x2 = suspicious["x2"]
        y2 = suspicious["y2"]


        # -------------------------------------------------
        # RECTANGLE
        # -------------------------------------------------

        draw.rectangle(
            [
                x1,
                y1,
                x2,
                y2,
            ],
            outline="red",
            width=4,
        )


        # -------------------------------------------------
        # LABEL
        # -------------------------------------------------

        label = (
            f"{position}: "
            f"{suspicious['region']} "
            f"{suspicious['score']:.0f}"
        )


        label_x = x1

        label_y = max(
            0,
            y1 - 15,
        )


        text_box = (
            draw.textbbox(
                (
                    label_x,
                    label_y,
                ),
                label,
            )
        )


        draw.rectangle(
            text_box,
            fill="white",
        )


        draw.text(
            (
                label_x,
                label_y,
            ),
            label,
            fill="red",
        )


    # =====================================================
    # SAVE
    # =====================================================

    output_folder = (

        HIGHLIGHT_FOLDER
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
            + "_suspicious_text.png"
        )
    )


    output_image.save(
        output_path
    )


    return output_path


# =========================================================
# SAVE JSON
# =========================================================

def save_result(
    document_type,
    result,
):

    output_folder = (

        OUTPUT_FOLDER
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
            + "_altered_text_locations.json"
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
# PRINT RESULT
# =========================================================

def print_result(
    result,
):

    print()
    print("========================================")
    print("ALTERED TEXT LOCALIZATION")
    print("========================================")


    print(
        f"Document: "
        f"{result['document']}"
    )


    print(
        f"Candidate threshold: "
        f"{result['candidate_threshold']:.2f}"
    )


    print(
        f"Suspicious areas: "
        f"{result['total_suspicious_areas']}"
    )


    print()


    for position, area in enumerate(
        result[
            "suspicious_areas"
        ],
        start=1,
    ):

        print(
            f"{position}. "
            f"{area['region']:<20} "
            f"score={area['score']:.2f} "
            f"box=({area['x1']}, "
            f"{area['y1']}) -> "
            f"({area['x2']}, "
            f"{area['y2']})"
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
        "Step 15 - Altered Text Localization"
    )


    for document_type, configuration in (
        DOCUMENTS.items()
    ):

        template_name = (
            configuration[
                "template"
            ]
        )


        for document_name in (
            configuration[
                "documents"
            ]
        ):

            result = (
                analyse_document(
                    document_type,
                    template_name,
                    document_name,
                )
            )


            if result is None:
                continue


            print_result(
                result
            )


            json_path = (
                save_result(
                    document_type,
                    result,
                )
            )


            document_image_name = (

                configuration[
                    "document_images"
                ][
                    document_name
                ]
            )


            image_path = (
                create_highlighted_document(
                    document_type,
                    document_name,
                    document_image_name,
                    result,
                )
            )


            print(
                f"JSON saved: "
                f"{json_path.name}"
            )


            if image_path:

                print(
                    f"Highlight saved: "
                    f"{image_path.name}"
                )


    print()
    print("========================================")
    print("STEP 15 COMPLETE")
    print("========================================")


if __name__ == "__main__":
    main()