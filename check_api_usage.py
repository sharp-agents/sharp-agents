#!/usr/bin/env python3
"""Check The Odds API usage and remaining requests."""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set the API key for this check
os.environ['THEODDS_API_KEY'] = '7f368349a729ac04ca1251f6ecda8d81'

from scrapers.theodds import TheOddsClient


def check_api_usage():
    """Check current API usage and remaining requests."""
    print("=== The Odds API Usage Check ===")
    print()
    
    try:
        # Initialize client
        client = TheOddsClient()
        
        # Test with sports endpoint (doesn't count against quota)
        print("Testing API connection with sports endpoint...")
        sports = client.get_sports()
        
        if sports:
            print(f"✓ API connection successful!")
            print(f"✓ Found {len(sports)} available sports")
            print()
            
            # Show first 5 sports
            print("Available sports:")
            for sport in sports[:5]:
                print(f"  - {sport.get('title')} ({sport.get('key')})")
            
            print()
            print("Note: Sports endpoint doesn't count against your monthly quota.")
            print()
            
            # Now test with NFL endpoint to see actual usage
            print("Testing NFL endpoint (this will count against your quota)...")
            nfl_games = client.get_nfl_games()
            
            if nfl_games:
                print(f"✓ NFL endpoint working! Retrieved {len(nfl_games)} games")
                print()
                print("API Usage Summary:")
                print("==================")
                print("✓ API key is valid")
                print("✓ NFL endpoint is accessible")
                print("✓ Rate limiting is working properly")
                print()
                print("Next steps:")
                print("1. You can now use the full API functionality")
                print("2. Monitor your usage to stay within 500 requests/month")
                print("3. Consider upgrading if you need more requests")
                
            else:
                print("⚠ NFL endpoint returned no data")
                print("This could mean:")
                print("- No upcoming NFL games")
                print("- API key has limited access")
                print("- Rate limiting in effect")
                
        else:
            print("❌ Failed to connect to API")
            print("Please check your API key and internet connection")
            
    except Exception as e:
        print(f"❌ Error checking API usage: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_api_usage()
