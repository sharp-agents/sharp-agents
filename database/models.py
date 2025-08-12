"""Database models for the application."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Market(Base):
    """Prediction market model."""
    
    __tablename__ = "markets"
    
    id = Column(Integer, primary_key=True)
    source = Column(String(50), nullable=False)  # polymarket, kalshi, etc.
    market_id = Column(String(100), unique=True, nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    category = Column(String(100))
    end_date = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Outcome(Base):
    """Market outcome model."""
    
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


class ArbitrageOpportunity(Base):
    """Arbitrage opportunity model."""
    
    __tablename__ = "arbitrage_opportunities"
    
    id = Column(Integer, primary_key=True)
    market_id = Column(Integer, nullable=False)
    source_a = Column(String(50), nullable=False)
    source_b = Column(String(50), nullable=False)
    price_difference = Column(Float, nullable=False)
    potential_profit = Column(Float)
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
