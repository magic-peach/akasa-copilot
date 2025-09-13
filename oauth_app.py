"""
Google OAuth Flask App for Akasa Airlines
Handles Google OAuth login and redirects to main application
Runs on localhost:5000 as required
"""

from flask import Flask, render_template_string, redirect, url_for, session, request, jsonify
from flask_cors import CORS
from google_oauth_service import oauth_service
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

# Set secret key for sessions
app.secret_key = os.urandom(24)

# Initialize OAuth service
oauth_service.init_app(app)

@app.route('/')
def home():
    """Home page with Google OAuth login"""
    if oauth_service.is_user_authenticated():
        user = oauth_service.get_current_user()
        return render_template_string(DASHBOARD_TEMPLATE, user=user)
    else:
        return render_template_string(LOGIN_TEMPLATE)

@app.route('/login')
def login():
    """Initiate Google OAuth login"""
    try:
        authorization_url = oauth_service.get_authorization_url()
        if authorization_url:
            logger.info("Redirecting to Google OAuth")
            return redirect(authorization_url)
        else:
            return "Error: Could not generate authorization URL", 500
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return f"Login error: {str(e)}", 500

@app.route('/oauth2callback')
def oauth_callback():
    """Handle OAuth callback from Google"""
    try:
        # Get authorization code and state from callback
        authorization_code = request.args.get('code')
        state = request.args.get('state')
        
        if not authorization_code:
            return "Error: No authorization code received", 400
        
        # Handle OAuth callback
        user_info = oauth_service.handle_oauth_callback(authorization_code, state)
        
        if user_info:
            logger.info(f"OAuth login successful for: {user_info.get('email')}")
            return redirect(url_for('dashboard'))
        else:
            return "Error: OAuth authentication failed", 400
            
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return f"OAuth callback error: {str(e)}", 500

@app.route('/dashboard')
def dashboard():
    """User dashboard after successful login"""
    if not oauth_service.is_user_authenticated():
        return redirect(url_for('home'))
    
    user = oauth_service.get_current_user()
    return render_template_string(DASHBOARD_TEMPLATE, user=user)

@app.route('/logout')
def logout():
    """Logout user and redirect to home"""
    oauth_service.logout_user()
    return redirect(url_for('home'))

@app.route('/api/user')
def get_user():
    """API endpoint to get current user info"""
    if oauth_service.is_user_authenticated():
        user = oauth_service.get_current_user()
        return jsonify({'success': True, 'user': user})
    else:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

@app.route('/goto-app')
def goto_app():
    """Redirect to main Akasa application"""
    if oauth_service.is_user_authenticated():
        # Redirect to main app on port 8080
        return redirect('http://localhost:8080/frontend/index.html')
    else:
        return redirect(url_for('home'))

# HTML Templates
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Akasa Copilot - Sign In</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { 
            background: linear-gradient(135deg, #121212 0%, #1a1a1a 100%);
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
            items-center;
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
        <div class="max-w-md w-full bg-gray-800 p-8 rounded-lg shadow-lg">
            <div class="text-center mb-8">
                <svg class="h-12 w-12 text-purple-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                </svg>
                <h1 class="text-3xl font-bold bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent">
                    Akasa Copilot
                </h1>
                <p class="text-gray-400 mt-2">Sign in to continue</p>
            </div>
            
            <div class="space-y-4">
                <a href="{{ url_for('login') }}" class="btn-google w-full justify-center">
                    <svg class="h-5 w-5" viewBox="0 0 24 24">
                        <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                        <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                    Continue with Google
                </a>
                
                <div class="text-center">
                    <p class="text-sm text-gray-400">
                        By signing in, you agree to our Terms of Service and Privacy Policy
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
    <title>Akasa Copilot - Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { 
            background: linear-gradient(135deg, #121212 0%, #1a1a1a 100%);
            min-height: 100vh;
        }
        .btn-primary {
            background: #6C63FF;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
        }
        .btn-primary:hover {
            background: #5a52e6;
            box-shadow: 0 4px 12px rgba(108, 99, 255, 0.3);
        }
        .btn-secondary {
            background: #374151;
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .btn-secondary:hover {
            background: #4B5563;
        }
    </style>
</head>
<body class="text-white">
    <div class="min-h-screen">
        <!-- Header -->
        <header class="bg-gray-800 border-b border-gray-700">
            <div class="container mx-auto px-6 py-4">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-3">
                        <svg class="h-8 w-8 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                        </svg>
                        <h1 class="text-2xl font-bold bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent">
                            Akasa Copilot
                        </h1>
                    </div>
                    <div class="flex items-center space-x-4">
                        <div class="flex items-center space-x-3">
                            {% if user.picture %}
                            <img src="{{ user.picture }}" alt="Profile" class="w-8 h-8 rounded-full">
                            {% endif %}
                            <span class="text-sm">{{ user.name }}</span>
                        </div>
                        <a href="{{ url_for('logout') }}" class="btn-secondary">Logout</a>
                    </div>
                </div>
            </div>
        </header>
        
        <!-- Main Content -->
        <main class="container mx-auto px-6 py-12">
            <div class="max-w-4xl mx-auto text-center">
                <h2 class="text-4xl font-bold mb-6">Welcome, {{ user.name }}!</h2>
                <p class="text-xl text-gray-400 mb-8">
                    You're successfully signed in with {{ user.email }}
                </p>
                
                <div class="bg-gray-800 rounded-lg p-8 mb-8">
                    <h3 class="text-2xl font-bold mb-4">Ready to explore flights?</h3>
                    <p class="text-gray-400 mb-6">
                        Access the enhanced Akasa Airlines application with AI-powered risk prediction,
                        voice search, and comprehensive flight analysis.
                    </p>
                    
                    <div class="flex flex-col sm:flex-row gap-4 justify-center">
                        <a href="http://localhost:8080/frontend/index.html" class="btn-primary text-lg py-3 px-6">
                            ✈️ Start Flight Search
                        </a>
                        <a href="http://localhost:8080/frontend/welcome.html" class="btn-secondary text-lg py-3 px-6">
                            📖 View Welcome Page
                        </a>
                    </div>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div class="bg-gray-800 rounded-lg p-6">
                        <h4 class="font-bold mb-2">🎤 Voice Search</h4>
                        <p class="text-sm text-gray-400">Use voice commands to search flights</p>
                    </div>
                    <div class="bg-gray-800 rounded-lg p-6">
                        <h4 class="font-bold mb-2">📊 Risk Analysis</h4>
                        <p class="text-sm text-gray-400">AI-powered flight risk prediction</p>
                    </div>
                    <div class="bg-gray-800 rounded-lg p-6">
                        <h4 class="font-bold mb-2">🏷️ PNR Tracking</h4>
                        <p class="text-sm text-gray-400">Track your flight status</p>
                    </div>
                </div>
            </div>
        </main>
    </div>
</body>
</html>
"""

if __name__ == '__main__':
    try:
        logger.info("Starting Google OAuth Flask app on localhost:5001")
        app.run(debug=True, host='localhost', port=5001)
    except Exception as e:
        logger.error(f"Error starting OAuth app: {str(e)}")