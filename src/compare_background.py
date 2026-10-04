from pathlib import Path
import json


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BACKGROUND_FOLDER = (
    PROJECT_ROOT
    / "results"
    / "background_analysis"
)

COMPARISON_FOLDER = (
    PROJECT_ROOT
    / "results"
    / "background_comparisons"
)


# =========================================================
# DOCUMENT CONFIGURATION
# =========================================================

DOCUMENTS = {

    "NIC": {
        "folder": "nic",

        "template":
            "nic_template_v1_normalized_background_features.json",

        "documents": [
            "nic_genuine_01_normalized_background_features.json",
            "nic_altered_01_normalized_background_features.json",
        ],
    },

    "DRIVING_LICENCE": {
        "folder": "driving_licence",

        "template":
            "driving_licence_template_v1_normalized_background_features.json",

        "documents": [
            "driving_licence_genuine_01_normalized_background_features.json",
            "driving_licence_altered_01_normalized_background_features.json",
        ],
    },
}


# =========================================================
# REGIONS USED FOR BACKGROUND COMPARISON
# =========================================================

ANALYSED_REGION_TYPES = {
    "text",
    "security_feature",
}


# =========================================================
# FEATURE WEIGHTS
# =========================================================

FEATURE_WEIGHTS = {

    "mean_brightness": 0.20,

    "brightness_stddev": 0.20,

    "bright_pixel_ratio": 0.10,

    "neighbour_difference": 0.25,

    "block_mean_stddev": 0.25,
}


# =========================================================
# MINIMUM REFERENCE VALUES
# =========================================================
#
# Prevent very small template values from creating
# extremely large percentage differences.
#
# =========================================================

FEATURE_FLOORS = {

    "mean_brightness": 20.0,

    "brightness_stddev": 5.0,

    "bright_pixel_ratio": 5.0,

    "neighbour_difference": 2.0,

    "block_mean_stddev": 5.0,
}


# =========================================================
# LOAD JSON
# =========================================================

def load_json(file_path):

    if not file_path.exists():

        print()
        print("ERROR: Required file not found.")
        print(file_path)

        return None


    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


# =========================================================
# NORMALIZED FEATURE DIFFERENCE
# =========================================================

def calculate_feature_difference(
    template_value,
    document_value,
    minimum_reference,
):
    """
    Calculate the relative difference between one
    document feature and its template feature.

    Output is limited to 0-100.
    """

    difference = abs(
        document_value
        - template_value
    )


    denominator = max(
        abs(template_value),
        minimum_reference,
    )


    percentage_difference = (
        difference
        / denominator
    ) * 100


    # Prevent a single feature from dominating
    # the combined comparison score.
    if percentage_difference > 100:

        percentage_difference = 100


    if percentage_difference < 0:

        percentage_difference = 0


    return percentage_difference


# =========================================================
# COMPARE ONE REGION
# =========================================================

def compare_region(
    template_features,
    document_features,
):
    """
    Compare selected background and texture features
    for one corresponding ROI.
    """

    feature_results = {}

    weighted_total = 0.0

    weight_total = 0.0


    for feature_name, weight in (
        FEATURE_WEIGHTS.items()
    ):

        # -------------------------------------------------
        # CHECK FEATURE EXISTS
        # -------------------------------------------------

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


        minimum_reference = (
            FEATURE_FLOORS[
                feature_name
            ]
        )


        # -------------------------------------------------
        # CALCULATE DIFFERENCE
        # -------------------------------------------------

        difference = (
            calculate_feature_difference(
                template_value,
                document_value,
                minimum_reference,
            )
        )


        # -------------------------------------------------
        # STORE FEATURE RESULT
        # -------------------------------------------------

        feature_results[
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


        weight_total += weight


    # -----------------------------------------------------
    # FINAL REGION DIFFERENCE SCORE
    # -----------------------------------------------------

    if weight_total == 0:

        region_score = 0.0

    else:

        region_score = (
            weighted_total
            / weight_total
        )


    if region_score > 100:

        region_score = 100


    return {

        "background_difference_score":
            round(
                region_score,
                4,
            ),

        "feature_comparisons":
            feature_results,
    }


# =========================================================
# COMPARE ONE DOCUMENT
# =========================================================

def compare_document(
    document_type,
    template_data,
    document_data,
):
    """
    Compare corresponding template and submitted
    document regions.
    """

    result = {

        "document_type":
            document_type,

        "template_image":
            template_data[
                "source_image"
            ],

        "document_image":
            document_data[
                "source_image"
            ],

        "regions": {},

        "ranked_candidate_regions": [],
    }


    template_regions = (
        template_data[
            "regions"
        ]
    )


    document_regions = (
        document_data[
            "regions"
        ]
    )


    # =====================================================
    # COMPARE REGIONS
    # =====================================================

    ranking = []


    for region_name, document_region in (
        document_regions.items()
    ):

        # -------------------------------------------------
        # REGION MUST EXIST IN TEMPLATE
        # -------------------------------------------------

        if region_name not in template_regions:

            continue


        region_type = (
            document_region[
                "type"
            ]
        )


        # -------------------------------------------------
        # ONLY BACKGROUND-RELEVANT REGION TYPES
        # -------------------------------------------------

        if region_type not in ANALYSED_REGION_TYPES:

            continue


        template_region = (
            template_regions[
                region_name
            ]
        )


        template_features = (
            template_region[
                "features"
            ]
        )


        document_features = (
            document_region[
                "features"
            ]
        )


        comparison = (
            compare_region(
                template_features,
                document_features,
            )
        )


        score = (
            comparison[
                "background_difference_score"
            ]
        )


        result["regions"][
            region_name
        ] = {

            "type":
                region_type,

            "background_difference_score":
                score,

            "feature_comparisons":
                comparison[
                    "feature_comparisons"
                ],
        }


        ranking.append(
            {
                "region":
                    region_name,

                "type":
                    region_type,

                "background_difference_score":
                    score,
            }
        )


    # =====================================================
    # SORT HIGHEST DIFFERENCE FIRST
    # =====================================================

    ranking.sort(
        key=lambda item:
            item[
                "background_difference_score"
            ],
        reverse=True,
    )


    result[
        "ranked_candidate_regions"
    ] = ranking


    # =====================================================
    # DOCUMENT-LEVEL BACKGROUND DIFFERENCE
    # =====================================================

    if ranking:

        total = 0.0


        for item in ranking:

            total += (
                item[
                    "background_difference_score"
                ]
            )


        average_score = (
            total
            / len(ranking)
        )

    else:

        average_score = 0.0


    result[
        "average_background_difference_score"
    ] = round(
        average_score,
        4,
    )


    return result


# =========================================================
# PRINT RESULT
# =========================================================

def print_comparison(
    result,
):

    print()
    print("========================================")
    print("BACKGROUND TEMPLATE COMPARISON")
    print("========================================")

    print(
        f"Document type: "
        f"{result['document_type']}"
    )

    print(
        f"Document: "
        f"{result['document_image']}"
    )

    print(
        f"Template: "
        f"{result['template_image']}"
    )

    print()

    print(
        "Regions ranked from highest "
        "difference to lowest:"
    )

    print()


    for position, item in enumerate(
        result[
            "ranked_candidate_regions"
        ],
        start=1,
    ):

        print(
            f"{position}. "
            f"{item['region']:<22} "
            f"{item['background_difference_score']:.2f}"
        )


    print()

    print(
        "Average background difference: "
        f"{result['average_background_difference_score']:.2f}"
    )

    print("========================================")


# =========================================================
# SAVE RESULT
# =========================================================

def save_result(
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


    document_name = Path(
        result[
            "document_image"
        ]
    ).stem


    output_path = (

        output_folder
        / (
            document_name
            + "_background_comparison.json"
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


    print(
        f"Saved comparison: "
        f"{output_path.name}"
    )


# =========================================================
# PROCESS DOCUMENT TYPE
# =========================================================

def process_document_type(
    document_type,
    configuration,
):

    folder = (

        BACKGROUND_FOLDER
        / configuration[
            "folder"
        ]
    )


    template_path = (

        folder
        / configuration[
            "template"
        ]
    )


    template_data = (
        load_json(
            template_path
        )
    )


    if template_data is None:

        return 0


    successful = 0


    for document_filename in (
        configuration[
            "documents"
        ]
    ):

        document_path = (
            folder
            / document_filename
        )


        document_data = (
            load_json(
                document_path
            )
        )


        if document_data is None:

            continue


        result = (
            compare_document(
                document_type,
                template_data,
                document_data,
            )
        )


        print_comparison(
            result
        )


        save_result(
            document_type,
            result,
        )


        successful += 1


    return successful


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print(
        "Document Alteration Detection Module"
    )

    print(
        "Step 10 - Background Template Comparison"
    )


    processed = 0


    for document_type, configuration in (
        DOCUMENTS.items()
    ):

        processed += (
            process_document_type(
                document_type,
                configuration,
            )
        )


    print()
    print("========================================")

    print(
        f"Documents compared: "
        f"{processed}"
    )

    print("========================================")


if __name__ == "__main__":
    main()