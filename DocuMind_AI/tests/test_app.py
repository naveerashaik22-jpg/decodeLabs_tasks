"""Drives the real Streamlit app (no browser) through the demo journey."""
import os, sys
from streamlit.testing.v1 import AppTest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
at = AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=180).run()
assert not at.exception, at.exception
next(b for b in at.button if b.label == "College notice").click().run()
assert not at.exception, at.exception
assert "doc" in at.session_state, "document was not processed"
print("PASS | sample document processed:", at.session_state["doc"]["cls"]["label"])
for page in ["Document Viewer", "Intelligence", "Assistant", "Trust & Privacy", "Insights", "Compare", "Export"]:
    at.session_state["nav"] = page
    at.run()
    assert not at.exception, (page, at.exception)
    print("PASS | page renders without error:", page)
at.session_state["nav"] = "Assistant"; at.run()
at.text_input(key="q_text").set_value("What is the email address?").run()
assert not at.exception, at.exception
print("PASS | assistant answered:", at.session_state["qa_hist"][0])
