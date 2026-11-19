"""Information extraction with regular expressions and simple rules.
Every entity keeps its character span, so it can be mapped back to OCR words."""
import re

_MON = (r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|"
        r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)")
DATE_PATTERNS = [
    ("DD/MM/YYYY", r"(?<![\d/])\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}(?![\d/])"),
    ("YYYY-MM-DD", r"(?<![\d/])\d{4}[/\-.]\d{1,2}[/\-.]\d{1,2}(?![\d/])"),
    ("DD Month YYYY", rf"\b\d{{1,2}}(?:st|nd|rd|th)?[\s\-]+(?:of\s+)?{_MON}\b\.?,?(?:[\s\-]+\d{{4}})?"),
    ("Month DD, YYYY", rf"\b{_MON}\b\.?\s+\d{{1,2}}(?:st|nd|rd|th)?\b(?:,?\s+\d{{4}})?"),
]
EMAIL = r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}"
URL = r"(?:https?://|www\.)[^\s<>\"']+"
MONEY = (r"(?:(?:₹|Rs\.?|INR|USD|US\$|\$|€|£)\s?\d[\d,]*(?:\.\d+)?"
         r"|\d[\d,]*(?:\.\d+)?\s?(?:rupees|rs\b\.?|inr|usd|dollars))")
PHONE_PATTERNS = [
    r"(?<![\w.@/\-])(?:\+?91[\s\-]?)?[6-9]\d{4}[\s\-]?\d{5}(?!\w)",
    r"(?<![\w.@/\-])\+\d{1,3}[\s\-]?\d{2,5}[\s\-]?\d{3,5}[\s\-]?\d{3,5}(?!\w)",
    r"(?<![\w.@/\-])\(?0\d{2,4}\)?[\s\-]\d{6,8}(?!\w)",
]
ORG_WORDS = r"(?:institute|university|college|school|company|pvt|ltd|limited|corporation|department|bank|technologies|solutions|supplies|academy|council|ministry|office of|trust|foundation|enterprises|industries|labs?)"
KINDS = ["Dates", "Amounts", "Emails", "Phone numbers", "URLs", "Names",
         "Organisations", "Identifiers"]


def _add(store, kind, idx, start, end, why, sensitive=False, subtype=""):
    value = idx.text[start:end].strip().rstrip(".,;:)")
    end = start + len(idx.text[start:end].rstrip().rstrip(".,;:)"))
    if not value:
        return
    ids = idx.ids_in_span(start, end)
    li = idx.line_index_at(start)
    store[kind].append({
        "kind": kind, "value": value, "start": start, "end": end, "ids": ids,
        "line": idx.lines[li]["text"] if idx.lines else "",
        "page": idx.page_of(ids), "conf": idx.mean_conf(ids),
        "why": why, "sensitive": sensitive, "subtype": subtype})


def _overlaps(taken, s, e):
    return any(s < te and e > ts for ts, te in taken)


def find_entities(idx) -> dict:
    t = idx.text
    out = {k: [] for k in KINDS}
    taken = []                     # spans already claimed (avoid double-counting)

    def claim(kind, pattern, why, flags=0, **kw):
        for m in re.finditer(pattern, t, flags):
            s, e = m.start(), m.end()
            if _overlaps(taken, s, e):
                continue
            if kw.get("validate") and not kw["validate"](m.group(0)):
                continue
            _add(out, kind, idx, s, e, why, kw.get("sensitive", False), kw.get("subtype", ""))
            taken.append((s, e))

    claim("Emails", EMAIL, "Matches the email format name@domain.tld", sensitive=True)
    claim("URLs", URL, "Starts with http(s):// or www.")
    claim("Amounts", MONEY, "Number with a currency symbol or currency word", re.I)
    claim("Identifiers", r"(?<!\d)\d{4}\s\d{4}\s\d{4}(?!\d)",
          "12 digits in groups of 4 (Aadhaar-like pattern)", sensitive=True, subtype="Aadhaar-like")
    claim("Identifiers", r"\b[A-Z]{5}\d{4}[A-Z]\b",
          "Pattern AAAAA9999A (PAN-like)", sensitive=True, subtype="PAN-like")
    claim("Identifiers", r"(?<!\d)(?:\d{4}[\s\-]){3}\d{4}(?!\d)",
          "16 digits in groups of 4 (card-number-like)", sensitive=True, subtype="Card-like")
    for name, p in DATE_PATTERNS:
        claim("Dates", p, f"Matches date format {name}", re.I)
    for p in PHONE_PATTERNS:
        claim("Phone numbers", p, "Phone-number pattern (10-13 digits)", sensitive=True,
              validate=lambda s: 10 <= len(re.sub(r"\D", "", s)) <= 13)
    # Labelled identifiers, e.g. "Reg No: 240071601054"
    lab = (r"\b((?:Reg(?:ister|istration)?\.?\s*(?:No|Number)|Roll\s*(?:No|Number)|"
           r"Student\s*ID|ID\s*(?:No|Number)|RRN|Certificate\s*(?:No|ID)|"
           r"Invoice\s*(?:No|Number)|Order\s*(?:No|ID)|Ref(?:erence)?\.?\s*(?:No|Number)))"
           r"\.?\s*[:\-#]?\s*([A-Z0-9][A-Z0-9\-/]{3,})")
    for m in re.finditer(lab, t, re.I):
        s, e = m.start(2), m.end(2)
        if _overlaps(taken, s, e):
            continue
        sens = not re.match(r"(?i)invoice|order|ref", m.group(1))
        _add(out, "Identifiers", idx, s, e, f"Value after the label '{m.group(1).strip()}'",
             sens, "Labelled ID")
        taken.append((s, e))
    claim("Identifiers", r"(?<![\w.])\d{9,16}(?![\w.])",
          "Long digit string (ID-like number)", sensitive=True, subtype="Long number")
    # Names: titles and labels only (reliable cases)
    for m in re.finditer(r"\b(?:Dr|Mr|Mrs|Ms|Prof|Shri|Smt)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}", t):
        _add(out, "Names", idx, m.start(), m.end(), "Title (Dr./Mr./Prof. ...) followed by a name")
    for m in re.finditer(r"\b(?:Name|Student Name|Candidate|Customer|Client|Issued by|Authori[sz]ed by|"
                         r"Signed by|Principal|Dean|HOD|Registrar)\s*[:\-]\s*([A-Z][A-Za-z.\' ]{2,40})", t):
        _add(out, "Names", idx, m.start(1), m.end(1), f"Value after the label '{m.group(0).split(':')[0].strip()}'")
    # Organisations: SHORT lines near the top with an organisation word and mostly
    # capitalised words (so ordinary sentences are not mistaken for names).
    for li, ln in enumerate(idx.lines[:12]):
        txt = re.sub(r"^\s*(?:company|organi[sz]ation|institution|issued by|from)\s*[:\-]\s*", "", ln["text"], flags=re.I)
        ws = txt.split()
        caps = sum(1 for w in ws if w[:1].isupper())
        if re.search(rf"\b{ORG_WORDS}\b", txt, re.I) and 1 <= len(ws) <= 7 and caps / max(len(ws), 1) >= 0.5:
            off = ln["text"].find(txt)
            _add(out, "Organisations", idx, ln["start"] + max(off, 0), ln["end"],
                 "Short capitalised line near the top containing an organisation word (Institute, Ltd, ...)")
    for k in out:
        out[k].sort(key=lambda e: e["start"])
    return out


def mask_value(value, mode="full", label="REDACTED"):
    if mode == "full":
        return f"[{label}]"
    keep = 2
    if len(value) <= keep * 2:
        return "*" * len(value)
    return value[:keep] + "*" * (len(value) - keep * 2) + value[-keep:]


def masked_text(idx, ents, mode="full"):
    """Return the document text with sensitive entities masked."""
    items = [e for k in ents.values() for e in k if e["sensitive"]]
    items.sort(key=lambda e: e["start"], reverse=True)
    t = idx.text
    for e in items:
        label = {"Emails": "EMAIL", "Phone numbers": "PHONE"}.get(e["kind"], "ID")
        t = t[:e["start"]] + mask_value(e["value"], mode, label) + t[e["end"]:]
    return t


def guess_header_name(idx):
    """First line = 2-3 capitalised words (e.g. a resume heading). Only used when
    the document is classified Personal. Returns an entity dict or None."""
    if not idx.lines:
        return None
    ln = idx.lines[0]
    if re.fullmatch(r"[A-Z][a-z]+(?: [A-Z][a-z.]+){1,2}", ln["text"].strip()):
        store = {"Names": []}
        _add(store, "Names", idx, ln["start"], ln["end"],
             "Name-like heading on the first line (inferred from position)")
        return store["Names"][0] if store["Names"] else None
    return None
