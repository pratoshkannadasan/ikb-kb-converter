"""
Template Generator Module
Generates final markdown files following the IKB template structure.
Enhanced with advanced markdown processing and validation.
Now supports both markdown and DOCX output formats.
"""

import logging
from typing import Dict, Optional, List, Tuple
import os
import re
from pathlib import Path
import json
from .docx_converter import DOCXConverter


class TemplateGenerator:
    """Generate final markdown files following the template with advanced processing."""
    
    def __init__(self, template_path: str = "IKB_Document_Template.md"):
        self.logger = logging.getLogger(__name__)
        self.template_path = template_path
        self.template_sections = {}
        self._load_template_structure()
        
    def _load_template_structure(self):
        """Load and parse template structure for advanced processing."""
        try:
            template = self.load_template()
            self.template_sections = self._parse_template_structure(template)
            self.logger.info(f"Template structure loaded with {len(self.template_sections)} sections")
        except Exception as e:
            self.logger.error(f"Error loading template structure: {str(e)}")
            self.template_sections = {}
    
    def _parse_template_structure(self, template: str) -> Dict:
        """Parse template to understand its structure and sections.
        
        Args:
            template (str): Template content
            
        Returns:
            Dict: Parsed template structure
        """
        sections = {}
        current_section = None
        current_content = []
        
        for line in template.split('\n'):
            # Check for headers
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if header_match:
                # Save previous section
                if current_section:
                    sections[current_section] = {
                        'level': sections.get(current_section, {}).get('level', 1),
                        'content': '\n'.join(current_content),
                        'line': line
                    }
                
                # Start new section
                level = header_match.group(1)
                title = header_match.group(2).strip()
                current_section = title
                sections[current_section] = {
                    'level': len(level),
                    'content': '',
                    'line': line
                }
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section]['content'] = '\n'.join(current_content)
        
        return sections
        
    def load_template(self) -> str:
        """Load IKB template structure.
        
        Returns:
            str: Template content
        """
        try:
            self.logger.info(f"Loading template from: {self.template_path}")
            
            if not os.path.exists(self.template_path):
                raise FileNotFoundError(f"Template file not found: {self.template_path}")
            
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            self.logger.info(f"Successfully loaded template ({len(template_content)} characters)")
            return template_content
            
        except Exception as e:
            self.logger.error(f"Error loading template: {str(e)}")
            raise
        
    def validate_markdown(self, content: str) -> Tuple[bool, List[str]]:
        """Comprehensive markdown validation with detailed feedback.
        
        Args:
            content (str): Markdown content to validate
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_issues)
        """
        try:
            issues = []
            
            if not content or not content.strip():
                issues.append("Content is empty")
                return False, issues
            
            # Check basic structure
            if len(content.strip()) < 200:
                issues.append("Content too short (< 200 characters)")
            
            # Check for headers
            header_count = len(re.findall(r'^#{1,6}\s+.+$', content, re.MULTILINE))
            if header_count < 3:
                issues.append(f"Insufficient headers found ({header_count}, expected at least 3)")
            
            # Check for required sections
            import config
            missing_sections = []
            for section in config.REQUIRED_SECTIONS:
                if section.lower() not in content.lower():
                    missing_sections.append(section)
            
            if missing_sections:
                issues.append(f"Missing required sections: {', '.join(missing_sections)}")
            
            # Check table formatting
            tables = re.findall(r'\|.+\|', content)
            if tables:
                malformed_tables = []
                for i, table_line in enumerate(tables):
                    if table_line.count('|') < 3:  # At least | col1 | col2 |
                        malformed_tables.append(f"Line {i+1}")
                
                if malformed_tables:
                    issues.append(f"Malformed table rows: {', '.join(malformed_tables)}")
            
            # Check list formatting
            list_items = re.findall(r'^[-*+]\s+.+$', content, re.MULTILINE)
            numbered_items = re.findall(r'^\d+\.\s+.+$', content, re.MULTILINE)
            
            if len(list_items) < 3:
                issues.append("Insufficient bullet points (< 3)")
            
            # Check for placeholder content
            placeholders = re.findall(r'\[.*?\]', content)
            concerning_placeholders = [p for p in placeholders if 'not available' in p.lower() or 'not specified' in p.lower()]
            
            if len(concerning_placeholders) > 5:
                issues.append(f"Too many placeholder values ({len(concerning_placeholders)})")
            
            is_valid = len(issues) == 0
            
            self.logger.info(f"Markdown validation: {'PASSED' if is_valid else 'FAILED'} ({len(issues)} issues)")
            return is_valid, issues
            
        except Exception as e:
            self.logger.error(f"Error validating markdown: {str(e)}")
            return False, [f"Validation error: {str(e)}"]
    
    def enhance_markdown_formatting(self, content: str) -> str:
        """Enhance markdown formatting for better readability and consistency.
        
        Args:
            content (str): Raw markdown content
            
        Returns:
            str: Enhanced markdown content
        """
        try:
            self.logger.info("Enhancing markdown formatting")
            
            # Clean up extra whitespace
            content = re.sub(r'\n{3,}', '\n\n', content)
            
            # Ensure proper spacing around headers
            content = re.sub(r'\n(#{1,6}\s+.+)\n', r'\n\n\1\n\n', content)
            
            # Fix table formatting
            content = self._fix_table_formatting(content)
            
            # Enhance list formatting
            content = self._enhance_list_formatting(content)
            
            # Add emphasis to important terms
            content = self._add_emphasis(content)
            
            # Clean up final formatting
            content = content.strip()
            content = re.sub(r'\n{3,}', '\n\n', content)
            
            self.logger.info("Markdown formatting enhanced")
            return content
            
        except Exception as e:
            self.logger.error(f"Error enhancing markdown: {str(e)}")
            return content
    
    def _fix_table_formatting(self, content: str) -> str:
        """Fix table formatting issues."""
        lines = content.split('\n')
        fixed_lines = []
        in_table = False
        
        for line in lines:
            if '|' in line and line.strip():
                # This is likely a table row
                if not in_table:
                    # Add spacing before table
                    if fixed_lines and fixed_lines[-1].strip():
                        fixed_lines.append('')
                    in_table = True
                
                # Clean up table row
                cells = [cell.strip() for cell in line.split('|')]
                if cells[0] == '':
                    cells = cells[1:]  # Remove empty first cell
                if cells and cells[-1] == '':
                    cells = cells[:-1]  # Remove empty last cell
                
                # Rebuild table row with proper spacing
                fixed_line = '| ' + ' | '.join(cells) + ' |'
                fixed_lines.append(fixed_line)
            else:
                if in_table:
                    # Add spacing after table
                    fixed_lines.append('')
                    in_table = False
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _enhance_list_formatting(self, content: str) -> str:
        """Enhance list formatting for consistency."""
        # Standardize bullet points
        content = re.sub(r'^[*+]\s+', '- ', content, flags=re.MULTILINE)
        
        # Ensure proper spacing in numbered lists
        content = re.sub(r'^(\d+)\.\s*', r'\1. ', content, flags=re.MULTILINE)
        
        return content
    
    def _add_emphasis(self, content: str) -> str:
        """Add emphasis to important terms."""
        # Make prices bold
        content = re.sub(r'(RM\s*\d+(?:\.\d{2})?)', r'**\1**', content)
        
        # Make plan names bold in tables
        content = re.sub(r'\|\s*([A-Za-z][\w\s]+(?:Plan|Pass|Package))\s*\|', r'| **\1** |', content)
        
        return content
    
    def save_document(self, content: str, output_path: str) -> str:
        """Write final markdown file.
        
        Args:
            content (str): Final markdown content
            output_path (str): Output file path
            
        Returns:
            str: Path to saved file
        """
        try:
            self.logger.info(f"Saving document to: {output_path}")
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)
            
            # Write content to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"Successfully saved document: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error saving document: {str(e)}")
            raise
    
    def save_document_dual_format(self, content: str, base_filename: str, 
                                  output_format: str = "docx") -> Dict[str, str]:
        """Save document in specified format(s) - markdown, docx, or both.
        
        Args:
            content (str): Markdown content to save
            base_filename (str): Base filename without extension
            output_format (str): "markdown", "docx", or "both"
            
        Returns:
            Dict[str, str]: Dictionary with format as key and file path as value
        """
        try:
            import config
            results = {}
            
            # Create output directories
            if output_format in ["markdown", "both"]:
                os.makedirs(config.MARKDOWN_OUTPUT_FOLDER, exist_ok=True)
            if output_format in ["docx", "both"]:
                os.makedirs(config.DOCX_OUTPUT_FOLDER, exist_ok=True)
            
            # Save markdown format
            if output_format in ["markdown", "both"]:
                md_path = os.path.join(config.MARKDOWN_OUTPUT_FOLDER, f"{base_filename}.md")
                results["markdown"] = self.save_document(content, md_path)
                self.logger.info(f"Markdown saved to: {md_path}")
            
            # Save DOCX format
            if output_format in ["docx", "both"]:
                docx_path = os.path.join(config.DOCX_OUTPUT_FOLDER, f"{base_filename}.docx")
                docx_converter = DOCXConverter()
                
                # Extract title from content for document properties
                title = self._extract_title_from_content(content)
                docx_converter.add_document_properties(title)
                
                # Convert and save
                results["docx"] = docx_converter.convert_markdown_to_docx(content, docx_path)
                self.logger.info(f"DOCX saved to: {docx_path}")
                
                # Validate DOCX output
                is_valid, issues = docx_converter.validate_docx_output(docx_path)
                if not is_valid:
                    self.logger.warning(f"DOCX validation issues: {'; '.join(issues)}")
                else:
                    self.logger.info("DOCX validation passed")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error saving document in dual format: {str(e)}")
            raise
    
    def _extract_title_from_content(self, content: str) -> str:
        """Extract document title from markdown content.
        
        Args:
            content (str): Markdown content
            
        Returns:
            str: Extracted title or default
        """
        lines = content.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
        return "IKB Document"
    
    def validate_and_fix_content(self, content: str) -> Tuple[str, List[str]]:
        """Validate content and apply automatic fixes where possible.
        
        Args:
            content (str): Content to validate and fix
            
        Returns:
            Tuple[str, List[str]]: (fixed_content, remaining_issues)
        """
        try:
            self.logger.info("Validating and fixing content issues")
            
            # First validate to identify issues
            is_valid, issues = self.validate_markdown(content)
            
            if is_valid:
                return content, []
            
            fixed_content = content
            remaining_issues = []
            
            # Fix common issues
            for issue in issues:
                if "too short" in issue.lower():
                    # Add more content structure
                    if len(fixed_content.strip()) < 200:
                        fixed_content += "\n\n## Additional Information\n\nFor more details, please contact customer service."
                
                elif "insufficient headers" in issue.lower():
                    # Add missing headers if content is very minimal
                    if fixed_content.count('#') < 3:
                        fixed_content += "\n\n## Service Details\n\nDetailed information available upon request.\n\n## Support\n\nCustomer support available 24/7."
                
                elif "malformed table" in issue.lower():
                    # Try to fix simple table issues
                    lines = fixed_content.split('\n')
                    for i, line in enumerate(lines):
                        if '|' in line and line.count('|') < 3:
                            # Add missing table separators
                            if not line.strip().startswith('|'):
                                lines[i] = '| ' + line.strip() + ' |'
                    fixed_content = '\n'.join(lines)
                
                else:
                    remaining_issues.append(issue)
            
            # Re-validate after fixes
            is_valid_after_fix, final_issues = self.validate_markdown(fixed_content)
            
            self.logger.info(f"Content validation and fixing complete - Fixed: {len(issues) - len(final_issues)} issues")
            
            return fixed_content, final_issues
            
        except Exception as e:
            self.logger.error(f"Error in validate_and_fix_content: {str(e)}")
            return content, [f"Fix error: {str(e)}"]
