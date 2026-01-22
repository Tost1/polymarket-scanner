# Polymarket Near-Certain Scanner (Read-only)

## Goal
Export near-certain Polymarket markets to an OnlyOffice-compatible `.xlsx` file for manual review.

## Data source
Gamma Markets API (public, read-only):
- Base: https://gamma-api.polymarket.com
- Markets endpoint: GET /markets
  - Use `closed=false` parameter to filter active markets
  - Use `include_tag=true` parameter to include tag data in response
  - Pagination: offset-based with `limit` and `offset` parameters
- Tags endpoint: GET /tags/slug/{slug} (for individual tag lookup)

## Inclusion criteria
- Market is `active=true`
- Market is `closed=false`
- YES price ≥ 0.95 OR NO price ≥ 0.95
- Time window: include only markets with Resolve_DateTime between now and now + 48 hours (rolling)

## Exclusions (must exclude if ANY apply)

### Tag-based exclusions (primary)
Exclude a market if any tag slug or label matches (case-insensitive):
- sports
- esports
- crypto

### Keyword-based exclusions (backup filter)
Apply to: `question`, `event.title`, `category`, `subcategory` (case-insensitive)

**Esports keywords:**
- esports
- cs2
- cs:go
- dota
- league of legends
- valorant
- overwatch

**Note:**  
A market is excluded if ANY of its tags OR ANY keyword matches an exclusion rule.

## Multi-outcome markets
- Flatten to 1 row per outcome
- Keep outcomes where price ≥ 0.95 (or ≤ 0.05 if inverted)
- Preserve parent event info

## Output (.xlsx for OnlyOffice)
- One sheet
- Sorted by `Resolve_DateTime` ascending (ending soonest first)

### Columns (exact order)
1. Event_Title  
2. Market_Question  
3. Outcome  
4. YES_Price  
5. NO_Price  
6. Certainty_Side (YES / NO / outcome name)  
7. Category  
8. Subcategory  
9. Volume  
10. Liquidity  
11. Resolve_DateTime  
12. Hours_Remaining  
13. Market_URL (clickable HYPERLINK formula)  
14. AI_Confidence (empty)  
15. AI_Rationale (empty)

## Non-goals
- No trading
- No live monitoring
- No AI ranking in this script

## Development workflow

### Testing requirements
- Each task must include a test command or verification step
- Claude provides the command
- You run the command locally
- You paste raw terminal output back to Claude
- No commits unless the test output is correct

### Test characteristics
- Manual verification (NOT unit tests)
- Real API data (no mocks)
- Console output must be human-readable
- Edge cases must be demonstrated when relevant

## Implementation notes (v1.0)
- Markets with empty `endDate` are skipped with warnings
- URL format: `https://polymarket.com/market/{slug}` where slug is from market data
- XLSX uses HYPERLINK formula: `=HYPERLINK("url","open")` for clickable links
- Binary markets: Certainty_Side is "YES" or "NO"
- Multi-outcome markets: Certainty_Side is the outcome name, NO_Price is empty
- Full pagination supported (no artificial limits in production)