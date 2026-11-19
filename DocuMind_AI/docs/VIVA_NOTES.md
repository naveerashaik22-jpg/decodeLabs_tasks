# Viva notes - DocuMind AI

## One-sentence pitch
A document-understanding app that reads a scan, extracts and classifies it, and answers questions only
from the document, proving every answer by highlighting the source words.

## Pipeline in one breath
Image/PDF -> OpenCV preprocessing -> Tesseract word boxes + confidence -> text index (character -> word) ->
regex extraction + rule-based classification -> evidence-based Q&A -> highlight on the image.

## Modules: what / why / limits
| Module | What it does | Why this choice | Limitation |
|---|---|---|---|
| ocr.py | Grayscale, blur, Otsu / adaptive threshold; Tesseract `image_to_data` | Word boxes + confidence enable highlighting and trust scores | Needs sharp, upright text |
| Variant selection | Runs 3 variants, keeps the one with most words >= 60% confidence | Raw word count is fooled by noise (found while testing) | Chosen on page 1 only |
| textindex.py | Keeps char offset -> word id | Lets any text match become image coordinates | Analysis uses original OCR, not edits |
| extract.py | Regex for dates, emails, phones, amounts, IDs | Predictable, explainable | Misses unusual formats |
| classify.py | Weighted keyword scores, heading bonus, Unclassified threshold | Explainable; no invented accuracy | Not trained ML |
| qa.py | Intent rules (date, email, amount, issuer...) + idf-weighted line retrieval | Never invents text; refuses safely | No reasoning, small synonym list |
| Quality score | 50% mean conf + 30% confident share + 20% (100 - noise) | Measurable signals, formula shown | Not a correctness guarantee |
| Privacy | Pattern detection + masking | Local-only, no uploads | Pattern based, can miss |

## Likely questions
- **Is this machine learning?** The OCR engine (Tesseract) is ML-based. Our classifier and assistant are
  rule-based on purpose: they are explainable, and we do not claim accuracy we have not measured.
- **Why not an LLM?** An LLM can invent answers. This design only returns text that exists in the document.
- **How do you stop wrong answers?** Intent rules, relevance checks, and refusal when nothing matches.
  During testing we found and fixed cases where a date or name was attached to the wrong question.
- **What is the Evidence Explorer?** Every fact stores its OCR word ids, so it can be drawn on the image.
- **What if the OCR is wrong?** Low-confidence words are shown in red, affected facts get a warning, and the
  quality score drops. The assistant adds a "verify on the image" note.
- **How was it tested?** 40 automated checks (OCR, rotation, PDF, extraction, classification, answers and
  refusals, privacy) plus a UI journey test. Samples are generated images, so real-world accuracy is not claimed.
- **What would you improve?** A trained classifier on real labelled data, small-angle deskew, table
  detection, multilingual OCR, and handwriting support.

## Timeline honesty
The four DecodeLabs tasks were completed and certified during the internship. DocuMind AI is an
enhancement built afterwards that reuses their ideas.
