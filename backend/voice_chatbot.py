"""
Voice-enabled chatbot system for Akasa Airlines
Handles speech-to-text, conversational AI, and text-to-speech
"""

import base64
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from database import db
from nlp_agent import nlp_agent
from genai_agent import flight_status_agent
from disruption_predictor import disruption_predictor
import logging

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
            'general_help': ['help', 'assistance', 'support', 'what can you do']
        }
    
    def process_voice_request(self, user_id: str, audio_data: Optional[str] = None, 
                            text_input: Optional[str] = None) -> Dict[str, Any]:
        """
        Process voice or text input through the conversational AI pipeline
        
        Args:
            user_id: User identifier for conversation tracking
            audio_data: Base64 encoded audio data (optional)
            text_input: Direct text input (optional)
            
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
            
            # Step 3: Classify intent and process request
            intent_result = self._classify_intent(user_text, chat_history)
            
            # Step 4: Route to appropriate agent based on intent
            agent_response = self._route_to_agent(intent_result, user_text, user_id, chat_history)
            
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
        Convert speech to text using OpenAI Whisper (mock implementation)
        In production, this would call OpenAI Whisper API or use Web Speech API
        """
        try:
            # Mock implementation - in production you would:
            # 1. Decode base64 audio data
            # 2. Call OpenAI Whisper API or use browser Web Speech API
            # 3. Return transcribed text
            
            # For demo purposes, simulate transcription
            mock_transcriptions = [
                "What is the status of my flight QP1001?",
                "Change my booking to next Monday",
                "I prefer window seats and vegetarian meals",
                "Subscribe me to flight alerts via SMS",
                "What is the risk of delay for flight QP1002?",
                "Show me my booking details",
                "Cancel my flight reservation"
            ]
            
            import random
            transcribed_text = random.choice(mock_transcriptions)
            
            logger.info(f"Mock speech-to-text result: {transcribed_text}")
            return transcribed_text
            
        except Exception as e:
            logger.error(f"Error in speech-to-text: {str(e)}")
            return None
    
    def _text_to_speech(self, text: str) -> Optional[str]:
        """
        Convert text to speech using OpenAI TTS or ElevenLabs (mock implementation)
        In production, this would call TTS APIs and return audio data
        """
        try:
            # Mock implementation - in production you would:
            # 1. Call OpenAI TTS API or ElevenLabs API
            # 2. Get audio data back
            # 3. Encode as base64 and return
            
            # For demo purposes, return mock audio data
            mock_audio_data = base64.b64encode(f"MOCK_AUDIO_DATA_FOR: {text}".encode()).decode()
            
            logger.info(f"Mock text-to-speech generated for: {text[:50]}...")
            return mock_audio_data
            
        except Exception as e:
            logger.error(f"Error in text-to-speech: {str(e)}")
            return None
    
    def _classify_intent(self, user_text: str, chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Classify user intent based on text and conversation history"""
        try:
            user_lower = user_text.lower()
            intent_scores = {}
            
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
                       user_id: str, chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Route request to appropriate specialized agent"""
        try:
            intent = intent_result['intent']
            
            if intent == 'flight_status':
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
                return self._suggest_flights_from_calendar(user_text, user_id)
            
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
        """Process alert subscription request"""
        try:
            # Extract preferred channel
            text_lower = user_text.lower()
            
            if any(word in text_lower for word in ['sms', 'text', 'phone']):
                channel = 'sms'
            elif any(word in text_lower for word in ['email', 'mail']):
                channel = 'email'
            elif any(word in text_lower for word in ['push', 'app', 'notification']):
                channel = 'push'
            else:
                channel = 'email'  # Default
            
            # Store subscription (this would integrate with actual services)
            subscription_data = {
                'user_id': user_id,
                'channel': channel,
                'active': True,
                'created_at': datetime.utcnow().isoformat()
            }
            
            return {
                'success': True,
                'channel': channel,
                'subscription_data': subscription_data
            }
            
        except Exception as e:
            logger.error(f"Error processing alert subscription: {str(e)}")
            return {'error': str(e)}
    
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
            # Import calendar analysis service
            from calendar_analysis_service import CalendarAnalysisService
            
            calendar_service = CalendarAnalysisService()
            
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
    
    def _suggest_flights_from_calendar(self, user_text: str, user_id: str) -> Dict[str, Any]:
        """Suggest flights based on calendar events"""
        try:
            # Get calendar analysis first
            calendar_analysis = self._analyze_calendar_events(user_id)
            
            if 'error' in calendar_analysis:
                return calendar_analysis
            
            # Extract travel preferences from user text
            origin = 'DEL'  # Default origin
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
            # Import cancellation cost service
            from cancellation_cost_service import CancellationCostService
            
            cost_service = CancellationCostService()
            
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