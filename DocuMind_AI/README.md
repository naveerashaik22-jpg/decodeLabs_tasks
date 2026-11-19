# DocuMind AI

**An Intelligent Document Understanding, Verification and Evidence-Based Assistance Platform**

Upload a scanned document (image or PDF). DocuMind AI reads it with OCR, extracts the facts that
matter, classifies it, tells you how much to trust the reading, protects sensitive data, and answers
your questions **only from what is written in the document**, highlighting the exact words on the page.

Built on the DecodeLabs internship projects: the OCR engine reuses the Project 4 Tesseract setup
(path detection, `--psm 6`, grayscale + Gaussian blur + Otsu); the question answering extends the
Project 1 chatbot idea; the scoring ideas come from Project 3; the classification and evaluation mindset
from Project 2. The original `decodeLabs_tasks` repository is untouched.

## What it does
| Area | Feature |
|---|---|
| OCR | PNG / JPG / PDF (up to 8 pages), 3 preprocessing variants compared automatically, 90/180/270 degree rotation fixed, word-level confidence and bounding boxes, low-confidence words in red, editable text |
| Intelligence | Dates, emails, phone numbers, amounts, URLs, names (only where labelled), organisations, ID-like numbers; each fact links to its source text and OCR words |
| Classification | Academic, Business, Financial, Legal, Technical, Notice, Personal, or **Unclassified**. **Rule-based keyword scoring, not trained ML**; shows the keywords behind each decision |
| Assistant | Intent rules + weighted retrieval over OCR lines. Answers only with supporting text; highlights evidence on the image; says "Insufficient evidence" otherwise. **No language model is used.** |
| Trust | OCR quality indicator from measurable signals, extraction warnings, missing-information check |
| Privacy shield | Detects emails / phones / ID-like numbers, masked text and blacked-out image export. No external services are called |
| Insights | Extractive summary, explained recommendations, chronological timeline |
| Compare | Two documents: changed lines (word-level diff) and changed facts |
| Export | TXT, JSON, masked TXT, masked image |

## Run on Windows
1. Install Python 3.10+ and Tesseract OCR (https://github.com/UB-Mannheim/tesseract/wiki, keep the default folder `C:\Program Files\Tesseract-OCR\`).
2. In PowerShell, inside this folder:
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
Open the Local URL shown (normally http://localhost:8501). If activation is blocked, run
`Set-ExecutionPolicy -Scope Process Bypass` first.

## Demo journey (about 3 minutes)
1. **Home**: click *College notice* (or upload your own). Watch the processing steps.
2. **Document Viewer**: green = confident words, red = low confidence.
3. **Intelligence**: category with the keywords behind it, extracted facts, Evidence Explorer.
4. **Assistant**: ask "What is the last date?", then "Who is the principal?" (it refuses).
5. **Trust & Privacy**: quality score, warnings, masked export.
6. Optional: **Compare** with the revised-notice sample, **Blurry notice** sample to show uncertainty.

## Architecture
```
app.py                Streamlit UI (8 pages) - presentation only
ui/theme.py           CSS design system and HTML components
core/pipeline.py      process_document(): runs everything, returns one result
core/ocr.py           loading (image/PDF), OpenCV preprocessing, orientation, Tesseract, quality, annotation
core/textindex.py     rebuilds text from OCR words and keeps character -> word mapping (the basis of evidence)
core/extract.py       regex / rule extraction + privacy masking
core/classify.py      weighted keyword classification (rule-based)
core/qa.py            question intent detection + evidence-based answering
core/insights.py      keywords, recommendations, timeline, completeness, comparison
tests/                make_samples.py, test_core.py (40 checks), test_app.py (UI journey)
samples/              generated test images (synthetic)
docs/screenshots/     screenshots from a real test run
```
Key idea: `textindex.py` records which OCR word produced every character. Any fact or answer found in
the text can therefore be mapped back to image coordinates, which is how evidence is highlighted.

## Tests
```
python tests\make_samples.py     # regenerate sample images (optional)
python tests\test_core.py        # 40 checks: OCR, rotation, PDF, extraction, classification, QA, refusals, privacy
python tests\test_app.py         # drives the real app through every page
```
Results on the development machine: `test_core.py` 40/40 passed, `test_app.py` all pages rendered and
the assistant answered. These tests use the generated sample images.

## Honest limitations
- The samples are generated from text, so they OCR cleanly. Real photos, handwriting, tables, stamps and
  low-resolution scans will be harder. No accuracy figure is claimed for real-world documents.
- OCR confidence is Tesseract's own estimate, not a guarantee of correctness. The quality score is a
  transparent formula (50% mean confidence, 30% share of confident words, 20% inverse noise), not a benchmark.
- Classification is keyword scoring with hand-written weights. It is explainable but not trained, and
  unusual documents may be Unclassified or mixed.
- The assistant matches keywords and rules. It cannot reason, combine facts, or understand paraphrases
  beyond a small synonym list. When unsure it refuses rather than guesses.
- Only 90/180/270 degree rotations are corrected; small skew is not. Tesseract is configured for English.
- Name detection only uses titles (Dr., Mr. ...) and labels (Name:, Issued by: ...). It does not guess names.
- PDFs are rasterised and OCR'd (first 8 pages), even if they contain a text layer.

## Deploying (Streamlit Community Cloud)
Main file: `DocuMind_AI/app.py` (when this folder sits inside the `decodeLabs_tasks` repo).
Tesseract is installed on the server through a `packages.txt` file in the repository root containing
`tesseract-ocr`. On a public deployment, uploaded files are processed on Streamlit's servers, so use
only sample or non-personal documents for demos.
