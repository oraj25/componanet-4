from pathlib import Path
import json

from PIL import Image


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

EXTRACTED_FOLDER = (
    PROJECT_ROOT
    / "results"
    / "extracted_regions"
)


# =========================================================
# DOCUMENT IMAGES
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
# LOAD CONFIGURATION
# =========================================================

def load_configuration():

    if not CONFIG_FILE.exists():

        print("ERROR: Configuration file not found.")
        print(f"Expected: {CONFIG_FILE}")

        raise SystemExit(1)


    with open(
        CONFIG_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


# =========================================================
# CONVERT NORMALIZED COORDINATES TO PIXELS
# =========================================================

def normalized_to_pixels(
    region,
    width,
    height,
):

    x1 = round(
        region["x1"] * width
    )

    y1 = round(
        region["y1"] * height
    )

    x2 = round(
        region["x2"] * width
    )

    y2 = round(
        region["y2"] * height
    )


    # -----------------------------------------------------
    # KEEP COORDINATES INSIDE IMAGE
    # -----------------------------------------------------

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
        x1 + 1,
        min(
            x2,
            width,
        ),
    )

    y2 = max(
        y1 + 1,
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
# MANUAL REGION EXTRACTION
# =========================================================

def extract_region_manually(
    source_image,
    coordinates,
):
    """
    Extract a rectangular image region manually by copying
    individual pixels into a new image.
    """

    x1, y1, x2, y2 = coordinates


    region_width = (
        x2 - x1
    )

    region_height = (
        y2 - y1
    )


    source_pixels = (
        source_image.load()
    )


    region_image = Image.new(
        "RGB",
        (
            region_width,
            region_height,
        ),
    )


    region_pixels = (
        region_image.load()
    )


    # -----------------------------------------------------
    # COPY PIXELS
    # -----------------------------------------------------

    for region_y in range(region_height):

        source_y = (
            y1 + region_y
        )


        for region_x in range(region_width):

            source_x = (
                x1 + region_x
            )


            region_pixels[
                region_x,
                region_y,
            ] = source_pixels[
                source_x,
                source_y,
            ]


    return region_image


# =========================================================
# EXTRACT REGIONS FROM ONE DOCUMENT
# =========================================================

def extract_document_regions(
    document_type,
    image_path,
    regions,
):

    if not image_path.exists():

        print()
        print(
            f"WARNING: Image not found: "
            f"{image_path}"
        )

        return 0


    with Image.open(image_path) as image:

        source_image = image.convert(
            "RGB"
        )

        width, height = (
            source_image.size
        )


        # -------------------------------------------------
        # CREATE OUTPUT FOLDER FOR THIS IMAGE
        # -------------------------------------------------

        image_output_folder = (
            EXTRACTED_FOLDER
            / document_type.lower()
            / image_path.stem
        )


        image_output_folder.mkdir(
            parents=True,
            exist_ok=True,
        )


        print()
        print("========================================")
        print(f"DOCUMENT TYPE: {document_type}")
        print(f"IMAGE: {image_path.name}")
        print("========================================")


        extracted_count = 0

        metadata = {
            "document_type": document_type,
            "source_image": image_path.name,
            "source_width": width,
            "source_height": height,
            "regions": {},
        }


        # -------------------------------------------------
        # PROCESS EVERY CONFIGURED REGION
        # -------------------------------------------------

        for region_name, region in regions.items():

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


            # ---------------------------------------------
            # EXTRACT REGION
            # ---------------------------------------------

            region_image = (
                extract_region_manually(
                    source_image,
                    coordinates,
                )
            )


            # ---------------------------------------------
            # SAVE REGION
            # ---------------------------------------------

            output_path = (
                image_output_folder
                / f"{region_name}.png"
            )


            region_image.save(
                output_path
            )


            region_width = (
                x2 - x1
            )

            region_height = (
                y2 - y1
            )


            # ---------------------------------------------
            # SAVE REGION INFORMATION
            # ---------------------------------------------

            metadata["regions"][
                region_name
            ] = {

                "type": region["type"],

                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,

                "width": region_width,
                "height": region_height,

                "file": output_path.name,
            }


            print(
                f"{region_name:<22} "
                f"{region_width} x "
                f"{region_height}"
            )


            extracted_count += 1


        # -------------------------------------------------
        # SAVE METADATA
        # -------------------------------------------------

        metadata_path = (
            image_output_folder
            / "regions.json"
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


        print()
        print(
            f"Extracted regions: "
            f"{extracted_count}"
        )

        print(
            f"Saved to: "
            f"{image_output_folder}"
        )


    return extracted_count


# =========================================================
# PROCESS DOCUMENT TYPE
# =========================================================

def process_document_type(
    document_type,
    configuration,
):

    if document_type not in configuration:

        print(
            f"ERROR: No configuration "
            f"for {document_type}"
        )

        return 0


    regions = (
        configuration[
            document_type
        ]["regions"]
    )


    image_names = (
        TEST_DOCUMENTS.get(
            document_type,
            []
        )
    )


    total_regions = 0


    for image_name in image_names:

        image_path = (
            NORMALIZED_FOLDER
            / image_name
        )


        count = (
            extract_document_regions(
                document_type,
                image_path,
                regions,
            )
        )


        total_regions += count


    return total_regions


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print(
        "Document Alteration Detection Module"
    )

    print(
        "Step 8 - ROI Extraction"
    )


    configuration = (
        load_configuration()
    )


    total_extracted = 0


    for document_type in TEST_DOCUMENTS:

        count = (
            process_document_type(
                document_type,
                configuration,
            )
        )

        total_extracted += count


    print()
    print("========================================")

    print(
        f"TOTAL REGIONS EXTRACTED: "
        f"{total_extracted}"
    )

    print("========================================")


if __name__ == "__main__":
    main()