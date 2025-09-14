"""
GenAI Flight Search Agent for FastAPI
Intelligent flight selection based on multiple criteria
"""

import random
import uuid
from datetime import datetime, timedelta, time
from typing import Dict, List, Any, Optional, Tuple
from database import db
from fastapi_models import FlightInfo, AirlineEnum, FlightSearchRequest
import logging

logger = logging.getLogger(__name__)

class FlightSearchAgent:
    """GenAI agent for intelligent flight search and selection"""
    
    def __init__(self):
        # Scoring weights for flight selection
        self.weights = {
            'price': 0.4,      # 40% weight on price
            'duration': 0.3,   # 30% weight on duration
            'risk': 0.2,       # 20% weight on risk factor
            'preference': 0.1  # 10% weight on preferences
        }
        
        # Risk factors by route and time
        self.route_risks = {
            'DEL-BOM': 0.3, 'BOM-DEL': 0.3,
            'DEL-BLR': 0.4, 'BLR-DEL': 0.4,
            'BOM-BLR': 0.2, 'BLR-BOM': 0.2,
            'DEL-GOA': 0.5, 'GOA-DEL': 0.5,
            'BOM-HYD': 0.25, 'HYD-BOM': 0.25
        }
        
        # Occasion-based preferences
        self.occasion_preferences = {
            'business': {'priority': 'time', 'risk_tolerance': 0.3},
            'leisure': {'priority': 'price', 'risk_tolerance': 0.6},
            'emergency': {'priority': 'time', 'risk_tolerance': 0.8},
            'family': {'priority': 'balance', 'risk_tolerance': 0.4}
        }
    
    def search_flights(self, search_request: FlightSearchRequest) -> Dict[str, Any]:
        """
        Main flight search function with GenAI decision making
        
        Args:
            search_request: Flight search criteria
            
        Returns:
            Search results with best flight and alternatives
        """
        try:
            start_time = datetime.utcnow()
            
            logger.info(f"Starting flight search: {search_request.origin} -> {search_request.destination} on {search_request.date}")
            
            # Step 1: Get available flights from database/mock data
            available_flights = self._get_available_flights(search_request)
            
            if not available_flights:
                return self._create_no_flights_response(search_request)
            
            # Step 2: Calculate risk factors for each flight
            flights_with_risk = self._calculate_risk_factors(available_flights, search_request)
            
            # Step 3: Score flights based on criteria
            scored_flights = self._score_flights(flights_with_risk, search_request)
            
            # Step 4: Select best flight using GenAI logic
            best_flight, reasoning = self._select_best_flight(scored_flights, search_request)
            
            # Step 5: Get alternatives (top 3-5 other options)
            alternatives = self._get_alternatives(scored_flights, best_flight, max_alternatives=4)
            
            # Step 6: Log search session
            session_id = self._log_search_session(search_request, best_flight, alternatives, reasoning)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(f"Flight search completed: found {len(available_flights)} flights, selected {best_flight['flight_number']}")
            
            return {
                'best_flight': best_flight,
                'alternatives': alternatives,
                'reasoning': reasoning,
                'search_criteria': search_request.dict(),
                'total_results': len(available_flights),
                'processing_time_ms': round(processing_time, 2),
                'session_id': session_id
            }
            
        except Exception as e:
            logger.error(f"Error in flight search: {str(e)}")
            return self._create_error_response(search_request, str(e))
    
    def _get_available_flights(self, search_request: FlightSearchRequest) -> List[Dict[str, Any]]:
        """Get available flights from database or generate mock data"""
        try:
            # Try to get flights from database first
            supabase = db.get_client()
            result = supabase.table('flights').select('*').eq('origin', search_request.origin).eq('destination', search_request.destination).execute()
            
            db_flights = result.data or []
            
            # If we have database flights, use them
            if db_flights:
                return self._format_db_flights(db_flights, search_request)
            
            # Otherwise, generate mock flights
            return self._generate_mock_flights(search_request)
            
        except Exception as e:
            logger.error(f"Error getting available flights: {str(e)}")
            return self._generate_mock_flights(search_request)
    
    def _generate_mock_flights(self, search_request: FlightSearchRequest) -> List[Dict[str, Any]]:
        """Generate realistic mock flight data"""
        try:
            flights = []
            airlines = list(AirlineEnum)
            
            # Generate 5-8 mock flights
            num_flights = random.randint(5, 8)
            
            for i in range(num_flights):
                airline = random.choice(airlines)
                
                # Generate realistic flight times
                base_departure = datetime.combine(search_request.date, time(6, 0))
                departure_offset = timedelta(hours=random.randint(0, 16), minutes=random.choice([0, 15, 30, 45]))
                departure_time = base_departure + departure_offset
                
                # Calculate duration based on route
                route_key = f"{search_request.origin}-{search_request.destination}"
                base_duration_minutes = self._get_base_duration(route_key)
                actual_duration = base_duration_minutes + random.randint(-15, 30)
                arrival_time = departure_time + timedelta(minutes=actual_duration)
                
                # Generate price based on airline and time
                base_price = self._get_base_price(route_key)
                price_variation = random.uniform(0.8, 1.4)
                
                # Peak time pricing
                if 7 <= departure_time.hour <= 9 or 17 <= departure_time.hour <= 19:
                    price_variation *= 1.2
                
                price = int(base_price * price_variation)
                
                flight = {
                    'id': str(uuid.uuid4()),
                    'airline': airline.value,
                    'flight_number': f"{self._get_airline_code(airline)}{random.randint(1000, 9999)}",
                    'origin': search_request.origin,
                    'destination': search_request.destination,
                    'departure_time': departure_time.isoformat(),
                    'arrival_time': arrival_time.isoformat(),
                    'duration': self._format_duration(actual_duration),
                    'price': price,
                    'risk_factor': 0.0,  # Will be calculated later
                    'aircraft_type': random.choice(['A320', 'B737', 'A321', 'B738']),
                    'seats_available': random.randint(10, 150)
                }
                
                flights.append(flight)
            
            return flights
            
        except Exception as e:
            logger.error(f"Error generating mock flights: {str(e)}")
            return []
    
    def _calculate_risk_factors(self, flights: List[Dict[str, Any]], search_request: FlightSearchRequest) -> List[Dict[str, Any]]:
        """Calculate risk factors for each flight"""
        try:
            route_key = f"{search_request.origin}-{search_request.destination}"
            base_risk = self.route_risks.get(route_key, 0.3)
            
            for flight in flights:
                departure_time = datetime.fromisoformat(flight['departure_time'])
                
                # Base route risk
                risk_factor = base_risk
                
                # Time-based risk adjustments
                hour = departure_time.hour
                if hour < 6 or hour > 22:  # Very early or late flights
                    risk_factor += 0.2
                elif 6 <= hour <= 8 or 18 <= hour <= 20:  # Peak hours
                    risk_factor += 0.1
                
                # Weather-based risk (mock)
                weather_risk = random.uniform(0.0, 0.3)
                risk_factor += weather_risk
                
                # Airline-based risk (some airlines more reliable)
                airline_risk_map = {
                    'Akasa Air': 0.1,
                    'Vistara': 0.15,
                    'IndiGo': 0.2,
                    'Air India': 0.25,
                    'SpiceJet': 0.3
                }
                airline_risk = airline_risk_map.get(flight['airline'], 0.2)
                risk_factor += airline_risk
                
                # Cap risk factor at 1.0
                flight['risk_factor'] = min(risk_factor, 1.0)
            
            return flights
            
        except Exception as e:
            logger.error(f"Error calculating risk factors: {str(e)}")
            return flights
    
    def _score_flights(self, flights: List[Dict[str, Any]], search_request: FlightSearchRequest) -> List[Dict[str, Any]]:
        """Score flights based on multiple criteria"""
        try:
            if not flights:
                return []
            
            # Normalize values for scoring
            prices = [f['price'] for f in flights]
            durations = [self._duration_to_minutes(f['duration']) for f in flights]
            risks = [f['risk_factor'] for f in flights]
            
            min_price, max_price = min(prices), max(prices)
            min_duration, max_duration = min(durations), max(durations)
            min_risk, max_risk = min(risks), max(risks)
            
            for i, flight in enumerate(flights):
                # Normalize scores (0-1, where 1 is best)
                price_score = 1 - ((flight['price'] - min_price) / (max_price - min_price)) if max_price > min_price else 1
                duration_score = 1 - ((durations[i] - min_duration) / (max_duration - min_duration)) if max_duration > min_duration else 1
                risk_score = 1 - ((flight['risk_factor'] - min_risk) / (max_risk - min_risk)) if max_risk > min_risk else 1
                
                # Preference score based on airline
                preference_score = 1.0
                if search_request.preferred_airline and flight['airline'] == search_request.preferred_airline.value:
                    preference_score = 1.2
                
                # Budget constraint
                if search_request.budget and flight['price'] > search_request.budget:
                    price_score *= 0.5  # Penalize over-budget flights
                
                # Occasion-based adjustments
                if search_request.occasion:
                    occasion_prefs = self.occasion_preferences.get(search_request.occasion, {})
                    priority = occasion_prefs.get('priority', 'balance')
                    
                    if priority == 'time':
                        duration_score *= 1.3
                    elif priority == 'price':
                        price_score *= 1.3
                
                # Calculate weighted total score
                total_score = (
                    price_score * self.weights['price'] +
                    duration_score * self.weights['duration'] +
                    risk_score * self.weights['risk'] +
                    preference_score * self.weights['preference']
                )
                
                flight['score'] = round(total_score, 3)
                flight['score_breakdown'] = {
                    'price_score': round(price_score, 3),
                    'duration_score': round(duration_score, 3),
                    'risk_score': round(risk_score, 3),
                    'preference_score': round(preference_score, 3),
                    'total_score': round(total_score, 3)
                }
            
            # Sort by score (highest first)
            flights.sort(key=lambda x: x['score'], reverse=True)
            
            return flights
            
        except Exception as e:
            logger.error(f"Error scoring flights: {str(e)}")
            return flights
    
    def _select_best_flight(self, scored_flights: List[Dict[str, Any]], search_request: FlightSearchRequest) -> Tuple[Dict[str, Any], str]:
        """Select the best flight and generate reasoning"""
        try:
            if not scored_flights:
                return {}, "No flights available for the selected criteria"
            
            best_flight = scored_flights[0]
            
            # Generate reasoning based on selection criteria
            reasoning_parts = []
            
            # Price reasoning
            if search_request.budget:
                if best_flight['price'] <= search_request.budget:
                    reasoning_parts.append(f"within your budget of ₹{search_request.budget}")
                else:
                    reasoning_parts.append(f"closest to your budget (₹{best_flight['price']} vs ₹{search_request.budget})")
            else:
                reasoning_parts.append(f"competitively priced at ₹{best_flight['price']}")
            
            # Duration reasoning
            reasoning_parts.append(f"optimal {best_flight['duration']} flight time")
            
            # Risk reasoning
            risk_level = "low" if best_flight['risk_factor'] < 0.3 else "moderate" if best_flight['risk_factor'] < 0.6 else "high"
            reasoning_parts.append(f"{risk_level} disruption risk ({best_flight['risk_factor']:.2f})")
            
            # Airline reasoning
            if search_request.preferred_airline and best_flight['airline'] == search_request.preferred_airline.value:
                reasoning_parts.append("matches your preferred airline")
            
            # Occasion reasoning
            if search_request.occasion:
                occasion_prefs = self.occasion_preferences.get(search_request.occasion, {})
                priority = occasion_prefs.get('priority', 'balance')
                
                if priority == 'time':
                    reasoning_parts.append(f"optimized for {search_request.occasion} travel (time priority)")
                elif priority == 'price':
                    reasoning_parts.append(f"optimized for {search_request.occasion} travel (cost priority)")
            
            reasoning = f"Selected {best_flight['airline']} flight {best_flight['flight_number']} as it offers the best combination of " + ", ".join(reasoning_parts) + f". Overall score: {best_flight['score']:.2f}/1.0"
            
            return best_flight, reasoning
            
        except Exception as e:
            logger.error(f"Error selecting best flight: {str(e)}")
            return scored_flights[0] if scored_flights else {}, f"Error in selection: {str(e)}"
    
    def _get_alternatives(self, scored_flights: List[Dict[str, Any]], best_flight: Dict[str, Any], max_alternatives: int = 4) -> List[Dict[str, Any]]:
        """Get alternative flight options"""
        try:
            alternatives = []
            
            for flight in scored_flights[1:max_alternatives+1]:  # Skip the best flight
                if flight['id'] != best_flight.get('id'):
                    alternatives.append(flight)
            
            return alternatives
            
        except Exception as e:
            logger.error(f"Error getting alternatives: {str(e)}")
            return []
    
    def _log_search_session(self, search_request: FlightSearchRequest, best_flight: Dict[str, Any], 
                           alternatives: List[Dict[str, Any]], reasoning: str) -> str:
        """Log search session to chatbot_sessions table"""
        try:
            session_id = str(uuid.uuid4())
            
            supabase = db.get_client()
            
            session_data = {
                'id': session_id,
                'user_id': f"search_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                'query': f"Flight search: {search_request.origin} to {search_request.destination}",
                'response': {
                    'search_criteria': search_request.dict(),
                    'best_flight': best_flight,
                    'alternatives_count': len(alternatives),
                    'reasoning': reasoning
                },
                'confidence_score': best_flight.get('score', 0.0)
            }
            
            result = supabase.table('chatbot_sessions').insert(session_data).execute()
            
            if result.data:
                logger.info(f"Logged search session {session_id}")
                return session_id
            else:
                logger.error("Failed to log search session")
                return session_id
                
        except Exception as e:
            logger.error(f"Error logging search session: {str(e)}")
            return str(uuid.uuid4())
    
    def _get_base_duration(self, route: str) -> int:
        """Get base flight duration in minutes"""
        durations = {
            'DEL-BOM': 135, 'BOM-DEL': 135,
            'DEL-BLR': 165, 'BLR-DEL': 165,
            'BOM-BLR': 90, 'BLR-BOM': 90,
            'DEL-GOA': 150, 'GOA-DEL': 150,
            'BOM-HYD': 75, 'HYD-BOM': 75,
            'BLR-HYD': 60, 'HYD-BLR': 60
        }
        return durations.get(route, 120)
    
    def _get_base_price(self, route: str) -> int:
        """Get base price for route"""
        prices = {
            'DEL-BOM': 4500, 'BOM-DEL': 4500,
            'DEL-BLR': 5500, 'BLR-DEL': 5500,
            'BOM-BLR': 3500, 'BLR-BOM': 3500,
            'DEL-GOA': 6000, 'GOA-DEL': 6000,
            'BOM-HYD': 3000, 'HYD-BOM': 3000,
            'BLR-HYD': 2500, 'HYD-BLR': 2500
        }
        return prices.get(route, 4000)
    
    def _get_airline_code(self, airline: AirlineEnum) -> str:
        """Get airline code"""
        codes = {
            AirlineEnum.AKASA: 'QP',
            AirlineEnum.INDIGO: '6E',
            AirlineEnum.SPICEJET: 'SG',
            AirlineEnum.VISTARA: 'UK',
            AirlineEnum.AIR_INDIA: 'AI'
        }
        return codes.get(airline, 'XX')
    
    def _format_duration(self, minutes: int) -> str:
        """Format duration in hours and minutes"""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}h {mins}m"
    
    def _duration_to_minutes(self, duration_str: str) -> int:
        """Convert duration string to minutes"""
        try:
            # Parse "2h 15m" format
            parts = duration_str.replace('h', '').replace('m', '').split()
            hours = int(parts[0]) if len(parts) > 0 else 0
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return hours * 60 + minutes
        except:
            return 120  # Default 2 hours
    
    def _format_db_flights(self, db_flights: List[Dict[str, Any]], search_request: FlightSearchRequest) -> List[Dict[str, Any]]:
        """Format database flights for processing"""
        formatted_flights = []
        
        for flight in db_flights:
            # Adjust departure time to requested date
            original_departure = datetime.fromisoformat(flight['departure_time'].replace('Z', ''))
            new_departure = datetime.combine(search_request.date, original_departure.time())
            
            duration_minutes = self._duration_to_minutes(flight['duration'])
            new_arrival = new_departure + timedelta(minutes=duration_minutes)
            
            formatted_flight = {
                'id': flight['id'],
                'airline': flight['airline'],
                'flight_number': flight['flight_number'],
                'origin': flight['origin'],
                'destination': flight['destination'],
                'departure_time': new_departure.isoformat(),
                'arrival_time': new_arrival.isoformat(),
                'duration': flight['duration'],
                'price': flight['price'],
                'risk_factor': 0.0,  # Will be calculated
                'aircraft_type': flight.get('aircraft_type'),
                'seats_available': flight.get('seats_available', 50)
            }
            
            formatted_flights.append(formatted_flight)
        
        return formatted_flights
    
    def _create_no_flights_response(self, search_request: FlightSearchRequest) -> Dict[str, Any]:
        """Create response when no flights are found"""
        return {
            'best_flight': None,
            'alternatives': [],
            'reasoning': f"No flights found for {search_request.origin} to {search_request.destination} on {search_request.date}",
            'search_criteria': search_request.dict(),
            'total_results': 0,
            'processing_time_ms': 0.0,
            'session_id': str(uuid.uuid4())
        }
    
    def _create_error_response(self, search_request: FlightSearchRequest, error_message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            'best_flight': None,
            'alternatives': [],
            'reasoning': f"Search failed: {error_message}",
            'search_criteria': search_request.dict(),
            'total_results': 0,
            'processing_time_ms': 0.0,
            'error': error_message,
            'session_id': str(uuid.uuid4())
        }

# Global flight search agent instance
flight_search_agent = FlightSearchAgent()