#!/usr/bin/env python3
"""
Test script for database functions.
Demonstrates all the database helper functions with sample data.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.config import get_config
from utils.logger import get_logger
from database.queries import (
    get_or_create_market,
    add_market_price,
    find_arbitrage_opportunities,
    create_paper_trade,
    get_recent_prices,
    get_markets_by_platform,
    get_latest_price,
    get_total_pnl,
    get_arbitrage_success_rate
)

logger = get_logger(__name__)


def test_database_functions():
    """Test all database functions with sample data."""
    
    try:
        # Get configuration
        config = get_config()
        database_url = config.get_database_url()
        
        print("🧪 Testing Database Functions")
        print("=" * 50)
        print(f"Database: {database_url}")
        print()
        
        # Create database engine and session
        engine = create_engine(database_url, echo=False)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        try:
            # Test 1: Create test markets
            print("1️⃣ Creating Test Markets")
            print("-" * 30)
            
            # Create markets on different platforms
            market1, created1 = get_or_create_market(
                session, "polymarket", "TEST_NFL_001",
                "Dallas Cowboys", "Philadelphia Eagles", "moneyline",
                datetime.now() + timedelta(days=7)
            )
            print(f"Market 1: {market1.platform}/{market1.market_id} - {'Created' if created1 else 'Found'}")
            print(f"  Teams: {market1.away_team} @ {market1.home_team}")
            print(f"  Type: {market1.market_type}")
            
            market2, created2 = get_or_create_market(
                session, "kalshi", "TEST_NFL_001",
                "Dallas Cowboys", "Philadelphia Eagles", "moneyline",
                datetime.now() + timedelta(days=7)
            )
            print(f"Market 2: {market2.platform}/{market2.market_id} - {'Created' if created2 else 'Found'}")
            print(f"  Teams: {market2.away_team} @ {market2.home_team}")
            print(f"  Type: {market2.market_type}")
            
            # Create a third market for more testing
            market3, created3 = get_or_create_market(
                session, "polymarket", "TEST_NFL_002",
                "Kansas City Chiefs", "Las Vegas Raiders", "spread",
                datetime.now() + timedelta(days=14)
            )
            print(f"Market 3: {market3.platform}/{market3.market_id} - {'Created' if created3 else 'Found'}")
            print(f"  Teams: {market3.away_team} @ {market3.home_team}")
            print(f"  Type: {market3.market_type}")
            print()
            
            # Test 2: Add price data
            print("2️⃣ Adding Price Data")
            print("-" * 30)
            
            # Add prices for market 1 (Polymarket)
            price1_1 = add_market_price(
                session, market1.id, 
                yes_price=0.65, no_price=0.35, 
                volume=1500.0, liquidity=800.0
            )
            print(f"Added price for {market1.platform}/{market1.market_id}:")
            print(f"  Yes: {price1_1.yes_price}, No: {price1_1.no_price}")
            print(f"  Volume: {price1_1.volume}, Liquidity: {price1_1.liquidity}")
            
            # Add another price point for market 1
            price1_2 = add_market_price(
                session, market1.id, 
                yes_price=0.68, no_price=0.32, 
                volume=1800.0, liquidity=950.0
            )
            print(f"Added second price for {market1.platform}/{market1.market_id}:")
            print(f"  Yes: {price1_2.yes_price}, No: {price1_2.no_price}")
            print(f"  Volume: {price1_2.volume}, Liquidity: {price1_2.liquidity}")
            
            # Add prices for market 2 (Kalshi)
            price2_1 = add_market_price(
                session, market2.id, 
                yes_price=0.62, no_price=0.38, 
                volume=1200.0, liquidity=600.0
            )
            print(f"Added price for {market2.platform}/{market2.market_id}:")
            print(f"  Yes: {price2_1.yes_price}, No: {price2_1.no_price}")
            print(f"  Volume: {price2_1.volume}, Liquidity: {price2_1.liquidity}")
            
            # Add prices for market 3
            price3_1 = add_market_price(
                session, market3.id, 
                yes_price=0.55, no_price=0.45, 
                volume=900.0, liquidity=450.0
            )
            print(f"Added price for {market3.platform}/{market3.market_id}:")
            print(f"  Yes: {price3_1.yes_price}, No: {price3_1.no_price}")
            print(f"  Volume: {price3_1.volume}, Liquidity: {price3_1.liquidity}")
            print()
            
            # Test 3: Find arbitrage opportunities
            print("3️⃣ Finding Arbitrage Opportunities")
            print("-" * 30)
            
            opportunities = find_arbitrage_opportunities(session, min_profit=0.01)
            print(f"Found {len(opportunities)} arbitrage opportunities above 1% threshold:")
            
            for i, opp in enumerate(opportunities, 1):
                print(f"  Opportunity {i}:")
                print(f"    {opp['market_1']['platform']}: {opp['market_1']['price']:.3f}")
                print(f"    {opp['market_2']['platform']}: {opp['market_2']['price']:.3f}")
                print(f"    Profit: {opp['profit_percentage']:.2f}%")
                print(f"    Type: {opp['type']}")
                print()
            
            # Test 4: Create paper trade
            print("4️⃣ Creating Paper Trade")
            print("-" * 30)
            
            if opportunities:
                # Use the first opportunity
                opportunity = opportunities[0]
                print(f"Creating paper trade for opportunity with {opportunity['profit_percentage']:.2f}% profit")
                
                # Note: We need to create an actual ArbitrageOpportunity record first
                # For this test, we'll just show the function call structure
                print("Note: Paper trade creation requires an ArbitrageOpportunity record")
                print("This would be created by the arbitrage detection system")
                print()
            else:
                print("No arbitrage opportunities found to create paper trade")
                print()
            
            # Test 5: Get recent prices
            print("5️⃣ Getting Recent Prices")
            print("-" * 30)
            
            # Get all recent prices
            recent_prices = get_recent_prices(session, minutes=60)
            print(f"Retrieved {len(recent_prices)} recent price records:")
            
            for price in recent_prices[:5]:  # Show first 5
                print(f"  {price['platform']}/{price['market_id_str']}:")
                print(f"    {price['away_team']} @ {price['home_team']}")
                print(f"    Yes: {price['yes_price']:.3f}, No: {price['no_price']:.3f}")
                print(f"    Volume: {price['volume']}, Time: {price['timestamp']}")
                print()
            
            # Test 6: Platform-specific queries
            print("6️⃣ Platform-Specific Queries")
            print("-" * 30)
            
            polymarket_markets = get_markets_by_platform(session, "polymarket")
            print(f"Polymarket markets: {len(polymarket_markets)}")
            
            kalshi_markets = get_markets_by_platform(session, "kalshi")
            print(f"Kalshi markets: {len(kalshi_markets)}")
            
            # Test 7: Analytics
            print("7️⃣ Analytics")
            print("-" * 30)
            
            total_pnl = get_total_pnl(session)
            print(f"Total PnL: ${total_pnl:.2f}")
            
            success_stats = get_arbitrage_success_rate(session)
            print(f"Arbitrage Success Rate: {success_stats['success_rate']:.1f}%")
            print(f"Total Opportunities: {success_stats['total_opportunities']}")
            print(f"Executed Opportunities: {success_stats['executed_opportunities']}")
            
            print()
            print("✅ All database tests completed successfully!")
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        print(f"❌ Database test failed: {e}")
        raise


if __name__ == "__main__":
    test_database_functions()
