"""One call that runs the whole document pipeline and returns a result dict."""
from core import classify, extract, insights
from core.ocr import load_pages, ocr_pages, quality_report
from core.textindex import DocIndex


def process_document(data: bytes, filename: str, psm=6, auto_select=True,
                     auto_orient=True, low_conf=60, progress=None):
    say = progress or (lambda m: None)
    say("Loading document...")
    pages, note = load_pages(data, filename)
    words, info = ocr_pages(pages, psm, auto_select, auto_orient, progress=say)
    say("Understanding the text...")
    idx = DocIndex(words)
    ents = extract.find_entities(idx)
    cls = classify.classify_document(idx.text, n_amounts=len(ents["Amounts"]))
    if cls["label"] == "Personal" and not ents["Names"]:
        g = extract.guess_header_name(idx)
        if g:
            ents["Names"].append(g)
    quality = quality_report(words, low_conf)
    return {
        "name": filename, "note": note, "pages": info["pages"], "words": words,
        "idx": idx, "ents": ents, "cls": cls, "quality": quality,
        "best": info["best"], "comparison": info["comparison"],
        "rotations": info["rotations"], "keywords": insights.keywords(idx, cls),
        "completeness": insights.completeness(cls, ents),
        "uncertainties": insights.uncertainties(words, ents, low_conf),
        "recs": insights.recommendations(cls, ents, quality, idx),
        "timeline": insights.timeline(ents),
    }
