"""Flask API routes for the application."""

from flask import Flask, jsonify, request
from database.queries import (
    get_markets_by_source, 
    get_market_by_id, 
    get_active_arbitrage_opportunities
)
from analysis.arbitrage import ArbitrageAnalyzer
from utils.logger import get_logger

logger = get_logger(__name__)


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    @app.route('/')
    def health_check():
        """Health check endpoint."""
        return jsonify({"status": "healthy", "message": "Sharp Agents API is running"})
    
    @app.route('/api/markets', methods=['GET'])
    def get_markets():
        """Get all markets with optional source filter."""
        source = request.args.get('source')
        # TODO: Implement actual database session
        # markets = get_markets_by_source(session, source) if source else get_all_markets(session)
        markets = []  # Placeholder
        return jsonify({"markets": markets})
    
    @app.route('/api/markets/<market_id>', methods=['GET'])
    def get_market(market_id):
        """Get a specific market by ID."""
        # TODO: Implement actual database session
        # market = get_market_by_id(session, market_id)
        market = None  # Placeholder
        if market:
            return jsonify({"market": market})
        return jsonify({"error": "Market not found"}), 404
    
    @app.route('/api/arbitrage', methods=['GET'])
    def get_arbitrage():
        """Get arbitrage opportunities."""
        # TODO: Implement actual database session
        # opportunities = get_active_arbitrage_opportunities(session)
        opportunities = []  # Placeholder
        return jsonify({"arbitrage_opportunities": opportunities})
    
    @app.route('/api/analysis/sentiment', methods=['POST'])
    def analyze_sentiment():
        """Analyze market sentiment using AI."""
        data = request.get_json()
        market_id = data.get('market_id')
        
        if not market_id:
            return jsonify({"error": "market_id is required"}), 400
        
        # TODO: Implement actual analysis
        return jsonify({"message": "Sentiment analysis endpoint"})
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({"error": "Internal server error"}), 500
    
    return app
