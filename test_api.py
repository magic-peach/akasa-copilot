#!/usr/bin/env python3
"""
Test script for Akasa Booking API endpoints
"""

import requests
import json
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://localhost:5000"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_create_booking():
    """Test creating a new booking"""
    print("\nTesting POST /bookings endpoint...")
    
    # Test data
    booking_data = {
        "customer_id": "CUST001",
        "flight_number": "QP1001",
        "origin": "DEL",
        "destination": "BOM",
        "depart_date": "2024-02-15",
        "status": "confirmed"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/bookings",
            json=booking_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            booking_id = response.json()["booking"]["id"]
            print(f"Created booking with ID: {booking_id}")
            return booking_id
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_get_booking(booking_id):
    """Test fetching a booking by ID"""
    print(f"\nTesting GET /bookings/{booking_id} endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/bookings/{booking_id}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_nonexistent_booking():
    """Test fetching a non-existent booking"""
    print("\nTesting GET /bookings with non-existent ID...")
    
    fake_id = "00000000-0000-0000-0000-000000000000"
    try:
        response = requests.get(f"{BASE_URL}/bookings/{fake_id}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 404
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_list_bookings():
    """Test listing all bookings"""
    print("\nTesting GET /bookings endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/bookings")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_create_invalid_booking():
    """Test creating a booking with invalid data"""
    print("\nTesting POST /bookings with invalid data...")
    
    # Missing required fields
    invalid_data = {
        "customer_id": "",
        "flight_number": "QP1001"
        # Missing origin, destination, depart_date
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/bookings",
            json=invalid_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 400
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_all_tests():
    """Run all API tests"""
    print("=" * 60)
    print("AKASA BOOKING API - ENDPOINT TESTS")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 6
    
    # Test 1: Health check
    if test_health_check():
        tests_passed += 1
        print("✅ Health check test passed")
    else:
        print("❌ Health check test failed")
    
    # Test 2: Create booking
    booking_id = test_create_booking()
    if booking_id:
        tests_passed += 1
        print("✅ Create booking test passed")
    else:
        print("❌ Create booking test failed")
    
    # Test 3: Get booking (only if create succeeded)
    if booking_id and test_get_booking(booking_id):
        tests_passed += 1
        print("✅ Get booking test passed")
    else:
        print("❌ Get booking test failed")
    
    # Test 4: Get non-existent booking
    if test_get_nonexistent_booking():
        tests_passed += 1
        print("✅ Get non-existent booking test passed")
    else:
        print("❌ Get non-existent booking test failed")
    
    # Test 5: List bookings
    if test_list_bookings():
        tests_passed += 1
        print("✅ List bookings test passed")
    else:
        print("❌ List bookings test failed")
    
    # Test 6: Create invalid booking
    if test_create_invalid_booking():
        tests_passed += 1
        print("✅ Create invalid booking test passed")
    else:
        print("❌ Create invalid booking test failed")
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {tests_passed}/{total_tests} tests passed")
    print("=" * 60)
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The API is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the API implementation.")

def test_request_booking_change(booking_id):
    """Test requesting a booking change"""
    print(f"\nTesting POST /bookings/{booking_id}/request-change endpoint...")
    
    change_request = {
        "new_date": "2024-03-15"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/bookings/{booking_id}/request-change",
            json=change_request,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            options = response.json().get('available_options', [])
            print(f"Found {len(options)} rebooking options")
            return options[0] if options else None
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_auto_rebook(booking_id, option):
    """Test auto-rebooking with a selected option"""
    print(f"\nTesting POST /bookings/{booking_id}/auto-rebook endpoint...")
    
    if not option:
        print("No option available for rebooking test")
        return False
    
    # Prepare rebooking data from the option
    rebook_data = {
        "flight_number": option['flight_number'],
        "depart_date": option['depart_date'],
        "departure_time": option['departure_time'],
        "price": option['price'],
        "aircraft_type": option.get('aircraft_type', 'A320')
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/bookings/{booking_id}/auto-rebook",
            json=rebook_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            new_booking_id = response.json()["new_booking"]["id"]
            print(f"Successfully rebooked to new booking ID: {new_booking_id}")
            return new_booking_id
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_invalid_change_request():
    """Test change request with invalid data"""
    print("\nTesting POST /bookings/request-change with invalid data...")
    
    fake_id = "00000000-0000-0000-0000-000000000000"
    invalid_data = {
        "new_date": "invalid-date"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/bookings/{fake_id}/request-change",
            json=invalid_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 400
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_all_tests():
    """Run all API tests"""
    print("=" * 60)
    print("AKASA BOOKING API - ENDPOINT TESTS")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 9  # Updated total test count
    
    # Test 1: Health check
    if test_health_check():
        tests_passed += 1
        print("✅ Health check test passed")
    else:
        print("❌ Health check test failed")
    
    # Test 2: Create booking
    booking_id = test_create_booking()
    if booking_id:
        tests_passed += 1
        print("✅ Create booking test passed")
    else:
        print("❌ Create booking test failed")
    
    # Test 3: Get booking (only if create succeeded)
    if booking_id and test_get_booking(booking_id):
        tests_passed += 1
        print("✅ Get booking test passed")
    else:
        print("❌ Get booking test failed")
    
    # Test 4: Get non-existent booking
    if test_get_nonexistent_booking():
        tests_passed += 1
        print("✅ Get non-existent booking test passed")
    else:
        print("❌ Get non-existent booking test failed")
    
    # Test 5: List bookings
    if test_list_bookings():
        tests_passed += 1
        print("✅ List bookings test passed")
    else:
        print("❌ List bookings test failed")
    
    # Test 6: Create invalid booking
    if test_create_invalid_booking():
        tests_passed += 1
        print("✅ Create invalid booking test passed")
    else:
        print("❌ Create invalid booking test failed")
    
    # Test 7: Request booking change (only if we have a booking)
    rebooking_option = None
    if booking_id:
        rebooking_option = test_request_booking_change(booking_id)
        if rebooking_option:
            tests_passed += 1
            print("✅ Request booking change test passed")
        else:
            print("❌ Request booking change test failed")
    else:
        print("❌ Request booking change test skipped (no booking available)")
    
    # Test 8: Auto-rebook (only if we have a booking and option)
    if booking_id and rebooking_option:
        new_booking_id = test_auto_rebook(booking_id, rebooking_option)
        if new_booking_id:
            tests_passed += 1
            print("✅ Auto-rebook test passed")
        else:
            print("❌ Auto-rebook test failed")
    else:
        print("❌ Auto-rebook test skipped (no booking or option available)")
    
    # Test 9: Invalid change request
    if test_invalid_change_request():
        tests_passed += 1
        print("✅ Invalid change request test passed")
    else:
        print("❌ Invalid change request test failed")
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {tests_passed}/{total_tests} tests passed")
    print("=" * 60)
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The API is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the API implementation.")

if __name__ == "__main__":
    print("Make sure the Flask application is running on http://localhost:5000")
    print("Press Enter to start tests or Ctrl+C to cancel...")
    input()
    run_all_tests()