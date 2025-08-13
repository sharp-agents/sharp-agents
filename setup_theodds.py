#!/usr/bin/env python3
"""Setup script for The Odds API configuration."""

import os
import sys
from pathlib import Path

def setup_theodds_api():
    """Setup The Odds API configuration."""
    print("=== The Odds API Setup ===")
    print()
    
    # Check if API key is already set
    api_key = os.getenv('THEODDS_API_KEY')
    if api_key:
        print(f"✓ The Odds API key is already configured: {api_key[:8]}...")
    else:
        print("⚠ The Odds API key is not configured.")
        print()
        print("To configure The Odds API, you can:")
        print("1. Set the environment variable:")
        print("   export THEODDS_API_KEY='your_api_key_here'")
        print()
        print("2. Create a .env file in your project root with:")
        print("   THEODDS_API_KEY=your_api_key_here")
        print()
        print("3. Or set it directly in your Python code:")
        print("   os.environ['THEODDS_API_KEY'] = 'your_api_key_here'")
        print()
        
        # Ask user if they want to set it now
        response = input("Would you like to set the API key now? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            new_key = input("Enter your The Odds API key: ").strip()
            if new_key:
                os.environ['THEODDS_API_KEY'] = new_key
                print("✓ API key set for this session.")
                print("Note: This is only set for the current session.")
                print("For permanent setup, use one of the methods above.")
            else:
                print("⚠ No API key provided.")
                return False
        else:
            print("Setup cancelled. Please configure the API key manually.")
            return False
    
    print()
    print("=== Testing Connection ===")
    
    try:
        # Test the connection
        from scrapers.theodds import TheOddsClient
        
        client = TheOddsClient()
        
        # Test getting sports list
        print("Testing API connection...")
        sports = client.get_sports()
        
        if sports:
            print(f"✓ Successfully connected to The Odds API!")
            print(f"✓ Found {len(sports)} available sports")
            print()
            print("Available sports (first 10):")
            for sport in sports[:10]:
                print(f"  - {sport.get('title')} ({sport.get('key')})")
            
            # Test NFL games specifically
            print()
            print("Testing NFL games endpoint...")
            nfl_games = client.get_nfl_games()
            
            if nfl_games:
                print(f"✓ Successfully retrieved {len(nfl_games)} NFL games")
                print()
                print("Upcoming NFL games (first 3):")
                for game in nfl_games[:3]:
                    print(f"  - {game.get('away_team')} @ {game.get('home_team')}")
                    print(f"    Time: {game.get('commence_time')}")
                    print()
            else:
                print("⚠ No NFL games found (may be off-season)")
            
            print("=== Setup Complete ===")
            print("✓ The Odds API is ready to use!")
            print()
            print("You can now:")
            print("- Run 'python test_theodds_api.py' to see live data")
            print("- Use TheOddsScraper in your arbitrage analysis")
            print("- Import and use TheOddsClient in your code")
            
            return True
            
        else:
            print("⚠ No sports data received from API")
            return False
            
    except ImportError as e:
        print(f"⚠ Error importing The Odds API modules: {e}")
        print("Make sure you have installed all required dependencies:")
        print("  pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"⚠ Error testing API connection: {e}")
        print("Please check your API key and internet connection.")
        return False


def main():
    """Main setup function."""
    try:
        success = setup_theodds_api()
        if success:
            print()
            print("🎉 Setup completed successfully!")
            sys.exit(0)
        else:
            print()
            print("❌ Setup failed. Please check the errors above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print()
        print("Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during setup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
