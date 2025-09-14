"""Calendar Service for Akasa Airlines
Combines calendar analysis and Google Calendar API integration
"""

import os
import json
import logging
import re
from flask import Flask, request, redirect, session, jsonify, render_template_string
from flask_cors import CORS
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from google_oauth_service import oauth_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CalendarEvent:
    """Represents a calendar event with flight-relevant information"""
    id: str
    title: str
    start_date: datetime
    end_date: datetime
    location: str
    description: str
    is_travel_related: bool = False
    suggested_departure: Optional[datetime] = None
    suggested_return: Optional[datetime] = None
    destination_city: Optional[str] = None
    origin_city: Optional[str] = None

# Calendar Analysis Functions

def analyze_calendar_events(events: List[Dict]) -> List[CalendarEvent]:
    """Analyze calendar events to identify travel-related events"""
    calendar_events = []
    
    for event in events:
        # Extract basic event information
        event_id = event.get('id', '')
        title = event.get('summary', 'Untitled Event')
        description = event.get('description', '')
        location = event.get('location', '')
        
        # Parse start and end dates
        start_date = parse_event_datetime(event.get('start', {}))
        end_date = parse_event_datetime(event.get('end', {}))
        
        if not start_date or not end_date:
            continue
        
        # Create calendar event
        calendar_event = CalendarEvent(
            id=event_id,
            title=title,
            start_date=start_date,
            end_date=end_date,
            location=location,
            description=description
        )
        
        # Check if event is travel-related
        calendar_event.is_travel_related = is_travel_related_event(calendar_event)
        
        # Extract travel information if relevant
        if calendar_event.is_travel_related:
            extract_travel_information(calendar_event)
        
        calendar_events.append(calendar_event)
    
    return calendar_events

def parse_event_datetime(date_info: Dict) -> Optional[datetime]:
    """Parse event datetime from Google Calendar API response"""
    if not date_info:
        return None
    
    # Handle all-day events
    if 'date' in date_info:
        date_str = date_info['date']
        return datetime.fromisoformat(date_str)
    
    # Handle timed events
    if 'dateTime' in date_info:
        datetime_str = date_info['dateTime']
        return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
    
    return None

def is_travel_related_event(event: CalendarEvent) -> bool:
    """Determine if an event is travel-related"""
    # Check title for travel keywords
    travel_keywords = ['flight', 'travel', 'trip', 'journey', 'vacation', 'holiday', 
                      'visit', 'tour', 'airport', 'departure', 'arrival', 'layover']
    
    title_lower = event.title.lower()
    desc_lower = event.description.lower()
    location_lower = event.location.lower()
    
    # Check if any travel keywords are in the title, description, or location
    for keyword in travel_keywords:
        if (keyword in title_lower or 
            keyword in desc_lower or 
            keyword in location_lower):
            return True
    
    # Check for airport codes in location
    airport_code_pattern = r'\b[A-Z]{3}\b'
    if re.search(airport_code_pattern, event.location):
        return True
    
    # Check for multi-day events (potential trips)
    duration = event.end_date - event.start_date
    if duration.days >= 2:
        return True
    
    return False

def extract_travel_information(event: CalendarEvent) -> None:
    """Extract travel information from event details"""
    # Extract airport codes
    airport_code_pattern = r'\b[A-Z]{3}\b'
    airport_codes = re.findall(airport_code_pattern, event.location + ' ' + event.description)
    
    if len(airport_codes) >= 2:
        event.origin_city = airport_codes[0]
        event.destination_city = airport_codes[1]
    
    # Extract suggested departure and return dates
    # For simplicity, use event start and end dates
    event.suggested_departure = event.start_date
    event.suggested_return = event.end_date

def get_travel_windows(events: List[CalendarEvent]) -> List[Dict]:
    """Generate travel windows based on calendar events"""
    travel_windows = []
    
    for event in events:
        if event.is_travel_related and event.suggested_departure and event.suggested_return:
            window = {
                'event_id': event.id,
                'event_title': event.title,
                'start_date': event.suggested_departure.isoformat(),
                'end_date': event.suggested_return.isoformat(),
                'origin': event.origin_city or 'Unknown',
                'destination': event.destination_city or 'Unknown',
                'confidence': 'high' if event.origin_city and event.destination_city else 'medium'
            }
            travel_windows.append(window)
    
    return travel_windows

def get_recommended_dates(events: List[CalendarEvent], days_before: int = 1) -> List[str]:
    """Get recommended travel dates based on calendar events"""
    recommended_dates = []
    
    for event in events:
        if event.is_travel_related and event.suggested_departure:
            # Recommend days before departure
            for i in range(1, days_before + 1):
                date = event.suggested_departure - timedelta(days=i)
                recommended_dates.append(date.strftime('%Y-%m-%d'))
            
            # Recommend departure day
            recommended_dates.append(event.suggested_departure.strftime('%Y-%m-%d'))
    
    return list(set(recommended_dates))  # Remove duplicates

# Create Flask app for calendar integration
app = Flask(__name__)
CORS(app)

# Set secret key for sessions
app.secret_key = os.urandom(24)

# OAuth 2.0 configuration
SCOPES = [
    'openid',
    'email', 
    'profile',
    'https://www.googleapis.com/auth/calendar.readonly'
]

CREDENTIALS_FILE = 'credentials.json'

def load_credentials():
    """Load OAuth credentials from file"""
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading credentials: {str(e)}")
        return None

def create_flow():
    """Create OAuth flow"""
    credentials_data = load_credentials()
    if not credentials_data:
        return None
    
    flow = Flow.from_client_config(
        client_config=credentials_data,
        scopes=SCOPES,
            redirect_uri="http://localhost:8081/auth/callback"
    )
    return flow

@app.route('/')
def home():
    """Home page"""
    if 'credentials' in session:
        return render_template_string(DASHBOARD_TEMPLATE, user=session.get('user_info', {}))
    else:
        return render_template_string(HOME_TEMPLATE)

@app.route('/login')
def login():
    """Login with Google"""
    flow = create_flow()
    if not flow:
        return jsonify({
            'error': 'OAuth configuration error',
            'message': 'Could not load OAuth credentials'
        }), 500
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    session['state'] = state
    return redirect(authorization_url)

@app.route('/callback')
def callback():
    """OAuth callback"""
    try:
        flow = create_flow()
        if not flow:
            return jsonify({
                'error': 'OAuth configuration error',
                'message': 'Could not load OAuth credentials'
            }), 500
        
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials
        
        # Store credentials in session
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        # Get user info
        user_info = get_user_info(credentials)
        session['user_info'] = user_info
        
        return redirect('/')
    except Exception as e:
        logger.error(f"Error in OAuth callback: {str(e)}")
        return jsonify({
            'error': 'OAuth callback error',
            'message': str(e)
        }), 500

def get_user_info(credentials):
    """Get user info from Google API"""
    try:
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        return user_info
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        return {}

@app.route('/events')
def events():
    """Get calendar events"""
    if 'credentials' not in session:
        return jsonify({
            'success': False,
            'message': 'Not authenticated'
        }), 401
    
    try:
        # Load credentials from session
        credentials_dict = session['credentials']
        credentials = Credentials(
            token=credentials_dict['token'],
            refresh_token=credentials_dict['refresh_token'],
            token_uri=credentials_dict['token_uri'],
            client_id=credentials_dict['client_id'],
            client_secret=credentials_dict['client_secret'],
            scopes=credentials_dict['scopes']
        )
        
        # Build calendar service
        service = build('calendar', 'v3', credentials=credentials)
        
        # Get calendar events
        now = datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Format events for response
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            formatted_events.append({
                'id': event['id'],
                'summary': event.get('summary', 'Untitled Event'),
                'start': start,
                'end': end,
                'location': event.get('location', ''),
                'description': event.get('description', '')
            })
        
        return jsonify({
            'success': True,
            'events': formatted_events
        })
    except Exception as e:
        logger.error(f"Error getting events: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect('/')

@app.route('/user')
def get_user():
    """Get user info"""
    if 'user_info' not in session:
        return jsonify({
            'success': False,
            'message': 'Not authenticated'
        }), 401
    
    return jsonify({
        'success': True,
        'user': session['user_info']
    })

@app.route('/analyze')
def analyze_events():
    """Analyze calendar events"""
    if 'credentials' not in session:
        return jsonify({
            'success': False,
            'message': 'Not authenticated'
        }), 401
    
    try:
        # Load credentials from session
        credentials_dict = session['credentials']
        credentials = Credentials(
            token=credentials_dict['token'],
            refresh_token=credentials_dict['refresh_token'],
            token_uri=credentials_dict['token_uri'],
            client_id=credentials_dict['client_id'],
            client_secret=credentials_dict['client_secret'],
            scopes=credentials_dict['scopes']
        )
        
        # Build calendar service
        service = build('calendar', 'v3', credentials=credentials)
        
        # Get calendar events for the next 3 months
        now = datetime.utcnow()
        three_months_later = now + timedelta(days=90)
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now.isoformat() + 'Z',
            timeMax=three_months_later.isoformat() + 'Z',
            maxResults=100,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Analyze events
        calendar_events = analyze_calendar_events(events)
        
        # Generate travel windows
        travel_windows = get_travel_windows(calendar_events)
        
        # Get recommended dates
        recommended_dates = get_recommended_dates(calendar_events)
        
        return jsonify({
            'success': True,
            'travel_windows': travel_windows,
            'recommended_dates': recommended_dates,
            'travel_events_count': sum(1 for e in calendar_events if e.is_travel_related)
        })
    except Exception as e:
        logger.error(f"Error analyzing events: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# HTML Templates
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Calendar API Integration</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .btn-google {
            background: #4285f4;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .btn-google:hover {
            background: #3367d6;
            box-shadow: 0 4px 12px rgba(66, 133, 244, 0.3);
        }
    </style>
</head>
<body class="text-white">
    <div class="min-h-screen flex items-center justify-center">
        <div class="max-w-md w-full bg-white bg-opacity-10 backdrop-blur-lg p-8 rounded-lg shadow-lg">
            <div class="text-center mb-8">
                <svg class="h-16 w-16 text-white mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3a2 2 0 012-2h4a2 2 0 012 2v4m-6 4v10a2 2 0 002 2h4a2 2 0 002-2V11m-6 0h8m-8 0H6a2 2 0 00-2 2v6a2 2 0 002 2h2m8-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2"></path>
                </svg>
                <h1 class="text-3xl font-bold mb-2">Google Calendar API</h1>
                <p class="text-gray-200">Flask Integration with OAuth 2.0</p>
            </div>

            <div class="space-y-4">
                <a href="/login" class="btn-google w-full justify-center">
                    <svg class="h-5 w-5" viewBox="0 0 24 24">
                        <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                        <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                    Sign in with Google
                </a>
                
                <div class="text-center">
                    <p class="text-sm text-gray-200">
                        Access your Google Calendar events securely
                    </p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Calendar Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .btn-primary {
            background: #4285f4;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
        }
        .btn-primary:hover {
            background: #3367d6;
            box-shadow: 0 4px 12px rgba(66, 133, 244, 0.3);
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .btn-secondary:hover {
            background: #5a6268;
        }
    </style>
</head>
<body class="text-white">
    <div class="min-h-screen">
        <!-- Header -->
        <header class="bg-white bg-opacity-10 backdrop-blur-lg border-b border-white border-opacity-20">
            <div class="container mx-auto px-6 py-4">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-3">
                        <svg class="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3a2 2 0 012-2h4a2 2 0 012 2v4m-6 4v10a2 2 0 002 2h4a2 2 0 002-2V11m-6 0h8m-8 0H6a2 2 0 00-2 2v6a2 2 0 002 2h2m8-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2"></path>
                        </svg>
                        <h1 class="text-2xl font-bold">Google Calendar API</h1>
                    </div>
                    <div class="flex items-center space-x-4">
                        <div class="flex items-center space-x-3">
                            {% if user.picture %}
                            <img src="{{ user.picture }}" alt="Profile" class="w-8 h-8 rounded-full">
                            {% endif %}
                            <span class="text-sm">{{ user.name }}</span>
                        </div>
                        <a href="/logout" class="btn-secondary">Logout</a>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="container mx-auto px-6 py-12">
            <div class="max-w-4xl mx-auto text-center">
                <h2 class="text-4xl font-bold mb-6">Welcome, {{ user.name }}!</h2>
                <p class="text-xl text-gray-200 mb-8">
                    You're successfully authenticated with {{ user.email }}
                </p>
                
                <div class="bg-white bg-opacity-10 backdrop-blur-lg rounded-lg p-8 mb-8">
                    <h3 class="text-2xl font-bold mb-4">Access Your Calendar</h3>
                    <p class="text-gray-200 mb-6">
                        View your upcoming Google Calendar events with secure OAuth 2.0 authentication.
                    </p>
                    
                    <div class="flex flex-col sm:flex-row gap-4 justify-center">
                        <button onclick="fetchEvents()" class="btn-primary text-lg py-3 px-6">
                            📅 Get Calendar Events
                        </button>
                        <button onclick="analyzeEvents()" class="btn-primary text-lg py-3 px-6">
                            🔍 Analyze Travel Events
                        </button>
                    </div>
                </div>
                
                <!-- Events Display -->
                <div id="events-container" class="hidden bg-white bg-opacity-10 backdrop-blur-lg rounded-lg p-8 mb-8">
                    <h3 class="text-2xl font-bold mb-4">Your Upcoming Events</h3>
                    <div id="events-list"></div>
                </div>
                
                <!-- Analysis Display -->
                <div id="analysis-container" class="hidden bg-white bg-opacity-10 backdrop-blur-lg rounded-lg p-8">
                    <h3 class="text-2xl font-bold mb-4">Travel Analysis</h3>
                    <div id="analysis-content"></div>
                </div>
            </div>
        </main>
    </div>

    <script>
        async function fetchEvents() {
            try {
                const response = await fetch('/events');
                const data = await response.json();
                
                const container = document.getElementById('events-container');
                const eventsList = document.getElementById('events-list');
                
                if (data.success) {
                    if (data.events.length === 0) {
                        eventsList.innerHTML = '<p class="text-gray-200">No upcoming events found.</p>';
                    } else {
                        eventsList.innerHTML = data.events.map(event => `
                            <div class="bg-white bg-opacity-20 rounded-lg p-4 mb-4 text-left">
                                <h4 class="font-bold text-lg">${event.summary}</h4>
                                <p class="text-gray-200 text-sm">📅 ${new Date(event.start).toLocaleString()}</p>
                                ${event.location ? `<p class="text-gray-200 text-sm">📍 ${event.location}</p>` : ''}
                                ${event.description ? `<p class="text-gray-200 text-sm mt-2">${event.description}</p>` : ''}
                            </div>
                        `).join('');
                    }
                    container.classList.remove('hidden');
                    document.getElementById('analysis-container').classList.add('hidden');
                } else {
                    alert('Error fetching events: ' + data.message);
                }
            } catch (error) {
                alert('Error fetching events: ' + error.message);
            }
        }
        
        async function analyzeEvents() {
            try {
                const response = await fetch('/analyze');
                const data = await response.json();
                
                const container = document.getElementById('analysis-container');
                const content = document.getElementById('analysis-content');
                
                if (data.success) {
                    let html = `<p class="mb-4">Found ${data.travel_events_count} travel-related events in your calendar.</p>`;
                    
                    if (data.travel_windows.length > 0) {
                        html += `
                            <div class="mb-6">
                                <h4 class="font-bold text-lg mb-2">Travel Windows</h4>
                                <div class="space-y-4">
                        `;
                        
                        data.travel_windows.forEach(window => {
                            html += `
                                <div class="bg-white bg-opacity-20 rounded-lg p-4 text-left">
                                    <h5 class="font-bold">${window.event_title}</h5>
                                    <p class="text-sm">📅 ${new Date(window.start_date).toLocaleDateString()} - ${new Date(window.end_date).toLocaleDateString()}</p>
                                    <p class="text-sm">✈️ ${window.origin} → ${window.destination}</p>
                                    <p class="text-sm">🎯 Confidence: ${window.confidence}</p>
                                </div>
                            `;
                        });
                        
                        html += `
                                </div>
                            </div>
                        `;
                    }
                    
                    if (data.recommended_dates.length > 0) {
                        html += `
                            <div>
                                <h4 class="font-bold text-lg mb-2">Recommended Travel Dates</h4>
                                <div class="flex flex-wrap gap-2">
                        `;
                        
                        data.recommended_dates.forEach(date => {
                            html += `
                                <span class="bg-purple-500 bg-opacity-30 border border-purple-500 border-opacity-50 rounded-full px-3 py-1 text-sm">
                                    ${date}
                                </span>
                            `;
                        });
                        
                        html += `
                                </div>
                            </div>
                        `;
                    }
                    
                    content.innerHTML = html;
                    container.classList.remove('hidden');
                    document.getElementById('events-container').classList.add('hidden');
                } else {
                    alert('Error analyzing events: ' + data.message);
                }
            } catch (error) {
                alert('Error analyzing events: ' + error.message);
            }
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    try:
        print("Starting Calendar Service...")
        app.run(debug=True, host='0.0.0.0', port=5001)
    except Exception as e:
        logger.error(f"Error starting Calendar Service: {str(e)}")