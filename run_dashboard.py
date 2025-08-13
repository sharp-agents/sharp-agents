#!/usr/bin/env python3
"""Launcher script for the Sharp Agents Dashboard."""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_environment():
    """Set up environment variables for the dashboard."""
    # Set The Odds API key
    if not os.getenv('THEODDS_API_KEY'):
        os.environ['THEODDS_API_KEY'] = '7f368349a729ac04ca1251f6ecda8d81'
        print("✓ Set THEODDS_API_KEY environment variable")
    
    # Set Flask configuration
    if not os.getenv('FLASK_ENV'):
        os.environ['FLASK_ENV'] = 'development'
        print("✓ Set FLASK_ENV to development")
    
    if not os.getenv('FLASK_DEBUG'):
        os.environ['FLASK_DEBUG'] = 'true'
        print("✓ Set FLASK_DEBUG to true")

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import flask
        print(f"✓ Flask {flask.__version__} is installed")
    except ImportError:
        print("❌ Flask is not installed. Installing...")
        os.system("pip install Flask Flask-Caching")
    
    try:
        import flask_caching
        print("✓ Flask-Caching is installed")
    except ImportError:
        print("❌ Flask-Caching is not installed. Installing...")
        os.system("pip install Flask-Caching")

def main():
    """Main launcher function."""
    print("🚀 Sharp Agents Dashboard Launcher")
    print("=" * 40)
    
    # Setup environment
    setup_environment()
    
    # Check dependencies
    check_dependencies()
    
    print(f"✓ API Key: {os.getenv('THEODDS_API_KEY')[:8]}...")
    
    print("\n📊 Starting Dashboard...")
    print("Dashboard will be available at: http://localhost:5001")
    print("Press Ctrl+C to stop the dashboard")
    print("-" * 40)
    
    try:
        # Import and run the dashboard
        from dashboard.app import app
        
        # Run the Flask app
        app.run(
            debug=True,
            host='0.0.0.0',
            port=5001,
            use_reloader=True
        )
        
    except ImportError as e:
        print(f"❌ Error importing dashboard: {e}")
        print("Make sure you're in the project root directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
