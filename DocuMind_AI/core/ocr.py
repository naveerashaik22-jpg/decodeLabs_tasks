"""OCR engine: OpenCV preprocessing + Tesseract word-level extraction.

Tesseract path detection and the `--psm 6` default are reused from Project 4
(Image_Text_Recognition) of the DecodeLabs internship.
"""
import io
import os
import re
import shutil

import cv2
import numpy as np
import pandas as pd
import pytesseract
from PIL import Image, ImageOps

# --- Tesseract path (same logic as Project 4) -------------------------------
if os.name == "nt":
    _win = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(_win):
        pytesseract.pytesseract.tesseract_cmd = _win
else:
    _path = shutil.which("tesseract")
    if _path:
        pytesseract.pytesseract.tesseract_cmd = _path

MAX_SIDE = 3000
MAX_PDF_PAGES = 8
WORD_COLUMNS = ["word_id", "page", "text", "conf", "left", "top", "width",
                "height", "block", "par", "line"]


def tesseract_available() -> bool:
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


# --- Loading images / PDFs ---------------------------------------------------
def load_pages(data: bytes, filename: str):
    """Return (list of RGB PIL pages, note). Supports images and PDFs."""
    name = filename.lower()
    if name.endswith(".pdf"):
        import pymupdf                                        # PyMuPDF
        doc = pymupdf.open(stream=data, filetype="pdf")
        total = len(doc)
        pages = []
        for i in range(min(total, MAX_PDF_PAGES)):
            pix = doc[i].get_pixmap(dpi=200)
            pages.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
        note = (f"PDF with {total} page(s); first {MAX_PDF_PAGES} processed."
                if total > MAX_PDF_PAGES else f"PDF with {total} page(s).")
    else:
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
        pages, note = [img], "Image file."
    out = []
    for p in pages:
        if max(p.size) > MAX_SIDE:
            p = p.copy(); p.thumbnail((MAX_SIDE, MAX_SIDE))
        out.append(p)
    return out, note


# --- Preprocessing -----------------------------------------------------------
def _prepare_gray(rgb):
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    scale, longest = 1.0, max(gray.shape)
    if longest < 1500:                                  # small images OCR poorly
        scale = 1500 / longest
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    return gray, scale


def preprocess_variants(rgb):
    """{name: (image, scale)} for each preprocessing variant."""
    gray, scale = _prepare_gray(rgb)
    denoised = cv2.GaussianBlur(gray, (5, 5), 0)                      # from Project 4
    _, otsu = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    adaptive = cv2.adaptiveThreshold(cv2.medianBlur(gray, 3), 255,
                                     cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 31, 15)
    return {"Grayscale": (gray, scale), "Otsu threshold": (otsu, scale),
            "Adaptive threshold": (adaptive, scale)}


# --- Orientation -------------------------------------------------------------
def fix_orientation(pil):
    """Use Tesseract OSD to detect 90/180/270 degree rotation. Returns
    (image, degrees_corrected). Small skew angles are not corrected."""
    try:
        osd = pytesseract.image_to_osd(np.array(pil.convert("L")),
                                       output_type=pytesseract.Output.DICT)
        rot, oconf = int(osd.get("rotate", 0)), float(osd.get("orientation_conf", 0))
    except Exception:
        return pil, 0
    if rot in (90, 180, 270) and oconf >= 1.5:
        return pil.rotate(-rot, expand=True, fillcolor=(255, 255, 255)), rot
    return pil, 0


# --- OCR ---------------------------------------------------------------------
def _ocr_words(img, scale, psm=6):
    data = pytesseract.image_to_data(img, config=f"--psm {psm}",
                                     output_type=pytesseract.Output.DICT)
    df = pd.DataFrame(data)
    df["conf"] = pd.to_numeric(df["conf"], errors="coerce")
    df = df[(df["conf"] >= 0) & (df["text"].astype(str).str.strip() != "")].copy()
    for c in ["left", "top", "width", "height"]:
        df[c] = (df[c] / scale).round().astype(int)          # back to original size
    df = df.rename(columns={"block_num": "block", "par_num": "par", "line_num": "line"})
    df["text"] = df["text"].astype(str).str.strip()
    return df.reset_index(drop=True)


def _confident(df):
    return int((df["conf"] >= 60).sum())


def ocr_pages(pages, psm=6, auto_select=True, auto_orient=True, progress=None):
    """OCR every page. The preprocessing variant is chosen on page 1 (the one
    with the most confident words) and reused for later pages.

    Returns (words_df, info) where info has: best, comparison, rotations, pages."""
    all_words, rotations, comparison, best, oriented = [], [], None, None, []
    counter = 0
    for pi, page in enumerate(pages, start=1):
        if progress:
            progress(f"Reading page {pi} of {len(pages)}...")
        rot = 0
        if auto_orient:
            page, rot = fix_orientation(page)
        rotations.append(rot)
        oriented.append(page)
        variants = preprocess_variants(np.array(page))
        if best is None:                                      # choose on first page
            if not auto_select:
                variants_to_try = {"Otsu threshold": variants["Otsu threshold"]}
            else:
                variants_to_try = variants
            results, rows = {}, []
            for name, (img, scale) in variants_to_try.items():
                df = _ocr_words(img, scale, psm)
                results[name] = df
                rows.append({"Preprocessing": name, "Words found": len(df),
                             "Confident words (>=60)": _confident(df),
                             "Mean confidence": round(df["conf"].mean(), 1) if len(df) else 0.0})
            comparison = pd.DataFrame(rows)
            # Most CONFIDENT words wins (raw word count is misleading on noisy
            # images, where Tesseract invents many low-confidence "words").
            best = max(results, key=lambda n: (_confident(results[n]),
                                               results[n]["conf"].mean() if len(results[n]) else 0))
            df = results[best]
        else:
            img, scale = variants[best]
            df = _ocr_words(img, scale, psm)
        df["page"] = pi
        df["word_id"] = range(counter, counter + len(df))
        counter += len(df)
        all_words.append(df)
    words = pd.concat(all_words, ignore_index=True) if all_words else pd.DataFrame(columns=WORD_COLUMNS)
    if len(words):
        words = words[WORD_COLUMNS]
    return words, {"best": best, "comparison": comparison,
                   "rotations": rotations, "pages": oriented}


# --- Document quality (measurable OCR signals) --------------------------------
def quality_report(words, low_conf=60):
    n = len(words)
    if n == 0:
        return {"score": 0, "label": "No text", "mean_conf": 0, "confident_pct": 0,
                "low_pct": 0, "noise_pct": 0, "words": 0}
    mean_conf = float(words["conf"].mean())
    confident_pct = 100 * float((words["conf"] >= low_conf).mean())
    def noisy(t):
        alnum = sum(ch.isalnum() for ch in t)
        return alnum / max(len(t), 1) < 0.5 or (len(t) > 3 and not re.search(r"[aeiouAEIOU0-9]", t))
    noise_pct = 100 * float(words["text"].map(noisy).mean())
    score = 0.5 * mean_conf + 0.3 * confident_pct + 0.2 * (100 - noise_pct)
    if n < 8:
        label = "Too little text"
    else:
        label = "Good" if score >= 85 else "Fair" if score >= 70 else "Poor"
    return {"score": round(score, 1), "label": label, "mean_conf": round(mean_conf, 1),
            "confident_pct": round(confident_pct, 1),
            "low_pct": round(100 - confident_pct, 1),
            "noise_pct": round(noise_pct, 1), "words": n}


# --- Annotation ---------------------------------------------------------------
def annotate(pil_image, words, low_conf, support_ids=None, answer_ids=None,
             show_normal=True, show_low=True, redact_ids=None, fill_redact=False):
    """Draw OCR boxes on a page image.
    green = confident, red = low confidence, cyan = supporting text,
    orange = answer words, black fill = redacted (privacy mask)."""
    img = np.array(pil_image.convert("RGB")).copy()
    thick = max(1, int(max(img.shape[:2]) / 900))
    support_ids, answer_ids = set(support_ids or []), set(answer_ids or [])
    redact_ids = set(redact_ids or [])
    for _, w in words.iterrows():
        x, y, bw, bh = int(w.left), int(w.top), int(w.width), int(w.height)
        wid = w.word_id
        if wid in redact_ids and fill_redact:
            cv2.rectangle(img, (x - 2, y - 2), (x + bw + 2, y + bh + 2), (0, 0, 0), -1)
        elif wid in redact_ids:
            cv2.rectangle(img, (x - 2, y - 2), (x + bw + 2, y + bh + 2), (168, 85, 247), thick * 3)
        elif wid in answer_ids:
            cv2.rectangle(img, (x - 3, y - 3), (x + bw + 3, y + bh + 3), (255, 140, 0), thick * 3)
        elif wid in support_ids:
            cv2.rectangle(img, (x - 2, y - 2), (x + bw + 2, y + bh + 2), (34, 211, 238), thick * 2)
        elif w.conf < low_conf and show_low:
            cv2.rectangle(img, (x, y), (x + bw, y + bh), (239, 68, 68), thick * 2)
        elif show_normal and w.conf >= low_conf:
            cv2.rectangle(img, (x, y), (x + bw, y + bh), (34, 197, 94), thick)
    return Image.fromarray(img)
