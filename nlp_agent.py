"""
Natural Language Processing Agent for Akasa Airlines
Interprets customer requests for booking changes and preference updates
"""

import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from database import db
import logging

logger = logging.getLogger(__name__)

class NLPAgent:
    """GenAI agent for interpreting natural language requests"""
    
    def __init__(self):
        # Date patterns for natural language parsing
        self.date_patterns = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6,
            'tomorrow': 1, 'next week': 7, 'next monday': None,
            'today': 0
        }
        
        # Seat preference patterns
        self.seat_patterns = {
            'window': ['window', 'by the window', 'window seat'],
            'aisle': ['aisle', 'aisle seat', 'corridor'],
            'middle': ['middle', 'center', 'middle seat'],
            'front': ['front', 'front row', 'up front'],
            'back': ['back', 'rear', 'back row'],
            'exit_row': ['exit row', 'emergency exit', 'extra legroom']
        }
        
        # Meal preference patterns
        self.meal_patterns = {
            'vegetarian': ['vegetarian', 'veg', 'no meat', 'veggie'],
            'vegan': ['vegan', 'plant based', 'no dairy'],
            'non_vegetarian': ['non-vegetarian', 'non-veg', 'meat', 'chicken', 'fish'],
            'jain': ['jain', 'jain food'],
            'diabetic': ['diabetic', 'sugar free', 'low sugar'],
            'gluten_free': ['gluten free', 'no gluten', 'celiac'],
            'no_preference': ['no preference', 'anything', 'regular']
        }
        
        # Notification preference patterns
        self.notification_patterns = {
            'email': ['email', 'e-mail', 'mail'],
            'sms': ['sms', 'text', 'message', 'phone'],
            'push': ['push notification', 'app notification', 'mobile app'],
            'all': ['all', 'everything', 'all methods'],
            'none': ['none', 'no notifications', 'disable']
        }
    
    def interpret_booking_change(self, request_text: str, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpret natural language booking change request
        
        Args:
            request_text: Natural language request
            booking_data: Current booking information
            
        Returns:
            Structured interpretation of the request
        """
        try:
            request_lower = request_text.lower().strip()
            
            # Initialize interpretation result
            interpretation = {
                'intent': 'unknown',
                'confidence': 0.0,
                'extracted_data': {},
                'original_request': request_text,
                'booking_id': booking_data.get('id'),
                'current_flight': booking_data.get('flight_number'),
                'current_date': booking_data.get('depart_date')
            }
            
            # Detect intent
            if any(word in request_lower for word in ['change', 'modify', 'update', 'reschedule']):
                interpretation['intent'] = 'change_booking'
                interpretation['confidence'] += 0.3
                
                # Extract date information
                new_date = self._extract_date_from_text(request_lower, booking_data.get('depart_date'))
                if new_date:
                    interpretation['extracted_data']['new_date'] = new_date
                    interpretation['confidence'] += 0.4
                
                # Extract time preferences
                time_preference = self._extract_time_preference(request_lower)
                if time_preference:
                    interpretation['extracted_data']['time_preference'] = time_preference
                    interpretation['confidence'] += 0.2
                
                # Extract destination changes
                destination_change = self._extract_destination_change(request_lower)
                if destination_change:
                    interpretation['extracted_data']['new_destination'] = destination_change
                    interpretation['confidence'] += 0.3
            
            elif any(word in request_lower for word in ['cancel', 'refund']):
                interpretation['intent'] = 'cancel_booking'
                interpretation['confidence'] = 0.8
            
            elif any(word in request_lower for word in ['status', 'information', 'details']):
                interpretation['intent'] = 'get_status'
                interpretation['confidence'] = 0.7
            
            # Cap confidence at 1.0
            interpretation['confidence'] = min(interpretation['confidence'], 1.0)
            
            logger.info(f"Interpreted booking change request: intent={interpretation['intent']}, confidence={interpretation['confidence']}")
            return interpretation
            
        except Exception as e:
            logger.error(f"Error interpreting booking change request: {str(e)}")
            return {
                'intent': 'error',
                'confidence': 0.0,
                'error': str(e),
                'original_request': request_text
            }
    
    def interpret_preference_update(self, request_text: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpret natural language preference update request
        
        Args:
            request_text: Natural language request
            customer_data: Current customer information
            
        Returns:
            Structured interpretation of preference updates
        """
        try:
            request_lower = request_text.lower().strip()
            
            interpretation = {
                'intent': 'update_preferences',
                'confidence': 0.0,
                'extracted_preferences': {},
                'original_request': request_text,
                'customer_id': customer_data.get('id')
            }
            
            # Extract seat preferences
            seat_pref = self._extract_seat_preference(request_lower)
            if seat_pref:
                interpretation['extracted_preferences']['seat_preference'] = seat_pref
                interpretation['confidence'] += 0.3
            
            # Extract meal preferences
            meal_pref = self._extract_meal_preference(request_lower)
            if meal_pref:
                interpretation['extracted_preferences']['meal_preference'] = meal_pref
                interpretation['confidence'] += 0.3
            
            # Extract notification preferences
            notification_pref = self._extract_notification_preference(request_lower)
            if notification_pref:
                interpretation['extracted_preferences']['notification_preference'] = notification_pref
                interpretation['confidence'] += 0.3
            
            # If no specific preferences found, try general preference detection
            if not interpretation['extracted_preferences']:
                if any(word in request_lower for word in ['prefer', 'like', 'want', 'need']):
                    interpretation['confidence'] = 0.2
                    interpretation['extracted_preferences']['general_request'] = request_text
            
            interpretation['confidence'] = min(interpretation['confidence'], 1.0)
            
            logger.info(f"Interpreted preference update: confidence={interpretation['confidence']}")
            return interpretation
            
        except Exception as e:
            logger.error(f"Error interpreting preference update: {str(e)}")
            return {
                'intent': 'error',
                'confidence': 0.0,
                'error': str(e),
                'original_request': request_text
            }
    
    def _extract_date_from_text(self, text: str, current_date: str) -> Optional[str]:
        """Extract date from natural language text"""
        try:
            current_dt = datetime.strptime(current_date, '%Y-%m-%d') if current_date else datetime.now()
            
            # Check for specific date patterns
            date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', text)
            if date_match:
                day, month, year = date_match.groups()
                if len(year) == 2:
                    year = '20' + year
                try:
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except:
                    pass
            
            # Check for day names
            for day_name, day_offset in self.date_patterns.items():
                if day_name in text:
                    if day_name == 'tomorrow':
                        new_date = current_dt + timedelta(days=1)
                        return new_date.strftime('%Y-%m-%d')
                    elif day_name == 'next week':
                        new_date = current_dt + timedelta(days=7)
                        return new_date.strftime('%Y-%m-%d')
                    elif day_name.startswith('next '):
                        # Handle "next monday", etc.
                        target_day = day_name.replace('next ', '')
                        if target_day in self.date_patterns:
                            target_weekday = self.date_patterns[target_day]
                            days_ahead = target_weekday - current_dt.weekday()
                            if days_ahead <= 0:
                                days_ahead += 7
                            new_date = current_dt + timedelta(days=days_ahead + 7)  # Next week
                            return new_date.strftime('%Y-%m-%d')
                    elif isinstance(day_offset, int):
                        # Handle regular day names for this week
                        days_ahead = day_offset - current_dt.weekday()
                        if days_ahead <= 0:
                            days_ahead += 7
                        new_date = current_dt + timedelta(days=days_ahead)
                        return new_date.strftime('%Y-%m-%d')
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting date: {str(e)}")
            return None
    
    def _extract_time_preference(self, text: str) -> Optional[str]:
        """Extract time preference from text"""
        if any(word in text for word in ['morning', 'early', 'am', '6am', '7am', '8am', '9am']):
            return 'morning'
        elif any(word in text for word in ['afternoon', 'noon', 'pm', '12pm', '1pm', '2pm', '3pm']):
            return 'afternoon'
        elif any(word in text for word in ['evening', 'night', '6pm', '7pm', '8pm', '9pm']):
            return 'evening'
        return None
    
    def _extract_destination_change(self, text: str) -> Optional[str]:
        """Extract destination change from text"""
        # Common airport codes and city names
        airports = {
            'delhi': 'DEL', 'mumbai': 'BOM', 'bangalore': 'BLR', 'bengaluru': 'BLR',
            'hyderabad': 'HYD', 'goa': 'GOA', 'kolkata': 'CCU', 'calcutta': 'CCU',
            'del': 'DEL', 'bom': 'BOM', 'blr': 'BLR', 'hyd': 'HYD', 'ccu': 'CCU'
        }
        
        for city, code in airports.items():
            if city in text:
                return code
        
        return None
    
    def _extract_seat_preference(self, text: str) -> Optional[str]:
        """Extract seat preference from text"""
        for pref_type, patterns in self.seat_patterns.items():
            if any(pattern in text for pattern in patterns):
                return pref_type
        return None
    
    def _extract_meal_preference(self, text: str) -> Optional[str]:
        """Extract meal preference from text"""
        for pref_type, patterns in self.meal_patterns.items():
            if any(pattern in text for pattern in patterns):
                return pref_type
        return None
    
    def _extract_notification_preference(self, text: str) -> Optional[str]:
        """Extract notification preference from text"""
        for pref_type, patterns in self.notification_patterns.items():
            if any(pattern in text for pattern in patterns):
                return pref_type
        return None
    
    def find_alternative_flights(self, booking_data: Dict[str, Any], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find alternative flights based on preferences
        
        Args:
            booking_data: Current booking information
            preferences: Extracted preferences from NLP
            
        Returns:
            List of alternative flight options
        """
        try:
            supabase = db.get_client()
            
            # Build query based on preferences
            origin = booking_data.get('origin')
            destination = preferences.get('new_destination', booking_data.get('destination'))
            new_date = preferences.get('new_date')
            time_preference = preferences.get('time_preference')
            
            if not new_date:
                return []
            
            # Query flights table for alternatives
            query = supabase.table('flights').select('*').eq('origin', origin).eq('destination', destination)
            
            # Filter by date (assuming scheduled_departure contains the date)
            result = query.execute()
            flights = result.data or []
            
            # Filter and score flights based on preferences
            alternatives = []
            for flight in flights:
                if not flight.get('scheduled_departure'):
                    continue
                
                flight_date = flight['scheduled_departure'][:10]  # Extract date part
                if flight_date != new_date:
                    continue
                
                # Score based on time preference
                score = 1.0
                if time_preference and flight.get('scheduled_departure'):
                    flight_hour = int(flight['scheduled_departure'][11:13])
                    if time_preference == 'morning' and 6 <= flight_hour <= 11:
                        score += 0.3
                    elif time_preference == 'afternoon' and 12 <= flight_hour <= 17:
                        score += 0.3
                    elif time_preference == 'evening' and 18 <= flight_hour <= 23:
                        score += 0.3
                
                alternatives.append({
                    **flight,
                    'match_score': score
                })
            
            # Sort by match score
            alternatives.sort(key=lambda x: x['match_score'], reverse=True)
            
            return alternatives[:5]  # Return top 5 alternatives
            
        except Exception as e:
            logger.error(f"Error finding alternative flights: {str(e)}")
            return []
    
    def store_nlp_session(self, session_data: Dict[str, Any]) -> str:
        """Store NLP session in chatbot_sessions table"""
        try:
            import uuid
            session_id = str(uuid.uuid4())
            
            supabase = db.get_client()
            
            session_record = {
                'id': session_id,
                'flight_id': session_data.get('booking_id', session_data.get('customer_id', 'unknown')),
                'query_type': session_data.get('intent', 'nlp_request'),
                'request_data': {
                    'original_request': session_data.get('original_request'),
                    'intent': session_data.get('intent'),
                    'confidence': session_data.get('confidence', 0.0)
                },
                'response_data': session_data.get('response_data', {}),
                'confidence_score': session_data.get('confidence', 0.0)
            }
            
            result = supabase.table('chatbot_sessions').insert(session_record).execute()
            
            if result.data:
                logger.info(f"Stored NLP session {session_id}")
                return session_id
            else:
                logger.error(f"Failed to store NLP session")
                return session_id
                
        except Exception as e:
            logger.error(f"Error storing NLP session: {str(e)}")
            return str(uuid.uuid4())

# Global NLP agent instance
nlp_agent = NLPAgent()