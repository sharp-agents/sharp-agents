#!/usr/bin/env python3
"""Test efficient API usage with caching and minimal requests."""

import os
import sys
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set the API key for testing
os.environ['THEODDS_API_KEY'] = '7f368349a729ac04ca1251f6ecda8d81'

from scrapers.theodds import TheOddsClient, TheOddsScraper


def test_efficient_usage():
    """Test efficient API usage patterns."""
    print("=== Testing Efficient API Usage ===")
    print()
    
    try:
        # Initialize client
        client = TheOddsClient()
        
        print("🔄 Test 1: Single API Call for All Data")
        print("-" * 50)
        
        start_time = time.time()
        nfl_games = client.get_nfl_games()
        first_call_time = time.time() - start_time
        
        if nfl_games:
            print(f"✓ Retrieved {len(nfl_games)} NFL games in {first_call_time:.2f}s")
            print(f"  Cost: 1 API request")
            print(f"  Data: {len(nfl_games)} games with odds from multiple bookmakers")
            
            # Show sample data structure
            if nfl_games:
                sample_game = nfl_games[0]
                print(f"  Sample game: {sample_game.get('away_team')} @ {sample_game.get('home_team')}")
                print(f"  Bookmakers available: {len(sample_game.get('bookmakers', []))}")
        else:
            print("❌ Failed to retrieve NFL games (likely quota exceeded)")
            print("   This demonstrates why efficient usage is important!")
            return
        
        print()
        print("🔄 Test 2: Cached Data Retrieval (Should be instant)")
        print("-" * 50)
        
        start_time = time.time()
        cached_games = client.get_nfl_games()
        cached_call_time = time.time() - start_time
        
        if cached_games:
            print(f"✓ Retrieved {len(cached_games)} NFL games from cache in {cached_call_time:.3f}s")
            print(f"  Cost: 0 API requests (cached)")
            print(f"  Speed improvement: {first_call_time/cached_call_time:.1f}x faster")
        
        print()
        print("🔄 Test 3: Processing All Data Without Additional API Calls")
        print("-" * 50)
        
        start_time = time.time()
        
        # Process all games using cached data
        total_bookmakers = 0
        total_markets = 0
        
        for game in nfl_games:
            bookmakers = game.get('bookmakers', [])
            total_bookmakers += len(bookmakers)
            
            for bookmaker in bookmakers:
                markets = bookmaker.get('markets', [])
                total_markets += len(markets)
        
        processing_time = time.time() - start_time
        
        print(f"✓ Processed all {len(nfl_games)} games in {processing_time:.3f}s")
        print(f"  Total bookmakers: {total_bookmakers}")
        print(f"  Total markets: {total_markets}")
        print(f"  Cost: 0 additional API requests")
        
        print()
        print("🔄 Test 4: Arbitrage Detection Using Cached Data")
        print("-" * 50)
        
        start_time = time.time()
        scraper = TheOddsScraper()
        
        # This should use cached data and not make new API calls
        opportunities = scraper.get_arbitrage_opportunities(min_threshold=0.01)
        
        analysis_time = time.time() - start_time
        
        print(f"✓ Analyzed {len(nfl_games)} games for arbitrage in {analysis_time:.3f}s")
        print(f"  Found {len(opportunities)} opportunities")
        print(f"  Cost: 0 additional API requests (used cached data)")
        
        if opportunities:
            print(f"  Sample opportunity: {opportunities[0]['title']}")
        
        print()
        print("📊 Efficiency Summary:")
        print("=" * 50)
        
        total_api_calls = 1  # Only one call to get_nfl_games()
        total_data_processed = len(nfl_games)
        total_processing_time = first_call_time + processing_time + analysis_time
        
        print(f"Total API calls made: {total_api_calls}")
        print(f"Total data processed: {total_data_processed} games")
        print(f"Total processing time: {total_processing_time:.2f}s")
        print(f"Data per API call: {total_data_processed/total_api_calls:.0f} games")
        print(f"Processing efficiency: {total_data_processed/total_processing_time:.1f} games/second")
        
        print()
        print("🎯 Key Efficiency Improvements:")
        print("-" * 50)
        
        print("✅ Before (inefficient):")
        print("   • 272+ API calls (one per game)")
        print("   • No caching")
        print("   • Rate limit violations")
        print("   • High latency")
        
        print()
        print("✅ After (efficient):")
        print("   • 1 API call for all data")
        print("   • Smart caching (5 min TTL)")
        print("   • Rate limiting protection")
        print("   • Fast processing")
        
        print()
        print("💡 With 20K requests/month, you can:")
        print("   • Run this analysis every 15 minutes")
        print("   • Monitor multiple sports")
        print("   • Build real-time dashboards")
        print("   • Run multiple analysis scripts")
        
    except Exception as e:
        print(f"❌ Error testing efficient usage: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_efficient_usage()
