"""Headline numbers from the prototype, checked against the backend.

Run from backend/:  pytest -q
These values were verified against the original single-file prototype (twin.html).
"""
from pathlib import Path

import pytest

from app import service as svc
from app.engine import Ctx, all_cards, snapshot
from app.state import Store

FRI_0900 = 20 * 1440 + 540   # Fri 21 Aug 09:00


@pytest.fixture()
def store(tmp_path: Path) -> Store:
    return Store(tmp_path / "state.json")


def test_snapshot_fri_0900():
    s = snapshot(FRI_0900)
    assert (len(s.open), len(s.past), len(s.due), len(s.later), len(s.noPlan), len(s.notPacked), len(s.dock)) == (3744, 1460, 1652, 612, 20, 81, 3)


def test_cards_fri_0900(store):
    cards = all_cards(Ctx(store=store, t=FRI_0900), snapshot(FRI_0900))
    titles = {c["rule"]: c["title"] for c in cards if c.get("tier") != "prevent"}
    assert titles["OUT-01"] == "313 orders to HK with FORWARDER 013 are past their planned day"
    assert titles["MGR-01"] == "On-time for orders planned Thu 20 Aug was 61.1%"
    assert [c["rule"] for c in cards].count("MGR-01") == 2   # yesterday's review + today's prevent card


def test_whatif_plus20():
    w = svc.get_whatif(20)
    assert w["typical"]["n"] == 29 and w["typical"]["range"] == "range 27–32"
    assert w["busiest"]["n"] == 37


def test_approve_then_card_is_covered(store, monkeypatch):
    monkeypatch.setattr(svc, "get_store", lambda: store)
    c = next(c for c in all_cards(Ctx(store=store, t=FRI_0900), snapshot(FRI_0900)) if c["rule"] == "OUT-01")
    r = svc.approve(FRI_0900, "out", c["key"], ["out"], None)
    assert r["toast"].startswith("OUT-01 approved")
    after = all_cards(Ctx(store=store, t=FRI_0900), snapshot(FRI_0900))
    assert not any(x["key"] == c["key"] for x in after)
    svc.undo(r["undo"])
    assert not store.tasks


def test_only_manager_changes_limits(store, monkeypatch):
    monkeypatch.setattr(svc, "get_store", lambda: store)
    with pytest.raises(svc.ActionError):
        svc.save_cfg(FRI_0900, "out", {"cut": 17})
    assert svc.save_cfg(FRI_0900, "mgr", {"cut": 17})["toast"] == "1 limit saved"
