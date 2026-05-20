"""
Conversion manager component for the document conversion frontend.
"""

import os
import re
import sys
from pathlib import Path

import streamlit as st


project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from main import DocumentConversionPipeline
    import config
except ImportError as exc:
    st.error(f"Could not import main pipeline: {exc}")
    st.error(f"Resolved project root: {project_root}")
    st.error("Please ensure you're running this from the doc-conv-pipeline directory")


class ConversionManager:
    """Manage document conversion and results rendering."""

    USD_TO_MYR_RATE = 4.24

    def __init__(self):
        self.pipeline = None
        self.conversion_results = {}
        import logging

        self.logger = logging.getLogger(__name__)

    def convert_usd_to_myr(self, usd_amount):
        """Convert USD to MYR."""
        return usd_amount * self.USD_TO_MYR_RATE

    def initialize_pipeline(self):
        """Initialize the document conversion pipeline."""
        try:
            if self.pipeline is None:
                self.pipeline = DocumentConversionPipeline()
            return True
        except Exception as exc:
            st.error(f"Failed to initialize conversion pipeline: {exc}")
            return False

    def _extract_document_payload(self, file_path):
        """Extract clean content and metadata from a source file."""
        document_summary = self.pipeline.document_extractor.get_document_summary(file_path)
        content = document_summary["cleaned_text"]
        hyperlinks = document_summary.get("hyperlinks", [])

        if not content.strip():
            raise ValueError(f"No content extracted from document: {os.path.basename(file_path)}")

        if hyperlinks:
            self.logger.info("Frontend: Extracted %s hyperlinks from %s", len(hyperlinks), os.path.basename(file_path))

        return {
            "file_path": file_path,
            "filename": os.path.basename(file_path),
            "content": content,
            "hyperlinks": hyperlinks,
            "summary": document_summary,
        }

    def _build_group_source_content(self, payloads):
        """Build the source content string for a single output group."""
        if len(payloads) == 1:
            return payloads[0]["content"]

        sections = []
        for payload in payloads:
            sections.append(
                f"Source document: {payload['filename']}\n\n{payload['content'].strip()}"
            )
        return "\n\n" + ("\n\n" + ("=" * 80) + "\n\n").join(sections)

    def _aggregate_hyperlinks(self, payloads):
        """Combine hyperlinks from all payloads in a group."""
        all_hyperlinks = []
        for payload in payloads:
            all_hyperlinks.extend(payload["hyperlinks"])
        return all_hyperlinks

    def _structure_content(self, content, hyperlinks):
        """Run the AI pipeline with the existing fallback chain."""
        template = self.pipeline.template_generator.load_template()

        try:
            structured_content = self.pipeline.ai_processor.structure_content_with_recommendations(
                content, template, hyperlinks
            )
        except Exception:
            try:
                structured_content = self.pipeline.ai_processor.process_with_retry_adaptive(
                    content, template, max_retries=config.MAX_RETRIES, hyperlinks=hyperlinks
                )
            except Exception:
                if hyperlinks:
                    try:
                        structured_content = self.pipeline.ai_processor.structure_content_with_hyperlinks(
                            content, template, hyperlinks
                        )
                    except Exception:
                        structured_content = self.pipeline.ai_processor.structure_content_adaptive(
                            content, template, hyperlinks
                        )
                else:
                    structured_content = self.pipeline.ai_processor.structure_content_adaptive(
                        content, template, hyperlinks
                    )

        return structured_content

    def _validate_hyperlinks(self, structured_content, hyperlinks):
        """Return hyperlink preservation summary."""
        if not hyperlinks:
            return {}

        markdown_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", structured_content)
        preserved_count = len(markdown_links)
        original_count = len(hyperlinks)
        preservation_rate = preserved_count / original_count if original_count > 0 else 1.0

        return {
            "original_count": original_count,
            "preserved_count": preserved_count,
            "preservation_rate": preservation_rate,
            "status": (
                "excellent"
                if preservation_rate >= 0.9
                else "good"
                if preservation_rate >= 0.7
                else "needs_improvement"
            ),
        }

    def _build_group_filename(self, payloads, group_index, total_groups):
        """Build the output base filename for a group."""
        if len(payloads) == 1:
            source_stem = Path(payloads[0]["filename"]).stem
            return f"converted_{source_stem}"

        if total_groups == 1:
            return f"converted_merged_{len(payloads)}_documents"

        return f"converted_group_{group_index}_of_{total_groups}"

    def _build_result(self, payloads, structured_content, saved_files, compliance_score, issues):
        """Build the frontend result payload."""
        final_is_valid, final_issues = self.pipeline.template_generator.validate_markdown(structured_content)
        hyperlinks = self._aggregate_hyperlinks(payloads)
        usage_summary = self.pipeline.ai_processor.usage_tracker.get_usage_summary()

        total_words = sum(payload["summary"]["summary_stats"]["total_words"] for payload in payloads)
        total_tables = sum(payload["summary"]["summary_stats"]["total_tables"] for payload in payloads)
        combined_source_name = payloads[0]["filename"] if len(payloads) == 1 else f"{len(payloads)} source documents"

        return {
            "success": True,
            "filename": combined_source_name,
            "source_filenames": [payload["filename"] for payload in payloads],
            "source_file_count": len(payloads),
            "saved_files": saved_files,
            "compliance_score": compliance_score,
            "validation_issues": issues,
            "final_validation": {
                "is_valid": final_is_valid,
                "issues": final_issues,
            },
            "hyperlink_preservation": self._validate_hyperlinks(structured_content, hyperlinks),
            "content_stats": {
                "words": total_words,
                "chars": len(structured_content),
                "tables": total_tables,
                "hyperlinks": len(hyperlinks),
            },
            "cost_info": {
                "api_calls": usage_summary["total_api_calls"],
                "total_tokens": usage_summary["total_tokens"],
                "input_tokens": usage_summary["total_input_tokens"],
                "output_tokens": usage_summary["total_output_tokens"],
                "cost_usd": usage_summary["total_cost"],
                "cost_myr": self.convert_usd_to_myr(usage_summary["total_cost"]),
                "average_cost_per_call_usd": usage_summary["average_cost_per_call"],
                "average_cost_per_call_myr": self.convert_usd_to_myr(usage_summary["average_cost_per_call"]),
            },
        }

    def convert_document_group(self, file_paths, output_format="docx", progress_callback=None, group_index=1, total_groups=1):
        """Convert one group of source files into one output document."""
        try:
            if not self.initialize_pipeline():
                return None

            if progress_callback:
                progress_callback(10, "Extracting source documents...")

            payloads = [self._extract_document_payload(file_path) for file_path in file_paths]
            combined_content = self._build_group_source_content(payloads)
            combined_hyperlinks = self._aggregate_hyperlinks(payloads)

            if progress_callback:
                progress_callback(40, "Structuring content with the AI pipeline...")

            structured_content = self._structure_content(combined_content, combined_hyperlinks)

            if progress_callback:
                progress_callback(70, "Validating and fixing content...")

            is_valid, compliance_score, issues = self.pipeline.ai_processor.validate_structure(structured_content)
            if not is_valid:
                fixed_content, remaining_issues = self.pipeline.template_generator.validate_and_fix_content(
                    structured_content
                )
                if len(remaining_issues) < len(issues):
                    structured_content = fixed_content
                    issues = remaining_issues

            if progress_callback:
                progress_callback(90, "Saving output document...")

            base_filename = self._build_group_filename(payloads, group_index, total_groups)
            saved_files = self.pipeline.template_generator.save_document_dual_format(
                structured_content, base_filename, output_format
            )

            if progress_callback:
                progress_callback(100, "Output document completed.")

            result = self._build_result(payloads, structured_content, saved_files, compliance_score, issues)
            result["group_index"] = group_index
            result["total_groups"] = total_groups
            if len(payloads) > 1:
                result["filename"] = f"Grouped Output {group_index}"
            return result
        except Exception as exc:
            if progress_callback:
                progress_callback(0, f"Conversion failed: {exc}")

            return {
                "success": False,
                "error": str(exc),
                "filename": f"Grouped Output {group_index}" if len(file_paths) > 1 else os.path.basename(file_paths[0]),
                "source_filenames": [os.path.basename(file_path) for file_path in file_paths],
                "source_file_count": len(file_paths),
                "saved_files": {},
            }

    def _partition_files(self, file_paths, output_count):
        """Split input files into ordered groups for output generation."""
        total_files = len(file_paths)
        output_count = max(1, min(output_count, total_files))
        base_group_size, remainder = divmod(total_files, output_count)
        groups = []
        start = 0

        for group_index in range(output_count):
            group_size = base_group_size + (1 if group_index < remainder else 0)
            end = start + group_size
            groups.append(file_paths[start:end])
            start = end

        return groups

    def convert_documents(self, file_paths, output_format="docx", output_count=None, progress_callback=None):
        """Convert selected input files into the requested number of outputs."""
        if not file_paths:
            return []

        total_inputs = len(file_paths)
        requested_outputs = output_count or total_inputs
        groups = self._partition_files(file_paths, requested_outputs)
        results = []

        for index, group in enumerate(groups, start=1):
            overall_progress = int(((index - 1) / len(groups)) * 100)
            group_label = f"Output {index}/{len(groups)}"

            if progress_callback:
                progress_callback(
                    overall_progress,
                    f"{group_label}: processing {len(group)} input file(s)",
                )

            def group_progress_callback(progress, message):
                combined_progress = int(overall_progress + (progress / len(groups)))
                if progress_callback:
                    progress_callback(combined_progress, f"{group_label}: {message}")

            result = self.convert_document_group(
                group,
                output_format=output_format,
                progress_callback=group_progress_callback,
                group_index=index,
                total_groups=len(groups),
            )
            results.append(result)

        if progress_callback:
            progress_callback(100, "All requested outputs completed.")

        return results

    def get_output_formats(self):
        """Return available output formats."""
        return {
            "docx": "DOCX",
            "markdown": "Markdown",
            "both": "Both formats",
        }

    def render_conversion_settings(self, input_file_count):
        """Render conversion settings."""
        st.subheader("Conversion Settings")

        format_options = self.get_output_formats()
        selected_format = st.selectbox(
            "Output Format",
            options=list(format_options.keys()),
            format_func=lambda value: format_options[value],
            index=0,
            help="Choose the output format for converted documents",
        )

        if input_file_count > 1:
            output_count = st.slider(
                "Number of Output KB Documents",
                min_value=1,
                max_value=input_file_count,
                value=input_file_count,
                step=1,
                help="1 merges all selected files into one output. Matching the input count keeps one output per file.",
            )
            if output_count == 1:
                st.caption(f"{input_file_count} input files will be merged into 1 output file.")
            elif output_count == input_file_count:
                st.caption("Each input file will render as its own KB output.")
            else:
                st.caption(
                    f"{input_file_count} input files will be grouped into {output_count} output files in upload order."
                )
        else:
            output_count = 1

        return {
            "output_format": selected_format,
            "output_count": output_count,
        }

    def render_results_section(self, results):
        """Render conversion results."""
        if not results:
            return

        st.subheader("Conversion Results")

        total_outputs = len(results)
        successful_files = sum(1 for result in results if result["success"])
        failed_files = total_outputs - successful_files

        total_cost_usd = sum(result.get("cost_info", {}).get("cost_usd", 0) for result in results if result["success"])
        total_cost_myr = sum(result.get("cost_info", {}).get("cost_myr", 0) for result in results if result["success"])
        total_api_calls = sum(result.get("cost_info", {}).get("api_calls", 0) for result in results if result["success"])
        total_tokens = sum(result.get("cost_info", {}).get("total_tokens", 0) for result in results if result["success"])

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Output Files", total_outputs)
        with col2:
            st.metric("Successful", successful_files, delta=successful_files)
        with col3:
            st.metric("Failed", failed_files, delta=-failed_files if failed_files > 0 else 0)
        with col4:
            st.metric("Total Cost (USD)", f"${total_cost_usd:.4f}")
        with col5:
            st.metric("Total Cost (MYR)", f"RM{total_cost_myr:.4f}")

        if successful_files > 0 and total_api_calls > 0:
            st.info(f"API usage summary: {total_api_calls} API calls, {total_tokens:,} tokens processed")

        for index, result in enumerate(results):
            filename = result.get("filename", f"Output {index + 1}")
            source_names = result.get("source_filenames", [])
            source_file_count = result.get("source_file_count", len(source_names))
            if source_file_count > 1:
                expander_label = f"Output {index + 1}"
            else:
                expander_label = f"Output {index + 1}: {filename}"

            with st.expander(expander_label, expanded=result["success"]):
                if source_file_count > 1:
                    st.markdown(f"**Output Name:** {filename}")
                if source_names:
                    st.caption(
                        f"Built from {source_file_count} input file(s): " + ", ".join(source_names)
                    )

                if result["success"]:
                    st.success("Conversion successful.")

                    if "content_stats" in result or "cost_info" in result:
                        col1, col2, col3, col4 = st.columns(4)

                        if "content_stats" in result:
                            with col1:
                                st.metric("Words", f"{result['content_stats']['words']:,}")
                            with col2:
                                st.metric("Characters", f"{result['content_stats']['chars']:,}")

                        if "cost_info" in result:
                            with col3:
                                st.metric("Cost (USD)", f"${result['cost_info']['cost_usd']:.4f}")
                            with col4:
                                st.metric("Cost (MYR)", f"RM{result['cost_info']['cost_myr']:.4f}")

                    if "cost_info" in result:
                        st.markdown("**API Usage Details**")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.text(f"API Calls: {result['cost_info']['api_calls']}")
                            st.text(f"Total Tokens: {result['cost_info']['total_tokens']:,}")
                        with col2:
                            st.text(f"Input Tokens: {result['cost_info']['input_tokens']:,}")
                            st.text(f"Output Tokens: {result['cost_info']['output_tokens']:,}")
                        st.markdown("---")

                    if "saved_files" in result:
                        st.subheader("Downloads")
                        for format_type, file_path in result["saved_files"].items():
                            if os.path.exists(file_path):
                                with open(file_path, "rb") as file_handle:
                                    file_data = file_handle.read()

                                st.download_button(
                                    label=f"Download {format_type.upper()} File",
                                    data=file_data,
                                    file_name=os.path.basename(file_path),
                                    mime=(
                                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                        if format_type == "docx"
                                        else "text/markdown"
                                    ),
                                    key=f"{filename}-{format_type}-{index}",
                                )

                    if "validation_issues" in result and result["validation_issues"]:
                        st.subheader("Validation Issues")
                        for issue in result["validation_issues"]:
                            st.warning(issue)
                else:
                    st.error("Conversion failed.")
                    if "error" in result:
                        st.error(f"Error: {result['error']}")
