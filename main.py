#!/usr/bin/env python3
"""
Sharp Agents - Main Application Entry Point
A prediction market analysis and arbitrage detection system.
"""

import sys
import time
import signal
import threading
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app import app, initialize_app
from scrapers.kalshi_scraper import KalshiScraper
from utils.logger import get_logger
from utils.config import get_config

# Global variables
logger = get_logger(__name__)
scheduler: Optional[BackgroundScheduler] = None
flask_thread: Optional[threading.Thread] = None
running = True


def print_startup_banner():
    """Print the startup banner with ASCII art."""
    banner = """
    ███████╗██╗  ██╗ █████╗ ██████╗ ██████╗     █████╗  ██████╗ ████████╗███╗   ██╗███████╗
    ██╔════╝██║  ██║██╔══██╗██╔══██╗██╔══██╗    ██╔══██╗██╔═══██╗╚══██╔══╝████╗  ██║██╔════╝
    ███████╗███████║███████║██████╔╝██████╔╝    ███████║██║   ██║   ██║   ██╔██╗ ██║███████╗
    ╚════██║██╔══██║██╔══██║██╔══██╗██╔══██╗    ██╔══██║██║   ██║   ██║   ██║╚██╗██║╚════██║
    ███████║██║  ██║██║  ██║██║  ██║██████╔╝    ██║  ██║╚██████╔╝   ██║   ██║ ╚████║███████║
    ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝     ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═══╝╚══════╝
    
    ================================================================================================
                                    NFL Market Monitor v0.1
    ================================================================================================
    
    🏈 Dashboard: http://localhost:5001
    🔄 Collection: Every 5 minutes
    📊 Platform: Kalshi + Polymarket
    🚀 Status: Starting up...
    
    ================================================================================================
    """
    print(banner)


def run_data_collection():
    """Run the data collection process."""
    try:
        logger.info("🔄 Starting scheduled data collection...")
        start_time = datetime.now()
        
        # Initialize scraper
        scraper = KalshiScraper()
        
        # Check authentication
        status = scraper.get_collection_status()
        if not status.get('client_authenticated'):
            logger.error("❌ Failed to authenticate with Kalshi API")
            return
        
        # Run collection
        collection_stats = scraper.run_collection()
        
        if collection_stats:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"✅ Data collection completed in {duration:.2f} seconds")
            logger.info(f"📊 Markets found: {collection_stats.get('total_markets_found', 0)}")
            logger.info(f"💾 Markets saved: {collection_stats.get('markets_saved', 0)}")
            logger.info(f"❌ Markets failed: {collection_stats.get('markets_failed', 0)}")
            
            if collection_stats.get('errors'):
                logger.warning(f"⚠️  Errors encountered: {len(collection_stats['errors'])}")
                for error in collection_stats['errors'][:3]:  # Log first 3 errors
                    logger.warning(f"   - {error}")
        else:
            logger.error("❌ Data collection failed - no statistics returned")
            
    except Exception as e:
        logger.error(f"❌ Error during scheduled data collection: {e}")


def start_flask_app():
    """Start the Flask application in a separate thread."""
    global app
    
    try:
        logger.info("🌐 Starting Flask web application...")
        
        # Initialize the app if not already done
        if not hasattr(app, 'initialized'):
            if initialize_app():
                app.initialized = True
                logger.info("✅ Flask application initialized successfully")
            else:
                logger.error("❌ Failed to initialize Flask application")
                return
        
        # Run Flask app
        app.run(
            host="0.0.0.0",
            port=5001,  # Use port 5001 to avoid macOS AirPlay conflict
            debug=False,  # Disable debug mode for production
            use_reloader=False  # Disable reloader when running in thread
        )
        
    except Exception as e:
        logger.error(f"❌ Error starting Flask application: {e}")


def setup_scheduler():
    """Setup the APScheduler for periodic data collection."""
    global scheduler
    
    try:
        logger.info("⏰ Setting up data collection scheduler...")
        
        # Create scheduler
        scheduler = BackgroundScheduler()
        
        # Add job to run every 5 minutes, starting after 5 minutes (not immediately)
        from datetime import timedelta
        next_run = datetime.now() + timedelta(minutes=5)
        
        scheduler.add_job(
            func=run_data_collection,
            trigger=IntervalTrigger(minutes=5),
            id='data_collection',
            name='Collect market data every 5 minutes',
            next_run_time=next_run,
            replace_existing=True
        )
        
        # Start scheduler
        scheduler.start()
        logger.info("✅ Scheduler started successfully")
        logger.info("🔄 Data collection scheduled every 5 minutes")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error setting up scheduler: {e}")
        return False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global running, scheduler, flask_thread
    
    print("\n" + "="*80)
    print("🛑 SHUTDOWN SIGNAL RECEIVED")
    print("="*80)
    
    logger.info("🛑 Shutdown signal received, starting graceful shutdown...")
    
    # Stop the main loop
    running = False
    
    # Shutdown scheduler
    if scheduler:
        logger.info("⏰ Shutting down scheduler...")
        scheduler.shutdown(wait=True)
        logger.info("✅ Scheduler shut down successfully")
    
    # Note: Flask thread will be terminated when main process exits
    
    print("✅ Graceful shutdown completed")
    print("👋 Goodbye!")
    
    # Exit cleanly
    sys.exit(0)


def main():
    """Main application entry point."""
    global running, flask_thread
    
    try:
        # Print startup banner
        print_startup_banner()
        
        # Load configuration
        config = get_config()
        logger.info("⚙️  Configuration loaded successfully")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
        
        # Initialize Flask app
        if not initialize_app():
            logger.error("❌ Failed to initialize Flask application")
            sys.exit(1)
        
        # Setup scheduler
        if not setup_scheduler():
            logger.error("❌ Failed to setup scheduler")
            sys.exit(1)
        
        # Start Flask app in a separate thread
        flask_thread = threading.Thread(
            target=start_flask_app,
            name="Flask-Thread",
            daemon=True
        )
        flask_thread.start()
        logger.info("🌐 Flask application started in background thread")
        
        # Wait a moment for Flask to start
        time.sleep(2)
        
        # Print status
        print("\n" + "="*80)
        print("🚀 SHARP AGENTS IS NOW RUNNING!")
        print("="*80)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Dashboard: http://localhost:5001")
        print(f"🔄 Data Collection: Every 5 minutes")
        print(f"📊 Logs: Check console output and log files")
        print("="*80)
        print("💡 Press Ctrl+C to stop the application gracefully")
        print("⏰ First data collection will run in 5 minutes")
        print("="*80 + "\n")
        
        # Note: Initial data collection will run after 5 minutes via scheduler
        logger.info("⏰ Initial data collection scheduled for 5 minutes from now")
        
        # Main loop - keep the application running
        logger.info("🔄 Entering main loop...")
        flask_start_time = time.time()
        
        while running:
            try:
                # Sleep for a longer interval to reduce CPU usage
                time.sleep(5)
                
                # Check if Flask thread is still alive (but don't restart constantly)
                if flask_thread and not flask_thread.is_alive():
                    # Only restart if it's been more than 30 seconds since last restart
                    if time.time() - flask_start_time > 30:
                        logger.warning("⚠️  Flask thread has stopped, restarting...")
                        flask_thread = threading.Thread(
                            target=start_flask_app,
                            name="Flask-Thread-Restart",
                            daemon=True
                        )
                        flask_thread.start()
                        flask_start_time = time.time()
                    else:
                        logger.debug("Flask thread stopped, but waiting before restart...")
                
            except KeyboardInterrupt:
                signal_handler(signal.SIGINT, None)
            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}")
                time.sleep(10)  # Wait longer before continuing
        
    except Exception as e:
        logger.error(f"❌ Fatal error in main application: {e}")
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
