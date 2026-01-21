# TODO (Scanner v1)

## Testing Protocol (MANDATORY)
For each task:
1. Claude outputs code + exact command to run
2. You paste code into files and run the command
3. You paste raw terminal output back to Claude
4. Claude fixes or confirms
5. Only then: commit and move to the next task

No interpretation. No debugging by you.

---

## Tasks

[PASS] 1. Fetch markets from GET /markets (handle pagination)  
    TEST: Print first 3 markets + total count
    NOTES: Offset-based pagination (limit=100). max_markets=300 for testing. Full fetch in final pipeline.

[PASS] 2. Fetch tags from GET /tags → build slug/label map  
    TEST: Print tag slugs/labels for sports / esports / crypto
    NOTES: Used /tags/slug/{slug} endpoint for direct lookups. Found all 3: sports (ID:1), esports (ID:64), crypto (ID:21).

[PASS] 3. Exclude by tag slugs (sports / esports / crypto ONLY)  
    TEST: Print count before/after + 3 excluded market titles
    NOTES: Used include_tag=true param on /markets endpoint. Excluded 212/300 markets (sports ID:1, esports ID:64, crypto ID:21).

[PASS] 4. Exclude by keywords (esports backup filter ONLY)  
    TEST: Print excluded titles caught by keyword filter
    NOTES: Keyword filter working correctly. 0 additional exclusions (all esports already caught by tag filter in Task 3).

[PASS] 5. Apply 0.95 threshold on outcome prices  
    TEST: Print count meeting threshold + 3 example markets
    NOTES: 64/88 markets meet threshold (≥0.95). Prices correctly parsed from stringified JSON arrays.

[ ] 6. Flatten multi-outcome markets to rows  
    TEST: Show before/after for 1 multi-outcome market

[ ] 7. Calculate Hours_Remaining + construct Market_URL  
    TEST: Print 3 rows with URLs + hours remaining

[ ] 8. Export to markets_raw.xlsx (sorted by Resolve_DateTime)  
    TEST: Open file in OnlyOffice and verify:
          - Column order
          - Sort order
          - Clickable URLs

---

## Completion Gate
After all tasks pass:
- Run full pipeline once
- Scanner is approved as v1.0
