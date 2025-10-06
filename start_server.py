#!/usr/bin/env python3
"""
FastCRM Server Startup Script
Ensures environment variables are loaded before starting the server
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Verify critical environment variables
required_vars = ["CRM_SECRET_KEY", "DATABASE_URL"]
missing_vars = []

for var in required_vars:
    if not os.getenv(var):
        missing_vars.append(var)

if missing_vars:
    print(f"Missing required environment variables: {', '.join(missing_vars)}")
    print("Please ensure .env file exists with all required variables")
    sys.exit(1)

print("Environment variables loaded successfully")
print(f"CRM_SECRET_KEY: {'SET' if os.getenv('CRM_SECRET_KEY') else 'NOT_SET'}")
print(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'NOT_SET')}")

# Import and start the application
try:
    from main import app
    print("FastCRM application imported successfully")
    
    import uvicorn
    print("Starting FastCRM server...")
    print("Server will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
    
except Exception as e:
    print(f"Error starting server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
