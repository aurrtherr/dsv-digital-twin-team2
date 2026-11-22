"""Screen: Data checks (view id "checks").
"""
from __future__ import annotations

import math

from ..engine import Ctx, kpi_fns, Snap
from ..fmt import fmt, pct, to_fixed
from .common import page_cards, page_kpis, R


def v_checks(ctx: Ctx, snap: Snap, p: dict) -> dict:
    q, K = ctx.D.dq, kpi_fns(ctx)
    rows = [
        ["DQ-01", "Planned date before order date", q["planned_before_created"], "orders", "Label; ask DSV which date is right"],
        ["DQ-02", "No planned date", q["no_planned_date"], "orders", ", ".join(f"{k} {fmt(v)}" for k, v in q["no_planned_date_by_type"].items())],
        ["DQ-03", "Docked, no receipt for 120 h+", None, "ASNs", "Raised live on Operations overview, not as a floor alert"],
        ["DQ-06", "Identical outbound rows", q["identical_rows"], "rows", "Label, never delete"],
        ["DQ-07", "Inbound rows with no dock time", q["rows_no_dock"], "rows", f"{fmt(q['asns_no_dock'])} ASNs"],
        ["DQ-07", "Inbound rows with no putaway zone", q["rows_no_zone"], "rows", ""],
        ["DQ-07", "Placeholder carton size (“X X”)", q["placeholder_sizes"], "rows", "No usable dimensions"],
        ["DQ-07", "Carton IDs shared by more than one order", q["shared_carton_ids"], "cartons", ""],
        ["—", "Urgent Flag = Y", q["urgent_y_rows"], "rows", f"{to_fixed(pct(q['urgent_y_rows'], q['outbound_rows']), 0)}% of {fmt(q['outbound_rows'])} outbound rows, so it cannot rank anything"],
    ]
    n_open = len(snap.noPlan) + K["early"](snap) + K["stuck"](snap)
    return {"lead": R((f"{fmt(n_open)} open record{'' if n_open == 1 else 's'} need a label right now.", True),
                      " The twin labels suspect records and keeps them; it never deletes. Data problems go to you, not the floor."),
            "kpis": page_kpis(ctx, snap, ["noPlan", "early", "stuck"], "checks"),
            "rows": [{"rule": r[0], "check": r[1], "count": r[2], "countText": fmt(r[2]) if r[2] is not None else None,
                      "frac": min(1, math.sqrt(r[2]) / math.sqrt(2000)) if r[2] is not None else 0, "unit": r[3], "note": r[4]} for r in rows],
            "cards": page_cards(ctx, snap, lambda c: c["rule"].startswith("DQ"), "Data cards")}
