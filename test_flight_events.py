#!/usr/bin/env python3
"""
Test script for flight event processing and disruption detection
"""

import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000"

def test_flight_event_webhook():
    """Test the flight event webhook endpoint"""
    print("Testing POST /webhook/flight-event endpoint...")
    
    # Test data for a normal flight
    normal_flight_event = {
        "flight_number": "QP1001",
        "status": "ON_TIME",
        "estimated_arrival": "2024-02-15T14:30:00Z",
        "scheduled_arrival": "2024-02-15T14:30:00Z",
        "origin": "DEL",
        "destination": "BOM"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/webhook/flight-event",
            json=normal_flight_event,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_delayed_flight_event():
    """Test flight event with significant delay (should trigger alert)"""
    print("\nTesting delayed flight event (>45 minutes)...")
    
    # Calculate times for a 60-minute delay
    scheduled_time = datetime.now() + timedelta(hours=2)
    delayed_time = scheduled_time + timedelta(minutes=60)
    
    delayed_flight_event = {
        "flight_number": "QP1002",
        "status": "DELAYED",
        "estimated_arrival": delayed_time.isoformat() + "Z",
        "scheduled_arrival": scheduled_time.isoformat() + "Z",
        "origin": "BOM",
        "destination": "BLR"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/webhook/flight-event",
            json=delayed_flight_event,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Wait a moment for background processing
        print("Waiting for background processing...")
        time.sleep(2)
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_cancelled_flight_event():
    """Test cancelled flight event (should trigger critical alert)"""
    print("\nTesting cancelled flight event...")
    
    cancelled_flight_event = {
        "flight_number": "QP1003",
        "status": "CANCELLED",
        "estimated_arrival": "2024-02-17T18:15:00Z",
        "scheduled_arrival": "2024-02-17T18:15:00Z",
        "origin": "BLR",
        "destination": "HYD"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/webhook/flight-event",
            json=cancelled_flight_event,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Wait a moment for background processing
        print("Waiting for background processing...")
        time.sleep(2)
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_flight_state():
    """Test getting flight state"""
    print("\nTesting GET /flight-state/{flight_number} endpoint...")
    
    flight_number = "QP1001"
    try:
        response = requests.get(f"{BASE_URL}/flight-state/{flight_number}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code in [200, 404]  # Both are valid responses
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_alerts():
    """Test getting alerts"""
    print("\nTesting GET /alerts endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/alerts?limit=5")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            alerts = response.json().get('alerts', [])
            return alerts  # Return alerts for further testing
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def test_resolve_alert(alert_id):
    """Test resolving an alert"""
    print(f"\nTesting POST /alerts/{alert_id}/resolve endpoint...")
    
    try:
        response = requests.post(f"{BASE_URL}/alerts/{alert_id}/resolve")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_invalid_flight_event():
    """Test flight event with invalid data"""
    print("\nTesting invalid flight event data...")
    
    invalid_event = {
        "flight_number": "",  # Invalid empty flight number
        "status": "INVALID_STATUS",  # Invalid status
        "estimated_arrival": "invalid-date"  # Invalid date format
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/webhook/flight-event",
            json=invalid_event,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 400
    except Exception as e:
        print(f"Error: {e}")
        return False

def simulate_flight_disruption_scenario():
    """Simulate a complete flight disruption scenario"""
    print("\n" + "="*60)
    print("FLIGHT DISRUPTION SIMULATION SCENARIO")
    print("="*60)
    
    # Step 1: Normal flight status
    print("\n1. Flight QP2001 starts as ON_TIME...")
    normal_event = {
        "flight_number": "QP2001",
        "status": "ON_TIME",
        "estimated_arrival": "2024-02-20T16:30:00Z",
        "scheduled_arrival": "2024-02-20T16:30:00Z",
        "origin": "DEL",
        "destination": "GOA"
    }
    
    requests.post(f"{BASE_URL}/webhook/flight-event", json=normal_event)
    time.sleep(1)
    
    # Step 2: Minor delay (should not trigger alert)
    print("\n2. Flight gets minor delay (30 minutes)...")
    minor_delay_event = {
        "flight_number": "QP2001",
        "status": "DELAYED",
        "estimated_arrival": "2024-02-20T17:00:00Z",
        "scheduled_arrival": "2024-02-20T16:30:00Z",
        "origin": "DEL",
        "destination": "GOA"
    }
    
    requests.post(f"{BASE_URL}/webhook/flight-event", json=minor_delay_event)
    time.sleep(2)
    
    # Step 3: Major delay (should trigger alert)
    print("\n3. Flight gets major delay (75 minutes)...")
    major_delay_event = {
        "flight_number": "QP2001",
        "status": "DELAYED",
        "estimated_arrival": "2024-02-20T17:45:00Z",
        "scheduled_arrival": "2024-02-20T16:30:00Z",
        "origin": "DEL",
        "destination": "GOA"
    }
    
    requests.post(f"{BASE_URL}/webhook/flight-event", json=major_delay_event)
    time.sleep(2)
    
    # Step 4: Flight cancelled (should trigger critical alert)
    print("\n4. Flight gets cancelled...")
    cancelled_event = {
        "flight_number": "QP2001",
        "status": "CANCELLED",
        "estimated_arrival": "2024-02-20T17:45:00Z",
        "scheduled_arrival": "2024-02-20T16:30:00Z",
        "origin": "DEL",
        "destination": "GOA"
    }
    
    requests.post(f"{BASE_URL}/webhook/flight-event", json=cancelled_event)
    time.sleep(2)
    
    print("\n5. Checking generated alerts...")
    alerts_response = requests.get(f"{BASE_URL}/alerts?flight_number=QP2001")
    if alerts_response.status_code == 200:
        alerts = alerts_response.json().get('alerts', [])
        print(f"Generated {len(alerts)} alerts for flight QP2001:")
        for alert in alerts:
            print(f"  - {alert['alert_type']}: {alert['message']} (Severity: {alert['severity']})")
    
    print("\n" + "="*60)
    print("DISRUPTION SCENARIO COMPLETED")
    print("="*60)

def run_all_flight_event_tests():
    """Run all flight event tests"""
    print("=" * 60)
    print("FLIGHT EVENT PROCESSING TESTS")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 7
    
    # Test 1: Normal flight event
    if test_flight_event_webhook():
        tests_passed += 1
        print("✅ Normal flight event test passed")
    else:
        print("❌ Normal flight event test failed")
    
    # Test 2: Delayed flight event
    if test_delayed_flight_event():
        tests_passed += 1
        print("✅ Delayed flight event test passed")
    else:
        print("❌ Delayed flight event test failed")
    
    # Test 3: Cancelled flight event
    if test_cancelled_flight_event():
        tests_passed += 1
        print("✅ Cancelled flight event test passed")
    else:
        print("❌ Cancelled flight event test failed")
    
    # Test 4: Get flight state
    if test_get_flight_state():
        tests_passed += 1
        print("✅ Get flight state test passed")
    else:
        print("❌ Get flight state test failed")
    
    # Test 5: Get alerts
    alerts = test_get_alerts()
    if alerts is not None:
        tests_passed += 1
        print("✅ Get alerts test passed")
        
        # Test 6: Resolve alert (if we have alerts)
        if alerts and len(alerts) > 0:
            alert_id = alerts[0]['id']
            if test_resolve_alert(alert_id):
                tests_passed += 1
                print("✅ Resolve alert test passed")
            else:
                print("❌ Resolve alert test failed")
        else:
            print("⚠️  Resolve alert test skipped (no alerts available)")
    else:
        print("❌ Get alerts test failed")
    
    # Test 7: Invalid flight event
    if test_invalid_flight_event():
        tests_passed += 1
        print("✅ Invalid flight event test passed")
    else:
        print("❌ Invalid flight event test failed")
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {tests_passed}/{total_tests} tests passed")
    print("=" * 60)
    
    if tests_passed == total_tests:
        print("🎉 All flight event tests passed!")
    else:
        print("⚠️  Some tests failed. Check the implementation.")

if __name__ == "__main__":
    print("Flight Event Processing Test Suite")
    print("Make sure the Flask application is running on http://localhost:5000")
    print("\nChoose an option:")
    print("1. Run all flight event tests")
    print("2. Run disruption simulation scenario")
    print("3. Both")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice in ['1', '3']:
        try:
            run_all_flight_event_tests()
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to the API. Make sure the server is running.")
        except Exception as e:
            print(f"❌ Error running tests: {e}")
    
    if choice in ['2', '3']:
        try:
            simulate_flight_disruption_scenario()
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to the API. Make sure the server is running.")
        except Exception as e:
            print(f"❌ Error running simulation: {e}")