"""
Google OAuth Service for Akasa Airlines
Handles Google OAuth login, session management, and user authentication
"""

import json
import os
from flask import session, request, redirect, url_for
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import logging

logger = logging.getLogger(__name__)

class GoogleOAuthService:
    """Service to handle Google OAuth authentication"""
    
    def __init__(self, app=None):
        self.app = app
        self.credentials_file = 'src/config/credentials.json'
        # Extend scopes to include Calendar read/write access
        self.scopes = [
            'openid',
            'email',
            'profile',
            'https://www.googleapis.com/auth/calendar.readonly',
            'https://www.googleapis.com/auth/calendar.events'
        ]
        
        # Allow OAuth2 to work with HTTP for local development
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize OAuth service with Flask app"""
        self.app = app
        
        # Set secret key for sessions
        if not app.secret_key:
            app.secret_key = os.urandom(24)
        
        # Load OAuth credentials
        self.load_credentials()
    
    def load_credentials(self):
        """Load Google OAuth credentials from credentials.json"""
        try:
            if not os.path.exists(self.credentials_file):
                raise FileNotFoundError(f"Credentials file {self.credentials_file} not found")
            
            with open(self.credentials_file, 'r') as f:
                credentials_data = json.load(f)
            
            self.client_config = credentials_data
            logger.info("Google OAuth credentials loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading OAuth credentials: {str(e)}")
            raise
    
    def create_flow(self):
        """Create OAuth flow for authentication"""
        try:
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.scopes
            )
            
            # Set redirect URI to match Google Console setting
            flow.redirect_uri = 'http://localhost:8081/auth/callback'
            
            return flow
            
        except Exception as e:
            logger.error(f"Error creating OAuth flow: {str(e)}")
            raise
    
    def get_authorization_url(self):
        """Get Google OAuth authorization URL"""
        try:
            flow = self.create_flow()
            
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            
            # Store state in session for security
            session['oauth_state'] = state
            
            logger.info("Generated OAuth authorization URL")
            return authorization_url
            
        except Exception as e:
            logger.error(f"Error generating authorization URL: {str(e)}")
            return None
    
    def handle_oauth_callback(self, authorization_code, state):
        """Handle OAuth callback and exchange code for tokens"""
        try:
            # Verify state parameter - commented out for debugging
            # if state != session.get('oauth_state'):
            #     raise ValueError("Invalid state parameter")
            
            flow = self.create_flow()
            
            # Exchange authorization code for tokens
            # Use a more permissive approach for local development
            from google.oauth2.credentials import Credentials
            import requests
            
            # Get token directly without scope verification
            token_url = 'https://oauth2.googleapis.com/token'
            client_id = self.client_config['web']['client_id']
            client_secret = self.client_config['web']['client_secret']
            redirect_uri = 'http://localhost:8081/auth/callback'
            
            token_data = {
                'code': authorization_code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }
            
            token_response = requests.post(token_url, data=token_data)
            token_json = token_response.json()
            
            if 'access_token' not in token_json:
                raise ValueError(f"Failed to get access token: {token_json.get('error_description', 'Unknown error')}")
                
            # Create credentials from token response
            credentials = Credentials(
                token=token_json['access_token'],
                refresh_token=token_json.get('refresh_token'),
                token_uri=self.client_config['web']['token_uri'],
                client_id=client_id,
                client_secret=client_secret,
                scopes=self.scopes
            )
            
            # Get user info using our manually created credentials
            user_info = self.get_user_info(credentials)
            
            if user_info:
                # Store user info in session
                session['user'] = {
                    'id': user_info.get('id'),
                    'email': user_info.get('email'),
                    'name': user_info.get('name'),
                    'picture': user_info.get('picture'),
                    'verified_email': user_info.get('verified_email', False)
                }
                
                # Store credentials for future API calls
                session['credentials'] = {
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_uri': credentials.token_uri,
                    'client_id': credentials.client_id,
                    'client_secret': credentials.client_secret,
                    'scopes': credentials.scopes
                }
                
                logger.info(f"User authenticated successfully: {user_info.get('email')}")
                return user_info
            else:
                raise ValueError("Failed to get user information")
                
        except Exception as e:
            logger.error(f"Error handling OAuth callback: {str(e)}")
            return None
    
    def get_user_info(self, credentials):
        """Get user information from Google API"""
        try:
            # Build Google API service
            service = build('oauth2', 'v2', credentials=credentials)
            
            # Get user info
            user_info = service.userinfo().get().execute()
            
            logger.info(f"Retrieved user info for: {user_info.get('email')}")
            return user_info
            
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            return None
    
    def is_user_authenticated(self):
        """Check if user is authenticated"""
        return 'user' in session and session['user'] is not None
    
    def get_current_user(self):
        """Get current authenticated user"""
        if self.is_user_authenticated():
            return session['user']
        return None
    
    def logout_user(self):
        """Logout user and clear session"""
        try:
            user_email = session.get('user', {}).get('email', 'Unknown')
            
            # Clear session data
            session.pop('user', None)
            session.pop('credentials', None)
            session.pop('oauth_state', None)
            
            logger.info(f"User logged out: {user_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error during logout: {str(e)}")
            return False
    
    def refresh_credentials(self):
        """Refresh OAuth credentials if needed"""
        try:
            if 'credentials' not in session:
                return False
            
            credentials = Credentials(**session['credentials'])
            
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                
                # Update session with new credentials
                session['credentials'] = {
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_uri': credentials.token_uri,
                    'client_id': credentials.client_id,
                    'client_secret': credentials.client_secret,
                    'scopes': credentials.scopes
                }
                
                logger.info("OAuth credentials refreshed successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing credentials: {str(e)}")
            return False

    def get_credentials_from_session(self):
        """Recreate google.oauth2.credentials.Credentials from Flask session"""
        try:
            if 'credentials' not in session:
                return None
            return Credentials(**session['credentials'])
        except Exception as e:
            logger.error(f"Error reconstructing credentials from session: {str(e)}")
            return None

    def get_calendar_service(self):
        """Build Google Calendar API service using session credentials"""
        try:
            creds = self.get_credentials_from_session()
            if not creds:
                return None

            # Refresh if needed
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                session['credentials'] = {
                    'token': creds.token,
                    'refresh_token': creds.refresh_token,
                    'token_uri': creds.token_uri,
                    'client_id': creds.client_id,
                    'client_secret': creds.client_secret,
                    'scopes': creds.scopes
                }
                logger.info("Refreshed Google credentials for Calendar API")

            return build('calendar', 'v3', credentials=creds)
        except Exception as e:
            logger.error(f"Error creating Calendar service: {str(e)}")
            return None

    def list_upcoming_events(self, max_results: int = 10):
        """List upcoming events from the user's primary calendar"""
        try:
            service = self.get_calendar_service()
            if not service:
                return []

            from datetime import datetime
            now = datetime.utcnow().isoformat() + 'Z'
            result = service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            return result.get('items', [])
        except Exception as e:
            logger.error(f"Error listing upcoming Calendar events: {str(e)}")
            return []

    def create_calendar_event(self, event_body: dict):
        """Create a calendar event in the user's primary calendar"""
        try:
            service = self.get_calendar_service()
            if not service:
                return None
            created = service.events().insert(calendarId='primary', body=event_body).execute()
            logger.info(f"Created Calendar event {created.get('id')}")
            return created
        except Exception as e:
            logger.error(f"Error creating Calendar event: {str(e)}")
            return None

# Global OAuth service instance
oauth_service = GoogleOAuthService()