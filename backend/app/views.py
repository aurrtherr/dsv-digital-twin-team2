"""View models: one function per screen, returning JSON-ready data for the React frontend.

The frontend only lays things out. Business logic (rules, statuses, projections, wording
of recommendations and comparisons) stays here, ported from the prototype's V.* functions.

Rich text: short sentences with bold parts are sent as a list of [text, bold] segments.
"""
from __future__ import annotations

import math
from typing import Any, Callable

import numpy as np

from .dataset import T0, T1
from .engine import (ASSIGN, DATA_CHECK, DQ_WAIT, ROLES, TIER_ORDER, TIERS, WEEK, Ctx, Snap, all_cards, auto_closed,
                     can_tick, can_tick_any, floor_sup, group_by, kpi_fns, last_weekday, mine, next_card_for, on_time,
                     outcome, part_done, project, prop_status, same_before, snapshot, task_status, todo, work)
from .fmt import (day_label, day_n, day_of, dkey, fmt, hhmm, hrs, in_min, js_num, js_round, pct, to_fixed, when)

Rich = list  # [[text, bold], ...]


def R(*parts) -> Rich:
    """R('plain ', ('bold', True), ' more') -> rich segments."""
    return [[p, False] if isinstance(p, str) else [p[0], True] for p in parts]


def num(x):
    return int(x) if isinstance(x, float) and x.is_integer() else x


def avg(xs):
    xs = list(xs)
    return sum(xs) / (len(xs) or 1)


SEV_LAB = lambda c: ["late", "Below target"] if c["rule"].startswith("MGR") else ["late", "Overdue"] if c["sev"] == "late" else ["due", "Due soon"] if c["sev"] == "due" else ["dq", "Data check"]
STAT = {"ok": ["✓", "On track"], "watch": ["●", "Watch"], "act": ["▲", "Act now"], "info": ["", "For context"]}
ROLE_INFO = {
    "out": {"intro": "Get today’s orders out the door. Start with the biggest overdue groups below.", "start": "outbound", "startLab": "Open Outbound"},
    "plan": {"intro": "Plan today’s packing and pickups. Send your suggestions to the outbound supervisor to approve.", "start": "atrisk", "startLab": "Open Packing priorities"},
    "in": {"intro": "Keep deliveries moving from the dock to the shelves. Start with the ones waiting longest.", "start": "inbound", "startLab": "Open Inbound"},
    "mgr": {"intro": "See how the week is going against target, and decide where the team needs help.", "start": "trends", "startLab": "Open Trends"},
    "dq": {"intro": "Check records that look wrong, so everyone works from data they can trust.", "start": "checks", "startLab": "Open Data checks"},
}


# ================================================================ cards, tasks, proposals
def card_view(ctx: Ctx, c: dict, snap: Snap) -> dict:
    role = ctx.role
    is_owner, is_prop, early = role == c["owner"], c.get("proposer") == role, c.get("tier") == "prevent"
    prop = next((p for p in ctx.store.proposals if p["key"] == c["key"] and p["created"] <= snap.t), None)
    if ctx.mode == "past":
        ctl = {"kind": "outcome", **outcome(ctx, c, snap.t)}
    elif ctx.mode == "next":
        ctl = {"kind": "next"}
    elif c.get("proposer") and not prop:
        ctl = {"kind": "propose"} if is_prop else {"kind": "waitPropose", "who": ROLES[c["proposer"]]["short"].lower()}
    elif is_owner:
        ctl = {"kind": "owner", "early": early}
    else:
        ctl = {"kind": "viewOnly", "who": ROLES[c["owner"]]["short"].lower()}
    prev = same_before(ctx, c, snap.t)
    open_prev = [x for x in prev if task_status(ctx, x, snap.t)["st"] != "done"]
    done_prev = [x for x in prev if task_status(ctx, x, snap.t)["st"] == "done"]
    notes = []
    if open_prev:
        notes.append(["wait", f"Same group already has an open task (since {when(open_prev[-1]['created'])})"])
    elif done_prev:
        notes.append(["info", f"Repeat · cleared before at {when(task_status(ctx, done_prev[-1], snap.t)['at'])}"])
    if prop:
        notes.append(["info", f"Proposed by planner {hhmm(prop['created'])}"])
    elif c.get("proposer"):
        notes.append(["", "Planner proposes · supervisor approves"])
    tier_tag = None
    if early:
        trig = c["trig"]
        tier_tag = ["wait", f"Prevent · fires {'at midnight' if trig >= (snap.day + 1) * 1440 else 'at ' + hhmm(trig)} (in {in_min(num(max(0, trig - snap.t)))})"]
    elif c.get("tier") == "review":
        tier_tag = ["", "Review · pattern"]
    sev = SEV_LAB(c)
    return {"key": c["key"], "rule": c["rule"], "sev": c["sev"], "sevCls": sev[0], "sevLab": sev[1], "tier": c.get("tier"),
            "tierTag": tier_tag, "ownerName": ROLES[c["owner"]]["name"], "notes": notes, "title": c["title"], "why": c["why"],
            "action": c["action"], "doer": c["doer"], "done": c["done"], "mine": is_owner or is_prop, "controls": ctl,
            "assign": c["assign"], "trig": num(c.get("trig")) if c.get("trig") is not None else None, "nIds": len(c["ids"]),
            "early": early}


def other_row(c: dict) -> dict:
    s = SEV_LAB(c)
    return {"rule": c["rule"], "sevCls": s[0], "sevLab": s[1], "title": c["title"], "ownerShort": ROLES[c["owner"]]["short"],
            "ownerName": ROLES[c["owner"]]["name"]}


def task_view(ctx: Ctx, x: dict, t: int) -> dict:
    s = task_status(ctx, x, t)
    tag = ("info" if s.get("out") == "self" else "ok") if s["st"] == "done" else "wait" if s["st"] == "wait" else ""
    ac = auto_closed(ctx, x, t)
    extra = []
    if s.get("late"):
        extra.append(["late", "After the due time"])
    if x.get("early"):
        av = " · avoided" if s["st"] == "done" and s.get("at") is not None and s["at"] <= x["trig"] else ""
        extra.append(["wait", f"Early action · rule would fire {when(x['trig'])}{av}"])
    if x.get("repeatOf") is not None:
        extra.append(["info", f"Repeat · same issue cleared {when(x['repeatOf'])}"])
    over = x.get("due") is not None and s["st"] not in ("done", "future") and t > x["due"]
    due_tag = None
    if x.get("due") is not None and s["st"] != "done":
        due_tag = ["late", f"Overdue · was due {when(x['due'])}"] if over else ["", f"Due {when(x['due'])}"]
    prog = None
    if s["st"] != "future":
        if x["check"] == "manual":
            prog = {"kind": "parts", "n": s["n"], "tot": s["tot"], "text": f"{s['n']} of {s['tot']} parts ticked"}
        elif x["check"] not in ("label", "review"):
            prog = {"kind": "data", "n": s["n"], "tot": s["tot"], "text": f"{fmt(s['n'])} of {fmt(s['tot'])} resolved in data"}
    parts = []
    for a in x["assign"]:
        d = part_done(x, a, t)
        can = ctx.can_act() and can_tick(x, a, ctx.role) and t >= x["created"]
        if not d and ac:
            parts.append({"a": a, "short": ASSIGN[a]["short"], "state": "nn"})
            continue
        parts.append({"a": a, "short": ASSIGN[a]["short"], "state": "ok" if d else "pending", "can": can,
                      "suffix": (" (you)" if a == ctx.role else " (via you)") if can else "",
                      "doneText": "done " + when(x["parts"][a]) if d else "pending",
                      "btn": "Mark my part done" if a == ctx.role else "Mark floor team part done"})
    return {"id": x["id"], "rule": x["rule"], "head": f"{'raised' if x['check'] == 'manual' else 'approved'} {when(x['created'])} by {ROLES[x['by']]['short']}",
            "statusTag": [tag, s["label"]], "dueTag": due_tag, "extra": extra, "over": over, "action": x["action"],
            "sub": x["title"] + (f" · “{x['note']}”" if x.get("note") else ""), "progress": prog, "parts": parts}


def prop_view(ctx: Ctx, p: dict, t: int) -> dict:
    s = prop_status(ctx, p, t)
    owner = ROLES[p.get("owner") or "out"]["short"].lower()
    steps = [["okk", f"Proposed {hhmm(p['created'])}"]]
    if s["st"] == "waiting":
        steps.append(["on", "Waiting for the " + owner])
    elif s["st"] == "approved":
        steps.append(["okk", "Approved by the " + owner])
        ts = task_status(ctx, s["task"], t)
        steps.append(["okk" if ts["st"] == "done" else "on", ts["label"]])
    else:
        steps.append(["bad", "Dismissed by the " + owner])
    return {"rule": p.get("rule") or "", "action": p.get("action") or "", "title": p.get("title") or "", "steps": steps,
            "reason": s["d"]["reason"] if s["st"] == "dismissed" else None}


# ================================================================ KPIs
def kpi_status(ctx: Ctx, k: dict, v: float) -> str:
    if k.get("mode") == "target":
        return "ok" if v >= k["target"] else "watch" if v >= k["target"] - 10 else "act"
    if k.get("mode") == "review":
        return "watch" if v > 0 else "ok"
    if k.get("mode") == "info" or k.get("base") is None:
        return "info"
    if k.get("dir") == "up":
        return "ok" if v >= 0.98 * k["base"] else "watch" if v >= 0.8 * k["base"] else "act"
    return "ok" if v <= 1.02 * k["base"] else "watch" if v <= ctx.cfg["load"] * k["base"] else "act"


def day_chart(ctx: Ctx, k: dict, snap: Snap, st: str) -> dict:
    K = kpi_fns(ctx)
    t, day = snap.t, snap.day
    t0 = min(day * 1440 + 360, t - 180)
    t1 = max(t + 60, min((day + 1) * 1440, max(t, day * 1440 + 20 * 60)))
    fn, others = K[k["key"]], [d for d in WEEK if d != day]
    today, base, after = [], [], []
    u = math.ceil(t0 / 60) * 60
    while u <= t1:
        off = u - day * 1440
        if others:
            base.append([u, avg(fn(snapshot(d * 1440 + off)) for d in others)])
        if u <= t:
            today.append([u, fn(snapshot(u))])
        u += 60
    today.append([t, k["val"]])
    if ctx.mode == "past":
        u = math.ceil((t + 1) / 60) * 60
        while u <= min(t1, ctx.t):
            after.append([u, fn(snapshot(u))])
            u += 60
    aria = f"{k['lab']} through the day: now {fmt(js_round(k['val']))}" + (f", usual at this hour {fmt(js_round(k['base']))}" if base else "")
    t1_lab = hhmm(t1 - 1 if t1 % 1440 == 0 else t1).replace("23:59", "24:00")
    return {"type": "day", "t0": t0, "t1": t1, "t": t, "val": k["val"], "today": today, "base": base, "after": after, "st": st,
            "aria": aria, "t0Lab": hhmm(t0), "nowLab": hhmm(t) if ctx.mode == "past" else "Now", "t1Lab": t1_lab}


def week_bars(ctx: Ctx, k: dict) -> dict:
    D = ctx.D
    if k["kind"] == "ontime":
        days = [d for d in WEEK if D.late_by_day.get(dkey(d)) and D.late_by_day[dkey(d)][0] >= 100 and d <= k["yd"]]
        vals = [on_time(d) for d in days]
        ref = k["target"]
        mx = 100
    else:
        days = [d for d in WEEK if d <= k["yd"]]
        vals = [k["src"](dkey(d)) for d in days]
        ref = k.get("base")
        mx = max(vals + [ref or 0]) * 1.12
    good = lambda v: v >= k["target"] if k["kind"] == "ontime" else (v <= ctx.cfg["load"] * k["base"] if k.get("dir") == "down" else True)
    lab = lambda v: to_fixed(v, 0) + "%" if k.get("pct") else fmt(v)
    bars = [{"label": day_n(d), "valText": lab(v), "frac": v / mx if mx else 0, "good": good(v), "current": d == k["yd"]} for d, v in zip(days, vals)]
    return {"type": "week", "bars": bars, "refFrac": (ref / mx) if (ref is not None and mx) else None, "info": k.get("dir") == "info",
            "aria": f"{k['lab']} by day: " + ", ".join(f"{b['label']} {b['valText']}" for b in bars),
            "refLab": f"Target {js_num(k['target'])}%" if k["kind"] == "ontime" else "Week average",
            "badLab": "Below target" if k["kind"] == "ontime" else "Over the limit"}


def kpi_card(ctx: Ctx, k: dict, snap: Snap, big: bool = True) -> dict:
    st = kpi_status(ctx, k, k["val"])
    ic, word = STAT[st]
    if k.get("mode") == "review" and st == "watch":
        word = "To review"
    f = (lambda v: to_fixed(v, 1) + "%") if k.get("pct") else (lambda v: fmt(js_round(v)))
    cmp = ""
    if k.get("mode") == "target":
        d = k["val"] - k["target"]
        cmp = f"{'▲' if d >= 0 else '▼'} {to_fixed(abs(d), 1)} pts vs {js_num(k['target'])}% target"
    elif k.get("base") is not None and k.get("mode") not in ("review", "info"):
        d = 100 * (k["val"] - k["base"]) / k["base"] if k["base"] else 0
        cmp = (f"Same as {k['baseLab']} ({f(k['base'])})" if abs(d) < 1
               else f"{'▲' if d > 0 else '▼'} {to_fixed(abs(d), 0)}% vs {k['baseLab']} ({f(k['base'])})")
    elif k.get("mode") == "review":
        cmp = "Label each record; never delete" if k["val"] else "Nothing to review"
    if k.get("mode") == "info" and k.get("base") is not None:
        d = 100 * (k["val"] - k["base"]) / k["base"] if k["base"] else 0
        cmp = f"{'Same as' if abs(d) < 1 else ('▲ ' if d > 0 else '▼ ') + to_fixed(abs(d), 0) + '% vs'} {k['baseLab']} ({f(k['base'])})"
    chart = None
    if big:
        chart = day_chart(ctx, k, snap, st) if k.get("key") else week_bars(ctx, k)
    return {"lab": k["lab"], "valText": f(k["val"]), "st": st, "icon": ic, "word": word, "cmp": cmp, "def": k["def"],
            "go": k.get("go"), "goLab": k.get("goLab"), "chart": chart}


def role_kpis(ctx: Ctx, snap: Snap, pick: list[str] | None = None, view: str | None = None) -> list[dict]:
    D, cfg = ctx.D, ctx.cfg
    K = kpi_fns(ctx)
    t, hh = snap.t, hhmm(snap.t)
    wk_idx = WEEK.index(snap.day) if snap.day in WEEK else -1
    tl = [day_n(d) for d in WEEK]

    def hour_kpi(key, **o):
        tr = [K[key](snapshot(d * 1440 + (t % 1440))) for d in WEEK]
        return {"key": key, "val": K[key](snap), "base": avg(tr), "baseLab": f"week avg at {hh}", "trend": tr, "cur": wk_idx, "tlabels": tl, **o}

    y = last_weekday(snap.day)
    ys = [d for d in WEEK if D.late_by_day.get(dkey(d)) and D.late_by_day[dkey(d)][0] >= 100]
    on_k = None if y is None else {"kind": "ontime", "yd": y, "lab": f"On time, orders planned {day_n(y)}", "val": on_time(y), "pct": True,
                                   "mode": "target", "target": cfg["ontime"], "def": f"Share handed over on their planned day. Target: {js_num(cfg['ontime'])}%.",
                                   "go": "trends", "goLab": "See trend"}

    def lines(src, lab, defn, dirn):
        if y is None:
            return None
        tr = [src(dkey(d)) for d in WEEK]
        return {"kind": "lines", "src": src, "yd": y, "lab": lab, "val": src(dkey(y)), "base": avg(tr), "baseLab": "week avg", "dir": dirn,
                "mode": "info" if dirn == "info" else None, "def": defn}

    wk = lambda k: D.in_lines_day.get(k, 0) + D.out_lines_day.get(k, 0)
    yl = day_n(y) if y is not None else ""
    past_k = hour_kpi("past", lab="Open orders past planned day", **{"def": "Not yet handed over, and the planned day has passed."}, go="outbound", goLab="See orders")
    np_k = hour_kpi("notPacked", lab="Due today, not fully packed", **{"def": "Planned for today with cartons still to pack."}, go="outbound", goLab="See orders")
    top_g = lambda: hour_kpi("topGroup", lab="Largest overdue group", **{"def": "Most past-due orders for one country and forwarder. One pickup clears it."}, go="outbound", goLab="See groups")
    due_k = lambda go: hour_kpi("due", lab="Orders due today", mode="info", **{"def": "Planned for today and not yet handed over."}, go=go, goLab="See packing priorities" if go == "atrisk" else "See orders")
    packed_k = lambda: hour_kpi("packedDue", lab="Due today already packed", pct=True, dir="up", **{"def": "Share of today’s orders ready for pickup."})
    dock_k = lambda: hour_kpi("dock", lab="Deliveries waiting at the dock", **{"def": "Docked but not yet received."}, go="inbound", goLab="See deliveries")
    over_k = lambda: hour_kpi("dockOver", lab="Waiting longer than usual", **{"def": "Over the usual dock-to-receipt time for their type (90% finish within it)."}, go="inbound", goLab="See deliveries")
    lines_in = lambda: lines(lambda k: D.in_lines_day.get(k, 0), f"Lines received {yl}", "Inbound lines received that day.", "info")
    stuck_k = lambda d="Almost certainly a data issue, not a real wait. Sent to the data owner.", goLab="See data checks": hour_kpi("stuck", lab="At the dock over 5 days", mode="review", **{"def": d}, go="checks", goLab=goLab)
    fwd_k = lambda lab, d: hour_kpi("fwd20", lab=lab, **{"def": d}, go="outbound", goLab="See forwarders")
    work_k = lambda: lines(wk, f"Workload {yl} (lines)", f"Inbound + outbound lines. Over {js_num(cfg['load'])}× the week average means plan extra people.", "down")
    noplan_k = lambda: hour_kpi("noPlan", lab="Open orders with no planned date", mode="review", **{"def": "Left out of late counts until we know how they are planned."}, go="checks", goLab="Review")
    early_k = lambda: hour_kpi("early", lab="Planned before they were created", mode="review", **{"def": "They look overdue the moment they appear. Label them; don’t delete."}, go="checks", goLab="Review")

    if pick:
        lib = {"past": lambda: past_k, "notPacked": lambda: np_k, "onTime": lambda: on_k, "topGroup": top_g, "due": lambda: due_k("atrisk"),
               "packedDue": packed_k, "dock": dock_k, "dockOver": over_k, "linesIn": lines_in, "stuck": stuck_k,
               "fwd20": lambda: fwd_k(f"Forwarders with {js_num(cfg['fwd'])}+ overdue", f"Forwarders holding {js_num(cfg['fwd'])} or more overdue orders. Worth a call."),
               "work": work_k, "noPlan": noplan_k, "early": early_k}
        ks = [k for k in (lib[n]() for n in pick) if k]
        out = []
        for k in ks:
            k = dict(k)
            if k.get("go") == view:
                k["go"] = None
            out.append(k)
        return out
    sets = {
        "out": [past_k, np_k, top_g(), on_k],
        "plan": [due_k("outbound"), np_k, packed_k(), past_k],
        "in": [dock_k(), over_k(), lines_in(), stuck_k()],
        "mgr": [on_k, past_k, fwd_k("Forwarders with 20+ overdue", "Forwarders holding 20 or more overdue orders. Worth a call."), work_k()],
        "dq": [noplan_k(), early_k(), stuck_k("Docked weeks ago with no receipt. Confirm or close the record.", "Review")],
    }
    return [k for k in sets.get(ctx.role, sets["out"]) if k]


def page_kpis(ctx: Ctx, snap: Snap, pick=None, view=None) -> list[dict]:
    return [kpi_card(ctx, k, snap) for k in role_kpis(ctx, snap, pick, view)]


def page_cards(ctx: Ctx, snap: Snap, test: Callable[[dict], bool], title: str) -> dict:
    cs = [c for c in all_cards(ctx, snap) if test(c)]
    mine_c = [c for c in cs if c["owner"] == ctx.role or c.get("proposer") == ctx.role]
    rest = [c for c in cs if c not in mine_c]
    return {"title": title, "n": len(cs), "sub": "Cards raised by the rules for this screen." if cs else f"No rule has fired for this screen at {hhmm(snap.t)}.",
            "mine": [card_view(ctx, c, snap) for c in mine_c], "rest": [other_row(c) for c in rest]}


# ================================================================ projections
def rng(e: dict) -> dict:
    if e["mid"] is not None:
        return {"main": fmt(e["mid"]), "sub": f"({fmt(e['lo'])}–{fmt(e['hi'])})"}
    return {"main": f"up to {fmt(e['worst'])}", "sub": None}


def proj_series(ctx: Ctx, snap: Snap, T: int, key: str) -> dict:
    now = snap.t
    t0 = max(snap.day * 1440 + 360, now - 720)
    stp = max(60, math.ceil((T - now) / 24 / 60) * 60)
    val = (lambda s: len(s.past)) if key == "past" else (lambda s: len(s.due)) if key == "due" else (lambda s: len(s.notPacked))
    hist, proj = [], []
    t = math.ceil(t0 / 60) * 60
    while t < now:
        hist.append([t, val(snapshot(t))])
        t += 60
    hist.append([now, val(snap)])
    if key != "np" and T > now:
        ts = list(range(now + stp, T, stp)) + [T]
        for u in ts:
            e = project(ctx, snap, u)[key]
            if not e:
                break
            proj.append([u, e["mid"] if e["mid"] is not None else e["worst"], e["lo"], e["hi"]])
    t1 = max(snap.day * 1440 + ctx.cfg["cut"] * 60 + 60, now + 60) if key == "np" else max(T, now + 60)
    return {"type": "proj", "hist": hist, "proj": proj, "t0": hist[0][0], "t1": t1, "now": now}


def _at_label(snap: Snap, T: int) -> str:
    return "midnight" if T == (snap.day + 1) * 1440 else hhmm(T) if day_of(T) == snap.day else when(T)


def proj_kpis(ctx: Ctx, snap: Snap, T: int) -> dict:
    p, role, cfg = project(ctx, snap, T), ctx.role, ctx.cfg
    at = _at_label(snap, T)
    cut_t = snap.day * 1440 + cfg["cut"] * 60

    def card(lab, val, foot, st="watch", chart=None, marks=None):
        if chart is not None and marks:
            chart["marks"] = [[m[0], m[1]] for m in marks]
        return {"lab": lab, "val": val, "foot": foot, "st": st, "chart": chart}

    def past_c():
        e = p["past"]
        foot = (f"Likely value; the range comes from this week’s pace on {e['days']} earlier day{'s' if e['days'] > 1 else ''}. {fmt(e['worst'])} if nothing ships."
                if e["mid"] is not None else "If nothing ships. No earlier days yet to judge the pace.")
        st = "act" if e["mid"] is not None and e["mid"] > len(snap.past) else "watch"
        return card(f"Past planned day at {at}", rng(e), foot, st, proj_series(ctx, snap, T, "past"), [[(snap.day + 1) * 1440, "Midnight"]])

    def due_c():
        if not p["due"]:
            return None
        return card(f"Due today, still open at {at}", rng(p["due"]), f"{fmt(p['due']['worst'])} are open now. Anything still open at midnight becomes late.",
                    "watch", proj_series(ctx, snap, T, "due"), [[cut_t, f"Cut-off {js_num(cfg['cut'])}:00"]])

    def ot_c():
        o = p["ontime"]
        if not o:
            return None
        val = ({"main": f"{to_fixed(o['mid'], 0)}%", "sub": f"({to_fixed(o['mn'], 0)}–{to_fixed(o['mx'], 0)}%)"} if o["mid"] is not None
               else {"main": f"{to_fixed(o['lo'], 0)}–100%", "sub": None})
        done = 100 * o["shipped"] / o["N"]
        chart = {"type": "ontime", "done": done, "mid": o["mid"], "mn": o["mn"], "mx": o["mx"], "target": cfg["ontime"],
                 "doneText": to_fixed(done, 0), "midText": to_fixed(o["mid"], 0) if o["mid"] is not None else "?"}
        return card("On time today, by midnight", val,
                    f"Target {js_num(cfg['ontime'])}%. {fmt(o['shipped'])} of {fmt(o['N'])} orders planned today have left so far; {fmt(o['D'])} are still open.",
                    "act" if o["mid"] is not None and o["mid"] < cfg["ontime"] else "ok", chart)

    def np_c():
        sr = proj_series(ctx, snap, T, "np")
        first = sr["hist"][0][1]
        n = p["notPacked"]
        foot = (f"Must be packed before the {js_num(cfg['cut'])}:00 cut-off" + (f" (in {in_min(cut_t - snap.t)})" if snap.t < cut_t else "") + ". "
                + (f"{fmt(first - n)} packed since {hhmm(sr['t0'])}." if first > n else ""))
        return card("Not packed, due today", {"main": fmt(n), "sub": None}, foot, "watch" if n else "ok", sr, [[cut_t, f"Cut-off {js_num(cfg['cut'])}:00"]])

    def dock_c():
        D = ctx.D
        W = max(60, T - snap.t)
        pts = [{"asn": D.asns[x["i"]][0], "atHH": hhmm(x["at"]), "left": 100 * (x["at"] - snap.t) / W, "type": D.types[D.a_type[x["i"]]]} for x in p["dockPass"]]
        n = len(pts)
        chart = {"type": "dock", "points": pts, "nowLab": hhmm(snap.t), "endLab": when(T)}
        return card(f"Deliveries passing usual time by {at}", {"main": fmt(n), "sub": None},
                    "Each dot is a delivery now at the dock, at the moment it goes over its usual time." if n else "None of the deliveries now at the dock goes over before then.",
                    "watch" if n else "ok", chart)

    sets = {"out": [past_c, due_c, ot_c], "plan": [due_c if p["due"] else past_c, np_c, ot_c], "in": [dock_c, past_c],
            "mgr": [ot_c, past_c, due_c], "dq": []}
    cards = [c for c in (f() for f in sets.get(role, [])) if c]
    known = hhmm(snap.t) if day_of(T) == snap.day else when(snap.t)
    return {"cards": cards, "legend": f"Projections use only what is known at {known}: planned dates, what is open and packed, and how fast orders left at this hour on earlier days this week. The range comes from how different the earlier days were; see how accurate this has been on Trends."}


def proj_panel(ctx: Ctx, snap: Snap, page: str):
    if ctx.mode != "next":
        return None
    D = ctx.D
    p = project(ctx, snap, ctx.at)
    at = _at_label(snap, ctx.at)
    if page == "inbound":
        rows = [{"asn": D.asns[x["i"]][0], "type": D.types[D.a_type[x["i"]]], "docked": when(int(D.a_dock[x["i"]])), "passes": hhmm(x["at"])} for x in p["dockPass"]]
        return {"at": at, "kind": "inbound", "rows": rows}
    chips = [R(f"Past planned day at {at}: ", (_rng_text(p["past"]), True))]
    if p["due"]:
        chips.append(R("Due today still open: ", (_rng_text(p["due"]), True)))
    chips.append(R("Not packed now: ", (fmt(p["notPacked"]), True)))
    return {"at": at, "kind": "orders", "chips": chips, "lanes": p["lanes"]}


def _rng_text(e):
    r = rng(e)
    return r["main"] + (" " + r["sub"] if r["sub"] else "")


def hindsight(ctx: Ctx, snap: Snap) -> dict:
    cs = [c for c in all_cards(ctx, snap) if c["owner"] == ctx.role or c.get("proposer") == ctx.role]
    os_ = [outcome(ctx, c, snap.t)["k"] for c in cs]
    n = lambda k: sum(1 for x in os_ if x == k)
    gone = sum(1 for i in snap.past if ctx.D.o_hand[i] <= ctx.t)
    return {"sub": f"Looking back from {when(ctx.t)} at the {len(cs)} card{'' if len(cs) == 1 else 's'} you had at {when(snap.t)}.",
            "approved": n("approved"), "dismissed": n("dismissed"), "self": n("self"), "open": n("open"),
            "pastThen": fmt(len(snap.past)), "gone": fmt(gone)}


def accuracy(ctx: Ctx) -> dict:
    rows = []
    for d in range(16, 23):
        mid, made = (d + 1) * 1440, d * 1440 + 540
        if mid > ctx.t:
            break
        e = project(ctx, snapshot(made), mid)["past"]
        act = len(snapshot(mid).past)
        rows.append({"day": day_n(d), "mid": e["mid"], "lo": e["lo"], "hi": e["hi"], "act": act, "ok": e["lo"] <= act <= e["hi"],
                     "err": act - e["mid"] if e["mid"] is not None else None})
    early = [x for x in ctx.store.tasks if x.get("early") and x["created"] <= ctx.t]
    avoided = sum(1 for x in early if (s := task_status(ctx, x, ctx.t))["st"] == "done" and s.get("at") is not None and s["at"] <= x["trig"])
    scored = [r for r in rows if r["mid"] is not None]
    hits = sum(1 for r in scored if r["ok"])
    return {"rows": [{**r, "midText": fmt(r["mid"]) if r["mid"] is not None else "–", "rangeText": f"{fmt(r['lo'])}–{fmt(r['hi'])}",
                      "actText": fmt(r["act"]), "errText": fmt(abs(r["err"])) if r["err"] is not None else None} for r in rows],
            "hits": hits, "scored": len(scored), "early": len(early), "avoided": avoided, "lesson": bool(scored) and hits * 2 < len(scored)}


# ================================================================ shared pieces
def recs(ctx: Ctx, snap: Snap, mine_c: list[dict]) -> dict:
    t = snap.t
    if ctx.mode == "next":
        cs = [c for c in mine_c if c.get("tier") == "prevent" and c["trig"] <= ctx.at]
        return {"kind": "next", "atWhen": when(ctx.at), "atHH": hhmm(ctx.at), "cards": [card_view(ctx, c, snap) for c in cs]}
    if not mine_c:
        nx = next_card_for(ctx, ctx.role, t) if ctx.can_act() else None
        return {"kind": "empty", "hh": hhmm(t),
                "next": {"rule": nx["c"]["rule"], "title": nx["c"]["title"], "t": nx["t"], "when": when(nx["t"])} if nx else None}
    tiers = []
    for k in TIER_ORDER.get(ctx.role, TIER_ORDER["out"]):
        cs = sorted([c for c in mine_c if c.get("tier") == k], key=lambda c: c.get("trig") or 0)
        if not cs:
            continue
        tiers.append({"k": k, "name": TIERS[k][0], "sub": TIERS[k][1], "n": len(cs), "open": k != "review" or ctx.role == "mgr",
                      "shown": [card_view(ctx, c, snap) for c in cs[:3]], "rest": [card_view(ctx, c, snap) for c in cs[3:]]})
    return {"kind": "tiers", "tiers": tiers}


def hbars(rows, mx=None, cls=""):
    mx = mx if mx is not None else max([r[1] for r in rows] + [1])
    return {"kind": "hbars", "rows": [{"nm": r[0], "n": r[1], "nText": fmt(r[1]), "frac": (r[1] / mx) if mx else 0} for r in rows], "cls": cls}


def look_first(ctx: Ctx, snap: Snap) -> dict:
    D, r, t = ctx.D, ctx.role, snap.t
    if r == "plan":
        g = [[k, len(v)] for k, v in group_by(snap.notPacked, D.lane)[:8]]
        return {"h": "Where to look first", "sub": "Due today and not fully packed, by country · forwarder. Pack the top lanes first.",
                "body": hbars(g, g[0][1], "acc") if g else {"kind": "empty", "text": "Everything due today is packed."}}
    if r == "in":
        rows = sorted([[f"{D.asns[i][0]} · {D.types[D.a_type[i]]}", js_round((t - D.a_dock[i]) / 60), ctx.usual_min(i) / 60] for i in snap.dock],
                      key=lambda x: -x[1])[:8]
        body = ({"kind": "dock", "rows": [{"nm": nm, "h": h, "hText": fmt(h), "over": h > u, "frac": min(1, h / max(u * 1.5, 1))} for nm, h, u in rows]}
                if rows else {"kind": "empty", "text": "No deliveries waiting at the dock."})
        return {"h": "Where to look first", "sub": "Deliveries waiting at the dock, longest wait first.", "body": body}
    if r == "mgr":
        rows = []
        for d in WEEK:
            v = D.late_by_day.get(dkey(d))
            if v and v[0] >= 100:
                rows.append({"nm": day_n(d), "v": 100 * v[1] / v[0], "sub": "n=" + fmt(v[0])})
        return {"h": "Where to look first", "sub": "Late rate by planned day (weekdays). On-time target 70% = late at most 30%; red bars miss it.",
                "body": {"kind": "pct", "rows": [{**x, "vText": to_fixed(x["v"], 0) + "%", "frac": min(100, x["v"]) / 100, "red": x["v"] >= 30} for x in rows]}}
    if r == "dq":
        K = kpi_fns(ctx)
        g = sorted([["DQ-02 · no planned date", K["noPlan"](snap)], ["DQ-01 · planned before created", K["early"](snap)],
                    ["DQ-03 · docked over 5 days", K["stuck"](snap)]], key=lambda x: -x[1])
        return {"h": "Where to look first", "sub": "Open suspect records by data check, at this hour.", "body": hbars(g, max(1, g[0][1]), "acc")}
    g = [[k, len(v)] for k, v in group_by(snap.past, D.lane)[:8]]
    return {"h": "Where to look first", "sub": "Open orders past their planned day, by country · forwarder",
            "body": hbars(g, g[0][1]) if g else {"kind": "empty", "text": "No past-due orders at this time."}}


def order_state(ctx: Ctx, i: int, t: int) -> str:
    D = ctx.D
    if D.o_created[i] > t:
        return "Not created yet"
    if D.o_hand[i] <= t:
        return "Handed over"
    if not D.o_has_plan[i]:
        return "No planned date"
    d = day_of(t)
    return "Past planned day" if D.o_planned[i] < d else "Due today" if D.o_planned[i] == d else "Planned later"


def order_table(ctx: Ctx, ids: list[int], t: int, cap: int = 60, hide: str = "") -> dict:
    D = ctx.D
    srt = sorted(ids, key=lambda i: ((int(D.o_planned[i]) if D.o_has_plan[i] else 99), int(D.o_created[i])))
    rows = []
    for i in srt[:cap]:
        rows.append({"i": i, "key": D.order_keys[i], "country": D.countries[D.o_country[i]], "fwd": D.fwds[D.o_fwd[i]],
                     "planned": day_n(int(D.o_planned[i])) if D.o_has_plan[i] else "—", "state": order_state(ctx, i, t),
                     "packed": hhmm(int(D.o_ready[i])) if D.o_has_ready[i] and D.o_ready[i] <= t else None,
                     "lines": int(D.o_lines[i]), "cartons": int(D.o_cartons[i])})
    return {"rows": rows, "hideC": "c" in hide, "hideF": "f" in hide, "total": len(ids), "cap": cap,
            "more": f"Showing {cap} of {fmt(len(ids))}, oldest planned day first." if len(ids) > cap else None}


def bars_spec(rows: list[dict], label: str, mx: float, grid: list, gfmt: Callable, ref=None, ref_label=None) -> dict:
    return {"label": label, "max": mx, "grid": [[g, gfmt(g)] for g in grid], "rows": rows, "ref": ref, "refLabel": ref_label}


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


def v_outbound(ctx: Ctx, snap: Snap, p: dict) -> dict:
    D, t = ctx.D, snap.t
    by = p.get("obBy") or "lane"
    seg = [["Past planned day", len(snap.past), "var(--late)"], ["Due today", len(snap.due), "var(--due)"],
           ["Planned later", len(snap.later), "var(--bar)"], ["No planned date", len(snap.noPlan), "var(--bar-2)"]]
    key_of = (lambda i: f"{D.o_country[i]}|{D.o_fwd[i]}") if by == "lane" else (lambda i: f"f|{D.o_fwd[i]}") if by == "fwd" else (lambda i: f"c|{D.o_country[i]}")
    lab_of = D.lane if by == "lane" else (lambda i: D.fwds[D.o_fwd[i]]) if by == "fwd" else (lambda i: D.countries[D.o_country[i]])
    live = [x for x in ctx.store.tasks if x["created"] <= t and x.get("kind") == "orders" and task_status(ctx, x, t)["st"] != "done"]
    rows = []
    for k, ids in group_by(snap.open, key_of):
        pp = [i for i in ids if D.o_has_plan[i] and D.o_planned[i] < snap.day]
        dd = [i for i in ids if D.o_has_plan[i] and D.o_planned[i] == snap.day]
        npk = sum(1 for i in dd if not D.o_has_ready[i] or D.o_ready[i] > t)
        pk = sum(1 for i in pp if D.o_has_ready[i] and D.o_ready[i] <= t)
        tk = next((x for x in live if any(key_of(i) == k for i in x["ids"])), None)
        rows.append({"k": k, "lab": lab_of(ids[0]), "ids": ids, "open": len(ids), "past": len(pp), "due": len(dd), "np": npk, "pk": pk,
                     "tk": tk["rule"] if tk else None})
    rows.sort(key=lambda r: (-r["past"], -r["open"]))
    top = rows[:12]
    mx = max([r["past"] for r in top] + [1])
    sel = next((r for r in rows if r["k"] == p.get("obSel")), top[0] if top else None)
    if top and top[0]["past"]:
        r0 = top[0]
        lead = R((r0["lab"], True), f" holds the most overdue orders ({fmt(r0['past'])}{', all packed: the hold-up is the pickup' if r0['pk'] == r0['past'] else ''}).")
    else:
        lead = R("No orders are past their planned day.")
    buckets = [["1 day late", 1, 1], ["2 days late", 2, 2], ["3–6 days late", 3, 6], ["7+ days late", 7, 99]]
    b = [[l, sum(1 for i in snap.past if a <= snap.day - D.o_planned[i] <= z)] for l, a, z in buckets]
    old = b[2][1] + b[3][1]
    cap = int(p.get("obCap") or 15)
    return {
        "lead": lead, "proj": proj_panel(ctx, snap, "outbound"), "kpis": page_kpis(ctx, snap, ["past", "notPacked", "topGroup", "onTime"], "outbound"),
        "total": fmt(len(snap.open)), "hh": hhmm(t), "seg": [[s[0], s[1], s[2], fmt(s[1])] for s in seg],
        "age": {"sub": R(f"Days past their planned day, at {hhmm(t)}. ", *((fmt(old), True), " have waited 3 days or more: chase these first.") if old else ("None has waited more than 2 days.",)),
                "bars": hbars(b, max([x[1] for x in b] + [1]))},
        "by": by, "groupHead": "Country · forwarder" if by == "lane" else "Forwarder" if by == "fwd" else "Country",
        "rows": [{"k": r["k"], "lab": r["lab"], "past": r["past"], "pastText": fmt(r["past"]), "frac": r["past"] / mx,
                  "due": fmt(r["due"]) if r["due"] else None, "np": fmt(r["np"]) if r["np"] else None, "tk": r["tk"], "sel": r is sel} for r in top],
        "groupsNote": f"Top {len(top)} of {fmt(len(rows))} groups. “Not packed” = due today with cartons still to pack.",
        "sel": {"lab": sel["lab"], "open": fmt(sel["open"]), "table": order_table(ctx, sel["ids"], t, cap, "cf" if by == "lane" else "f" if by == "fwd" else "c"),
                "moreBtn": ("more" if min(60, len(sel["ids"])) - cap > 0 else "fewer") if len(sel["ids"]) > cap else None} if sel else None,
        "cards": page_cards(ctx, snap, lambda c: c["rule"].startswith("OUT"), "Outbound cards"),
        "foot": f"{fmt(len(snap.noPlan))} open orders with no planned date are left out of past-due and due-today counts (DQ-02).",
    }


def v_inbound(ctx: Ctx, snap: Snap, p: dict) -> dict:
    D, t = ctx.D, snap.t
    short = lambda m: f"{day_n(day_of(m)).split(' ')[0]} {hhmm(m)}"
    rows = []
    for i in snap.dock:
        a = D.asns[i]
        w = t - int(D.a_dock[i])
        u = ctx.usual_min(i)
        st = "dq" if w > DQ_WAIT else "over" if w > u else "ok"
        cap = max(u * 1.6, min(w, u * 3))
        docked = day_label(day_of(int(D.a_dock[i]))).split(" ", 1)[1] if w > 1440 * 6 else short(int(D.a_dock[i]))
        rows.append({"i": i, "asn": a[0], "hv": bool(D.hv[i]), "ref": a[5] or None, "docked": docked, "type": D.types[D.a_type[i]],
                     "lines": a[4], "st": st, "w": w, "u": u, "waited": hrs(w), "usual": js_num(u / 60),
                     "wf": min(100, 100 * w / cap), "uf": 100 * u / cap})
    rows.sort(key=lambda r: ((r["st"] == "dq"), -(r["w"] / r["u"])))
    over = [r for r in rows if r["st"] == "over"]
    dq = [r for r in rows if r["st"] == "dq"]
    if over:
        n = len(over)
        lead = R((f"{n} deliver{'ies are' if n > 1 else 'y is'} past the usual time.", True), " Start with the top row.")
    elif rows:
        lead = R(f"All {len(rows) - len(dq)} real waits are within their usual time." + (f" {len(dq)} record{'s look' if len(dq) > 1 else ' looks'} wrong and went to the data owner." if dq else ""))
    else:
        lead = R("Nothing is waiting at the dock.")
    m = D.a_has_gr & (D.a_gr > t - 1440) & (D.a_gr <= t)
    got = sorted([int(i) for i in np.flatnonzero(m)], key=lambda i: -int(D.a_gr[i]))
    rr = sorted([[ty, sum(1 for i in got if D.a_type[i] == k)] for k, ty in enumerate(D.types)], key=lambda r: -r[1])
    rr = [r for r in rr if r[1]]
    lst = [{"i": i, "asn": D.asns[i][0], "hv": bool(D.hv[i]), "ref": D.asns[i][5] or "–", "type": D.types[D.a_type[i]],
            "docked": when(int(D.a_dock[i])) if D.a_has_dock[i] else "—", "received": when(int(D.a_gr[i])), "lines": D.asns[i][4]} for i in got[:60]]
    return {
        "lead": lead, "proj": proj_panel(ctx, snap, "inbound"), "kpis": page_kpis(ctx, snap, ["dock", "dockOver", "linesIn", "stuck"], "inbound"),
        "rows": rows, "got": fmt(len(got)),
        "byType": hbars([[f"{r[0]} · usual {js_num(D.usual[r[0]])} h", r[1]] for r in rr], max([r[1] for r in rr] + [1]), "acc"),
        "list": lst, "cards": page_cards(ctx, snap, lambda c: c["rule"].startswith("IN") or c["rule"] == "DQ-03", "Inbound cards"),
        "foot": f"No shipment ref shown = DSV’s report has none for that delivery (usual for Normal deliveries). {fmt(D.dq['asns_no_dock'])} ASNs have no dock time and never show here (DQ-07).",
    }


def v_trace(ctx: Ctx, snap: Snap, p: dict) -> dict:
    D, t = ctx.D, snap.t
    C = D.cartons
    q = (p.get("traceQ") or "").strip()
    hits = [i for i, c in enumerate(C) if q and (c[0] == q or c[1] == q or c[5] == q or c[8] == q)]
    n_m = sum(1 for c in C if c[1])
    inside = int((D.c_has_gr & (D.c_gr <= t) & (D.c_hand > t)).sum())
    tot, miss = 35092, len(C) - n_m
    other = tot - len(C)
    K = kpi_fns(ctx)
    others = [d for d in WEEK if d != snap.day]
    kb = {"key": "milkIn", "lab": f"Milkrun cartons in the warehouse at {hhmm(t)}", "val": inside,
          "def": "Received, not yet handed over to a forwarder.", "mode": "info",
          "base": avg(K["milkIn"](snapshot(d * 1440 + t % 1440)) for d in others) if others else None, "baseLab": f"week avg at {hhmm(t)}"}
    res = None
    if q and hits:
        f = C[hits[0]]
        asn_set = {C[i][1] for i in hits if C[i][1]}
        ord_set = {C[i][5] for i in hits}
        pts = [x for x in [["Dock → receipt", f[2], f[3]], ["Receipt → Cyclone", f[3], f[4]], ["Cyclone → order", f[4], f[6]], ["Order → handover", f[6], f[7]]]
               if x[1] is not None and x[2] is not None and x[2] >= x[1]]
        dur = lambda m: f"{m} min" if m < 60 else to_fixed(m / 60, 1) + " h"
        total = sum(max(1, x[2] - x[1]) for x in pts)

        def step(lab, v, sub):
            st = "none" if v is None else "future" if v > t else ""
            return {"lab": lab, "st": st, "val": "not in data" if v is None else when(v), "sub": "after the replay time" if v is not None and v > t else (sub or "")}

        res = {"summary": f"{fmt(len(hits))} carton{'s' if len(hits) > 1 else ''} · {len(asn_set)} ASN · {len(ord_set)} order · first carton shown, {D.countries[f[10]]} via {D.fwds[f[9]]}",
               "time": {"total": dur(total), "parts": [{"lab": x[0], "w": max(1, x[2] - x[1]), "dur": dur(x[2] - x[1])} for x in pts]} if pts else None,
               "steps": [step("Docked", f[2], "ASN " + f[1] if f[1] else ""), step("Received", f[3], "goods receipt" if f[1] else "carton has no inbound match"),
                         step("Cyclone scan", f[4], "carton " + f[0]), step("Order created", f[6], "order " + f[5]), step("Handed over", f[7], D.fwds[f[9]])],
               "rows": [{"carton": C[i][0], "asn": C[i][1] or "—", "order": C[i][5], "received": when(C[i][3]), "cyclone": when(C[i][4]),
                         "handed": when(C[i][7]) if C[i][7] <= t else None} for i in hits[:40]],
               "more": f"Showing 40 of {fmt(len(hits))}." if len(hits) > 40 else None}
    return {"q": q, "examples": [["Carton", C[0][0]], ["ASN", "0000031762"], ["Order", C[50][5]]], "noHit": bool(q) and not hits,
            "coverage": {"nM": fmt(n_m), "pctText": to_fixed(pct(n_m, len(C)), 1), "nC": fmt(len(C)), "tot": fmt(tot), "miss": fmt(miss), "other": fmt(other),
                         "segs": [[n_m, "var(--ok)", "Traceable"], [miss, "var(--due)", "Milkrun, no inbound match"], [other, "var(--bar-2)", "Other flows, no shared ID"]]},
            "kpi": kpi_card(ctx, kb, snap), "result": res}


def v_trends(ctx: Ctx, snap: Snap, p: dict) -> dict:
    D, cfg = ctx.D, ctx.cfg
    wkend = bool(p.get("trWk"))
    all_d = list(D.late_by_day.keys())
    days = [d for d in all_d if wkend or D.late_by_day[d][0] >= 100]
    sm = [d for d in all_d if D.late_by_day[d][0] >= 100]
    tot = sum(D.late_by_day[d][0] for d in sm)
    late = sum(D.late_by_day[d][1] for d in sm)
    avg_l = 100 * late / tot
    tgt = 100 - cfg["ontime"]
    miss = [d for d in sm if 100 * D.late_by_day[d][1] / D.late_by_day[d][0] > tgt]
    worst = sorted(sm, key=lambda d: -D.late_by_day[d][1] / D.late_by_day[d][0])[0] if sm else None
    dn = lambda d: day_n(int(d[8:]) - 1)
    rows = []
    for d in days:
        n, l = D.late_by_day[d]
        v = 100 * l / n
        rows.append({"label": dn(d), "sub": fmt(n) + " orders", "vals": [v], "faint": n < 100, "colors": ["var(--late)" if v > tgt else "var(--ok)"],
                     "tips": [to_fixed(v, 1) + "% late, " + fmt(n) + " orders"], "valLabels": [to_fixed(v, 0) + "%"]})
    ld = [d for d in D.out_lines_day if "2026-08-17" <= d <= "2026-08-23" and (wkend or d not in ("2026-08-22", "2026-08-23"))]
    rows2 = [{"label": dn(d), "vals": [D.in_lines_day.get(d, 0), D.out_lines_day.get(d, 0)], "hl": int(d[8:]) - 1 == snap.day,
              "colors": ["var(--bar-2)", "var(--bar)"], "tips": [fmt(D.in_lines_day.get(d, 0)) + " inbound lines", fmt(D.out_lines_day.get(d, 0)) + " outbound lines"]}
             for d in ld]
    wl = [D.in_lines_day.get(d, 0) + D.out_lines_day.get(d, 0) for d in ld]
    wavg = avg(wl[:5])
    peak = ld[wl.index(max(wl))] if wl else None
    by: dict[int, list[int]] = {}
    m = D.o_has_plan & (D.o_planned >= 16) & (D.o_planned <= 22)
    for i in np.flatnonzero(m):
        r = by.setdefault(int(D.o_fwd[i]), [0, 0])
        r[0] += 1
        if D.o_hand[i] // 1440 > D.o_planned[i]:
            r[1] += 1
    rk = sorted([(f, r) for f, r in by.items() if r[0] >= cfg["fwdMin"]], key=lambda x: -x[1][1])[:8]
    flag = [(f, r) for f, r in by.items() if r[0] >= cfg["fwdMin"] and 100 * r[1] / r[0] >= cfg["fwdLate"]]
    flag_late = sum(r[1] for _, r in flag)
    on_wk = 100 - avg_l
    stat = lambda lab, val, foot, st: {"lab": lab, "val": val, "foot": foot, "st": st, "icon": STAT[st][0], "word": STAT[st][1]}
    max_wl = max(wl) if wl else 0
    sub = R((f"{len(miss)} of {len(sm)} weekdays missed the {js_num(cfg['ontime'])}% on-time target", True),
            (f", worst {day_label(int(worst[8:]) - 1)}" if worst else "") + f". {len(flag)} forwarders account for {to_fixed(pct(flag_late, late), 0)}% of late orders. Week-level views; they don’t follow the replay time.")
    return {
        "sub": sub, "wkend": wkend,
        "stats": [stat("On time this week", to_fixed(on_wk, 1) + "%", f"Weekdays, {fmt(tot)} orders. Target {js_num(cfg['ontime'])}%.",
                       "ok" if on_wk >= cfg["ontime"] else "watch" if on_wk >= cfg["ontime"] - 10 else "act"),
                  stat("Days below target", f"{len(miss)} of {len(sm)}", ", ".join(dn(d) for d in miss) or "None", "act" if miss else "ok"),
                  stat("Forwarders to review", str(len(flag)), f"{js_num(cfg['fwdLate'])}%+ of their orders late ({js_num(cfg['fwdMin'])}+ orders)", "watch" if flag else "ok"),
                  stat("Busiest day", dn(peak) if peak else "–", f"{fmt(max_wl)} lines, {to_fixed(max_wl / wavg, 2)}× the weekday average" if peak else "",
                       "watch" if max_wl > cfg["load"] * wavg else "ok")],
        "accuracy": accuracy(ctx),
        "lateChart": bars_spec(rows, "Late rate by planned day", 110, [0, 25, 50, 75, 100], lambda g: f"{g}%", tgt,
                               f"Target: at most {js_num(tgt)}% late · week average {to_fixed(avg_l, 1)}%"),
        "lateNote": "Red = missed the target, green = met it." + (" Grey = weekend days with under 100 orders; their rates swing." if wkend else " Weekends hidden: under 100 orders a day."),
        "fwdBars": hbars([[f"{D.fwds[f]} · {to_fixed(pct(r[1], r[0]), 0)}%", r[1]] for f, r in rk], max([r[1] for _, r in rk] + [1])),
        "workChart": bars_spec(rows2, "Inbound and outbound lines per day", max([v for r in rows2 for v in r["vals"]] + [1]) * 1.12,
                               [0, 2500, 5000, 7500, 10000], lambda g: f"{g // 1000}k" if g else "0"),
        "cards": page_cards(ctx, snap, lambda c: c["rule"].startswith("MGR"), "Manager reviews"),
    }


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


RULES = [
    ["IN-01", "Docked, not received in usual time", "in", "live"], ["IN-02", "High-value delivery waiting too long", "in", "live"],
    ["IN-03", "Received quantity differs", "in", "Checked: 0 of 36,533 lines flagged this week"], ["IN-04", "Milkrun carton, no order", "in", "live"],
    ["IN-05", "Returns (RMA) received", "in", "live"],
    ["OUT-01", "Past planned day (top group)", "out", "live"], ["OUT-02", "Created late on its planned day", "out", "live"],
    ["OUT-03", "Not handed over by the cut-off", "out", "live"], ["OUT-04", "Forwarder with many overdue", "out", "live"],
    ["OUT-05", "Country with many overdue", "out", "live"], ["OUT-06", "Due today, not fully packed (planner proposes)", "out", "live"],
    ["DQ-01", "Planned before created", "dq", "live"], ["DQ-02", "No planned date", "dq", "live"], ["DQ-03", "Dock with no receipt (120 h+)", "dq", "live"],
    ["DQ-04", "Contents mismatch", "dq", "Not built yet"], ["DQ-05", "Clock drift (+8 h)", "dq", "Resolved on load"],
    ["DQ-06", "Identical rows: label, never delete", "dq", "Count on Data checks"], ["DQ-07", "Missing fields", "dq", "Counts on Data checks"],
    ["MGR-01", "On-time below target", "mgr", "live"], ["MGR-02", "Forwarder with a high late share", "mgr", "live"],
    ["MGR-03", "Receipts to SEQ / HBS above limit", "mgr", "live"], ["MGR-04", "Workload above limit", "mgr", "live"],
]


def v_rules(ctx: Ctx, snap: Snap, p: dict) -> dict:
    cfg = ctx.cfg
    live: dict[str, int] = {}
    for c in all_cards(ctx, snap):
        live[c["rule"]] = live.get(c["rule"], 0) + 1
    j = js_num
    lim = {"IN-02": f"{j(cfg['hvWait'])} h", "IN-04": f"{j(cfg['milk'])} min", "OUT-02": f"after {j(cfg['created'])}:00", "OUT-03": f"{j(cfg['cut'])}:00",
           "OUT-04": f"{j(cfg['fwd'])}+ orders", "OUT-05": f"{j(cfg['ctry'])}+ orders", "MGR-01": f"< {j(cfg['ontime'])}%", "MGR-02": f"{j(cfg['fwdLate'])}%+ late",
           "MGR-03": f"> {j(cfg['zone'])}%", "MGR-04": f"> {j(cfg['load'])}×", "IN-01": "usual time", "DQ-03": "120 h"}
    grp = [["in", "Inbound · inbound supervisor approves"], ["out", "Outbound · outbound supervisor approves, planner proposes"],
           ["dq", "Data checks · labels only, no floor alert"], ["mgr", "Manager reviews · operations manager decides"]]
    n_live = sum(1 for r in RULES if r[3] == "live")
    firing = len(live)
    kpi_reg = [
        ["On time", "Share of orders planned for a day that were handed over on that calendar day", "Outbound sup., Ops manager", f"Target {j(cfg['ontime'])}% (proposed)"],
        ["Late", "Handed over on a later calendar day than the Planned Post Date (working definition WA-05)", "All", "Waits on DSV (PC-01)"],
        ["Past planned day", "Open orders whose planned day has passed", "Outbound sup., Planner, Ops manager", "Baseline: week average at that hour"],
        ["Due today, not packed", "Planned for today with cartons still to pack", "Outbound sup., Planner", "Baseline: week average at that hour"],
        ["Waiting longer than usual", "Docked, not received, past the time 90% of that delivery type finish within", "Inbound sup.", "Baseline: week average at that hour"],
        ["Workload", "Inbound + outbound lines in a day", "Ops manager, Planner", f"Limit {j(cfg['load'])}× the weekday average (proposed)"],
        ["Suspect records open", "Orders and deliveries caught by the data checks, not yet labelled", "Data owner", "Target: falling"],
    ]
    return {"lead": R((f"{n_live} of {len(RULES)} rules run on the data; {firing} {'is' if firing == 1 else 'are'} raising a card at {hhmm(snap.t)}.", True),
                      " A rule only raises a card; a person always approves or dismisses it. The operations manager sets the limits on Settings."),
            "groups": [{"lab": lab, "rules": [{"id": r[0], "name": r[1], "lim": lim.get(r[0], "–"), "live": r[3] == "live", "note": r[3], "now": live.get(r[0], 0)}
                                              for r in RULES if r[2] == o]} for o, lab in grp],
            "kpiReg": kpi_reg}


def v_atrisk(ctx: Ctx, snap: Snap, p: dict) -> dict:
    D, cfg, t, day = ctx.D, ctx.cfg, snap.t, snap.day
    due, np_ = list(snap.due), list(snap.notPacked)
    late = {i for i in due if D.o_created[i] >= day * 1440 + cfg["created"] * 60}
    cards = all_cards(ctx, snap)
    c6 = next((c for c in cards if c["rule"] == "OUT-06"), None)
    c2 = next((c for c in cards if c["rule"] == "OUT-02"), None)
    kf = lambda i: f"{D.o_country[i]}|{D.o_fwd[i]}"
    gs = []
    for k, ids in group_by(np_, kf):
        allg = [i for i in due if kf(i) == k]
        gs.append({"k": k, "ids": ids, "all": len(allg), "lab": D.lane(ids[0]), "late": sum(1 for i in ids if i in late)})
    sel = next((g for g in gs if g["k"] == p.get("arSel")), gs[0] if gs else None)
    if np_:
        lead = R((f"{fmt(len(np_))} of {fmt(len(due))} orders due today are not fully packed.", True), " Pack the top lanes first; the rest only need a pickup.")
    else:
        lead = R(("Everything due today is packed.", True), f" {fmt(len(due))} orders only need a pickup.")
    if late:
        lead += R(f" {len(late)} were created after {js_num(cfg['created'])}:00 and usually leave late (OUT-02).")
    return {"lead": lead, "proj": proj_panel(ctx, snap, "atrisk"), "kpis": page_kpis(ctx, snap, ["due", "notPacked", "packedDue", "past"], "atrisk"),
            "hasLate": bool(late),
            "lanes": [{"k": g["k"], "lab": g["lab"], "n": fmt(len(g["ids"])), "pk": g["all"] - len(g["ids"]), "all": g["all"],
                       "frac": (g["all"] - len(g["ids"])) / max(1, g["all"]), "late": g["late"] or None, "sel": g is sel} for g in gs[:12]],
            "sel": {"lab": sel["lab"], "n": len(sel["ids"]), "table": order_table(ctx, sel["ids"], t, 40, "cf")} if sel else None,
            "cards": [card_view(ctx, c, snap) for c in (c6, c2) if c]}


def v_settings(ctx: Ctx, snap: Snap, p: dict) -> dict:
    from .state import CFG_DEF, CFG_META
    can = ctx.role == "mgr" and ctx.can_act()
    return {"can": can, "rows": [{"k": k, "lab": lab, "unit": unit, "rule": rule, "min": mn, "max": mx, "step": st, "value": ctx.cfg[k],
                                  "def": CFG_DEF[k], "changed": ctx.cfg[k] != CFG_DEF[k]} for k, lab, unit, rule, mn, mx, st in CFG_META]}


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


VIEWS: dict[str, Callable[[Ctx, Snap, dict], dict]] = {
    "shift": v_shift, "atrisk": v_atrisk, "outbound": v_outbound, "inbound": v_inbound, "trace": v_trace, "trends": v_trends,
    "whatif": v_whatif, "checks": v_checks, "rules": v_rules, "settings": v_settings, "tasks": v_tasks,
}


# ================================================================ header timeline, drill-downs
TL_PAST = {"shift": ["Since shift start (06:00 today)", lambda d, cfg: d * 1440 + 360], "yday": ["Since yesterday 06:00", lambda d, cfg: (d - 1) * 1440 + 360],
           "d3": ["Last 3 days", lambda d, cfg: (d - 3) * 1440], "week": ["Whole replay week", lambda d, cfg: T0]}
TL_NEXT = {"cut": ["To today’s cut-off", lambda d, cfg: d * 1440 + cfg["cut"] * 60], "mid": ["To midnight tonight", lambda d, cfg: (d + 1) * 1440],
           "tom9": ["To tomorrow 09:00", lambda d, cfg: (d + 1) * 1440 + 540], "tom": ["To the end of tomorrow", lambda d, cfg: (d + 2) * 1440]}


def tl_window(ctx: Ctx, tl_past: str | None, tl_next: str | None) -> tuple[int, int]:
    d = day_of(ctx.t)
    pf = TL_PAST.get(tl_past or "yday", TL_PAST["yday"])[1]
    nf = TL_NEXT.get(tl_next or "mid", TL_NEXT["mid"])[1]
    return min(ctx.t - 60, max(T0, pf(d, ctx.cfg))), max(ctx.t + 60, nf(d, ctx.cfg))


def timeline(ctx: Ctx, tl_past: str | None, tl_next: str | None) -> dict:
    w0, w1 = tl_window(ctx, tl_past, tl_next)
    now, d, cut = ctx.t, day_of(ctx.t), ctx.cfg["cut"]
    st = 180 if w1 - w0 > 3.5 * 1440 else 60
    hs = [[t, len(snapshot(t).past)] for t in range(w0, now + 1, st)] + [[now, len(snapshot(now).past)]]
    s_now = snapshot(now)
    fs = []
    for t in range(now + st, w1 + 1, st):
        e = project(ctx, s_now, t)["past"]
        fs.append([t, e["mid"] if e["mid"] is not None else e["worst"]])
    long_ = w1 - w0 > 3.5 * 1440
    if long_:
        cand = [[dd * 1440, day_n(dd)] for dd in range(day_of(w0), day_of(w0) + 10)] + [[now, "Now"]]
    else:
        c = js_num(cut)
        cand = [[(d - 1) * 1440 + cut * 60, f"Yesterday {c}:00"], [d * 1440 + 360, "Shift start 06:00"], [now, "Now"], [d * 1440 + cut * 60, f"Cut-off {c}:00"],
                [(d + 1) * 1440, "Midnight"], [(d + 1) * 1440 + 540, "Tomorrow 09:00"], [(d + 1) * 1440 + cut * 60, f"Tomorrow {c}:00"], [(d + 2) * 1440, "Tomorrow midnight"]]
    gap = (w1 - w0) * 0.075
    lms: list = []
    for c in sorted([c for c in cand if w0 <= c[0] <= w1 and (c[1] == "Now" or abs(c[0] - now) >= gap)], key=lambda c: c[0]):
        last = lms[-1] if lms else None
        if c[1] == "Now" or not last or c[0] - last[0] >= gap:
            lms.append(c)
        elif last[1] != "Now":
            lms[-1] = c
    return {"w0": w0, "w1": w1, "now": now, "hs": hs, "fs": fs, "lms": [[num(a), b] for a, b in lms]}


def order_detail(ctx: Ctx, i: int) -> dict:
    D, t = ctx.D, ctx.view_t()
    L, cs = D.extra["OL"][i], D.cartons_of(i)
    rows = [L[j:j + 4] for j in range(0, len(L), 4)]
    st = order_state(ctx, i, t)
    return {"i": i, "key": D.order_keys[i], "state": st, "dn": D.dns[D.o_dn[i]], "lane": D.lane(i), "created": when(int(D.o_created[i])),
            "planned": day_label(int(D.o_planned[i])) if D.o_has_plan[i] else "none (DQ-02)",
            "packed": when(int(D.o_ready[i])) if D.o_has_ready[i] and D.o_ready[i] <= t else "not yet",
            "handed": when(int(D.o_hand[i])) if D.o_hand[i] <= t else "not yet",
            "lines": [{"line": r[0], "sku": D.extra["skus"][r[1]], "qty": fmt(r[2]), "carton": cs[r[3]], "milk": cs[r[3]] in D.milk_ids} for r in rows],
            "foot": f"{len(rows)} line{'s' if len(rows) > 1 else ''} · {len(cs)} carton{'s' if len(cs) > 1 else ''}. Lines and cartons come from DSV’s outbound report."}


def asn_detail(ctx: Ctx, i: int) -> dict:
    D, t = ctx.D, ctx.view_t()
    a, L = D.asns[i], D.extra["AL"][i]
    rows = [L[j:j + 6] for j in range(0, len(L), 6)]
    got = bool(D.a_has_gr[i] and D.a_gr[i] <= t)
    bad = sum(1 for r in rows if r[3] != r[4]) if got else 0
    return {"i": i, "asn": a[0], "ref": a[5] or None, "type": D.types[D.a_type[i]], "hv": bool(D.hv[i]), "got": got, "bad": bad,
            "docked": when(int(D.a_dock[i])) if D.a_has_dock[i] else "—", "received": when(int(D.a_gr[i])) if got else "not yet",
            "lines": [{"line": r[0], "sku": D.extra["skus"][r[1]], "pack": r[2], "exp": fmt(r[3]), "rcv": fmt(r[4]) if got else "—",
                       "match": None if not got else r[3] == r[4], "zone": D.zones[r[5]]} for r in rows]}


def lookup(ctx: Ctx, q: str) -> dict:
    D = ctx.D
    q = q.strip()
    qq = q.rjust(10, "0")
    for k in (q, qq):
        if k in D.order_index:
            return {"kind": "order", "i": D.order_index[k]}
    for k in (q, qq):
        if k in D.asn_index:
            return {"kind": "asn", "i": D.asn_index[k]}
    return {"kind": None, "msg": f"No order or ASN “{q}” in this week’s data"}
