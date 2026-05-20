"""
Test script for API cost tracking functionality.
"""

import logging
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.ai_processor import AIProcessor
import config

def setup_logging():
    """Set up logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/cost_tracking_test.log')
        ]
    )

def test_cost_tracking():
    """Test the cost tracking functionality."""
    print("🧪 Testing API Cost Tracking")
    print("=" * 50)
    
    try:
        # Initialize AI processor
        ai_processor = AIProcessor()
        
        # Test with a simple content
        test_content = """
        CelcomDigi Business Postpaid 5G Test Document
        
        This is a test document for cost tracking.
        
        Features:
        - 5G connectivity
        - Unlimited data
        - Business rates
        
        Pricing: RM 58 per month
        """
        
        # Load template
        template_path = os.path.join(os.path.dirname(__file__), '..', 'IKB_Document_Template.md')
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        print("📤 Sending test content to OpenAI...")
        print(f"   Content length: {len(test_content)} characters")
        
        # Process content
        result = ai_processor.structure_content(test_content, template)
        
        print("📥 Response received!")
        print(f"   Response length: {len(result)} characters")
        
        # Get usage summary
        usage_summary = ai_processor.usage_tracker.get_usage_summary()
        
        print("\n💰 Cost Tracking Results:")
        print(f"   API Calls: {usage_summary['total_api_calls']}")
        print(f"   Input Tokens: {usage_summary['total_input_tokens']:,}")
        print(f"   Output Tokens: {usage_summary['total_output_tokens']:,}")
        print(f"   Total Tokens: {usage_summary['total_tokens']:,}")
        print(f"   Total Cost: ${usage_summary['total_cost']:.6f}")
        print(f"   Cost per Call: ${usage_summary['average_cost_per_call']:.6f}")
        
        # Log detailed summary
        ai_processor.log_usage_summary()
        
        print("\n✅ Cost tracking test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Cost tracking test failed: {e}")
        logging.error(f"Cost tracking test error: {e}")
        return False

def main():
    """Main test function."""
    load_dotenv()
    setup_logging()
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        return
    
    # Run the test
    success = test_cost_tracking()
    
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Some tests failed!")

if __name__ == "__main__":
    main()
