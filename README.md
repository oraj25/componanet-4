# Document Alteration Detection Module — Component 4

## AI-Assisted Customer Verification System for Banking Agents

This repository contains **Component 4 — Physical Document Alteration Detection** of the AI-Assisted Customer Verification System.

The module analyses photographs of physical identity and supporting documents captured using the Android application and identifies visual evidence that may indicate document alteration.

The system is designed to detect indicators such as:

- overwritten or replaced text
- erased or covered areas
- inconsistent text structure
- unusual document backgrounds
- abnormal edge patterns
- possible pasted or replaced photographs
- suspicious signatures, logos, or security elements
- inconsistencies against an approved document template
- OCR field-format problems
- localized suspicious areas

The system does **not make the final decision that a document is fraudulent**.

Instead, it produces an explainable risk score and highlights suspicious regions for review by an administrator or fraud investigator.

---

# 1. Current Project Status

The current implementation supports the main alteration-detection pipeline for:

| Document Type | OCR | Template Analysis | Alteration Detection | Risk Scoring |
|---|---:|---:|---:|---:|
| Sri Lankan National Identity Card | ✅ | ✅ | ✅ | ✅ |
| Sri Lankan Driving Licence | ✅ | ✅ | ✅ | ✅ |
| Bank Statement | Partial | ❌ | ❌ | ❌ |
| Business Registration / Company Certificate | Partial | ❌ | ❌ | ❌ |
| Vehicle Registration / CR Book | Partial | ❌ | ❌ | ❌ |
| Other documents | Partial | ❌ | ❌ | ❌ |

The Python physical-alteration pipeline is therefore currently considered **implemented for NIC and Driving Licence only**.

Support for the other required document types remains incomplete.

---

# 2. Important System Principle

This project intentionally does **not** use a ready-made document-fraud-detection library.

The document-alteration algorithms were implemented manually using:

- Python
- standard Python libraries
- Pillow for basic image loading/saving
- custom pixel processing
- custom grayscale conversion
- custom thresholding
- custom Sobel edge analysis
- custom connected-component analysis
- custom statistical comparisons
- custom template comparison
- custom risk scoring

Google ML Kit is used on Android **only for OCR**.

ML Kit performs:

```text
Image pixels
    ↓
Recognized characters/text
```

It does **not** perform:

```text
Fraud detection
Document alteration detection
Photo replacement detection
Risk scoring
Template comparison
Fake/real classification
```

Those functions are implemented by this Component 4 code.

---

# 3. High-Level Architecture

```text
┌─────────────────────────────────────────────┐
│               Android Application           │
│                                             │
│  Camera2                                    │
│     ↓                                       │
│  Capture Physical Document                  │
│     ↓                                       │
│  Image Quality Processing                   │
│     ↓                                       │
│  Google ML Kit OCR                          │
│     ↓                                       │
│  OCR Text + Bounding Boxes + Field Values   │
└─────────────────────┬───────────────────────┘
                      │
                      │ Multipart HTTP Request
                      │
                      ▼
┌─────────────────────────────────────────────┐
│               FastAPI Backend               │
│                                             │
│  Original Image                             │
│  Document Type                              │
│  OCR JSON                                   │
└─────────────────────┬───────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│      Component 4 Python Detection Engine    │
│                                             │
│  OCR Validation                             │
│       ↓                                     │
│  Document Crop / Preprocessing              │
│       ↓                                     │
│  Normalization                              │
│       ↓                                     │
│  ROI Extraction                             │
│       ↓                                     │
│  Background Analysis                        │
│       ↓                                     │
│  Edge Analysis                              │
│       ↓                                     │
│  Text Structure Analysis                    │
│       ↓                                     │
│  Photo Analysis                             │
│       ↓                                     │
│  Signature / Logo Analysis                  │
│       ↓                                     │
│  Local Alteration Detection                 │
│       ↓                                     │
│  Suspicious Region Highlighting             │
│       ↓                                     │
│  Risk Scoring                               │
└─────────────────────┬───────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│              Analysis Result                │
│                                             │
│  Risk Score                                 │
│  LOW / MEDIUM / HIGH                        │
│  Findings                                   │
│  Suspicious Regions                         │
│  Highlighted Image                          │
│  Recommended Action                         │
└─────────────────────┬───────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│             Android Admin Dashboard         │
│                                             │
│  Original Image                             │
│  Highlighted Image                          │
│  Risk Score                                 │
│  OCR Information                            │
│  Detector Scores                            │
│  Suspicious Findings                        │
│  Recommended Action                         │
└─────────────────────────────────────────────┘
```

---

# 4. Component 4 Data Flow

A document follows this pipeline:

```text
Physical Document
        ↓
Android Camera2 Capture
        ↓
ML Kit OCR
        ↓
FastAPI Upload
        ↓
OCR Validation
        ↓
Document Boundary Detection / Cropping
        ↓
Image Normalization
        ↓
Template ROI Mapping
        ↓
ROI Extraction
        ↓
┌───────────────────────────────────┐
│ Background / Texture Analysis     │
│ Edge Analysis                     │
│ Text Structure Analysis           │
│ Photo Border Analysis             │
│ Signature / Logo Analysis         │
│ Local Alteration Detection        │
└───────────────────────────────────┘
        ↓
Evidence Combination
        ↓
Risk Scoring
        ↓
Highlighted Suspicious Image
        ↓
Admin Review
```

---

# 5. Repository Structure

The Component 4 project is approximately organised as:

```text
DocumentAlterationDetection/
│
├── backend/
│   ├── __init__.py
│   └── main.py
│
├── config/
│   ├── document_regions.json
│   └── ...
│
├── data/
│   │
│   ├── templates/
│   │   ├── nic_template_v1.jpg
│   │   └── driving_licence_template_v1.jpg
│   │
│   ├── genuine/
│   └── altered/
│
├── src/
│   ├── __init__.py
│   ├── check_image.py
│   ├── grayscale.py
│   ├── threshold.py
│   ├── edge_detection.py
│   ├── normalize.py
│   ├── template_regions.py
│   ├── extract_regions.py
│   ├── background_analysis.py
│   ├── compare_background.py
│   ├── roi_edge_analysis.py
│   ├── text_structure_analysis.py
│   ├── photo_analysis.py
│   ├── signature_logo_analysis.py
│   ├── altered_text_localization.py
│   ├── document_crop.py
│   ├── ocr_validation.py
│   ├── risk_scoring.py
│   └── analysis_pipeline.py
│
├── results/
│   ├── api_requests/
│   ├── pipeline_test/
│   └── ...
│
├── requirements.txt
├── .gitignore
└── README.md
```

The Android application contains Component 4 integration files such as:

```text
app/src/main/java/com/example/securedocumentcapture3/
│
├── CaptureActivity.kt
├── MlKitOcrProcessor.kt
├── OcrModels.kt
├── OcrFieldExtractor.kt
├── DocumentOcrData.kt
├── BackendApiClient.kt
│
├── AdminLoginActivity.kt
├── AdminDashboardActivity.kt
├── AdminDocumentDetailActivity.kt
├── AdminApiClient.kt
│
└── SecureStorage.kt
```

---

# 6. Approved Document Templates

The detection system is template based.

Each supported document type has an approved reference image.

Current templates:

```text
data/templates/nic_template_v1.jpg

data/templates/driving_licence_template_v1.jpg
```

The template establishes the expected:

- document dimensions
- general layout
- photo position
- text-field positions
- signature position
- logo location
- security-feature areas
- background characteristics

The submitted document is compared against these expected characteristics.

---

# 7. Region of Interest Configuration

Document fields are configured in:

```text
config/document_regions.json
```

Coordinates use normalized values:

```text
0.0 → left/top
1.0 → right/bottom
```

Example:

```json
{
    "NIC": {
        "regions": {
            "nic_number": {
                "x1": 0.54,
                "y1": 0.18,
                "x2": 0.93,
                "y2": 0.31,
                "type": "text"
            }
        }
    }
}
```

The normalized coordinates are converted into actual pixel coordinates according to the normalized document dimensions.

This allows the same ROI configuration to work with images of different input resolutions after normalization.

---

# 8. Document Preprocessing

## 8.1 Document Cropping

Real Android captures often contain:

```text
desk
table
background
shadows
empty space
```

around the document.

Comparing the entire photograph against a document template causes incorrect ROI positions and severe false positives.

A custom document-cropping stage was therefore introduced in:

```text
src/document_crop.py
```

The current approach estimates the surrounding background colour from image borders and searches for areas whose RGB colour distance differs sufficiently from the background.

Current development parameters include:

```text
BACKGROUND_THRESHOLD = 28

MINIMUM_DOCUMENT_RATIO = 0.08
```

The detected area is cropped before template normalization.

### Important limitation

The cropping algorithm is currently heuristic and requires further testing.

It may fail when:

- the document colour is similar to the table/background
- the background is highly textured
- several objects are visible
- strong shadows exist
- document edges are unclear

Perspective correction is also not yet complete.

This is one of the most important remaining improvements.

---

# 9. Image Normalization

Implemented in:

```text
src/normalize.py
```

The submitted document is converted to the same expected dimensions as the approved template.

The purpose is to ensure that:

```text
template ROI coordinates
```

and:

```text
submitted-document ROI coordinates
```

refer to approximately the same physical locations.

The current normalization performs image resizing.

### Current limitation

Simple resizing is insufficient when the card is:

- rotated
- photographed from an angle
- perspective distorted
- only partly visible

A future version should perform:

```text
corner detection
        ↓
four-point perspective transform
        ↓
canonical document alignment
```

before ROI comparison.

---

# 10. ROI Extraction

Implemented in:

```text
src/extract_regions.py
```

Each configured document region is extracted separately.

Typical NIC ROIs include:

```text
government_logo
photo
nic_number
name
sex
date_of_birth
holder_signature
```

Typical Driving Licence ROIs include fields such as:

```text
licence_number
nic_number
name
address
date_of_birth
photo
blood_group
holder_signature
official_signature
government_logo
security_mark
```

The extraction algorithm manually copies the required pixels from the source image.

Metadata is also saved containing:

```text
x1
y1
x2
y2
width
height
region type
```

This metadata is later used to convert suspicious local coordinates back into full-document coordinates.

---

# 11. Manual Grayscale Conversion

Several analysis modules use our own grayscale conversion.

For each RGB pixel:

```text
Gray =
0.299 × Red
+
0.587 × Green
+
0.114 × Blue
```

The result is constrained to:

```text
0 – 255
```

No ready-made fraud-analysis preprocessing function is used.

---

# 12. Thresholding

The text and symbol analysis use an automatically calculated threshold based on the image intensity histogram.

The algorithm evaluates possible thresholds and searches for the threshold producing the strongest separation between dark and light pixel groups.

The resulting binary image is approximately:

```text
0   → foreground / text
255 → background
```

This is used for connected-component analysis.

---

# 13. Background and Texture Analysis

Implemented in:

```text
src/background_analysis.py
```

This stage identifies unusual local texture or intensity patterns that may be associated with:

- erasing
- covering
- replacing text
- pasted content
- different printing/background characteristics

For each ROI the module calculates:

### Mean Brightness

Average grayscale intensity.

```text
mean_brightness
```

### Brightness Standard Deviation

Measures intensity variation.

```text
brightness_stddev
```

### Dark Pixel Ratio

Percentage of pixels below the dark threshold.

```text
dark_pixel_ratio
```

### Bright Pixel Ratio

Percentage of very bright pixels.

```text
bright_pixel_ratio
```

### Neighbour Difference

Each pixel is compared with its right and lower neighbour.

```text
abs(current_pixel - neighbouring_pixel)
```

Large values indicate stronger local texture variation.

Output:

```text
neighbour_difference
```

### Local Block Variation

The ROI is divided into:

```text
16 × 16
```

pixel blocks.

The mean brightness of every block is calculated.

Variation between block means is stored as:

```text
block_mean_stddev
```

This helps identify local patches with backgrounds unlike surrounding areas.

---

# 14. Background Template Comparison

Implemented in:

```text
src/compare_background.py
```

Corresponding template and submitted-document ROIs are compared.

Current feature weights:

```text
Mean brightness             20%
Brightness deviation        20%
Bright-pixel ratio          10%
Neighbour difference        25%
Block variation             25%
```

The result is:

```text
background_difference_score
```

with an analytical range of:

```text
0 – 100
```

This is a difference score.

It is **not a probability of fraud**.

---

# 15. Edge Analysis

Implemented in:

```text
src/roi_edge_analysis.py
```

The system implements its own Sobel-based edge detector.

Horizontal Sobel kernel:

```text
-1   0   1
-2   0   2
-1   0   1
```

Vertical Sobel kernel:

```text
-1  -2  -1
 0   0   0
 1   2   1
```

For each pixel:

```text
Gradient Magnitude =
sqrt(
    gradientX²
    +
    gradientY²
)
```

An adaptive threshold is calculated from:

```text
mean gradient
+
standard deviation
```

The current implementation constrains this threshold between approximately:

```text
40 – 600
```

Measured edge features include:

```text
edge_ratio
border_edge_ratio
centre_edge_ratio

left_edge_ratio
right_edge_ratio
top_edge_ratio
bottom_edge_ratio

mean_edge_strength
```

The output becomes:

```text
edge_difference_score
```

---

# 16. Text Structure Analysis

Implemented in:

```text
src/text_structure_analysis.py
```

This module analyses document text **without depending on OCR character values**.

It performs:

```text
grayscale conversion
        ↓
automatic threshold
        ↓
binary image
        ↓
8-connected component detection
        ↓
component filtering
        ↓
text-line grouping
        ↓
structural measurements
```

Connected components are identified using neighbouring pixels in eight directions.

Measured features include:

```text
component_count

mean_component_width
component_width_stddev

mean_component_height
component_height_stddev

mean_horizontal_gap
horizontal_gap_stddev

baseline_stddev

foreground_ratio
```

This allows the detector to identify possible changes in:

- character size
- text spacing
- baseline alignment
- foreground density
- printing structure

The result is:

```text
text_structure_difference_score
```

---

# 17. Photo Replacement Analysis

Implemented in:

```text
src/photo_analysis.py
```

The system intentionally does **not attempt facial identity verification**.

Instead it analyses the photograph boundary.

This is important because a genuine customer's face should naturally differ from the template person's face.

The module analyses:

```text
photo perimeter
border edge density
left boundary
right boundary
top boundary
bottom boundary
border gradient strength
```

Possible replacement/pasting may introduce abnormal rectangular edges.

The output is:

```text
photo_border_difference_score
```

This is supporting evidence only.

---

# 18. Signature, Logo and Security Feature Analysis

Implemented in:

```text
src/signature_logo_analysis.py
```

Applicable region types include:

```text
signature
logo
security_feature
```

The module performs thresholding and connected-component extraction.

Features include:

```text
foreground_ratio

component_count

mean_component_area

bounding_box_ratio

centre_x_ratio

centre_y_ratio
```

The result is:

```text
symbol_difference_score
```

### Important signature limitation

A holder signature cannot be declared forged simply because it differs from the template.

Without a known reference signature for that specific customer, this module only detects structural inconsistencies.

Therefore:

```text
signature difference
≠
confirmed forged signature
```

---

# 19. Altered-Text Localization

Implemented in:

```text
src/altered_text_localization.py
```

This module attempts to locate suspicious areas **inside** text ROIs.

Each ROI is divided into:

```text
16 × 16 pixel blocks
```

Each corresponding template/document block is compared.

Local block features include:

```text
brightness
brightness variation
texture variation
edge density
```

Current local score weighting:

```text
Brightness difference     20%
Variation difference      25%
Texture difference        30%
Edge difference           25%
```

An adaptive candidate threshold is calculated approximately as:

```text
mean block score
+
block-score standard deviation
```

with a development minimum threshold of:

```text
30
```

Blocks above the threshold are considered candidate suspicious areas.

Adjacent candidate blocks are merged.

Their ROI coordinates are converted back to full-document coordinates.

Result example:

```json
{
    "region": "nic_number",
    "score": 82.5,
    "x1": 610,
    "y1": 130,
    "x2": 670,
    "y2": 160
}
```

---

# 20. Highlighted Suspicious Image

After localization, Component 4 creates:

```text
highlighted_suspicious_areas.png
```

Suspicious candidate locations are drawn using red rectangles.

Example conceptual output:

```text
┌───────────────────────────────────────┐
│       NATIONAL IDENTITY CARD          │
│                                       │
│  Photo                                │
│                                       │
│  NIC: ┌───────────────────────┐       │
│       │ 200229900760           │       │
│       └───────────────────────┘       │
│                                       │
│  Name: OMAL RAJ WIJETUNGA            │
│                                       │
└───────────────────────────────────────┘
```

The red boxes mean:

```text
Visual inconsistency requiring review
```

They do **not** mean:

```text
Confirmed fraud
```

---

# 21. OCR Architecture

Originally, Tesseract OCR was considered.

The architecture was changed.

The current system uses:

```text
Google ML Kit Text Recognition
```

inside the Android application.

Tesseract is **not required**.

Therefore the Python backend does not require:

```text
tesseract.exe
pytesseract
```

---

# 22. Android ML Kit OCR

Implemented through files such as:

```text
MlKitOcrProcessor.kt
OcrModels.kt
OcrFieldExtractor.kt
DocumentOcrData.kt
```

The captured JPEG is converted into an ML Kit `InputImage`.

ML Kit returns:

```text
full recognized text

text lines

bounding boxes
```

Example:

```json
{
    "text": "200229900760",
    "boundingBox": {
        "left": 1042,
        "top": 356,
        "right": 1356,
        "bottom": 398
    }
}
```

---

# 23. OCR Candidate Field Extraction

The Android application attempts to identify important values such as:

```text
NIC number
Driving licence number
Name
Dates
Blood group
```

For example:

```text
NIC Number:
200229900760

Name:
OMAL RAJ WIJETUNGA

DOB:
25.10.2002
```

These are considered **candidate values**.

Python validates them again.

---

# 24. OCR Limitations

The current ML Kit configuration mainly targets Latin text.

Sri Lankan documents contain:

```text
Sinhala
Tamil
English
```

Therefore the current OCR often recognises English/numeric fields well but may produce incorrect Sinhala/Tamil text.

Common OCR errors observed include:

```text
O ↔ 0

spacing around date separators

partial field labels

incorrect multilingual characters
```

The field extractor contains basic normalization for some of these conditions.

More robust multilingual OCR remains an improvement area.

---

# 25. Python OCR Validation

Implemented in:

```text
src/ocr_validation.py
```

Python does **not rerun OCR**.

Instead it validates the ML Kit results.

Checks include:

```text
OCR payload structure

NIC format

Driving licence number format

Name structure

Date format

Calendar date validity

Blood group validity

OCR candidate vs full text

Bounding box validity

Bounding boxes inside image
```

Example NIC formats accepted include:

```text
12 digit new NIC

XXXXXXXXXXXX
```

and old NIC format:

```text
XXXXXXXXXV
XXXXXXXXXX
```

where the final character is:

```text
V or X
```

OCR validation returns:

```text
PASS
```

or:

```text
REVIEW
```

`REVIEW` does not mean fraud.

For example:

```text
DATE_MISSING
```

may simply mean ML Kit did not correctly recognize a date.

---

# 26. Risk Scoring Engine

Implemented in:

```text
src/risk_scoring.py
```

The final score combines multiple independent detectors.

Current development weights:

| Component | Weight |
|---|---:|
| Background analysis | 18% |
| Edge analysis | 18% |
| Text structure | 18% |
| Photo analysis | 12% |
| Signature/logo/security analysis | 10% |
| Localized alteration | 16% |
| OCR validation | 8% |

Total:

```text
100%
```

---

# 27. OCR Risk Contribution

OCR deliberately receives only:

```text
8%
```

of the final weight.

This prevents poor OCR quality from incorrectly dominating the fraud analysis.

OCR issue types are assigned supporting values.

Examples include:

```text
INVALID_NIC_FORMAT
INVALID_LICENCE_NUMBER
NIC_TEXT_INCONSISTENCY
LICENCE_TEXT_INCONSISTENCY
DATE_MISSING
NAME_MISSING
INVALID_DATE_FORMAT
```

The raw OCR evidence score is capped before final weighting.

OCR therefore acts as **supporting evidence** rather than primary visual evidence.

---

# 28. Current Risk Thresholds

Current development thresholds are:

```text
0.00 – 34.99
LOW

35.00 – 64.99
MEDIUM

65.00 – 100.00
HIGH
```

However, a HIGH classification additionally requires at least two strong independent visual evidence sources.

Current strong-evidence threshold:

```text
45
```

Visual evidence sources include:

```text
background

edge

text

photo

symbol

localization
```

This reduces the chance that one noisy detector alone causes a HIGH result.

---

# 29. Meaning of the Risk Score

A result such as:

```text
Risk Score: 72
```

does **not** mean:

```text
72% chance of fraud
```

Instead it means:

```text
Weighted document alteration review score = 72/100
```

It is intended to help prioritize manual investigation.

---

# 30. Recommended Actions

The current system uses actions similar to:

### LOW

```text
CONTINUE_NORMAL_PROCESS
```

### MEDIUM

```text
MANUAL_REVIEW_REQUIRED
```

### HIGH

```text
FRAUD_INVESTIGATOR_REVIEW_REQUIRED
```

The final determination remains with the investigator.

---

# 31. FastAPI Backend

Implemented primarily in:

```text
backend/main.py
```

FastAPI connects the Android application to Component 4.

The main document submission endpoint is:

```text
POST /api/v1/analyze-document
```

The Android application sends:

```text
image
document_type
ocr_json
```

as multipart form data.

---

# 32. Android → Backend Request

Conceptually:

```text
POST /api/v1/analyze-document

image:
captured_document.jpg

document_type:
National_Identity_Card

ocr_json:
{
    ...
}
```

Document types are mapped internally.

Example:

```text
National_Identity_Card
        ↓
NIC
```

and:

```text
Driving_Licence
        ↓
DRIVING_LICENCE
```

---

# 33. Backend Processing Order

The backend processing order is important.

It should be:

```text
1. Validate document type
2. Validate uploaded image
3. Parse OCR JSON
4. Generate document UUID
5. Save original image
6. Save OCR result
7. Validate OCR
8. Save OCR validation
9. Run alteration detection
10. Run risk scoring
11. Save request metadata
12. Return final API result
```

The OCR validation result must exist before the analysis pipeline receives it.

---

# 34. FastAPI Response

A successful completed response is conceptually:

```json
{
    "success": true,
    "document_id": "UUID",
    "document_type": "NIC",
    "ocr_validation_status": "PASS",
    "alteration_analysis_status": "COMPLETE",
    "suspicious_area_count": 2,
    "highlighted_image": "highlighted_suspicious_areas.png",
    "risk_score": 48.32,
    "risk_level": "MEDIUM",
    "recommended_action": "MANUAL_REVIEW_REQUIRED",
    "next_stage": "RESULT_READY"
}
```

---

# 35. Per-Request Backend Storage

Each submitted document receives a UUID.

Example:

```text
results/api_requests/
└── 52d4e109-4289-4d3b-99e2-1e7d3d0b9564/
```

A completed request may contain:

```text
captured_document.jpg

ocr.json

ocr_validation.json

request.json

analysis/
├── preprocessing/
│   ├── cropped_document.png
│   └── crop_result.json
│
├── normalized/
│   ├── template.png
│   └── document.png
│
├── regions/
│   ├── template/
│   └── document/
│
├── edge_maps/
│
├── region_metadata.json

├── background_analysis.json
├── edge_analysis.json
├── text_analysis.json
├── photo_analysis.json
├── symbol_analysis.json
├── altered_text_localization.json

├── highlighted_suspicious_areas.png
├── risk_score.json
└── analysis_result.json
```

---

# 36. Analysis Pipeline

The complete detection pipeline is controlled through:

```text
src/analysis_pipeline.py
```

It links previously independent algorithms into one operation.

Conceptually:

```python
run_analysis_pipeline(
    captured_image_path,
    document_type,
    output_folder,
    ocr_validation
)
```

It runs:

```text
cropping
normalization
ROI extraction
background analysis
edge analysis
text analysis
photo analysis
symbol analysis
altered-text localization
highlight generation
risk scoring
```

---

# 37. Android Camera Integration

The current camera component uses:

```text
Android Camera2 API
```

not CameraX.

The captured JPEG is temporarily held as:

```kotlin
ByteArray
```

inside:

```text
CaptureActivity.kt
```

The flow after the user presses:

```text
Use Photo
```

is:

```text
Captured JPEG ByteArray
        ↓
ML Kit OCR
        ↓
Create DocumentOcrData
        ↓
Send image + OCR to FastAPI
        ↓
Backend analysis
        ↓
Secure local storage
```

---

# 38. Android Secure Storage

The existing application also performs encrypted local document storage.

The secure-storage component uses Android cryptographic storage and AES/GCM encryption.

Therefore local document storage remains separate from Component 4 backend analysis.

Conceptually:

```text
Captured document
      ├───────────────→ Component 4 analysis server
      │
      └───────────────→ encrypted local Android storage
```

---

# 39. Android Development Network Connection

During development the physical Android phone connects to FastAPI through:

```bash
adb reverse tcp:8000 tcp:8000
```

FastAPI runs locally:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Android can then use:

```text
http://127.0.0.1:8000
```

as the development backend URL.

---

# 40. Production Network Requirement

The current development environment permits:

```text
HTTP
```

and Android may temporarily use:

```xml
android:usesCleartextTraffic="true"
```

This is **not suitable for production**.

A deployed version should use:

```text
HTTPS/TLS
```

and:

```text
android:usesCleartextTraffic="false"
```

---

# 41. Admin Dashboard

The Android application contains an administrative review interface.

The intended admin flow is:

```text
Admin Login
     ↓
Fraud Analysis Dashboard
     ↓
All Submitted Documents
     ↓
Select Case
     ↓
Detailed Analysis
```

The dashboard should display:

```text
Document Type

Submission Time

Risk Score

Risk Level

OCR Validation Status

Analysis Status

Suspicious Area Count
```

---

# 42. Admin Case Review Screen

Selecting one case should display:

```text
Original Captured Image

Highlighted Suspicious Image

Risk Score

LOW / MEDIUM / HIGH

Recommended Action

OCR-extracted information

Background Analysis Score

Edge Analysis Score

Text Structure Score

Photo Analysis Score

Signature / Logo Score

Localized Alteration Score

Investigation Findings

Suspicious Regions
```

Raw JSON should not normally be displayed to the administrator.

The UI should convert backend JSON into human-readable investigation information.

---

# 43. Admin API Endpoints

Current administrative endpoints include functionality equivalent to:

```text
GET /api/v1/admin/documents
```

Returns all document cases.

```text
GET /api/v1/admin/documents/{document_id}
```

Returns full case details.

```text
GET /api/v1/admin/documents/{document_id}/image/original
```

Returns the original submitted image.

```text
GET /api/v1/admin/documents/{document_id}/image/highlighted
```

Returns:

```text
highlighted_suspicious_areas.png
```

---

# 44. Why Risk Score May Show N/A

The admin UI shows:

```text
N/A
```

or:

```text
NOT_CALCULATED
```

when Step 19 or Step 20 fails.

For example:

```text
OCR succeeded
       ↓
OCR validation succeeded
       ↓
Physical analysis ERROR
       ↓
risk_score.json not created
       ↓
Admin displays N/A
```

Errors are saved in:

```text
analysis/analysis_error.json
```

This file should be checked first when:

```text
risk score = N/A
```

or the highlighted image is missing.

---

# 45. Current Analysis Result Files

The final key files are:

## `analysis_result.json`

Overall Component 4 result.

## `risk_score.json`

Final risk calculation.

## `highlighted_suspicious_areas.png`

Visual investigator output.

## `ocr_validation.json`

OCR field validation.

## `altered_text_localization.json`

Suspicious region coordinates.

---

# 46. Python Installation

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Core backend requirements include packages such as:

```text
fastapi
uvicorn
python-multipart
Pillow
```

The Python alteration detection does not require Tesseract.

---

# 47. Android OCR Dependency

The Android app currently uses the bundled ML Kit Latin text-recognition dependency.

The application module includes a dependency equivalent to:

```kotlin
implementation(
    "com.google.mlkit:text-recognition:16.0.1"
)
```

The application also requires:

```text
CAMERA
INTERNET
```

permissions.

---

# 48. Starting the Development System

Start the Python backend:

```powershell
.\.venv\Scripts\Activate.ps1

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Check:

```text
http://127.0.0.1:8000/health
```

Connect the Android phone:

```powershell
adb devices
```

Then:

```powershell
adb reverse tcp:8000 tcp:8000
```

Run the Android application from Android Studio.

---

# 49. Testing Workflow

For a complete test:

```text
1. Start FastAPI

2. Configure adb reverse

3. Run Android app

4. Select supported document

5. Capture physical document

6. Press Use Photo

7. ML Kit performs OCR

8. Android uploads image + OCR

9. Python validates OCR

10. Python crops / normalizes image

11. ROIs are extracted

12. Visual analysis runs

13. Suspicious areas are localized

14. Risk score is calculated

15. Result is returned

16. Admin opens dashboard

17. Admin reviews original and highlighted images
```

---

# 50. Test Data

The development dataset should contain separate categories:

```text
templates/
genuine/
altered/
```

Templates are approved reference images.

Genuine documents are used to measure normal variation.

Altered images are used to test whether modified areas receive higher anomaly scores.

---

# 51. Important Testing Rule

The same image should **not** be treated as both the training/calibration reference and final proof of detection performance.

A larger independent test set is required before claiming reliable accuracy.

Current testing is primarily prototype/functional testing.

---

# 52. Current Known Issues and Required Improvements

## 52.1 Perspective Correction — Incomplete

This is currently one of the largest technical limitations.

Real captured documents may be:

```text
rotated
tilted
perspective distorted
off-centre
```

The current template system expects approximately aligned images.

Required improvement:

```text
document edge detection
        ↓
four corner detection
        ↓
perspective transformation
        ↓
canonical orientation
```

---

## 52.2 Document Cropping — Requires Improvement

The current custom background-based crop works best when the card clearly differs from the surrounding surface.

It requires more testing under:

```text
dark backgrounds
white backgrounds
complex tables
shadows
partially visible documents
multiple objects
```

---

## 52.3 Rotation Detection — Incomplete

Documents photographed sideways need automatic orientation correction.

This is particularly important for Driving Licences.

---

## 52.4 ROI Accuracy — Requires Calibration

`document_regions.json` was manually configured from current templates.

New versions of documents may have different layouts.

ROI configurations must therefore support:

```text
document type
document version
template version
```

in the future.

---

## 52.5 Risk Thresholds — Provisional

Current risk levels:

```text
LOW    < 35
MEDIUM 35 – 64.99
HIGH   ≥ 65
```

are development thresholds.

They have **not yet been statistically calibrated using a large real-world dataset**.

Before claiming production accuracy, genuine and altered samples should be collected and threshold performance measured using:

```text
false-positive rate
false-negative rate
precision
recall
F1-score
confusion matrix
```

---

## 52.6 Detector Weights — Provisional

Current weights were selected logically for the prototype.

They should later be calibrated based on experimental results.

---

## 52.7 OCR Date Detection — Needs Improvement

Current OCR has occasionally returned text such as:

```text
2002/o25
```

instead of a valid date.

Date parsing requires additional normalization for OCR mistakes such as:

```text
O → 0
I → 1
spaces around separators
missing separators
```

---

## 52.8 Sinhala and Tamil OCR — Limited

The current ML Kit configuration primarily supports Latin text recognition.

The system therefore works better with:

```text
English text
numbers
dates
identification numbers
```

than complete Sinhala/Tamil extraction.

---

## 52.9 Photo Detection Is Not Face Verification

The photo module detects possible replacement boundaries.

It does not verify:

```text
Is this actually the same person?
```

Facial verification belongs to another component.

---

## 52.10 Signature Detection Is Not Signature Authentication

The system identifies structural anomalies.

It cannot state that a holder signature is forged without an approved customer signature reference.

---

## 52.11 Additional Document Types — Incomplete

The following still require:

```text
approved template
ROI configuration
feature calibration
validation rules
test samples
```

before full support:

```text
Bank Statement

Business Registration

Certificate of Incorporation

Vehicle Registration / CR Book

Salary Slip

Utility Bill

Other Certificates
```

---

## 52.12 Admin Authentication — Prototype Only

The Android prototype currently contains credentials similar to:

```text
admin
Admin@123
```

inside client-side code.

This is insecure and must not be used in production.

Required improvement:

```text
backend authentication
password hashing
session/token authentication
role-based access control
```

Authentication should eventually be provided through Component 1.

---

## 52.13 Admin Backend Endpoints — Require Authentication

Current development administrative endpoints may be accessible without server-side authorization.

Production endpoints must enforce:

```text
authenticated user
        ↓
admin role
        ↓
authorized case access
```

---

## 52.14 Agent Identification — Not Yet Integrated

Component 4 currently generates a document UUID.

It does not yet reliably store:

```text
agent ID
customer ID
branch ID
session ID
```

These should come from the authentication/customer-management components.

This is required to allow administrators to review cases by agent/customer.

---

## 52.15 Database Integration — Incomplete

Current Component 4 development outputs are file based under:

```text
results/api_requests/
```

Production integration should store appropriate metadata and results in the project's central database.

Images may remain in protected file/object storage with database references.

---

## 52.16 Audit Logging — Incomplete

A production system should log:

```text
who submitted the document
when it was submitted
who reviewed it
risk score
review decision
status changes
access to sensitive documents
```

---

## 52.17 HTTPS — Incomplete for Local Development

Current local testing uses HTTP.

Production must use HTTPS.

---

## 52.18 Result Retention — Incomplete

Current result folders contain sensitive identity information.

A production retention policy must define:

```text
how long originals remain
how long OCR is retained
who can access images
when analysis files are deleted
```

---

## 52.19 Image Privacy

The following can contain sensitive personal information:

```text
captured_document.jpg

ocr.json

ocr_validation.json

analysis_result.json

highlighted_suspicious_areas.png
```

These should not be publicly committed to GitHub.

---

## 52.20 False Positives From Image Conditions

The detector may respond strongly to:

```text
lighting
shadows
camera noise
compression
focus
different printer/scanner quality
document wear
lamination reflections
perspective distortion
```

Therefore image normalization and calibration are essential before deployment.

---

# 53. Security Considerations

The final implementation should enforce:

```text
HTTPS transport encryption

authenticated backend access

admin RBAC

encrypted document storage

secure secret storage

audit logging

restricted file access

PII retention controls

input validation

maximum upload sizes

safe document IDs

secure error handling
```

The existing Android application already performs encrypted local document storage, but backend storage security still needs production hardening.

---

# 54. Git Security

Do not commit real captured identity documents.

Recommended `.gitignore` entries include:

```gitignore
.venv/
__pycache__/
*.pyc

.idea/
.vscode/

.gradle/
build/
app/build/

local.properties

results/api_requests/
results/pipeline_test/

*.log
```

Approved synthetic/reference templates can remain tracked when appropriate.

Real NICs, licences, bank statements, and customer documents should not be uploaded to a public repository.

---

# 55. Current Component 4 Outputs

The module currently intends to provide:

```text
Document ID

Document Type

OCR Validation Status

OCR Issues

Risk Score

Risk Level

Recommended Action

Background Score

Edge Score

Text Score

Photo Score

Symbol Score

Localized Alteration Score

Suspicious Area Count

Suspicious Coordinates

Investigation Findings

Original Image

Highlighted Suspicious Image
```

---

# 56. Example Final Investigator Result

```text
Document:
National Identity Card

Analysis Status:
COMPLETE

Risk:
MEDIUM

Risk Score:
52.7 / 100

Recommended Action:
MANUAL REVIEW REQUIRED


Detector Results

Background:
45.7 / 100

Edges:
63.2 / 100

Text Structure:
59.2 / 100

Photo:
48.0 / 100

Signature / Logo:
32.4 / 100

Localized Alteration:
61.3 / 100


Detected Findings

• Unusual edge structure near NIC number.

• Background texture differs around date of birth.

• Text structure differs from approved template.

• Local visual inconsistency detected around NIC number.


System Decision:

Possible alteration detected.
Manual investigator review required.
```

This should not be represented as:

```text
Document definitely fraudulent
```

unless a human investigator confirms it.

---

# 57. Component Responsibility

Component 4 is responsible for:

```text
physical document visual analysis

OCR-result validation

template comparison

alteration localization

visual evidence generation

risk scoring
```

It is **not** responsible for:

```text
user authentication

customer account creation

face recognition

final fraud decision

central banking database verification
```

Those belong to other system components or human review.

---

# 58. Current Strengths

The current prototype demonstrates:

```text
live Android document capture

on-device OCR

Android → FastAPI communication

template-based ROI processing

manual pixel-level analysis algorithms

background analysis

edge analysis

text structure analysis

photo-border analysis

signature/logo/security analysis

localized alteration detection

highlight generation

multi-detector risk scoring

administrator review integration
```

The system also keeps OCR and visual alteration detection independent, which improves explainability.

---

# 59. Most Important Remaining Technical Work

Before considering Component 4 complete, the highest-priority work is:

```text
1. Reliable document boundary detection

2. Automatic orientation correction

3. Four-corner perspective correction

4. Better alignment between captured document and template

5. Calibration using larger genuine/altered datasets

6. Reduction of false-positive suspicious blocks

7. Additional document templates

8. Better OCR normalization

9. Full authenticated admin integration

10. Database and agent/customer integration

11. HTTPS and backend security hardening

12. End-to-end testing on multiple Android devices
```

The first four are particularly important because template-based detection depends heavily on correct document alignment.

---

# 60. Development Warning

The project is currently a **prototype / academic fraud-screening system**.

The current scores and thresholds should not be used as the sole basis for rejecting a real banking customer.

The intended workflow is:

```text
Automated screening
        ↓
Explainable findings
        ↓
LOW / MEDIUM / HIGH review priority
        ↓
Human investigator
        ↓
Final decision
```

---

# 61. Future Improvements

Future versions can extend the system with:

```text
perspective transformation

automatic template version detection

better color normalization

illumination correction

document-specific thresholds

larger calibration dataset

multilingual OCR

server authentication

database-backed cases

investigator notes

case status workflow

agent/customer linkage

audit logs

secure cloud object storage

automatic report generation

performance metrics

unit and integration tests
```

A later machine-learning model could also be researched, but the current academic implementation intentionally focuses on explainable manually implemented detection algorithms.

---

# 62. Summary

Component 4 currently provides an explainable physical-document alteration-analysis pipeline integrating an Android capture application with a Python FastAPI backend.

The Android application performs document capture and ML Kit OCR.

The Python backend performs the actual alteration detection through custom algorithms for:

```text
template comparison
background analysis
edge analysis
text structure analysis
photo-border analysis
signature/logo/security analysis
localized alteration detection
OCR validation
risk scoring
```

The resulting evidence is returned to an administrator through a fraud-analysis dashboard that is intended to display both the original capture and an annotated suspicious-area image.

The system is currently functional as a prototype for NIC and Driving Licence analysis, but significant work remains in document alignment, perspective correction, threshold calibration, additional document support, security hardening, database integration, and real-world testing before it can be considered production ready.
