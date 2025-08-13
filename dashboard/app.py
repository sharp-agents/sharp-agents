#!/usr/bin/env python3
"""Sharp Agents Dashboard - Sports Betting & Prediction Markets."""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
import logging

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask, render_template, jsonify, request, session
from flask_caching import Cache

# Import our scrapers
from scrapers.theodds import TheOddsScraper, TheOddsClient
from scrapers.kalshi_scraper import KalshiScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Configure caching
cache_config = {
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutes
}
cache = Cache(app, config=cache_config)

# Initialize scrapers
theodds_scraper = None
kalshi_scraper = None

def initialize_scrapers():
    """Initialize scrapers with proper error handling."""
    global theodds_scraper, kalshi_scraper
    
    # Ensure API key is set
    if not os.getenv('THEODDS_API_KEY'):
        os.environ['THEODDS_API_KEY'] = '7f368349a729ac04ca1251f6ecda8d81'
    
    try:
        # Initialize The Odds API scraper
        theodds_scraper = TheOddsScraper()
        logger.info("The Odds API scraper initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize The Odds API scraper: {e}")
        theodds_scraper = None
    
    try:
        # Initialize Kalshi scraper
        kalshi_scraper = KalshiScraper()
        logger.info("Kalshi scraper initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Kalshi scraper: {e}")
        kalshi_scraper = None

# Initialize scrapers on startup
initialize_scrapers()

@app.route('/')
def dashboard():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/sportsbook/odds')
@cache.cached(timeout=300)  # Cache for 5 minutes
def get_sportsbook_odds():
    """Get sportsbook odds from The Odds API."""
    try:
        if not theodds_scraper:
            return jsonify({'error': 'The Odds API scraper not available'}), 500
        
        # Get NFL games with odds
        nfl_games = theodds_scraper.client.get_nfl_games()
        
        if not nfl_games:
            return jsonify({'error': 'No NFL games found'}), 404
        
        # Process and format the data
        formatted_games = []
        for game in nfl_games[:20]:  # Limit to first 20 games for performance
            game_data = {
                'id': game.get('id'),
                'title': f"{game.get('away_team')} @ {game.get('home_team')}",
                'away_team': game.get('away_team'),
                'home_team': game.get('home_team'),
                'commence_time': game.get('commence_time'),
                'bookmakers': []
            }
            
            # Extract odds from each bookmaker
            for bookmaker in game.get('bookmakers', []):
                bm_data = {
                    'name': bookmaker.get('title'),
                    'key': bookmaker.get('key'),
                    'odds': {}
                }
                
                for market in bookmaker.get('markets', []):
                    if market.get('key') == 'h2h':  # Moneyline
                        for outcome in market.get('outcomes', []):
                            team = outcome.get('name')
                            odds = outcome.get('price')
                            bm_data['odds'][team] = odds
                
                if bm_data['odds']:
                    game_data['bookmakers'].append(bm_data)
            
            formatted_games.append(game_data)
        
        return jsonify({
            'success': True,
            'data': formatted_games,
            'total_games': len(nfl_games),
            'cached_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching sportsbook odds: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sportsbook/arbitrage')
@cache.cached(timeout=300)  # Cache for 5 minutes
def get_sportsbook_arbitrage():
    """Get arbitrage opportunities from sportsbook odds."""
    try:
        if not theodds_scraper:
            return jsonify({'error': 'The Odds API scraper not available'}), 500
        
        # Get arbitrage opportunities
        opportunities = theodds_scraper.get_arbitrage_opportunities(min_threshold=0.01)
        
        # Format opportunities for display
        formatted_opportunities = []
        for opp in opportunities[:10]:  # Limit to first 10
            opp_data = {
                'id': opp.get('market_id'),
                'title': opp.get('title'),
                'type': opp.get('arbitrage_type'),
                'home_team': opp.get('home_team'),
                'away_team': opp.get('away_team'),
                'commence_time': opp.get('commence_time'),
                'details': opp.get('arbitrage_details'),
                'recommended_bets': opp.get('recommended_bets')
            }
            formatted_opportunities.append(opp_data)
        
        return jsonify({
            'success': True,
            'data': formatted_opportunities,
            'total_opportunities': len(opportunities),
            'cached_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching arbitrage opportunities: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/kalshi/markets')
@cache.cached(timeout=300)  # Cache for 5 minutes
def get_kalshi_markets():
    """Get Kalshi prediction markets."""
    try:
        if not kalshi_scraper:
            return jsonify({'error': 'Kalshi scraper not available'}), 500
        
        # Get markets from Kalshi
        markets = kalshi_scraper.fetch_markets()
        
        if not markets:
            return jsonify({'error': 'No Kalshi markets found'}), 404
        
        # Format markets for display
        formatted_markets = []
        for market in markets[:20]:  # Limit to first 20
            market_data = {
                'id': market.get('id'),
                'title': market.get('title'),
                'ticker': market.get('ticker'),
                'event_date': market.get('event_date'),
                'home_team': market.get('home_team'),
                'away_team': market.get('away_team'),
                'yes_bid': market.get('yes_bid'),
                'yes_ask': market.get('yes_ask'),
                'no_bid': market.get('no_bid'),
                'no_ask': market.get('no_ask'),
                'volume': market.get('volume'),
                'open_interest': market.get('open_interest'),
                'last_price': market.get('last_price')
            }
            formatted_markets.append(market_data)
        
        return jsonify({
            'success': True,
            'data': formatted_markets,
            'total_markets': len(markets),
            'cached_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching Kalshi markets: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/combined/opportunities')
@cache.cached(timeout=300)  # Cache for 5 minutes
def get_combined_opportunities():
    """Get combined opportunities from both platforms."""
    try:
        opportunities = {
            'sportsbook': [],
            'kalshi': [],
            'cross_platform': []
        }
        
        # Get sportsbook opportunities
        if theodds_scraper:
            try:
                sportsbook_opps = theodds_scraper.get_arbitrage_opportunities(min_threshold=0.01)
                opportunities['sportsbook'] = sportsbook_opps[:5]
            except Exception as e:
                logger.error(f"Error getting sportsbook opportunities: {e}")
        
        # Get Kalshi opportunities (markets with high volume/interest)
        if kalshi_scraper:
            try:
                kalshi_markets = kalshi_scraper.fetch_markets()
                # Filter for high-volume markets
                high_volume_markets = [
                    m for m in kalshi_markets 
                    if m.get('volume', 0) > 1000 or m.get('open_interest', 0) > 5000
                ]
                opportunities['kalshi'] = high_volume_markets[:5]
            except Exception as e:
                logger.error(f"Error getting Kalshi opportunities: {e}")
        
        # Cross-platform analysis could be added here
        # For now, we'll identify markets that exist on both platforms
        
        return jsonify({
            'success': True,
            'data': opportunities,
            'cached_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting combined opportunities: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def get_status():
    """Get system status and API health."""
    status = {
        'timestamp': datetime.now().isoformat(),
        'theodds_api': {
            'available': theodds_scraper is not None,
            'status': 'healthy' if theodds_scraper else 'unavailable'
        },
        'kalshi': {
            'available': kalshi_scraper is not None,
            'status': 'healthy' if kalshi_scraper else 'unavailable'
        },
        'cache': {
            'type': 'simple',
            'timeout': 300
        }
    }
    
    return jsonify(status)

@app.route('/api/refresh')
def refresh_data():
    """Manually refresh cached data."""
    try:
        # Clear cache
        cache.clear()
        
        # Re-initialize scrapers
        initialize_scrapers()
        
        return jsonify({
            'success': True,
            'message': 'Cache cleared and scrapers refreshed',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    # Set environment variables if not already set
    if not os.getenv('THEODDS_API_KEY'):
        os.environ['THEODDS_API_KEY'] = '7f368349a729ac04ca1251f6ecda8d81'
    
    # Run the dashboard on port 5001 to avoid AirPlay conflicts
    app.run(debug=True, host='0.0.0.0', port=5001)
