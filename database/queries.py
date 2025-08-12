"""Database query functions."""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from .models import Market, MarketPrice, ArbitrageOpportunity, PaperTrade
import logging

logger = logging.getLogger(__name__)


# Market queries
def get_markets_by_platform(session: Session, platform: str) -> List[Market]:
    """Get all markets from a specific platform."""
    return session.query(Market).filter(Market.platform == platform).all()


def get_market_by_id(session: Session, market_id: str) -> Optional[Market]:
    """Get a market by its platform ID."""
    return session.query(Market).filter(Market.market_id == market_id).first()


def get_markets_by_type(session: Session, market_type: str) -> List[Market]:
    """Get all markets of a specific type."""
    return session.query(Market).filter(Market.market_type == market_type).all()


def get_markets_by_team(session: Session, team_name: str) -> List[Market]:
    """Get all markets involving a specific team."""
    return session.query(Market).filter(
        or_(
            Market.home_team.contains(team_name),
            Market.away_team.contains(team_name)
        )
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


# MarketPrice queries
def get_latest_price(session: Session, market_id: int) -> Optional[MarketPrice]:
    """Get the latest price for a market."""
    return session.query(MarketPrice).filter(
        MarketPrice.market_id == market_id
    ).order_by(desc(MarketPrice.timestamp)).first()


def get_price_history(session: Session, market_id: int, hours: int = 24) -> List[MarketPrice]:
    """Get price history for a market over the last N hours."""
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    return session.query(MarketPrice).filter(
        and_(
            MarketPrice.market_id == market_id,
            MarketPrice.timestamp >= cutoff_time
        )
    ).order_by(MarketPrice.timestamp).all()


def create_market_price(session: Session, price_data: dict) -> MarketPrice:
    """Create a new market price record."""
    price = MarketPrice(**price_data)
    session.add(price)
    session.commit()
    return price


# ArbitrageOpportunity queries
def get_active_arbitrage_opportunities(session: Session) -> List[ArbitrageOpportunity]:
    """Get all active arbitrage opportunities."""
    return session.query(ArbitrageOpportunity).filter(
        ArbitrageOpportunity.status == "active"
    ).order_by(desc(ArbitrageOpportunity.profit_percentage)).all()


def get_arbitrage_opportunities_by_profit(session: Session, min_profit: float) -> List[ArbitrageOpportunity]:
    """Get arbitrage opportunities above a minimum profit threshold."""
    return session.query(ArbitrageOpportunity).filter(
        and_(
            ArbitrageOpportunity.profit_percentage >= min_profit,
            ArbitrageOpportunity.status == "active"
        )
    ).order_by(desc(ArbitrageOpportunity.profit_percentage)).all()


def get_arbitrage_opportunities_by_platforms(session: Session, platform_1: str, platform_2: str) -> List[ArbitrageOpportunity]:
    """Get arbitrage opportunities between two specific platforms."""
    return session.query(ArbitrageOpportunity).filter(
        and_(
            or_(
                and_(
                    ArbitrageOpportunity.platform_1 == platform_1,
                    ArbitrageOpportunity.platform_2 == platform_2
                ),
                and_(
                    ArbitrageOpportunity.platform_1 == platform_2,
                    ArbitrageOpportunity.platform_2 == platform_1
                )
            ),
            ArbitrageOpportunity.status == "active"
        )
    ).all()


def create_arbitrage_opportunity(session: Session, opportunity_data: dict) -> ArbitrageOpportunity:
    """Create a new arbitrage opportunity."""
    opportunity = ArbitrageOpportunity(**opportunity_data)
    session.add(opportunity)
    session.commit()
    return opportunity


def update_arbitrage_status(session: Session, opportunity_id: int, status: str) -> Optional[ArbitrageOpportunity]:
    """Update the status of an arbitrage opportunity."""
    opportunity = session.query(ArbitrageOpportunity).filter(
        ArbitrageOpportunity.id == opportunity_id
    ).first()
    if opportunity:
        opportunity.status = status
        session.commit()
    return opportunity


# PaperTrade queries
def get_open_paper_trades(session: Session) -> List[PaperTrade]:
    """Get all open paper trades."""
    return session.query(PaperTrade).filter(PaperTrade.status == "open").all()


def get_paper_trades_by_opportunity(session: Session, opportunity_id: int) -> List[PaperTrade]:
    """Get all paper trades for a specific arbitrage opportunity."""
    return session.query(PaperTrade).filter(PaperTrade.opportunity_id == opportunity_id).all()


def create_paper_trade(session: Session, trade_data: dict) -> PaperTrade:
    """Create a new paper trade."""
    trade = PaperTrade(**trade_data)
    session.add(trade)
    session.commit()
    return trade


def close_paper_trade(session: Session, trade_id: int, exit_price: float, pnl: float) -> Optional[PaperTrade]:
    """Close a paper trade."""
    trade = session.query(PaperTrade).filter(PaperTrade.id == trade_id).first()
    if trade and trade.status == "open":
        trade.exit_price = exit_price
        trade.pnl = pnl
        trade.status = "closed"
        session.commit()
    return trade


# Analytics queries
def get_total_pnl(session: Session) -> float:
    """Get total PnL from all closed paper trades."""
    result = session.query(func.sum(PaperTrade.pnl)).filter(
        PaperTrade.status == "closed"
    ).scalar()
    return result or 0.0


def get_arbitrage_success_rate(session: Session) -> Dict[str, Any]:
    """Get arbitrage opportunity success rate statistics."""
    total_opportunities = session.query(func.count(ArbitrageOpportunity.id)).scalar()
    executed_opportunities = session.query(func.count(ArbitrageOpportunity.id)).filter(
        ArbitrageOpportunity.status == "executed"
    ).scalar()
    
    success_rate = (executed_opportunities / total_opportunities * 100) if total_opportunities > 0 else 0
    
    return {
        "total_opportunities": total_opportunities,
        "executed_opportunities": executed_opportunities,
        "success_rate": success_rate
    }


# New helper functions with session management and error handling
def get_or_create_market(session: Session, platform: str, market_id: str, 
                        home_team: str, away_team: str, market_type: str, 
                        event_date: Optional[datetime] = None) -> Tuple[Market, bool]:
    """
    Get existing market or create new one.
    
    Returns:
        Tuple[Market, bool]: (market, created) where created indicates if it's new
    """
    try:
        # Try to find existing market
        existing_market = get_market_by_id(session, market_id)
        if existing_market:
            return existing_market, False
        
        # Create new market
        market_data = {
            "platform": platform,
            "market_id": market_id,
            "home_team": home_team,
            "away_team": away_team,
            "market_type": market_type,
            "event_date": event_date
        }
        
        new_market = create_market(session, market_data)
        logger.info(f"Created new market: {platform}/{market_id}")
        return new_market, True
        
    except Exception as e:
        logger.error(f"Error in get_or_create_market: {e}")
        session.rollback()
        raise


def add_market_price(session: Session, market_id: int, yes_price: Optional[float] = None,
                    no_price: Optional[float] = None, volume: Optional[float] = None,
                    liquidity: Optional[float] = None) -> MarketPrice:
    """
    Add new price point for a market.
    
    Args:
        market_id: ID of the market
        yes_price: Yes price for binary markets
        no_price: No price for binary markets
        volume: Trading volume
        liquidity: Market liquidity
        
    Returns:
        MarketPrice: Created price record
    """
    try:
        # Verify market exists
        market = session.query(Market).filter(Market.id == market_id).first()
        if not market:
            raise ValueError(f"Market with ID {market_id} not found")
        
        price_data = {
            "market_id": market_id,
            "yes_price": yes_price,
            "no_price": no_price,
            "volume": volume,
            "liquidity": liquidity
        }
        
        # Remove None values
        price_data = {k: v for k, v in price_data.items() if v is not None}
        
        new_price = create_market_price(session, price_data)
        logger.info(f"Added price for market {market_id}: yes={yes_price}, no={no_price}")
        return new_price
        
    except Exception as e:
        logger.error(f"Error in add_market_price: {e}")
        session.rollback()
        raise


def find_arbitrage_opportunities(session: Session, min_profit: float = 0.02) -> List[Dict[str, Any]]:
    """
    Find arbitrage opportunities by comparing prices across platforms.
    
    Args:
        min_profit: Minimum profit threshold (as decimal, e.g., 0.02 for 2%)
        
    Returns:
        List of arbitrage opportunities above threshold
    """
    try:
        opportunities = []
        
        # Get all active markets with recent prices
        markets = session.query(Market).filter(Market.platform.in_(['polymarket', 'kalshi'])).all()
        
        for i, market1 in enumerate(markets):
            for market2 in markets[i+1:]:
                # Skip if same platform
                if market1.platform == market2.platform:
                    continue
                
                # Get latest prices for both markets
                price1 = get_latest_price(session, market1.id)
                price2 = get_latest_price(session, market2.id)
                
                if not price1 or not price2:
                    continue
                
                # Calculate potential arbitrage
                if price1.yes_price and price2.yes_price:
                    # Binary market arbitrage
                    profit_pct = abs(price1.yes_price - price2.yes_price)
                    
                    if profit_pct >= min_profit:
                        opportunity = {
                            "market_1": {
                                "id": market1.id,
                                "platform": market1.platform,
                                "market_id": market1.market_id,
                                "price": price1.yes_price
                            },
                            "market_2": {
                                "id": market2.id,
                                "platform": market2.platform,
                                "market_id": market2.market_id,
                                "price": price2.yes_price
                            },
                            "profit_percentage": profit_pct * 100,
                            "type": "binary_arbitrage"
                        }
                        opportunities.append(opportunity)
        
        # Sort by profit percentage
        opportunities.sort(key=lambda x: x["profit_percentage"], reverse=True)
        
        logger.info(f"Found {len(opportunities)} arbitrage opportunities above {min_profit*100}% threshold")
        return opportunities
        
    except Exception as e:
        logger.error(f"Error in find_arbitrage_opportunities: {e}")
        session.rollback()
        raise


def create_paper_trade(session: Session, opportunity_id: int, position_size: float, 
                      entry_price: float) -> PaperTrade:
    """
    Create new paper trade entry.
    
    Args:
        opportunity_id: ID of the arbitrage opportunity
        position_size: Size of the position
        entry_price: Entry price for the trade
        
    Returns:
        PaperTrade: Created paper trade
    """
    try:
        # Verify opportunity exists and is active
        opportunity = session.query(ArbitrageOpportunity).filter(
            and_(
                ArbitrageOpportunity.id == opportunity_id,
                ArbitrageOpportunity.status == "active"
            )
        ).first()
        
        if not opportunity:
            raise ValueError(f"Active arbitrage opportunity with ID {opportunity_id} not found")
        
        trade_data = {
            "opportunity_id": opportunity_id,
            "position_size": position_size,
            "entry_price": entry_price,
            "status": "open"
        }
        
        new_trade = create_paper_trade(session, trade_data)
        logger.info(f"Created paper trade for opportunity {opportunity_id}: size={position_size}, price={entry_price}")
        return new_trade
        
    except Exception as e:
        logger.error(f"Error in create_paper_trade: {e}")
        session.rollback()
        raise


def get_recent_prices(session: Session, platform: Optional[str] = None, minutes: int = 60) -> List[Dict[str, Any]]:
    """
    Get recent price data.
    
    Args:
        platform: Optional platform filter
        minutes: Number of minutes to look back
        
    Returns:
        List of recent price records with market info
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        # Build query
        query = session.query(MarketPrice, Market).join(Market, MarketPrice.market_id == Market.id)
        
        if platform:
            query = query.filter(Market.platform == platform)
        
        query = query.filter(MarketPrice.timestamp >= cutoff_time)
        query = query.order_by(desc(MarketPrice.timestamp))
        
        results = query.all()
        
        # Format results
        price_data = []
        for price, market in results:
            price_data.append({
                "price_id": price.id,
                "market_id": market.id,
                "platform": market.platform,
                "market_id_str": market.market_id,
                "home_team": market.home_team,
                "away_team": market.away_team,
                "market_type": market.market_type,
                "timestamp": price.timestamp,
                "yes_price": price.yes_price,
                "no_price": price.no_price,
                "volume": price.volume,
                "liquidity": price.liquidity
            })
        
        logger.info(f"Retrieved {len(price_data)} recent price records from last {minutes} minutes")
        return price_data
        
    except Exception as e:
        logger.error(f"Error in get_recent_prices: {e}")
        session.rollback()
        raise
