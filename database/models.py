"""Database models for the application."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Market(Base):
    """Prediction market model."""
    
    __tablename__ = "markets"
    
    id = Column(Integer, primary_key=True)
    platform = Column(String(50), nullable=False)  # 'polymarket' or 'kalshi'
    market_id = Column(String(100), nullable=False)  # unique platform ID
    ticker = Column(String(100), nullable=True)  # Kalshi's market ticker
    title = Column(String(500), nullable=True)  # Full market title
    event_ticker = Column(String(100), nullable=True)  # Event identifier
    event_date = Column(DateTime, nullable=True)
    home_team = Column(String(100), nullable=True)
    away_team = Column(String(100), nullable=True)
    market_type = Column(String(50), nullable=False)  # 'binary', 'categorical', 'scalar'
    open_interest = Column(Float, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Add unique constraint on (platform, ticker)
    __table_args__ = (
        UniqueConstraint('platform', 'ticker', name='uq_platform_ticker'),
    )
    
    # Relationships
    prices = relationship("MarketPrice", back_populates="market", cascade="all, delete-orphan")
    
    def get_latest_price(self):
        """Get the most recent price data for this market."""
        if self.prices:
            return max(self.prices, key=lambda p: p.timestamp)
        return None
    
    def is_nfl_market(self):
        """Check if this market is NFL-related based on title or teams."""
        if self.home_team or self.away_team:
            return True
        if self.title and any(keyword in self.title.upper() for keyword in ['NFL', 'FOOTBALL', 'SUPER BOWL']):
            return True
        return False
    
    def validate_market_data(self):
        """Validate that required market data is present."""
        required_fields = ['platform', 'market_type']
        missing_fields = [field for field in required_fields if not getattr(self, field)]
        
        if missing_fields:
            return False, f"Missing required fields: {missing_fields}"
        
        # Validate market type
        valid_types = ['binary', 'categorical', 'scalar']
        if self.market_type not in valid_types:
            return False, f"Invalid market type: {self.market_type}. Must be one of {valid_types}"
        
        return True, "Market data is valid"
    arbitrage_opportunities_1 = relationship(
        "ArbitrageOpportunity", 
        foreign_keys="ArbitrageOpportunity.market_1_id",
        back_populates="market_1"
    )
    arbitrage_opportunities_2 = relationship(
        "ArbitrageOpportunity", 
        foreign_keys="ArbitrageOpportunity.market_2_id",
        back_populates="market_2"
    )
    
    def __repr__(self):
        return f"<Market(id={self.id}, platform='{self.platform}', ticker='{self.ticker}', title='{self.title}')>"


class MarketPrice(Base):
    """Market price data model."""
    
    __tablename__ = "market_prices"
    
    id = Column(Integer, primary_key=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    timestamp = Column(DateTime, default=func.now())
    yes_bid = Column(Float, nullable=True)  # Best bid for yes outcome
    yes_ask = Column(Float, nullable=True)  # Best ask for yes outcome
    no_bid = Column(Float, nullable=True)   # Best bid for no outcome
    no_ask = Column(Float, nullable=True)   # Best ask for no outcome
    spread = Column(Float, nullable=True)    # Calculated as ask - bid
    last_trade_price = Column(Float, nullable=True)  # Last trade price
    volume = Column(Float, nullable=True)
    liquidity = Column(Float, nullable=True)
    
    # Legacy fields for backward compatibility
    yes_price = Column(Float, nullable=True)  # for binary markets (deprecated)
    no_price = Column(Float, nullable=True)   # for binary markets (deprecated)
    
    # Relationships
    market = relationship("Market", back_populates="prices")
    
    def calculate_spread(self):
        """Calculate and update the spread (ask - bid) for yes outcome."""
        if self.yes_ask is not None and self.yes_bid is not None:
            self.spread = self.yes_ask - self.yes_bid
        return self.spread
    
    def validate_price_data(self):
        """Validate that price data is reasonable."""
        errors = []
        
        # Check for negative prices
        if self.yes_bid is not None and self.yes_bid < 0:
            errors.append("yes_bid cannot be negative")
        if self.yes_ask is not None and self.yes_ask < 0:
            errors.append("yes_ask cannot be negative")
        if self.no_bid is not None and self.no_bid < 0:
            errors.append("no_bid cannot be negative")
        if self.no_ask is not None and self.no_ask < 0:
            errors.append("no_ask cannot be negative")
        
        # Check that ask >= bid
        if self.yes_ask is not None and self.yes_bid is not None and self.yes_ask < self.yes_bid:
            errors.append("yes_ask must be >= yes_bid")
        if self.no_ask is not None and self.no_bid is not None and self.no_ask < self.no_bid:
            errors.append("no_ask must be >= no_bid")
        
        # Check that prices are between 0 and 1 for binary markets
        if self.yes_bid is not None and (self.yes_bid < 0 or self.yes_bid > 1):
            errors.append("yes_bid must be between 0 and 1")
        if self.yes_ask is not None and (self.yes_ask < 0 or self.yes_ask > 1):
            errors.append("yes_ask must be between 0 and 1")
        
        return len(errors) == 0, errors
    
    @classmethod
    def create_with_spread(cls, market_id, yes_bid, yes_ask, no_bid=None, no_ask=None, **kwargs):
        """Create a new MarketPrice instance with automatic spread calculation."""
        instance = cls(
            market_id=market_id,
            yes_bid=yes_bid,
            yes_ask=yes_ask,
            no_bid=no_bid,
            no_ask=no_ask,
            **kwargs
        )
        
        # Calculate spread
        instance.calculate_spread()
        
        # Validate the data
        is_valid, errors = instance.validate_price_data()
        if not is_valid:
            raise ValueError(f"Invalid price data: {errors}")
        
        return instance
    
    def __repr__(self):
        return f"<MarketPrice(id={self.id}, market_id={self.market_id}, yes_bid={self.yes_bid}, yes_ask={self.yes_ask}, timestamp={self.timestamp})>"


class ArbitrageOpportunity(Base):
    """Arbitrage opportunity model."""
    
    __tablename__ = "arbitrage_opportunities"
    
    id = Column(Integer, primary_key=True)
    timestamp_detected = Column(DateTime, default=func.now())
    platform_1 = Column(String(50), nullable=False)
    platform_2 = Column(String(50), nullable=False)
    market_1_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    market_2_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    profit_percentage = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default="active")  # 'active', 'expired', 'executed'
    
    # Relationships
    market_1 = relationship("Market", foreign_keys=[market_1_id], back_populates="arbitrage_opportunities_1")
    market_2 = relationship("Market", foreign_keys=[market_2_id], back_populates="arbitrage_opportunities_2")
    paper_trades = relationship("PaperTrade", back_populates="opportunity", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ArbitrageOpportunity(id={self.id}, profit={self.profit_percentage}%, status='{self.status}')>"


class PaperTrade(Base):
    """Paper trade model for tracking arbitrage trades."""
    
    __tablename__ = "paper_trades"
    
    id = Column(Integer, primary_key=True)
    opportunity_id = Column(Integer, ForeignKey("arbitrage_opportunities.id"), nullable=False)
    entry_timestamp = Column(DateTime, default=func.now())
    position_size = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    pnl = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default="open")  # 'open', 'closed'
    
    # Relationships
    opportunity = relationship("ArbitrageOpportunity", back_populates="paper_trades")
    
    def __repr__(self):
        return f"<PaperTrade(id={self.id}, status='{self.status}', pnl={self.pnl})>"


# Legacy models for backward compatibility (can be removed later)
class Outcome(Base):
    """Legacy outcome model - kept for backward compatibility."""
    
    __tablename__ = "outcomes"
    
    id = Column(Integer, primary_key=True)
    market_id = Column(Integer, nullable=False)
    outcome_id = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    probability = Column(Float)
    volume = Column(Float)
    last_price = Column(Float)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
