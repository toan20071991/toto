from __future__ import annotations

import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from unittest.mock import patch

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from lotto_analyzer.analyzer import analyze_numbers, resolve_date_range, suggest_numbers
from lotto_analyzer.models import DrawRecord
from lotto_analyzer.parser import parse_csv_file
from lotto_analyzer.report import CHARTS, SIMULATIONS, _calculate, write_report


def _strict_json(path: Path):
    def reject_constant(value):
        raise ValueError(f"Non-finite JSON value: {value}")
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)


class ReportTests(unittest.TestCase):
    def test_statistics_range_bonus_accounting_and_determinism(self) -> None:
        records = [
            DrawRecord(date(2026, 1, 1), (10, 11, 12, 13, 14, 15, 16)),
            DrawRecord(date(2026, 1, 2), (11, 12, 13, 14, 15, 16, 17)),
        ]
        first, data = _calculate(records, 10, 18, 12)
        second, _ = _calculate(records, 10, 18, 12)
        self.assertEqual(first, second)
        self.assertEqual(sum(hits for _, hits in first["main_frequency_ranking"]), 12)
        self.assertEqual(sum(hits for _, hits in first["bonus_frequency_ranking"]), 2)
        self.assertEqual(dict(first["bonus_frequency_ranking"])[16], 1)
        self.assertEqual(first["expected_sum"], 84)
        self.assertAlmostEqual(first["expected_pair_frequency"], 2 * 30 / 72)
        self.assertEqual(sum(pair[2] for pair in first["top_pairs"]), 25)
        np.testing.assert_array_equal(np.diag(data[4]), data[2])
        self.assertEqual(data[4][np.triu_indices(9, 1)].sum(), 30)
        self.assertEqual(records[0].numbers, (10, 11, 12, 13, 14, 15, 16))
        self.assertEqual(SIMULATIONS, 5000)

    def test_wide_pair_counts(self) -> None:
        records = [DrawRecord(date(2026, 1, 1), (1, 2, 3, 4, 5, 6, 7))] * 32769
        statistics, _ = _calculate(records, 1, 7, 1)
        self.assertEqual(statistics["top_pairs"][0], (1, 2, 32769))

    def test_shared_preset_and_custom_windows(self) -> None:
        records = [
            DrawRecord(date(2025, 1, 1), (1, 2, 3, 4, 5, 6, 7)),
            DrawRecord(date(2026, 1, 1), (1, 2, 3, 4, 5, 6, 8)),
            DrawRecord(date(2026, 1, 31), (1, 2, 3, 4, 5, 6, 9)),
        ]
        with tempfile.TemporaryDirectory() as temporary, patch("lotto_analyzer.report._render_charts"):
            for window in (None, "3m", "6m", "1y", "2y", "custom"):
                with self.subTest(window=window):
                    start, end = resolve_date_range(records, window, date(2026, 1, 1), date(2026, 1, 31))
                    result = write_report(records, temporary, 1, 9, window,
                                          date(2026, 1, 1), date(2026, 1, 31), simulations=2)
                    self.assertEqual(result["draws"], sum(start <= row.draw_date <= end for row in records))
                    self.assertEqual(result["window_start"], str(start))
                    self.assertEqual(result["window_end"], str(end))
            self.assertEqual(result["draws"], 2)

    def test_empty_invalid_single_and_constant_histories_refresh_artifacts(self) -> None:
        single = DrawRecord(date(2026, 1, 1), (10, 11, 12, 13, 14, 15, 16))
        duplicate = DrawRecord(date(2026, 1, 2), (10, 10, 12, 13, 14, 15, 16))
        out_of_range = DrawRecord(date(2026, 1, 3), (10, 11, 12, 13, 14, 15, 99))
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            for records in ([single], [single, single], [duplicate, out_of_range], []):
                with self.subTest(records=len(records)):
                    for filename in (*CHARTS, "statistics.json", "report.md"):
                        (folder / filename).write_text("stale", encoding="utf-8")
                    before_style = dict(plt.rcParams)
                    result = write_report(records, folder, 10, 18, simulations=2)
                    self.assertEqual(json.loads(json.dumps(result, allow_nan=False)),
                                     _strict_json(folder / "statistics.json"))
                    self.assertIn("not predictions", (folder / "report.md").read_text(encoding="utf-8"))
                    for filename in CHARTS:
                        with Image.open(folder / filename) as image:
                            self.assertGreater(image.width, 500)
                            self.assertGreater(float(np.asarray(image).std()), 1)
                    self.assertEqual(plt.get_fignums(), [])
                    self.assertEqual(dict(plt.rcParams), before_style)
                    if len(records) == 1:
                        self.assertIsNone(result["mean_overlap_between_draws"])
                        self.assertIsNone(result["overlap_monte_carlo_p"])
                    if not result["draws"]:
                        self.assertEqual(result["status"], "unavailable")
                        self.assertEqual(result["excluded_report_rows"], len(records))

    def test_narrow_range_and_no_matching_dates(self) -> None:
        record = DrawRecord(date(2026, 1, 1), (1, 1, 2, 3, 4, 5, 6))
        with tempfile.TemporaryDirectory() as temporary, patch("lotto_analyzer.report._unavailable_charts"):
            result = write_report([record], temporary, 1, 6, simulations=2)
            self.assertEqual(result["status"], "unavailable")
            result = write_report([record], temporary, 1, 49, "custom",
                                  date(2027, 1, 1), date(2027, 1, 31), simulations=2)
            self.assertEqual(result["filtered_rows"], 0)
            self.assertEqual(result["draws"], 0)

    def test_cli_refreshes_all_artifacts_without_changing_csv_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            source = folder / "draws.csv"
            source.write_text(
                "2025-01-01,10,11,12,13,14,15,16\n"
                "2026-01-01,10,11,12,13,14,15,16\n"
                "2026-01-02,11,12,13,14,15,16,17\n"
                "2026-01-03,10,10,12,13,14,15,16\n"
                "bad,row\n", encoding="utf-8",
            )
            range_path = folder / "range.json"
            range_path.write_text('{"min_value": 10, "max_value": 18}', encoding="utf-8")
            ranking_path = folder / "rank.csv"
            suggestion_path = folder / "suggest.csv"
            config = {
                "input": str(source), "output": str(ranking_path),
                "suggestion_output": str(suggestion_path), "range_config": str(range_path),
                "window": "custom", "start_date": "2026-01-01", "end_date": "2026-01-03",
                "recent_draw_count": 1, "bottom_count": 3,
            }
            config_path = folder / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            records, summary = parse_csv_file(source, 10, 18)
            rows, _ = analyze_numbers(records, summary, count=3, window="custom",
                                      custom_start=date(2026, 1, 1), custom_end=date(2026, 1, 3),
                                      min_value=10, max_value=18)
            expected_ranking = io.StringIO(newline="")
            writer = csv.writer(expected_ranking)
            writer.writerow(["rank", "number", "frequency", "percentage"])
            writer.writerows([row.rank, row.number, row.frequency, f"{row.percentage:.3f}"] for row in rows)
            expected_suggestions = io.StringIO(newline="")
            writer = csv.writer(expected_suggestions)
            writer.writerow(["number"])
            writer.writerows([number] for number in suggest_numbers(records, 1, [row.number for row in rows]))
            input_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            environment = dict(os.environ)
            environment.pop("PYTHONPATH", None)
            report_folder = folder / "toto_patterns"
            old_times = {}
            original_statistics = None
            for module in ("src.lotto_analyzer.cli", "lotto_analyzer.cli"):
                completed = subprocess.run(
                    [sys.executable, "-B", "-m", module, str(config_path)],
                    cwd=Path(__file__).resolve().parents[1], env=environment,
                    capture_output=True, text=True, check=True,
                )
                self.assertIn("report_draws=2", completed.stdout)
                self.assertIn("report_excluded_rows=1", completed.stdout)
                self.assertEqual(ranking_path.read_bytes(), expected_ranking.getvalue().encode())
                self.assertEqual(suggestion_path.read_bytes(), expected_suggestions.getvalue().encode())
                self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), input_hash)
                statistics = _strict_json(report_folder / "statistics.json")
                self.assertEqual(statistics["simulations"], 5000)
                if original_statistics is not None:
                    self.assertEqual(statistics, original_statistics)
                original_statistics = statistics
                for filename in (*CHARTS, "statistics.json", "report.md"):
                    artifact = report_folder / filename
                    self.assertGreater(artifact.stat().st_mtime_ns, old_times.get(filename, 0))
                    os.utime(artifact, ns=(1_000_000_000, 1_000_000_000))
                    old_times[filename] = artifact.stat().st_mtime_ns


if __name__ == "__main__":
    unittest.main()