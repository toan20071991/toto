from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

from .analyzer import analyze_least_combinations
from .config import load_range_config
from .parser import parse_csv_file


def _parse_date_arg(value: str):
    return datetime.strptime(value, "%Y-%m-%d").date()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze least-appearing lottery numbers")
    parser.add_argument("--input", required=True, help="Input CSV path")
    parser.add_argument("--output", required=True, help="Output CSV path")
    parser.add_argument(
        "--config",
        default="config/range.json",
        help="Config JSON path containing min_value and max_value",
    )
    parser.add_argument("--bottom-count", type=int, default=10, help="Minimum number of least-appearing combos to output")
    parser.add_argument("--window", choices=["3m", "1y", "2y", "custom"], default="1y")
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
                "combo",
            ]
        )
        for row in rows:
            writer.writerow([row.rank, " ".join(str(n) for n in row.combo)])

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

    if args.window == "custom" and (args.start_date is None or args.end_date is None):
        parser.error("custom window requires --start-date and --end-date")

    try:
        range_config = load_range_config(args.config)
    except ValueError as exc:
        parser.error(str(exc))

    records, parse_summary = parse_csv_file(
        args.input,
        min_value=range_config.min_value,
        max_value=range_config.max_value,
    )
    rows, summary = analyze_least_combinations(
        records=records,
        parse_summary=parse_summary,
        bottom_count=args.bottom_count,
        window=args.window,
        custom_start=args.start_date,
        custom_end=args.end_date,
        min_value=range_config.min_value,
        max_value=range_config.max_value,
    )
    _write_output(args.output, rows, summary)


if __name__ == "__main__":
    main()
