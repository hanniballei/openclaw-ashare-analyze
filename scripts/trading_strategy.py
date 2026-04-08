#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from run import execute_legacy_wrapper  # noqa: E402


if __name__ == "__main__":
    execute_legacy_wrapper("trading_strategy", "Generate a trading strategy payload from a user query.")
