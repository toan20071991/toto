from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from typing import Sequence

from .models import AnalysisRow, AnalysisSummary, DrawRecord, ParseSummary


def _resolve_date_range(
    records: Sequence[DrawRecord],
    window: str | None,
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

    if window is None:
        return min(r.draw_date for r in records), max(r.draw_date for r in records)

    end = custom_end or max(r.draw_date for r in records)
    if window == "3m":
        return end - timedelta(days=90), end
    if window == "6m":
        return end - timedelta(days=180), end
    if window == "1y":
        return end - timedelta(days=365), end
    if window == "2y":
        return end - timedelta(days=730), end
    raise ValueError("window must be one of: 3m, 6m, 1y, 2y, custom")


def analyze_numbers(
    records: Sequence[DrawRecord],
    parse_summary: ParseSummary,
    count: int = 10,
    mode: str = "least",
    window: str | None = None,
    custom_start: date | None = None,
    custom_end: date | None = None,
    min_value: int | None = None,
    max_value: int | None = None,
) -> tuple[list[AnalysisRow], AnalysisSummary]:
    if count < 0:
        raise ValueError("count must be >= 0")
    if mode not in ("least", "most"):
        raise ValueError("mode must be 'least' or 'most'")
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

    target_rows = max(1, count)
    ranked: list[tuple[int, int]] = []
    for number in candidate_numbers:
        ranked.append((counter.get(number, 0), number))

    selected: list[tuple[int, int]] = []
    if mode == "most":
        ranked.sort(key=lambda item: (-item[0], item[1]))
        if ranked:
            if target_rows >= len(ranked):
                selected = ranked
            else:
                cutoff_frequency = ranked[target_rows - 1][0]
                selected = [item for item in ranked if item[0] >= cutoff_frequency]
    else:  # "least"
        ranked.sort(key=lambda item: (item[0], item[1]))
        if ranked:
            if target_rows >= len(ranked):
                selected = ranked
            else:
                cutoff_frequency = ranked[target_rows - 1][0]
                selected = [item for item in ranked if item[0] <= cutoff_frequency]

    current_rank = 0
    previous_frequency: int | None = None
    for frequency, number in selected:
        if previous_frequency is None or frequency != previous_frequency:
            current_rank += 1
            previous_frequency = frequency
        percentage = 0.0
        if total_numeric_cells > 0:
            percentage = round((frequency / total_numeric_cells) * 100, 3)
        rows.append(
            AnalysisRow(
                rank=current_rank,
                number=number,
                frequency=frequency,
                percentage=percentage,
            )
        )

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
    window: str | None = None,
    custom_start: date | None = None,
    custom_end: date | None = None,
    min_value: int | None = None,
    max_value: int | None = None,
) -> tuple[list[AnalysisRow], AnalysisSummary]:
    return analyze_numbers(
        records=records,
        parse_summary=parse_summary,
        count=bottom_count,
        mode="least",
        window=window,
        custom_start=custom_start,
        custom_end=custom_end,
        min_value=min_value,
        max_value=max_value,
    )


def analyze_most_numbers(
    records: Sequence[DrawRecord],
    parse_summary: ParseSummary,
    top_count: int,
    window: str | None = None,
    custom_start: date | None = None,
    custom_end: date | None = None,
    min_value: int | None = None,
    max_value: int | None = None,
) -> tuple[list[AnalysisRow], AnalysisSummary]:
    return analyze_numbers(
        records=records,
        parse_summary=parse_summary,
        count=top_count,
        mode="most",
        window=window,
        custom_start=custom_start,
        custom_end=custom_end,
        min_value=min_value,
        max_value=max_value,
    )


def analyze_least_combinations(
    records: Sequence[DrawRecord],
    parse_summary: ParseSummary,
    bottom_count: int,
    window: str | None = None,
    custom_start: date | None = None,
    custom_end: date | None = None,
    min_value: int | None = None,
    max_value: int | None = None,
) -> tuple[list[AnalysisRow], AnalysisSummary]:
    return analyze_least_numbers(
        records=records,
        parse_summary=parse_summary,
        bottom_count=bottom_count,
        window=window,
        custom_start=custom_start,
        custom_end=custom_end,
        min_value=min_value,
        max_value=max_value,
    )
