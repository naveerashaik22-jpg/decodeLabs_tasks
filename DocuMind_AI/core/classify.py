"""Explainable RULE-BASED document classification.

This is weighted keyword scoring. It is NOT a trained machine-learning model
and no accuracy figure is claimed for it."""
import re

# category -> {term: weight}. Heavier weight = more specific to the category.
LEXICON = {
    "Academic": {"university": 2, "college": 2, "institute": 1, "semester": 2, "examination": 2,
                 "exam": 1, "hall ticket": 3, "timetable": 3, "syllabus": 3, "student": 2,
                 "course": 1, "internship": 2, "certificate": 1, "marks": 2,
                 "grade": 1, "cgpa": 3, "department": 1, "faculty": 1, "lecture": 1,
                 "assignment": 2, "project report": 2, "register number": 2, "roll no": 2,
                 "attendance": 2, "curriculum": 2, "professor": 1, "b.tech": 2, "degree": 1,
                 "academic": 2, "campus": 1, "viva": 2, "thesis": 2},
    "Business": {"company": 1, "client": 2, "proposal": 2, "quotation": 3, "purchase order": 3,
                 "order": 1, "vendor": 2, "supplier": 2, "contract": 1, "meeting": 1,
                 "deliverable": 2, "stakeholder": 2, "sales": 1, "revenue": 2, "marketing": 1,
                 "customer": 1, "business": 2, "pvt ltd": 2, "limited": 1, "offer letter": 3,
                 "employee": 2, "agenda": 2, "minutes of": 2, "project": 1},
    "Financial": {"invoice": 3, "receipt": 3, "amount": 2, "total": 2, "payment": 2,
                  "payable": 2, "balance": 2, "bank": 2, "account": 1, "gst": 3, "tax": 2,
                  "bill": 2, "paid": 1, "due": 1, "salary": 2, "credit": 1, "debit": 1,
                  "transaction": 2, "subtotal": 3, "upi": 2, "cheque": 2, "statement": 2,
                  "loan": 2, "interest": 1, "ifsc": 3, "rs": 1, "inr": 1},
    "Legal": {"agreement": 3, "hereby": 1, "clause": 3, "party": 1, "parties": 2,
              "terms and conditions": 3, "liable": 2, "liability": 2, "jurisdiction": 3,
              "court": 2, "affidavit": 3, "notary": 3, "indemnity": 3, "whereas": 3,
              "witness": 2, "legal": 2, "undersigned": 2, "breach": 2, "confidential": 1},
    "Technical": {"software": 2, "algorithm": 3, "api": 3, "server": 2, "database": 2,
                  "code": 1, "function": 1, "install": 2, "configuration": 2, "error": 1,
                  "version": 1, "python": 2, "java": 2, "model": 1, "data": 1, "network": 2,
                  "protocol": 2, "architecture": 2, "module": 1, "interface": 1,
                  "framework": 2, "deploy": 2, "debug": 2, "specification": 2},
    "Notice": {"notice": 4, "circular": 4, "notification": 3, "announcement": 3,
               "all students": 3, "attention": 2, "informed": 2, "hereby informed": 3, "deadline": 2,
               "last date": 3, "due date": 2, "kindly": 2, "scheduled": 1, "holiday": 2,
               "regarding": 1, "instructed": 2, "mandatory": 2, "reminder": 2, "venue": 1},
    "Personal": {"resume": 4, "curriculum vitae": 4, "objective": 2, "skills": 2,
                 "experience": 1, "education": 1, "date of birth": 3, "dob": 3, "father": 2,
                 "mother": 2, "aadhaar": 3, "passport": 3, "hobbies": 3, "languages known": 3,
                 "declaration": 2, "nationality": 3, "marital status": 3, "gender": 2,
                 "blood group": 3, "personal details": 3, "linkedin": 2, "github": 2},
}
MIN_SCORE = 4          # below this total weight the document stays Unclassified


def _term_re(term):
    return re.compile(rf"(?<![a-z]){re.escape(term)}(?:s|es)?(?![a-z])")


_COMPILED = {c: {t: _term_re(t) for t in terms} for c, terms in LEXICON.items()}


def classify_document(text: str, n_amounts: int = 0):
    """Returns dict: label, scores, matched (category -> [(term, weight)]),
    confidence_share, runner_up, unclassified(bool), explanation."""
    low = text.lower()
    header = " ".join(low.split("\n")[:3])
    scores, matched = {}, {}
    for cat, terms in _COMPILED.items():
        hits, total = [], 0.0
        for term, rx in terms.items():
            if rx.search(low):
                w = LEXICON[cat][term]
                if rx.search(header):
                    w += 5 if w >= 3 else 0.5        # strong term in the heading = document type
                hits.append((term, w)); total += w
        scores[cat], matched[cat] = round(total, 1), sorted(hits, key=lambda x: -x[1])
    if n_amounts:
        scores["Financial"] = round(scores["Financial"] + min(n_amounts, 2), 1)
    ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
    (top, top_s), (second, second_s) = ranked[0], ranked[1]
    total = sum(scores.values()) or 1
    unclassified = top_s < MIN_SCORE
    mixed = (not unclassified) and second_s >= 0.75 * top_s
    if unclassified:
        expl = (f"Only {top_s} points of keyword evidence were found; at least {MIN_SCORE} "
                "are needed, so no category is assigned.")
    else:
        expl = (f"'{top}' has the highest keyword score ({top_s} points, "
                f"{round(100 * top_s / total)}% of all evidence).")
        if mixed:
            expl += f" '{second}' is close ({second_s}), so this document mixes both."
    return {"label": "Unclassified" if unclassified else top, "scores": scores,
            "matched": matched, "share": round(100 * top_s / total) if not unclassified else 0,
            "runner_up": second if mixed else None, "unclassified": unclassified,
            "top_score": top_s, "explanation": expl}
