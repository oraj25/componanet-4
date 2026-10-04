from pathlib import Path
import json

from PIL import Image, ImageDraw


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG_FILE = (
    PROJECT_ROOT
    / "config"
    / "document_regions.json"
)

NORMALIZED_FOLDER = (
    PROJECT_ROOT
    / "results"
    / "normalized"
)

PREVIEW_FOLDER = (
    PROJECT_ROOT
    / "results"
    / "region_previews"
)


# =========================================================
# TEST DOCUMENTS
# =========================================================

TEST_DOCUMENTS = {
    "NIC": [
        "nic_template_v1_normalized.png",
        "nic_genuine_01_normalized.png",
        "nic_altered_01_normalized.png",
    ],

    "DRIVING_LICENCE": [
        "driving_licence_template_v1_normalized.png",
        "driving_licence_genuine_01_normalized.png",
        "driving_licence_altered_01_normalized.png",
    ],
}


# =========================================================
# LOAD REGION CONFIGURATION
# =========================================================

def load_configuration():

    if not CONFIG_FILE.exists():

        print("ERROR: Region configuration file not found.")
        print(f"Expected: {CONFIG_FILE}")

        raise SystemExit(1)


    with open(
        CONFIG_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        configuration = json.load(file)


    return configuration


# =========================================================
# VALIDATE REGION
# =========================================================

def validate_region(region_name, region):

    required_values = [
        "x1",
        "y1",
        "x2",
        "y2",
        "type",
    ]


    for key in required_values:

        if key not in region:

            print(
                f"ERROR: '{region_name}' "
                f"is missing '{key}'."
            )

            return False


    x1 = region["x1"]
    y1 = region["y1"]
    x2 = region["x2"]
    y2 = region["y2"]


    # Coordinates must remain inside the image.
    if not (
        0 <= x1 <= 1
        and 0 <= y1 <= 1
        and 0 <= x2 <= 1
        and 0 <= y2 <= 1
    ):

        print(
            f"ERROR: Invalid coordinates "
            f"for '{region_name}'."
        )

        return False


    # Bottom-right must be after top-left.
    if x2 <= x1 or y2 <= y1:

        print(
            f"ERROR: Invalid region size "
            f"for '{region_name}'."
        )

        return False


    return True


# =========================================================
# CONVERT NORMALIZED COORDINATES TO PIXELS
# =========================================================

def normalized_to_pixels(
    region,
    width,
    height,
):

    x1 = round(
        region["x1"]
        * width
    )

    y1 = round(
        region["y1"]
        * height
    )

    x2 = round(
        region["x2"]
        * width
    )

    y2 = round(
        region["y2"]
        * height
    )


    # Prevent coordinates exceeding the image.
    x1 = max(
        0,
        min(
            x1,
            width - 1,
        ),
    )

    y1 = max(
        0,
        min(
            y1,
            height - 1,
        ),
    )

    x2 = max(
        1,
        min(
            x2,
            width,
        ),
    )

    y2 = max(
        1,
        min(
            y2,
            height,
        ),
    )


    return (
        x1,
        y1,
        x2,
        y2,
    )


# =========================================================
# DRAW REGION BOX
# =========================================================

def draw_region(
    draw,
    region_name,
    region_type,
    coordinates,
):

    x1, y1, x2, y2 = coordinates


    # -----------------------------------------------------
    # DRAW RECTANGLE
    # -----------------------------------------------------

    line_width = 3


    for offset in range(line_width):

        draw.rectangle(
            [
                x1 + offset,
                y1 + offset,
                x2 - offset,
                y2 - offset,
            ],
            outline="red",
        )


    # -----------------------------------------------------
    # DRAW LABEL BACKGROUND
    # -----------------------------------------------------

    label = (
        f"{region_name} [{region_type}]"
    )


    text_x = x1 + 3

    text_y = y1 + 3


    text_box = draw.textbbox(
        (
            text_x,
            text_y,
        ),
        label,
    )


    draw.rectangle(
        text_box,
        fill="white",
    )


    # -----------------------------------------------------
    # DRAW LABEL
    # -----------------------------------------------------

    draw.text(
        (
            text_x,
            text_y,
        ),
        label,
        fill="black",
    )


# =========================================================
# CREATE REGION PREVIEW
# =========================================================

def create_region_preview(
    document_type,
    image_path,
    regions,
):

    if not image_path.exists():

        print()
        print(
            f"WARNING: Image not found: "
            f"{image_path.name}"
        )

        return False


    with Image.open(image_path) as image:

        preview_image = image.convert(
            "RGB"
        )

        width, height = (
            preview_image.size
        )


        draw = ImageDraw.Draw(
            preview_image
        )


        print()
        print("----------------------------------------")

        print(
            f"Document type: {document_type}"
        )

        print(
            f"Image: {image_path.name}"
        )


        # -------------------------------------------------
        # PROCESS REGIONS
        # -------------------------------------------------

        for region_name, region in regions.items():

            if not validate_region(
                region_name,
                region,
            ):

                continue


            coordinates = (
                normalized_to_pixels(
                    region,
                    width,
                    height,
                )
            )


            region_type = (
                region["type"]
            )


            draw_region(
                draw,
                region_name,
                region_type,
                coordinates,
            )


            x1, y1, x2, y2 = coordinates


            print(
                f"{region_name:<22} "
                f"({x1}, {y1}) -> "
                f"({x2}, {y2})"
            )


        # -------------------------------------------------
        # SAVE PREVIEW
        # -------------------------------------------------

        PREVIEW_FOLDER.mkdir(
            parents=True,
            exist_ok=True,
        )


        output_name = (
            image_path.stem
            + "_regions.png"
        )


        output_path = (
            PREVIEW_FOLDER
            / output_name
        )


        preview_image.save(
            output_path
        )


        print(
            f"Saved preview: "
            f"{output_path.name}"
        )

        print("----------------------------------------")


    return True


# =========================================================
# PROCESS DOCUMENT TYPE
# =========================================================

def process_document_type(
    document_type,
    configuration,
):

    if document_type not in configuration:

        print()
        print(
            f"ERROR: No configuration "
            f"for {document_type}"
        )

        return


    regions = (
        configuration[
            document_type
        ]["regions"]
    )


    image_names = (
        TEST_DOCUMENTS.get(
            document_type,
            [],
        )
    )


    for image_name in image_names:

        image_path = (
            NORMALIZED_FOLDER
            / image_name
        )


        create_region_preview(
            document_type,
            image_path,
            regions,
        )


# =========================================================
# MAIN PROGRAM
# =========================================================

def main():

    print()
    print(
        "Document Alteration Detection Module"
    )

    print(
        "Step 7 - Template Region Mapping"
    )


    configuration = (
        load_configuration()
    )


    for document_type in TEST_DOCUMENTS:

        process_document_type(
            document_type,
            configuration,
        )


    print()
    print("========================================")
    print("REGION PREVIEWS CREATED")
    print("========================================")


if __name__ == "__main__":
    main()