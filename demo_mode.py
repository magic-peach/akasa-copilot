#!/usr/bin/env python3
"""
Demo mode for Akasa Booking API
Runs without Supabase for testing and demonstration
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime
import json
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# In-memory storage for demo mode
demo_data = {
    'bookings': {},
    'customers': {},
    'flight_states': {},
    'alerts': {},
    'chat_sessions': {}
}

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'mode': 'demo',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'Akasa Booking API (Demo Mode)'
    }), 200

@app.route('/bookings', methods=['POST'])
def create_booking():
    """Create a new booking (demo mode)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Generate booking ID
        booking_id = str(uuid.uuid4())
        
        # Create booking
        booking = {
            'id': booking_id,
            'customer_id': data.get('customer_id'),
            'flight_number': data.get('flight_number'),
            'origin': data.get('origin'),
            'destination': data.get('destination'),
            'depart_date': data.get('depart_date'),
            'status': data.get('status', 'confirmed'),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Store in memory
        demo_data['bookings'][booking_id] = booking
        
        logger.info(f"Created demo booking: {booking_id}")
        
        return jsonify({
            'message': 'Booking created successfully (demo mode)',
            'booking': booking
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating booking: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/bookings/<booking_id>', methods=['GET'])
def get_booking(booking_id):
    """Get booking by ID (demo mode)"""
    try:
        booking = demo_data['bookings'].get(booking_id)
        
        if booking:
            return jsonify({'booking': booking}), 200
        else:
            return jsonify({'error': 'Booking not found'}), 404
            
    except Exception as e:
        logger.error(f"Error fetching booking: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/bookings', methods=['GET'])
def list_bookings():
    """List all bookings (demo mode)"""
    try:
        bookings = list(demo_data['bookings'].values())
        
        return jsonify({
            'bookings': bookings,
            'count': len(bookings),
            'mode': 'demo'
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing bookings: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/chat/voice', methods=['POST'])
def voice_chat_demo():
    """Voice chat endpoint (demo mode)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        user_id = data.get('user_id', 'demo_user')
        text_input = data.get('text_input', '')
        
        # Simple demo responses
        demo_responses = {
            'status': f"Flight QP1001 is currently on time. Departure at 12:00 PM from Delhi to Mumbai.",
            'change': f"I understand you want to change your booking. Available options for Monday include flights at 9:30 AM and 2:15 PM.",
            'risk': f"The disruption risk for your flight is LOW (0.25). Weather conditions are favorable.",
            'help': f"I'm your Akasa AI assistant. I can help with flight status, booking changes, and preferences."
        }
        
        # Simple intent detection
        text_lower = text_input.lower()
        if any(word in text_lower for word in ['status', 'flight']):
            response_text = demo_responses['status']
            intent = 'flight_status'
        elif any(word in text_lower for word in ['change', 'reschedule']):
            response_text = demo_responses['change']
            intent = 'booking_change'
        elif any(word in text_lower for word in ['risk', 'delay']):
            response_text = demo_responses['risk']
            intent = 'disruption_risk'
        else:
            response_text = demo_responses['help']
            intent = 'general_help'
        
        # Store session
        session_id = str(uuid.uuid4())
        demo_data['chat_sessions'][session_id] = {
            'user_id': user_id,
            'input': text_input,
            'response': response_text,
            'intent': intent,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'user_input': text_input,
            'intent': intent,
            'confidence': 0.8,
            'response': {
                'text': response_text,
                'audio': 'MOCK_AUDIO_DATA',
                'suggestions': ['Check flight status', 'Change booking', 'Get help']
            },
            'mode': 'demo'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in voice chat: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/flights/<flight_id>/status', methods=['GET'])
def get_flight_status_demo(flight_id):
    """Get flight status (demo mode)"""
    try:
        # Demo flight status
        demo_status = {
            'flight_number': flight_id,
            'status': 'ON_TIME',
            'gate': 'G12',
            'terminal': 'T3',
            'eta': '2024-02-15T14:30:00Z',
            'etd': '2024-02-15T12:00:00Z',
            'origin': {'code': 'DEL', 'name': 'Delhi'},
            'destination': {'code': 'BOM', 'name': 'Mumbai'},
            'confidence_score': 0.92,
            'last_updated': datetime.utcnow().isoformat() + 'Z'
        }
        
        return jsonify({
            'success': True,
            'flight_status': demo_status,
            'mode': 'demo'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting flight status: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/flights/<flight_id>/risk', methods=['GET'])
def get_flight_risk_demo(flight_id):
    """Get flight disruption risk (demo mode)"""
    try:
        import random
        
        # Demo risk prediction
        risk_score = round(random.uniform(0.1, 0.8), 3)
        
        if risk_score < 0.3:
            risk_level = 'LOW'
        elif risk_score < 0.6:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'HIGH'
        
        demo_prediction = {
            'flight_id': flight_id,
            'flight_number': flight_id,
            'disruption_risk': risk_score,
            'risk_level': risk_level,
            'risk_factors': {
                'weather_score': round(random.uniform(0.1, 0.5), 3),
                'historical_score': round(random.uniform(0.1, 0.4), 3),
                'real_time_score': round(random.uniform(0.1, 0.3), 3),
                'route_score': round(random.uniform(0.2, 0.6), 3)
            },
            'confidence': 0.85,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'disruption_prediction': demo_prediction,
            'mode': 'demo'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting flight risk: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/demo/info', methods=['GET'])
def demo_info():
    """Demo mode information"""
    return jsonify({
        'mode': 'demo',
        'message': 'Running in demo mode without Supabase',
        'features': [
            'Basic booking operations',
            'Voice chat simulation',
            'Flight status demo',
            'Risk prediction demo'
        ],
        'note': 'To use full features, set up Supabase credentials in .env file',
        'data_storage': 'In-memory (resets on restart)',
        'current_data': {
            'bookings': len(demo_data['bookings']),
            'chat_sessions': len(demo_data['chat_sessions'])
        }
    }), 200

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 AKASA BOOKING API - DEMO MODE")
    print("=" * 50)
    print("✅ Running without Supabase for testing")
    print("🌐 Server starting at http://localhost:5000")
    print("📚 Try these endpoints:")
    print("   GET  /health - Health check")
    print("   GET  /demo/info - Demo information")
    print("   POST /bookings - Create booking")
    print("   POST /chat/voice - Voice chat demo")
    print("   GET  /flights/{id}/status - Flight status")
    print("   GET  /flights/{id}/risk - Risk prediction")
    print("-" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)