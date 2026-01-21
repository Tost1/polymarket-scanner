#!/usr/bin/env python3
"""
Polymarket Near-Certain Scanner
Tasks 1-3: Fetch markets + tags + exclude by tag slugs
"""

import requests
import json


def fetch_all_markets(max_markets=None):
    """
    Fetch all markets from Polymarket Gamma API with pagination.
    Returns list of all market objects with tags included.
    
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
            "offset": offset,
            "closed": "false",
            "include_tag": "true"  # CRITICAL: includes tags in response
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
                print(f"✓ Found (label: '{tag_data.get('label', 'N/A')}', ID: {tag_data.get('id')})")
            elif response.status_code == 404:
                print(f"✗ Not found (404)")
            else:
                print(f"✗ Error (status {response.status_code})")
                
        except requests.exceptions.RequestException as e:
            print(f"✗ Error: {e}")
    
    return found_tags


def exclude_by_tags(markets, exclusion_tags):
    """
    Exclude markets that have any of the exclusion tags.
    Tags are now included in market objects via include_tag=true.
    Returns (filtered_markets, excluded_markets).
    """
    # Build set of exclusion tag IDs and slugs/labels (case-insensitive)
    exclusion_ids = set(int(tag['id']) for tag in exclusion_tags.values() if tag['id'])
    exclusion_slugs = set(tag['slug'].lower() for tag in exclusion_tags.values())
    exclusion_labels = set(tag['label'].lower() for tag in exclusion_tags.values())
    
    filtered = []
    excluded = []
    
    for market in markets:
        # Get tags array from market (now included with include_tag=true)
        market_tags = market.get('tags', [])
        
        # Check if any market tag matches exclusion criteria
        has_excluded_tag = False
        matched_tags = []
        
        for tag in market_tags:
            tag_id = tag.get('id')
            tag_slug = tag.get('slug', '').lower()
            tag_label = tag.get('label', '').lower()
            
            # Match on ID, slug, or label
            if (tag_id in exclusion_ids or 
                tag_slug in exclusion_slugs or 
                tag_label in exclusion_labels):
                has_excluded_tag = True
                matched_tags.append(tag)
        
        if has_excluded_tag:
            market['_matched_tags'] = matched_tags  # Store for debugging
            excluded.append(market)
        else:
            filtered.append(market)
    
    return filtered, excluded


def main():
    """Test Task 3: Exclude by tag slugs and print counts + sample excluded titles"""
    print("="*60)
    print("TASK 3: Exclude by tag slugs (sports/esports/crypto)")
    print("="*60)
    print()
    
    # Fetch exclusion tags
    exclusion_tags = fetch_exclusion_tags()
    print()
    
    # Fetch markets with tags included
    markets = fetch_all_markets(max_markets=300)
    print()
    
    # Apply exclusions
    print("Applying tag-based exclusions...")
    filtered_markets, excluded_markets = exclude_by_tags(markets, exclusion_tags)
    
    print(f"\n{'='*60}")
    print("EXCLUSION RESULTS")
    print(f"{'='*60}")
    print(f"Before exclusion: {len(markets)} markets")
    print(f"After exclusion:  {len(filtered_markets)} markets")
    print(f"Excluded:         {len(excluded_markets)} markets")
    print(f"{'='*60}")
    
    # Show 3 excluded market titles
    if excluded_markets:
        print(f"\nFirst 3 excluded market titles:\n")
        for i, market in enumerate(excluded_markets[:3], 1):
            question = market.get('question', 'N/A')
            matched_tags = market.get('_matched_tags', [])
            tag_info = ', '.join([f"{t.get('label', 'N/A')} (ID:{t.get('id')})" for t in matched_tags])
            print(f"{i}. {question}")
            print(f"   Excluded by tags: [{tag_info}]")
            print()
    else:
        print("\nNo markets were excluded.")


if __name__ == "__main__":
    main()