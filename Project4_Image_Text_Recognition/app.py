import streamlit as st
import cv2
import pytesseract
import numpy as np
from PIL import Image

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Vision | Text Recognition",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tesseract location
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

.main {
    padding-top: 1rem;
}

.hero {
    padding: 2rem;
    border-radius: 20px;
    background: linear-gradient(135deg, #172554, #1e3a8a);
    color: white;
    text-align: center;
    margin-bottom: 25px;
}

.hero h1 {
    font-size: 42px;
    margin-bottom: 8px;
}

.hero p {
    font-size: 18px;
    opacity: 0.9;
}

.section-title {
    font-size: 25px;
    font-weight: 700;
    margin-top: 15px;
    margin-bottom: 12px;
}

.info-card {
    padding: 18px;
    border-radius: 15px;
    border: 1px solid rgba(128,128,128,0.25);
    background-color: rgba(128,128,128,0.08);
    margin-bottom: 15px;
}

.result-card {
    padding: 20px;
    border-radius: 15px;
    border: 2px solid rgba(59,130,246,0.35);
    background-color: rgba(59,130,246,0.08);
}

.small-text {
    color: #777;
    font-size: 14px;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="hero">

<h1>🤖 AI Vision</h1>

<p>
Image & Text Recognition System
</p>

<p>
Upload an image → preprocess it → extract text using OCR
</p>

</div>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Recognition Settings")

    st.write(
        "Upload a clear image containing printed text "
        "for better recognition."
    )

    st.divider()

    st.subheader("🔧 Processing Pipeline")

    st.write("1️⃣ Image Upload")
    st.write("2️⃣ Grayscale Conversion")
    st.write("3️⃣ Gaussian Blur")
    st.write("4️⃣ Thresholding")
    st.write("5️⃣ OCR Recognition")

    st.divider()

    st.info(
        "💡 Tip: Clear, high-contrast images usually "
        "produce better OCR results."
    )

# ============================================================
# UPLOAD SECTION
# ============================================================

st.markdown(
    '<div class="section-title">📤 Upload Your Image</div>',
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader(
    "Choose an image containing text",
    type=["png", "jpg", "jpeg"],
    help="Supported formats: PNG, JPG and JPEG"
)

# ============================================================
# MAIN PROCESSING
# ============================================================

if uploaded_file is not None:

    image = Image.open(uploaded_file).convert("RGB")

    image_array = np.array(image)

    # Convert RGB → OpenCV
    image_cv = cv2.cvtColor(
        image_array,
        cv2.COLOR_RGB2BGR
    )

    # ========================================================
    # ORIGINAL IMAGE
    # ========================================================

    st.markdown(
        '<div class="section-title">🖼️ Original Image</div>',
        unsafe_allow_html=True
    )

    st.image(
        image,
        use_container_width=True
    )

    # ========================================================
    # IMAGE INFORMATION
    # ========================================================

    width, height = image.size

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "📐 Width",
        f"{width}px"
    )

    col2.metric(
        "📏 Height",
        f"{height}px"
    )

    col3.metric(
        "📦 Format",
        uploaded_file.type.split("/")[-1].upper()
    )

    st.divider()

    # ========================================================
    # PREPROCESSING
    # ========================================================

    st.markdown(
        '<div class="section-title">⚙️ Image Preprocessing</div>',
        unsafe_allow_html=True
    )

    # Grayscale
    gray = cv2.cvtColor(
        image_cv,
        cv2.COLOR_BGR2GRAY
    )

    # Gaussian Blur
    blurred = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    # Threshold
    _, processed = cv2.threshold(
        blurred,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    tab1, tab2, tab3 = st.tabs(
        ["⚫ Grayscale", "🌫️ Gaussian Blur", "⬜ Threshold"]
    )

    with tab1:

        st.write(
            "Converts the image into grayscale to simplify "
            "the visual information."
        )

        st.image(
            gray,
            use_container_width=True
        )

    with tab2:

        st.write(
            "Gaussian blur helps reduce small image noise "
            "and imperfections."
        )

        st.image(
            blurred,
            use_container_width=True
        )

    with tab3:

        st.write(
            "Thresholding creates a high-contrast image "
            "that makes text easier for OCR to recognize."
        )

        st.image(
            processed,
            use_container_width=True
        )

    # ========================================================
    # OCR SECTION
    # ========================================================

    st.divider()

    st.markdown(
        '<div class="section-title">🤖 AI Text Recognition</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Click the button below to extract readable text "
        "from the processed image."
    )

    if st.button(
        "✨ Extract Text",
        use_container_width=True,
        type="primary"
    ):

        with st.spinner("🔍 Analyzing image and recognizing text..."):

            try:

                extracted_text = pytesseract.image_to_string(
                    processed,
                    config="--psm 6"
                )

                # ============================================
                # RESULT
                # ============================================

                if extracted_text.strip():

                    st.success(
                        "✅ Text recognized successfully!"
                    )

                    st.markdown(
                        '<div class="result-card">',
                        unsafe_allow_html=True
                    )

                    st.subheader("📝 Extracted Text")

                    st.text_area(
                        "Recognition Output",
                        extracted_text,
                        height=250,
                        label_visibility="collapsed"
                    )

                    st.markdown(
                        '</div>',
                        unsafe_allow_html=True
                    )

                    # ========================================
                    # STATISTICS
                    # ========================================

                    st.subheader("📊 Recognition Statistics")

                    words = extracted_text.split()

                    characters = len(extracted_text)

                    lines = len(
                        [
                            line
                            for line in extracted_text.splitlines()
                            if line.strip()
                        ]
                    )

                    c1, c2, c3 = st.columns(3)

                    c1.metric(
                        "🔤 Characters",
                        characters
                    )

                    c2.metric(
                        "📝 Words",
                        len(words)
                    )

                    c3.metric(
                        "📄 Lines",
                        lines
                    )

                else:

                    st.warning(
                        "⚠️ No readable text was detected."
                    )

                    st.info(
                        "Try using a clearer image with larger "
                        "or darker text."
                    )

            except Exception as error:

                st.error(
                    f"❌ OCR Error: {error}"
                )

else:

    # ========================================================
    # EMPTY STATE
    # ========================================================

    st.markdown(
        """
        <div class="info-card">

        <h3>👆 Get Started</h3>

        <p>
        Upload an image containing text to begin the
        recognition process.
        </p>

        <p class="small-text">
        Recommended: clear printed text with good lighting
        and strong contrast.
        </p>

        </div>
        """,
        unsafe_allow_html=True
    )

# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🤖 AI Image & Text Recognition | "
    "DecodeLabs Artificial Intelligence Internship — Project 4"
)