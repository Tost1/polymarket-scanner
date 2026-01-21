#!/usr/bin/env python3
"""
Polymarket Near-Certain Scanner - Task 1: Fetch markets with pagination
"""

import requests
import json


def fetch_all_markets(max_markets=None):
    """
    Fetch all markets from Polymarket Gamma API with pagination.
    Returns list of all market objects.
    
    Args:
        max_markets: Optional limit on total markets to fetch (for testing)
    """
    base_url = "https://gamma-api.polymarket.com/markets"
    all_markets = []
    offset = 0
    limit = 100  # Reasonable batch size
    
    print(f"Starting fetch from {base_url}")
    
    while True:
        params = {
            "limit": limit,
            "offset": offset
        }
        
        print(f"Fetching batch: offset={offset}, limit={limit}...", end=" ", flush=True)
        
        try:
            response = requests.get(base_url, params=params, timeout=30)
            print(f"Status: {response.status_code}", end=" ", flush=True)
            response.raise_for_status()
            markets = response.json()
            
            print(f"Got {len(markets)} markets")
            
            if not markets or len(markets) == 0:
                # No more markets to fetch
                print("No more markets, stopping pagination")
                break
            
            all_markets.extend(markets)
            
            # Stop if we've reached the max_markets limit
            if max_markets and len(all_markets) >= max_markets:
                print(f"Reached max_markets limit ({max_markets}), stopping")
                all_markets = all_markets[:max_markets]
                break
            
            # If we got fewer results than the limit, we've reached the end
            if len(markets) < limit:
                print(f"Received fewer than {limit} markets, stopping pagination")
                break
            
            offset += limit
            
        except requests.exceptions.RequestException as e:
            print(f"\nError fetching markets at offset {offset}: {e}")
            break
    
    return all_markets


def main():
    """Test: Print first 3 markets + total count"""
    print("Fetching markets from Polymarket (limited to 300 for testing)...")
    markets = fetch_all_markets(max_markets=300)
    
    print(f"\n{'='*60}")
    print(f"Total markets fetched: {len(markets)}")
    print(f"{'='*60}")
    print(f"\nFirst 3 markets:")
    
    for i, market in enumerate(markets[:3], 1):
        print(f"\n--- Market {i} ---")
        print(f"Question: {market.get('question', 'N/A')}")
        print(f"Slug: {market.get('slug', 'N/A')}")
        print(f"Active: {market.get('active', 'N/A')}")
        print(f"Closed: {market.get('closed', 'N/A')}")


if __name__ == "__main__":
    main()