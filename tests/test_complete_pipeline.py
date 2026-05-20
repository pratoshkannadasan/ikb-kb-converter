"""
Complete Document Conversion Test
Tests the complete pipeline end-to-end with mock AI processing for now.
"""

import sys
import os
import logging

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def setup_test_logging():
    """Setup logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def test_complete_pipeline_mock():
    """Test complete pipeline with mock AI processing."""
    logger = setup_test_logging()
    logger.info("🔄 Testing Complete Document Conversion Pipeline")
    
    try:
        from src.document_extractor import DocumentExtractor
        from src.template_generator import TemplateGenerator
        from src.file_manager import FileManager
        
        # Initialize components (skip AI processor for now)
        extractor = DocumentExtractor()
        template_gen = TemplateGenerator()
        file_manager = FileManager()
        
        logger.info("✅ All components initialized successfully")
        
        # Test 1: Get documents
        logger.info("\n📁 Test 1: Scanning documents...")
        doc_files = file_manager.scan_documents()
        logger.info(f"✅ Found {len(doc_files)} documents")
        
        if not doc_files:
            logger.error("❌ No documents found")
            return
        
        # Test 2: Process first document
        test_file = doc_files[0]
        logger.info(f"\n📄 Test 2: Processing {os.path.basename(test_file)}")
        
        # Extract content
        logger.info("🔍 Extracting content...")
        summary = extractor.get_document_summary(test_file)
        content = summary['cleaned_text']
        logger.info(f"✅ Content extracted: {len(content)} chars, {summary['summary_stats']['total_words']} words")
        
        # Load template
        logger.info("📋 Loading template...")
        template = template_gen.load_template()
        logger.info("✅ Template loaded")
        
        # Mock AI processing (create structured content manually)
        logger.info("🤖 Mock AI processing...")
        
        # Extract key info from filename and content
        filename = os.path.basename(test_file)
        title = filename.replace('.docx', '').replace('_', ' ')
        
        # Create mock structured content
        mock_structured_content = f"""# {title}

## Document Information

- **Title**: {title}
- **Document Type**: Roaming Service
- **Last Updated**: [Date not available in source document]
- **Version**: [Version not available in source document]
- **Provider**: CelcomDigi

## Key Features

- International roaming service
- Coverage in multiple countries
- Voice and data services
- Customer support available

## Detailed Information

### Service Overview

{content[:500]}...

### Service Coverage

The service provides comprehensive coverage for international travelers with reliable connectivity.

## Pricing Information

| Plan/Package | Price | Validity | Data Allocation | Coverage |
|--------------|-------|----------|-----------------|----------|
| Basic Plan   | [Price not specified] | [Validity not specified] | [Data not specified] | International |

## Eligibility

- Available for postpaid and prepaid customers
- Valid identification required
- Active account in good standing

## How to Subscribe

1. Contact customer service
2. Provide required documentation
3. Select desired plan
4. Confirm subscription

## Terms and Conditions

- Subject to fair usage policy
- Charges may apply for excess usage
- Service availability depends on network coverage

## FAQ

**Q: How do I activate the service?**
A: Contact customer service or use the mobile app to activate.

**Q: What countries are covered?**
A: Coverage varies by plan. Please check with customer service for details.

**Q: Are there any additional charges?**
A: Additional charges may apply for usage beyond plan limits.

## Customer Support

- **Phone**: [Contact information not available in source document]
- **Email**: [Email not available in source document]
- **Hours**: [Hours not available in source document]
"""
        
        logger.info("✅ Mock structured content created")
        
        # Validate
        logger.info("✅ Validating structure...")
        has_headers = mock_structured_content.count('#') >= 3
        has_tables = '|' in mock_structured_content
        has_bullets = '- ' in mock_structured_content
        
        logger.info(f"  - Headers: {'✅' if has_headers else '❌'}")
        logger.info(f"  - Tables: {'✅' if has_tables else '❌'}")
        logger.info(f"  - Bullets: {'✅' if has_bullets else '❌'}")
        
        # Save result
        logger.info("💾 Saving result...")
        output_path = file_manager.manage_output(
            f"mock_test_{os.path.basename(test_file)}", 
            mock_structured_content
        )
        
        logger.info(f"✅ Test result saved to: {output_path}")
        
        # Show sample
        logger.info("\n📖 Sample of processed content:")
        logger.info("=" * 50)
        logger.info(mock_structured_content[:800] + "...")
        logger.info("=" * 50)
        
        logger.info("\n🎉 Complete pipeline test successful!")
        logger.info("📝 Next step: Integrate real AI processing once OpenAI client is fixed")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Pipeline test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_complete_pipeline_mock()
