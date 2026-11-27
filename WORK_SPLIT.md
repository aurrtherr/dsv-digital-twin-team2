# Who does what

Each feature has its own files, front and back, so people working on different features never edit the same file.

**How to use this page**
1. Pick a feature in Table 1 and put your name in the **Person** column. One person per feature.
2. Pick improvements in Table 2 that belong to your feature(s). Put your name there too, and set Status to *Doing*.
3. Only edit the files listed for your feature. If an improvement needs a file from another feature, message that feature's person first.
4. Merge into `main` through a pull request; the automatic check must be green.

Edit this file in the same pull request as your work (or straight on GitHub) so the table stays current.

## Table 1: Features

| # | Feature (screen) | What it does now | Backend file | Frontend file | Person |
|---|---|---|---|---|---|
| F1 | Operations overview | Start page for each role: headline numbers against target, rule cards to act on, projections to the cut-off, "look here first" | `backend/app/screens/shift.py` | `frontend/src/views/Shift.tsx` | |
| F2 | Packing priorities | Orders due today that are not fully packed, grouped; the planner proposes, the outbound supervisor approves | `backend/app/screens/atrisk.py` | `frontend/src/views/AtRisk.tsx` | |
| F3 | Tasks | Tasks created from approved cards, ticking parts done, proposals, dismissed cards, activity log | `backend/app/screens/tasks.py` | `frontend/src/views/Tasks.tsx` | |
| F4 | Outbound | Open orders grouped by lane, forwarder or country; overdue groups; order table | `backend/app/screens/outbound.py` | `frontend/src/views/Outbound.tsx` | |
| F5 | Inbound | Deliveries at the dock against their usual dock-to-receipt time; waiting list | `backend/app/screens/inbound.py` | `frontend/src/views/Inbound.tsx` | |
| F6 | Milkrun trace | Inbound LPN → outbound carton → order, with search (the only exact inbound-to-outbound link) | `backend/app/screens/trace.py` | `frontend/src/views/Trace.tsx` | |
| F7 | Trends | The week day by day: on-time share, handovers, receipts, weekend toggle | `backend/app/screens/trends.py` | `frontend/src/views/Trends.tsx` | |
| F8 | What-if | Volume +X% → people needed (about 505 lines per person per day, range shown) | `backend/app/screens/whatif.py` | `frontend/src/views/WhatIf.tsx` | |
| F9 | Data checks | Counts of records to review: no planned date, planned before created, stuck at dock, identical rows, missing fields | `backend/app/screens/checks.py` | `frontend/src/views/Checks.tsx` | |
| F10 | Rules | Catalogue of the 22 rules (IN, OUT, DQ, MGR) and whether each is live | `backend/app/screens/rules.py` | `frontend/src/views/Rules.tsx` | |
| F11 | Settings | Limits such as cut-off hour and thresholds; only the operations manager can change them | `backend/app/screens/settings.py`, defaults in `backend/app/state.py` | `frontend/src/views/Settings.tsx` | |
| F12 | Header timeline and replay | Timeline in the header, replay clock, "look back" mode | `backend/app/screens/timeline.py` | `frontend/src/components/Timeline.tsx` | |
| F13 | Order and ASN details, lookup | Pop-up with an order's lines and cartons or an ASN's lines; search by order or ASN number | `backend/app/screens/details.py` | `frontend/src/components/Dialogs.tsx`, `OrderTable.tsx` | |
| F14 | Shared core: data and rules | Excel → data build, replay snapshot, all rule logic, projections, KPIs, tests | `backend/app/engine.py`, `dataset.py`, `build_data.py`, `screens/common.py`, `backend/tests/` | `frontend/src/types.ts`, `api.ts` | |
| F15 | App shell and look | Sidebar, role switch, dark mode, colours and fonts, shared components and charts | none | `frontend/src/App.tsx`, `styles.css`, `components/common.tsx`, `charts.tsx`, `Kpi.tsx`, `Card.tsx` | |
| F16 | Setup, check and hosting | Automatic check on pull requests, README, getting the demo online | `.github/`, `README.md`, `backend/app/main.py`, `dev_server.py` | `frontend/vite.config.ts`, `package.json` | |

F14 is used by every screen, so its person reviews any change to those files.

## Table 2: Improvements

Status: *To do*, *Doing*, *Done*, *Waiting for DSV* (cannot finish until DSV answers that Round 2 question), *Decide first* (the team needs to agree whether to build it).

"Review notebook" means `notebooks/Feasure_Final_review_16Nov.ipynb`; § numbers are its section headings.

| # | Improvement | Feature | Where it comes from | Person | Status |
|---|---|---|---|---|---|
| I1 | Hourly receiving-queue chart (ASNs docked, not yet received, hour by hour) | F5 | Review notebook §2.3 *Receiving work: dock states, waiting time and P90* (already works there: tick "Show hourly receiving queue trend (24h)"; not in the app yet) | alicia | To do |
| I2 | Count "lines per ASN" on the 3-part key (ASN# + Ref Line# + Functional Packing), not Ref Line# alone | F14, F5 | Review notebook §2.3 ("ASN lines" column still counts Ref Line# only, see the 🟨 note) and §2 setup code (`NOT CHANGED, TO DO`) | Alicia | To do |
| I3 | Build rule DQ-04 "Contents mismatch" from the Milkrun content check (99.1% of 3,242 linked orders reconcile, 28 do not) | F14, F9, F10 | Review notebook §7.1 *Milk run quantity reconciliation by SKU and lot* | | Decide first |
| I4 | Stage timing: median and P90 for dock → receipt → order → handover | F7 | Review notebook §3.1 *Elapsed process timing for linked milk run units* | | To do |
| I5 | Hourly event activity chart and a 3-hour "recent events" list | F1 or F3 | Review notebook §4 *Event activity and recent history* | | Decide first |
| I6 | Switch between lateness definitions A–D (23.4%, 4.1%, 58.5%, 21.5%) | F7, F11 | Review notebook §6 *Handover performance and group analysis*; DSV Round 2 Q1 | | Waiting for DSV |
| I7 | Forwarder × country matrix of overdue orders | F4 or F7 | Review notebook §6 *Handover performance and group analysis* | | To do |
| I8 | Earlier-handover what-if next to the staffing what-if | F8 | Review notebook §9 *Historical what-if: earlier handover and readiness* |Ming Kai | Waiting for review |
| I9 | Show a SKU + lot match as a clearly labelled "possible link" for non-Milkrun flows (never as an exact trace) | F6 | Review notebook §5.1 *Optional experiment: suggesting an ASN from SKU, lot and receipt time* | | Decide first |
| I10 | Shipped-quantity totals, counting Qty Shipped once per order line | F4 | Review notebook §2.1 *Outbound shipping activity and outstanding work*; Issue 1 (currently option D: no units total); DSV Round 2 Q5 | | Waiting for DSV |
| I11 | Capacity what-if: change in the share of receipts to non-AS zones (HBS + SEQ) → location capacity needed | F8 | DSV B9 (their first suggested what-if) |Ming Kai | Waiting for Review |
| I12 | Use DSV's required shipment timing and forwarder cut-offs in OUT-02, OUT-03 and the "past planned day" logic | F14, F11 | DSV Round 2 Q1, Q2 | | Waiting for DSV |
| I13 | Use DSV's work per person and cost per extra person as the what-if baseline | F8 | DSV Round 2 Q3, Q4 |Ming Kai | Waiting for Review |
| I14 | Set default limits and rule owners from DSV's answers on alert thresholds and who acts | F11, F14 | DSV Round 2 Q7, Q8, Q9 | | Waiting for DSV |
| I15 | Order the cards by DSV's priority when several issues happen at once | F1, F14 | DSV Round 2 Q10 | | Waiting for DSV |
| I16 | Update the identical-rows check for the 148 outbound identical rows once DSV says whether they are real | F9 | DSV Round 2 Q6 | | Waiting for DSV |
| I17 | Handle Urgent Flag and blank Shipment Ref the way DSV confirms | F9 | DSV Round 2 Q13, Q14 | | Waiting for DSV |
| I18 | Run the app from a fresh clone (`npm install`, `uvicorn`) and fix any install or type errors | F16 | Not yet tested with a real install | | To do |
| I19 | Put the demo online (frontend on GitHub Pages via `.github/workflows/pages.yml`, backend on Render via `render.yaml`) | F16 | Team decision; check data privacy with Prof. Xu | aurrtherr | Doing |
| I20 | Match the screens to the Figma design: spacing, colours, wording | F15 | W10 Figma prototype | | To do |

Add new rows at the bottom with the next number (I21, I22, …) and the feature they belong to.
