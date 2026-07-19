# Lottery Combination Analyzer

This project implements a stage-gated workflow and a Python CLI tool for analyzing least-appearing lottery numbers.

## Requirement Baseline

- Current requirement version: 1.6.0
- Requirement source: docs/requirements.md
- Design source: docs/design.md
- Task source: docs/tasks.md

## Target Input Contract (Requirements v1.6.0)

- CSV rows with no header and no footer
- Exact column order:
  - date,n1,n2,n3,n4,n5,n6,n7
- date format: YYYY-MM-DD
- n1..n7: integers in configured positive range from config file

## Range Config

- Default config path: config/range.json
- Required fields:
  - min_value (positive integer)
  - max_value (positive integer)
- Constraint:
  - min_value <= max_value

## Current Implementation Note

- Implementation is aligned with requirements v1.6.0, including configured-range candidate expansion, count-based output selection (`bottom-count`), and tie-inclusive cutoff.
- Task execution evidence is tracked in docs/task-results.md.

## Current Analysis Rule

- Frequency is computed per number across all filtered `n1..n7` cells
- Candidate set includes all values in configured range `[min_value,max_value]`; unseen values are treated as count 0
- Percentage uses denominator `total_numeric_cells`
- Least-appearing selection ranks 6-number combinations using aggregate member-number frequency score
- Input parameter is `bottom-count` (integer), interpreted as minimum result count
- If multiple combinations tie at the cutoff rank, all tied combinations are included
- Therefore, output row count is at least `bottom-count` and can be larger due to ties
- Tie break is deterministic by lexical combination ordering

## Project Structure

- `docs/requirements.md`: requirement gate artifact
- `docs/design.md`: design gate artifact
- `docs/tasks.md`: task gate artifact
- `src/lotto_analyzer/`: implementation
- `tests/`: verification tests

## Run

Analyzer command:

python -m lotto_analyzer.cli --input data.csv --config config/range.json --bottom-count 10 --window 1y --output result.csv

Examples:

python -m lotto_analyzer.cli --input data.csv --config config/range.json --bottom-count 5 --window 3m --output result.csv
python -m lotto_analyzer.cli --input data.csv --config config/range.json --bottom-count 15 --window custom --start-date 2024-01-01 --end-date 2025-12-31 --output result.csv

Create test CSV data by date range (latest date at top):

python testSample/createCSVtest.py --from-date 2025-07-20 --to-date 2026-07-19 --seed 20071991 --output testSample/sample.csv

## Test

python -m unittest discover -s tests -p "test_*.py"

## Run With Docker

Prerequisites (all machines):

- Install Docker (Docker Desktop on Windows/macOS, Docker Engine on Linux).
- Open a terminal in the project root (folder containing Dockerfile).

Linux/macOS steps:

1) Build image

docker build -t lotto-analyzer:0.1.0 .

2) Run analyzer

docker run --rm \
  -v "$(pwd)/testSample:/data" \
  -v "$(pwd)/config:/config" \
  lotto-analyzer:0.1.0 \
  --input /data/sample.csv \
  --config /config/range.json \
  --bottom-count 10 \
  --window 1y \
  --output /data/result.csv

3) Check output

Output file is created at testSample/result.csv on your host machine.

Windows PowerShell steps:

1) Build image

docker build -t lotto-analyzer:0.1.0 .

2) Run analyzer

docker run --rm `
  -v "${PWD}/testSample:/data" `
  -v "${PWD}/config:/config" `
  lotto-analyzer:0.1.0 `
  --input /data/sample.csv `
  --config /config/range.json `
  --bottom-count 10 `
  --window 1y `
  --output /data/result.csv

3) Check output

Output file is created at testSample/result.csv on your host machine.

Windows Command Prompt (cmd.exe) steps:

1) Build image

docker build -t lotto-analyzer:0.1.0 .

2) Run analyzer

docker run --rm ^
  -v "%cd%/testSample:/data" ^
  -v "%cd%/config:/config" ^
  lotto-analyzer:0.1.0 ^
  --input /data/sample.csv ^
  --config /config/range.json ^
  --bottom-count 10 ^
  --window 1y ^
  --output /data/result.csv

3) Check output

Output file is created at testSample/result.csv on your host machine.

Tip:

- Volume mounts keep input and output files on your local machine.

## Run With Docker Compose

Use this when you want one-command execution from docker-compose.yml.

Linux/macOS:

1) Build and run using compose file

docker compose up --build

2) One-off execution (container removed after run)

docker compose run --rm lotto-analyzer

3) Override arguments (example: custom date window)

docker compose run --rm lotto-analyzer --input /data/sample.csv --config /config/range.json --bottom-count 15 --window custom --start-date 2025-01-01 --end-date 2025-12-31 --output /data/result_custom.csv

Windows PowerShell:

1) Build and run using compose file

docker compose up --build

2) One-off execution (container removed after run)

docker compose run --rm lotto-analyzer

3) Override arguments (example: custom date window)

docker compose run --rm lotto-analyzer --input /data/sample.csv --config /config/range.json --bottom-count 15 --window custom --start-date 2025-01-01 --end-date 2025-12-31 --output /data/result_custom.csv

Windows Command Prompt (cmd.exe):

1) Build and run using compose file

docker compose up --build

2) One-off execution (container removed after run)

docker compose run --rm lotto-analyzer

3) Override arguments (example: custom date window)

docker compose run --rm lotto-analyzer --input /data/sample.csv --config /config/range.json --bottom-count 15 --window custom --start-date 2025-01-01 --end-date 2025-12-31 --output /data/result_custom.csv

Compose output location:

- testSample/result.csv (or the output path you pass in override arguments)