from pathlib import Path
import json

from PIL import (
    Image,
    ImageDraw,
)

from src.risk_scoring import (
    calculate_risk_score,
)

from src.document_crop import (
    crop_document,
)
# =========================================================
# IMPORT OUR EXISTING ALGORITHMS
# =========================================================

from src.normalize import (
    resize_image_manually,
)

from src.extract_regions import (
    normalized_to_pixels,
    extract_region_manually,
)

from src.background_analysis import (
    analyse_region as analyse_background_region,
)

from src.compare_background import (
    compare_region as compare_background_region,
)

from src.roi_edge_analysis import (
    analyse_region as analyse_edge_region,
    compare_region as compare_edge_region,
)

from src.text_structure_analysis import (
    analyse_text_region,
    compare_text_region,
)

from src.photo_analysis import (
    analyse_photo_region,
    compare_photo,
)

from src.signature_logo_analysis import (
    analyse_region as analyse_symbol_region,
    compare_region as compare_symbol_region,
)

from src.altered_text_localization import (
    compare_text_region as compare_text_blocks,
    calculate_candidate_threshold,
    merge_boxes,
)


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)


REGION_CONFIG_FILE = (
    PROJECT_ROOT
    / "config"
    / "document_regions.json"
)


# =========================================================
# APPROVED TEMPLATE FILES
# =========================================================

TEMPLATE_FILES = {

    "NIC":
        PROJECT_ROOT
        / "data"
        / "templates"
        / "nic_template_v1.jpg",

    "DRIVING_LICENCE":
        PROJECT_ROOT
        / "data"
        / "templates"
        / "driving_licence_template_v1.jpg",
}


# =========================================================
# LOAD JSON
# =========================================================

def load_json(
    path,
):

    if not path.exists():

        raise FileNotFoundError(
            f"Required file not found: {path}"
        )


    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(
            file
        )


# =========================================================
# SAVE JSON
# =========================================================

def save_json(
    path,
    data,
):

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False,
        )


# =========================================================
# PREPARE NORMALIZED DOCUMENT
# =========================================================

def normalize_submitted_document(
    captured_image_path,
    template_path,
    output_folder,
):

    with Image.open(
        template_path
    ) as template_source:

        template_image = (
            template_source.convert(
                "RGB"
            )
        )


        template_width, template_height = (
            template_image.size
        )


    # =====================================================
    # LOAD SUBMITTED DOCUMENT
    # =====================================================

    with Image.open(
        captured_image_path
    ) as submitted_source:

        submitted_image = (
            submitted_source.convert(
                "RGB"
            )
        )


        normalized_document = (
            resize_image_manually(

                submitted_image,

                template_width,

                template_height,
            )
        )


    # =====================================================
    # OUTPUT FILES
    # =====================================================

    normalized_folder = (
        output_folder
        / "normalized"
    )


    normalized_folder.mkdir(
        parents=True,
        exist_ok=True,
    )


    template_output = (
        normalized_folder
        / "template.png"
    )


    document_output = (
        normalized_folder
        / "document.png"
    )


    template_image.save(
        template_output
    )


    normalized_document.save(
        document_output
    )


    return (
        template_output,
        document_output,
        template_width,
        template_height,
    )


# =========================================================
# EXTRACT TEMPLATE + DOCUMENT REGIONS
# =========================================================

def extract_all_regions(
    document_type,
    template_path,
    document_path,
    configuration,
    output_folder,
):

    regions = (
        configuration[
            document_type
        ][
            "regions"
        ]
    )


    with Image.open(
        template_path
    ) as template_source:

        template_image = (
            template_source.convert(
                "RGB"
            )
        )


    with Image.open(
        document_path
    ) as document_source:

        document_image = (
            document_source.convert(
                "RGB"
            )
        )


    width, height = (
        document_image.size
    )


    template_roi_folder = (
        output_folder
        / "regions"
        / "template"
    )


    document_roi_folder = (
        output_folder
        / "regions"
        / "document"
    )


    template_roi_folder.mkdir(
        parents=True,
        exist_ok=True,
    )


    document_roi_folder.mkdir(
        parents=True,
        exist_ok=True,
    )


    metadata = {}


    # =====================================================
    # PROCESS CONFIGURED ROIS
    # =====================================================

    for region_name, region in (
        regions.items()
    ):

        coordinates = (
            normalized_to_pixels(
                region,
                width,
                height,
            )
        )


        (
            x1,
            y1,
            x2,
            y2,

        ) = coordinates


        # =================================================
        # TEMPLATE ROI
        # =================================================

        template_roi = (
            extract_region_manually(
                template_image,
                coordinates,
            )
        )


        # =================================================
        # DOCUMENT ROI
        # =================================================

        document_roi = (
            extract_region_manually(
                document_image,
                coordinates,
            )
        )


        template_region_path = (

            template_roi_folder
            / f"{region_name}.png"
        )


        document_region_path = (

            document_roi_folder
            / f"{region_name}.png"
        )


        template_roi.save(
            template_region_path
        )


        document_roi.save(
            document_region_path
        )


        metadata[
            region_name
        ] = {

            "type":
                region[
                    "type"
                ],

            "x1":
                x1,

            "y1":
                y1,

            "x2":
                x2,

            "y2":
                y2,

            "template_file":
                str(
                    template_region_path
                ),

            "document_file":
                str(
                    document_region_path
                ),
        }


    save_json(

        output_folder
        / "region_metadata.json",

        metadata,
    )


    return metadata


# =========================================================
# BACKGROUND ANALYSIS
# =========================================================

def run_background_analysis(
    metadata,
):

    results = {}


    for region_name, region in (
        metadata.items()
    ):

        region_type = (
            region[
                "type"
            ]
        )


        # Background comparison is most meaningful
        # for text/security areas.
        if region_type not in {
            "text",
            "security_feature",
        }:

            continue


        template_features = (
            analyse_background_region(

                Path(
                    region[
                        "template_file"
                    ]
                )
            )
        )


        document_features = (
            analyse_background_region(

                Path(
                    region[
                        "document_file"
                    ]
                )
            )
        )


        comparison = (
            compare_background_region(
                template_features,
                document_features,
            )
        )


        results[
            region_name
        ] = {

            "type":
                region_type,

            **comparison,
        }


    return results


# =========================================================
# EDGE ANALYSIS
# =========================================================

def run_edge_analysis(
    metadata,
    output_folder,
):

    results = {}


    edge_folder = (
        output_folder
        / "edge_maps"
    )


    edge_folder.mkdir(
        parents=True,
        exist_ok=True,
    )


    for region_name, region in (
        metadata.items()
    ):

        region_type = (
            region[
                "type"
            ]
        )


        (
            template_features,
            template_edge_image,

        ) = analyse_edge_region(

            Path(
                region[
                    "template_file"
                ]
            )
        )


        (
            document_features,
            document_edge_image,

        ) = analyse_edge_region(

            Path(
                region[
                    "document_file"
                ]
            )
        )


        document_edge_image.save(

            edge_folder
            / f"{region_name}_edges.png"
        )


        comparison = (
            compare_edge_region(
                region_type,
                template_features,
                document_features,
            )
        )


        results[
            region_name
        ] = {

            "type":
                region_type,

            **comparison,
        }


    return results


# =========================================================
# TEXT STRUCTURE ANALYSIS
# =========================================================

def run_text_analysis(
    metadata,
):

    results = {}


    for region_name, region in (
        metadata.items()
    ):

        if (
            region[
                "type"
            ]
            != "text"
        ):

            continue


        (
            template_features,
            _,

        ) = analyse_text_region(

            Path(
                region[
                    "template_file"
                ]
            )
        )


        (
            document_features,
            _,

        ) = analyse_text_region(

            Path(
                region[
                    "document_file"
                ]
            )
        )


        comparison = (
            compare_text_region(
                template_features,
                document_features,
            )
        )


        results[
            region_name
        ] = comparison


    return results


# =========================================================
# PHOTO ANALYSIS
# =========================================================

def run_photo_analysis(
    document_type,
    metadata,
):

    if "photo" not in metadata:

        return None


    region = (
        metadata[
            "photo"
        ]
    )


    template_features = (
        analyse_photo_region(

            Path(
                region[
                    "template_file"
                ]
            )
        )
    )


    document_features = (
        analyse_photo_region(

            Path(
                region[
                    "document_file"
                ]
            )
        )
    )


    # Existing Step 13 compare_photo() expects
    # document-result shaped structures.

    template_result = {

        "document":
            "approved_template",

        "photo_region": {
            "features":
                template_features,
        },
    }


    document_result = {

        "document":
            "submitted_document",

        "photo_region": {
            "features":
                document_features,
        },
    }


    return compare_photo(

        document_type,

        template_result,

        document_result,
    )


# =========================================================
# SIGNATURE / LOGO / SECURITY FEATURE ANALYSIS
# =========================================================

def run_symbol_analysis(
    metadata,
):

    results = {}


    valid_types = {
        "signature",
        "logo",
        "security_feature",
    }


    for region_name, region in (
        metadata.items()
    ):

        region_type = (
            region[
                "type"
            ]
        )


        if (
            region_type
            not in valid_types
        ):

            continue


        (
            template_features,
            _,

        ) = analyse_symbol_region(

            Path(
                region[
                    "template_file"
                ]
            )
        )


        (
            document_features,
            _,

        ) = analyse_symbol_region(

            Path(
                region[
                    "document_file"
                ]
            )
        )


        comparison = (
            compare_symbol_region(
                region_type,
                template_features,
                document_features,
            )
        )


        results[
            region_name
        ] = {

            "type":
                region_type,

            **comparison,
        }


    return results


# =========================================================
# ALTERED TEXT LOCALIZATION
# =========================================================

def run_text_localization(
    metadata,
):

    region_block_results = {}

    all_blocks = []


    # =====================================================
    # CALCULATE BLOCK SCORES
    # =====================================================

    for region_name, region in (
        metadata.items()
    ):

        if (
            region[
                "type"
            ]
            != "text"
        ):

            continue


        blocks = (
            compare_text_blocks(

                Path(
                    region[
                        "template_file"
                    ]
                ),

                Path(
                    region[
                        "document_file"
                    ]
                ),
            )
        )


        region_block_results[
            region_name
        ] = blocks


        all_blocks.extend(
            blocks
        )


    # =====================================================
    # ADAPTIVE THRESHOLD
    # =====================================================

    threshold = (
        calculate_candidate_threshold(
            all_blocks
        )
    )


    suspicious_areas = []


    # =====================================================
    # SELECT + MERGE CANDIDATES
    # =====================================================

    for region_name, blocks in (
        region_block_results.items()
    ):

        region = (
            metadata[
                region_name
            ]
        )


        suspicious_blocks = [

            block

            for block in blocks

            if (
                block[
                    "score"
                ]
                >= threshold
            )
        ]


        merged = (
            merge_boxes(
                suspicious_blocks
            )
        )


        # =================================================
        # ROI COORDINATES -> FULL DOCUMENT COORDINATES
        # =================================================

        for block in merged:

            suspicious_areas.append(
                {

                    "region":
                        region_name,

                    "reason":
                        (
                            "Local text/background/"
                            "edge inconsistency"
                        ),

                    "score":
                        round(
                            block[
                                "score"
                            ],
                            4,
                        ),

                    "x1":
                        region[
                            "x1"
                        ]
                        + block[
                            "x1"
                        ],

                    "y1":
                        region[
                            "y1"
                        ]
                        + block[
                            "y1"
                        ],

                    "x2":
                        region[
                            "x1"
                        ]
                        + block[
                            "x2"
                        ],

                    "y2":
                        region[
                            "y1"
                        ]
                        + block[
                            "y2"
                        ],
                }
            )


    suspicious_areas.sort(

        key=lambda area:
            area[
                "score"
            ],

        reverse=True,
    )


    return {

        "candidate_threshold":
            round(
                threshold,
                4,
            ),

        "suspicious_area_count":
            len(
                suspicious_areas
            ),

        "suspicious_areas":
            suspicious_areas,
    }


# =========================================================
# CREATE HIGHLIGHTED DOCUMENT
# =========================================================

def create_highlighted_document(
    normalized_document_path,
    suspicious_areas,
    output_path,
):

    with Image.open(
        normalized_document_path
    ) as source:

        image = (
            source.convert(
                "RGB"
            )
        )


    draw = ImageDraw.Draw(
        image
    )


    for index, area in enumerate(
        suspicious_areas,
        start=1,
    ):

        x1 = area["x1"]
        y1 = area["y1"]

        x2 = area["x2"]
        y2 = area["y2"]


        # =================================================
        # RED SUSPICIOUS BOX
        # =================================================

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


        label = (
            f"{index}. "
            f"{area['region']} "
            f"{area['score']:.0f}"
        )


        label_y = max(
            0,
            y1 - 14,
        )


        box = draw.textbbox(
            (
                x1,
                label_y,
            ),
            label,
        )


        draw.rectangle(
            box,
            fill="white",
        )


        draw.text(
            (
                x1,
                label_y,
            ),
            label,
            fill="red",
        )


    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


    image.save(
        output_path
    )


# =========================================================
# MAIN COMPONENT 4 PIPELINE
# =========================================================

def run_analysis_pipeline(
    captured_image_path,
    document_type,
    output_folder,
    ocr_validation=None,
):

    captured_image_path = Path(
        captured_image_path
    )


    output_folder = Path(
        output_folder
    )


    output_folder.mkdir(
        parents=True,
        exist_ok=True,
    )


    # =====================================================
    # CHECK DOCUMENT SUPPORT
    # =====================================================

    if (
        document_type
        not in TEMPLATE_FILES
    ):

        return {

            "status":
                "NOT_SUPPORTED",

            "document_type":
                document_type,

            "message":
                (
                    "Alteration analysis template "
                    "is not configured for this "
                    "document type."
                ),
        }


    template_path = (
        TEMPLATE_FILES[
            document_type
        ]
    )


    if not template_path.exists():

        raise FileNotFoundError(
            f"Approved template missing: {template_path}"
        )


    configuration = (
        load_json(
            REGION_CONFIG_FILE
        )
    )


    if (
        document_type
        not in configuration
    ):

        raise ValueError(
            (
                "ROI configuration missing for "
                + document_type
            )
        )

    # =====================================================
    # 0. DOCUMENT CROPPING
    # =====================================================

    preprocessing_folder = (
        output_folder
        / "preprocessing"
    )


    cropped_document_path = (
        preprocessing_folder
        / "cropped_document.png"
    )


    crop_result = (
        crop_document(

            captured_image_path,

            cropped_document_path,
        )
    )


    save_json(

        preprocessing_folder
        / "crop_result.json",

        crop_result,
    )


    # =====================================================
    # 1. NORMALIZATION
    # =====================================================

    (
        normalized_template,
        normalized_document,
        width,
        height,

    ) = normalize_submitted_document(

        cropped_document_path,

        template_path,

        output_folder,
    )


    # =====================================================
    # 2. ROI EXTRACTION
    # =====================================================

    metadata = (
        extract_all_regions(

            document_type,

            normalized_template,

            normalized_document,

            configuration,

            output_folder,
        )
    )


    # =====================================================
    # 3. BACKGROUND ANALYSIS
    # =====================================================

    background_results = (
        run_background_analysis(
            metadata
        )
    )


    save_json(

        output_folder
        / "background_analysis.json",

        background_results,
    )


    # =====================================================
    # 4. EDGE ANALYSIS
    # =====================================================

    edge_results = (
        run_edge_analysis(
            metadata,
            output_folder,
        )
    )


    save_json(

        output_folder
        / "edge_analysis.json",

        edge_results,
    )


    # =====================================================
    # 5. TEXT STRUCTURE ANALYSIS
    # =====================================================

    text_results = (
        run_text_analysis(
            metadata
        )
    )


    save_json(

        output_folder
        / "text_analysis.json",

        text_results,
    )


    # =====================================================
    # 6. PHOTO ANALYSIS
    # =====================================================

    photo_results = (
        run_photo_analysis(
            document_type,
            metadata,
        )
    )


    save_json(

        output_folder
        / "photo_analysis.json",

        photo_results,
    )


    # =====================================================
    # 7. SIGNATURE / LOGO ANALYSIS
    # =====================================================

    symbol_results = (
        run_symbol_analysis(
            metadata
        )
    )


    save_json(

        output_folder
        / "symbol_analysis.json",

        symbol_results,
    )


    # =====================================================
    # 8. ALTERED TEXT LOCALIZATION
    # =====================================================

    localization_results = (
        run_text_localization(
            metadata
        )
    )


    save_json(

        output_folder
        / "altered_text_localization.json",

        localization_results,
    )


    # =====================================================
    # 9. CREATE HIGHLIGHTED IMAGE
    # =====================================================

    highlighted_path = (

        output_folder
        / "highlighted_suspicious_areas.png"
    )


    create_highlighted_document(

        normalized_document,

        localization_results[
            "suspicious_areas"
        ],

        highlighted_path,
    )

    # =====================================================
    # 10. RISK SCORING
    # =====================================================

    analysis_for_risk = {

        "background_analysis":
            background_results,

        "edge_analysis":
            edge_results,

        "text_analysis":
            text_results,

        "photo_analysis":
            photo_results,

        "symbol_analysis":
            symbol_results,

        "altered_text_localization":
            localization_results,
    }


    risk_result = (
        calculate_risk_score(

            analysis_for_risk,

            ocr_validation=
                ocr_validation,
        )
    )


    # =====================================================
    # SAVE RISK RESULT
    # =====================================================

    save_json(

        output_folder
        / "risk_score.json",

        risk_result,
    )

    # =====================================================
    # COMPLETE RESULT
    # =====================================================

    result = {

        "status":
            "COMPLETE",

        "document_type":
            document_type,

        "template":
            template_path.name,

        "normalized_width":
            width,

        "normalized_height":
            height,

        "region_count":
            len(
                metadata
            ),

        "background_analysis":
            background_results,

        "edge_analysis":
            edge_results,

        "text_analysis":
            text_results,

        "photo_analysis":
            photo_results,

        "symbol_analysis":
            symbol_results,

        "altered_text_localization":
            localization_results,

        "suspicious_area_count":
            localization_results[
                "suspicious_area_count"
            ],

        "highlighted_image":
            highlighted_path.name,

        # Final risk scoring is Step 20.
        "risk_score":
            risk_result[
                "risk_score"
            ],

        "risk_level":
            risk_result[
                "risk_level"
            ],

        "recommended_action":
            risk_result[
                "recommended_action"
            ],

        "risk_details":
            risk_result,
    }


    save_json(

        output_folder
        / "analysis_result.json",

        result,
    )


    return result