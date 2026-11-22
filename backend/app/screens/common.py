"""Shared building blocks used by several screens: rich text, cards, tasks, KPI tiles, charts, projections, order tables.

Rich text: short sentences with bold parts are sent as a list of [text, bold] segments (see R).

Owned by the shared-core owner. Change with care: every screen uses these.
"""
from __future__ import annotations

import math
from typing import Callable

from ..engine import (
    all_cards, ASSIGN, auto_closed, can_tick, Ctx, group_by, kpi_fns, last_weekday, next_card_for,
    on_time, outcome, part_done, project, prop_status, ROLES, same_before, Snap, snapshot,
    task_status, TIER_ORDER, TIERS, WEEK)
from ..fmt import day_n, day_of, dkey, fmt, hhmm, in_min, js_num, js_round, to_fixed, when


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
