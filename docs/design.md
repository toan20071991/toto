# Design (Gate 2)

## Metadata
- Design Version: 1.7.0
- Status: Approved for Implementation
- Linked Requirement Version: 1.7.0

## Architecture

Modules:
- `config.py`
  - Config file loading for numeric range settings.
  - Validation of config bounds.
- `parser.py`
  - CSV row parsing and structural validation.
  - Numeric value validation against configured bounds.
- `analyzer.py`
  - Date-range filtering.
  - Per-number frequency and percentage calculations.
  - Candidate set expansion from configured range including zero-frequency numbers.
  - Ranked per-number output (least to most) with bottom-count selection and tie-inclusive cutoff.
- `cli.py`
  - Argument parsing.
  - Workflow orchestration.
  - Report output.

## Data Model

Record fields:
- `draw_date`: date
- `numbers`: tuple[int, int, int, int, int, int, int]

Summary fields:
- `total_rows`
- `valid_rows`
- `invalid_rows`
- `filtered_rows`
- `total_numeric_cells`
- `unique_numbers`

Output row fields:
- `number` (candidate value from configured range)
- `frequency` (occurrence count in filtered observations)
- `percentage` (`frequency / total_numeric_cells * 100`, rounded to 3 decimal places)

## Core Algorithms

1. Parse and validate rows.
  - Input row format: `date,n1,n2,n3,n4,n5,n6,n7` (no header)
2. Load `min_value` and `max_value` from config file.
3. Validate config bounds as positive integers with `min_value <= max_value`.
4. Validate each number against configured bounds and keep row values as individual observations.
5. Resolve date window:
  - if no date range is specified: use all available data (`min(draw_date)` to `max(draw_date)`)
  - `3m`: end date minus 90 days
  - `6m`: end date minus 180 days
  - `1y`: end date minus 365 days
  - `2y`: end date minus 730 days
  - `custom`: user-provided start/end
6. Filter rows by date range.
7. Expand filtered rows into numeric observations from all `n1..n7` cells.
8. Count frequencies by number value for observed numbers.
9. Build candidate number set from config range `[min_value, max_value]`.
10. Expand counts so every candidate number exists; missing numbers get count `0`.
11. Compute percentages: `count / total_numeric_cells * 100` for each candidate number; round to 3 decimal places.
12. Rank numbers by deterministic ordering `(frequency asc, number asc)`.
13. Apply `bottom-count` cutoff: include at least `n = max(1, bottom_count)` ranked numbers.
14. If additional numbers share the same cutoff frequency, include all tied numbers.
15. Emit final ranked numbers in deterministic least-to-most order with `number`, `frequency`, and `percentage`.

## Traceability
- RQ-004, RQ-004a -> `config.py`, `parser.py`
- RQ-001..RQ-003, RQ-005 -> `parser.py`
- RQ-006..RQ-010, RQ-007a -> `analyzer.py`
- RQ-011..RQ-012 -> `cli.py`
- NFR-001..NFR-004 -> `analyzer.py`, `cli.py`, `tests/*`

## Error Handling
- Missing or unreadable config file returns a clear configuration error.
- Invalid config bounds (non-positive values or `min_value > max_value`) return a clear configuration error.
- Malformed rows are rejected and counted.
- Invalid CLI arguments raise clear parser errors.
- Empty filtered dataset returns empty result list and summary with zero numeric-cell totals.

## Design Review Checklist
- All requirements mapped to modules.
- Determinism guaranteed by explicit sorting rules.
- Boundary behaviors documented (bottom-count, tie-inclusive cutoff, never-seen numbers, percentage rounding, and empty data).
