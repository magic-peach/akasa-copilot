"""
Voice-enabled chatbot system for Akasa Airlines
Handles speech-to-text, conversational AI, and text-to-speech
"""

import base64
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from src.utils.database import db
# Removed unused imports
import logging

# Mock agent imports - these would be real services in production
class MockFlightStatusAgent:
    def get_flight_status(self, flight_number):
        return {
            'flight_number': flight_number,
            'status': 'On Time',
            'eta': '14:30',
            'gate': 'A12'
        }

class MockDisruptionPredictor:
    def predict_disruption(self, flight_number):
        return {
            'flight_number': flight_number,
            'risk_level': 'Low',
            'disruption_risk': 0.15,
            'recommendations': ['Check weather updates', 'Arrive early']
        }

class MockNLPAgent:
    def interpret_booking_change(self, text, booking_data):
        return {
            'intent': 'change_booking',
            'confidence': 0.8,
            'extracted_data': {'new_date': '2024-02-20'}
        }
    
    def interpret_preference_update(self, text, customer_data):
        return {
            'extracted_preferences': {'seat_preference': 'window', 'meal_preference': 'vegetarian'}
        }

# Initialize mock agents
flight_status_agent = MockFlightStatusAgent()
disruption_predictor = MockDisruptionPredictor()
nlp_agent = MockNLPAgent()

# Mock services
class MockCalendarAnalysisService:
    def analyze_calendar_events(self, user_id):
        return {
            'travel_events': 2,
            'suggestions': [
                {'date': '2024-02-15', 'destination': 'Mumbai', 'reason': 'Business meeting'},
                {'date': '2024-02-20', 'destination': 'Delhi', 'reason': 'Conference'}
            ]
        }

class MockCancellationCostService:
    def predict_cancellation_cost(self, airline, fare_class, booking_date, departure_date, days_before):
        return type('CostResult', (), {
            'cancellation_fee': 500 if days_before == 0 else 1000,
            'refund_amount': 8000 if days_before == 0 else 6000,
            'total_loss': 500 if days_before == 0 else 1000,
            'recommendation': 'Cancel now for lower fees' if days_before == 0 else 'Consider changing instead'
        })()

calendar_analysis_service = MockCalendarAnalysisService()
cancellation_cost_service = MockCancellationCostService()

logger = logging.getLogger(__name__)

class VoiceChatbot:
    """Voice-enabled conversational AI agent with memory"""
    
    def __init__(self):
        self.openai_api_key = None  # Mock implementation
        self.elevenlabs_api_key = None  # Mock implementation
        
        # Intent classification patterns
        self.intent_patterns = {
            'flight_status': ['status', 'flight', 'delayed', 'on time', 'arrival', 'departure'],
            'booking_change': ['change', 'reschedule', 'modify', 'move', 'different date'],
            'disruption_risk': ['risk', 'prediction', 'weather', 'delay risk', 'cancellation'],
            'preferences': ['prefer', 'like', 'seat', 'meal', 'notification'],
            'alert_subscription': ['subscribe', 'notify', 'alert', 'updates', 'notifications'],
            'booking_info': ['booking', 'reservation', 'ticket', 'confirmation'],
            'calendar_analysis': ['calendar', 'events', 'schedule', 'meetings', 'appointments', 'analyze calendar'],
            'flight_suggestions': ['suggest flights', 'recommend flights', 'best dates', 'travel suggestions'],
            'cancellation_cost': ['cancellation cost', 'cancel flight', 'refund', 'penalty'],
            'travel_destination': ['best places', 'where to go', 'travel destinations', 'places to visit', 'recommend places'],
            'travel_timing': ['best time', 'when to go', 'season', 'weather', 'climate'],
            'travel_budget': ['budget', 'cost', 'expensive', 'cheap', 'affordable'],
            'travel_activities': ['things to do', 'activities', 'attractions', 'sightseeing', 'places to see'],
            'travel_tips': ['tips', 'advice', 'recommendations', 'what to know', 'travel guide'],
            'general_help': ['help', 'assistance', 'support', 'what can you do']
        }
        
        # Travel destination dictionary with intelligent responses
        self.travel_dictionary = self._initialize_travel_dictionary()
    
    def _initialize_travel_dictionary(self) -> Dict[str, Dict[str, Any]]:
        """Initialize comprehensive travel dictionary with 25+ questions and responses"""
        return {
            # Best places to travel during summer
            "best_places_summer": {
                "question_patterns": [
                    "best places to travel during summer",
                    "where to go in summer",
                    "summer destinations",
                    "best summer vacation spots"
                ],
                "response": "For summer travel, I recommend these amazing destinations: **Goa** for beaches and nightlife, **Manali** for cool mountain weather, **Kashmir** for breathtaking landscapes, **Ladakh** for adventure, **Ooty** for hill station charm, **Munnar** for tea gardens, and **Andaman Islands** for pristine beaches. Where would you like to travel from?",
                "requires_location": True,
                "follow_up": "What's your budget range for this summer trip?"
            },
            
            # Best places to travel during winter
            "best_places_winter": {
                "question_patterns": [
                    "best places to travel during winter",
                    "where to go in winter",
                    "winter destinations",
                    "best winter vacation spots"
                ],
                "response": "Winter is perfect for these destinations: **Goa** for warm beaches, **Kerala** for backwaters and Ayurveda, **Rajasthan** for palaces and desert, **Tamil Nadu** for temples and culture, **Karnataka** for heritage sites, **Maharashtra** for hill stations, and **Gujarat** for festivals. Which city are you traveling from?",
                "requires_location": True,
                "follow_up": "Are you looking for a beach holiday or cultural experience?"
            },
            
            # Best places to travel during monsoon
            "best_places_monsoon": {
                "question_patterns": [
                    "best places to travel during monsoon",
                    "where to go in rainy season",
                    "monsoon destinations",
                    "best places in rainy season"
                ],
                "response": "Monsoon brings out the best in these places: **Kerala** for lush green landscapes and backwaters, **Goa** for fewer crowds and lower prices, **Munnar** for misty tea gardens, **Coorg** for coffee plantations, **Kodaikanal** for romantic weather, **Lonavala** for waterfalls, and **Shillong** for living root bridges. What's your departure city?",
                "requires_location": True,
                "follow_up": "Do you prefer hill stations or coastal areas?"
            },
            
            # Budget travel destinations
            "budget_destinations": {
                "question_patterns": [
                    "cheap travel destinations",
                    "budget friendly places",
                    "affordable travel spots",
                    "low cost destinations"
                ],
                "response": "Great budget-friendly destinations include: **Pondicherry** for French colonial charm, **Hampi** for ancient ruins, **Pushkar** for spiritual vibes, **McLeod Ganj** for Tibetan culture, **Alleppey** for houseboat stays, **Gokarna** for peaceful beaches, and **Rishikesh** for adventure sports. Where are you starting your journey from?",
                "requires_location": True,
                "follow_up": "What's your approximate budget per person?"
            },
            
            # Luxury travel destinations
            "luxury_destinations": {
                "question_patterns": [
                    "luxury travel destinations",
                    "premium vacation spots",
                    "high end travel places",
                    "expensive but worth it destinations"
                ],
                "response": "For luxury travel, consider: **Udaipur** for palace hotels, **Kerala** for luxury backwater cruises, **Goa** for 5-star beach resorts, **Rajasthan** for royal experiences, **Himachal Pradesh** for luxury mountain retreats, **Karnataka** for heritage palace stays, and **Tamil Nadu** for luxury temple tours. Which city are you departing from?",
                "requires_location": True,
                "follow_up": "Are you interested in spa treatments or adventure activities?"
            },
            
            # Family travel destinations
            "family_destinations": {
                "question_patterns": [
                    "family friendly destinations",
                    "best places for family vacation",
                    "family travel spots",
                    "places to visit with kids"
                ],
                "response": "Perfect family destinations include: **Disneyland Mumbai** for theme park fun, **Kerala** for backwater houseboats, **Rajasthan** for palace tours, **Goa** for beach activities, **Himachal Pradesh** for mountain adventures, **Karnataka** for wildlife sanctuaries, and **Tamil Nadu** for cultural experiences. Where is your family located?",
                "requires_location": True,
                "follow_up": "What age groups are in your family?"
            },
            
            # Adventure travel destinations
            "adventure_destinations": {
                "question_patterns": [
                    "adventure travel destinations",
                    "places for adventure sports",
                    "thrilling vacation spots",
                    "adventure activities"
                ],
                "response": "Adventure seekers love: **Rishikesh** for white water rafting, **Ladakh** for trekking and biking, **Goa** for water sports, **Himachal Pradesh** for paragliding, **Karnataka** for rock climbing, **Kerala** for jungle safaris, and **Rajasthan** for desert camping. What's your adventure level - beginner or experienced?",
                "requires_location": True,
                "follow_up": "Are you interested in water sports, mountain activities, or desert adventures?"
            },
            
            # Romantic destinations
            "romantic_destinations": {
                "question_patterns": [
                    "romantic destinations",
                    "honeymoon places",
                    "couple vacation spots",
                    "romantic getaways"
                ],
                "response": "Romantic destinations perfect for couples: **Goa** for beach sunsets, **Kerala** for backwater cruises, **Udaipur** for palace romance, **Kashmir** for scenic beauty, **Munnar** for misty hills, **Andaman** for private beaches, and **Pondicherry** for French charm. Where are you and your partner located?",
                "requires_location": True,
                "follow_up": "Are you planning a honeymoon or anniversary celebration?"
            },
            
            # Cultural destinations
            "cultural_destinations": {
                "question_patterns": [
                    "cultural destinations",
                    "heritage places",
                    "historical sites",
                    "cultural tourism"
                ],
                "response": "Rich cultural destinations include: **Varanasi** for spiritual heritage, **Rajasthan** for royal palaces, **Tamil Nadu** for ancient temples, **Kerala** for traditional arts, **Karnataka** for historical monuments, **Maharashtra** for cave temples, and **Gujarat** for folk culture. Which city are you traveling from?",
                "requires_location": True,
                "follow_up": "Are you interested in temples, palaces, or traditional arts?"
            },
            
            # Beach destinations
            "beach_destinations": {
                "question_patterns": [
                    "beach destinations",
                    "best beaches",
                    "coastal places",
                    "beach vacation spots"
                ],
                "response": "Beautiful beach destinations: **Goa** for vibrant beaches, **Kerala** for peaceful backwaters, **Andaman** for pristine beaches, **Lakshadweep** for coral reefs, **Maharashtra** for Konkan coast, **Karnataka** for Gokarna beaches, and **Tamil Nadu** for Marina Beach. Where are you starting from?",
                "requires_location": True,
                "follow_up": "Do you prefer party beaches or quiet, secluded ones?"
            },
            
            # Hill station destinations
            "hill_station_destinations": {
                "question_patterns": [
                    "hill station destinations",
                    "mountain places",
                    "cool weather destinations",
                    "hill vacation spots"
                ],
                "response": "Charming hill stations include: **Shimla** for colonial charm, **Manali** for adventure, **Ooty** for tea gardens, **Munnar** for misty hills, **Kodaikanal** for romantic weather, **Darjeeling** for tea and views, and **Coorg** for coffee plantations. What's your departure city?",
                "requires_location": True,
                "follow_up": "Are you looking for adventure activities or peaceful relaxation?"
            },
            
            # Wildlife destinations
            "wildlife_destinations": {
                "question_patterns": [
                    "wildlife destinations",
                    "national parks",
                    "safari places",
                    "animal watching"
                ],
                "response": "Excellent wildlife destinations: **Ranthambore** for tiger spotting, **Jim Corbett** for diverse wildlife, **Kaziranga** for one-horned rhinos, **Bandipur** for elephants, **Periyar** for boat safaris, **Gir** for Asiatic lions, and **Kanha** for tiger reserves. Where are you located?",
                "requires_location": True,
                "follow_up": "Are you interested in tiger safaris or bird watching?"
            },
            
            # Spiritual destinations
            "spiritual_destinations": {
                "question_patterns": [
                    "spiritual destinations",
                    "pilgrimage places",
                    "religious sites",
                    "spiritual retreats"
                ],
                "response": "Sacred spiritual destinations: **Varanasi** for Ganga ghats, **Haridwar** for holy dips, **Rishikesh** for yoga and meditation, **Tirupati** for temple visits, **Amritsar** for Golden Temple, **Bodh Gaya** for Buddhist sites, and **Pushkar** for sacred lake. Which city are you departing from?",
                "requires_location": True,
                "follow_up": "Are you interested in yoga retreats or temple visits?"
            },
            
            # Food destinations
            "food_destinations": {
                "question_patterns": [
                    "food destinations",
                    "culinary tourism",
                    "best food places",
                    "foodie destinations"
                ],
                "response": "Food lover's paradise: **Delhi** for street food, **Mumbai** for diverse cuisine, **Kolkata** for Bengali sweets, **Hyderabad** for biryani, **Chennai** for South Indian food, **Punjab** for rich curries, and **Kerala** for seafood. Where are you starting your food journey from?",
                "requires_location": True,
                "follow_up": "Are you interested in street food or fine dining experiences?"
            },
            
            # Photography destinations
            "photography_destinations": {
                "question_patterns": [
                    "photography destinations",
                    "best places for photography",
                    "photogenic places",
                    "instagram worthy spots"
                ],
                "response": "Photographer's dream destinations: **Ladakh** for dramatic landscapes, **Kashmir** for scenic beauty, **Rajasthan** for colorful culture, **Kerala** for backwater scenes, **Goa** for beach photography, **Himachal Pradesh** for mountain vistas, and **Tamil Nadu** for temple architecture. What's your photography style - landscapes or portraits?",
                "requires_location": True,
                "follow_up": "Are you interested in nature photography or cultural photography?"
            },
            
            # Solo travel destinations
            "solo_destinations": {
                "question_patterns": [
                    "solo travel destinations",
                    "safe places for solo travelers",
                    "solo vacation spots",
                    "places for solo trips"
                ],
                "response": "Great solo travel destinations: **Goa** for beach relaxation, **Rishikesh** for spiritual growth, **Hampi** for historical exploration, **Pondicherry** for peaceful vibes, **McLeod Ganj** for Tibetan culture, **Alleppey** for backwater solitude, and **Pushkar** for spiritual retreats. Where are you located?",
                "requires_location": True,
                "follow_up": "Are you looking for adventure or peaceful solo time?"
            },
            
            # Weekend getaway destinations
            "weekend_destinations": {
                "question_patterns": [
                    "weekend getaway destinations",
                    "short trip places",
                    "weekend vacation spots",
                    "quick getaways"
                ],
                "response": "Perfect weekend getaways: **Lonavala** from Mumbai, **Nainital** from Delhi, **Coorg** from Bangalore, **Mahabalipuram** from Chennai, **Mount Abu** from Ahmedabad, **Matheran** from Mumbai, and **Kasauli** from Chandigarh. Which city are you traveling from?",
                "requires_location": True,
                "follow_up": "Are you looking for a relaxing or adventurous weekend?"
            },
            
            # Monsoon specific activities
            "monsoon_activities": {
                "question_patterns": [
                    "things to do in monsoon",
                    "monsoon activities",
                    "rainy season activities",
                    "monsoon experiences"
                ],
                "response": "Amazing monsoon activities: **Kerala backwater cruises** for misty boat rides, **Goa** for fewer crowds and lower prices, **Munnar** for tea garden walks, **Lonavala** for waterfall visits, **Coorg** for coffee plantation tours, **Kodaikanal** for romantic weather, and **Shillong** for living root bridges. Where would you like to experience monsoon?",
                "requires_location": True,
                "follow_up": "Do you prefer indoor activities or outdoor monsoon experiences?"
            },
            
            # Best time to visit specific places
            "best_time_visit": {
                "question_patterns": [
                    "best time to visit",
                    "when to go to",
                    "ideal season for",
                    "weather for travel"
                ],
                "response": "The best time to visit depends on the destination: **Goa** is great October to March, **Kashmir** is beautiful April to October, **Kerala** is perfect October to March, **Rajasthan** is best October to March, **Himachal Pradesh** is ideal April to October, **Karnataka** is good year-round, and **Tamil Nadu** is best October to March. Which destination are you asking about?",
                "requires_location": True,
                "follow_up": "Are you planning a specific month or season?"
            },
            
            # Travel tips and advice
            "travel_tips": {
                "question_patterns": [
                    "travel tips",
                    "travel advice",
                    "travel recommendations",
                    "what to know before traveling"
                ],
                "response": "Essential travel tips: **Book flights early** for better prices, **Pack light** but include essentials, **Check weather** before departure, **Carry copies** of important documents, **Download offline maps**, **Learn basic local phrases**, **Carry emergency contacts**, and **Get travel insurance**. What specific travel advice do you need?",
                "requires_location": False,
                "follow_up": "Are you a first-time traveler or looking for specific destination tips?"
            },
            
            # Budget travel tips
            "budget_tips": {
                "question_patterns": [
                    "budget travel tips",
                    "how to travel cheap",
                    "money saving travel tips",
                    "affordable travel advice"
                ],
                "response": "Smart budget travel tips: **Travel off-season** for lower prices, **Book accommodation in advance**, **Use public transport**, **Eat local food**, **Look for free activities**, **Travel with friends** to split costs, **Use travel apps** for deals, and **Pack snacks** to avoid expensive food. What's your travel budget range?",
                "requires_location": False,
                "follow_up": "Are you planning domestic or international travel?"
            },
            
            # Safety travel tips
            "safety_tips": {
                "question_patterns": [
                    "travel safety tips",
                    "safe travel advice",
                    "travel security tips",
                    "how to stay safe while traveling"
                ],
                "response": "Important safety tips: **Share your itinerary** with family, **Keep emergency contacts** handy, **Avoid isolated areas** at night, **Keep valuables secure**, **Use trusted transportation**, **Stay aware** of your surroundings, **Carry a first aid kit**, and **Know local emergency numbers**. Are you traveling solo or with others?",
                "requires_location": False,
                "follow_up": "Are you concerned about any specific safety aspects?"
            }
        }
    
    def process_voice_request(self, user_id: str, audio_data: Optional[str] = None, 
                            text_input: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process voice or text input through the conversational AI pipeline
        
        Args:
            user_id: User identifier for conversation tracking
            audio_data: Base64 encoded audio data (optional)
            text_input: Direct text input (optional)
            context: Additional context including current search, recent bookings, etc.
            
        Returns:
            Complete response with text and audio
        """
        try:
            # Step 1: Convert audio to text (if audio provided)
            if audio_data:
                user_text = self._speech_to_text(audio_data)
                if not user_text:
                    return self._create_error_response("Could not understand the audio. Please try again.")
            elif text_input:
                user_text = text_input
            else:
                return self._create_error_response("No audio or text input provided.")
            
            logger.info(f"Processing voice request from user {user_id}: {user_text}")
            
            # Step 2: Get conversation history for context
            chat_history = self.get_chat_history(user_id, limit=5)
            
            # Step 3: Enhance context with provided context
            enhanced_context = self._enhance_context(context, user_text, chat_history)
            
            # Step 4: Classify intent and process request
            intent_result = self._classify_intent(user_text, chat_history, enhanced_context)
            
            # Step 5: Route to appropriate agent based on intent
            agent_response = self._route_to_agent(intent_result, user_text, user_id, chat_history, enhanced_context)
            
            # Step 5: Generate conversational response
            conversational_response = self._generate_conversational_response(
                user_text, agent_response, intent_result, chat_history
            )
            
            # Step 6: Convert response to speech
            audio_response = self._text_to_speech(conversational_response['text'])
            
            # Step 7: Save conversation in chatbot_sessions
            session_id = self._save_conversation(
                user_id, user_text, conversational_response, intent_result, audio_data is not None
            )
            
            # Step 8: Return complete response
            return {
                'success': True,
                'session_id': session_id,
                'user_input': user_text,
                'intent': intent_result['intent'],
                'confidence': intent_result['confidence'],
                'response': {
                    'text': conversational_response['text'],
                    'audio': audio_response,
                    'data': conversational_response.get('data'),
                    'suggestions': conversational_response.get('suggestions', [])
                },
                'conversation_context': {
                    'history_used': len(chat_history),
                    'context_relevant': conversational_response.get('context_used', False)
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing voice request: {str(e)}")
            return self._create_error_response(f"An error occurred: {str(e)}")
    
    def _speech_to_text(self, audio_data: str) -> Optional[str]:
        """
        Convert speech to text using browser Web Speech API
        This method will be called from the frontend with transcribed text
        """
        try:
            # In the frontend implementation, we'll use the Web Speech API
            # This method is kept for compatibility but actual STT happens in browser
            
            # For demo purposes, simulate transcription
            mock_transcriptions = [
                "What is the status of my flight QP1001?",
                "Change my booking to next Monday",
                "I prefer window seats and vegetarian meals",
                "Subscribe me to flight alerts via SMS",
                "What is the risk of delay for flight QP1002?",
                "Show me my booking details",
                "Cancel my flight reservation",
                "Best places to travel during summer",
                "Where should I go for a romantic vacation?",
                "What are the best budget destinations?",
                "Family friendly places to visit",
                "Adventure travel destinations",
                "Best time to visit Goa",
                "Travel safety tips",
                "Weekend getaway destinations"
            ]
            
            import random
            transcribed_text = random.choice(mock_transcriptions)
            
            logger.info(f"Speech-to-text result: {transcribed_text}")
            return transcribed_text
            
        except Exception as e:
            logger.error(f"Error in speech-to-text: {str(e)}")
            return None
    
    def _text_to_speech(self, text: str) -> Optional[str]:
        """
        Convert text to speech using browser Web Speech API
        This method will be called from the frontend for TTS
        """
        try:
            # In the frontend implementation, we'll use the Web Speech API
            # This method is kept for compatibility but actual TTS happens in browser
            
            # For demo purposes, return mock audio data
            mock_audio_data = base64.b64encode(f"TTS_AUDIO_FOR: {text}".encode()).decode()
            
            logger.info(f"Text-to-speech generated for: {text[:50]}...")
            return mock_audio_data
            
        except Exception as e:
            logger.error(f"Error in text-to-speech: {str(e)}")
            return None
    
    def _check_travel_dictionary(self, user_text: str) -> Optional[Dict[str, Any]]:
        """Check if user query matches any travel dictionary patterns"""
        try:
            user_lower = user_text.lower()
            
            # Check each travel dictionary entry
            for key, entry in self.travel_dictionary.items():
                for pattern in entry["question_patterns"]:
                    pattern_lower = pattern.lower()
                    # Check if the pattern words are present in the user text
                    pattern_words = pattern_lower.split()
                    if len(pattern_words) > 0:
                        # Count how many pattern words are found in user text
                        matches = sum(1 for word in pattern_words if word in user_lower)
                        # If more than half the pattern words match, consider it a match
                        if matches >= len(pattern_words) * 0.6:
                            return {
                                'key': key,
                                'entry': entry,
                                'matched_pattern': pattern,
                                'match_score': matches / len(pattern_words)
                            }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking travel dictionary: {str(e)}")
            return None
    
    def _extract_location_from_text(self, user_text: str) -> Optional[str]:
        """Extract location information from user text"""
        try:
            user_lower = user_text.lower()
            
            # Common location indicators
            location_indicators = ['from', 'to', 'in', 'at', 'near', 'around']
            
            # City mappings
            city_mappings = {
                'delhi': 'DEL', 'mumbai': 'BOM', 'bangalore': 'BLR', 'hyderabad': 'HYD',
                'chennai': 'MAA', 'kolkata': 'CCU', 'goa': 'GOA', 'pune': 'PNQ',
                'ahmedabad': 'AMD', 'jaipur': 'JAI', 'lucknow': 'LKO', 'chandigarh': 'IXC',
                'indore': 'IDR', 'bhubaneswar': 'BBI', 'coimbatore': 'CJB', 'vadodara': 'BDQ',
                'nagpur': 'NAG', 'kochi': 'COK', 'bhopal': 'BHO', 'visakhapatnam': 'VTZ',
                'patna': 'PAT', 'ludhiana': 'LUH', 'agra': 'AGR', 'nashik': 'ISK',
                'faridabad': 'FBD', 'meerut': 'MUT', 'rajkot': 'RAJ', 'kalyan': 'KLY',
                'vasai': 'VAS', 'varanasi': 'VNS', 'srinagar': 'SXR', 'amritsar': 'ATQ',
                'ranchi': 'IXR', 'howrah': 'HWH', 'cochin': 'COK', 'rajahmundry': 'RJA',
                'madurai': 'IXM', 'salem': 'SXV', 'tiruchirapalli': 'TRZ', 'tirupati': 'TIR'
            }
            
            # Look for city names in the text
            for city, code in city_mappings.items():
                if city in user_lower:
                    return code
            
            # Look for patterns like "from Mumbai", "to Delhi", etc.
            words = user_lower.split()
            for i, word in enumerate(words):
                if word in location_indicators and i + 1 < len(words):
                    next_word = words[i + 1]
                    if next_word in city_mappings:
                        return city_mappings[next_word]
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting location: {str(e)}")
            return None
    
    def _handle_travel_dictionary_query(self, travel_match: Dict[str, Any], user_text: str, user_id: str) -> Dict[str, Any]:
        """Handle travel dictionary queries with location validation"""
        try:
            entry = travel_match['entry']
            key = travel_match['key']
            
            # Check if location is required and extract it
            if entry.get('requires_location', False):
                location = self._extract_location_from_text(user_text)
                
                if not location:
                    # Ask for location information
                    return {
                        'success': True,
                        'requires_location': True,
                        'response': entry['response'],
                        'follow_up_question': "Which city are you traveling from?",
                        'dictionary_key': key,
                        'suggestions': [
                            "I'm traveling from Delhi",
                            "I'm traveling from Mumbai", 
                            "I'm traveling from Bangalore",
                            "I'm traveling from Chennai"
                        ]
                    }
                else:
                    # Location found, provide complete response
                    response_text = entry['response']
                    if location:
                        response_text += f" Since you're traveling from {location}, I can help you find the best flights and routes."
                    
                    return {
                        'success': True,
                        'response': response_text,
                        'location': location,
                        'follow_up': entry.get('follow_up', ''),
                        'dictionary_key': key,
                        'suggestions': [
                            "Show me flights to these destinations",
                            "What's the best time to visit?",
                            "Tell me more about these places",
                            "What activities can I do there?"
                        ]
                    }
            else:
                # No location required, provide direct response
                return {
                    'success': True,
                    'response': entry['response'],
                    'follow_up': entry.get('follow_up', ''),
                    'dictionary_key': key,
                    'suggestions': [
                        "Tell me more about this",
                        "What else should I know?",
                        "Give me more tips",
                        "What about other destinations?"
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error handling travel dictionary query: {str(e)}")
            return {'error': f'Could not process travel query: {str(e)}'}
    
    def _enhance_context(self, context: Optional[Dict[str, Any]], user_text: str, chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Enhance context with current search parameters and recent bookings"""
        try:
            enhanced_context = {
                'user_text': user_text,
                'chat_history': chat_history,
                'current_search': context.get('current_search', {}) if context else {},
                'recent_bookings': context.get('recent_bookings', []) if context else [],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Add location context if available
            if context and context.get('current_search'):
                search = context['current_search']
                if search.get('origin'):
                    enhanced_context['user_location'] = search['origin']
                if search.get('destination'):
                    enhanced_context['target_destination'] = search['destination']
                if search.get('date'):
                    enhanced_context['travel_date'] = search['date']
                if search.get('budget'):
                    enhanced_context['budget'] = search['budget']
            
            return enhanced_context
            
        except Exception as e:
            logger.error(f"Error enhancing context: {str(e)}")
            return {'user_text': user_text, 'chat_history': chat_history}

    def _classify_intent(self, user_text: str, chat_history: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Classify user intent based on text and conversation history"""
        try:
            user_lower = user_text.lower()
            intent_scores = {}
            
            # First check travel dictionary
            travel_match = self._check_travel_dictionary(user_text)
            if travel_match:
                return {
                    'intent': 'travel_dictionary',
                    'confidence': 0.9,
                    'travel_match': travel_match,
                    'all_scores': {'travel_dictionary': 0.9}
                }
            
            # Score each intent based on keyword matching
            for intent, keywords in self.intent_patterns.items():
                score = sum(1 for keyword in keywords if keyword in user_lower)
                if score > 0:
                    intent_scores[intent] = score / len(keywords)
            
            # Consider conversation context
            if chat_history:
                last_intent = chat_history[0].get('request_data', {}).get('intent')
                if last_intent and last_intent in intent_scores:
                    intent_scores[last_intent] *= 1.2  # Boost related intents
            
            # Consider enhanced context for better intent classification
            if context:
                # Boost flight_suggestions if user has recent bookings
                if context.get('recent_bookings') and 'flight_suggestions' in intent_scores:
                    intent_scores['flight_suggestions'] *= 1.3
                
                # Boost calendar_analysis if user is searching for flights
                if context.get('current_search', {}).get('origin') and 'calendar_analysis' in intent_scores:
                    intent_scores['calendar_analysis'] *= 1.2
            
            # Determine best intent
            if intent_scores:
                best_intent = max(intent_scores, key=intent_scores.get)
                confidence = min(intent_scores[best_intent], 1.0)
            else:
                best_intent = 'general_help'
                confidence = 0.3
            
            return {
                'intent': best_intent,
                'confidence': confidence,
                'all_scores': intent_scores
            }
            
        except Exception as e:
            logger.error(f"Error classifying intent: {str(e)}")
            return {'intent': 'general_help', 'confidence': 0.1}
    
    def _route_to_agent(self, intent_result: Dict[str, Any], user_text: str, 
                       user_id: str, chat_history: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Route request to appropriate specialized agent"""
        try:
            intent = intent_result['intent']
            
            if intent == 'travel_dictionary':
                # Handle travel dictionary queries
                travel_match = intent_result.get('travel_match')
                if travel_match:
                    return self._handle_travel_dictionary_query(travel_match, user_text, user_id)
                else:
                    return {'error': 'Travel query not recognized'}
            
            elif intent == 'flight_status':
                # Extract flight number from text
                flight_number = self._extract_flight_number(user_text, chat_history)
                if flight_number:
                    return flight_status_agent.get_flight_status(flight_number)
                else:
                    return {'error': 'Please specify a flight number'}
            
            elif intent == 'disruption_risk':
                # Extract flight number for risk prediction
                flight_number = self._extract_flight_number(user_text, chat_history)
                if flight_number:
                    return disruption_predictor.predict_disruption(flight_number)
                else:
                    return {'error': 'Please specify a flight number for risk assessment'}
            
            elif intent == 'booking_change':
                # Extract booking ID from context or text
                booking_id = self._extract_booking_id(user_text, chat_history, user_id)
                if booking_id:
                    # Use NLP agent for booking changes
                    booking_data = self._get_booking_data(booking_id)
                    if booking_data:
                        return nlp_agent.interpret_booking_change(user_text, booking_data)
                    else:
                        return {'error': 'Booking not found'}
                else:
                    return {'error': 'Please specify your booking ID or provide more details'}
            
            elif intent == 'preferences':
                # Handle preference updates
                customer_data = self._get_customer_data(user_id)
                if customer_data:
                    return nlp_agent.interpret_preference_update(user_text, customer_data)
                else:
                    return {'error': 'Customer profile not found'}
            
            elif intent == 'alert_subscription':
                # Handle alert subscription requests
                return self._process_alert_subscription(user_text, user_id)
            
            elif intent == 'booking_info':
                # Get booking information
                booking_id = self._extract_booking_id(user_text, chat_history, user_id)
                if booking_id:
                    booking_data = self._get_booking_data(booking_id)
                    return {'booking_data': booking_data} if booking_data else {'error': 'Booking not found'}
                else:
                    return {'error': 'Please provide your booking ID'}
            
            elif intent == 'calendar_analysis':
                # Analyze calendar events for travel planning
                return self._analyze_calendar_events(user_id)
            
            elif intent == 'flight_suggestions':
                # Suggest flights based on calendar events
                origin = context.get('user_location', 'DEL') if context else 'DEL'
                return self._suggest_flights_from_calendar(user_text, user_id, origin)
            
            elif intent == 'cancellation_cost':
                # Calculate cancellation costs
                booking_id = self._extract_booking_id(user_text, chat_history, user_id)
                if booking_id:
                    return self._calculate_cancellation_cost(booking_id, user_text)
                else:
                    return {'error': 'Please provide your booking ID for cancellation cost calculation'}
            
            else:  # general_help
                return self._generate_help_response(chat_history)
                
        except Exception as e:
            logger.error(f"Error routing to agent: {str(e)}")
            return {'error': f'Processing error: {str(e)}'}
    
    def _generate_conversational_response(self, user_text: str, agent_response: Dict[str, Any], 
                                        intent_result: Dict[str, Any], 
                                        chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate natural conversational response"""
        try:
            intent = intent_result['intent']
            
            # Check for errors first
            if agent_response.get('error'):
                return {
                    'text': f"I'm sorry, {agent_response['error']}. How else can I help you?",
                    'data': None,
                    'suggestions': [
                        "Check flight status",
                        "Change booking date",
                        "Update preferences",
                        "Subscribe to alerts"
                    ]
                }
            
            # Handle travel dictionary responses
            if intent == 'travel_dictionary':
                if agent_response.get('requires_location'):
                    return {
                        'text': agent_response['response'],
                        'data': agent_response,
                        'follow_up_question': agent_response.get('follow_up_question'),
                        'suggestions': agent_response.get('suggestions', []),
                        'context_used': True
                    }
                else:
                    response_text = agent_response.get('response', '')
                    if agent_response.get('follow_up'):
                        response_text += f" {agent_response['follow_up']}"
                    
                    return {
                        'text': response_text,
                        'data': agent_response,
                        'suggestions': agent_response.get('suggestions', []),
                        'context_used': True
                    }
            
            # Generate response based on intent
            if intent == 'flight_status':
                flight_data = agent_response
                status = flight_data.get('status', 'Unknown')
                flight_num = flight_data.get('flight_number', 'your flight')
                eta = flight_data.get('eta', 'Unknown')
                
                response_text = f"Your flight {flight_num} is currently {status.lower()}."
                if eta and eta != 'Unknown':
                    response_text += f" The estimated arrival time is {eta}."
                
                return {
                    'text': response_text,
                    'data': flight_data,
                    'context_used': True
                }
            
            elif intent == 'disruption_risk':
                risk_data = agent_response
                flight_num = risk_data.get('flight_number', 'your flight')
                risk_level = risk_data.get('risk_level', 'Unknown')
                risk_score = risk_data.get('disruption_risk', 0.0)
                
                response_text = f"The disruption risk for flight {flight_num} is {risk_level.lower()} with a score of {risk_score:.2f}."
                
                recommendations = risk_data.get('recommendations', [])
                if recommendations:
                    response_text += f" I recommend: {', '.join(recommendations[:2])}."
                
                return {
                    'text': response_text,
                    'data': risk_data,
                    'context_used': True
                }
            
            elif intent == 'booking_change':
                if agent_response.get('intent') == 'change_booking':
                    confidence = agent_response.get('confidence', 0.0)
                    extracted_date = agent_response.get('extracted_data', {}).get('new_date')
                    
                    if confidence > 0.5 and extracted_date:
                        response_text = f"I understand you want to change your booking to {extracted_date}. Let me find available options for you."
                    else:
                        response_text = "I'm not sure I understood your change request completely. Could you please specify the new date more clearly?"
                else:
                    response_text = "I couldn't understand your booking change request. Please try again with a specific date."
                
                return {
                    'text': response_text,
                    'data': agent_response,
                    'suggestions': [
                        "Change to Monday",
                        "Reschedule to next week",
                        "Move to February 20th"
                    ]
                }
            
            elif intent == 'preferences':
                extracted_prefs = agent_response.get('extracted_preferences', {})
                if extracted_prefs:
                    pref_list = ', '.join(f"{k.replace('_', ' ')}: {v}" for k, v in extracted_prefs.items())
                    response_text = f"I've updated your preferences: {pref_list}. Is there anything else you'd like to change?"
                else:
                    response_text = "I couldn't understand your preference request. Please try again."
                
                return {
                    'text': response_text,
                    'data': agent_response,
                    'suggestions': [
                        "I prefer window seats",
                        "I want vegetarian meals",
                        "Send me SMS notifications"
                    ]
                }
            
            elif intent == 'alert_subscription':
                subscription_result = agent_response
                if subscription_result.get('success'):
                    channel = subscription_result.get('channel', 'notifications')
                    response_text = f"Great! I've subscribed you to flight alerts via {channel}. You'll receive updates about delays and cancellations."
                else:
                    response_text = "I couldn't set up your alert subscription. Please specify how you'd like to receive notifications."
                
                return {
                    'text': response_text,
                    'data': subscription_result,
                    'suggestions': [
                        "Subscribe via SMS",
                        "Subscribe via email",
                        "Subscribe to all alerts"
                    ]
                }
            
            elif intent == 'booking_info':
                booking_data = agent_response.get('booking_data')
                if booking_data:
                    flight_num = booking_data.get('flight_number', 'Unknown')
                    date = booking_data.get('depart_date', 'Unknown')
                    route = f"{booking_data.get('origin', '')} to {booking_data.get('destination', '')}"
                    
                    response_text = f"Your booking details: Flight {flight_num} on {date} from {route}."
                else:
                    response_text = "I couldn't find your booking information. Please provide your booking ID."
                
                return {
                    'text': response_text,
                    'data': booking_data
                }
            
            elif intent == 'calendar_analysis':
                calendar_data = agent_response
                travel_events = calendar_data.get('travel_events', 0)
                
                if travel_events > 0:
                    response_text = f"I found {travel_events} travel-related events in your calendar. "
                    response_text += "I can suggest optimal flight dates based on your schedule."
                else:
                    response_text = "I analyzed your calendar but didn't find any travel-related events. "
                    response_text += "Would you like me to help you plan upcoming trips?"
                
                return {
                    'text': response_text,
                    'data': calendar_data,
                    'suggestions': [
                        "Suggest flights for my events",
                        "Show travel recommendations",
                        "Add travel event to calendar"
                    ]
                }
            
            elif intent == 'flight_suggestions':
                suggestion_data = agent_response
                suggestions = suggestion_data.get('flight_suggestions', [])
                origin = suggestion_data.get('origin', 'your location')
                
                if suggestions:
                    response_text = f"Based on your calendar, I recommend flights from {origin}. "
                    response_text += f"I found {len(suggestions)} optimal travel windows for your events."
                else:
                    response_text = "I couldn't find specific flight suggestions based on your calendar. "
                    response_text += "Would you like me to search for flights to specific destinations?"
                
                return {
                    'text': response_text,
                    'data': suggestion_data,
                    'suggestions': [
                        "Search flights to Mumbai",
                        "Search flights to Bangalore",
                        "Check calendar conflicts"
                    ]
                }
            
            elif intent == 'cancellation_cost':
                cost_data = agent_response
                costs = cost_data.get('cancellation_costs', {})
                
                if costs:
                    cost_now = costs.get('now', {})
                    cost_later = costs.get('week_later', {})
                    
                    response_text = f"Here are your cancellation costs: "
                    response_text += f"If you cancel now, the fee is ₹{cost_now.get('fee', 0)} with a refund of ₹{cost_now.get('refund', 0)}. "
                    response_text += f"If you cancel a week later, the fee increases to ₹{cost_later.get('fee', 0)} with a refund of ₹{cost_later.get('refund', 0)}."
                else:
                    response_text = "I couldn't calculate the cancellation costs. Please check your booking details."
                
                return {
                    'text': response_text,
                    'data': cost_data,
                    'suggestions': [
                        "Check booking details",
                        "Change booking instead",
                        "Contact support"
                    ]
                }
            
            else:  # general_help
                help_response = agent_response
                response_text = "I'm your Akasa Airlines assistant. I can help you with flight status, booking changes, preferences, and alerts. What would you like to do?"
                
                return {
                    'text': response_text,
                    'data': help_response,
                    'suggestions': [
                        "Check flight status",
                        "Analyze my calendar",
                        "Suggest flights",
                        "Calculate cancellation cost"
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error generating conversational response: {str(e)}")
            return {
                'text': "I'm sorry, I encountered an error processing your request. Please try again.",
                'data': None
            }
    
    def get_chat_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve chat history for conversation context"""
        try:
            supabase = db.get_client()
            
            # Get recent chat sessions for this user
            result = supabase.table('chatbot_sessions').select('*').eq('flight_id', user_id).order('created_at', desc=True).limit(limit).execute()
            
            chat_history = result.data or []
            
            logger.info(f"Retrieved {len(chat_history)} chat history entries for user {user_id}")
            return chat_history
            
        except Exception as e:
            logger.error(f"Error retrieving chat history: {str(e)}")
            return []
    
    def _extract_flight_number(self, text: str, chat_history: List[Dict[str, Any]]) -> Optional[str]:
        """Extract flight number from text or conversation history"""
        # Look for flight number pattern in current text
        import re
        flight_pattern = r'\b(QP\d{4}|\d{4})\b'
        match = re.search(flight_pattern, text.upper())
        
        if match:
            flight_num = match.group(1)
            if not flight_num.startswith('QP'):
                flight_num = 'QP' + flight_num
            return flight_num
        
        # Look in conversation history
        for session in chat_history:
            response_data = session.get('response_data', {})
            if 'flight_number' in response_data:
                return response_data['flight_number']
        
        return None
    
    def _extract_booking_id(self, text: str, chat_history: List[Dict[str, Any]], user_id: str) -> Optional[str]:
        """Extract booking ID from text, history, or user's recent bookings"""
        # Look for UUID pattern in text
        import re
        uuid_pattern = r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b'
        match = re.search(uuid_pattern, text.lower())
        
        if match:
            return match.group(0)
        
        # Look in conversation history
        for session in chat_history:
            response_data = session.get('response_data', {})
            if 'booking_id' in response_data:
                return response_data['booking_id']
        
        # Try to find user's most recent booking
        try:
            supabase = db.get_client()
            result = supabase.table('bookings').select('*').eq('customer_id', user_id).order('created_at', desc=True).limit(1).execute()
            
            if result.data:
                return result.data[0]['id']
        except:
            pass
        
        return None
    
    def _get_booking_data(self, booking_id: str) -> Optional[Dict[str, Any]]:
        """Get booking data from database"""
        try:
            supabase = db.get_client()
            result = supabase.table('bookings').select('*').eq('id', booking_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting booking data: {str(e)}")
            return None
    
    def _get_customer_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get customer data from database"""
        try:
            supabase = db.get_client()
            result = supabase.table('customers').select('*').eq('id', user_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting customer data: {str(e)}")
            return None
    
    def _process_alert_subscription(self, user_text: str, user_id: str) -> Dict[str, Any]:
        """Process alert subscription requests"""
        try:
            user_lower = user_text.lower()
            
            # Determine subscription channel
            if 'sms' in user_lower or 'text' in user_lower:
                channel = 'SMS'
            elif 'email' in user_lower:
                channel = 'email'
            else:
                channel = 'notifications'
            
            return {
                'success': True,
                'channel': channel,
                'user_id': user_id,
                'message': f'Subscribed to {channel} alerts'
            }
            
        except Exception as e:
            logger.error(f"Error processing alert subscription: {str(e)}")
            return {'error': f'Could not process subscription: {str(e)}'}
    
    
    def _generate_help_response(self, chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate helpful response based on conversation history"""
        capabilities = [
            "Check flight status and delays",
            "Change booking dates and times",
            "Update seat and meal preferences",
            "Subscribe to flight alerts",
            "Predict disruption risks",
            "Get booking information"
        ]
        
        return {
            'capabilities': capabilities,
            'help_text': "I can assist you with various flight-related tasks."
        }
    
    def _save_conversation(self, user_id: str, user_input: str, response: Dict[str, Any], 
                          intent_result: Dict[str, Any], was_voice: bool) -> str:
        """Save conversation in chatbot_sessions"""
        try:
            import uuid
            session_id = str(uuid.uuid4())
            
            supabase = db.get_client()
            
            session_data = {
                'id': session_id,
                'flight_id': user_id,  # Using user_id as flight_id for tracking
                'query_type': f"voice_chat_{intent_result['intent']}",
                'request_data': {
                    'user_input': user_input,
                    'intent': intent_result['intent'],
                    'confidence': intent_result['confidence'],
                    'was_voice': was_voice
                },
                'response_data': response,
                'confidence_score': intent_result['confidence']
            }
            
            result = supabase.table('chatbot_sessions').insert(session_data).execute()
            
            if result.data:
                logger.info(f"Saved voice conversation session {session_id}")
                return session_id
            else:
                logger.error(f"Failed to save conversation session")
                return session_id
                
        except Exception as e:
            logger.error(f"Error saving conversation: {str(e)}")
            return str(uuid.uuid4())
    
    def _analyze_calendar_events(self, user_id: str) -> Dict[str, Any]:
        """Analyze calendar events for travel planning"""
        try:
            # Use mock calendar analysis service
            calendar_service = calendar_analysis_service
            
            # Get calendar events (mock implementation)
            events = [
                {
                    'summary': 'Business Meeting in Mumbai',
                    'start': {'dateTime': '2024-01-15T10:00:00Z'},
                    'end': {'dateTime': '2024-01-15T12:00:00Z'},
                    'location': 'Mumbai, India'
                },
                {
                    'summary': 'Conference in Bangalore',
                    'start': {'dateTime': '2024-01-20T09:00:00Z'},
                    'end': {'dateTime': '2024-01-22T17:00:00Z'},
                    'location': 'Bangalore, India'
                }
            ]
            
            analysis = calendar_service.analyze_events_for_travel(events)
            
            return {
                'success': True,
                'calendar_analysis': analysis,
                'travel_events': len([e for e in analysis if e.is_travel_related]),
                'suggestions': calendar_service.generate_travel_suggestions(analysis)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing calendar: {str(e)}")
            return {'error': f'Could not analyze calendar: {str(e)}'}
    
    def _suggest_flights_from_calendar(self, user_text: str, user_id: str, origin: str = 'DEL') -> Dict[str, Any]:
        """Suggest flights based on calendar events"""
        try:
            # Get calendar analysis first
            calendar_analysis = self._analyze_calendar_events(user_id)
            
            if 'error' in calendar_analysis:
                return calendar_analysis
            
            # Extract travel preferences from user text
            budget = 10000  # Default budget
            
            # Simple text parsing for origin and budget
            if 'from' in user_text.lower():
                words = user_text.lower().split()
                try:
                    from_idx = words.index('from')
                    if from_idx + 1 < len(words):
                        origin_city = words[from_idx + 1]
                        # Map city names to codes
                        city_codes = {
                            'delhi': 'DEL', 'mumbai': 'BOM', 'bangalore': 'BLR',
                            'hyderabad': 'HYD', 'chennai': 'MAA', 'kolkata': 'CCU'
                        }
                        origin = city_codes.get(origin_city, 'DEL')
                except ValueError:
                    pass
            
            if 'budget' in user_text.lower() or 'under' in user_text.lower():
                import re
                numbers = re.findall(r'\d+', user_text)
                if numbers:
                    budget = int(numbers[0])
            
            suggestions = calendar_analysis.get('suggestions', [])
            
            return {
                'success': True,
                'flight_suggestions': suggestions,
                'origin': origin,
                'budget': budget,
                'calendar_events': calendar_analysis.get('travel_events', 0)
            }
            
        except Exception as e:
            logger.error(f"Error suggesting flights: {str(e)}")
            return {'error': f'Could not generate flight suggestions: {str(e)}'}
    
    def _calculate_cancellation_cost(self, booking_id: str, user_text: str) -> Dict[str, Any]:
        """Calculate cancellation costs for a booking"""
        try:
            # Use mock cancellation cost service
            cost_service = cancellation_cost_service
            
            # Get booking data
            booking_data = self._get_booking_data(booking_id)
            if not booking_data:
                return {'error': 'Booking not found'}
            
            # Extract timing from user text (now vs later)
            timing = 'now'
            if 'week later' in user_text.lower() or 'later' in user_text.lower():
                timing = 'week_later'
            
            # Calculate costs for both scenarios
            cost_now = cost_service.predict_cancellation_cost(
                booking_data.get('airline', 'AI'),
                booking_data.get('fare_class', 'Economy'),
                booking_data.get('booking_date', datetime.now().isoformat()),
                booking_data.get('departure_date', (datetime.now() + timedelta(days=7)).isoformat()),
                0  # Cancel now
            )
            
            cost_later = cost_service.predict_cancellation_cost(
                booking_data.get('airline', 'AI'),
                booking_data.get('fare_class', 'Economy'),
                booking_data.get('booking_date', datetime.now().isoformat()),
                booking_data.get('departure_date', (datetime.now() + timedelta(days=7)).isoformat()),
                7  # Cancel in 7 days
            )
            
            return {
                'success': True,
                'booking_id': booking_id,
                'cancellation_costs': {
                    'now': {
                        'fee': cost_now.cancellation_fee,
                        'refund': cost_now.refund_amount,
                        'total_loss': cost_now.total_loss
                    },
                    'week_later': {
                        'fee': cost_later.cancellation_fee,
                        'refund': cost_later.refund_amount,
                        'total_loss': cost_later.total_loss
                    }
                },
                'recommendation': cost_now.recommendation
            }
            
        except Exception as e:
            logger.error(f"Error calculating cancellation cost: {str(e)}")
            return {'error': f'Could not calculate cancellation cost: {str(e)}'}
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            'success': False,
            'error': error_message,
            'response': {
                'text': error_message,
                'audio': self._text_to_speech(error_message),
                'suggestions': [
                    "Try asking about flight status",
                    "Ask to change your booking",
                    "Update your preferences"
                ]
            },
            'timestamp': datetime.utcnow().isoformat()
        }

# Global voice chatbot instance
voice_chatbot = VoiceChatbot()