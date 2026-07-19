from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
import heapq
from itertools import combinations
from typing import Sequence

from .models import AnalysisRow, AnalysisSummary, DrawRecord, ParseSummary


def _resolve_date_range(
    records: Sequence[DrawRecord],
    window: str,
    custom_start: date | None,
    custom_end: date | None,
) -> tuple[date, date]:
    if window == "custom":
        if custom_start is None or custom_end is None:
            raise ValueError("custom window requires start and end dates")
        if custom_start > custom_end:
            raise ValueError("start date cannot be after end date")
        return custom_start, custom_end

    if not records:
        today = date.today()
        return today, today

    end = custom_end or max(r.draw_date for r in records)
    if window == "3m":
        return end - timedelta(days=90), end
    if window == "1y":
        return end - timedelta(days=365), end
    if window == "2y":
        return end - timedelta(days=730), end
    raise ValueError("window must be one of: 3m, 1y, 2y, custom")


def analyze_least_combinations(
    records: Sequence[DrawRecord],
    parse_summary: ParseSummary,
    bottom_count: int,
    window: str,
    custom_start: date | None = None,
    custom_end: date | None = None,
    min_value: int | None = None,
    max_value: int | None = None,
) -> tuple[list[AnalysisRow], AnalysisSummary]:
    if bottom_count < 0:
        raise ValueError("bottom_count must be >= 0")
    if (min_value is None) != (max_value is None):
        raise ValueError("min_value and max_value must be provided together")
    if min_value is not None and max_value is not None and min_value > max_value:
        raise ValueError("min_value cannot be greater than max_value")

    start_date, end_date = _resolve_date_range(records, window, custom_start, custom_end)

    filtered = [r for r in records if start_date <= r.draw_date <= end_date]
    observations = [n for record in filtered for n in record.numbers]

    counter: Counter[int] = Counter(observations)
    unique_count = len(counter)
    filtered_rows = len(filtered)
    total_numeric_cells = len(observations)

    rows: list[AnalysisRow] = []
    candidate_numbers = sorted(counter.keys())
    if min_value is not None and max_value is not None:
        candidate_numbers = list(range(min_value, max_value + 1))

    combo_size = 6
    target_rows = max(1, bottom_count)
    if len(candidate_numbers) >= combo_size:
        # First pass finds the cutoff score for the bottom-countth combination.
        score_heap: list[int] = []
        for combo in combinations(candidate_numbers, combo_size):
            score = sum(counter.get(n, 0) for n in combo)
            if len(score_heap) < target_rows:
                heapq.heappush(score_heap, -score)
            elif score < -score_heap[0]:
                heapq.heapreplace(score_heap, -score)

        if score_heap:
            cutoff_score = -score_heap[0]
            selected: list[tuple[int, tuple[int, int, int, int, int, int]]] = []
            for combo in combinations(candidate_numbers, combo_size):
                score = sum(counter.get(n, 0) for n in combo)
                if score <= cutoff_score:
                    selected.append((score, combo))

            selected.sort(key=lambda item: (item[0], item[1]))
            current_rank = 0
            previous_score: int | None = None
            for score, combo in selected:
                if previous_score is None or score != previous_score:
                    current_rank += 1
                    previous_score = score
                rows.append(AnalysisRow(rank=current_rank, combo=combo))

    summary = AnalysisSummary(
        total_rows=parse_summary.total_rows,
        valid_rows=parse_summary.valid_rows,
        invalid_rows=parse_summary.invalid_rows,
        filtered_rows=filtered_rows,
        total_numeric_cells=total_numeric_cells,
        unique_numbers=unique_count,
    )
    return rows, summary


def analyze_least_numbers(
    records: Sequence[DrawRecord],
    parse_summary: ParseSummary,
    bottom_count: int,
    window: str,
    custom_start: date | None = None,
    custom_end: date | None = None,
    min_value: int | None = None,
    max_value: int | None = None,
) -> tuple[list[AnalysisRow], AnalysisSummary]:
    return analyze_least_combinations(
        records=records,
        parse_summary=parse_summary,
        bottom_count=bottom_count,
        window=window,
        custom_start=custom_start,
        custom_end=custom_end,
        min_value=min_value,
        max_value=max_value,
    )
