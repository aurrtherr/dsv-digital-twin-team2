# Data Analysis Team Meeting Outcome

_Exported from the team Google Doc "DSV Digital Twin – Team 2" on 23 Nov 2026. The Google Doc is the master copy._

## Meeting Pointers: Data Analysis Handover (18 Nov 2026)

- 3 ways to approach the data analysis
  - More as active filtering thing
  - the tool to obtain individual point of data
  - Hybrid
- Section 2.1
  - For the outbound work
  - The first one is high level
  - The second one is more on the actions that need to be taken
  - Inspect dispatch record can just leave out
- Section 2.2
  - In the inbound we an investigate all the abnormal lines. There are a few the issue status for example the double lines
  - We need to show
  - The dock waiting the benchmark is 90th percentile for the
  - Some of it is unknown dock type only 14 for daily
- Section 3
  - Is similar to the which one in section 2.2 which one has been abnormally have not been docked for a certain period of time using the 90th percentile benchmark
  - Some of it has no end date
- Section 4
  - There is a dashboard where everyhour what are the event done in that hour for example dock in, goods receipt, etc, which we there is a filter
- Section 5
  - The idea of 5.1: if we dont have much information, when there is no link, using sku and vendor lot, 90% can be backtested: which 10% are unable to be linked because it might be because of the out of the timeframe
- Section 6
  - Actually the data doesn't include all the date that is missing
  - Specifically of what are the problem of each of the problematic or flagged rows
  - No handover observed might be the most crucial one
    - It might be because it hasn’t happened yet but we still need to flag it
- Section 7
  - Can put for the data owner to flag
  - Section 7.1 dropped
- Section 8
  - Recommendation rules of what to do
  - X hour earlier
    - To improve the lateness percentage
- What if:
  - How many money are you willing to put in (/h) and show what is the minimal singapore wage
  - The amount of people
- It would be nice to have an ai assistant for the dashboard each of them have a template what to put in their home page but if they want to customize it can
- For the trends page it should show the daily performance and hourly performance should show the filter whether we want it to be daily or hourly
- Put in the settings the light and dark
  - Also add the fonts changes font size
  - Add the language diversity all the singapore languages
- For all of the data use weekly trend or hourly trend
- For the UI team do the

### 1. Progress and deliverables

- Midterm presented on 13 Nov.
- The Feasure_Final notebook analyses the DSV inbound and outbound reports. It covers:
  - Warehouse activity and open work
  - Receiving quantities and dock waits
  - Milkrun traceability
  - Handover performance against the planned date
  - Data-quality checks
  - Needs-attention rules
  - A historical what-if (earlier handover)
- W10: Esther and Hern complete the Figma prototype.
- W11: Mk and Alicia build the working demo.
- Round 2 questions (15) sent through the course hub on 17 Nov. The next DSV consultation should focus on the decisions needed to turn our working assumptions into confirmed DSV rules.

### 2. Feedback from DSV and the TA

**DSV on lateness (11 Nov)**
- The Planned Post Date alone does not prove lateness: release can be delayed on purpose (for example a customer hold or a full flight).
- So the dashboard says "released after the planned date". It is a signal to review, not proof of lateness.
- For each order, show: planned date, actual handover date, days after the planned date, and a review status.
- The files have no customer shipment deadlines or holds, so we cannot work them out (asked DSV in Q27).
- Milkrun to ABC and Scrap orders have no planned date: they are internal movements and are not judged late.
**Staffing what-if (DSV B9 and TA feedback, 13 Nov)**
- DSV gave a baseline of 20 people and suggested: if volume rises by X%, how many more people are needed?
- The TA asked for a measurable, transparent calculation: the rate per person, the people needed, and the cost of the extra people.
- The what-if should show: workload, work per person (our assumption), people needed, extra people and estimated cost.
- Every assumption is shown on screen and can be changed by the user.
- It is a prototype estimate, not a check that the warehouse can really be staffed that way.

### 3. Numbers check (recalculated on the full DSV files; all match the deck)

**Handover**
- 15,649 orders planned 17–23 Aug: 25.5% released after their planned date (definition A).
- 23.4% of all 18,965 measurable orders.
- 513 orders have no planned date (501 Milkrun to ABC, 12 Scrap).
- 181 orders have a planned date before they were created (DSV A4: likely urgent orders).
- 0 orders have conflicting planned dates.
- At 21 Aug 09:00: 1,460 open orders were past their planned day. 313 of them go to HK with forwarder 013, and 99.9% of those 313 were already packed.
- At 20 Aug 18:00: 573 open orders past their planned day, 152 planned before creation and 1 long dock wait. Quantity differences: 84 on the 2-part key, 0 on the 3-part key.
- Normal dock-to-receipt P90 = 5.2 hours.
**Receiving**
- 36,533 inbound lines, all match the expected quantity (0 differences).
- On the 2-part key (ASN + line), 109 lines look exactly 2×. They match once Functional Packing is added to the key (DSV A5).
- No source rows are changed or corrected.
**Milkrun trace**
- 7,869 outbound Milkrun cartons; 5,564 are exactly linked to an inbound receipt.
- 2,305 outbound cartons have no inbound receipt: they were received before the inbound file starts.
- 2,057 inbound cartons have no outbound order yet: received, but not shipped in this week.
- Identical rows: 12,738 inbound (normal split boxes, keep them) and 148 outbound (142 Milkrun, to review in Q30).
**Milkrun quantity check**
- 99.1% of fully linked Milkrun orders reconcile (3,214 of 3,242).
- 99.3% of 4,353 SKU/lot keys match.
- All 31 mismatched keys have inbound exactly 2× outbound.
- The 28 mismatched orders contain 76 of the 148 identical outbound rows.
**What this means**
- The gaps look like a quantity-grain or repeated-row issue, not missing stock.
- DSV needs to confirm (Q25, Q30) before we draw any operational conclusion.

### 4. Quantity decision: how to count Qty Shipped

- The original notebook adds up Qty Shipped on every row: 1,038,100,865. Counted once per order line it is 695,808,651, so the row total is about 49% higher. The 16 Nov review copy already counts once per order line.
**Recommended working rule**
- Count Qty Shipped once per Order Key + Order Line Number, when the line's SKU, lot and quantity are the same on all its rows.
**Why**
- All 10,684 multi-carton lines repeat the same quantity on every row.
- It matches how inbound is counted (expected quantity once per line).
- It is what makes the 99.1% Milkrun reconciliation work.
- It stops forwarder and daily totals from being inflated.
- Anyone can reproduce it from the order and line fields.
**Still uncertain**
- DSV has not confirmed whether Qty Shipped is a line total or a carton total (Q25).
- The 31 exactly-2× mismatches may mean a few lines record a per-carton quantity.
- Until Q25 and Q30 are answered, label the per-line total as our assumption, and show the row total only as a raw figure with a warning.
**Do not**
- Split a line's quantity evenly across its cartons: the data does not say how it was split.
- Call the result a physical carton quantity before DSV confirms.
**For staffing**
- Use counts instead of units (orders, lines, cartons). This suits workload, but it does not replace the quantity check.

### 5. Rule names

- Problem: the notebook used ORD-01, DATE-01, QTY-01 and ASN-01, while the prototype and deck use IN, OUT, DQ and MGR.
- Proposal: keep the prototype's names, since the deck and the 16 Nov notebook copy already use them. Renumbering now would break the links between the three.
  - IN: inbound rules (owner: inbound team)
  - OUT: outbound rules (owner: outbound / shipping team)
  - DQ: data-quality checks (owner: data owner)
  - MGR: manager rules (owner: operations manager)
- Notebook to prototype: ASN-01 → IN-01 (docked, not received in usual time); ORD-01 → OUT-01 (past planned day); QTY-01 → IN-03 (received quantity differs); DATE-01 → DQ-01 (planned before created).
- Milkrun checks keep their current IDs: IN-04 (Milkrun carton, no order) and DQ-04 (contents mismatch, not built yet; notebook 7.1 is its logic). Add a separate ML group only if the team prefers it, and update the deck at the same time.
- Every rule should show: name, trigger, threshold, owner, suggested action, data source, and whether it is confirmed by DSV or our working assumption.

### 6. Staffing what-if (main what-if for the W11 demo)

**Inputs**
- Volume change (%)
- Workload unit: lines (default), cartons or orders
- Work per person per day (default about 505 lines: 20 people on the week-average load)
- Number of shifts and productive hours per shift (once DSV answers Q32)
- Cost per person per shift or month (our assumption until Q34)
- Period: typical weekday or week average
- Optional: inbound / outbound split
**Calculation (shown step by step)**
- Daily workload = inbound lines + outbound order lines for the chosen period
- New workload = daily workload × (1 + volume change)
- People needed = round up (new workload ÷ work per person)
- Extra people = people needed − current staff
- Extra cost = extra people × cost per person
- Range = repeat with work per person 10% higher and 10% lower
**Example (current prototype numbers)**
- A typical weekday has 12,062 lines, so it needs 24 people at today's volume (weekends are much lower, so weekdays already need more than the 20-person average).
- At +20%: 14,474 lines ÷ 505 = 29 people (range 27–32). That is 5 more than today's weekday need, or 9 more than the 20-person baseline.
- Extra cost = extra people × the cost rate we agree on.
**Controls and outputs**
- Controls: volume change, work per person, cost per person
- Outputs: people needed, extra people, extra cost and the range
