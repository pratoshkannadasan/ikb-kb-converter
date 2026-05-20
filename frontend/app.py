"""
Document Conversion Pipeline - Streamlit Frontend.
"""

import streamlit as st

from components.conversion_manager import ConversionManager
from components.upload_handler import UploadHandler


st.set_page_config(
    page_title="IKB Document Conversion Tool",
    page_icon="DOC",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def inject_styles():
    """Apply the visual system for the Streamlit app."""
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Instrument+Sans:wght@400;500;600&display=swap');

            :root {
                --bg: #f6f2e8;
                --paper: rgba(255, 252, 245, 0.88);
                --ink: #17211c;
                --muted: #5f6c62;
                --line: rgba(23, 33, 28, 0.10);
                --accent: #1c7c54;
                --shadow: 0 24px 60px rgba(45, 54, 47, 0.10);
            }

            html, body, [data-testid="stAppViewContainer"] {
                background:
                    radial-gradient(circle at top left, rgba(209, 123, 40, 0.18), transparent 28%),
                    radial-gradient(circle at top right, rgba(28, 124, 84, 0.18), transparent 32%),
                    linear-gradient(180deg, #fbf8f1 0%, var(--bg) 100%);
                color: var(--ink);
            }

            [data-testid="stAppViewContainer"] * {
                font-family: "Instrument Sans", sans-serif;
            }

            h1, h2, h3, h4 {
                font-family: "Space Grotesk", sans-serif !important;
                color: var(--ink);
                letter-spacing: -0.03em;
            }

            [data-testid="stHeader"] {
                background: transparent;
            }

            [data-testid="stMainBlockContainer"] {
                padding-top: 2rem;
                padding-bottom: 3rem;
                max-width: 1220px;
            }

            .hero-shell {
                background:
                    linear-gradient(135deg, rgba(255,255,255,0.90), rgba(247, 240, 225, 0.84)),
                    linear-gradient(120deg, rgba(28,124,84,0.10), rgba(209,123,40,0.10));
                border: 1px solid rgba(255,255,255,0.75);
                border-radius: 28px;
                padding: 1.4rem 1.5rem;
                box-shadow: var(--shadow);
                overflow: hidden;
                text-align: center;
            }

            .eyebrow {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.45rem 0.8rem;
                border-radius: 999px;
                background: rgba(28, 124, 84, 0.10);
                color: var(--accent);
                font-size: 0.82rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                margin: 0 auto;
            }

            .hero-grid {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 0.7rem;
                margin-top: 0.75rem;
                text-align: center;
            }

            .hero-title {
                font-size: clamp(1.7rem, 3vw, 2.5rem);
                line-height: 1;
                margin: 0;
            }

            .hero-copy {
                display: block;
                color: var(--muted);
                font-size: 0.95rem;
                line-height: 1.5;
                max-width: 40rem;
                margin: 0 auto;
                text-align: center;
                width: 100%;
            }

            .hero-panel {
                background: rgba(23, 33, 28, 0.94);
                color: #f8f2e7;
                border-radius: 24px;
                padding: 1.2rem 1.3rem;
            }

            .hero-panel h3 {
                color: #fff6e8;
                margin: 0 0 0.6rem 0;
                font-size: 1.05rem;
            }

            .hero-panel p {
                margin: 0.2rem 0;
                color: rgba(248, 242, 231, 0.82);
                font-size: 0.95rem;
            }

            .stats-grid {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.9rem;
                margin-top: 1rem;
            }

            .stat-card,
            .surface-card {
                background: var(--paper);
                border: 1px solid var(--line);
                border-radius: 22px;
                box-shadow: var(--shadow);
                backdrop-filter: blur(12px);
            }

            .stat-card {
                padding: 1rem 1.1rem;
            }

            .stat-label {
                color: var(--muted);
                font-size: 0.82rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
            }

            .stat-value {
                margin-top: 0.35rem;
                font-family: "Space Grotesk", sans-serif;
                font-size: 1.4rem;
                font-weight: 700;
                color: var(--ink);
            }

            .surface-card {
                padding: 1.2rem 1.25rem;
                margin-top: 1rem;
            }

            .main-stack {
                display: grid;
                gap: 1rem;
            }

            .file-item-card {
                padding: 1rem 1rem 0.9rem 1rem;
                margin-top: 0.85rem;
                border-radius: 18px;
                border: 1px solid var(--line);
                background: rgba(255, 252, 245, 0.84);
                box-shadow: 0 10px 30px rgba(45, 54, 47, 0.06);
                overflow: hidden;
            }

            .file-item-header {
                display: grid;
                grid-template-columns: minmax(0, 1fr);
                gap: 0.35rem;
                min-width: 0;
                margin-bottom: 0.85rem;
            }

            .file-item-title {
                min-width: 0;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                font-family: "Space Grotesk", sans-serif;
                font-size: 0.98rem;
                font-weight: 700;
                color: var(--ink);
            }

            .file-item-subtitle {
                min-width: 0;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                color: var(--muted);
                font-size: 0.84rem;
            }

            .surface-title {
                margin: 0 0 0.35rem 0;
                font-family: "Space Grotesk", sans-serif;
                font-size: 1.1rem;
                font-weight: 700;
            }

            .surface-copy {
                margin: 0;
                color: var(--muted);
                line-height: 1.65;
                font-size: 0.95rem;
            }

            .mini-list {
                margin: 0.9rem 0 0 0;
                padding-left: 1.05rem;
                color: var(--muted);
            }

            .mini-list li {
                margin-bottom: 0.4rem;
            }

            [data-testid="stFileUploader"],
            [data-testid="stExpander"],
            [data-testid="stMetric"],
            [data-testid="stAlert"] {
                border-radius: 18px;
            }

            [data-testid="stFileUploader"] {
                border: 1.5px dashed rgba(28, 124, 84, 0.35);
                background: rgba(255, 252, 245, 0.72);
                padding: 0.75rem;
            }

            [data-testid="stMetric"] {
                background: rgba(255,255,255,0.62);
                border: 1px solid var(--line);
                padding: 0.65rem 0.8rem;
            }

            .stButton > button {
                border-radius: 999px;
                min-height: 3rem;
                font-weight: 700;
                border: none;
                background: linear-gradient(135deg, var(--accent), #145f40);
                box-shadow: 0 12px 24px rgba(28, 124, 84, 0.22);
            }

            .stButton > button:hover {
                filter: brightness(1.03);
            }

            .stSelectbox > div > div {
                border-radius: 14px;
            }

            @media (max-width: 900px) {
                .hero-grid,
                .stats-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def initialize_session_state():
    """Initialize session state variables."""
    if "upload_handler" not in st.session_state:
        st.session_state.upload_handler = UploadHandler()

    if "conversion_manager" not in st.session_state:
        st.session_state.conversion_manager = ConversionManager()

    if "conversion_results" not in st.session_state:
        st.session_state.conversion_results = []

    if "is_converting" not in st.session_state:
        st.session_state.is_converting = False


def render_hero():
    """Render the top hero section."""
    st.markdown(
        """
        <section class="hero-shell">
            <div class="eyebrow">IKB</div>
            <div class="hero-grid">
                <div>
                    <h1 class="hero-title">Document Conversion Tool</h1>
                    <p class="hero-copy" style="text-align:center; margin:0 auto;">Upload files. Choose outputs. Convert.</p>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def main():
    """Main application function."""
    inject_styles()
    initialize_session_state()
    render_hero()

    try:
        from main import DocumentConversionPipeline  # noqa: F401

        pipeline_available = True
    except ImportError as exc:
        st.error("Could not import the main conversion pipeline.")
        st.error(f"Error: {exc}")
        st.info("Run this app from the repository root after installing requirements.")
        pipeline_available = False

    if not pipeline_available:
        st.stop()

    st.markdown('<div class="main-stack">', unsafe_allow_html=True)
    with st.container():
        uploaded_files = st.session_state.upload_handler.render_upload_section()

        if uploaded_files:
            conversion_settings = st.session_state.conversion_manager.render_conversion_settings(len(uploaded_files))
            convert_button = st.button(
                "Convert Documents",
                type="primary",
                disabled=st.session_state.is_converting,
                use_container_width=True,
            )

            if convert_button and not st.session_state.is_converting:
                st.session_state.is_converting = True
                temp_file_paths = []

                for uploaded_file in uploaded_files:
                    temp_path = st.session_state.upload_handler.save_uploaded_file(uploaded_file)
                    if temp_path:
                        temp_file_paths.append(temp_path)

                if temp_file_paths:
                    st.markdown(
                        """
                        <div class="surface-card">
                            <h3 class="surface-title">Conversion Progress</h3>
                            <p class="surface-copy">Processing uploaded files and shaping them into the IKB structure.</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    def progress_callback(progress, message):
                        progress_bar.progress(progress)
                        status_text.text(message)

                    with st.spinner("Converting documents..."):
                        st.session_state.conversion_results = st.session_state.conversion_manager.convert_documents(
                            temp_file_paths,
                            output_format=conversion_settings["output_format"],
                            output_count=conversion_settings["output_count"],
                            progress_callback=progress_callback,
                        )

                    st.session_state.upload_handler.cleanup_temp_files()
                    st.session_state.is_converting = False

                    if st.session_state.conversion_results:
                        successful_conversions = sum(
                            1 for result in st.session_state.conversion_results if result["success"]
                        )
                        total_conversions = len(st.session_state.conversion_results)
                        if successful_conversions == total_conversions:
                            st.success(f"All {total_conversions} document(s) converted successfully.")
                        else:
                            st.warning(
                                f"{successful_conversions} of {total_conversions} document(s) converted successfully."
                            )

                    st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.conversion_results:
        st.markdown(
            """
            <div class="surface-card">
                <h3 class="surface-title">Results</h3>
                <p class="surface-copy">Downloads and status.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.session_state.conversion_manager.render_results_section(st.session_state.conversion_results)


if __name__ == "__main__":
    main()
