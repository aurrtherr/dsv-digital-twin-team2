"""Screen: Staffing what-if (view id "whatif").
"""
from __future__ import annotations

import math

from ..engine import Ctx, Snap
from ..fmt import day_label, day_n, fmt, js_round
from .common import bars_spec, R


WI_DAYS = ["2026-08-17", "2026-08-18", "2026-08-19", "2026-08-20", "2026-08-21", "2026-08-22", "2026-08-23"]


def whatif(ctx: Ctx, wi: int) -> dict:
    D = ctx.D
    load = [D.in_lines_day.get(d, 0) + D.out_lines_day.get(d, 0) for d in WI_DAYS]
    av = sum(load) / len(load)
    prod = av / 20
    x = wi / 100
    need = lambda v, pr=prod: math.ceil(v * (1 + x) / pr - 1e-9)
    peak_i = load.index(max(load))
    wd = load[:5]
    over = sum(1 for v in wd if need(v) > 20)
    wavg = sum(wd) / 5
    lo = lambda v: need(v, prod * 1.1)
    hi = lambda v: need(v, prod * 0.9)
    sign = "+" if wi > 0 else ""
    rows = []
    for k, d in enumerate(WI_DAYS):
        n = need(load[k])
        rows.append({"label": day_n(int(d[8:]) - 1), "vals": [n], "faint": k > 4, "colors": ["var(--due)" if n > 20 else "var(--bar)"],
                     "tips": [f"{n} people"], "valLabels": [f"{n} (+{n - 20})" if n > 20 else str(n)]})
    table = [{"day": r["label"], "lines": fmt(load[k]), "linesX": fmt(js_round(load[k] * (1 + wi / 100))), "people": need(load[k]),
              "delta": f"{'+' if need(load[k]) - 20 > 0 else ''}{need(load[k]) - 20}", "over": need(load[k]) > 20} for k, r in enumerate(rows)]
    nw = need(wavg)
    return {
        "wi": wi, "sentence": R("At ", (f"{sign}{wi}% volume", True), " a typical weekday needs ", (f"{nw} people", True),
                                f" ({'+' if nw - 20 >= 0 else ''}{nw - 20} vs today) and the busiest day ", (str(need(load[peak_i])), True), f". {over} of 5 weekdays go over 20."),
        "typical": {"n": nw, "range": f"range {lo(wavg)}–{hi(wavg)}"},
        "busiest": {"lab": f"Busiest day ({day_label(int(WI_DAYS[peak_i][8:]) - 1)})", "n": need(load[peak_i]), "range": f"range {lo(load[peak_i])}–{hi(load[peak_i])}"},
        "avgLoad": f"{fmt(js_round(av))} lines a day (Mon–Sun)", "prod": f"{fmt(js_round(prod))} lines per person a day",
        "chart": bars_spec(rows, "People needed each day", max([45] + [r["vals"][0] for r in rows]) * 1.1, [0, 10, 20, 30, 40], str, 20, "Today: 20 people"),
        "table": table, "linesHead": f"Lines at {sign}{wi}%",
    }


def v_whatif(ctx: Ctx, snap: Snap, p: dict) -> dict:
    return whatif(ctx, int(p.get("wi", 20)))
