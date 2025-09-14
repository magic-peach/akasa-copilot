from flask import Flask, request, jsonify, session, redirect
from flask_cors import CORS
from src.services.event_service import event_processor
from src.services.voice_chatbot import voice_chatbot
from src.services.flight_search_service import flight_search_service
from src.services.advanced_risk_predictor import advanced_risk_predictor
from src.services.google_oauth_service import oauth_service
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
            'pnr': pnr_number,
            'booking_info': pnr_info
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

@app.route('/flights/comprehensive-analysis', methods=['POST'])
def comprehensive_flight_analysis():
    """Perform comprehensive flight analysis"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        analysis_result = advanced_risk_predictor.comprehensive_analysis(data)
        
        logger.info(f"Comprehensive analysis completed for route {analysis_result['route']}")
        
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