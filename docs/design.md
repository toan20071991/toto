# Design (Gate 2)

## Metadata
- Design Version: 1.9.0
- Status: Approved for Implementation
- Linked Requirement Version: 1.9.0

## Architecture

Modules:
- `config.py`
  - Config file loading for numeric range settings (`config/range.json`).
  - Config file loading for analyzer execution parameters (`config/analyzer_config.json`).
  - Validation of config bounds and configuration parameters.
- `parser.py`
  - CSV row parsing and structural validation.
  - Numeric value validation against configured bounds.
- `analyzer.py`
  - Date-range filtering.
  - Per-number frequency and percentage calculations.
  - Candidate set expansion from configured range including zero-frequency numbers.
  - Ranked per-number output: least-to-most with `bottom-count` selection or most-to-least with `top-count` selection and tie-inclusive cutoff.
- `cli.py`
  - Short-form CLI argument parsing (supports zero arguments, single `--config-file` / positional config file path, or full explicit CLI arguments).
  - Merges CLI flags over JSON configuration parameters.
  - Workflow orchestration and CSV output generation.

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

Analyzer Configuration Schema (`analyzer_config.json`):
- `input`: string (default `"output/toto_results.csv"`) - Input CSV path.
- `output`: string (default `"output/analyze_result.csv"`) - Output CSV path.
- `range_config`: string (default `"config/range.json"`) - Path to numeric range configuration JSON file.
- `mode`: string (`"least"` or `"most"`, default `"least"`) - Ranking mode.
- `bottom_count`: integer (default `10`) - Minimum least-appearing rows to output.
- `top_count`: integer (optional) - Minimum most-appearing rows to output.
- `window`: string (optional, `"3m"`, `"6m"`, `"1y"`, `"2y"`, `"custom"`, or `null`).
- `start_date`: string (optional `YYYY-MM-DD`).
- `end_date`: string (optional `YYYY-MM-DD`).

## Core Algorithms

1. **Configuration Resolution Order**:
   - Check if an explicit config file path is passed via CLI (`--config-file` or single positional argument).
   - If no config file path is passed, check if default file `config/analyzer_config.json` exists and load it.
   - Parse JSON configuration file to extract default parameters (`input`, `output`, `range_config`, `mode`, `bottom_count`, `top_count`, `window`, `start_date`, `end_date`).
   - Merge explicit CLI options over JSON configuration file values (CLI options override JSON config).
   - Apply fallback defaults for any remaining unspecified parameters (`input="output/toto_results.csv"`, `output="output/analyze_result.csv"`, `range_config="config/range.json"`).

2. Parse and validate input rows from resolved `input` CSV.
3. Load `min_value` and `max_value` from resolved `range_config` path.
4. Validate config bounds as positive integers with `min_value <= max_value`.
5. Validate each number against configured bounds and keep row values as individual observations.
6. Resolve date window:
  - if no date range is specified: use all available data (`min(draw_date)` to `max(draw_date)`)
  - `3m`: end date minus 90 days
  - `6m`: end date minus 180 days
  - `1y`: end date minus 365 days
  - `2y`: end date minus 730 days
  - `custom`: user-provided start/end
7. Filter rows by date range.
8. Expand filtered rows into numeric observations from all `n1..n7` cells.
9. Count frequencies by number value for observed numbers.
10. Build candidate number set from config range `[min_value, max_value]`.
11. Expand counts so every candidate number exists; missing numbers get count `0`.
12. Compute percentages: `count / total_numeric_cells * 100` for each candidate number; round to 3 decimal places.
13. Rank numbers by deterministic ordering:
  - **Least-Appearing Mode** (`mode="least"`): sort candidates by `(frequency asc, number asc)`.
  - **Most-Appearing Mode** (`mode="most"`): sort candidates by `(frequency desc, number asc)`.
14. Apply count cutoff: include at least `n = max(1, count)` ranked numbers.
15. If additional numbers share the same cutoff frequency, include all tied numbers.
16. Emit final ranked numbers in deterministic order (`least` or `most`) to resolved `output` CSV path with `rank`, `number`, `frequency`, and `percentage`.

## Traceability
- RQ-004, RQ-004a -> `config.py`, `parser.py`
- RQ-001..RQ-003, RQ-005 -> `parser.py`
- RQ-006..RQ-010, RQ-007a, RQ-009a -> `analyzer.py`
- RQ-011..RQ-012, RQ-013, RQ-013a -> `config.py`, `cli.py`
- NFR-001..NFR-004 -> `analyzer.py`, `cli.py`, `tests/*`

## Error Handling
- Missing or unreadable range config file returns a clear configuration error.
- Missing custom analyzer config file specified explicitly on CLI returns a clear file error.
- Invalid config bounds (non-positive values or `min_value > max_value`) return a clear configuration error.
- Malformed rows are rejected and counted.
- Invalid CLI arguments raise clear parser errors.
- Empty filtered dataset returns empty result list and summary with zero numeric-cell totals.

## Design Review Checklist
- All requirements mapped to modules.
- Short-form execution supported with zero arguments or single config file argument.
- Determinism guaranteed by explicit sorting rules for both least-appearing and most-appearing modes.
- Boundary behaviors documented (bottom-count, top-count, tie-inclusive cutoff, never-seen numbers, percentage rounding, and empty data).
