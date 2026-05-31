# Project Context Reference

Use this reference when documentation work needs repo context.

## Product And Scope

The repository implements a university project named Distributed E-Commerce Core. It demonstrates a realistic distributed order flow with microservices, multiple frontends, reproducible failures, auditability, and local Docker-based operation.

The system is intentionally simulation-focused. Real payment providers and production compliance are out of scope. Provider behavior, failure modes, and demo scenarios should remain controllable.

## Services

| Area | Responsibility |
| --- | --- |
| `shop-service` | External API gateway, auth, roles, product catalog, basket, orders, Saga orchestration, idempotent checkout. |
| `warehouse-service` | Stock ownership, product stock, reservations, cancellation, final booking, stock adjustments, concurrency protection. |
| `billing-service` | Payment facade, charge, refund, provider stubs, webhooks, provider-mode simulation. |
| `invoice-service` | Async invoice generation after `PaymentSucceeded`; invoice failures must not roll back successful payment/order completion. |
| `audit-service` | Append-only snapshots, order timelines, search/read models, SSE stream, no business decision authority. |

## Frontends

| Frontend | Purpose |
| --- | --- |
| `storefront-ui` | Customer product, basket, checkout, own order status. |
| `admin-dashboard` | Admin order search, audit timeline, status overview, health and demo visibility. |
| `warehouse-wms` | Logistics stock and reservation views, stock adjustments. |
| `simulation-panel` | Demo control, failure modes, scenario execution, concurrency tests. |

## Architecture Invariants

- Shop-Service is the only regular external business API entry point.
- Frontends must not directly call Warehouse, Billing, Invoice, or Audit except through deliberate admin/monitoring flows.
- Each stateful service owns its own persistence; direct cross-service database access is forbidden.
- Cross-service consistency is handled by Saga steps, idempotent commands, events, and compensations.
- Warehouse prevents overselling via database-backed concurrency control, not in-memory locking.
- Billing hides provider specifics behind a payment facade.
- Invoice is asynchronous and non-blocking for successful checkout completion.
- Audit stores immutable snapshots and supports diagnosis; it must not decide business validity.

## Cross-Cutting Concepts

- `correlationId` / `X-Correlation-Id`: connects logs, audit, events, service calls, and UI timelines.
- `X-Idempotency-Key`: required for critical commands such as checkout.
- RFC 7807 Problem Details: common error shape for HTTP errors.
- RabbitMQ: event transport for async flows and audit/invoice integration.
- Redis: idempotency/session/cache concerns.
- PostgreSQL: service-owned persistence.
- Loki/Grafana: observability target for logs and dashboards.

## Current Documentation Model

- Active source of truth is direct HTML under `konzept/index.html` and `konzept/pages/**/*.html`.
- Shared styling lives in `konzept/assets/styles.css`.
- Archived Markdown is under `konzept/archive/markdown-sources/` and must not be edited as the visible source.
- The generator was removed and must not be reintroduced unless explicitly requested.

## Known Documentation Anchors

- Concept overview: `konzept/index.html`.
- Communication and service map: `konzept/pages/architektur/02_systemarchitektur_kommunikation.html`.
- Contract catalog: `konzept/pages/architektur/02a_contracts_und_schnittstellen.html`.
- Service chapters: `konzept/pages/services/*.html`.
- Tests, TDD, demo and acceptance: `konzept/pages/qualitaet/12_tests_abnahme_demo.html`.
- Infrastructure and repository: `konzept/pages/betrieb/11_infrastruktur_deployment_repo.html`.
