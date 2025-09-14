# 📅 Google Calendar API Integration Setup Guide

## ✅ **What's Been Created**

### **Files Created:**
- [`calendar_app.py`](calendar_app.py) - Main Flask application with Google Calendar API integration
- [`credentials_template.json`](credentials_template.json) - Template for Google Cloud Console credentials

### **Features Implemented:**
- **OAuth 2.0 Flow**: Secure Google authentication
- **Three Required Endpoints**:
  - `/login` - Redirects user to Google OAuth login
  - `/callback` - Handles OAuth callback and stores credentials in session
  - `/events` - Fetches next 10 upcoming events from user's primary calendar
- **Session Management**: Secure token storage in memory
- **User Interface**: Professional web interface with Tailwind CSS

## 🔧 **Setup Instructions**

### **Step 1: Google Cloud Console Setup**

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create or Select Project**:
   - Create a new project or select existing one
   - Note the Project ID

3. **Enable Google Calendar API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

4. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - Choose "Web application"
   - Set name: "Calendar API Flask App"
   - Add Authorized redirect URI: `http://localhost:5000/callback`
   - Click "Create"

5. **Download Credentials**:
   - Click the download button for your OAuth 2.0 Client ID
   - Save the file as `credentials.json` in the project root
   - Or use the template and fill in your values

### **Step 2: Setup Credentials File**

**Option A: Download from Google Cloud Console**
```bash
# Download credentials.json from Google Cloud Console
# Place it in the project root directory
```

**Option B: Use Template**
```bash
# Copy the template
cp credentials_template.json credentials.json

# Edit credentials.json with your values:
# - Replace YOUR_CLIENT_ID with your actual client ID
# - Replace YOUR_CLIENT_SECRET with your actual client secret  
# - Replace your-project-id with your actual project ID
```

### **Step 3: Install Dependencies**

All required dependencies are already in [`requirements.txt`](requirements.txt):
```bash
# Install dependencies
pip install -r requirements.txt
```

Required packages:
- `Flask==2.3.3` - Web framework
- `flask-cors==4.0.0` - CORS support
- `google-auth==2.23.4` - Google authentication
- `google-auth-oauthlib==1.1.0` - OAuth 2.0 flow
- `google-auth-httplib2==0.1.1` - HTTP transport
- `google-api-python-client==2.108.0` - Google API client

### **Step 4: Run the Application**

```bash
# Start the Flask app on localhost:5000
python calendar_app.py
```

The app will be available at: `http://localhost:5000`

## 🚀 **How to Use**

### **1. Access the Application**
Open your browser and go to: `http://localhost:5000`

### **2. Sign in with Google**
- Click "Sign in with Google"
- Authorize the application to access your calendar
- Grant permissions for calendar read access

### **3. View Calendar Events**
- After authentication, you'll see the dashboard
- Click "Get Calendar Events" to fetch your upcoming events
- Or visit `/events` endpoint directly for JSON response

## 📋 **API Endpoints**

### **Authentication Endpoints**

#### **GET /login**
- **Purpose**: Redirect user to Google OAuth login
- **Response**: Redirects to Google OAuth consent screen
- **Usage**: `http://localhost:5000/login`

#### **GET /callback**
- **Purpose**: Handle Google OAuth callback and store credentials
- **Parameters**: `code` (authorization code), `state` (security token)
- **Response**: Redirects to dashboard on success
- **Usage**: Automatically called by Google OAuth flow

### **Calendar Endpoints**

#### **GET /events**
- **Purpose**: Fetch next 10 upcoming events from user's primary calendar
- **Authentication**: Required (OAuth 2.0)
- **Response**: JSON array of calendar events
- **Usage**: `http://localhost:5000/events`

**Example Response:**
```json
{
  "success": true,
  "events": [
    {
      "id": "event_id",
      "summary": "Meeting with Team",
      "description": "Weekly team sync",
      "start": "2024-01-15T10:00:00Z",
      "end": "2024-01-15T11:00:00Z",
      "location": "Conference Room A",
      "attendees": [
        {
          "email": "user@example.com",
          "responseStatus": "accepted"
        }
      ],
      "creator": {
        "email": "organizer@example.com"
      },
      "htmlLink": "https://calendar.google.com/event?eid=...",
      "status": "confirmed"
    }
  ],
  "count": 1,
  "user": {
    "email": "user@example.com",
    "name": "John Doe"
  },
  "timestamp": "2024-01-15T08:00:00.000Z"
}
```

### **Utility Endpoints**

#### **GET /**
- **Purpose**: Home page with authentication status
- **Response**: HTML dashboard if authenticated, login page if not

#### **GET /user**
- **Purpose**: Get current authenticated user info
- **Response**: JSON with user details or 401 if not authenticated

#### **GET /logout**
- **Purpose**: Logout user and clear session
- **Response**: Redirects to home page

## 🔐 **Security Features**

### **OAuth 2.0 Implementation**
- **State Parameter**: CSRF protection during OAuth flow
- **Secure Sessions**: Flask sessions with random secret key
- **Token Storage**: Credentials stored securely in server-side sessions
- **Automatic Refresh**: Expired tokens are automatically refreshed

### **Scopes Requested**
- `openid` - Basic OpenID Connect
- `email` - User email address
- `profile` - User profile information
- `https://www.googleapis.com/auth/calendar.readonly` - Read-only calendar access

## 🧪 **Testing the Integration**

### **1. Basic Authentication Test**
```bash
# Visit login endpoint
curl -L http://localhost:5000/login
```

### **2. Events API Test**
```bash
# After authentication, test events endpoint
curl -b cookies.txt http://localhost:5000/events
```

### **3. User Info Test**
```bash
# Check authenticated user
curl -b cookies.txt http://localhost:5000/user
```

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **"Credentials file not found"**
- Ensure `credentials.json` exists in project root
- Check file permissions
- Verify JSON format is valid

#### **"Invalid redirect URI"**
- Verify redirect URI in Google Cloud Console: `http://localhost:5000/callback`
- Ensure exact match including protocol and port

#### **"Access denied"**
- Check OAuth consent screen configuration
- Verify Calendar API is enabled
- Ensure user has calendar access

#### **"Token expired"**
- Tokens are automatically refreshed
- Clear browser cookies and re-authenticate if issues persist

### **Debug Mode**
The app runs in debug mode by default. Check console logs for detailed error information.

## 📝 **Next Steps**

### **Production Deployment**
- Set `app.secret_key` to a fixed secure value
- Use environment variables for sensitive configuration
- Implement proper session storage (Redis, database)
- Add HTTPS support
- Configure production OAuth redirect URIs

### **Enhanced Features**
- Add calendar event creation
- Implement calendar selection (multiple calendars)
- Add event filtering and search
- Implement webhook notifications
- Add calendar event modification

## ✅ **Verification Checklist**

- [ ] Google Cloud Console project created
- [ ] Calendar API enabled
- [ ] OAuth 2.0 credentials configured
- [ ] `credentials.json` file in place
- [ ] Dependencies installed
- [ ] App running on `localhost:5000`
- [ ] OAuth flow working
- [ ] Calendar events fetching successfully

**The Google Calendar API integration is now ready for testing! 🎉**