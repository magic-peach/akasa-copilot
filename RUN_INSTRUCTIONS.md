# How to Run the Enhanced Akasa Airlines Application

## Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

## Step-by-Step Setup Instructions

### 1. Navigate to the Project Directory
```bash
cd /Users/akankshatrehun/Desktop/akasa
```

### 2. Create and Activate Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment (macOS/Linux)
source venv/bin/activate

# On Windows, use:
# venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Start the Backend Server
```bash
python app.py
```

You should see output like:
```
INFO:event_service:Event processing background workers started
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5001
 * Running on http://192.168.0.107:5001
```

### 5. Open the Frontend
Open your web browser and navigate to:
```
file:///Users/akankshatrehun/Desktop/akasa/frontend/index.html
```

Or simply double-click the `frontend/index.html` file to open it in your default browser.

## ✅ What You Should See

1. **Homepage**: Modern dark-themed interface with flight search form
2. **Backend Connected**: Green notification confirming API connection
3. **Search Form**: Fields for From, To, Date, and Budget
4. **Voice Button**: Purple floating button in bottom-right corner

## 🎯 How to Test All Features

### Test Flight Search
1. **Default Search**: Click "Search Flights" (uses DEL to BOM, tomorrow's date, ₹10,000 budget)
2. **Custom Search**: 
   - From: DEL, BOM, BLR, HYD, GOA, CCU, MAA, AMD, PNQ, JAI
   - To: Any of the above airports
   - Date: Select any future date
   - Budget: Try different amounts (5000, 7000, 10000, 15000)

### Test Risk Analysis
1. Click "Predict Risk Score" on any flight
2. View the comprehensive risk analysis with:
   - Pie chart showing risk factors breakdown
   - Gauge chart showing overall risk score
   - Bar chart showing cost analysis
   - Detailed recommendations and AI conclusion

### Test PNR Tracking
1. Click "Track PNR" in the header
2. Enter any PNR number (e.g., "ABC123", "XYZ789")
3. Click "Track" to see detailed flight information

### Test Voice Assistant
1. **Voice Search**: Click the microphone button next to "Search Flights"
2. **General Voice**: Click the floating purple voice button
3. Say commands like:
   - "Search flights from Delhi to Mumbai"
   - "Find flights under 5000 rupees"
   - "What's the status of my flight?"

### Test Booking Flow
1. Click "Book Now" on any flight
2. Confirm redirect to booking.com
3. Return and test PNR tracking

## 🔧 Troubleshooting

### Backend Issues
- **Port 5001 in use**: Kill existing processes or change port in `app.py`
- **Module not found**: Ensure virtual environment is activated and dependencies installed
- **Permission errors**: Check file permissions in the project directory
- **Port 5000 conflict**: macOS AirPlay uses port 5000, so we use 5001 instead

### Frontend Issues
- **CORS errors**: Ensure backend is running on http://127.0.0.1:5001
- **Charts not loading**: Check internet connection (Chart.js loads from CDN)
- **Voice not working**: Use Chrome/Edge browsers for best voice recognition support

### Common Solutions
```bash
# If backend fails to start
pkill -f "python app.py"
source venv/bin/activate
python app.py

# If dependencies are missing
pip install --upgrade pip
pip install -r requirements.txt

# If virtual environment issues
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 📱 Browser Compatibility
- **Recommended**: Chrome, Edge, Safari (latest versions)
- **Voice Features**: Chrome and Edge work best
- **Charts**: All modern browsers supported

## 🎉 Features to Explore

1. **Multiple Flights**: See 8-12 flights with different airlines and prices
2. **Price Categories**: Below ₹5k, ₹7k, ₹10k, ₹15k, and Premium
3. **Risk Scoring**: Low/Medium/High risk with detailed analysis
4. **Interactive Charts**: Pie, gauge, and bar charts with animations
5. **Voice Search**: Natural language flight search
6. **PNR Tracking**: Complete flight status and passenger details
7. **Responsive Design**: Works on desktop, tablet, and mobile

## 🚀 Quick Start (One Command)
```bash
cd /Users/akankshatrehun/Desktop/akasa && source venv/bin/activate && python app.py
```

Then open: `file:///Users/akankshatrehun/Desktop/akasa/frontend/index.html`

Enjoy exploring the enhanced Akasa Airlines application! 🛫