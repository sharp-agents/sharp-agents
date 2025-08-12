"""Kalshi scraper for collecting NFL prediction market data."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base import BaseScraper
from .kalshi import KalshiClient


class KalshiScraper(BaseScraper):
    """Kalshi scraper that inherits from BaseScraper for NFL market data collection."""
    
    def __init__(self):
        """Initialize Kalshi scraper with client."""
        super().__init__("kalshi")
        self.client = KalshiClient()
        self.logger.info("KalshiScraper initialized")
        
        # NFL-related keywords for filtering
        self.nfl_keywords = [
            'NFL', 'FOOTBALL', 'SUPER BOWL', 'PLAYOFFS', 'REGULAR SEASON',
            'DIVISION', 'CONFERENCE', 'WILDCARD', 'CHAMPIONSHIP',
            'PATRIOTS', 'BILLS', 'DOLPHINS', 'JETS',  # AFC East
            'BENGALS', 'BROWNS', 'RAVENS', 'STEELERS',  # AFC North
            'COLTS', 'JAGUARS', 'TEXANS', 'TITANS',  # AFC South
            'BRONCOS', 'CHIEFS', 'RAIDERS', 'CHARGERS',  # AFC West
            'COWBOYS', 'EAGLES', 'GIANTS', 'COMMANDERS',  # NFC East
            'BEARS', 'LIONS', 'PACKERS', 'VIKINGS',  # NFC North
            'FALCONS', 'PANTHERS', 'SAINTS', 'BUCCANEERS',  # NFC South
            'CARDINALS', 'RAMS', '49ERS', 'SEAHAWKS'  # NFC West
        ]
    
    def _is_nfl_market(self, market: Dict[str, Any]) -> bool:
        """Check if a market is NFL-related based on title or event ticker."""
        try:
            title = market.get('title', '').upper()
            event_ticker = market.get('event_ticker', '').upper()
            
            # Check if any NFL keyword is in the title
            if any(keyword in title for keyword in self.nfl_keywords):
                return True
            
            # Check if event ticker contains NFL
            if 'NFL' in event_ticker:
                return True
            
            # Check for common NFL patterns in title
            nfl_patterns = [
                'NFL:', 'FOOTBALL:', 'SUPER BOWL', 'PLAYOFFS',
                'WEEK', 'GAME', 'VS', 'AT', 'HOME', 'AWAY'
            ]
            
            if any(pattern in title for pattern in nfl_patterns):
                return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Error checking if market is NFL-related: {e}")
            return False
    
    def fetch_markets(self) -> List[Dict[str, Any]]:
        """Fetch all open NFL markets from Kalshi.
        
        Returns:
            List of NFL market data dictionaries
        """
        try:
            self.logger.info("Starting to fetch NFL markets from Kalshi...")
            
            # Ensure client is authenticated
            if not self.client._ensure_auth():
                self.logger.error("Failed to authenticate with Kalshi API")
                return []
            
            # Get NFL game markets specifically from the KXNFLGAME series
            nfl_game_markets = self.client.request('GET', '/markets?series_ticker=KXNFLGAME&status=open')
            if not nfl_game_markets or 'markets' not in nfl_game_markets:
                self.logger.warning("No NFL game markets found")
                return []
            
            nfl_markets = nfl_game_markets['markets']
            self.logger.info(f"Found {len(nfl_markets)} NFL game markets from KXNFLGAME series")
            
            # Log some examples of found markets
            if nfl_markets:
                for i, market in enumerate(nfl_markets[:3]):
                    title = market.get('title', 'Unknown')
                    ticker = market.get('ticker', 'Unknown')
                    self.logger.debug(f"NFL Market {i+1}: {title} ({ticker})")
            
            return nfl_markets
            
        except Exception as e:
            self.logger.error(f"Error fetching markets: {e}")
            return []
    
    def fetch_prices(self, market_ticker: str) -> Optional[Dict[str, Any]]:
        """Fetch orderbook and prices for a specific market.
        
        Args:
            market_ticker: Market ticker/ID
            
        Returns:
            Orderbook data with bid/ask prices or None if error
        """
        try:
            self.logger.debug(f"Fetching prices for market: {market_ticker}")
            
            # Ensure client is authenticated
            if not self.client._ensure_auth():
                self.logger.error("Failed to authenticate with Kalshi API")
                return None
            
            # Get orderbook for the market
            orderbook = self.client.get_orderbook(market_ticker)
            if not orderbook:
                self.logger.warning(f"No orderbook data found for {market_ticker}")
                return None
            
            # Extract and structure price data
            price_data = {
                'market_ticker': market_ticker,
                'timestamp': datetime.now(),
                'orderbook': orderbook,
                'yes_bid': 0.0,
                'yes_ask': 0.0,
                'no_bid': 0.0,
                'no_ask': 0.0
            }
            
            # Try to extract bid/ask prices from orderbook
            try:
                # Handle different orderbook formats
                if 'orderbook' in orderbook and 'yes' in orderbook['orderbook'] and 'no' in orderbook['orderbook']:
                    # New Kalshi API format with nested orderbook
                    yes_orders = orderbook['orderbook']['yes']
                    no_orders = orderbook['orderbook']['no']
                    
                    if yes_orders:
                        # Best bid for yes is highest price (first element after sorting by price desc)
                        yes_orders_sorted = sorted(yes_orders, key=lambda x: x[0], reverse=True)
                        price_data['yes_bid'] = float(yes_orders_sorted[0][0]) / 100.0  # Convert cents to dollars
                        
                        # Best ask for yes is lowest price (first element after sorting by price asc)
                        yes_orders_sorted_asc = sorted(yes_orders, key=lambda x: x[0])
                        price_data['yes_ask'] = float(yes_orders_sorted_asc[0][0]) / 100.0  # Convert cents to dollars
                    
                    if no_orders:
                        # Best bid for no is highest price
                        no_orders_sorted = sorted(no_orders, key=lambda x: x[0], reverse=True)
                        price_data['no_bid'] = float(no_orders_sorted[0][0]) / 100.0  # Convert cents to dollars
                        
                        # Best ask for no is lowest price
                        no_orders_sorted_asc = sorted(no_orders, key=lambda x: x[0])
                        price_data['no_ask'] = float(no_orders_sorted_asc[0][0]) / 100.0  # Convert cents to dollars
                
                elif 'yes' in orderbook and 'no' in orderbook:
                    # Legacy binary market format
                    yes_data = orderbook.get('yes', {})
                    no_data = orderbook.get('no', {})
                    
                    # Extract best bid/ask for yes
                    if 'bids' in yes_data and yes_data['bids']:
                        price_data['yes_bid'] = float(yes_data['bids'][0].get('price', 0))
                    if 'asks' in yes_data and yes_data['asks']:
                        price_data['yes_ask'] = float(yes_data['asks'][0].get('price', 0))
                    
                    # Extract best bid/ask for no
                    if 'bids' in no_data and no_data['bids']:
                        price_data['no_bid'] = float(no_data['bids'][0].get('price', 0))
                    if 'asks' in no_data and no_data['asks']:
                        price_data['no_ask'] = float(no_data['asks'][0].get('price', 0))
                
                elif 'bids' in orderbook and 'asks' in orderbook:
                    # Simple orderbook format
                    if orderbook['bids']:
                        price_data['yes_bid'] = float(orderbook['bids'][0].get('price', 0))
                    if orderbook['asks']:
                        price_data['yes_ask'] = float(orderbook['asks'][0].get('price', 0))
                        # For binary markets, no_ask = 1 - yes_ask
                        price_data['no_ask'] = 1.0 - price_data['yes_ask']
                        price_data['no_bid'] = 1.0 - price_data['yes_bid']
                
                self.logger.debug(f"Extracted prices for {market_ticker}: Yes({price_data['yes_bid']:.3f}/{price_data['yes_ask']:.3f}) No({price_data['no_bid']:.3f}/{price_data['no_ask']:.3f})")
                
            except Exception as e:
                self.logger.warning(f"Error extracting prices from orderbook for {market_ticker}: {e}")
            
            return price_data
            
        except Exception as e:
            self.logger.error(f"Error fetching prices for {market_ticker}: {e}")
            return None
    
    def run_collection(self) -> Dict[str, Any]:
        """Run complete NFL market data collection process.
        
        Returns:
            Dictionary with collection summary statistics
        """
        start_time = datetime.now()
        self.logger.info("Starting NFL market data collection...")
        
        collection_stats = {
            'start_time': start_time,
            'end_time': None,
            'total_markets_found': 0,
            'markets_processed': 0,
            'markets_saved': 0,
            'markets_failed': 0,
            'errors': [],
            'processing_time_seconds': 0
        }
        
        try:
            # Step 1: Fetch all NFL markets
            self.logger.info("Step 1: Fetching NFL markets...")
            nfl_markets = self.fetch_markets()
            collection_stats['total_markets_found'] = len(nfl_markets)
            
            if not nfl_markets:
                self.logger.warning("No NFL markets found to process")
                return collection_stats
            
            # Step 2: Process each market
            self.logger.info(f"Step 2: Processing {len(nfl_markets)} NFL markets...")
            
            for i, market in enumerate(nfl_markets):
                try:
                    market_id = market.get('ticker') or market.get('id') or f"market_{i}"
                    self.logger.info(f"Processing market {i+1}/{len(nfl_markets)}: {market_id}")
                    
                    # Fetch orderbook/prices
                    orderbook = self.fetch_prices(market_id)
                    if not orderbook:
                        self.logger.warning(f"No orderbook data for {market_id}, skipping...")
                        collection_stats['markets_failed'] += 1
                        continue
                    
                    # Normalize market data
                    normalized_data = self.normalize_market_data(
                        self.platform_name, 
                        market, 
                        orderbook
                    )
                    
                    if not normalized_data:
                        self.logger.warning(f"Failed to normalize data for {market_id}")
                        collection_stats['markets_failed'] += 1
                        continue
                    
                    # Save to database
                    save_success = self.save_to_db(normalized_data)
                    if save_success:
                        collection_stats['markets_saved'] += 1
                        self.logger.info(f"Successfully saved market {market_id}")
                    else:
                        self.logger.warning(f"Failed to save market {market_id}")
                        collection_stats['markets_failed'] += 1
                    
                    collection_stats['markets_processed'] += 1
                    
                    # Log progress every 10 markets
                    if (i + 1) % 10 == 0:
                        self.logger.info(f"Progress: {i+1}/{len(nfl_markets)} markets processed")
                
                except Exception as e:
                    error_msg = f"Error processing market {market.get('ticker', 'unknown')}: {e}"
                    self.logger.error(error_msg)
                    collection_stats['errors'].append(error_msg)
                    collection_stats['markets_failed'] += 1
                    continue
            
            # Step 3: Collection complete
            end_time = datetime.now()
            collection_stats['end_time'] = end_time
            collection_stats['processing_time_seconds'] = (end_time - start_time).total_seconds()
            
            # Log final summary
            self.logger.info("NFL market collection completed!")
            self.logger.info(f"Summary: {collection_stats['markets_processed']} processed, "
                           f"{collection_stats['markets_saved']} saved, "
                           f"{collection_stats['markets_failed']} failed")
            self.logger.info(f"Processing time: {collection_stats['processing_time_seconds']:.2f} seconds")
            
            if collection_stats['errors']:
                self.logger.warning(f"Encountered {len(collection_stats['errors'])} errors during collection")
                for error in collection_stats['errors'][:5]:  # Log first 5 errors
                    self.logger.warning(f"Error: {error}")
            
            return collection_stats
            
        except Exception as e:
            error_msg = f"Fatal error during collection: {e}"
            self.logger.error(error_msg)
            collection_stats['errors'].append(error_msg)
            collection_stats['end_time'] = datetime.now()
            collection_stats['processing_time_seconds'] = (collection_stats['end_time'] - start_time).total_seconds()
            return collection_stats
    
    def get_collection_status(self) -> Dict[str, Any]:
        """Get current status of the scraper and client."""
        try:
            status = {
                'platform': self.platform_name,
                'client_authenticated': self.client._ensure_auth(),
                'last_collection': getattr(self, '_last_collection_time', None),
                'client_status': {
                    'base_url': self.client.base_url,
                    'has_api_key': bool(self.client.api_key),
                    'has_api_secret': bool(self.client.api_secret),
                    'safe_mode': self.client.safe_mode
                }
            }
            return status
        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
            return {'error': str(e)}


def test_kalshi_scraper():
    """Test function for KalshiScraper functionality."""
    print("Testing KalshiScraper...")
    
    # Create scraper
    scraper = KalshiScraper()
    
    # Check status
    status = scraper.get_collection_status()
    print(f"Scraper Status: {status}")
    
    # Test market fetching
    print("\nTesting market fetching...")
    markets = scraper.fetch_markets()
    print(f"Found {len(markets)} NFL markets")
    
    if markets:
        # Test price fetching for first market
        first_market = markets[0]
        market_id = first_market.get('ticker') or first_market.get('id')
        print(f"\nTesting price fetching for market: {market_id}")
        
        prices = scraper.fetch_prices(market_id)
        if prices:
            print(f"Price data: {prices}")
        else:
            print("No price data found")
    
    # Test data normalization
    if markets:
        print("\nTesting data normalization...")
        normalized = scraper.normalize_market_data(
            scraper.platform_name,
            markets[0],
            {'bids': [], 'asks': []}  # Empty orderbook for testing
        )
        print(f"Normalized data keys: {list(normalized.keys())}")
        print(f"Title: {normalized.get('title')}")
        print(f"Home team: {normalized.get('home_team')}")
        print(f"Away team: {normalized.get('away_team')}")


if __name__ == "__main__":
    # Setup basic logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    test_kalshi_scraper()
