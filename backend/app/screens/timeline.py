"""Header timeline (shown on every screen) and its time-window presets.
"""
from __future__ import annotations

from ..dataset import T0
from ..engine import Ctx, project, snapshot
from ..fmt import day_n, day_of, js_num
from .common import num


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
