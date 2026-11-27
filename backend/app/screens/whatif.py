"""Screen: Staffing what-if (view id "whatif").
If volume changes by X%, how many people are needed each day and what does
that manpower cost?
"""
from __future__ import annotations

import math

from ..engine import Ctx, Snap
from ..fmt import day_label, day_n, fmt, js_round
from .common import bars_spec, R


WI_DAYS = ["2026-08-17", "2026-08-18", "2026-08-19", "2026-08-20", "2026-08-21", "2026-08-22", "2026-08-23"]

STAFF = 20            # people on shift per day today
SHIFT_HOURS = 8.0     # hours per shift
PROD_BAND = 0.10      # +/-10% productivity for the low/high range
NORMAL_WEEK_HOURS = 44     # MOM normal working hours per week
DEFAULT_WAGE = 2200        # fallback only; live value comes from Settings ("wage")


def money(v: float) -> str:
    return f"S${js_round(v):,}"


def _signed(n: int) -> str:
    return f"+{n}" if n > 0 else str(n)


def _need(lines: float, prod: float) -> int:
    """People needed. 1e-9 stops float noise (20.0000001) rounding up to 21."""
    return math.ceil(lines / prod - 1e-9)

def whatif(ctx: Ctx, wi: int) -> dict:
    D = ctx.D
    x = wi / 100
    sign = "+" if wi > 0 else ""

    # 1-4. Manpower
    load = [D.in_lines_day.get(d, 0) + D.out_lines_day.get(d, 0) for d in WI_DAYS]
    av = sum(load) / len(load)
    prod = av / STAFF
    prod_hr = prod / SHIFT_HOURS
    load_x = [v * (1 + x) for v in load]
    need = [_need(v, prod) for v in load_x]
    need_lo = lambda v: _need(v, prod * (1 + PROD_BAND))
    need_hi = lambda v: _need(v, prod * (1 - PROD_BAND))

    peak_i = load.index(max(load))
    wk_lines = sum(load_x[:5]) / 5
    nw = _need(wk_lines, prod)
    over = sum(1 for n in need[:5] if n > STAFF)

    # 5-6. Additional cost per day
    wage = float(getattr(ctx, "cfg", {}).get("wage", DEFAULT_WAGE))
    hr = 12 * wage / (52 * NORMAL_WEEK_HOURS)
    extra = lambda people: max(0, people - STAFF) * SHIFT_HOURS * hr
    costs = [extra(n) for n in need]
    peak_cost = costs[peak_i]

    rows, table = [], []
    for k, d in enumerate(WI_DAYS):
        n = need[k]
        lab = day_n(int(d[8:]) - 1)
        tip = f"{n} people" + (f" · +{money(costs[k])}" if costs[k] else "")
        rows.append({"label": lab, "vals": [n], "faint": k > 4,
                     "colors": ["var(--due)" if n > STAFF else "var(--bar)"],
                     "tips": [tip],
                     "valLabels": [f"{n} ({_signed(n - STAFF)})" if n > STAFF else str(n)]})
        table.append({"day": lab, "lines": fmt(load[k]), "linesX": fmt(js_round(load_x[k])),
                      "people": n, "delta": _signed(n - STAFF), "over": n > STAFF,
                      "extraCost": money(costs[k])})

    derivation = [
        {"step": "1. Average daily load", "formula": f"({' + '.join(fmt(v) for v in load)}) / 7",
         "value": f"{fmt(js_round(av))} lines a day"},
        {"step": "2. Productivity", "formula": f"{fmt(js_round(av))} lines / {STAFF} people / {SHIFT_HOURS:g} h",
         "value": f"{fmt(js_round(prod))} lines a person a day = {prod_hr:.1f} an hour",
         "check": f"WERC median is 35 lines/hour outbound and 22 inbound; ours is "
                  f"{'below' if prod_hr < 22 else 'within' if prod_hr <= 35 else 'above'} that band."},
        {"step": "3. Typical weekday load", "formula": f"{fmt(js_round(wk_lines / (1 + x)))} x (1 {'+' if x >= 0 else '-'} {abs(wi)}%)",
         "value": f"{fmt(js_round(wk_lines))} lines"},
        {"step": "4. Manpower needed", "formula": f"ceil({fmt(js_round(wk_lines))} / {fmt(js_round(prod))})",
         "value": f"{nw} people ({_signed(nw - STAFF)} vs today)"},
        {"step": "5. Cost of one staff hour",
         "formula": f"12 x {money(wage)} / (52 x {NORMAL_WEEK_HOURS})",
         "value": f"S${hr:.2f} an hour"},
        {"step": "6. Additional cost of a typical weekday",
         "formula": f"{max(0, nw - STAFF)} extra people x {SHIFT_HOURS:g} h x S${hr:.2f}",
         "value": f"{money(extra(nw))} a day"},
    ]

    cost_parts = ([" The extra manpower costs ", (f"{money(extra(nw))} on a typical weekday", True),
                   " and ", (money(peak_cost), True), " on the busiest day."]
                  if peak_cost or extra(nw) else [" No additional manpower is needed."])

    return {
        "wi": wi,
        "sentence": R("At ", (f"{sign}{wi}% volume", True), " a typical weekday needs ", (f"{nw} people", True),
                      f" ({_signed(nw - STAFF)} vs today) and the busiest day ", (str(need[peak_i]), True),
                      f". {over} of 5 weekdays go over {STAFF}.", *cost_parts),
        "typical": {"n": nw, "range": f"range {need_lo(wk_lines)}–{need_hi(wk_lines)}",
                    "extraCost": money(extra(nw))},
        "busiest": {"lab": f"Busiest day ({day_label(int(WI_DAYS[peak_i][8:]) - 1)})", "n": need[peak_i],
                    "range": f"range {need_lo(load_x[peak_i])}–{need_hi(load_x[peak_i])}",
                    "extraCost": money(peak_cost)},
        "rate": f"S${hr:.2f} an hour",
        "wage": {"value": money(wage), "placeholder": wage == DEFAULT_WAGE,
                 "note": "Basic monthly wage, set on the Settings screen"},
        "avgLoad": f"{fmt(js_round(av))} lines a day (Mon–Sun)",
        "prod": f"{fmt(js_round(prod))} lines per person a day ({prod_hr:.1f} an hour)",
        "chart": bars_spec(rows, "People needed each day", max([45] + need) * 1.1, [0, 10, 20, 30, 40], str,
                           STAFF, f"Today: {STAFF} people"),
        "table": table,
        "linesHead": f"Lines at {sign}{wi}%",
        "derivation": derivation,
        "caveats": [
            "Additional people are costed at basic pay only; CPF, on-costs, overtime and temp premiums are not included.",
            "The basic wage is a placeholder until changed on the Settings screen.",
        ],
    }


def v_whatif(ctx: Ctx, snap: Snap, p: dict) -> dict:
    return whatif(ctx, int(p.get("wi", 20)))

