"""
Document Extractor Module
Handles extraction of text, tables, and metadata from Word documents and PDFs.
"""

import logging
from docx import Document
from typing import Dict, List, Optional
import os
import re

# PDF processing imports
import PyPDF2
import pdfplumber

# Import config for PDF settings
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))
import config


class DocumentExtractor:
    """Extract content from Word documents and PDFs for processing."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract all text content from Word document.
        
        Args:
            file_path (str): Path to the Word document
            
        Returns:
            str: Extracted text content
        """
        try:
            self.logger.info(f"Extracting text from: {file_path}")
            doc = Document(file_path)
            full_text = []
            
            # Extract paragraph text
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    full_text.append(paragraph.text.strip())
            
            # Extract text from tables
            for table in doc.tables:
                table_text = self._extract_table_text(table)
                if table_text:
                    full_text.append(table_text)
            
            extracted_text = "\n".join(full_text)
            self.logger.info(f"Successfully extracted {len(extracted_text)} characters")
            return extracted_text
            
        except Exception as e:
            self.logger.error(f"Error extracting text from {file_path}: {str(e)}")
            raise
        
    # Legacy methods removed - use extract_tables_from_document() and extract_metadata_from_document() instead
    
    def extract_hyperlinks_from_docx(self, file_path: str) -> List[Dict]:
        """Extract all hyperlinks from Word document including those in tables.
        
        Args:
            file_path (str): Path to the Word document
            
        Returns:
            List[Dict]: List of hyperlinks with text, URL, and location info
        """
        try:
            self.logger.info(f"Extracting hyperlinks from: {file_path}")
            
            # Debug: Check if hyperlinks exist (commented out for production)
            # self.debug_hyperlinks(file_path)
            
            # Try the xpath-based method first
            doc = Document(file_path)
            hyperlinks = []
            
            # Extract hyperlinks from paragraphs
            for para_idx, paragraph in enumerate(doc.paragraphs):
                para_links = self._extract_links_from_paragraph(paragraph, f"paragraph_{para_idx}")
                hyperlinks.extend(para_links)
            
            # Extract hyperlinks from tables
            for table_idx, table in enumerate(doc.tables):
                table_links = self._extract_links_from_table(table, f"table_{table_idx}")
                hyperlinks.extend(table_links)
            
            # If no hyperlinks found, try XML-based extraction as fallback
            if len(hyperlinks) == 0:
                self.logger.info("No hyperlinks found with xpath method, trying XML-based extraction...")
                hyperlinks = self._extract_hyperlinks_xml_fallback(file_path)
            
            self.logger.info(f"Successfully extracted {len(hyperlinks)} hyperlinks")
            return hyperlinks
            
        except Exception as e:
            self.logger.error(f"Error extracting hyperlinks from {file_path}: {str(e)}")
            return []

    # DEBUG METHOD - Commented out for production use
    # def debug_hyperlinks(self, file_path: str):
    #     """Debug method to check if hyperlinks exist in the document."""
    #     try:
    #         import zipfile
    #         import xml.etree.ElementTree as ET
    #         
    #         with zipfile.ZipFile(file_path, 'r') as docx_zip:
    #             # Check relationships file
    #             try:
    #                 rels_xml = docx_zip.read('word/_rels/document.xml.rels')
    #                 rels_root = ET.fromstring(rels_xml)
    #                 
    #                 hyperlink_rels = []
    #                 for rel in rels_root.findall('.//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'):
    #                     rel_type = rel.get('Type')
    #                     if rel_type and 'hyperlink' in rel_type.lower():
    #                         hyperlink_rels.append({
    #                             'id': rel.get('Id'),
    #                             'target': rel.get('Target'),
    #                             'type': rel_type
    #                         })
    #                 
    #                 self.logger.info(f"DEBUG: Found {len(hyperlink_rels)} hyperlink relationships")
    #                 for rel in hyperlink_rels:
    #                     self.logger.info(f"  - {rel['id']}: {rel['target']}")
    #                 
    #             except Exception as e:
    #                 self.logger.info(f"DEBUG: No relationships file or error: {str(e)}")
    #             
    #             # Check document content
    #             try:
    #                 doc_xml = docx_zip.read('word/document.xml')
    #                 content = doc_xml.decode('utf-8')
    #                 
    #                 hyperlink_count = content.count('w:hyperlink')
    #                 self.logger.info(f"DEBUG: Found {hyperlink_count} hyperlink elements in document XML")
    #                 
    #                 if hyperlink_count > 0:
    #                     # Show first few hyperlink elements
    #                     import re
    #                     hyperlink_matches = re.findall(r'<w:hyperlink[^>]*>.*?</w:hyperlink>', content, re.DOTALL)
    #                     for i, match in enumerate(hyperlink_matches[:3]):
    #                         self.logger.info(f"  Hyperlink {i+1}: {match[:100]}...")
    #                 
    #             except Exception as e:
    #                 self.logger.info(f"DEBUG: Error reading document XML: {str(e)}")
    #                 
    #     except Exception as e:
    #         self.logger.error(f"DEBUG: Error opening document: {str(e)}")

    def _extract_hyperlinks_xml_fallback(self, file_path: str) -> List[Dict]:
        """Fallback hyperlink extraction using direct XML parsing."""
        try:
            self.logger.info("Using XML-based hyperlink extraction fallback")
            
            import zipfile
            import xml.etree.ElementTree as ET
            
            hyperlinks = []
            
            with zipfile.ZipFile(file_path, 'r') as docx_zip:
                # Read document relationships
                relationships = {}
                try:
                    rels_xml = docx_zip.read('word/_rels/document.xml.rels')
                    rels_root = ET.fromstring(rels_xml)
                    
                    for rel in rels_root.findall('.//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'):
                        rel_id = rel.get('Id')
                        target = rel.get('Target')
                        rel_type = rel.get('Type')
                        
                        if rel_type == 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink':
                            relationships[rel_id] = target
                            
                except Exception as e:
                    self.logger.warning(f"Could not read relationships: {str(e)}")
                
                # Read main document
                try:
                    doc_xml = docx_zip.read('word/document.xml')
                    doc_root = ET.fromstring(doc_xml)
                    
                    # Find all hyperlinks in the document
                    namespaces = {
                        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
                        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
                    }
                    
                    # Find hyperlinks in paragraphs
                    for para_idx, para in enumerate(doc_root.findall('.//w:p', namespaces)):
                        para_links = self._extract_links_from_xml_paragraph(para, f"paragraph_{para_idx}", relationships, namespaces)
                        hyperlinks.extend(para_links)
                    
                    # Find hyperlinks in tables
                    for table_idx, table in enumerate(doc_root.findall('.//w:tbl', namespaces)):
                        table_links = self._extract_links_from_xml_table(table, f"table_{table_idx}", relationships, namespaces)
                        hyperlinks.extend(table_links)
                        
                except Exception as e:
                    self.logger.warning(f"Could not read document XML: {str(e)}")
            
            self.logger.info(f"XML fallback extraction found {len(hyperlinks)} hyperlinks")
            return hyperlinks
            
        except Exception as e:
            self.logger.error(f"XML fallback extraction failed: {str(e)}")
            return []

    def _extract_links_from_xml_paragraph(self, para_xml, location: str, relationships: dict, namespaces: dict) -> List[Dict]:
        """Extract links from XML paragraph element."""
        links = []
        
        try:
            for hyperlink in para_xml.findall('.//w:hyperlink', namespaces):
                rel_id = hyperlink.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                
                if rel_id and rel_id in relationships:
                    url = relationships[rel_id]
                    
                    # Get text content
                    text_elements = hyperlink.findall('.//w:t', namespaces)
                    link_text = ''.join([elem.text or '' for elem in text_elements])
                    
                    if link_text or url:
                        links.append({
                            'text': link_text or url,
                            'url': url,
                            'location': location,
                            'type': 'paragraph'
                        })
                        self.logger.debug(f"XML: Found hyperlink: '{link_text}' -> {url}")
        
        except Exception as e:
            self.logger.warning(f"Error extracting links from XML paragraph: {str(e)}")
        
        return links

    def _extract_links_from_xml_table(self, table_xml, location: str, relationships: dict, namespaces: dict) -> List[Dict]:
        """Extract links from XML table element."""
        links = []
        
        try:
            for row_idx, row in enumerate(table_xml.findall('.//w:tr', namespaces)):
                for col_idx, cell in enumerate(row.findall('.//w:tc', namespaces)):
                    cell_location = f"{location}_row_{row_idx}_col_{col_idx}"
                    
                    for para in cell.findall('.//w:p', namespaces):
                        para_links = self._extract_links_from_xml_paragraph(para, cell_location, relationships, namespaces)
                        # Update type to indicate table location
                        for link in para_links:
                            link['type'] = 'table_cell'
                            link['row'] = row_idx
                            link['column'] = col_idx
                        links.extend(para_links)
        
        except Exception as e:
            self.logger.warning(f"Error extracting links from XML table: {str(e)}")
        
        return links

    def _extract_links_from_paragraph(self, paragraph, location: str) -> List[Dict]:
        """Extract hyperlinks from a paragraph with enhanced error handling."""
        links = []
        
        try:
            # Get the paragraph's XML element
            paragraph_xml = paragraph._element
            
            if not paragraph_xml:
                self.logger.debug(f"No XML element found for paragraph at {location}")
                return links
            
            # Define namespace map for findall
            namespace_map = {
                'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
                'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
            }
            
            # Find hyperlink elements using findall with namespace prefixes
            hyperlink_elements = paragraph_xml.findall('.//w:hyperlink', namespace_map)
            self.logger.debug(f"Found {len(hyperlink_elements)} hyperlink elements in paragraph at {location}")
            
            for i, hyperlink_elem in enumerate(hyperlink_elements):
                try:
                    # Get relationship ID with multiple possible attribute names
                    rel_id = (hyperlink_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id') or 
                             hyperlink_elem.get('r:id') or
                             hyperlink_elem.get('id'))
                    
                    if not rel_id:
                        # Try to get external link directly
                        external_link = hyperlink_elem.get('w:anchor')
                        if external_link:
                            # Get the text content
                            text_elements = hyperlink_elem.findall('.//w:t', namespace_map)
                            link_text = ''.join([elem.text or '' for elem in text_elements])
                            
                            links.append({
                                'text': link_text or external_link,
                                'url': f"#{external_link}",  # Internal anchor link
                                'location': location,
                                'type': 'paragraph'
                            })
                            self.logger.debug(f"Found anchor hyperlink: '{link_text}' -> #{external_link}")
                        else:
                            self.logger.debug(f"No relationship ID found for hyperlink {i} at {location}")
                        continue
                    
                    # Get the actual URL from document relationships
                    url = self._get_url_from_relationship(paragraph.part, rel_id)
                    
                    if url:
                        # Get the text content of the hyperlink
                        text_elements = hyperlink_elem.findall('.//w:t', namespace_map)
                        link_text = ''.join([elem.text or '' for elem in text_elements])
                        
                        # Validate the extracted link
                        if self._validate_hyperlink(link_text, url):
                            links.append({
                                'text': link_text or url,
                                'url': url,
                                'location': location,
                                'type': 'paragraph',
                                'rel_id': rel_id  # Add rel_id for debugging
                            })
                            self.logger.debug(f"Successfully extracted hyperlink: '{link_text}' -> {url}")
                        else:
                            self.logger.debug(f"Invalid hyperlink skipped: '{link_text}' -> {url}")
                    else:
                        self.logger.debug(f"No URL found for relationship ID {rel_id} at {location}")
                        
                except Exception as link_error:
                    self.logger.warning(f"Error processing hyperlink {i} at {location}: {str(link_error)}")
                    continue
        
        except Exception as e:
            self.logger.warning(f"Error extracting links from paragraph at {location}: {str(e)}")
        
        return links

    def _extract_links_from_table(self, table, location: str) -> List[Dict]:
        """Extract hyperlinks from table cells."""
        links = []
        
        try:
            for row_idx, row in enumerate(table.rows):
                for col_idx, cell in enumerate(row.cells):
                    cell_location = f"{location}_row_{row_idx}_col_{col_idx}"
                    
                    for paragraph in cell.paragraphs:
                        para_links = self._extract_links_from_paragraph(paragraph, cell_location)
                        # Update type to indicate table location
                        for link in para_links:
                            link['type'] = 'table_cell'
                            link['row'] = row_idx
                            link['column'] = col_idx
                        links.extend(para_links)
        
        except Exception as e:
            self.logger.warning(f"Error extracting links from table: {str(e)}")
        
        return links

    def _get_url_from_relationship(self, part, rel_id: str) -> str:
        """Get URL from document relationship ID with enhanced error handling."""
        try:
            if not part or not hasattr(part, 'rels'):
                self.logger.debug(f"Invalid part object for relationship {rel_id}")
                return ""
                
            if rel_id in part.rels:
                relationship = part.rels[rel_id]
                url = getattr(relationship, 'target_ref', '') or getattr(relationship, '_target', '')
                
                if url:
                    self.logger.debug(f"Successfully resolved relationship {rel_id} -> {url}")
                    return url
                else:
                    self.logger.debug(f"Empty URL for relationship {rel_id}")
                    return ""
            else:
                # List available relationship IDs for debugging
                available_rels = list(part.rels.keys()) if hasattr(part, 'rels') else []
                self.logger.debug(f"Relationship ID {rel_id} not found. Available: {available_rels[:5]}")
                return ""
        except (KeyError, AttributeError) as e:
            self.logger.warning(f"Error getting URL from relationship {rel_id}: {str(e)}")
            return ""
    
    def _validate_hyperlink(self, text: str, url: str) -> bool:
        """Validate extracted hyperlink data."""
        try:
            # Basic validation checks
            if not url or not url.strip():
                return False
                
            # Skip obviously invalid URLs
            if url in ['#', '', 'None', 'null']:
                return False
                
            # Accept various URL formats
            import re
            valid_patterns = [
                r'^https?://',      # HTTP/HTTPS URLs
                r'^mailto:',        # Email links
                r'^tel:',          # Phone links
                r'^#',             # Anchor links
                r'^ftp://',        # FTP links
                r'^file://',       # File links
                r'^\w+://',        # Other protocols
            ]
            
            url_lower = url.lower()
            if any(re.match(pattern, url_lower) for pattern in valid_patterns):
                return True
                
            # Accept relative URLs or paths
            if '/' in url or '\\' in url:
                return True
                
            # Accept what looks like a domain name
            if '.' in url and not url.startswith('.'):
                return True
                
            self.logger.debug(f"URL failed validation: {url}")
            return False
            
        except Exception as e:
            self.logger.debug(f"Error validating hyperlink '{text}' -> '{url}': {str(e)}")
            return False

    def extract_text_with_links(self, file_path: str) -> Dict:
        """Extract text content while preserving hyperlink information."""
        try:
            # Get regular text content
            text_content = self.extract_text_from_docx(file_path)
            
            # Get hyperlinks
            hyperlinks = self.extract_hyperlinks_from_docx(file_path)
            
            # Create enhanced text with link annotations
            enhanced_text = self._annotate_text_with_links(text_content, hyperlinks)
            
            return {
                'text_content': text_content,
                'enhanced_text': enhanced_text,
                'hyperlinks': hyperlinks,
                'link_count': len(hyperlinks)
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting text with links: {str(e)}")
            raise

    def _annotate_text_with_links(self, text: str, hyperlinks: List[Dict]) -> str:
        """Annotate text with markdown-style links."""
        enhanced_text = text
        
        self.logger.debug(f"Annotating text with {len(hyperlinks)} hyperlinks")
        
        # Sort links by text length (longest first) to avoid partial replacements
        sorted_links = sorted(hyperlinks, key=lambda x: len(x.get('text', '')), reverse=True)
        
        links_added = 0
        for i, link in enumerate(sorted_links):
            link_text = link.get('text', '').strip()
            link_url = link.get('url', '').strip()
            
            self.logger.debug(f"Processing hyperlink {i+1}: text='{link_text}', url='{link_url}'")
            
            if not link_text or not link_url:
                self.logger.debug(f"Skipping hyperlink {i+1}: missing text or URL")
                continue
            
            # Try exact match first
            if link_text in enhanced_text:
                markdown_link = f"[{link_text}]({link_url})"
                enhanced_text = enhanced_text.replace(link_text, markdown_link, 1)
                links_added += 1
                self.logger.debug(f"Added hyperlink {i+1} (exact match): '{link_text}' -> {link_url}")
                continue
            
            # Try case-insensitive match
            import re
            pattern = re.escape(link_text)
            match = re.search(pattern, enhanced_text, re.IGNORECASE)
            if match:
                actual_text = match.group(0)
                markdown_link = f"[{actual_text}]({link_url})"
                enhanced_text = enhanced_text.replace(actual_text, markdown_link, 1)
                links_added += 1
                self.logger.debug(f"Added hyperlink {i+1} (case-insensitive): '{actual_text}' -> {link_url}")
                continue
            
            # Try fuzzy match for links with minor differences
            # Look for text that contains most of the link text words
            if len(link_text.split()) > 1:
                words = link_text.split()
                # Try to find text that contains at least 70% of the words
                min_words = max(1, int(len(words) * 0.7))
                pattern_words = []
                
                for word in words[:min_words]:
                    pattern_words.append(re.escape(word))
                
                fuzzy_pattern = r'\b' + r'.{0,10}\b'.join(pattern_words) + r'.{0,20}\b'
                fuzzy_match = re.search(fuzzy_pattern, enhanced_text, re.IGNORECASE)
                
                if fuzzy_match:
                    matched_text = fuzzy_match.group(0).strip()
                    # Only use if the match is reasonable length
                    if len(matched_text) <= len(link_text) * 2:
                        markdown_link = f"[{matched_text}]({link_url})"
                        enhanced_text = enhanced_text.replace(matched_text, markdown_link, 1)
                        links_added += 1
                        self.logger.debug(f"Added hyperlink {i+1} (fuzzy match): '{matched_text}' -> {link_url}")
                        continue
            
            # If no match found, add the link at the end of the text (fallback)
            fallback_link = f"\n\n[{link_text}]({link_url})"
            enhanced_text += fallback_link
            links_added += 1
            self.logger.debug(f"Added hyperlink {i+1} (fallback): '{link_text}' -> {link_url}")
        
        self.logger.info(f"Successfully added {links_added}/{len(hyperlinks)} hyperlinks to enhanced text")
        return enhanced_text
        
    def clean_text(self, text: str) -> str:
        """Remove formatting artifacts and clean text while preserving hyperlinks.
        
        Args:
            text (str): Raw text content (may contain markdown hyperlinks)
            
        Returns:
            str: Cleaned text with preserved hyperlinks
        """
        if not text:
            return ""
        
        import re
        
        # First, extract and temporarily replace hyperlinks to protect them during cleaning
        hyperlink_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        hyperlinks = []
        
        def hyperlink_replacer(match):
            hyperlinks.append(match.group(0))  # Store the full hyperlink
            return f"__HYPERLINK_PLACEHOLDER_{len(hyperlinks)-1}__"
        
        # Replace hyperlinks with placeholders
        text_with_placeholders = re.sub(hyperlink_pattern, hyperlink_replacer, text)
        
        # Remove excessive whitespace
        cleaned = ' '.join(text_with_placeholders.split())
        
        # Remove common formatting artifacts
        cleaned = cleaned.replace('\x0b', ' ')  # Vertical tab
        cleaned = cleaned.replace('\x0c', ' ')  # Form feed
        cleaned = cleaned.replace('\xa0', ' ')  # Non-breaking space
        
        # Remove multiple consecutive spaces (but preserve single spaces in hyperlinks)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Restore hyperlinks from placeholders
        for i, hyperlink in enumerate(hyperlinks):
            placeholder = f"__HYPERLINK_PLACEHOLDER_{i}__"
            cleaned = cleaned.replace(placeholder, hyperlink)
        
        # Remove leading/trailing whitespace
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _extract_table_text(self, table) -> str:
        """Helper method to extract text from a table.
        
        Args:
            table: Word document table object
            
        Returns:
            str: Formatted table text
        """
        table_lines = []
        
        for row in table.rows:
            row_cells = []
            for cell in row.cells:
                cell_text = self.clean_text(cell.text)
                row_cells.append(cell_text)
            
            # Join cells with pipe separator for markdown-like format
            table_lines.append(" | ".join(row_cells))
        
        return "\n".join(table_lines)
    
    # PDF Processing Methods
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract all text content from PDF document.
        
        Args:
            file_path (str): Path to the PDF document
            
        Returns:
            str: Extracted text content
        """
        try:
            self.logger.info(f"Extracting text from PDF: {file_path}")
            
            # Use pdfplumber for better text extraction (especially tables)
            full_text = []
            
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    self.logger.debug(f"Processing page {page_num}/{len(pdf.pages)}")
                    
                    # Extract text from page
                    page_text = page.extract_text()
                    if page_text:
                        full_text.append(page_text.strip())
                    
                    # Extract tables if enabled
                    if config.PDF_PROCESSING_SETTINGS.get('extract_tables', True):
                        tables = page.extract_tables()
                        for table in tables:
                            if table:
                                table_text = self._format_pdf_table(table)
                                if table_text:
                                    full_text.append(table_text)
            
            extracted_text = "\n\n".join(full_text)
            self.logger.info(f"Successfully extracted {len(extracted_text)} characters from PDF")
            return extracted_text
            
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            # Fallback to PyPDF2 if pdfplumber fails
            return self._extract_text_fallback_pypdf2(file_path)
    
    def _extract_text_fallback_pypdf2(self, file_path: str) -> str:
        """Fallback PDF text extraction using PyPDF2."""
        try:
            self.logger.info("Using PyPDF2 fallback for PDF text extraction")
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                full_text = []
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        full_text.append(page_text.strip())
                
                extracted_text = "\n\n".join(full_text)
                self.logger.info(f"PyPDF2 fallback extracted {len(extracted_text)} characters")
                return extracted_text
                
        except Exception as e:
            self.logger.error(f"PyPDF2 fallback also failed: {str(e)}")
            raise
    
    def _format_pdf_table(self, table: list) -> str:
        """Format extracted PDF table as markdown-style text."""
        if not table or not any(table):
            return ""
        
        formatted_rows = []
        for row in table:
            if row and any(cell for cell in row if cell):
                # Clean and format cells
                clean_row = [str(cell).strip() if cell else "" for cell in row]
                formatted_rows.append(" | ".join(clean_row))
        
        return "\n".join(formatted_rows) if formatted_rows else ""
    
    def extract_tables_from_pdf(self, file_path: str) -> List[Dict]:
        """Extract tables from PDF document.
        
        Args:
            file_path (str): Path to the PDF document
            
        Returns:
            List[Dict]: List of table data
        """
        try:
            self.logger.info(f"Extracting tables from PDF: {file_path}")
            
            tables_data = []
            
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    tables = page.extract_tables()
                    
                    for table_num, table in enumerate(tables, 1):
                        if table and any(any(cell for cell in row if cell) for row in table):
                            table_data = {
                                'page': page_num,
                                'table_index': table_num,
                                'headers': table[0] if table else [],
                                'rows': table[1:] if len(table) > 1 else [],
                                'raw_data': table
                            }
                            tables_data.append(table_data)
            
            self.logger.info(f"Successfully extracted {len(tables_data)} tables from PDF")
            return tables_data
            
        except Exception as e:
            self.logger.error(f"Error extracting tables from PDF {file_path}: {str(e)}")
            return []
    
    def extract_metadata_from_pdf(self, file_path: str) -> Dict:
        """Extract metadata from PDF document.
        
        Args:
            file_path (str): Path to the PDF document
            
        Returns:
            Dict: PDF metadata
        """
        try:
            self.logger.info(f"Extracting metadata from PDF: {file_path}")
            
            metadata = {
                'filename': os.path.basename(file_path),
                'file_size': os.path.getsize(file_path),
                'file_type': 'PDF',
                'pages': 0,
                'title': '',
                'author': '',
                'subject': '',
                'creator': '',
                'producer': '',
                'creation_date': '',
                'modification_date': ''
            }
            
            # Use PyPDF2 for metadata extraction
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata['pages'] = len(pdf_reader.pages)
                
                if pdf_reader.metadata:
                    pdf_metadata = pdf_reader.metadata
                    metadata.update({
                        'title': str(pdf_metadata.get('/Title', '')),
                        'author': str(pdf_metadata.get('/Author', '')),
                        'subject': str(pdf_metadata.get('/Subject', '')),
                        'creator': str(pdf_metadata.get('/Creator', '')),
                        'producer': str(pdf_metadata.get('/Producer', '')),
                        'creation_date': str(pdf_metadata.get('/CreationDate', '')),
                        'modification_date': str(pdf_metadata.get('/ModDate', ''))
                    })
            
            self.logger.info("Successfully extracted PDF metadata")
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error extracting PDF metadata from {file_path}: {str(e)}")
            return metadata  # Return basic metadata even if extraction fails
    
    # Unified Document Processing Methods
    def extract_text_from_document(self, file_path: str) -> str:
        """Extract text from document (DOCX or PDF).
        
        Args:
            file_path (str): Path to the document
            
        Returns:
            str: Extracted text content
        """
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.docx':
            return self.extract_text_from_docx(file_path)
        elif file_extension == '.pdf':
            return self.extract_text_from_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    def extract_tables_from_document(self, file_path: str) -> List[Dict]:
        """Extract tables from document (DOCX or PDF).
        
        Args:
            file_path (str): Path to the document
            
        Returns:
            List[Dict]: List of table data
        """
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.docx':
            # Implement DOCX table extraction directly
            try:
                self.logger.info(f"Extracting tables from DOCX: {file_path}")
                doc = Document(file_path)
                tables_data = []
                
                for table_idx, table in enumerate(doc.tables):
                    if table.rows:
                        # Extract table headers (first row)
                        headers = []
                        if table.rows:
                            header_row = table.rows[0]
                            for cell in header_row.cells:
                                headers.append(cell.text.strip())
                        
                        # Extract table data (remaining rows)
                        rows = []
                        for row in table.rows[1:]:
                            row_data = []
                            for cell in row.cells:
                                row_data.append(cell.text.strip())
                            if any(row_data):  # Only add non-empty rows
                                rows.append(row_data)
                        
                        # Create table data structure
                        table_data = {
                            'table_index': table_idx,
                            'headers': headers,
                            'rows': rows,
                            'total_rows': len(rows),
                            'total_columns': len(headers) if headers else (len(rows[0]) if rows else 0)
                        }
                        tables_data.append(table_data)
                
                self.logger.info(f"Successfully extracted {len(tables_data)} tables from DOCX")
                return tables_data
                
            except Exception as e:
                self.logger.error(f"Error extracting tables from DOCX {file_path}: {str(e)}")
                return []
        elif file_extension == '.pdf':
            return self.extract_tables_from_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    def extract_metadata_from_document(self, file_path: str) -> Dict:
        """Extract metadata from document (DOCX or PDF).
        
        Args:
            file_path (str): Path to the document
            
        Returns:
            Dict: Document metadata
        """
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.docx':
            # Implement DOCX metadata extraction directly
            try:
                self.logger.info(f"Extracting metadata from DOCX: {file_path}")
                doc = Document(file_path)
                
                metadata = {
                    'filename': os.path.basename(file_path),
                    'file_size': os.path.getsize(file_path),
                    'file_type': 'DOCX',
                    'paragraphs': len(doc.paragraphs),
                    'tables': len(doc.tables),
                    'title': '',
                    'author': '',
                    'subject': '',
                    'created': '',
                    'modified': '',
                    'last_modified_by': ''
                }
                
                # Extract core properties if available
                if hasattr(doc, 'core_properties') and doc.core_properties:
                    core_props = doc.core_properties
                    metadata.update({
                        'title': getattr(core_props, 'title', '') or '',
                        'author': getattr(core_props, 'author', '') or '',
                        'subject': getattr(core_props, 'subject', '') or '',
                        'created': str(getattr(core_props, 'created', '') or ''),
                        'modified': str(getattr(core_props, 'modified', '') or ''),
                        'last_modified_by': getattr(core_props, 'last_modified_by', '') or ''
                    })
                
                self.logger.info("Successfully extracted DOCX metadata")
                return metadata
                
            except Exception as e:
                self.logger.error(f"Error extracting metadata from DOCX {file_path}: {str(e)}")
                # Return basic metadata even if extraction fails
                return {
                    'filename': os.path.basename(file_path),
                    'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                    'file_type': 'DOCX',
                    'paragraphs': 0,
                    'tables': 0,
                    'title': '',
                    'author': '',
                    'subject': '',
                    'created': '',
                    'modified': '',
                    'last_modified_by': ''
                }
        elif file_extension == '.pdf':
            return self.extract_metadata_from_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    def get_document_summary(self, file_path: str) -> Dict:
        """Get a comprehensive summary of the document (DOCX or PDF).
        
        Args:
            file_path (str): Path to the document
            
        Returns:
            Dict: Complete document summary
        """
        try:
            self.logger.info(f"Creating document summary for: {file_path}")
            
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.docx':
                # Enhanced extraction with links for DOCX
                text_with_links = self.extract_text_with_links(file_path)
                raw_text_content = text_with_links['text_content']  # Original text without links
                enhanced_text_content = text_with_links['enhanced_text']  # Text with markdown links
                hyperlinks = text_with_links['hyperlinks']
                
                # Use enhanced text as the main content and clean it (preserving hyperlinks)
                text_content = enhanced_text_content
                cleaned_text = self.clean_text(enhanced_text_content)  # This now preserves hyperlinks
            else:
                # Regular extraction for PDF (could be enhanced later)
                raw_text_content = self.extract_text_from_document(file_path)
                text_content = raw_text_content
                cleaned_text = self.clean_text(raw_text_content)
                hyperlinks = []
            
            tables_data = self.extract_tables_from_document(file_path)
            metadata = self.extract_metadata_from_document(file_path)
            
            summary = {
                'metadata': metadata,
                'text_content': text_content,  # Now contains hyperlinks for DOCX files
                'cleaned_text': cleaned_text,  # Now preserves hyperlinks during cleaning
                'raw_text_content': raw_text_content if file_extension == '.docx' else text_content,  # Original text without links
                'tables': tables_data,
                'hyperlinks': hyperlinks,  # Add hyperlinks to summary
                'summary_stats': {
                    'total_characters': len(text_content),
                    'total_words': len(text_content.split()) if text_content else 0,
                    'total_tables': len(tables_data),
                    'total_links': len(hyperlinks),  # Add link count
                    'has_content': bool(text_content.strip()),
                    'file_type': metadata.get('file_type', 'Unknown')
                }
            }
            
            self.logger.info(f"Successfully created document summary with {len(hyperlinks)} links")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error creating document summary for {file_path}: {str(e)}")
            raise
