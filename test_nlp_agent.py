#!/usr/bin/env python3
"""
Test script for Natural Language Processing agent functionality
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_nlp_booking_change():
    """Test NLP-powered booking change"""
    print("Testing POST /bookings/{id}/change-date with NLP...")
    
    # First, create a booking to test with
    booking_data = {
        "customer_id": "CUST001",
        "flight_number": "QP1001",
        "origin": "DEL",
        "destination": "BOM",
        "depart_date": "2024-02-15",
        "status": "confirmed"
    }
    
    try:
        # Create booking
        create_response = requests.post(f"{BASE_URL}/bookings", json=booking_data)
        if create_response.status_code != 201:
            print("❌ Failed to create test booking")
            return False
        
        booking_id = create_response.json()["booking"]["id"]
        print(f"Created test booking: {booking_id}")
        
        # Test NLP booking change
        nlp_requests = [
            "Change my flight to Monday",
            "Reschedule to next Tuesday",
            "Move my flight to February 20th",
            "I want to travel tomorrow morning"
        ]
        
        for nlp_request in nlp_requests:
            print(f"\nTesting request: '{nlp_request}'")
            
            change_data = {"request": nlp_request}
            response = requests.post(
                f"{BASE_URL}/bookings/{booking_id}/change-date",
                json=change_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                interpretation = data.get('interpretation', {})
                print(f"Intent: {interpretation.get('intent', 'unknown')}")
                print(f"Confidence: {interpretation.get('confidence', 0.0)}")
                print(f"Extracted Date: {interpretation.get('extracted_data', {}).get('new_date', 'None')}")
                print(f"Alternatives Found: {len(data.get('alternatives', []))}")
            else:
                print(f"Response: {json.dumps(response.json(), indent=2)}")
            
            time.sleep(0.5)
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_customer_preferences():
    """Test customer preference management"""
    print("\nTesting customer preference endpoints...")
    
    # First, create a customer
    customer_data = {
        "name": "Test Customer",
        "email": "test.customer@email.com",
        "phone": "+91-9876543999"
    }
    
    try:
        # Create customer
        create_response = requests.post(f"{BASE_URL}/customers", json=customer_data)
        if create_response.status_code != 201:
            print("❌ Failed to create test customer")
            return False
        
        customer_id = create_response.json()["customer"]["id"]
        print(f"Created test customer: {customer_id}")
        
        # Test getting preferences
        get_response = requests.get(f"{BASE_URL}/customers/{customer_id}/preferences")
        print(f"Get preferences status: {get_response.status_code}")
        if get_response.status_code == 200:
            customer = get_response.json()["customer"]
            print(f"Current preferences: seat={customer.get('seat_preference')}, meal={customer.get('meal_preference')}")
        
        # Test NLP preference updates
        nlp_requests = [
            "I prefer window seats",
            "I want vegetarian meals",
            "Send me SMS notifications",
            "I like aisle seats and vegan food",
            "No notifications please"
        ]
        
        for nlp_request in nlp_requests:
            print(f"\nTesting preference request: '{nlp_request}'")
            
            pref_data = {"request": nlp_request}
            response = requests.post(
                f"{BASE_URL}/customers/{customer_id}/preferences",
                json=pref_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                interpretation = data.get('interpretation', {})
                updated_prefs = data.get('updated_preferences', {})
                print(f"Confidence: {interpretation.get('confidence', 0.0)}")
                print(f"Updated: {list(updated_prefs.keys())}")
            else:
                print(f"Response: {json.dumps(response.json(), indent=2)}")
            
            time.sleep(0.5)
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_nlp_edge_cases():
    """Test NLP agent with edge cases and unclear requests"""
    print("\nTesting NLP edge cases...")
    
    # Create a test booking first
    booking_data = {
        "customer_id": "CUST002",
        "flight_number": "QP1002",
        "origin": "BOM",
        "destination": "BLR",
        "depart_date": "2024-02-16",
        "status": "confirmed"
    }
    
    try:
        create_response = requests.post(f"{BASE_URL}/bookings", json=booking_data)
        if create_response.status_code != 201:
            print("❌ Failed to create test booking")
            return False
        
        booking_id = create_response.json()["booking"]["id"]
        
        # Test unclear requests
        unclear_requests = [
            "Hello",
            "I need help",
            "Something is wrong",
            "Change my booking please",  # No specific date
            "Cancel everything"
        ]
        
        for unclear_request in unclear_requests:
            print(f"\nTesting unclear request: '{unclear_request}'")
            
            change_data = {"request": unclear_request}
            response = requests.post(
                f"{BASE_URL}/bookings/{booking_id}/change-date",
                json=change_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            if response.status_code != 200:
                data = response.json()
                print(f"Expected error: {data.get('message', 'Unknown error')}")
            
            time.sleep(0.3)
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_list_customers():
    """Test listing customers"""
    print("\nTesting GET /customers endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/customers?limit=5")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            customers = data.get('customers', [])
            print(f"Found {len(customers)} customers")
            return True
        return False
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_chatbot_sessions_nlp():
    """Test chatbot sessions created by NLP agent"""
    print("\nTesting chatbot sessions from NLP interactions...")
    
    try:
        response = requests.get(f"{BASE_URL}/chatbot-sessions?query_type=change_booking&limit=3")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            sessions = data.get('sessions', [])
            print(f"Found {len(sessions)} NLP sessions")
            
            for session in sessions:
                query_type = session.get('query_type', 'unknown')
                confidence = session.get('confidence_score', 0.0)
                created = session.get('created_at', 'unknown')
                print(f"  Session: {query_type} (confidence: {confidence}, created: {created})")
            
            return True
        return False
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_comprehensive_nlp_test():
    """Run a comprehensive test of the NLP system"""
    print("\n" + "="*60)
    print("COMPREHENSIVE NLP AGENT TEST SCENARIO")
    print("="*60)
    
    # Step 1: Test booking change with clear request
    print("\n1. Testing clear booking change request...")
    booking_data = {
        "customer_id": "CUST003",
        "flight_number": "QP1003",
        "origin": "BLR",
        "destination": "HYD",
        "depart_date": "2024-02-17",
        "status": "confirmed"
    }
    
    create_response = requests.post(f"{BASE_URL}/bookings", json=booking_data)
    if create_response.status_code == 201:
        booking_id = create_response.json()["booking"]["id"]
        
        change_request = {"request": "Change my flight to next Monday morning"}
        change_response = requests.post(f"{BASE_URL}/bookings/{booking_id}/change-date", json=change_request)
        
        if change_response.status_code == 200:
            data = change_response.json()
            interpretation = data.get('interpretation', {})
            print(f"   ✅ Request understood with confidence: {interpretation.get('confidence', 0.0)}")
            print(f"   Extracted date: {interpretation.get('extracted_data', {}).get('new_date', 'None')}")
        else:
            print(f"   ❌ Request failed: {change_response.json().get('message', 'Unknown error')}")
    
    time.sleep(1)
    
    # Step 2: Test customer preference update
    print("\n2. Testing customer preference update...")
    customer_data = {
        "name": "NLP Test Customer",
        "email": "nlp.test@email.com"
    }
    
    create_customer_response = requests.post(f"{BASE_URL}/customers", json=customer_data)
    if create_customer_response.status_code == 201:
        customer_id = create_customer_response.json()["customer"]["id"]
        
        pref_request = {"request": "I prefer window seats and vegetarian meals"}
        pref_response = requests.post(f"{BASE_URL}/customers/{customer_id}/preferences", json=pref_request)
        
        if pref_response.status_code == 200:
            data = pref_response.json()
            interpretation = data.get('interpretation', {})
            updated_prefs = data.get('updated_preferences', {})
            print(f"   ✅ Preferences updated with confidence: {interpretation.get('confidence', 0.0)}")
            print(f"   Updated: {list(updated_prefs.keys())}")
        else:
            print(f"   ❌ Preference update failed: {pref_response.json().get('message', 'Unknown error')}")
    
    time.sleep(1)
    
    # Step 3: Check NLP sessions were created
    print("\n3. Checking NLP sessions...")
    sessions_response = requests.get(f"{BASE_URL}/chatbot-sessions?limit=5")
    if sessions_response.status_code == 200:
        sessions_data = sessions_response.json()
        sessions = sessions_data.get('sessions', [])
        nlp_sessions = [s for s in sessions if s.get('query_type') in ['change_booking', 'update_preferences']]
        print(f"   Found {len(nlp_sessions)} NLP sessions")
    
    print("\n" + "="*60)
    print("COMPREHENSIVE NLP TEST COMPLETED")
    print("="*60)

def run_all_nlp_tests():
    """Run all NLP agent tests"""
    print("=" * 60)
    print("NLP AGENT TESTS")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 5
    
    # Test 1: NLP booking change
    if test_nlp_booking_change():
        tests_passed += 1
        print("✅ NLP booking change test passed")
    else:
        print("❌ NLP booking change test failed")
    
    # Test 2: Customer preferences
    if test_customer_preferences():
        tests_passed += 1
        print("✅ Customer preferences test passed")
    else:
        print("❌ Customer preferences test failed")
    
    # Test 3: NLP edge cases
    if test_nlp_edge_cases():
        tests_passed += 1
        print("✅ NLP edge cases test passed")
    else:
        print("❌ NLP edge cases test failed")
    
    # Test 4: List customers
    if test_list_customers():
        tests_passed += 1
        print("✅ List customers test passed")
    else:
        print("❌ List customers test failed")
    
    # Test 5: Chatbot sessions
    if test_chatbot_sessions_nlp():
        tests_passed += 1
        print("✅ Chatbot sessions test passed")
    else:
        print("❌ Chatbot sessions test failed")
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {tests_passed}/{total_tests} tests passed")
    print("=" * 60)
    
    if tests_passed == total_tests:
        print("🎉 All NLP agent tests passed!")
    else:
        print("⚠️  Some tests failed. Check the implementation.")

if __name__ == "__main__":
    print("NLP Agent Test Suite")
    print("Make sure the Flask application is running on http://localhost:5000")
    print("\nChoose an option:")
    print("1. Run all NLP agent tests")
    print("2. Run comprehensive test scenario")
    print("3. Both")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice in ['1', '3']:
        try:
            run_all_nlp_tests()
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to the API. Make sure the server is running.")
        except Exception as e:
            print(f"❌ Error running tests: {e}")
    
    if choice in ['2', '3']:
        try:
            run_comprehensive_nlp_test()
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to the API. Make sure the server is running.")
        except Exception as e:
            print(f"❌ Error running comprehensive test: {e}")