"""Base scraper class for all data scrapers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import logging
import re


class BaseScraper(ABC):
    """Abstract base class for all prediction market scrapers."""
    
    def __init__(self, platform_name: str):
        """Initialize base scraper with platform name."""
        self.platform_name = platform_name
        self.logger = logging.getLogger(f"scraper.{platform_name}")
        
        # Common team name patterns for parsing
        self.team_patterns = {
            # NFL Teams
            'patriots': ['patriots', 'new england', 'ne'],
            'bills': ['bills', 'buffalo', 'buf'],
            'dolphins': ['dolphins', 'miami', 'mia'],
            'jets': ['jets', 'new york jets', 'nyj'],
            'bengals': ['bengals', 'cincinnati', 'cin'],
            'browns': ['browns', 'cleveland', 'cle'],
            'ravens': ['ravens', 'baltimore', 'bal'],
            'steelers': ['steelers', 'pittsburgh', 'pit'],
            'colts': ['colts', 'indianapolis', 'ind'],
            'jaguars': ['jaguars', 'jacksonville', 'jax'],
            'texans': ['texans', 'houston', 'hou'],
            'titans': ['titans', 'tennessee', 'ten'],
            'broncos': ['broncos', 'denver', 'den'],
            'chiefs': ['chiefs', 'kansas city', 'kc'],
            'raiders': ['raiders', 'las vegas', 'lv', 'oakland'],
            'chargers': ['chargers', 'los angeles chargers', 'lac'],
            'cowboys': ['cowboys', 'dallas', 'dal'],
            'eagles': ['eagles', 'philadelphia', 'phi'],
            'giants': ['giants', 'new york giants', 'nyg'],
            'commanders': ['commanders', 'washington', 'was', 'redskins'],
            'bears': ['bears', 'chicago', 'chi'],
            'lions': ['lions', 'detroit', 'det'],
            'packers': ['packers', 'green bay', 'gb'],
            'vikings': ['vikings', 'minnesota', 'min'],
            'falcons': ['falcons', 'atlanta', 'atl'],
            'panthers': ['panthers', 'carolina', 'car'],
            'saints': ['saints', 'new orleans', 'no'],
            'buccaneers': ['buccaneers', 'tampa bay', 'tb'],
            'cardinals': ['cardinals', 'arizona', 'ari'],
            'rams': ['rams', 'los angeles rams', 'lar'],
            '49ers': ['49ers', 'san francisco', 'sf'],
            'seahawks': ['seahawks', 'seattle', 'sea'],
            
            # NBA Teams
            'lakers': ['lakers', 'los angeles lakers', 'la lakers'],
            'celtics': ['celtics', 'boston', 'bos'],
            'warriors': ['warriors', 'golden state', 'gs'],
            'bulls': ['bulls', 'chicago', 'chi'],
            'heat': ['heat', 'miami', 'mia'],
            'knicks': ['knicks', 'new york', 'ny'],
            'nets': ['nets', 'brooklyn', 'bkn'],
            
            # MLB Teams
            'yankees': ['yankees', 'new york yankees', 'nyy'],
            'red sox': ['red sox', 'boston', 'bos'],
            'dodgers': ['dodgers', 'los angeles', 'la'],
            'giants': ['giants', 'san francisco', 'sf'],
            'cubs': ['cubs', 'chicago', 'chi'],
            'cardinals': ['cardinals', 'st louis', 'stl'],
            
            # Generic patterns
            'home': ['home', 'host', 'hosting'],
            'away': ['away', 'visiting', 'visitor']
        }
    
    @abstractmethod
    def fetch_markets(self) -> List[Dict[str, Any]]:
        """Fetch all available markets from the platform. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def fetch_prices(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Fetch current prices/orderbook for a specific market. Must be implemented by subclasses."""
        pass
    
    def parse_teams_from_title(self, title: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract team names from market title.
        
        Args:
            title: Market title string
            
        Returns:
            Tuple of (home_team, away_team) or (None, None) if no teams found
        """
        if not title:
            return None, None
        
        title_lower = title.lower()
        
        # Common patterns for team vs team
        vs_patterns = [
            r'(\w+(?:\s+\w+)*)\s+vs\.?\s+(\w+(?:\s+\w+)*)',  # "Chiefs vs Ravens"
            r'(\w+(?:\s+\w+)*)\s+@\s+(\w+(?:\s+\w+)*)',      # "Chiefs @ Ravens"
            r'(\w+(?:\s+\w+)*)\s+at\s+(\w+(?:\s+\w+)*)',     # "Chiefs at Ravens"
            r'(\w+(?:\s+\w+)*)\s+versus\s+(\w+(?:\s+\w+)*)', # "Chiefs versus Ravens"
        ]
        
        # Try to match team vs team patterns
        for pattern in vs_patterns:
            match = re.search(pattern, title_lower)
            if match:
                team1, team2 = match.groups()
                return self._identify_teams(team1.strip(), team2.strip())
        
        # Look for team names in the title
        found_teams = []
        for team_name, variations in self.team_patterns.items():
            for variation in variations:
                if variation in title_lower:
                    found_teams.append(team_name)
                    break
        
        # If we found exactly 2 teams, try to determine home/away
        if len(found_teams) == 2:
            return self._determine_home_away(title_lower, found_teams[0], found_teams[1])
        elif len(found_teams) == 1:
            return found_teams[0], None
        else:
            return None, None
    
    def _identify_teams(self, team1: str, team2: str) -> Tuple[str, str]:
        """Identify which team is home vs away based on context."""
        # Check if team names match our known patterns
        team1_normalized = self._normalize_team_name(team1)
        team2_normalized = self._normalize_team_name(team2)
        
        if team1_normalized and team2_normalized:
            # For now, assume first team is home (common in "Team A vs Team B" format)
            return team1_normalized, team2_normalized
        
        return team1, team2
    
    def _normalize_team_name(self, team_name: str) -> Optional[str]:
        """Normalize team name to standard format."""
        team_lower = team_name.lower()
        
        for standard_name, variations in self.team_patterns.items():
            if team_lower in variations or team_lower == standard_name:
                return standard_name
        
        return None
    
    def _determine_home_away(self, title: str, team1: str, team2: str) -> Tuple[str, str]:
        """Determine which team is home vs away based on title context."""
        # Look for home/away indicators
        if any(indicator in title for indicator in self.team_patterns['home']):
            # If we find "home" indicators, the first team mentioned is likely home
            return team1, team2
        elif any(indicator in title for indicator in self.team_patterns['away']):
            # If we find "away" indicators, the second team mentioned is likely home
            return team2, team1
        else:
            # Default: first team is home
            return team1, team2
    
    def normalize_market_data(self, platform: str, raw_market: Dict[str, Any], 
                            orderbook: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Convert raw market data to standardized format.
        
        Args:
            platform: Platform name (e.g., 'kalshi', 'polymarket')
            raw_market: Raw market data from the platform
            orderbook: Optional orderbook/price data
            
        Returns:
            Normalized market data in standard format
        """
        try:
            # Extract basic market info
            market_id = raw_market.get('id') or raw_market.get('market_id') or raw_market.get('ticker')
            ticker = raw_market.get('ticker') or raw_market.get('market_id') or market_id
            title = raw_market.get('title') or raw_market.get('name') or ''
            
            # Parse event date
            event_date = None
            date_str = raw_market.get('event_date') or raw_market.get('close_date') or raw_market.get('expiration')
            if date_str:
                try:
                    if isinstance(date_str, str):
                        # Try common date formats
                        for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']:
                            try:
                                event_date = datetime.strptime(date_str, fmt)
                                break
                            except ValueError:
                                continue
                    elif isinstance(date_str, (int, float)):
                        # Unix timestamp
                        event_date = datetime.fromtimestamp(date_str)
                except Exception as e:
                    self.logger.warning(f"Could not parse date '{date_str}': {e}")
            
            # Parse teams from title
            home_team, away_team = self.parse_teams_from_title(title)
            
            # Extract price data from orderbook
            yes_bid = yes_ask = no_bid = no_ask = 0.0
            volume = raw_market.get('volume', 0.0) or 0.0
            open_interest = raw_market.get('open_interest', 0.0) or 0.0
            last_price = raw_market.get('last_price', 0.0) or 0.0
            
            if orderbook:
                # Extract bid/ask from orderbook structure
                # This will vary by platform, so we need to handle different formats
                yes_bid = self._extract_price(orderbook, 'yes', 'bid') or 0.0
                yes_ask = self._extract_price(orderbook, 'yes', 'ask') or 0.0
                no_bid = self._extract_price(orderbook, 'no', 'bid') or 0.0
                no_ask = self._extract_price(orderbook, 'no', 'ask') or 0.0
            
            # Determine market type
            market_type = 'binary'  # Default to binary for now
            if raw_market.get('type') in ['categorical', 'scalar']:
                market_type = raw_market.get('type')
            
            normalized_data = {
                'platform': platform,
                'market_id': str(market_id) if market_id else '',
                'ticker': str(ticker) if ticker else '',
                'event_date': event_date,
                'title': str(title),
                'home_team': home_team,
                'away_team': away_team,
                'market_type': market_type,
                'yes_bid': float(yes_bid),
                'yes_ask': float(yes_ask),
                'no_bid': float(no_bid),
                'no_ask': float(no_ask),
                'volume': float(volume),
                'open_interest': float(open_interest),
                'last_price': float(last_price),
                'raw_data': raw_market,  # Keep original data for reference
                'normalized_at': datetime.now()
            }
            
            self.logger.debug(f"Normalized market data for {market_id}: {title}")
            return normalized_data
            
        except Exception as e:
            self.logger.error(f"Error normalizing market data: {e}")
            # Return minimal normalized data on error
            return {
                'platform': platform,
                'market_id': str(raw_market.get('id', '')),
                'ticker': str(raw_market.get('ticker', '')),
                'event_date': None,
                'title': str(raw_market.get('title', '')),
                'home_team': None,
                'away_team': None,
                'market_type': 'binary',
                'yes_bid': 0.0,
                'yes_ask': 0.0,
                'no_bid': 0.0,
                'no_ask': 0.0,
                'volume': 0.0,
                'open_interest': 0.0,
                'last_price': 0.0,
                'raw_data': raw_market,
                'normalized_at': datetime.now(),
                'error': str(e)
            }
    
    def _extract_price(self, orderbook: Dict[str, Any], outcome: str, side: str) -> Optional[float]:
        """Extract price from orderbook for specific outcome and side."""
        try:
            # Handle different orderbook formats
            if 'bids' in orderbook and 'asks' in orderbook:
                # Standard format with bids/asks arrays
                if side == 'bid':
                    bids = orderbook.get('bids', [])
                    if bids and len(bids) > 0:
                        return float(bids[0].get('price', 0))
                elif side == 'ask':
                    asks = orderbook.get('asks', [])
                    if asks and len(asks) > 0:
                        return float(asks[0].get('price', 0))
            
            elif 'orderbook' in orderbook:
                # Nested orderbook format
                nested_ob = orderbook['orderbook']
                if outcome in nested_ob:
                    outcome_ob = nested_ob[outcome]
                    if side == 'bid' and 'bids' in outcome_ob:
                        bids = outcome_ob['bids']
                        if bids and len(bids) > 0:
                            return float(bids[0].get('price', 0))
                    elif side == 'ask' and 'asks' in outcome_ob:
                        asks = outcome_ob['asks']
                        if asks and len(asks) > 0:
                            return float(asks[0].get('price', 0))
            
            # Try direct key access
            key = f"{outcome}_{side}"
            if key in orderbook:
                return float(orderbook[key])
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Could not extract {side} price for {outcome}: {e}")
            return None
    
    def save_to_db(self, normalized_data: Dict[str, Any]) -> bool:
        """Save normalized market data to database.
        
        Args:
            normalized_data: Normalized market data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Import here to avoid circular imports
            from database.queries import insert_market_data
            
            # Prepare data for database insertion
            db_data = {
                'platform': normalized_data['platform'],
                'market_id': normalized_data['market_id'],
                'ticker': normalized_data['ticker'],
                'event_date': normalized_data['event_date'],
                'title': normalized_data['title'],
                'home_team': normalized_data['home_team'],
                'away_team': normalized_data['away_team'],
                'market_type': normalized_data['market_type'],
                'yes_bid': normalized_data['yes_bid'],
                'yes_ask': normalized_data['yes_ask'],
                'no_bid': normalized_data['no_bid'],
                'no_ask': normalized_data['no_ask'],
                'volume': normalized_data['volume'],
                'open_interest': normalized_data['open_interest'],
                'last_price': normalized_data['last_price'],
                'last_updated': normalized_data['normalized_at']
            }
            
            # Insert into database
            success = insert_market_data(db_data)
            
            if success:
                self.logger.info(f"Successfully saved market data for {normalized_data['market_id']}")
            else:
                self.logger.warning(f"Failed to save market data for {normalized_data['market_id']}")
            
            return success
            
        except ImportError:
            self.logger.error("Database module not available")
            return False
        except Exception as e:
            self.logger.error(f"Error saving to database: {e}")
            return False
    
    def scrape_and_save(self) -> List[Dict[str, Any]]:
        """Convenience method to fetch markets, normalize, and save to database."""
        try:
            # Fetch markets
            markets = self.fetch_markets()
            if not markets:
                self.logger.warning("No markets fetched")
                return []
            
            normalized_markets = []
            
            for market in markets:
                try:
                    # Fetch prices for each market
                    market_id = market.get('id') or market.get('market_id') or market.get('ticker')
                    if market_id:
                        orderbook = self.fetch_prices(market_id)
                    else:
                        orderbook = None
                    
                    # Normalize data
                    normalized = self.normalize_market_data(self.platform_name, market, orderbook)
                    normalized_markets.append(normalized)
                    
                    # Save to database
                    self.save_to_db(normalized)
                    
                except Exception as e:
                    self.logger.error(f"Error processing market {market.get('id', 'unknown')}: {e}")
                    continue
            
            self.logger.info(f"Successfully processed {len(normalized_markets)} markets")
            return normalized_markets
            
        except Exception as e:
            self.logger.error(f"Error in scrape_and_save: {e}")
            return []
