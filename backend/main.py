from pathlib import Path
from datetime import datetime, timezone
import json
import uuid

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from src.ocr_validation import (
    validate_ocr_payload,
)

from src.analysis_pipeline import (
    run_analysis_pipeline,
)

from fastapi.responses import FileResponse


# =========================================================
# APPLICATION
# =========================================================

app = FastAPI(
    title="Document Alteration Detection API",
    version="1.1.0",
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

REQUEST_FOLDER = (
    PROJECT_ROOT
    / "results"
    / "api_requests"
)


# =========================================================
# SETTINGS
# =========================================================

MAX_IMAGE_SIZE = (
    15
    * 1024
    * 1024
)


ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
}


# =========================================================
# DOCUMENT TYPE MAPPING
# =========================================================

DOCUMENT_TYPE_MAPPING = {

    "National_Identity_Card":
        "NIC",

    "Driving_Licence":
        "DRIVING_LICENCE",

    "Salary_Slip":
        "SALARY_SLIP",

    "Bank_Statement":
        "BANK_STATEMENT",

    "Utility_Bill":
        "UTILITY_BILL",

    "Other_Certificate":
        "OTHER_CERTIFICATE",
}


CURRENTLY_SUPPORTED = {
    "NIC",
    "DRIVING_LICENCE",
}


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health_check():

    return {
        "status": "OK",
        "component":
            "Document Alteration Detection Module",
        "version":
            "1.1.0",
    }


# =========================================================
# DOCUMENT SUBMISSION
# =========================================================

@app.post(
    "/api/v1/analyze-document"
)
async def analyze_document(

    image: UploadFile = File(...),

    document_type: str = Form(...),

    ocr_json: str = Form(...),
):

    # =====================================================
    # DOCUMENT TYPE
    # =====================================================

    internal_document_type = (
        DOCUMENT_TYPE_MAPPING.get(
            document_type
        )
    )

    if internal_document_type is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported document type: "
                f"{document_type}"
            ),
        )


    # =====================================================
    # IMAGE TYPE
    # =====================================================

    content_type = (
        image.content_type
        or ""
    )

    if (
        content_type
        not in ALLOWED_IMAGE_TYPES
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Only JPEG and PNG images "
                "are accepted."
            ),
        )


    # =====================================================
    # READ IMAGE
    # =====================================================

    image_bytes = (
        await image.read()
    )

    if not image_bytes:

        raise HTTPException(
            status_code=400,
            detail="Received image is empty.",
        )

    if (
        len(image_bytes)
        > MAX_IMAGE_SIZE
    ):

        raise HTTPException(
            status_code=413,
            detail="Image exceeds 15 MB limit.",
        )


    # =====================================================
    # OCR JSON
    # =====================================================

    try:

        ocr_data = json.loads(
            ocr_json
        )

    except json.JSONDecodeError:

        raise HTTPException(
            status_code=400,
            detail="Invalid OCR JSON.",
        )


    if not isinstance(
        ocr_data,
        dict,
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "OCR payload must "
                "be a JSON object."
            ),
        )


    # =====================================================
    # DOCUMENT ID
    # =====================================================

    document_id = str(
        uuid.uuid4()
    )

    received_at = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )


    # =====================================================
    # REQUEST FOLDER
    # =====================================================

    document_folder = (
        REQUEST_FOLDER
        / document_id
    )

    document_folder.mkdir(
        parents=True,
        exist_ok=False,
    )


    # =====================================================
    # SAVE ORIGINAL IMAGE
    # =====================================================

    extension = (
        ".png"
        if content_type == "image/png"
        else ".jpg"
    )

    image_path = (
        document_folder
        / (
            "captured_document"
            + extension
        )
    )

    image_path.write_bytes(
        image_bytes
    )


    # =====================================================
    # SAVE RAW OCR RESULT
    # =====================================================

    ocr_path = (
        document_folder
        / "ocr.json"
    )

    with open(
        ocr_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            ocr_data,
            file,
            indent=4,
            ensure_ascii=False,
        )


    # =====================================================
    # STEP 18 - OCR VALIDATION
    # =====================================================

    try:

        ocr_validation = (
            validate_ocr_payload(
                ocr_data,
                internal_document_type,
                image_path,
            )
        )

    except Exception as exception:

        ocr_validation = {

            "document_type":
                internal_document_type,

            "status":
                "REVIEW",

            "issue_count":
                1,

            "issues": [

                {
                    "code":
                        "OCR_VALIDATION_ERROR",

                    "field":
                        "ocr",

                    "message":
                        str(
                            exception
                        ),
                }
            ],
        }


    validation_path = (
        document_folder
        / "ocr_validation.json"
    )

    with open(
        validation_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            ocr_validation,
            file,
            indent=4,
            ensure_ascii=False,
        )


    # =====================================================
    # STEP 19 - PHYSICAL ALTERATION ANALYSIS
    # =====================================================

    analysis_folder = (
        document_folder
        / "analysis"
    )

    analysis_folder.mkdir(
        parents=True,
        exist_ok=True,
    )


    try:

        alteration_analysis = (
            run_analysis_pipeline(

                captured_image_path=
                    image_path,

                document_type=
                    internal_document_type,

                output_folder=
                    analysis_folder,

                ocr_validation=
                    ocr_validation,
            )
        )

        analysis_status = (
            alteration_analysis.get(
                "status",
                "UNKNOWN",
            )
        )


    except Exception as exception:

        alteration_analysis = {

            "status":
                "ERROR",

            "error":
                str(
                    exception
                ),
        }

        analysis_status = (
            "ERROR"
        )

        with open(
            analysis_folder
            / "analysis_error.json",
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                alteration_analysis,
                file,
                indent=4,
            )


    # =====================================================
    # REQUEST METADATA
    # =====================================================

    metadata = {

        "document_id":
            document_id,

        "android_document_type":
            document_type,

        "internal_document_type":
            internal_document_type,

        "received_at":
            received_at,

        "image_file":
            image_path.name,

        "image_size_bytes":
            len(image_bytes),

        "ocr_available":
            bool(
                ocr_data.get(
                    "fullText"
                )
            ),

        "ocr_line_count":
            len(
                ocr_data.get(
                    "lines",
                    [],
                )
            ),

        "ocr_validation_status":
            ocr_validation[
                "status"
            ],

        "ocr_issue_count":
            ocr_validation[
                "issue_count"
            ],

        "analysis_supported":
            (
                internal_document_type
                in CURRENTLY_SUPPORTED
            ),

        "alteration_analysis_status":
            analysis_status,

        "suspicious_area_count":
            alteration_analysis.get(
                "suspicious_area_count",
                0,
            ),
    }


    metadata_path = (
        document_folder
        / "request.json"
    )

    with open(
        metadata_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            indent=4,
        )


    # =====================================================
    # RESPONSE
    # =====================================================

    return {

        "success":
            True,

        "document_id":
            document_id,

        "document_type":
            internal_document_type,

        "analysis_supported":
            (
                internal_document_type
                in CURRENTLY_SUPPORTED
            ),

        "ocr_received":
            metadata[
                "ocr_available"
            ],

        "ocr_line_count":
            metadata[
                "ocr_line_count"
            ],

        "ocr_validation_status":
            ocr_validation[
                "status"
            ],

        "ocr_issue_count":
            ocr_validation[
                "issue_count"
            ],

        "ocr_issues":
            ocr_validation[
                "issues"
            ],

        "message":
            "Document received and OCR validated successfully.",

        "alteration_analysis_status":
            analysis_status,

        "suspicious_area_count":
            alteration_analysis.get(
                "suspicious_area_count",
                0,
            ),

        "highlighted_image":
            alteration_analysis.get(
                "highlighted_image"
            ),

        "risk_score":
            alteration_analysis.get(
                "risk_score"
            ),

        "risk_level":
            alteration_analysis.get(
                "risk_level"
            ),

        "recommended_action":
            alteration_analysis.get(
                "recommended_action"
            ),

        "next_stage":
            "RESULT_READY",
    }


# =========================================================
# ADMIN DASHBOARD HELPERS
# =========================================================

def load_json_if_exists(
    path: Path,
):

    if not path.exists():
        return {}


    try:

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(
                file
            )

    except Exception:

        return {}


# =========================================================
# SAFE DOCUMENT FOLDER
# =========================================================

def get_admin_document_folder(
    document_id: str,
):

    try:

        # Ensures the ID really is a UUID.
        uuid.UUID(
            document_id
        )

    except ValueError:

        raise HTTPException(
            status_code=400,
            detail="Invalid document ID.",
        )


    folder = (
        REQUEST_FOLDER
        / document_id
    )


    if not folder.exists():

        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )


    return folder


# =========================================================
# ADMIN - LIST ALL DOCUMENTS
# =========================================================

@app.get(
    "/api/v1/admin/documents"
)
def admin_list_documents():

    documents = []


    if not REQUEST_FOLDER.exists():

        return {
            "count": 0,
            "documents": [],
        }


    for document_folder in (
        REQUEST_FOLDER.iterdir()
    ):

        if not document_folder.is_dir():
            continue


        request_data = (
            load_json_if_exists(
                document_folder
                / "request.json"
            )
        )


        if not request_data:
            continue


        analysis_data = (
            load_json_if_exists(
                document_folder
                / "analysis"
                / "analysis_result.json"
            )
        )


        risk_data = (
            load_json_if_exists(
                document_folder
                / "analysis"
                / "risk_score.json"
            )
        )


        ocr_validation = (
            load_json_if_exists(
                document_folder
                / "ocr_validation.json"
            )
        )


        # Prefer risk_score.json.
        risk_score = (
            risk_data.get(
                "risk_score"
            )
        )


        if risk_score is None:

            risk_score = (
                analysis_data.get(
                    "risk_score"
                )
            )


        risk_level = (
            risk_data.get(
                "risk_level"
            )
            or
            analysis_data.get(
                "risk_level"
            )
            or
            "NOT_CALCULATED"
        )


        recommended_action = (
            risk_data.get(
                "recommended_action"
            )
            or
            analysis_data.get(
                "recommended_action"
            )
        )


        suspicious_count = (
            analysis_data.get(
                "suspicious_area_count",
                request_data.get(
                    "suspicious_area_count",
                    0,
                ),
            )
        )


        documents.append(
            {
                "document_id":
                    request_data.get(
                        "document_id",
                        document_folder.name,
                    ),

                "document_type":
                    request_data.get(
                        "internal_document_type",
                        "UNKNOWN",
                    ),

                "android_document_type":
                    request_data.get(
                        "android_document_type",
                        "UNKNOWN",
                    ),

                "received_at":
                    request_data.get(
                        "received_at",
                        "",
                    ),

                "ocr_validation_status":
                    ocr_validation.get(
                        "status",
                        request_data.get(
                            "ocr_validation_status",
                            "UNKNOWN",
                        ),
                    ),

                "ocr_issue_count":
                    ocr_validation.get(
                        "issue_count",
                        0,
                    ),

                "analysis_status":
                    request_data.get(
                        "alteration_analysis_status",
                        analysis_data.get(
                            "status",
                            "PENDING",
                        ),
                    ),

                "risk_score":
                    risk_score,

                "risk_level":
                    risk_level,

                "recommended_action":
                    recommended_action,

                "suspicious_area_count":
                    suspicious_count,

                "highlighted_image_available":
                    (
                        document_folder
                        / "analysis"
                        / "highlighted_suspicious_areas.png"
                    ).exists(),
            }
        )


    # Newest submission first.
    documents.sort(
        key=lambda item:
            item.get(
                "received_at",
                "",
            ),
        reverse=True,
    )


    return {
        "count":
            len(documents),

        "documents":
            documents,
    }


# =========================================================
# ADMIN - ONE DOCUMENT FULL DETAILS
# =========================================================

@app.get(
    "/api/v1/admin/documents/{document_id}"
)
def admin_document_details(
    document_id: str,
):

    folder = (
        get_admin_document_folder(
            document_id
        )
    )

    analysis_folder = (
        folder
        / "analysis"
    )


    request_data = (
        load_json_if_exists(
            folder
            / "request.json"
        )
    )


    ocr_data = (
        load_json_if_exists(
            folder
            / "ocr.json"
        )
    )


    ocr_validation = (
        load_json_if_exists(
            folder
            / "ocr_validation.json"
        )
    )


    analysis_result = (
        load_json_if_exists(
            analysis_folder
            / "analysis_result.json"
        )
    )


    risk_result = (
        load_json_if_exists(
            analysis_folder
            / "risk_score.json"
        )
    )


    background_result = (
        load_json_if_exists(
            analysis_folder
            / "background_analysis.json"
        )
    )


    edge_result = (
        load_json_if_exists(
            analysis_folder
            / "edge_analysis.json"
        )
    )


    text_result = (
        load_json_if_exists(
            analysis_folder
            / "text_analysis.json"
        )
    )


    photo_result = (
        load_json_if_exists(
            analysis_folder
            / "photo_analysis.json"
        )
    )


    symbol_result = (
        load_json_if_exists(
            analysis_folder
            / "symbol_analysis.json"
        )
    )


    localization_result = (
        load_json_if_exists(
            analysis_folder
            / "altered_text_localization.json"
        )
    )


    analysis_error = (
        load_json_if_exists(
            analysis_folder
            / "analysis_error.json"
        )
    )


    original_image_available = (

        (
            folder
            / "captured_document.jpg"
        ).exists()

        or

        (
            folder
            / "captured_document.png"
        ).exists()
    )


    highlighted_image_available = (

        analysis_folder
        / "highlighted_suspicious_areas.png"

    ).exists()


    risk_score = (
        risk_result.get(
            "risk_score"
        )
    )


    if risk_score is None:

        risk_score = (
            analysis_result.get(
                "risk_score"
            )
        )


    risk_level = (
        risk_result.get(
            "risk_level"
        )
        or
        analysis_result.get(
            "risk_level"
        )
        or
        "NOT_CALCULATED"
    )


    recommended_action = (
        risk_result.get(
            "recommended_action"
        )
        or
        analysis_result.get(
            "recommended_action"
        )
        or
        "NOT_AVAILABLE"
    )


    return {

        "document_id":
            document_id,

        "document_type":
            request_data.get(
                "internal_document_type",
                "UNKNOWN",
            ),

        "received_at":
            request_data.get(
                "received_at",
                "",
            ),

        "analysis_status":
            request_data.get(
                "alteration_analysis_status",
                analysis_result.get(
                    "status",
                    "PENDING",
                ),
            ),

        "risk_score":
            risk_score,

        "risk_level":
            risk_level,

        "recommended_action":
            recommended_action,

        "ocr":
            ocr_data,

        "ocr_validation":
            ocr_validation,

        "background_analysis":
            background_result,

        "edge_analysis":
            edge_result,

        "text_analysis":
            text_result,

        "photo_analysis":
            photo_result,

        "symbol_analysis":
            symbol_result,

        "altered_text_localization":
            localization_result,

        "risk":
            risk_result,

        "analysis_error":
            analysis_error,

        "original_image_available":
            original_image_available,

        "highlighted_image_available":
            highlighted_image_available,
    }

# =========================================================
# ADMIN - DOCUMENT IMAGES
# =========================================================

@app.get(
    "/api/v1/admin/documents/"
    "{document_id}/image/{image_type}"
)
def admin_document_image(
    document_id: str,
    image_type: str,
):

    folder = (
        get_admin_document_folder(
            document_id
        )
    )


    # =====================================================
    # ORIGINAL IMAGE
    # =====================================================

    if image_type == "original":

        jpg = (
            folder
            / "captured_document.jpg"
        )


        png = (
            folder
            / "captured_document.png"
        )


        if jpg.exists():

            return FileResponse(
                jpg,
                media_type="image/jpeg",
            )


        if png.exists():

            return FileResponse(
                png,
                media_type="image/png",
            )


    # =====================================================
    # HIGHLIGHTED RESULT
    # =====================================================

    elif image_type == "highlighted":

        highlighted = (
            folder
            / "analysis"
            / "highlighted_suspicious_areas.png"
        )


        if highlighted.exists():

            return FileResponse(
                highlighted,
                media_type="image/png",
            )


    raise HTTPException(
        status_code=404,
        detail="Requested image not found.",
    )