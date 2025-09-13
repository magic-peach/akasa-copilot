#!/usr/bin/env python3
"""
Test script for GenAI agent flight status retrieval functionality
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_genai_flight_status():
    """Test the GenAI agent flight status endpoint"""
    print("Testing GET /flights/{flight_id}/status endpoint...")
    
    # Test with a known flight number
    flight_id = "QP1001"
    
    try:
        response = requests.get(f"{BASE_URL}/flights/{flight_id}/status")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            flight_status = data.get('flight_status', {})
            
            # Validate required fields
            required_fields = ['flight_number', 'status', 'confidence_score']
            missing_fields = [field for field in required_fields if field not in flight_status]
            
            if not missing_fields:
                print(f"✅ All required fields present")
                print(f"   Flight: {flight_status['flight_number']}")
                print(f"   Status: {flight_status['status']}")
                print(f"   Confidence: {flight_status['confidence_score']}")
                print(f"   ETA: {flight_status.get('eta', 'N/A')}")
                print(f"   Gate: {flight_status.get('gate', 'N/A')}")
                return True
            else:
                print(f"❌ Missing required fields: {missing_fields}")
                return False
        else:
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_genai_with_unknown_flight():
    """Test GenAI agent with unknown flight"""
    print("\nTesting GenAI agent with unknown flight...")
    
    unknown_flight = "XX9999"
    
    try:
        response = requests.get(f"{BASE_URL}/flights/{unknown_flight}/status")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Should still return a response with low confidence
        if response.status_code in [200, 404]:
            return True
        return False
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_genai_with_invalid_flight_id():
    """Test GenAI agent with invalid flight ID"""
    print("\nTesting GenAI agent with invalid flight ID...")
    
    try:
        response = requests.get(f"{BASE_URL}/flights//status")  # Empty flight ID
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 404  # Should return 404 for invalid path
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_list_flights():
    """Test listing flights"""
    print("\nTesting GET /flights endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/flights?limit=5")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            flights = data.get('flights', [])
            print(f"Found {len(flights)} flights")
            return True
        return False
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_flight_metadata():
    """Test getting flight metadata"""
    print("\nTesting GET /flights/{flight_id} endpoint...")
    
    flight_id = "QP1001"
    
    try:
        response = requests.get(f"{BASE_URL}/flights/{flight_id}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            flight = data.get('flight', {})
            print(f"Flight metadata retrieved for: {flight.get('flight_number', 'Unknown')}")
            return True
        return response.status_code == 404  # Also valid if not found
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_chatbot_sessions():
    """Test getting chatbot sessions"""
    print("\nTesting GET /chatbot-sessions endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/chatbot-sessions?limit=3")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            sessions = data.get('sessions', [])
            print(f"Found {len(sessions)} chatbot sessions")
            return True
        return False
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_genai_confidence_scoring():
    """Test confidence scoring with multiple flights"""
    print("\nTesting confidence scoring with multiple flights...")
    
    test_flights = ["QP1001", "QP1002", "QP9999", "XX0000"]
    confidence_scores = []
    
    for flight_id in test_flights:
        try:
            response = requests.get(f"{BASE_URL}/flights/{flight_id}/status")
            if response.status_code == 200:
                data = response.json()
                flight_status = data.get('flight_status', {})
                confidence = flight_status.get('confidence_score', 0.0)
                confidence_scores.append((flight_id, confidence))
                print(f"  {flight_id}: confidence = {confidence}")
            time.sleep(0.5)  # Small delay between requests
        except Exception as e:
            print(f"  {flight_id}: error = {e}")
    
    if confidence_scores:
        avg_confidence = sum(score for _, score in confidence_scores) / len(confidence_scores)
        print(f"Average confidence score: {avg_confidence:.2f}")
        return True
    
    return False

def test_data_source_integration():
    """Test data source integration and merging"""
    print("\nTesting data source integration...")
    
    flight_id = "QP1001"
    
    try:
        response = requests.get(f"{BASE_URL}/flights/{flight_id}/status")
        if response.status_code == 200:
            data = response.json()
            flight_status = data.get('flight_status', {})
            data_sources = flight_status.get('data_sources', {})
            
            print(f"Data sources used:")
            print(f"  Metadata available: {data_sources.get('metadata_available', False)}")
            print(f"  External data available: {data_sources.get('external_data_available', False)}")
            print(f"  External source: {data_sources.get('external_source', 'unknown')}")
            
            # Check if agent info is present
            agent_info = data.get('agent_info', {})
            if agent_info:
                print(f"Agent processing info:")
                print(f"  Session ID: {agent_info.get('session_id', 'N/A')}")
                print(f"  Processing time: {agent_info.get('processing_time', 'N/A')}")
            
            return True
        return False
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_comprehensive_genai_test():
    """Run a comprehensive test of the GenAI agent system"""
    print("\n" + "="*60)
    print("COMPREHENSIVE GENAI AGENT TEST SCENARIO")
    print("="*60)
    
    # Step 1: Test with known flight
    print("\n1. Testing with known flight (should have high confidence)...")
    response1 = requests.get(f"{BASE_URL}/flights/QP1001/status")
    if response1.status_code == 200:
        data1 = response1.json()
        confidence1 = data1.get('flight_status', {}).get('confidence_score', 0.0)
        print(f"   Known flight confidence: {confidence1}")
    
    time.sleep(1)
    
    # Step 2: Test with unknown flight
    print("\n2. Testing with unknown flight (should have lower confidence)...")
    response2 = requests.get(f"{BASE_URL}/flights/XX9999/status")
    if response2.status_code == 200:
        data2 = response2.json()
        confidence2 = data2.get('flight_status', {}).get('confidence_score', 0.0)
        print(f"   Unknown flight confidence: {confidence2}")
    
    time.sleep(1)
    
    # Step 3: Check chatbot sessions were created
    print("\n3. Checking chatbot sessions were created...")
    sessions_response = requests.get(f"{BASE_URL}/chatbot-sessions?limit=5")
    if sessions_response.status_code == 200:
        sessions_data = sessions_response.json()
        sessions = sessions_data.get('sessions', [])
        print(f"   Found {len(sessions)} recent sessions")
        
        # Show recent sessions
        for session in sessions[:2]:
            flight_id = session.get('flight_id', 'Unknown')
            confidence = session.get('confidence_score', 0.0)
            created_at = session.get('created_at', 'Unknown')
            print(f"   Session: {flight_id} (confidence: {confidence}, created: {created_at})")
    
    print("\n" + "="*60)
    print("COMPREHENSIVE TEST COMPLETED")
    print("="*60)

def run_all_genai_tests():
    """Run all GenAI agent tests"""
    print("=" * 60)
    print("GENAI AGENT FLIGHT STATUS TESTS")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 8
    
    # Test 1: Basic GenAI flight status
    if test_genai_flight_status():
        tests_passed += 1
        print("✅ GenAI flight status test passed")
    else:
        print("❌ GenAI flight status test failed")
    
    # Test 2: Unknown flight
    if test_genai_with_unknown_flight():
        tests_passed += 1
        print("✅ Unknown flight test passed")
    else:
        print("❌ Unknown flight test failed")
    
    # Test 3: Invalid flight ID
    if test_genai_with_invalid_flight_id():
        tests_passed += 1
        print("✅ Invalid flight ID test passed")
    else:
        print("❌ Invalid flight ID test failed")
    
    # Test 4: List flights
    if test_list_flights():
        tests_passed += 1
        print("✅ List flights test passed")
    else:
        print("❌ List flights test failed")
    
    # Test 5: Get flight metadata
    if test_get_flight_metadata():
        tests_passed += 1
        print("✅ Get flight metadata test passed")
    else:
        print("❌ Get flight metadata test failed")
    
    # Test 6: Chatbot sessions
    if test_chatbot_sessions():
        tests_passed += 1
        print("✅ Chatbot sessions test passed")
    else:
        print("❌ Chatbot sessions test failed")
    
    # Test 7: Confidence scoring
    if test_genai_confidence_scoring():
        tests_passed += 1
        print("✅ Confidence scoring test passed")
    else:
        print("❌ Confidence scoring test failed")
    
    # Test 8: Data source integration
    if test_data_source_integration():
        tests_passed += 1
        print("✅ Data source integration test passed")
    else:
        print("❌ Data source integration test failed")
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {tests_passed}/{total_tests} tests passed")
    print("=" * 60)
    
    if tests_passed == total_tests:
        print("🎉 All GenAI agent tests passed!")
    else:
        print("⚠️  Some tests failed. Check the implementation.")

if __name__ == "__main__":
    print("GenAI Agent Test Suite")
    print("Make sure the Flask application is running on http://localhost:5000")
    print("\nChoose an option:")
    print("1. Run all GenAI agent tests")
    print("2. Run comprehensive test scenario")
    print("3. Both")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice in ['1', '3']:
        try:
            run_all_genai_tests()
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to the API. Make sure the server is running.")
        except Exception as e:
            print(f"❌ Error running tests: {e}")
    
    if choice in ['2', '3']:
        try:
            run_comprehensive_genai_test()
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to the API. Make sure the server is running.")
        except Exception as e:
            print(f"❌ Error running comprehensive test: {e}")