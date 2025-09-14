#!/bin/bash

# Google OAuth Flask App Startup Script
echo "🚀 Starting Google OAuth Authentication Server..."

# Navigate to project directory
cd /Users/akankshatrehun/Desktop/akasa

# Kill any existing processes on port 5000
echo "🔄 Stopping any existing processes on port 5000..."
lsof -ti:5000 | xargs kill -9 2>/dev/null || true

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Install OAuth dependencies
echo "📥 Installing OAuth dependencies..."
pip install google-auth==2.23.4 google-auth-oauthlib==1.1.0 google-auth-httplib2==0.1.1

# Start the OAuth Flask app
echo "🔐 Starting OAuth server on port 5000..."
python oauth_app.py &

# Wait a moment for server to start
sleep 3

# Open OAuth app in default browser
echo "🌐 Opening OAuth login in browser..."
open "http://localhost:5000"

echo ""
echo "✅ OAuth application started successfully!"
echo ""
echo "📋 OAuth App Features:"
echo "   • Google OAuth login on: http://localhost:5000"
echo "   • Secure session management"
echo "   • User profile display"
echo "   • Logout functionality"
echo "   • Redirect to main app after login"
echo ""
echo "🔗 Integration:"
echo "   • OAuth App (port 5000) handles authentication"
echo "   • Main App (port 8080) handles flight booking"
echo "   • Seamless redirect between apps"
echo ""
echo "🛑 To stop the OAuth app:"
echo "   Press Ctrl+C or run: lsof -ti:5000 | xargs kill -9"
echo ""

# Keep script running to show logs
wait