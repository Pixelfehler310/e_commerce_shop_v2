# Konzeptordner: Distributed E-Commerce Core

Dieser Ordner enthält ein aus dem PDF `Ganzheitliches_Technisches_Umsetzungskonzept_Maximal_Erweitert.pdf` ausgearbeitetes, stark detailliertes Umsetzungskonzept für den Distributed E-Commerce Core.

Der Einstieg erfolgt über die klickbare HTML-Übersicht:

- [index.html](index.html)

## Leseweg

1. [00_quickstart_und_leseweg.md](00_quickstart_und_leseweg.md) - Orientierung, Zielbild und empfohlene Reihenfolge.
2. [01_anforderungen_ziele_scope.md](01_anforderungen_ziele_scope.md) - fachliche und technische Anforderungen.
3. [02_systemarchitektur_kommunikation.md](02_systemarchitektur_kommunikation.md) - Systemlandschaft, Kommunikationsmuster und Verantwortlichkeiten.
4. [03_service_shop.md](03_service_shop.md) - Shop-Service als Gateway, IAM, Katalog, Warenkorb und Saga-Orchestrator.
5. [04_service_warehouse.md](04_service_warehouse.md) - Warehouse-Service, Bestand, Reservierung und Concurrency Control.
6. [05_service_billing_invoice.md](05_service_billing_invoice.md) - Payment-Fassade, Zahlungszustände, Webhooks und Rechnungen.
7. [06_audit_service.md](06_audit_service.md) - Audit-Service, Snapshots, Event-Store-Light und Admin-Lesemodelle.
8. [07_saga_transaktionen_konsistenz.md](07_saga_transaktionen_konsistenz.md) - Orchestrierte Saga, Happy Path, Fehlerpfade und Kompensation.
9. [08_idempotenz_resilienz_security.md](08_idempotenz_resilienz_security.md) - Idempotenz, Circuit Breaker, Retry, Auth und Guards.
10. [09_frontends_simulationssuite.md](09_frontends_simulationssuite.md) - Customer View, Admin View, WMS und Demo-Control-Panel.
11. [10_observability_logging_tracing.md](10_observability_logging_tracing.md) - JSON-Logging, Correlation IDs, Loki/Grafana und Dashboards.
12. [11_infrastruktur_deployment_repo.md](11_infrastruktur_deployment_repo.md) - Docker Compose, Umgebungsvariablen und Repository-Struktur.
13. [12_tests_abnahme_demo.md](12_tests_abnahme_demo.md) - Teststrategie, Abnahmekriterien und Präsentationsszenarien.
14. [13_umsetzungsplan_roadmap.md](13_umsetzungsplan_roadmap.md) - Phasenplan, Meilensteine, Risiken und Priorisierung.

## Grundprinzipien

- Jeder Microservice besitzt seine eigene Datenhaltung; direkte Fremd-Datenbankzugriffe sind verboten.
- Der Shop-Service ist der einzige externe API-Einstiegspunkt und orchestriert den Bestellprozess.
- Geschäftsrelevante Zustandswechsel werden als unveränderliche Audit-Snapshots protokolliert.
- Der Warehouse-Service verhindert Überverkäufe durch pessimistische Sperren in PostgreSQL.
- Die Payment-Integration erfolgt ausschließlich über eine konfigurierbare Fassade.
- Fehler- und Demo-Szenarien sind keine Nebensache, sondern explizite Systemfunktionen.