from flask import Flask, request, jsonify, session, redirect
from flask_cors import CORS
from src.services.event_service import event_processor
from src.services.voice_chatbot import voice_chatbot
from src.services.flight_search_service import flight_search_service
from src.services.advanced_risk_predictor import advanced_risk_predictor
from src.services.google_oauth_service import oauth_service
from src.services.calendar_service import calendar_service
import logging
from datetime import datetime
import atexit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='views', static_url_path='/views')
CORS(app)
# Initialize Google OAuth for calendar integration
oauth_service.init_app(app)

# Start the event processing background worker
event_processor.start_background_worker()

# Ensure background worker stops when app shuts down
atexit.register(event_processor.stop_background_worker)

# =====================
# Google OAuth Routes
# =====================

@app.route('/login')
def login():
    """Initiate Google OAuth login"""
    try:
        url = oauth_service.get_authorization_url()
        return redirect(url)
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login error', 'message': str(e)}), 500

@app.route('/auth/callback')
def auth_callback():
    """OAuth callback route for /auth/callback - redirects to main callback with params"""
    # Preserve all query parameters when redirecting
    query_string = request.query_string.decode('utf-8')
    if query_string:
        return redirect(f'/callback?{query_string}')
    else:
        return redirect('/callback')

@app.route('/oauth2callback')
def oauth2callback():
    """Legacy OAuth callback route - redirects to new callback with params"""
    # Preserve all query parameters when redirecting
    query_string = request.query_string.decode('utf-8')
    if query_string:
        return redirect(f'/callback?{query_string}')
    else:
        return redirect('/callback')

@app.route('/callback')
def callback():
    """Handle Google OAuth callback, store credentials, and prefetch events"""
    try:
        authorization_code = request.args.get('code')
        state = request.args.get('state')
        if not authorization_code:
            return jsonify({'error': 'No authorization code'}), 400

        user_info = oauth_service.handle_oauth_callback(authorization_code, state)
        # Prefetch and cache events for faster UX
        events = oauth_service.list_upcoming_events(50)
        session['calendar_events'] = events

        logger.info(f"OAuth login successful for: {user_info.get('email') if user_info else 'unknown'}")
        # Store user info in session for frontend access
        session['user_info'] = user_info
        # Redirect to the search page
        return redirect('/search')
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return jsonify({'error': 'OAuth callback failed', 'message': str(e)}), 500

@app.route('/user/info', methods=['GET'])
def get_user_info():
    """Get current user information from OAuth session"""
    try:
        if 'user_info' not in session:
            return jsonify({'error': 'User not authenticated'}), 401
        
        user_info = session['user_info']
        return jsonify({
            'success': True,
            'user': {
                'name': user_info.get('name', ''),
                'email': user_info.get('email', ''),
                'picture': user_info.get('picture', ''),
                'is_authenticated': True
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        return jsonify({'error': 'Failed to get user info'}), 500

@app.route('/logout', methods=['POST'])
def logout():
    """Logout user and clear session"""
    try:
        session.clear()
        return jsonify({'success': True, 'message': 'Logged out successfully'}), 200
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({'error': 'Logout failed'}), 500

# =====================
# Calendar Sync Routes
# =====================

@app.route('/calendar/events', methods=['GET'])
def get_calendar_events():
    """Get user's calendar events"""
    try:
        if 'user_info' not in session:
            return jsonify({'error': 'User not authenticated'}), 401
        
        user_id = session['user_info'].get('email', 'unknown')
        days_ahead = request.args.get('days_ahead', 30, type=int)
        
        # Sync calendar events
        events = calendar_service.sync_calendar_events(user_id, days_ahead)
        
        # Convert events to JSON-serializable format
        events_data = []
        for event in events:
            events_data.append({
                'id': event.id,
                'summary': event.summary,
                'start_time': event.start_time.isoformat(),
                'end_time': event.end_time.isoformat(),
                'location': event.location,
                'description': event.description,
                'is_travel_related': event.is_travel_related,
                'destination_city': event.destination_city,
                'destination_airport': event.destination_airport,
                'travel_type': event.travel_type,
                'priority': event.priority
            })
        
        return jsonify({
            'success': True,
            'events': events_data,
            'total_events': len(events_data),
            'travel_events': len([e for e in events_data if e['is_travel_related']])
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching calendar events: {str(e)}")
        return jsonify({'error': 'Failed to fetch calendar events', 'message': str(e)}), 500

@app.route('/calendar/flight-suggestions', methods=['GET'])
def get_flight_suggestions():
    """Get flight suggestions based on calendar events"""
    try:
        if 'user_info' not in session:
            return jsonify({'error': 'User not authenticated'}), 401
        
        user_id = session['user_info'].get('email', 'unknown')
        origin = request.args.get('origin', 'DEL')
        
        # Generate flight suggestions
        suggestions = calendar_service.generate_flight_suggestions(user_id, origin)
        
        # Convert suggestions to JSON-serializable format
        suggestions_data = []
        for suggestion in suggestions:
            suggestions_data.append({
                'event_id': suggestion.event_id,
                'event_summary': suggestion.event_summary,
                'destination': suggestion.destination,
                'suggested_departure': suggestion.suggested_departure.isoformat(),
                'suggested_return': suggestion.suggested_return.isoformat(),
                'flight_options': suggestion.flight_options,
                'conflict_warning': suggestion.conflict_warning,
                'priority_score': suggestion.priority_score
            })
        
        return jsonify({
            'success': True,
            'suggestions': suggestions_data,
            'total_suggestions': len(suggestions_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating flight suggestions: {str(e)}")
        return jsonify({'error': 'Failed to generate flight suggestions', 'message': str(e)}), 500

@app.route('/calendar/check-conflicts', methods=['POST'])
def check_booking_conflicts():
    """Check for conflicts between flight booking and calendar events"""
    try:
        if 'user_info' not in session:
            return jsonify({'error': 'User not authenticated'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No booking details provided'}), 400
        
        user_id = session['user_info'].get('email', 'unknown')
        
        # Detect booking conflicts
        conflicts = calendar_service.detect_booking_conflicts(user_id, data)
        
        # Convert conflicts to JSON-serializable format
        conflicts_data = []
        for conflict in conflicts:
            conflicts_data.append({
                'booking_id': conflict.booking_id,
                'flight_details': conflict.flight_details,
                'conflicting_events': [
                    {
                        'id': event.id,
                        'summary': event.summary,
                        'start_time': event.start_time.isoformat(),
                        'end_time': event.end_time.isoformat(),
                        'location': event.location,
                        'travel_type': event.travel_type,
                        'priority': event.priority
                    } for event in conflict.conflicting_events
                ],
                'conflict_type': conflict.conflict_type,
                'severity': conflict.severity,
                'suggested_actions': conflict.suggested_actions
            })
        
        # Send conflict warnings if any conflicts found
        if conflicts:
            calendar_service.send_conflict_warning(user_id, conflicts)
        
        return jsonify({
            'success': True,
            'conflicts': conflicts_data,
            'has_conflicts': len(conflicts_data) > 0,
            'total_conflicts': len(conflicts_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking booking conflicts: {str(e)}")
        return jsonify({'error': 'Failed to check booking conflicts', 'message': str(e)}), 500

# =====================
# Frontend Routes
# =====================

@app.route('/')
def index():
    """Serve the welcome page"""
    return app.send_static_file('index.html')

@app.route('/signup')
def signup():
    """Serve the signup page"""
    return app.send_static_file('signup.html')

@app.route('/signin')
def signin():
    """Serve the signin page"""
    return app.send_static_file('signin.html')

@app.route('/search')
def search():
    """Serve the search page"""
    return app.send_static_file('search.html')

# =====================
# API Routes
# =====================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }), 200

@app.route('/flights/search', methods=['POST'])
def search_flights():
    """Search for flights based on criteria"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Extract search parameters
        origin = data.get('origin', 'DEL')
        destination = data.get('destination', 'BOM')
        date = data.get('date')
        budget = data.get('budget', 10000)

        # Use flight search service
        results = flight_search_service.search_flights(
            origin=origin,
            destination=destination,
            date=date,
            budget=budget
        )

        return jsonify({
            'success': True,
            'flights': results,
            'search_params': {
                'origin': origin,
                'destination': destination,
                'date': date,
                'budget': budget
            }
        }), 200

    except Exception as e:
        logger.error(f"Flight search error: {str(e)}")
        return jsonify({'error': 'Flight search failed', 'message': str(e)}), 500

@app.route('/flights/<flight_id>/risk-analysis', methods=['GET'])
def get_flight_risk_analysis(flight_id):
    """Get risk analysis for a specific flight"""
    try:
        analysis = advanced_risk_predictor.analyze_flight_risk(flight_id)
        
        # Add weather data to the analysis
        if analysis.get('success') and analysis.get('analysis'):
            # Get origin and destination from the analysis
            flight_data = analysis['analysis'].get('flight', {})
            origin = flight_data.get('origin', 'DEL')
            destination = flight_data.get('destination', 'BOM')
            
            # Fetch weather data for both airports
            try:
                import requests
                origin_weather_response = requests.get(f'http://localhost:8081/weather/{origin}')
                dest_weather_response = requests.get(f'http://localhost:8081/weather/{destination}')
                
                if origin_weather_response.status_code == 200:
                    origin_weather = origin_weather_response.json().get('weather', {})
                    analysis['analysis']['origin_weather'] = origin_weather
                
                if dest_weather_response.status_code == 200:
                    dest_weather = dest_weather_response.json().get('weather', {})
                    analysis['analysis']['destination_weather'] = dest_weather
                    
            except Exception as weather_error:
                logger.warning(f"Could not fetch weather data: {weather_error}")
                # Add mock weather data if API call fails
                analysis['analysis']['origin_weather'] = {
                    'current': {'condition': {'text': 'Clear'}, 'temp_c': 28}
                }
                analysis['analysis']['destination_weather'] = {
                    'current': {'condition': {'text': 'Clear'}, 'temp_c': 30}
                }
        
        return jsonify({
            'success': True,
            'flight_id': flight_id,
            'risk_analysis': analysis
        }), 200
    except Exception as e:
        logger.error(f"Risk analysis error: {str(e)}")
        return jsonify({'error': 'Risk analysis failed', 'message': str(e)}), 500

@app.route('/pnr/<pnr_number>', methods=['GET'])
def get_pnr_info(pnr_number):
    """Get PNR information"""
    try:
        pnr_info = flight_search_service.get_pnr_info(pnr_number)
        return jsonify({
            'success': True,
            'pnr_details': pnr_info
        }), 200
    except Exception as e:
        logger.error(f"PNR lookup error: {str(e)}")
        return jsonify({'error': 'PNR lookup failed', 'message': str(e)}), 500

@app.route('/chat/voice', methods=['POST'])
def voice_chat():
    """Handle voice chat requests"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400

        message = data['message']
        response = voice_chatbot.process_voice_message(message)
        
        return jsonify({
            'success': True,
            'response': response
        }), 200
    except Exception as e:
        logger.error(f"Voice chat error: {str(e)}")
        return jsonify({'error': 'Voice chat failed', 'message': str(e)}), 500

@app.route('/weather/<airport_code>', methods=['GET'])
def get_weather_data(airport_code):
    """Get weather data for a specific airport"""
    try:
        # Mock weather data - in production, this would call a real weather API
        weather_data = {
            'airport_code': airport_code,
            'current': {
                'temp_c': 28,
                'temp_f': 82,
                'condition': {
                    'text': 'Clear',
                    'icon': '//cdn.weatherapi.com/weather/64x64/day/113.png'
                },
                'humidity': 65,
                'wind_kph': 12,
                'wind_dir': 'NE',
                'pressure_mb': 1013,
                'visibility_km': 10
            },
            'forecast': {
                'today': {
                    'max_temp_c': 32,
                    'min_temp_c': 24,
                    'condition': 'Sunny',
                    'chance_of_rain': 10
                },
                'tomorrow': {
                    'max_temp_c': 30,
                    'min_temp_c': 22,
                    'condition': 'Partly Cloudy',
                    'chance_of_rain': 20
                }
            },
            'alerts': [],
            'last_updated': datetime.utcnow().isoformat()
        }
        
        # Add some variation based on airport code
        if airport_code in ['BOM', 'GOA']:
            weather_data['current']['condition']['text'] = 'Partly Cloudy'
            weather_data['forecast']['today']['chance_of_rain'] = 30
        elif airport_code in ['DEL', 'LKO']:
            weather_data['current']['condition']['text'] = 'Haze'
            weather_data['current']['visibility_km'] = 5
        elif airport_code in ['CCU', 'MAA']:
            weather_data['current']['condition']['text'] = 'Light Rain'
            weather_data['forecast']['today']['chance_of_rain'] = 60
        
        return jsonify({
            'success': True,
            'weather': weather_data
        }), 200
        
    except Exception as e:
        logger.error(f"Weather API error: {str(e)}")
        return jsonify({'error': 'Weather data unavailable', 'message': str(e)}), 500

@app.route('/flights/comprehensive-analysis', methods=['POST'])
def comprehensive_flight_analysis():
    """Perform comprehensive flight analysis"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        flights = data.get('flights', [])
        if not flights:
            return jsonify({'error': 'No flights provided for analysis'}), 400

        analysis_result = advanced_risk_predictor.predict_comprehensive_risk(flights)
        
        if 'error' in analysis_result:
            return jsonify({'error': analysis_result['error']}), 500
        
        logger.info(f"Comprehensive analysis completed for route {analysis_result.get('route', 'Unknown')}")
        
        return jsonify({
            'success': True,
            'comprehensive_analysis': analysis_result,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in comprehensive flight analysis: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred during comprehensive analysis'
        }), 500

if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0', port=8081)
    finally:
        # Ensure background worker is stopped
        event_processor.stop_background_worker()