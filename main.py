#!/usr/bin/env python3
"""
Sharp Agents - Main Application Entry Point
A prediction market analysis and arbitrage detection system.
"""

from api.routes import create_app
from utils.logger import get_logger
from utils.config import get_config

logger = get_logger(__name__)


def main():
    """Main application entry point."""
    print("Sharp Agents Starting...")
    
    # Load configuration
    config = get_config()
    print(f"Database URL: {config.get_database_url()}")
    print(f"Server Port: {config.get_flask_port()}")
    print("Configuration loaded successfully")
    
    logger.info("Starting Sharp Agents application...")
    
    # Create Flask app
    app = create_app()
    
    # Run the application
    if __name__ == "__main__":
        logger.info("Running in development mode")
        app.run(
            host="0.0.0.0",
            port=config.get_flask_port(),
            debug=True
        )
    else:
        logger.info("Application initialized successfully")
        return app


if __name__ == "__main__":
    main()
