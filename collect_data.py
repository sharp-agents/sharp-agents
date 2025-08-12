#!/usr/bin/env python3
"""
Data collection script for Kalshi NFL prediction markets.
Collects market data, saves to database, and provides comprehensive summary.
"""

import sys
import time
import logging
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

# Add project root to path
sys.path.append('.')

from scrapers.kalshi_scraper import KalshiScraper
from database.queries import get_market_summary, get_nfl_markets
from utils.config import get_config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class DataCollector:
    """Main data collection orchestrator."""
    
    def __init__(self):
        """Initialize the data collector."""
        self.config = get_config()
        self.logger = self._setup_logging()
        self.scraper = None
        self.session = None
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/data_collection.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    
    def _print_header(self):
        """Print collection header."""
        print("\n" + "="*80)
        print("🏈 KALSHI NFL MARKET DATA COLLECTION")
        print("="*80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Configuration: Safe Mode = {self.config.is_safe_mode()}")
        print(f"Request Timeout: {self.config.get_kalshi_request_timeout()}s")
        print("="*80 + "\n")
    
    def _print_progress(self, current: int, total: int, market_title: str = ""):
        """Print progress bar with market info."""
        if total == 0:
            return
        
        percentage = (current / total) * 100
        bar_length = 40
        filled_length = int(bar_length * current // total)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        # Clear line and print progress
        print(f"\r🔄 Progress: [{bar}] {percentage:5.1f}% ({current}/{total})", end='', flush=True)
        
        if market_title:
            print(f" | Processing: {market_title[:50]}{'...' if len(market_title) > 50 else ''}")
        else:
            print()
    
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
        
        # Print price information if available
        if 'latest_price' in market and market['latest_price']:
            price = market['latest_price']
            print(f"   💵  Latest Prices:")
            print(f"      Yes: Bid ${price.get('yes_bid', 'N/A'):.3f} | Ask ${price.get('yes_ask', 'N/A'):.3f}")
            print(f"      No:  Bid ${price.get('no_bid', 'N/A'):.3f} | Ask ${price.get('no_ask', 'N/A'):.3f}")
            print(f"      📈  Spread: ${price.get('spread', 'N/A'):.3f}")
            print(f"      📊  Volume: {price.get('volume', 'N/A')}")
            print(f"      🕒  Last Update: {price.get('timestamp', 'N/A')}")
    
    def _print_summary_stats(self, collection_stats: Dict[str, Any]):
        """Print collection summary statistics."""
        print("\n" + "="*80)
        print("📊 COLLECTION SUMMARY")
        print("="*80)
        
        # Basic stats
        print(f"⏱️  Total Processing Time: {collection_stats.get('processing_time_seconds', 0):.2f} seconds")
        print(f"🔍 Total Markets Found: {collection_stats.get('total_markets_found', 0)}")
        print(f"✅ Markets Processed: {collection_stats.get('markets_processed', 0)}")
        print(f"💾 Markets Saved: {collection_stats.get('markets_saved', 0)}")
        print(f"❌ Markets Failed: {collection_stats.get('markets_failed', 0)}")
        
        # Error summary
        errors = collection_stats.get('errors', [])
        if errors:
            print(f"\n⚠️  Errors Encountered: {len(errors)}")
            for i, error in enumerate(errors[:3]):  # Show first 3 errors
                print(f"   {i+1}. {error}")
            if len(errors) > 3:
                print(f"   ... and {len(errors) - 3} more errors")
        
        print("="*80)
    
    def _print_database_summary(self):
        """Print database summary statistics."""
        try:
            print("\n🗄️  DATABASE SUMMARY")
            print("-" * 40)
            
            # Get market summary
            summary = get_market_summary(self.session)
            
            print(f"📈 Total Markets: {summary.get('total_markets', 0)}")
            print(f"🌐 Platforms: {summary.get('total_platforms', 0)}")
            
            # Platform breakdown
            platform_counts = summary.get('platform_counts', {})
            for platform, count in platform_counts.items():
                print(f"   {platform.title()}: {count} markets")
            
            # Spread statistics
            spread_stats = summary.get('spread_statistics', {})
            if spread_stats:
                print(f"\n📊 Spread Statistics:")
                for platform, stats in spread_stats.items():
                    avg_spread = stats.get('avg_spread', 0)
                    print(f"   {platform.title()}: Avg ${avg_spread:.3f}")
            
            # Volume statistics
            volume_stats = summary.get('volume_statistics', {})
            if volume_stats:
                print(f"\n💰 Volume Statistics:")
                for platform, stats in volume_stats.items():
                    total_vol = stats.get('total_volume', 0)
                    print(f"   {platform.title()}: Total ${total_vol:,.0f}")
            
            # Recent activity
            recent_activity = summary.get('recent_activity', {})
            if recent_activity:
                print(f"\n🕒 Recent Activity (Last Hour):")
                for platform, count in recent_activity.items():
                    print(f"   {platform.title()}: {count} active markets")
            
        except Exception as e:
            print(f"❌ Error getting database summary: {e}")
    
    def _print_nfl_markets_summary(self):
        """Print NFL markets specific summary."""
        try:
            print("\n🏈 NFL MARKETS SUMMARY")
            print("-" * 40)
            
            # Get NFL markets
            nfl_markets = get_nfl_markets(self.session)
            
            if not nfl_markets:
                print("❌ No NFL markets found in database")
                return
            
            print(f"🏈 Total NFL Markets: {len(nfl_markets)}")
            
            # Group by platform
            platform_nfl = {}
            for market in nfl_markets:
                platform = market.get('platform', 'unknown')
                if platform not in platform_nfl:
                    platform_nfl[platform] = []
                platform_nfl[platform].append(market)
            
            for platform, markets in platform_nfl.items():
                print(f"\n   {platform.title()}: {len(markets)} markets")
                
                # Show top markets by volume
                markets_with_volume = []
                for m in markets:
                    latest_price = m.get('latest_price')
                    if latest_price and latest_price.get('volume') is not None:
                        markets_with_volume.append(m)
                
                if markets_with_volume:
                    top_market = max(markets_with_volume, 
                                   key=lambda x: x.get('latest_price', {}).get('volume', 0))
                    volume = top_market.get('latest_price', {}).get('volume', 0)
                    title = top_market.get('title', 'Unknown')
                    print(f"      Most Liquid: {title[:40]}{'...' if len(title) > 40 else ''}")
                    print(f"      Volume: ${volume:,.0f}")
                else:
                    print("      No volume data available")
            
            # Calculate average spread for NFL markets
            spreads = []
            for market in nfl_markets:
                latest_price = market.get('latest_price')
                if latest_price and latest_price.get('spread') is not None:
                    spreads.append(latest_price['spread'])
            
            if spreads:
                avg_spread = sum(spreads) / len(spreads)
                print(f"\n📈 Average NFL Market Spread: ${avg_spread:.3f}")
            else:
                print("\n📈 No spread data available for NFL markets")
            
        except Exception as e:
            print(f"❌ Error getting NFL markets summary: {e}")
    
    def _print_footer(self):
        """Print collection footer."""
        print("\n" + "="*80)
        print("🎯 DATA COLLECTION COMPLETE")
        print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
    
    def initialize(self) -> bool:
        """Initialize scraper and database connection."""
        try:
            print("🔧 Initializing data collector...")
            
            # Initialize scraper
            self.scraper = KalshiScraper()
            print("✅ KalshiScraper initialized")
            
            # Check scraper status
            status = self.scraper.get_collection_status()
            if not status.get('client_authenticated'):
                print("❌ Failed to authenticate with Kalshi API")
                return False
            
            print("✅ Kalshi API authentication successful")
            
            # Initialize database session
            database_url = self.config.get_database_url()
            engine = create_engine(database_url, echo=False)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            self.session = SessionLocal()
            print("✅ Database session established")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            print(f"❌ Initialization failed: {e}")
            return False
    
    def run_collection(self) -> bool:
        """Run the complete data collection process."""
        try:
            print("🚀 Starting NFL market data collection...")
            
            # Run collection
            collection_stats = self.scraper.run_collection()
            
            if not collection_stats:
                print("❌ Collection failed - no statistics returned")
                return False
            
            # Print collection summary
            self._print_summary_stats(collection_stats)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Collection failed: {e}")
            print(f"❌ Collection failed: {e}")
            return False
    
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
            if not self.run_collection():
                print("❌ Failed to run data collection")
                return False
            
            # Print database summary
            self._print_database_summary()
            
            # Print NFL markets summary
            self._print_nfl_markets_summary()
            
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
        finally:
            # Cleanup
            if self.session:
                self.session.close()


def main():
    """Main entry point."""
    print("🏈 Kalshi NFL Market Data Collector")
    print("Starting data collection process...\n")
    
    # Create and run collector
    collector = DataCollector()
    success = collector.run()
    
    if success:
        print("✅ Data collection completed successfully!")
        sys.exit(0)
    else:
        print("❌ Data collection failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
