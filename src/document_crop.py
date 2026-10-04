from pathlib import Path

from PIL import Image


# =========================================================
# SETTINGS
# =========================================================

DOWNSAMPLE_MAX_WIDTH = 500

BACKGROUND_THRESHOLD = 28.0

MINIMUM_DOCUMENT_RATIO = 0.08


# =========================================================
# COLOR DISTANCE
# =========================================================

def color_distance(
    first,
    second,
):

    red_difference = (
        first[0]
        - second[0]
    )

    green_difference = (
        first[1]
        - second[1]
    )

    blue_difference = (
        first[2]
        - second[2]
    )


    return (

        red_difference
        * red_difference

        +

        green_difference
        * green_difference

        +

        blue_difference
        * blue_difference

    ) ** 0.5


# =========================================================
# MEAN COLOR
# =========================================================

def mean_color(
    colors,
):

    if not colors:

        return (
            255,
            255,
            255,
        )


    red = 0
    green = 0
    blue = 0


    for color in colors:

        red += color[0]
        green += color[1]
        blue += color[2]


    count = len(
        colors
    )


    return (
        red / count,
        green / count,
        blue / count,
    )


# =========================================================
# ESTIMATE BACKGROUND COLOR
# =========================================================

def estimate_background_color(
    image,
):
    """
    Estimate surrounding surface color from image edges.
    """

    width, height = (
        image.size
    )


    pixels = (
        image.load()
    )


    samples = []


    border_size = max(
        5,
        int(
            min(
                width,
                height,
            )
            * 0.04
        ),
    )


    # =====================================================
    # TOP + BOTTOM
    # =====================================================

    for y in range(
        border_size
    ):

        for x in range(
            0,
            width,
            4,
        ):

            samples.append(
                pixels[
                    x,
                    y,
                ]
            )


            samples.append(
                pixels[
                    x,
                    height - 1 - y,
                ]
            )


    # =====================================================
    # LEFT + RIGHT
    # =====================================================

    for x in range(
        border_size
    ):

        for y in range(
            0,
            height,
            4,
        ):

            samples.append(
                pixels[
                    x,
                    y,
                ]
            )


            samples.append(
                pixels[
                    width - 1 - x,
                    y,
                ]
            )


    return mean_color(
        samples
    )


# =========================================================
# FIND DOCUMENT BOUNDING BOX
# =========================================================

def find_document_bounds(
    image,
):

    image = image.convert(
        "RGB"
    )


    width, height = (
        image.size
    )


    pixels = (
        image.load()
    )


    background_color = (
        estimate_background_color(
            image
        )
    )


    active_x = []

    active_y = []


    # =====================================================
    # SCAN IMAGE
    # =====================================================

    step = max(
        1,
        width // 500,
    )


    for y in range(
        0,
        height,
        step,
    ):

        for x in range(
            0,
            width,
            step,
        ):

            pixel = (
                pixels[
                    x,
                    y,
                ]
            )


            difference = (
                color_distance(
                    pixel,
                    background_color,
                )
            )


            if (
                difference
                >= BACKGROUND_THRESHOLD
            ):

                active_x.append(
                    x
                )

                active_y.append(
                    y
                )


    if (
        not active_x
        or
        not active_y
    ):

        return None


    x1 = min(
        active_x
    )

    x2 = max(
        active_x
    )


    y1 = min(
        active_y
    )

    y2 = max(
        active_y
    )


    # =====================================================
    # ADD SMALL MARGIN
    # =====================================================

    horizontal_margin = int(
        width * 0.015
    )


    vertical_margin = int(
        height * 0.015
    )


    x1 = max(
        0,
        x1 - horizontal_margin,
    )


    y1 = max(
        0,
        y1 - vertical_margin,
    )


    x2 = min(
        width,
        x2 + horizontal_margin,
    )


    y2 = min(
        height,
        y2 + vertical_margin,
    )


    detected_width = (
        x2 - x1
    )


    detected_height = (
        y2 - y1
    )


    detected_area = (
        detected_width
        * detected_height
    )


    image_area = (
        width
        * height
    )


    if (
        detected_area
        <
        image_area
        * MINIMUM_DOCUMENT_RATIO
    ):

        return None


    return (
        x1,
        y1,
        x2,
        y2,
    )


# =========================================================
# CROP DOCUMENT
# =========================================================

def crop_document(
    input_path,
    output_path,
):

    input_path = Path(
        input_path
    )


    output_path = Path(
        output_path
    )


    with Image.open(
        input_path
    ) as source:

        image = (
            source.convert(
                "RGB"
            )
        )


        bounds = (
            find_document_bounds(
                image
            )
        )


        if bounds is None:

            # Safe fallback:
            # preserve original rather than failing.
            cropped = image.copy()

            detection_status = (
                "NOT_DETECTED"
            )


        else:

            cropped = image.crop(
                bounds
            )

            detection_status = (
                "CROPPED"
            )


        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )


        cropped.save(
            output_path
        )


    return {

        "status":
            detection_status,

        "bounds":
            bounds,

        "width":
            cropped.width,

        "height":
            cropped.height,

        "output":
            str(
                output_path
            ),
    }