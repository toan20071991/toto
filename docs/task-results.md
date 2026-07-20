# Task Results Log

## Metadata
- Log Version: 1.0.0
- Purpose: Persistent execution log for task runs and verification evidence.
- Linked Task Plan: docs/tasks.md

## Logging Rules
- Add one entry each time a task is executed or re-verified.
- Do not delete old entries; append new entries with timestamp and status.
- If a task is re-run, use the same Task ID and increment the Run ID.

## Entry Template
- Run ID: TR-XXX
- Task ID: T-XXX
- Date: YYYY-MM-DD
- Executor: Copilot or User
- Command(s):
  - command line used
- Inputs:
  - key input files
  - parameters
- Output/Evidence:
  - generated files
  - summary values
- Result: PASS or FAIL
- Notes:
  - issues found, fixes applied, follow-up actions

## Results

### TR-001
- Task ID: T-007 (legacy migration record)
- Date: 2026-07-19
- Executor: Copilot
- Command(s):
  - u:/01_SourceCode/98_Personal/01_toto/.venv/Scripts/python.exe -m unittest discover -s tests -p test_*.py
- Inputs:
  - src/lotto_analyzer
  - tests
- Output/Evidence:
  - unit tests passed: 3 passed, 0 failed
  - priority-related code paths removed from parser, analyzer, cli, tests
- Result: PASS
- Notes:
  - Completed removal of priority logic to align with requirements v1.1.0 baseline.

### TR-002
- Task ID: Validation Run (sample output check)
- Date: 2026-07-19
- Executor: Copilot
- Command(s):
  - u:/01_SourceCode/98_Personal/01_toto/.venv/Scripts/python.exe -m lotto_analyzer.cli --input testSample/sample.csv --x-percent 10 --window 1y --output testSample/result.csv
- Inputs:
  - testSample/sample.csv
  - x-percent=10
  - window=1y
- Output/Evidence:
  - testSample/result.csv
  - summary: total_rows=365, valid_rows=365, invalid_rows=0, filtered_rows=365, unique_combinations=365, result_rows=37
  - independent recomputation confirmed all output rows match
- Result: PASS
- Notes:
  - This validation reflects the implementation state at run time; future requirements may change output schema and metrics.

### TR-003
- Task ID: T-002 to T-007 (v1.3.0 implementation batch)
- Date: 2026-07-19
- Executor: Copilot
- Command(s):
  - u:/01_SourceCode/98_Personal/01_toto/.venv/Scripts/python.exe -m unittest discover -s tests -p test_*.py
- Inputs:
  - docs/requirements.md v1.3.0
  - docs/design.md v1.3.0
  - config/range.json
- Output/Evidence:
  - Added config loader: src/lotto_analyzer/config.py
  - Parser validates n1..n7 against configured min/max bounds
  - Analyzer switched to per-number frequency and percentage
  - CLI now accepts --config and writes schema rank,number,count,percentage
  - unit tests passed: 5 passed, 0 failed
- Result: PASS
- Notes:
  - Implementation now follows config-driven positive range requirement and per-number analytics model.

### TR-004
- Task ID: Validation Run (v1.3.0 sample output check)
- Date: 2026-07-19
- Executor: Copilot
- Command(s):
  - u:/01_SourceCode/98_Personal/01_toto/.venv/Scripts/python.exe -m lotto_analyzer.cli --input testSample/sample.csv --config config/range.json --x-percent 10 --window 1y --output testSample/result_v13.csv
  - Independent recomputation check via python -c against testSample/sample.csv and testSample/result_v13.csv
- Inputs:
  - testSample/sample.csv
  - config/range.json (min_value=1, max_value=49)
  - x-percent=10
  - window=1y
- Output/Evidence:
  - testSample/result_v13.csv
  - summary: total_rows=365, valid_rows=365, invalid_rows=0, filtered_rows=365, total_numeric_cells=2555, unique_numbers=49, result_rows=5
  - independent recomputation: expected_rows=5, got_rows=5, all_rows_match=True
- Result: PASS
- Notes:
  - Output schema and calculations are consistent with requirements v1.3.0.

### TR-005
- Task ID: T-005 to T-007 (v1.4.0 combo implementation batch)
- Date: 2026-07-19
- Executor: Copilot
- Command(s):
  - $env:PYTHONPATH='src'; u:/01_SourceCode/98_Personal/01_toto/.venv/Scripts/python.exe -m unittest discover -s tests -p "test_*.py"
  - $env:PYTHONPATH='src'; u:/01_SourceCode/98_Personal/01_toto/.venv/Scripts/python.exe -m lotto_analyzer.cli --input testSample/sample.csv --config config/range.json --x-percent 15 --window 1y --output testSample/result_v14.csv
- Inputs:
  - docs/requirements.md v1.4.0
  - docs/design.md v1.4.0
  - testSample/sample.csv
  - config/range.json (min_value=1, max_value=49)
- Output/Evidence:
  - Unit tests passed: 6 passed, 0 failed
  - Implemented combo output schema in CLI: rank,combo
  - Generated file: testSample/result_v14.csv
  - summary: total_rows=365, valid_rows=365, invalid_rows=0, filtered_rows=365, total_numeric_cells=2555, unique_numbers=49, result_rows=28
  - combo result count matches C(8,6)=28 for x-percent=15
- Result: PASS
- Notes:
  - Behavior now aligns with RQ-009 and AC-008 by generating all unordered 6-number combinations from the selected bottom-percentile pool.

### TR-006
- Task ID: Validation Run (v1.4.0 dual-path check)
- Date: 2026-07-19
- Executor: Copilot
- Command(s):
  - $env:PYTHONPATH='src'; u:/01_SourceCode/98_Personal/01_toto/.venv/Scripts/python.exe -m unittest discover -s tests -p "test_*.py"
  - $env:PYTHONPATH='src'; u:/01_SourceCode/98_Personal/01_toto/.venv/Scripts/python.exe -m lotto_analyzer.cli --input testSample/sample.csv --config config/range.json --x-percent 15 --window 1y --output testSample/result_v14_validation_15.csv
  - $env:PYTHONPATH='src'; u:/01_SourceCode/98_Personal/01_toto/.venv/Scripts/python.exe -m lotto_analyzer.cli --input testSample/sample.csv --config config/range.json --x-percent 10 --window 1y --output testSample/result_v14_validation_10.csv
- Inputs:
  - testSample/sample.csv
  - config/range.json (min_value=1, max_value=49)
  - x-percent=15 and x-percent=10
  - window=1y
- Output/Evidence:
  - unit tests passed: 6 passed, 0 failed
  - testSample/result_v14_validation_15.csv: 29 lines total (header + 28 combos)
  - testSample/result_v14_validation_10.csv: 1 line total (header only, 0 combos)
  - CLI summary for both runs: total_rows=365, valid_rows=365, invalid_rows=0, filtered_rows=365, total_numeric_cells=2555, unique_numbers=49
- Result: PASS
- Notes:
  - For x-percent=15, selected pool size is ceil(49*15/100)=8 and combo count matches C(8,6)=28.
  - For x-percent=10, selected pool size is ceil(49*10/100)=5 (<6), so output correctly contains no combo rows.

### TR-007
- Task ID: T-005 to T-007 (v1.5.0 zero-frequency candidate-set update)
- Date: 2026-07-19
- Executor: Copilot
- Command(s):
  - $env:PYTHONPATH='src'; u:/01_SourceCode/98_Personal/01_toto/.venv/Scripts/python.exe -m unittest discover -s tests -p "test_*.py"
  - $env:PYTHONPATH='src'; u:/01_SourceCode/98_Personal/01_toto/.venv/Scripts/python.exe -m lotto_analyzer.cli --input .\testSample\sample.csv --config .\config\range.json --x-percent 5 --window 3m --output .\result.csv
  - $env:PYTHONPATH='src'; u:/01_SourceCode/98_Personal/01_toto/.venv/Scripts/python.exe -c "from datetime import timedelta; from lotto_analyzer.parser import parse_csv_file; from lotto_analyzer.config import load_range_config; cfg=load_range_config('config/range.json'); records,_=parse_csv_file('testSample/sample.csv', min_value=cfg.min_value, max_value=cfg.max_value); end=max(r.draw_date for r in records); start=end-timedelta(days=90); filt=[r for r in records if start<=r.draw_date<=end]; seen={n for r in filt for n in r.numbers}; allnums=set(range(cfg.min_value, cfg.max_value+1)); missing=sorted(allnums-seen); print(len(filt), len(seen), len(missing))"
- Inputs:
  - docs/requirements.md v1.5.0
  - docs/design.md v1.5.0
  - testSample/sample.csv
  - config/range.json (min_value=1, max_value=49)
- Output/Evidence:
  - unit tests passed: 7 passed, 0 failed
  - user's command summary: filtered_rows=91, total_numeric_cells=637, unique_numbers=49, result_rows=0
  - 3m filtered window coverage check: seen_count=49, missing_count=0
- Result: PASS
- Notes:
  - Analyzer now ranks full configured range and treats missing in-range numbers as count 0.
  - In this specific dataset/window there are no missing numbers, so x-percent=5 still yields pool size 3 and therefore zero 6-number combos.

### TR-008
- Task ID: T-005 to T-007 (v1.6.0 bottom-count and tie-inclusive cutoff)
- Date: 2026-07-19
- Executor: Copilot
- Command(s):
  - $env:PYTHONPATH='src'; u:/01_SourceCode/98_Personal/01_toto/.venv/Scripts/python.exe -m unittest discover -s tests -p "test_*.py"
  - $env:PYTHONPATH='src'; u:/01_SourceCode/98_Personal/01_toto/.venv/Scripts/python.exe -m lotto_analyzer.cli --input .\testSample\sample.csv --config .\config\range.json --bottom-count 10 --window 3m --output .\result.csv
- Inputs:
  - docs/requirements.md v1.6.0
  - docs/design.md v1.6.0
  - testSample/sample.csv
  - config/range.json (min_value=1, max_value=49)
  - bottom-count=10
  - window=3m
- Output/Evidence:
  - unit tests passed: 7 passed, 0 failed
  - CLI summary: total_rows=365, valid_rows=365, invalid_rows=0, filtered_rows=91, total_numeric_cells=637, unique_numbers=49, result_rows=15
  - output row count exceeds requested minimum because cutoff-score ties are included
- Result: PASS
- Notes:
  - CLI parameter migrated from x-percent to bottom-count.
  - Analyzer now ranks 6-number combinations by aggregate member-number frequency score and includes all rows tied at cutoff.

### TR-009
- Task ID: T-005 to T-007 (v1.7.0 ranked-number implementation batch)
- Date: 2026-07-20
- Executor: Copilot
- Command(s):
  - u:/01_SourceCode/98_Personal/01_toto/.venv/Scripts/python.exe -m unittest discover -s tests -p "test_*.py"
  - u:/01_SourceCode/98_Personal/01_toto/.venv/Scripts/python.exe -m lotto_analyzer.cli --input .\output\toto_results_test.csv --config .\config\range.json --bottom-count 10 --output result.csv --window 1y
- Inputs:
  - docs/requirements.md v1.7.0
  - docs/design.md v1.7.0
  - docs/tasks.md v1.7.0
  - output/toto_results_test.csv
  - config/range.json
  - bottom-count=10
  - window=1y
- Output/Evidence:
  - unit tests passed: 9 passed, 0 failed
  - CLI summary: total_rows=298, valid_rows=298, invalid_rows=0, filtered_rows=105, total_numeric_cells=735, unique_numbers=49, result_rows=11
  - output schema verified: rank,number,frequency,percentage
  - sample output percentages formatted to 3 decimals (e.g., 0.952, 1.497, 1.633)
- Result: PASS
- Notes:
  - Replaced combination generation/ranking with deterministic per-number ranking `(frequency asc, number asc)`.
  - Tie-inclusive cutoff applied to frequency at requested `bottom-count` boundary.

### TR-010
- Task ID: T-008 (legacy assumption cleanup for v1.7.0)
- Date: 2026-07-20
- Executor: Copilot
- Command(s):
  - u:/01_SourceCode/98_Personal/01_toto/.venv/Scripts/python.exe -m unittest discover -s tests -p "test_*.py"
  - Source scan: grep for legacy `rank,combo` / `combo` usage in src/lotto_analyzer
- Inputs:
  - tests/test_parser.py
  - src/lotto_analyzer/*
- Output/Evidence:
  - Parser test range updated to config-driven bounds (`max_value=60`) while preserving invalid-row coverage with value `100`
  - unit tests passed: 9 passed, 0 failed
  - no combo schema string found in core source package
- Result: PASS
- Notes:
  - Removed remaining fixed-range test assumption and verified current source is aligned to ranked-number output model.
