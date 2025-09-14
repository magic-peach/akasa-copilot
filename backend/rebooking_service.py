"""
Rebooking service for Akasa Booking API
Handles flight change requests, availability checking, and automatic rebooking
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from models import Booking

class RebookingService:
    """Service class for handling booking changes and rebooking operations"""
    
    # Mock flight data for availability checking
    MOCK_FLIGHTS = {
        'DEL-BOM': ['QP1001', 'QP1003', 'QP1005', 'QP1007'],
        'BOM-DEL': ['QP1002', 'QP1004', 'QP1006', 'QP1008'],
        'BOM-BLR': ['QP2001', 'QP2003', 'QP2005'],
        'BLR-BOM': ['QP2002', 'QP2004', 'QP2006'],
        'DEL-BLR': ['QP3001', 'QP3003'],
        'BLR-DEL': ['QP3002', 'QP3004'],
        'BOM-HYD': ['QP4001', 'QP4003'],
        'HYD-BOM': ['QP4002', 'QP4004']
    }
    
    # Base prices for different routes (in INR)
    BASE_PRICES = {
        'DEL-BOM': 4500,
        'BOM-DEL': 4500,
        'BOM-BLR': 3500,
        'BLR-BOM': 3500,
        'DEL-BLR': 5500,
        'BLR-DEL': 5500,
        'BOM-HYD': 3000,
        'HYD-BOM': 3000
    }
    
    def check_availability(self, origin: str, destination: str, new_date: str) -> List[Dict[str, Any]]:
        """
        Mock function to check flight availability for a given route and date
        
        Args:
            origin: Origin airport code
            destination: Destination airport code
            new_date: Requested date in YYYY-MM-DD format
            
        Returns:
            List of available flight options
        """
        route_key = f"{origin}-{destination}"
        available_flights = self.MOCK_FLIGHTS.get(route_key, [])
        
        if not available_flights:
            return []
        
        # Parse the requested date
        try:
            request_date = datetime.strptime(new_date, '%Y-%m-%d')
        except ValueError:
            return []
        
        # Check if the date is in the future
        if request_date.date() <= datetime.now().date():
            return []
        
        # Generate mock availability (simulate some flights being full)
        options = []
        base_price = self.BASE_PRICES.get(route_key, 4000)
        
        for flight_num in available_flights:
            # Randomly simulate availability (80% chance of being available)
            if random.random() < 0.8:
                # Add some price variation based on demand simulation
                price_multiplier = random.uniform(0.9, 1.4)
                price = int(base_price * price_multiplier)
                
                # Generate different time slots
                departure_times = ['06:00', '09:30', '13:15', '17:45', '21:20']
                departure_time = random.choice(departure_times)
                
                options.append({
                    'flight_number': flight_num,
                    'departure_time': departure_time,
                    'price': price,
                    'seats_available': random.randint(5, 45),
                    'aircraft_type': random.choice(['A320', 'B737', 'A321']),
                    'duration': self._calculate_flight_duration(origin, destination)
                })
        
        # Sort by price
        options.sort(key=lambda x: x['price'])
        return options
    
    def calculate_cost_difference(self, original_booking: Dict[str, Any], new_option: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate the cost difference between original booking and new option
        
        Args:
            original_booking: Original booking details
            new_option: New flight option details
            
        Returns:
            Cost difference information
        """
        # Get original route price (stub - in real implementation, this would come from booking history)
        original_route = f"{original_booking['origin']}-{original_booking['destination']}"
        original_price = self.BASE_PRICES.get(original_route, 4000)
        
        # Add some variation to simulate original booking price
        original_price = int(original_price * random.uniform(0.95, 1.1))
        
        new_price = new_option['price']
        difference = new_price - original_price
        
        # Calculate change fee (flat fee for changes)
        change_fee = 500 if difference >= 0 else 200  # Lower fee for downgrades
        
        total_cost = difference + change_fee if difference > 0 else change_fee
        
        return {
            'original_price': original_price,
            'new_price': new_price,
            'price_difference': difference,
            'change_fee': change_fee,
            'total_cost': max(total_cost, 0),  # Never negative
            'refund_amount': abs(difference) - change_fee if difference < 0 and abs(difference) > change_fee else 0
        }
    
    def auto_rebook(self, booking: Dict[str, Any], option: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate automatic rebooking with the selected option
        
        Args:
            booking: Original booking details
            option: Selected rebooking option
            
        Returns:
            New booking confirmation details
        """
        # Generate new booking ID and confirmation
        import uuid
        new_booking_id = str(uuid.uuid4())
        confirmation_code = f"AK{random.randint(100000, 999999)}"
        
        # Create updated booking details
        updated_booking = {
            'id': new_booking_id,
            'customer_id': booking['customer_id'],
            'flight_number': option['flight_number'],
            'origin': booking['origin'],
            'destination': booking['destination'],
            'depart_date': option.get('depart_date', booking['depart_date']),
            'departure_time': option['departure_time'],
            'status': 'confirmed',
            'confirmation_code': confirmation_code,
            'aircraft_type': option['aircraft_type'],
            'seat_number': f"{random.randint(1, 30)}{random.choice(['A', 'B', 'C', 'D', 'E', 'F'])}",
            'gate': f"G{random.randint(1, 20)}",
            'terminal': random.choice(['T1', 'T2', 'T3']),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'rebooking_reason': 'Customer requested change',
            'original_booking_id': booking['id']
        }
        
        return {
            'success': True,
            'message': 'Booking successfully changed',
            'new_booking': updated_booking,
            'confirmation_code': confirmation_code,
            'change_summary': {
                'original_flight': booking['flight_number'],
                'new_flight': option['flight_number'],
                'original_date': booking['depart_date'],
                'new_date': option.get('depart_date', booking['depart_date']),
                'cost_impact': self.calculate_cost_difference(booking, option)
            }
        }
    
    def _calculate_flight_duration(self, origin: str, destination: str) -> str:
        """Calculate estimated flight duration based on route"""
        # Mock flight durations (in reality, this would be from a flight database)
        durations = {
            'DEL-BOM': '2h 15m',
            'BOM-DEL': '2h 15m',
            'BOM-BLR': '1h 30m',
            'BLR-BOM': '1h 30m',
            'DEL-BLR': '2h 45m',
            'BLR-DEL': '2h 45m',
            'BOM-HYD': '1h 15m',
            'HYD-BOM': '1h 15m'
        }
        
        return durations.get(f"{origin}-{destination}", "2h 00m")

# Initialize the service
rebooking_service = RebookingService()