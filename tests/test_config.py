from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lotto_analyzer.config import load_analyzer_config, load_range_config


class ConfigTests(unittest.TestCase):
    def test_load_valid_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "range.json"
            path.write_text('{"min_value": 1, "max_value": 49}', encoding="utf-8")

            cfg = load_range_config(path)

        self.assertEqual(cfg.min_value, 1)
        self.assertEqual(cfg.max_value, 49)

    def test_invalid_bounds_raise_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "range.json"
            path.write_text('{"min_value": 50, "max_value": 49}', encoding="utf-8")

            with self.assertRaises(ValueError):
                load_range_config(path)

    def test_load_analyzer_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "analyzer_config.json"
            path.write_text(
                '{"input": "in.csv", "output": "out.csv", "mode": "most", "top_count": 5, "window": "6m"}',
                encoding="utf-8",
            )

            cfg = load_analyzer_config(path)

        self.assertEqual(cfg.input, "in.csv")
        self.assertEqual(cfg.output, "out.csv")
        self.assertEqual(cfg.mode, "most")
        self.assertEqual(cfg.top_count, 5)
        self.assertEqual(cfg.window, "6m")


if __name__ == "__main__":
    unittest.main()
