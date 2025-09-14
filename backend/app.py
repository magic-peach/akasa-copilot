from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from database import db
from models import Booking
from rebooking_service import rebooking_service
from event_service import event_processor
from event_models import FlightState
from genai_agent import flight_status_agent
from disruption_predictor import disruption_predictor
from nlp_agent import nlp_agent
from voice_chatbot import voice_chatbot
from notification_service import notification_service
from flight_search_service import flight_search_service
from advanced_risk_predictor import advanced_risk_predictor
from google_oauth_service import oauth_service
import logging
import random
from datetime import datetime, timedelta
import atexit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='frontend', static_url_path='/frontend')
CORS(app)
# Initialize Google OAuth for calendar integration
oauth_service.init_app(app)

# Start the event processing background worker
event_processor.start_background_worker()

# Ensure background worker stops when app shuts down
atexit.register(event_processor.stop_background_worker)

# =====================
# Google Calendar Integration (OAuth + Helpers)
# =====================
def _parse_event_start_date(ev):
    """Parse event start into date object"""
    try:
        start = ev.get('start', {})
        val = start.get('dateTime') or start.get('date')
        if not val:
            return None
        if 'T' in val:
            dt = datetime.fromisoformat(val.replace('Z', '+00:00'))
            return dt.date()
        else:
            return datetime.strptime(val, '%Y-%m-%d').date()
    except Exception:
        return None

def _events_from_session(max_results: int = 50):
    """Get cached Google events or fetch and cache them"""
    try:
        events = session.get('calendar_events')
        if not events:
            events = oauth_service.list_upcoming_events(max_results)
            if events is not None:
                session['calendar_events'] = events
        return events or []
    except Exception:
        return []

def _build_travel_windows(events):
    """Build travel windows from events: day-before and day-of each event"""
    windows = set()
    details = []
    for ev in events:
        d = _parse_event_start_date(ev)
        if not d:
            continue
        windows.add(d.isoformat())
        windows.add((d - timedelta(days=1)).isoformat())
        details.append({
            'summary': ev.get('summary', 'No Title'),
            'event_date': d.isoformat(),
            'suggested_travel_dates': [(d - timedelta(days=1)).isoformat(), d.isoformat()],
            'location': ev.get('location', '')
        })
    return sorted(list(windows)), details

def get_calendar_suggestions_for_search(date_str: str):
    """Return recommended dates derived from Google Calendar for search UX"""
    events = _events_from_session()
    if not events:
        return {}
    windows, _ = _build_travel_windows(events)
    return {
        'recommended_dates': windows,
        'source': 'google_calendar',
        'count_events_considered': len(events)
    }

def _estimate_cancellation_cost(origin: str, destination: str):
    """Heuristic estimate for cancellation costs now vs a week later"""
    route_key = f"{origin}-{destination}"
    base = rebooking_service.BASE_PRICES.get(route_key, 4000)
    cancel_now = int(base * 0.20 + 500)
    cancel_in_week = int(base * 0.35 + 500)
    return {
        'currency': 'INR',
        'cancel_now': cancel_now,
        'cancel_in_week': cancel_in_week,
        'assumptions': 'Heuristic estimate: 20%+₹500 if cancelled now vs 35%+₹500 if cancelled in 7 days.'
    }

def _assess_booking_against_calendar(booking_date: str, origin: str, destination: str):
    """Compare a booking date to calendar event windows and compute advice/warnings"""
    events = _events_from_session()
    if not events:
        return None
    windows, details = _build_travel_windows(events)
    on_track = booking_date in windows

    nearest = None
    try:
        bdate = datetime.strptime(booking_date, '%Y-%m-%d').date()
        min_delta = None
        for d in details:
            ed = datetime.strptime(d['event_date'], '%Y-%m-%d').date()
            delta = abs((ed - bdate).days)
            if min_delta is None or delta < min_delta:
                min_delta = delta
                nearest = d
    except Exception:
        pass

    warning = None
    if not on_track and nearest:
        warning = f"Booking date {booking_date} does not align with nearby calendar event on {nearest['event_date']} ('{nearest['summary']}')."

    return {
        'aligned_with_schedule': on_track,
        'nearest_event': nearest,
        'warning': warning,
        'recommended_dates': windows,
        'cancellation_cost_estimate': _estimate_cancellation_cost(origin, destination)
    }

# ---------------------
# Calendar OAuth Routes
# ---------------------
@app.route('/calendar/login')
def calendar_login():
    """Redirect user to Google OAuth for Calendar access"""
    try:
        url = oauth_service.get_authorization_url()
        if not url:
            return jsonify({'error': 'Failed to initiate Google OAuth'}), 500
        return redirect(url)
    except Exception as e:
        logger.error(f"Calendar login error: {str(e)}")
        return jsonify({'error': 'Login error', 'message': str(e)}), 500

@app.route('/oauth2callback')
def oauth2callback():
    """Legacy OAuth callback route - redirects to new callback"""
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
        # Redirect to the main frontend index page
        return redirect('/frontend/index.html')
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return jsonify({'error': 'OAuth callback failed', 'message': str(e)}), 500

@app.route('/calendar/events', methods=['GET'])
def calendar_events():
    """Return upcoming Google Calendar events"""
    if 'credentials' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated with Google'}), 401
    # Refresh events from Google Calendar
    events = oauth_service.list_upcoming_events(50)
    session['calendar_events'] = events
    return jsonify({'success': True, 'count': len(events), 'events': events}), 200

@app.route('/calendar/sync', methods=['GET'])
def sync_calendar_events():
    """Sync Google Calendar events and return travel opportunities"""
    if 'credentials' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated with Google'}), 401
    # Refresh events from Google Calendar
    events = oauth_service.list_upcoming_events(50)
    session['calendar_events'] = events
    
    # Process events to find travel opportunities
    windows, details = _build_travel_windows(events)
    
    return jsonify({
        'success': True, 
        'count': len(events), 
        'events': events,
        'travel_windows': windows,
        'travel_details': details
    }), 200

@app.route('/calendar/travel-windows', methods=['GET'])
def calendar_travel_windows():
    """Return recommended travel dates derived from Calendar events"""
    if 'credentials' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated with Google'}), 401
    events = _events_from_session()
    windows, details = _build_travel_windows(events)
    return jsonify({'success': True, 'recommended_dates': windows, 'details': details}), 200

@app.route('/calendar/add-event', methods=['POST'])
def calendar_add_event():
    """Create a new event in the user's Google Calendar"""
    if 'credentials' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated with Google'}), 401
    try:
        data = request.get_json() or {}
        summary = data.get('summary', 'Flight')
        description = data.get('description', '')
        location = data.get('location', '')
        start = data.get('start')  # RFC3339 string
        end = data.get('end')      # RFC3339 string

        if not start or not end:
            return jsonify({'error': 'start and end are required in RFC3339 format'}), 400

        event_body = {
            'summary': summary,
            'description': description,
            'location': location,
            'start': {'dateTime': start},
            'end': {'dateTime': end}
        }
        created = oauth_service.create_calendar_event(event_body)
        if not created:
            return jsonify({'success': False, 'message': 'Failed to create calendar event'}), 500
        return jsonify({'success': True, 'event': created}), 201
    except Exception as e:
        logger.error(f"Error creating calendar event: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Root route to serve welcome page
@app.route('/')
def index():
    """Serve the welcome page"""
    return app.send_static_file('welcome.html')

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'Akasa Booking API'
    }), 200

@app.route('/bookings', methods=['POST'])
def create_booking():
    """Create a new booking"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No JSON data provided',
                'message': 'Request body must contain valid JSON'
            }), 400
        
        # Create booking object
        booking = Booking.from_dict(data)
        
        # Validate booking data
        validation_errors = booking.validate()
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': validation_errors
            }), 400
        
        # Insert booking into database
        supabase = db.get_client()
        result = supabase.table('bookings').insert(booking.to_dict()).execute()
        
        if result.data:
            created_booking = result.data[0]
            logger.info(f"Created booking with ID: {created_booking['id']}")
            
            # Assess against Google Calendar if available and provide advice
            schedule_advice = None
            try:
                schedule_advice = _assess_booking_against_calendar(
                    created_booking['depart_date'],
                    created_booking['origin'],
                    created_booking['destination']
                )
            except Exception:
                schedule_advice = None

            # Optionally create a Google Calendar event for the booking (all-day)
            calendar_event = None
            try:
                if 'credentials' in session:
                    start_date = datetime.strptime(created_booking['depart_date'], '%Y-%m-%d').date()
                    event_body = {
                        'summary': f"Flight {created_booking['flight_number']} {created_booking['origin']} -> {created_booking['destination']}",
                        'description': f"Akasa booking ID: {created_booking['id']}",
                        'start': {'date': start_date.isoformat()},
                        'end': {'date': (start_date + timedelta(days=1)).isoformat()}
                    }
                    calendar_event = oauth_service.create_calendar_event(event_body)
            except Exception as e:
                logger.error(f"Failed to create calendar event: {str(e)}")

            return jsonify({
                'message': 'Booking created successfully',
                'booking': created_booking,
                'schedule_advice': schedule_advice,
                'calendar_event': {
                    'id': calendar_event.get('id'),
                    'htmlLink': calendar_event.get('htmlLink')
                } if calendar_event else None
            }), 201
        else:
            logger.error("Failed to create booking - no data returned")
            return jsonify({
                'error': 'Failed to create booking',
                'message': 'Database operation failed'
            }), 500
            
    except Exception as e:
        logger.error(f"Error creating booking: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while creating the booking'
        }), 500

@app.route('/bookings/<booking_id>', methods=['GET'])
def get_booking(booking_id):
    """Fetch a booking by ID"""
    try:
        # Validate booking_id format (basic UUID validation)
        if not booking_id or len(booking_id.strip()) == 0:
            return jsonify({
                'error': 'Invalid booking ID',
                'message': 'Booking ID cannot be empty'
            }), 400
        
        # Query database for booking
        supabase = db.get_client()
        result = supabase.table('bookings').select('*').eq('id', booking_id).execute()
        
        if result.data and len(result.data) > 0:
            booking = result.data[0]
            logger.info(f"Retrieved booking with ID: {booking_id}")
            
            return jsonify({
                'booking': booking
            }), 200
        else:
            logger.info(f"Booking not found with ID: {booking_id}")
            return jsonify({
                'error': 'Booking not found',
                'message': f'No booking found with ID: {booking_id}'
            }), 404
            
    except Exception as e:
        logger.error(f"Error fetching booking {booking_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while fetching the booking'
        }), 500

@app.route('/bookings', methods=['GET'])
def list_bookings():
    """List all bookings with optional filtering"""
    try:
        # Get query parameters for filtering
        customer_id = request.args.get('customer_id')
        flight_number = request.args.get('flight_number')
        status = request.args.get('status')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        supabase = db.get_client()
        query = supabase.table('bookings').select('*')
        
        # Apply filters
        if customer_id:
            query = query.eq('customer_id', customer_id)
        if flight_number:
            query = query.eq('flight_number', flight_number)
        if status:
            query = query.eq('status', status)
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1)
        
        # Order by created_at descending
        query = query.order('created_at', desc=True)
        
        result = query.execute()
        
        bookings = result.data or []
        
        return jsonify({
            'bookings': bookings,
            'count': len(bookings),
            'offset': offset,
            'limit': limit
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing bookings: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while fetching bookings'
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource was not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

@app.route('/bookings/<booking_id>/request-change', methods=['POST'])
def request_booking_change(booking_id):
    """Request a booking change with new date and get available options"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No JSON data provided',
                'message': 'Request body must contain valid JSON with new_date'
            }), 400
        
        new_date = data.get('new_date')
        if not new_date:
            return jsonify({
                'error': 'Missing required field',
                'message': 'new_date is required in YYYY-MM-DD format'
            }), 400
        
        # Validate date format
        try:
            datetime.strptime(new_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({
                'error': 'Invalid date format',
                'message': 'new_date must be in YYYY-MM-DD format'
            }), 400
        
        # Get the original booking
        supabase = db.get_client()
        result = supabase.table('bookings').select('*').eq('id', booking_id).execute()
        
        if not result.data or len(result.data) == 0:
            return jsonify({
                'error': 'Booking not found',
                'message': f'No booking found with ID: {booking_id}'
            }), 404
        
        original_booking = result.data[0]
        
        # Check if booking can be changed
        if original_booking['status'] not in ['confirmed', 'pending']:
            return jsonify({
                'error': 'Booking cannot be changed',
                'message': f'Bookings with status "{original_booking["status"]}" cannot be modified'
            }), 400
        
        # Check availability for the new date
        available_options = rebooking_service.check_availability(
            original_booking['origin'],
            original_booking['destination'],
            new_date
        )
        
        if not available_options:
            return jsonify({
                'error': 'No flights available',
                'message': f'No flights available from {original_booking["origin"]} to {original_booking["destination"]} on {new_date}'
            }), 404
        
        # Calculate cost differences for each option
        options_with_costs = []
        for option in available_options:
            option['depart_date'] = new_date  # Add the requested date to the option
            cost_info = rebooking_service.calculate_cost_difference(original_booking, option)
            
            options_with_costs.append({
                **option,
                'cost_breakdown': cost_info
            })
        
        logger.info(f"Found {len(options_with_costs)} rebooking options for booking {booking_id}")
        
        return jsonify({
            'original_booking': {
                'id': original_booking['id'],
                'flight_number': original_booking['flight_number'],
                'depart_date': original_booking['depart_date'],
                'origin': original_booking['origin'],
                'destination': original_booking['destination']
            },
            'requested_date': new_date,
            'available_options': options_with_costs,
            'message': f'Found {len(options_with_costs)} available flights for your requested change'
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing change request for booking {booking_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while processing the change request'
        }), 500

@app.route('/bookings/<booking_id>/auto-rebook', methods=['POST'])
def auto_rebook_booking(booking_id):
    """Automatically rebook a flight with the selected option"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No JSON data provided',
                'message': 'Request body must contain rebooking option details'
            }), 400
        
        # Validate required fields
        required_fields = ['flight_number', 'depart_date', 'departure_time', 'price']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'message': f'The following fields are required: {", ".join(missing_fields)}'
            }), 400
        
        # Get the original booking
        supabase = db.get_client()
        result = supabase.table('bookings').select('*').eq('id', booking_id).execute()
        
        if not result.data or len(result.data) == 0:
            return jsonify({
                'error': 'Booking not found',
                'message': f'No booking found with ID: {booking_id}'
            }), 404
        
        original_booking = result.data[0]
        
        # Check if booking can be changed
        if original_booking['status'] not in ['confirmed', 'pending']:
            return jsonify({
                'error': 'Booking cannot be changed',
                'message': f'Bookings with status "{original_booking["status"]}" cannot be modified'
            }), 400
        
        # Validate the new date
        try:
            datetime.strptime(data['depart_date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({
                'error': 'Invalid date format',
                'message': 'depart_date must be in YYYY-MM-DD format'
            }), 400
        
        # Perform the auto-rebooking
        rebooking_result = rebooking_service.auto_rebook(original_booking, data)
        
        if not rebooking_result['success']:
            return jsonify({
                'error': 'Rebooking failed',
                'message': 'Failed to process the rebooking request'
            }), 500
        
        # Update the original booking status to 'cancelled'
        update_result = supabase.table('bookings').update({
            'status': 'cancelled',
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', booking_id).execute()
        
        # Insert the new booking (in a real system, this would be a transaction)
        new_booking_data = rebooking_result['new_booking']
        # Remove fields that aren't in our database schema
        db_booking_data = {
            'id': new_booking_data['id'],
            'customer_id': new_booking_data['customer_id'],
            'flight_number': new_booking_data['flight_number'],
            'origin': new_booking_data['origin'],
            'destination': new_booking_data['destination'],
            'depart_date': new_booking_data['depart_date'],
            'status': new_booking_data['status']
        }
        
        insert_result = supabase.table('bookings').insert(db_booking_data).execute()
        
        if not insert_result.data:
            logger.error("Failed to create new booking record")
            return jsonify({
                'error': 'Rebooking failed',
                'message': 'Failed to create new booking record'
            }), 500
        
        logger.info(f"Successfully rebooked booking {booking_id} to new booking {new_booking_data['id']}")
        
        return jsonify({
            'success': True,
            'message': 'Flight successfully rebooked',
            'original_booking_id': booking_id,
            'new_booking': rebooking_result['new_booking'],
            'confirmation_code': rebooking_result['confirmation_code'],
            'change_summary': rebooking_result['change_summary']
        }), 200
        
    except Exception as e:
        logger.error(f"Error auto-rebooking booking {booking_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while processing the rebooking'
        }), 500

@app.route('/webhook/flight-event', methods=['POST'])
def flight_event_webhook():
    """Webhook endpoint for receiving flight events"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No JSON data provided',
                'message': 'Request body must contain valid JSON with flight event data'
            }), 400
        
        # Validate required fields
        required_fields = ['flight_number', 'status', 'estimated_arrival']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'message': f'The following fields are required: {", ".join(missing_fields)}'
            }), 400
        
        # Create flight state object for validation
        flight_state = FlightState.from_dict(data)
        validation_errors = flight_state.validate()
        
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': validation_errors
            }), 400
        
        # Add event to processing queue
        success = event_processor.add_flight_event(data)
        
        if not success:
            return jsonify({
                'error': 'Failed to process event',
                'message': 'The flight event could not be added to the processing queue'
            }), 500
        
        logger.info(f"Received flight event: {flight_state.flight_number} - {flight_state.status}")
        
        return jsonify({
            'message': 'Flight event received and queued for processing',
            'flight_number': flight_state.flight_number,
            'status': flight_state.status,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing flight event webhook: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while processing the flight event'
        }), 500

@app.route('/flight-state/<flight_number>', methods=['GET'])
def get_flight_state(flight_number):
    """Get current flight state"""
    try:
        # Get flight state from event processor
        flight_state = event_processor.get_flight_state(flight_number)
        
        if flight_state:
            return jsonify({
                'flight_state': flight_state.to_dict()
            }), 200
        
        # If not in memory, try database
        supabase = db.get_client()
        result = supabase.table('flight_state').select('*').eq('flight_number', flight_number).execute()
        
        if result.data and len(result.data) > 0:
            return jsonify({
                'flight_state': result.data[0]
            }), 200
        else:
            return jsonify({
                'error': 'Flight state not found',
                'message': f'No flight state found for flight {flight_number}'
            }), 404
            
    except Exception as e:
        logger.error(f"Error fetching flight state {flight_number}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while fetching flight state'
        }), 500

@app.route('/alerts', methods=['GET'])
def get_alerts():
    """Get recent alerts"""
    try:
        limit = request.args.get('limit', 10, type=int)
        flight_number = request.args.get('flight_number')
        severity = request.args.get('severity')
        resolved = request.args.get('resolved')
        
        # Get alerts from database
        supabase = db.get_client()
        query = supabase.table('alerts').select('*')
        
        # Apply filters
        if flight_number:
            query = query.eq('flight_number', flight_number)
        if severity:
            query = query.eq('severity', severity)
        if resolved is not None:
            query = query.eq('resolved', resolved.lower() == 'true')
        
        # Apply limit and ordering
        query = query.order('created_at', desc=True).limit(limit)
        
        result = query.execute()
        alerts = result.data or []
        
        return jsonify({
            'alerts': alerts,
            'count': len(alerts),
            'limit': limit
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching alerts: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while fetching alerts'
        }), 500

@app.route('/alerts/<alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Mark an alert as resolved"""
    try:
        supabase = db.get_client()
        
        # Update alert status
        result = supabase.table('alerts').update({
            'resolved': True,
            'resolved_at': datetime.utcnow().isoformat()
        }).eq('id', alert_id).execute()
        
        if result.data and len(result.data) > 0:
            logger.info(f"Resolved alert {alert_id}")
            return jsonify({
                'message': 'Alert resolved successfully',
                'alert_id': alert_id
            }), 200
        else:
            return jsonify({
                'error': 'Alert not found',
                'message': f'No alert found with ID: {alert_id}'
            }), 404
            
    except Exception as e:
        logger.error(f"Error resolving alert {alert_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while resolving the alert'
        }), 500

@app.route('/flights/<flight_id>/status', methods=['GET'])
def get_flight_status_genai(flight_id):
    """
    GenAI agent endpoint for intelligent flight status retrieval
    Integrates multiple data sources and provides confidence-scored responses
    """
    try:
        # Validate flight_id
        if not flight_id or len(flight_id.strip()) == 0:
            return jsonify({
                'error': 'Invalid flight ID',
                'message': 'Flight ID cannot be empty'
            }), 400
        
        logger.info(f"GenAI agent processing flight status request for: {flight_id}")
        
        # Use GenAI agent to retrieve comprehensive flight status
        flight_status = flight_status_agent.get_flight_status(flight_id)
        
        # Check if we got an error response
        if flight_status.get('status') == 'ERROR':
            return jsonify({
                'error': 'Flight status retrieval failed',
                'message': flight_status.get('error', 'Unknown error occurred'),
                'flight_id': flight_id
            }), 404
        
        # Log successful retrieval
        confidence = flight_status.get('confidence_score', 0.0)
        logger.info(f"Retrieved flight status for {flight_id} with confidence {confidence}")
        
        # Return successful response
        return jsonify({
            'success': True,
            'flight_status': flight_status,
            'agent_info': {
                'processing_time': datetime.utcnow().isoformat(),
                'data_sources_used': flight_status.get('data_sources', {}),
                'session_id': flight_status.get('session_id')
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in GenAI flight status endpoint for {flight_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while retrieving flight status',
            'flight_id': flight_id
        }), 500

@app.route('/chatbot-sessions', methods=['GET'])
def get_chatbot_sessions():
    """Get recent chatbot sessions for monitoring and analysis"""
    try:
        limit = request.args.get('limit', 10, type=int)
        flight_id = request.args.get('flight_id')
        min_confidence = request.args.get('min_confidence', type=float)
        
        # Build query
        supabase = db.get_client()
        query = supabase.table('chatbot_sessions').select('*')
        
        # Apply filters
        if flight_id:
            query = query.eq('flight_id', flight_id)
        if min_confidence is not None:
            query = query.gte('confidence_score', min_confidence)
        
        # Apply ordering and limit
        query = query.order('created_at', desc=True).limit(limit)
        
        result = query.execute()
        sessions = result.data or []
        
        return jsonify({
            'sessions': sessions,
            'count': len(sessions),
            'limit': limit
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching chatbot sessions: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while fetching chatbot sessions'
        }), 500

@app.route('/flights', methods=['GET'])
def list_flights():
    """List flights with optional filtering"""
    try:
        # Get query parameters
        origin = request.args.get('origin')
        destination = request.args.get('destination')
        status = request.args.get('status')
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        supabase = db.get_client()
        query = supabase.table('flights').select('*')
        
        # Apply filters
        if origin:
            query = query.eq('origin', origin.upper())
        if destination:
            query = query.eq('destination', destination.upper())
        if status:
            query = query.eq('status', status.upper())
        
        # Apply pagination and ordering
        query = query.range(offset, offset + limit - 1)
        query = query.order('scheduled_departure', desc=False)
        
        result = query.execute()
        flights = result.data or []
        
        return jsonify({
            'flights': flights,
            'count': len(flights),
            'offset': offset,
            'limit': limit
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing flights: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while fetching flights'
        }), 500

@app.route('/flights/<flight_id>', methods=['GET'])
def get_flight_metadata(flight_id):
    """Get flight metadata from the flights table"""
    try:
        supabase = db.get_client()
        
        # Try to find by ID first, then by flight_number
        result = supabase.table('flights').select('*').eq('id', flight_id).execute()
        
        if not result.data:
            # Try by flight_number
            result = supabase.table('flights').select('*').eq('flight_number', flight_id).execute()
        
        if result.data and len(result.data) > 0:
            flight = result.data[0]
            return jsonify({
                'flight': flight
            }), 200
        else:
            return jsonify({
                'error': 'Flight not found',
                'message': f'No flight found with ID or flight number: {flight_id}'
            }), 404
            
    except Exception as e:
        logger.error(f"Error fetching flight metadata {flight_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while fetching flight metadata'
        }), 500

@app.route('/flights/<flight_id>/risk', methods=['GET'])
def get_flight_disruption_risk(flight_id):
    """
    GenAI agent endpoint for predicting flight disruption risk
    Combines weather data, historical patterns, and real-time delays
    """
    try:
        # Validate flight_id
        if not flight_id or len(flight_id.strip()) == 0:
            return jsonify({
                'error': 'Invalid flight ID',
                'message': 'Flight ID cannot be empty'
            }), 400
        
        logger.info(f"Disruption prediction request for flight: {flight_id}")
        
        # Use disruption predictor to analyze risk
        prediction_result = disruption_predictor.predict_disruption(flight_id)
        
        # Check if we got an error response
        if prediction_result.get('error'):
            return jsonify({
                'error': 'Disruption prediction failed',
                'message': prediction_result.get('error', 'Unknown error occurred'),
                'flight_id': flight_id
            }), 404
        
        # Store prediction result in database
        prediction_id = store_disruption_prediction(prediction_result)
        
        # Add prediction ID to response
        prediction_result['prediction_id'] = prediction_id
        
        # Log successful prediction
        risk_score = prediction_result.get('disruption_risk', 0.0)
        risk_level = prediction_result.get('risk_level', 'UNKNOWN')
        logger.info(f"Disruption prediction for {flight_id}: risk={risk_score}, level={risk_level}")
        
        # Return successful response
        return jsonify({
            'success': True,
            'disruption_prediction': prediction_result,
            'prediction_info': {
                'processing_time': datetime.utcnow().isoformat(),
                'prediction_id': prediction_id,
                'model_version': prediction_result.get('model_version', '1.0')
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in disruption prediction endpoint for {flight_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while predicting disruption risk',
            'flight_id': flight_id
        }), 500

def store_disruption_prediction(prediction_result: dict) -> str:
    """Store disruption prediction in database"""
    try:
        import uuid
        prediction_id = str(uuid.uuid4())
        
        supabase = db.get_client()
        
        prediction_data = {
            'id': prediction_id,
            'flight_id': prediction_result['flight_id'],
            'flight_number': prediction_result['flight_number'],
            'origin': prediction_result['origin'],
            'destination': prediction_result['destination'],
            'disruption_risk': prediction_result['disruption_risk'],
            'risk_level': prediction_result['risk_level'],
            'risk_factors': prediction_result.get('risk_factors', {}),
            'contributing_factors': prediction_result.get('contributing_factors', []),
            'recommendations': prediction_result.get('recommendations', []),
            'confidence': prediction_result.get('confidence', 0.0),
            'model_version': prediction_result.get('model_version', '1.0')
        }
        
        result = supabase.table('disruption_predictions').insert(prediction_data).execute()
        
        if result.data:
            logger.info(f"Stored disruption prediction {prediction_id}")
            return prediction_id
        else:
            logger.error(f"Failed to store disruption prediction for {prediction_result['flight_id']}")
            return prediction_id  # Return ID anyway for tracking
            
    except Exception as e:
        logger.error(f"Error storing disruption prediction: {str(e)}")
        return str(uuid.uuid4())  # Return a UUID anyway

@app.route('/chat/voice', methods=['POST'])
def voice_chat():
    """
    Voice-enabled chatbot endpoint
    Handles speech-to-text, conversational AI, and text-to-speech
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No JSON data provided',
                'message': 'Request body must contain audio_data or text_input'
            }), 400
        
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({
                'error': 'Missing user_id',
                'message': 'user_id is required for conversation tracking'
            }), 400
        
        audio_data = data.get('audio_data')  # Base64 encoded audio
        text_input = data.get('text_input')   # Direct text input
        
        if not audio_data and not text_input:
            return jsonify({
                'error': 'No input provided',
                'message': 'Either audio_data or text_input must be provided'
            }), 400
        
        logger.info(f"Voice chat request from user {user_id}")
        
        # Process through voice chatbot
        chat_response = voice_chatbot.process_voice_request(user_id, audio_data, text_input)
        
        if not chat_response.get('success'):
            return jsonify(chat_response), 400
        
        logger.info(f"Voice chat processed successfully for user {user_id}")
        
        return jsonify(chat_response), 200
        
    except Exception as e:
        logger.error(f"Error in voice chat endpoint: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while processing your voice request'
        }), 500

@app.route('/bookings/<booking_id>/change-date', methods=['POST'])
def change_booking_date_nlp(booking_id):
    """
    Natural language booking date change endpoint
    Interprets requests like "change my flight to Monday"
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data or 'request' not in data:
            return jsonify({
                'error': 'No request provided',
                'message': 'Request body must contain "request" field with natural language text'
            }), 400
        
        request_text = data['request']
        
        # Get the original booking
        supabase = db.get_client()
        result = supabase.table('bookings').select('*').eq('id', booking_id).execute()
        
        if not result.data or len(result.data) == 0:
            return jsonify({
                'error': 'Booking not found',
                'message': f'No booking found with ID: {booking_id}'
            }), 404
        
        booking_data = result.data[0]
        
        # Use NLP agent to interpret the request
        interpretation = nlp_agent.interpret_booking_change(request_text, booking_data)
        
        if interpretation['intent'] != 'change_booking':
            return jsonify({
                'error': 'Request not understood',
                'message': 'Could not interpret the booking change request',
                'interpretation': interpretation
            }), 400
        
        if interpretation['confidence'] < 0.5:
            return jsonify({
                'error': 'Low confidence interpretation',
                'message': 'Please provide a clearer request for booking changes',
                'interpretation': interpretation,
                'suggestions': [
                    'Try: "Change my flight to Monday"',
                    'Try: "Reschedule to February 20th"',
                    'Try: "Move to next Tuesday morning"'
                ]
            }), 400
        
        # Extract new date from interpretation
        new_date = interpretation['extracted_data'].get('new_date')
        if not new_date:
            return jsonify({
                'error': 'No date found',
                'message': 'Could not extract a valid date from your request',
                'interpretation': interpretation
            }), 400
        
        # Find alternative flights
        alternatives = nlp_agent.find_alternative_flights(booking_data, interpretation['extracted_data'])
        
        if not alternatives:
            return jsonify({
                'error': 'No alternatives found',
                'message': f'No flights available for your requested change to {new_date}',
                'interpretation': interpretation
            }), 404
        
        # Store NLP session
        session_data = {
            'booking_id': booking_id,
            'intent': interpretation['intent'],
            'confidence': interpretation['confidence'],
            'original_request': request_text,
            'response_data': {
                'alternatives_found': len(alternatives),
                'new_date': new_date,
                'interpretation': interpretation
            }
        }
        session_id = nlp_agent.store_nlp_session(session_data)
        
        logger.info(f"NLP booking change request processed for {booking_id}: {len(alternatives)} alternatives found")
        
        return jsonify({
            'success': True,
            'message': 'Booking change request understood',
            'interpretation': interpretation,
            'original_booking': {
                'id': booking_data['id'],
                'flight_number': booking_data['flight_number'],
                'depart_date': booking_data['depart_date'],
                'origin': booking_data['origin'],
                'destination': booking_data['destination']
            },
            'alternatives': alternatives[:3],  # Return top 3 alternatives
            'session_id': session_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing NLP booking change for {booking_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while processing your request'
        }), 500

@app.route('/flights/search', methods=['POST'])
def search_flights():
    """
    Search for flights based on user criteria
    Returns multiple flight options with risk scores
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No JSON data provided',
                'message': 'Request body must contain search criteria'
            }), 400
        
        # Extract search parameters
        origin = data.get('origin', '').strip().upper()
        destination = data.get('destination', '').strip().upper()
        date = data.get('date', '')
        budget = data.get('budget', 0)
        passenger_count = data.get('passenger_count', 1)
        
        # Validate required fields
        if not origin or not destination or not date:
            return jsonify({
                'error': 'Missing required fields',
                'message': 'origin, destination, and date are required'
            }), 400
        
        if budget <= 0:
            return jsonify({
                'error': 'Invalid budget',
                'message': 'Budget must be greater than 0'
            }), 400
        
        logger.info(f"Flight search request: {origin} to {destination} on {date}, budget: {budget}")
        
        # Search for flights
        flights = flight_search_service.search_flights(origin, destination, date, budget, passenger_count)
        
        if not flights:
            return jsonify({
                'error': 'No flights found',
                'message': f'No flights available for {origin} to {destination} on {date} within budget ₹{budget}',
                'search_criteria': {
                    'origin': origin,
                    'destination': destination,
                    'date': date,
                    'budget': budget,
                    'passenger_count': passenger_count
                }
            }), 404
        
        logger.info(f"Found {len(flights)} flights for {origin} to {destination}")
        
        calendar_suggestions = get_calendar_suggestions_for_search(date)
        try:
            recommended = calendar_suggestions.get('recommended_dates') or []
            date_in_recommended = date in recommended
        except Exception:
            date_in_recommended = False

        return jsonify({
            'success': True,
            'flights': flights,
            'count': len(flights),
            'search_criteria': {
                'origin': origin,
                'destination': destination,
                'date': date,
                'budget': budget,
                'passenger_count': passenger_count
            },
            'calendar_suggestions': calendar_suggestions,
            'date_alignment': {
                'is_recommended_day': date_in_recommended,
                'reason': 'Date aligns with upcoming calendar event windows' if date_in_recommended else 'Date not in recommended travel windows derived from Google Calendar'
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching flights: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while searching for flights'
        }), 500

@app.route('/flights/<flight_id>/risk-analysis', methods=['GET'])
def get_flight_risk_analysis(flight_id):
    """
    Get detailed risk analysis for a specific flight
    Returns comprehensive risk breakdown with charts data
    """
    try:
        # Use advanced risk predictor with real-time data
        from aviation_api_service import aviation_api_service
        
        # Get flight details from aviation API
        flight_status = aviation_api_service.get_flight_status(flight_id)
        
        if "error" in flight_status:
            # Fall back to demo data if API fails
            risk_analysis = {
                'flight_id': flight_id,
                'overall_risk_score': random.uniform(65, 95),
                'risk_level': random.choice(['Low Risk', 'Medium Risk', 'High Risk']),
                'risk_factors': {
                    'weather_risk': random.uniform(10, 40),
                    'operational_risk': random.uniform(15, 35),
                    'airport_risk': random.uniform(10, 30),
                    'seasonal_risk': random.uniform(5, 25),
                    'regulatory_risk': random.uniform(5, 15),
                    'passenger_risk': random.uniform(10, 30),
                    'technology_risk': random.uniform(5, 20),
                    'pricing_risk': random.uniform(10, 25)
                },
                'recommendations': [
                    "Check weather forecast before travel",
                    "Arrive at airport 2 hours early",
                    "Consider travel insurance"
                ],
                'historical_performance': {
                    'on_time_percentage': random.uniform(75, 95),
                    'average_delay_minutes': random.randint(5, 30),
                    'cancellation_rate': random.uniform(1, 5)
                },
                'using_real_time_data': False
            }
        else:
            # Create flight object for risk prediction
            flight = {
                'flight_number': flight_id,
                'airline': flight_status.get('airline', 'Unknown'),
                'origin': {'code': flight_status.get('departure', {}).get('iataCode', 'DEL')},
                'destination': {'code': flight_status.get('arrival', {}).get('iataCode', 'BOM')},
                'departure_datetime': flight_status.get('departure', {}).get('scheduledTime', datetime.now().isoformat()),
                'price': random.randint(5000, 15000)  # Placeholder price
            }
            
            # Get advanced risk analysis
            analysis = advanced_risk_predictor.predict_comprehensive_risk([flight])
            
            # Create comprehensive risk analysis response
            if analysis.get('success') and analysis.get('flight_analyses'):
                flight_analysis = analysis['flight_analyses'][0]  # Get first flight analysis
                risk_analysis = {
                    'flight_id': flight_id,
                    'overall_risk_score': flight_analysis.get('risk_score', 75),
                    'risk_level': flight_analysis.get('risk_level', 'Medium Risk'),
                    'risk_factors': flight_analysis.get('risk_factors', {}),
                    'recommendations': flight_analysis.get('recommendations', [
                        "Check weather forecast before travel",
                        "Monitor flight status before departure"
                    ]),
                    'historical_performance': {
                        'on_time_percentage': random.uniform(75, 95),
                        'average_delay_minutes': random.randint(5, 30),
                        'cancellation_rate': random.uniform(1, 5)
                    },
                    'using_real_time_data': True
                }
            else:
                # Fallback if analysis fails
                risk_analysis = {
                    'flight_id': flight_id,
                    'overall_risk_score': random.uniform(65, 95),
                    'risk_level': random.choice(['Low Risk', 'Medium Risk', 'High Risk']),
                    'risk_factors': {
                        'weather_risk': random.uniform(10, 40),
                        'operational_risk': random.uniform(15, 35),
                        'airport_risk': random.uniform(10, 30),
                        'seasonal_risk': random.uniform(5, 25),
                        'regulatory_risk': random.uniform(5, 15),
                        'passenger_risk': random.uniform(10, 30),
                        'technology_risk': random.uniform(5, 20),
                        'pricing_risk': random.uniform(10, 25)
                    },
                    'recommendations': [
                        "Check weather forecast before travel",
                        "Monitor flight status before departure"
                    ],
                    'historical_performance': {
                        'on_time_percentage': random.uniform(75, 95),
                        'average_delay_minutes': random.randint(5, 30),
                        'cancellation_rate': random.uniform(1, 5)
                    },
                    'using_real_time_data': False
                }
        
        
        # Adjust risk level based on score
        score = risk_analysis['overall_risk_score']
        if score >= 80:
            risk_analysis['risk_level'] = 'Low Risk'
            risk_analysis['risk_color'] = 'green'
        elif score >= 60:
            risk_analysis['risk_level'] = 'Medium Risk'
            risk_analysis['risk_color'] = 'yellow'
        else:
            risk_analysis['risk_level'] = 'High Risk'
            risk_analysis['risk_color'] = 'red'
        
        return jsonify({
            'success': True,
            'risk_analysis': risk_analysis,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting risk analysis for flight {flight_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while analyzing flight risk'
        }), 500

@app.route('/pnr/<pnr_number>', methods=['GET'])
def get_pnr_details(pnr_number):
    """
    Get flight details and status by PNR number
    Returns real-time flight data from aviation API
    """
    try:
        if not pnr_number or len(pnr_number) < 6:
            return jsonify({
                'error': 'Invalid PNR',
                'message': 'PNR number must be at least 6 characters'
            }), 400
        
        # Use aviation API to get real PNR details
        from aviation_api_service import aviation_api_service
        
        # Get PNR details from aviation API
        pnr_data = aviation_api_service.get_flight_by_pnr(pnr_number)
        
        if "error" in pnr_data:
            # Fall back to mock data if API fails
            logger.warning(f"Failed to get real-time PNR data: {pnr_data.get('error')}. Using mock data.")
            
            # Generate mock PNR data
            mock_pnr_data = {
                'pnr': pnr_number.upper(),
                'status': random.choice(['Confirmed', 'Waitlisted', 'Cancelled']),
                'booking_date': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
                'passenger_name': 'John Doe',
                'contact_email': 'john.doe@example.com',
                'contact_phone': '+91-9876543210',
                'flight_details': {
                    'flight_number': f"QP{random.randint(1000, 9999)}",
                    'airline': 'Akasa Air',
                    'origin': {
                        'code': 'DEL',
                        'name': 'Indira Gandhi International Airport',
                        'city': 'Delhi',
                        'terminal': 'T3'
                    },
                    'destination': {
                        'code': 'BOM',
                        'name': 'Chhatrapati Shivaji Maharaj International Airport',
                        'city': 'Mumbai',
                        'terminal': 'T2'
                    },
                    'departure_date': (datetime.now() + timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
                    'departure_time': f"{random.randint(6, 22):02d}:{random.choice(['00', '15', '30', '45'])}",
                    'arrival_time': f"{random.randint(8, 23):02d}:{random.choice(['00', '15', '30', '45'])}",
                    'duration': '2h 15m',
                    'aircraft_type': 'A320',
                    'seat_number': f"{random.randint(1, 30)}{random.choice(['A', 'B', 'C', 'D', 'E', 'F'])}",
                    'class': 'Economy',
                    'meal_preference': random.choice(['Vegetarian', 'Non-Vegetarian', 'Vegan']),
                    'baggage_allowance': '15kg'
                },
                'using_real_time_data': False,
                'current_status': {
                'status': random.choice(['On Time', 'Delayed', 'Boarding', 'Departed', 'Arrived']),
                'gate': f"G{random.randint(1, 25)}",
                'terminal': 'T3',
                'delay_minutes': random.randint(0, 60) if random.choice([True, False]) else 0,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            }
            
            return jsonify({
                'success': True,
                'pnr_details': mock_pnr_data,
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        else:
            # Format the API response for frontend
            flight_details = pnr_data.get('flight_details', {})
            
            # Create a structured response with real-time data
            real_time_pnr = {
                'pnr': pnr_number.upper(),
                'status': flight_details.get('status', 'Confirmed'),
                'booking_date': pnr_data.get('timestamp', datetime.now().strftime('%Y-%m-%d')),
                'passenger_name': pnr_data.get('passenger_name', 'Passenger'),
                'flight_details': {
                    'flight_number': flight_details.get('flight_number', ''),
                    'airline': flight_details.get('airline', 'Unknown'),
                    'origin': {
                        'code': flight_details.get('origin', ''),
                        'name': f"{flight_details.get('origin', '')} Airport",
                        'city': flight_details.get('origin', ''),
                        'terminal': 'T1'
                    },
                    'destination': {
                        'code': flight_details.get('destination', ''),
                        'name': f"{flight_details.get('destination', '')} Airport",
                        'city': flight_details.get('destination', ''),
                        'terminal': 'T1'
                    },
                    'departure_date': flight_details.get('departure_date', ''),
                    'departure_time': flight_details.get('departure_time', ''),
                    'arrival_time': flight_details.get('arrival_time', ''),
                    'duration': '2h 15m',  # Placeholder
                    'aircraft_type': 'A320',  # Placeholder
                    'seat_number': pnr_data.get('seat', 'Not assigned'),
                    'class': pnr_data.get('class', 'Economy'),
                    'baggage_allowance': pnr_data.get('baggage_allowance', '15kg')
                },
                'current_status': {
                    'status': flight_details.get('status', 'On Time'),
                    'gate': 'TBD',
                    'terminal': 'T1',
                    'delay_minutes': 0,
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                'using_real_time_data': True
            }
            
            logger.info(f"Retrieved real-time PNR details for {pnr_number}")
            
            return jsonify({
                'success': True,
                'pnr_details': real_time_pnr,
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving PNR details for {pnr_number}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while retrieving PNR details'
        }), 500

@app.route('/flights/comprehensive-analysis', methods=['POST'])
def get_comprehensive_flight_analysis():
    """
    Get comprehensive analysis of all flights for a route
    Returns detailed comparison, statistics, and final verdict
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data or 'flights' not in data:
            return jsonify({
                'error': 'No flight data provided',
                'message': 'Request body must contain flights array'
            }), 400
        
        flights = data['flights']
        
        if not flights or len(flights) == 0:
            return jsonify({
                'error': 'No flights to analyze',
                'message': 'At least one flight is required for analysis'
            }), 400
        
        logger.info(f"Comprehensive analysis request for {len(flights)} flights")
        
        # Use advanced risk predictor for comprehensive analysis
        analysis_result = advanced_risk_predictor.predict_comprehensive_risk(flights)
        
        if analysis_result.get('error'):
            return jsonify({
                'error': 'Analysis failed',
                'message': analysis_result['error']
            }), 500
        
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