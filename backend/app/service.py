"""Request handling, independent of the web framework (so it can be tested directly).

`frame()` returns everything one screen render needs. The action functions change the
shared state and return a toast message plus an `undo` token the frontend can send back.
"""
from __future__ import annotations

import copy
from typing import Any

from .dataset import T0, T1, get_dataset
from .engine import ASSIGN, ROLES, Ctx, all_cards, rules, same_before, snapshot, task_status, todo
from .fmt import day_label, day_of, fmt, hhmm, when
from .state import CFG_DEF, CFG_META, get_store, new_id
from .views import (TL_NEXT, TL_PAST, VIEWS, asn_detail, lookup, order_detail, timeline, tl_window, whatif)

NAV_GROUPS = [
    ["home", "Home", ["shift", "atrisk", "tasks"]],
    ["floor", "Floor", ["outbound", "inbound", "trace"]],
    ["analyse", "Analyse", ["trends", "whatif"]],
    ["setup", "Data & rules", ["checks", "rules", "settings"]],
]
VIEW_NAMES = [["shift", "Operations overview"], ["atrisk", "Packing priorities"], ["outbound", "Outbound"], ["inbound", "Inbound"],
              ["trace", "Milkrun trace"], ["trends", "Trends"], ["whatif", "What-if"], ["checks", "Data checks"], ["rules", "Rules"],
              ["settings", "Settings"], ["tasks", "Tasks"]]
PROJ_VIEWS = ["shift", "atrisk", "outbound", "inbound", "trends"]


class ActionError(ValueError):
    pass


def _clamp_t(t: int) -> int:
    return max(T0, min(T1, int(t)))


def make_ctx(t: int, at: int | None, role: str) -> Ctx:
    if role not in ROLES:
        role = "out"
    t = _clamp_t(t)
    return Ctx(store=get_store(), t=t, at=None if at is None or int(at) == t else int(at), role=role)


def meta() -> dict:
    return {"T0": T0, "T1": T1, "roles": ROLES, "assign": ASSIGN, "views": VIEW_NAMES, "navGroups": NAV_GROUPS,
            "projViews": PROJ_VIEWS, "cfgMeta": CFG_META, "cfgDef": CFG_DEF,
            "tlPast": {k: v[0] for k, v in TL_PAST.items()}, "tlNext": {k: v[0] for k, v in TL_NEXT.items()},
            "days": [[16 + k, day_label(16 + k).replace(" Aug", "")] for k in range(8)]}


def frame(t: int, at: int | None, role: str, view: str, params: dict) -> dict:
    ctx = make_ctx(t, at, role)
    if view not in VIEWS:
        view = "shift"
    snap = snapshot(ctx.view_t())
    store = ctx.store
    my_open = sum(1 for x in store.tasks if x["created"] <= ctx.t and todo(ctx, x, ctx.role, ctx.t))
    w0, w1 = tl_window(ctx, params.get("tlPast"), params.get("tlNext"))
    return {"t": ctx.t, "at": ctx.at, "mode": ctx.mode, "role": ctx.role, "view": view, "myOpen": my_open, "cfg": store.cfg,
            "version": store.version, "timeline": timeline(ctx, params.get("tlPast"), params.get("tlNext")),
            "noPlan": fmt(len(snap.noPlan)), "data": VIEWS[view](ctx, snap, params)}


# ---------------------------------------------------------------- read endpoints
def get_order(i: int, t: int, at: int | None, role: str) -> dict:
    ctx = make_ctx(t, at, role)
    if not 0 <= i < ctx.D.n_orders:
        raise ActionError("No such order")
    return order_detail(ctx, i)


def get_asn(i: int, t: int, at: int | None, role: str) -> dict:
    ctx = make_ctx(t, at, role)
    if not 0 <= i < len(ctx.D.asns):
        raise ActionError("No such ASN")
    return asn_detail(ctx, i)


def get_lookup(q: str) -> dict:
    return lookup(make_ctx(T0, None, "out"), q)


def get_whatif(wi: int) -> dict:
    return whatif(make_ctx(T0, None, "out"), max(-30, min(60, int(wi))))


# ---------------------------------------------------------------- actions
def _find_card(ctx: Ctx, key: str) -> dict:
    c = next((x for x in all_cards(ctx, snapshot(ctx.t)) if x["key"] == key), None)
    if not c:
        raise ActionError("That card is no longer raised at this time. Refresh and try again.")
    return c


def _need_now(ctx: Ctx) -> None:
    if not ctx.can_act():
        raise ActionError("Actions are only possible in Now, not in Past or Projection.")


def _assign(a: list[str]) -> list[str]:
    a = [x for x in a if x in ASSIGN]
    if not a:
        raise ActionError("Tick at least one role who will do this.")
    return a


def approve(t: int, role: str, key: str, assign: list[str], due: int | None, note: str = "") -> dict:
    ctx = make_ctx(t, None, role)
    _need_now(ctx)
    c = _find_card(ctx, key)
    if c["owner"] != ctx.role:
        raise ActionError(f"Only the {ROLES[c['owner']]['short'].lower()} can approve this card.")
    if c.get("proposer") and not any(p["key"] == key and p["created"] <= ctx.t for p in ctx.store.proposals):
        raise ActionError("This card must be proposed by the planner first.")
    assign = _assign(assign)
    early = c.get("tier") == "prevent"
    with ctx.store.lock:
        dp = [x for x in same_before(ctx, c, ctx.t) if task_status(ctx, x, ctx.t)["st"] == "done"]
        x = {"id": new_id(), "parts": {}, "rule": c["rule"], "key": c["key"], "grp": c.get("grp"),
             "repeatOf": task_status(ctx, dp[-1], ctx.t)["at"] if dp else None, "kind": c["kind"], "check": c["check"], "ids": c["ids"],
             "title": c["title"], "action": c["action"], "assign": assign, "due": int(due) if due not in (None, "") else None,
             "note": (note or "").strip(), "by": ctx.role, "created": ctx.t}
        if early:
            x["early"] = True
            x["trig"] = c["trig"]
        ctx.store.tasks.append(x)
        ctx.store.save()
    n = len(assign)
    return {"toast": f"{c['rule']} {'early action created' if early else 'approved'} · {n} role{'s' if n > 1 else ''} assigned",
            "undo": {"type": "task", "id": x["id"]}}


def dismiss(t: int, role: str, key: str, reason: str, details: str = "") -> dict:
    ctx = make_ctx(t, None, role)
    _need_now(ctx)
    c = _find_card(ctx, key)
    if c["owner"] != ctx.role:
        raise ActionError(f"Only the {ROLES[c['owner']]['short'].lower()} can dismiss this card.")
    if reason == "Other" and not (details or "").strip():
        raise ActionError("Add a few words on why, so the team knows.")
    full = reason + (": " + details.strip() if (details or "").strip() else "")
    d = {"id": new_id(), "rule": c["rule"], "key": c["key"], "ids": c["ids"], "title": c["title"], "reason": full, "by": ctx.role, "created": ctx.t}
    with ctx.store.lock:
        ctx.store.dismissed.append(d)
        ctx.store.save()
    return {"toast": f"{c['rule']} dismissed", "undo": {"type": "dismissed", "id": d["id"]}}


def propose(t: int, role: str, key: str) -> dict:
    ctx = make_ctx(t, None, role)
    _need_now(ctx)
    c = _find_card(ctx, key)
    if c.get("proposer") != ctx.role:
        raise ActionError("Only the planner proposes this card.")
    p = {"id": new_id(), "key": key, "created": ctx.t, "by": ctx.role, "rule": c["rule"], "title": c["title"], "action": c["action"], "owner": c["owner"]}
    with ctx.store.lock:
        ctx.store.proposals.append(p)
        ctx.store.save()
    return {"toast": f"{c['rule']} proposed · waiting for the {ROLES[c['owner']]['short'].lower()}", "undo": {"type": "proposal", "id": p["id"]}}


def tick(t: int, role: str, task_id: str, part: str, done: bool = True) -> dict:
    from .engine import can_tick
    ctx = make_ctx(t, None, role)
    _need_now(ctx)
    x = next((y for y in ctx.store.tasks if y["id"] == task_id), None)
    if not x or part not in x["assign"]:
        raise ActionError("No such task part.")
    if not can_tick(x, part, ctx.role):
        raise ActionError("You cannot tick this part.")
    with ctx.store.lock:
        prev = x["parts"].get(part)
        if done:
            x["parts"][part] = ctx.t
        else:
            x["parts"].pop(part, None)
        ctx.store.save()
    if not done:
        return {"toast": None, "undo": None}
    return {"toast": f"{x['rule']} · {ASSIGN[part]['short']} part marked done", "undo": {"type": "part", "id": task_id, "part": part, "prev": prev}}


def new_task(t: int, role: str, title: str, assign: list[str], due: int | None, note: str = "") -> dict:
    ctx = make_ctx(t, None, role)
    _need_now(ctx)
    title = (title or "").strip()
    if not title:
        raise ActionError("Say what needs doing.")
    assign = _assign(assign)
    x = {"id": new_id(), "parts": {}, "rule": "TASK", "key": "manual|" + new_id(), "kind": None, "check": "manual", "ids": [],
         "title": "Raised by the " + ROLES[ctx.role]["short"].lower(), "action": title[:120], "assign": assign,
         "due": int(due) if due not in (None, "") else None, "note": (note or "").strip(), "by": ctx.role, "created": ctx.t}
    with ctx.store.lock:
        ctx.store.tasks.append(x)
        ctx.store.save()
    return {"toast": f"Task created · {len(assign)} role{'s' if len(assign) > 1 else ''}", "undo": {"type": "task", "id": x["id"]}}


def seed(t: int, role: str) -> dict:
    ctx = make_ctx(t, None, role)
    _need_now(ctx)
    at = min(ctx.t, T1)
    cs = rules(ctx, snapshot(at))
    made = []
    with ctx.store.lock:
        for r in ["OUT-01", "OUT-06", "IN-01", "DQ-03", "MGR-01"]:
            c = next((x for x in cs if x["rule"] == r and not any(y.get("key") == x["key"] for y in ctx.store.tasks)), None)
            if c:
                ctx.store.tasks.append({"id": new_id(), "parts": {}, "rule": c["rule"], "key": c["key"], "grp": c.get("grp"), "kind": c["kind"],
                                        "check": c["check"], "ids": c["ids"], "title": c["title"], "action": c["action"], "assign": c["assign"],
                                        "due": at + 180, "note": "Example task", "by": c["owner"], "created": at})
                made.append(c["rule"])
        if not any(x["rule"] == "IN-01" for x in cs):
            ctx.store.tasks.append({"id": new_id(), "parts": {}, "rule": "TASK", "key": "manual|" + new_id(), "kind": None, "check": "manual", "ids": [],
                                    "title": "Raised by the inbound sup.", "action": "Recount the oldest delivery at the dock with the floor team",
                                    "assign": ["in", "floor"], "due": at + 120, "note": "Example task", "by": "in", "created": at})
            made.append("TASK")
        ctx.store.save()
    return {"toast": f"Added {len(made)} example tasks ({', '.join(made)})", "undo": None}


def save_cfg(t: int, role: str, values: dict) -> dict:
    ctx = make_ctx(t, None, role)
    _need_now(ctx)
    if ctx.role != "mgr":
        raise ActionError("Only the operations manager can change the limits.")
    prev = copy.deepcopy(ctx.store.cfg)
    ch, new = [], dict(ctx.store.cfg)
    for k, lab, unit, _, mn, mx, _st in CFG_META:
        try:
            v = float(values.get(k, ctx.store.cfg[k]))
        except (TypeError, ValueError):
            raise ActionError(f"{lab}: enter {mn}–{mx}")
        v = int(v) if v.is_integer() else v
        if not (mn <= v <= mx):
            raise ActionError(f"{lab}: enter {mn}–{mx}")
        if v != ctx.store.cfg[k]:
            ch.append(f"{lab} {ctx.store.cfg[k]} → {v}")
            new[k] = v
    if not ch:
        return {"toast": "No changes", "undo": None}
    with ctx.store.lock:
        ctx.store.s["cfg"] = new
        for m in ch:
            ctx.store.log.append({"t": ctx.t, "by": ctx.role, "msg": "Changed limit: " + m})
        ctx.store.save()
    return {"toast": f"{len(ch)} limit{'s' if len(ch) > 1 else ''} saved", "undo": {"type": "cfg", "prev": prev, "nlog": len(ch)}}


def reset_cfg(t: int, role: str) -> dict:
    ctx = make_ctx(t, None, role)
    _need_now(ctx)
    if ctx.role != "mgr":
        raise ActionError("Only the operations manager can change the limits.")
    prev = copy.deepcopy(ctx.store.cfg)
    with ctx.store.lock:
        ctx.store.s["cfg"] = dict(CFG_DEF)
        ctx.store.log.append({"t": ctx.t, "by": ctx.role, "msg": "Reset all limits to defaults"})
        ctx.store.save()
    return {"toast": "Limits back to defaults", "undo": {"type": "cfg", "prev": prev, "nlog": 1}}


def undo(token: dict) -> dict:
    store = get_store()
    ty = token.get("type")
    with store.lock:
        if ty in ("task", "dismissed", "proposal"):
            lst = {"task": store.tasks, "dismissed": store.dismissed, "proposal": store.proposals}[ty]
            for k, x in enumerate(lst):
                if x.get("id") == token.get("id"):
                    del lst[k]
                    break
        elif ty == "part":
            x = next((y for y in store.tasks if y["id"] == token.get("id")), None)
            if x:
                if token.get("prev") is None:
                    x["parts"].pop(token["part"], None)
                else:
                    x["parts"][token["part"]] = token["prev"]
        elif ty == "cfg":
            store.s["cfg"] = {**CFG_DEF, **(token.get("prev") or {})}
            n = int(token.get("nlog") or 0)
            if n:
                del store.log[-n:]
        else:
            raise ActionError("Nothing to undo.")
        store.save()
    return {"toast": "Undone", "undo": None}


def reset_demo() -> dict:
    get_store().reset()
    return {"toast": "Demo reset", "undo": None}
