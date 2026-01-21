#!/usr/bin/env python3
"""
Polymarket Near-Certain Scanner
Tasks 1-7: Fetch markets + tags + exclude + threshold + flatten + 48h window + hours/URL
"""

import requests
import json
from datetime import datetime, timezone, timedelta


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


def exclude_by_keywords(markets):
    """
    Exclude markets matching esports keywords (backup filter).
    Searches in: question, event.title, category, subcategory (case-insensitive).
    Returns (filtered_markets, excluded_markets).
    """
    esports_keywords = [
        'esports',
        'cs2',
        'cs:go',
        'dota',
        'league of legends',
        'valorant',
        'overwatch'
    ]
    
    filtered = []
    excluded = []
    
    for market in markets:
        # Extract searchable fields
        question = market.get('question', '').lower()
        event_title = market.get('event', {}).get('title', '').lower() if isinstance(market.get('event'), dict) else ''
        category = market.get('category', '').lower()
        subcategory = market.get('subcategory', '').lower()
        
        # Combine all searchable text
        searchable_text = f"{question} {event_title} {category} {subcategory}"
        
        # Check if any keyword matches
        matched_keywords = []
        for keyword in esports_keywords:
            if keyword in searchable_text:
                matched_keywords.append(keyword)
        
        if matched_keywords:
            market['_matched_keywords'] = matched_keywords  # Store for debugging
            excluded.append(market)
        else:
            filtered.append(market)
    
    return filtered, excluded


def apply_price_threshold(markets, threshold=0.95):
    """
    Keep markets where ANY outcome price >= threshold.
    
    Market data structure:
    - outcomes: stringified JSON array like '["Yes", "No"]'
    - outcomePrices: stringified JSON array like '["0.65", "0.35"]'
    
    Returns (markets_meeting_threshold, markets_below_threshold).
    """
    meeting_threshold = []
    below_threshold = []
    
    for market in markets:
        # Parse outcomes and prices (they're stringified JSON)
        outcomes_str = market.get('outcomes', '[]')
        prices_str = market.get('outcomePrices', '[]')
        
        try:
            outcomes = json.loads(outcomes_str)
            prices = json.loads(prices_str)
            
            # Convert price strings to floats
            prices = [float(p) for p in prices]
            
            # Check if ANY price meets threshold
            max_price = max(prices) if prices else 0.0
            
            if max_price >= threshold:
                # Store parsed data for later use
                market['_parsed_outcomes'] = outcomes
                market['_parsed_prices'] = prices
                market['_max_price'] = max_price
                meeting_threshold.append(market)
            else:
                below_threshold.append(market)
                
        except (json.JSONDecodeError, ValueError) as e:
            # Skip markets with malformed price data
            print(f"Warning: Skipping market due to parse error: {e}")
            below_threshold.append(market)
    
    return meeting_threshold, below_threshold


def flatten_multi_outcome_markets(markets, threshold=0.95):
    """
    Flatten multi-outcome markets to one row per outcome.
    Only keep outcomes where price >= threshold.
    
    Each row contains:
    - Original market data
    - Specific outcome name
    - YES price for that outcome
    - NO price (1 - YES price)
    
    Returns list of flattened rows.
    """
    flattened_rows = []
    
    for market in markets:
        outcomes = market.get('_parsed_outcomes', [])
        prices = market.get('_parsed_prices', [])
        
        # Ensure we have matching outcomes and prices
        if len(outcomes) != len(prices):
            print(f"Warning: Mismatched outcomes/prices for market '{market.get('question', 'N/A')}'")
            continue
        
        # Create one row per outcome that meets threshold
        for outcome, yes_price in zip(outcomes, prices):
            if yes_price >= threshold:
                row = {
                    'market': market,  # Keep reference to original market
                    'outcome': outcome,
                    'yes_price': yes_price,
                    'no_price': 1.0 - yes_price
                }
                flattened_rows.append(row)
    
    return flattened_rows


def apply_time_window(rows, window_hours=48):
    """
    Filter rows to keep only markets ending within the next window_hours.
    Exclude markets with missing endDate.
    Add hours_remaining and market_url to each row.
    
    Returns (rows_in_window, rows_outside_window, now, window_end, min_date, max_date).
    """
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(hours=window_hours)
    
    in_window = []
    outside_window = []
    all_dates = []
    
    for row in rows:
        market = row['market']
        end_date_str = market.get('endDate')
        
        # Exclude markets with missing endDate
        if not end_date_str:
            outside_window.append(row)
            continue
        
        try:
            # Parse ISO 8601 datetime
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            all_dates.append(end_date)
            
            # Check if within window
            if now <= end_date <= window_end:
                # Calculate hours remaining
                time_remaining = end_date - now
                hours_remaining = time_remaining.total_seconds() / 3600
                
                # Construct market URL using slug
                slug = market.get('slug', '')
                market_url = f"https://polymarket.com/event/{slug}" if slug else ""
                
                # Add calculated fields to row
                row['resolve_datetime'] = end_date
                row['hours_remaining'] = hours_remaining
                row['market_url'] = market_url
                
                in_window.append(row)
            else:
                outside_window.append(row)
                
        except (ValueError, AttributeError) as e:
            # Skip markets with malformed endDate
            print(f"Warning: Skipping market due to date parse error: {e}")
            outside_window.append(row)
    
    # Calculate min/max dates seen
    min_date = min(all_dates) if all_dates else None
    max_date = max(all_dates) if all_dates else None
    
    return in_window, outside_window, now, window_end, min_date, max_date


def main():
    """Test Task 7: Apply 48h time window and calculate hours/URL"""
    print("="*60)
    print("TASK 7: Apply 48h time window + calculate hours/URL")
    print("="*60)
    print()
    
    # Fetch exclusion tags
    exclusion_tags = fetch_exclusion_tags()
    print()
    
    # Fetch markets with tags included (increased sample size)
    markets = fetch_all_markets(max_markets=2000)
    print()
    
    # Apply tag-based exclusions
    print("Applying tag-based exclusions...")
    after_tags, excluded_by_tags = exclude_by_tags(markets, exclusion_tags)
    print(f"After tag exclusions: {len(after_tags)} markets remaining")
    print()
    
    # Apply keyword-based exclusions
    print("Applying keyword-based exclusions...")
    after_keywords, excluded_by_keywords = exclude_by_keywords(after_tags)
    print(f"After keyword exclusions: {len(after_keywords)} markets remaining")
    print()
    
    # Apply price threshold
    print("Applying 0.95 price threshold...")
    final_markets, below_threshold = apply_price_threshold(after_keywords, threshold=0.95)
    print(f"Markets meeting threshold: {len(final_markets)}")
    print()
    
    # Flatten multi-outcome markets
    print("Flattening multi-outcome markets...")
    flattened_rows = flatten_multi_outcome_markets(final_markets, threshold=0.95)
    print(f"Total flattened rows: {len(flattened_rows)}")
    print()
    
    # Apply 48-hour time window
    print("Applying 48-hour time window...")
    rows_in_window, rows_outside, now, window_end, min_date, max_date = apply_time_window(flattened_rows, window_hours=48)
    
    print(f"\n{'='*60}")
    print("TIME WINDOW RESULTS")
    print(f"{'='*60}")
    print(f"NOW (UTC):          {now.isoformat()}")
    print(f"WINDOW_END (UTC):   {window_end.isoformat()}")
    print(f"Before time filter: {len(flattened_rows)} rows")
    print(f"After time filter:  {len(rows_in_window)} rows")
    print(f"Outside window:     {len(rows_outside)} rows")
    if min_date and max_date:
        print(f"MIN Resolve_DateTime: {min_date.isoformat()}")
        print(f"MAX Resolve_DateTime: {max_date.isoformat()}")
    else:
        print(f"MIN/MAX Resolve_DateTime: No valid dates found")
    print(f"{'='*60}")
    
    # Show 3 sample rows
    if rows_in_window:
        print(f"\nFirst 3 rows within 48h window:\n")
        for i, row in enumerate(rows_in_window[:3], 1):
            market = row['market']
            question = market.get('question', 'N/A')
            
            print(f"{i}. {question}")
            print(f"   Outcome:           {row['outcome']}")
            print(f"   Resolve_DateTime:  {row['resolve_datetime'].isoformat()}")
            print(f"   Hours_Remaining:   {row['hours_remaining']:.2f}")
            print(f"   Market_URL:        {row['market_url']}")
            print()
        
        # Assert all samples are within 0-48 hours
        print("ASSERTION CHECK:")
        for i, row in enumerate(rows_in_window[:3], 1):
            hrs = row['hours_remaining']
            in_range = 0 <= hrs <= 48
            status = "✓ PASS" if in_range else "✗ FAIL"
            print(f"  Sample {i}: {hrs:.2f}h - {status} (0 <= Hours_Remaining <= 48)")
    else:
        print("\nNo markets found within 48-hour window in this batch.")


if __name__ == "__main__":
    main()