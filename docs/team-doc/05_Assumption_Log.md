# Assumption Log

_Exported from the team Google Doc "DSV Digital Twin – Team 2" on 23 Nov 2026. The Google Doc is the master copy._

## DSV Digital Twin – Assumption Log

Last updated Nov 13, 2026 · Owner @esther
The course asks every team to state its working definitions in an assumption log and keep them easy to change until DSV replies. This log has three parts: the **working assumptions** the design and prototype rely on, the **client answers still pending** that could overturn them, and the **data issues** found in the reports with how we treat each one. Question numbers (Q1–Q23) point to the Client Q&A Log; A1–B9 point to the Course Addendum clarifications (6 Nov, with DSV’s follow-up answers added in the version of 11 Nov); "29 Oct" is Ying's email. All data figures were checked on the full files on 11 Nov 2026.
**Status key**
- **Confirmed** – stated by DSV in writing.
- **Course guidance** – set by the course or Ying; DSV has not contradicted it.
- **Verified in data** – our assumption, tested on the full files.
- **Working** – our choice; must be stated in deliverables and is easy to change.

### 1. Working assumptions

| **ID** | **Area** | **Assumption** | **Basis** | **Status** | **Impact if wrong** | **Link** |
|---|---|---|---|---|---|---|
| WA-01 | Time | Add 8 hours to inbound Dock and GR times; outbound times are not shifted. | Ying 29 Oct; Important Notes.txt | Course guidance | Every inbound-to-outbound duration and the Milkrun trace timeline shift by 8 h. | Q3 |
| WA-02 | Keys | An inbound line is WMS ASN# + Ref Line# + Functional Packing. | DSV A5; all 36,533 lines reconcile on this key | Confirmed | 109 lines would show as false 2x over-receipts. | Q9, Q18 |
| WA-03 | Keys | Milkrun trace key: inbound LPN (Milkrun to ABC) = outbound Carton ID (Milkrun from ABC). | Important Notes.txt; Ying 29 Oct; 5,564 IDs link | Confirmed | Milkrun traceability module loses its only exact link. | Q3 |
| WA-04 | Keys | Normal, Stock Transfer, RMA and AIFTA flows have no exact inbound-to-outbound link and are shown as separate views. A SKU + Vendor Lot match is shown only as "approximate". | DSV A2; Ying 29 Oct | Confirmed | Approximate links could be misread as proof of where stock went. | Q2 |
| WA-05 | Lateness | An order is late when its handover calendar day is after its Planned Post Date (definition A). Alternatives kept switchable: B = 2+ days after; C = after 18:00 on the planned day; D = after noon the next day. | Our choice; notebook Section 6. Qualified by DSV (11 Nov, A4 follow-up): don’t judge lateness from the Planned Post Date alone, since release can move on purpose (a customer hold, a fully booked flight). The twin shows it as a signal to review, not proof of lateness. | Working (qualified by DSV, 11 Nov) | Rate (25.5% under A for orders planned 17–23 Aug; 23.4% over the whole extract) and all lateness alerts change. | Q6, Q27, Q28 |
| WA-06 | Lateness | Orders with no Planned Post Date (all Milkrun to ABC and Scrap, 513 orders) are "on-time not applicable" and left out of the lateness KPI. | DSV (11 Nov, A4 follow-up): Milkrun to ABC and Scrap are internal movements, so the Planned Post Date is not their lateness indicator | Confirmed | Lateness KPI denominator changes; these flows may need their own target. | Q17 |
| WA-07 | Dates | A Planned Post Date earlier than the order creation day (181 orders) marks an urgent order, not a data error. Kept in all KPIs and shown as information. | DSV A4 | Confirmed | Would need an alert instead of a tag. | Q8, Q29 |
| WA-08 | Forwarder | A Final Forwarder different from the Default (62% of orders) is normal and never triggers an alert. | DSV A6 | Confirmed | – | Q7 |
| WA-09 | Milestones | "Ready to ship" = Packing Confirmation for Normal; Cyclone receipt for Milkrun from ABC (fallback: adjusted inbound GR of the same ID). | Field presence by flow (Normal never has Cyclone; Milkrun never has packing) | Working | Readiness and open-work views would use the wrong milestone. | Q4, Q20 |
| WA-10 | Milestones | Cyclone is only expected on Milkrun from ABC; its absence on other flows is not flagged. | Ying 29 Oct; data; DSV (11 Nov, A3 follow-up): Cyclone applies only to Milkrun cartons from Level 3, and not every carton passes it | Confirmed | If every carton should pass Cyclone, missing scans become a data issue. | Q4 |
| WA-11 | Milestones | The same process milestones apply to every movement type (AIFTA, RMA, Stock Transfer, Scrap) unless DSV says otherwise. | DSV A1 (AIFTA uses normal milestones) | Working | Separate KPIs or lead times per type would be needed. | Q16 |
| WA-12 | LPN | A blank inbound LPN means packing was not yet confirmed at extract time; it is not an error. | DSV A2 | Confirmed | – | Q2 |
| WA-13 | Coverage | The 2,305 Milkrun cartons with no inbound receipt were received before the inbound extract began. | Ying 29 Oct; all have a Cyclone time before 17 Aug 02:21 (adjusted first Milkrun GR); DSV (11 Nov, A2 follow-up): receipt dates are likely before the inbound extract | Confirmed | Would become missing-receipt exceptions. | Q14 |
| WA-14 | Coverage | Inbound covers goods receipts on 17–24 Aug (adjusted); outbound covers orders handed over on 17–24 Aug. Open work and backlog are rebuilt as of a past moment, and "today" for the replay is the latest recorded event (24 Aug 2026). | Inferred from date ranges; notebook Section 1 | Working | Backlog counts and edge-of-window lateness rates would be biased differently. | Q24 |
| WA-15 | Quantity | Any difference between received and expected quantity on the 3-part line key is flagged; tolerance is zero. | DSV (11 Nov, A5 follow-up): any difference between expected and received quantity on a Normal shipment is an exception to escalate; currently 0 such lines | Confirmed | Alerts could be too noisy or too quiet once a tolerance is given. | Q18 |
| WA-16 | Quantity | Qty Shipped is an order-line total repeated on every carton row, so it is counted once per Order Key + Order Line Number. | 10,684 multi-carton lines all repeat the same quantity; Milkrun orders reconcile 99.1% on this basis | Verified in data | Shipped volume would be overstated if summed per row. | Q25 |
| WA-17 | Quantity | Identical inbound rows (12,738) are separate split boxes of equal size, not duplicate postings, and are not removed. | Every line reconciles exactly when they are kept | Verified in data | Received quantities would be overstated. | Q9 |
| WA-18 | Scope | Diagnosis is limited to planned-date and quantity reconciliation and Milkrun traceability. Cycle-time, bottleneck and exception analysis are not built. | Course addendum; Ying 29 Oct | Course guidance | – | Q5 |
| WA-19 | What-if | The what-if follows DSV's suggestion: volume +X% scales required staff from a baseline of 20 in proportion (constant productivity), or a change in non-AS putaway share scales location capacity. It is presented as a prototype, not a forecast. | DSV B9; course addendum. In the prototype, 20 people match the week-average load, so +20% volume needs 29 on a typical weekday (range 27–32) TA feedback (13 Nov): show the rate per person and the cost of extra staff openly. | Working | Result is indicative only; non-linear effects (shifts, automation limits) are not modelled. | Q10, Q32, Q34 |
| WA-20 | Recommendations | Every recommendation is rule-based, shows the rule, the triggering data and the threshold, and needs a human approval before any action. | Course addendum; Ying 29 Oct; playbook. DSV (11 Nov, B8 follow-up): KPIs are order release status, quantity discrepancies and shipment readiness; actions are reprioritise urgent orders, adjust manpower, investigate discrepancies, and escalate shipment or forwarder issues to the shipping team; alert owners are the Operations Supervisor (quantity mismatch), the Outbound/Shipping Team (shipment not ready near its required timing) and the Operations Manager (workload above capacity) | Course guidance | – | Q11, Q13, Q31 |
| WA-21 | Prioritisation | When several issues occur at once, the closest Planned Post Date comes first, then the larger quantity affected. | Our choice | Working | Ordering of the supervisor's work list changes. | Q23 |
| WA-22 | Supervisor view | Shift-start views open at ASN and line level for inbound, and at order level (country code, final forwarder) for outbound. | DSV B7 | Confirmed | – | Q1, Q33 |
| WA-23 | Recommendations | Approving a rule assigns a task to an existing role: inbound supervisor, outbound supervisor, planner, operations manager or data owner, and DSV's shipping team for forwarder and pickup issues. The floor team gets its tasks through its supervisor. The work happens by phone or in DSV's systems, and the twin checks the next data to close the task. Data checks only label records, so they need no approval. | Our choice; DSV (11 Nov, B8 follow-up) for the alert owners | Working | Task routing and the Tasks screen change. | Q11, Q12, Q26 |

### 2. Pending client answers

| **ID** | **Open question for DSV** | **Linked assumption** | **Sent** | **What changes if the answer differs** | **Link** |
|---|---|---|---|---|---|
| PC-01 | What does "late" mean, and which KPIs matter most? | WA-05 | 7 Nov; answered 11 Nov (qualified) | Answered 11 Nov, qualified: KPIs given; the Planned Post Date alone doesn’t prove lateness. Still open: the required shipment timing per order. | Q6 |
| PC-02 | How is on-time judged for rows with no Planned Post Date? | WA-06 | 7 Nov; answered 11 Nov | Answered 11 Nov: internal movements, not judged late (WA-06 confirmed). | Q17 |
| PC-03 | When does a quantity difference count as an issue? | WA-15 | 7 Nov; answered 11 Nov | Answered 11 Nov: any Normal-shipment difference is escalated (WA-15 confirmed). | Q18 |
| PC-04 | Which alert triggers apply, and which role acts? | WA-20 | 7 Nov; answered 11 Nov | Answered 11 Nov: Operations Supervisor, Outbound/Shipping Team and Operations Manager own the alerts (WA-20). | Q12 |
| PC-05 | Which actions can a supervisor take? | WA-20 | 7 Nov; answered 11 Nov | Answered 11 Nov: reprioritise, adjust manpower, investigate, escalate to the shipping team (WA-20). | Q11 |
| PC-06 | Is Cyclone the sorter scan, and does every carton pass through it? | WA-09, WA-10 | 7 Nov; answered 11 Nov | Answered 11 Nov: Cyclone is Milkrun only, from Level 3 (WA-10 confirmed). | Q4 |
| PC-07 | Confirm the 2,305 unmatched Milkrun cartons pre-date the inbound extract. | WA-13 | 7 Nov; answered 11 Nov | Answered 11 Nov: receipts likely before the extract (WA-13 confirmed). | Q14 |
| PC-08 | Which date field decides whether a row is in each report? | WA-14 | Asked in A2, not answered | Backlog reconstruction and edge-of-window bias. | Q24 |
| PC-09 | Is Qty Shipped an order-line total repeated per carton? | WA-16 | Not yet sent | Shipped-volume totals. | Q25 |
| PC-10 | Do movement types have different KPIs or lead times? | WA-11 | Not yet sent | Per-type targets. | Q16 |
| PC-11 | What are the steps from order creation to packing to cargo release for each flow? | WA-09 | Not yet sent | Process model and milestones. | Q20 |
| PC-12 | What is the serial suffix in long LPNs (SKU + lot + serial), and does it link to anything? | WA-04 | Not yet sent | Possible extra trace for non-Milkrun flows. | Q19 |
| PC-13 | How is a late order or quantity mismatch investigated today, and how are issues prioritised? | WA-21 | Not yet sent | User journey and priority rule. | Q22, Q23 |
| PC-14 | Who carries out each action (for example booking a pickup or re-ordering packing), and how do they receive tasks today? | WA-23 | Not yet sent | Task routing, roles and the floor-team hand-off. | Q26 |
| PC-15 | What is the required shipment timing for an order, and are customer holds or flight changes recorded anywhere? | WA-05 | Not yet sent (raised by DSV's 11 Nov answer) | Whether "released after the planned date" can become a real lateness KPI. | Q27 |
| PC-16 | What are the forwarder pickup or cut-off times? | WA-05 | Not yet sent | Lateness option C (18:00 cut-off) and how the batched handover is read (24% of cartons in the 18:00 hour, 36% on Mondays). | Q28 |
| PC-17 | What does the Urgent Flag mean, when it is "Y" on every outbound row? | WA-07, WA-21 | Not yet sent | Which orders count as urgent, and the priority order. | Q29 |
| PC-18 | Are the 148 identical outbound rows duplicate postings? | DI-10 | Not yet sent | Shipped-quantity totals. | Q30 |
| PC-19 | Are there targets or thresholds for each alert (on-time target, "not ready" window, capacity)? | WA-20 | Not yet sent | Alert thresholds, which are our own for now. | Q31 |
| PC-20 | How much work does one person handle per shift, and how are the 20 people split? | WA-19 | Not yet sent | The staffing what-if result and its range. | Q32 |
| PC-21 | Should supervisors use the ASN when Shipment Ref is blank? | WA-22 | Not yet sent | Shift-start view for Normal, RMA and AIFTA flows. | Q33 |
| PC-22 | What does one extra person cost, or what cost rate should we use? | WA-19 | Not yet sent (raised by TA feedback, 13 Nov) | Whether the what-if can show the cost of extra staff, not just the head count. | Q34 |

DSV answered PC-01 to PC-07 on 11 Nov (course addendum, version 11 Nov); PC-01 stays partly open for the required shipment timing. PC-08 to PC-22 are for the mid-project consultation (Q19 and Q23–Q34 in the Q&A Log).

### 3. Data issues

| **ID** | **Issue** | **Evidence (full files)** | **Treatment** | **Status** |
|---|---|---|---|---|
| DI-01 | 109 inbound lines look exactly 2x their expected quantity. | 95 Milkrun, 14 Normal when keyed on ASN# + Ref Line# only. | Use the 3-part key (WA-02); all lines then match. | Resolved |
| DI-02 | Inbound times are 8 hours behind outbound. | Milkrun GR would fall ~8 h after the matching Cyclone scan. | Add 8 h to inbound times (WA-01). | Handled |
| DI-03 | Glossary labels inbound Milkrun as "Milkrun from ABC". | Inbound data only contains "Milkrun to ABC". | Use "Milkrun to ABC" for inbound (DSV A1). | Resolved |
| DI-04 | Blank inbound LPNs prevent carton-level tracing. | 54.1% of inbound rows; 67% of Normal, 76% of Stock Transfer. | Treat as "packing not confirmed" (WA-12); trace at ASN and line level. | Accepted limit |
| DI-05 | Milkrun records without a counterpart. | 2,305 outbound cartons with no receipt; 2,057 received LPNs with no outbound yet. | Pre-window receipts (WA-13, confirmed by DSV 11 Nov); received but not yet shipped in the window. | Explained |
| DI-06 | Outbound file contains no open orders. | Every outbound row has a handover time. | Rebuild open work as of a past time (WA-14); note survivorship bias in late rates. | Accepted limit |
| DI-07 | Orders with no Planned Post Date. | 513 orders: all Milkrun to ABC and Scrap. | Internal movements, not judged late (WA-06; DSV 11 Nov). | Explained (DSV 11 Nov) |
| DI-08 | Planned Post Date before order creation. | 181 orders. | Tag as urgent (WA-07). | Explained |
| DI-09 | Qty Shipped repeats on each carton row of an order line. | 10,684 multi-carton lines, all with identical quantity per row. | Count once per order line (WA-16). | Handled |
| DI-10 | Identical duplicate rows. | Inbound 12,738 rows; outbound 148 extra rows (mostly Milkrun). | Inbound kept as split boxes (WA-17); outbound duplicates need review before quantity totals. | Open (outbound) |
| DI-11 | Shipment Ref missing, so DSV's first supervisor check is not always possible. | Blank on 95% of Normal rows and all RMA and AIFTA rows; present on Milkrun and Stock Transfer. | Fall back to ASN for Normal flow in the shift-start view. | Accepted limit |
| DI-12 | Fields with no signal. | Urgent Flag = Y on every outbound row; Strategic Goods Flag always N; High Value Flag Y on 5 inbound rows; Storer is always IXX. | Not used for prioritisation or filtering. | Accepted limit |
| DI-13 | Missing dock times. | 867 inbound rows (676 Stock Transfer, 191 RMA). | Dock-to-GR not computed for these ASNs. | Accepted limit |
| DI-14 | Missing putaway zone. | 140 Normal rows. | Shown as "Unknown" in the putaway what-if. | Accepted limit |
| DI-15 | Inconsistent or placeholder values. | Hub Flag "No" vs "NO"; 1,991 carton dimensions " X X "; carton weight 0 or blank on 95% of Normal rows; 75 LPNs with a decimal point inside the lot. | Normalise case; treat placeholders and zero weights as missing; don't use weight or dimensions in the design. | Handled |
| DI-16 | Carton IDs shared across orders. | 121 rows on 12 Carton IDs (Milkrun to ABC and Scrap). | Show all linked orders; never pick one arbitrarily. | Handled |
| DI-17 | Only about one week of data, with no labour, equipment, capacity or inventory data. | Course addendum. | Any prediction or what-if is labelled a prototype. | Accepted limit |

No impossible sequences were found: no GR before dock, no handover before order creation, and no packing after handover.

### Change history

| **Date** | **Change** |
|---|---|
| 11 Nov 2026 | Log created: 22 working assumptions, 13 pending client answers and 17 data issues, all checked on the full files. |
| 13 Nov 2026 | Added DSV's follow-up answers (course addendum, version 11 Nov). WA-06, WA-10, WA-13 and WA-15 are now Confirmed; WA-05 is qualified (the Planned Post Date alone doesn't prove lateness); KPIs, actions and alert owners added to WA-20; WA-19 notes the prototype result; WA-23 added. PC-01 to PC-07 answered; PC-14 and PC-15 added. DI-07 explained. |
| 13 Nov 2026 | Cross-checked against the Q&A Log so every open item has a question. PC-08, PC-09, PC-14 and PC-15 now point to Q24–Q27; PC-16 to PC-21 added (Q28–Q33: forwarder cut-off times, Urgent Flag, duplicate outbound rows, alert thresholds, staff productivity, Shipment Ref fallback). Link column updated for WA-05, 07, 14, 16, 19, 20, 22 and 23. |
| 15 Nov 2026 | TA midterm feedback on the staffing what-if: WA-19 notes it; PC-22 added (cost per extra person, Q34). |
