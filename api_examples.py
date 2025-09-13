#!/usr/bin/env python3
"""
API Usage Examples for Akasa Booking API
Demonstrates how to use the booking and rebooking endpoints
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000"

def example_booking_workflow():
    """Demonstrate a complete booking and rebooking workflow"""
    print("=" * 60)
    print("AKASA BOOKING API - USAGE EXAMPLES")
    print("=" * 60)
    
    # Step 1: Create a new booking
    print("\n1. Creating a new booking...")
    booking_data = {
        "customer_id": "CUST001",
        "flight_number": "QP1001",
        "origin": "DEL",
        "destination": "BOM",
        "depart_date": "2024-02-15",
        "status": "confirmed"
    }
    
    response = requests.post(f"{BASE_URL}/bookings", json=booking_data)
    if response.status_code == 201:
        booking = response.json()["booking"]
        booking_id = booking["id"]
        print(f"✅ Booking created successfully!")
        print(f"   Booking ID: {booking_id}")
        print(f"   Flight: {booking['flight_number']}")
        print(f"   Route: {booking['origin']} → {booking['destination']}")
        print(f"   Date: {booking['depart_date']}")
    else:
        print(f"❌ Failed to create booking: {response.json()}")
        return
    
    # Step 2: Request a booking change
    print(f"\n2. Requesting a booking change...")
    change_request = {
        "new_date": "2024-03-15"
    }
    
    response = requests.post(
        f"{BASE_URL}/bookings/{booking_id}/request-change",
        json=change_request
    )
    
    if response.status_code == 200:
        change_data = response.json()
        options = change_data["available_options"]
        print(f"✅ Found {len(options)} rebooking options!")
        
        if options:
            best_option = options[0]  # Take the first (cheapest) option
            print(f"   Best Option:")
            print(f"   Flight: {best_option['flight_number']}")
            print(f"   Time: {best_option['departure_time']}")
            print(f"   Price: ₹{best_option['price']}")
            print(f"   Cost Impact: ₹{best_option['cost_breakdown']['total_cost']}")
            
            # Step 3: Auto-rebook with the selected option
            print(f"\n3. Auto-rebooking with selected option...")
            rebook_data = {
                "flight_number": best_option['flight_number'],
                "depart_date": best_option['depart_date'],
                "departure_time": best_option['departure_time'],
                "price": best_option['price'],
                "aircraft_type": best_option.get('aircraft_type', 'A320')
            }
            
            response = requests.post(
                f"{BASE_URL}/bookings/{booking_id}/auto-rebook",
                json=rebook_data
            )
            
            if response.status_code == 200:
                rebook_result = response.json()
                new_booking = rebook_result["new_booking"]
                print(f"✅ Rebooking successful!")
                print(f"   New Booking ID: {new_booking['id']}")
                print(f"   Confirmation Code: {rebook_result['confirmation_code']}")
                print(f"   New Flight: {new_booking['flight_number']}")
                print(f"   New Date: {new_booking['depart_date']}")
                print(f"   Seat: {new_booking.get('seat_number', 'TBD')}")
                print(f"   Gate: {new_booking.get('gate', 'TBD')}")
                
                # Step 4: Verify the new booking
                print(f"\n4. Verifying the new booking...")
                response = requests.get(f"{BASE_URL}/bookings/{new_booking['id']}")
                if response.status_code == 200:
                    verified_booking = response.json()["booking"]
                    print(f"✅ New booking verified!")
                    print(f"   Status: {verified_booking['status']}")
                    print(f"   Created: {verified_booking['created_at']}")
                else:
                    print(f"❌ Failed to verify new booking")
                
            else:
                print(f"❌ Rebooking failed: {response.json()}")
        else:
            print("❌ No rebooking options available")
    else:
        print(f"❌ Change request failed: {response.json()}")
    
    print("\n" + "=" * 60)
    print("WORKFLOW COMPLETED")
    print("=" * 60)

def example_api_calls():
    """Show individual API call examples"""
    print("\n" + "=" * 60)
    print("INDIVIDUAL API CALL EXAMPLES")
    print("=" * 60)
    
    # Health check
    print("\n📋 Health Check:")
    print("GET /health")
    print("curl -X GET http://localhost:5000/health")
    
    # Create booking
    print("\n📝 Create Booking:")
    print("POST /bookings")
    print("""curl -X POST http://localhost:5000/bookings \\
  -H "Content-Type: application/json" \\
  -d '{
    "customer_id": "CUST001",
    "flight_number": "QP1001",
    "origin": "DEL",
    "destination": "BOM",
    "depart_date": "2024-02-15",
    "status": "confirmed"
  }'""")
    
    # Get booking
    print("\n🔍 Get Booking:")
    print("GET /bookings/{id}")
    print("curl -X GET http://localhost:5000/bookings/{booking_id}")
    
    # List bookings
    print("\n📋 List Bookings:")
    print("GET /bookings")
    print("curl -X GET 'http://localhost:5000/bookings?customer_id=CUST001&limit=10'")
    
    # Request change
    print("\n🔄 Request Booking Change:")
    print("POST /bookings/{id}/request-change")
    print("""curl -X POST http://localhost:5000/bookings/{booking_id}/request-change \\
  -H "Content-Type: application/json" \\
  -d '{
    "new_date": "2024-03-15"
  }'""")
    
    # Auto-rebook
    print("\n🚀 Auto-Rebook:")
    print("POST /bookings/{id}/auto-rebook")
    print("""curl -X POST http://localhost:5000/bookings/{booking_id}/auto-rebook \\
  -H "Content-Type: application/json" \\
  -d '{
    "flight_number": "QP1001",
    "depart_date": "2024-03-15",
    "departure_time": "09:30",
    "price": 4800,
    "aircraft_type": "A320"
  }'""")

if __name__ == "__main__":
    print("Akasa Booking API - Usage Examples")
    print("Make sure the Flask application is running on http://localhost:5000")
    print("\nChoose an option:")
    print("1. Run complete booking workflow example")
    print("2. Show API call examples")
    print("3. Both")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice in ['1', '3']:
        try:
            example_booking_workflow()
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to the API. Make sure the server is running.")
        except Exception as e:
            print(f"❌ Error running workflow: {e}")
    
    if choice in ['2', '3']:
        example_api_calls()