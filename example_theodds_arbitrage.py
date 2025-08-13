#!/usr/bin/env python3
"""Example script demonstrating The Odds API arbitrage detection."""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set the API key for this example
os.environ['THEODDS_API_KEY'] = '7f368349a729ac04ca1251f6ecda8d81'

from scrapers.theodds import TheOddsScraper, TheOddsClient


def analyze_nfl_odds():
    """Analyze NFL odds and find the best opportunities."""
    print("=== NFL Odds Analysis ===")
    print()
    
    # Initialize the scraper
    scraper = TheOddsScraper()
    
    # Get all NFL markets
    print("Fetching NFL markets...")
    markets = scraper.fetch_markets()
    
    if not markets:
        print("No NFL markets found.")
        return
    
    print(f"Found {len(markets)} NFL markets")
    print()
    
    # Analyze each market for best odds
    for i, market in enumerate(markets[:5]):  # Analyze first 5 markets
        print(f"Market {i+1}: {market['title']}")
        print(f"Time: {market['commence_time']}")
        
        # Extract odds data directly from market (no additional API calls)
        odds_data = scraper._extract_odds_data(market)
        
        if odds_data and 'best_odds' in odds_data:
            best_odds = odds_data['best_odds']
            
            print("Best odds across bookmakers:")
            for team, team_data in best_odds.items():
                american_odds = team_data['american_odds']
                probability = team_data['probability']
                bookmakers = team_data['bookmakers']
                
                print(f"  {team}: {american_odds:+d} ({probability:.1%})")
                
                # Show top 3 bookmakers for this team
                for bookmaker in bookmakers[:3]:
                    print(f"    - {bookmaker['title']}: {bookmaker['american_odds']:+d}")
            
            # Calculate total probability
            total_prob = sum(team_data['probability'] for team_data in best_odds.values())
            print(f"  Total Probability: {total_prob:.1%}")
            
            # Check for arbitrage opportunity
            if total_prob < 0.95:  # Less than 95% total probability
                arbitrage_pct = (1.0 - total_prob) * 100
                print(f"  🎯 ARBITRAGE OPPORTUNITY: {arbitrage_pct:.2f}%")
            elif total_prob < 1.0:
                print(f"  ⚠ Close to arbitrage: {total_prob:.1%}")
            else:
                print(f"  ✓ No arbitrage: {total_prob:.1%}")
        
        print()
    
    # Find all arbitrage opportunities
    print("=== Searching for Arbitrage Opportunities ===")
    opportunities = scraper.get_arbitrage_opportunities(min_threshold=0.01)  # 1% threshold
    
    if opportunities:
        print(f"Found {len(opportunities)} arbitrage opportunities:")
        print()
        
        for i, opp in enumerate(opportunities[:3]):  # Show first 3 opportunities
            print(f"Opportunity {i+1}: {opp['title']}")
            
            # Handle different arbitrage types
            if opp['arbitrage_type'] == 'true_arbitrage':
                details = opp['arbitrage_details']
                print(f"Type: True Arbitrage")
                print(f"Arbitrage: {details['arbitrage_percentage']:.2f}%")
                print(f"Total Probability: {details['total_probability']:.1%}")
                
                # Show recommended bets
                bets = opp['recommended_bets']
                if bets:
                    print(f"Bet per team: ${bets['bet_amount_per_team']:.2f}")
                    print(f"Total bet amount: ${bets['total_bet_amount']:.2f}")
                    print(f"Guaranteed return: ${bets['guaranteed_return']:.2f}")
                    print(f"Guaranteed profit: ${bets['guaranteed_profit']:.2f}")
                    print(f"ROI: {bets['roi_percentage']:.2f}%")
            
            elif opp['arbitrage_type'] == 'cross_bookmaker':
                details = opp['arbitrage_details']
                print(f"Type: Cross-Bookmaker Value")
                print(f"Opportunities: {details['total_opportunities']}")
                
                # Show recommended bets
                bets = opp['recommended_bets']
                if bets:
                    print(f"Total bet amount: ${bets['total_bet_amount']:.2f}")
                    print(f"Expected profit: ${bets['total_expected_profit']:.2f}")
                    print(f"ROI: {bets['roi_percentage']:.2f}%")
            
            print()
    else:
        print("No arbitrage opportunities found with current threshold.")


def compare_bookmakers():
    """Compare odds across different bookmakers."""
    print("=== Bookmaker Comparison ===")
    print()
    
    client = TheOddsClient()
    
    # Get NFL games
    nfl_games = client.get_nfl_games()
    
    if not nfl_games:
        print("No NFL games found.")
        return
    
    # Analyze first game
    game = nfl_games[0]
    print(f"Game: {game['away_team']} @ {game['home_team']}")
    print(f"Time: {game['commence_time']}")
    print()
    
    bookmakers = game.get('bookmakers', [])
    
    if not bookmakers:
        print("No bookmaker data available.")
        return
    
    print("Odds comparison across bookmakers:")
    print("-" * 60)
    print(f"{'Bookmaker':<20} {'Away Team':<15} {'Home Team':<15}")
    print("-" * 60)
    
    for bookmaker in bookmakers:
        name = bookmaker.get('title', 'Unknown')
        markets = bookmaker.get('markets', [])
        
        away_odds = home_odds = "N/A"
        
        for market in markets:
            if market.get('key') == 'h2h':
                outcomes = market.get('outcomes', [])
                for outcome in outcomes:
                    team = outcome.get('name')
                    odds = outcome.get('price')
                    
                    if team == game['away_team']:
                        away_odds = f"{odds:+d}"
                    elif team == game['home_team']:
                        home_odds = f"{odds:+d}"
        
        print(f"{name:<20} {away_odds:<15} {home_odds:<15}")
    
    print("-" * 60)


def main():
    """Main function to run examples."""
    try:
        print("The Odds API - Arbitrage Detection Examples")
        print("=" * 50)
        print()
        
        # Example 1: Analyze NFL odds
        analyze_nfl_odds()
        
        print()
        print("-" * 50)
        print()
        
        # Example 2: Compare bookmakers
        compare_bookmakers()
        
        print()
        print("Examples completed successfully!")
        print()
        print("Key takeaways:")
        print("- The Odds API provides real-time odds from multiple bookmakers")
        print("- You can compare odds across platforms to find the best value")
        print("- Arbitrage opportunities exist when total probability < 100%")
        print("- The scraper automatically normalizes American odds to probabilities")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
