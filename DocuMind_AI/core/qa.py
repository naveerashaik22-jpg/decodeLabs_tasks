"""Evidence-based document assistant.

No language model is used. A question is (1) mapped to an intent by rules,
(2) answered from extracted entities or by retrieving the best-matching OCR
lines (idf-weighted term matching with a small synonym list). An answer is
returned ONLY when supporting text exists in the document; the answer words and
supporting words are returned as OCR word ids so the UI can highlight them."""
import math
import re

STOP = set("""a an the is are was were be been of on in at to for from by with and or but not
this that these those it its as what which who whom whose when where why how do does did can
could should would will shall may might me my you your tell give show find please about
document there their they them we our us i has have had any all if then than so such""".split())

SYN = {"exam": ["examination", "test"], "examination": ["exam"], "date": ["day", "dated"],
       "fee": ["amount", "payment", "charges"], "amount": ["fee", "total", "payment"],
       "submit": ["submission", "submitted"], "submission": ["submit"],
       "contact": ["phone", "email", "mail", "call"], "venue": ["location", "place", "hall"],
       "time": ["timing", "schedule"], "schedule": ["time", "timetable"],
       "teacher": ["faculty", "professor"], "company": ["organisation", "organization"]}

CUES = {
    "deadline": r"last date|deadline|due date|due on|due by|on or before|submit|submission|no later than|before|closing|expires?|by\b",
    "exam": r"exam|examination|test|viva|hall ticket|practical|assessment",
    "issue": r"issued|dated|date of issue|generated",
    "total": r"grand total|total|amount payable|net payable|balance due|amount due|payable|net amount",
    "instr": r"\bmust\b|\bshould\b|\bshall\b|required|mandatory|kindly|please|submit|bring|carry|ensure|do not|don't|not allowed|need to|has to|will be (?:held|issued|available)|contact|report to|last date|deadline",
}


def stem(w):
    for suf in ("ing", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)]
    return w


def tokens(text):
    return [stem(w) for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP and len(w) > 1]


def _expand(toks):
    out = set(toks)
    for t in list(toks):
        for k, vs in SYN.items():
            if stem(k) == t:
                out.update(stem(v) for v in vs)
    return out


def _fact(ent):
    return {"text": ent["value"], "ids": ent["ids"], "conf": ent["conf"], "page": ent["page"]}


def _result(found, intent="", answer="", support=None, answer_ids=None, method="",
            confidence="", note="", others=None):
    support = support or []
    sup_ids = [i for s in support for i in s["ids"]]
    return {"found": found, "intent": intent, "answer": answer, "support": support,
            "answer_ids": answer_ids or [], "support_ids": sup_ids, "method": method,
            "confidence": confidence, "note": note, "others": others or []}


def _line_obj(idx, pos):
    ln = idx.lines[idx.line_index_at(pos)]
    return {"text": ln["text"], "ids": ln["ids"], "page": ln["page"]}


def _warn_low(res, idx, low_conf=60):
    """Add an OCR-uncertainty warning when the answer words were read with low confidence."""
    if res["found"] and res["answer_ids"]:
        c = idx.mean_conf(res["answer_ids"])
        if c < low_conf:
            res["note"] = (res["note"] + " " if res["note"] else "") + \
                f"OCR confidence for these words is only {c}%. Please verify against the image."
    return res


# ---------------------------------------------------------------- intents ----
def detect_intent(q):
    ql = q.lower()
    rules = [
        ("summary", r"summar|overview|gist|in brief|what is (?:this|the) (?:document|notice|letter)|what.*(?:document|notice) (?:is )?about|tell me about"),
        ("instructions", r"instruction|guideline|\brules?\b|what (?:should|must|do) i\b|what (?:needs|has) to|requirements?|to[- ]do|important points|action"),
        ("email", r"e-?mail|mail id"),
        ("phone", r"phone|mobile|contact number|telephone|whatsapp|call\b"),
        ("url", r"website|web ?site|\burl\b|\blink\b"),
        ("issuer", r"who (?:issued|sent|wrote|signed|published|released|is the sender)|issued by|issuer|sender|which (?:company|institution|institute|college|university|organi[sz]ation)|from whom"),
        ("money", r"total|amount|price|cost|\bfees?\b|payable|balance|how much|invoice value|subtotal|\brs\b|rupees"),
        ("deadline", r"last date|deadline|due date|submit(?:ted)? (?:by|before)|closing date|submission date|by when"),
        ("exam", r"\bexam|examination|\btest\b|\bviva\b"),
        ("date", r"\bwhen\b|\bdate\b|\bday\b|scheduled|held on|what time"),
        ("name", r"\bname\b|who is|whose|which person"),
    ]
    for name, rx in rules:
        if re.search(rx, ql):
            return name
    return "general"


# ----------------------------------------------------------- fact answers ----
def _dates_with_cue(idx, ents, cue_rx):
    """Dates whose own line (or the line before) contains the cue."""
    out = []
    for e in ents["Dates"]:
        li = idx.line_index_at(e["start"])
        ctx = idx.lines[li]["text"]
        prev = idx.lines[li - 1]["text"] if li > 0 else ""
        if re.search(cue_rx, ctx, re.I):
            out.append((2, e))
        elif re.search(cue_rx, prev, re.I) and not re.search(r"[.?!]\s*$", prev) \
                and not re.search(CUES["deadline"] if cue_rx != CUES["deadline"] else CUES["exam"], ctx, re.I):
            # The cue is on the previous line AND that sentence is unfinished, so
            # the date on this line belongs to it. A finished sentence does not count.
            out.append((1, e))
    out.sort(key=lambda x: -x[0])
    return [e for _, e in out]


def _answer_entities(kind, label, intent, ents, idx, q):
    items = ents[kind]
    if not items:
        return None
    q_t = _expand(tokens(q))
    def rel(e):
        return len(q_t & set(tokens(e["line"])))
    items = sorted(items, key=lambda e: (-rel(e), e["start"]))
    best = items[0]
    res = _result(True, intent, best["value"], [_line_obj(idx, best["start"])], best["ids"],
                  f"Found by pattern matching ({best['why'].lower()}).", "High")
    res["others"] = [e["value"] for e in items[1:6]]
    return res


def _answer_money(ents, idx, q):
    amts = ents["Amounts"]
    if not amts:
        return None
    scored = []
    for e in amts:
        li = idx.line_index_at(e["start"])
        ctx = idx.lines[li]["text"]
        s = 0
        if re.search(r"grand total|amount payable|net payable|balance due|amount due|net amount", ctx, re.I):
            s = 4
        elif re.search(r"\btotal\b|payable|due", ctx, re.I):
            s = 3
        elif re.search(r"subtotal|amount|fee|price|cost", ctx, re.I):
            s = 1
        s += len(_expand(tokens(q)) & set(tokens(ctx))) * 0.5
        scored.append((s, e))
    scored.sort(key=lambda x: (-x[0], x[1]["start"]))
    s, best = scored[0]
    conf = "High" if s >= 3 else "Medium"
    res = _result(True, "money", best["value"], [_line_obj(idx, best["start"])], best["ids"],
                  "Currency amount ranked by wording on its line (total / payable / due).", conf)
    res["others"] = [e["value"] for _, e in scored[1:5]]
    return res


def _answer_date(intent, ents, idx, q):
    dates = ents["Dates"]
    if not dates:
        return None
    if intent == "deadline":
        c = _dates_with_cue(idx, ents, CUES["deadline"])
        why = "Date on a line containing deadline wording (last date, submit, due ...)."
    elif intent == "exam":
        c = _dates_with_cue(idx, ents, CUES["exam"])
        why = "Date on a line mentioning an exam / test."
    else:
        # Generic date words (date, when, day ...) do not make a line relevant.
        generic = {"date", "day", "time", "held", "schedul", "dated"}
        q_t = _expand([t for t in tokens(q) if t not in generic])
        if q_t:                      # question names a specific topic: it must match
            c = [e for e in dates if q_t & set(tokens(e["line"]))]
            c.sort(key=lambda e: (-len(q_t & set(tokens(e["line"]))), e["start"]))
            why = "Date on a line that matches the topic of your question."
        elif len(dates) == 1:
            c, why = dates, "The only date found in the document."
        else:
            c, why = [], ""
    if not c:
        return None
    best = c[0]
    res = _result(True, intent, best["value"], [_line_obj(idx, best["start"])], best["ids"],
                  why, "High" if intent in ("deadline", "exam") else "Medium")
    res["others"] = [e["value"] for e in c[1:5]]
    return res


def _answer_issuer(ents, idx):
    # 1. explicit labels near the end or start of a line
    for ln in idx.lines:
        m = re.match(r"(?i)\s*(issued by|from|sender|authori[sz]ed by|signed by|regards|sincerely|yours (?:faithfully|sincerely))\s*[:\-]?\s*(.*)$", ln["text"])
        if m and m.group(2).strip():
            return _result(True, "issuer", m.group(2).strip(), [ln], ln["ids"],
                           f"Text after the label '{m.group(1)}'.", "High")
    named = [e for e in ents["Names"] if "Issued by" in e["why"] or "Authori" in e["why"] or "Signed" in e["why"]]
    if named:
        e = named[0]
        return _result(True, "issuer", e["value"], [_line_obj(idx, e["start"])], e["ids"],
                       e["why"] + ".", "High")
    if ents["Organisations"]:
        e = ents["Organisations"][0]
        return _result(True, "issuer", e["value"], [_line_obj(idx, e["start"])], e["ids"],
                       "Organisation name at the top of the document (inferred from position).",
                       "Medium", "No explicit 'issued by' label was found, so this is the most "
                       "likely issuer based on the letterhead position.")
    return None


def _answer_name(ents, idx, q):
    if not ents["Names"]:
        return None
    topic = set(tokens(q)) - {"name", "person", "peopl", "mention"}
    if topic:                        # e.g. "who is the principal" needs a Principal label
        rel = [n for n in ents["Names"] if topic & set(tokens(n["line"] + " " + n["why"]))]
        if not rel:
            return None
        ents = {**ents, "Names": rel}
    e = ents["Names"][0]
    res = _result(True, "name", e["value"], [_line_obj(idx, e["start"])], e["ids"],
                  e["why"] + ".", "Medium")
    res["others"] = [n["value"] for n in ents["Names"][1:5]]
    return res


# ---------------------------------------------------- summary / instructions --
def summarise(idx, ents, cls=None, max_lines=4):
    lines = [l for l in idx.lines if len(l["text"].split()) >= 3]
    if not lines:
        return None
    tf = {}
    for l in lines:
        for t in set(tokens(l["text"])):
            tf[t] = tf.get(t, 0) + 1
    ent_ids = {i for k in ("Dates", "Amounts", "Emails", "Phone numbers") for e in ents[k] for i in e["ids"]}
    scored = []
    n = len(idx.lines)
    for pos, l in enumerate(idx.lines):
        if len(l["text"].split()) < 3:
            continue
        toks = tokens(l["text"])
        s = sum(tf.get(t, 0) for t in toks) / math.sqrt(max(len(toks), 1))
        if ent_ids & set(l["ids"]):
            s += 1.5
        if re.search(CUES["instr"], l["text"], re.I):
            s += 1.0
        if pos < max(2, n // 4):
            s += 0.8
        scored.append((s, pos, l))
    pick = sorted(sorted(scored, key=lambda x: -x[0])[:max_lines], key=lambda x: x[1])
    return [p[2] for p in pick]


def _answer_summary(ents, idx, cls):
    chosen = summarise(idx, ents, cls)
    if not chosen:
        return None
    answer = " ".join(l["text"] for l in chosen)
    res = _result(True, "summary", answer, chosen, [], "Extractive summary: the most informative "
                  "lines, chosen by keyword frequency, key facts and position. Nothing is generated.",
                  "Medium", "This summary only reuses lines from the document.")
    return res


def _answer_instructions(idx):
    chosen = []
    for pos, l in enumerate(idx.lines):
        if pos == 0:
            continue
        if re.search(CUES["instr"], l["text"], re.I) and len(l["text"].split()) >= 4:
            chosen.append(l)
    if not chosen:
        return None
    chosen = chosen[:6]
    return _result(True, "instructions", "\n".join("- " + l["text"] for l in chosen), chosen, [],
                   "Lines containing obligation or action wording (must, should, kindly, submit, "
                   "contact, last date ...).", "Medium")


# -------------------------------------------------------- general retrieval ---
def _retrieve(q, idx):
    q_toks = tokens(q)
    if not q_toks:
        return None
    q_set = set(q_toks)
    q_exp = _expand(q_toks)
    lines = [l for l in idx.lines if l["text"].strip()]
    docs = [set(tokens(l["text"])) for l in lines]
    N = len(lines)
    df = {}
    for d in docs:
        for t in d:
            df[t] = df.get(t, 0) + 1
    idf = lambda t: math.log((N + 1) / (df.get(t, 0) + 0.5)) + 1
    denom = sum(idf(t) for t in q_set) or 1
    scored = []
    for l, d in zip(lines, docs):
        hit = {t for t in q_set if t in d}
        syn_hit = {t for t in q_exp - q_set if t in d}
        score = (sum(idf(t) for t in hit) + 0.6 * min(len(syn_hit), 1) * 1.0) / denom
        if hit or syn_hit:
            scored.append((score, l, hit | syn_hit))
    scored.sort(key=lambda x: -x[0])
    if not scored:
        return None
    top = scored[0]
    # Require substantial coverage of the question's meaningful words.
    if top[0] < 0.5 or not any(len(t) >= 4 for t in top[2]):
        return None
    chosen = [top] + [s for s in scored[1:3] if s[0] >= 0.85 * top[0] and s[0] >= 0.5]
    support = [c[1] for c in chosen]
    res = _result(True, "general", chosen[0][1]["text"], support, [],
                  "Best-matching document line(s) by weighted keyword overlap.",
                  "High" if top[0] >= 0.8 else "Medium")
    res["matches"] = [{"Line": c[1]["text"], "Match score": round(min(c[0], 1.0), 2),
                       "Matched words": ", ".join(sorted(c[2]))} for c in chosen]
    return res


def answer_question(question, idx, ents, cls=None, low_conf=60):
    """Main entry. Returns a result dict (see _result)."""
    q = question.strip()
    if not q or not idx.lines:
        return _result(False, "", note="Ask a question about the uploaded document.")
    intent = detect_intent(q)
    res = None
    if intent == "summary":
        res = _answer_summary(ents, idx, cls)
    elif intent == "instructions":
        res = _answer_instructions(idx)
    elif intent == "email":
        res = _answer_entities("Emails", "email", "email", ents, idx, q)
    elif intent == "phone":
        res = _answer_entities("Phone numbers", "phone", "phone", ents, idx, q)
    elif intent == "url":
        res = _answer_entities("URLs", "URL", "url", ents, idx, q)
    elif intent == "issuer":
        res = _answer_issuer(ents, idx)
    elif intent == "money":
        res = _answer_money(ents, idx, q)
    elif intent in ("deadline", "exam", "date"):
        res = _answer_date(intent, ents, idx, q)
    elif intent == "name":
        res = _answer_name(ents, idx, q)
    # Generic retrieval is only for open questions, never for fact-type questions
    # (dates, amounts, contacts, names ...) where a loose line match would mislead.
    if res is None and intent == "general":
        res = _retrieve(q, idx)
    # Date questions: the date itself may be unreadable (OCR misread it). If a line
    # with the right wording and digits exists, show it as LOW-confidence evidence.
    if res is None and intent in ("exam", "deadline"):
        rx = CUES["exam"] if intent == "exam" else r"last date|deadline|due date"
        for ln in idx.lines:
            if re.search(rx, ln["text"], re.I) and re.search(r"\d", ln["text"]) and \
                    set(tokens(q)) & set(tokens(ln["text"])):
                res = _result(True, intent, ln["text"], [ln], [], "A line with the right wording was found, "
                              "but no valid date could be extracted from it.", "Low",
                              "The date in this line may have been misread by OCR. Check the image.")
                break
    if res is None:
        r = _result(False, intent)
        r["note"] = "The document does not contain enough information to answer this."
        if intent in ("deadline",) and ents["Dates"]:
            r["note"] += (" Dates were found, but none appears next to deadline wording: "
                          + ", ".join(e["value"] for e in ents["Dates"][:4]) + ".")
        return r
    return _warn_low(res, idx, low_conf)
