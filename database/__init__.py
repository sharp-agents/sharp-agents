# Database package for data models and queries

from .models import Base, Market, MarketPrice, ArbitrageOpportunity, PaperTrade
from .queries import (
    # Market queries
    get_markets_by_platform,
    get_market_by_id,
    get_markets_by_type,
    get_markets_by_team,
    create_market,
    update_market,
    
    # MarketPrice queries
    get_latest_price,
    get_price_history,
    create_market_price,
    
    # ArbitrageOpportunity queries
    get_active_arbitrage_opportunities,
    get_arbitrage_opportunities_by_profit,
    get_arbitrage_opportunities_by_platforms,
    create_arbitrage_opportunity,
    update_arbitrage_status,
    
    # PaperTrade queries
    get_open_paper_trades,
    get_paper_trades_by_opportunity,
    create_paper_trade,
    close_paper_trade,
    
    # Analytics queries
    get_total_pnl,
    get_arbitrage_success_rate,
    
    # New helper functions
    get_or_create_market,
    add_market_price,
    find_arbitrage_opportunities,
    create_paper_trade,
    get_recent_prices
)

__all__ = [
    # Models
    'Base',
    'Market',
    'MarketPrice', 
    'ArbitrageOpportunity',
    'PaperTrade',
    
    # Query functions
    'get_markets_by_platform',
    'get_market_by_id',
    'get_markets_by_type',
    'get_markets_by_team',
    'create_market',
    'update_market',
    'get_latest_price',
    'get_price_history',
    'create_market_price',
    'get_active_arbitrage_opportunities',
    'get_arbitrage_opportunities_by_profit',
    'get_arbitrage_opportunities_by_platforms',
    'create_arbitrage_opportunity',
    'update_arbitrage_status',
    'get_open_paper_trades',
    'get_paper_trades_by_opportunity',
    'create_paper_trade',
    'close_paper_trade',
    'get_total_pnl',
    'get_arbitrage_success_rate',
    
    # New helper functions
    'get_or_create_market',
    'add_market_price',
    'find_arbitrage_opportunities',
    'create_paper_trade',
    'get_recent_prices'
]
