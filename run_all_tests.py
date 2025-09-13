#!/usr/bin/env python3
"""
Comprehensive test runner for the entire Akasa Booking API platform
Runs all test suites in sequence
"""

import subprocess
import sys
import time
import requests

BASE_URL = "http://localhost:5000"

def check_server_running():
    """Check if the Flask server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def run_test_suite(test_file, description):
    """Run a specific test suite"""
    print(f"\n{'='*60}")
    print(f"RUNNING: {description}")
    print(f"File: {test_file}")
    print(f"{'='*60}")
    
    try:
        # Run the test file
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=300)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Test suite timed out (5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Error running test suite: {e}")
        return False

def main():
    """Main test runner"""
    print("🚀 AKASA BOOKING API - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    # Check if server is running
    if not check_server_running():
        print("❌ Flask server is not running!")
        print("Please start the server with: python app.py")
        print("Then run this test suite again.")
        sys.exit(1)
    
    print("✅ Flask server is running")
    
    # Define test suites
    test_suites = [
        ("test_api.py", "Core Booking API Tests"),
        ("test_flight_events.py", "Flight Event Processing Tests"),
        ("test_genai_agent.py", "GenAI Agent Tests"),
        ("test_disruption_prediction.py", "Disruption Prediction Tests"),
        ("test_nlp_agent.py", "Natural Language Processing Tests"),
        ("test_voice_chatbot.py", "Voice Chatbot & Alert Subscription Tests")
    ]
    
    results = []
    total_start_time = time.time()
    
    # Run each test suite
    for test_file, description in test_suites:
        start_time = time.time()
        success = run_test_suite(test_file, description)
        end_time = time.time()
        
        duration = end_time - start_time
        results.append((description, success, duration))
        
        if success:
            print(f"✅ {description} - PASSED ({duration:.1f}s)")
        else:
            print(f"❌ {description} - FAILED ({duration:.1f}s)")
        
        # Small delay between test suites
        time.sleep(2)
    
    # Print final results
    total_duration = time.time() - total_start_time
    passed_tests = sum(1 for _, success, _ in results if success)
    total_tests = len(results)
    
    print("\n" + "="*60)
    print("FINAL TEST RESULTS")
    print("="*60)
    
    for description, success, duration in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status:<10} {description:<40} ({duration:.1f}s)")
    
    print("-"*60)
    print(f"SUMMARY: {passed_tests}/{total_tests} test suites passed")
    print(f"TOTAL TIME: {total_duration:.1f} seconds")
    
    if passed_tests == total_tests:
        print("🎉 ALL TEST SUITES PASSED!")
        print("The Akasa Booking API platform is working correctly.")
    else:
        print("⚠️  SOME TEST SUITES FAILED!")
        print("Please review the failed tests and fix any issues.")
    
    print("="*60)
    
    # Exit with appropriate code
    sys.exit(0 if passed_tests == total_tests else 1)

if __name__ == "__main__":
    print("Akasa Booking API - Comprehensive Test Runner")
    print("This will run all test suites in sequence.")
    print("Make sure the Flask application is running on http://localhost:5000")
    print("\nPress Enter to start all tests or Ctrl+C to cancel...")
    
    try:
        input()
        main()
    except KeyboardInterrupt:
        print("\n❌ Test run cancelled by user")
        sys.exit(1)