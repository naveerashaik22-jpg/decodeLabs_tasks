"""DocuMind AI - Intelligent Document Understanding, Verification and
Evidence-Based Assistance Platform.

Run:  streamlit run app.py
"""
import hashlib
import io
import json
import os

import pandas as pd
import streamlit as st

from core.extract import masked_text
from core.insights import compare_documents, word_diff_html
from core.ocr import annotate, tesseract_available
from core.pipeline import process_document
from core.qa import answer_question
from ui import theme as T

ROOT = os.path.dirname(os.path.abspath(__file__))
st.set_page_config(page_title="DocuMind AI", page_icon="📄", layout="wide",
                   initial_sidebar_state="expanded")
st.markdown(T.CSS, unsafe_allow_html=True)

SAMPLES = {
    "College notice": "samples/sample_notice.png",
    "Invoice": "samples/sample_invoice.png",
    "Resume": "samples/sample_resume.png",
    "Blurry notice": "samples/sample_notice_degraded.png",
}
PAGES = ["Home", "Document Viewer", "Intelligence", "Assistant",
         "Trust & Privacy", "Insights", "Compare", "Export"]
ss = st.session_state
ss.setdefault("nav", "Home")


def go(page):
    ss["nav"] = page


# ================================================================ sidebar ====
with st.sidebar:
    st.markdown(f'<div class="dm-brand"><div class="dm-logo">{T.icon("logo")}</div>'
                '<div><b>DocuMind AI</b><small>Document intelligence</small></div></div>',
                unsafe_allow_html=True)
    st.radio("Navigation", PAGES, key="nav", label_visibility="collapsed")
    st.markdown("---")
    with st.expander("OCR settings"):
        low_conf = st.slider("Low-confidence threshold", 30, 90, 60,
                             help="Words below this OCR confidence are marked red.")
        psm = st.selectbox("Tesseract layout (--psm)", [6, 3, 4, 11], index=0,
                           help="6 = one uniform text block, the setting used in Project 4.")
        auto_pre = st.checkbox("Auto-select best preprocessing", True)
        auto_orient = st.checkbox("Auto-correct page rotation", True)
    ok = tesseract_available()
    st.markdown(f'<div class="dm-status"><span class="dm-dot {"" if ok else "off"}"></span>'
                f'{"Tesseract OCR ready" if ok else "Tesseract not found"}</div>',
                unsafe_allow_html=True)
    st.markdown('<p class="dm-side-note" style="margin-top:.8rem">Documents are processed by the machine '
                'running this app and are not sent to any third-party service. On a public demo, '
                'avoid uploading real personal documents.</p>', unsafe_allow_html=True)
    if ss.get("doc"):
        st.markdown(f'<p class="dm-side-note">Current document:<br><b style="color:#e6edf7">'
                    f'{T.esc(ss["doc"]["name"])}</b></p>', unsafe_allow_html=True)

page = ss["nav"]


# ================================================================ helpers ====
def read_sample(label):
    path = os.path.join(ROOT, SAMPLES[label] if label in SAMPLES else label)
    with open(path, "rb") as f:
        return f.read()


def run_pipeline(data, name, status_label="Processing document"):
    with st.status(f"{status_label}...", expanded=True) as status:
        try:
            doc = process_document(data, name, psm=psm, auto_select=auto_pre,
                                   auto_orient=auto_orient, low_conf=low_conf,
                                   progress=lambda m: status.update(label=m))
            status.update(label="Document ready", state="complete", expanded=False)
            return doc
        except Exception as e:
            status.update(label="Processing failed", state="error")
            st.error(f"Could not process this file: {e}")
            return None


def need_doc(ic="doc"):
    st.markdown(T.empty_state(ic, "No document yet",
                              "Upload a document or load a sample on the Home page to see results here."),
                unsafe_allow_html=True)
    st.button("Go to Home", on_click=go, args=("Home",))


def page_image(doc, pno, **kw):
    w = doc["words"]
    return annotate(doc["pages"][pno - 1], w[w["page"] == pno], low_conf, **kw)


def page_picker(doc, key):
    n = len(doc["pages"])
    if n <= 1:
        return 1
    return st.segmented_control("Page", list(range(1, n + 1)), default=1, key=key) or 1


def img_bytes(pil):
    b = io.BytesIO(); pil.save(b, format="PNG"); return b.getvalue()


def entity_flat(doc):
    return [e for k in doc["ents"].values() for e in k]


# ================================================================== HOME =====
if page == "Home":
    st.markdown(T.HERO, unsafe_allow_html=True)
    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        up = st.file_uploader("Upload a document", type=["png", "jpg", "jpeg", "pdf"],
                              help="PNG, JPG, JPEG or PDF. Scans and photos work best when they are sharp and upright.")
    with c2:
        st.markdown('<div class="dm-label" style="margin-top:.2rem">Or try a sample (generated test images)</div>',
                    unsafe_allow_html=True)
        sc = st.columns(2)
        for i, label in enumerate(SAMPLES):
            if sc[i % 2].button(label, key=f"s_{label}", width="stretch"):
                ss["source"] = ("sample", label, read_sample(label), label)
    if up is not None and up.file_id != ss.get("last_up"):
        ss["last_up"] = up.file_id
        ss["source"] = ("upload", up.name, up.getvalue(), up.name)

    src = ss.get("source")
    if src:
        _, _, data, name = src
        key = hashlib.md5(data + f"{psm}{auto_pre}{auto_orient}{low_conf}".encode()).hexdigest()
        if ss.get("doc_key") != key:
            if not tesseract_available():
                st.error("Tesseract OCR is not installed or was not found. See the README.")
            else:
                doc = run_pipeline(data, name)
                if doc:
                    ss.update(doc=doc, doc_key=key, qa_hist=[], last_q=None, q_text="")
    doc = ss.get("doc")
    if doc:
        q, cls = doc["quality"], doc["cls"]
        st.markdown(T.stats([
            ("Document", doc["name"][:22], doc["note"]),
            ("Pages", len(doc["pages"]), "OCR'd"),
            ("Words read", q["words"], f"mean confidence {q['mean_conf']}%"),
            ("Category", cls["label"], "rule-based"),
            ("OCR quality", q["label"], f"{q['score']}/100"),
        ]), unsafe_allow_html=True)
        b = st.columns(4)
        b[0].button("Open Assistant", on_click=go, args=("Assistant",), type="primary", width="stretch")
        b[1].button("View OCR result", on_click=go, args=("Document Viewer",), width="stretch")
        b[2].button("See intelligence", on_click=go, args=("Intelligence",), width="stretch")
        b[3].button("Trust and privacy", on_click=go, args=("Trust & Privacy",), width="stretch")
    else:
        st.markdown(T.empty_state("upload", "Drop a document to begin",
                                  "Your first result appears here as soon as the OCR finishes."),
                    unsafe_allow_html=True)

# ============================================================ VIEWER =========
elif page == "Document Viewer":
    st.markdown(T.page_header("eye", "Document Viewer", "OCR result with word-level confidence"),
                unsafe_allow_html=True)
    doc = ss.get("doc")
    if not doc:
        need_doc("eye")
    elif doc["words"].empty:
        st.markdown(T.card("<b>No readable text was detected.</b><div class='dm-muted'>Try a sharper or "
                           "higher-resolution image, or change the layout mode (--psm) in the sidebar.</div>",
                           "accent-bad"), unsafe_allow_html=True)
    else:
        w, q = doc["words"], doc["quality"]
        low = w[w["conf"] < low_conf]
        rot = [r for r in doc["rotations"] if r]
        st.markdown(T.stats([
            ("Pages", len(doc["pages"]), ", ".join(f"rotated {r} deg corrected" for r in rot) if rot else "orientation OK"),
            ("Words", len(w), ""), ("Mean confidence", f"{q['mean_conf']}%", "Tesseract's own estimate"),
            ("Low confidence", len(low), f"below {low_conf}%"),
            ("Preprocessing", doc["best"], "chosen automatically" if auto_pre else "fixed"),
        ]), unsafe_allow_html=True)
        left, right = st.columns([3, 2], gap="large")
        with left:
            pno = page_picker(doc, f"vp_{ss['doc_key']}")
            t1, t2 = st.columns(2)
            show_ok = t1.toggle("Confident words (green)", True)
            show_low = t2.toggle("Low-confidence words (red)", True)
            st.image(page_image(doc, pno, show_normal=show_ok, show_low=show_low),
                     caption=f"Page {pno}. Green = confident, red = below {low_conf}% confidence.",
                     width="stretch")
        with right:
            st.markdown('<div class="dm-label">Extracted text (editable)</div>', unsafe_allow_html=True)
            edited = st.text_area("Extracted text", doc["idx"].text.strip(), height=360,
                                  key=f"edit_{ss['doc_key']}", label_visibility="collapsed")
            st.caption(f"{len(edited.split())} words, {len(edited)} characters. Edits are used for "
                       "exports; analysis always uses the original OCR so evidence stays traceable.")
        with st.expander(f"Low-confidence words ({len(low)})"):
            if len(low):
                st.dataframe(low[["page", "text", "conf"]].rename(
                    columns={"page": "Page", "text": "Word", "conf": "Confidence"}).round(1),
                    hide_index=True, width="stretch")
            else:
                st.write("None. All words are at or above the threshold.")
        with st.expander("Preprocessing comparison (first page)"):
            st.dataframe(doc["comparison"], hide_index=True, width="stretch")
            st.caption("The variant with the most confident words (>= 60%) is used for every page.")
        with st.expander("Page-wise text"):
            for pn in range(1, len(doc["pages"]) + 1):
                txt = " ".join(w[w["page"] == pn]["text"])
                st.markdown(f"**Page {pn}**")
                st.write(txt if txt else "(no text detected)")

# ========================================================= INTELLIGENCE ======
elif page == "Intelligence":
    st.markdown(T.page_header("spark", "Document Intelligence", "What the document is and what it contains"),
                unsafe_allow_html=True)
    doc = ss.get("doc")
    if not doc or doc["words"].empty:
        need_doc("spark")
    else:
        cls, ents = doc["cls"], doc["ents"]
        c1, c2 = st.columns([2, 3], gap="large")
        with c1:
            runner = f' {T.pill("also " + cls["runner_up"], "violet")}' if cls["runner_up"] else ""
            label = cls["label"]
            sub = ("No category has enough evidence." if cls["unclassified"]
                   else f"{cls['share']}% of keyword evidence")
            st.markdown(T.card(
                f'<div class="dm-big">{T.esc(label)}</div>'
                f'<div style="margin:.6rem 0">{T.pill("Rule-based", "cyan")}{T.pill("Not a trained ML model", "warn")}{runner}</div>'
                f'<div class="dm-muted">{T.esc(sub)}<br>{T.esc(cls["explanation"])}</div>',
                "accent-cyan", "Document category"), unsafe_allow_html=True)
        with c2:
            top = max(cls["scores"].values()) or 1
            rows = "".join(T.bar(k, v, top) for k, v in sorted(cls["scores"].items(), key=lambda x: -x[1]))
            st.markdown(T.card(rows, "", "Keyword evidence per category (points)"), unsafe_allow_html=True)
        if not cls["unclassified"]:
            hits = cls["matched"][cls["label"]]
            st.markdown(T.card("".join(T.chip(f"{t}  +{w:g}") for t, w in hits[:14]) or "-", "",
                               f"Keywords behind the '{cls['label']}' decision"), unsafe_allow_html=True)
        st.markdown("#### Extracted information")
        kinds = list(ents)
        for row in (kinds[:4], kinds[4:]):
            cols = st.columns(4)
            for col, kind in zip(cols, row):
                items = ents[kind]
                body = "".join(
                    f'<div style="margin-bottom:.5rem"><div class="dm-text">{T.esc(e["value"])}</div>'
                    f'<div class="dm-muted" style="font-size:.76rem">page {e["page"]} · OCR {e["conf"]}%'
                    f'{" · sensitive" if e["sensitive"] else ""}</div></div>' for e in items[:6]
                ) or '<div class="dm-muted"><i>none found</i></div>'
                if len(items) > 6:
                    body += f'<div class="dm-muted">+ {len(items) - 6} more</div>'
                col.markdown(T.card(body, "accent-cyan" if items else "", f"{kind} ({len(items)})"),
                             unsafe_allow_html=True)
        st.markdown(T.card("".join(T.chip(k) for k in doc["keywords"]), "", "Important keywords"),
                    unsafe_allow_html=True)
        st.markdown("#### Evidence Explorer")
        st.caption("Pick any extracted fact to see why it was detected and where it is on the page.")
        facts = entity_flat(doc)
        if facts:
            opts = {f"{e['kind'][:-1] if e['kind'].endswith('s') else e['kind']}: {e['value']}  (page {e['page']})": e for e in facts}
            pick = st.selectbox("Extracted fact", list(opts), label_visibility="collapsed")
            e = opts[pick]
            a, b = st.columns([2, 3], gap="large")
            with a:
                st.markdown(T.card(
                    f'<div class="dm-med">{T.esc(e["value"])}</div>'
                    f'<div class="dm-muted" style="margin:.5rem 0">Why detected: {T.esc(e["why"])}</div>'
                    f'<div class="dm-label">Source text</div><div class="dm-quote">{T.esc(e["line"])}</div>'
                    f'<div style="margin-top:.5rem">{T.pill(f"OCR confidence {e["conf"]}%", "good" if e["conf"] >= low_conf else "bad")}'
                    f'{T.pill(f"page {e["page"]}")}</div>', "accent-cyan", "Fact detail"), unsafe_allow_html=True)
            with b:
                line_ids = next((l["ids"] for l in doc["idx"].lines if set(e["ids"]) & set(l["ids"])), [])
                st.image(page_image(doc, e["page"], answer_ids=e["ids"], support_ids=line_ids, show_normal=False),
                         caption="Orange = the fact, cyan = the line it was found in", width="stretch")
        else:
            st.info("No facts were extracted from this document.")

# ============================================================ ASSISTANT ======
elif page == "Assistant":
    st.markdown(T.page_header("chat", "Evidence-Based Assistant",
                              "Answers come only from the document, with the source highlighted"),
                unsafe_allow_html=True)
    doc = ss.get("doc")
    if not doc or doc["words"].empty:
        need_doc("chat")
    else:
        st.caption("This is rule-based retrieval over your OCR text, not a language model. It answers "
                   "only when the document contains supporting text.")
        examples = ["What is the last date?", "What is the examination date?", "Who issued this notice?",
                    "What is the email address?", "What is the total amount?",
                    "Summarise this document", "What are the important instructions?"]
        ec = st.columns(4)
        for i, ex in enumerate(examples):
            ec[i % 4].button(ex, key=f"ex{i}", width="stretch",
                             on_click=lambda t=ex: ss.update(q_text=t))
        q = st.text_input("Ask your document", key="q_text",
                          placeholder="Type a question and press Enter", label_visibility="collapsed")
        if q.strip():
            res = answer_question(q, doc["idx"], doc["ents"], doc["cls"], low_conf)
            if ss.get("last_q") != q:
                ss["last_q"] = q
                ss["qa_hist"].insert(0, {"q": q, "found": res["found"], "a": res["answer"][:90]})
            if res["found"]:
                a, b = st.columns([5, 6], gap="large")
                with a:
                    ans = T.esc(res["answer"]).replace("\n", "<br>")
                    sup = "".join(f'<div class="dm-quote">{T.esc(s["text"])}'
                                  f' <span class="dm-muted">(page {s["page"]})</span></div>' for s in res["support"])
                    conf_kind = {"High": "good", "Medium": "warn"}.get(res["confidence"], "")
                    body = (f'<div class="dm-med" style="margin-bottom:.5rem">{ans}</div>'
                            f'<div>{T.pill("Evidence found", "good")}{T.pill(res["confidence"] + " confidence", conf_kind)}'
                            f'{T.pill(res["intent"] or "general", "violet")}</div>'
                            f'<div class="dm-label" style="margin-top:.7rem">Supporting text from the document</div>{sup}'
                            f'<div class="dm-muted" style="margin-top:.5rem">How: {T.esc(res["method"])}</div>')
                    if res["note"]:
                        body += f'<div class="dm-muted" style="margin-top:.4rem;color:#fcd34d">{T.esc(res["note"])}</div>'
                    if res["others"]:
                        body += (f'<div class="dm-muted" style="margin-top:.4rem">Also found: '
                                 f'{T.esc(", ".join(res["others"]))}</div>')
                    st.markdown(T.card(body, "accent-good", "Answer"), unsafe_allow_html=True)
                    if res.get("matches"):
                        st.dataframe(pd.DataFrame(res["matches"]), hide_index=True, width="stretch")
                with b:
                    first = res["support"][0]["page"] if res["support"] else 1
                    st.image(page_image(doc, first, support_ids=res["support_ids"],
                                        answer_ids=res["answer_ids"], show_normal=False, show_low=False),
                             caption="Orange = answer words, cyan = supporting text", width="stretch")
            else:
                st.markdown(T.card(
                    '<div class="dm-med">Insufficient evidence</div>'
                    f'<div class="dm-muted" style="margin-top:.4rem">The document does not contain enough '
                    f'information to answer: "{T.esc(q)}".</div>'
                    f'<div class="dm-muted" style="margin-top:.4rem">{T.esc(res["note"])}</div>',
                    "accent-bad", "No answer"), unsafe_allow_html=True)
        if len(ss["qa_hist"]) > 1:
            with st.expander("Question history (this session)"):
                for h in ss["qa_hist"]:
                    st.markdown(f'{T.pill("found" if h["found"] else "no evidence", "good" if h["found"] else "bad")} '
                                f'{T.esc(h["q"])}', unsafe_allow_html=True)

# ======================================================== TRUST & PRIVACY ====
elif page == "Trust & Privacy":
    st.markdown(T.page_header("shield", "Trust & Privacy", "How reliable the reading is, and what is sensitive"),
                unsafe_allow_html=True)
    doc = ss.get("doc")
    if not doc or doc["words"].empty:
        need_doc("shield")
    else:
        q, comp = doc["quality"], doc["completeness"]
        st.markdown("#### Document health report")
        a, b, c = st.columns([1.1, 1.6, 1.6], gap="large")
        with a:
            st.markdown(T.card(T.ring(q["score"], q["label"]) +
                               '<div class="dm-muted" style="text-align:center;margin-top:.5rem">OCR quality indicator</div>',
                               "", "Quality"), unsafe_allow_html=True)
        with b:
            st.markdown(T.card(
                T.bar("Mean word confidence", q["mean_conf"], 100, "%") +
                T.bar(f"Words at or above {low_conf}%", q["confident_pct"], 100, "%") +
                T.bar("Noise-like tokens", q["noise_pct"], 100, "%") +
                '<div class="dm-muted" style="font-size:.78rem">Score = 50% mean confidence + 30% share of confident '
                'words + 20% (100 - noise). OCR confidence is Tesseract\'s estimate, not a guarantee of correctness.</div>',
                "", "Measured OCR signals"), unsafe_allow_html=True)
        with c:
            if comp:
                body = (f'<div class="dm-med">{comp["pct"]}% of expected fields found</div>' +
                        "".join(T.pill(p, "good") for p in comp["present"]) +
                        "".join(T.pill("missing: " + m, "bad") for m in comp["missing"]) +
                        f'<div class="dm-muted" style="margin-top:.4rem">Expected for a {T.esc(comp["category"])} document.</div>')
            else:
                body = '<div class="dm-muted">No expected-field checklist for this category.</div>'
            st.markdown(T.card(body, "accent-warn" if comp and comp["missing"] else "", "Missing-information check"),
                        unsafe_allow_html=True)
        unc = doc["uncertainties"]
        if unc:
            st.markdown(T.card("".join(f'<div class="dm-text" style="margin-bottom:.3rem">• {T.esc(u)}</div>'
                                       for u in unc[:8]), "accent-warn", "Extraction warnings"),
                        unsafe_allow_html=True)
        else:
            st.markdown(T.card('<div class="dm-text">No extraction warnings. All extracted facts were read with '
                               'confidence above the threshold.</div>', "accent-good", "Extraction warnings"),
                        unsafe_allow_html=True)

        st.markdown("#### Privacy shield")
        sens = [e for e in entity_flat(doc) if e["sensitive"]]
        st.caption("Detection uses patterns (emails, phone numbers, ID-like numbers). It can miss unusual formats. "
                   "Processing happens inside this app; nothing is sent to external services.")
        if not sens:
            st.markdown(T.card('<div class="dm-text">No sensitive patterns were detected.</div>', "accent-good",
                               "Sensitive data"), unsafe_allow_html=True)
        else:
            mode_label = st.radio("Mask style", ["Full redaction", "Partial mask"], horizontal=True)
            mode = "full" if mode_label == "Full redaction" else "partial"
            reveal = st.toggle("Show original values", False)
            from core.extract import mask_value
            rows = [{"Type": e["subtype"] or e["kind"], "Value": e["value"] if reveal else
                     mask_value(e["value"], "partial"), "Page": e["page"], "Why flagged": e["why"]} for e in sens]
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
            tx, im = st.columns(2, gap="large")
            m_text = masked_text(doc["idx"], doc["ents"], mode)
            with tx:
                st.markdown('<div class="dm-label">Masked text preview</div>', unsafe_allow_html=True)
                st.text_area("Masked text", m_text.strip(), height=240, label_visibility="collapsed")
                st.download_button("Download masked TXT", m_text, "documind_masked.txt", "text/plain")
            with im:
                pno = page_picker(doc, f"pp_{ss['doc_key']}")
                rid = [i for e in sens for i in e["ids"]]
                fill = st.toggle("Black-out boxes in the image", True)
                pimg = page_image(doc, pno, redact_ids=rid, fill_redact=fill, show_normal=False, show_low=False)
                st.image(pimg, caption="Sensitive words " + ("blacked out" if fill else "outlined in purple"),
                         width="stretch")
                st.download_button("Download masked image (PNG)", img_bytes(pimg), "documind_masked.png", "image/png")

# ============================================================== INSIGHTS =====
elif page == "Insights":
    st.markdown(T.page_header("clock", "Insights", "Summary, recommendations and timeline built from the document"),
                unsafe_allow_html=True)
    doc = ss.get("doc")
    if not doc or doc["words"].empty:
        need_doc("clock")
    else:
        sm = answer_question("Summarise this document", doc["idx"], doc["ents"], doc["cls"], low_conf)
        c1, c2 = st.columns([3, 2], gap="large")
        with c1:
            if sm["found"]:
                body = "".join(f'<div class="dm-quote">{T.esc(s["text"])}</div>' for s in sm["support"])
                st.markdown(T.card(body + f'<div class="dm-muted" style="margin-top:.5rem">{T.esc(sm["note"])}</div>',
                                   "accent-cyan", "Smart summary (extractive)"), unsafe_allow_html=True)
            st.markdown("#### Recommendations")
            if not doc["recs"]:
                st.info("No recommendations for this document.")
            for title, why, evidence, _ids in doc["recs"]:
                ev = f'<div class="dm-quote">{T.esc(evidence)}</div>' if evidence else ""
                st.markdown(T.card(f'<div class="dm-med" style="font-size:1.05rem">{T.esc(title)}</div>'
                                   f'<div class="dm-muted" style="margin-top:.3rem"><b>Why:</b> {T.esc(why)}</div>{ev}',
                                   "accent-cyan"), unsafe_allow_html=True)
        with c2:
            st.markdown("#### Timeline")
            if not doc["timeline"]:
                st.markdown(T.card('<div class="dm-muted">No dates were detected in this document.</div>'),
                            unsafe_allow_html=True)
            else:
                items = "".join(f'<div class="it"><div class="d">{T.esc(t["date"])}</div>'
                                f'<div class="e">{T.esc(t["event"])}</div></div>' for t in doc["timeline"])
                st.markdown(T.card(f'<div class="dm-tl">{items}</div>'), unsafe_allow_html=True)
                st.caption("Dates are shown in chronological order. Two-digit and numeric dates are read as day/month/year.")

# =============================================================== COMPARE =====
elif page == "Compare":
    st.markdown(T.page_header("columns", "Compare Documents", "Find what changed between two versions"),
                unsafe_allow_html=True)
    doc = ss.get("doc")
    if not doc:
        need_doc("columns")
    else:
        c1, c2 = st.columns(2, gap="large")
        c1.markdown(T.card(f'<div class="dm-med">{T.esc(doc["name"])}</div>', "accent-cyan",
                           "Document A (current)"), unsafe_allow_html=True)
        with c2:
            upb = st.file_uploader("Document B", type=["png", "jpg", "jpeg", "pdf"], key="up_b")
            use_rev = st.button("Use revised notice sample as Document B")
        if use_rev:
            ss["src_b"] = ("samples/sample_notice_revised.png", "Revised notice (sample)")
        if upb is not None and upb.file_id != ss.get("last_up_b"):
            ss["last_up_b"] = upb.file_id
            ss["src_b"] = (None, upb.name, upb.getvalue())
        sb = ss.get("src_b")
        if sb:
            data_b = read_sample(sb[0]) if sb[0] else sb[2]
            name_b = sb[1]
            kb = hashlib.md5(data_b).hexdigest()
            if ss.get("doc_b_key") != kb:
                d = run_pipeline(data_b, name_b, "Processing document B")
                if d:
                    ss["doc_b"], ss["doc_b_key"] = d, kb
            docb = ss.get("doc_b")
            if docb:
                cmp = compare_documents([l["text"] for l in doc["idx"].lines],
                                        [l["text"] for l in docb["idx"].lines], doc["ents"], docb["ents"])
                st.markdown(T.stats([("Text similarity", f"{cmp['similarity']}%", "line-level"),
                                     ("Changed lines", len(cmp["changed"]), ""),
                                     ("Only in A", len(cmp["removed"]), ""), ("Only in B", len(cmp["added"]), ""),
                                     ("Unchanged", len(cmp["common"]), "")]), unsafe_allow_html=True)
                if cmp["changed"]:
                    body = ""
                    for a, b in cmp["changed"]:
                        ha, hb = word_diff_html(a, b)
                        body += (f'<div class="dm-text" style="margin-bottom:.7rem"><div class="dm-muted">A</div>{ha}'
                                 f'<div class="dm-muted" style="margin-top:.3rem">B</div>{hb}</div>')
                    st.markdown(T.card(body, "accent-warn", "Changed lines"), unsafe_allow_html=True)
                rows = []
                for kind, f in cmp["facts"].items():
                    for v in f["only_a"]:
                        rows.append({"Fact type": kind, "Status": "Only in A", "Value": v})
                    for v in f["only_b"]:
                        rows.append({"Fact type": kind, "Status": "Only in B", "Value": v})
                    for v in f["both"]:
                        rows.append({"Fact type": kind, "Status": "Same in both", "Value": v})
                if rows:
                    st.markdown("#### Facts compared")
                    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
                if cmp["added"] or cmp["removed"]:
                    with st.expander("Lines present in only one document"):
                        for l in cmp["removed"]:
                            st.markdown(T.pill("only in A", "bad") + T.esc(l), unsafe_allow_html=True)
                        for l in cmp["added"]:
                            st.markdown(T.pill("only in B", "good") + T.esc(l), unsafe_allow_html=True)
        else:
            st.markdown(T.empty_state("columns", "Add a second document",
                                      "Upload Document B or use the revised notice sample to compare."),
                        unsafe_allow_html=True)

# ================================================================ EXPORT =====
elif page == "Export":
    st.markdown(T.page_header("download", "Export Centre", "Download your results"), unsafe_allow_html=True)
    doc = ss.get("doc")
    if not doc or doc["words"].empty:
        need_doc("download")
    else:
        edited = ss.get(f"edit_{ss['doc_key']}", doc["idx"].text.strip())
        ents = {k: [{x: e[x] for x in ("value", "page", "conf", "why", "sensitive")} for e in v]
                for k, v in doc["ents"].items()}
        report = {"file": doc["name"], "pages": len(doc["pages"]),
                  "classification": {"method": "rule-based keyword scoring (not trained ML)",
                                     "label": doc["cls"]["label"], "scores": doc["cls"]["scores"],
                                     "explanation": doc["cls"]["explanation"]},
                  "ocr_quality": doc["quality"], "entities": ents, "keywords": doc["keywords"],
                  "warnings": doc["uncertainties"], "text": edited}
        c = st.columns(3, gap="large")
        with c[0]:
            st.markdown(T.card('<div class="dm-text">The extracted text, including any edits you made in the viewer.</div>',
                               "", "Extracted text (TXT)"), unsafe_allow_html=True)
            st.download_button("Download TXT", edited, "documind_text.txt", "text/plain", width="stretch")
        with c[1]:
            st.markdown(T.card('<div class="dm-text">Classification, entities, keywords, quality and warnings.</div>',
                               "", "Results (JSON)"), unsafe_allow_html=True)
            st.download_button("Download JSON", json.dumps(report, indent=2, ensure_ascii=False),
                               "documind_results.json", "application/json", width="stretch")
        with c[2]:
            st.markdown(T.card('<div class="dm-text">The text with emails, phone numbers and IDs redacted.</div>',
                               "", "Masked text (TXT)"), unsafe_allow_html=True)
            st.download_button("Download masked TXT", masked_text(doc["idx"], doc["ents"], "full"),
                               "documind_masked.txt", "text/plain", width="stretch")
