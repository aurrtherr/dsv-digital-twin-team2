"""Fallback server using only the Python standard library (no FastAPI needed).

Same routes as app/main.py. It can also serve the built frontend (frontend/dist), so the
whole twin runs with one command:

    python -m app.dev_server --port 8000 --static ../frontend/dist

Use app/main.py (FastAPI + uvicorn) for normal development; it adds /docs and validation.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import service as svc

STATIC: Path | None = None


def _int(v, default=None):
    if v in (None, ""):
        return default
    return int(v)


def _get(path: str, q: dict) -> dict:
    g = lambda k, d=None: q.get(k, [d])[0]
    if path == "/api/health":
        from .dataset import get_dataset
        D = get_dataset()
        return {"ok": True, "orders": D.n_orders, "asns": len(D.asns), "cartons": len(D.cartons)}
    if path == "/api/meta":
        return svc.meta()
    if path == "/api/frame":
        params = {k: g(k) for k in ("obBy", "obSel", "arSel", "traceQ", "tlPast", "tlNext")}
        params["obCap"] = _int(g("obCap"))
        params["trWk"] = g("trWk") in ("true", "1")
        params["wi"] = _int(g("wi"), 20)
        return svc.frame(int(g("t")), _int(g("at")), g("role", "out"), g("view", "shift"), params)
    if path.startswith("/api/order/"):
        return svc.get_order(int(path.rsplit("/", 1)[1]), int(g("t")), _int(g("at")), g("role", "out"))
    if path.startswith("/api/asn/"):
        return svc.get_asn(int(path.rsplit("/", 1)[1]), int(g("t")), _int(g("at")), g("role", "out"))
    if path == "/api/lookup":
        return svc.get_lookup(g("q", ""))
    if path == "/api/whatif":
        return svc.get_whatif(_int(g("wi"), 20))
    raise KeyError(path)


def _post(path: str, b: dict) -> dict:
    name = path.rsplit("/", 1)[1]
    t, role = b.get("t"), b.get("role")
    if name == "approve":
        return svc.approve(t, role, b["key"], b.get("assign", []), b.get("due"), b.get("note", ""))
    if name == "dismiss":
        return svc.dismiss(t, role, b["key"], b.get("reason", ""), b.get("details", ""))
    if name == "propose":
        return svc.propose(t, role, b["key"])
    if name == "tick":
        return svc.tick(t, role, b["id"], b["part"], b.get("done", True))
    if name == "task":
        return svc.new_task(t, role, b.get("title", ""), b.get("assign", []), b.get("due"), b.get("note", ""))
    if name == "seed":
        return svc.seed(t, role)
    if name == "cfg":
        return svc.save_cfg(t, role, b.get("values", {}))
    if name == "cfg-reset":
        return svc.reset_cfg(t, role)
    if name == "undo":
        return svc.undo(b.get("token") or {})
    if name == "reset":
        return svc.reset_demo()
    raise KeyError(path)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj) -> None:
        self._send(code, json.dumps(obj, ensure_ascii=False).encode())

    def do_OPTIONS(self) -> None:  # CORS preflight
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _dispatch(self, fn, *a) -> None:
        try:
            self._json(200, fn(*a))
        except svc.ActionError as e:
            self._json(400, {"detail": str(e)})
        except KeyError:
            self._json(404, {"detail": "Not found"})
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            self._json(500, {"detail": f"{type(e).__name__}: {e}"})

    def do_GET(self) -> None:
        u = urlparse(self.path)
        if u.path.startswith("/api/"):
            return self._dispatch(_get, u.path, parse_qs(u.query))
        if STATIC:
            f = (STATIC / u.path.lstrip("/")).resolve()
            if not str(f).startswith(str(STATIC.resolve())) or not f.is_file():
                f = STATIC / "index.html"
            self._send(200, f.read_bytes(), mimetypes.guess_type(str(f))[0] or "application/octet-stream")
            return
        self._json(404, {"detail": "Not found"})

    def do_POST(self) -> None:
        u = urlparse(self.path)
        n = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            return self._json(400, {"detail": "Bad JSON"})
        self._dispatch(_post, u.path, body)

    def log_message(self, fmt, *args) -> None:  # quieter logs
        pass


def main() -> None:
    global STATIC
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--static", default=None, help="folder with the built frontend (frontend/dist)")
    a = ap.parse_args()
    STATIC = Path(a.static) if a.static else None
    print(f"Twin backend on http://localhost:{a.port}" + (f" (serving {STATIC})" if STATIC else ""))
    ThreadingHTTPServer(("", a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
