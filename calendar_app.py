"""
Google Calendar API Flask App
Implements OAuth 2.0 flow and Calendar API integration
Runs on localhost:5000 as required
"""

import os
import json
from flask import Flask, request, redirect, session, jsonify, render_template_string
from flask_cors import CORS
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
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
    """Load Google OAuth credentials from credentials.json"""
    try:
        if not os.path.exists(CREDENTIALS_FILE):
            raise FileNotFoundError(f"Credentials file {CREDENTIALS_FILE} not found")
        
        with open(CREDENTIALS_FILE, 'r') as f:
            credentials_data = json.load(f)
        
        logger.info("Google OAuth credentials loaded successfully")
        return credentials_data
        
    except Exception as e:
        logger.error(f"Error loading OAuth credentials: {str(e)}")
        raise

def create_flow():
    """Create OAuth flow for authentication"""
    try:
        credentials_data = load_credentials()
        
        flow = Flow.from_client_config(
            credentials_data,
            scopes=SCOPES
        )
        
        # Set redirect URI for localhost:5000
        flow.redirect_uri = 'http://localhost:5000/callback'
        
        return flow
        
    except Exception as e:
        logger.error(f"Error creating OAuth flow: {str(e)}")
        raise

@app.route('/')
def home():
    """Home page"""
    if 'credentials' in session:
        user = session.get('user', {})
        return render_template_string(DASHBOARD_TEMPLATE, user=user)
    else:
        return render_template_string(HOME_TEMPLATE)

@app.route('/login')
def login():
    """Initiate Google OAuth login - redirect user to Google login"""
    try:
        flow = create_flow()
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        # Store state in session for security
        session['oauth_state'] = state
        
        logger.info("Redirecting to Google OAuth for Calendar access")
        return redirect(authorization_url)
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'error': 'Login failed',
            'message': str(e)
        }), 500

@app.route('/callback')
def callback():
    """Handle Google OAuth callback and store credentials in session"""
    try:
        # Verify state parameter for security
        state = request.args.get('state')
        if state != session.get('oauth_state'):
            return jsonify({
                'error': 'Invalid state parameter',
                'message': 'Security validation failed'
            }), 400
        
        # Get authorization code
        authorization_code = request.args.get('code')
        if not authorization_code:
            return jsonify({
                'error': 'No authorization code',
                'message': 'Authorization code not received from Google'
            }), 400
        
        # Exchange authorization code for tokens
        flow = create_flow()
        flow.fetch_token(authorization_response=request.url)
        
        credentials = flow.credentials
        
        # Get user info
        user_info = get_user_info(credentials)
        
        if user_info:
            # Store user info and credentials in session
            session['user'] = {
                'id': user_info.get('id'),
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'picture': user_info.get('picture'),
                'verified_email': user_info.get('verified_email', False)
            }
            
            # Store credentials securely in session (in memory)
            session['credentials'] = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
            
            logger.info(f"User authenticated successfully: {user_info.get('email')}")
            return redirect('/')
        else:
            return jsonify({
                'error': 'Authentication failed',
                'message': 'Failed to get user information from Google'
            }), 400
            
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return jsonify({
            'error': 'Callback failed',
            'message': str(e)
        }), 500

def get_user_info(credentials):
    """Get user information from Google API"""
    try:
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        
        logger.info(f"Retrieved user info for: {user_info.get('email')}")
        return user_info
        
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        return None

@app.route('/events')
def events():
    """Fetch next 10 upcoming events from the user's primary calendar"""
    try:
        # Check if user is authenticated
        if 'credentials' not in session:
            return jsonify({
                'error': 'Not authenticated',
                'message': 'Please login first to access calendar events'
            }), 401
        
        # Recreate credentials from session
        credentials = Credentials(**session['credentials'])
        
        # Refresh credentials if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            
            # Update session with refreshed credentials
            session['credentials'] = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
        
        # Build Calendar API service
        service = build('calendar', 'v3', credentials=credentials)
        
        # Get current time in RFC3339 format
        now = datetime.utcnow().isoformat() + 'Z'
        
        # Fetch next 10 upcoming events from primary calendar
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events_list = events_result.get('items', [])
        
        # Format events for JSON response
        formatted_events = []
        for event in events_list:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            formatted_event = {
                'id': event.get('id'),
                'summary': event.get('summary', 'No Title'),
                'description': event.get('description', ''),
                'start': start,
                'end': end,
                'location': event.get('location', ''),
                'attendees': [
                    {
                        'email': attendee.get('email'),
                        'responseStatus': attendee.get('responseStatus')
                    }
                    for attendee in event.get('attendees', [])
                ],
                'creator': event.get('creator', {}),
                'organizer': event.get('organizer', {}),
                'htmlLink': event.get('htmlLink'),
                'status': event.get('status')
            }
            formatted_events.append(formatted_event)
        
        user = session.get('user', {})
        logger.info(f"Retrieved {len(formatted_events)} events for user: {user.get('email')}")
        
        return jsonify({
            'success': True,
            'events': formatted_events,
            'count': len(formatted_events),
            'user': user,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except HttpError as error:
        logger.error(f"Google Calendar API error: {error}")
        return jsonify({
            'error': 'Calendar API error',
            'message': f'Failed to fetch calendar events: {error}'
        }), 500
        
    except Exception as e:
        logger.error(f"Error fetching calendar events: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while fetching calendar events'
        }), 500

@app.route('/logout')
def logout():
    """Logout user and clear session"""
    try:
        user_email = session.get('user', {}).get('email', 'Unknown')
        
        # Clear session data
        session.clear()
        
        logger.info(f"User logged out: {user_email}")
        return redirect('/')
        
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        return redirect('/')

@app.route('/user')
def get_user():
    """Get current user info"""
    if 'user' in session:
        return jsonify({
            'success': True,
            'user': session['user']
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': 'Not authenticated'
        }), 401

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
                        <a href="/events" class="btn-secondary text-lg py-3 px-6">
                            🔗 Events API Endpoint
                        </a>
                    </div>
                </div>
                
                <!-- Events Display -->
                <div id="events-container" class="hidden bg-white bg-opacity-10 backdrop-blur-lg rounded-lg p-8">
                    <h3 class="text-2xl font-bold mb-4">Your Upcoming Events</h3>
                    <div id="events-list"></div>
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
                } else {
                    alert('Error fetching events: ' + data.message);
                }
            } catch (error) {
                alert('Error fetching events: ' + error.message);
            }
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    try:
        logger.info("Starting Google Calendar API Flask app on localhost:5000")
        app.run(debug=True, host='localhost', port=5000)
    except Exception as e:
        logger.error(f"Error starting Calendar app: {str(e)}")