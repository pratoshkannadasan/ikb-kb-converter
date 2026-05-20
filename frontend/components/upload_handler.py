"""
Upload handler component for the document conversion frontend.
"""

import os
import tempfile
from pathlib import Path

import streamlit as st


class UploadHandler:
    """Handle document upload, validation, and temporary file management."""

    def __init__(self, max_file_size_mb=5):
        self.max_file_size_mb = max_file_size_mb
        self.supported_extensions = [".docx", ".pdf"]
        self.temp_dir = tempfile.mkdtemp(prefix="doc_conversion_")

    def validate_file(self, uploaded_file):
        """Validate uploaded file format and size."""
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
        }

        if uploaded_file.name:
            file_extension = Path(uploaded_file.name).suffix.lower()
            if file_extension not in self.supported_extensions:
                validation_results["is_valid"] = False
                validation_results["errors"].append(
                    f"Unsupported file format: {file_extension}. Only .docx and .pdf files are supported."
                )

        if uploaded_file.size:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            if file_size_mb > self.max_file_size_mb:
                validation_results["is_valid"] = False
                validation_results["errors"].append(
                    f"File too large: {file_size_mb:.1f}MB. Maximum size is {self.max_file_size_mb}MB."
                )

        return validation_results

    def save_uploaded_file(self, uploaded_file):
        """Save uploaded file to the temporary directory and return its path."""
        try:
            safe_filename = "".join(
                character for character in uploaded_file.name if character.isalnum() or character in (" ", "-", "_", ".")
            ).rstrip()
            temp_file_path = os.path.join(self.temp_dir, safe_filename)

            with open(temp_file_path, "wb") as file_handle:
                file_handle.write(uploaded_file.getbuffer())

            return temp_file_path
        except Exception as exc:
            st.error(f"Error saving uploaded file: {exc}")
            return None

    def get_file_info(self, uploaded_file):
        """Return summary details for an uploaded file."""
        if not uploaded_file:
            return None

        file_size_mb = uploaded_file.size / (1024 * 1024)
        file_extension = Path(uploaded_file.name).suffix.lower()

        if file_extension == ".pdf":
            file_type = "PDF Document"
        elif file_extension == ".docx":
            file_type = "Word Document"
        else:
            file_type = "Document"

        return {
            "name": uploaded_file.name,
            "size_mb": round(file_size_mb, 2),
            "type": file_type,
            "extension": file_extension,
        }

    def cleanup_temp_files(self):
        """Remove temporary files."""
        try:
            import shutil

            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as exc:
            st.warning(f"Warning: Could not clean up temporary files: {exc}")

    def render_upload_section(self):
        """Render the file upload section of the UI."""
        st.subheader("Source Documents")
        st.caption("Upload DOCX or PDF files for conversion into the IKB template structure.")

        uploaded_files = st.file_uploader(
            "Choose DOCX or PDF files",
            type=["docx", "pdf"],
            accept_multiple_files=True,
            help=f"Upload .docx or .pdf files up to {self.max_file_size_mb}MB each",
        )

        if uploaded_files:
            valid_files = []

            for uploaded_file in uploaded_files:
                file_info = self.get_file_info(uploaded_file)
                validation = self.validate_file(uploaded_file)
                title_text = f"{file_info['type']}: {uploaded_file.name}"
                st.markdown(
                    f"""
                    <div class="file-item-card" title="{title_text}">
                        <div class="file-item-header">
                            <div class="file-item-title" title="{title_text}">{title_text}</div>
                            <div class="file-item-subtitle" title="{uploaded_file.name}">{uploaded_file.name}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                with st.container():
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Type", file_info["type"])
                    with col2:
                        st.metric("Size", f"{file_info['size_mb']} MB")
                    with col3:
                        if validation["is_valid"]:
                            st.success("Valid")
                            valid_files.append(uploaded_file)
                        else:
                            st.error("Invalid")

                    if validation["errors"]:
                        for error in validation["errors"]:
                            st.error(error)

                    if validation["warnings"]:
                        for warning in validation["warnings"]:
                            st.warning(warning)

            return valid_files

        return []
