"""Database models for the application."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Market(Base):
    """Prediction market model."""
    
    __tablename__ = "markets"
    
    id = Column(Integer, primary_key=True)
    platform = Column(String(50), nullable=False)  # 'polymarket' or 'kalshi'
    market_id = Column(String(100), unique=True, nullable=False)  # unique platform ID
    event_date = Column(DateTime, nullable=True)
    home_team = Column(String(100), nullable=True)
    away_team = Column(String(100), nullable=True)
    market_type = Column(String(50), nullable=False)  # 'moneyline', 'spread', 'total'
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    prices = relationship("MarketPrice", back_populates="market", cascade="all, delete-orphan")
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
        return f"<Market(id={self.id}, platform='{self.platform}', market_id='{self.market_id}')>"


class MarketPrice(Base):
    """Market price data model."""
    
    __tablename__ = "market_prices"
    
    id = Column(Integer, primary_key=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    timestamp = Column(DateTime, default=func.now())
    yes_price = Column(Float, nullable=True)  # for binary markets
    no_price = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)
    liquidity = Column(Float, nullable=True)
    
    # Relationships
    market = relationship("Market", back_populates="prices")
    
    def __repr__(self):
        return f"<MarketPrice(id={self.id}, market_id={self.market_id}, timestamp={self.timestamp})>"


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
