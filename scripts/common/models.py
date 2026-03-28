from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional


class SkillRuntimeError(RuntimeError):
    """Raised when a scenario cannot produce a trustworthy payload."""


@dataclass
class Candle:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    amount: float = 0.0
    prev_close: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InstrumentMatch:
    symbol: str
    name: str
    instrument_type: str
    market: str = "CN"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ThemeMatch:
    query: str
    name: str
    source: str
    provider: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PositionInput:
    shares: Optional[int] = None
    avg_price: Optional[float] = None
    entry_date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
