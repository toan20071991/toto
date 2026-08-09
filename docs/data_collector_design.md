# Data Collector Design (Gate 2)

## Metadata
- Design Version: 1.2.0
- Status: Approved for Implementation
- Linked Requirement Version: 1.2.0
- Effective Date: 2026-08-09
- Target Component: `src/data_collector/data_collect.py`

## Architecture

Component Breakdown of `src/data_collector/data_collect.py`:

- **Config Loader & File Inspector**:
  - Loads configuration JSON from `config/collector_config.json`.
  - Inspects existing output CSV file (`OUTPUT_FILE`).
  - Reads top row to determine `latest_existing_date`.
- **Date Parser & Normalizer (`parse_date`)**:
  - Cleans date strings by removing weekday prefixes (regex `^(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s*`).
  - Attempts parsing across multiple standard date formats (`%d %b %Y`, `%d/%m/%Y`, `%Y-%m-%d`).
  - Returns `datetime` object or `None`.
- **Browser Automation Controller (`sync_playwright`)**:
  - Controls headless Chromium browser instance via Playwright.
  - Passes standard desktop `user_agent` string to prevent headless detection blocks.
  - Navigates to target URL with `domcontentloaded` wait state.
- **Draw Option Extractor (`get_available_dates`)**:
  - Evaluates DOM JavaScript to extract all available dropdown draw items (`value` and visible `text`).
  - De-duplicates items by `value` preserving chronological listing order.
- **Page Event Synchronizer (`select_dropdown_date`)**:
  - Checks current dropdown selected value to avoid redundant navigation triggers.
  - Wraps option selection (`select_option`) and DOM `change` event dispatch in `page.expect_navigation` context.
  - Waits for DOM element `td.win1` (8,000 ms timeout) and applies 0.4s render stabilization sleep.
- **HTML Parser & Extractor (`parse_draw_table`, `extract_additional_number`)**:
  - Parses rendered page HTML using BeautifulSoup.
  - Extracts 6 winning numbers from `td.win1` through `td.win6`.
  - Extracts 1 additional number from `td.additional`, `td.additional-number`, or container text search matching `additional` with regex `\b\d{1,2}\b` (defaults to `"null"` if missing).
  - Formats CSV row string: `YYYY-MM-DD,win1,win2,win3,win4,win5,win6,additional`.
- **CSV Output Persistence Manager (`save_to_csv`)**:
  - In standard mode (`append=False`), overwrites output CSV file.
  - In append mode (`append=True`), reads existing rows, isolates new unique rows, and prepends new rows to the top of the output file.

## Data Model

### Configuration Schema (`collector_config.json`)
- `url`: string (required) - Web page URL for TOTO draw results.
- `output`: string (optional, default `"output/toto_results.csv"`) - File path for CSV export.
- `date`: string (optional) - Explicit target cut-off date boundary for collection loop. Overrides the 1-year default for empty files.
- `append`: boolean (optional, default `true`) - Default file append setting.

### Target Output CSV Record
- `draw_date`: string (`YYYY-MM-DD`)
- `win1`: integer (1..49 string)
- `win2`: integer (1..49 string)
- `win3`: integer (1..49 string)
- `win4`: integer (1..49 string)
- `win5`: integer (1..49 string)
- `win6`: integer (1..49 string)
- `additional`: integer (1..49 string) or `"null"`

Row format: `YYYY-MM-DD,win1,win2,win3,win4,win5,win6,additional` (8 comma-separated fields, headerless).

## Core Algorithms

1. **Initialization & Existing File Inspection**:
   - Resolve path to `config/collector_config.json`.
   - Read JSON parameters (`url`, `output`, `date`, `append`).
   - Check if `OUTPUT_FILE` exists and contains data:
     - If `OUTPUT_FILE` exists and has valid rows:
       - Read top line and parse date into `latest_existing_date`.
       - Set `effective_limit_date = latest_existing_date`.
     - Else (`OUTPUT_FILE` is empty or missing):
       - If `config["date"]` is non-empty, set `effective_limit_date = parse_date(config["date"])`.
       - Else, set `effective_limit_date = datetime.now() - timedelta(days=365)` (1 year ago from today).

2. **Browser Execution & Initial Render**:
   - Launch Playwright Chromium in headless mode with standard `user_agent`.
   - Open new browser page.
   - Navigate to `URL` with `wait_until="domcontentloaded"`.
   - Wait up to 12,000 ms for selector `td.win1`. If timeout occurs, log error and exit cleanly.

3. **Draw Options Extraction & Deduplication**:
   - Call `get_available_dates(page)`.
   - Execute JS in page context to retrieve all `<select option>` elements as array of `{ value, text }`.
   - Filter out empty entries and de-duplicate by `value` while preserving chronological dropdown order.

4. **Time-Series Iteration & Cut-Off Boundary Filtering**:
   - Loop over extracted draw items sequentially (newest to oldest):
     - Parse `draw_item['text']` into `current_date_obj`.
     - Check boundary condition:
       - If `effective_limit_date` exists and `current_date_obj <= effective_limit_date`:
         - Log notification: `Reached boundary/existing date ({draw_item['text']}). Stopping collection loop.`
         - Stop collection loop immediately (`break`).
     - Call `select_dropdown_date(page, draw_item['value'])`.
     - Retrieve updated `page.content()`.
     - Call `parse_draw_table(html, default_date_str=draw_item['text'])`.
     - If valid CSV row string is returned, print to stdout and append to `collected_rows`.
     - If exception occurs for single draw, catch silently and continue loop.

5. **Dropdown Interaction & DOM Synchronization**:
   - Query current DOM selected option value. If already selected, return immediately.
   - Execute `page.select_option("select", value=target_value)` and dispatch `change` event inside `page.expect_navigation(timeout=10000, wait_until="domcontentloaded")`.
   - On fallback (if no navigation frame occurs), catch exception and continue.
   - Wait for `td.win1` selector (8,000 ms timeout) and pause 0.4 seconds.

6. **HTML Parsing & Number Extraction**:
   - Instantiates `BeautifulSoup(html_content, "parser")`.
   - Resolves result table matching selectors `table.table-draw-list`, `.tables-wrapper table`, `table.toto-table`, or parent `table` containing `td.win1`.
   - Format `draw_date` as `YYYY-MM-DD`.
   - Extract `td.win1` through `td.win6`. Verify all 6 cells contain numeric digit strings. Return `None` if incomplete.
   - Resolve additional number via selector `td.additional`, `td.additional-number`, or container text search for keyword `"additional"` matching regex `\b\d{1,2}\b`. Default to `"null"` if missing.
   - Join into string: `{formatted_date},{win1},{win2},{win3},{win4},{win5},{win6},{additional}`.

7. **CSV Output Persistence**:
   - If `collected_rows` is empty, log message `No new rows to append.` and exit cleanly.
   - Prepend `collected_rows` to the top of `OUTPUT_FILE` and write all existing historical rows below.

## Traceability

- `RQ-DC-001`, `RQ-DC-002` -> Config Loader & File Inspector (`collector_config.json`)
- `RQ-DC-003`, `RQ-DC-004` -> CLI Entry Point & `argparse` (`--append`)
- `RQ-DC-005`..`RQ-DC-008` -> `parse_date()`
- `RQ-DC-009`..`RQ-DC-012` -> `get_available_dates()`, Playwright setup
- `RQ-DC-013`, `RQ-DC-014`, `RQ-DC-014a`, `RQ-DC-014b` -> `main()` collection loop, 1-year default calculation, & `latest_existing_date` boundary check
- `RQ-DC-015`..`RQ-DC-018` -> `select_dropdown_date()`
- `RQ-DC-019`..`RQ-DC-024` -> `parse_draw_table()`, `extract_additional_number()`
- `RQ-DC-025`..`RQ-DC-027` -> `save_to_csv()`
- `NFR-DC-001`..`NFR-DC-004` -> Exception handling, timeouts, and logging
