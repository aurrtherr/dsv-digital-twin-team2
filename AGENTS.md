# Instructions for AI coding assistants

This repo is a student prototype of a warehouse "digital twin" for DSV (SUTD 40.318). Several people change it at the same time with AI help. Follow these rules so changes do not break each other.

## Before changing anything
- Ask which feature (F1–F16) or improvement (I1, I2, …) in `WORK_SPLIT.md` this work is for, unless the request already says.
- Only edit the files listed for that feature in `WORK_SPLIT.md`. If the change needs another feature's files, stop and say which file and why, so the person can check with its owner.
- Run `git pull` first so you work on the latest `main`.

## How the code is split
- `backend/` (Python) does every calculation: data build, replay snapshot, rules, projections, KPIs, what-if, shared state.
- `frontend/` (React + TypeScript) does layout and interaction only. Do not put business logic or calculations in `.tsx` files; add a field to the backend screen's output instead.
- One screen = one backend file in `backend/app/screens/<screen>.py` (function `v_<screen>`) + one frontend file in `frontend/src/views/<Screen>.tsx`. The JSON shape is typed in `frontend/src/types.ts`.
- Shared code (`backend/app/engine.py`, `dataset.py`, `build_data.py`, `screens/common.py`) is used by every screen. Change it only when the task is for F14, and keep existing function signatures working.
- New rules: add them in a new file (for example `backend/app/rules_inbound.py`) and wire them in with as small a change to `engine.py` as possible.

## Do not
- Do not edit `prototype/twin.html`. It is the frozen reference the app was ported from.
- Do not rewrite, reorder or reformat whole files. Change only the lines the task needs; large rewrites cause merge conflicts for everyone else.
- Do not rename or move existing files, functions or API fields unless the task asks for it.
- Do not commit `*.xlsx`, `*.csv`, `backend/state.json`, `node_modules/` or `frontend/dist/`.
- Do not change the data rules below.

## Data rules (DSV-confirmed, keep them)
- Add +8 hours to inbound Dock and GR times before comparing with outbound times.
- An inbound line is WMS ASN# + Ref Line# + Functional Packing.
- Count Qty Shipped once per Order Key + Order Line Number (it repeats on every carton row).
- The only exact inbound-to-outbound link is Milkrun: inbound LPN = outbound Carton ID.
- Times are whole minutes since 2026-08-01 00:00, rounded up.
- "Released after the planned date" is a signal to review, not proof of lateness.
- Rule IDs: IN-xx, OUT-xx, DQ-xx, MGR-xx. Keep existing IDs.

## Before finishing
1. Backend: `cd backend && pytest -q` must pass.
2. Frontend: `cd frontend && npm run build` must pass.
3. If a number shown in the app changed on purpose, say which number, old → new, and why, and update `backend/tests/test_engine.py`. If it changed by accident, fix the code.
4. Work on a branch named `<name>/<topic>`, commit with a clear message, push, and open a pull request. Do not push to `main`.
5. Update the Status of the improvement in `WORK_SPLIT.md`.

## Running locally
- Backend: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000`
- Frontend: `cd frontend && npm install && npm run dev`, then open http://localhost:5173
- The Excel files are not needed: `backend/app/data/twin_data.json` is committed.
- Course rule: only Claude, Gemini or Microsoft Copilot may be used with the DSV data.
