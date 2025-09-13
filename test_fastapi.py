#!/usr/bin/env python3
"""
Test script for FastAPI flight booking service
"""

import requests
import json
from datetime import datetime, date, time

FASTAPI_BASE_URL = "http://localhost:8000"

def test_fastapi_health():
    """Test FastAPI health endpoint"""
    print("Testing FastAPI health endpoint...")
    
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_flight_search():
    """Test flight search endpoint"""
    print("\nTesting POST /flights/search endpoint...")
    
    search_data = {
        "date": "2024-03-15",
        "time": "09:00:00",
        "origin": "DEL",
        "destination": "BOM",
        "occasion": "business",
        "budget": 6000,
        "preferred_airline": "Akasa Air",
        "passengers": 1
    }
    
    try:
        response = requests.post(
            f"{FASTAPI_BASE_URL}/flights/search",
            json=search_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Best Flight: {data['best_flight']['airline']} {data['best_flight']['flight_number']}")
            print(f"Price: ₹{data['best_flight']['price']}")
            print(f"Duration: {data['best_flight']['duration']}")
            print(f"Risk Factor: {data['best_flight']['risk_factor']}")
            print(f"Alternatives: {len(data['alternatives'])}")
            print(f"Reasoning: {data['reasoning'][:100]}...")
            
            return data['best_flight']['id']  # Return flight ID for booking test
        else:
            print(f"Error: {response.json()}")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_flight_booking(flight_id):
    """Test flight booking endpoint"""
    print(f"\nTesting POST /flights/book endpoint...")
    
    if not flight_id:
        print("No flight ID available for booking test")
        return None
    
    booking_data = {
        "customer_id": "CUST_FASTAPI_001",
        "flight_id": flight_id,
        "passenger_details": {
            "name": "John Doe",
            "email": "john.doe@email.com",
            "phone": "+91-9876543210"
        }
    }
    
    try:
        response = requests.post(
            f"{FASTAPI_BASE_URL}/flights/book",
            json=booking_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            booking = data['booking']
            print(f"Booking ID: {booking['id']}")
            print(f"Status: {booking['status']}")
            print(f"Booking Link: {booking['booking_link']}")
            print(f"Message: {data['message']}")
            
            return booking['id']  # Return booking ID for status test
        else:
            print(f"Error: {response.json()}")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_flight_status(booking_id):
    """Test flight status endpoint"""
    print(f"\nTesting GET /flights/{booking_id}/status endpoint...")
    
    if not booking_id:
        print("No booking ID available for status test")
        return False
    
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/flights/{booking_id}/status")
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Booking ID: {data['booking_id']}")
            print(f"Flight Status: {data['status']}")
            print(f"Departure: {data['departure_time']}")
            print(f"Gate: {data['gate_info']}")
            print(f"Terminal: {data['terminal']}")
            if data['delay_minutes']:
                print(f"Delay: {data['delay_minutes']} minutes")
            
            return True
        else:
            print(f"Error: {response.json()}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_cancel_and_rebook(booking_id):
    """Test cancel and rebook endpoint"""
    print(f"\nTesting POST /flights/cancel-and-rebook endpoint...")
    
    if not booking_id:
        print("No booking ID available for cancel and rebook test")
        return False
    
    rebook_data = {
        "booking_id": booking_id,
        "new_date": "2024-03-20",
        "new_time": "14:00:00",
        "budget": 7000
    }
    
    try:
        response = requests.post(
            f"{FASTAPI_BASE_URL}/flights/cancel-and-rebook",
            json=rebook_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Cancelled Booking: {data['cancelled_booking']['id']}")
            print(f"New Options: {len(data['new_options'])}")
            print(f"Reasoning: {data['reasoning'][:100]}...")
            
            # Show first new option
            if data['new_options']:
                first_option = data['new_options'][0]
                print(f"Best New Option: {first_option['airline']} {first_option['flight_number']} - ₹{first_option['price']}")
            
            return True
        else:
            print(f"Error: {response.json()}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_chatbot_sessions():
    """Test chatbot sessions endpoint"""
    print(f"\nTesting GET /chatbot-sessions/{{user_id}} endpoint...")
    
    user_id = "CUST_FASTAPI_001"
    
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/chatbot-sessions/{user_id}?limit=5")
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            sessions = data['sessions']
            print(f"Found {len(sessions)} sessions for user {user_id}")
            
            for session in sessions[:3]:
                query = session.get('query', 'Unknown')
                confidence = session.get('confidence_score', 0.0)
                created = session.get('created_at', 'Unknown')
                print(f"  Session: {query} (confidence: {confidence}, created: {created})")
            
            return True
        else:
            print(f"Error: {response.json()}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_api_documentation():
    """Test FastAPI auto-generated documentation"""
    print(f"\nTesting FastAPI documentation endpoints...")
    
    try:
        # Test OpenAPI docs
        docs_response = requests.get(f"{FASTAPI_BASE_URL}/docs")
        print(f"OpenAPI Docs Status: {docs_response.status_code}")
        
        # Test ReDoc
        redoc_response = requests.get(f"{FASTAPI_BASE_URL}/redoc")
        print(f"ReDoc Status: {redoc_response.status_code}")
        
        # Test OpenAPI JSON
        openapi_response = requests.get(f"{FASTAPI_BASE_URL}/openapi.json")
        print(f"OpenAPI JSON Status: {openapi_response.status_code}")
        
        if openapi_response.status_code == 200:
            openapi_data = openapi_response.json()
            print(f"API Title: {openapi_data.get('info', {}).get('title', 'Unknown')}")
            print(f"API Version: {openapi_data.get('info', {}).get('version', 'Unknown')}")
            print(f"Endpoints: {len(openapi_data.get('paths', {}))}")
        
        return docs_response.status_code == 200 and redoc_response.status_code == 200
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_comprehensive_fastapi_test():
    """Run comprehensive FastAPI test scenario"""
    print("\n" + "="*60)
    print("COMPREHENSIVE FASTAPI TEST SCENARIO")
    print("="*60)
    
    # Step 1: Search for flights
    print("\n1. Searching for flights...")
    search_data = {
        "date": "2024-03-15",
        "origin": "DEL",
        "destination": "BOM",
        "occasion": "leisure",
        "budget": 5000
    }
    
    search_response = requests.post(f"{FASTAPI_BASE_URL}/flights/search", json=search_data)
    if search_response.status_code == 200:
        search_result = search_response.json()
        best_flight_id = search_result['best_flight']['id']
        print(f"   ✅ Found flights: {search_result['total_results']} options")
        print(f"   Best: {search_result['best_flight']['airline']} - ₹{search_result['best_flight']['price']}")
        
        # Step 2: Book the best flight
        print("\n2. Booking the best flight...")
        booking_data = {
            "customer_id": "CUST_SCENARIO_001",
            "flight_id": best_flight_id
        }
        
        booking_response = requests.post(f"{FASTAPI_BASE_URL}/flights/book", json=booking_data)
        if booking_response.status_code == 200:
            booking_result = booking_response.json()
            booking_id = booking_result['booking']['id']
            print(f"   ✅ Booking created: {booking_id}")
            print(f"   Link: {booking_result['booking']['booking_link']}")
            
            # Step 3: Check flight status
            print("\n3. Checking flight status...")
            status_response = requests.get(f"{FASTAPI_BASE_URL}/flights/{booking_id}/status")
            if status_response.status_code == 200:
                status_result = status_response.json()
                print(f"   ✅ Status: {status_result['status']}")
                print(f"   Gate: {status_result['gate_info']}")
                
                # Step 4: Cancel and rebook
                print("\n4. Testing cancel and rebook...")
                rebook_data = {
                    "booking_id": booking_id,
                    "new_date": "2024-03-20",
                    "budget": 6000
                }
                
                rebook_response = requests.post(f"{FASTAPI_BASE_URL}/flights/cancel-and-rebook", json=rebook_data)
                if rebook_response.status_code == 200:
                    rebook_result = rebook_response.json()
                    print(f"   ✅ Cancelled and found {len(rebook_result['new_options'])} new options")
                else:
                    print(f"   ❌ Rebook failed: {rebook_response.json()}")
            else:
                print(f"   ❌ Status check failed: {status_response.json()}")
        else:
            print(f"   ❌ Booking failed: {booking_response.json()}")
    else:
        print(f"   ❌ Search failed: {search_response.json()}")
    
    print("\n" + "="*60)
    print("COMPREHENSIVE FASTAPI TEST COMPLETED")
    print("="*60)

def run_all_fastapi_tests():
    """Run all FastAPI tests"""
    print("=" * 60)
    print("FASTAPI FLIGHT BOOKING TESTS")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 6
    
    # Test 1: Health check
    if test_fastapi_health():
        tests_passed += 1
        print("✅ FastAPI health test passed")
    else:
        print("❌ FastAPI health test failed")
    
    # Test 2: Flight search
    flight_id = test_flight_search()
    if flight_id:
        tests_passed += 1
        print("✅ Flight search test passed")
    else:
        print("❌ Flight search test failed")
    
    # Test 3: Flight booking
    booking_id = test_flight_booking(flight_id)
    if booking_id:
        tests_passed += 1
        print("✅ Flight booking test passed")
    else:
        print("❌ Flight booking test failed")
    
    # Test 4: Flight status
    if test_flight_status(booking_id):
        tests_passed += 1
        print("✅ Flight status test passed")
    else:
        print("❌ Flight status test failed")
    
    # Test 5: Cancel and rebook
    if test_cancel_and_rebook(booking_id):
        tests_passed += 1
        print("✅ Cancel and rebook test passed")
    else:
        print("❌ Cancel and rebook test failed")
    
    # Test 6: Chatbot sessions
    if test_chatbot_sessions():
        tests_passed += 1
        print("✅ Chatbot sessions test passed")
    else:
        print("❌ Chatbot sessions test failed")
    
    # Test 7: API documentation
    if test_api_documentation():
        tests_passed += 1
        print("✅ API documentation test passed")
        total_tests = 7  # Update total
    else:
        print("❌ API documentation test failed")
        total_tests = 7  # Update total
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {tests_passed}/{total_tests} tests passed")
    print("=" * 60)
    
    if tests_passed == total_tests:
        print("🎉 All FastAPI tests passed!")
    else:
        print("⚠️  Some tests failed. Check the implementation.")

if __name__ == "__main__":
    print("FastAPI Flight Booking Test Suite")
    print("Make sure the FastAPI application is running on http://localhost:8000")
    print("Start it with: python fastapi_app.py")
    print("\nChoose an option:")
    print("1. Run all FastAPI tests")
    print("2. Run comprehensive test scenario")
    print("3. Both")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice in ['1', '3']:
        try:
            run_all_fastapi_tests()
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to FastAPI. Make sure the server is running on port 8000.")
        except Exception as e:
            print(f"❌ Error running tests: {e}")
    
    if choice in ['2', '3']:
        try:
            run_comprehensive_fastapi_test()
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to FastAPI. Make sure the server is running on port 8000.")
        except Exception as e:
            print(f"❌ Error running comprehensive test: {e}")