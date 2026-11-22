# DSV strategy alignment for the Digital Twin

Use this as a design check for every feature: each one should serve a DSV goal below and stay inside the course scope. Checked against DSV's own website on 19 Oct 2026. Coverage figure corrected 6 Nov 2026.

## Verified from DSV

**Leverage to Lead (DSV strategy to 2030)**: five priorities ([source](https://www.dsv.com/en/about-dsv/purpose-and-strategy)):
- Customers: grow with large global clients; better digital experience for smaller ones.
- Operations: improve the network and productivity, including through AI.
- Technology: consolidate core systems (TMS, WMS, ERP) and build digital capabilities.
- Leadership: develop talent and an AI- and technology-minded culture.
- M&A: integrate acquisitions well.

**Business philosophy** ([source](https://www.dsv.com/en-us/about-dsv/business-philosophy)):
- Door-to-door logistics.
- Continuous improvement "to eliminate redundancy and improve efficiency".
- "Converting fixed costs into controlled, visible costs".
- Four factors for choosing a logistics partner: capacity, flexibility, know-how and cost. These are selection factors, not KPIs DSV says it measures against.
- Innovation and value creation are mentioned only generally.

**Not verified, so don't cite**: autonomous inventory drones, transactional pricing, control towers, emissions, kitting and labelling, or a "six core variables" framework.

## How the twin maps to DSV's goals

| Twin level (brief) | Course scope item | DSV goal it serves |
|---|---|---|
| 1 Visibility | Event replay; ASN/order/line/carton view; Milkrun trace | Technology: one view across WMS exports instead of many systems. Visible costs: see where work and time sit. |
| 2 Diagnosis | Planned-date and quantity reconciliation | Continuous improvement: find redundancy and mismatches (e.g. 2x receipts, late releases). |
| 3 Prediction | One what-if prototype | Operations: productivity through data and AI, as a proof of concept only. |
| 4 Recommendation | Explainable, rule-based actions | Operations and Leadership: supervisors act on clear rules they can trust. |

## Design checks for future work

1. **Name the DSV goal.** Every screen or feature should name which goal above it serves. If none, cut it.
2. **Stay in scope.** The course addendum puts cycle-time, bottleneck and exception analysis, real-time integration, full inventory reconstruction, labour/equipment optimisation, 3D modelling and autonomous recommendations out of scope. Frame timing as plan vs actual or state at time t. Prof. Xu confirmed on 30 Oct 2026: choose the diagnosis within planned-date and quantity reconciliation and Milkrun traceability.
3. **Big picture first.** Open presentations with DSV's goal and the warehouse-wide week (TA feedback, Week 5), then show the detailed evidence.
4. **Be honest about coverage.** Only Milkrun traces exactly: 5,564 cartons, 16% of all 35,092 outbound cartons (71% of the 7,869 Milkrun cartons). Say so wherever traceability appears. Any Normal-flow link is approximate and must be labelled an assumption.
5. **Align times first.** Add 8 hours to inbound Dock and GR times before comparing them with outbound times.
6. **Cite only verified DSV claims.** Use the sources above.

## Questions and working definitions

Answers from Clarifications – Round 1 (30 Oct 2026), the questions still with DSV, and our working definitions are kept in the Assumption Log (`docs/team-doc/Assumption_Log.md`).
