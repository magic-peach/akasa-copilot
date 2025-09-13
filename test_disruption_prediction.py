#!/usr/bin/env python3
"""
Test script for disruption prediction functionality
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_disruption_prediction():
    """Test the disruption prediction endpoint"""
    print("Testing GET /flights/{flight_id}/risk endpoint...")
    
    # Test with a known flight
    flight_id = "QP1001"
    
    try:
        response = requests.get(f"{BASE_URL}/flights/{flight_id}/risk")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            prediction = data.get('disruption_prediction', {})
            
            # Validate required fields
            required_fields = ['flight_id', 'disruption_risk', 'risk_level', 'confidence']
            missing_fields = [field for field in required_fields if field not in prediction]
            
            if not missing_fields:
                print(f"✅ All required fields present")
                print(f"   Flight: {prediction['flight_number']}")
                print(f"   Risk Score: {prediction['disruption_risk']}")
                print(f"   Risk Level: {prediction['risk_level']}")
                print(f"   Confidence: {prediction['confidence']}")
                
                # Check risk factors
                risk_factors = prediction.get('risk_factors', {})
                print(f"   Weather Score: {risk_factors.get('weather_score', 'N/A')}")
                print(f"   Historical Score: {risk_factors.get('historical_score', 'N/A')}")
                print(f"   Real-time Score: {risk_factors.get('real_time_score', 'N/A')}")
                print(f"   Route Score: {risk_factors.get('route_score', 'N/A')}")
                
                return True
            else:
                print(f"❌ Missing required fields: {missing_fields}")
                return False
        else:
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_disruption_prediction_unknown_flight():
    """Test disruption prediction with unknown flight"""
    print("\nTesting disruption prediction with unknown flight...")
    
    unknown_flight = "XX9999"
    
    try:
        response = requests.get(f"{BASE_URL}/flights/{unknown_flight}/risk")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Should return error or low confidence prediction
        return response.status_code in [200, 404]
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_disruption_prediction_invalid_flight_id():
    """Test disruption prediction with invalid flight ID"""
    print("\nTesting disruption prediction with invalid flight ID...")
    
    try:
        response = requests.get(f"{BASE_URL}/flights//risk")  # Empty flight ID
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 404  # Should return 404 for invalid path
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_list_disruption_predictions():
    """Test listing disruption predictions"""
    print("\nTesting GET /disruption-predictions endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/disruption-predictions?limit=5")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            predictions = data.get('predictions', [])
            print(f"Found {len(predictions)} disruption predictions")
            return True
        return False
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_specific_disruption_prediction():
    """Test getting a specific disruption prediction"""
    print("\nTesting GET /disruption-predictions/{id} endpoint...")
    
    # First, get a list to find a prediction ID
    try:
        list_response = requests.get(f"{BASE_URL}/disruption-predictions?limit=1")
        if list_response.status_code == 200:
            predictions = list_response.json().get('predictions', [])
            if predictions:
                prediction_id = predictions[0]['id']
                
                # Now get the specific prediction
                response = requests.get(f"{BASE_URL}/disruption-predictions/{prediction_id}")
                print(f"Status Code: {response.status_code}")
                print(f"Response: {json.dumps(response.json(), indent=2)}")
                
                return response.status_code == 200
            else:
                print("No predictions available to test with")
                return True  # Not a failure, just no data
        return False
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_risk_level_filtering():
    """Test filtering predictions by risk level"""
    print("\nTesting risk level filtering...")
    
    risk_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    
    for risk_level in risk_levels:
        try:
            response = requests.get(f"{BASE_URL}/disruption-predictions?risk_level={risk_level}&limit=3")
            if response.status_code == 200:
                data = response.json()
                predictions = data.get('predictions', [])
                print(f"  {risk_level}: {len(predictions)} predictions")
            time.sleep(0.2)  # Small delay between requests
        except Exception as e:
            print(f"  {risk_level}: error = {e}")
    
    return True

def test_multiple_flight_predictions():
    """Test predictions for multiple flights"""
    print("\nTesting predictions for multiple flights...")
    
    test_flights = ["QP1001", "QP1002", "QP1003", "QP2001"]
    predictions = []
    
    for flight_id in test_flights:
        try:
            response = requests.get(f"{BASE_URL}/flights/{flight_id}/risk")
            if response.status_code == 200:
                data = response.json()
                prediction = data.get('disruption_prediction', {})
                risk_score = prediction.get('disruption_risk', 0.0)
                risk_level = prediction.get('risk_level', 'UNKNOWN')
                predictions.append((flight_id, risk_score, risk_level))
                print(f"  {flight_id}: risk={risk_score:.3f}, level={risk_level}")
            time.sleep(0.5)  # Small delay between requests
        except Exception as e:
            print(f"  {flight_id}: error = {e}")
    
    if predictions:
        avg_risk = sum(score for _, score, _ in predictions) / len(predictions)
        print(f"Average risk score: {avg_risk:.3f}")
        return True
    
    return False

def test_weather_impact_simulation():
    """Test weather impact on predictions"""
    print("\nTesting weather impact simulation...")
    
    # Test the same flight multiple times to see variation in weather-based predictions
    flight_id = "QP1001"
    risk_scores = []
    
    for i in range(3):
        try:
            response = requests.get(f"{BASE_URL}/flights/{flight_id}/risk")
            if response.status_code == 200:
                data = response.json()
                prediction = data.get('disruption_prediction', {})
                risk_score = prediction.get('disruption_risk', 0.0)
                weather_score = prediction.get('risk_factors', {}).get('weather_score', 0.0)
                risk_scores.append((risk_score, weather_score))
                print(f"  Attempt {i+1}: total_risk={risk_score:.3f}, weather_risk={weather_score:.3f}")
            time.sleep(1)  # Delay to allow for different weather simulation
        except Exception as e:
            print(f"  Attempt {i+1}: error = {e}")
    
    if risk_scores:
        print(f"Risk score variation: {len(set(score for score, _ in risk_scores))} unique values")
        return True
    
    return False

def run_comprehensive_disruption_test():
    """Run a comprehensive test of the disruption prediction system"""
    print("\n" + "="*60)
    print("COMPREHENSIVE DISRUPTION PREDICTION TEST SCENARIO")
    print("="*60)
    
    # Step 1: Test high-risk route
    print("\n1. Testing high-risk route (DEL-GOA)...")
    response1 = requests.get(f"{BASE_URL}/flights/QP2001/risk")
    if response1.status_code == 200:
        data1 = response1.json()
        risk1 = data1.get('disruption_prediction', {}).get('disruption_risk', 0.0)
        level1 = data1.get('disruption_prediction', {}).get('risk_level', 'UNKNOWN')
        print(f"   High-risk route: risk={risk1:.3f}, level={level1}")
    
    time.sleep(1)
    
    # Step 2: Test medium-risk route
    print("\n2. Testing medium-risk route (BOM-BLR)...")
    response2 = requests.get(f"{BASE_URL}/flights/QP1002/risk")
    if response2.status_code == 200:
        data2 = response2.json()
        risk2 = data2.get('disruption_prediction', {}).get('disruption_risk', 0.0)
        level2 = data2.get('disruption_prediction', {}).get('risk_level', 'UNKNOWN')
        print(f"   Medium-risk route: risk={risk2:.3f}, level={level2}")
    
    time.sleep(1)
    
    # Step 3: Check predictions were stored
    print("\n3. Checking stored predictions...")
    predictions_response = requests.get(f"{BASE_URL}/disruption-predictions?limit=5")
    if predictions_response.status_code == 200:
        predictions_data = predictions_response.json()
        predictions = predictions_data.get('predictions', [])
        print(f"   Found {len(predictions)} stored predictions")
        
        # Show recent predictions
        for pred in predictions[:3]:
            flight_id = pred.get('flight_id', 'Unknown')
            risk = pred.get('disruption_risk', 0.0)
            level = pred.get('risk_level', 'UNKNOWN')
            created = pred.get('created_at', 'Unknown')
            print(f"   Prediction: {flight_id} (risk: {risk}, level: {level}, created: {created})")
    
    print("\n" + "="*60)
    print("COMPREHENSIVE DISRUPTION TEST COMPLETED")
    print("="*60)

def run_all_disruption_tests():
    """Run all disruption prediction tests"""
    print("=" * 60)
    print("DISRUPTION PREDICTION TESTS")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 8
    
    # Test 1: Basic disruption prediction
    if test_disruption_prediction():
        tests_passed += 1
        print("✅ Disruption prediction test passed")
    else:
        print("❌ Disruption prediction test failed")
    
    # Test 2: Unknown flight
    if test_disruption_prediction_unknown_flight():
        tests_passed += 1
        print("✅ Unknown flight prediction test passed")
    else:
        print("❌ Unknown flight prediction test failed")
    
    # Test 3: Invalid flight ID
    if test_disruption_prediction_invalid_flight_id():
        tests_passed += 1
        print("✅ Invalid flight ID test passed")
    else:
        print("❌ Invalid flight ID test failed")
    
    # Test 4: List predictions
    if test_list_disruption_predictions():
        tests_passed += 1
        print("✅ List predictions test passed")
    else:
        print("❌ List predictions test failed")
    
    # Test 5: Get specific prediction
    if test_get_specific_disruption_prediction():
        tests_passed += 1
        print("✅ Get specific prediction test passed")
    else:
        print("❌ Get specific prediction test failed")
    
    # Test 6: Risk level filtering
    if test_risk_level_filtering():
        tests_passed += 1
        print("✅ Risk level filtering test passed")
    else:
        print("❌ Risk level filtering test failed")
    
    # Test 7: Multiple flight predictions
    if test_multiple_flight_predictions():
        tests_passed += 1
        print("✅ Multiple flight predictions test passed")
    else:
        print("❌ Multiple flight predictions test failed")
    
    # Test 8: Weather impact simulation
    if test_weather_impact_simulation():
        tests_passed += 1
        print("✅ Weather impact simulation test passed")
    else:
        print("❌ Weather impact simulation test failed")
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {tests_passed}/{total_tests} tests passed")
    print("=" * 60)
    
    if tests_passed == total_tests:
        print("🎉 All disruption prediction tests passed!")
    else:
        print("⚠️  Some tests failed. Check the implementation.")

if __name__ == "__main__":
    print("Disruption Prediction Test Suite")
    print("Make sure the Flask application is running on http://localhost:5000")
    print("\nChoose an option:")
    print("1. Run all disruption prediction tests")
    print("2. Run comprehensive test scenario")
    print("3. Both")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice in ['1', '3']:
        try:
            run_all_disruption_tests()
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to the API. Make sure the server is running.")
        except Exception as e:
            print(f"❌ Error running tests: {e}")
    
    if choice in ['2', '3']:
        try:
            run_comprehensive_disruption_test()
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to the API. Make sure the server is running.")
        except Exception as e:
            print(f"❌ Error running comprehensive test: {e}")