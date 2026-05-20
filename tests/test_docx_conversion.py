#!/usr/bin/env python3
"""
DOCX Conversion Test Script
Tests the new DOCX conversion functionality.
"""

import sys
import os
sys.path.append('.')

from src.document_extractor import DocumentExtractor
from src.template_generator import TemplateGenerator
from src.file_manager import FileManager
from src.ai_processor import AIProcessor
from src.docx_converter import DOCXConverter
import config

def test_docx_conversion():
    """Test the DOCX conversion pipeline."""
    print("🧪 Testing DOCX Conversion Pipeline")
    print("=" * 50)
    
    try:
        # Initialize components
        print("🔧 Initializing components...")
        extractor = DocumentExtractor()
        generator = TemplateGenerator()
        file_manager = FileManager()
        docx_converter = DOCXConverter()
        print("✅ Components initialized")
        
        # Get a test document
        docs = file_manager.scan_documents()
        if not docs:
            print("❌ No documents found in docs/ folder")
            return
            
        test_doc = docs[0]  # Use first document
        print(f"📄 Testing with: {os.path.basename(test_doc)}")
        
        # Extract content
        print("📤 Extracting document content...")
        doc_summary = extractor.get_document_summary(test_doc)
        content = doc_summary.get('cleaned_text', '') or doc_summary.get('text_content', '')
        print(f"✅ Extracted {len(content)} characters")
        
        # Create sample structured content for testing
        sample_markdown = f"""# {os.path.basename(test_doc).replace('.docx', '')}

## Document Information

- **Title**: Test Document
- **Document Type**: Roaming Service
- **Last Updated**: 28/07/2025
- **Version**: 1.0
- **Provider**: CelcomDigi

## Key Features

- International roaming service
- Voice and data coverage
- Multiple country support
- 24/7 customer support

## Detailed Information

### Service Overview

This is a comprehensive roaming service that provides seamless connectivity across multiple countries. The service includes both voice and data capabilities with competitive pricing.

### Coverage Details

The service covers over 50 countries worldwide with high-speed data access and clear voice quality.

## Pricing Information

| Plan | Price | Data | Validity | Countries |
|------|--------|------|----------|-----------|
| Basic | RM 25 | 1GB | 7 days | 10+ |
| Standard | RM 50 | 3GB | 14 days | 25+ |
| Premium | RM 100 | 10GB | 30 days | 50+ |

## Eligibility

- Must be active CelcomDigi customer
- Postpaid or prepaid account in good standing
- Valid identification required

## How to Subscribe

1. Dial *123# from your mobile
2. Select roaming services
3. Choose your preferred plan
4. Confirm subscription
5. Receive confirmation SMS

## Terms and Conditions

- Service activation within 24 hours
- Fair usage policy applies
- No refunds after activation
- Subject to roaming partner availability

## FAQ

**Q: How do I check my roaming balance?**
A: Dial *123# and select balance inquiry.

**Q: Can I use the service in all countries?**
A: Service availability depends on roaming agreements.

## Customer Support

- Phone: 1-300-123-2355
- Email: support@celcomdigi.com
- Live Chat: Available 24/7
- Website: www.celcomdigi.com
"""
        
        print("\n🔄 Testing DOCX conversion...")
        
        # Test direct DOCX conversion
        output_dir = "converted_docs/test"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "test_conversion.docx")
        
        # Convert to DOCX
        result_path = docx_converter.convert_markdown_to_docx(sample_markdown, output_path)
        print(f"✅ DOCX created at: {result_path}")
        
        # Validate the DOCX
        print("🔍 Validating DOCX output...")
        is_valid, issues = docx_converter.validate_docx_output(result_path)
        
        if is_valid:
            print("✅ DOCX validation PASSED")
        else:
            print(f"⚠️ DOCX validation issues found:")
            for issue in issues:
                print(f"  - {issue}")
        
        # Test dual format saving
        print("\n📋 Testing dual format saving...")
        base_filename = "test_dual_format"
        
        # Test all format options
        for format_option in ["markdown", "docx", "both"]:
            print(f"\n🧪 Testing format: {format_option}")
            try:
                saved_files = generator.save_document_dual_format(
                    sample_markdown, f"{base_filename}_{format_option}", format_option
                )
                
                for format_type, path in saved_files.items():
                    print(f"  ✅ {format_type.upper()}: {path}")
                    
                    # Quick validation
                    if os.path.exists(path):
                        file_size = os.path.getsize(path)
                        print(f"     File size: {file_size:,} bytes")
                    else:
                        print(f"     ❌ File not found!")
                        
            except Exception as e:
                print(f"  ❌ Error with {format_option}: {str(e)}")
        
        print("\n" + "=" * 50)
        print("🎉 DOCX Conversion Test Completed!")
        print("\n📁 Check the following directories for output:")
        print(f"  • Test files: {output_dir}")
        print(f"  • DOCX files: {config.DOCX_OUTPUT_FOLDER}")
        print(f"  • Markdown files: {config.MARKDOWN_OUTPUT_FOLDER}")
        
        print(f"\n💡 Tips for reviewing DOCX files:")
        print("  • Open the DOCX files in Microsoft Word")
        print("  • Check formatting, tables, and text styling")
        print("  • Verify editability for stakeholders")
        print("  • Compare with original markdown content")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

def test_docx_converter_only():
    """Test just the DOCX converter with sample content."""
    print("🧪 Testing DOCX Converter Only")
    print("=" * 50)
    
    try:
        converter = DOCXConverter()
        
        # Simple test content
        test_content = """# Sample Document

## Features
- Feature 1
- Feature 2

## Pricing

| Plan | Price |
|------|-------|
| Basic | RM 50 |
| Premium | RM 100 |

## Contact
Email: test@example.com
"""
        
        output_path = "converted_docs/test/simple_test.docx"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        print("🔄 Converting simple markdown to DOCX...")
        result = converter.convert_markdown_to_docx(test_content, output_path)
        print(f"✅ Simple conversion successful: {result}")
        
        # Validate
        is_valid, issues = converter.validate_docx_output(result)
        print(f"✅ Validation result: {'PASSED' if is_valid else 'FAILED'}")
        if issues:
            for issue in issues:
                print(f"  - {issue}")
                
    except Exception as e:
        print(f"❌ Simple test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Choose test to run:")
    print("1. Full DOCX Pipeline Test")
    print("2. DOCX Converter Only Test")
    print("3. Both tests")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        test_docx_conversion()
    elif choice == "2":
        test_docx_converter_only()
    elif choice == "3":
        test_docx_converter_only()
        print("\n" + "=" * 70 + "\n")
        test_docx_conversion()
    else:
        print("Invalid choice. Running full test...")
        test_docx_conversion()
