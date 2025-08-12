"""Database initialization script for Sharp Agents."""

import sys
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.config import get_config
from utils.logger import get_logger
from database.models import Base, Market, MarketPrice, ArbitrageOpportunity, PaperTrade

logger = get_logger(__name__)


def create_tables(engine):
    """Create all database tables."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(engine)
    logger.info("All tables created successfully")


def drop_tables(engine):
    """Drop all database tables."""
    logger.info("Dropping existing database tables...")
    Base.metadata.drop_all(engine)
    logger.info("All tables dropped successfully")


def seed_data(session):
    """Seed the database with sample NFL markets."""
    logger.info("Seeding database with sample data...")
    
    # Sample NFL markets with proper datetime objects
    sample_markets = [
        {
            "platform": "polymarket",
            "market_id": "POLY_NFL_001",
            "event_date": datetime(2024, 1, 15, 20, 0, 0),
            "home_team": "Kansas City Chiefs",
            "away_team": "Buffalo Bills",
            "market_type": "moneyline"
        },
        {
            "platform": "polymarket",
            "market_id": "POLY_NFL_002",
            "event_date": datetime(2024, 1, 16, 20, 0, 0),
            "home_team": "San Francisco 49ers",
            "away_team": "Green Bay Packers",
            "market_type": "spread"
        },
        {
            "platform": "kalshi",
            "market_id": "KALSHI_NFL_001",
            "event_date": datetime(2024, 1, 15, 20, 0, 0),
            "home_team": "Kansas City Chiefs",
            "away_team": "Buffalo Bills",
            "market_type": "total"
        },
        {
            "platform": "kalshi",
            "market_id": "KALSHI_NFL_002",
            "event_date": datetime(2024, 1, 16, 20, 0, 0),
            "home_team": "San Francisco 49ers",
            "away_team": "Green Bay Packers",
            "market_type": "moneyline"
        },
        {
            "platform": "polymarket",
            "market_id": "POLY_NFL_003",
            "event_date": datetime(2024, 1, 17, 20, 0, 0),
            "home_team": "Baltimore Ravens",
            "away_team": "Houston Texans",
            "market_type": "spread"
        }
    ]
    
    # Create markets
    created_markets = []
    for market_data in sample_markets:
        market = Market(**market_data)
        session.add(market)
        created_markets.append(market)
    
    session.commit()
    logger.info(f"Created {len(created_markets)} sample markets")
    
    # Create sample market prices for the first market
    if created_markets:
        first_market = created_markets[0]
        sample_prices = [
            {
                "market_id": first_market.id,
                "yes_price": 0.65,
                "no_price": 0.35,
                "volume": 1000.0,
                "liquidity": 500.0
            },
            {
                "market_id": first_market.id,
                "yes_price": 0.68,
                "no_price": 0.32,
                "volume": 1200.0,
                "liquidity": 600.0
            }
        ]
        
        for price_data in sample_prices:
            price = MarketPrice(**price_data)
            session.add(price)
        
        session.commit()
        logger.info(f"Created {len(sample_prices)} sample price records")
    
    # Create a sample arbitrage opportunity
    if len(created_markets) >= 2:
        opportunity = ArbitrageOpportunity(
            platform_1="polymarket",
            platform_2="kalshi",
            market_1_id=created_markets[0].id,
            market_2_id=created_markets[2].id,  # Use the Kalshi market
            profit_percentage=2.5,
            status="active"
        )
        session.add(opportunity)
        session.commit()
        logger.info("Created 1 sample arbitrage opportunity")
    
    logger.info("Database seeding completed successfully")


def main():
    """Main function to initialize the database."""
    try:
        # Get configuration
        config = get_config()
        database_url = config.get_database_url()
        
        print(f"Initializing database: {database_url}")
        
        # Create database engine
        engine = create_engine(database_url, echo=True)
        
        # Create session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create session
        session = SessionLocal()
        
        try:
            # Drop existing tables
            drop_tables(engine)
            
            # Create new tables
            create_tables(engine)
            
            # Seed sample data
            seed_data(session)
            
            print("✅ Database initialization completed successfully!")
            print(f"📊 Created tables: {', '.join(Base.metadata.tables.keys())}")
            print("🌱 Sample data seeded with 5 NFL markets")
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
