"""Database query functions."""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from .models import Market, Outcome, ArbitrageOpportunity


def get_markets_by_source(session: Session, source: str) -> List[Market]:
    """Get all markets from a specific source."""
    return session.query(Market).filter(Market.source == source).all()


def get_market_by_id(session: Session, market_id: str) -> Optional[Market]:
    """Get a market by its ID."""
    return session.query(Market).filter(Market.market_id == market_id).first()


def get_outcomes_for_market(session: Session, market_id: int) -> List[Outcome]:
    """Get all outcomes for a specific market."""
    return session.query(Outcome).filter(Outcome.market_id == market_id).all()


def get_active_arbitrage_opportunities(session: Session) -> List[ArbitrageOpportunity]:
    """Get all active arbitrage opportunities."""
    return session.query(ArbitrageOpportunity).filter(
        ArbitrageOpportunity.is_active == True
    ).all()


def create_market(session: Session, market_data: dict) -> Market:
    """Create a new market."""
    market = Market(**market_data)
    session.add(market)
    session.commit()
    return market


def update_market(session: Session, market_id: str, update_data: dict) -> Optional[Market]:
    """Update an existing market."""
    market = get_market_by_id(session, market_id)
    if market:
        for key, value in update_data.items():
            setattr(market, key, value)
        session.commit()
    return market
