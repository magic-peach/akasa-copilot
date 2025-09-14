# Google OAuth Setup Guide

## Prerequisites
1. A Google Cloud Platform account
2. A Google Cloud Project

## Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note down your project ID

## Step 2: Enable Google+ API
1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google+ API" and enable it
3. Also enable "Google Calendar API" for calendar integration

## Step 3: Create OAuth 2.0 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Web application" as the application type
4. Set the name (e.g., "Akasa Copilot OAuth")
5. Add authorized redirect URIs:
   - `http://localhost:5000/callback`
   - `http://localhost:5000/oauth2callback`
6. Click "Create"

## Step 4: Download Credentials
1. After creating the OAuth client, click the download button (⬇️)
2. Save the downloaded JSON file as `credentials.json`
3. Place it in the backend directory: `/akasa-copilot/backend/credentials.json`

## Step 5: Update credentials.json
The file should look like this:
```json
{
  "web": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_CLIENT_SECRET",
    "redirect_uris": [
      "http://localhost:5000/callback",
      "http://localhost:5000/oauth2callback"
    ]
  }
}
```

## Step 6: Test the Setup
1. Start the backend server: `python app.py`
2. Open the frontend and try signing in with Google
3. You should be redirected to Google's OAuth consent screen
4. After authorization, you'll be redirected back to the search page

## Troubleshooting
- **"Invalid redirect URI"**: Make sure the redirect URIs in Google Console match exactly
- **"Client ID not found"**: Verify the credentials.json file is in the correct location
- **"Access blocked"**: Check if the Google+ API is enabled in your project

## Security Notes
- Never commit `credentials.json` to version control
- The file is already in `.gitignore` for security
- For production, use environment variables instead of the JSON file