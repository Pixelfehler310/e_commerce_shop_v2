# Living Documentation Workflow

Use this workflow when a code change, architecture change, or planning change should be reflected in the concept site.

## Intent

Living documentation means the concept site should explain the architecture that is actually emerging, not only the original plan. It should stay useful for implementation, reviews, tests, and demos.

## Architecture-Relevant Triggers

Update or review documentation when a change touches:

- Service boundaries, modules, controllers, DTOs, interfaces, or endpoint paths.
- Events, queues, routing keys, consumers, producers, or audit event types.
- Persistence ownership, schemas, migrations, idempotency stores, locking, transactions.
- Saga flow, compensation behavior, status transitions, retries, circuit breakers.
- Auth, roles, guards, error shape, secrets, network exposure.
- Docker Compose, ports, health checks, environment variables, observability.
- Frontend API usage, admin timelines, simulation flows, WMS/storefront behavior.
- Tests that define contracts, acceptance behavior, concurrency, or demo scenarios.

## Review Steps

1. Read the relevant implementation files before editing docs.
2. Identify what changed at the architecture level.
3. Classify the change as one of:
   - `Implemented`: code exists and docs should reflect it.
   - `Planned`: design is intended but not implemented yet.
   - `Prototype`: code exists but is not final design.
   - `Needs decision`: code and concept disagree or intent is unclear.
4. Update the closest conceptual chapter only if its model changed.
5. Update the `Technische Architektur` section for implementation-near details.
6. Update the contract catalog if the change affects REST, events, DTOs, headers, error behavior, or payloads.
7. Update test/demo docs if the change affects verification or presentation.
8. Run local link validation after structural HTML edits.

## Architecture Delta Format

When documenting an emerging architecture decision or implementation delta, include this shape somewhere appropriate:

```text
Datum: <current date>
Ausloeser: <code change, decision, bug, test, demo need>
Status: Implemented | Planned | Prototype | Needs decision
Betroffene Bereiche: <services/frontends/contracts/tests>
Entscheidung oder Beobachtung: <short statement>
Konsequenzen: <runtime, data, test, operation, security impact>
Nachweis: <tests, files, endpoints, commands, demo scenario>
Offene Punkte: <what still needs clarification>
```

## Writing Rules

- Keep high-level concept pages stable and readable.
- Put implementation-near detail in the technical architecture section.
- Prefer tables for endpoints, event contracts, data ownership, and deltas.
- Mark uncertainty explicitly; do not write uncertain assumptions as final architecture.
- Link to related pages instead of duplicating long content.
- Avoid documenting every code detail; document decisions, contracts, flows, responsibilities, and consequences.

## Conceptual Consistency Rules

- A contract change must be reflected in the contract catalog and any affected service chapter.
- A Saga/status change must be reflected in Saga docs, service docs, tests, and audit expectations.
- A persistence or ownership change must be reflected in architecture, service docs, and infrastructure if needed.
- A frontend flow change must be reflected in frontend docs and, if it changes API expectations, contract docs.
- An observability or health change must be reflected in operations docs and technical architecture.
