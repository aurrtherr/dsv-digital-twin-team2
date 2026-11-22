"""Formatting helpers that match the original JavaScript prototype exactly.

JavaScript's toFixed rounds halves up on the exact binary value, Math.round rounds
halves towards +infinity, and toLocaleString('en-US') adds thousands separators.
Python's defaults differ (banker's rounding), so these helpers keep the backend's
text identical to the prototype's.
"""
from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal

WD = ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]  # 1 Aug 2026 is a Saturday


def to_fixed(x: float, digits: int = 1) -> str:
    q = Decimal(1).scaleb(-digits)
    d = Decimal(float(x)).quantize(q, rounding=ROUND_HALF_UP)
    return format(d, "f")


def js_round(x: float) -> int:
    return int(math.floor(x + 0.5))


def js_num(x) -> str:
    """Number#toString for the values this app prints (no exponents)."""
    if isinstance(x, bool):
        return str(x).lower()
    if isinstance(x, int):
        return str(x)
    f = float(x)
    if f.is_integer():
        return str(int(f))
    return repr(f)


def fmt(n) -> str:
    """Number(n).toLocaleString('en-US'): thousands separators, at most 3 decimals."""
    f = float(n)
    if f.is_integer():
        return f"{int(f):,}"
    d = Decimal(f).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    s = f"{d:,.3f}".rstrip("0").rstrip(".")
    return s


def pct(a, b) -> float:
    return 100 * a / b if b else 0


def day_of(t: int) -> int:
    return t // 1440


def day_label(d: int) -> str:
    return f"{WD[d % 7]} {d + 1} Aug"


def day_n(d: int) -> str:
    return day_label(d).replace(" Aug", "")


def hhmm(t) -> str:
    m = int(((t % 1440) + 1440) % 1440)
    return f"{m // 60:02d}:{m % 60:02d}"


def when(t) -> str:
    return "—" if t is None else f"{day_label(day_of(t))} {hhmm(t)}"


def hrs(m) -> str:
    return to_fixed(m / 60, 1)


def dkey(d: int) -> str:
    return f"2026-08-{d + 1:02d}"


def in_min(m: int) -> str:
    if m < 60:
        return f"{m} min"
    return f"{m // 60} h" + (f" {m % 60} min" if m % 60 else "")


def plural(n: int, one: str, many: str) -> str:
    return one if n == 1 else many
