"""Demo log-in accounts: one person per role, so a log-in opens that role's view.

This is a prototype stand-in for real sign-in, not security. The repo is public,
so anyone can read these. Edit names and passwords here; roles must be keys of
engine.ROLES (in, out, plan, mgr, dq).
"""
from __future__ import annotations

from typing import Optional

DEMO_USERS = [
    {"name": "Aisha", "password": "inboundsupervisor", "role": "in"},
    {"name": "John", "password": "outboundsupervisor", "role": "out"},
    {"name": "Mei", "password": "planner", "role": "plan"},
    {"name": "Raj", "password": "operationsmanager", "role": "mgr"},
    {"name": "Sam", "password": "dataowner", "role": "dq"},
]


def check_login(name: str, password: str) -> Optional[dict]:
    """Return {"name", "role"} when name (any case) and password match, else None."""
    n = name.strip().lower()
    for u in DEMO_USERS:
        if u["name"].lower() == n and u["password"] == password.strip():
            return {"name": u["name"], "role": u["role"]}
    return None
