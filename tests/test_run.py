from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import run  # noqa: E402
from scripts.common.models import SkillRuntimeError  # noqa: E402


class RunEntrypointTest(unittest.TestCase):
    def test_dispatch_stock_task(self) -> None:
        expected = {"scenario": "STOCK_ANALYZE", "symbol": "002156.XSHE"}

        with patch.object(run, "analyze_stock_request", return_value=expected):
            payload = run.dispatch_task(
                Namespace(
                    task="stock_analyze",
                    query="分析通富微电",
                    symbol="002156",
                    theme="",
                    bars=90,
                    top=10,
                )
            )

        self.assertEqual(payload, expected)

    def test_error_payload_maps_runtime_error_code(self) -> None:
        exc = SkillRuntimeError("未配置 RQDATA_PRIMARY_URI，无法执行 A 股、ETF 或大盘分析。请先设置 RQData 连接环境变量。")

        payload = run.build_error_payload(exc, task="market_overview")

        self.assertEqual(payload["ok"], False)
        self.assertEqual(payload["error"]["code"], "rqdata_unavailable")
        self.assertEqual(payload["error"]["task"], "market_overview")

    def test_run_help_is_directory_independent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [sys.executable, str(ROOT / "run.py"), "--help"],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn("--task", result.stdout)
        self.assertIn("stock_analyze", result.stdout)

    def test_legacy_wrapper_help_is_directory_independent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "analyze_market.py"), "--help"],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                env=os.environ.copy(),
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn("--query", result.stdout)


if __name__ == "__main__":
    unittest.main()
