# =========================================================
# DOCUMENT ALTERATION DETECTION
# STEP 20 - RISK SCORING ENGINE
# =========================================================


# =========================================================
# COMPONENT WEIGHTS
# =========================================================
#
# Total = 1.00
#
# OCR receives a smaller weight because OCR errors can
# happen because of lighting, language, quality, etc.
#
# =========================================================

COMPONENT_WEIGHTS = {

    "background": 0.18,

    "edge": 0.18,

    "text": 0.18,

    "photo": 0.12,

    "symbol": 0.10,

    "localization": 0.16,

    "ocr": 0.08,
}


# =========================================================
# RISK THRESHOLDS
# =========================================================

LOW_RISK_LIMIT = 35.0

HIGH_RISK_LIMIT = 65.0


# A detector score above this value is treated as
# meaningful independent visual evidence.
STRONG_EVIDENCE_THRESHOLD = 45.0


# =========================================================
# SCORE LIMIT
# =========================================================

def clamp_score(
    value,
):

    try:

        value = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return 0.0


    if value < 0:
        return 0.0


    if value > 100:
        return 100.0


    return value


# =========================================================
# COLLECT REGION SCORES
# =========================================================

def collect_region_scores(
    analysis,
    score_key,
):

    scores = []


    if not isinstance(
        analysis,
        dict,
    ):

        return scores


    for region_name, region in (
        analysis.items()
    ):

        if not isinstance(
            region,
            dict,
        ):

            continue


        value = region.get(
            score_key
        )


        if isinstance(
            value,
            (
                int,
                float,
            ),
        ):

            scores.append(
                clamp_score(
                    value
                )
            )


    return scores


# =========================================================
# TOP SCORE AVERAGE
# =========================================================
#
# We do not average every field because one heavily
# altered region could otherwise be hidden by many
# normal regions.
#
# =========================================================

def calculate_top_average(
    scores,
    maximum_items=3,
):

    if not scores:

        return 0.0


    sorted_scores = sorted(
        scores,
        reverse=True,
    )


    selected = (
        sorted_scores[
            :maximum_items
        ]
    )


    return (
        sum(selected)
        / len(selected)
    )


# =========================================================
# STRONGEST REGION
# =========================================================

def find_strongest_region(
    analysis,
    score_key,
):

    best_region = None

    best_score = 0.0


    if not isinstance(
        analysis,
        dict,
    ):

        return (
            None,
            0.0,
        )


    for region_name, data in (
        analysis.items()
    ):

        if not isinstance(
            data,
            dict,
        ):

            continue


        score = clamp_score(
            data.get(
                score_key,
                0,
            )
        )


        if score > best_score:

            best_score = score

            best_region = (
                region_name
            )


    return (
        best_region,
        best_score,
    )


# =========================================================
# LOCALIZED ALTERATION SCORE
# =========================================================

def calculate_localization_score(
    localization,
):

    if not isinstance(
        localization,
        dict,
    ):

        return 0.0


    suspicious_areas = (
        localization.get(
            "suspicious_areas",
            [],
        )
    )


    if not suspicious_areas:

        return 0.0


    scores = []


    for area in suspicious_areas:

        if not isinstance(
            area,
            dict,
        ):

            continue


        scores.append(
            clamp_score(
                area.get(
                    "score",
                    0,
                )
            )
        )


    if not scores:

        return 0.0


    # =====================================================
    # SEVERITY
    # =====================================================

    strongest_area = max(
        scores
    )


    # =====================================================
    # NUMBER OF LOCATIONS
    # =====================================================
    #
    # 1 area  = 20
    # 2 areas = 40
    # ...
    # 5+      = 100
    #
    # =====================================================

    count_score = min(
        100.0,
        len(scores) * 20.0,
    )


    # Severity is more important than count.
    final_score = (

        strongest_area
        * 0.75

        +

        count_score
        * 0.25
    )


    return clamp_score(
        final_score
    )


# =========================================================
# OCR REVIEW SCORE
# =========================================================
#
# OCR problems are supporting evidence only.
# They must never independently prove fraud.
#
# =========================================================

OCR_ISSUE_WEIGHTS = {

    # Identification format problems.
    "INVALID_NIC_FORMAT": 30,

    "INVALID_LICENCE_NUMBER": 30,

    "NIC_TEXT_INCONSISTENCY": 25,

    "LICENCE_TEXT_INCONSISTENCY": 25,


    # Missing important OCR values.
    "NIC_NUMBER_MISSING": 15,

    "LICENCE_NUMBER_MISSING": 15,

    "NAME_MISSING": 10,

    "DATE_MISSING": 10,


    # Format problems.
    "INVALID_DATE_FORMAT": 15,

    "INVALID_NAME_FORMAT": 10,

    "INVALID_BLOOD_GROUP": 10,


    # General OCR problems.
    "OCR_TEXT_EMPTY": 15,

    "INVALID_DATE_LIST": 10,

    "INVALID_FIELDS_STRUCTURE": 10,

    "INVALID_LINES_STRUCTURE": 10,


    # Bounding-box problems.
    "INVALID_BOUNDING_BOX": 8,

    "INCOMPLETE_BOUNDING_BOX": 8,

    "INVALID_BOUNDING_BOX_VALUES": 8,

    "INVALID_BOUNDING_BOX_SIZE": 8,

    "BOUNDING_BOX_OUTSIDE_IMAGE": 8,


    # Other.
    "OCR_VALIDATION_NOT_CONFIGURED": 5,

    "IMAGE_READ_ERROR": 10,
}


def calculate_ocr_score(
    ocr_validation,
):

    if not isinstance(
        ocr_validation,
        dict,
    ):

        return 0.0


    issues = (
        ocr_validation.get(
            "issues",
            [],
        )
    )


    if not isinstance(
        issues,
        list,
    ):

        return 0.0


    score = 0.0


    for issue in issues:

        if not isinstance(
            issue,
            dict,
        ):

            continue


        issue_code = (
            issue.get(
                "code",
                "",
            )
        )


        score += (
            OCR_ISSUE_WEIGHTS.get(
                issue_code,
                8,
            )
        )


    # OCR cannot produce more than 50/100
    # before its main weight is applied.
    return min(
        score,
        50.0,
    )


# =========================================================
# CALCULATE COMPONENT SCORES
# =========================================================

def calculate_component_scores(
    alteration_analysis,
    ocr_validation=None,
):

    # =====================================================
    # BACKGROUND
    # =====================================================

    background_scores = (
        collect_region_scores(

            alteration_analysis.get(
                "background_analysis",
                {},
            ),

            "background_difference_score",
        )
    )


    background_score = (
        calculate_top_average(
            background_scores,
            maximum_items=3,
        )
    )


    # =====================================================
    # EDGE
    # =====================================================

    edge_scores = (
        collect_region_scores(

            alteration_analysis.get(
                "edge_analysis",
                {},
            ),

            "edge_difference_score",
        )
    )


    edge_score = (
        calculate_top_average(
            edge_scores,
            maximum_items=3,
        )
    )


    # =====================================================
    # TEXT STRUCTURE
    # =====================================================

    text_scores = (
        collect_region_scores(

            alteration_analysis.get(
                "text_analysis",
                {},
            ),

            "text_structure_difference_score",
        )
    )


    text_score = (
        calculate_top_average(
            text_scores,
            maximum_items=3,
        )
    )


    # =====================================================
    # PHOTO
    # =====================================================

    photo_analysis = (
        alteration_analysis.get(
            "photo_analysis"
        )
    )


    if isinstance(
        photo_analysis,
        dict,
    ):

        photo_score = clamp_score(

            photo_analysis.get(
                "photo_border_difference_score",
                0,
            )
        )

    else:

        photo_score = 0.0


    # =====================================================
    # SYMBOL / LOGO / SIGNATURE
    # =====================================================

    symbol_scores = (
        collect_region_scores(

            alteration_analysis.get(
                "symbol_analysis",
                {},
            ),

            "symbol_difference_score",
        )
    )


    symbol_score = (
        calculate_top_average(
            symbol_scores,
            maximum_items=2,
        )
    )


    # =====================================================
    # LOCAL ALTERATION
    # =====================================================

    localization_score = (
        calculate_localization_score(

            alteration_analysis.get(
                "altered_text_localization",
                {},
            )
        )
    )


    # =====================================================
    # OCR
    # =====================================================

    ocr_score = (
        calculate_ocr_score(
            ocr_validation
        )
    )


    return {

        "background":
            round(
                background_score,
                4,
            ),

        "edge":
            round(
                edge_score,
                4,
            ),

        "text":
            round(
                text_score,
                4,
            ),

        "photo":
            round(
                photo_score,
                4,
            ),

        "symbol":
            round(
                symbol_score,
                4,
            ),

        "localization":
            round(
                localization_score,
                4,
            ),

        "ocr":
            round(
                ocr_score,
                4,
            ),
    }


# =========================================================
# BUILD FINDINGS
# =========================================================

def build_findings(
    alteration_analysis,
    component_scores,
    ocr_validation,
):

    findings = []


    # =====================================================
    # BACKGROUND
    # =====================================================

    region, score = (
        find_strongest_region(

            alteration_analysis.get(
                "background_analysis",
                {},
            ),

            "background_difference_score",
        )
    )


    if (
        region is not None
        and score >= 30
    ):

        findings.append(
            {
                "category":
                    "BACKGROUND",

                "region":
                    region,

                "score":
                    round(
                        score,
                        2,
                    ),

                "message":
                    (
                        "Unusual background or "
                        "texture characteristics detected."
                    ),
            }
        )


    # =====================================================
    # EDGE
    # =====================================================

    region, score = (
        find_strongest_region(

            alteration_analysis.get(
                "edge_analysis",
                {},
            ),

            "edge_difference_score",
        )
    )


    if (
        region is not None
        and score >= 30
    ):

        findings.append(
            {
                "category":
                    "EDGE",

                "region":
                    region,

                "score":
                    round(
                        score,
                        2,
                    ),

                "message":
                    (
                        "Unusual edge structure "
                        "detected in this region."
                    ),
            }
        )


    # =====================================================
    # TEXT STRUCTURE
    # =====================================================

    region, score = (
        find_strongest_region(

            alteration_analysis.get(
                "text_analysis",
                {},
            ),

            "text_structure_difference_score",
        )
    )


    if (
        region is not None
        and score >= 30
    ):

        findings.append(
            {
                "category":
                    "TEXT_STRUCTURE",

                "region":
                    region,

                "score":
                    round(
                        score,
                        2,
                    ),

                "message":
                    (
                        "Text size, spacing or "
                        "alignment differs from "
                        "the reference structure."
                    ),
            }
        )


    # =====================================================
    # PHOTO
    # =====================================================

    photo_score = (
        component_scores[
            "photo"
        ]
    )


    if photo_score >= 30:

        findings.append(
            {
                "category":
                    "PHOTO",

                "region":
                    "photo",

                "score":
                    round(
                        photo_score,
                        2,
                    ),

                "message":
                    (
                        "Photo-border characteristics "
                        "differ from the approved template."
                    ),
            }
        )


    # =====================================================
    # SYMBOL
    # =====================================================

    region, score = (
        find_strongest_region(

            alteration_analysis.get(
                "symbol_analysis",
                {},
            ),

            "symbol_difference_score",
        )
    )


    if (
        region is not None
        and score >= 30
    ):

        findings.append(
            {
                "category":
                    "SYMBOL",

                "region":
                    region,

                "score":
                    round(
                        score,
                        2,
                    ),

                "message":
                    (
                        "Signature, logo or security "
                        "feature structure is inconsistent."
                    ),
            }
        )


    # =====================================================
    # LOCALIZED ALTERATION
    # =====================================================

    localization = (
        alteration_analysis.get(
            "altered_text_localization",
            {},
        )
    )


    suspicious_count = (
        localization.get(
            "suspicious_area_count",
            0,
        )
        if isinstance(
            localization,
            dict,
        )
        else 0
    )


    if suspicious_count > 0:

        findings.append(
            {
                "category":
                    "LOCALIZED_ALTERATION",

                "region":
                    "multiple"
                    if suspicious_count > 1
                    else "text_region",

                "score":
                    round(
                        component_scores[
                            "localization"
                        ],
                        2,
                    ),

                "message":
                    (
                        f"{suspicious_count} local "
                        "visual inconsistency area(s) "
                        "were detected."
                    ),
            }
        )


    # =====================================================
    # OCR
    # =====================================================

    if isinstance(
        ocr_validation,
        dict,
    ):

        issues = (
            ocr_validation.get(
                "issues",
                [],
            )
        )


        if issues:

            findings.append(
                {
                    "category":
                        "OCR_VALIDATION",

                    "region":
                        "document_text",

                    "score":
                        round(
                            component_scores[
                                "ocr"
                            ],
                            2,
                        ),

                    "message":
                        (
                            f"{len(issues)} OCR "
                            "validation issue(s) "
                            "require review."
                        ),
                }
            )


    # =====================================================
    # HIGHEST FIRST
    # =====================================================

    findings.sort(

        key=lambda finding:
            finding[
                "score"
            ],

        reverse=True,
    )


    return findings


# =========================================================
# CALCULATE FINAL RISK
# =========================================================

def calculate_risk_score(
    alteration_analysis,
    ocr_validation=None,
):

    if not isinstance(
        alteration_analysis,
        dict,
    ):

        raise ValueError(
            "Alteration analysis must be a dictionary."
        )


    # =====================================================
    # COMPONENT SCORES
    # =====================================================

    component_scores = (
        calculate_component_scores(
            alteration_analysis,
            ocr_validation,
        )
    )


    # =====================================================
    # WEIGHTED SCORE
    # =====================================================

    weighted_breakdown = {}


    final_score = 0.0


    for component, weight in (
        COMPONENT_WEIGHTS.items()
    ):

        score = (
            component_scores[
                component
            ]
        )


        weighted_value = (
            score * weight
        )


        weighted_breakdown[
            component
        ] = {

            "score":
                round(
                    score,
                    4,
                ),

            "weight":
                weight,

            "weighted_value":
                round(
                    weighted_value,
                    4,
                ),
        }


        final_score += (
            weighted_value
        )


    final_score = (
        clamp_score(
            final_score
        )
    )


    # =====================================================
    # INDEPENDENT VISUAL EVIDENCE
    # =====================================================
    #
    # OCR is intentionally not counted here.
    #
    # =====================================================

    visual_components = [

        "background",

        "edge",

        "text",

        "photo",

        "symbol",

        "localization",
    ]


    strong_evidence_sources = []


    for component in visual_components:

        if (
            component_scores[
                component
            ]
            >= STRONG_EVIDENCE_THRESHOLD
        ):

            strong_evidence_sources.append(
                component
            )


    evidence_count = len(
        strong_evidence_sources
    )


    # =====================================================
    # RISK LEVEL
    # =====================================================

    if final_score < LOW_RISK_LIMIT:

        risk_level = (
            "LOW"
        )


        recommended_action = (
            "CONTINUE_NORMAL_PROCESS"
        )


    elif final_score < HIGH_RISK_LIMIT:

        risk_level = (
            "MEDIUM"
        )


        recommended_action = (
            "MANUAL_REVIEW_REQUIRED"
        )


    else:

        # ================================================
        # HIGH requires evidence from more than one
        # independent visual detector.
        # ================================================

        if evidence_count >= 2:

            risk_level = (
                "HIGH"
            )


            recommended_action = (
                "FRAUD_INVESTIGATOR_REVIEW_REQUIRED"
            )


        else:

            # High numeric score from only one detector
            # is not enough to declare HIGH automatically.
            risk_level = (
                "MEDIUM"
            )


            recommended_action = (
                "MANUAL_REVIEW_REQUIRED"
            )


    # =====================================================
    # FINDINGS
    # =====================================================

    findings = (
        build_findings(
            alteration_analysis,
            component_scores,
            ocr_validation,
        )
    )


    # =====================================================
    # RESULT
    # =====================================================

    return {

        "risk_score":
            round(
                final_score,
                2,
            ),

        "risk_level":
            risk_level,

        "recommended_action":
            recommended_action,

        "component_scores":
            component_scores,

        "weighted_breakdown":
            weighted_breakdown,

        "strong_evidence_count":
            evidence_count,

        "strong_evidence_sources":
            strong_evidence_sources,

        "finding_count":
            len(findings),

        "findings":
            findings,

        "thresholds":
            {
                "low":
                    "0.00 - 34.99",

                "medium":
                    "35.00 - 64.99",

                "high":
                    "65.00 - 100.00 with at least two strong visual evidence sources",

                "strong_evidence_threshold":
                    STRONG_EVIDENCE_THRESHOLD,
            },

        "decision_note":
            (
                "The risk score identifies possible "
                "document alterations and is not a "
                "fraud probability or final fraud decision. "
                "Medium and High results require manual review."
            ),
    }