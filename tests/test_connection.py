"""
Simple AI Connection Test
Tests basic OpenAI connectivity without complex processing.
"""

import sys
import os
import logging

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.ai_processor import AIProcessor
import config

def test_openai_connection():
    """Simple test to verify OpenAI connection."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    logger.info("🔗 Testing OpenAI Connection")
    
    try:
        # Test 1: Initialize AI processor
        logger.info("1. Initializing AI processor...")
        ai_processor = AIProcessor()
        logger.info("✅ AI processor initialized successfully")
        
        # Test 2: Simple API call
        logger.info("2. Testing simple API call...")
        
        response = ai_processor.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": "Say 'Hello, World!' if you can read this."}
            ],
            max_tokens=50,
            temperature=0
        )
        
        result = response.choices[0].message.content
        logger.info(f"✅ API call successful: {result}")
        
        # Test 3: Test validation function
        logger.info("3. Testing validation function...")
        test_content = """
        # Document Information
        - **Title**: Test Document
        
        ## Key Features
        - Feature 1
        - Feature 2
        
        ## Pricing Information
        | Plan | Price |
        |------|-------|
        | Basic | $10 |
        """
        
        is_valid = ai_processor.validate_structure(test_content)
        logger.info(f"✅ Validation test: {'PASSED' if is_valid else 'FAILED'}")
        
        logger.info("🎉 All connection tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Connection test failed: {str(e)}")
        logger.info("\nPossible issues:")
        logger.info("1. Check your OpenAI API key in .env file")
        logger.info("2. Verify internet connection")
        logger.info("3. Check OpenAI API status")
        logger.info("4. Ensure sufficient API credits")
        return False

if __name__ == "__main__":
    test_openai_connection()
