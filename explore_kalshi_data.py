#!/usr/bin/env python3
"""
Explore Kalshi API data from working endpoints.
"""

import sys
from pathlib import Path
import requests
import json

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.config import get_config


def explore_kalshi_data():
    """Explore the working Kalshi API endpoints."""
    
    try:
        config = get_config()
        api_url = config.KALSHI_API_URL
        
        print("🔍 Exploring Kalshi API Data")
        print("=" * 50)
        print(f"API URL: {api_url}")
        print()
        
        # Test 1: Events endpoint
        print("1️⃣ Events Data")
        print("-" * 30)
        
        try:
            response = requests.get(f"{api_url}/events", timeout=30)
            print(f"Status: {response.status_code}, Size: {len(response.text)} chars")
            
            if response.status_code == 200 and response.text.strip():
                events_data = response.json()
                print(f"Response keys: {list(events_data.keys())}")
                
                if 'events' in events_data and events_data['events']:
                    events = events_data['events']
                    print(f"Number of events: {len(events)}")
                    
                    # Show first few events
                    for i, event in enumerate(events[:3]):
                        print(f"\nEvent {i+1}:")
                        print(f"  ID: {event.get('id', 'N/A')}")
                        print(f"  Title: {event.get('title', 'N/A')}")
                        print(f"  Status: {event.get('status', 'N/A')}")
                        print(f"  End Date: {event.get('end_date', 'N/A')}")
                        
                        # Show available keys
                        available_keys = list(event.keys())
                        print(f"  Available fields: {available_keys[:10]}...")
                        
                else:
                    print("No events found in response")
                    
        except Exception as e:
            print(f"Error exploring events: {e}")
        
        print()
        
        # Test 2: Series endpoint
        print("2️⃣ Series Data")
        print("-" * 30)
        
        try:
            response = requests.get(f"{api_url}/series", timeout=30)
            print(f"Status: {response.status_code}, Size: {len(response.text)} chars")
            
            if response.status_code == 200 and response.text.strip():
                series_data = response.json()
                print(f"Response keys: {list(series_data.keys())}")
                
                if 'series' in series_data and series_data['series']:
                    series_list = series_data['series']
                    print(f"Number of series: {len(series_list)}")
                    
                    # Show first few series
                    for i, series in enumerate(series_list[:3]):
                        print(f"\nSeries {i+1}:")
                        print(f"  ID: {series.get('id', 'N/A')}")
                        print(f"  Title: {series.get('title', 'N/A')}")
                        print(f"  Status: {series.get('status', 'N/A')}")
                        
                        # Show available keys
                        available_keys = list(series.keys())
                        print(f"  Available fields: {available_keys[:10]}...")
                        
                else:
                    print("No series found in response")
                    
        except Exception as e:
            print(f"Error exploring series: {e}")
        
        print()
        
        # Test 3: Trades endpoint
        print("3️⃣ Trades Data")
        print("-" * 30)
        
        try:
            response = requests.get(f"{api_url}/trades", timeout=30)
            print(f"Status: {response.status_code}, Size: {len(response.text)} chars")
            
            if response.status_code == 200 and response.text.strip():
                trades_data = response.json()
                print(f"Response keys: {list(trades_data.keys())}")
                
                if 'trades' in trades_data and trades_data['trades']:
                    trades = trades_data['trades']
                    print(f"Number of trades: {len(trades)}")
                    
                    # Show first few trades
                    for i, trade in enumerate(trades[:3]):
                        print(f"\nTrade {i+1}:")
                        print(f"  ID: {trade.get('id', 'N/A')}")
                        print(f"  Contract ID: {trade.get('contract_id', 'N/A')}")
                        print(f"  Price: {trade.get('price', 'N/A')}")
                        print(f"  Size: {trade.get('size', 'N/A')}")
                        print(f"  Side: {trade.get('side', 'N/A')}")
                        
                        # Show available keys
                        available_keys = list(trade.keys())
                        print(f"  Available fields: {available_keys[:10]}...")
                        
                else:
                    print("No trades found in response")
                    
        except Exception as e:
            print(f"Error exploring trades: {e}")
        
        print()
        print("✅ Kalshi API exploration completed!")
        
    except Exception as e:
        print(f"❌ Exploration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    explore_kalshi_data()
