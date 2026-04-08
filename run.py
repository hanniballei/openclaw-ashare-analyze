#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from common.analysis_engine import (  # noqa: E402
    analyze_etf_request,
    analyze_market_request,
    analyze_stock_request,
    analyze_theme_request,
    analyze_us_stock_request,
    build_trading_strategy_request,
    run_stock_picker_request,
)
from common.formatters import to_json  # noqa: E402
from common.models import SkillRuntimeError  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified entrypoint for the ashare-analyze skill.")
    parser.add_argument(
        "--task",
        required=True,
        choices=[
            "stock_analyze",
            "etf_analyze",
            "market_overview",
            "trading_strategy",
            "us_stock",
            "stock_picker",
            "theme_analyze",
        ],
    )
    parser.add_argument("--query", default="")
    parser.add_argument("--symbol", default="")
    parser.add_argument("--theme", default="")
    parser.add_argument("--bars", type=int, default=90)
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--compact", action="store_true")
    return parser


def execute_legacy_wrapper(task: str, description: str, argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=description)
    if task == "market_overview":
        parser.add_argument("--query", default="今天 A 股走势如何")
        parser.add_argument("--bars", type=int, default=90)
        parser.add_argument("--compact", action="store_true")
    elif task == "theme_analyze":
        parser.add_argument("--query", default="")
        parser.add_argument("--theme", default="")
        parser.add_argument("--bars", type=int, default=90)
        parser.add_argument("--top", type=int, default=5)
        parser.add_argument("--compact", action="store_true")
    elif task == "stock_picker":
        parser.add_argument("--query", default="")
        parser.add_argument("--symbol", default="")
        parser.add_argument("--bars", type=int, default=90)
        parser.add_argument("--top", type=int, default=10)
        parser.add_argument("--compact", action="store_true")
    else:
        parser.add_argument("--query", default="")
        parser.add_argument("--symbol", default="")
        parser.add_argument("--bars", type=int, default=90)
        parser.add_argument("--compact", action="store_true")

    parsed = parser.parse_args(argv)
    if not hasattr(parsed, "task"):
        setattr(parsed, "task", task)
    try:
        payload = dispatch_task(parsed)
    except SkillRuntimeError as exc:
        print(to_json(build_error_payload(exc, task=task), pretty=not getattr(parsed, "compact", False)))
        raise SystemExit(1)
    print(to_json(payload, pretty=not getattr(parsed, "compact", False)))


def dispatch_task(args: argparse.Namespace) -> Dict[str, Any]:
    if args.task == "stock_analyze":
        _require_any(args, "query", "symbol")
        return analyze_stock_request(query=args.query, symbol=args.symbol or None, bars=args.bars)
    if args.task == "etf_analyze":
        _require_any(args, "query", "symbol")
        return analyze_etf_request(query=args.query, symbol=args.symbol or None, bars=args.bars)
    if args.task == "market_overview":
        return analyze_market_request(query=args.query or "今天 A 股走势如何", bars=args.bars)
    if args.task == "trading_strategy":
        _require_any(args, "query", "symbol")
        return build_trading_strategy_request(query=args.query, symbol=args.symbol or None, bars=args.bars)
    if args.task == "us_stock":
        _require_any(args, "query", "symbol")
        return analyze_us_stock_request(query=args.query, symbol=args.symbol or None, bars=args.bars)
    if args.task == "stock_picker":
        _require_any(args, "query", "symbol")
        return run_stock_picker_request(query=args.query, symbol=args.symbol or None, bars=args.bars, top=args.top)
    if args.task == "theme_analyze":
        if not args.query and not args.theme:
            raise SkillRuntimeError("请至少提供 --query 或 --theme，用于确定主题。")
        return analyze_theme_request(query=args.query or args.theme, theme=args.theme or None, bars=args.bars, top=args.top)
    raise SkillRuntimeError(f"未支持的 task: {args.task}")


def build_error_payload(exc: SkillRuntimeError, task: str) -> Dict[str, Any]:
    return {
        "ok": False,
        "error": {
            "code": _classify_error_code(str(exc)),
            "message": str(exc),
            "task": task,
        },
    }


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        payload = dispatch_task(args)
    except SkillRuntimeError as exc:
        print(to_json(build_error_payload(exc, task=args.task), pretty=not args.compact))
        raise SystemExit(1)
    print(to_json(payload, pretty=not args.compact))


def _require_any(args: argparse.Namespace, *fields: str) -> None:
    if any(getattr(args, field, "") for field in fields):
        return
    rendered = " 或 ".join(f"--{field}" for field in fields)
    raise SkillRuntimeError(f"请至少提供 {rendered}。")


def _classify_error_code(message: str) -> str:
    if "未配置 RQDATA_PRIMARY_URI" in message or "RQData 主连接失败" in message or "RQData 主备连接均失败" in message:
        return "rqdata_unavailable"
    if "未安装 rqdatac" in message or "未安装 yfinance" in message:
        return "dependency_missing"
    if "未在 RQData 中找到标的" in message:
        return "symbol_not_found"
    if "未在 RQData 中匹配到主题/板块" in message:
        return "theme_not_found"
    if "未获取到 ETF 成分股" in message:
        return "empty_payload"
    return "runtime_error"


if __name__ == "__main__":
    main()
