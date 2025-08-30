#!/usr/bin/env python3
"""
Startup script for Image Context Analyzer Web Server
"""

import os
import sys
import subprocess
import importlib

def check_dependencies():
    """Check if required packages are installed."""
    required_packages = [
        'flask',
        'flask_cors',
        'google.generativeai',
        'PIL',
        'dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'PIL':
                importlib.import_module('PIL')
            elif package == 'flask_cors':
                importlib.import_module('flask_cors')
            else:
                importlib.import_module(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 Install them with: pip install -r requirements.txt")
        return False
    
    return True

def check_env_file():
    """Check if .env file exists and has API key."""
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("💡 Please create a .env file with your Gemini API key:")
        print("   GEMINI_API_KEY=your_actual_api_key_here")
        return False
    
    # Load and check API key
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        print("❌ Invalid or missing GEMINI_API_KEY in .env file!")
        print("💡 Please update your .env file with your actual API key")
        return False
    
    return True

def main():
    """Main startup function."""
    print("🚀 Image Context Analyzer - Web Server Startup")
    print("=" * 50)
    
    # Check dependencies
    print("🔧 Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    print("✅ All dependencies are installed")
    
    # Check environment
    print("\n🌍 Checking environment...")
    if not check_env_file():
        sys.exit(1)
    print("✅ Environment is configured")
    
    # Check if web_server.py exists
    if not os.path.exists('web_server.py'):
        print("❌ web_server.py not found!")
        print("💡 Please ensure all project files are present")
        sys.exit(1)
    
    print("\n🎉 All checks passed! Starting web server...")
    print("📱 The web interface will be available at: http://localhost:5000")
    print("🧪 Test endpoint: http://localhost:5000/test")
    print("🏥 Health check: http://localhost:5000/health")
    print("🔄 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Start the web server
        subprocess.run([sys.executable, 'web_server.py'])
    except KeyboardInterrupt:
        print("\n👋 Web server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting web server: {e}")

if __name__ == "__main__":
    main()
