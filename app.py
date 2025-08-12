#!/usr/bin/env python3
"""
Flask web application for Sharp Agents Market Monitor.
Provides web interface for monitoring prediction markets and triggering data collection.
"""

import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.append('.')

from flask import Flask, render_template, jsonify, request
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from utils.config import get_config
from database.queries import get_active_markets, get_market_summary
from scrapers.kalshi_scraper import KalshiScraper


# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sharp-agents-secret-key-2024'

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
config = None
engine = None
SessionLocal = None


def initialize_app():
    """Initialize the Flask application with configuration and database."""
    global config, engine, SessionLocal
    
    try:
        # Get configuration
        config = get_config()
        
        # Initialize database connection
        database_url = config.get_database_url()
        engine = create_engine(database_url, echo=False)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        logger.info("Flask application initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Flask application: {e}")
        return False


def get_db_session() -> Session:
    """Get a database session."""
    if SessionLocal:
        return SessionLocal()
    else:
        raise RuntimeError("Database not initialized")


@app.route('/')
def index():
    """Main page showing market monitor dashboard."""
    try:
        session = get_db_session()
        
        # Get active markets (last hour)
        markets = get_active_markets(session, hours=1)
        
        # Format market data for display
        formatted_markets = []
        for market in markets:
            latest_price = market.get('latest_price', {})
            
            formatted_market = {
                'id': market.get('id'),
                'platform': market.get('platform', 'Unknown'),
                'ticker': market.get('ticker', 'Unknown'),
                'title': market.get('title', 'Unknown'),
                'market_type': market.get('market_type', 'Unknown'),
                'home_team': market.get('home_team'),
                'away_team': market.get('away_team'),
                'yes_bid': latest_price.get('yes_bid'),
                'yes_ask': latest_price.get('yes_ask'),
                'no_bid': latest_price.get('no_bid'),
                'no_ask': latest_price.get('no_ask'),
                'spread': latest_price.get('spread'),
                'volume': latest_price.get('volume'),
                'last_trade_price': latest_price.get('last_trade_price'),
                'last_updated': latest_price.get('timestamp'),
                'created_at': market.get('created_at'),
                'updated_at': market.get('updated_at')
            }
            formatted_markets.append(formatted_market)
        
        # Get market summary
        summary = get_market_summary(session)
        
        session.close()
        
        return render_template('index.html', 
                             markets=formatted_markets, 
                             summary=summary,
                             last_refresh=datetime.now())
                             
    except Exception as e:
        logger.error(f"Error rendering index page: {e}")
        return render_template('index.html', 
                             markets=[], 
                             summary={},
                             error=str(e),
                             last_refresh=datetime.now())


@app.route('/api/markets')
def api_markets():
    """API endpoint returning all markets as JSON."""
    try:
        session = get_db_session()
        
        # Get active markets
        markets = get_active_markets(session, hours=24)  # Last 24 hours
        
        # Format for JSON response
        markets_data = []
        for market in markets:
            latest_price = market.get('latest_price', {})
            
            market_data = {
                'id': market.get('id'),
                'platform': market.get('platform'),
                'ticker': market.get('ticker'),
                'title': market.get('title'),
                'market_type': market.get('market_type'),
                'home_team': market.get('home_team'),
                'away_team': market.get('away_team'),
                'event_date': market.get('event_date'),
                'open_interest': market.get('open_interest'),
                'latest_price': {
                    'yes_bid': latest_price.get('yes_bid'),
                    'yes_ask': latest_price.get('yes_ask'),
                    'no_bid': latest_price.get('no_bid'),
                    'no_ask': latest_price.get('no_ask'),
                    'spread': latest_price.get('spread'),
                    'volume': latest_price.get('volume'),
                    'last_trade_price': latest_price.get('last_trade_price'),
                    'timestamp': latest_price.get('timestamp')
                },
                'created_at': market.get('created_at'),
                'updated_at': market.get('updated_at')
            }
            markets_data.append(market_data)
        
        session.close()
        
        return jsonify({
            'success': True,
            'count': len(markets_data),
            'markets': markets_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in /api/markets: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/collect', methods=['POST'])
def api_collect():
    """API endpoint to trigger data collection."""
    try:
        logger.info("Data collection triggered via API")
        
        # Initialize scraper
        scraper = KalshiScraper()
        
        # Check authentication
        status = scraper.get_collection_status()
        if not status.get('client_authenticated'):
            return jsonify({
                'success': False,
                'error': 'Failed to authenticate with Kalshi API',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        # Run collection
        collection_stats = scraper.run_collection()
        
        if not collection_stats:
            return jsonify({
                'success': False,
                'error': 'Collection failed - no statistics returned',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        # Return collection results
        return jsonify({
            'success': True,
            'message': 'Data collection completed successfully',
            'stats': collection_stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in /api/collect: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/status')
def api_status():
    """API endpoint returning system status."""
    try:
        session = get_db_session()
        
        # Get market summary
        summary = get_market_summary(session)
        
        # Get active markets count
        active_markets = get_active_markets(session, hours=1)
        
        session.close()
        
        return jsonify({
            'success': True,
            'status': {
                'database_connected': True,
                'total_markets': summary.get('total_markets', 0),
                'active_markets': len(active_markets),
                'platforms': summary.get('total_platforms', 0),
                'last_refresh': datetime.now().isoformat()
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in /api/status: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'timestamp': datetime.now().isoformat()
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'timestamp': datetime.now().isoformat()
    }), 500


if __name__ == '__main__':
    # Initialize the application
    if not initialize_app():
        logger.error("Failed to initialize application")
        sys.exit(1)
    
    # Run the Flask app
    logger.info("Starting Flask application on port 8000")
    app.run(host='0.0.0.0', port=8000, debug=True)
