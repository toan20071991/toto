from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from .models import DrawRecord, ParseSummary


EXPECTED_COLUMNS = 8


def _to_int(value: str) -> int:
    return int(value.strip())


def _parse_date(value: str):
    return datetime.strptime(value.strip(), "%Y-%m-%d").date()


def _validate_numbers(
    numbers: List[int], min_value: int, max_value: int
) -> Tuple[int, int, int, int, int, int, int]:
    if len(numbers) != 7:
        raise ValueError("A record must contain exactly 7 numbers.")
    for n in numbers:
        if n < min_value or n > max_value:
            raise ValueError(f"Numbers must be in configured range {min_value}..{max_value}.")
    return tuple(numbers)  # type: ignore[return-value]


def parse_csv_file(
    input_path: str | Path,
    min_value: int,
    max_value: int,
) -> tuple[list[DrawRecord], ParseSummary]:
    path = Path(input_path)
    records: list[DrawRecord] = []
    total_rows = 0
    invalid_rows = 0

    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            total_rows += 1
            if len(row) != EXPECTED_COLUMNS:
                invalid_rows += 1
                continue
            try:
                draw_date = _parse_date(row[0])
                numbers = [_to_int(v) for v in row[1:8]]
                validated = _validate_numbers(numbers, min_value=min_value, max_value=max_value)
            except (ValueError, TypeError):
                invalid_rows += 1
                continue
            records.append(DrawRecord(draw_date=draw_date, numbers=validated))

    summary = ParseSummary(
        total_rows=total_rows,
        valid_rows=len(records),
        invalid_rows=invalid_rows,
    )
    return records, summary
