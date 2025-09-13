# 🚀 Simple Run Guide - Enhanced Akasa Airlines App

## ⚡ **Quick Start (Recommended)**

### **Option 1: Use the Startup Script**
```bash
cd /Users/akankshatrehun/Desktop/akasa
./start_app.sh
```

### **Option 2: Manual Steps**
```bash
# 1. Navigate to project
cd /Users/akankshatrehun/Desktop/akasa

# 2. Kill any existing processes
pkill -f "python.*app.py"

# 3. Activate virtual environment
source venv/bin/activate

# 4. Start backend
python app.py
```

**Expected Output:**
```
INFO:event_service:Event processing background workers started
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:8080
```

### **Step 3: Open Frontend**
Open your browser and go to:
```
file:///Users/akankshatrehun/Desktop/akasa/frontend/index.html
```

## ✅ **What You Should See**

1. **Green "Backend Connected" notification** - Confirms API is working
2. **Flight search form** with From, To, Date, Budget fields
3. **Multiple flights** (8-12) when you click "Search Flights"
4. **"Predict Risk Score" buttons** next to each flight
5. **"Track PNR" button** in the header
6. **Purple voice assistant button** in bottom-right corner

## 🎯 **Test All Features**

### **Flight Search**
- Try different routes: DEL↔BOM, BLR↔HYD, GOA↔CCU
- Test different budgets: 5000, 7000, 10000, 15000
- See flights categorized: "Below ₹5k", "Below ₹7k", etc.

### **Risk Analysis**
- Click "Predict Risk Score" on any flight
- View pie charts, gauge charts, and bar charts
- Read AI conclusion and recommendations

### **PNR Tracking**
- Click "Track PNR" in header
- Enter any PNR (e.g., "ABC123", "XYZ789")
- View complete flight and passenger details

### **Voice Assistant**
- Click microphone next to "Search Flights"
- Say: "Search flights from Delhi to Mumbai under 5000 rupees"
- Use floating voice button for general queries

## 🔧 **If Port Issues Persist**

### **Kill All Python Processes**
```bash
sudo pkill -f python
```

### **Use Different Port**
Edit `app.py` line 1175 and `frontend/index.html` line 354:
```python
# In app.py
app.run(debug=True, host='0.0.0.0', port=9000)
```
```javascript
// In frontend/index.html
const API_BASE = 'http://localhost:9000';
```

### **Check What's Using Ports**
```bash
lsof -i :5000
lsof -i :5001
lsof -i :8080
```

## 🎉 **Features Implemented**

✅ **Multiple Flights** - 8-12 flights per search with different airlines
✅ **Price Categories** - Below ₹5k, ₹7k, ₹10k, ₹15k, Premium
✅ **Risk Analysis** - 8 risk factors with interactive charts
✅ **Voice Search** - Natural language flight search
✅ **PNR Tracking** - Complete flight status and details
✅ **booking.com Integration** - Seamless booking flow
✅ **AI Recommendations** - Intelligent flight analysis
✅ **Professional UI** - Modern dark theme with animations

**Enjoy your enhanced flight booking experience!** ✈️