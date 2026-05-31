# Technical Architecture Section Reference

Use this reference when creating or maintaining the dedicated technical architecture section in the concept site.

## Purpose

The `Technische Architektur` section is separate from the broader concept chapters. It tracks the implementation-near architecture that emerges while coding: actual service modules, runtime dependencies, contracts, decision deltas, deployment details, and verification state.

The section should answer: "What architecture does the current codebase actually have, and how does that relate to the intended concept?"

## Target Location

Create and maintain pages under:

```text
konzept/pages/technische-architektur/
```

Recommended starting pages:

| Page | Purpose |
| --- | --- |
| `index.html` | Technical architecture overview, current architecture status, links to subpages. |
| `service-boundaries.html` | Actual service responsibilities, modules, ownership, public/internal interfaces. |
| `runtime-flows.html` | Implemented request/event flows, Saga path, compensation paths, async handling. |
| `contracts-and-events.html` | Implementation-near contracts, event patterns, DTO status; link to main contract catalog. |
| `data-and-consistency.html` | Persistence ownership, migrations, transaction boundaries, idempotency, locking. |
| `operations-and-observability.html` | Docker, health checks, environment, logging, metrics, traceability. |
| `decision-log.html` | Architecture deltas and decisions with date, status, consequences, evidence. |

Do not create all subpages blindly. Start with `index.html` and the pages needed for the current documentation task.

## Navigation Integration

When adding the section:

- Add a chapter card or content band in `konzept/index.html`.
- Add a `Technische Architektur` group to sidebars in affected pages.
- If the section becomes a primary documentation area, add it to all page sidebars.
- Maintain relative links so pages work when opened directly from disk.
- Keep breadcrumbs aligned, e.g. `Uebersicht > Technische Architektur > Runtime Flows`.

## Page Structure

Use the existing document shell:

- `body class="doc-page"`
- sidebar with brand and chapter navigation
- `main id="inhalt" class="page-shell doc-shell"`
- `header class="doc-hero"`
- `div class="doc-layout"`
- `aside class="toc-card"`
- `article class="article-content"`
- `nav class="doc-pagination"`

Use existing CSS classes before adding new styling.

## Content Model

Each technical architecture page should distinguish:

| Label | Meaning |
| --- | --- |
| `Implemented` | Verified in current code or tests. |
| `Planned` | Intended design, not yet implemented. |
| `Prototype` | Exists but not final enough to treat as stable. |
| `Needs decision` | Code, concept, or expectation conflict. |

Prefer short evidence references such as controller names, package scripts, Docker service names, test names, or page links. Avoid long code listings unless the code itself is the contract.

## Decision Log Entry Template

Use this table shape in `decision-log.html` or page-specific decision sections:

| Datum | Status | Thema | Entscheidung/Beobachtung | Betroffene Bereiche | Konsequenz | Nachweis | Offen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| YYYY-MM-DD | Implemented | Example | Short statement | Services/contracts/tests | Impact | File/test/link | Next question |

## Relationship To Existing Concept Pages

- `02_systemarchitektur_kommunikation.html`: high-level architecture and communication rules.
- `02a_contracts_und_schnittstellen.html`: readable contract catalog and canonical examples.
- Service chapters: conceptual service responsibilities and expected behavior.
- `12_tests_abnahme_demo.html`: verification strategy, TDD model, demo acceptance.
- `11_infrastruktur_deployment_repo.html`: local platform, Docker, env, repository structure.

The technical architecture section should link to these pages and add implementation-near status, not duplicate every paragraph.
