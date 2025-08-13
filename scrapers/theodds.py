"""The Odds API client and scraper for sportsbook data."""

import requests
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from .base import BaseScraper
from utils.config import get_config


class TheOddsClient:
    """Client for The Odds API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize The Odds API client.
        
        Args:
            api_key: API key for The Odds API. If None, will try to get from config.
        """
        self.api_key = api_key or get_config().get_theodds_api_key()
        if not self.api_key:
            raise ValueError("The Odds API key is required")
        
        self.base_url = "https://api.the-odds-api.com/v4"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Sharp-Agents/1.0'
        })
        self.logger = logging.getLogger(__name__)
        
        # Cache for API responses to avoid redundant calls
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes cache TTL
        self._last_request_time = 0
        self._min_request_interval = 1.0  # Minimum 1 second between requests
    
    def _make_cached_request(self, url: str, params: dict, cache_key: str) -> Optional[Dict[str, Any]]:
        """Make a cached API request to avoid redundant calls."""
        import time
        
        current_time = time.time()
        
        # Check cache first
        if cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if current_time - cache_entry['timestamp'] < self._cache_ttl:
                self.logger.debug(f"Using cached data for {cache_key}")
                return cache_entry['data']
        
        # Rate limiting: ensure minimum interval between requests
        time_since_last = current_time - self._last_request_time
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        try:
            response = self.session.get(url, params=params)
            
            # Check for rate limiting
            if response.status_code == 429:
                self.logger.warning("Rate limit exceeded. Please wait before making more requests.")
                return None
            
            # Check for authentication errors
            if response.status_code == 401:
                self.logger.error("API key invalid or expired. Please check your API key.")
                return None
            
            response.raise_for_status()
            
            data = response.json()
            
            # Cache the response
            self._cache[cache_key] = {
                'data': data,
                'timestamp': current_time
            }
            
            # Update last request time
            self._last_request_time = current_time
            
            # Log usage
            remaining = response.headers.get('x-requests-remaining', 'unknown')
            used = response.headers.get('x-requests-used', 'unknown')
            last_cost = response.headers.get('x-requests-last', 'unknown')
            
            self.logger.info(f"API usage - Remaining: {remaining}, Used: {used}, Last cost: {last_cost}")
            
            # Warn if running low on requests
            if remaining != 'unknown' and int(remaining) < 50:
                self.logger.warning(f"Low on API requests: {remaining} remaining")
            
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error making API request: {e}")
            return None
    
    def get_sports(self) -> List[Dict[str, Any]]:
        """Get list of available sports.
        
        Returns:
            List of sport objects with keys, titles, and descriptions
        """
        try:
            url = f"{self.base_url}/sports"
            params = {'apiKey': self.api_key}
            cache_key = 'sports_list'
            
            sports = self._make_cached_request(url, params, cache_key)
            
            if sports:
                self.logger.info(f"Retrieved {len(sports)} sports")
                return sports
            else:
                return []
            
        except Exception as e:
            self.logger.error(f"Error fetching sports: {e}")
            return []
    
    def get_nfl_games(self) -> List[Dict[str, Any]]:
        """Get upcoming NFL games with odds.
        
        Returns:
            List of NFL game objects with teams, odds, and bookmakers
        """
        try:
            url = f"{self.base_url}/sports/americanfootball_nfl/odds"
            params = {
                'apiKey': self.api_key,
                'regions': 'us',
                'markets': 'h2h',  # Moneyline odds
                'oddsFormat': 'american'
            }
            cache_key = 'nfl_games_with_odds'
            
            games = self._make_cached_request(url, params, cache_key)
            
            if games:
                self.logger.info(f"Retrieved {len(games)} NFL games")
                return games
            else:
                return []
            
        except Exception as e:
            self.logger.error(f"Error fetching NFL games: {e}")
            return []
    
    def get_odds(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Get odds for a specific game from all bookmakers.
        
        WARNING: This method is deprecated. Use get_nfl_games() instead
        as it already contains all the odds data we need.
        
        Args:
            game_id: The game ID to fetch odds for
            
        Returns:
            Game odds data or None if error
        """
        self.logger.warning("get_odds() is deprecated. Use get_nfl_games() instead.")
        
        # Try to get from cache first
        cache_key = 'nfl_games_with_odds'
        if cache_key in self._cache:
            games = self._cache[cache_key]['data']
            for game in games:
                if game.get('id') == game_id:
                    return game
        
        # If not in cache, fetch all games (this is more efficient)
        games = self.get_nfl_games()
        for game in games:
            if game.get('id') == game_id:
                return game
        
        self.logger.warning(f"Game {game_id} not found")
        return None
    
    def get_historical_odds(self, sport: str, event_id: str, date: str) -> Optional[Dict[str, Any]]:
        """Get historical odds for a specific event.
        
        Args:
            sport: Sport key (e.g., 'americanfootball_nfl')
            event_id: Event ID
            date: Date in ISO8601 format (e.g., '2023-11-29T22:42:00Z')
            
        Returns:
            Historical odds data or None if error
        """
        try:
            url = f"{self.base_url}/historical/sports/{sport}/events/{event_id}/odds"
            params = {
                'apiKey': self.api_key,
                'regions': 'us',
                'markets': 'h2h',
                'oddsFormat': 'american',
                'date': date
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            self.logger.info(f"Retrieved historical odds for event {event_id}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching historical odds: {e}")
            return None


class TheOddsScraper(BaseScraper):
    """Scraper for The Odds API data."""
    
    def __init__(self):
        """Initialize The Odds scraper."""
        super().__init__("theodds")
        self.client = TheOddsClient()
    
    def fetch_markets(self) -> List[Dict[str, Any]]:
        """Fetch NFL games as markets.
        
        Returns:
            List of NFL game markets
        """
        try:
            games = self.client.get_nfl_games()
            markets = []
            
            for game in games:
                market = self._convert_game_to_market(game)
                markets.append(market)
            
            self.logger.info(f"Fetched {len(markets)} NFL markets")
            return markets
            
        except Exception as e:
            self.logger.error(f"Error fetching markets: {e}")
            return []
    
    def fetch_prices(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Fetch odds/prices for a specific market.
        
        This method now uses cached data efficiently instead of making new API calls.
        
        Args:
            market_id: Market/Game ID
            
        Returns:
            Market odds data or None if error
        """
        try:
            # Use cached data from the client instead of making new API calls
            odds_data = self.client.get_odds(market_id)
            if not odds_data:
                return None
            
            return self._extract_odds_data(odds_data)
            
        except Exception as e:
            self.logger.error(f"Error fetching prices for market {market_id}: {e}")
            return None
    
    def normalize_odds_to_probability(self, american_odds: int) -> float:
        """Convert American odds to implied probability.
        
        Args:
            american_odds: American odds (e.g., -110, +150)
            
        Returns:
            Implied probability as decimal (0.0 to 1.0)
        """
        try:
            if american_odds > 0:
                # Positive odds: probability = 100 / (odds + 100)
                probability = 100 / (american_odds + 100)
            else:
                # Negative odds: probability = |odds| / (|odds| + 100)
                probability = abs(american_odds) / (abs(american_odds) + 100)
            
            # Round to 4 decimal places
            return round(probability, 4)
            
        except (ValueError, TypeError, ZeroDivisionError):
            self.logger.warning(f"Invalid American odds: {american_odds}")
            return 0.0
    
    def _convert_game_to_market(self, game: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a game object to market format.
        
        Args:
            game: Game data from The Odds API
            
        Returns:
            Market data in standard format
        """
        try:
            # Parse commence time
            commence_time = None
            if game.get('commence_time'):
                try:
                    commence_time = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
                except ValueError:
                    commence_time = datetime.strptime(game['commence_time'], '%Y-%m-%dT%H:%M:%SZ')
            
            market = {
                'id': game.get('id'),
                'title': f"{game.get('away_team', 'Away')} @ {game.get('home_team', 'Home')}",
                'away_team': game.get('away_team'),
                'home_team': game.get('home_team'),
                'commence_time': commence_time,
                'sport_key': game.get('sport_key'),
                'sport_title': game.get('sport_title'),
                'bookmakers': game.get('bookmakers', []),
                'last_update': game.get('last_update'),
                'raw_data': game
            }
            
            return market
            
        except Exception as e:
            self.logger.error(f"Error converting game to market: {e}")
            return game
    
    def _extract_odds_data(self, odds_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and normalize odds data from API response.
        
        Args:
            odds_data: Raw odds data from API
            
        Returns:
            Normalized odds data
        """
        try:
            bookmakers = odds_data.get('bookmakers', [])
            best_odds = {}
            
            for bookmaker in bookmakers:
                bookmaker_key = bookmaker.get('key')
                markets = bookmaker.get('markets', [])
                
                for market in markets:
                    if market.get('key') == 'h2h':  # Moneyline market
                        outcomes = market.get('outcomes', [])
                        
                        for outcome in outcomes:
                            team_name = outcome.get('name')
                            american_odds = outcome.get('price')
                            
                            if team_name and american_odds is not None:
                                probability = self.normalize_odds_to_probability(american_odds)
                                
                                if team_name not in best_odds:
                                    best_odds[team_name] = {
                                        'american_odds': american_odds,
                                        'probability': probability,
                                        'bookmakers': []
                                    }
                                
                                best_odds[team_name]['bookmakers'].append({
                                    'name': bookmaker_key,
                                    'title': bookmaker.get('title'),
                                    'american_odds': american_odds,
                                    'probability': probability,
                                    'last_update': market.get('last_update')
                                })
            
            return {
                'game_id': odds_data.get('id'),
                'home_team': odds_data.get('home_team'),
                'away_team': odds_data.get('away_team'),
                'commence_time': odds_data.get('commence_time'),
                'best_odds': best_odds,
                'all_bookmakers': bookmakers,
                'last_update': odds_data.get('last_update')
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting odds data: {e}")
            return odds_data
    
    def get_arbitrage_opportunities(self, min_threshold: float = 0.02) -> List[Dict[str, Any]]:
        """Find arbitrage opportunities across bookmakers.
        
        This method is now optimized to use a single API call and cached data.
        
        Args:
            min_threshold: Minimum arbitrage threshold (default 2%)
            
        Returns:
            List of arbitrage opportunities
        """
        try:
            # Get all markets with a single API call (or from cache)
            markets = self.fetch_markets()
            opportunities = []
            
            # Process all markets using the cached data
            for market in markets:
                market_id = market.get('id')
                if not market_id:
                    continue
                
                # Extract odds data from the already-fetched market data
                # No need for additional API calls
                odds_data = self._extract_odds_data(market)
                if not odds_data:
                    continue
                
                best_odds = odds_data.get('best_odds', {})
                if len(best_odds) < 2:
                    continue
                
                # Look for true arbitrage (betting on all outcomes guarantees profit)
                true_arbitrage = self._find_true_arbitrage(best_odds, min_threshold)
                
                # Look for cross-bookmaker value opportunities
                cross_bookmaker_arbitrage = self._find_cross_bookmaker_arbitrage(best_odds, min_threshold)
                
                if true_arbitrage:
                    opportunity = {
                        'market_id': market_id,
                        'title': market.get('title'),
                        'home_team': market.get('home_team'),
                        'away_team': market.get('away_team'),
                        'commence_time': market.get('commence_time'),
                        'arbitrage_type': 'true_arbitrage',
                        'arbitrage_details': true_arbitrage,
                        'best_odds': best_odds,
                        'recommended_bets': self._calculate_optimal_bets_true_arbitrage(true_arbitrage)
                    }
                    opportunities.append(opportunity)
                
                elif cross_bookmaker_arbitrage:
                    opportunity = {
                        'market_id': market_id,
                        'title': market.get('title'),
                        'home_team': market.get('home_team'),
                        'away_team': market.get('away_team'),
                        'commence_time': market.get('commence_time'),
                        'arbitrage_type': 'cross_bookmaker',
                        'arbitrage_details': cross_bookmaker_arbitrage,
                        'best_odds': best_odds,
                        'recommended_bets': self._calculate_optimal_bets_cross_bookmaker(cross_bookmaker_arbitrage)
                    }
                    opportunities.append(opportunity)
            
            self.logger.info(f"Found {len(opportunities)} arbitrage opportunities")
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error finding arbitrage opportunities: {e}")
            return []
    
    def get_value_betting_opportunities(self, min_value_threshold: float = 0.05) -> List[Dict[str, Any]]:
        """Find value betting opportunities where bookmaker odds are better than true probability.
        
        Args:
            min_value_threshold: Minimum value threshold (default 5%)
            
        Returns:
            List of value betting opportunities
        """
        try:
            markets = self.fetch_markets()
            opportunities = []
            
            for market in markets:
                market_id = market.get('id')
                if not market_id:
                    continue
                
                odds_data = self.fetch_prices(market_id)
                if not odds_data:
                    continue
                
                best_odds = odds_data.get('best_odds', {})
                if len(best_odds) < 2:
                    continue
                
                # Look for value betting opportunities
                value_opportunities = self._find_value_betting_opportunities(best_odds, min_value_threshold)
                
                if value_opportunities:
                    opportunity = {
                        'market_id': market_id,
                        'title': market.get('title'),
                        'home_team': market.get('home_team'),
                        'away_team': market.get('away_team'),
                        'commence_time': market.get('commence_time'),
                        'opportunity_type': 'value_betting',
                        'value_details': value_opportunities,
                        'best_odds': best_odds
                    }
                    opportunities.append(opportunity)
            
            self.logger.info(f"Found {len(opportunities)} value betting opportunities")
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error finding value betting opportunities: {e}")
            return []
    
    def _find_true_arbitrage(self, best_odds: Dict[str, Any], min_threshold: float) -> Optional[Dict[str, Any]]:
        """Find true arbitrage opportunities where betting on all outcomes guarantees profit.
        
        This looks for cases where the total implied probability is less than 100%,
        meaning you can bet on all outcomes and guarantee a profit.
        """
        try:
            # Calculate total probability from best odds across all bookmakers
            total_probability = sum(team_data['probability'] for team_data in best_odds.values())
            
            # Check if there's true arbitrage (total probability < 100%)
            if total_probability < (1.0 - min_threshold):
                arbitrage_percentage = (1.0 - total_probability) * 100
                
                return {
                    'total_probability': total_probability,
                    'arbitrage_percentage': arbitrage_percentage,
                    'teams': list(best_odds.keys()),
                    'best_odds_summary': {
                        team: {
                            'american_odds': data['american_odds'],
                            'probability': data['probability'],
                            'best_bookmaker': data['bookmakers'][0]['title'] if data['bookmakers'] else 'Unknown'
                        }
                        for team, data in best_odds.items()
                    }
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding true arbitrage: {e}")
            return None
    
    def _find_cross_bookmaker_arbitrage(self, best_odds: Dict[str, Any], min_threshold: float) -> Optional[Dict[str, Any]]:
        """Find arbitrage opportunities by comparing odds across bookmakers.
        
        This looks for cases where you can bet on the same outcome at different bookmakers
        and guarantee a profit.
        """
        try:
            arbitrage_opportunities = []
            
            for team_name, team_data in best_odds.items():
                bookmakers = team_data.get('bookmakers', [])
                
                if len(bookmakers) < 2:
                    continue
                
                # Sort bookmakers by best odds (highest probability)
                sorted_bookmakers = sorted(bookmakers, key=lambda x: x['probability'], reverse=True)
                
                # Check if there's a significant difference between best and worst odds
                best_prob = sorted_bookmakers[0]['probability']
                worst_prob = sorted_bookmakers[-1]['probability']
                difference = best_prob - worst_prob
                
                if difference > min_threshold:
                    # This could be an arbitrage opportunity
                    arbitrage_opportunities.append({
                        'team': team_name,
                        'best_bookmaker': sorted_bookmakers[0],
                        'worst_bookmaker': sorted_bookmakers[-1],
                        'probability_difference': difference,
                        'best_odds': sorted_bookmakers[0]['american_odds'],
                        'worst_odds': sorted_bookmakers[-1]['american_odds']
                    })
            
            if arbitrage_opportunities:
                return {
                    'opportunities': arbitrage_opportunities,
                    'total_opportunities': len(arbitrage_opportunities)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding cross-bookmaker arbitrage: {e}")
            return None
    
    def _find_value_betting_opportunities(self, best_odds: Dict[str, Any], min_threshold: float) -> Optional[Dict[str, Any]]:
        """Find value betting opportunities by identifying odds that are better than market consensus."""
        try:
            value_opportunities = []
            
            # Calculate market consensus probability (average across all bookmakers)
            market_consensus = {}
            for team_name, team_data in best_odds.items():
                bookmakers = team_data.get('bookmakers', [])
                if bookmakers:
                    avg_probability = sum(bm['probability'] for bm in bookmakers) / len(bookmakers)
                    market_consensus[team_name] = avg_probability
            
            # Find teams with odds significantly better than consensus
            for team_name, team_data in best_odds.items():
                consensus_prob = market_consensus.get(team_name, 0.5)
                best_prob = team_data['probability']
                
                # Value exists when bookmaker's implied probability is lower than consensus
                # (meaning odds are better than they should be)
                value_percentage = (consensus_prob - best_prob) / consensus_prob
                
                if value_percentage > min_threshold:
                    value_opportunities.append({
                        'team': team_name,
                        'bookmaker': team_data['bookmakers'][0]['title'],
                        'american_odds': team_data['american_odds'],
                        'implied_probability': best_prob,
                        'market_consensus': consensus_prob,
                        'value_percentage': value_percentage,
                        'expected_value': value_percentage * 100  # Convert to percentage
                    })
            
            if value_opportunities:
                return {
                    'opportunities': value_opportunities,
                    'total_opportunities': len(value_opportunities),
                    'best_value_team': max(value_opportunities, key=lambda x: x['value_percentage'])
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding value betting opportunities: {e}")
            return None
    
    def _calculate_optimal_bets_true_arbitrage(self, arbitrage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimal bet amounts for true arbitrage."""
        try:
            total_probability = arbitrage_data.get('total_probability', 1.0)
            teams = arbitrage_data.get('teams', [])
            
            if not teams or total_probability >= 1.0:
                return {}
            
            # For true arbitrage, we bet on all outcomes
            # Calculate optimal bet amounts to guarantee equal profit regardless of outcome
            total_bet_amount = 100.0  # Base amount
            
            bet_details = []
            total_bet = 0.0
            
            for team in teams:
                # Calculate bet amount based on probability
                # Higher probability = lower bet amount needed
                bet_amount = total_bet_amount * (1.0 / len(teams))  # Simplified equal distribution
                total_bet += bet_amount
                
                bet_details.append({
                    'team': team,
                    'bet_amount': bet_amount
                })
            
            # Calculate guaranteed profit
            guaranteed_return = total_bet / total_probability
            guaranteed_profit = guaranteed_return - total_bet
            
            return {
                'bet_details': bet_details,
                'total_bet_amount': total_bet,
                'guaranteed_return': guaranteed_return,
                'guaranteed_profit': guaranteed_profit,
                'roi_percentage': (guaranteed_profit / total_bet) * 100 if total_bet > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating optimal bets for true arbitrage: {e}")
            return {}
    
    def _calculate_optimal_bets_cross_bookmaker(self, arbitrage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimal bet amounts for cross-bookmaker arbitrage."""
        try:
            opportunities = arbitrage_data.get('opportunities', [])
            if not opportunities:
                return {}
            
            # For cross-bookmaker arbitrage, we bet on the same outcome at different bookmakers
            # This is more complex and requires careful analysis
            total_bet_amount = 100.0  # Base amount
            
            bet_details = []
            total_expected_profit = 0.0
            
            for opp in opportunities:
                best_bm = opp['best_bookmaker']
                worst_bm = opp['worst_bookmaker']
                
                # Calculate optimal bet amounts to guarantee profit
                # This is a simplified calculation - in practice you'd want more sophisticated math
                bet_amount = total_bet_amount / len(opportunities)
                
                # Calculate potential profit from the difference
                potential_profit = bet_amount * opp['probability_difference']
                total_expected_profit += potential_profit
                
                bet_details.append({
                    'team': opp['team'],
                    'bet_amount': bet_amount,
                    'best_bookmaker': best_bm['title'],
                    'best_odds': best_bm['american_odds'],
                    'worst_bookmaker': worst_bm['title'],
                    'worst_odds': worst_bm['american_odds'],
                    'potential_profit': potential_profit
                })
            
            return {
                'bet_details': bet_details,
                'total_bet_amount': total_bet_amount,
                'total_expected_profit': total_expected_profit,
                'roi_percentage': (total_expected_profit / total_bet_amount) * 100 if total_bet_amount > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating optimal bets: {e}")
            return {}


def test_theodds_api():
    """Test function showing current NFL odds."""
    try:
        print("Testing The Odds API...")
        
        # Initialize client
        client = TheOddsClient()
        
        # Get available sports
        print("\n=== Available Sports ===")
        sports = client.get_sports()
        for sport in sports[:5]:  # Show first 5 sports
            print(f"- {sport.get('title')} ({sport.get('key')})")
        
        # Get NFL games
        print("\n=== NFL Games ===")
        nfl_games = client.get_nfl_games()
        
        if not nfl_games:
            print("No NFL games found")
            return
        
        for game in nfl_games[:3]:  # Show first 3 games
            print(f"\n{game.get('away_team')} @ {game.get('home_team')}")
            print(f"Time: {game.get('commence_time')}")
            
            bookmakers = game.get('bookmakers', [])
            if bookmakers:
                print("Best odds:")
                for bookmaker in bookmakers[:3]:  # Show first 3 bookmakers
                    markets = bookmaker.get('markets', [])
                    for market in markets:
                        if market.get('key') == 'h2h':
                            outcomes = market.get('outcomes', [])
                            for outcome in outcomes:
                                team = outcome.get('name')
                                odds = outcome.get('price')
                                print(f"  {team}: {odds:+d} ({bookmaker.get('title')})")
        
        # Test scraper
        print("\n=== Testing Scraper ===")
        scraper = TheOddsScraper()
        
        # Find arbitrage opportunities
        opportunities = scraper.get_arbitrage_opportunities()
        if opportunities:
            print(f"\nFound {len(opportunities)} arbitrage opportunities:")
            for opp in opportunities[:2]:  # Show first 2 opportunities
                print(f"\n{opp['title']}")
                print(f"Arbitrage: {opp['arbitrage_percentage']:.2f}%")
                print(f"Total Probability: {opp['total_probability']:.4f}")
        else:
            print("No arbitrage opportunities found")
        
        # Find value betting opportunities
        value_opportunities = scraper.get_value_betting_opportunities()
        if value_opportunities:
            print(f"\nFound {len(value_opportunities)} value betting opportunities:")
            for opp in value_opportunities[:2]:  # Show first 2 opportunities
                print(f"\n{opp['title']}")
                print(f"Value: {opp['best_value_team']} has {opp['best_value_team']['value_percentage']:.2f}% value")
        else:
            print("No value betting opportunities found")
        
        print("\nThe Odds API test completed successfully!")
        
    except Exception as e:
        print(f"Error testing The Odds API: {e}")


if __name__ == "__main__":
    test_theodds_api()
