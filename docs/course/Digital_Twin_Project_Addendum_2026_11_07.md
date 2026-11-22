# Digital_Twin_Project_Addendum_2026-11-07

_Exported from the team Google Doc "DSV Digital Twin – Team 2" on 23 Nov 2026. The Google Doc is the master copy._

Digital Twin Project — Course  Addendum 
**Client:** DSV 
**Version date: 7 November 2026** 
This document supplements DSV’s Digital Twin Project Brief (provided separately), which covers the background,  problem statement, available data, and Digital Twin maturity model. Please read that brief first. This addendum  defines the scope boundaries, data/tooling policies, and consultation arrangements specific to this course. 
Core Scope (mandatory) 
• Historical event-replay view of inbound and outbound operations 
• Operational visibility at ASN, order, line, and carton level 
• Planned-date and quantity reconciliation 
• A Milkrun handling-unit traceability module 
• One limited prediction or what-if simulation use case 
• Explainable, rules-based operational recommendations 
Out of Scope 
• Cycle-time, bottleneck, and exception analysis 
• Real-time system integration 
• Full inventory reconstruction 
• Labour and equipment optimization 
• 3D modelling 
• Autonomous (non-explainable) recommendations 
**Important constraint:** the provided data covers approximately one operational week only, and does not include  labour, equipment, capacity, or inventory-snapshot data. Any predictive component should therefore be treated and  presented as a prototype/proof-of-concept, not a production-grade forecast. 
Data & NDA 
Data is pre-anonymised by DSV — **no NDA is required**. 
AI Tool Use 
Students may freely use AI tools as part of their workflow, restricted to: **Claude, Gemini, and Microsoft Copilot /  MS Suite-integrated models**. Other AI tools should not be used with the provided data. 
Deliverable 
A design for the Digital Twin (concept, architecture, user journeys, key interactions) illustrated with a small proof of-concept — e.g., mockups (Figma or similar) plus a working demo of one or two of the mandatory components  using the provided data. This is a design/ideation exercise, not a request for a fully working end-to-end system.
Client Consultation 
DSV has offered up to two consultations with the team, if needed — e.g. one early on to confirm understanding of  the operational process, and one mid-project to validate the team’s process model and prototype direction. Teams  should use DSV’s design brief and data glossary as their primary reference and reach out for consultation as  genuinely needed. 
Clarifications – Round 1 (6 November 2026) 
Each question below is the one sent to DSV, followed by DSV’s answer in DSV’s own words. Notes added by the  course are labelled as such. 
**A1. Milkrun labels and movement types** 
Question: The glossary defines inbound "Milkrun from ABC", but the inbound report says "Milkrun to ABC", and  the outbound report contains both. The same cartons appear as "Milkrun to ABC" inbound and "Milkrun from  ABC" outbound, linked by LPN and Carton ID. What are the direction and viewpoint of each label? For AIFTA,  RMA, Stock Transfer and Scrap Order, please explain briefly their operational meaning and which process  milestones apply. 
• Milkrun: The inbound report should only contain “Milkrun to ABC.” There was an error in the glossary.  The outbound report may contain both “Milkrun to ABC” and “Milkrun from ABC.” 
• AIFTA: Refers to non-GST goods. The applicable normal process milestones should be followed for this  movement. 
• RMA: Refers to returned goods that are not in perfect condition. 
• Stock Transfer: Refers to the internal movement of stock between locations, including stock transferred  from the warehouse to ABC via the Milkrun process. 
• Scrap Order: Refers to goods designated for disposal. 
**A2. Traceability and report coverage** 
Question: About 54% of inbound LPNs are blank (about two thirds of Normal lines), and only Milkrun LPNs match  outbound Carton IDs. Is there a linking identifier in the reports for other flows? If not, should the prototype show  them as separate views? Which date field and window decide inclusion in each report? About 2,305 Milkrun  cartons have no matching receipt: could they relate to receipts before the inbound extract started? 
• The blank LPNs indicate that packing confirmation had not yet taken place at the time the data was  extracted. 
• There is no common linking identifier in the reports for the other flows. For the prototype, these can  therefore be presented as separate views. 
**A3. Cyclone and sequence** 
Question: What operational event does "Receiving of Shipping Carton into Cyclone" record, and which flows  should have it? For Milkrun, is it expected that the Cyclone timestamp precedes order creation, and what does  order creation represent? Should a missing packing confirmation on some flows be treated as not applicable? 
• For Milkrun, it is expected that the Cyclone timestamp can occur before order creation. The goods first  arrive at the warehouse and are received into Cyclone. The admin then creates the order to arrange for the  items to be shipped out. 
**A4. Planned dates** 
Question: Which actual event should be compared with Planned Post Date, and what tolerance applies? How  should students read the 181 orders whose planned date precedes their creation date? For "Milkrun to ABC" and  Scrap Order rows with no planned date, is reconciliation not applicable, or should another rule be used? 
• For cases where the planned date precedes the order creation date, this may be due to an urgent order  requirement.
**A5. Doubled quantities** 
Question: After counting the expected quantity once per ASN line and summing the received rows, 109 lines have  received quantity of exactly twice the expected quantity (95 Milkrun, 14 Normal). In 96 of them the line appears as  exactly two rows. Identical-looking rows also occur in lines that reconcile correctly. Is there a transaction identifier or reporting rule that separates valid multiple receipts from duplicate entries? 
• For duplicated lines with the same WMS ASN# and Ref Line#, the functional packing is different.  Different functional pack types, for example different product box types such as a pizza box, are counted  separately, which can result in what appears to be duplicated lines. 
• Example from DSV’s reply (rows from the inbound report): Ref Line# 00002 appears twice, once with  functional packing ITR and once with ITY, and each row has its own expected and received quantity. 

| **WMS ASN#** | **Ref Line#** | **SKU** | **Functional**<br>**Packing** | **Qty Exp** | **Qty Rcvd** |
|---|---|---|---|---|---|
| 0000031368 | 00001 | MA005933387 | ITR | 10,000 | 10,000 |
| 0000031368 | 00002 | MA001055002 | ITR | 17,500 | 17,500 |
| 0000031368 | 00002 | MA001055002 | ITY | 17,500 | 17,500 |

• Course note: when each inbound line is identified by WMS ASN#, Ref Line# and Functional Packing,  every line reconciles exactly to its expected quantity. The 109 “doubled” lines are not over-receipts. **A6. Forwarders** 
Question: About 62% of orders ship with a different forwarder from the default. When is that normal, and when  should it prompt a review? 
• It is normal for the actual forwarder to differ from the default forwarder, so this does not need to be treated  as an exception requiring review. 
**B7. First checks at the start of a shift** 
Question: What are the first one or two checks a supervisor makes at the start of a shift, and at which level (ASN,  order, line or carton)? 
• Inbound: Check the shipment reference, ASN and line-level information. 
• Outbound: Check the country code and final forwarder. 
**B8. Example rules for planned-date or quantity reconciliation** 
Question: Could you give one or two example rules for planned-date or quantity reconciliation, with the trigger, the permitted action and the responsible role? 
• DSV asked: Could you clarify what the students are trying to solve with this question? This will help us  provide a more relevant example rule, including the trigger, permitted action and responsible role. • Course note: the teams’ original questions on KPIs, alert triggers and supervisor actions were sent to DSV  on 7 November 2026 in reply. 
**B9. What-if scenario** 
Question: Which single limited what-if scenario would be most useful within the supplied data? For example, would showing how a later cargo handover changes the planned-date comparison be relevant, or would another scenario  suit better? 
• A more useful scenario would be to assess the impact of changes in the inventory or operational profile. For example: 
• If the proportion of non-AS putaway zone types (Column L in the inbound data) changes, how much  warehouse location capacity would be required? 
• If inbound and/or outbound volume increases by XX%, how many additional resources would be needed to operate effectively? For the baseline, the students may assume a current manpower level of 20 persons.
**Follow-up sent to DSV (7 November 2026)** 
• Course note: the following points were sent back to DSV on 7 November 2026. Their answers will be  added to this section when received. Until then, state your working assumption: whether the 2,305  unmatched Milkrun cartons were received before the inbound extract started; whether “Receiving of  Shipping Carton into Cyclone” is the sorter scan and whether every carton passes through it; whether “late” means released after the Planned Post Date; how lateness is judged for rows with no Planned Post Date;  when a quantity difference counts as an issue; and which KPIs, alert triggers and supervisor actions apply.
