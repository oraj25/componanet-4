from datetime import date, datetime
from pathlib import Path
import json
import re

from PIL import Image


# =========================================================
# SUPPORTED DOCUMENT TYPES
# =========================================================

SUPPORTED_DOCUMENT_TYPES = {
    "NIC",
    "DRIVING_LICENCE",
}


# =========================================================
# NORMALIZATION
# =========================================================

def normalize_text(value):
    """
    Normalize general OCR text.
    """

    if value is None:
        return ""

    value = str(value).strip()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value


def normalize_alphanumeric(value):
    """
    Remove spaces and punctuation for ID comparison.
    """

    value = normalize_text(value).upper()

    return re.sub(
        r"[^A-Z0-9]",
        "",
        value,
    )


def normalize_digits(value):
    """
    Keep only digits.
    """

    return re.sub(
        r"\D",
        "",
        normalize_text(value),
    )


# =========================================================
# ISSUE CREATION
# =========================================================

def create_issue(
    code,
    field,
    message,
):
    return {
        "code": code,
        "field": field,
        "message": message,
    }


# =========================================================
# NIC VALIDATION
# =========================================================

def validate_nic_number(value):

    cleaned = normalize_alphanumeric(
        value
    )

    # New Sri Lankan NIC:
    # 12 digits.
    if re.fullmatch(
        r"\d{12}",
        cleaned,
    ):
        return True


    # Older Sri Lankan NIC:
    # 9 digits followed by V or X.
    if re.fullmatch(
        r"\d{9}[VX]",
        cleaned,
    ):
        return True


    return False


# =========================================================
# DRIVING LICENCE NUMBER VALIDATION
# =========================================================

def validate_licence_number(value):

    cleaned = normalize_alphanumeric(
        value
    )


    # Initial format rule suitable for our current samples.
    #
    # Example:
    # B6200049
    #
    # One to three letters followed by
    # five to ten digits.

    if re.fullmatch(
        r"[A-Z]{1,3}\d{5,10}",
        cleaned,
    ):
        return True


    return False


# =========================================================
# NAME VALIDATION
# =========================================================

def validate_name(value):

    text = normalize_text(
        value
    )


    if len(text) < 3:
        return False


    # Names should not normally contain numeric values.
    if any(
        character.isdigit()
        for character in text
    ):
        return False


    letter_count = sum(
        1
        for character in text
        if character.isalpha()
    )


    if letter_count < 3:
        return False


    return True


# =========================================================
# BLOOD GROUP VALIDATION
# =========================================================

def validate_blood_group(value):

    cleaned = (
        normalize_text(value)
        .upper()
        .replace(
            " ",
            "",
        )
    )


    accepted = {
        "A+",
        "A-",
        "B+",
        "B-",
        "AB+",
        "AB-",
        "O+",
        "O-",
    }


    return cleaned in accepted


# =========================================================
# DATE VALIDATION
# =========================================================

def parse_date_candidate(value):
    """
    Accept formats such as:

    25/10/2002
    25-10-2002
    25.10.2002

    2002/10/25
    2002-10-25
    """

    text = normalize_text(
        value
    )


    match = re.fullmatch(
        r"(\d{1,4})[./-](\d{1,2})[./-](\d{1,4})",
        text,
    )


    if match is None:
        return None


    first = match.group(1)
    second = match.group(2)
    third = match.group(3)


    try:

        # ================================================
        # YYYY/MM/DD
        # ================================================

        if len(first) == 4:

            year = int(first)
            month = int(second)
            day = int(third)


        # ================================================
        # DD/MM/YYYY
        # ================================================

        elif len(third) == 4:

            day = int(first)
            month = int(second)
            year = int(third)


        else:

            return None


        parsed = datetime(
            year,
            month,
            day,
        ).date()


    except ValueError:

        return None


    # Reasonable document date range.
    current_year = (
        date.today().year
    )


    if not (
        1900
        <= parsed.year
        <= current_year + 20
    ):
        return None


    return parsed


def validate_date(value):

    return (
        parse_date_candidate(value)
        is not None
    )


# =========================================================
# CHECK VALUE EXISTS IN OCR TEXT
# =========================================================

def candidate_exists_in_text(
    candidate,
    full_text,
):

    if candidate is None:
        return False


    candidate_clean = (
        normalize_alphanumeric(
            candidate
        )
    )


    full_text_clean = (
        normalize_alphanumeric(
            full_text
        )
    )


    if not candidate_clean:
        return False


    return (
        candidate_clean
        in full_text_clean
    )


# =========================================================
# VALIDATE OCR BOUNDING BOXES
# =========================================================

def validate_bounding_boxes(
    lines,
    image_width,
    image_height,
):

    issues = []


    for index, line in enumerate(
        lines
    ):

        if not isinstance(
            line,
            dict,
        ):

            issues.append(
                create_issue(
                    "INVALID_OCR_LINE",
                    f"lines[{index}]",
                    "OCR line is not a valid object.",
                )
            )

            continue


        box = line.get(
            "boundingBox"
        )


        # ML Kit may legitimately return no box.
        if box is None:
            continue


        if not isinstance(
            box,
            dict,
        ):

            issues.append(
                create_issue(
                    "INVALID_BOUNDING_BOX",
                    f"lines[{index}]",
                    "Bounding box is not a valid object.",
                )
            )

            continue


        required = [
            "left",
            "top",
            "right",
            "bottom",
        ]


        if not all(
            key in box
            for key in required
        ):

            issues.append(
                create_issue(
                    "INCOMPLETE_BOUNDING_BOX",
                    f"lines[{index}]",
                    "OCR bounding box is incomplete.",
                )
            )

            continue


        try:

            left = int(
                box["left"]
            )

            top = int(
                box["top"]
            )

            right = int(
                box["right"]
            )

            bottom = int(
                box["bottom"]
            )


        except (
            TypeError,
            ValueError,
        ):

            issues.append(
                create_issue(
                    "INVALID_BOUNDING_BOX_VALUES",
                    f"lines[{index}]",
                    "OCR bounding box contains invalid values.",
                )
            )

            continue


        # ================================================
        # LOGICAL BOX SIZE
        # ================================================

        if (
            right <= left
            or
            bottom <= top
        ):

            issues.append(
                create_issue(
                    "INVALID_BOUNDING_BOX_SIZE",
                    f"lines[{index}]",
                    "OCR bounding box has invalid dimensions.",
                )
            )

            continue


        # ================================================
        # IMAGE BOUNDARIES
        # ================================================

        if (
            left < 0
            or
            top < 0
            or
            right > image_width
            or
            bottom > image_height
        ):

            issues.append(
                create_issue(
                    "BOUNDING_BOX_OUTSIDE_IMAGE",
                    f"lines[{index}]",
                    "OCR bounding box extends outside the captured image.",
                )
            )


    return issues


# =========================================================
# VALIDATE NIC DOCUMENT
# =========================================================

def validate_nic(
    fields,
    full_text,
):

    issues = []


    nic_number = fields.get(
        "nicNumber"
    )


    possible_name = fields.get(
        "possibleName"
    )


    dates = fields.get(
        "dates",
        [],
    )


    # =====================================================
    # NIC NUMBER
    # =====================================================

    if not nic_number:

        issues.append(
            create_issue(
                "NIC_NUMBER_MISSING",
                "nicNumber",
                "NIC number was not identified by OCR.",
            )
        )


    elif not validate_nic_number(
        nic_number
    ):

        issues.append(
            create_issue(
                "INVALID_NIC_FORMAT",
                "nicNumber",
                "Detected NIC number does not match a supported Sri Lankan NIC format.",
            )
        )


    elif not candidate_exists_in_text(
        nic_number,
        full_text,
    ):

        issues.append(
            create_issue(
                "NIC_TEXT_INCONSISTENCY",
                "nicNumber",
                "NIC candidate does not match the OCR full text.",
            )
        )


    # =====================================================
    # NAME
    # =====================================================

    if not possible_name:

        issues.append(
            create_issue(
                "NAME_MISSING",
                "possibleName",
                "Name was not identified by OCR.",
            )
        )


    elif not validate_name(
        possible_name
    ):

        issues.append(
            create_issue(
                "INVALID_NAME_FORMAT",
                "possibleName",
                "Detected name has an unexpected format.",
            )
        )


    # =====================================================
    # DATE
    # =====================================================

    if not isinstance(
        dates,
        list,
    ):

        issues.append(
            create_issue(
                "INVALID_DATE_LIST",
                "dates",
                "OCR date candidates are not in list format.",
            )
        )


    elif len(dates) == 0:

        issues.append(
            create_issue(
                "DATE_MISSING",
                "dates",
                "No date candidate was detected on the NIC.",
            )
        )


    else:

        valid_date_found = any(
            validate_date(
                candidate
            )
            for candidate in dates
        )


        if not valid_date_found:

            issues.append(
                create_issue(
                    "INVALID_DATE_FORMAT",
                    "dates",
                    "No detected date has a valid calendar format.",
                )
            )


    return issues


# =========================================================
# VALIDATE DRIVING LICENCE
# =========================================================

def validate_driving_licence(
    fields,
    full_text,
):

    issues = []


    licence_number = fields.get(
        "licenceNumber"
    )


    possible_name = fields.get(
        "possibleName"
    )


    dates = fields.get(
        "dates",
        [],
    )


    blood_group = fields.get(
        "bloodGroup"
    )


    # =====================================================
    # LICENCE NUMBER
    # =====================================================

    if not licence_number:

        issues.append(
            create_issue(
                "LICENCE_NUMBER_MISSING",
                "licenceNumber",
                "Driving licence number was not identified.",
            )
        )


    elif not validate_licence_number(
        licence_number
    ):

        issues.append(
            create_issue(
                "INVALID_LICENCE_NUMBER",
                "licenceNumber",
                "Detected driving licence number has an unexpected format.",
            )
        )


    elif not candidate_exists_in_text(
        licence_number,
        full_text,
    ):

        issues.append(
            create_issue(
                "LICENCE_TEXT_INCONSISTENCY",
                "licenceNumber",
                "Licence-number candidate does not match the OCR full text.",
            )
        )


    # =====================================================
    # NAME
    # =====================================================

    if not possible_name:

        issues.append(
            create_issue(
                "NAME_MISSING",
                "possibleName",
                "Name was not identified on the driving licence.",
            )
        )


    elif not validate_name(
        possible_name
    ):

        issues.append(
            create_issue(
                "INVALID_NAME_FORMAT",
                "possibleName",
                "Detected name has an unexpected format.",
            )
        )


    # =====================================================
    # DATES
    # =====================================================

    if not isinstance(
        dates,
        list,
    ):

        issues.append(
            create_issue(
                "INVALID_DATE_LIST",
                "dates",
                "OCR date candidates are not in list format.",
            )
        )


    elif len(dates) == 0:

        issues.append(
            create_issue(
                "DATE_MISSING",
                "dates",
                "No date was detected on the driving licence.",
            )
        )


    else:

        valid_dates = [
            value
            for value in dates
            if validate_date(
                value
            )
        ]


        if not valid_dates:

            issues.append(
                create_issue(
                    "INVALID_DATE_FORMAT",
                    "dates",
                    "No detected driving-licence date has a valid calendar format.",
                )
            )


    # =====================================================
    # BLOOD GROUP
    #
    # Optional because OCR may fail to extract this field.
    # If present, it must be valid.
    # =====================================================

    if (
        blood_group
        and
        not validate_blood_group(
            blood_group
        )
    ):

        issues.append(
            create_issue(
                "INVALID_BLOOD_GROUP",
                "bloodGroup",
                "Detected blood group is not recognized.",
            )
        )


    return issues


# =========================================================
# MAIN OCR PAYLOAD VALIDATOR
# =========================================================

def validate_ocr_payload(
    ocr_data,
    internal_document_type,
    image_path,
):

    issues = []


    # =====================================================
    # BASIC STRUCTURE
    # =====================================================

    if not isinstance(
        ocr_data,
        dict,
    ):

        return {
            "status": "REVIEW",
            "issue_count": 1,
            "issues": [
                create_issue(
                    "INVALID_OCR_PAYLOAD",
                    "ocr",
                    "OCR payload is not a JSON object.",
                )
            ],
        }


    full_text = normalize_text(
        ocr_data.get(
            "fullText"
        )
    )


    lines = ocr_data.get(
        "lines",
        [],
    )


    fields = ocr_data.get(
        "fields",
        {},
    )


    if not isinstance(
        lines,
        list,
    ):

        lines = []

        issues.append(
            create_issue(
                "INVALID_LINES_STRUCTURE",
                "lines",
                "OCR lines value is not a list.",
            )
        )


    if not isinstance(
        fields,
        dict,
    ):

        fields = {}

        issues.append(
            create_issue(
                "INVALID_FIELDS_STRUCTURE",
                "fields",
                "OCR fields value is not an object.",
            )
        )


    # =====================================================
    # EMPTY OCR CHECK
    # =====================================================

    if not full_text:

        issues.append(
            create_issue(
                "OCR_TEXT_EMPTY",
                "fullText",
                "ML Kit did not return document text.",
            )
        )


    # =====================================================
    # IMAGE SIZE
    # =====================================================

    try:

        with Image.open(
            image_path
        ) as image:

            image_width, image_height = (
                image.size
            )


    except Exception as exception:

        return {
            "status": "REVIEW",
            "issue_count": 1,
            "issues": [
                create_issue(
                    "IMAGE_READ_ERROR",
                    "image",
                    (
                        "Unable to read captured image: "
                        + str(exception)
                    ),
                )
            ],
        }


    # =====================================================
    # BOUNDING BOX VALIDATION
    # =====================================================

    issues.extend(
        validate_bounding_boxes(
            lines,
            image_width,
            image_height,
        )
    )


    # =====================================================
    # DOCUMENT-SPECIFIC VALIDATION
    # =====================================================

    if (
        internal_document_type
        == "NIC"
    ):

        issues.extend(
            validate_nic(
                fields,
                full_text,
            )
        )


    elif (
        internal_document_type
        == "DRIVING_LICENCE"
    ):

        issues.extend(
            validate_driving_licence(
                fields,
                full_text,
            )
        )


    else:

        issues.append(
            create_issue(
                "OCR_VALIDATION_NOT_CONFIGURED",
                "document_type",
                (
                    "OCR validation rules are not yet configured for "
                    + internal_document_type
                ),
            )
        )


    # =====================================================
    # RESULT
    # =====================================================

    status = (
        "PASS"
        if len(issues) == 0
        else "REVIEW"
    )


    return {

        "document_type":
            internal_document_type,

        "status":
            status,

        "issue_count":
            len(issues),

        "image_width":
            image_width,

        "image_height":
            image_height,

        "ocr_text_present":
            bool(full_text),

        "ocr_line_count":
            len(lines),

        "validated_fields":
            {
                "nic_number":
                    fields.get(
                        "nicNumber"
                    ),

                "licence_number":
                    fields.get(
                        "licenceNumber"
                    ),

                "possible_name":
                    fields.get(
                        "possibleName"
                    ),

                "dates":
                    fields.get(
                        "dates",
                        [],
                    ),

                "blood_group":
                    fields.get(
                        "bloodGroup"
                    ),
            },

        "issues":
            issues,
    }


# =========================================================
# COMMAND-LINE TEST
# =========================================================

def main():

    import sys


    if len(sys.argv) != 4:

        print(
            "Usage:"
        )

        print(
            "python -m src.ocr_validation "
            "<ocr.json> "
            "<image.jpg> "
            "<NIC|DRIVING_LICENCE>"
        )

        raise SystemExit(1)


    ocr_path = Path(
        sys.argv[1]
    )


    image_path = Path(
        sys.argv[2]
    )


    document_type = (
        sys.argv[3]
        .strip()
        .upper()
    )


    with open(
        ocr_path,
        "r",
        encoding="utf-8",
    ) as file:

        ocr_data = json.load(
            file
        )


    result = validate_ocr_payload(
        ocr_data,
        document_type,
        image_path,
    )


    print(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()