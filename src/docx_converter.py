"""
DOCX Converter Module
Converts structured markdown content to professional DOCX format.
"""

import logging
import os
import re
from typing import Dict, List, Optional, Tuple
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.shared import OxmlElement, qn
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml


class DOCXConverter:
    """Convert markdown content to professionally formatted DOCX documents."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.document = None
        
        # Styling configuration
        self.styles = {
            'font_name': 'Calibri',
            'font_size': 11,
            'header_colors': {
                'h1': RGBColor(31, 78, 121),    # Dark blue
                'h2': RGBColor(46, 117, 182),   # Medium blue  
                'h3': RGBColor(112, 173, 71),   # Green
                'h4': RGBColor(68, 114, 196),   # Light blue
            },
            'table_style': 'Light Grid Accent 1'
        }
    
    def convert_markdown_to_docx(self, markdown_content: str, output_path: str) -> str:
        """Main conversion function from markdown to DOCX.
        
        Args:
            markdown_content (str): Structured markdown content
            output_path (str): Output path for DOCX file
            
        Returns:
            str: Path to created DOCX file
        """
        try:
            self.logger.info("Starting markdown to DOCX conversion")
            
            # Create new document
            self.document = Document()
            
            # Set document margins
            self._set_document_margins()
            
            # Process markdown content line by line
            lines = markdown_content.split('\n')
            self._process_markdown_lines(lines)
            
            # Save document
            output_dir = os.path.dirname(output_path)
            if output_dir:  # Only create directories if there's a directory path
                os.makedirs(output_dir, exist_ok=True)
            self.document.save(output_path)
            
            self.logger.info(f"DOCX document saved to: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error converting to DOCX: {str(e)}")
            raise
    
    def _set_document_margins(self):
        """Set professional document margins."""
        sections = self.document.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)
    
    def _process_markdown_lines(self, lines: List[str]):
        """Process markdown lines and convert to DOCX elements."""
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                # Add paragraph break for empty lines
                self.document.add_paragraph()
                i += 1
                continue
            
            # Headers
            if line.startswith('#'):
                self._add_header(line)
                i += 1
            
            # Tables
            elif line.startswith('|') and '|---' not in line:
                table_lines, i = self._extract_table_lines(lines, i)
                if table_lines:
                    self._add_table(table_lines)
            
            # Lists
            elif line.startswith('-') or line.startswith('*'):
                list_lines, i = self._extract_list_lines(lines, i)
                self._add_list(list_lines)
            
            # Numbered lists
            elif re.match(r'^\d+\.', line):
                list_lines, i = self._extract_numbered_list_lines(lines, i)
                self._add_numbered_list(list_lines)
            
            # Bold text patterns (standalone)
            elif line.startswith('**') and line.endswith('**'):
                self._add_bold_paragraph(line)
                i += 1
            
            # Regular paragraphs
            else:
                self._add_paragraph(line)
                i += 1
    
    def _add_header(self, line: str):
        """Add header with appropriate styling."""
        # Count header level
        level = 0
        for char in line:
            if char == '#':
                level += 1
            else:
                break
        
        # Extract header text
        header_text = line[level:].strip()
        
        # Add header paragraph
        if level == 1:
            paragraph = self.document.add_heading(header_text, 1)
            # Make title larger and colored
            run = paragraph.runs[0]
            run.font.size = Pt(18)
            run.font.color.rgb = self.styles['header_colors']['h1']
            run.bold = True
        elif level == 2:
            paragraph = self.document.add_heading(header_text, 2)
            run = paragraph.runs[0]
            run.font.size = Pt(14)
            run.font.color.rgb = self.styles['header_colors']['h2']
            run.bold = True
        elif level == 3:
            paragraph = self.document.add_heading(header_text, 3)
            run = paragraph.runs[0]
            run.font.size = Pt(12)
            run.font.color.rgb = self.styles['header_colors']['h3']
            run.bold = True
        else:
            # Level 4+ headers as bold paragraphs
            paragraph = self.document.add_paragraph()
            run = paragraph.add_run(header_text)
            run.bold = True
            run.font.size = Pt(11)
            run.font.color.rgb = self.styles['header_colors'].get('h4', RGBColor(0, 0, 0))
    
    def _extract_table_lines(self, lines: List[str], start_index: int) -> Tuple[List[str], int]:
        """Extract consecutive table lines."""
        table_lines = []
        i = start_index
        
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('|') or line.startswith('+') or '---' in line:
                if '---' in line:  # Skip separator lines
                    i += 1
                    continue
                table_lines.append(line)
                i += 1
            else:
                break
        
        return table_lines, i
    
    def _add_table(self, table_lines: List[str]):
        """Add a formatted table to the document."""
        if not table_lines:
            return
        
        # Parse table data
        rows = []
        for line in table_lines:
            # Split by | and clean up
            cells = [cell.strip() for cell in line.split('|')[1:-1]]  # Remove empty first/last
            if cells:
                rows.append(cells)
        
        if not rows:
            return
        
        # Create table
        table = self.document.add_table(rows=len(rows), cols=len(rows[0]))
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        # Add data to table
        for row_idx, row_data in enumerate(rows):
            for col_idx, cell_data in enumerate(row_data):
                if row_idx < len(table.rows) and col_idx < len(table.rows[row_idx].cells):
                    cell = table.rows[row_idx].cells[col_idx]
                    
                    # Clear existing content and add formatted content
                    cell.text = ""
                    paragraph = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
                    
                    # Clean and process cell data (remove HTML tags)
                    cleaned_cell_data = self._clean_markdown_artifacts(cell_data)
                    
                    # Handle line breaks in table cells
                    self._process_text_with_line_breaks(paragraph, cleaned_cell_data)
                    
                    # Style header row
                    if row_idx == 0:
                        for run in paragraph.runs:
                            run.bold = True
                            run.font.color.rgb = RGBColor(255, 255, 255)  # White text
                        
                        # Add background color to header
                        self._set_cell_background(cell, "366092")  # Dark blue background
        
        # Apply table style
        table.style = 'Light Grid Accent 1'
        
        # Add spacing after table
        self.document.add_paragraph()
    
    def _set_cell_background(self, cell, color_hex: str):
        """Set background color for table cell."""
        cell_xml_element = cell._tc
        table_cell_properties = cell_xml_element.get_or_add_tcPr()
        shade_obj = OxmlElement('w:shd')
        shade_obj.set(qn('w:fill'), color_hex)
        table_cell_properties.append(shade_obj)
    
    def _extract_list_lines(self, lines: List[str], start_index: int) -> Tuple[List[str], int]:
        """Extract consecutive bullet list lines."""
        list_lines = []
        i = start_index
        
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('-') or line.startswith('*') or (line.startswith(' ') and list_lines):
                list_lines.append(line)
                i += 1
            else:
                break
        
        return list_lines, i
    
    def _add_list(self, list_lines: List[str]):
        """Add bullet list to document."""
        for line in list_lines:
            # Clean up the line and remove markdown artifacts
            text = line.lstrip('- *').strip()
            text = self._clean_markdown_artifacts(text)
            
            if text:
                paragraph = self.document.add_paragraph(text, style='List Bullet')
                
                # Process any remaining inline formatting
                # Clear the paragraph first and re-add with formatting
                paragraph.clear()
                self._process_inline_formatting(paragraph, text)
                
                # Set font for all runs
                for run in paragraph.runs:
                    run.font.name = self.styles['font_name']
                    run.font.size = Pt(self.styles['font_size'])
    
    def _extract_numbered_list_lines(self, lines: List[str], start_index: int) -> Tuple[List[str], int]:
        """Extract consecutive numbered list lines."""
        list_lines = []
        i = start_index
        
        while i < len(lines):
            line = lines[i].strip()
            if re.match(r'^\d+\.', line) or (line.startswith(' ') and list_lines):
                list_lines.append(line)
                i += 1
            else:
                break
        
        return list_lines, i
    
    def _add_numbered_list(self, list_lines: List[str]):
        """Add numbered list to document."""
        for line in list_lines:
            # Clean up the line - remove number and dot
            text = re.sub(r'^\d+\.\s*', '', line).strip()
            if text:
                paragraph = self.document.add_paragraph(text, style='List Number')
                # Set font
                for run in paragraph.runs:
                    run.font.name = self.styles['font_name']
                    run.font.size = Pt(self.styles['font_size'])
    
    def _add_bold_paragraph(self, line: str):
        """Add paragraph with bold text."""
        text = line.strip('*').strip()
        paragraph = self.document.add_paragraph()
        run = paragraph.add_run(text)
        run.bold = True
        run.font.name = self.styles['font_name']
        run.font.size = Pt(self.styles['font_size'])
    
    def _add_paragraph(self, line: str):
        """Add regular paragraph with text formatting."""
        paragraph = self.document.add_paragraph()
        
        # Clean up any remaining markdown artifacts
        cleaned_line = self._clean_markdown_artifacts(line)
        
        # Process inline formatting (bold, italic)
        self._process_inline_formatting(paragraph, cleaned_line)
        
        # Set paragraph font
        for run in paragraph.runs:
            run.font.name = self.styles['font_name']
            run.font.size = Pt(self.styles['font_size'])
    
    def _clean_markdown_artifacts(self, text: str) -> str:
        """Clean up any remaining markdown formatting artifacts and HTML tags."""
        # Remove any standalone asterisks that weren't processed
        # This handles cases where markdown formatting wasn't properly closed
        cleaned = re.sub(r'\*{1,2}(?!\w)', '', text)  # Remove trailing asterisks
        cleaned = re.sub(r'(?<!\w)\*{1,2}', '', cleaned)  # Remove leading asterisks
        
        # Remove HTML tags that might come from AI processing
        # Handle common HTML tags: <br>, <br/>, <br />, <p>, </p>, <div>, </div>, etc.
        cleaned = re.sub(r'<br\s*/?>', '\n', cleaned, flags=re.IGNORECASE)  # Convert <br> to line break
        cleaned = re.sub(r'</?(?:p|div|span|strong|b|em|i|u)[^>]*>', '', cleaned, flags=re.IGNORECASE)  # Remove other HTML tags
        cleaned = re.sub(r'&nbsp;', ' ', cleaned, flags=re.IGNORECASE)  # Convert HTML space entities
        cleaned = re.sub(r'&amp;', '&', cleaned, flags=re.IGNORECASE)  # Convert HTML ampersand entities
        cleaned = re.sub(r'&lt;', '<', cleaned, flags=re.IGNORECASE)  # Convert HTML less-than entities
        cleaned = re.sub(r'&gt;', '>', cleaned, flags=re.IGNORECASE)  # Convert HTML greater-than entities
        
        # Clean up multiple spaces but preserve single line breaks
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)  # Multiple spaces/tabs to single space
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)  # Multiple line breaks to single
        cleaned = re.sub(r'^\s+|\s+$', '', cleaned)  # Trim leading/trailing whitespace
        
        return cleaned.strip()
    
    def _process_text_with_line_breaks(self, paragraph, text: str):
        """Process text that may contain line breaks, handling them properly in DOCX."""
        # Split text by line breaks
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            if line.strip():  # Only process non-empty lines
                # Process inline formatting for each line
                self._process_inline_formatting(paragraph, line.strip())
                
                # Add line break if not the last line and there are more lines
                if i < len(lines) - 1 and any(l.strip() for l in lines[i+1:]):
                    # Add a line break run
                    run = paragraph.add_run()
                    run.add_break()
    
    def _process_inline_formatting(self, paragraph, text: str):
        """Process inline markdown formatting like **bold**, *italic*, and [links](url)."""
        # Enhanced regex patterns for formatting
        bold_pattern = r'\*\*(.*?)\*\*'
        italic_pattern = r'(?<!\*)\*([^*]+?)\*(?!\*)'  # Improved italic pattern to avoid conflicts with bold
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'  # Pattern for markdown links [text](url)
        
        # Find all formatting matches
        bold_matches = list(re.finditer(bold_pattern, text))
        italic_matches = list(re.finditer(italic_pattern, text))
        link_matches = list(re.finditer(link_pattern, text))
        
        # Combine and sort all matches by position
        all_matches = []
        
        # Add bold matches
        for match in bold_matches:
            all_matches.append(('bold', match.start(), match.end(), match.group(1)))
        
        # Add italic matches (exclude those inside bold patterns)
        for match in italic_matches:
            # Check if this italic match overlaps with any bold match
            overlaps_with_bold = any(
                match.start() >= bold_match.start() and match.end() <= bold_match.end() 
                for bold_match in bold_matches
            )
            if not overlaps_with_bold:
                all_matches.append(('italic', match.start(), match.end(), match.group(1)))
        
        # Add link matches
        for match in link_matches:
            # Check if this link overlaps with bold or italic
            overlaps = any(
                match.start() >= other_match.start() and match.end() <= other_match.end() 
                for other_match in bold_matches + italic_matches
            )
            if not overlaps:
                all_matches.append(('link', match.start(), match.end(), match.group(1), match.group(2)))
        
        # Sort by start position
        all_matches.sort(key=lambda x: x[1])
        
        # Process text with formatting
        if all_matches:
            current_pos = 0
            
            for match_data in all_matches:
                match_type = match_data[0]
                start = match_data[1]
                end = match_data[2]
                
                # Add any plain text before this formatted section
                if current_pos < start:
                    plain_text = text[current_pos:start]
                    if plain_text:
                        paragraph.add_run(plain_text)
                
                # Add the formatted text
                if match_type == 'link':
                    content = match_data[3]  # Link text
                    url = match_data[4]      # Link URL
                    
                    # Create hyperlink in DOCX
                    self._add_hyperlink(paragraph, content, url)
                else:
                    content = match_data[3]
                    formatted_run = paragraph.add_run(content)
                    if match_type == 'bold':
                        formatted_run.bold = True
                    elif match_type == 'italic':
                        formatted_run.italic = True
                
                # Update position to after this match
                current_pos = end
            
            # Add any remaining plain text after the last formatted section
            if current_pos < len(text):
                remaining_text = text[current_pos:]
                if remaining_text:
                    paragraph.add_run(remaining_text)
        else:
            # No formatting found - add text as-is
            paragraph.add_run(text)
    
    def _add_hyperlink(self, paragraph, text: str, url: str):
        """Add a hyperlink as plain text in markdown format for consistent RAG processing."""
        # Always use markdown format for consistent output
        markdown_link = f"[{text}]({url})"
        paragraph.add_run(markdown_link)
    
    def add_document_properties(self, title: str, author: str = "Document Conversion Pipeline"):
        """Add document properties for better organization."""
        if self.document:
            core_props = self.document.core_properties
            core_props.title = title
            core_props.author = author
            core_props.comments = "Generated by IKB Document Conversion Pipeline"
    
    def validate_docx_output(self, output_path: str) -> Tuple[bool, List[str]]:
        """Validate the created DOCX file."""
        issues = []
        
        try:
            # Check if file exists
            if not os.path.exists(output_path):
                issues.append("DOCX file was not created")
                return False, issues
            
            # Check file size
            file_size = os.path.getsize(output_path)
            if file_size < 1000:  # Less than 1KB seems too small
                issues.append("DOCX file seems too small")
            
            # Try to open the document
            test_doc = Document(output_path)
            
            # Check if document has content
            if len(test_doc.paragraphs) == 0:
                issues.append("DOCX document has no paragraphs")
            
            # Check for tables
            if len(test_doc.tables) == 0:
                issues.append("DOCX document has no tables (pricing information missing?)")
            
            self.logger.info(f"DOCX validation complete: {len(issues)} issues found")
            return len(issues) == 0, issues
            
        except Exception as e:
            issues.append(f"Error validating DOCX: {str(e)}")
            return False, issues
