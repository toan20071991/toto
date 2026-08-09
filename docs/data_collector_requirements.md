# Data Collector Requirements (Gate 1)

## Metadata
- Requirement Version: 1.2.0
- Status: Approved for Implementation
- Effective Date: 2026-08-09
- Owner: Project Team

## Functional Requirements
- RQ-DC-001: The system shall read configuration settings from `config/collector_config.json` relative to the script execution environment.
- RQ-DC-002: The system shall support configuration settings `url` (target URL, required), `output` (output CSV path, default `output/toto_results.csv`), `date` (explicit target boundary cut-off date, optional), and `append` (default write mode setting, default `true`).
- RQ-DC-003: The system shall provide a CLI entry point `python src/data_collector/data_collect.py`.
- RQ-DC-004: The system shall accept an optional `--append` CLI flag to override file writing mode and prepend new unique draw rows to the top of the output file.
- RQ-DC-005: The system shall parse and clean draw date strings extracted from web elements and configuration parameters.
- RQ-DC-006: The system shall automatically strip optional leading weekday prefixes (`Mon, `, `Tue, `, `Wed, `, `Thu, `, `Fri, `, `Sat, `, `Sun, `).
- RQ-DC-007: The system shall support date string formats `%d %b %Y`, `%d/%m/%Y`, and `%Y-%m-%d`.
- RQ-DC-008: The system shall normalize valid draw dates into ISO standard format `YYYY-MM-DD` for output CSV rows.
- RQ-DC-009: The system shall launch a headless Chromium browser instance via Playwright (`sync_playwright`) to render dynamic web page content.
- RQ-DC-010: The system shall navigate to the configured `url` and wait for element `td.win1` within a 12,000 ms timeout.
- RQ-DC-011: The system shall extract all HTML `<select>` option elements containing non-empty visible text and option values.
- RQ-DC-012: The system shall de-duplicate extracted draw options based on option values while maintaining original chronological listing order.
- RQ-DC-013: The system shall iterate through extracted draw options sequentially from newest to oldest.
- RQ-DC-014: If the output file already contains data, the system shall identify the latest draw date in the file (`latest_existing_date`) and terminate collection as soon as it encounters a draw date less than or equal to `latest_existing_date`.
- RQ-DC-014a: If the output file is empty or missing and no explicit `date` is configured, the system shall default the cut-off date to 1 year prior to the execution date (`today - 365 days`).
- RQ-DC-014b: If an explicit `date` is configured in `config/collector_config.json`, that date shall override the 1-year default for empty files.
- RQ-DC-015: The system shall select each draw date option from the dropdown menu (`select`).
- RQ-DC-016: The system shall check if the target option is already selected before triggering dropdown change events.
- RQ-DC-017: The system shall dispatch a DOM `change` event within an explicit navigation context (`page.expect_navigation`) to handle full-page reloads and inline frame updates safely.
- RQ-DC-018: The system shall wait for element `td.win1` within an 8,000 ms timeout and apply a 0.4s DOM stabilization delay before parsing.
- RQ-DC-019: The system shall parse rendered page HTML using BeautifulSoup to extract lottery draw numbers.
- RQ-DC-020: The system shall locate the target draw table matching selectors `table.table-draw-list`, `.tables-wrapper table`, `table.toto-table`, or parent `table` containing `td.win1`.
- RQ-DC-021: The system shall extract exactly 6 winning numbers from table cells `td.win1` through `td.win6`, requiring each value to be numeric digits.
- RQ-DC-022: The system shall extract 1 additional lottery number from cells `td.additional`, `td.additional-number`, or container elements matching text `additional` with numbers in range `1..49`.
- RQ-DC-023: If the additional lottery number cannot be found, the system shall default the value to `"null"`.
- RQ-DC-024: The system shall format each valid extracted draw row as `date,n1,n2,n3,n4,n5,n6,n7` (`YYYY-MM-DD,win1,win2,win3,win4,win5,win6,additional`).
- RQ-DC-025: The system shall output data to the configured CSV file path.
- RQ-DC-026: When writing new rows to an existing output file, the system shall prepend new unique draw rows to the top of the file and preserve all existing historical rows below.
- RQ-DC-027: When writing to a new or empty file, the system shall save all newly collected draw rows in chronological order (newest draw at top).

## Non-Functional Requirements
- NFR-DC-001: Data compatibility with `lotto_analyzer` input schema (`date,n1,n2,n3,n4,n5,n6,n7` with no header).
- NFR-DC-002: Individual draw parsing failures shall be logged and dropped without halting the overall collection loop for remaining draw items.
- NFR-DC-003: Dynamic DOM rendering and network navigation shall enforce explicit timeout bounds (8s - 12s) to prevent execution hangs.
- NFR-DC-004: Standard console progress logging to stdout.

## Acceptance Criteria
- AC-DC-001: Given an empty output file, running `python src/data_collector/data_collect.py` collects all available draws within 1 year from execution date.
- AC-DC-002: Given an existing output file with latest date `2026-07-16`, collection terminates immediately upon encountering `2026-07-16` and prepends only newer draws to the top of the file.
- AC-DC-003: Given an output file up to date with the latest available draw, running the script halts after checking the first draw option without recollecting existing data.
- AC-DC-004: Given a draw result missing the additional number cell, the 8th output column defaults to `null`.
- AC-DC-005: Given an unreachable URL or page timeout, the application logs an explicit error message and exits cleanly without crashing.

## Change Log
- 1.2.0: Updated requirement for empty files to collect 1 year of data from execution date, and existing files to automatically stop collection at `latest_existing_date` and prepend new rows.
- 1.1.0: Updated `date` config behavior for empty string handling.
- 1.0.0: Initial implementation baseline for Data Collector requirements.
