# Lottery Number Frequency Analyzer

This project implements a stage-gated workflow and a Python CLI tool for analyzing least-appearing lottery numbers.

## Requirement Baseline

- Lotto Analyzer requirement version: 1.7.0 (Source: `docs/requirements.md`, Design: `docs/design.md`)
- Data Collector requirement version: 1.2.0 (Source: `docs/data_collector_requirements.md`, Design: `docs/data_collector_design.md`)
- Task source: `docs/tasks.md`

## Target Input Contract (Requirements v1.7.0)

- CSV rows with no header and no footer
- Exact column order:
  - date,n1,n2,n3,n4,n5,n6,n7
- date format: YYYY-MM-DD
- n1..n7: integers in configured positive range from config file

## Range Config (`config/range.json`)

- Default config path: `config/range.json`

| Field | Type / Format | Explanation | Behavior if Empty / Omitted |
| :--- | :--- | :--- | :--- |
| `min_value` | Positive Integer (e.g. `1`) | Lower bound of valid lottery numbers. | **Required**. Triggers configuration error if missing. |
| `max_value` | Positive Integer (e.g. `49`) | Upper bound of valid lottery numbers (`min_value <= max_value`). | **Required**. Triggers configuration error if missing. |

Example `config/range.json` format:

```json
{
  "min_value": 1,
  "max_value": 49
}
```

## Current Implementation Note

- Implementation is aligned with requirements v1.7.0, including configured-range candidate expansion, count-based output selection (`bottom-count`), deterministic least-to-most number ranking, and tie-inclusive cutoff.
- Data Collector implementation is aligned with requirements v1.2.0, supporting Playwright headless scraping, automatic 1-year initial collection, and incremental prepending.
- Analyzer implementation is aligned with requirements v1.9.0, supporting short-form execution, JSON config file parameter loading, and `top-count` / `mode` options.
- Task execution evidence is tracked in `docs/task-results.md`.

## Current Analysis Rule

- Frequency is computed per number across all filtered `n1..n7` cells
- Candidate set includes all values in configured range `[min_value,max_value]`; unseen values are treated as count 0
- Percentage uses denominator `total_numeric_cells` and is rounded to 3 decimal places
- Least-appearing selection ranks individual numbers from least appearance to most appearance (`mode="least"`)
- Most-appearing selection ranks individual numbers from most appearance to least appearance (`mode="most"`)
- Input parameters are `bottom-count` or `top-count` (integer), interpreted as minimum result count
- If multiple numbers tie at the cutoff rank, all tied numbers are included
- Therefore, output row count is at least `bottom-count`/`top-count` and can be larger due to ties
- Tie break is deterministic by `(frequency asc, number asc)` for least mode, or `(frequency desc, number asc)` for most mode

## Output Schema

- CSV output columns:
  - rank
  - number
  - frequency
  - percentage

## Project Structure

- `docs/requirements.md`: Lotto Analyzer requirement gate artifact
- `docs/design.md`: Lotto Analyzer design gate artifact
- `docs/data_collector_requirements.md`: Data Collector requirement gate artifact
- `docs/data_collector_design.md`: Data Collector design gate artifact
- `docs/tasks.md`: task gate artifact
- `src/lotto_analyzer/`: Analyzer implementation
- `src/data_collector/`: Data Collector implementation
- `tests/`: verification tests

## Run

Analyzer commands:

1. **Short-Form (Default Config)**:
   ```bash
   python -m src.lotto_analyzer.cli
   ```
   *Loads parameters from `config/analyzer_config.json` automatically.*

2. **Custom Config File**:
   ```bash
   python -m src.lotto_analyzer.cli custom_config.json
   ```

3. **Explicit CLI Flags (Overrides Config File)**:
   ```bash
   python -m src.lotto_analyzer.cli --input data.csv --config config/range.json --bottom-count 10 --window 1y --output result.csv
   python -m src.lotto_analyzer.cli --top-count 10 --mode most
   ```

### Analyzer Configuration (`config/analyzer_config.json`)

Example `config/analyzer_config.json` format:

```json
{
  "input": "output/toto_results.csv",
  "output": "output/analyze_result.csv",
  "range_config": "config/range.json",
  "mode": "least",
  "bottom_count": 10,
  "top_count": null,
  "window": "1y",
  "start_date": null,
  "end_date": null
}
```

| Field | Type / Format | Explanation | Behavior if Empty / Null / Omitted |
| :--- | :--- | :--- | :--- |
| `input` | String (Filepath, e.g. `"output/toto_results.csv"`) | Path to input CSV file containing draw records. | Defaults to `"output/toto_results.csv"`. |
| `output` | String (Filepath, e.g. `"output/analyze_result.csv"`) | Path where analysis CSV results will be saved. | Defaults to `"output/analyze_result.csv"`. |
| `range_config` | String (Filepath, e.g. `"config/range.json"`) | Path to numeric range bounds config JSON file. | Defaults to `"config/range.json"`. |
| `mode` | String (`"least"` or `"most"`) | Analysis ranking mode (`"least"` = least-appearing first, `"most"` = most-appearing first). | Defaults to `"least"`. |
| `bottom_count` | Integer (e.g. `10`) | Minimum number of least-appearing ranked rows to output (includes cutoff ties). | Defaults to `10` when `mode` is `"least"`. |
| `top_count` | Integer (e.g. `10`) | Minimum number of most-appearing ranked rows to output (includes cutoff ties). | Defaults to `10` when `mode` is `"most"`. |
| `window` | String (`"3m"`, `"6m"`, `"1y"`, `"2y"`, `"custom"`, or `null`) | Time window preset for filtering draw dates prior to analysis. | If `null` or empty `""`, uses **all available data** in the input CSV file. |
| `start_date` | String (`"YYYY-MM-DD"`, e.g. `"2025-01-01"`) | Custom window start date (inclusive). | Required only when `window` is `"custom"`. Ignored otherwise. |
| `end_date` | String (`"YYYY-MM-DD"`, e.g. `"2025-12-31"`) | Custom window end date (inclusive). | Required only when `window` is `"custom"`. Ignored otherwise. |

### Null & Empty Configuration Handling

When parameters are set to `null`, empty string `""`, or omitted in configuration files, the scripts execute explicit fallback behaviors:

#### Analyzer Script (`config/analyzer_config.json`)
- **`window` (`null` or `""`)**: Disables date range filtering. The script analyzes **all historical draw records** in the input CSV file from earliest to latest.
- **`bottom_count` / `top_count` (`null`)**:
  - If `mode` is `"least"`, `bottom_count` defaults to **10** (outputs at least 10 least-appearing numbers).
  - If `mode` is `"most"`, `top_count` defaults to **10** (outputs at least 10 most-appearing numbers).
  - Specifying `--top-count N` on the CLI automatically resolves `mode` to `"most"`.
- **`mode` (`null` or `""`)**: Defaults to `"least"`. If `top_count` is set while `bottom_count` is null, mode automatically resolves to `"most"`.
- **`start_date` / `end_date` (`null` or `""`)**: Ignored for preset windows (`3m`, `6m`, `1y`, `2y`) or when `window` is `null`. If `window` is explicitly `"custom"`, setting either date to `null` raises an error requiring both `YYYY-MM-DD` dates.
- **`input` / `output` / `range_config` (`null` or `""`)**: Automatically fall back to standard project paths (`output/toto_results.csv`, `output/analyze_result.csv`, `config/range.json`).

#### Data Collector Script (`config/collector_config.json`)
- **`date` (`""` or `null`)**:
  - **Existing CSV Output**: If the output file already contains draw data, the script inspects the top row's draw date (`latest_existing_date`), collects only newer draws, and **stops immediately** upon reaching `latest_existing_date` to prevent recollecting data.
  - **Empty / Missing CSV Output**: The script automatically sets the collection boundary to **1 year ago from today** (`today - 365 days`) and collects 1 year of draw data.
- **`output` (`""` or `null`)**: Defaults to `"output/toto_results.csv"`.
- **`append` (`null`)**: Defaults to `true` (prepends new unique rows to the top of the file).

Sample output header (`rank,number,frequency,percentage`):

```csv
rank,number,frequency,percentage
1,47,27,1.205
2,45,35,1.562
```

Create test CSV data by date range (latest date at top):

python testSample/createCSVtest.py --from-date 2025-07-20 --to-date 2026-07-19 --seed 20071991 --output testSample/sample.csv

## Collect webpage data

Run the collector directly from the root directory with JSON config:

python src/data_collector/data_collect.py

### Data Collection Behavior (v1.2.0)

- **Incremental Prepending**: If the target CSV output file already contains draw data, the collector identifies the latest existing draw date, collects only newer draws, and prepends them to the top of the file without recollecting existing data.
- **Empty File Default**: If the output CSV file is empty or missing and `"date"` is `""` (or omitted), the collector automatically collects **1 year of draw data** from the current execution date (`today - 365 days`).
- **Explicit Date Boundary**: If `"date"` is set to a non-empty date string (e.g. `"16-Jul-2026"` or `"2026-07-16"`), all data back to that explicit boundary date will be collected.

### Data Collector Configuration (`config/collector_config.json`)

Example `config/collector_config.json` format:

```json
{
  "url": "https://www.singaporepools.com.sg/en/product/pages/toto_results.aspx",
  "output": "output/toto_results.csv",
  "append": true,
  "date": ""
}
```

| Field | Type / Format | Explanation | Behavior if Empty / Omitted |
| :--- | :--- | :--- | :--- |
| `url` | String (URL, e.g. `"https://www.singaporepools.com.sg/..."`) | Target webpage URL for Singapore Pools TOTO results. | **Required**. System logs error if unreachable. |
| `output` | String (Filepath, e.g. `"output/toto_results.csv"`) | Filepath where collected CSV rows will be written. | Defaults to `"output/toto_results.csv"`. |
| `append` | Boolean (`true` or `false`) | File writing mode. When `true`, prepends new rows to top of output file. | Defaults to `true`. |
| `date` | String (`"DD-MMM-YYYY"`, `"YYYY-MM-DD"`, or `"DD/MM/YYYY"`) | Cut-off boundary date for historical draw collection. | If empty `""` or omitted: <br>• **If output CSV has data**: stops automatically at the latest existing date in the file and prepends only newer draws.<br>• **If output CSV is empty/missing**: automatically collects **1 year of draw data** (`today - 365 days`). |

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