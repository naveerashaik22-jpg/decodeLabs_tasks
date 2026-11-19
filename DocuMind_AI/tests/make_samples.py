"""Generates SAMPLE test images (synthetic, rendered from text) into samples/."""
from PIL import Image, ImageDraw, ImageFont
import os
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
if not os.path.exists(F):
    F = "arial.ttf"   # Windows
def make(name, lines):
    font = ImageFont.truetype(F, 30)
    img = Image.new("RGB", (1200, 120 + 52 * len(lines)), "white")
    d = ImageDraw.Draw(img)
    for i, t in enumerate(lines):
        d.text((60, 60 + 52 * i), t, fill="black", font=font)
    os.makedirs("samples", exist_ok=True)
    img.save(f"samples/{name}.png")
make("sample_notice", [
 "B.S. Abdur Rahman Crescent Institute",
 "NOTICE",
 "All students of the Computer Science department are informed",
 "that the semester examination will be held on 15 December 2026.",
 "The last date to submit the project report is 05/12/2026.",
 "Hall tickets will be issued by the exam cell office.",
 "For queries contact examcell@crescent.example or call 9876543210.",
])
make("sample_invoice", [
 "INVOICE",
 "Company: Nova Supplies Pvt Ltd",
 "Invoice date: March 12, 2026",
 "Customer: Ravi Traders",
 "Total amount payable: Rs 45,000 including GST",
 "Payment due within 30 days of the order.",
 "Email billing@novasupplies.example for payment queries.",
])

# Degraded copy (blur + noise + low contrast + slight rotation) for testing
# low-confidence highlighting. Synthetic degradation, not a real scan.
import numpy as np
img = Image.open("samples/sample_notice.png").convert("L")
img = img.rotate(2.0, expand=True, fillcolor=255)
from PIL import ImageFilter
img = img.filter(ImageFilter.GaussianBlur(1.6))
a = np.asarray(img).astype(float)
a = 110 + a * 0.45
a += np.random.default_rng(1).normal(0, 22, a.shape)
Image.fromarray(np.clip(a, 0, 255).astype("uint8")).convert("RGB").save("samples/sample_notice_degraded.png")

# More samples to exercise different document types
make("sample_notice_revised", [
 "B.S. Abdur Rahman Crescent Institute",
 "NOTICE",
 "All students of the Computer Science department are informed",
 "that the semester examination will be held on 18 December 2026.",
 "The last date to submit the project report is 08/12/2026.",
 "Hall tickets will be issued by the exam cell office.",
 "For queries contact exams@crescent.example or call 9123456780.",
])
make("sample_resume", [
 "Shaik Example",
 "Curriculum Vitae",
 "Objective: To work as a software trainee in a reputed company.",
 "Skills: Python, Java, SQL, Machine Learning",
 "Education: B.Tech Computer Science, 2024 - 2028",
 "Date of Birth: 12/03/2005    Nationality: Indian",
 "Mobile: +91 98765 43210    Email: example.student@mail.example",
 "Aadhaar: 1234 5678 9012    Reg No: 240071601054",
])
