#!/usr/bin/env python3
"""
Simplified data collection script for Kalshi NFL prediction markets.
Collects market data without orderbook calls (Elections API limitation).
"""

import sys
import logging
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
sys.path.append('.')

from scrapers.kalshi_scraper import KalshiScraper
from utils.config import get_config


class SimpleDataCollector:
    """Simplified data collector that focuses on market data without orderbooks."""
    
    def __init__(self):
        """Initialize the simple data collector."""
        self.config = get_config()
        self.logger = self._setup_logging()
        self.scraper = None
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/simple_data_collection.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    
    def _print_header(self):
        """Print collection header."""
        print("\n" + "="*80)
        print("🏈 KALSHI NFL MARKET DATA COLLECTION (SIMPLE)")
        print("="*80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Configuration: Safe Mode = {self.config.is_safe_mode()}")
        print(f"Request Timeout: {self.config.get_kalshi_request_timeout()}s")
        print("Note: Elections API - collecting market data only (no orderbooks)")
        print("="*80 + "\n")
    
    def _print_market_info(self, market: Dict[str, Any], index: int):
        """Print detailed market information."""
        print(f"\n📊 Market {index + 1}:")
        print(f"   🏷️  Title: {market.get('title', 'Unknown')}")
        print(f"   🆔  Ticker: {market.get('ticker', 'Unknown')}")
        print(f"   🏟️  Event: {market.get('event_ticker', 'N/A')}")
        print(f"   🏠  Home Team: {market.get('home_team', 'N/A')}")
        print(f"   ✈️  Away Team: {market.get('away_team', 'N/A')}")
        print(f"   📅  Event Date: {market.get('event_date', 'N/A')}")
        print(f"   💰  Open Interest: {market.get('open_interest', 'N/A')}")
        print(f"   📊  Market Type: {market.get('market_type', 'N/A')}")
    
    def _print_summary_stats(self, markets: List[Dict[str, Any]], processing_time: float):
        """Print collection summary statistics."""
        print("\n" + "="*80)
        print("📊 COLLECTION SUMMARY")
        print("="*80)
        
        # Basic stats
        print(f"⏱️  Total Processing Time: {processing_time:.2f} seconds")
        print(f"🔍 Total Markets Found: {len(markets)}")
        
        # Market type breakdown
        market_types = {}
        for market in markets:
            market_type = market.get('market_type', 'unknown')
            market_types[market_type] = market_types.get(market_type, 0) + 1
        
        print(f"\n📊 Market Type Breakdown:")
        for market_type, count in market_types.items():
            print(f"   {market_type.title()}: {count} markets")
        
        # Team analysis
        teams_found = set()
        for market in markets:
            if market.get('home_team'):
                teams_found.add(market['home_team'])
            if market.get('away_team'):
                teams_found.add(market['away_team'])
        
        print(f"\n🏈 Teams Found: {len(teams_found)}")
        if teams_found:
            print("   Top teams:")
            for team in sorted(list(teams_found))[:10]:  # Show first 10
                print(f"      {team}")
            if len(teams_found) > 10:
                print(f"      ... and {len(teams_found) - 10} more")
        
        print("="*80)
    
    def _print_footer(self):
        """Print collection footer."""
        print("\n" + "="*80)
        print("🎯 SIMPLE DATA COLLECTION COMPLETE")
        print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
    
    def initialize(self) -> bool:
        """Initialize scraper."""
        try:
            print("🔧 Initializing simple data collector...")
            
            # Initialize scraper
            self.scraper = KalshiScraper()
            print("✅ KalshiScraper initialized")
            
            # Check scraper status
            status = self.scraper.get_collection_status()
            if not status.get('client_authenticated'):
                print("❌ Failed to authenticate with Kalshi API")
                return False
            
            print("✅ Kalshi API authentication successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            print(f"❌ Initialization failed: {e}")
            return False
    
    def run_collection(self) -> List[Dict[str, Any]]:
        """Run the simplified data collection process."""
        try:
            print("🚀 Starting NFL market data collection (markets only)...")
            
            # Fetch markets only (no orderbook calls)
            markets = self.scraper.fetch_markets()
            
            if not markets:
                print("❌ No markets found")
                return []
            
            print(f"✅ Found {len(markets)} NFL-related markets")
            
            # Print each market found
            for i, market in enumerate(markets):
                self._print_market_info(market, i)
                
                # Show progress every 10 markets
                if (i + 1) % 10 == 0:
                    print(f"\n🔄 Progress: {i+1}/{len(markets)} markets processed")
            
            return markets
            
        except Exception as e:
            self.logger.error(f"Collection failed: {e}")
            print(f"❌ Collection failed: {e}")
            return []
    
    def run(self):
        """Main execution method."""
        try:
            # Print header
            self._print_header()
            
            # Initialize
            if not self.initialize():
                print("❌ Failed to initialize data collector")
                return False
            
            # Run collection
            start_time = datetime.now()
            markets = self.run_collection()
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            if not markets:
                print("❌ No markets collected")
                return False
            
            # Print summary
            self._print_summary_stats(markets, processing_time)
            
            # Print footer
            self._print_footer()
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Data collection interrupted by user")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            print(f"❌ Unexpected error: {e}")
            return False


def main():
    """Main entry point."""
    print("🏈 Kalshi NFL Market Data Collector (Simple)")
    print("Starting simplified data collection process...\n")
    
    # Create and run collector
    collector = SimpleDataCollector()
    success = collector.run()
    
    if success:
        print("✅ Simple data collection completed successfully!")
        sys.exit(0)
    else:
        print("❌ Simple data collection failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
