# Employee Leave Management (ELM) — pilot

This folder contains an initial backend-domain prototype for Assignment 6, produced during the local DeepSeek-Coder 6.7B pilot using Ollama and Aider.

## Included in this prototype

- Leave categories: CL, RH, SCL, EL, COL, and VL.
- Employee leave balances with a unique employee/type/year combination and a calculated available balance.
- Leave applications with dates, half-day flag, reason, station-leave flag, and a basic status field.
- Optional substitute nomination with pending/accepted/declined response states.
- Basic date validation for applications.

## Limitations / follow-up work

- This is an initial model-layer prototype, not a complete ELM implementation.
- Django app registration, migrations, API serializers/views/routes, React pages, role-based authorization, configurable policy/hierarchy, holiday and academic-calendar integration, SLA reminders, and full workflow transitions still need to be implemented and verified.
- No test or build result is claimed in this pilot PR.
