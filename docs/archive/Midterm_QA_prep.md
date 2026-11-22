# Midterm Q&A prep

_Exported from the team Google Doc "DSV Digital Twin – Team 2" on 23 Nov 2026. The Google Doc is the master copy._

## Midterm Q&A Prep – DSV Digital Twin (Team 2)

Nov 12, 2026 

### How to use this

There are 52 likely questions, grouped by deck section, each with a 20–40 second answer that uses only numbers from our slides and the assumption log. The person who presented a section takes its questions; anyone can add a number.
**Three lines to come back to when stuck**
- "The data was given to us without connections between inbound and outbound; the twin's first job is to put both reports on one clock and link what can be linked."
- "Every recommendation is a rule with its threshold shown, and a person approves it. Nothing changes the warehouse on its own."
- "Where DSV hasn't answered yet, it's one setting in our assumption log, so we can rerun in under an hour."
**Honesty rules for answers**
- Don't call the prototype "live" or "AI-powered". It replays one week of DSV's data (17–24 Aug).
- Projections are pace-based with a range, not a forecast model. A forecast model is Stage 2 and needs 4–8 weeks of data.
- If we don't know, say "DSV answered our follow-up on 11 Nov; this part is still open" or "that's a question for the consultation", and give our working choice.
- Use one number per fact: 25.5% released after the planned date (orders planned 17–23 Aug, 15,649 orders). Mention 23.4% only if asked about the whole extract.

### Background and problem

**Q1. What problem are you actually solving?** DSV told us they have data everywhere but not the information to decide quickly. The inbound and outbound reports don't connect: 84% of outbound cartons have no link back to their receipt. Our problem statement is how a digital twin can help managers see what is happening, why, and what to do next.
**Q2. Why does this matter to DSV and not just to us?** It maps to three of their own goals: the company mission of operational excellence through connectivity and transparency, Leverage to Lead 2030 (consolidating systems like the WMS), and the brief's ask for visibility, predictive insights and decision support. All three need records that connect, which the data doesn't yet have.
**Q3. Where does the 84% come from?** Only Milkrun cartons trace end to end: 5,564 of 35,092 outbound cartons, about 16%. The other 84% have no shared ID with an inbound receipt. DSV confirmed in answer A2 that no common linking identifier exists for the other flows.
**Q4. Why is "25.5% late and unflagged" a problem if goods still ship?** 3,997 of 15,649 orders planned 17–23 Aug were released on a later day than planned, and no field marks them. A supervisor only finds out by comparing two dates by hand. The twin makes that comparison for every order and ranks what to chase.
**Q5. Why mention the Urgent Flag?** It is "Y" on all 64,641 outbound rows, so it can't separate urgent from normal orders. It shows a field that exists but carries no signal, which is why we left it out of the twin. We've asked DSV what it is meant to mean (Q25).
**Q6. How big is one week at this site?** 1,481 inbound deliveries (36,533 lines) and 19,478 outbound orders (35,092 cartons on 3,246 handling units). Inbound is steady all week; outbound drops to 786 cartons on Saturday 22 Aug and 56 on Sunday.

### Scope and approach

**Q7. Why did you leave out bottlenecks, exceptions and forecasting?** The course addendum (7 Nov) set them out of scope. In scope are the six mandatory components: event replay, visibility at ASN, order, line and carton level, planned-date and quantity reconciliation, Milkrun traceability, a what-if prototype and explainable rules.
**Q8. Isn't one week too little for a digital twin?** It's enough to replay and diagnose: every event of the week sits on one clock and every line reconciles. It's not enough to forecast, so we label the what-if a prototype, show ranges, and list the forecast model as Stage 2 (4–8 weeks of data).
**Q9. Where does each of the six components stand?** Replay and drill-down run in the prototype. Reconciliation is analysed (36,533 of 36,533 lines match; 25.5% of orders released after plan). The Milkrun link is verified on 5,564 cartons. The staffing what-if runs in the prototype, and 17 of 22 rules run on the data.
**Q10. What is your method in one breath?** Five steps: profile and clean the data, rebuild one event model (+8 h fix, LPN = Carton ID link), validate it with independent recounts, analyse and design the rules, what-if and journeys, then prototype and walk it through the user journeys.
**Q11. How will you know you've succeeded?** Three criteria from the scope slide: actionable findings from DSV's own data, a working twin experience, and clear next steps for DSV. At the final we'll show each journey end to end on the real week.
**Q12. What tools are you using?** Python (pandas) on DSV's Excel files, read-only, for cleaning and analysis. The prototype is a web app built on the cleaned event data. Figma for the screen designs.

### Data and analysis

**Q13. Why add 8 hours to inbound times?** The inbound report is on a different clock. On all 5,564 matched Milkrun cartons, after +8 h the Cyclone scan falls 0–39 seconds before the goods receipt (median 10 s), so they are the same moment. The course confirmed the offset. It's one constant in our code.
**Q14. How did you clean the data?** Six steps: read IDs as text, treat blanks as missing, shift inbound +8 h, use the three-part line key, sum split rows, and count shipped quantity once per line. A sanity check found zero impossible time orders: no receipt before docking, no handover before order creation.
**Q15. What is the three-part line key, and why does it matter?** WMS ASN# + Ref Line# + Functional Packing. DSV confirmed (A5) that pack types like ITR and ITY count separately. With it, all 36,533 lines reconcile exactly. Without it, 109 lines looked doubled and would have been flagged as false over-receipts.
**Q16. How does the Milkrun trace work?** For Milkrun, the inbound LPN equals the outbound Carton ID, which DSV confirmed. 5,564 of 7,869 Milkrun cartons (71%) match. The other 2,305 were scanned into Cyclone by 16 Aug 21:17, before the first receipt in our window, so we label them "receipt outside window", not errors.
**Q17. Why can't you trace Normal-flow cartons?** There is no shared ID (DSV A2), and 54% of inbound LPNs are blank because packing wasn't confirmed at extract time. A SKU + Vendor Lot guess reaches only about 22% of Normal orders, so we show it only as "inferred", never as exact.
**Q18. How do you define "late"?** Released on a later calendar day than the Planned Post Date: 25.5% of 15,649 orders planned 17–23 Aug. Other definitions give 4.1% (2+ days) to 58.5% (after 18:00). DSV answered on 11 Nov that the Planned Post Date alone doesn't prove lateness, since release can move on purpose (a customer hold, a full flight). So we call it "released after the planned date" and treat it as a signal to review; it stays one setting.
**Q19. Why 25.5% on one slide and 23.4% elsewhere?** 23.4% is the whole extract (4,436 of 18,965 orders), which is biased at the edges of the week. 25.5% uses only plan dates fully covered by the data, so it's the fair number. Both may understate lateness, because the file lists only released cargo.
**Q20. Which forwarders drive lateness?** Late orders are concentrated: nine forwarders carry 55% of the orders released after plan (48.7% over the whole extract). A final forwarder that differs from the default is normal (DSV A6), so we don't flag swaps; most are neighbouring codes, which looks like a code mapping.

### Assumptions and data issues

**Q21. How many of your assumptions are actually backed?** 16 of 23: 11 confirmed by DSV in writing (4 of them on 11 Nov), 3 from DSV's brief and 2 verified in the data. Of the other 7, DSV qualified one (late) and six go to the consultation.
**Q22. What if DSV's answers change your definitions?** It already happened once: on 11 Nov DSV qualified "late", and we changed the label in an hour. Every assumption is one setting, so changing "late" or a threshold is a rerun in under an hour, not a rebuild.
**Q23. What's still open with DSV?** DSV answered all 7 follow-up questions on 11 Nov. What is left goes to the consultation: the required shipment timing per order, who carries out each action, the date that puts a row in each report, and how issues are prioritised.
**Q24. What data issues did you find?** 17 in the full files: 6 fixed or handled, 3 explained, 7 accepted limits we design around and label, 1 still open. DSV explained the 513 orders with no planned date on 11 Nov: they are internal Milkrun to ABC and Scrap moves. The open one is 148 duplicate outbound rows, flagged before any quantity totals.
**Q25. Doesn't 54% blank LPNs mean the data is bad?** No. DSV confirmed (A2) a blank LPN means packing hadn't been confirmed when the data was pulled. Most blanks describe the process: each flow fills a different set of fields. We show those rows as "not yet packed".
**Q26. Why keep the 181 orders planned before they were created?** DSV said (A4) they may be urgent orders. Dropping them would hide real work, so we keep them and label them "possibly urgent".

### Design and prototype

**Q27. Who are your users, and did DSV confirm them?** Five roles: inbound supervisor, outbound supervisor, planner, operations manager and data owner. They're our proposal, built from DSV's brief and their answer on what supervisors check first (B7). We'll confirm them at the consultation (PC-14); roles are one setting.
**Q28. Why does the outbound supervisor start on the Operations overview?** DSV said outbound supervisors check country code and final forwarder first (B7). So the overview opens with what is overdue by country and forwarder, and what has to leave before the 18:00 peak.
**Q29. Walk us through the screens.** Operations overview is home. Then Packing priorities (unpacked orders by lane), Outbound (overdue by age, down to cartons), Inbound (dock waits vs the usual), Milkrun trace (one carton from dock to forwarder), Trends, What-if, Data checks and Tasks. All run on one clock.
**Q30. What does the time slider do, and would a supervisor really use it?** It moves the whole twin to any moment: past to review what happened (e.g. at a shift handover), now to act, and ahead to the cut-off and end of today. Only "now" lets you approve tasks; the past is read-only. Settings let a user extend how far back or ahead it reaches.
**Q31. How do the projections work? Is that AI?** No. They're pace-based: today's pace so far, scaled to the cut-off, shown as a range. They feed "Prevent" cards, which are less urgent than cards based on what is already wrong. A real forecast model is Stage 2.
**Q32. How accurate are the projections?** Not very yet, and the Trends page says so: at Friday, 0 of 3 projections landed in their range. Pickups come in batches (24% of cartons leave in the 18:00 hour), so a smooth pace misses the jumps. That's the reason a model trained on more weeks is Stage 2.
**Q33. Two kinds of recommendations: what's the difference?** Now cards come from rules on the current state, like an order still here after its planned day; they're urgent. Prevent cards come from the projection, like a forwarder on pace to pass 20 overdue by noon; they're earlier warnings.
**Q34. Show us the architecture in one sentence.** A data layer cleans and aligns both reports into one event store; the twin model tracks every order's state by hour and runs the rules; the interface lets people see, drill down and approve. Visibility and diagnosis are in the prototype; prediction and recommendation grow in Stage 2.

### Rules, what-if and evaluation

**Q35. How do the rules work? Give an example.** Each rule has a trigger, a threshold, an action and an owner. OUT-01: an order still here after its planned day → book a pickup today, owned by the outbound supervisor. At 20 Aug 18:00 it fired on 573 orders. The rule, its data and its threshold show on the card.
**Q36. Why rules and not machine learning?** DSV's brief asks for explainable recommendations with the reason shown, and one week of data can't train a reliable model. A supervisor can check a rule against what they see on the floor; they can't check a black box.
**Q37. Where did the thresholds come from?** From the data where we could, e.g. "usual" dock wait is what 90% of deliveries meet (5.2 h). The rest are our working choices, kept in one table, DSV gave its KPIs and alert owners on 11 Nov but no thresholds, so the numbers stay ours.
**Q38. What happens when someone approves a card?** It assigns a task to an existing role; it doesn't change the warehouse itself. The work happens by phone or in DSV's systems. If a rule needs two roles, each ticks off its own part. The twin checks the next data and closes the task when the issue clears.
**Q39. What if the issue clears before anyone acts on the task?** The twin rechecks each task against new data. If the order has shipped, the task closes as "cleared by data", so nobody chases a problem that's gone, and it still shows in the history.
**Q40. Explain the what-if.** DSV suggested two (B9); we picked staffing. If volume rises by X%, how many people are needed, from a base of 20. In the prototype, +20% volume needs 29 people on a typical weekday (range 27–32), because 20 people match the week-average load and weekdays are busier. It's a simple ratio, labelled a prototype, because labour optimisation is out of scope and there's no labour data.
**Q41. How will you evaluate the twin?** Walk the four user journeys on the real week, check each figure against an independent recount in the notebook, and test the rules by replaying the week: did a rule fire before the problem showed up in the data? We'll ask DSV to try the journeys at the consultation.

### Plan, risks and value

**Q42. What are your main risks?** Four: DSV answers change a definition (high; one setting, rerun in an hour), only one week of data (high; what-if labelled a prototype with a range), the demo build slips (medium; Milkrun trace first in week 11, a recorded backup video in week 13), and roles not validated (medium; confirm at the consultation).
**Q43. What do you deliver at the final on 20 Dec?** The full design of all six components, the Figma mockups, and a working demo of the Milkrun trace, the rules and the what-if on DSV's real week, with handover notes on what DSV would need to run it on more data.
**Q44. What would DSV need to do to use this for real?** Three things: a regular data feed instead of a one-off extract (a connector to the WMS), a shared ID or packing confirmation for Normal-flow cartons so they can be traced like Milkrun, and their own KPI and alert definitions to replace our working ones. With 4–8 weeks of data, a forecast model becomes possible.

### Tough and curveball questions

**Q45. Isn't this just a dashboard?** A dashboard shows totals. The twin rebuilds the state of every order, line and carton at any hour from both reports on one clock, runs rules on that state, and lets you replay, act now or look ahead. Approved actions become tasks that the twin closes when the data shows the issue is gone.
**Q46. Your slides say "4 of 22" rules run, but the architecture says 17. Which is it?** 22 rules are written. Both slides now say 17: the current build runs 17 on the data. The rest need data we don't have or DSV's thresholds.
**Q47. The checklist says "9 screens" but you showed eleven.** Fixed: the checklist now says 11 screens, all on one replay clock.
**Q48. One slide says 9 forwarders carry 55% of late orders, another says 49%.** Checked: 55% is for orders planned 17–23 Aug; 48.7% is the whole extract. The slides now all use 55%.
**Q49. The what-if says "Result pending". Do you have a number?** Yes, it now runs in the prototype: +20% volume → 29 people on a typical weekday (range 27–32), from DSV's base of 20. What we still can't do is check it against DSV's real staffing ratios, which aren't in the data.
**Q50. Why not just ask DSV to add a "late" flag in the WMS?** That would help, and it's in our handover notes. But a flag alone doesn't say why it's late, who should act, or what is about to go late. The twin adds that context and the action.
**Q51. What would you do differently if you started again?** Ask DSV about definitions ("late", the Urgent Flag, KPIs) in week one rather than after the analysis, because so much depends on them.
**Q52. Has DSV seen or validated any of this?** They've answered our Round 1 questions (A1–B9) and our 7 Nov follow-up (on 11 Nov) in writing, and those answers are built in. The design and roles go to them at the mid-project consultation. If not yet shown, say so plainly.
