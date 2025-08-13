#!/usr/bin/env python3
"""Monitor The Odds API usage and provide efficiency recommendations."""

import os
import sys
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set the API key for monitoring
os.environ['THEODDS_API_KEY'] = '7f368349a729ac04ca1251f6ecda8d81'

from scrapers.theodds import TheOddsClient


def monitor_api_usage():
    """Monitor API usage and provide efficiency recommendations."""
    print("=== The Odds API Usage Monitor ===")
    print()
    
    try:
        client = TheOddsClient()
        
        print("📊 Current API Status:")
        print("=" * 40)
        
        # Test sports endpoint (free)
        print("Testing sports endpoint (free)...")
        start_time = time.time()
        sports = client.get_sports()
        sports_time = time.time() - start_time
        
        if sports:
            print(f"✓ Sports endpoint working - {len(sports)} sports found")
            print(f"  Time: {sports_time:.2f}s")
            print(f"  Cost: 0 (free endpoint)")
        else:
            print("❌ Sports endpoint failed")
            return
        
        print()
        print("📈 API Usage Analysis:")
        print("=" * 40)
        
        # Test NFL endpoint (counts against quota)
        print("Testing NFL endpoint (counts against quota)...")
        start_time = time.time()
        nfl_games = client.get_nfl_games()
        nfl_time = time.time() - start_time
        
        if nfl_games:
            print(f"✓ NFL endpoint working - {len(nfl_games)} games found")
            print(f"  Time: {nfl_time:.2f}s")
            print(f"  Cost: 1 request")
            print(f"  Data per request: {len(nfl_games)} games with odds from multiple bookmakers")
        else:
            print("❌ NFL endpoint failed - likely quota exceeded")
            print()
            print("💡 Recommendations:")
            print("1. Wait for monthly quota reset")
            print("2. Upgrade to higher tier plan")
            print("3. Use cached data if available")
            return
        
        print()
        print("🎯 Efficiency Recommendations:")
        print("=" * 40)
        
        print("✅ DO:")
        print("  • Use get_nfl_games() once and cache the results")
        print("  • Process all 272 games from a single API call")
        print("  • Cache data for 5+ minutes to avoid redundant calls")
        print("  • Use sports endpoint for free data")
        print("  • Monitor usage with response headers")
        
        print()
        print("❌ DON'T:")
        print("  • Call get_odds() for each individual game")
        print("  • Make API calls in tight loops")
        print("  • Ignore rate limiting (1 second minimum between calls)")
        print("  • Forget to check remaining quota")
        
        print()
        print("📊 Usage Patterns:")
        print("=" * 40)
        
        print("Typical usage scenarios:")
        print()
        print("1. 🟢 Light Usage (50-100 requests/month):")
        print("   • Check odds 2-3 times per day")
        print("   • Cache data for 1-2 hours")
        print("   • Perfect for personal use")
        
        print()
        print("2. 🟡 Medium Usage (100-500 requests/month):")
        print("   • Check odds every hour")
        print("   • Cache data for 15-30 minutes")
        print("   • Good for active monitoring")
        
        print()
        print("3. 🔴 Heavy Usage (500+ requests/month):")
        print("   • Check odds every 5-15 minutes")
        print("   • Cache data for 5-10 minutes")
        print("   • Consider upgrading plan")
        
        print()
        print("💡 Smart Caching Strategy:")
        print("=" * 40)
        
        print("• Sports list: Cache for 24 hours (rarely changes)")
        print("• NFL games: Cache for 5-15 minutes (odds change frequently)")
        print("• Historical data: Cache for 1 hour (static)")
        print("• Use cache TTL based on data volatility")
        
        print()
        print("🚀 Upgrade Recommendations:")
        print("=" * 40)
        
        print("Current: Free tier (500 requests/month)")
        print("Next: 20K requests/month")
        print()
        print("With 20K requests/month you can:")
        print("• Check odds every 2-3 minutes")
        print("• Run multiple analysis scripts")
        print("• Monitor multiple sports")
        print("• Build real-time applications")
        
        print()
        print("📝 Implementation Tips:")
        print("=" * 40)
        
        print("1. Always check cache before making API calls")
        print("2. Implement exponential backoff for rate limits")
        print("3. Log all API usage for monitoring")
        print("4. Use batch operations when possible")
        print("5. Consider webhook notifications for real-time updates")
        
    except Exception as e:
        print(f"❌ Error monitoring API usage: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    monitor_api_usage()
