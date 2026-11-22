"""FastAPI app: the HTTP layer over service.py.

Run (from backend/):  uvicorn app.main:app --reload --port 8000
API docs:             http://localhost:8000/docs
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import service as svc

app = FastAPI(title="DSV Warehouse Twin API", version="1.0.0",
              description="Backend for the DSV Digital Twin prototype (SUTD 40.318, Team 2). Replay of one week of DSV data.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _wrap(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except svc.ActionError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------- read
@app.get("/api/health")
def health() -> dict:
    from .dataset import get_dataset
    D = get_dataset()
    return {"ok": True, "orders": D.n_orders, "asns": len(D.asns), "cartons": len(D.cartons)}


@app.get("/api/meta")
def meta() -> dict:
    return svc.meta()


@app.get("/api/frame")
def frame(t: int, role: str = "out", view: str = "shift", at: Optional[int] = None,
          obBy: Optional[str] = None, obSel: Optional[str] = None, obCap: Optional[int] = None, arSel: Optional[str] = None,
          traceQ: Optional[str] = None, trWk: bool = False, wi: int = 20, tlPast: Optional[str] = None, tlNext: Optional[str] = None) -> dict:
    params = {"obBy": obBy, "obSel": obSel, "obCap": obCap, "arSel": arSel, "traceQ": traceQ, "trWk": trWk, "wi": wi,
              "tlPast": tlPast, "tlNext": tlNext}
    return svc.frame(t, at, role, view, params)


@app.get("/api/order/{i}")
def order(i: int, t: int, role: str = "out", at: Optional[int] = None) -> dict:
    return _wrap(svc.get_order, i, t, at, role)


@app.get("/api/asn/{i}")
def asn(i: int, t: int, role: str = "out", at: Optional[int] = None) -> dict:
    return _wrap(svc.get_asn, i, t, at, role)


@app.get("/api/lookup")
def lookup(q: str = Query(..., min_length=1)) -> dict:
    return svc.get_lookup(q)


@app.get("/api/whatif")
def whatif(wi: int = 20) -> dict:
    return svc.get_whatif(wi)


# ---------------------------------------------------------------- actions
class Base(BaseModel):
    t: int
    role: str


class ApproveIn(Base):
    key: str
    assign: list[str]
    due: Optional[int] = None
    note: str = ""


class DismissIn(Base):
    key: str
    reason: str
    details: str = ""


class ProposeIn(Base):
    key: str


class TickIn(Base):
    id: str
    part: str
    done: bool = True


class TaskIn(Base):
    title: str
    assign: list[str]
    due: Optional[int] = None
    note: str = ""


class CfgIn(Base):
    values: dict[str, Any] = Field(default_factory=dict)


class UndoIn(BaseModel):
    token: dict[str, Any]


@app.post("/api/actions/approve")
def approve(b: ApproveIn) -> dict:
    return _wrap(svc.approve, b.t, b.role, b.key, b.assign, b.due, b.note)


@app.post("/api/actions/dismiss")
def dismiss(b: DismissIn) -> dict:
    return _wrap(svc.dismiss, b.t, b.role, b.key, b.reason, b.details)


@app.post("/api/actions/propose")
def propose(b: ProposeIn) -> dict:
    return _wrap(svc.propose, b.t, b.role, b.key)


@app.post("/api/actions/tick")
def tick(b: TickIn) -> dict:
    return _wrap(svc.tick, b.t, b.role, b.id, b.part, b.done)


@app.post("/api/actions/task")
def task(b: TaskIn) -> dict:
    return _wrap(svc.new_task, b.t, b.role, b.title, b.assign, b.due, b.note)


@app.post("/api/actions/seed")
def seed(b: Base) -> dict:
    return _wrap(svc.seed, b.t, b.role)


@app.post("/api/actions/cfg")
def cfg(b: CfgIn) -> dict:
    return _wrap(svc.save_cfg, b.t, b.role, b.values)


@app.post("/api/actions/cfg-reset")
def cfg_reset(b: Base) -> dict:
    return _wrap(svc.reset_cfg, b.t, b.role)


@app.post("/api/actions/undo")
def undo(b: UndoIn) -> dict:
    return _wrap(svc.undo, b.token)


@app.post("/api/actions/reset")
def reset() -> dict:
    return svc.reset_demo()
