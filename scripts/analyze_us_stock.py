#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from common.analysis_engine import main_us_stock  # noqa: E402
from common.models import SkillRuntimeError  # noqa: E402


if __name__ == "__main__":
    try:
        main_us_stock()
    except SkillRuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise SystemExit(1)
