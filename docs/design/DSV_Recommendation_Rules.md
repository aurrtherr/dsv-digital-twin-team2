# DSV Recommendation Rules: full catalogue (draft)

_Team 2 draft, 11 Nov 2026. Extends section 2.4 of `DSV_Digital_Twin_Design.md` (rules R1 to R5) to 26 rules, grouped by the user who acts on them. Every count below was recomputed from the two raw reports (outbound clock; inbound +8 h). Rule IDs here replace R1 to R5: R1 is now O1, R2 is O5, R3 is I1, R4 is O3, R5 is M6._

> **Note (23 Nov 2026):** the prototype (`prototype/twin.html`) later renamed these rules to IN-xx, OUT-xx, DQ-xx and MGR-xx. Use the prototype's names in new work; this file is kept as the design record.

**How to read this.** Each rule is explainable: a trigger, the evidence shown, a suggested action and a role. A rule only proposes. A person accepts, defers or dismisses it, with a reason (human in the loop, no autonomous action).

**Status:** Working (data-backed, our choice, pending DSV on the definition) · Proposed (sensible, but needs a DSV or scope check first) · Info (a label, not an alert) · Hold (do not ship until DSV answers).

**Severity:** High (act today) · Medium (review this shift) · Low or Info (label or weekly review).

**Counts are back-tests on one week of data.** The outbound file lists only released cargo, so we know in hindsight which orders were finally late; a live twin would not. Precision means: of the orders the rule flagged, the share that were finally released after the planned day (working definition D1).

---

## 1. Outbound shift lead (country code and final forwarder, DSV B7)

| ID | Rule | Trigger | Evidence shown | Suggested action | Sev. | Status | Back-test in the extract |
|---|---|---|---|---|---|---|---|
| **O1** | Planned-day cut-off risk (was R1) | Order created, not yet released at 18:00 on its planned day | Planned day, created time, forwarder, country, cut-off used | Confirm today's pickup with the forwarder; escalate if none | High | Working | 10,419 flagged; 39.2% finally late; 92.0% of late orders caught. Cut-off sensitivity: 12:00 flags 17,310 (22.0% precise); 15:00 flags 16,254 (24.2%); 21:00 flags 5,186 (81.0%) |
| **O2** | Late-created order | Order created after 12:00 on its planned day | Created time vs planned day | Tell the planner now; confirm the earliest possible pickup, or re-plan | High | Proposed | 659 orders; 95.4% finally late |
| **O3** | Planned before created (was R4) | Planned date is on an earlier day than creation | Both dates | Label "possibly urgent" (DSV A4); no escalation | Info | Confirmed reason | 181 orders; all 181 released late |
| **O4** | Past-plan backlog at start of shift | At 12:00, order unreleased and its planned day was an earlier day | List grouped by forwarder and country, oldest first | Work the list oldest first; escalate orders 2 or more days past plan | High | Proposed | 12:00 snapshot, 18 to 24 Aug: 959 · 751 · 913 · 1,308 · 223 · 139 · 122 orders |
| **O5** | Forwarder backlog (was R2) | A final forwarder has 20 or more past-plan unreleased orders at 12:00 | Count and oldest order for that forwarder | Review that forwarder's handover plan; ask for an extra slot | High | Working (placeholder threshold) | Forwarder-days firing, 18 to 24 Aug: 9 · 8 · 9 · 10 · 2 · 1 · 1. Largest single backlog: 313 orders (21 Aug) |
| **O6** | Country lane backlog | A country code has 50 or more past-plan unreleased orders at 12:00 | Count by country and forwarder | Prioritise that lane; check cut-offs for it | Medium | Proposed | Countries firing, 18 to 24 Aug: 6 · 4 · 5 · 4 · 1 · 0 · 0. Peaks: HK 680 (21 Aug), US 441 (20 Aug) |
| **O7** | Forwarder lateness ranking | Forwarder with 30 or more orders and a late rate of 90% or more | Ranked list with order counts | Weekly handover review with that forwarder. A ranking, never a stated cause | Medium | Working | 9 of 42 forwarders; they hold 48.7% of all late orders |
| **O8** | Early release | Released 2 or more days before the planned day | Planned vs release | Check whether the plan date or slot can be re-used; positive signal | Info | Proposed | 103 orders (215 for 1 or more days) |
| **O9** | No plan, no forwarder | Movement type has no planned date, forwarder or country | Type label | Show as "no planned date"; exclude from lateness (D5, pending DSV) | Info | Working | 515 orders, 2,023 rows (Milkrun to ABC 501 orders, Scrap 12, Stock Transfer 2) |

## 2. Inbound supervisor (shipment reference, ASN and line, DSV B7)

| ID | Rule | Trigger | Evidence shown | Suggested action | Sev. | Status | Back-test in the extract |
|---|---|---|---|---|---|---|---|
| **I1** | Quantity mismatch (was R3) | Summed received differs from expected on an ASN line (line = ASN + Ref Line# + Functional Packing); tolerance is a setting, default 0% | Expected, received, pack types | Check with receiving; confirm pack types | High | Working (when a difference is an issue: DSV pending) | 0 of 36,533 lines fire |
| **I2** | Pack-type split line | One Ref Line# carries two functional pack types | Both pack-type lines side by side | Check each pack type as its own line; not an error (DSV A5) | Info | Confirmed | 109 Ref Line#s |
| **I3** | Docked, not received | Dock-in seen, no goods receipt after 24 h (state at time t) | ASN, shipment type, dock time, wait so far | Ask receiving or yard to confirm the dock and start the receipt | High | Proposed (check scope: a state at time t, not cycle-time analysis) | 1 or 2 ASNs a day at 12:00 (18 to 24 Aug). Longest completed wait: ASN 0000032007, RMA, high value, 43 h. For context, dock-to-receipt P95 is 14.7 h |
| **I4** | High-value ASN waiting | High Value Flag = Y, docked, not received after 4 h | ASN, flag, wait | Put at the front of the receiving queue | High | Proposed | 1 ASN (5 rows) in the extract; its wait was 43 h, so the rule would have fired |
| **I5** | RMA receipt | New RMA ASN received (DSV A1: returned goods not in perfect condition) | ASN, lines | Route for inspection before putaway | Medium | Proposed (needs DSV to confirm the process) | 10 RMA ASNs, 220 rows |
| **I6** | Received with no dock record | ASN has goods receipt but no dock-in time | ASN | Ask receiving to confirm the dock event | Low | Working | 19 ASNs, 867 rows |
| **I7** | Missing putaway zone | Putaway Zone blank on a receipt row | Row | Label; ask for the zone | Low | Working | 140 rows (all Normal) |
| **I8** | Blank LPN after receipt | Normal or Stock Transfer row with blank LPN more than 24 h after receipt | ASN, row | Ask packing to confirm (DSV A2: packing not yet confirmed) | Info | **Hold.** The pattern does not fit: 62 to 76% of Normal rows are blank on every receipt day, including the first | 28,612 rows, 982 ASNs would fire. Too noisy until DSV explains it |
| **I9** | Non-AS putaway share high | Share of receipt rows in SEQ or HBS above 25% for a day | Daily share, zone split | Check SEQ and HBS location capacity (DSV B9a) | Medium | Working | Days firing: 17 Aug (31.1%), 18 Aug (25.9%), 23 Aug (25.6%). Note SEQ is exactly the Milkrun inbound rows |
| **I10** | Daily load above baseline | Inbound plus outbound lines per person above 1.25 times the week's average, with a 20-person baseline (DSV B9b) | Lines per person, baseline and assumption | Consider extra people that day | Medium | Working (prototype, not a forecast; assumes 20 people cover both) | Days firing: 17 Aug (720 lines per person, 1.43 times average), 18 Aug (767, 1.52 times) |

## 3. Milkrun traceability (all roles)

| ID | Rule | Trigger | Evidence shown | Suggested action | Sev. | Status | Back-test in the extract |
|---|---|---|---|---|---|---|---|
| **M1** | Scanned, no order yet | Cyclone scan seen, no order created after 2 h | Carton, scan time | Remind the admin to create the order (DSV A3) | Medium | Proposed (the extract only holds created orders; a stage-timing view, so check scope) | 382 of 7,869 cartons took more than 2 h; 61 more than 4 h. P95 is 117 min |
| **M2** | Linked-carton content check | Inbound LPN and outbound carton disagree on SKU and vendor lot | Both lists | Hold the carton; check the content | High | Proposed | 0 of 5,564 differ: contents agree on every linked carton |
| **M3** | Clock offset watch | Cyclone scan more than 60 s from goods receipt plus 8 h | Carton, gap | Tell the data owner the clock alignment may have changed | Medium | Working | 0 of 5,564; the largest gap is 39 s |
| **M4** | ID integrity | LPN under 2 ASNs, carton with 2 release times, or carton holding 2 orders | The IDs | Data owner checks the source rows | Low | Working | 7 LPNs, 11 cartons, 12 cartons |
| **M5** | Receipt outside window (was R5) | Outbound Milkrun carton with no receipt in the extract | Carton | Label "receipt outside window"; no alert | Info | Working (pending DSV) | 2,305 cartons |
| **M6** | Awaiting release | Inbound Milkrun LPN with no outbound carton in the extract | LPN | Label "not yet released or outside window end"; no alert | Info | Working | 2,057 LPNs |
| **M7** | Identical outbound rows | Row identical to another outbound row | Row | Keep, label "identical source row"; never delete. Inbound identical rows are valid split receipts, so no inbound rule | Info | Working | 148 surplus outbound rows |

## 4. Operations manager (reviews, not alerts)

| ID | Rule | Trigger | Suggested action | Status | Back-test |
|---|---|---|---|---|---|
| **O10** | Daily on-time dip | On-time rate for a planned day below 70%, with at least 100 orders | Next-morning review of that day's late orders and forwarders | Proposed | Planned days firing: 19 Aug (68.5%) and 20 Aug (61.1%). Others: 17 Aug 75.8%, 18 Aug 84.5%, 21 Aug 79.7%. 22 and 23 Aug have under 100 orders |
| **O7, I9, I10** | See above | | | | |

---

## Settings table (thresholds in one place)

| Setting | Default | Used by |
|---|---|---|
| Cut-off hour on planned day | 18:00 | O1 |
| Late-created hour | 12:00 | O2 |
| Backlog snapshot hour | 12:00 | O4, O5, O6 |
| Forwarder backlog size | 20 orders | O5 |
| Country backlog size | 50 orders | O6 |
| Forwarder late rate / minimum orders | 90% / 30 | O7 |
| Daily on-time floor / minimum orders | 70% / 100 | O10 |
| Quantity tolerance | 0% | I1 |
| Docked wait / high-value wait | 24 h / 4 h | I3, I4 |
| Non-AS putaway share | 25% | I9 |
| Load factor / baseline people | 1.25 / 20 | I10 |
| Scan-to-order delay | 120 min | M1 |
| Clock tolerance | 60 s | M3 |

## Priority when several rules fire

High before Medium before Info; within High: I4, O2, O1 at 21:00, I3, O5, I1, O1 at 18:00. DSV has not told us how managers prioritise (Q23, not sent), so this order is our proposal.

## Deliberately not rules

| Candidate | Why not |
|---|---|
| "Forwarder changed" alert | DSV A6: normal, not an exception. 62% of orders |
| Urgent Flag priority | The flag is Y on all 64,641 outbound rows |
| Packed but unreleased at 12:00 on the planned day | Flags 85 to 94% of orders (2,925 of 3,110 on 17 Aug) and only 14 to 38% finish late |
| Order created to release over 24 h (Milkrun) | 5,835 of 7,869 cartons (74%); not a useful signal |
| Duplicate inbound rows | 12,738 identical rows exist, mostly valid split receipts |
| Cycle-time, bottleneck or stage-time analysis as a rule family | Out of scope (addendum). Only plan vs actual and state-at-time-t views |
| Autonomous actions | Out of scope. Every rule needs a person's decision |

## Open points for DSV and the team

- Definition of "late" and tolerance (D1): changes O1 to O3, O7, O10.
- When a quantity difference is an issue (D2): changes I1.
- Why the inbound LPN is blank (I8): decides whether I8 ships.
- What the outbound "Milkrun to ABC", Scrap and Stock Transfer rows are (O9).
- How managers prioritise (Q23, not sent).
- Whether 20 people cover inbound and outbound together (I10).
- Rules marked Proposed and flagged "check scope" (I3, M1) need the same check: DSV's timestamp note mentions cycle-time and bottleneck analysis, but the addendum excludes it.
