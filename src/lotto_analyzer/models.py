from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Tuple


CombinationKey = Tuple[int, int, int, int, int, int, int]


@dataclass(frozen=True)
class DrawRecord:
    draw_date: date
    numbers: CombinationKey


@dataclass(frozen=True)
class ParseSummary:
    total_rows: int
    valid_rows: int
    invalid_rows: int


@dataclass(frozen=True)
class AnalysisRow:
    rank: int
    number: int
    frequency: int
    percentage: float


@dataclass(frozen=True)
class AnalysisSummary:
    total_rows: int
    valid_rows: int
    invalid_rows: int
    filtered_rows: int
    total_numeric_cells: int
    unique_numbers: int
