"""
Test Runner Script
Provides easy access to run all tests from the main directory.
"""

import os
import sys
import subprocess

def run_test(test_name):
    """Run a specific test."""
    test_path = os.path.join('tests', f'test_{test_name}.py')
    if os.path.exists(test_path):
        print(f"🧪 Running {test_name} test...")
        result = subprocess.run([sys.executable, test_path], capture_output=False)
        return result.returncode == 0
    else:
        print(f"❌ Test file not found: {test_path}")
        return False

def main():
    """Main test runner function."""
    print("🧪 Document Conversion Pipeline - Test Runner")
    print("=" * 50)
    
    tests = {
        '1': ('extraction', 'Document Extraction Test'),
        '2': ('connection', 'OpenAI Connection Test'), 
        '3': ('cost_tracking', 'API Cost Tracking Test'),
        '4': ('ai_processing', 'AI Processing Test'),
        '5': ('complete_pipeline', 'Complete Pipeline Test'),
        'all': ('all', 'Run All Tests')
    }
    
    print("Available tests:")
    for key, (name, description) in tests.items():
        print(f"  {key}. {description}")
    
    choice = input("\nEnter your choice (1-5 or 'all'): ").strip()
    
    if choice == 'all':
        print("\n🚀 Running all tests...")
        test_order = ['extraction', 'connection', 'cost_tracking', 'ai_processing', 'complete_pipeline']
        results = []
        
        for test in test_order:
            print(f"\n{'='*60}")
            success = run_test(test)
            results.append((test, success))
            print(f"{'='*60}")
        
        print(f"\n📊 Test Results Summary:")
        for test, success in results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"  {test}: {status}")
            
    elif choice in tests and choice != 'all':
        test_name, description = tests[choice]
        print(f"\n🚀 Running {description}...")
        success = run_test(test_name)
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n📊 Result: {status}")
        
    else:
        print("❌ Invalid choice!")

if __name__ == "__main__":
    main()
