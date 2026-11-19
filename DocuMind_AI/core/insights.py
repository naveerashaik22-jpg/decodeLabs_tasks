"""Insights built only from extracted content: keywords, recommendations,
timeline, completeness checks and document comparison."""
import difflib
import re
from collections import Counter

from dateutil import parser as dparser

from core.qa import STOP, CUES, tokens

# Fields we expect to see in each kind of document (used for missing-information checks)
EXPECTED = {
    "Notice": [("an issuing organisation", "Organisations"), ("a date", "Dates"),
               ("a contact (email or phone)", ("Emails", "Phone numbers"))],
    "Financial": [("an amount", "Amounts"), ("a date", "Dates"),
                  ("an organisation", "Organisations")],
    "Academic": [("a date", "Dates"), ("an organisation", "Organisations")],
    "Business": [("a date", "Dates"), ("an organisation", "Organisations"),
                 ("a contact (email or phone)", ("Emails", "Phone numbers"))],
    "Legal": [("a date", "Dates"), ("a named party", "Names")],
    "Personal": [("a contact (email or phone)", ("Emails", "Phone numbers")), ("a name", "Names")],
}


def keywords(idx, cls, top=10):
    """Frequency-based keywords plus category keywords. Simple and explainable."""
    words = re.findall(r"[A-Za-z][A-Za-z\-]{3,}", idx.text)
    cnt = Counter(w.lower() for w in words if w.lower() not in STOP)
    header = set(re.findall(r"[a-z]{4,}", " ".join(idx.text.lower().split("\n")[:2])))
    for w in header:
        if w in cnt:
            cnt[w] += 1.5
    cat_terms = {t for t, _ in cls["matched"].get(cls["label"], [])} if not cls["unclassified"] else set()
    for w in list(cnt):
        if w in cat_terms:
            cnt[w] += 1
    return [w for w, _ in cnt.most_common(top)]


def completeness(cls, ents):
    cat = cls["label"]
    exp = EXPECTED.get(cat)
    if not exp:
        return None
    present, missing = [], []
    for label, kinds in exp:
        kinds = (kinds,) if isinstance(kinds, str) else kinds
        (present if any(ents[k] for k in kinds) else missing).append(label)
    return {"category": cat, "present": present, "missing": missing,
            "pct": round(100 * len(present) / len(exp))}


def uncertainties(words, ents, low_conf=60):
    out = []
    low = words[words["conf"] < low_conf]
    if len(low):
        out.append(f"{len(low)} word(s) were read with OCR confidence below {low_conf}%.")
    for kind, items in ents.items():
        for e in items:
            if e["conf"] < low_conf:
                out.append(f"{kind[:-1] if kind.endswith('s') else kind} '{e['value']}' has low OCR "
                           f"confidence ({e['conf']}%). Verify it on the image.")
    return out


def recommendations(cls, ents, quality, idx):
    recs = []
    lab = cls["label"]
    deadline_dates = []
    for e in ents["Dates"]:
        li = idx.line_index_at(e["start"])
        if re.search(CUES["deadline"], idx.lines[li]["text"], re.I) and \
                re.search(r"last date|deadline|due|submit", idx.lines[li]["text"], re.I):
            deadline_dates.append(e)
    if deadline_dates:
        e = deadline_dates[0]
        recs.append(("Review the deadline", f"A date ({e['value']}) appears next to deadline wording.",
                     e["line"], e["ids"]))
    exam = [e for e in ents["Dates"] if re.search(r"exam|test|viva|hall ticket", e["line"], re.I)]
    if exam:
        recs.append(("Note the examination date", f"A date ({exam[0]['value']}) is on a line "
                     "that mentions an examination.", exam[0]["line"], exam[0]["ids"]))
    if lab == "Academic" and re.search(r"time ?table|schedule", idx.text, re.I):
        recs.append(("Identify examination dates", "The document looks academic and mentions a "
                     "timetable or schedule.", "", []))
    if lab == "Financial" or ents["Amounts"]:
        if ents["Amounts"]:
            recs.append(("Check the total and payment details",
                         f"{len(ents['Amounts'])} amount(s) were found"
                         + (" in a financial document." if lab == "Financial" else "."),
                         ents["Amounts"][0]["line"], ents["Amounts"][0]["ids"]))
    if ents["Emails"] or ents["Phone numbers"]:
        c = (ents["Emails"] + ents["Phone numbers"])[0]
        recs.append(("Keep the contact details for follow-up", "An email address or phone number "
                     "was found.", c["line"], c["ids"]))
    sens = [e for k in ents.values() for e in k if e["sensitive"]]
    if sens:
        recs.append(("Mask sensitive data before sharing", f"{len(sens)} sensitive item(s) "
                     "(email, phone or ID-like number) were detected.", "", []))
    if quality["label"] in ("Poor", "Too little text"):
        recs.append(("Upload a clearer image", f"The OCR quality indicator is {quality['label']} "
                     f"({quality['score']}/100).", "", []))
    elif quality["label"] == "Fair":
        recs.append(("Verify highlighted words manually", f"The OCR quality indicator is Fair "
                     f"({quality['score']}/100), so some words may be misread.", "", []))
    if cls["unclassified"]:
        recs.append(("Check the document type manually", cls["explanation"], "", []))
    return recs


def timeline(ents):
    """Dates in chronological order. Dates without a year are listed last."""
    dated, undated = [], []
    for e in ents["Dates"]:
        try:
            has_year = bool(re.search(r"\d{4}|\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2}\b", e["value"]))
            d = dparser.parse(e["value"], dayfirst=True, fuzzy=True)
            (dated if has_year else undated).append((d, e))
        except (ValueError, OverflowError):
            undated.append((None, e))
    dated.sort(key=lambda x: x[0])
    rows = []
    for d, e in dated:
        rows.append({"date": d.strftime("%d %b %Y"), "value": e["value"], "event": e["line"],
                     "ids": e["ids"], "page": e["page"], "note": ""})
    for d, e in undated:
        rows.append({"date": "Year not stated", "value": e["value"], "event": e["line"],
                     "ids": e["ids"], "page": e["page"], "note": "No year in the text"})
    return rows


# ------------------------------------------------------------ comparison -----
def compare_documents(a_lines, b_lines, a_ents, b_ents):
    """Line-level and fact-level comparison of two documents."""
    sm = difflib.SequenceMatcher(None, a_lines, b_lines, autojunk=False)
    common, changed, removed, added = [], [], [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            common += a_lines[i1:i2]
        elif tag == "replace":
            for x, y in zip(a_lines[i1:i2], b_lines[j1:j2]):
                changed.append((x, y))
            removed += a_lines[i1 + (j2 - j1):i2] if (i2 - i1) > (j2 - j1) else []
            added += b_lines[j1 + (i2 - i1):j2] if (j2 - j1) > (i2 - i1) else []
        elif tag == "delete":
            removed += a_lines[i1:i2]
        elif tag == "insert":
            added += b_lines[j1:j2]
    facts = {}
    for kind in ("Dates", "Amounts", "Emails", "Phone numbers", "URLs"):
        sa = {e["value"] for e in a_ents[kind]}
        sb = {e["value"] for e in b_ents[kind]}
        facts[kind] = {"only_a": sorted(sa - sb), "only_b": sorted(sb - sa), "both": sorted(sa & sb)}
    return {"similarity": round(100 * sm.ratio()), "common": common, "changed": changed,
            "removed": removed, "added": added, "facts": facts}


def word_diff_html(a, b):
    """Inline word-level diff as HTML (deleted = red, inserted = green)."""
    import html
    wa, wb = a.split(), b.split()
    out_a, out_b = [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, wa, wb).get_opcodes():
        ta, tb = html.escape(" ".join(wa[i1:i2])), html.escape(" ".join(wb[j1:j2]))
        if tag == "equal":
            out_a.append(ta); out_b.append(tb)
        else:
            if ta: out_a.append(f'<span class="df-del">{ta}</span>')
            if tb: out_b.append(f'<span class="df-add">{tb}</span>')
    return " ".join(out_a), " ".join(out_b)
