from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RangeConfig:
    min_value: int
    max_value: int


def _as_positive_int(value: object, field_name: str) -> int:
    if not isinstance(value, int):
        raise ValueError(f"Config field '{field_name}' must be an integer.")
    if value <= 0:
        raise ValueError(f"Config field '{field_name}' must be a positive integer.")
    return value


def load_range_config(config_path: str | Path) -> RangeConfig:
    path = Path(config_path)
    if not path.exists():
        raise ValueError(f"Config file not found: {path}")

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Config file is not valid JSON: {path}") from exc

    if not isinstance(raw, dict):
        raise ValueError("Config JSON must be an object.")

    min_value = _as_positive_int(raw.get("min_value"), "min_value")
    max_value = _as_positive_int(raw.get("max_value"), "max_value")
    if min_value > max_value:
        raise ValueError("Config bounds are invalid: min_value must be <= max_value.")

    return RangeConfig(min_value=min_value, max_value=max_value)
