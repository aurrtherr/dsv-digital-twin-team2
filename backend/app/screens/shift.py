"""Screen: Shift overview (view id "shift").
"""
from __future__ import annotations

from ..engine import all_cards, Ctx, prop_status, ROLES, Snap, task_status, todo
from ..fmt import fmt
from .common import (
    hindsight, look_first, other_row, page_kpis, proj_kpis, prop_view, recs, ROLE_INFO, task_view)


# ================================================================ screens
def v_shift(ctx: Ctx, snap: Snap, p: dict) -> dict:
    role, t = ctx.role, snap.t
    cards = all_cards(ctx, snap)
    mine_c = [c for c in cards if c["owner"] == role or c.get("proposer") == role]
    other = [c for c in cards if c not in mine_c]
    live = [x for x in ctx.store.tasks if x["created"] <= t]
    to_do = [x for x in live if todo(ctx, x, role, t)]
    by_me = [x for x in live if x["by"] == role and task_status(ctx, x, t)["st"] != "done"]
    my_props = [q for q in ctx.store.proposals if q["by"] == role and q["created"] <= t]
    wait_props = [q for q in my_props if prop_status(ctx, q, t)["st"] == "waiting"]
    if to_do:
        follow = {"kind": "tasks", "items": [task_view(ctx, x, t) for x in list(reversed(to_do))[:3]]}
    elif by_me:
        follow = {"kind": "tasks", "items": [task_view(ctx, x, t) for x in list(reversed(by_me))[:2]]}
    elif my_props:
        follow = {"kind": "props", "items": [prop_view(ctx, q, t) for q in list(reversed(my_props))[:2]]}
    else:
        follow = {"kind": "empty"}
    info = ROLE_INFO[role]
    return {
        "title": f"Operations overview · {ROLES[role]['name']}", "intro": info["intro"], "lateChip": role in ("out", "plan", "mgr"),
        "start": {"view": info["start"], "label": info["startLab"]},
        "proj": proj_kpis(ctx, snap, ctx.at) if ctx.mode == "next" else None,
        "kpis": page_kpis(ctx, snap) if ctx.mode != "next" else [],
        "hindsight": hindsight(ctx, snap) if ctx.mode == "past" else None,
        "nMine": len(mine_c), "recs": recs(ctx, snap, mine_c), "others": [other_row(c) for c in other],
        "lookFirst": look_first(ctx, snap),
        "follow": {"toDo": len(to_do), "byMe": len(by_me), "waitProps": len(wait_props), "list": follow},
        "foot": f"Replay of DSV’s Daily Inbound and Outbound reports, 17–24 Aug 2026. Inbound times are corrected to the same clock as outbound. {fmt(len(snap.noPlan))} open orders with no planned date are left out of past-due and due-today counts.",
    }
