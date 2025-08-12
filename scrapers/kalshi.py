"""Kalshi API client for prediction market data."""

import requests
import time
import logging
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from utils.config import get_config


class KalshiClient:
    """Kalshi API client with authentication and data collection capabilities."""
    
    def __init__(self):
        """Initialize Kalshi client with configuration."""
        self.config = get_config()
        self.base_url = self.config.KALSHI_API_URL
        self.api_key = self.config.KALSHI_API_KEY
        self.api_secret = self.config.KALSHI_API_SECRET
        self.timeout = self.config.KALSHI_REQUEST_TIMEOUT
        self.safe_mode = self.config.is_safe_mode()
        
        # Authentication state
        self.auth_token = None
        self.token_expires_at = None
        
        # Rate limiting
        self.last_request_time = 0
        self.max_requests_per_second = 10
        self.min_request_interval = 1.0 / self.max_requests_per_second
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Validate credentials
        if not self.api_key or not self.api_secret:
            self.logger.warning("Kalshi API credentials not configured")
    
    def _rate_limit(self):
        """Implement rate limiting to respect API limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _is_token_expired(self) -> bool:
        """Check if the current auth token is expired."""
        if not self.token_expires_at:
            return True
        return datetime.now() >= self.token_expires_at
    
    def _decode_token_expiry(self, token: str) -> Optional[datetime]:
        """Decode JWT token to get expiration time."""
        try:
            # Decode without verification to get payload
            payload = jwt.decode(token, options={"verify_signature": False})
            exp_timestamp = payload.get('exp')
            if exp_timestamp:
                return datetime.fromtimestamp(exp_timestamp)
        except Exception as e:
            self.logger.error(f"Error decoding JWT token: {e}")
        return None
    
    def login(self) -> bool:
        """Authenticate with Kalshi API using API key and secret."""
        if not self.api_key or not self.api_secret:
            self.logger.error("API credentials not configured")
            return False
        
        try:
            self._rate_limit()
            
            # For Kalshi Elections API, use API key as username and secret as password
            # For Kalshi Trading API, use email/password
            if "elections.kalshi.com" in self.base_url:
                # Elections API authentication
                auth_headers = {
                    "X-API-Key": self.api_key,
                    "X-API-Secret": self.api_secret
                }
                
                # Test authentication with a simple endpoint
                response = requests.get(
                    f"{self.base_url}/events",
                    headers=auth_headers,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    self.auth_token = f"{self.api_key}:{self.api_secret}"  # Store as combined token
                    self.token_expires_at = datetime.now() + timedelta(hours=24)  # Elections API tokens don't expire
                    self.logger.info("Successfully authenticated with Kalshi Elections API")
                    return True
                else:
                    self.logger.error(f"Elections API authentication failed with status {response.status_code}: {response.text}")
                    return False
            else:
                # Trading API authentication (original logic)
                login_data = {
                    "email": self.api_key,
                    "password": self.api_secret
                }
                
                response = requests.post(
                    f"{self.base_url}/login",
                    json=login_data,
                    timeout=self.timeout
                )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('token')
                
                if self.auth_token:
                    # Decode token to get expiration
                    self.token_expires_at = self._decode_token_expiry(self.auth_token)
                    self.logger.info("Successfully authenticated with Kalshi API")
                    return True
                else:
                    self.logger.error("No token received in login response")
                    return False
            else:
                self.logger.error(f"Login failed with status {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Login request failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during login: {e}")
            return False
    
    def _ensure_auth(self) -> bool:
        """Ensure we have a valid authentication token."""
        if self._is_token_expired():
            return self.login()
        return True
    
    def request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make authenticated request to Kalshi API with error handling and retries."""
        if not self._ensure_auth():
            self.logger.error("Authentication failed")
            return None
        
        # Add authentication headers
        headers = kwargs.get('headers', {})
        
        if "elections.kalshi.com" in self.base_url:
            # Elections API uses X-API-Key and X-API-Secret headers
            api_key, api_secret = self.auth_token.split(':', 1)
            headers['X-API-Key'] = api_key
            headers['X-API-Secret'] = api_secret
        else:
            # Trading API uses Bearer token
            headers['Authorization'] = f'Bearer {self.auth_token}'
        
        kwargs['headers'] = headers
        
        # Add timeout
        kwargs['timeout'] = self.timeout
        
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                self._rate_limit()
                
                url = f"{self.base_url}{endpoint}"
                response = requests.request(method, url, **kwargs)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    # Token expired, try to refresh
                    self.logger.warning("Token expired, attempting to refresh...")
                    if self.login():
                        # Retry with new token
                        headers['Authorization'] = f'Bearer {self.auth_token}'
                        kwargs['headers'] = headers
                        continue
                    else:
                        self.logger.error("Failed to refresh authentication token")
                        return None
                elif response.status_code == 429:
                    # Rate limited, wait and retry
                    wait_time = (2 ** attempt) * base_delay
                    self.logger.warning(f"Rate limited, waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"API request failed with status {response.status_code}: {response.text}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * base_delay
                    self.logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"Request failed after {max_retries} attempts: {e}")
                    return None
            except Exception as e:
                self.logger.error(f"Unexpected error during request: {e}")
                return None
        
        return None
    
    def get_markets(self, event_ticker: Optional[str] = None, status: str = 'open') -> List[Dict[str, Any]]:
        """Get all markets, optionally filtered by event ticker and status."""
        if "elections.kalshi.com" in self.base_url:
            # Elections API endpoint
            endpoint = "/events"
            params = {}
            
            if event_ticker:
                params['event_id'] = event_ticker
            
            response = self.request('GET', endpoint, params=params)
            if response and 'events' in response:
                return response['events']
            return []
        else:
            # Trading API endpoint
            endpoint = "/markets"
            params = {'status': status}
            
            if event_ticker:
                params['event_ticker'] = event_ticker
            
            response = self.request('GET', endpoint, params=params)
            if response and 'markets' in response:
                return response['markets']
            return []
    
    def get_market(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific market."""
        if "elections.kalshi.com" in self.base_url:
            # Elections API endpoint
            endpoint = f"/events/{ticker}"
            return self.request('GET', endpoint)
        else:
            # Trading API endpoint
            endpoint = f"/markets/{ticker}"
            return self.request('GET', endpoint)
    
    def get_orderbook(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get current bid/ask prices for a market."""
        endpoint = f"/markets/{ticker}/orderbook"
        return self.request('GET', endpoint)
    
    def get_trades(self, ticker: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent trades for a market."""
        endpoint = f"/markets/{ticker}/trades"
        params = {'limit': limit}
        
        response = self.request('GET', endpoint, params=params)
        if response and 'trades' in response:
            return response['trades']
        return []
    
    def search_nfl_markets(self) -> List[Dict[str, Any]]:
        """Search for NFL-related markets using event ticker filters."""
        if "elections.kalshi.com" in self.base_url:
            # For Elections API, search for election-related events
            # This is a placeholder - you can customize based on what elections data you want
            election_keywords = ['PRESIDENT', 'SENATE', 'HOUSE', 'GOVERNOR']
            all_election_markets = []
            
            for keyword in election_keywords:
                try:
                    # Search for events containing the keyword
                    markets = self.get_markets()
                    filtered_markets = [m for m in markets if keyword in m.get('title', '').upper()]
                    all_election_markets.extend(filtered_markets)
                    self.logger.info(f"Found {len(filtered_markets)} markets for {keyword}")
                except Exception as e:
                    self.logger.warning(f"Error fetching markets for {keyword}: {e}")
            
            return all_election_markets
        else:
            # For Trading API, search for NFL markets
            nfl_tickers = [
                'NFL-SUPER-BOWL',
                'NFL-PLAYOFFS',
                'NFL-REGULAR-SEASON',
                'NFL-DIVISION',
                'NFL-CONFERENCE',
                'NFL-WILDCARD'
            ]
            
            all_nfl_markets = []
            
            for ticker in nfl_tickers:
                try:
                    markets = self.get_markets(event_ticker=ticker, status='open')
                    all_nfl_markets.extend(markets)
                    self.logger.info(f"Found {len(markets)} markets for {ticker}")
                except Exception as e:
                    self.logger.warning(f"Error fetching markets for {ticker}: {e}")
            
            return all_nfl_markets
    
    def search_nfl_markets_detailed(self) -> List[Dict[str, Any]]:
        """Search specifically for NFL-related markets with comprehensive filtering."""
        nfl_keywords = [
            'NFL', 'FOOTBALL', 'SUPER BOWL', 'PLAYOFFS', 'REGULAR SEASON',
            'DIVISION', 'CONFERENCE', 'WILDCARD', 'CHAMPIONSHIP',
            'PATRIOTS', 'BILLS', 'DOLPHINS', 'JETS',  # AFC East
            'BENGALS', 'BROWNS', 'RAVENS', 'STEELERS',  # AFC North
            'COLTS', 'JAGUARS', 'TEXANS', 'TITANS',  # AFC South
            'BRONCOS', 'CHIEFS', 'RAIDERS', 'CHARGERS',  # AFC West
            'COWBOYS', 'EAGLES', 'GIANTS', 'COMMANDERS',  # NFC East
            'BEARS', 'LIONS', 'PACKERS', 'VIKINGS',  # NFC North
            'FALCONS', 'PANTHERS', 'SAINTS', 'BUCCANEERS',  # NFC South
            'CARDINALS', 'RAMS', '49ERS', 'SEAHAWKS'  # NFC West
        ]
        
        all_nfl_markets = []
        
        try:
            # Get all markets first
            all_markets = self.get_markets()
            
            # Filter for NFL-related markets
            for market in all_markets:
                title = market.get('title', '').upper()
                description = market.get('description', '').upper()
                
                # Check if any NFL keyword is in the title or description
                if any(keyword in title or keyword in description for keyword in nfl_keywords):
                    all_nfl_markets.append(market)
            
            self.logger.info(f"Found {len(all_nfl_markets)} NFL-related markets out of {len(all_markets)} total markets")
            
        except Exception as e:
            self.logger.error(f"Error searching for NFL markets: {e}")
        
        return all_nfl_markets
    
    def search_nfl_markets_by_team(self, team_name: str) -> List[Dict[str, Any]]:
        """Search for NFL markets related to a specific team."""
        team_keywords = {
            'patriots': ['PATRIOTS', 'NEW ENGLAND', 'NE'],
            'bills': ['BILLS', 'BUFFALO', 'BUF'],
            'bengals': ['BENGALS', 'CINCINNATI', 'CIN'],
            'browns': ['BROWNS', 'CLEVELAND', 'CLE'],
            'ravens': ['RAVENS', 'BALTIMORE', 'BAL'],
            'steelers': ['STEELERS', 'PITTSBURGH', 'PIT'],
            'colts': ['COLTS', 'INDIANAPOLIS', 'IND'],
            'jaguars': ['JAGUARS', 'JACKSONVILLE', 'JAX'],
            'texans': ['TEXANS', 'HOUSTON', 'HOU'],
            'titans': ['TITANS', 'TENNESSEE', 'TEN'],
            'broncos': ['BRONCOS', 'DENVER', 'DEN'],
            'chiefs': ['CHIEFS', 'KANSAS CITY', 'KC'],
            'raiders': ['RAIDERS', 'LAS VEGAS', 'LV'],
            'chargers': ['CHARGERS', 'LOS ANGELES', 'LAC'],
            'cowboys': ['COWBOYS', 'DALLAS', 'DAL'],
            'eagles': ['EAGLES', 'PHILADELPHIA', 'PHI'],
            'giants': ['GIANTS', 'NEW YORK', 'NYG'],
            'commanders': ['COMMANDERS', 'WASHINGTON', 'WAS'],
            'bears': ['BEARS', 'CHICAGO', 'CHI'],
            'lions': ['LIONS', 'DETROIT', 'DET'],
            'packers': ['PACKERS', 'GREEN BAY', 'GB'],
            'vikings': ['VIKINGS', 'MINNESOTA', 'MIN'],
            'falcons': ['FALCONS', 'ATLANTA', 'ATL'],
            'panthers': ['PANTHERS', 'CAROLINA', 'CAR'],
            'saints': ['SAINTS', 'NEW ORLEANS', 'NO'],
            'buccaneers': ['BUCCANEERS', 'TAMPA BAY', 'TB'],
            'cardinals': ['CARDINALS', 'ARIZONA', 'ARI'],
            'rams': ['RAMS', 'LOS ANGELES', 'LAR'],
            '49ers': ['49ERS', 'SAN FRANCISCO', 'SF'],
            'seahawks': ['SEAHAWKS', 'SEATTLE', 'SEA']
        }
        
        team_name_lower = team_name.lower()
        if team_name_lower not in team_keywords:
            self.logger.warning(f"Unknown team: {team_name}. Available teams: {list(team_keywords.keys())}")
            return []
        
        keywords = team_keywords[team_name_lower]
        team_markets = []
        
        try:
            all_markets = self.get_markets()
            
            for market in all_markets:
                title = market.get('title', '').upper()
                description = market.get('description', '').upper()
                
                if any(keyword in title or keyword in description for keyword in keywords):
                    team_markets.append(market)
            
            self.logger.info(f"Found {len(team_markets)} markets for {team_name}")
            
        except Exception as e:
            self.logger.error(f"Error searching for {team_name} markets: {e}")
        
        return team_markets
    
    def search_nfl_markets_by_event_type(self, event_type: str) -> List[Dict[str, Any]]:
        """Search for NFL markets by specific event type."""
        event_types = {
            'super_bowl': ['SUPER BOWL', 'SUPERBOWL', 'CHAMPIONSHIP'],
            'playoffs': ['PLAYOFFS', 'POSTSEASON', 'WILDCARD', 'DIVISION', 'CONFERENCE'],
            'regular_season': ['REGULAR SEASON', 'WEEK', 'GAME'],
            'draft': ['DRAFT', 'NFL DRAFT', 'ROOKIE'],
            'awards': ['MVP', 'OFFENSIVE PLAYER', 'DEFENSIVE PLAYER', 'ROOKIE OF THE YEAR'],
            'coaching': ['COACH', 'HEAD COACH', 'FIRING', 'HIRING']
        }
        
        event_type_lower = event_type.lower()
        if event_type_lower not in event_types:
            self.logger.warning(f"Unknown event type: {event_type}. Available types: {list(event_types.keys())}")
            return []
        
        keywords = event_types[event_type_lower]
        event_markets = []
        
        try:
            all_markets = self.get_markets()
            
            for keyword in keywords:
                try:
                    # Search for events containing the keyword
                    markets = self.get_markets()
                    filtered_markets = [m for m in markets if keyword in m.get('title', '').upper()]
                    event_markets.extend(filtered_markets)
                    self.logger.info(f"Found {len(filtered_markets)} markets for {keyword}")
                except Exception as e:
                    self.logger.warning(f"Error fetching markets for {keyword}: {e}")
            
            self.logger.info(f"Found {len(event_markets)} {event_type} markets")
            
        except Exception as e:
            self.logger.error(f"Error searching for {event_type} markets: {e}")
        
        return event_markets


def test_kalshi_client():
    """Test function for Kalshi client functionality."""
    print("Testing Kalshi API Client...")
    
    # Create client
    client = KalshiClient()
    
    # Check if credentials are configured
    if not client.api_key or not client.api_secret:
        print("⚠️  Kalshi API credentials not configured. Set KALSHI_API_KEY and KALSHI_API_SECRET environment variables.")
        return
    
    # Login
    print("🔐 Attempting to login...")
    if client.login():
        print("✅ Successfully authenticated!")
        
        # Fetch markets
        print("📊 Fetching markets...")
        markets = client.get_markets()
        
        if markets:
            print(f"✅ Found {len(markets)} total markets")
            
            # Print first 5 markets
            print("\n📋 First 5 markets:")
            for i, market in enumerate(markets[:5]):
                print(f"  {i+1}. {market.get('title', 'Unknown')} ({market.get('ticker', 'N/A')})")
                print(f"     Status: {market.get('status', 'Unknown')}")
                print(f"     Event: {market.get('event_ticker', 'N/A')}")
                print()
        else:
            print("❌ No markets found")
        
        # Search for relevant markets based on API type
        if "elections.kalshi.com" in client.base_url:
            print("🗳️  Searching for election markets...")
            election_markets = client.search_nfl_markets()  # This now searches for elections
            
            if election_markets:
                print(f"✅ Found {len(election_markets)} election-related markets")
                
                # Print first 3 election markets
                print("\n🗳️  First 3 election markets:")
                for i, market in enumerate(election_markets[:3]):
                    print(f"  {i+1}. {market.get('title', 'Unknown')} ({market.get('event_id', 'N/A')})")
                    print(f"     Status: {market.get('status', 'N/A')}")
                    print()
            else:
                print("❌ No election markets found")
            
            # Test NFL search methods (even though we're on Elections API)
            print("🏈 Testing NFL search methods...")
            
            # Test detailed NFL search
            nfl_markets_detailed = client.search_nfl_markets_detailed()
            print(f"🔍 Detailed NFL search found: {len(nfl_markets_detailed)} markets")
            
            # Test team-specific search
            patriots_markets = client.search_nfl_markets_by_team('patriots')
            print(f"🏈 Patriots markets found: {len(patriots_markets)}")
            
            # Test event type search
            super_bowl_markets = client.search_nfl_markets_by_event_type('super_bowl')
            print(f"🏆 Super Bowl markets found: {len(super_bowl_markets)}")
            
        else:
            print("🏈 Searching for NFL markets...")
            nfl_markets = client.search_nfl_markets()
            
            if nfl_markets:
                print(f"✅ Found {len(nfl_markets)} NFL-related markets")
                
                # Print first 3 NFL markets
                print("\n🏈 First 3 NFL markets:")
                for i, market in enumerate(nfl_markets[:3]):
                    print(f"  {i+1}. {market.get('title', 'Unknown')} ({market.get('ticker', 'N/A')})")
                    print(f"     Event: {market.get('event_ticker', 'N/A')}")
                    print()
            else:
                print("❌ No NFL markets found")
            
            # Test additional NFL search methods
            print("🏈 Testing additional NFL search methods...")
            
            # Test detailed NFL search
            nfl_markets_detailed = client.search_nfl_markets_detailed()
            print(f"🔍 Detailed NFL search found: {len(nfl_markets_detailed)} markets")
            
            # Test team-specific search
            chiefs_markets = client.search_nfl_markets_by_team('chiefs')
            print(f"🏈 Chiefs markets found: {len(chiefs_markets)}")
            
            # Test event type search
            playoff_markets = client.search_nfl_markets_by_event_type('playoffs')
            print(f"🏆 Playoff markets found: {len(playoff_markets)}")
            
    else:
        print("❌ Authentication failed")


if __name__ == "__main__":
    # Setup basic logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    test_kalshi_client()
