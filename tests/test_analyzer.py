from __future__ import annotations

import unittest
from datetime import date

from lotto_analyzer.analyzer import analyze_least_numbers
from lotto_analyzer.models import DrawRecord, ParseSummary


class AnalyzerTests(unittest.TestCase):
    def test_bottom_count_returns_at_least_requested_rows(self) -> None:
        records = [
            DrawRecord(date(2026, 1, 1), (1, 2, 3, 4, 5, 6, 7)),
            DrawRecord(date(2026, 1, 2), (1, 2, 4, 3, 9, 10, 11)),
        ]
        summary = ParseSummary(total_rows=2, valid_rows=2, invalid_rows=0)

        rows, analysis = analyze_least_numbers(
            records=records,
            parse_summary=summary,
            bottom_count=10,
            window="custom",
            custom_start=date(2026, 1, 1),
            custom_end=date(2026, 1, 31),
            min_value=1,
            max_value=11,
        )

        self.assertEqual(analysis.filtered_rows, 2)
        self.assertEqual(analysis.total_numeric_cells, 14)
        self.assertEqual(analysis.unique_numbers, 10)
        self.assertGreaterEqual(len(rows), 10)
        self.assertEqual(rows[0].rank, 1)
        self.assertEqual(rows[0].number, 8)
        self.assertEqual(rows[0].frequency, 0)
        self.assertEqual(rows[0].percentage, 0.0)

    def test_date_range_filter(self) -> None:
        records = [
            DrawRecord(date(2026, 1, 1), (1, 2, 3, 4, 5, 6, 7)),
            DrawRecord(date(2026, 1, 2), (1, 2, 3, 4, 5, 6, 8)),
            DrawRecord(date(2026, 1, 3), (1, 2, 3, 4, 5, 6, 9)),
        ]
        summary = ParseSummary(total_rows=3, valid_rows=3, invalid_rows=0)

        rows, analysis = analyze_least_numbers(
            records=records,
            parse_summary=summary,
            bottom_count=5,
            window="custom",
            custom_start=date(2026, 1, 2),
            custom_end=date(2026, 1, 31),
            min_value=1,
            max_value=9,
        )

        self.assertEqual(analysis.filtered_rows, 2)
        self.assertEqual(analysis.total_numeric_cells, 14)
        self.assertEqual(analysis.unique_numbers, 8)
        self.assertGreaterEqual(len(rows), 5)
        self.assertEqual(rows[0].number, 7)
        self.assertEqual(rows[0].frequency, 0)

    def test_bottom_count_with_small_candidate_range_returns_ranked_numbers(self) -> None:
        records = [
            DrawRecord(date(2026, 1, 1), (1, 2, 3, 4, 5, 6, 7)),
        ]
        summary = ParseSummary(total_rows=1, valid_rows=1, invalid_rows=0)

        rows, analysis = analyze_least_numbers(
            records=records,
            parse_summary=summary,
            bottom_count=1,
            window="custom",
            custom_start=date(2026, 1, 1),
            custom_end=date(2026, 1, 31),
            min_value=1,
            max_value=5,
        )

        self.assertEqual(analysis.unique_numbers, 7)
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0].rank, 1)
        self.assertEqual(rows[0].number, 1)

    def test_tie_at_cutoff_includes_all_rows(self) -> None:
        records = [
            DrawRecord(date(2026, 1, 1), (1, 2, 3, 4, 5, 6, 7)),
        ]
        summary = ParseSummary(total_rows=1, valid_rows=1, invalid_rows=0)

        rows, analysis = analyze_least_numbers(
            records=records,
            parse_summary=summary,
            bottom_count=3,
            window="custom",
            custom_start=date(2026, 1, 1),
            custom_end=date(2026, 1, 31),
            min_value=1,
            max_value=8,
        )

        self.assertEqual(analysis.total_numeric_cells, 7)
        self.assertEqual(len(rows), 8)
        self.assertEqual(rows[0].rank, 1)
        self.assertEqual(rows[0].frequency, 0)
        self.assertEqual(rows[0].number, 8)

    def test_none_window_uses_all_data(self) -> None:
        records = [
            DrawRecord(date(2026, 1, 1), (1, 2, 3, 4, 5, 6, 7)),
            DrawRecord(date(2026, 1, 2), (1, 2, 3, 4, 5, 6, 8)),
            DrawRecord(date(2026, 1, 3), (1, 2, 3, 4, 5, 6, 9)),
        ]
        summary = ParseSummary(total_rows=3, valid_rows=3, invalid_rows=0)

        rows, analysis = analyze_least_numbers(
            records=records,
            parse_summary=summary,
            bottom_count=5,
            window=None,
            min_value=1,
            max_value=9,
        )

        self.assertEqual(analysis.filtered_rows, 3)
        self.assertEqual(analysis.total_numeric_cells, 21)
        self.assertEqual(analysis.unique_numbers, 9)
        self.assertGreaterEqual(len(rows), 5)

    def test_percentage_is_rounded_to_three_decimals(self) -> None:
        records = [
            DrawRecord(date(2026, 1, 1), (1, 1, 1, 2, 2, 3, 4)),
        ]
        summary = ParseSummary(total_rows=1, valid_rows=1, invalid_rows=0)

        rows, analysis = analyze_least_numbers(
            records=records,
            parse_summary=summary,
            bottom_count=4,
            window="custom",
            custom_start=date(2026, 1, 1),
            custom_end=date(2026, 1, 31),
            min_value=1,
            max_value=4,
        )

        self.assertEqual(analysis.total_numeric_cells, 7)
        percentage_by_number = {row.number: row.percentage for row in rows}
        self.assertEqual(percentage_by_number[1], 42.857)
        self.assertEqual(percentage_by_number[2], 28.571)
        self.assertEqual(percentage_by_number[3], 14.286)
        self.assertEqual(percentage_by_number[4], 14.286)


if __name__ == "__main__":
    unittest.main()
