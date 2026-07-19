from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lotto_analyzer.config import load_range_config


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


if __name__ == "__main__":
    unittest.main()
