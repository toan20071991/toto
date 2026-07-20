from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lotto_analyzer.parser import parse_csv_file


class ParserTests(unittest.TestCase):
    def test_parse_valid_and_invalid_rows(self) -> None:
        content = "\n".join(
            [
                "2026-01-10,5,1,8,12,30,45,60",
                "bad-date,5,1,8,12,30,45,60",
                "2026-01-12,5,1,8,12,30,45,100",
                "2026-01-11,5,1,8,12,30,45",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.csv"
            path.write_text(content, encoding="utf-8")

            records, summary = parse_csv_file(path, min_value=1, max_value=60)

        self.assertEqual(summary.total_rows, 4)
        self.assertEqual(summary.valid_rows, 1)
        self.assertEqual(summary.invalid_rows, 3)
        self.assertEqual(records[0].numbers, (5, 1, 8, 12, 30, 45, 60))


if __name__ == "__main__":
    unittest.main()
