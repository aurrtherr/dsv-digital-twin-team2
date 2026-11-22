"""Screen: Tasks and activity log (view id "tasks").
"""
from __future__ import annotations

from ..engine import ASSIGN, can_tick_any, Ctx, DATA_CHECK, floor_sup, mine, ROLES, Snap, task_status, todo
from ..fmt import hhmm, when
from .common import prop_view, task_view


def activity(ctx: Ctx, t: int) -> list:
    ev = []
    for x in ctx.store.tasks:
        if x["created"] <= t:
            ev.append([x["created"], x["by"], f"{'Raised' if x['check'] == 'manual' and x['rule'] == 'TASK' else 'Approved'} {x['rule']}: {x['action']}"])
        for a, at in (x.get("parts") or {}).items():
            if at <= t:
                ev.append([at, floor_sup(x) if a == "floor" else a, f"Ticked {ASSIGN[a]['short']} part · {x['rule']}"])
        st = task_status(ctx, x, t)
        if st["st"] == "done" and st.get("at") is not None:
            ev.append([st["at"], "twin", f"Closed by the data · {x['rule']} ({'cleared before anyone acted' if st.get('out') == 'self' else 'resolved after action'})"])
    for q in ctx.store.proposals:
        if q["created"] <= t:
            ev.append([q["created"], q["by"], f"Proposed {q.get('rule') or ''}"])
    for d in ctx.store.dismissed:
        if d["created"] <= t:
            ev.append([d["created"], d["by"], f"Dismissed {d['rule']}: {d['reason']}"])
    for l in ctx.store.log:
        ev.append([l["t"], l["by"], l["msg"]])
    ev.sort(key=lambda e: -e[0])
    who = lambda w: "Twin" if w == "twin" else ROLES[w]["short"] if w in ROLES else w
    return [{"when": when(e[0]), "who": who(e[1]), "what": e[2]} for e in ev]


def v_tasks(ctx: Ctx, snap: Snap, p: dict) -> dict:
    t, role = snap.t, ctx.role
    all_t = list(reversed([x for x in ctx.store.tasks if x["created"] <= t]))
    st = lambda x: task_status(ctx, x, t)["st"]
    is_over = lambda x: x.get("due") is not None and t > x["due"] and st(x) != "done"
    order = lambda xs: [x for x in xs if is_over(x)] + [x for x in xs if not is_over(x) and st(x) != "done"] + [x for x in xs if st(x) == "done"]
    to_do = order([x for x in all_t if todo(ctx, x, role, t)])
    assigned = order([x for x in all_t if mine(x, role) and not todo(ctx, x, role, t)])
    by_me = order([x for x in all_t if x["by"] == role and not todo(ctx, x, role, t)])
    props = list(reversed([q for q in ctx.store.proposals if q["by"] == role and q["created"] <= t]))
    dis = list(reversed([x for x in ctx.store.dismissed if x["created"] <= t]))
    res = [task_status(ctx, x, t) for x in all_t if x["check"] in DATA_CHECK and st(x) == "done"]
    n_act = sum(1 for r in res if r.get("out") == "action")
    mine_t = [x for x in all_t if todo(ctx, x, role, t) or can_tick_any(x, role) or mine(x, role) or x["by"] == role]
    ov = sum(1 for x in mine_t if is_over(x))
    dn = sum(1 for x in mine_t if st(x) == "done")
    tv = lambda xs: [task_view(ctx, x, t) for x in xs]
    return {"title": f"Tasks · {ROLES[role]['name']}", "canAct": ctx.can_act(), "hh": hhmm(t), "nAll": len(all_t),
            "glance": {"n": len(mine_t), "over": ov, "open": len(mine_t) - ov - dn, "done": dn} if all_t else None,
            "closed": {"n": len(res), "act": n_act, "self": len(res) - n_act, "late": sum(1 for r in res if r.get("late"))} if res else None,
            "toDo": tv(to_do), "byMe": tv(by_me), "props": [prop_view(ctx, q, t) for q in props], "showProps": bool(props) or role == "plan",
            "assigned": tv(assigned), "all": tv(order(all_t)), "activity": activity(ctx, t)[:80], "nActivity": len(activity(ctx, t)),
            "dismissed": [{"rule": x["rule"], "head": f"{when(x['created'])} by {ROLES[x['by']]['short']}", "title": x["title"], "reason": x["reason"]} for x in dis]}
