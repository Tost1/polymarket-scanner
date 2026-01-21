#!/usr/bin/env python3
"""
Polymarket Near-Certain Scanner
Tasks 1-2: Fetch markets with pagination + Fetch tags and build slug/label map
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


def fetch_exclusion_tags():
    """
    Fetch specific exclusion tags (sports, esports, crypto) using individual lookups.
    Returns dict with found tags: {slug: {slug, label, id}}
    """
    base_url = "https://gamma-api.polymarket.com/tags/slug"
    exclusion_slugs = ['sports', 'esports', 'crypto']
    found_tags = {}
    
    print(f"Fetching exclusion tags...")
    
    for slug in exclusion_slugs:
        url = f"{base_url}/{slug}"
        print(f"  Checking '{slug}'...", end=" ", flush=True)
        
        try:
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                tag_data = response.json()
                found_tags[slug] = {
                    'slug': tag_data.get('slug', slug),
                    'label': tag_data.get('label', ''),
                    'id': tag_data.get('id', '')
                }
                print(f"✓ Found (label: '{tag_data.get('label', 'N/A')}')")
            elif response.status_code == 404:
                print(f"✗ Not found (404)")
            else:
                print(f"✗ Error (status {response.status_code})")
                
        except requests.exceptions.RequestException as e:
            print(f"✗ Error: {e}")
    
    return found_tags


def main():
    """Test Task 2: Print tag slugs/labels for sports / esports / crypto"""
    print("="*60)
    print("TASK 2: Fetch tags and build slug/label map")
    print("="*60)
    print()
    
    exclusion_tags = fetch_exclusion_tags()
    
    print(f"\n{'='*60}")
    print("EXCLUSION TAGS SUMMARY")
    print(f"{'='*60}\n")
    
    for slug in ['sports', 'esports', 'crypto']:
        print(f"--- '{slug}' ---")
        if slug in exclusion_tags:
            tag = exclusion_tags[slug]
            print(f"  Status: FOUND ✓")
            print(f"  Slug:   {tag['slug']}")
            print(f"  Label:  {tag['label']}")
            print(f"  ID:     {tag['id']}")
        else:
            print(f"  Status: NOT FOUND ✗")
        print()
    
    print(f"{'='*60}")
    print(f"Task 2 complete: {len(exclusion_tags)}/3 exclusion tags found")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()