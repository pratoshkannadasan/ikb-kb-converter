"""
Test Script for Document Extraction
Tests the document extractor and file manager with sample documents.
"""

import sys
import os
import logging

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.document_extractor import DocumentExtractor
from src.file_manager import FileManager
from src.template_generator import TemplateGenerator
import config

def setup_test_logging():
    """Setup logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def test_document_extraction():
    """Test document extraction functionality."""
    logger = setup_test_logging()
    logger.info("🧪 Starting Document Extraction Tests")
    
    try:
        # Initialize components
        extractor = DocumentExtractor()
        file_manager = FileManager()
        template_gen = TemplateGenerator()
        
        # Test 1: Scan for documents
        logger.info("\n📁 Test 1: Scanning for documents...")
        doc_files = file_manager.scan_documents()
        logger.info(f"Found {len(doc_files)} documents")
        
        if not doc_files:
            logger.warning("No documents found in docs/ folder")
            return
        
        # Test 2: Validate files
        logger.info("\n✅ Test 2: Validating files...")
        validation = file_manager.validate_input_files(doc_files)
        logger.info(f"Valid files: {validation['valid_count']}")
        logger.info(f"Invalid files: {validation['invalid_count']}")
        logger.info(f"Total size: {validation['total_size_mb']} MB")
        
        # Test 3: Extract from first few documents
        test_files = doc_files[:3]  # Test with first 3 documents
        logger.info(f"\n🔍 Test 3: Testing extraction with {len(test_files)} documents...")
        
        for i, file_path in enumerate(test_files, 1):
            logger.info(f"\n--- Testing Document {i}: {os.path.basename(file_path)} ---")
            
            try:
                # Test text extraction
                text_content = extractor.extract_text_from_docx(file_path)
                logger.info(f"✓ Text extracted: {len(text_content)} characters")
                
                # Test table extraction
                tables = extractor.extract_tables(file_path)
                logger.info(f"✓ Tables extracted: {len(tables)} tables")
                
                # Test metadata extraction
                metadata = extractor.extract_metadata(file_path)
                logger.info(f"✓ Metadata extracted: {metadata['filename']}")
                logger.info(f"  - File size: {metadata['file_size_mb']} MB")
                logger.info(f"  - Paragraphs: {metadata['paragraph_count']}")
                logger.info(f"  - Tables: {metadata['table_count']}")
                
                # Test complete summary
                summary = extractor.get_document_summary(file_path)
                logger.info(f"✓ Summary created:")
                logger.info(f"  - Total words: {summary['summary_stats']['total_words']}")
                logger.info(f"  - Has content: {summary['summary_stats']['has_content']}")
                
            except Exception as e:
                logger.error(f"❌ Error processing {file_path}: {str(e)}")
        
        # Test 4: Template loading
        logger.info(f"\n📄 Test 4: Testing template functionality...")
        try:
            template_content = template_gen.load_template()
            logger.info(f"✓ Template loaded: {len(template_content)} characters")
            
            # Test template validation
            is_valid, issues = template_gen.validate_markdown(template_content)
            logger.info(f"✓ Template validation: {'Valid' if is_valid else 'Has issues'}")
            if issues:
                logger.info(f"  - Issues found: {len(issues)}")
            
        except Exception as e:
            logger.error(f"❌ Template error: {str(e)}")
        
        logger.info("\n🎉 Document extraction tests completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    test_document_extraction()
