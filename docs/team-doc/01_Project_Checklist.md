# Project Checklist (Timeline)

_Exported from the team Google Doc "DSV Digital Twin – Team 2" on 23 Nov 2026. The Google Doc is the master copy._

## DSV Digital Twin: Project Checklist (Team 2)

Last updated 15 Nov 2026. ☑ = done, ☐ = not done. Items marked (confirm) are my best reading of the documents; please correct them.

### 1. Key deadlines (all 11:59pm)

☑ 12 Nov 2026: Midterm (Week 9) presentation link posted in the Team Midterm Presentation tab (15%, group; 8 min talk + 2–3 min Q&A). Presented 13 Nov; feedback to come.
☐ 20 Nov 2026, 1:30pm: Regent field trip (3% participation, individual) OR attend Guest Lecture III (DSV) on 4 Dec, Week 12 Friday class
☐ 6 Dec / 10 Dec 2026: Final presentation link in the Team Final Presentation tab (15%, group; tab hidden for now). Check which session we are in.
☐ 20 Dec 2026: Final submission on eDimension (10%, group)
☐ 20 Dec 2026: Final individual reflection on eDimension (5%, individual)

## 2. Already done

☑ Project preferences submitted (Week 1)
☑ Project allocated: Project 7, Digital Twin (DSV)
☑ Individual pitch presented (Week 5, 12%)
☑ Team formed: Team 2 (all members are listed in the Team Formation tab)
☑ Round 1 questions submitted to DSV (the Hub says collection closed on 29 Oct)
☑ Prof. Xu's Round 1 answers received (30 Oct, recorded in team notes)
☑ DSV's Round 1 answers received (course addendum, 7 Nov 2026) and copied into the Assumption Log and Q&A tabs
☑ +8h timestamp alignment applied to inbound GR and Dock times
☑ Milkrun link checked on the data (LPN = Carton ID, 5,564 of 7,869 cartons)
☑ Inbound quantity reconciliation checked: with Functional Packing in the line key, all 36,533 lines match (DSV A5; the 109 "2x" lines were two pack types)
☑ Assumption log and DSV questions-and-answers log drafted
☑ DSV strategy alignment checked against dsv.com
☑ Full analysis notebook and block-by-block findings written (6 Nov): quantities, timestamps, forwarders, lateness, back-test, prototype rules
☑ Working prototype built on the full DSV files (event replay, drill-down, Milkrun trace, 17 of 22 rules, staffing what-if)
☑ DSV's follow-up answers (addendum version 11 Nov) copied into the Assumption Log and Q&A Log (13 Nov)
☑ Midterm deck finished, with appendix slides on each feature and one user flow; midterm presented (13 Nov)
☑ Q&A Log cross-checked against the Assumption Log: Q24–Q33 added so every open item has a question (13 Nov)

## 3. Midterm presentation (presented 13 Nov).

Guideline released 5 Nov: 8 minutes per team, strictly timed, plus 2–3 minutes of questions. One deck per team, linked in the Team Midterm Presentation tab by the end of Thursday 12 Nov (the running order is posted there). All 13 teams present in one class, which may run up to 30 minutes over. Feedback comes after the session, not on the spot.
☑ Background and problem (10%): the client, the problem, why it matters
☑ Scope and approach (20%): project scope and the framework of our method
☑ Progress so far (35%): findings and accomplishments, with the methods used and evidence
☑ Assumptions and open issues (15%, shared with the plan): working assumptions, pending DSV answers, data issues
☑ Plan to the final (15%, shared with assumptions): a week-by-week timeline and the main risks
☑ Presentation and Q&A (20%): clear, on time, sound answers
☑ Use the Core Scope (section 5) as the checklist; report any optional extensions separately
☑ Re-read the brief's version date and any "Clarifications – Round 1" section before finalising (addendum version 11 Nov checked)
☑ Confirm format, timing and grading criteria (Midterm Guideline, 5 Nov)
☑ Rehearse to 8 minutes and test the link in a private window before posting
☑ Check the running order in the Team Midterm Presentation tab
☐ Read the midterm feedback when it is released and add any changes to the plan (TA feedback so far: make the staffing what-if quantifiable and transparent; clarification email drafted 15 Nov)

## 4. Final deliverable (due 20 Dec).

DSV and the addendum ask for a design plus a small proof of concept
☑ Design: concept (midterm deck; refine for the final)
☑ Design: architecture (midterm deck; refine for the final)
☑ Design: user journeys (midterm deck and one user flow; refine for the final)
☑ Design: key interactions (shown in the prototype screens; refine for the final)
☐ Figma prototype or mockups (the addendum says "Figma or similar"); planned for W10 (Esther, Hern)
☑ Working demo of one or two mandatory components, using the provided data (the prototype covers all six; polish for the final)
☐ Confirm with the instructor whether a written report is also required, and the file format

## 5. Mandatory scope (all six must be covered)

☑ Historical event-replay view of inbound and outbound operations (in the prototype)
☑ Operational visibility at ASN, order, line and carton level (prototype drill-down)
☑ Planned-date and quantity reconciliation (notebook Blocks 5 and 14; in the prototype as "released after the planned date" review signals and quantity checks on the 3-part line key)
☑ Milkrun handling-unit traceability module (link verified; trace view in the prototype)
☑ One limited prediction or what-if use case, presented as a prototype (staffing what-if, DSV option b: +20% volume needs 29 people on a typical weekday, range 27–32; see WA-19)
☑ Explainable, rules-based recommendations (rule and reason shown; 17 of 22 rules run in the prototype)

## 6. Out of scope: do not build

Cycle-time, bottleneck and exception analysis; real-time integration; full inventory reconstruction; labour and equipment optimisation; 3D modelling; autonomous (non-explainable) recommendations.
☐ Resolve the conflict: DSV's timestamp note mentions cycle-time and bottleneck analysis, but the addendum excludes them. Until then, frame timing as event replay or plan versus actual. Working decision (6 Nov): at the midterm show only plan versus actual and event replay; keep the stage-timing analysis (notebook Blocks 10 to 13) as internal evidence.

## 7. DSV consultations (up to two)

☐ Consultation 1, early: confirm understanding of the operational process (confirm whether this has been used)
☐ Consultation 2, mid-project: validate the process model and prototype direction
☑ Follow-up of 7 Nov answered by DSV on 11 Nov (addendum version 11 Nov): unmatched Milkrun cartons, Cyclone, lateness (qualified), rows with no planned date, quantity escalation, and KPIs, alert owners and supervisor actions. See the Q&A Log and Assumption Log. Answered in Round 1: Q1, Q2, Q7, Q8, Q9, Q10 (suggestions) and Q15.
☐ Send the open questions in the second round: 13 are open (Q19, Q23–Q34) and 5 are partly answered (Q5, Q6, Q16, Q20, Q22). All are on the consultation agenda in the Q&A Log.
☐ After the midterm: add the team's second-round questions in the Team Formation tab
☑ DSV's "Clarifications – Round 1" received (6 Nov, in the course addendum dated 7 Nov)

## 8. Ongoing

☐ Check the Course Hub and the project folder's brief version date before each work session
☐ Keep short weekly notes on AI use and where it was wrong (for the reflection)
☐ Use only Claude, Gemini or Microsoft Copilot with the DSV data
☐ Cite only DSV claims that were verified; label any Normal-flow link as inferred

## 9. Prototype improvements (review of 15 Nov)

**Match DSV's 11 Nov answers (do first)**
☐ Change the "late" wording on Trends and the late chips to "released after the planned date" (a signal to review), to match the deck and logs
☐ Label the 70% on-time target as our working target, like the limits on Settings
☐ Update the label on rows with no planned date: internal movements, not judged late (DSV, 11 Nov)
☐ Add the shipping team as a team tasks can go to (forwarder and pickup issues), and match alert owners to DSV's list
☐ Use DSV's three KPI names on the overview: order release status, quantity discrepancies, shipment readiness
**Make the mandatory scope easier to see**
☐ Add a reconciliation summary: 36,533 inbound lines checked, 0 differences; 148 identical outbound rows to review
☐ Milkrun trace: label the 2,305 cartons with no receipt as "received before the extract (DSV)" and the 2,057 as "not yet shipped in this window"
☐ Rules: build the remaining 5 of 22 where the data allows, or mark them "not in this prototype" with the reason
**Label our own assumptions**
☐ Mark the 18:00 cut-off as our assumption until DSV answers Q28
☐ What-if (TA midterm feedback): show the calculation step by step: the rate (work per person), people needed, and the cost of extra staff; show the "same work per person" assumption on screen and make the baseline easy to update after Q32; build the putaway what-if only if time allows
☐ Tasks screen: say that tasks are saved in this browser only
**Before the final**
☐ Walk DSV through one task per role at the consultation and note where people get stuck
☐ Retake the appendix screenshots after these changes so the deck matches the prototype

W8 Mid Presentation Prep (done)
W9 Data Analytics (What to include in Digital Twin) – Tigger, Regnars
W10 Figma – Esther, Hern
W11 Working Demo – Mk, Alicia
W12 Presentation Slide Prep + Buffer
W 13 Final Presentation
