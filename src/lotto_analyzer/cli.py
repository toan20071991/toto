from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

from .analyzer import analyze_numbers
from .config import load_analyzer_config, load_range_config
from .parser import parse_csv_file


def _parse_date_arg(value: str):
    return datetime.strptime(value, "%Y-%m-%d").date()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze lottery number frequencies")
    parser.add_argument(
        "config_file",
        nargs="?",
        default=None,
        help="Path to analyzer config JSON file (default: config/analyzer_config.json)",
    )
    parser.add_argument("--config-file", dest="flag_config_file", help="Path to analyzer config JSON file")
    parser.add_argument("--input", help="Input CSV path")
    parser.add_argument("--output", help="Output CSV path")
    parser.add_argument(
        "--config",
        dest="range_config",
        help="Config JSON path containing min_value and max_value",
    )
    parser.add_argument("--bottom-count", type=int, help="Minimum number of least-appearing numbers to output")
    parser.add_argument("--top-count", type=int, help="Minimum number of most-appearing numbers to output")
    parser.add_argument(
        "--mode",
        choices=["least", "most"],
        default=None,
        help="Analysis mode: 'least' for least-appearing numbers, 'most' for most-appearing numbers",
    )
    parser.add_argument(
        "--window",
        choices=["3m", "6m", "1y", "2y", "custom"],
        default=None,
        help="Date window preset; if omitted, use all available data",
    )
    parser.add_argument("--start-date", type=_parse_date_arg, help="Custom start date YYYY-MM-DD")
    parser.add_argument("--end-date", type=_parse_date_arg, help="Custom end date YYYY-MM-DD")
    return parser


def _write_output(path: str | Path, rows, summary) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "rank",
                "number",
                "frequency",
                "percentage",
            ]
        )
        for row in rows:
            writer.writerow([row.rank, row.number, row.frequency, f"{row.percentage:.3f}"])

    print("Summary")
    print(f"total_rows={summary.total_rows}")
    print(f"valid_rows={summary.valid_rows}")
    print(f"invalid_rows={summary.invalid_rows}")
    print(f"filtered_rows={summary.filtered_rows}")
    print(f"total_numeric_cells={summary.total_numeric_cells}")
    print(f"unique_numbers={summary.unique_numbers}")
    print(f"result_rows={len(rows)}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    config_file_path = args.flag_config_file or args.config_file or "config/analyzer_config.json"
    
    try:
        analyzer_config = load_analyzer_config(config_file_path)
    except ValueError as exc:
        parser.error(str(exc))

    input_path = args.input or analyzer_config.input
    output_path = args.output or analyzer_config.output
    range_config_path = args.range_config or analyzer_config.range_config
    mode = args.mode or analyzer_config.mode or "least"
    bottom_count = args.bottom_count if args.bottom_count is not None else analyzer_config.bottom_count
    top_count = args.top_count if args.top_count is not None else analyzer_config.top_count
    window = args.window or analyzer_config.window

    start_date = args.start_date
    if start_date is None and analyzer_config.start_date:
        try:
            start_date = _parse_date_arg(analyzer_config.start_date)
        except ValueError:
            parser.error(f"Invalid start_date in config: {analyzer_config.start_date}")

    end_date = args.end_date
    if end_date is None and analyzer_config.end_date:
        try:
            end_date = _parse_date_arg(analyzer_config.end_date)
        except ValueError:
            parser.error(f"Invalid end_date in config: {analyzer_config.end_date}")

    if window == "custom" and (start_date is None or end_date is None):
        parser.error("custom window requires --start-date and --end-date (or start_date and end_date in config)")

    if mode == "most":
        count = top_count if top_count is not None else (bottom_count if bottom_count is not None else 10)
    else:
        count = bottom_count if bottom_count is not None else (top_count if top_count is not None else 10)

    try:
        range_config = load_range_config(range_config_path)
    except ValueError as exc:
        parser.error(str(exc))

    records, parse_summary = parse_csv_file(
        input_path,
        min_value=range_config.min_value,
        max_value=range_config.max_value,
    )
    rows, summary = analyze_numbers(
        records=records,
        parse_summary=parse_summary,
        count=count,
        mode=mode,
        window=window,
        custom_start=start_date,
        custom_end=end_date,
        min_value=range_config.min_value,
        max_value=range_config.max_value,
    )
    _write_output(output_path, rows, summary)


if __name__ == "__main__":
    main()
