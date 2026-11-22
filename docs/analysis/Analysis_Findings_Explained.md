# DSV Digital Twin: what the notebook does, block by block, and what it tells us

> **Note (23 Nov 2026):** written on 5–6 Nov, before DSV's Round 1 and 11 Nov answers. Two things have changed since: (1) the 109 "exactly 2×" inbound lines are not over-receipts. They are two Functional Packing types on one Ref Line# (DSV A5); with the 3-part key all 36,533 lines reconcile. (2) "Late" is now shown as "released after the planned date", a signal to review, not proof of lateness (DSV, 11 Nov). The full build `DSV_Digital_Twin_Analysis.ipynb` is not in this repo; the core build is in `notebooks/`.

Companion to `DSV_Digital_Twin_Analysis.ipynb`. Every number below was produced by running the notebook on the two raw Excel reports (`Daily_Inbound_Report.xlsx`, `Daily_Outbound_Report.xlsx`). Block numbers match the notebook headings. Each block has the same five parts: **Purpose**, **Method**, **Result**, **Insight**, **Caveat**. Where a block fed a slide, it says which.

**Two builds from the same code.** `DSV_Digital_Twin_Analysis.ipynb` is the full version. `DSV_Digital_Twin_Core.ipynb` leaves out the exploratory timing blocks (10 to 13 and 14c), so it stays inside the project scope when shared outside the team. Both run end to end and pass their self-checks (28 in the full build, 27 in the core build). All settings (time-slider moments, example moment, rule thresholds, output folder) are in Block 0.

How certain each statement is:
- **Fact** means it is counted directly from the data.
- **Confirmed** means DSV or the course told us (timestamp note, Clarifications round 1).
- **Hypothesis** means it is our reading and needs DSV to confirm.

---

## 0. Executive summary

| # | Finding | Where |
|---|---|---|
| 1 | The two reports share one key only for Milkrun: inbound LPN = outbound Carton ID. That joins 5,564 cartons, which is 15.9% of all 35,092 outbound cartons and 70.7% of the 7,869 outbound Milkrun cartons. So 84% of cartons cannot be followed end to end. | Block 8 |
| 2 | The 8-hour gap between goods receipt and the Cyclone (sorter) scan is a time-zone offset, not processing time. After adding 8 h to inbound times, the scan falls 0 to 39 seconds before GR on all 5,564 joined cartons. | Block 9 |
| 3 | 99.7% of the 36,424 inbound ASN lines receive exactly what was expected. The other 109 lines (32 ASNs) received exactly double. None were short. | Block 5 |
| 4 | For a joined Milkrun carton, the median wait from order created to cargo released is 32.8 h, about 99% of the time between receipt and release. Receipt, sorting and order creation together take about 1.3 h. | Blocks 10 and 11 |
| 5 | Release is batched: 3,449 distinct release times for 35,092 cartons, with 24% of cartons released in the 18:00 hour and 36% on Mondays. | Block 12 |
| 6 | Release wait differs a lot by forwarder. Among the six busiest, medians run from 23 h to 36 h. The same forwarders are slow in both Milkrun and Normal flows (rank correlation 0.78). | Block 13 |
| 7 | 23.4% of 18,965 orders were released on a later day than planned. Nine of 42 forwarders (30+ orders) were 90% or more late, and they carry 48.7% of all late orders while handling 11.5% of orders. The 23.4% is edge-biased: in the fully covered window (planned 17 to 23 Aug) it is 25.5%, and under other definitions of late it ranges from 5.6% to 56.8%. The nine-forwarder finding survives (9 of 39 in the covered window, 54.9% of late orders). | Blocks 14 and 14d |
| 8 | The final forwarder differs from the default on 62% of orders, and 72% of those swaps are to a neighbouring code (082 to 083, 088 to 089). In 9 of the 10 biggest swaps the final code never appears as a default code, so this looks like a code mapping (one carrier, two code lists), not a switch of carrier. Still a hypothesis for DSV (Q7). | Blocks 15 and 15b |
| 9 | Where there is no shared ID, "same SKU + vendor lot, latest receipt before the order" picks the right ASN 91% of the time on Milkrun (once the +8 h is applied). But for Normal orders only 22% have any receipt at all in the extract, so inference reaches little of the Normal flow. | Block 16 |
| 10 | A rule such as "order still unreleased at 18:00 on its planned day" flags 10,419 orders and 39% end up late over all orders with a plan date (8,933 and 42.3% in the fully covered window, planned 17 to 23 Aug). The same rule at 21:00 is 81% precise. | Block 19 |

**Five numbers or wordings on the current slides and logs should change** (details in Block 20): "1,462 ASNs" should be 1,481; the 8 h gap is now confirmed, not "likely"; "at least four fifths" is now about 99%; the 72.8% inference accuracy in the Assumption Log omitted the +8 h and is 90.7% with it; and the "62% switch forwarder" wording should wait for DSV's answer to Q7, because the evidence now points to a code mapping.

**Scope reminder.** Blocks 10 to 13 and 14c are cycle-time analysis. The addendum puts that out of scope as a deliverable. We use it only to choose where the one what-if sits, and the slides already word it that way.

---

## Part A. Set-up and data quality

### Block 0. Set-up, constants and helpers
- **Purpose:** put every assumption in one place so it can be changed once.
- **Method:** imports; `OFFSET = 8 hours` (the course note says to add 8 h to inbound times before comparing with outbound); colour palette; two helpers (`hours(a, b)` for elapsed hours, `pct(x)` for formatting); an empty `FINDINGS` dictionary that every later block fills.
- **Result:** nothing printed except the offset.
- **Insight:** keeping `FINDINGS` means Blocks 20 and 21 build the summary and the self-checks from the same numbers the analysis produced, so the write-up cannot drift from the code.
- **Caveat:** if DSV later says the offset is not exactly 8 h, change `OFFSET` and rerun; Blocks 9, 10, 16 and 17 all follow.

### Block 1. Load both reports and parse types
- **Purpose:** get clean tables with correct types.
- **Method:** read every cell as text (keeps leading zeros in ASN, order and line numbers), strip spaces, turn blanks (the reports use a single space) into missing values, then convert dates and quantities. Outbound time columns are renamed for short code: `created`, `planned`, `cyclone`, `packing`, `release`. Inbound: `dock`, `gr`. An ASN line key is `ASN + Ref Line`.
- **Result:**
  - Inbound: 57,988 rows, 1,481 ASNs, 36,424 ASN lines.
  - Outbound: 64,641 rows, 19,478 orders, 35,092 cartons.
  - Inbound goods receipt runs 16 Aug 16:12 to 24 Aug 15:48 (raw clock); dock-in from 3 Aug; outbound orders created from 28 Jul; cargo released 17 Aug 03:07 to 24 Aug 21:40.
- **Insight:** the data cover about one week of releases, but orders were created over almost four weeks and inbound docking goes back to 3 Aug. Most records near the edges belong to events that started before, or have not finished by, the window. That shapes several caveats below.
- **Caveat:** reading everything as text is deliberate. Do not let Excel convert the ID columns to numbers.

### Block 2. Profile the columns: blanks and categories
- **Purpose:** know what each flow looks like before analysing it.
- **Method:** share of blanks per column; counts by Shipment Type (inbound) and DN Type (outbound), at row, line, order and carton level; a bar chart of each.
- **Result:**

| Inbound type | Rows | Lines | ASNs |
|---|---|---|---|
| Normal | 33,685 | 17,389 | 726 |
| Milkrun to ABC | 12,606 | 12,511 | 255 |
| Stock Transfer | 11,467 | 6,467 | 487 |
| RMA | 220 | 47 | 10 |
| AIFTA | 10 | 10 | 3 |

| Outbound type | Rows | Orders | Cartons |
|---|---|---|---|
| Normal | 49,489 | 14,205 | 26,718 |
| Milkrun from ABC | 13,129 | 4,758 | 7,869 |
| Milkrun to ABC | 1,794 | 501 | 491 |
| Scrap Order | 226 | 12 | 12 |
| Stock Transfer | 3 | 2 | 2 |

  Other facts: one storer (IXX) in both files. Inbound putaway zones: AS 44,355 rows, SEQ 12,606, HBS 887, blank 140. **Urgent Flag is "Y" on all 64,641 outbound rows.** Large blank shares: inbound LPN 54.1%, Shipment Ref 55.5%, Hub Flag and Box Num 21.7%; outbound Cyclone time 79.7%, Packing time 23.4%, Wave Key 21.2%, Planned Post Date 3.1%.
- **Insight:**
  - Normal is the bulk of both flows. Milkrun is the smaller flow but the only one we can trace exactly.
  - The Urgent Flag carries no information in this extract, so it cannot be used to prioritise.
  - The blanks are not random: they line up with flow type (see Block 3), so they describe the process rather than data loss.
- **Caveat:** the glossary says inbound Milkrun is labelled "Milkrun from ABC", but the data label inbound Milkrun as "Milkrun to ABC" and outbound as "Milkrun from ABC". That is Assumption A4 and Question 15 with DSV. We show labels as recorded.

### Block 3. Data-quality checks
- **Purpose:** find what could quietly distort later results.
- **Method:** exact-duplicate rows; blank rate and ID length of LPN by flow; Carton ID lengths; which events (dock, Cyclone, packing, planned date) exist for which flow.
- **Result:**
  - 16,634 inbound rows have an identical twin (12,738 surplus copies). Outbound: 287 rows (148 surplus).
  - Inbound LPN is blank on 67.2% of Normal rows and 76.1% of Stock Transfer rows, and never blank for Milkrun, RMA or AIFTA.
  - Milkrun LPNs are always 13 characters, the same shape as the 13-character outbound Carton IDs. Normal LPNs are mostly 8 characters (10,589 rows), with a few 24 or 27 characters.
  - Outbound Carton ID: 62,618 rows have 13 characters; 2,023 have 7 (the trolley rows).
  - Dock-in is blank on 86.8% of RMA rows and 5.9% of Stock Transfer rows.
  - Planned Post Date is blank on all 1,794 "Milkrun to ABC" rows and all 226 Scrap Order rows.
  - The Cyclone time exists only on "Milkrun from ABC" rows (100% of them); Packing time only on Normal rows (100%).
- **Insight:**
  - The key point is the LPN shape. A Normal LPN does not look like a Carton ID, which is the reason there is no exact join for Normal. This is the factual basis for the "84% no shared ID" claim.
  - Exact-duplicate rows are common because split receipts repeat the same box group. They are not errors by themselves (Block 5c proves it).
  - Cyclone vs Packing means the two flows have different event sets. The digital twin must map "equivalent events" per flow (Assumption T3).
- **Caveat:** we do not know whether every Normal carton passes through the Cyclone. The data only say it has no Cyclone time (Question 4).

### Block 4. Is the ASN count 1,462 or 1,481?
- **Purpose:** check the figure shown on slide 2.
- **Method:** count distinct ASNs overall and among rows that have a dock-in time.
- **Result:** 1,481 ASNs in the report; 1,462 have a dock-in time; 19 do not. All 19 are Stock Transfer or RMA ASNs.
- **Insight:** slide 2's "1,462 ASNs" is the dock-in count, not the report's ASN count. A judge who counts distinct ASNs would get 1,481.
- **Fix:** write "1,481 ASNs" or "1,462 ASNs with a dock time".

---

## Part B. Reconciliation (in scope)

### Block 5. Planned vs received quantities per ASN line
**5a. Roll split receipts into lines**
- **Purpose:** compare expected with received quantity at the right level.
- **Method:** one ASN line can span several rows (a split receipt). Group by `ASN + Ref Line`, take Qty Exp once (it is the same on every row of a line, which the code asserts), and sum Qty Rcvd. Then compare.
- **Result:** 57,988 rows become 36,424 lines (21,564 rows are extra pieces). 27,840 lines have one row, 5,044 have two, 1,380 have three, and a long tail has more. Outcome per line: **36,315 exact (99.70%)**, **109 exactly 2x**, **0 short**, 0 other. By type, the 109 are 95 Milkrun and 14 Normal; none in Stock Transfer, RMA or AIFTA. The surplus is 972,500 units out of 682,649,467 received (0.142%).
- **Insight:** the exceptions have a clean signature (exactly double, never short), which makes a precise rule possible: "received = 2 × expected, flag as suspected duplicate posting". We flag and do not correct.
- **Caveat:** summing rows matters. Compared row by row, many split rows would look like shortages. We do not know whether 2x is a duplicate posting or a genuine over-delivery (Question 9).

**5b. Look at the exceptions**
- **Method:** list ASNs with 2x lines; chart the ratio distribution (log scale) and the top ASNs.
- **Result:** the 109 lines sit in 32 ASNs. Three ASNs hold 41 of them: 0000031377 (22 lines, 37% of its 59), 0000031370 (11 of 60) and 0000031422 (8 of 49). In no ASN is every line doubled.
- **Insight:** concentrated, not spread. A supervisor can review about three ASNs to cover 38% of the exceptions. It also suggests a per-ASN cause (a receiving session), not a product problem.

**5c. Are the 2x lines special?**
- **Method:** compare split patterns; test the duplicate-posting idea by dropping exact-duplicate rows and re-summing.
- **Result:** every 2x line is split over more than one row (mean 4.31 rows vs 1.58 for other lines). Duplicate rows make up 59.1% of rows in 2x lines vs 28.7% overall. All rows of a split line share one GR time. Dropping duplicate rows fixes **0 of the 109** lines and would push **3,764 currently exact lines short**.
- **Insight:** 2x lines are the heavily split ones, which is consistent with a receiving-side double posting. But exact-duplicate rows are a normal feature of correct split receipts, so "remove duplicates" is not a valid fix. That is why the rule is "flag at exactly 2x" and not "dedupe".
- **Caveat:** hypothesis only. The cause is a DSV question.

---

## Part C. Traceability

### Block 6. Inbound timing and volumes
- **Purpose:** know how long receipt takes and how inbound work is spread across the week.
- **Method:** dock-in to GR in hours by type (both are inbound-system clocks, so no offset is needed); rows per day and per hour using GR + 8 h.
- **Result:** median dock-to-GR: Milkrun 0.88 h, Normal 3.45 h, Stock Transfer 4.30 h, AIFTA 4.09 h, RMA 25.4 h (only 29 rows with a dock time). No negative values. Rows per day run from 5,585 (22 Aug) to 9,096 (18 Aug). The busiest hours are 15:00 to 17:00 (peak 4,735 rows at 17:00).
- **Insight:** Milkrun cartons are received about four times faster than Normal. Inbound work arrives all day and night, so receipt is not the bottleneck candidate.
- **Caveat:** the chart uses the adjusted clock, so hours are on the outbound-system clock.

### Block 7. The outbound side: orders, cartons and event order
**7a. Structure**
- **Result:** 35,092 cartons; each belongs to one DN type and one forwarder. 11 cartons show two release times and 12 hold lines from more than one order. 19,478 orders; the median order has 1 carton and 1 line (maximum 34 cartons, 89 lines). Top destinations by orders: HK 4,757, CN 3,685, JP 2,704, US 1,838, SG 1,360. Carton types by rows: ORDTOTE 36,859, ABC-P3A 13,067, ABC-P3 8,563, TROLLEY 2,023.
- **Insight:** most orders are single-line, single-carton, so carton and order level are nearly the same for most of the flow. The code also asserts that planned date, release time and final forwarder are constant within an order, which let us use order-level fields safely.

**7b. Which events exist, in what order**
- **Result:** Normal: order created, then packing confirmed, then cargo released, in 100% of 49,489 rows. Milkrun: Cyclone scan, then order created, then cargo released, in 100% of 13,129 rows. The Milkrun order is created after the carton is scanned.
- **Insight:** the event order is perfectly consistent, so a replay can rely on it. The Milkrun order being created *after* the scan suggests the order is created automatically from the scan (Question 21), but that is not in any file.

### Block 8. The join: inbound LPN = outbound Carton ID
**8a. Build the join**
- **Method:** aggregate to carton level on each side and join on ID. Also test every other plausible outbound column against the inbound LPN.
- **Result:** 11,480 distinct inbound LPNs (7 appear under two ASNs). **5,564 cartons join**: all are outbound "Milkrun from ABC" and inbound "Milkrun to ABC". That is 15.9% of 35,092 cartons and 70.7% of 7,869 outbound Milkrun cartons, so **84.1% of outbound cartons share no ID with any receipt**. Inbound LPN matches no other outbound column (LP, External Order Key, Order Key, Wave Key, Loading List): zero rows.
- **Insight:** this is the structural limit of the project. Exact traceability is a Milkrun-only capability. Slide 2's 84% and the "Milkrun first" design decision both come from here.
- **Caveat:** DSV confirmed LPN = Carton ID for Milkrun. Whether another key exists for Normal is still open (Question 2).

**8b. Both ends of the Milkrun flow**
- **Result:** inbound Milkrun LPNs: 7,621, of which 5,564 match and 2,057 do not. Outbound Milkrun cartons: 7,869, of which 5,564 match and 2,305 do not.
  - The 2,305 unmatched outbound cartons were scanned between 6 Aug 14:24 and 16 Aug 21:17, all before the first Milkrun receipt in the data (17 Aug 02:21 on the adjusted clock). So 100% were received before the window.
  - The 2,057 unmatched inbound cartons were received (adjusted) from 17 Aug 07:10 to 24 Aug 20:08, median 23 Aug 19:59. The outbound report ends at the last release, 24 Aug 21:40.
- **Insight:** both gaps have an innocent explanation. Unmatched outbound cartons were received before the data started, and unmatched inbound cartons were received late in the week and had not been released when the extract ended. They are "out of window", not errors, and the twin should label them that way (Assumption A3).
- **Caveat:** "most were not yet released" is the natural reading, but the data cannot prove those cartons are still in the building.

**8c. The 84% picture (slide 2)**
- A 100-square waffle: 16 blue (traceable), 84 orange (no shared ID). Each square is 1% of 35,092 cartons.

### Block 9. Timestamp alignment: is the 8-hour gap a clock offset?
- **Purpose:** test the DSV/course explanation on the data.
- **Method:** for each joined carton, compute Cyclone scan minus GR, raw and after adding 8 h to GR.
- **Result:** raw gap median 7.997 h, between 7.989 and 8.000 h, on every one of 5,564 cartons. After +8 h the scan falls 0 to 39 seconds before GR (median 10 s) on every carton.
- **Insight:** the 8 h is a time-zone difference. On the same physical moment, the receiving system and the sorter record the same event, and after correction they agree to within a minute. So receipt-to-sorter is effectively zero, and any analysis that leaves the 8 h in will overstate receipt-based times by 8 h.
- **Caveat:** this says the two clocks differ by 8 h; it does not tell us which one is "local time".
- **Slides:** "likely a clock offset (to confirm)" on slide 3 is now confirmed.

---

## Part D. Where the time goes [exploratory]

### Block 10. Stage-by-stage timing of a Milkrun carton (5,564 joined)
- *Setup for Blocks 10 to 14 (Block 9b):* adds the derived columns once so every later block uses the same definitions: `gr_adj` and `dock_adj` (inbound time plus 8 h), and `wait` (hours from order created to cargo released) for joined cartons, all cartons and orders.
- **Method:** compute each hop with the offset applied: dock to GR, GR to scan, scan to order created, order created to release, and combined spans.
- **Result (hours):**

| Hop | 25% | Median | 75% | 90% |
|---|---|---|---|---|
| dock to GR | 0.57 | 0.87 | 1.60 | 3.17 |
| GR to scan (adjusted) | 0 | 0 | 0 | 0 |
| scan to order created | 0.30 | 0.39 | 0.48 | 0.91 |
| **order created to released** | **22.80** | **32.79** | **51.14** | **70.59** |
| GR to released (adjusted) | 23.44 | 33.52 | 51.95 | 70.80 |
| dock to released (adjusted) | 24.68 | 35.77 | 52.75 | 72.38 |
| GR to released (raw, no offset) | 31.44 | 41.52 | 59.95 | 78.80 |

  The wait after order creation is 98.8% of receipt-to-release for the median carton (97.8% median-of-medians; 95.6% of dock-to-release). Using the raw, uncorrected GR gives 79%, which is where "at least four fifths" came from.
- **Insight:** a Milkrun carton spends about 1.3 h being received, scanned and turned into an order, then about 33 h waiting to be handed to a forwarder. The first part is quick and the second is nearly everything. The what-if therefore sits on the release step.
- **Caveat:** these are medians of joined cartons, i.e. cartons that *have* been released. Cartons still waiting are missing (Block 11c). The stage bar chart on slide 3 should now show receipt-to-scan as about zero, not 8 h.

### Block 11. Release wait: distribution, flow comparison and the survivor caveat
**11a. Distribution (joined cartons)**
- **Result:** shortest 1.1 h, median 32.8 h, 90th percentile 70.6 h, longest 135.3 h. 27.6% are released within 24 h, 72.7% within 48 h, and 8.4% wait more than 72 h. The histogram is right-skewed with a small cluster near 125 to 135 h.
- **Insight:** the median hides a long tail. One in twelve cartons waits over three days.

**11b. Do other flows wait too? (all cartons)**
- **Result:** median order-created-to-release wait: Normal 58.4 h (middle half 36.8 to 110.9 h; split 22.5 h order-to-packing and 30.5 h packing-to-release); Milkrun from ABC 35.5 h (23.6 to 62.4); Milkrun to ABC 3.4 h (491 cartons); Scrap 170 h (12 cartons).
- **Insight:** the wait is not a Milkrun quirk. Normal cartons wait longer, and the packing-to-release half (30.5 h) is as long as the Milkrun wait. The Milkrun wait for all 7,869 cartons (35.5 h) is a little higher than for the 5,564 joined (32.8 h) probably because the unjoined ones include cartons received before the window, which had already been waiting longer.
- **Caveat:** Normal timing uses packing as the middle event because Normal has no Cyclone time.

**11c. Survivor caveat**
- **Result:** every outbound row has a release time, so the report only lists cargo that has been released. 161 orders were created in the final 24 h before the last release. Orders by created date are thin until 9 Aug and peak on 15 and 16 Aug (2,718 and 3,701).
- **Insight:** orders that were created late in the window and still waiting are not in the file, so all wait statistics are understated, and the share of late orders (Block 14) may be too.

### Block 12. Release is batched: when does cargo leave?
- **Method:** distinct release timestamps, release by hour and weekday, and median wait by the weekday the order was created.
- **Result:** 3,449 distinct release times for 35,092 cartons (889 distinct minutes). The largest single timestamp releases 178 cartons (17 Aug 16:10:41). 23.8% of cartons are released in the 18:00 hour. Monday carries 36.1% of releases. Median wait by weekday created: Mon 37.9 h, Tue 44.2, Wed 56.3, Thu 39.4, **Fri 75.6, Sat 80.3**, Sun 48.7. Orders created per day are highest at the weekend (Sat 4,174, Sun 4,833).
- **Insight:** cargo leaves in waves, mostly in the late afternoon, and Monday is the big catch-up day. Orders created on Friday and Saturday wait about twice as long as those created Monday or Thursday, consistent with a weekend with few pickups. This explains why a release can be "late by one day" without anything being wrong in the warehouse. It also explains the shape of the what-if curve (Block 18).
- **Weekday intervals (added):** bootstrap 95% intervals for the median wait by weekday created, in hours: Mon 37.9 (37.1 to 39.0), Tue 44.2 (41.7 to 46.5), Wed 56.3 (55.2 to 58.4), Thu 39.4 (38.3 to 41.1), Fri 75.6 (75.2 to 76.0), Sat 80.3 (78.8 to 81.5), Sun 48.7 (48.1 to 49.0). The Friday and Saturday intervals sit far above Monday and Thursday, so the weekday difference is real in this extract.
- **Caveat:** a pattern, not a cause. We do not have forwarder pickup schedules.

### Block 13. Forwarders: same step, different wait
**13a. Joined Milkrun cartons by final forwarder**
- **Result:** 52 forwarders carry the 5,564 cartons; 13 have 100 or more. The six busiest:

| Forwarder | Cartons | Median wait (h) | Middle half (h) |
|---|---|---|---|
| 089 | 848 | 22.7 | 15.7 to 32.1 |
| 064 | 336 | 29.3 | 21.3 to 39.0 |
| 083 | 590 | 29.8 | 26.7 to 42.3 |
| 026 | 413 | 32.1 | 17.6 to 40.6 |
| 098 | 455 | 35.7 | 27.8 to 52.8 |
| 033 | 501 | 36.3 | 30.0 to 52.6 |

  Kruskal-Wallis across the 13 forwarders with 100+ cartons: H = 791, p about 1e-161. Among those 13, forwarder 013 sits far out at a 76 h median (102 cartons).
- **Insight:** forwarder identity explains a large part of the spread; this is not noise. Slide 3's "23 to 36 hours" range is correct for the six busiest.
- **Caveat:** the test says the differences are real. It does not say *why*. The cause (pickup schedule, destination mix, contract) is a DSV question.

**13b. Is it specific to Milkrun?**
- **Result:** 30 forwarders have 30 or more orders in both flows. Spearman rank correlation of their median waits is **0.78**.
- **Insight:** forwarders that are slow for Milkrun are also slow for Normal, so the effect belongs to the forwarder, not the flow. That supports putting the what-if on the release step for all flows.

**13c. Is the forwarder effect just flow, weekday and time of day? (added)**
- **Method:** ordinary least squares (numpy) of log(wait) on flow, weekday created and 6-hour block of creation, fitted on 18,689 orders from the 42 forwarders with 30+ orders; then the same model with forwarder added. The adjusted ratio is a forwarder's typical wait divided by what flow, weekday and time of day alone would predict (1.0 = as expected).
- **Result:** flow, weekday and time of day explain 15.3% of the variation in log-wait; adding the forwarder lifts it to 27.0% (forwarder adds 11.7 points). The rank correlation between the raw median wait and the adjusted effect across forwarders is 0.96. Adjusted ratios: 084 0.57, 099 0.63, 087 0.65 at the fast end; 078 1.95, 013 2.12, 039 2.13 at the slow end. Forwarder 013 and 039 wait about twice as long as their mix would predict.
- **Insight:** the forwarder effect is not a side effect of which days or hours its orders were created. The ranking barely changes after adjusting, so the raw medians can be used as a ranking.
- **Caveat:** 27.0% means most variation is still unexplained. It is a description, not a causal model. Exploratory.

---

## Part E. Planned dates (in scope)

### Block 14. Late = released on a later day than the Planned Post Date
**14a. Overall**
- **Method:** keep orders with a planned date; late means the release *date* is after the planned date.
- **Result:** 18,965 of 19,478 orders have a planned date (blank on 501 "Milkrun to ABC" and 12 Scrap). **4,436 are late = 23.4%.** 75.5% are released on the planned day. Late orders are mostly one day late (median 1, mean 1.6, maximum 56 days). Day distribution: on the day 14,314; +1 day 3,377; +2 402; +3 409; +4 67; +5 49; 6 or more 132. By flow: Milkrun 4,758 orders, 1,148 late (24.1%); Normal 14,205, 3,287 late (23.1%). 215 orders (1.1%) were released before the planned day. 181 orders have a planned date earlier than the day they were created.
- **Insight:** lateness is mostly "a day late", not "weeks late", and the rate is the same in both flows. Those 181 orders can never be on time as recorded.
- **Caveat:** "late" is our working definition (Assumption D1; Question 6 with DSV). Calendar-day comparison hides how close to midnight a release was.

**14b. By forwarder (slide 2 middle chart)**
- **Result:** 66 forwarders overall; 42 with 30+ orders; **9 are 90% or more late**: 112 (787 of 787), 013 (313 of 313), 018 (99 of 99), 069 (80 of 80), 080 (170 of 170), 092 (30 of 30), 090 (82 of 83), 096 (153 of 157), 044 (448 of 471). The median forwarder is 17.5% late. The nine handle 2,190 orders (11.5%) but account for **48.7% of all late orders**.
- **Insight:** half of all lateness sits with nine forwarders. That is the single best place to look, and the slide 2 claim ("9 forwarders are 90%+ late") is verified.

**14c. Is lateness the same as a long wait?**
- **Result:** across the 42 forwarders, Spearman(median wait, late rate) = 0.61. By release day: 17 Aug 7.6% late (3,523 orders), 18 Aug 22.1%, 19 Aug 24.8%, 20 Aug 29.6%, 21 Aug 48.9%, 22 Aug (Sat) 82.7% (341 orders), 24 Aug (Mon) 5.2% (2,963).
- **Insight:** long waits and lateness are linked but not identical (0.61). The day pattern climbs through the week and resets on Monday, which fits the weekend batching in Block 12.
- **Caveat:** the day pattern mixes real effects with window edges (the extract starts at the first release and drops unreleased orders). Do not quote the daily rates as a trend.

**14d. How sensitive is the 23.4%? (added)**
- **Method:** (1) recompute the late rate under four definitions; (2) split orders by planned date to expose the edges of the extract; (3) repeat the forwarder test in the fully covered window.
- **Result, definitions:** A, released on a later calendar day than planned (working definition): 4,436 orders, **23.4%**. B, released 2 or more days after the planned day: 1,059, **5.6%**. C, released after 18:00 on the planned day or later: 10,775, **56.8%**. D, released after noon on the day after the planned day: 3,798, **20.0%**.
- **Result, edges:** orders planned before 17 Aug: 439, all late (only late ones can be seen, because the extract starts at the first release). Orders planned 24 Aug or later: 2,877, none late (only on-time ones can be seen). Orders planned 17 to 23 Aug: 15,649, **25.5% late**. Even this window is slightly low, since orders released after 24 Aug are missing.
- **Result, forwarders:** in the covered window 39 forwarders have 30+ orders and 9 of them are 90%+ late. They hold 14.3% of orders and 54.9% of late orders. Eight are the same as before; 071 is new and 092 drops out (too few orders).
- **Insight:** the headline depends on the definition by a factor of ten, and on the window by about two points. The nine-forwarder finding holds up either way, which makes it the safer thing to show. This is why Question 6 (what counts as late) matters.
- **Caveat:** 25.5% is also a lower bound. Quote 23.4% with its definition, or the covered-window figure with its date range, never one without the other.

### Block 15. Forwarder changes: default vs final
- **Result:** 18,958 orders have both forwarders. The final differs from the default on **62.0%** (Milkrun 62.1%, Normal 62.0%). 102 distinct default forwarders become 66 final ones. Most common swaps: 082 to 083 (2,691 orders), 088 to 089 (1,432), 025 to 026 (1,161), 063 to 064 (804), 099 to 098 (575). **72.3% of changed orders swap to a neighbouring code (differing by 1).** Late rate is 18.9% when the forwarder changed vs 30.6% when unchanged.
- **Insight:** the "62% forwarder change" headline is probably inflated by pairs of codes that belong to the same carrier (for example service levels or sites). 102 default codes collapsing into 66 final ones fits that. It is also why the lateness of "changed" orders is *lower*, which would be odd if the change were a genuine escalation.
- **Caveat:** hypothesis. The anonymised numbering could be a coincidence of how names were assigned. Ask DSV (Question 7) before presenting 62% as "switching".

**15b. Testing the sister-code hypothesis (added)**
- **Method:** two independent clues. (1) For each default forwarder with 100+ changed orders, how concentrated are its changes on one final forwarder? (2) Does that final code ever appear as a default code on any order? (A real switch between carriers would also leave orders where the final code was the default.) A third check, country-mix similarity against the final code's unswapped orders, can only be run where such orders exist.
- **Result:** 15 default forwarders have 100+ changed orders; 13 of them send 90% or more to a single final forwarder (082 to 083, 088 to 089, 063 to 064, 099 to 098, 049 to 103, 104 to 105, 012 to 013, 100 to 101, 121 to 122 at 97 to 100%; 025 to 026 at 53%). **In 9 of the 10 biggest swaps the final code never appears as a default code.** The one testable pair (099 and 098, 982 unswapped orders) has a country-mix similarity of 0.80, against 0.25 on average for other final codes.
- **Insight:** the final code looks like the re-coded version of the default code: one carrier, two code lists. That would make "62% switch forwarder" a coding artefact. It also explains why the nine "90% late" forwarders (013, 112 and others) sit at the end of such pairs.
- **Caveat:** still a hypothesis. It is consistent with the evidence, but only DSV can confirm it (Question 7). Until then the wording is "final code differs from default code", never "changed carrier".

---

## Part F. Inference

### Block 16. Back-test: SKU + vendor lot + "latest receipt before the order"
**16a. Back-test where the truth is known**
- **Method:** for the 9,313 outbound Milkrun rows (5,564 cartons) we know the true ASN from the exact carton ID. Pretend we do not. Candidates = inbound receipts with the same SKU and vendor lot posted (GR + offset) at or before the order was created. Pick the latest. Score the pick. Four variants: offset 0 or 8 h; Milkrun candidates only or all inbound types.
- **Result:**

| Offset | Candidates | Unique by SKU+lot alone | Unique after time filter | True ASN among candidates | Latest-receipt pick correct |
|---|---|---|---|---|---|
| +0 h | Milkrun only | 27.0% | 40.5% | 100% | 72.8% |
| +0 h | all types | 21.3% | 35.7% | 100% | 71.4% |
| **+8 h** | **Milkrun only** | 27.0% | 48.6% | 100% | **90.7%** |
| +8 h | all types | 21.3% | 42.9% | 100% | 90.4% |

- **Insight:** the right ASN is *always* among the candidates, but SKU+lot alone is unique only about one time in four. Adding "latest before the order" makes it right about 91% of the time once the offset is applied. The 72.8% and 27% in the Assumption Log reproduce exactly in the +0 h rows, so that log figure was computed without the correction and is too low.
- **Caveat:** this is Milkrun only, where receipts and orders are tightly linked in time. We cannot validate the rule for Normal, so any inferred Normal link must be shown as "inferred".

**16b. How much of Normal could inference even reach?**
- **Result:** 22,374 distinct Normal (SKU, lot, order-time) combinations. Only 22.4% have any inbound receipt of that SKU+lot before the order (18.9% counting Normal-type receipts only). Only 33.7% of the 10,222 distinct Normal SKU+lot pairs appear anywhere in the week's inbound. 40.7% of inbound SKU+lot pairs appear on more than one ASN.
- **Insight:** the limit for Normal is not just the matching rule, it is missing data: for most Normal shipments the stock was received before the extract began. So the realistic design is exact trace for Milkrun, inferred and tagged for the rest, and honest about coverage. This is the "breadth for traceability" trade-off on slide 4.

**16c. Does a carton with many rows count many times? (added)**
- **Method:** the back-test in 16a is per row. 16c recomputes accuracy per carton and resamples whole cartons 500 times for a confidence interval.
- **Result:** row-level accuracy 90.7%; carton-level, the average share of rows right is 90.2% and **89.1% of cartons have every row right**. The 95% interval for row accuracy, resampling cartons, is **89.9% to 91.5%**. Cartons with 1 to 4 rows are all within 88% to 91%.
- **Insight:** cartons with several rows do not drive the result, and the number is stable. The slide can say "about 90%" with confidence on Milkrun.
- **Caveat:** Milkrun candidates only, where the ground truth exists. It says nothing about Normal accuracy.

---

## Part G. Prototype logic

### Block 17. A unified event table and a time-slider snapshot
**17a. The event table**
- **Method:** stack all events into one long table: carton, event, time, flow. Milkrun gets dock-in, goods receipt (both shifted +8 h), Cyclone scan, order created, release. Normal gets order created, packing confirmed, release.
- **Result:** 114,889 events for 34,587 cartons (the 505 Milkrun-to-ABC, Scrap and Stock Transfer cartons are left out). Counts: Milkrun 7,869 each of Cyclone, order created, released and 5,564 each of dock-in and receipt; Normal 26,718 each of order created, packing, released.
- **Insight:** this is the core data structure of the replay. Everything else on the screen (time slider, carton trace, counts) is a query on this table.

**17b. One carton's journey**
- Carton 4038421004001 (ASN 0000032011, forwarder 026): dock 20 Aug 08:09, receipt 09:00:54, Cyclone scan 09:00:48, order created 09:28:24, released 21 Aug 18:15:50. About 1.3 h to an order, then about 33 h to release.
- **Insight:** the picture shows the story of the project in one glance: four events within 80 minutes, then a long wait.

**17c. The time slider**
- **Result:** a `snapshot(t)` function. At 18 Aug 12:00: 8,549 orders awaiting release, 959 of them already past planned date. At 20 Aug 12:00: 5,615 and 913. At 22 Aug 12:00: 2,321 and 223. Open orders fall from about 9,000 to 10,000 on 17 Aug to under 3,000 by 22 Aug.
- **Insight:** this is the "visibility" feature working on real data: pick a moment, see what was open and how much was already overdue.
- **Caveat:** the right-hand fall is partly artificial because the file only has released cargo. From the first release (17 Aug 03:07) the left side is reliable, because any order open then would be released later and so is in the file.

### Block 18. The one what-if: release earlier on the slowest step
- **Method:** if cargo were handed over X hours earlier (never before the order was created), what share of orders would be released on or before their planned day? Sweep X from 0 to 48 h for all orders, the nine worst forwarders, and everyone else.
- **Result:**

| | 0 h | 6 h | 12 h | 24 h |
|---|---|---|---|---|
| all orders | 23.4% | 23.4% | 20.0% | 5.7% |
| 9 forwarders 90%+ late | 98.7% | 98.7% | 78.2% | 16.2% |
| all other forwarders | 13.6% | 13.6% | 12.4% | 4.3% |

- **Insight:** lateness is a step function of release time. Pulling release forward by 6 h changes nothing, because most releases are in the late afternoon and stay on the same calendar day. It only starts to move after about 10 h, and most of the drop comes between 12 h and 20 h, because an 18:00 release needs roughly 18 h or more to cross back over midnight. For the nine worst forwarders, a day earlier cuts lateness from 99% to 16%. This is sensitivity, not a forecast.
- **Caveat:** assumes the forwarder could collect earlier, which we do not know. It is arithmetic on observed data, with no behavioural model. The addendum asks for one limited what-if presented as a prototype; this is it.

### Block 19. Rule-based, explainable actions
**19a. Back-test the rule "still unreleased at HH:00 on the planned day"**
- **Result:**

| Cut-off | Flagged | Finally late | Precision | False alarms |
|---|---|---|---|---|
| 08:00 | 17,496 | 3,469 | 19.8% | 14,027 |
| 12:00 | 17,310 | 3,807 | 22.0% | 13,503 |
| 15:00 | 16,254 | 3,941 | 24.2% | 12,313 |
| 18:00 | 10,419 | 4,080 | 39.2% | 6,339 |
| 21:00 | 5,186 | 4,199 | 81.0% | 987 |

- **Insight (corrected):** recall is not 100%. An order created after the cut-off on its planned day cannot be flagged by that rule, so recall rises with the cut-off hour; in the fully covered window it is about 82% at 08:00 and 95% at 18:00 (3,779 of 3,997 late orders). The real trade-off is warning time against false alarms. The table above covers all orders with a plan date; in the covered window the 18:00 rule flags 8,933 orders and 42.3% end up late. 18:00 is a sensible default (39% precision with some time left to act), 21:00 is almost certain but too late for most actions.
- **Caveat:** the thresholds are ours (Assumption R1). Test them at the mid-project consultation.

**19a (added). The 18:00 rule for every planned day.** Run separately for each planned day in the covered window, precision of "unreleased at 18:00" was: 17 Aug 42.5% (2,313 flagged), 18 Aug 21.2% (2,783), 19 Aug 52.2% (1,256), 20 Aug 67.4% (1,763), 21 Aug 43.0% (802); 22 and 23 Aug have too few orders (20 and 11) to judge. The single 39% hides a range of 21% to 67%, so the cut-off should be tuned with DSV rather than fixed. The notebook now shows a recall column too, with the corrected values (an earlier version said recall is 100% by construction, which is wrong once orders created after the cut-off are excluded).

**19b. The rule table**
- **Result** at the example moment 20 Aug 18:00: R1 planned-date risk, 1,763 orders planned for 20 Aug are still open; R2 forwarder backlog (20 or more orders open longer than 24 h), 24 forwarders, led by 033 (442), 026 (327), 013 (308), 083 (238); R3 quantity, 109 lines at exactly 2x in 32 ASNs; R4 data sanity, 181 orders with a planned date earlier than creation.
- **Insight:** each action carries its rule and its reason, as the addendum requires, and all thresholds sit in one dictionary (`TH`). These four rules already map to the Diagnosis and Recommendation levels.
- **Caveat:** R1 is evaluated at one moment only, and R2's 24 h and 20-order thresholds are placeholders.

---

## Part H. Wrap-up

### Block 20. Findings table and the corrections the slides need
- **Result:** an eleven-row table (F1 to F11) with the number, the block, whether it is in scope or exploratory, and confidence. F11 is the edge-bias finding (Block 14d). In the core build the exploratory rows F4 to F6 are dropped. A second table lists the slide and log wording that the notebook changes:

| Slide | Current wording | What the data now says |
|---|---|---|
| 2 | "1,462 ASNs" | 1,481 ASNs in the report (1,462 have a dock time) |
| 2 and 3 | "sorter scan always ~8 h after receipt, likely a clock offset" | confirmed time-zone offset; about 0 s once corrected |
| 3 | "at least four fifths of the total" (79%) | about 99% of receipt-to-release with the offset applied; "at least four fifths" is still true but understates it |
| 3 | receipt-based total 41.5 h | 33.5 h |
| Assumption Log T2 | "latest receipt picks the right ASN 72.8%" | 72.8% is without the +8 h; 90.7% with it |
| Assumption Log D4 and Q7 | "62% of orders ship with a different forwarder" | probably a code mapping: in 9 of the 10 biggest swaps the final code never appears as a default code; do not call it switching until DSV answers |

### Block 21. Self-checks
- **Method:** 28 assertions (27 in the core build, which has no median-wait check) on the headline numbers (row counts, 109 lines in 32 ASNs, 5,564 joined, the 39 s offset bound, the 9 of 42 forwarders and so on). The notebook stops with an error if any one changes.
- **Result:** all pass in both builds. The added checks cover the 9-of-10 final-code-never-default result and the 90.7% back-test.
- **Insight:** this lets the team rerun the notebook on a refreshed extract and see immediately which slide numbers moved.

### Block 22. Oddities and questions for DSV
- **Result:** 7 inbound LPNs under two ASNs; 11 outbound cartons with two release times; 12 cartons holding lines of more than one order; 148 surplus exact-duplicate outbound rows; 215 orders released before their planned day; 181 orders planned before they were created; 181 late orders released five or more days after plan; 19 ASNs with no dock-in time; Urgent Flag = Y on every row.

### Block 23. Export tidy tables for the Figma and demo work (added)
- **Purpose:** hand the prototype work clean data so the mock-ups and the working demo show real numbers.
- **Result:** `outputs/` holds seven CSVs, a README and `dsv_twin_tables.zip`: `events.csv` (114,889 events: carton, event, time, flow), `carton_journey_milkrun.csv` (5,564 joined cartons with stage times), `orders_lateness.csv` (18,965 orders with planned date, release, days late, forwarders), `asn_line_reconciliation.csv` (36,424 lines with ratio and status), `forwarder_summary.csv` (66 forwarders), `rules.csv` (the four explainable rules with example reasons) and `time_slider_snapshots.csv` (open and past-due counts at the three slider moments).
- **Insight:** all times are already on the outbound clock (+8 h applied to inbound), so the demo does not need to repeat the correction. The time slider is a query on `events.csv`.
- **Caveat:** exports contain only released cargo (see Block 11), so counts near the right edge of the window are understated.

---

## Questions this analysis suggests for DSV
1. **Q9:** are the 109 exactly-2x lines duplicate postings or genuine over-receipts? (Concentrated in three ASNs.)
2. **Q7:** are default and final forwarder codes sister codes of one carrier? (72% of swaps are to a neighbouring number.)
3. **Q6:** is "released on a later calendar day than planned" the right definition of late?
4. **Q8:** why do 181 orders have a planned date before they were created?
5. **New:** what are forwarder pickup schedules? (Release is batched at 18:00 and on Mondays; waits differ by forwarder.)
6. **Q4:** does every Normal carton go through the Cyclone? (It has packing but no Cyclone time.)
7. **New:** what is the Urgent Flag for, if it is "Y" on every outbound row?
8. **Q2:** is there any other identifier for Normal flows? (Inference reaches only about 22% of Normal orders even if the rule were perfect.)

## What this notebook cannot tell us
- **Why** anything is slow or late. It shows where and how much, never the cause.
- Anything about cartons still in the building at 24 Aug 21:40. The outbound report lists only released cargo.
- Whether the inferred link works for Normal. It was validated only on Milkrun.
- Whether the 8 h offset is exactly 8 h in daylight-saving periods. It was exact on all 5,564 joined cartons within one week.
