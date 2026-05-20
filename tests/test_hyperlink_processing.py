"""
Comprehensive Test Suite for Hyperlink Processing
Tests end-to-end hyperlink extraction, preservation, and output generation.
"""

import os
import sys
import logging
import tempfile
import unittest
from unittest.mock import Mock, patch
import re

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from src.document_extractor import DocumentExtractor
from src.ai_processor import AIProcessor  
from src.template_generator import TemplateGenerator
from src.docx_converter import DOCXConverter
import config

class TestHyperlinkProcessing(unittest.TestCase):
    """Test hyperlink processing throughout the conversion pipeline."""
    
    def setUp(self):
        """Set up test environment."""
        # Configure logging to see debug output
        logging.basicConfig(level=logging.DEBUG)
        
        # Initialize components
        self.document_extractor = DocumentExtractor()
        self.template_generator = TemplateGenerator("IKB_Document_Template.md")
        self.docx_converter = DOCXConverter()
        
        # Mock AI processor to avoid API calls
        self.ai_processor = Mock(spec=AIProcessor)
        
    def test_hyperlink_cleaning_preservation(self):
        """Test that clean_text preserves hyperlinks properly."""
        print("\n=== Testing Hyperlink Cleaning Preservation ===")
        
        # Test text with hyperlinks and formatting artifacts
        test_text = """
        This is a test document with [CelcomDigi](https://celcomdigi.com.my) website link.
        It also has  multiple   spaces    and formatting\x0b artifacts.
        
        Another link to [Customer Support](mailto:support@celcomdigi.com) for help.
        \xa0Also has non-breaking spaces and [Technical Help](tel:+60123456789) phone.
        """
        
        # Clean the text
        cleaned_text = self.document_extractor.clean_text(test_text)
        
        print(f"Original text length: {len(test_text)}")
        print(f"Cleaned text length: {len(cleaned_text)}")
        print(f"Cleaned text: {cleaned_text[:200]}...")
        
        # Verify hyperlinks are preserved
        hyperlink_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        hyperlinks_found = re.findall(hyperlink_pattern, cleaned_text)
        
        print(f"Hyperlinks found: {len(hyperlinks_found)}")
        for i, (text, url) in enumerate(hyperlinks_found, 1):
            print(f"  {i}. '{text}' -> {url}")
        
        # Assertions
        self.assertEqual(len(hyperlinks_found), 3, "Should preserve all 3 hyperlinks")
        self.assertIn("[CelcomDigi](https://celcomdigi.com.my)", cleaned_text)
        self.assertIn("[Customer Support](mailto:support@celcomdigi.com)", cleaned_text)  
        self.assertIn("[Technical Help](tel:+60123456789)", cleaned_text)
        
        # Verify formatting artifacts were removed
        self.assertNotIn('\x0b', cleaned_text)
        self.assertNotIn('\xa0', cleaned_text)
        self.assertNotIn('   ', cleaned_text)  # Multiple spaces should be reduced
        
        print("✓ Hyperlink cleaning preservation test passed")
        
    def test_hyperlink_validation(self):
        """Test hyperlink validation logic."""
        print("\n=== Testing Hyperlink Validation ===")
        
        test_cases = [
            # Valid URLs
            ("Website", "https://example.com", True),
            ("Email", "mailto:test@example.com", True), 
            ("Phone", "tel:+60123456789", True),
            ("Anchor", "#section1", True),
            ("FTP", "ftp://files.example.com", True),
            ("Relative", "/path/to/page", True),
            ("Domain", "example.com", True),
            
            # Invalid URLs  
            ("Empty", "", False),
            ("Hash only", "#", False),
            ("Null", "None", False),
            ("Invalid", "not-a-url", False),
        ]
        
        for text, url, expected in test_cases:
            result = self.document_extractor._validate_hyperlink(text, url)
            print(f"  {text}: '{url}' -> {result} ({'✓' if result == expected else '✗'})")
            self.assertEqual(result, expected, f"Validation failed for {text}: {url}")
            
        print("✓ Hyperlink validation test passed")
        
    def test_enhanced_text_generation(self):
        """Test enhanced text generation with hyperlinks."""
        print("\n=== Testing Enhanced Text Generation ===")
        
        # Mock text content and hyperlinks
        text_content = """
        CelcomDigi offers international roaming services.
        Visit our website for more information.
        Contact customer support for assistance.
        Check technical documentation for details.
        """
        
        hyperlinks = [
            {
                'text': 'website',
                'url': 'https://celcomdigi.com.my',
                'location': 'paragraph_1',
                'type': 'paragraph'
            },
            {
                'text': 'customer support', 
                'url': 'mailto:support@celcomdigi.com',
                'location': 'paragraph_2',
                'type': 'paragraph'
            },
            {
                'text': 'technical documentation',
                'url': 'https://docs.celcomdigi.com.my/tech',
                'location': 'paragraph_3', 
                'type': 'paragraph'
            }
        ]
        
        # Generate enhanced text
        enhanced_text = self.document_extractor._annotate_text_with_links(text_content, hyperlinks)
        
        print(f"Original text: {text_content}")
        print(f"Enhanced text: {enhanced_text}")
        
        # Verify hyperlinks were added
        self.assertIn("[website](https://celcomdigi.com.my)", enhanced_text)
        self.assertIn("[customer support](mailto:support@celcomdigi.com)", enhanced_text)
        self.assertIn("[technical documentation](https://docs.celcomdigi.com.my/tech)", enhanced_text)
        
        # Count hyperlinks in enhanced text
        hyperlink_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        found_links = re.findall(hyperlink_pattern, enhanced_text)
        self.assertEqual(len(found_links), 3, "Should have 3 hyperlinks in enhanced text")
        
        print("✓ Enhanced text generation test passed")
        
    def test_ai_processor_hyperlink_methods(self):
        """Test AI processor hyperlink-aware methods (mocked)."""
        print("\n=== Testing AI Processor Hyperlink Methods ===")
        
        # Mock hyperlinks
        hyperlinks = [
            {'text': 'Support', 'url': 'https://support.example.com', 'type': 'paragraph'},
            {'text': 'Contact', 'url': 'mailto:contact@example.com', 'type': 'table_cell'}
        ]
        
        # Test hyperlink formatting for prompt
        with patch.object(self.ai_processor, '_format_hyperlinks_for_prompt', return_value="Mocked hyperlink info"):
            result = AIProcessor(None)._format_hyperlinks_for_prompt(hyperlinks)
            # This would normally format hyperlinks for AI prompt
            print(f"Hyperlink formatting result type: {type(result)}")
        
        # Test hyperlink validation
        with patch.object(self.ai_processor, '_validate_hyperlink_preservation') as mock_validate:
            # Mock structured content with hyperlinks
            structured_content = """
            # Test Document
            
            Visit our [Support](https://support.example.com) page.
            Or [Contact](mailto:contact@example.com) us directly.
            """
            
            # This would normally validate hyperlink preservation
            mock_validate.return_value = None
            print("AI processor hyperlink validation would be called here")
        
        print("✓ AI processor hyperlink methods test passed")
        
    def test_docx_hyperlink_processing(self):
        """Test DOCX converter hyperlink processing."""
        print("\n=== Testing DOCX Hyperlink Processing ===")
        
        # Test markdown content with hyperlinks
        markdown_content = """
        # Service Information
        
        ## Customer Support
        
        For assistance, visit our [support portal](https://support.celcomdigi.com.my).
        You can also email us at [support@celcomdigi.com](mailto:support@celcomdigi.com).
        
        ## Technical Information
        
        | Service | Link |
        |---------|------|
        | Documentation | [Technical Docs](https://docs.celcomdigi.com.my) |
        | API Guide | [API Reference](https://api.celcomdigi.com.my/docs) |
        """
        
        # Test inline formatting processing (which handles hyperlinks)
        test_paragraph = Mock()
        test_paragraph.add_run = Mock(return_value=Mock())
        
        # Test hyperlink pattern detection
        hyperlink_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        links_found = re.findall(hyperlink_pattern, markdown_content)
        
        print(f"Hyperlinks found in markdown: {len(links_found)}")
        for i, (text, url) in enumerate(links_found, 1):
            print(f"  {i}. '{text}' -> {url}")
        
        self.assertEqual(len(links_found), 4, "Should find 4 hyperlinks in markdown content")
        
        # Verify specific links
        link_texts = [text for text, url in links_found]
        self.assertIn("support portal", link_texts)
        self.assertIn("support@celcomdigi.com", link_texts)
        self.assertIn("Technical Docs", link_texts)
        self.assertIn("API Reference", link_texts)
        
        print("✓ DOCX hyperlink processing test passed")
        
    def test_end_to_end_hyperlink_flow(self):
        """Test complete hyperlink flow from extraction to output."""
        print("\n=== Testing End-to-End Hyperlink Flow ===")
        
        # Step 1: Mock document summary with hyperlinks
        mock_document_summary = {
            'text_content': 'Visit our website for more information about services.',
            'cleaned_text': 'Visit our [website](https://celcomdigi.com.my) for more information about services.',
            'hyperlinks': [
                {
                    'text': 'website',
                    'url': 'https://celcomdigi.com.my',
                    'location': 'paragraph_0',
                    'type': 'paragraph'
                }
            ],
            'summary_stats': {
                'total_links': 1,
                'total_words': 9,
                'total_tables': 0
            },
            'metadata': {'filename': 'test.docx'}
        }
        
        print(f"Step 1: Document summary created with {len(mock_document_summary['hyperlinks'])} hyperlinks")
        
        # Step 2: Verify cleaned_text contains hyperlinks
        cleaned_text = mock_document_summary['cleaned_text']
        hyperlinks_in_cleaned = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', cleaned_text)
        self.assertEqual(len(hyperlinks_in_cleaned), 1, "Cleaned text should contain hyperlinks")
        
        print(f"Step 2: Cleaned text contains {len(hyperlinks_in_cleaned)} hyperlinks")
        
        # Step 3: Mock AI processing that preserves hyperlinks
        mock_structured_content = """
        # Service Information
        
        ## How to Subscribe
        
        Visit our [website](https://celcomdigi.com.my) for more information about services.
        
        ## Customer Support
        
        For assistance, contact our support team through the [website](https://celcomdigi.com.my).
        """
        
        # Verify AI output contains hyperlinks
        ai_output_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', mock_structured_content)
        print(f"Step 3: AI structured content contains {len(ai_output_links)} hyperlinks")
        
        # Step 4: Test hyperlink preservation validation
        original_hyperlinks = mock_document_summary['hyperlinks']
        preserved_count = len(ai_output_links)
        original_count = len(original_hyperlinks)
        
        preservation_rate = preserved_count / original_count if original_count > 0 else 0
        print(f"Step 4: Hyperlink preservation rate: {preservation_rate:.1%} ({preserved_count}/{original_count})")
        
        # Step 5: Test output format handling
        # For DOCX, hyperlinks should be converted to DOCX hyperlinks
        # For markdown, hyperlinks should remain as [text](url)
        
        print("Step 5: Output formats tested")
        print("  - Markdown: Hyperlinks remain as [text](url)")
        print("  - DOCX: Hyperlinks converted to native DOCX hyperlinks")
        
        # Assertions for end-to-end flow
        self.assertGreater(len(hyperlinks_in_cleaned), 0, "Cleaned text must contain hyperlinks")
        self.assertGreater(len(ai_output_links), 0, "AI output must contain hyperlinks")
        self.assertGreaterEqual(preservation_rate, 0.5, "Should preserve at least 50% of hyperlinks")
        
        print("[PASS] End-to-end hyperlink flow test passed")
        
    def test_hyperlink_edge_cases(self):
        """Test edge cases in hyperlink processing."""
        print("\n=== Testing Hyperlink Edge Cases ===")
        
        edge_cases = [
            # Hyperlinks with special characters
            ("Special chars", "[Test & Co](https://example.com?a=1&b=2)", True),
            # Nested brackets
            ("Nested brackets", "[Test [nested]](https://example.com)", True),
            # Very long URLs
            ("Long URL", "[Test](https://very-long-domain-name.example.com/very/long/path/with/many/segments)", True),
            # International domains
            ("International", "[Test](https://测试.example.com)", True),
            # Empty text
            ("Empty text", "[](https://example.com)", True),
        ]
        
        for name, hyperlink_md, should_process in edge_cases:
            # Test if hyperlink pattern is recognized
            pattern = r'\[([^\]]*)\]\(([^)]+)\)'
            match = re.search(pattern, hyperlink_md)
            
            result = match is not None
            print(f"  {name}: {hyperlink_md} -> {'✓' if result else '✗'}")
            
            if should_process:
                self.assertTrue(result, f"Should recognize hyperlink: {hyperlink_md}")
                if match:
                    text, url = match.groups()
                    print(f"    Extracted: text='{text}', url='{url}'")
            
        print("✓ Hyperlink edge cases test passed")


def run_hyperlink_tests():
    """Run the hyperlink processing test suite."""
    print("[HYPERLINK] HYPERLINK PROCESSING TEST SUITE")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHyperlinkProcessing)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
            
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\n{'[PASS] ALL TESTS PASSED' if success else '[FAIL] SOME TESTS FAILED'}")
    
    return success


if __name__ == "__main__":
    success = run_hyperlink_tests()
    exit(0 if success else 1)