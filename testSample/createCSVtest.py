from __future__ import annotations

import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


def parse_date(value: str):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Expected format YYYY-MM-DD."
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create a CSV file with rows: date,n1,n2,n3,n4,n5,n6,n7 "
            "for each day in a date range."
        )
    )
    parser.add_argument(
        "--from-date",
        required=True,
        type=parse_date,
        help="Start date in YYYY-MM-DD",
    )
    parser.add_argument(
        "--to-date",
        required=True,
        type=parse_date,
        help="End date in YYYY-MM-DD",
    )
    parser.add_argument(
        "--output",
        default="test_data.csv",
        help="Output CSV path (default: test_data.csv)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for reproducible output",
    )
    return parser


def generate_rows(from_date, to_date):
    current = to_date
    while current >= from_date:
        nums = random.sample(range(1, 50), 7)
        yield [current.isoformat(), *nums]
        current -= timedelta(days=1)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.from_date > args.to_date:
        parser.error("--from-date must be earlier than or equal to --to-date")

    if args.seed is not None:
        random.seed(args.seed)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in generate_rows(args.from_date, args.to_date):
            writer.writerow(row)

    total_days = (args.to_date - args.from_date).days + 1
    print(f"Created {output_path} with {total_days} rows.")


if __name__ == "__main__":
    main()
