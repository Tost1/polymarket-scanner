# HANDOFF — Polymarket Near-Certain Scanner

## Project
Repository: polymarket-scanner  
Purpose: Read-only scanner that exports near-certain Polymarket markets to OnlyOffice `.xlsx`

## Frozen Files (authoritative)
- spec.md → requirements, filters, output schema
- TODO.md → task order + testing protocol

These files override any chat memory or assumptions.

## Current Status
- Spec: FROZEN
- TODO: FROZEN
- Implementation: Task 1 COMPLETE (scanner.py created)
- Implementation: Task 2 COMPLETE (exclusion tags fetched)
- Implementation: Task 3 COMPLETE (tag-based exclusions working)
- Implementation: Task 4 COMPLETE (keyword-based backup filter working)
- Implementation: Task 5 COMPLETE (0.95 price threshold applied)
- Implementation: Task 6 COMPLETE (multi-outcome flattening working)
- Implementation: Task 7 COMPLETE (48h time window + hours/URL working)
- Implementation: Task 8 COMPLETE (XLSX export with working URLs)
- **Scanner v1.0 COMPLETE**: Full pipeline production-ready (25,208 markets → 337 exported)


## Working Mode
- Work on EXACTLY ONE task from TODO.md at a time
- No skipping tasks
- No parallel work
- No refactors unless explicitly requested

## Execution Model (CRITICAL)
- Claude writes code
- Claude ALWAYS outputs the **ENTIRE contents of any file that must change**
- Human **copies and pastes the full file verbatim**
- Human does NOT:
  - edit
  - re-indent
  - add lines
  - remove lines
  - fix formatting
- Claude provides ONE exact terminal command to run
- Human runs the command and pastes **raw terminal output**
- Claude diagnoses and fixes
- Repeat until test passes
- Only then commit and move to next task

Human is a mechanical executor, not a reviewer or editor.

## Code Constraints
- Single script unless unavoidable
- No classes unless strictly required
- No abstractions
- Small, readable functions only
- Assume previous code MAY be wrong unless explicitly shown

## Non-goals
- No trading
- No live monitoring
- No AI ranking
- No performance optimization

## Next Task
Refer to TODO.md and start with the first unchecked task.

