#!/bin/bash

# Enhanced Akasa Airlines Application Startup Script
echo "🚀 Starting Enhanced Akasa Airlines Application..."

# Navigate to project directory
cd /Users/akankshatrehun/Desktop/akasa

# Kill any existing Python processes
echo "🔄 Stopping any existing processes..."
pkill -f "python.*app.py" 2>/dev/null || true

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Start the Flask backend
echo "🖥️  Starting backend server on port 8080..."
python app.py &

# Wait a moment for server to start
sleep 3

# Open welcome page in default browser
echo "🌐 Opening welcome page in browser..."
open "file:///Users/akankshatrehun/Desktop/akasa/frontend/welcome.html"

echo ""
echo "✅ Application started successfully!"
echo ""
echo "📋 What you can do now:"
echo "   • Backend running on: http://localhost:8080"
echo "   • Frontend opened in your browser"
echo "   • Test flight search with different routes and budgets"
echo "   • Click 'Predict Risk Score' to see detailed analysis"
echo "   • Use 'Track PNR' to test flight tracking"
echo "   • Try voice search with the microphone button"
echo ""
echo "🛑 To stop the application:"
echo "   Press Ctrl+C or run: pkill -f 'python.*app.py'"
echo ""

# Keep script running to show logs
wait