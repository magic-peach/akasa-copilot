#!/usr/bin/env python3
"""
Startup script for Akasa Booking API
"""

import os
import sys
from dotenv import load_dotenv

def check_environment():
    """Check if required environment variables are set"""
    load_dotenv()
    
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease create a .env file based on .env.example")
        print("and add your Supabase credentials.")
        return False
    
    print("✅ Environment variables configured")
    return True

def main():
    """Main startup function"""
    print("=" * 50)
    print("🚀 AKASA BOOKING API")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Import and run the Flask app
    try:
        from app import app
        print("✅ Flask application loaded")
        print("🌐 Starting server on http://localhost:5000")
        print("📚 API documentation available in README.md")
        print("🧪 Run tests with: python test_api.py")
        print("-" * 50)
        
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except ImportError as e:
        print(f"❌ Failed to import Flask application: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()