"""Shared twin state: tasks, dismissals, proposals, alert limits and the change log.

In the single-file prototype this lived in the browser (localStorage). Here it lives on
the server in one JSON file, so everyone using the same backend sees the same tasks.
UI-only preferences (screen, role, theme, simulated time) stay in the browser.
"""
from __future__ import annotations

import json
import os
import threading
import time
import random
import string
from pathlib import Path

STATE_FILE = Path(os.environ.get("TWIN_STATE_FILE", Path(__file__).parent.parent / "state.json"))

CFG_DEF = {"cut": 18, "created": 12, "fwd": 20, "ctry": 50, "milk": 120, "hvWait": 4,
           "ontime": 70, "fwdLate": 90, "fwdMin": 30, "zone": 25, "load": 1.25, "wage": 2200}
# key, label, unit, used by, min, max, step
CFG_META = [
    ["cut", "Escalation cut-off on the planned day", "h (24 h clock)", "OUT-03", 12, 23, 1],
    ["created", "Late-created hour on the planned day", "h", "OUT-02", 8, 18, 1],
    ["fwd", "Overdue orders per forwarder", "orders", "OUT-04", 5, 100, 5],
    ["ctry", "Overdue orders per country", "orders", "OUT-05", 10, 200, 10],
    ["milk", "Milkrun carton with no order after", "minutes", "IN-04", 30, 480, 30],
    ["hvWait", "High-value delivery waiting longer than", "h", "IN-02", 1, 24, 1],
    ["ontime", "On-time target for a planned day", "%", "MGR-01 and KPIs", 50, 100, 5],
    ["fwdLate", "Forwarder late share worth a review", "%", "MGR-02", 50, 100, 5],
    ["fwdMin", "Minimum orders for that forwarder review", "orders", "MGR-02", 10, 200, 10],
    ["zone", "Share of receipts to SEQ / HBS zones", "%", "MGR-03", 10, 60, 5],
    ["load", "Workload vs the week average", "× average", "MGR-04 and KPIs", 1.05, 2, 0.05],
    ["wage", "Basic monthly wage (placeholder)", "S$ / month", "Staffing what-if", 1000, 10000, 50],
]


def new_id() -> str:
    return "t" + format(int(time.time() * 1000), "x") + "".join(random.choices(string.ascii_lowercase + string.digits, k=4))


def _empty() -> dict:
    return {"tasks": [], "dismissed": [], "proposals": [], "cfg": dict(CFG_DEF), "log": []}


class Store:
    """Very small JSON-file store. One process; a lock keeps writes consistent."""

    def __init__(self, path: Path = STATE_FILE):
        self.path = path
        self.lock = threading.RLock()
        self.version = 0
        self.s = _empty()
        if path.exists():
            try:
                with open(path) as f:
                    loaded = json.load(f)
                self.s.update({k: loaded[k] for k in self.s if k in loaded})
                self.s["cfg"] = {**CFG_DEF, **self.s.get("cfg", {})}
            except (OSError, ValueError):
                pass
        for i, x in enumerate(self.s["tasks"]):
            x.setdefault("id", f"t{i}_{x.get('created')}")
            x.setdefault("parts", {})

    def save(self) -> None:
        with self.lock:
            self.version += 1
            tmp = self.path.with_suffix(".tmp")
            with open(tmp, "w") as f:
                json.dump(self.s, f)
            tmp.replace(self.path)

    def reset(self) -> None:
        with self.lock:
            self.s = _empty()
            self.save()

    # shorthand
    @property
    def tasks(self) -> list[dict]:
        return self.s["tasks"]

    @property
    def dismissed(self) -> list[dict]:
        return self.s["dismissed"]

    @property
    def proposals(self) -> list[dict]:
        return self.s["proposals"]

    @property
    def cfg(self) -> dict:
        return self.s["cfg"]

    @property
    def log(self) -> list[dict]:
        return self.s["log"]


_store: Store | None = None


def get_store() -> Store:
    global _store
    if _store is None:
        _store = Store()
    return _store
