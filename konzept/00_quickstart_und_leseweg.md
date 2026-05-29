# Quickstart und Leseweg

## Zweck dieses Konzepts

Dieses Konzept übersetzt das PDF in einen umsetzbaren, teamtauglichen Architektur- und Implementierungsplan. Es beschreibt nicht nur die Zielarchitektur, sondern konkretisiert Verantwortlichkeiten, Schnittstellen, Datenflüsse, Fehlerpfade, Testfälle, Deployment-Bausteine und Demo-Szenarien.

Das Ziel ist ein verteilter Online-Shop als Microservice-System mit folgenden Schwerpunkten:

- Strikte fachliche Trennung der Services.
- Eigene Datenhaltung je Service.
- Orchestrierte Saga für verteilte Konsistenz.
- Belastbare Bestandsführung mit pessimistischen Datenbanksperren.
- Konfigurierbare Payment-Fassade mit synchronen und asynchronen Anbieter-Stubs.
- Audit-Snapshots für Nachvollziehbarkeit, Debugging und Admin-Visualisierung.
- Mehrere Frontend-Views für Kunden, Administration, Lager und Simulation.
- Docker-Compose-basierter Betrieb mit Observability-Stack.

## Empfohlener Einstieg

Wer das System zuerst verstehen möchte, liest in dieser Reihenfolge:

1. Ziele und Scope in [01_anforderungen_ziele_scope.md](01_anforderungen_ziele_scope.md).
2. Architektur und Kommunikation in [02_systemarchitektur_kommunikation.md](02_systemarchitektur_kommunikation.md).
3. Saga-Abläufe in [07_saga_transaktionen_konsistenz.md](07_saga_transaktionen_konsistenz.md).
4. Service-Details in [03_service_shop.md](03_service_shop.md), [04_service_warehouse.md](04_service_warehouse.md), [05_service_billing_invoice.md](05_service_billing_invoice.md) und [06_audit_service.md](06_audit_service.md).
5. Frontend- und Demo-Sicht in [09_frontends_simulationssuite.md](09_frontends_simulationssuite.md).
6. Tests und Abnahme in [12_tests_abnahme_demo.md](12_tests_abnahme_demo.md).

## Zielbild in einem Satz

Das System soll demonstrieren, wie ein realistisch verteilter E-Commerce-Kern trotz getrennter Datenbanken, synchroner und asynchroner Kommunikation, Zahlungsfehlern, Nebenläufigkeit und Service-Ausfällen einen nachvollziehbaren, konsistenten und präsentierbaren Bestellprozess abbildet.

## Wichtigste Architekturentscheidungen

| Entscheidung | Konsequenz |
| --- | --- |
| Shop-Service als einziges Gateway | Frontends sprechen keine internen Services direkt an. |
| Datenbank pro Service | Keine versteckte Kopplung über gemeinsame Tabellen. |
| Saga-Orchestrierung im Shop-Service | Bestellfluss bleibt zentral nachvollziehbar und kompensierbar. |
| RabbitMQ für Domain-Events | Rechnung und Audit laufen entkoppelt und robust. |
| Redis für Idempotenz und Sessions | Doppelbestellungen und Wiederholungen werden kontrolliert. |
| PostgreSQL `SELECT ... FOR UPDATE` im Warehouse | Überverkäufe werden auf Datenbankebene verhindert. |
| Payment-Fassade im Billing-Service | Anbieter können gewechselt oder erweitert werden, ohne Business-Code umzubauen. |
| Audit-Service ohne Business-Logik | Audit bleibt generisch, append-only und langfristig auswertbar. |

## Ergebnisartefakte

Das fertige Projekt soll mindestens diese Artefakte enthalten:

- `docker-compose.yml` zum Start aller Services und Infrastrukturkomponenten.
- Fünf Backend-Services: Shop, Warehouse, Billing, Invoice, Audit.
- Vier Frontends: Customer Storefront, Admin Dashboard, Warehouse WMS, Simulation Panel.
- PostgreSQL-Instanzen pro zustandsbehaftetem Service.
- RabbitMQ für asynchrone Events.
- Redis für Idempotenz und Sessions.
- Loki/Grafana oder vergleichbarer Stack für Logs und Dashboards.
- Dokumentierte APIs, Datenmodelle, Events, ADRs und Demo-Skripte.

## Begriffe

| Begriff | Bedeutung |
| --- | --- |
| `correlationId` | Eindeutiger technischer Schlüssel für einen Bestell- oder Prozessdurchlauf. |
| `X-Correlation-Id` | HTTP-Header zur Weitergabe der Prozessidentität zwischen Services. |
| `X-Idempotency-Key` | Client-seitig erzeugter Schlüssel zur Verhinderung doppelter Bestellverarbeitung. |
| Saga | Folge lokaler Transaktionen mit Kompensationsschritten statt verteilter ACID-Transaktion. |
| Snapshot | Unveränderlicher Audit-Datensatz zu einem Zustand oder Ereignis. |
| Payment-Fassade | Einheitliche Schnittstelle vor mehreren Zahlungsanbieter-Adaptern. |
| Reservation | Temporäre Lagerblockierung vor Zahlung und finaler Ausbuchung. |
| Booking | Endgültige Abbuchung reservierter Ware nach erfolgreicher Zahlung. |

## Abgrenzung

Das Konzept beschreibt ein simulatorisches Universitätsprojekt. Es ist bewusst realitätsnah aufgebaut, bindet aber keine echten Zahlungsanbieter mit echten API-Schlüsseln an. Payment-Anbieter werden über Stubs, MSW und Faker simuliert. Sicherheitsmechanismen wie JWT, Rollen und Guards werden fachlich umgesetzt, ersetzen aber keine produktionsreife Compliance-Prüfung für echte Zahlungsdaten.