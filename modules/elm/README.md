# Employee Leave Management (ELM) — DeepSeek-Coder 6.7B pilot

This is a limited backend pilot for Fusion ERP Lab Assignment 6, not a complete
implementation of the ELM specification.

## Included
- Leave types CL, RH, SCL, EL, COL, and VL.
- Policy records, published calendar-day records, annual balances, applications,
  and substitute nominations.
- Employee identity references use stable numeric IAM IDs; this service does not
  create a second local employee/authentication table.
- Service helpers for basic date counting, published RH date checks, overlap checks,
  balance checks, substitute consent, and draft submission.
- Basic day-counting unit tests.

## Rules represented
- EL/COL/VL count continuous calendar dates, including weekends and closed holidays.
- CL/SCL/RH count weekdays excluding published closed dates.
- RH must match a published RH date.
- Half-day leave is one-day CL and counts 0.5.
- A substitute cannot be the applicant; accepted consent moves an application from
  awaiting-substitute to review.

## Known limitations
This pilot does not yet implement the full ELM workflow. It does not yet include
institutional hierarchy/role authorization, API serializers and views, frontend pages,
a locally generated/verified migration, atomic balance reservation and debit, cross-year
balance splitting, full calendar publication lifecycle, RH effective-date/version
management, VL-to-EL conversion, resumption and extension, post-approval cancellation
workflow, offline sanctioned records, SLA reminders/escalation, or export/print views.
Employee-category eligibility and final sanction routing need integration with the
institution's authoritative configuration. Tests have not been executed in the remote
repository environment; run them locally before treating the implementation as verified.

## Tooling for the pilot
- Model: DeepSeek Coder 6.7B (deepseek-coder:6.7b, Q4_0)
- Runtime: Ollama
- Coding agent: Aider v0.86.2
