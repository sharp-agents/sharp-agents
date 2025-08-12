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


def get_nfl_markets(session: Session, platform: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get all NFL-related markets with latest price information.
    
    Args:
        session: Database session
        platform: Optional platform filter
        
    Returns:
        List of NFL markets with price data
    """
    try:
        # Build query for NFL markets
        query = session.query(
            Market,
            MarketPrice.yes_bid,
            MarketPrice.yes_ask,
            MarketPrice.no_bid,
            MarketPrice.no_ask,
            MarketPrice.spread,
            MarketPrice.volume,
            MarketPrice.last_trade_price,
            MarketPrice.timestamp.label('last_price_time')
        ).join(
            MarketPrice, Market.id == MarketPrice.market_id
        ).filter(
            or_(
                Market.home_team.isnot(None),
                Market.away_team.isnot(None),
                Market.title.contains('NFL'),
                Market.title.contains('FOOTBALL'),
                Market.title.contains('SUPER BOWL')
            )
        )
        
        if platform:
            query = query.filter(Market.platform == platform)
        
        # Get results ordered by market ID and timestamp
        results = query.order_by(
            Market.id, 
            desc(MarketPrice.timestamp)
        ).all()
        
        # Group by market and get latest price
        nfl_markets = {}
        for result in results:
            market = result[0]  # Market object
            if market.id not in nfl_markets:
                nfl_markets[market.id] = {
                    'market': market,
                    'latest_price': {
                        'yes_bid': result[1],
                        'yes_ask': result[2],
                        'no_bid': result[3],
                        'no_ask': result[4],
                        'spread': result[5],
                        'volume': result[6],
                        'last_trade_price': result[7],
                        'timestamp': result[8]
                    }
                }
        
        # Convert to list format
        nfl_markets_list = []
        for market_data in nfl_markets.values():
            market = market_data['market']
            price = market_data['latest_price']
            
            nfl_markets_list.append({
                'id': market.id,
                'platform': market.platform,
                'ticker': market.ticker,
                'title': market.title,
                'market_type': market.market_type,
                'home_team': market.home_team,
                'away_team': market.away_team,
                'event_date': market.event_date,
                'open_interest': market.open_interest,
                'latest_price': price,
                'created_at': market.created_at,
                'updated_at': market.updated_at
            })
        
        logger.info(f"Found {len(nfl_markets_list)} NFL markets")
        return nfl_markets_list
        
    except Exception as e:
        logger.error(f"Error in get_nfl_markets: {e}")
        session.rollback()
        raise


def create_market(session: Session, market_data: dict) -> Market:
    """Create a new market."""
    market = Market(**market_data)
    session.add(market)
    session.commit()
    return market


def upsert_market(session: Session, market_data: dict) -> Tuple[Market, bool]:
    """
    Create market if doesn't exist, update if exists.
    Uses platform + ticker as unique key.
    
    Args:
        session: Database session
        market_data: Market data dictionary
        
    Returns:
        Tuple[Market, bool]: (market, created) where created indicates if it's new
    """
    try:
        platform = market_data.get('platform')
        ticker = market_data.get('ticker')
        
        if not platform or not ticker:
            raise ValueError("Both platform and ticker are required for upsert")
        
        # Try to find existing market by platform + ticker
        existing_market = session.query(Market).filter(
            and_(Market.platform == platform, Market.ticker == ticker)
        ).first()
        
        if existing_market:
            # Update existing market
            for key, value in market_data.items():
                if hasattr(existing_market, key):
                    setattr(existing_market, key, value)
            existing_market.updated_at = datetime.utcnow()
            session.commit()
            logger.info(f"Updated existing market: {platform}/{ticker}")
            return existing_market, False
        else:
            # Create new market
            new_market = Market(**market_data)
            session.add(new_market)
            session.commit()
            logger.info(f"Created new market: {platform}/{ticker}")
            return new_market, True
            
    except Exception as e:
        logger.error(f"Error in upsert_market: {e}")
        session.rollback()
        raise


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


def get_active_markets(session: Session, platform: Optional[str] = None, hours: int = 1) -> List[Dict[str, Any]]:
    """
    Get markets with recent prices (last N hours).
    
    Args:
        session: Database session
        platform: Optional platform filter
        hours: Number of hours to look back for recent prices
        
    Returns:
        List of active markets with latest price info
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Build query to get markets with recent prices
        query = session.query(
            Market,
            MarketPrice.yes_bid,
            MarketPrice.yes_ask,
            MarketPrice.no_bid,
            MarketPrice.no_ask,
            MarketPrice.spread,
            MarketPrice.volume,
            MarketPrice.last_trade_price,
            MarketPrice.timestamp.label('last_price_time')
        ).join(
            MarketPrice, Market.id == MarketPrice.market_id
        ).filter(
            MarketPrice.timestamp >= cutoff_time
        )
        
        if platform:
            query = query.filter(Market.platform == platform)
        
        # Get the latest price for each market
        results = query.order_by(
            Market.id, 
            desc(MarketPrice.timestamp)
        ).all()
        
        # Group by market and get latest price
        active_markets = {}
        for result in results:
            market = result[0]  # Market object
            if market.id not in active_markets:
                active_markets[market.id] = {
                    'market': market,
                    'latest_price': {
                        'yes_bid': result[1],
                        'yes_ask': result[2],
                        'no_bid': result[3],
                        'no_ask': result[4],
                        'spread': result[5],
                        'volume': result[6],
                        'last_trade_price': result[7],
                        'timestamp': result[8]
                    }
                }
        
        # Convert to list format
        active_markets_list = []
        for market_data in active_markets.values():
            market = market_data['market']
            price = market_data['latest_price']
            
            active_markets_list.append({
                'id': market.id,
                'platform': market.platform,
                'ticker': market.ticker,
                'title': market.title,
                'market_type': market.market_type,
                'home_team': market.home_team,
                'away_team': market.away_team,
                'event_date': market.event_date,
                'open_interest': market.open_interest,
                'latest_price': price,
                'created_at': market.created_at,
                'updated_at': market.updated_at
            })
        
        logger.info(f"Found {len(active_markets_list)} active markets with recent prices (last {hours} hours)")
        return active_markets_list
        
    except Exception as e:
        logger.error(f"Error in get_active_markets: {e}")
        session.rollback()
        raise


def create_market_price(session: Session, price_data: dict) -> MarketPrice:
    """Create a new market price record."""
    price = MarketPrice(**price_data)
    session.add(price)
    session.commit()
    return price


def add_price_snapshot(session: Session, market_id: int, price_data: dict) -> MarketPrice:
    """
    Add new price record with automatic spread calculation.
    
    Args:
        session: Database session
        market_id: ID of the market
        price_data: Price data dictionary with yes_bid, yes_ask, etc.
        
    Returns:
        MarketPrice: Created price record
    """
    try:
        # Verify market exists
        market = session.query(Market).filter(Market.id == market_id).first()
        if not market:
            raise ValueError(f"Market with ID {market_id} not found")
        
        # Create price record using the new model structure
        price_record = MarketPrice(
            market_id=market_id,
            yes_bid=price_data.get('yes_bid'),
            yes_ask=price_data.get('yes_ask'),
            no_bid=price_data.get('no_bid'),
            no_ask=price_data.get('no_ask'),
            last_trade_price=price_data.get('last_trade_price'),
            volume=price_data.get('volume'),
            open_interest=price_data.get('open_interest'),
            liquidity=price_data.get('liquidity')
        )
        
        # Calculate spread automatically
        price_record.calculate_spread()
        
        # Validate price data
        is_valid, errors = price_record.validate_price_data()
        if not is_valid:
            logger.warning(f"Price validation warnings for market {market_id}: {errors}")
        
        session.add(price_record)
        session.commit()
        
        logger.info(f"Added price snapshot for market {market_id}: "
                   f"yes({price_record.yes_bid:.3f}/{price_record.yes_ask:.3f}) "
                   f"spread={price_record.spread:.3f}")
        
        return price_record
        
    except Exception as e:
        logger.error(f"Error in add_price_snapshot: {e}")
        session.rollback()
        raise


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


def get_market_summary(session: Session) -> Dict[str, Any]:
    """
    Get comprehensive market summary statistics.
    
    Returns:
        Dictionary with count by platform, average spreads, total volume, etc.
    """
    try:
        # Count markets by platform
        platform_counts = session.query(
            Market.platform,
            func.count(Market.id).label('count')
        ).group_by(Market.platform).all()
        
        platform_summary = {row.platform: row.count for row in platform_counts}
        
        # Get average spreads by platform
        spread_stats = session.query(
            Market.platform,
            func.avg(MarketPrice.spread).label('avg_spread'),
            func.min(MarketPrice.spread).label('min_spread'),
            func.max(MarketPrice.spread).label('max_spread')
        ).join(
            MarketPrice, Market.id == MarketPrice.market_id
        ).filter(
            MarketPrice.spread.isnot(None)
        ).group_by(Market.platform).all()
        
        spread_summary = {}
        for row in spread_stats:
            spread_summary[row.platform] = {
                'avg_spread': float(row.avg_spread) if row.avg_spread else 0.0,
                'min_spread': float(row.min_spread) if row.min_spread else 0.0,
                'max_spread': float(row.max_spread) if row.max_spread else 0.0
            }
        
        # Get total volume by platform
        volume_stats = session.query(
            Market.platform,
            func.sum(MarketPrice.volume).label('total_volume'),
            func.avg(MarketPrice.volume).label('avg_volume')
        ).join(
            MarketPrice, Market.id == MarketPrice.market_id
        ).filter(
            MarketPrice.volume.isnot(None)
        ).group_by(Market.platform).all()
        
        volume_summary = {}
        for row in volume_stats:
            volume_summary[row.platform] = {
                'total_volume': float(row.total_volume) if row.total_volume else 0.0,
                'avg_volume': float(row.avg_volume) if row.avg_volume else 0.0
            }
        
        # Get market type distribution
        type_counts = session.query(
            Market.market_type,
            func.count(Market.id).label('count')
        ).group_by(Market.market_type).all()
        
        type_summary = {row.market_type: row.count for row in type_counts}
        
        # Get recent activity (markets with prices in last hour)
        recent_cutoff = datetime.utcnow() - timedelta(hours=1)
        recent_markets = session.query(
            Market.platform,
            func.count(func.distinct(Market.id)).label('count')
        ).join(
            MarketPrice, Market.id == MarketPrice.market_id
        ).filter(
            MarketPrice.timestamp >= recent_cutoff
        ).group_by(Market.platform).all()
        
        recent_summary = {row.platform: row.count for row in recent_markets}
        
        # Compile final summary
        summary = {
            'platform_counts': platform_summary,
            'market_type_distribution': type_summary,
            'spread_statistics': spread_summary,
            'volume_statistics': volume_summary,
            'recent_activity': recent_summary,
            'total_markets': sum(platform_summary.values()),
            'total_platforms': len(platform_summary),
            'summary_timestamp': datetime.utcnow()
        }
        
        logger.info(f"Generated market summary: {summary['total_markets']} total markets across {summary['total_platforms']} platforms")
        return summary
        
    except Exception as e:
        logger.error(f"Error in get_market_summary: {e}")
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
                "ticker": market.ticker,
                "title": market.title,
                "home_team": market.home_team,
                "away_team": market.away_team,
                "market_type": market.market_type,
                "timestamp": price.timestamp,
                "yes_bid": price.yes_bid,
                "yes_ask": price.yes_ask,
                "no_bid": price.no_bid,
                "no_ask": price.no_ask,
                "spread": price.spread,
                "last_trade_price": price.last_trade_price,
                "volume": price.volume,
                "liquidity": price.liquidity
            })
        
        logger.info(f"Retrieved {len(price_data)} recent price records from last {minutes} minutes")
        return price_data
        
    except Exception as e:
        logger.error(f"Error in get_recent_prices: {e}")
        session.rollback()
        raise


def insert_market_data(session: Session, market_data: dict) -> bool:
    """
    Insert or update market data with prices.
    This is a convenience function that combines market and price insertion.
    
    Args:
        session: Database session
        market_data: Dictionary containing market and price data
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Extract market and price data
        market_fields = [
            'platform', 'ticker', 'title', 'event_ticker', 'event_date',
            'home_team', 'away_team', 'market_type', 'open_interest'
        ]
        
        price_fields = [
            'yes_bid', 'yes_ask', 'no_bid', 'no_ask', 'last_trade_price',
            'volume', 'open_interest'
        ]
        
        # Separate market and price data
        market_info = {k: market_data.get(k) for k in market_fields if market_data.get(k) is not None}
        price_info = {k: market_data.get(k) for k in price_fields if market_data.get(k) is not None}
        
        # Upsert market
        market, created = upsert_market(session, market_info)
        
        # Add price snapshot if price data exists
        if price_info and market.id:
            add_price_snapshot(session, market.id, price_info)
        
        logger.info(f"Successfully inserted market data for {market_info.get('platform')}/{market_info.get('ticker')}")
        return True
        
    except Exception as e:
        logger.error(f"Error in insert_market_data: {e}")
        session.rollback()
        return False
