# Konzeptordner: Distributed E-Commerce Core

Dieser Ordner enthält ein aus dem PDF `Ganzheitliches_Technisches_Umsetzungskonzept_Maximal_Erweitert.pdf` ausgearbeitetes, stark detailliertes Umsetzungskonzept für den Distributed E-Commerce Core.

Der Einstieg erfolgt über die klickbare HTML-Übersicht. Die Markdown-Dateien bleiben als bearbeitbare Quellen erhalten; die lesbare, verschachtelte HTML-Fassung liegt unter `pages/`.

- [index.html](index.html)

## Leseweg

1. [Quickstart und Leseweg](pages/grundlagen/00_quickstart_und_leseweg.html) - Orientierung, Zielbild und empfohlene Reihenfolge.
2. [Anforderungen, Ziele und Scope](pages/grundlagen/01_anforderungen_ziele_scope.html) - fachliche und technische Anforderungen.
3. [Anforderungsdokument](pages/grundlagen/01a_anforderungsdokument.html) - prüfbare funktionale, nichtfunktionale, subsystembezogene und betriebliche Anforderungen.
4. [Systemarchitektur und Kommunikation](pages/architektur/02_systemarchitektur_kommunikation.html) - Systemlandschaft, Kommunikationsmuster und Verantwortlichkeiten.
5. [Shop-Service](pages/services/03_service_shop.html) - Shop-Service als Gateway, IAM, Katalog, Warenkorb und Saga-Orchestrator.
6. [Warehouse-Service](pages/services/04_service_warehouse.html) - Warehouse-Service, Bestand, Reservierung und Concurrency Control.
7. [Billing und Invoice](pages/services/05_service_billing_invoice.html) - Payment-Fassade, Zahlungszustände, Webhooks und Rechnungen.
8. [Audit-Service](pages/services/06_audit_service.html) - Audit-Service, Snapshots, Event-Store-Light und Admin-Lesemodelle.
9. [Saga, Transaktionen und Konsistenz](pages/architektur/07_saga_transaktionen_konsistenz.html) - Orchestrierte Saga, Happy Path, Fehlerpfade und Kompensation.
10. [Idempotenz, Resilienz und Security](pages/qualitaet/08_idempotenz_resilienz_security.html) - Idempotenz, Circuit Breaker, Retry, Auth und Guards.
11. [Frontends und Simulationssuite](pages/frontends/09_frontends_simulationssuite.html) - Customer View, Admin View, WMS und Demo-Control-Panel.
12. [Observability, Logging und Tracing](pages/qualitaet/10_observability_logging_tracing.html) - JSON-Logging, Correlation IDs, Loki/Grafana und Dashboards.
13. [Infrastruktur, Deployment und Repository](pages/betrieb/11_infrastruktur_deployment_repo.html) - Docker Compose, Umgebungsvariablen und Repository-Struktur.
14. [Tests, Abnahme und Demo](pages/qualitaet/12_tests_abnahme_demo.html) - Teststrategie, Abnahmekriterien und Präsentationsszenarien.
15. [Umsetzungsplan und Roadmap](pages/planung/13_umsetzungsplan_roadmap.html) - Phasenplan, Meilensteine, Risiken und Priorisierung.

## HTML neu generieren

Wenn sich Markdown-Inhalte ändern, kann die HTML-Fassung mit folgendem Befehl aktualisiert werden:

```powershell
python .\konzept\tools\build_concept_html.py
```

## Grundprinzipien

- Jeder Microservice besitzt seine eigene Datenhaltung; direkte Fremd-Datenbankzugriffe sind verboten.
- Der Shop-Service ist der einzige externe API-Einstiegspunkt und orchestriert den Bestellprozess.
- Geschäftsrelevante Zustandswechsel werden als unveränderliche Audit-Snapshots protokolliert.
- Der Warehouse-Service verhindert Überverkäufe durch pessimistische Sperren in PostgreSQL.
- Die Payment-Integration erfolgt ausschließlich über eine konfigurierbare Fassade.
- Fehler- und Demo-Szenarien sind keine Nebensache, sondern explizite Systemfunktionen.