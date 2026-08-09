# Requirements (Gate 1)

## Metadata
- Requirement Version: 1.9.0
- Status: Approved for Implementation
- Effective Date: 2026-08-09
- Owner: Project Team

## Functional Requirements
- RQ-001: The system shall read input CSV files where every row matches `date,n1,n2,n3,n4,n5,n6,n7`.
- RQ-002: The system shall reject malformed rows and track invalid row counts.
- RQ-003: The system shall validate `date` using `YYYY-MM-DD`.
- RQ-004: The system shall load numeric range settings from a config file and validate each number `n1..n7` against that configured range.
- RQ-004a: The configured range bounds shall be positive integers with `min_value <= max_value`.
- RQ-005: The system shall treat each valid `n1..n7` value as an individual observation for frequency analysis.
- RQ-006: The system shall support date filtering with presets `3m`, `6m`, `1y`, `2y`, and custom start/end range; if no date range is specified, filtering shall include all available data.
- RQ-007: The system shall compute frequency by number value across all filtered valid numeric cells (`n1..n7`).
- RQ-007a: The frequency candidate set shall include every integer in configured range [`min_value`, `max_value`], and numbers not present in filtered data shall have frequency 0.
- RQ-008: The system shall compute percentage of each number over total filtered valid numeric cells, rounded to 3 decimal places.
- RQ-009: The system shall rank numbers from least appearance to most appearance when given an integer input `bottom-count` meaning the minimum number of least-appearing ranked number rows to output.
- RQ-009a: The system shall rank numbers from most appearance to least appearance when given an integer input `top-count` meaning the minimum number of most-appearing ranked number rows to output (highest frequency ranked first).
- RQ-010: The system shall use deterministic tie handling; when multiple numbers share the same cutoff rank, all tied numbers shall be included in output.
- RQ-011: The system shall export result CSV including ranked number output with frequency and percentage values generated from `bottom-count` or `top-count` selection.
- RQ-012: The system shall produce summary metrics: total rows, valid rows, invalid rows, filtered rows, total numeric cells analyzed, unique numbers.
- RQ-013: The system shall support loading all analyzer parameters from a JSON configuration file (default: `config/analyzer_config.json`).
- RQ-013a: The system shall support short-form CLI execution with zero arguments (referring to `config/analyzer_config.json`) or a single positional/flag argument to a custom configuration JSON file. Explicit command-line options shall override JSON configuration file settings.

## Non-Functional Requirements
- NFR-001: Deterministic output for same input and parameters.
- NFR-002: Command-line execution with explicit parameters or short-form configuration file execution.
- NFR-003: Unit tests for core parser, filtering, analysis, and configuration file loading behavior.
- NFR-004: Clear error messages for invalid arguments and malformed data.

## Acceptance Criteria
- AC-001: Given a valid CSV, tool completes and writes output CSV.
- AC-002: Given mixed valid/invalid rows, invalid rows are counted and skipped.
- AC-003: Given `bottom-count`, target output size for ranked numbers equals `max(1, bottom-count)` when no cutoff tie exists.
- AC-004: Given equal frequencies, result ordering is stable and deterministic.
- AC-005: Given two rows `1,2,3,4,5,6,7` and `1,2,4,3,9,10,11` (date omitted for brevity), numbers `1`, `2`, `3`, and `4` each appear 2 times and are tied as most frequent.
- AC-006: Given config values `min_value` and `max_value`, each numeric field outside that range is treated as invalid input.
- AC-007: Given invalid config bounds (non-positive values or `min_value > max_value`), the tool fails with a clear configuration error.
- AC-008: Given `bottom-count = n`, output contains at least `n` ranked numbers; if no tie occurs at cutoff, output count is exactly `n`.
- AC-009: Given a valid number in configured range that never appears in filtered rows, that number is treated as count 0 and prioritized among least-present numbers by deterministic tie handling.
- AC-010: Given multiple numbers tied at cutoff rank, output includes all numbers at that rank, so output count can be greater than `bottom-count` or `top-count`.
- AC-011: Given computed percentage values, output percentages are rounded to 3 decimal places.
- AC-012: Given `top-count = n`, output ranks numbers from most appearance to least appearance and contains at least `n` ranked numbers; if no tie occurs at cutoff, output count is exactly `n`.
- AC-013: Given no command-line arguments, running `python -m lotto_analyzer.cli` automatically loads parameters from `config/analyzer_config.json` and executes the analysis.

## Change Log
- 1.9.0: Added support for loading analyzer parameters from `config/analyzer_config.json` enabling short-form execution with zero or one argument.
- 1.8.0: Added `top-count` parameter support to rank numbers from most appearance to least appearance (highest frequency ranked first).
- 1.7.0: Replaced 6-number combination output with ranked per-number output (least to most), including frequency and percentage rounded to 3 decimal places.
- 1.6.0: Replaced percentile-based combo selection with count-based `bottom-count` selection and tie-inclusive cutoff output.
- 1.5.0: Included all configured-range numbers (including never-seen numbers with count 0) in least-selection and combo generation.
- 1.4.0: Updated least-selection behavior to generate unordered 6-number combinations from bottom x% pool and export combos.
- 1.3.0: Replaced fixed numeric range with config-driven positive range validation.
- 1.2.0: Switched analysis from full-row combination frequency to per-number frequency across `n1..n7`.
- 1.1.0: Removed priority from CSV schema and removed priority-related requirements.
- 1.0.0: Initial implementation baseline.
