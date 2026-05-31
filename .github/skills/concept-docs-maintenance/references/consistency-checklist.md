# Consistency Checklist

Use this checklist before completing concept or living architecture documentation work.

## Source Model

- Active docs are direct HTML under `konzept/index.html` and `konzept/pages/**/*.html`.
- Archived Markdown under `konzept/archive/markdown-sources/` is reference only.
- No visible page should tell the user to edit Markdown or run a generator.

## Conceptual Consistency

- Service ownership still matches the intended architecture.
- Shop remains the external gateway and Saga orchestrator.
- Warehouse remains stock owner and concurrency boundary.
- Billing remains payment facade owner.
- Invoice remains async and non-blocking for successful checkout.
- Audit remains append-only and non-decisional.
- Data ownership and direct database access rules are not contradicted.

## Contract Consistency

- REST paths match controller stubs or implemented controllers.
- Event names match producers/consumers or are marked planned.
- Request/response shapes are not presented as final if DTOs are still `unknown`.
- Headers, idempotency keys, correlation IDs, and error formats are documented where relevant.
- Contract tests or test TODOs exist for critical service boundaries.

## Living Architecture Consistency

- Architecture-relevant changes are reflected in `konzept/pages/technische-architektur/` when that section exists or is being introduced.
- Implementation status is labeled as `Implemented`, `Planned`, `Prototype`, or `Needs decision`.
- Decision log entries include date, status, affected areas, consequence, evidence, and open questions.
- High-level concept pages are not overloaded with implementation noise.

## HTML Site Consistency

- `konzept/index.html` chapter cards and quick links are updated if pages changed.
- Sidebars include new/renamed pages where needed.
- Breadcrumbs, page titles, lead text, TOC, and pagination are coherent.
- Relative links work from each HTML page location.
- Shared styles are reused before adding CSS.

## Validation Searches

Search active HTML for stale references:

```text
Markdown-Quelle
build_concept_html
README.md
href="*.md
```

Run the local href check from `SKILL.md` after structural link edits.