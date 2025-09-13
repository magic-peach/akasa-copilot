#!/usr/bin/env python3
"""
Test script for voice chatbot and alert subscription functionality
"""

import requests
import json
import base64
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_voice_chatbot_text():
    """Test voice chatbot with text input"""
    print("Testing POST /chat/voice endpoint with text input...")
    
    test_requests = [
        {
            "user_id": "CUST001",
            "text_input": "What is the status of my flight QP1001?"
        },
        {
            "user_id": "CUST001", 
            "text_input": "Change my booking to next Monday"
        },
        {
            "user_id": "CUST001",
            "text_input": "I prefer window seats and vegetarian meals"
        },
        {
            "user_id": "CUST001",
            "text_input": "Subscribe me to flight alerts via SMS"
        }
    ]
    
    try:
        for i, chat_request in enumerate(test_requests):
            print(f"\nTest {i+1}: '{chat_request['text_input']}'")
            
            response = requests.post(
                f"{BASE_URL}/chat/voice",
                json=chat_request,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Intent: {data.get('intent', 'unknown')}")
                print(f"Confidence: {data.get('confidence', 0.0)}")
                print(f"Response: {data.get('response', {}).get('text', 'No response')}")
                print(f"Session ID: {data.get('session_id', 'None')}")
            else:
                print(f"Error: {response.json()}")
            
            time.sleep(1)
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_voice_chatbot_audio():
    """Test voice chatbot with mock audio input"""
    print("\nTesting POST /chat/voice endpoint with audio input...")
    
    # Create mock audio data (base64 encoded)
    mock_audio = base64.b64encode(b"mock_audio_data_for_testing").decode()
    
    chat_request = {
        "user_id": "CUST002",
        "audio_data": mock_audio
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat/voice",
            json=chat_request,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Transcribed: {data.get('user_input', 'No transcription')}")
            print(f"Intent: {data.get('intent', 'unknown')}")
            print(f"Response: {data.get('response', {}).get('text', 'No response')}")
            print(f"Audio Response: {'Yes' if data.get('response', {}).get('audio') else 'No'}")
            return True
        else:
            print(f"Error: {response.json()}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_alert_subscription():
    """Test alert subscription endpoint"""
    print("\nTesting POST /alerts/subscribe endpoint...")
    
    subscription_requests = [
        {
            "user_id": "CUST001",
            "request": "Subscribe me to flight alerts via SMS",
            "contact_info": "+91-9876543210"
        },
        {
            "user_id": "CUST002",
            "request": "I want email notifications for flight updates",
            "contact_info": "customer@email.com"
        },
        {
            "user_id": "CUST003",
            "channel": "push",
            "contact_info": "push_token_123",
            "subscription_type": "delay_alerts"
        }
    ]
    
    try:
        for i, sub_request in enumerate(subscription_requests):
            print(f"\nSubscription {i+1}: {sub_request.get('request', sub_request.get('channel'))}")
            
            response = requests.post(
                f"{BASE_URL}/alerts/subscribe",
                json=sub_request,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            if response.status_code == 201:
                data = response.json()
                subscription = data.get('subscription', {})
                print(f"Channel: {subscription.get('channel', 'unknown')}")
                print(f"Action: {subscription.get('action', 'unknown')}")
                print(f"Message: {data.get('message', 'No message')}")
            else:
                print(f"Error: {response.json()}")
            
            time.sleep(1)
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_chat_history():
    """Test chat history retrieval"""
    print("\nTesting GET /chat/history/{user_id} endpoint...")
    
    user_id = "CUST001"
    
    try:
        response = requests.get(f"{BASE_URL}/chat/history/{user_id}?limit=5")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            history = data.get('chat_history', [])
            print(f"Found {len(history)} chat history entries")
            
            for i, session in enumerate(history[:3]):
                query_type = session.get('query_type', 'unknown')
                confidence = session.get('confidence_score', 0.0)
                created = session.get('created_at', 'unknown')
                print(f"  {i+1}. {query_type} (confidence: {confidence}, created: {created})")
            
            return True
        else:
            print(f"Error: {response.json()}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_list_alert_subscriptions():
    """Test listing alert subscriptions"""
    print("\nTesting GET /alerts/subscriptions endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/alerts/subscriptions?limit=5")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            subscriptions = data.get('subscriptions', [])
            print(f"Found {len(subscriptions)} alert subscriptions")
            
            for sub in subscriptions:
                user_id = sub.get('user_id', 'unknown')
                channel = sub.get('channel', 'unknown')
                active = sub.get('active', False)
                print(f"  User: {user_id}, Channel: {channel}, Active: {active}")
            
            return True
        else:
            print(f"Error: {response.json()}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_conversational_memory():
    """Test conversational memory and context"""
    print("\nTesting conversational memory...")
    
    user_id = "CUST004"
    
    # Conversation sequence to test memory
    conversation = [
        "What is the status of flight QP1001?",
        "Change that flight to Monday",  # Should remember QP1001
        "What about the risk of delay?",  # Should still remember QP1001
        "Subscribe me to alerts for that flight"  # Should remember context
    ]
    
    try:
        for i, message in enumerate(conversation):
            print(f"\nConversation step {i+1}: '{message}'")
            
            chat_request = {
                "user_id": user_id,
                "text_input": message
            }
            
            response = requests.post(
                f"{BASE_URL}/chat/voice",
                json=chat_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"Intent: {data.get('intent', 'unknown')}")
                print(f"Response: {data.get('response', {}).get('text', 'No response')[:100]}...")
                print(f"Context Used: {data.get('conversation_context', {}).get('history_used', 0)} previous messages")
            else:
                print(f"Error: {response.json()}")
            
            time.sleep(1.5)  # Allow time for session storage
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_invalid_voice_requests():
    """Test voice chatbot with invalid requests"""
    print("\nTesting invalid voice requests...")
    
    invalid_requests = [
        {},  # Empty request
        {"user_id": "CUST001"},  # No input
        {"text_input": "Hello"},  # No user_id
        {"user_id": "", "text_input": "Hello"},  # Empty user_id
    ]
    
    try:
        for i, invalid_request in enumerate(invalid_requests):
            print(f"\nInvalid request {i+1}: {invalid_request}")
            
            response = requests.post(
                f"{BASE_URL}/chat/voice",
                json=invalid_request,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            if response.status_code == 400:
                print(f"Expected error: {response.json().get('message', 'Unknown error')}")
            else:
                print(f"Unexpected response: {response.json()}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_comprehensive_voice_test():
    """Run a comprehensive test of the voice chatbot system"""
    print("\n" + "="*60)
    print("COMPREHENSIVE VOICE CHATBOT TEST SCENARIO")
    print("="*60)
    
    user_id = "CUST_VOICE_TEST"
    
    # Step 1: Initial greeting
    print("\n1. Testing initial greeting...")
    greeting_request = {
        "user_id": user_id,
        "text_input": "Hello, I need help with my flight"
    }
    
    response1 = requests.post(f"{BASE_URL}/chat/voice", json=greeting_request)
    if response1.status_code == 200:
        data1 = response1.json()
        print(f"   Response: {data1.get('response', {}).get('text', 'No response')}")
    
    time.sleep(1)
    
    # Step 2: Flight status inquiry
    print("\n2. Testing flight status inquiry...")
    status_request = {
        "user_id": user_id,
        "text_input": "Check the status of flight QP1001"
    }
    
    response2 = requests.post(f"{BASE_URL}/chat/voice", json=status_request)
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"   Intent: {data2.get('intent', 'unknown')}")
        print(f"   Response: {data2.get('response', {}).get('text', 'No response')}")
    
    time.sleep(1)
    
    # Step 3: Alert subscription
    print("\n3. Testing alert subscription...")
    subscribe_request = {
        "user_id": user_id,
        "request": "Subscribe me to SMS alerts",
        "contact_info": "+91-9999999999"
    }
    
    response3 = requests.post(f"{BASE_URL}/alerts/subscribe", json=subscribe_request)
    if response3.status_code == 201:
        data3 = response3.json()
        print(f"   Subscription: {data3.get('message', 'No message')}")
    
    time.sleep(1)
    
    # Step 4: Check conversation history
    print("\n4. Checking conversation history...")
    history_response = requests.get(f"{BASE_URL}/chat/history/{user_id}")
    if history_response.status_code == 200:
        history_data = history_response.json()
        history = history_data.get('chat_history', [])
        print(f"   Found {len(history)} conversation entries")
    
    print("\n" + "="*60)
    print("COMPREHENSIVE VOICE TEST COMPLETED")
    print("="*60)

def run_all_voice_tests():
    """Run all voice chatbot tests"""
    print("=" * 60)
    print("VOICE CHATBOT & ALERT SUBSCRIPTION TESTS")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 7
    
    # Test 1: Voice chatbot with text
    if test_voice_chatbot_text():
        tests_passed += 1
        print("✅ Voice chatbot text test passed")
    else:
        print("❌ Voice chatbot text test failed")
    
    # Test 2: Voice chatbot with audio
    if test_voice_chatbot_audio():
        tests_passed += 1
        print("✅ Voice chatbot audio test passed")
    else:
        print("❌ Voice chatbot audio test failed")
    
    # Test 3: Alert subscription
    if test_alert_subscription():
        tests_passed += 1
        print("✅ Alert subscription test passed")
    else:
        print("❌ Alert subscription test failed")
    
    # Test 4: Chat history
    if test_chat_history():
        tests_passed += 1
        print("✅ Chat history test passed")
    else:
        print("❌ Chat history test failed")
    
    # Test 5: List subscriptions
    if test_list_alert_subscriptions():
        tests_passed += 1
        print("✅ List subscriptions test passed")
    else:
        print("❌ List subscriptions test failed")
    
    # Test 6: Conversational memory
    if test_conversational_memory():
        tests_passed += 1
        print("✅ Conversational memory test passed")
    else:
        print("❌ Conversational memory test failed")
    
    # Test 7: Invalid requests
    if test_invalid_voice_requests():
        tests_passed += 1
        print("✅ Invalid requests test passed")
    else:
        print("❌ Invalid requests test failed")
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {tests_passed}/{total_tests} tests passed")
    print("=" * 60)
    
    if tests_passed == total_tests:
        print("🎉 All voice chatbot tests passed!")
    else:
        print("⚠️  Some tests failed. Check the implementation.")

if __name__ == "__main__":
    print("Voice Chatbot & Alert Subscription Test Suite")
    print("Make sure the Flask application is running on http://localhost:5000")
    print("\nChoose an option:")
    print("1. Run all voice chatbot tests")
    print("2. Run comprehensive test scenario")
    print("3. Both")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice in ['1', '3']:
        try:
            run_all_voice_tests()
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to the API. Make sure the server is running.")
        except Exception as e:
            print(f"❌ Error running tests: {e}")
    
    if choice in ['2', '3']:
        try:
            run_comprehensive_voice_test()
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to the API. Make sure the server is running.")
        except Exception as e:
            print(f"❌ Error running comprehensive test: {e}")