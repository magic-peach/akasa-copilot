# 🔐 Google OAuth Integration Setup Guide

## 🎉 **Complete Enhanced Akasa Airlines Application with Google OAuth**

I have successfully implemented Google OAuth login integration alongside all the previously requested features. Here's how to run the complete system:

## 🚀 **Two-App Architecture:**

### **1. OAuth App (Port 5000)**
- **Google OAuth login** with credentials.json
- **Secure session management**
- **User profile display**
- **Logout functionality**

### **2. Main App (Port 8080)**
- **Enhanced flight search** with 20 cities
- **Advanced risk prediction** with diverse scores
- **Real voice input** using Web Speech API
- **Comprehensive flight analysis**

## 🔧 **Setup Instructions:**

### **Step 1: Start Main Application (Port 8080)**
```bash
cd /Users/akankshatrehun/Desktop/akasa
./start_app.sh
```

### **Step 2: Start OAuth Application (Port 5000)**
```bash
cd /Users/akankshatrehun/Desktop/akasa
./start_oauth_app.sh
```

## 🎯 **Complete User Flow:**

### **Option A: With Google OAuth**
1. **OAuth Login** → Go to `http://localhost:5000`
2. **Google Sign-In** → Click "Continue with Google"
3. **Google Authentication** → Grant permissions
4. **Dashboard** → See user profile and welcome message
5. **Main App** → Click "✈️ Start Flight Search" → Redirects to port 8080
6. **Flight Booking** → Use all enhanced features

### **Option B: Direct Access**
1. **Welcome Page** → Go to `http://localhost:8080/frontend/welcome.html`
2. **Main App** → Click "✈️ Start Flight Search"
3. **Flight Booking** → Use all features without authentication

## 🔐 **OAuth Features:**

### **Google OAuth Login**
- **Secure authentication** using Google's OAuth 2.0
- **User profile fetching** - Name, email, profile picture
- **Session management** - Secure server-side sessions
- **Logout functionality** - Clear sessions and redirect

### **Integration Points**
- **Sign In buttons** redirect to OAuth app
- **Post-login redirect** to main application
- **Seamless user experience** between authentication and booking

## 🎯 **Test All Features:**

### **1. Google OAuth Flow**
1. Go to `http://localhost:5000`
2. Click "Continue with Google"
3. Sign in with your Google account
4. Grant permissions
5. See dashboard with your profile
6. Click "✈️ Start Flight Search"

### **2. Enhanced Flight Features**
- **20 cities** in dropdowns
- **Real voice search** - "Search flights from Delhi to Mumbai"
- **Diverse risk scores** - Low (<30), Medium (30-70), High (>70)
- **Comprehensive analysis** - "📊 Analyze All Flights"

### **3. Advanced Risk Prediction**
- **Individual flight analysis** with pie/gauge charts
- **Route comparison** with dual-axis charts
- **AI final verdict** with recommendations

## 📋 **Files Created for OAuth:**

1. **[`google_oauth_service.py`](google_oauth_service.py:1)** - OAuth service handler
2. **[`oauth_app.py`](oauth_app.py:1)** - Dedicated OAuth Flask app
3. **[`start_oauth_app.sh`](start_oauth_app.sh:1)** - OAuth app startup script
4. **[`credentials.json`](credentials.json:1)** - Google OAuth credentials (already existed)

## 🔧 **Troubleshooting:**

### **OAuth Issues**
- **Port 5000 in use**: Run `lsof -ti:5000 | xargs kill -9`
- **Credentials error**: Ensure `credentials.json` is valid
- **Redirect URI**: Must match Google Cloud Console settings

### **Integration Issues**
- **Main app not accessible**: Ensure port 8080 is running
- **Cross-origin errors**: Both apps have CORS enabled
- **Session issues**: Clear browser cookies and try again

## 🎉 **Complete Feature Set:**

### **✅ Authentication & Security**
- Google OAuth 2.0 integration
- Secure session management
- User profile management
- Logout functionality

### **✅ Enhanced Flight Booking**
- 20 major Indian cities
- 6 airlines with realistic risk profiles
- Advanced risk prediction model
- Real voice input with Web Speech API

### **✅ Advanced Analytics**
- Individual flight risk analysis
- Comprehensive route comparison
- AI-powered recommendations
- Professional data visualizations

### **✅ Complete User Experience**
- Welcome → OAuth Login → Flight Booking
- PNR tracking and booking.com integration
- Voice assistant and natural language processing

## 🚀 **Quick Start Commands:**

### **Start Both Apps:**
```bash
# Terminal 1: Main App
cd /Users/akankshatrehun/Desktop/akasa && ./start_app.sh

# Terminal 2: OAuth App
cd /Users/akankshatrehun/Desktop/akasa && ./start_oauth_app.sh
```

### **Access Points:**
- **OAuth Login**: `http://localhost:5000`
- **Main App**: `http://localhost:8080/frontend/welcome.html`

**The complete Akasa Airlines application now features Google OAuth authentication, advanced AI risk prediction, real voice input, and comprehensive flight analysis!** 🛫🔐🤖