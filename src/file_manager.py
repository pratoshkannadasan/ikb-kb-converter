"""
File Manager Module
Handles all file operations and batch processing.
"""

import logging
from typing import List, Dict, Optional
import os
from pathlib import Path
import glob
import sys

# Import config
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))
import config


class FileManager:
    """Handle file operations and batch processing."""
    
    def __init__(self, input_folder: str = "docs", output_folder: str = "converted_docs"):
        self.logger = logging.getLogger(__name__)
        self.input_folder = input_folder
        self.output_folder = output_folder
        
        # Create output folder if it doesn't exist
        os.makedirs(self.output_folder, exist_ok=True)
        
    def scan_documents(self) -> List[str]:
        """Find all supported documents in input folder.
        
        Returns:
            List[str]: List of document file paths
        """
        try:
            self.logger.info(f"Scanning for documents in: {self.input_folder}")
            
            if not os.path.exists(self.input_folder):
                self.logger.warning(f"Input folder does not exist: {self.input_folder}")
                return []
            
            doc_files = []
            
            # Search for all supported file types
            for extension in config.SUPPORTED_EXTENSIONS:
                pattern = os.path.join(self.input_folder, f"*{extension}")
                files = glob.glob(pattern)
                
                self.logger.debug(f"Found {len(files)} {extension} files")
                
                # Filter out temporary files (starting with ~$)
                for file_path in files:
                    filename = os.path.basename(file_path)
                    if not filename.startswith('~$'):
                        doc_files.append(os.path.abspath(file_path))
            
            self.logger.info(f"Found {len(doc_files)} total document files")
            return sorted(doc_files)
            
        except Exception as e:
            self.logger.error(f"Error scanning documents: {str(e)}")
            raise
        
    def batch_process(self, file_list: List[str]) -> List[Dict]:
        """Process multiple documents.
        
        Args:
            file_list (List[str]): List of file paths to process
            
        Returns:
            List[Dict]: Processing results
        """
        try:
            self.logger.info(f"Starting batch processing of {len(file_list)} files")
            results = []
            
            for i, file_path in enumerate(file_list, 1):
                self.logger.info(f"Processing file {i}/{len(file_list)}: {os.path.basename(file_path)}")
                
                try:
                    # Process individual file
                    result = {
                        'file_path': file_path,
                        'filename': os.path.basename(file_path),
                        'index': i,
                        'status': 'processing',
                        'error': None,
                        'processing_time': None,
                        'output_path': None
                    }
                    
                    import time
                    start_time = time.time()
                    
                    # This will be integrated with the main pipeline
                    # For now, just record the file info
                    result['status'] = 'queued'
                    result['processing_time'] = time.time() - start_time
                    
                    results.append(result)
                    
                except Exception as e:
                    self.logger.error(f"Error processing {file_path}: {str(e)}")
                    result = {
                        'file_path': file_path,
                        'filename': os.path.basename(file_path),
                        'index': i,
                        'status': 'error',
                        'error': str(e)
                    }
                    results.append(result)
            
            self.logger.info(f"Batch processing completed. {len(results)} files processed")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in batch processing: {str(e)}")
            raise
        
    def manage_output(self, filename: str, content: str) -> str:
        """Organize converted files.
        
        Args:
            filename (str): Original filename
            content (str): Converted content
            
        Returns:
            str: Output file path
        """
        try:
            # Create output filename
            base_name = Path(filename).stem
            output_filename = f"converted_{base_name}.md"
            output_path = os.path.join(self.output_folder, output_filename)
            
            self.logger.info(f"Saving converted content to: {output_path}")
            
            # Write content to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"Successfully saved file: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error managing output for {filename}: {str(e)}")
            raise
        
    def cleanup_temp(self) -> None:
        """Clean temporary files.
        """
        try:
            # Clean up any temporary files or directories
            temp_patterns = [
                "*.tmp",
                "*.temp",
                "*~",
                ".DS_Store",
                "Thumbs.db"
            ]
            
            for pattern in temp_patterns:
                temp_files = glob.glob(os.path.join(self.output_folder, pattern))
                for temp_file in temp_files:
                    try:
                        os.remove(temp_file)
                        self.logger.info(f"Removed temporary file: {temp_file}")
                    except Exception as e:
                        self.logger.warning(f"Could not remove {temp_file}: {str(e)}")
            
            self.logger.info("Temporary file cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
    
    def get_file_stats(self, file_path: str) -> Dict:
        """Get statistics about a file.
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            Dict: File statistics
        """
        try:
            stat = os.stat(file_path)
            return {
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'is_readable': os.access(file_path, os.R_OK),
                'exists': os.path.exists(file_path)
            }
        except Exception as e:
            self.logger.error(f"Error getting file stats for {file_path}: {str(e)}")
            return {}
    
    def validate_input_files(self, file_list: List[str]) -> Dict:
        """Validate input files before processing.
        
        Args:
            file_list (List[str]): List of file paths to validate
            
        Returns:
            Dict: Validation results
        """
        try:
            self.logger.info(f"Validating {len(file_list)} input files")
            
            valid_files = []
            invalid_files = []
            total_size = 0
            
            for file_path in file_list:
                try:
                    # Check if file exists and is readable
                    if not os.path.exists(file_path):
                        invalid_files.append({
                            'file': file_path,
                            'reason': 'File does not exist'
                        })
                        continue
                    
                    if not os.access(file_path, os.R_OK):
                        invalid_files.append({
                            'file': file_path,
                            'reason': 'File not readable'
                        })
                        continue
                    
                    # Check file extension
                    file_extension = os.path.splitext(file_path)[1].lower()
                    if file_extension not in config.SUPPORTED_EXTENSIONS:
                        invalid_files.append({
                            'file': file_path,
                            'reason': f'Unsupported file type: {file_extension}'
                        })
                        continue
                    
                    # Check file size
                    file_stats = self.get_file_stats(file_path)
                    if file_stats.get('size_mb', 0) >= config.MAX_FILE_SIZE_MB:
                        invalid_files.append({
                            'file': file_path,
                            'reason': f'File too large ({file_stats.get("size_mb", 0):.1f}MB > {config.MAX_FILE_SIZE_MB}MB)'
                        })
                        continue
                    
                    # File-specific validation
                    if file_extension == '.pdf':
                        # Basic PDF validation
                        try:
                            import PyPDF2
                            with open(file_path, 'rb') as f:
                                pdf_reader = PyPDF2.PdfReader(f)
                                if len(pdf_reader.pages) == 0:
                                    invalid_files.append({
                                        'file': file_path,
                                        'reason': 'PDF has no pages'
                                    })
                                    continue
                        except Exception as e:
                            invalid_files.append({
                                'file': file_path,
                                'reason': f'Invalid PDF: {str(e)}'
                            })
                            continue
                    
                    elif file_extension == '.docx':
                        # Basic DOCX validation (existing logic)
                        try:
                            from docx import Document
                            doc = Document(file_path)
                            # Just try to access paragraphs to validate
                            _ = len(doc.paragraphs)
                        except Exception as e:
                            invalid_files.append({
                                'file': file_path,
                                'reason': f'Invalid DOCX: {str(e)}'
                            })
                            continue
                    
                    # If we get here, file is valid
                    valid_files.append(file_path)
                    total_size += file_stats.get('size_bytes', 0)
                    
                except Exception as e:
                    invalid_files.append({
                        'file': file_path,
                        'reason': f'Validation error: {str(e)}'
                    })
            
            validation_result = {
                'total_files': len(file_list),
                'valid_files': valid_files,
                'invalid_files': invalid_files,
                'valid_count': len(valid_files),
                'invalid_count': len(invalid_files),
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
            
            self.logger.info(f"Validation complete: {len(valid_files)} valid, {len(invalid_files)} invalid")
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Error during file validation: {str(e)}")
            raise
