from pathlib import Path

from PIL import Image


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

IMAGE_PATH = (
    PROJECT_ROOT
    / "data"
    / "genuine"
    / "nic_genuine_01.jpg"
)


# ---------------------------------------------------------
# CHECK WHETHER IMAGE EXISTS
# ---------------------------------------------------------

if not IMAGE_PATH.exists():

    print("ERROR: Image was not found.")
    print(f"Expected location: {IMAGE_PATH}")

    raise SystemExit(1)


# ---------------------------------------------------------
# LOAD IMAGE
# ---------------------------------------------------------

image = Image.open(IMAGE_PATH)


# ---------------------------------------------------------
# READ BASIC IMAGE INFORMATION
# ---------------------------------------------------------

width, height = image.size

if width <= 0 or height <= 0:

    print("ERROR: Invalid image dimensions.")

    image.close()

    raise SystemExit(1)



print("Document image loaded successfully.")
print()

print("File:", IMAGE_PATH.name)
print("Format:", image.format)
print("Width:", width)
print("Height:", height)
print("Colour mode:", image.mode)
print("Total pixels:", width * height)


# ---------------------------------------------------------
# READ SAMPLE PIXELS
# ---------------------------------------------------------

top_left_pixel = image.getpixel(
    (0, 0)
)

centre_pixel = image.getpixel(
    (
        width // 2,
        height // 2,
    )
)


print()
print("Top-left pixel:", top_left_pixel)
print("Centre pixel:", centre_pixel)


# ---------------------------------------------------------
# CLOSE IMAGE
# ---------------------------------------------------------

image.close()