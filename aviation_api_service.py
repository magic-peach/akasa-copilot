"""Aviation API Service for Akasa Airlines
Handles real-time flight data fetching from aviation API
"""

import requests
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AviationApiService:
    """Service to interact with Aviation API for real-time flight data"""
    
    def __init__(self):
        self.api_key = "be98ccc8ef17b8414acdd27b85b7446e"  # API key provided
        self.base_url = "https://aviation-edge.com/v2/public"
        self.cache = {}  # Simple cache to reduce API calls
        self.cache_expiry = 300  # Cache expiry in seconds (5 minutes)
        self.cache_timestamps = {}  # Track when cache entries were created
    
    def get_flight_status(self, flight_number: str) -> Dict[str, Any]:
        """Get real-time status of a specific flight"""
        try:
            cache_key = f"flight_status_{flight_number}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            endpoint = f"{self.base_url}/flightStatus"
            params = {
                "key": self.api_key,
                "flightIata": flight_number
            }
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            self._add_to_cache(cache_key, data)
            
            logger.info(f"Retrieved flight status for {flight_number}")
            return data
        except Exception as e:
            logger.error(f"Error getting flight status for {flight_number}: {str(e)}")
            return {"error": str(e), "flight_number": flight_number}
    
    def get_airport_delays(self, airport_code: str) -> Dict[str, Any]:
        """Get current delays at a specific airport"""
        try:
            cache_key = f"airport_delays_{airport_code}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            endpoint = f"{self.base_url}/timetable"
            params = {
                "key": self.api_key,
                "iataCode": airport_code,
                "type": "departure"
            }
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Process data to extract delay information
            delay_info = self._process_delay_information(data, airport_code)
            self._add_to_cache(cache_key, delay_info)
            
            logger.info(f"Retrieved delay information for {airport_code}")
            return delay_info
        except Exception as e:
            logger.error(f"Error getting airport delays for {airport_code}: {str(e)}")
            return {"error": str(e), "airport_code": airport_code}
    
    def get_flight_price(self, origin: str, destination: str, date: str) -> Dict[str, Any]:
        """Get flight price information"""
        try:
            cache_key = f"flight_price_{origin}_{destination}_{date}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            endpoint = f"{self.base_url}/flightPrice"
            params = {
                "key": self.api_key,
                "depIata": origin,
                "arrIata": destination,
                "date": date
            }
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            self._add_to_cache(cache_key, data)
            
            logger.info(f"Retrieved flight prices for {origin} to {destination} on {date}")
            return data
        except Exception as e:
            logger.error(f"Error getting flight prices: {str(e)}")
            return {"error": str(e), "route": f"{origin}-{destination}"}
    
    def get_flight_by_pnr(self, pnr: str) -> Dict[str, Any]:
        """Get flight details by PNR number"""
        try:
            cache_key = f"flight_pnr_{pnr}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Note: This is a mock implementation as PNR lookup typically requires
            # airline-specific APIs and authentication
            endpoint = f"{self.base_url}/pnr"
            params = {
                "key": self.api_key,
                "pnr": pnr
            }
            
            # In a real implementation, this would call the actual API
            # For now, we'll simulate a response
            simulated_data = self._simulate_pnr_response(pnr)
            self._add_to_cache(cache_key, simulated_data)
            
            logger.info(f"Retrieved flight details for PNR {pnr}")
            return simulated_data
        except Exception as e:
            logger.error(f"Error getting flight details for PNR {pnr}: {str(e)}")
            return {"error": str(e), "pnr": pnr}
    
    def get_airport_weather(self, airport_code: str) -> Dict[str, Any]:
        """Get current weather at a specific airport"""
        try:
            cache_key = f"airport_weather_{airport_code}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            endpoint = f"{self.base_url}/weather"
            params = {
                "key": self.api_key,
                "iataCode": airport_code
            }
            
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            self._add_to_cache(cache_key, data)
            
            logger.info(f"Retrieved weather information for {airport_code}")
            return data
        except Exception as e:
            logger.error(f"Error getting airport weather for {airport_code}: {str(e)}")
            return {"error": str(e), "airport_code": airport_code}
    
    def _process_delay_information(self, data: List[Dict[str, Any]], airport_code: str) -> Dict[str, Any]:
        """Process raw timetable data to extract delay information"""
        try:
            delayed_flights = 0
            total_flights = len(data)
            avg_delay_minutes = 0
            delay_minutes_sum = 0
            
            for flight in data:
                departure = flight.get('departure', {})
                scheduled = departure.get('scheduledTime', '')
                actual = departure.get('actualTime', '')
                
                if scheduled and actual:
                    try:
                        scheduled_time = datetime.strptime(scheduled, '%H:%M')
                        actual_time = datetime.strptime(actual, '%H:%M')
                        
                        # Handle cases where delay crosses midnight
                        if actual_time < scheduled_time:
                            actual_time = actual_time + timedelta(days=1)
                        
                        delay_minutes = (actual_time - scheduled_time).total_seconds() / 60
                        
                        if delay_minutes > 15:  # Consider delays over 15 minutes
                            delayed_flights += 1
                            delay_minutes_sum += delay_minutes
                    except ValueError:
                        continue
            
            if delayed_flights > 0:
                avg_delay_minutes = delay_minutes_sum / delayed_flights
            
            delay_percentage = (delayed_flights / total_flights) * 100 if total_flights > 0 else 0
            
            return {
                'airport_code': airport_code,
                'total_flights': total_flights,
                'delayed_flights': delayed_flights,
                'delay_percentage': round(delay_percentage, 2),
                'avg_delay_minutes': round(avg_delay_minutes, 2),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error processing delay information: {str(e)}")
            return {
                'airport_code': airport_code,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _simulate_pnr_response(self, pnr: str) -> Dict[str, Any]:
        """Simulate a PNR response for demonstration purposes"""
        airlines = ['Akasa Air', 'IndiGo', 'Vistara', 'Air India', 'SpiceJet', 'Go First']
        origins = ['DEL', 'BOM', 'BLR', 'HYD', 'MAA', 'CCU']
        destinations = ['BOM', 'DEL', 'BLR', 'HYD', 'MAA', 'CCU']
        
        import random
        from datetime import datetime, timedelta
        
        # Generate a deterministic but seemingly random response based on PNR
        pnr_hash = sum(ord(c) for c in pnr)
        random.seed(pnr_hash)
        
        airline = airlines[pnr_hash % len(airlines)]
        origin = origins[pnr_hash % len(origins)]
        
        # Ensure destination is different from origin
        dest_idx = (pnr_hash + 1) % len(destinations)
        destination = destinations[dest_idx]
        
        # Generate flight number
        flight_number = f"{airline[:2].upper()}{100 + (pnr_hash % 900)}"
        
        # Generate dates
        today = datetime.now()
        departure_date = today + timedelta(days=(pnr_hash % 30))
        departure_time = f"{8 + (pnr_hash % 14):02d}:{(pnr_hash % 60):02d}"
        arrival_time = f"{(10 + (pnr_hash % 14)) % 24:02d}:{(pnr_hash % 60):02d}"
        
        return {
            'pnr': pnr,
            'passenger_name': f"PASSENGER/{pnr[:3].upper()}",
            'flight_details': {
                'airline': airline,
                'flight_number': flight_number,
                'origin': origin,
                'destination': destination,
                'departure_date': departure_date.strftime('%Y-%m-%d'),
                'departure_time': departure_time,
                'arrival_time': arrival_time,
                'status': random.choice(['Confirmed', 'Checked In', 'Boarding', 'Departed', 'Arrived'])
            },
            'seat': f"{random.choice(['A', 'B', 'C', 'D', 'E', 'F'])}{random.randint(1, 30)}",
            'class': random.choice(['Economy', 'Premium Economy', 'Business']),
            'baggage_allowance': f"{15 + (pnr_hash % 10)} kg",
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _add_to_cache(self, key: str, data: Any) -> None:
        """Add data to cache with timestamp"""
        self.cache[key] = data
        self.cache_timestamps[key] = datetime.utcnow().timestamp()
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache if not expired"""
        if key in self.cache and key in self.cache_timestamps:
            timestamp = self.cache_timestamps[key]
            now = datetime.utcnow().timestamp()
            
            if now - timestamp < self.cache_expiry:
                return self.cache[key]
        
        return None

# Create a global instance for easy import
aviation_api_service = AviationApiService()