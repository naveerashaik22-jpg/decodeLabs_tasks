"""Automated tests for the DocuMind core engine. Run:  python tests/test_core.py
Uses the generated sample images (run tests/make_samples.py first if missing)."""
import os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from PIL import Image
from core.pipeline import process_document
from core.qa import answer_question
from core.extract import masked_text
from core.ocr import fix_orientation

S = lambda n: os.path.join(ROOT, "samples", n)
def load(n): return process_document(open(S(n), "rb").read(), n)
results = []
def check(name, cond, detail=""):
    cond = bool(cond); results.append(cond); print(("PASS" if cond else "FAIL"), "|", name, ("| " + str(detail)) if detail else "")

notice, invoice, resume, blurry = (load(f) for f in
    ["sample_notice.png", "sample_invoice.png", "sample_resume.png", "sample_notice_degraded.png"])
ask = lambda d, q: answer_question(q, d["idx"], d["ents"], d["cls"])

# --- OCR ---------------------------------------------------------------------
check("OCR reads clean notice (>=45 words, quality Good)", len(notice["words"]) >= 45 and notice["quality"]["label"] == "Good", notice["quality"])
check("OCR keeps word coordinates inside the image",
      (notice["words"]["left"] >= 0).all() and (notice["words"]["left"] + notice["words"]["width"] <= notice["pages"][0].width + 5).all())
check("Blurry image: Otsu chosen, not the noisy variant", blurry["best"] == "Otsu threshold", blurry["best"])
check("Blurry image has low-confidence words flagged", len(blurry["words"][blurry["words"]["conf"] < 60]) >= 3)
check("Blank image gives no words and no crash", len(process_document(
    (lambda b: (Image.new("RGB", (600, 400), "white").save(b, format="PNG"), b.getvalue())[1])(__import__("io").BytesIO()), "blank.png")["words"]) == 0)

# --- orientation -------------------------------------------------------------
img = Image.open(S("sample_notice.png"))
for deg in (90, 180, 270):
    _, fixed = fix_orientation(img.rotate(deg, expand=True, fillcolor=(255, 255, 255)))
    check(f"Orientation: image rotated {deg} deg is detected", fixed == deg, fixed)

# --- PDF, multi-page ---------------------------------------------------------
pdf = os.path.join(tempfile.gettempdir(), "documind_test.pdf")
a, b = Image.open(S("sample_notice.png")).convert("RGB"), Image.open(S("sample_invoice.png")).convert("RGB")
a.save(pdf, save_all=True, append_images=[b])
pd_doc = process_document(open(pdf, "rb").read(), "t.pdf")
check("PDF: 2 pages processed", len(pd_doc["pages"]) == 2 and set(pd_doc["words"]["page"]) == {1, 2}, set(pd_doc["words"]["page"]))
check("PDF: facts from both pages found", any("Rs 45,000" in e["value"] for e in pd_doc["ents"]["Amounts"]) and pd_doc["ents"]["Dates"])

# --- extraction --------------------------------------------------------------
check("Extract: notice dates", {e["value"] for e in notice["ents"]["Dates"]} == {"15 December 2026", "05/12/2026"})
check("Extract: email + phone", [e["value"] for e in notice["ents"]["Emails"]] == ["examcell@crescent.example"] and [e["value"] for e in notice["ents"]["Phone numbers"]] == ["9876543210"])
check("Extract: invoice amount", [e["value"] for e in invoice["ents"]["Amounts"]] == ["Rs 45,000"])
check("Extract: resume Aadhaar-like + reg no", {e["value"] for e in resume["ents"]["Identifiers"]} >= {"1234 5678 9012", "240071601054"})
check("Extract: no sentence mistaken for organisation", all(len(e["value"].split()) <= 7 for e in notice["ents"]["Organisations"]))
check("Evidence: every entity maps to OCR words", all(e["ids"] for d in (notice, invoice, resume) for k in d["ents"].values() for e in k))

# --- classification ----------------------------------------------------------
check("Classify: notice -> Notice", notice["cls"]["label"] == "Notice", notice["cls"]["scores"])
check("Classify: invoice -> Financial", invoice["cls"]["label"] == "Financial")
check("Classify: resume -> Personal", resume["cls"]["label"] == "Personal")
from core.classify import classify_document
check("Classify: gibberish -> Unclassified", classify_document("zzz qqq www random words here")["label"] == "Unclassified")

# --- question answering (positive) -------------------------------------------
check("QA: last date", ask(notice, "What is the last date?")["answer"] == "05/12/2026")
check("QA: examination date", ask(notice, "What is the examination date?")["answer"] == "15 December 2026")
check("QA: email address (was broken in MVP)", ask(notice, "What is the email address?")["answer"] == "examcell@crescent.example")
check("QA: contact email address", ask(notice, "What is the contact email address?")["answer"] == "examcell@crescent.example")
check("QA: issuer", ask(notice, "Who issued this notice?")["answer"].startswith("B.S. Abdur Rahman"))
check("QA: total amount", ask(invoice, "What is the total amount?")["answer"] == "Rs 45,000")
check("QA: phone", ask(resume, "What is the mobile number?")["answer"] == "+91 98765 43210")
check("QA: summary + instructions return document lines", ask(notice, "Summarise this document")["found"] and ask(notice, "What are the important instructions?")["found"])
check("QA: answer words highlighted (ids returned)", len(ask(notice, "What is the last date?")["answer_ids"]) >= 1)
# --- question answering (must refuse) ----------------------------------------
for d, q in [(notice, "Who is the principal?"), (notice, "What is the date of birth?"), (notice, "What is the total amount?"),
             (invoice, "When is the hall ticket issued?"), (invoice, "Who is the principal?"), (invoice, "What is the phone number?")]:
    check(f"QA refuses: {q}", not ask(d, q)["found"])
check("QA: blurry exam date is NOT answered with the wrong date",
      ask(blurry, "When is the semester examination?")["answer"] != "05/12/2026")
check("QA: blurry low-confidence date flagged for review", ask(blurry, "What is the last date?")["answer"] == "05/12/2026")

# --- privacy -----------------------------------------------------------------
m = masked_text(resume["idx"], resume["ents"], "full")
check("Privacy: email/phone/IDs masked", all(x not in m for x in ["example.student@mail.example", "98765 43210", "1234 5678 9012", "240071601054"]), m[:0])
check("Privacy: non-sensitive text kept", "Curriculum Vitae" in m)
check("Privacy: partial mask keeps ends", "ex" in masked_text(notice["idx"], notice["ents"], "partial"))

print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
