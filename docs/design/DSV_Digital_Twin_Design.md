# DSV Digital Twin: detailed design (concept, architecture, user journeys, key interactions)

_Team 2 draft, 11 Nov 2026. Built on the IMDA "Digital Twin: Playbook for Enterprises", the course addendum (7 Nov 2026), the DSV brief, and the team's Assumption Log, Q&A log and analysis notebook. Every number comes from the team's analysis of the two reports (all times on the outbound clock, inbound +8 h). Figma mockups: see "Figma file" at the end._

> **Note (23 Nov 2026):** written before DSV's 11 Nov follow-up answers and the midterm. Since then: "late" is shown as "released after the planned date" (a signal to review), the rule names follow the prototype (IN, OUT, DQ, MGR), and the staffing what-if uses a typical weekday (24 people today, 29 at +20%, range 27–32). See `docs/team-doc/` for the current logs.

**Status key used in this document:** Fact (counted from the data) · Confirmed (DSV or the course said so) · Working (our choice, pending DSV) · Proposed (a design decision for the team to approve).

---

## 0. Design in one page

| | |
|---|---|
| **Name** | DSV Warehouse Twin: "Shift Command" |
| **Vision (IMDA style: short, actionable, measurable)** | Give a DSV shift supervisor one view of what was received, what is waiting to ship and what is past its planned date, so they can act on the right orders before the planned day ends. |
| **Twin type (IMDA 1.1)** | A thin **process twin** (order-to-delivery events), because the data is event records, not machine signals. |
| **Core question (DSV brief)** | What is happening now, why, and what should we do next? |
| **Maturity target (IMDA levels / DSV levels)** | Visibility and Diagnosis built and demonstrated on real data; Prediction as one what-if prototype; Recommendation as explainable rules with a human approving every action. |
| **Rollout framing (IMDA two-stage)** | Stage 1 "Monitor and establish baseline" is what the data supports. Stage 2 "Predict and simulate" is a prototype only. IMDA asks for 4 to 8 weeks of stable data before Stage 2; we have about one week, so Stage 2 is labelled proof of concept. |
| **Deliverable (addendum)** | A design (this document) plus mockups (Figma) plus a small working demo of one or two mandatory components. Not an end-to-end system. |

---

## 1. Design: concept

### 1.1 Problem and why a twin

DSV's own words: "We have data everywhere, but we do not always have the information needed to make decisions quickly." Supervisors consult separate systems for order status, receipts and traceability. In our extract the symptoms are concrete:

- **Fact:** 23.4% of 18,965 orders with a plan date were released on a later calendar day than planned (25.5% in the fully covered window, planned 17 to 23 Aug). Under other definitions of "late" the figure ranges from 5.6% to 56.8%, so the definition must be agreed with DSV (D1, pending).
- **Fact:** only Milkrun cartons can be followed from receipt to release: 5,564 cartons, which is 70.7% of the 7,869 outbound Milkrun cartons and 15.9% of all 35,092 outbound cartons. The other flows share no ID between the reports (Confirmed, DSV A2).
- **Fact:** the two systems' clocks differ by 8 hours. After adding 8 h to inbound times, the Cyclone scan falls 0 to 39 seconds before goods receipt on all 5,564 joined cartons (Confirmed, timestamp note).

A twin helps because it puts one corrected, linked, time-aware view over both reports and shows the reason next to every flag.

### 1.2 Fit check (IMDA 1.3 "Is a digital twin for you?")

| IMDA criterion | Our situation | Verdict |
|---|---|---|
| Material cost impact | Late release and unlinked flows affect delivery reliability for a large client base | Good fit |
| Repeatable and stable process | Event order is 100% consistent: Normal = order created, packing confirmed, cargo released; Milkrun = Cyclone scan, order created, cargo released | Good fit |
| Accessible operational data | Two Excel reports plus a glossary, pre-anonymised, no NDA | Good fit |
| Data quality and ownership | DSV owns the data and has answered Round 1; seven questions still pending | Partly: needs a named DSV data owner in production |
| Stable baseline | About one week only; outbound lists only released cargo | **Weak: so Stage 2 is a prototype** |
| Missing signals | No labour, equipment, capacity or inventory snapshots | Why labour and inventory optimisation are out of scope |

### 1.3 Scope (addendum, mandatory)

| # | Core scope item | Design answer | Screen |
|---|---|---|---|
| 1 | Historical event-replay view | Time slider over a unified event table; counts and lists at any chosen moment | S2 |
| 2 | Visibility at ASN, order, line and carton level | Two drill paths: inbound ASN > line; outbound order > line > carton | S3, S4 |
| 3 | Planned-date and quantity reconciliation | Planned vs released by day; summed received vs expected per ASN line | S5 |
| 4 | Milkrun handling-unit traceability | Carton page joined on inbound LPN = outbound Carton ID, with coverage shown | S6 |
| 5 | One limited prediction or what-if | Volume what-if: if volume rises X%, how many people are needed (baseline 20), as a ratio estimate | S7 |
| 6 | Explainable rules-based recommendations | Rule cards that show trigger, evidence, role and action | S1, S8 |

**Out of scope (addendum), and how the design stays clear of it:** cycle-time, bottleneck and exception analysis (we show plan vs actual and event replay, never "where the time goes"); real-time integration (replay of an extract); full inventory reconstruction; labour and equipment optimisation (the what-if is a simple ratio, not a roster); 3D modelling; autonomous recommendations (every action needs a person's approval).

### 1.4 KPIs and baselines (IMDA: "set measurable KPIs and baselines")

Baselines are from the one-week extract and are meant to be re-measured, not treated as targets. Targets are for DSV to set.

| KPI | Level | Baseline | Status |
|---|---|---|---|
| Orders released on the planned day | Order | 75.5% (whole extract) | Working definition D1 |
| Late-release rate (later calendar day than planned) | Order | 23.4% whole extract; 25.5% covered window | Working; pending Q6 |
| Open orders past planned date at time t | Order | e.g. 959 at 18 Aug 12:00; 913 at 20 Aug 12:00; 223 at 22 Aug 12:00 | Fact (left side of window is reliable) |
| ASN lines reconciled (summed received = expected) | Line | 36,533 of 36,533 | Confirmed (DSV A5), verified |
| Milkrun cartons traceable end to end | Carton | 5,564 of 7,869 (70.7%) | Fact |
| Forwarder concentration of lateness | Forwarder | 9 of 42 forwarders (30+ orders) are 90%+ late and hold 48.7% of late orders | Fact; show as a ranking, never as a cause |

### 1.5 How the twin serves DSV's goals

Each screen names a DSV goal (from `DSV_Strategy_Alignment.md`): Technology (one view across WMS exports), Operations (productivity with data and AI), Continuous improvement (find mismatches and redundancy), Visible costs (see where the work sits), Leadership (supervisors trust and act on clear rules). A feature that serves none is cut.

---

## 2. Design: architecture

### 2.1 Layers (IMDA reference architecture, mapped to our prototype)

```
 USER INTERFACE   Shift Command: overview, replay, ASN/order/carton drill-down,
                  Milkrun trace, reconciliation, what-if, action queue
        ▲
 TWIN & INTELLIGENCE   Analytics: rules engine (R1 to R5), what-if calculator, inferred-link tagging
        ▲              Twin model: entities, states, KPI logic, evidence labels
        ▲
 DATA CONNECTIVITY     Ingest, clean (types as text, IDs keep leading zeros), align clock (+8 h),
                       build keys, write canonical tables
        ▲
 DATA                  Daily_Inbound_Report.xlsx · Daily_Outbound_Report.xlsx · Data_Glossary.xlsx
                       (static context = glossary, asset/zone/forwarder codes;
                        dynamic events = timestamps; enterprise data = orders, ASNs)
```

IMDA says the process-optimisation twin should invest most in the **data layer**. We follow that: most of the effort is clock alignment, keys and honest coverage labels, not visuals.

### 2.2 Layer by layer

| Layer | What it does here | Key design choices | Playbook link |
|---|---|---|---|
| **Data** | Holds the three source files unchanged; the extract is a snapshot, so it is a replay source, not a live feed | Raw files are never edited; work on copies | 3.2 data readiness: static + dynamic + enterprise data |
| **Data connectivity** | Python notebook ingests and writes tidy tables (notebook Block 23: `events.csv`, `carton_journey_milkrun.csv`, `orders_lateness.csv`, `asn_line_reconciliation.csv`, `forwarder_summary.csv`, `rules.csv`, `time_slider_snapshots.csv`) | Read every column as text to keep leading zeros; add 8 h to inbound Dock and GR once, in one constant; inbound line key = WMS ASN# + Ref Line# + Functional Packing; Milkrun link key = inbound LPN = outbound Carton ID | "Standardise timestamps, units and asset IDs" |
| **Twin model** | Represents the warehouse as entities with states and KPI logic | See 2.3 | "Represent states; define KPIs and thresholds; track root cause across assets" |
| **AI / analytics** | Rules engine, reconciliation, one what-if calculator, optional inferred links | Rules are explicit tables with thresholds in one place; AI (Claude, Gemini or Copilot only, per the addendum) helps *build* and *explain*, but no model makes a decision | 3.2 AI governance: testing, versioning, human-in-the-loop |
| **User interface** | Role-based views, time slider, drill-down, action queue | Show each role only what it needs; evidence labels on every number | 3.1 Employees: role-specific views |

### 2.3 Twin model (entities, states, relations)

| Entity | Key | States / events it carries | Source |
|---|---|---|---|
| **ASN** | WMS ASN# | Docked, goods received (GR) | Inbound |
| **ASN line** | ASN# + Ref Line# + Functional Packing | Expected qty, summed received qty, reconciled / not reconciled | Inbound |
| **Handling unit (Milkrun)** | LPN = Carton ID | Docked, received, Cyclone scan, order created, released | Both (exact link) |
| **Order** | Order Key | Created, planned date, released; late / on time / early / no plan | Outbound |
| **Order line** | Order Key + Line | Qty shipped | Outbound |
| **Carton** | Carton ID | Normal: packing confirmed. Milkrun: Cyclone scan | Outbound |
| **Forwarder** | Default and Final Forwarder code | Order counts, late counts (a ranking only) | Outbound |

**Event table (the core data structure).** One long table: carton or order, event name, timestamp (outbound clock), flow. The time slider and the carton timeline are both queries on it (114,889 events for 34,587 cartons in the current build).

**Evidence labels (IMDA "trusted data" principle).** Every number or link carries one of: `Exact` (key match), `Inferred` (SKU + vendor lot + latest receipt, 90.7% right on the Milkrun back-test, Normal flow not validated), `Assumed` (working definition, pending DSV), `Out of window` (received before the extract, or not yet released at its end).

### 2.4 Rules engine (explainable by design)

All thresholds sit in one table so DSV can change them. Rule text and reason are shown to the user.

| ID | Trigger | Suggested action | Role | Status |
|---|---|---|---|---|
| R1 Planned-date risk | Order still unreleased at 18:00 on its planned day | Confirm pickup time with the forwarder; escalate if none | Outbound lead | Working. At 18:00: 10,419 orders flagged, 39% finally late (21% to 67% by planned day); 21:00 is 81% precise but leaves little time to act |
| R2 Forwarder backlog | Forwarder has 20 or more orders unreleased and past planned date | Review the forwarder's handover plan | Outbound lead | Working; placeholder threshold |
| R3 Quantity mismatch | Summed Qty Rcvd differs from Qty Exp for an ASN line (key includes Functional Packing) | Check with receiving; confirm pack types | Inbound supervisor | Working. **Currently 0 of 36,533 lines trigger**; the rule is shown so a refreshed extract would flag them. When a difference counts as an issue is pending with DSV |
| R4 Data sanity | Planned date earlier than order creation | Label "possibly urgent"; no action | None (information) | Confirmed reason (DSV A4); 181 orders |
| R5 Milkrun trace gap | Milkrun carton with no matching receipt in the extract | Label "receipt outside window"; no alert | None (information) | Working (A3); 2,305 outbound cartons |

Not used: the Urgent Flag (it is "Y" on every outbound row, so it cannot prioritise) and any "forwarder changed" alert (DSV A6: normal, not an exception).

**Human-in-the-loop (IMDA).** A rule *proposes*; a named role *accepts, defers or dismisses*, with a reason. The action log is the audit trail. Nothing changes a schedule or a setpoint automatically.

### 2.5 What-if calculator (the one prediction use case)

DSV suggested two (B9). We pick **(b) volume and people** for the prototype and keep **(a) putaway-zone capacity** as the documented extension. Reason: (b) needs only numbers we have plus the 20-person baseline DSV gave; (a) would need location capacity data we do not have.

| Step | Value | Basis |
|---|---|---|
| Workload unit | ASN lines received (Functional Packing in key) + order lines released, per day | Fact |
| Week 17 to 23 Aug | 32,844 inbound lines + 37,845 outbound lines = 70,689 | Fact |
| Average day | 10,098 lines → about 505 lines per person per day with 20 people | Assumption: 20 people cover both inbound and outbound (to confirm with DSV) |
| Peak day (18 Aug) | 15,349 lines, 1.52 times the average | Fact |
| Estimate at +X% volume | People = 20 × (1 + X%) on an average day; × 1.52 if staffed for the peak day | Constant-productivity ratio, not an optimiser |

| Volume change | Average-day people | Peak-day people |
|---|---|---|
| +0% | 20.0 | 30.4 |
| +10% | 22.0 | 33.4 |
| +20% | 24.0 | 36.5 |
| +30% | 26.0 | 39.5 |
| +50% | 30.0 | 45.6 |

Presented as a prototype. It is not a forecast, and not labour optimisation. Caveats to show on screen: one week of data, weekend days are low (release is batched, Monday-heavy), and productivity is held constant.

### 2.6 Governance, security and build approach (IMDA 3.2 step 3)

| Area | Design position |
|---|---|
| Data governance | Named owners (proposed): DSV for the reports, the team for the derived tables. Role-based views. Quality checks built in: ID shape, blank-rate and coverage banners. Auditability: the notebook's 28 self-checks fail loudly if headline numbers change |
| AI governance | Only Claude, Gemini or Microsoft Copilot on the data (addendum). No autonomous action. Rules are inspectable. Back-test shown with the rule (R1 precision table). Keep a log of where AI was wrong (course reflection) |
| Security and privacy | Data is pre-anonymised by DSV; no NDA. In production: role-based access, encryption in transit and at rest, IT/OT separation, PDPA-aligned handling. Out of prototype scope but listed so DSV sees the path |
| Build approach (IMDA configurable vs bespoke) | Prototype is bespoke and light (notebook plus a small UI). For a production path we recommend a **configurable platform** with connectors to WMS/ERP: faster, cheaper, and enough for rules and simple what-ifs |
| Deployment | Prototype runs on an extract. Production would need a streaming feed (out of scope) |

---

## 3. Design: user journeys

### 3.1 People

| Role | Needs (IMDA: show each role only what it needs) | First check (DSV B7) |
|---|---|---|
| **Inbound supervisor** | Is everything expected on today's ASNs received and reconciled? | Shipment reference, ASN and line |
| **Outbound shift lead** | Which orders will miss their planned day, with which forwarder, to which country? | Country code and final forwarder |
| **Operations manager** | How is the week going, what do we change if volume grows? | Trends, what-if |
| **Data owner (DSV IT/analyst)** | Can I trust these numbers, what are the assumptions? | Data-quality and assumptions panel |

### 3.2 Journeys

**J1. Inbound supervisor: start-of-shift check** (S1 → S3)
1. Opens Shift Command; overview shows ASNs received since the last shift and reconciliation status.
2. Searches or filters by shipment reference. *System:* ASN list with line counts and status chips.
3. Opens an ASN. *System:* lines with Functional Packing, expected vs summed received, reconciled chip. Split pack types (e.g. ITR and ITY on one Ref Line#) are shown as separate lines, as DSV defined.
4. Blank LPN shows "not yet packed", not "missing".
5. Success: the supervisor sees "all lines reconciled" or the exceptions (R3) in under a minute, without opening another system.

**J2. Outbound shift lead: act on a planned-date risk** (S1 → S4 → S8)
1. Overview lists orders unreleased and past or near planned date, grouped by country and final forwarder (DSV B7).
2. At 18:00 rule R1 raises a card: "Order 0000924401 · HK · Final forwarder 013 · planned 20 Aug · not released · Rule R1".
3. Opens the order. *System:* timeline (created, packed, planned, now), cartons, lines, forwarder history, rule evidence ("39% of orders unreleased at 18:00 end up late").
4. Chooses *Accept* (assigns the action, e.g. confirm pickup with forwarder), *Defer* or *Dismiss*, with a reason.
5. Success: the action is logged; the order leaves the queue when released.

**J3. Anyone: trace a Milkrun carton** (S6)
1. Types a carton ID or LPN in the global search (example `4038421004001`).
2. *System:* five-step trace: docked 20 Aug 08:09 · received 09:00:54 · Cyclone scan 09:00:48 · order created 09:28:24 · released 21 Aug 18:15:50, with an `Exact` badge and the ASN (0000032011, ref DSC7959).
3. Planned date 21 Aug, released 21 Aug: on time.
4. If the carton is not found: the page explains why (not Milkrun, so no shared ID; or received before the extract: "receipt outside window") and offers the separate inbound and outbound views.
5. Success: a question like "where is this carton?" is answered with evidence and a clear coverage statement.

**J4. Inbound supervisor or analyst: investigate a mismatch** (S5)
1. Opens Reconciliation; sees planned vs released by day and quantity status by ASN.
2. Clicks a day or a forwarder bar. *System:* the orders behind it, each with its plan, release and rule label (late, on time, early, possibly urgent).
3. Opens an ASN line with a difference (none in the current extract; the screen shows the empty state "36,533 of 36,533 lines reconcile" and how the check works).
4. Success: every flag opens to rows, and every row shows its rule and reason.

**J5. Operations manager: ask "what if volume grows?"** (S7)
1. Opens What-if; baseline is pre-filled: 20 people, 10,098 lines per day.
2. Moves the volume slider to +20%. *System:* average-day people 24.0, peak-day 36.5, with assumptions listed beside the result.
3. Saves the scenario with a note, or resets.
4. Success: a defensible number with its assumptions visible, labelled "prototype".

**J6. Manager: replay a past moment** (S2)
1. Drags the time slider to 20 Aug 18:00.
2. *System:* orders awaiting release, how many are past planned date, ASNs received so far, with the event log scrolled to that moment.
3. Steps forward hour by hour to see the build-up and the release waves.
4. Success: "what did the floor look like then?" without a spreadsheet.

---

## 4. Design: key interactions

### 4.1 Interaction specification

| # | Interaction | Behaviour | Data / rule behind it | Why (playbook / DSV) |
|---|---|---|---|---|
| I1 | **Time slider** | Drag or step by hour; all counts, lists and the event log recompute for time t. Play/pause for replay | `snapshot(t)` over the event table | Core scope 1; "state at time t" |
| I2 | **Drill-down** | Overview tile → list → detail. Inbound: ASN → line. Outbound: order → line → carton. Breadcrumb always shown | Keys in 2.3 | Core scope 2; IMDA "drill from plant to component" |
| I3 | **Global search** | One box accepts ASN, shipment ref, order key, carton ID or LPN and routes to the right page | ID shapes (13-char Carton ID; 10-digit ASN) | DSV B7 first checks |
| I4 | **Evidence badge** | Every number and link shows Exact, Inferred, Assumed or Out of window; click shows the basis | Section 2.3 | IMDA data governance; honesty about the 16% coverage |
| I5 | **Rule card** | Shows rule ID, trigger, evidence rows, precision from back-test, suggested action, role | Rules table 2.4 | Addendum: explainable |
| I6 | **Accept / defer / dismiss** | Person chooses, adds a reason; logged with time and role; nothing automatic | Action log | IMDA: human-in-the-loop first |
| I7 | **Threshold editor** | Manager changes the cut-off (default 18:00) and sees flagged count and precision change before saving | Back-test table | Thresholds are working assumptions |
| I8 | **What-if sliders** | Volume %, baseline people, peak vs average basis; result and assumptions update live | Section 2.5 | DSV B9 |
| I9 | **Coverage banner** | Where a view cannot be complete, a banner says so ("Outbound lists released cargo only; recent days understated") | Assumption A5 | IMDA data readiness |
| I10 | **Role switcher** | Inbound / Outbound / Manager / Data owner changes the default landing view and the first filter | DSV B7 | IMDA role-based views |
| I11 | **Assumptions panel** | One click opens the live Assumption Log entries relevant to the screen, with status | Assumption Log | Course: state working assumptions |
| I12 | **Persistent replay control** | A compact "Replay: Thu 20 Aug 18:00" control with back/forward 1 h sits in the top bar of every screen, so the viewed moment is never ambiguous. Arrow keys step 1 h; Shift + arrow steps 6 h | Same `snapshot(t)` | Critique: replay mode was only in the subtitle |
| I13 | **View as table** | Every chart has a "View as table" toggle showing the same numbers in a real table, including the selected bar's values | Same data as the chart | WCAG 1.4.1, 2.1.1; supervisors who prefer tables |
| I14 | **Focus and keyboard** | Visible 2 px focus ring on every interactive element; rows, chips and bars are focusable; changes in counts after a slider move are announced politely | Component states | WCAG 2.4.7, 2.1.1, 4.1.3 |

### 4.2 States to design for

- **Empty** (no lines to reconcile; no rules fired).
- **Edge of window** (before 17 Aug 03:07 or after 24 Aug 21:40): warn that counts are partial.
- **Not found** (carton in no report; carton not Milkrun).
- **Pending DSV** (definition of late, thresholds): show "Working definition" chip.
- **Low confidence** (inferred link): dashed outline, never styled as exact.

### 4.3 Visual and accessibility notes

- Status uses colour plus text and icon (never colour alone). Orange ("action") and amber ("warn") are almost the same brightness (1.19:1), so they must also differ by icon and label, and by pattern in charts.
- Times always show the clock used ("outbound clock, inbound +8 h").
- One accent colour for "needs action"; neutral for everything else; a distinct dashed style for inferred or assumed values.
- Tables first for supervisors; charts only where they help (planned vs released by day, forwarder ranking, load by hour). Every chart has a table view (I13).
- Colour tokens after the accessibility review: `ok` #166A4C (5.69:1 on its soft fill), `action` #B23A0A (5.18:1 on its soft fill), new `control-border` #7C8BA3 (3.45:1 on white) for inputs, filters and slider tracks; the pale `border` #DCE2EC stays for cards only.
- Minimum text size 12 px; controls at least 32 px high on desktop and 44 px on touch; at 800 px wide or less the sidebar collapses to a menu and tables scroll sideways (reflow at 200% zoom).
- Design rationale (DSV goal, maturity level) lives in an annotation layer, not in the product screen.

---

## 5. Screens in the Figma file

| ID | Screen | Role | Core scope | Journey |
|---|---|---|---|---|
| S1 | Shift Command (overview + action queue) | All | 1, 2, 6 | J1, J2 |
| S2 | Event replay (time slider) | Manager, outbound lead | 1 | J6 |
| S3 | Inbound: ASN and line view | Inbound supervisor | 2, 3 | J1 |
| S4 | Outbound: order and carton view | Outbound lead | 2, 3 | J2 |
| S5 | Reconciliation (planned vs released; quantity) | Analyst, supervisors | 3 | J4 |
| S6 | Milkrun carton trace | All | 4 | J3 |
| S7 | What-if: volume and people | Manager | 5 | J5 |
| S8 | Rule card and action log | Outbound lead, inbound supervisor | 6 | J2 |

---

## 6. Check against the IMDA readiness checklist (3.3)

| Checklist block | Status |
|---|---|
| Define use case: 1 to 2 pain points, one-sentence use case, scope, KPIs | Done in 0, 1.1, 1.4. Targets pending with DSV |
| Check data readiness: availability, integration, security, quality and ownership | Availability and quality verified in the notebook. Integration: extract only. Ownership: DSV to name an owner |
| Governance and security | Section 2.6; production items listed, not built |
| Two-stage rollout | Stage 1 evidence = overview, replay, drill-down, reconciliation, trace. Stage 2 = what-if prototype and rules. Gap: IMDA's 4 to 8 weeks of stable data |

## 7. Risks and open items

| Risk / open item | Effect on the design | Next step |
|---|---|---|
| Definition of "late" pending (Q6) | KPI and R1 labels are "Working definition" | Ask DSV at consultation; keep one config value |
| KPIs, alert triggers and supervisor actions pending (DSV asked what we are trying to solve) | Rules and actions are our proposals | Re-send with this design as the answer: "supervisors need to know which orders will miss the planned day, in time to act" |
| Whether Cyclone scan is the sorter scan and all cartons pass it (T3) | Milkrun trace labels the event "Cyclone scan" | Confirm |
| 20 people cover inbound and outbound? | What-if headline depends on it | Confirm at consultation |
| Outbound lists released cargo only (A5) | Recent-day counts understated; banner I9 | Ask DSV whether a snapshot of unreleased orders exists |
| One week of data | Prediction stays a prototype | State it on every what-if screen |
| 16% of cartons traceable | Trace is Milkrun only | Always show coverage; label Normal links inferred |
| Possible conflict: DSV timestamp note mentions cycle-time and bottleneck; addendum excludes them | Design shows plan vs actual and replay only | Keep the working decision (6 Nov) |

## 8. Figma file

File: https://www.figma.com/design/D6I1seUCiehF70EwfCAAj3 ("DSV Digital Twin: Shift Command (Team 2)"), page "Screens (S1-S8)". Built from real extract numbers, with colour tokens as Figma variables and reusable Chip and KPI tile components.

**State of the file (11 Nov 2026):**
- S1 to S6 are built and were checked visually. S3 and S5 had small fixes (column width, a clipped line, thousands separators) that were applied but not re-checked.
- S7 (What-if) and S8 (Action log and rules) are built but were **not checked visually**: the Figma Starter plan's tool-call limit was reached first. Open them and look for clipped text.
- The first page, "Concept, architecture, journeys", is **empty**. The architecture layers (section 2.1) and the six journeys (section 3.2) exist only in this document. They still need drawing in Figma (a FigJam board or frames).
- The Starter plan allows 3 pages and a limited number of MCP calls, so continuing needs a new quota window or a paid plan, or a team member building the page by hand from sections 2.1 and 3.2.
- The what-if (S7) uses DSV suggestion B9(b). If the team prefers B9(a), S7 changes.
- The action log entries on S8 are illustrative and labelled so; they are not real DSV decisions.
- Keep the Figma file and this document in step when a screen or rule changes.
- **Review fixes (section 9) are written into this document but were not applied to Figma**: the Figma tool-call limit was still reached when I tried. Section 9 lists each edit so it can be done by hand or re-run when the limit resets.

---

## 9. Review fixes: accessibility audit and design critique (11 Nov 2026)

Audit standard: WCAG 2.1 AA. Contrast was measured from the palette values; S1 to S6 were viewed; S7 and S8 were not viewed (Figma limit). Keyboard and screen-reader items are requirements for the demo build.

**Status key:** ✅ done in this document · ⬜ still to apply in Figma (edit listed).

### 9.1 Accessibility fixes

| # | Finding | Severity | Fix | Spec | Figma edit to make |
|---|---|---|---|---|---|
| A1 | Control borders (search, filters, slider track) at 1.30:1 | Critical | New `control-border` #7C8BA3 (3.45:1) for controls | ✅ 4.3 | ⬜ Add variable; apply to "Search" strokes, filter chips, slider tracks on S1 to S8 |
| A2 | S5 stacked bars rely on colour; orange and amber are 1.03:1 | Critical | White 2 px gaps, counts in each row label ("4,057 orders · 3,398 on day · 627 late"), table view, pattern for 2+ days late | ✅ 4.1 I13, 4.3 | ⬜ Add strokes and extend the row labels on S5 |
| A3 | Chip text: green 4.30:1, orange 4.47:1 | Major | `ok` → #166A4C (5.69:1), `action` → #B23A0A (5.18:1) | ✅ 4.3 | ⬜ Change the two variable values |
| A4 | Greyed log rows at 55% opacity (2.2 to 3.7:1) | Major | No opacity. Italic text plus an "after this moment" chip | ✅ this table | ⬜ S2 event log: remove opacity, add chip |
| A5 | S2 bars distinguished by colour and opacity only | Major | Value label on the selected bar; "View as table" | ✅ I13 | ⬜ Add label and button on S2 |
| A6 | No focus states | Major | 2 px `primary` ring, 2 px offset, on every interactive component | ✅ I14 | ⬜ Add focus variants to Button, Chip (filter), Table row, Nav item |
| A7 | Fixed 1440 layout; no reflow at 200% | Major | Add an 800 px layout: collapsed sidebar menu, stacked tiles, tables scroll | ✅ 4.3 | ⬜ Draw one narrow frame for S1 |
| A8 | Filters look like static chips | Major | Dropdown chevron and hover, open and selected states; named as buttons | ✅ I14 | ⬜ Add chevron to filter chips on S3 and S4 |
| A9 | Text at 10 and 11 px | Minor | Minimum 12 px | ✅ 4.3 | ⬜ Raise chart labels, chips and table headers to 12 px (Chip component first) |
| A10 | Buttons about 26 px high | Minor | 32 px minimum desktop, 44 px touch | ✅ 4.3 | ⬜ Button padding 5 → 8 px |
| A11 | Bars open orders by click only | Minor | Focusable bars and a linked table row | ✅ I13, I14 | covered by A5 and A6 |

**Build requirements for the demo (not testable until it exists):** landmarks (header, nav, main); real table markup with header cells; a text summary per chart; arrow-key control of the time slider; a polite live region that announces updated counts; page language and titles; visible focus order that follows reading order (top bar, title, tiles, body left to right).

### 9.2 Design critique fixes

| # | Finding | Fix | Spec | Figma edit to make |
|---|---|---|---|---|
| C1 | Replay mode shown only in the subtitle | Persistent replay control in every top bar (I12) | ✅ 4.1 | ⬜ Add a "Replay: Thu 20 Aug 18:00, back / forward" control to all eight top bars |
| C2 | "At risk today (R1)" tile has the same weight as the others, not linked to the queue | Make it the lead tile (2 px `action` outline) and have it filter the action queue | ✅ this table | ⬜ S1 tile 3 |
| C3 | Rule cards R3 (0) and R4 (information) take equal space with R1 and R2 | Collapse to one line: "No action: R3 quantity (0 lines), R4 planned before created (181, information only)" | ✅ this table | ⬜ S1: delete two cards, add the line |
| C4 | "Reconciled" and "not yet packed" chips repeat on every row (S3) | Show a chip only when a row differs from the norm; state the norm in the column header ("Status (exceptions only)", "LPN (blank = not yet packed)") | ✅ this table | ⬜ S3: remove chips, rename headers |
| C5 | S5 forwarder chart: eight bars at about 100% say little | Rank by number of late orders (112: 783, 044: 395, 013: 313, 080: 170, 096: 146, 018: 99, 090: 72, 069: 70); bar length = late orders | ✅ this table | ⬜ S5 right card |
| C6 | Two late-rate tiles invite confusion | Headline the covered-window figure (25.5%); label the whole-extract figure (23.4%) as edge-biased and secondary | ✅ this table | ⬜ S5 tiles 2 and 3 |
| C7 | S6: scan (09:00:48) appears after receipt (09:00:54), explanation at the bottom | Put the explanation inline on step 3 | ✅ this table | ⬜ S6 step 3 text |
| C8 | Coverage repeated in the top bar and a banner | Keep the top-bar coverage control; the S1 banner keeps only the traceability statement | ✅ this table | ⬜ S1 banner text |
| C9 | Design annotations ("DSV goal", "Level 1 Visibility") shown as if product UI | Move to an annotation layer with a dashed outline | ✅ 4.3 | ⬜ Restyle the "Tags" rows on all screens |
| C10 | Subtitle size 13 px on S1, S2 and 12.5 px elsewhere | One size: 13 px | ✅ this table | ⬜ S3 to S8 subtitles |
| C11 | Only colours are tokens; cards, buttons, table rows, rule cards are not components; Chip uses fill overrides | Componentize Card, Button, Table row, Rule card, Nav item; make Chip a variant set (ok, action, warn, primary, muted); add spacing, radius and text-style tokens | ✅ this table | ⬜ Rebuild when quota allows |
| C12 | S7 "Baseline people" handle sits at 18 on a 10 to 30 scale while the value reads 20 | Handle at the midpoint | ✅ this table | ⬜ S7 second slider |

### 9.3 Still not checked
S7 and S8 visually; S3 and S5 after their earlier fixes; real keyboard and screen-reader behaviour (nothing built yet); contrast in Figma itself (measured from palette values).
