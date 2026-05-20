"""
AI Processor Test Script
Tests the AI processing functionality with sample document content.
"""

import sys
import os
import logging

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.document_extractor import DocumentExtractor
from src.ai_processor import AIProcessor
from src.template_generator import TemplateGenerator
from src.file_manager import FileManager
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

def test_ai_processing():
    """Test AI processing functionality."""
    logger = setup_test_logging()
    logger.info("🤖 Starting AI Processing Tests")
    
    try:
        # Initialize components
        extractor = DocumentExtractor()
        ai_processor = AIProcessor()
        template_gen = TemplateGenerator()
        file_manager = FileManager()
        
        # Test 1: Load template
        logger.info("\n📄 Test 1: Loading template...")
        template = template_gen.load_template()
        logger.info(f"✓ Template loaded: {len(template)} characters")
        
        # Test 2: Get sample documents
        logger.info("\n📁 Test 2: Getting sample documents...")
        doc_files = file_manager.scan_documents()
        if not doc_files:
            logger.error("❌ No documents found for testing")
            return
        
        # Test with first document
        test_file = doc_files[0]
        logger.info(f"Testing with: {os.path.basename(test_file)}")
        
        # Test 3: Extract content
        logger.info("\n🔍 Test 3: Extracting document content...")
        document_summary = extractor.get_document_summary(test_file)
        content = document_summary['cleaned_text']
        logger.info(f"✓ Content extracted: {len(content)} characters, {len(content.split())} words")
        
        # Test 4: AI section generation
        logger.info("\n🧠 Test 4: Testing AI section generation...")
        sections = ai_processor.generate_sections(content)
        logger.info(f"✓ Sections generated:")
        for key, value in sections.items():
            if isinstance(value, list):
                logger.info(f"  - {key}: {len(value)} items")
            else:
                logger.info(f"  - {key}: {str(value)[:50]}...")
        
        # Test 5: Full AI processing
        logger.info("\n🚀 Test 5: Full AI content structuring...")
        logger.info("⚠️  This will use OpenAI API credits - processing...")
        
        try:
            structured_content = ai_processor.structure_content(content, template)
            logger.info(f"✓ AI processing completed: {len(structured_content)} characters")
            
            # Test 6: Validation
            logger.info("\n✅ Test 6: Validating structured content...")
            is_valid = ai_processor.validate_structure(structured_content)
            logger.info(f"✓ Validation result: {'PASSED' if is_valid else 'FAILED'}")
            
            # Test 7: Handle missing info
            logger.info("\n🔧 Test 7: Testing missing info handling...")
            processed_content = ai_processor.handle_missing_info(structured_content)
            logger.info(f"✓ Missing info handling completed")
            
            # Test 8: Save result
            logger.info("\n💾 Test 8: Saving test result...")
            output_filename = f"test_ai_output_{os.path.basename(test_file).replace('.docx', '.md')}"
            output_path = file_manager.manage_output(output_filename, processed_content)
            logger.info(f"✓ Test result saved to: {output_path}")
            
            # Show sample of the result
            logger.info("\n📖 Sample of AI-processed content:")
            logger.info("=" * 50)
            logger.info(processed_content[:1000] + "..." if len(processed_content) > 1000 else processed_content)
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"❌ AI processing failed: {str(e)}")
            logger.info("This might be due to:")
            logger.info("1. OpenAI API key not set or invalid")
            logger.info("2. Network connectivity issues") 
            logger.info("3. OpenAI API rate limits")
            logger.info("4. Insufficient API credits")
            return
        
        logger.info("\n🎉 AI processing tests completed successfully!")
        logger.info(f"📁 Check the output file at: {output_path}")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        raise

def test_with_retry():
    """Test the retry functionality."""
    logger = setup_test_logging()
    logger.info("🔄 Testing AI processing with retry logic")
    
    try:
        ai_processor = AIProcessor()
        template_gen = TemplateGenerator()
        
        # Sample content for testing
        sample_content = """
        CelcomDigi Roaming Service
        
        This is a premium roaming service for international travelers.
        
        Features:
        - International roaming in 50+ countries
        - High-speed data access
        - Voice and SMS support
        - 24/7 customer support
        
        Pricing:
        - Daily pass: RM25
        - Weekly pass: RM150  
        - Monthly pass: RM500
        
        How to subscribe:
        1. Dial *123# 
        2. Select roaming options
        3. Choose your preferred plan
        4. Confirm subscription
        """
        
        template = template_gen.load_template()
        
        logger.info("🔄 Testing retry processing...")
        result = ai_processor.process_with_retry(sample_content, template, max_retries=2)
        
        logger.info(f"✓ Retry processing successful: {len(result)} characters")
        logger.info("\n📖 Sample result:")
        logger.info("=" * 30)
        logger.info(result[:500] + "..." if len(result) > 500 else result)
        logger.info("=" * 30)
        
    except Exception as e:
        logger.error(f"❌ Retry test failed: {str(e)}")

if __name__ == "__main__":
    print("Choose test to run:")
    print("1. Full AI Processing Test (uses OpenAI API)")
    print("2. Retry Logic Test (uses OpenAI API)")
    print("3. Both tests")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        test_ai_processing()
    elif choice == "2":
        test_with_retry()
    elif choice == "3":
        test_ai_processing()
        print("\n" + "="*60 + "\n")
        test_with_retry()
    else:
        print("Invalid choice. Running full test...")
        test_ai_processing()
